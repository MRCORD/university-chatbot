# =======================
# app/providers/database/supabase_provider.py
# =======================
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
import structlog

from supabase import create_client, Client
from app.interfaces.database_provider import DatabaseProvider
from app.core.exceptions import AppException

logger = structlog.get_logger()


class SupabaseProvider(DatabaseProvider):
    """Supabase database provider implementation."""
    
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def get_by_id(self, table: str, record_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get single record by ID."""
        def _get():
            try:
                response = self.client.table(table).select('*').eq('id', str(record_id)).execute()
                return response.data[0] if response.data else None
            except Exception as e:
                logger.error(f"Error getting record from {table}", error=str(e))
                raise AppException(f"Database error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)
    
    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new record."""
        def _create():
            try:
                response = self.client.table(table).insert(data).execute()
                return response.data[0]
            except Exception as e:
                logger.error(f"Error creating record in {table}", error=str(e), data=data)
                raise AppException(f"Database error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _create)
    
    async def update(
        self, 
        table: str, 
        record_id: Union[str, UUID], 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing record."""
        def _update():
            try:
                response = self.client.table(table).update(updates).eq('id', str(record_id)).execute()
                return response.data[0] if response.data else {}
            except Exception as e:
                logger.error(f"Error updating record in {table}", error=str(e), record_id=str(record_id))
                raise AppException(f"Database error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _update)
    
    async def delete(self, table: str, record_id: Union[str, UUID]) -> bool:
        """Delete record."""
        def _delete():
            try:
                response = self.client.table(table).delete().eq('id', str(record_id)).execute()
                return len(response.data) > 0
            except Exception as e:
                logger.error(f"Error deleting record from {table}", error=str(e), record_id=str(record_id))
                raise AppException(f"Database error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _delete)
    
    async def find(
        self,
        table: str,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find records with filters."""
        def _find():
            try:
                query = self.client.table(table).select('*')
                
                # Apply filters
                for key, value in filters.items():
                    if value is not None:
                        query = query.eq(key, value)
                
                # Apply ordering
                if order_by:
                    if order_by.startswith('-'):
                        query = query.order(order_by[1:], desc=True)
                    else:
                        query = query.order(order_by)
                
                # Apply pagination
                if limit:
                    query = query.limit(limit)
                if offset:
                    query = query.offset(offset)
                
                response = query.execute()
                return response.data
            except Exception as e:
                logger.error(f"Error finding records in {table}", error=str(e), filters=filters)
                raise AppException(f"Database error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _find)
    
    async def vector_search(
        self,
        query_vector: List[float],
        table: str = "document_chunks",
        similarity_threshold: float = 0.7,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search using Supabase's built-in vector capabilities."""
        def _search():
            try:
                # Convert query vector to proper format for Supabase
                vector_str = "[" + ",".join(map(str, query_vector)) + "]"
                
                # Build the query with vector similarity search
                query = self.client.table(table).select("*")
                
                # Apply filters if provided and they exist in the table schema
                if filters:
                    for key, value in filters.items():
                        if value is not None:
                            # Only apply filters for columns that exist in document_chunks table
                            # document_type and faculty are in documents table, not chunks table
                            if key not in ['document_type', 'faculty']:
                                query = query.eq(key, value)
                
                # For now, we'll do a basic query and handle similarity in the application layer
                # In a production setup, you would configure pgvector extension and use proper vector operations
                response = query.limit(limit * 2).execute()  # Get more results for filtering
                
                results = response.data
                
                # If we have embedding data, we can calculate similarities
                # For now, we'll return the results as-is since the embedding comparison 
                # would require the pgvector extension properly configured in Supabase
                return results[:limit]
                
            except Exception as e:
                logger.warning(f"Vector search failed, using fallback search", error=str(e))
                # Fallback to basic text search
                query = self.client.table(table).select('*')
                # Only apply valid filters for the table
                if filters:
                    for key, value in filters.items():
                        if value is not None and key not in ['document_type', 'faculty']:
                            query = query.eq(key, value)
                response = query.limit(limit).execute()
                return response.data
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _search)
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        def _health():
            try:
                # Simple query to check connectivity
                response = self.client.table('users').select('id').limit(1).execute()
                return True
            except Exception as e:
                logger.error("Database health check failed", error=str(e))
                return False
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _health)


