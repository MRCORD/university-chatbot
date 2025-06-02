# =======================
# app/models/common.py
# =======================
from typing import List, Optional, Dict, Any, Generic, TypeVar
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.base import BaseResponse, PaginationResponse


# Generic type for paginated responses
T = TypeVar('T')


class Status(str, Enum):
    """General status enum for various operations."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels for various entities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class Faculty(str, Enum):
    """University faculties."""
    ENGINEERING = "engineering"
    MEDICINE = "medicine"
    LAW = "law"
    BUSINESS = "business"
    ARTS = "arts"
    SCIENCE = "science"
    EDUCATION = "education"
    SOCIAL_SCIENCES = "social_sciences"
    ARCHITECTURE = "architecture"
    PHARMACY = "pharmacy"


class AcademicYear(str, Enum):
    """Academic years."""
    YEAR_2023_2024 = "2023-2024"
    YEAR_2024_2025 = "2024-2025"
    YEAR_2025_2026 = "2025-2026"
    YEAR_2026_2027 = "2026-2027"


class Semester(str, Enum):
    """Academic semesters."""
    FALL = "fall"
    SPRING = "spring"
    SUMMER = "summer"


# Common Response Models
class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseResponse):
    """Standard error response."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseResponse):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseResponse, Generic[T]):
    """Generic paginated response."""
    data: List[T]
    pagination: PaginationResponse
    total_count: int


class HealthCheckResponse(BaseResponse):
    """Health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    uptime: Optional[float] = None
    dependencies: Dict[str, str] = Field(default_factory=dict)


# Common Search and Filter Models
class SearchFilter(BaseModel):
    """Base search filter."""
    query: Optional[str] = Field(None, description="Search query")
    faculty: Optional[Faculty] = Field(None, description="Filter by faculty")
    academic_year: Optional[AcademicYear] = Field(None, description="Filter by academic year")
    status: Optional[Status] = Field(None, description="Filter by status")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class SortBy(BaseModel):
    """Sorting configuration."""
    field: str = Field(..., description="Field to sort by")
    order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")


# Common Metadata Models
class AuditInfo(BaseModel):
    """Audit information for tracking changes."""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    version: int = Field(default=1, description="Entity version for optimistic locking")


class ContactInfo(BaseModel):
    """Contact information model."""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    office_hours: Optional[str] = None


class FileInfo(BaseModel):
    """File information model."""
    filename: str
    content_type: str
    size: int
    checksum: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)


# Notification and Communication Models
class NotificationType(str, Enum):
    """Types of notifications."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"


class Notification(BaseModel):
    """Notification model."""
    title: str
    message: str
    type: NotificationType
    channel: NotificationChannel
    recipient: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None


# API Response Wrappers
class APIResponse(BaseResponse):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorResponse] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def success_response(cls, data: Any = None, message: str = "Success", meta: Dict[str, Any] = None):
        """Create a success response."""
        return cls(
            success=True,
            data=data,
            meta=meta or {"message": message}
        )

    @classmethod
    def error_response(cls, message: str, code: str = "ERROR", details: List[ErrorDetail] = None):
        """Create an error response."""
        return cls(
            success=False,
            error=ErrorResponse(
                error=code,
                message=message,
                details=details
            )
        )


# Configuration Models
class SystemSettings(BaseModel):
    """System configuration settings."""
    maintenance_mode: bool = False
    max_file_size: int = Field(default=10485760, description="Max file size in bytes (10MB)")
    supported_file_types: List[str] = Field(
        default_factory=lambda: ["pdf", "doc", "docx", "txt", "md"]
    )
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    rate_limit: Dict[str, int] = Field(
        default_factory=lambda: {"requests_per_minute": 60, "requests_per_hour": 1000}
    )