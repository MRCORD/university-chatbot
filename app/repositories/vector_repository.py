# =======================
# app/repositories/vector_repository.py
# =======================
from typing import List, Dict, Any, Optional
import structlog
from app.repositories.base import BaseRepository
from app.interfaces.database_provider import DatabaseProvider

logger = structlog.get_logger()


class VectorRepository(BaseRepository):
    """Enhanced vector repository for vector search operations."""
    
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
        """Perform vector similarity search with enhanced filtering."""
        try:
            # Build filters
            filters = {}
            if document_type:
                filters['document_type'] = document_type
            if faculty:
                filters['faculty'] = faculty
            
            # Perform vector search using database provider
            results = await self.db.vector_search(
                query_vector=query_vector,
                table="document_chunks",
                similarity_threshold=similarity_threshold,
                limit=limit,
                filters=filters
            )
            
            # Add similarity scores if not present
            for result in results:
                if 'similarity_score' not in result:
                    result['similarity_score'] = 0.8  # Default score
            
            # Sort by similarity score (highest first)
            results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            logger.info("Vector search completed", 
                       results_found=len(results),
                       similarity_threshold=similarity_threshold)
            
            return results
            
        except Exception as e:
            logger.error("Vector search failed", 
                        error=str(e),
                        similarity_threshold=similarity_threshold)
            # Return empty results instead of failing
            return []
    
    async def create_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document chunk with embedding."""
        try:
            # Validate required fields
            required_fields = ['document_id', 'content', 'embedding']
            for field in required_fields:
                if field not in chunk_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create the chunk
            chunk = await self.create(chunk_data)
            
            logger.info("Document chunk created", 
                       chunk_id=chunk['id'],
                       document_id=chunk_data['document_id'])
            
            return chunk
            
        except Exception as e:
            logger.error("Failed to create document chunk", 
                        document_id=chunk_data.get('document_id'),
                        error=str(e))
            raise
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        try:
            chunks = await self.find(
                filters={'document_id': document_id},
                order_by='chunk_index'
            )
            
            logger.info("Retrieved document chunks", 
                       document_id=document_id,
                       chunk_count=len(chunks))
            
            return chunks
            
        except Exception as e:
            logger.error("Failed to get document chunks", 
                        document_id=document_id,
                        error=str(e))
            return []
    
    async def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks for a specific document."""
        try:
            chunks = await self.get_chunks_by_document_id(document_id)
            deleted_count = 0
            
            for chunk in chunks:
                success = await self.delete(chunk['id'])
                if success:
                    deleted_count += 1
            
            logger.info("Deleted document chunks", 
                       document_id=document_id,
                       deleted_count=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to delete document chunks", 
                        document_id=document_id,
                        error=str(e))
            return 0
    
    async def search_by_text(
        self, 
        query_text: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fallback text search when vector search fails."""
        try:
            # Simple text search using database full-text search
            # This is a fallback when vector search is not available
            results = await self.find(
                filters={},
                limit=limit
            )
            
            # Filter results that contain query terms
            query_terms = query_text.lower().split()
            filtered_results = []
            
            for result in results:
                content = result.get('content', '').lower()
                if any(term in content for term in query_terms):
                    # Add a simple score based on term matches
                    score = sum(1 for term in query_terms if term in content) / len(query_terms)
                    result['similarity_score'] = score
                    filtered_results.append(result)
            
            # Sort by score
            filtered_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            logger.info("Text search completed", 
                       query=query_text,
                       results_found=len(filtered_results))
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error("Text search failed", 
                        query=query_text,
                        error=str(e))
            return []
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get statistics about document chunks."""
        try:
            # Get total chunks
            all_chunks = await self.find(filters={})
            total_chunks = len(all_chunks)
            
            # Group by document
            doc_stats = {}
            for chunk in all_chunks:
                doc_id = chunk['document_id']
                if doc_id not in doc_stats:
                    doc_stats[doc_id] = 0
                doc_stats[doc_id] += 1
            
            stats = {
                'total_chunks': total_chunks,
                'total_documents': len(doc_stats),
                'avg_chunks_per_document': total_chunks / len(doc_stats) if doc_stats else 0,
                'documents_with_chunks': list(doc_stats.keys())
            }
            
            logger.info("Document statistics calculated", **stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to calculate statistics", error=str(e))
            return {
                'total_chunks': 0,
                'total_documents': 0,
                'avg_chunks_per_document': 0,
                'documents_with_chunks': []
            }
    
    async def find_similar_chunks(
        self, 
        chunk_id: str, 
        similarity_threshold: float = 0.8,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find chunks similar to a given chunk."""
        try:
            # Get the reference chunk
            reference_chunk = await self.get_by_id(chunk_id)
            if not reference_chunk or 'embedding' not in reference_chunk:
                return []
            
            # Use the chunk's embedding to find similar chunks
            results = await self.vector_search(
                query_vector=reference_chunk['embedding'],
                similarity_threshold=similarity_threshold,
                limit=limit + 1  # +1 to exclude the reference chunk itself
            )
            
            # Remove the reference chunk from results
            filtered_results = [r for r in results if r['id'] != chunk_id]
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error("Failed to find similar chunks", 
                        chunk_id=chunk_id,
                        error=str(e))
            return []
    
    async def update_chunk_metadata(
        self, 
        chunk_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Update chunk metadata without changing the embedding."""
        try:
            # Get current chunk
            current_chunk = await self.get_by_id(chunk_id)
            if not current_chunk:
                return False
            
            # Update only metadata fields
            update_data = {}
            allowed_fields = ['page_number', 'section_title', 'character_count']
            
            for field in allowed_fields:
                if field in metadata:
                    update_data[field] = metadata[field]
            
            if not update_data:
                return True  # Nothing to update
            
            await self.update(chunk_id, update_data)
            
            logger.info("Chunk metadata updated", 
                       chunk_id=chunk_id,
                       updated_fields=list(update_data.keys()))
            
            return True
            
        except Exception as e:
            logger.error("Failed to update chunk metadata", 
                        chunk_id=chunk_id,
                        error=str(e))
            return False