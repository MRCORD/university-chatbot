# =======================
# app/engines/langgraph/engine.py
# =======================
"""
Main modular LangGraph conversation engine.

Simple coordinator that sets up tools, nodes, and workflow to process conversations.
Follows KISS principle - clear setup, minimal complexity, focused responsibility.
"""

from typing import Dict, Any, List, Optional
import time
import structlog

from app.interfaces.conversation_engine import (
    ConversationEngine, ConversationContext, ConversationResponse, QueryType
)
from app.engines.langgraph.state.conversation_state import ConversationState, StateManager
from app.engines.langgraph.state.schemas import IntentType
from app.engines.langgraph.tools import create_tool_registry
from app.engines.langgraph.nodes import create_node_registry
from app.engines.langgraph.workflows import create_chat_workflow

logger = structlog.get_logger()


class ModularLangGraphEngine(ConversationEngine):
    """
    Main LangGraph conversation engine.
    
    Simple coordinator that:
    1. Sets up tools (service wrappers)
    2. Sets up nodes (workflow steps)  
    3. Sets up workflow (orchestration)
    4. Processes conversations
    
    That's it. KISS.
    """
    
    def __init__(self, services: Dict[str, Any], providers: Dict[str, Any]):
        """
        Initialize the engine with service dependencies.
        
        Args:
            services: Dictionary of service instances (DocumentService, etc.)
            providers: Dictionary of provider instances (LLMProvider, etc.)
        """
        self.services = services
        self.providers = providers
        
        # Setup components
        self.tools = self._setup_tools()
        self.nodes = self._setup_nodes()
        self.workflow = self._setup_workflow()
        
        # Metrics
        self._conversation_count = 0
        self._total_processing_time = 0.0
        
        logger.info("ModularLangGraphEngine initialized",
                   tools=list(self.tools.keys()),
                   nodes=list(self.nodes.keys()),
                   workflow_available=self.workflow is not None)
    
    async def process_query(
        self,
        user_message: str,
        context: ConversationContext
    ) -> ConversationResponse:
        """
        Process user query through the LangGraph workflow.
        
        Args:
            user_message: User's input message
            context: Conversation context and metadata
            
        Returns:
            ConversationResponse with AI-generated response
        """
        start_time = time.time()
        
        try:
            logger.info("Processing conversation query",
                       user_id=context.user_id,
                       message_preview=user_message[:50],
                       session_id=context.session_id)
            
            # Initialize conversation state
            state = StateManager.initialize_state(
                user_message=user_message,
                user_id=context.user_id,
                conversation_id=context.session_id,
                conversation_history=context.conversation_history
            )
            
            # Execute workflow
            final_state = await self.workflow.execute(state)
            
            # Convert to response format
            response = self._convert_to_response(final_state)
            
            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(processing_time, success=True)
            
            logger.info("Conversation query processed successfully",
                       user_id=context.user_id,
                       intent=final_state.get('intent'),
                       processing_time=processing_time,
                       response_length=len(response.response_text))
            
            return response
            
        except Exception as e:
            # Handle processing errors
            processing_time = time.time() - start_time
            self._update_metrics(processing_time, success=False)
            
            logger.error("Conversation query processing failed",
                        user_id=context.user_id,
                        error=str(e),
                        processing_time=processing_time,
                        exc_info=True)
            
            # Return fallback response
            return self._create_fallback_response(user_message, str(e))
    
    async def initialize_documents(self, document_paths: List[str]) -> bool:
        """
        Initialize documents for the engine.
        
        Note: Our engine doesn't need document initialization since
        documents are processed via the DocumentService when uploaded.
        
        Args:
            document_paths: List of document paths (unused)
            
        Returns:
            True (always successful)
        """
        logger.info("Document initialization requested", 
                   document_count=len(document_paths))
        
        # Check if document tool is available and healthy
        if 'document' in self.tools:
            return await self.tools['document'].health_check()
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check engine health and component status.
        
        Returns:
            Dictionary with health status of all components
        """
        try:
            # Check tool health
            tool_health = {}
            for name, tool in self.tools.items():
                tool_health[name] = await tool.health_check()
            
            # Check node availability
            node_health = {name: node is not None for name, node in self.nodes.items()}
            
            # Overall health
            all_tools_healthy = all(tool_health.values())
            all_nodes_available = all(node_health.values())
            workflow_available = self.workflow is not None
            
            overall_health = all_tools_healthy and all_nodes_available and workflow_available
            
            health_info = {
                'status': 'healthy' if overall_health else 'degraded',
                'engine': 'ModularLangGraphEngine',
                'components': {
                    'tools': tool_health,
                    'nodes': node_health,
                    'workflow': workflow_available
                },
                'metrics': self._get_metrics(),
                'workflow_info': self.workflow.get_workflow_info() if hasattr(self.workflow, 'get_workflow_info') else {}
            }
            
            logger.info("Engine health check completed", 
                       status=health_info['status'],
                       tools_healthy=all_tools_healthy,
                       nodes_available=all_nodes_available)
            
            return health_info
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'engine': 'ModularLangGraphEngine'
            }
    
    def _setup_tools(self) -> Dict[str, Any]:
        """Setup tool registry from services and providers."""
        try:
            tools = create_tool_registry(
                document_service=self.services.get('document_service'),
                complaint_service=self.services.get('complaint_service'),
                llm_provider=self.providers.get('llm_provider')
            )
            
            logger.info("Tools setup completed", tool_count=len(tools))
            return tools
            
        except Exception as e:
            logger.error("Tool setup failed", error=str(e))
            return {}
    
    def _setup_nodes(self) -> Dict[str, Any]:
        """Setup node registry with tool dependencies."""
        try:
            if not self.tools:
                logger.warning("No tools available for node setup")
                return {}
            
            nodes = create_node_registry(self.tools)
            
            logger.info("Nodes setup completed", node_count=len(nodes))
            return nodes
            
        except Exception as e:
            logger.error("Node setup failed", error=str(e))
            return {}
    
    def _setup_workflow(self) -> Optional[Any]:
        """Setup main chat workflow."""
        try:
            if not self.nodes:
                logger.warning("No nodes available for workflow setup")
                return None
            
            workflow = create_chat_workflow(self.nodes)
            
            logger.info("Workflow setup completed")
            return workflow
            
        except Exception as e:
            logger.error("Workflow setup failed", error=str(e))
            return None
    
    def _convert_to_response(self, state: ConversationState) -> ConversationResponse:
        """
        Convert internal state to ConversationResponse.
        
        Args:
            state: Final conversation state
            
        Returns:
            ConversationResponse for external use
        """
        # Map intent to QueryType
        intent_mapping = {
            IntentType.QUESTION.value: QueryType.DOCUMENT_QA,
            IntentType.COMPLAINT.value: QueryType.COMPLAINT_SUBMISSION,
            IntentType.GENERAL.value: QueryType.GENERAL_INFO
        }
        
        intent = state.get('intent', IntentType.GENERAL.value)
        query_type = intent_mapping.get(intent, QueryType.GENERAL_INFO)
        
        # Get response text
        response_text = state.get('response') or "Lo siento, no pude procesar tu mensaje."
        
        # Get sources and confidence
        sources = state.get('sources', [])
        confidence = state.get('confidence', 0.5)
        
        # Get suggested actions
        suggested_actions = state.get('suggested_actions', [])
        
        # Get tool result for structured data
        tool_result = state.get('tool_result', {})
        structured_data = tool_result if tool_result else None
        
        # Check if followup is needed (low confidence or error)
        requires_followup = confidence < 0.5 or bool(state.get('error_info'))
        
        # Create metadata
        metadata = {
            'engine': 'ModularLangGraphEngine',
            'intent': intent,
            'tool_type': state.get('tool_type'),
            'tool_success': state.get('tool_success'),
            'processing_step': state.get('processing_step'),
            **state.get('metadata', {})
        }
        
        return ConversationResponse(
            response_text=response_text,
            query_type=query_type,
            sources=sources,
            confidence_score=confidence,
            structured_data=structured_data,
            suggested_actions=suggested_actions,
            requires_followup=requires_followup,
            metadata=metadata
        )
    
    def _create_fallback_response(self, user_message: str, error: str) -> ConversationResponse:
        """
        Create fallback response when processing fails.
        
        Args:
            user_message: Original user message
            error: Error that occurred
            
        Returns:
            Fallback ConversationResponse
        """
        return ConversationResponse(
            response_text="Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?",
            query_type=QueryType.GENERAL_INFO,
            sources=[],
            confidence_score=0.1,
            structured_data=None,
            suggested_actions=[
                "Intenta reformular tu pregunta",
                "Contacta soporte si el problema persiste"
            ],
            requires_followup=True,
            metadata={
                'engine': 'ModularLangGraphEngine',
                'error': error,
                'fallback': True,
                'original_message': user_message[:100]
            }
        )
    
    def _update_metrics(self, processing_time: float, success: bool):
        """Update internal metrics."""
        self._conversation_count += 1
        self._total_processing_time += processing_time
        
        if self._conversation_count % 100 == 0:  # Log every 100 conversations
            logger.info("Engine metrics update",
                       conversation_count=self._conversation_count,
                       avg_processing_time=self._total_processing_time / self._conversation_count,
                       success=success)
    
    def _get_metrics(self) -> Dict[str, Any]:
        """Get current engine metrics."""
        return {
            'conversation_count': self._conversation_count,
            'total_processing_time': self._total_processing_time,
            'average_processing_time': (
                self._total_processing_time / self._conversation_count 
                if self._conversation_count > 0 else 0.0
            ),
            'tools_available': list(self.tools.keys()),
            'nodes_available': list(self.nodes.keys()),
            'workflow_available': self.workflow is not None
        }