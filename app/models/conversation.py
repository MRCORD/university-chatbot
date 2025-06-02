# =======================
# app/models/conversation.py
# =======================
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field

from app.models.base import BaseEntity, BaseRequest, BaseResponse


class ConversationType(str, Enum):
    DOCUMENT_QA = "document_qa"
    COMPLAINT_SUBMISSION = "complaint_submission"
    PROCEDURE_HELP = "procedure_help"
    GENERAL = "general"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    STRUCTURED_DATA = "structured_data"
    ERROR = "error"


# Request Models
class ChatRequest(BaseRequest):
    """Request to send a chat message."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    user_id: str = Field(..., description="User ID")
    conversation_type: Optional[ConversationType] = Field(None, description="Type of conversation")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


# Response Models
class MessageResponse(BaseResponse):
    """Chat message response."""
    id: str
    role: MessageRole
    content: str
    message_type: MessageType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationResponse(BaseResponse):
    """Conversation with messages response."""
    id: str
    title: Optional[str]
    conversation_type: ConversationType
    status: ConversationStatus
    engine_used: str
    messages: List[MessageResponse]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime]


class ChatResponse(BaseResponse):
    """Response to a chat message."""
    conversation_id: str
    message: MessageResponse
    sources: List[str] = Field(default_factory=list, description="Document sources used")
    confidence_score: float = Field(default=0.0, description="Response confidence")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested next actions")


class ConversationListResponse(BaseResponse):
    """List of conversations response."""
    conversations: List[ConversationResponse]

