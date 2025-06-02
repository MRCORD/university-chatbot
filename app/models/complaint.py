# =======================
# app/models/complaint.py
# =======================
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field

from app.models.base import BaseEntity, BaseRequest, BaseResponse


class ComplaintCategory(str, Enum):
    ADMINISTRATIVE = "administrative"
    ACADEMIC = "academic"
    INFRASTRUCTURE = "infrastructure"
    TECHNOLOGY = "technology"
    SERVICES = "services"
    FINANCIAL = "financial"
    OTHER = "other"


class ComplaintPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ComplaintStatus(str, Enum):
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class UrgencyLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# Request Models
class ComplaintSubmissionRequest(BaseRequest):
    """Request to submit a complaint."""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: ComplaintCategory
    is_anonymous: bool = Field(default=False)
    user_id: Optional[str] = Field(None, description="Required if not anonymous")
    conversation_id: Optional[str] = Field(None, description="Associated conversation")


# Response Models
class ComplaintResponse(BaseResponse):
    """Complaint response."""
    id: str
    title: str
    description: str
    category: ComplaintCategory
    priority: ComplaintPriority
    status: ComplaintStatus
    urgency_level: UrgencyLevel
    affected_service: Optional[str]
    suggested_department: Optional[str]
    ai_generated_tags: List[str] = Field(default_factory=list)
    upvotes: int = Field(default=0)
    view_count: int = Field(default=0)
    is_anonymous: bool
    similar_complaint_ids: List[str] = Field(default_factory=list)
    resolved_at: Optional[datetime]
    created_at: datetime


class ComplaintListResponse(BaseResponse):
    """List of complaints response."""
    complaints: List[ComplaintResponse]
    total: int

