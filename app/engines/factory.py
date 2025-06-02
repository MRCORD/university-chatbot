# =======================
# app/engines/factory.py
# =======================
from typing import Dict, Any
import structlog

from app.interfaces.conversation_engine import ConversationEngine
from app.core.config import Settings
from app.core.exceptions import AppException

logger = structlog.get_logger()


class ConversationEngineFactory:
    """Factory for creating conversation engines."""
    
    def __init__(self, settings: Settings, container):
        self.settings = settings
        self.container = container
        self._engines: Dict[str, ConversationEngine] = {}
    
    def get_engine(self, engine_type: str) -> ConversationEngine:
        """Get conversation engine by type."""
        if engine_type not in self._engines:
            self._engines[engine_type] = self._create_engine(engine_type)
        return self._engines[engine_type]
    
    def _create_engine(self, engine_type: str) -> ConversationEngine:
        """Create engine instance."""
        if engine_type == "langgraph":
            # For now, return a simple mock
            # In full implementation, this would create LangGraphEngine
            from app.engines.base import MockConversationEngine
            return MockConversationEngine()
        elif engine_type == "openai":
            # Future implementation
            raise AppException(f"Engine type {engine_type} not implemented yet")
        else:
            raise AppException(f"Unknown engine type: {engine_type}")


