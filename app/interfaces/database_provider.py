# =======================
# app/interfaces/database_provider.py
# =======================
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from uuid import UUID


class DatabaseProvider(ABC):
    """Abstract interface for database operations."""
    
    @abstractmethod
    async def get_by_id(self, table: str, record_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get single record by ID."""
        pass
    
    @abstractmethod
    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new record."""
        pass
    
    @abstractmethod
    async def update(
        self, 
        table: str, 
        record_id: Union[str, UUID], 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing record."""
        pass
    
    @abstractmethod
    async def delete(self, table: str, record_id: Union[str, UUID]) -> bool:
        """Delete record."""
        pass
    
    @abstractmethod
    async def find(
        self, 
        table: str, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find records with filters."""
        pass
    
    @abstractmethod
    async def vector_search(
        self,
        query_vector: List[float],
        table: str = "document_chunks",
        similarity_threshold: float = 0.7,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check database connectivity."""
        pass


