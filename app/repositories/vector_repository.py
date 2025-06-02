# =======================
# app/repositories/vector_repository.py
# =======================
from typing import List, Dict, Any, Optional
from app.repositories.base import BaseRepository
from app.interfaces.database_provider import DatabaseProvider


class VectorRepository(BaseRepository):
    """Vector repository for vector search operations."""
    
    def __init__(self, db_provider: DatabaseProvider):
        super().__init__(db_provider, 'document_chunks')
    
    async def vector_search(
        self,
        query_vector: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 10,
        document_type: Optional[str] = None,
        faculty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        filters = {}
        if document_type:
            filters['document_type'] = document_type
        if faculty:
            filters['faculty'] = faculty
        
        return await self.db.vector_search(
            query_vector=query_vector,
            similarity_threshold=similarity_threshold,
            limit=limit,
            filters=filters
        )