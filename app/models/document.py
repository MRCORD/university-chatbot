# =======================
# app/models/document.py
# =======================
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field
from datetime import datetime

from app.models.base import BaseEntity, BaseRequest, BaseResponse


class DocumentType(str, Enum):
    ACADEMIC_REGULATIONS = "academic_regulations"
    PROCEDURES = "procedures"
    DEADLINES_CALENDAR = "deadlines_calendar"
    ADMINISTRATIVE_RULES = "administrative_rules"
    FACULTY_SPECIFIC = "faculty_specific"
    GENERAL_INFORMATION = "general_information"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REPROCESSING = "reprocessing"


# Request Models
class DocumentUploadRequest(BaseRequest):
    """Request to upload a document."""
    document_type: DocumentType
    faculty: Optional[str] = None
    academic_year: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentSearchRequest(BaseRequest):
    """Request to search documents."""
    query: str = Field(..., min_length=1, max_length=500)
    document_type: Optional[DocumentType] = None
    faculty: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


# Response Models
class DocumentResponse(BaseResponse):
    """Document response."""
    id: str
    filename: str
    original_filename: str
    document_type: DocumentType
    storage_url: Optional[str]
    file_size_bytes: Optional[int]
    faculty: Optional[str]
    academic_year: Optional[str]
    processing_status: ProcessingStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime  # Changed from created_at to match database schema


class DocumentChunkResponse(BaseResponse):
    """Document chunk response."""
    id: str
    content: str
    page_number: Optional[int]
    section_title: Optional[str]
    similarity_score: float = Field(default=0.0)
    document: DocumentResponse


class DocumentSearchResponse(BaseResponse):
    """Document search results."""
    query: str
    chunks: List[DocumentChunkResponse]
    total_found: int

