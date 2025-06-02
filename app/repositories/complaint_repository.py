# =======================
# app/repositories/complaint_repository.py
# =======================
from typing import List, Dict, Any
from app.repositories.base import BaseRepository
from app.interfaces.database_provider import DatabaseProvider


class ComplaintRepository(BaseRepository):
    """Complaint repository for complaint-related database operations."""
    
    def __init__(self, db_provider: DatabaseProvider):
        super().__init__(db_provider, 'complaints')
    
    async def get_public_complaints(
        self, 
        limit: int = 50,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get public complaints for dashboard."""
        filters = {'is_anonymous': False}
        if category:
            filters['category'] = category
        
        return await self.find(
            filters,
            limit=limit,
            order_by='-created_at'
        )


