# =======================
# app/engines/langgraph/nodes/classification.py
# =======================
"""
Intent classification node for LangGraph workflows.

Simple node that classifies user intent using LLMTool.
Follows KISS principle - one job, do it well.
"""

import structlog

from app.engines.langgraph.nodes.base_node import BaseNode
from app.engines.langgraph.state.conversation_state import ConversationState, StateManager
from app.engines.langgraph.state.schemas import IntentType

logger = structlog.get_logger()


class ClassificationNode(BaseNode):
    """
    Classifies user intent from message.
    
    Simple responsibility:
    1. Take user message
    2. Call LLMTool to classify intent
    3. Update state with intent and confidence
    
    That's it. KISS.
    """
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """
        Classify user intent and update state.
        
        Args:
            state: Current conversation state
            
        Returns:
            State updated with intent and confidence
        """
        self._log_start(state)
        
        try:
            # Get user message
            user_message = state.get('user_message', '')
            conversation_history = state.get('conversation_history', [])
            
            if not user_message:
                # No message to classify - default to general
                StateManager.update_intent(state, IntentType.GENERAL.value, 0.5)
                self._log_complete(state)
                return state
            
            # Get LLM tool
            llm_tool = self.tools.get('llm')
            if not llm_tool:
                # No LLM tool - fallback to simple classification
                intent = self._simple_fallback_classification(user_message)
                StateManager.update_intent(state, intent.value, 0.3)
                self._log_complete(state)
                return state
            
            # Call LLM tool for classification
            classification_result = await llm_tool.classify_intent(
                user_message=user_message,
                conversation_history=conversation_history
            )
            
            # Update state with classification result
            StateManager.update_intent(
                state, 
                classification_result.intent.value,
                classification_result.confidence
            )
            
            # Add classification metadata
            state['metadata']['classification'] = {
                'model_used': classification_result.model_used,
                'reasoning': classification_result.reasoning
            }
            
            self._log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Classification failed: {str(e)}"
            self._log_error(state, error_msg)
            
            # Fallback classification on error
            intent = self._simple_fallback_classification(state.get('user_message', ''))
            StateManager.update_intent(state, intent.value, 0.2)
            StateManager.add_error(state, "classification_error", error_msg)
            
            return state
    
    def _simple_fallback_classification(self, message: str) -> IntentType:
        """
        Simple keyword-based classification fallback.
        
        Args:
            message: User message
            
        Returns:
            IntentType based on simple keywords
        """
        if not message:
            return IntentType.GENERAL
        
        message_lower = message.lower()
        
        # Simple question patterns
        question_words = ['cómo', 'cuándo', 'dónde', 'qué', 'quién', 'por qué']
        if any(word in message_lower for word in question_words):
            return IntentType.QUESTION
        
        # Simple complaint patterns  
        complaint_words = ['problema', 'issue', 'error', 'no funciona', 'mal']
        if any(word in message_lower for word in complaint_words):
            return IntentType.COMPLAINT
        
        # Default to general conversation
        return IntentType.GENERAL