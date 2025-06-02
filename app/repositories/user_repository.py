# =======================
# app/repositories/user_repository.py
# =======================
from typing import Optional, Dict, Any
from app.repositories.base import BaseRepository
from app.interfaces.database_provider import DatabaseProvider


class UserRepository(BaseRepository):
    """User repository for user-related database operations."""
    
    def __init__(self, db_provider: DatabaseProvider):
        super().__init__(db_provider, 'users')
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        users = await self.find({'email': email})
        return users[0] if users else None
    
    async def get_by_student_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get user by student ID."""
        users = await self.find({'student_id': student_id})
        return users[0] if users else None


