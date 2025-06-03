# =======================
# app/engines/langgraph/workflows/__init__.py
# =======================
"""
Workflow orchestration for LangGraph conversation processing.

Simple workflow definitions that connect nodes with clean routing logic.
Follows KISS principle - minimal abstractions, maximum clarity.
"""

from .base_workflow import BaseWorkflow
from .chat_workflow import ChatWorkflow

__all__ = [
    'BaseWorkflow',
    'ChatWorkflow'
]

# Simple workflow registry
def create_chat_workflow(nodes: dict) -> ChatWorkflow:
    """
    Create the main chat workflow with node dependencies.
    
    Args:
        nodes: Dictionary of node instances
        
    Returns:
        Configured ChatWorkflow instance
    """
    return ChatWorkflow(nodes)