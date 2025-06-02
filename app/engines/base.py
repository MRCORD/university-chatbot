# =======================
# app/engines/base.py
# =======================
from typing import List, Dict, Any
import structlog

from app.interfaces.conversation_engine import (
    ConversationEngine, ConversationContext, ConversationResponse, QueryType
)

logger = structlog.get_logger()


class MockConversationEngine(ConversationEngine):
    """Mock conversation engine for testing."""
    
    async def process_query(
        self,
        user_message: str,
        context: ConversationContext
    ) -> ConversationResponse:
        """Process query with mock response."""
        return ConversationResponse(
            response_text=f"Mock response to: {user_message}",
            query_type=QueryType.GENERAL_INFO,
            sources=["mock_source"],
            confidence_score=0.8,
            structured_data=None,
            suggested_actions=["Ask another question"],
            requires_followup=False,
            metadata={"engine": "mock"}
        )
    
    async def initialize_documents(self, document_paths: List[str]) -> bool:
        """Mock document initialization."""
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {"status": "healthy", "engine": "mock"}