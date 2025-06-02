# =======================
# app/models/base.py
# =======================
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class BaseEntity(BaseModel):
    """Base model for all entities."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BaseRequest(BaseModel):
    """Base model for API requests."""
    
    class Config:
        str_strip_whitespace = True


class BaseResponse(BaseModel):
    """Base model for API responses."""
    
    class Config:
        from_attributes = True


class PaginationRequest(BaseModel):
    """Pagination request parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginationResponse(BaseModel):
    """Pagination response metadata."""
    page: int
    limit: int
    total: int
    total_pages: int

