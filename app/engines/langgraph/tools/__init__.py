# =======================
# app/engines/langgraph/tools/__init__.py
# =======================
"""
Tool wrappers for integrating existing services with LangGraph workflows.

This module provides standardized tool interfaces that wrap existing services
(DocumentService, ComplaintService, LLMProvider) for use in LangGraph workflows.
All tools return standardized ToolResult objects for consistent error handling
and data flow.
"""

from .base_tool import BaseTool, ToolExecutionError
from .document_tool import DocumentTool
from .complaint_tool import ComplaintTool
from .llm_tool import LLMTool

__all__ = [
    # Base interfaces
    'BaseTool',
    'ToolExecutionError',
    
    # Service-specific tools
    'DocumentTool',
    'ComplaintTool', 
    'LLMTool'
]

# Tool module metadata
TOOLS_INFO = {
    "base_tool": "Abstract base class and error handling for all tools",
    "document_tool": "Wraps DocumentService for document search and retrieval",
    "complaint_tool": "Wraps ComplaintService for complaint submission and processing",
    "llm_tool": "Wraps LLMProvider for intent classification and text generation"
}


def get_tools_info() -> dict:
    """Get information about available tools."""
    return TOOLS_INFO.copy()


def create_tool_registry(
    document_service=None,
    complaint_service=None,
    llm_provider=None
) -> dict:
    """
    Create a registry of all available tools.
    
    Args:
        document_service: DocumentService instance
        complaint_service: ComplaintService instance  
        llm_provider: LLMProvider instance
        
    Returns:
        Dictionary mapping tool names to tool instances
    """
    registry = {}
    
    if document_service:
        registry['document'] = DocumentTool(document_service)
    
    if complaint_service:
        registry['complaint'] = ComplaintTool(complaint_service)
        
    if llm_provider:
        registry['llm'] = LLMTool(llm_provider)
    
    return registry