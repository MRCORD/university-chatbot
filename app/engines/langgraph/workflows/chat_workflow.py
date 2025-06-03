# =======================
# app/engines/langgraph/workflows/chat_workflow.py
# =======================
"""
Main chat workflow for LangGraph conversation processing.

Simple workflow that connects classification, execution, and formatting nodes.
Follows KISS principle - clear routing, no complex logic.
"""

import structlog

from app.engines.langgraph.workflows.base_workflow import BaseWorkflow, StateGraph, LANGGRAPH_AVAILABLE
from app.engines.langgraph.state.conversation_state import ConversationState
from app.engines.langgraph.state.schemas import IntentType

logger = structlog.get_logger()


class ChatWorkflow(BaseWorkflow):
    """
    Main conversation workflow.
    
    Simple flow:
    1. Classify user intent 
    2. Route to appropriate handler (document/complaint/general)
    3. Format conversational response
    
    That's it. KISS.
    """
    
    def build_workflow(self):
        """
        Build the simple chat workflow.
        
        Flow: START → classify → route → execute → format → END
        
        Returns:
            Compiled LangGraph workflow or fallback handler
        """
        if not LANGGRAPH_AVAILABLE:
            logger.info("Building fallback workflow (LangGraph not available)")
            return self._build_fallback_workflow()
        
        logger.info("Building LangGraph workflow")
        
        # Create workflow graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("document_search", self._document_search_node)
        workflow.add_node("complaint_processing", self._complaint_processing_node)
        workflow.add_node("general_chat", self._general_chat_node)
        workflow.add_node("format_response", self._format_response_node)
        
        # Define the flow
        workflow.set_entry_point("classify")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "classify",
            self._route_by_intent,
            {
                "document_search": "document_search",
                "complaint_processing": "complaint_processing", 
                "general_chat": "general_chat"
            }
        )
        
        # All execution paths lead to formatting
        workflow.add_edge("document_search", "format_response")
        workflow.add_edge("complaint_processing", "format_response")
        workflow.add_edge("general_chat", "format_response")
        
        # End after formatting
        workflow.set_finish_point("format_response")
        
        return workflow.compile()
    
    def _route_by_intent(self, state: ConversationState) -> str:
        """
        Simple routing based on classified intent.
        
        Args:
            state: Current conversation state with classified intent
            
        Returns:
            Next node name to execute
        """
        intent = state.get('intent', IntentType.GENERAL.value)
        
        if intent == IntentType.QUESTION.value:
            return "document_search"
        elif intent == IntentType.COMPLAINT.value:
            return "complaint_processing"
        else:
            return "general_chat"
    
    # Node wrapper functions for LangGraph
    async def _classify_node(self, state: ConversationState) -> ConversationState:
        """Wrapper for classification node."""
        return await self.nodes['classification'].execute(state)
    
    async def _document_search_node(self, state: ConversationState) -> ConversationState:
        """Wrapper for document search node."""
        return await self.nodes['document_search'].execute(state)
    
    async def _complaint_processing_node(self, state: ConversationState) -> ConversationState:
        """Wrapper for complaint processing node."""
        return await self.nodes['complaint_processing'].execute(state)
    
    async def _general_chat_node(self, state: ConversationState) -> ConversationState:
        """Wrapper for general chat using LLM tool."""
        try:
            # Get LLM tool for general chat
            llm_tool = None
            for node in self.nodes.values():
                if hasattr(node, 'tools') and 'llm' in node.tools:
                    llm_tool = node.tools['llm']
                    break
            
            if llm_tool:
                # Generate UP-specific response
                chat_result = await llm_tool.generate_up_response(
                    user_message=state.get('user_message', ''),
                    context={'conversation_history': state.get('conversation_history', [])}
                )
                
                # Update state with chat result
                from app.engines.langgraph.state.conversation_state import StateManager
                StateManager.update_tool_result(
                    state,
                    tool_type="llm",
                    tool_result={
                        'type': 'general_chat',
                        'response': chat_result.data.get('response', 'Hola! ¿En qué puedo ayudarte?')
                    },
                    success=chat_result.success
                )
            else:
                # Fallback if no LLM tool available
                from app.engines.langgraph.state.conversation_state import StateManager
                StateManager.update_tool_result(
                    state,
                    tool_type="llm",
                    tool_result={
                        'type': 'general_chat',
                        'response': '¡Hola! Soy el asistente de UP. ¿En qué puedo ayudarte?'
                    },
                    success=True
                )
            
            return state
            
        except Exception as e:
            logger.error("General chat processing failed", error=str(e))
            
            # Fallback response
            from app.engines.langgraph.state.conversation_state import StateManager
            StateManager.update_tool_result(
                state,
                tool_type="llm",
                tool_result={
                    'type': 'general_chat',
                    'response': 'Hola! ¿En qué puedo ayudarte hoy?'
                },
                success=True
            )
            return state
    
    async def _format_response_node(self, state: ConversationState) -> ConversationState:
        """Wrapper for response formatting node."""
        return await self.nodes['response_formatting'].execute(state)
    
    def _build_fallback_workflow(self):
        """
        Build simple fallback workflow when LangGraph is not available.
        
        Returns:
            Simple workflow object that mimics LangGraph interface
        """
        class FallbackWorkflow:
            def __init__(self, chat_workflow):
                self.chat_workflow = chat_workflow
            
            async def ainvoke(self, state: ConversationState) -> ConversationState:
                return await self.chat_workflow._fallback_execution(state)
        
        return FallbackWorkflow(self)
    
    async def _fallback_execution(self, state: ConversationState) -> ConversationState:
        """
        Simple fallback execution when LangGraph is not available.
        
        Manually executes the workflow steps in sequence.
        
        Args:
            state: Initial conversation state
            
        Returns:
            Final state after manual execution
        """
        try:
            logger.info("Executing fallback workflow", user_id=state.get('user_id'))
            
            # Step 1: Classify intent
            state = await self.nodes['classification'].execute(state)
            
            # Step 2: Route and execute based on intent
            intent = state.get('intent', IntentType.GENERAL.value)
            
            if intent == IntentType.QUESTION.value:
                state = await self.nodes['document_search'].execute(state)
            elif intent == IntentType.COMPLAINT.value:
                state = await self.nodes['complaint_processing'].execute(state)
            else:
                state = await self._general_chat_node(state)
            
            # Step 3: Format response
            state = await self.nodes['response_formatting'].execute(state)
            
            logger.info("Fallback workflow completed", 
                       user_id=state.get('user_id'),
                       intent=intent,
                       success=bool(state.get('response')))
            
            return state
            
        except Exception as e:
            logger.error("Fallback workflow failed", 
                        user_id=state.get('user_id'),
                        error=str(e))
            
            # Ultimate fallback - return simple error response
            from app.engines.langgraph.state.conversation_state import StateManager
            StateManager.update_response(
                state,
                response="Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?",
                confidence=0.1,
                suggested_actions=["Intenta reformular tu pregunta"]
            )
            StateManager.add_error(state, "workflow_error", str(e))
            
            return state
    
    def get_workflow_info(self) -> dict:
        """
        Get information about this workflow.
        
        Returns:
            Dictionary with workflow details
        """
        return {
            'workflow_name': self.workflow_name,
            'langgraph_available': LANGGRAPH_AVAILABLE,
            'nodes': list(self.nodes.keys()),
            'flow': [
                'classify (intent classification)',
                'route (by intent)',
                'execute (document_search | complaint_processing | general_chat)',
                'format_response (final response)'
            ],
            'supported_intents': [intent.value for intent in IntentType],
            'execution_mode': 'langgraph' if LANGGRAPH_AVAILABLE else 'fallback'
        }