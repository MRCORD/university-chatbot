# =======================
# app/repositories/base.py
# =======================
from typing import Optional, List, Dict, Any, Union, Generic, TypeVar
from uuid import UUID
import structlog

from app.interfaces.database_provider import DatabaseProvider
from app.core.exceptions import NotFoundException

logger = structlog.get_logger()

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common database operations."""
    
    def __init__(self, db_provider: DatabaseProvider, table_name: str):
        self.db = db_provider
        self.table_name = table_name
    
    async def get_by_id(self, record_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get record by ID."""
        try:
            return await self.db.get_by_id(self.table_name, record_id)
        except Exception as e:
            logger.error(f"Error getting {self.table_name} by ID", record_id=str(record_id), error=str(e))
            raise
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new record."""
        try:
            return await self.db.create(self.table_name, data)
        except Exception as e:
            logger.error(f"Error creating {self.table_name}", data=data, error=str(e))
            raise
    
    async def update(self, record_id: Union[str, UUID], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing record."""
        try:
            result = await self.db.update(self.table_name, record_id, updates)
            if not result:
                raise NotFoundException(f"{self.table_name.title()} not found")
            return result
        except Exception as e:
            logger.error(f"Error updating {self.table_name}", record_id=str(record_id), error=str(e))
            raise
    
    async def delete(self, record_id: Union[str, UUID]) -> bool:
        """Delete record."""
        try:
            return await self.db.delete(self.table_name, record_id)
        except Exception as e:
            logger.error(f"Error deleting {self.table_name}", record_id=str(record_id), error=str(e))
            raise
    
    async def find(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find records with filters."""
        try:
            return await self.db.find(
                self.table_name, 
                filters, 
                limit=limit, 
                offset=offset, 
                order_by=order_by
            )
        except Exception as e:
            logger.error(f"Error finding {self.table_name}", filters=filters, error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check repository health."""
        return await self.db.health_check()


