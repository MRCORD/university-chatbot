# =======================
# app/engines/langgraph/state/__init__.py
# =======================
"""
State management module for LangGraph conversation workflows.

This module provides state models, schemas, and utilities for managing
conversation state throughout the LangGraph workflow execution.
"""

from .conversation_state import ConversationState, StateManager
from .schemas import (
    IntentClassificationResult, 
    ToolResult, 
    DocumentSearchResult,
    ComplaintSubmissionResult,
    GeneralChatResult
)

__all__ = [
    # Core state management
    'ConversationState',
    'StateManager',
    
    # Result schemas
    'IntentClassificationResult',
    'ToolResult',
    'DocumentSearchResult', 
    'ComplaintSubmissionResult',
    'GeneralChatResult'
]

# State module metadata
STATE_INFO = {
    "conversation_state": "Core TypedDict state model for workflow",
    "state_manager": "Utilities for state manipulation and validation",
    "schemas": "Pydantic models for type-safe data validation"
}


def get_state_info() -> dict:
    """Get information about state management components."""
    return STATE_INFO.copy()