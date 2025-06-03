# =======================
# app/engines/langgraph/nodes/base_node.py
# =======================
"""
Base node interface for LangGraph workflow nodes.

Simple base class that defines the common interface for all workflow nodes.
Follows KISS principle - minimal interface, maximum clarity.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import structlog

from app.engines.langgraph.state.conversation_state import ConversationState
from app.engines.langgraph.tools.base_tool import BaseTool

logger = structlog.get_logger()


class BaseNode(ABC):
    """
    Simple base class for all workflow nodes.
    
    Design Principle: KISS
    - Nodes orchestrate, tools do the work
    - Each node has ONE responsibility  
    - Simple, focused interface
    """
    
    def __init__(self, tools: Dict[str, BaseTool]):
        """
        Initialize node with tool dependencies.
        
        Args:
            tools: Dictionary of available tools
        """
        self.tools = tools
        self.node_name = self.__class__.__name__
    
    @abstractmethod
    async def execute(self, state: ConversationState) -> ConversationState:
        """
        Execute the node's responsibility.
        
        This is the main method that each node implements.
        It should:
        1. Take current state
        2. Do ONE specific thing (using tools)
        3. Update and return state
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated conversation state
        """
        pass
    
    def _log_start(self, state: ConversationState):
        """Log node execution start."""
        logger.info(f"{self.node_name} started",
                   user_id=state.get('user_id'),
                   processing_step=state.get('processing_step'),
                   message_preview=state.get('user_message', '')[:30])
    
    def _log_complete(self, state: ConversationState, success: bool = True):
        """Log node execution completion."""
        logger.info(f"{self.node_name} completed",
                   user_id=state.get('user_id'),
                   success=success,
                   processing_step=state.get('processing_step'))
    
    def _log_error(self, state: ConversationState, error: str):
        """Log node execution error."""
        logger.error(f"{self.node_name} failed",
                     user_id=state.get('user_id'),
                     error=error,
                     processing_step=state.get('processing_step'))
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.node_name}(tools={list(self.tools.keys())})"