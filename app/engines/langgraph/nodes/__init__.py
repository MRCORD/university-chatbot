# =======================
# app/engines/langgraph/nodes/__init__.py
# =======================
"""
Workflow nodes for LangGraph conversation processing.

This module provides simple, focused nodes that orchestrate tool calls
for different parts of the conversation workflow. Each node has a single
responsibility and delegates actual work to tools.

Design Principle: KISS - Keep It Simple, Stupid
- Each node does ONE thing
- Nodes orchestrate, tools do the work
- Simple, readable, maintainable code
"""

from .base_node import BaseNode
from .classification import ClassificationNode
from .document_search import DocumentSearchNode
from .complaint_processing import ComplaintProcessingNode
from .response_formatting import ResponseFormattingNode

__all__ = [
    'BaseNode',
    'ClassificationNode',
    'DocumentSearchNode', 
    'ComplaintProcessingNode',
    'ResponseFormattingNode'
]

# Simple node registry for easy setup
def create_node_registry(tools: dict) -> dict:
    """
    Create all nodes with tool dependencies.
    
    Args:
        tools: Dictionary of tool instances
        
    Returns:
        Dictionary mapping node names to node instances
    """
    return {
        'classification': ClassificationNode(tools),
        'document_search': DocumentSearchNode(tools),
        'complaint_processing': ComplaintProcessingNode(tools),
        'response_formatting': ResponseFormattingNode(tools)
    }