# =======================
# app/repositories/conversation_repository.py
# =======================
from typing import List, Dict, Any
from app.repositories.base import BaseRepository
from app.interfaces.database_provider import DatabaseProvider


class ConversationRepository(BaseRepository):
    """Conversation repository for conversation-related database operations."""
    
    def __init__(self, db_provider: DatabaseProvider):
        super().__init__(db_provider, 'conversations')
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get conversations for a user."""
        return await self.find(
            {'user_id': user_id},
            limit=limit,
            offset=offset,
            order_by='-created_at'
        )


