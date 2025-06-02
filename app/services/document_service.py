# =======================
# app/services/document_service.py
# =======================
from typing import List, Optional, BinaryIO
import structlog

from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.interfaces.storage_provider import StorageProvider
from app.services.embedding_service import EmbeddingService
from app.models.document import (
    DocumentType, ProcessingStatus, DocumentResponse, 
    DocumentSearchRequest, DocumentSearchResponse
)
from app.core.exceptions import AppException

logger = structlog.get_logger()


class DocumentService:
    """Service for managing documents and document search."""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        storage_provider: StorageProvider,
        embedding_service: EmbeddingService,
        vector_repo: VectorRepository
    ):
        self.document_repo = document_repo
        self.storage = storage_provider
        self.embeddings = embedding_service
        self.vector_repo = vector_repo
    
    async def upload_document(
        self,
        file: BinaryIO,
        filename: str,
        document_type: DocumentType,
        uploaded_by: str,
        faculty: Optional[str] = None,
        academic_year: Optional[str] = None
    ) -> DocumentResponse:
        """Upload and process a document."""
        try:
            # Generate storage path
            storage_path = f"documents/{document_type.value}/{filename}"
            
            # Upload to storage
            storage_url = await self.storage.upload_file(
                bucket="official-documents",
                file_path=storage_path,
                file=file,
                content_type="application/pdf"
            )
            
            # Create document record
            document_data = {
                'filename': filename,
                'original_filename': filename,
                'document_type': document_type.value,
                'storage_bucket': 'official-documents',
                'storage_path': storage_path,
                'storage_url': storage_url,
                'faculty': faculty,
                'academic_year': academic_year,
                'uploaded_by': uploaded_by,
                'processing_status': ProcessingStatus.PENDING.value,
                'metadata': {}
            }
            
            document = await self.document_repo.create(document_data)
            
            # TODO: Trigger background processing
            logger.info("Document uploaded successfully", document_id=document['id'])
            
            return DocumentResponse(
                id=document['id'],
                filename=document['filename'],
                original_filename=document['original_filename'],
                document_type=DocumentType(document['document_type']),
                storage_url=document.get('storage_url'),
                file_size_bytes=document.get('file_size_bytes'),
                faculty=document.get('faculty'),
                academic_year=document.get('academic_year'),
                processing_status=ProcessingStatus(document['processing_status']),
                metadata=document.get('metadata', {}),
                created_at=document['created_at']
            )
            
        except Exception as e:
            logger.error("Error uploading document", filename=filename, error=str(e))
            raise AppException(f"Failed to upload document: {str(e)}")
    
    async def search_documents(self, request: DocumentSearchRequest) -> DocumentSearchResponse:
        """Search documents using vector similarity."""
        try:
            # Generate query embedding
            query_embeddings = await self.embeddings.embed_texts([request.query])
            query_vector = query_embeddings[0]
            
            # Perform vector search
            results = await self.vector_repo.vector_search(
                query_vector=query_vector,
                similarity_threshold=request.similarity_threshold,
                limit=request.limit,
                document_type=request.document_type.value if request.document_type else None,
                faculty=request.faculty
            )
            
            # For now, return simplified results
            # In full implementation, we'd join with document metadata
            return DocumentSearchResponse(
                query=request.query,
                chunks=[],  # TODO: Convert results to DocumentChunkResponse
                total_found=len(results)
            )
            
        except Exception as e:
            logger.error("Error searching documents", query=request.query, error=str(e))
            raise AppException(f"Failed to search documents: {str(e)}")


