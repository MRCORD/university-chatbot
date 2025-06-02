# =======================
# app/services/user_service.py
# =======================
from typing import Optional
import structlog

from app.repositories.user_repository import UserRepository
from app.models.user import UserCreateRequest, UserResponse, UserType
from app.core.exceptions import AppException

logger = structlog.get_logger()


class UserService:
    """Service for user management."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def create_user(self, request: UserCreateRequest) -> UserResponse:
        """Create a new user."""
        try:
            # Check if user already exists
            existing = await self.user_repo.get_by_email(request.email)
            if existing:
                raise AppException("User already exists with this email", status_code=400)
            
            user_data = {
                'email': request.email,
                'student_id': request.student_id,
                'faculty': request.faculty,
                'year_of_study': request.year_of_study,
                'user_type': request.user_type.value,
                'preferences': request.preferences,
                'is_active': True
            }
            
            user = await self.user_repo.create(user_data)
            
            return UserResponse(
                id=user['id'],
                email=user['email'],
                student_id=user.get('student_id'),
                faculty=user.get('faculty'),
                year_of_study=user.get('year_of_study'),
                user_type=UserType(user['user_type']),
                preferences=user.get('preferences', {}),
                is_active=user['is_active'],
                created_at=user['created_at']
            )
            
        except Exception as e:
            logger.error("Error creating user", email=request.email, error=str(e))
            raise AppException(f"Failed to create user: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return None
            
            return UserResponse(
                id=user['id'],
                email=user['email'],
                student_id=user.get('student_id'),
                faculty=user.get('faculty'),
                year_of_study=user.get('year_of_study'),
                user_type=UserType(user['user_type']),
                preferences=user.get('preferences', {}),
                is_active=user['is_active'],
                created_at=user['created_at']
            )
            
        except Exception as e:
            logger.error("Error getting user", user_id=user_id, error=str(e))
            raise AppException(f"Failed to get user: {str(e)}")


