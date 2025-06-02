# =======================
# app/engines/langgraph_engine.py
# =======================
from typing import Dict, Any, List, Optional
import structlog
import json

from app.interfaces.conversation_engine import (
    ConversationEngine, ConversationContext, ConversationResponse, QueryType
)
from app.models.document import DocumentSearchRequest
from app.models.complaint import ComplaintSubmissionRequest, ComplaintCategory
from app.core.exceptions import ConversationEngineException

logger = structlog.get_logger()

try:
    from langgraph import StateGraph, START, END
    from typing_extensions import TypedDict
except ImportError:
    logger.warning("LangGraph not installed. Install with: pip install langgraph")
    StateGraph = None
    START = "START"
    END = "END"
    TypedDict = dict


class ConversationState(TypedDict):
    """State for LangGraph conversation workflow."""
    user_message: str
    user_id: str
    conversation_history: List[Dict[str, str]]
    intent: Optional[str]
    tool_result: Optional[Dict[str, Any]]
    response: Optional[str]
    sources: List[str]
    confidence: float
    suggested_actions: List[str]
    metadata: Dict[str, Any]


class SimpleLangGraphEngine(ConversationEngine):
    """Simple LangGraph engine for chat routing only."""
    
    def __init__(
        self, 
        document_service,
        complaint_service,
        llm_provider
    ):
        self.document_service = document_service
        self.complaint_service = complaint_service
        self.llm = llm_provider
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build simple 3-node workflow for chat routing."""
        if not StateGraph:
            logger.warning("LangGraph not available, using fallback")
            return None
        
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("execute_action", self._execute_action)
        workflow.add_node("format_response", self._format_response)
        
        # Add edges
        workflow.add_edge(START, "classify_intent")
        workflow.add_edge("classify_intent", "execute_action")
        workflow.add_edge("execute_action", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def process_query(
        self,
        user_message: str,
        context: ConversationContext
    ) -> ConversationResponse:
        """Process user query using LangGraph workflow."""
        try:
            if not self.workflow:
                # Fallback if LangGraph not available
                return await self._fallback_processing(user_message, context)
            
            # Initialize state
            state = ConversationState(
                user_message=user_message,
                user_id=context.user_id,
                conversation_history=context.conversation_history,
                intent=None,
                tool_result=None,
                response=None,
                sources=[],
                confidence=0.8,
                suggested_actions=[],
                metadata={}
            )
            
            # Run workflow
            result = await self.workflow.ainvoke(state)
            
            # Convert to response format
            return ConversationResponse(
                response_text=result['response'],
                query_type=self._map_intent_to_query_type(result['intent']),
                sources=result['sources'],
                confidence_score=result['confidence'],
                structured_data=result.get('tool_result'),
                suggested_actions=result['suggested_actions'],
                requires_followup=False,
                metadata={
                    'engine': 'langgraph',
                    'intent': result['intent'],
                    **result['metadata']
                }
            )
            
        except Exception as e:
            logger.error("LangGraph processing failed", error=str(e))
            # Fallback to simple processing
            return await self._fallback_processing(user_message, context)
    
    async def _classify_intent(self, state: ConversationState) -> ConversationState:
        """Classify user intent using LLM."""
        try:
            prompt = f"""
Analiza este mensaje de un estudiante de Universidad del Pacífico y clasifica su intención:

Mensaje: "{state['user_message']}"

Responde con UNA sola palabra:
- "pregunta" - si está preguntando sobre procedimientos, reglamentos, fechas límite de UP
- "queja" - si está reportando un problema, issue o queja
- "conversacion" - si es saludo, agradecimiento, o conversación general

