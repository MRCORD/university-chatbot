# =======================
# app/repositories/document_repository.py
# =======================
from typing import List, Dict, Any, Optional
from app.repositories.base import BaseRepository
from app.interfaces.database_provider import DatabaseProvider


class DocumentRepository(BaseRepository):
    """Document repository for document-related database operations."""
    
    def __init__(self, db_provider: DatabaseProvider):
        super().__init__(db_provider, 'documents')
    
    async def get_by_type(
        self, 
        document_type: str, 
        faculty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get documents by type and optionally faculty."""
        filters = {'document_type': document_type, 'is_active': True}
        if faculty:
            filters['faculty'] = faculty
        return await self.find(filters)
    
    async def get_pending_processing(self) -> List[Dict[str, Any]]:
        """Get documents pending processing."""
        return await self.find({'processing_status': 'pending'})


