# =======================
# app/engines/langgraph/tools/document_tool.py
# =======================
"""
Document tool for integrating DocumentService with LangGraph workflows.

This tool wraps the existing DocumentService to provide standardized
document search and retrieval functionality for LangGraph workflows.
"""

from typing import List, Optional, Dict, Any
import structlog

from app.services.document_service import DocumentService
from app.models.document import DocumentSearchRequest, DocumentType
from app.engines.langgraph.tools.base_tool import BaseTool, ToolExecutionError
from app.engines.langgraph.state.schemas import ToolType, DocumentSearchResult

logger = structlog.get_logger()


class DocumentTool(BaseTool):
    """
    Tool for document search and retrieval operations.
    
    This tool wraps the DocumentService to provide document search
    capabilities within LangGraph workflows, with standardized
    error handling and result formatting.
    """
    
    def __init__(self, document_service: DocumentService):
        """
        Initialize the document tool.
        
        Args:
            document_service: Instance of DocumentService
        """
        super().__init__(document_service, "DocumentTool")
        self.document_service = document_service
    
    @property
    def tool_type(self) -> ToolType:
        """Return the tool type for document operations."""
        return ToolType.DOCUMENT
    
    async def execute(self, **kwargs) -> DocumentSearchResult:
        """
        Execute document search operation.
        
        This method should not be called directly. Use search_documents()
        or other specific methods instead.
        
        Args:
            **kwargs: Search parameters
            
        Returns:
            DocumentSearchResult with search results
        """
        # Delegate to search_documents as the primary operation
        return await self.search_documents(**kwargs)
    
    async def search_documents(
        self,
        query: str,
        document_type: Optional[DocumentType] = None,
        faculty: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> DocumentSearchResult:
        """
        Search for documents using vector similarity.
        
        Args:
            query: Search query text
            document_type: Optional document type filter
            faculty: Optional faculty filter
            limit: Maximum number of results (default: 5)
            similarity_threshold: Minimum similarity score (default: 0.7)
            
        Returns:
            DocumentSearchResult with search results
            
        Raises:
            ToolExecutionError: If search operation fails
        """
        try:
            # Validate input parameters
            if not query or not query.strip():
                raise ToolExecutionError(
                    "Search query cannot be empty",
                    error_type="invalid_input",
                    details={'query': query}
                )
            
            if limit <= 0 or limit > 50:
                raise ToolExecutionError(
                    "Search limit must be between 1 and 50",
                    error_type="invalid_input",
                    details={'limit': limit}
                )
            
            if not 0.0 <= similarity_threshold <= 1.0:
                raise ToolExecutionError(
                    "Similarity threshold must be between 0.0 and 1.0",
                    error_type="invalid_input",
                    details={'similarity_threshold': similarity_threshold}
                )
            
            # Create search request
            search_request = DocumentSearchRequest(
                query=query.strip(),
                document_type=document_type,
                faculty=faculty,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            logger.info("Executing document search",
                       query=query[:50],
                       document_type=document_type.value if document_type else None,
                       faculty=faculty,
                       limit=limit,
                       similarity_threshold=similarity_threshold)
            
            # Execute search using DocumentService
            search_response = await self.document_service.search_documents(search_request)
            
            # Process results
            chunks_found = len(search_response.chunks)
            best_similarity = 0.0
            sources = []
            content_parts = []
            
            if search_response.chunks:
                # Get best similarity score
                best_similarity = max(chunk.similarity_score for chunk in search_response.chunks)
                
                # Extract sources (unique document filenames)
                sources = list(set(chunk.document.filename for chunk in search_response.chunks))
                
                # Combine content from top chunks
                for chunk in search_response.chunks[:3]:  # Top 3 chunks
                    content_parts.append(chunk.content)
            
            # Determine success and confidence
            success = chunks_found > 0
            confidence = best_similarity if success else 0.0
            
            # Create result data
            result_data = {
                'query': query,
                'content': '\n\n'.join(content_parts) if content_parts else '',
                'chunks': [
                    {
                        'content': chunk.content,
                        'similarity_score': chunk.similarity_score,
                        'document_filename': chunk.document.filename,
                        'page_number': chunk.page_number
                    }
                    for chunk in search_response.chunks
                ],
                'total_found': search_response.total_found
            }
            
            logger.info("Document search completed",
                       query=query[:50],
                       chunks_found=chunks_found,
                       best_similarity=best_similarity,
                       sources_count=len(sources))
            
            # Return successful result
            return DocumentSearchResult(
                tool_type=ToolType.DOCUMENT,
                success=success,
                data=result_data,
                sources=sources,
                confidence=confidence,
                query=query,
                chunks_found=chunks_found,
                best_similarity=best_similarity,
                documents_searched=1  # We search across all documents
            )
            
        except ToolExecutionError:
            # Re-raise tool execution errors
            raise
            
        except Exception as e:
            logger.error("Document search failed with unexpected error",
                        query=query[:50],
                        error=str(e),
                        exc_info=True)
            
            raise ToolExecutionError(
                f"Document search failed: {str(e)}",
                error_type="service_error",
                details={
                    'query': query,
                    'document_type': document_type.value if document_type else None,
                    'faculty': faculty,
                    'exception_type': type(e).__name__
                },
                recoverable=True
            )
    
    async def get_document_by_id(self, document_id: str) -> DocumentSearchResult:
        """
        Get a specific document by ID.
        
        Args:
            document_id: Document identifier
            
        Returns:
            DocumentSearchResult with document information
            
        Raises:
            ToolExecutionError: If document retrieval fails
        """
        try:
            if not document_id or not document_id.strip():
                raise ToolExecutionError(
                    "Document ID cannot be empty",
                    error_type="invalid_input",
                    details={'document_id': document_id}
                )
            
            logger.info("Retrieving document by ID", document_id=document_id)
            
            # Get document using DocumentService
            document = await self.document_service.get_document_by_id(document_id.strip())
            
            if not document:
                return DocumentSearchResult(
                    tool_type=ToolType.DOCUMENT,
                    success=False,
                    data={'document_id': document_id},
                    sources=[],
                    confidence=0.0,
                    query=f"document_id:{document_id}",
                    chunks_found=0,
                    best_similarity=0.0,
                    documents_searched=1
                )
            
            # Create result data
            result_data = {
                'document_id': document_id,
                'filename': document.filename,
                'document_type': document.document_type.value,
                'faculty': document.faculty,
                'processing_status': document.processing_status.value,
                'metadata': document.metadata
            }
            
            logger.info("Document retrieved successfully",
                       document_id=document_id,
                       filename=document.filename)
            
            return DocumentSearchResult(
                tool_type=ToolType.DOCUMENT,
                success=True,
                data=result_data,
                sources=[document.filename],
                confidence=1.0,
                query=f"document_id:{document_id}",
                chunks_found=1,
                best_similarity=1.0,
                documents_searched=1
            )
            
        except ToolExecutionError:
            # Re-raise tool execution errors
            raise
            
        except Exception as e:
            logger.error("Document retrieval failed",
                        document_id=document_id,
                        error=str(e),
                        exc_info=True)
            
            raise ToolExecutionError(
                f"Document retrieval failed: {str(e)}",
                error_type="service_error",
                details={
                    'document_id': document_id,
                    'exception_type': type(e).__name__
                },
                recoverable=True
            )
    
    async def get_processing_status(self, document_id: str) -> DocumentSearchResult:
        """
        Get document processing status.
        
        Args:
            document_id: Document identifier
            
        Returns:
            DocumentSearchResult with processing status
            
        Raises:
            ToolExecutionError: If status check fails
        """
        try:
            if not document_id or not document_id.strip():
                raise ToolExecutionError(
                    "Document ID cannot be empty",
                    error_type="invalid_input",
                    details={'document_id': document_id}
                )
            
            logger.info("Checking document processing status", document_id=document_id)
            
            # Get processing status
            status = await self.document_service.get_processing_status(document_id.strip())
            
            result_data = {
                'document_id': document_id,
                'processing_status': status.value,
                'is_completed': status.value == 'completed',
                'is_failed': status.value == 'failed'
            }
            
            logger.info("Document status retrieved",
                       document_id=document_id,
                       status=status.value)
            
            return DocumentSearchResult(
                tool_type=ToolType.DOCUMENT,
                success=True,
                data=result_data,
                sources=[],
                confidence=1.0,
                query=f"status:{document_id}",
                chunks_found=0,
                best_similarity=1.0,
                documents_searched=1
            )
            
        except Exception as e:
            logger.error("Document status check failed",
                        document_id=document_id,
                        error=str(e))
            
            raise ToolExecutionError(
                f"Document status check failed: {str(e)}",
                error_type="service_error",
                details={
                    'document_id': document_id,
                    'exception_type': type(e).__name__
                },
                recoverable=True
            )
    
    async def health_check(self) -> bool:
        """
        Check if the document service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Try a simple search to verify service is working
            test_request = DocumentSearchRequest(
                query="test",
                limit=1,
                similarity_threshold=0.9
            )
            
            await self.document_service.search_documents(test_request)
            return True
            
        except Exception as e:
            logger.warning("Document service health check failed", error=str(e))
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about this tool's capabilities.
        
        Returns:
            Dictionary describing tool capabilities
        """
        return {
            'tool_name': self.tool_name,
            'tool_type': self.tool_type.value,
            'operations': [
                'search_documents',
                'get_document_by_id', 
                'get_processing_status'
            ],
            'supported_document_types': [dt.value for dt in DocumentType],
            'max_search_limit': 50,
            'supports_filtering': {
                'document_type': True,
                'faculty': True,
                'similarity_threshold': True
            }
        }