Respuesta:"""

            intent = await self.llm.generate_text(prompt, max_tokens=10, temperature=0.1)
            state['intent'] = intent.strip().lower()
            
            logger.info("Intent classified", 
                       message=state['user_message'][:50],
                       intent=state['intent'])
            
        except Exception as e:
            logger.error("Intent classification failed", error=str(e))
            state['intent'] = 'conversacion'  # Default fallback
        
        return state
    
    async def _execute_action(self, state: ConversationState) -> ConversationState:
        """Execute appropriate action based on intent."""
        intent = state['intent']
        message = state['user_message']
        user_id = state['user_id']
        
        try:
            if intent == "pregunta":
                # Use DocumentService for Q&A
                search_request = DocumentSearchRequest(
                    query=message,
                    limit=3,
                    similarity_threshold=0.7
                )
                
                search_result = await self.document_service.search_documents(search_request)
                
                if search_result.chunks:
                    # Found relevant documents
                    best_chunk = search_result.chunks[0]
                    state['tool_result'] = {
                        'type': 'document_search',
                        'content': best_chunk.content,
                        'document_name': best_chunk.document.filename,
                        'similarity_score': best_chunk.similarity_score
                    }
                    state['sources'] = [chunk.document.filename for chunk in search_result.chunks[:2]]
                    state['confidence'] = min(0.9, best_chunk.similarity_score + 0.1)
                else:
                    # No documents found
                    state['tool_result'] = {
                        'type': 'no_documents',
                        'message': 'No encontré información específica sobre eso en los documentos de UP.'
                    }
                    state['sources'] = []
                    state['confidence'] = 0.3
            
            elif intent == "queja":
                # Use ComplaintService to submit complaint
                complaint_request = ComplaintSubmissionRequest(
                    title="Reporte desde chat",
                    description=message,
                    category=ComplaintCategory.OTHER,  # Will be auto-categorized later
                    is_anonymous=True,
                    user_id=user_id
                )
                
                complaint_result = await self.complaint_service.submit_complaint(complaint_request)
                
                state['tool_result'] = {
                    'type': 'complaint_submitted',
                    'complaint_id': complaint_result.id,
                    'short_id': complaint_result.id[:8]
                }
                state['sources'] = []
                state['confidence'] = 0.95
            
            else:  # conversacion
                # Direct LLM response for general chat
                chat_prompt = f"""
Eres un asistente útil para estudiantes de Universidad del Pacífico en Lima, Perú.
Responde de manera amigable y profesional.

Estudiante: {message}

Respuesta:"""
                
                llm_response = await self.llm.generate_text(
                    chat_prompt, 
                    max_tokens=200, 
                    temperature=0.7
                )
                
                state['tool_result'] = {
                    'type': 'general_chat',
                    'response': llm_response
                }
                state['sources'] = []
                state['confidence'] = 0.8
            
        except Exception as e:
            logger.error("Action execution failed", 
                        intent=intent, 
                        error=str(e))
            # Fallback response
            state['tool_result'] = {
                'type': 'error',
                'response': 'Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?'
            }
            state['sources'] = []
            state['confidence'] = 0.1
        
        return state
    
    async def _format_response(self, state: ConversationState) -> ConversationState:
        """Format final response based on tool results."""
        tool_result = state['tool_result']
        intent = state['intent']
        
        try:
            if tool_result['type'] == 'document_search':
                # Format document-based response
                content = tool_result['content']
                doc_name = tool_result['document_name']
                
                response = f"""Según los documentos de UP:

{content}

📄 Fuente: {doc_name}"""
                
                state['suggested_actions'] = [
                    "¿Necesitas más detalles sobre este tema?",
                    "¿Hay algo más en lo que pueda ayudarte?"
                ]
            
            elif tool_result['type'] == 'no_documents':
                response = f"""{tool_result['message']}

¿Podrías ser más específico o usar palabras clave diferentes? También puedo ayudarte con:
• Procedimientos académicos
• Fechas límite importantes
• Reglamentos de la universidad"""
                
                state['suggested_actions'] = [
                    "Intenta con palabras clave más específicas",
                    "Pregunta sobre un tema específico"
                ]
            
            elif tool_result['type'] == 'complaint_submitted':
                short_id = tool_result['short_id']
                response = f"""✅ He registrado tu reporte exitosamente.

📋 ID del reporte: #{short_id}

