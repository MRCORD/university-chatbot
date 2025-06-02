# =======================
# app/interfaces/conversation_engine.py
# =======================
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.models.conversation import ConversationType


class QueryType(Enum):
    DOCUMENT_QA = "document_qa"
    COMPLAINT_SUBMISSION = "complaint_submission" 
    GENERAL_INFO = "general_info"
    PROCEDURE_HELP = "procedure_help"


@dataclass
class ConversationContext:
    user_id: str
    session_id: str
    query_type: Optional[QueryType]
    conversation_history: List[Dict[str, str]]
    user_metadata: Dict[str, Any]
    current_documents: List[str]


@dataclass
class ConversationResponse:
    response_text: str
    query_type: QueryType
    sources: List[str]
    confidence_score: float
    structured_data: Optional[Dict[str, Any]]
    suggested_actions: List[str]
    requires_followup: bool
    metadata: Dict[str, Any]


class ConversationEngine(ABC):
    """Abstract interface for conversation engines."""
    
    @abstractmethod
    async def process_query(
        self,
        user_message: str,
        context: ConversationContext
    ) -> ConversationResponse:
        """Process user query and return response."""
        pass
    
    @abstractmethod
    async def initialize_documents(self, document_paths: List[str]) -> bool:
        """Initialize engine with document knowledge base."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check engine health and status."""
        pass


