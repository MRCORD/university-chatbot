# =======================
# app/models/user.py
# =======================
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import EmailStr, Field

from app.models.base import BaseEntity, BaseRequest, BaseResponse


class UserType(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"
    STAFF = "staff"
    GUEST = "guest"


# Request Models
class UserCreateRequest(BaseRequest):
    """Request to create a user."""
    email: EmailStr
    student_id: Optional[str] = None
    faculty: Optional[str] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=7)
    user_type: UserType = Field(default=UserType.STUDENT)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserUpdateRequest(BaseRequest):
    """Request to update a user."""
    faculty: Optional[str] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=7)
    preferences: Optional[Dict[str, Any]] = None


# Response Models
class UserResponse(BaseResponse):
    """User response."""
    id: str
    email: EmailStr
    student_id: Optional[str]
    faculty: Optional[str]
    year_of_study: Optional[int]
    user_type: UserType
    preferences: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    created_at: datetime