Tu reporte será revisado por el equipo administrativo. Puedes hacer seguimiento con este ID."""
                
                state['suggested_actions'] = [
                    "¿Hay algo más en lo que pueda ayudarte?",
                    "¿Quieres reportar otro problema?"
                ]
            
            elif tool_result['type'] == 'general_chat':
                response = tool_result['response']
                state['suggested_actions'] = [
                    "Pregunta sobre procedimientos de UP",
                    "Reporta un problema"
                ]
            
            else:  # error case
                response = tool_result['response']
                state['suggested_actions'] = [
                    "Intenta reformular tu pregunta",
                    "Contacta soporte si el problema persiste"
                ]
            
            state['response'] = response
            state['metadata'] = {
                'tool_used': tool_result['type'],
                'processing_time': None  # Could add timing
            }
            
        except Exception as e:
            logger.error("Response formatting failed", error=str(e))
            state['response'] = "Lo siento, hubo un error procesando tu mensaje."
            state['suggested_actions'] = []
        
        return state
    
    def _map_intent_to_query_type(self, intent: str) -> QueryType:
        """Map internal intent to QueryType enum."""
        mapping = {
            'pregunta': QueryType.DOCUMENT_QA,
            'queja': QueryType.COMPLAINT_SUBMISSION,
            'conversacion': QueryType.GENERAL_INFO
        }
        return mapping.get(intent, QueryType.GENERAL_INFO)
    
    async def _fallback_processing(
        self, 
        user_message: str, 
        context: ConversationContext
    ) -> ConversationResponse:
        """Fallback processing when LangGraph is not available."""
        try:
            # Simple keyword-based routing
            message_lower = user_message.lower()
            
            # Check for question keywords
            question_keywords = ['cómo', 'cuándo', 'dónde', 'qué', 'quién', 'procedimiento', 'reglamento']
            if any(keyword in message_lower for keyword in question_keywords):
                # Try document search
                search_request = DocumentSearchRequest(query=user_message, limit=2)
                search_result = await self.document_service.search_documents(search_request)
                
                if search_result.chunks:
                    response_text = f"Según los documentos de UP:\n\n{search_result.chunks[0].content}"
                    sources = [chunk.document.filename for chunk in search_result.chunks]
                    query_type = QueryType.DOCUMENT_QA
                else:
                    response_text = "No encontré información específica sobre eso en los documentos."
                    sources = []
                    query_type = QueryType.GENERAL_INFO
            
            # Check for complaint keywords
            elif any(word in message_lower for word in ['problema', 'issue', 'error', 'falla', 'no funciona']):
                response_text = "He notado que reportas un problema. ¿Podrías dar más detalles para ayudarte mejor?"
                sources = []
                query_type = QueryType.COMPLAINT_SUBMISSION
            
            else:
                # General response
                response_text = f"Hola! Soy el asistente de UP. Vi tu mensaje: '{user_message}'. ¿En qué puedo ayudarte específicamente?"
                sources = []
                query_type = QueryType.GENERAL_INFO
            
            return ConversationResponse(
                response_text=response_text,
                query_type=query_type,
                sources=sources,
                confidence_score=0.7,
                structured_data=None,
                suggested_actions=["Pregunta sobre procedimientos", "Reporta un problema"],
                requires_followup=False,
                metadata={'engine': 'fallback'}
            )
            
        except Exception as e:
            logger.error("Fallback processing failed", error=str(e))
            return ConversationResponse(
                response_text="Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?",
                query_type=QueryType.GENERAL_INFO,
                sources=[],
                confidence_score=0.1,
                structured_data=None,
                suggested_actions=["Intenta de nuevo", "Contacta soporte"],
                requires_followup=False,
                metadata={'engine': 'error_fallback'}
            )
    
    async def initialize_documents(self, document_paths: List[str]) -> bool:
        """Initialize documents - not needed for our approach."""
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check engine health."""
        return {
            "status": "healthy",
            "engine": "langgraph",
            "workflow_available": self.workflow is not None,
            "llm_available": self.llm is not None,
            "services_available": {
                "document_service": self.document_service is not None,
                "complaint_service": self.complaint_service is not None
            }
        }