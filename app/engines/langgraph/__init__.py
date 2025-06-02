# =======================
# app/engines/langgraph/__init__.py
# =======================
"""
LangGraph modular conversation engine implementation.

This module provides a modular, maintainable LangGraph-based conversation engine
for the Universidad del Pacífico chatbot. It integrates with existing services
through a clean tool-based architecture.
"""

from .engine import ModularLangGraphEngine

__version__ = "1.0.0"
__all__ = ['ModularLangGraphEngine']

# Module metadata
MODULE_INFO = {
    "name": "LangGraph Conversation Engine",
    "version": __version__,
    "description": "Modular LangGraph implementation for UP chatbot",
    "components": [
        "state - State management and schemas",
        "tools - Service integration wrappers", 
        "nodes - Individual workflow components",
        "workflows - Workflow orchestration",
        "utils - Cross-cutting utilities"
    ]
}


def get_module_info() -> dict:
    """Get information about this LangGraph module."""
    return MODULE_INFO.copy()