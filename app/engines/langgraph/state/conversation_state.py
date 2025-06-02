# =======================
# app/engines/langgraph/state/conversation_state.py
# =======================
"""
Core conversation state management for LangGraph workflows.

This module defines the state structure that flows through the LangGraph
workflow and provides utilities for state manipulation and validation.
"""

from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
import structlog

logger = structlog.get_logger()


class ConversationState(TypedDict, total=False):
    """
    Core state model for LangGraph conversation workflows.
    
    This TypedDict defines all the data that flows through the workflow nodes.
    Using TypedDict provides type safety while maintaining compatibility with LangGraph.
    """
    
    # Input data
    user_message: str                           # Original user input
    user_id: str                               # User identifier
    conversation_id: Optional[str]             # Conversation session ID
    conversation_history: List[Dict[str, str]] # Previous message context
    
    # Processing state
    intent: Optional[str]                      # Classified intent (pregunta/queja/conversacion)
    intent_confidence: float                   # Confidence in classification (0.0-1.0)
    processing_step: Optional[str]             # Current workflow step
    
    # Tool execution results
    tool_result: Optional[Dict[str, Any]]      # Result from service tool execution
    tool_type: Optional[str]                  # Type of tool used (document/complaint/llm)
    tool_success: bool                        # Whether tool execution succeeded
    
    # Response data
    response: Optional[str]                   # Final formatted response text
    sources: List[str]                        # Document sources for response
    confidence: float                         # Overall response confidence
    suggested_actions: List[str]              # Suggested follow-up actions
    
    # Metadata and debugging
    metadata: Dict[str, Any]                  # Additional context data
    error_info: Optional[Dict[str, Any]]      # Error information if workflow fails
    processing_time: Optional[float]          # Time taken for processing
    timestamp: Optional[datetime]             # When state was last updated


