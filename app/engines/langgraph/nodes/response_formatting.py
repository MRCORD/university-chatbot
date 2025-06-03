# =======================
# app/engines/langgraph/nodes/response_formatting.py
# =======================
"""
Response formatting node for LangGraph workflows.

Simple node that formats final conversational responses.
Follows KISS principle - one job, do it well.
"""

import structlog

from app.engines.langgraph.nodes.base_node import BaseNode
from app.engines.langgraph.state.conversation_state import ConversationState, StateManager
from app.engines.langgraph.state.schemas import IntentType

logger = structlog.get_logger()


class ResponseFormattingNode(BaseNode):
    """
    Formats final conversational response based on intent and tool results.
    
    Simple responsibility:
    1. Look at intent and tool results
    2. Format appropriate conversational response
    3. Add suggested actions
    
    That's it. KISS.
    """
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """
        Format final response and update state.
        
        Args:
            state: Current conversation state
            
        Returns:
            State updated with formatted response
        """
        self._log_start(state)
        
        try:
            intent = state.get('intent', '')
            tool_result = state.get('tool_result', {})
            tool_success = state.get('tool_success', False)
            sources = state.get('sources', [])
            
            # Format response based on intent
            if intent == IntentType.QUESTION.value:
                response, actions = self._format_question_response(tool_result, tool_success, sources)
            elif intent == IntentType.COMPLAINT.value:
                response, actions = self._format_complaint_response(tool_result, tool_success)
            else:
                response, actions = self._format_general_response(state)
            
            # Update state with formatted response
            StateManager.update_response(
                state,
                response=response,
                confidence=state.get('confidence', 0.8),
                suggested_actions=actions
            )
            
            self._log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Response formatting failed: {str(e)}"
            self._log_error(state, error_msg)
            
            # Fallback response
            fallback_response = "Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?"
            StateManager.update_response(
                state,
                response=fallback_response,
                confidence=0.1,
                suggested_actions=["Intenta reformular tu pregunta"]
            )
            StateManager.add_error(state, "response_formatting_error", error_msg)
            
            return state
    
    def _format_question_response(self, tool_result: dict, success: bool, sources: list) -> tuple:
        """Format response for document questions."""
        
        if success and tool_result.get('type') == 'document_search':
            # Found relevant documents
            content = tool_result.get('content', '')
            
            response = f"Según los documentos de UP:\n\n{content}"
            
            # Add sources if available
            if sources:
                source_text = ", ".join(sources[:2])  # Max 2 sources for readability
                response += f"\n\n📄 Fuente: {source_text}"
            
            actions = [
                "¿Necesitas más detalles sobre este tema?",
                "¿Hay algo más en lo que pueda ayudarte?"
            ]
            
        else:
            # No documents found or search failed
            response = """No encontré información específica sobre eso en los documentos de UP.

¿Podrías ser más específico o usar palabras clave diferentes? También puedo ayudarte con:
• Procedimientos académicos
• Fechas límite importantes  
• Reglamentos de la universidad"""
            
            actions = [
                "Intenta con palabras clave más específicas",
                "Pregunta sobre un tema específico",
                "Reporta un problema"
            ]
        
        return response, actions
    
    def _format_complaint_response(self, tool_result: dict, success: bool) -> tuple:
        """Format response for complaint submissions."""
        
        if success and tool_result.get('type') == 'complaint_submitted':
            # Complaint submitted successfully
            short_id = tool_result.get('short_id', 'desconocido')
            
            response = f"""✅ He registrado tu reporte exitosamente.

📋 ID del reporte: #{short_id}

Tu reporte será revisado por el equipo administrativo. Puedes hacer seguimiento con este ID."""
            
            actions = [
                "¿Hay algo más en lo que pueda ayudarte?",
                "¿Quieres reportar otro problema?"
            ]
            
        else:
            # Complaint submission failed
            response = """Lo siento, no pude registrar tu reporte en este momento.

Por favor intenta de nuevo en unos minutos, o contacta directamente con la administración si es urgente."""
            
            actions = [
                "Intenta reportar de nuevo",
                "Pregunta sobre procedimientos de UP"
            ]
        
        return response, actions
    
    def _format_general_response(self, state: ConversationState) -> tuple:
        """Format response for general conversation."""
        
        user_message = state.get('user_message', '')
        
        # Simple, friendly general response
        if any(greeting in user_message.lower() for greeting in ['hola', 'buenos', 'buenas']):
            response = """¡Hola! Soy el asistente virtual de Universidad del Pacífico.

Puedo ayudarte con:
• Información sobre procedimientos académicos
• Búsqueda en documentos oficiales de UP
• Registro de reportes o problemas

¿En qué puedo ayudarte hoy?"""
            
        elif any(thanks in user_message.lower() for thanks in ['gracias', 'thank']):
            response = """¡De nada! Me alegra haber podido ayudarte.

Si tienes más preguntas sobre UP o necesitas ayuda con algún procedimiento, no dudes en preguntar."""
            
        else:
            response = f"""Vi tu mensaje: "{user_message[:50]}..."

Soy el asistente de Universidad del Pacífico. ¿En qué puedo ayudarte específicamente?"""
        
        actions = [
            "Pregunta sobre procedimientos de UP",
            "Buscar en documentos oficiales", 
            "Reportar un problema"
        ]
        
        return response, actions