class StateManager:
    """
    Utilities for managing and manipulating conversation state.
    
    This class provides static methods for common state operations,
    ensuring consistent state handling across all workflow nodes.
    """
    
    @staticmethod
    def initialize_state(
        user_message: str, 
        user_id: str,
        conversation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ConversationState:
        """
        Initialize a new conversation state.
        
        Args:
            user_message: The user's input message
            user_id: Unique identifier for the user
            conversation_id: Optional conversation session ID
            conversation_history: Optional previous message context
            
        Returns:
            Initialized ConversationState with default values
        """
        return ConversationState(
            # Input data
            user_message=user_message,
            user_id=user_id,
            conversation_id=conversation_id,
            conversation_history=conversation_history or [],
            
            # Processing state - initialized as None/empty
            intent=None,
            intent_confidence=0.0,
            processing_step="initialized",
            
            # Tool execution - initialized as None/empty
            tool_result=None,
            tool_type=None,
            tool_success=False,
            
            # Response data - initialized as empty
            response=None,
            sources=[],
            confidence=0.0,
            suggested_actions=[],
            
            # Metadata
            metadata={},
            error_info=None,
            processing_time=None,
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def update_intent(
        state: ConversationState, 
        intent: str, 
        confidence: float
    ) -> ConversationState:
        """
        Update state with classified intent.
        
        Args:
            state: Current conversation state
            intent: Classified intent (pregunta/queja/conversacion)
            confidence: Classification confidence (0.0-1.0)
            
        Returns:
            Updated state with intent information
        """
        state['intent'] = intent
        state['intent_confidence'] = confidence
        state['processing_step'] = "intent_classified"
        state['timestamp'] = datetime.utcnow()
        
        logger.info("Intent updated", 
                   intent=intent, 
                   confidence=confidence,
                   user_id=state.get('user_id'))
        
        return state
    
    @staticmethod
    def update_tool_result(
        state: ConversationState,
        tool_type: str,
        tool_result: Dict[str, Any],
        success: bool,
        sources: Optional[List[str]] = None
    ) -> ConversationState:
        """
        Update state with tool execution results.
        
        Args:
            state: Current conversation state
            tool_type: Type of tool executed (document/complaint/llm)
            tool_result: Result data from tool execution
            success: Whether tool execution succeeded
            sources: Optional list of source documents
            
        Returns:
            Updated state with tool results
        """
        state['tool_type'] = tool_type
        state['tool_result'] = tool_result
        state['tool_success'] = success
        state['processing_step'] = f"{tool_type}_executed"
        state['timestamp'] = datetime.utcnow()
        
        if sources:
            state['sources'] = sources
        
        logger.info("Tool result updated",
                   tool_type=tool_type,
                   success=success,
                   sources_count=len(sources) if sources else 0,
                   user_id=state.get('user_id'))
        
        return state
    
    @staticmethod
    def update_response(
        state: ConversationState,
        response: str,
        confidence: float,
        suggested_actions: Optional[List[str]] = None
    ) -> ConversationState:
        """
        Update state with final formatted response.
        
        Args:
            state: Current conversation state
            response: Final response text
            confidence: Response confidence score
            suggested_actions: Optional suggested follow-up actions
            
        Returns:
            Updated state with response information
        """
        state['response'] = response
        state['confidence'] = confidence
        state['processing_step'] = "response_formatted"
        state['timestamp'] = datetime.utcnow()
        
        if suggested_actions:
            state['suggested_actions'] = suggested_actions
        
        logger.info("Response updated",
                   response_length=len(response),
                   confidence=confidence,
                   actions_count=len(suggested_actions) if suggested_actions else 0,
                   user_id=state.get('user_id'))
        
        return state
    
    @staticmethod
    def add_error(
        state: ConversationState,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """
        Add error information to state.
        
        Args:
            state: Current conversation state
            error_type: Type of error (classification/tool/formatting/etc.)
            error_message: Human-readable error message
            error_details: Optional additional error details
            
        Returns:
            Updated state with error information
        """
        state['error_info'] = {
            'type': error_type,
            'message': error_message,
            'details': error_details or {},
            'timestamp': datetime.utcnow().isoformat(),
            'processing_step': state.get('processing_step', 'unknown')
        }
        
        logger.error("Error added to state",
                    error_type=error_type,
                    error_message=error_message,
                    processing_step=state.get('processing_step'),
                    user_id=state.get('user_id'))
        
        return state
    
    @staticmethod
    def validate_state(state: ConversationState) -> bool:
        """
        Validate that state contains required fields.
        
        Args:
            state: Conversation state to validate
            
        Returns:
            True if state is valid, False otherwise
        """
        required_fields = ['user_message', 'user_id']
        
        for field in required_fields:
            if field not in state or state[field] is None:
                logger.warning("State validation failed", 
                             missing_field=field,
                             user_id=state.get('user_id'))
                return False
        
        return True
    
    @staticmethod
    def get_state_summary(state: ConversationState) -> Dict[str, Any]:
        """
        Get a summary of current state for debugging/monitoring.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dictionary with key state information
        """
        return {
            'user_id': state.get('user_id'),
            'message_length': len(state.get('user_message', '')),
            'intent': state.get('intent'),
            'intent_confidence': state.get('intent_confidence'),
            'processing_step': state.get('processing_step'),
            'tool_type': state.get('tool_type'),
            'tool_success': state.get('tool_success'),
            'has_response': bool(state.get('response')),
            'sources_count': len(state.get('sources', [])),
            'confidence': state.get('confidence'),
            'has_error': bool(state.get('error_info')),
            'timestamp': state.get('timestamp')
        }
    
    @staticmethod
    def is_ready_for_response(state: ConversationState) -> bool:
        """
        Check if state is ready for final response generation.
        
        Args:
            state: Current conversation state
            
        Returns:
            True if ready for response, False otherwise
        """
        return (
            state.get('intent') is not None and
            state.get('tool_result') is not None and
            state.get('tool_success', False) is True
        )
    
    @staticmethod
    def reset_processing_state(state: ConversationState) -> ConversationState:
        """
        Reset processing-related state while keeping input data.
        
        Useful for retrying failed workflows.
        
        Args:
            state: Current conversation state
            
        Returns:
            State with processing fields reset
        """
        # Keep input data, reset processing state
        state['intent'] = None
        state['intent_confidence'] = 0.0
        state['processing_step'] = "reset"
        state['tool_result'] = None
        state['tool_type'] = None
        state['tool_success'] = False
        state['response'] = None
        state['sources'] = []
        state['confidence'] = 0.0
        state['suggested_actions'] = []
        state['error_info'] = None
        state['timestamp'] = datetime.utcnow()
        
        logger.info("Processing state reset", 
                   user_id=state.get('user_id'))
        
        return state