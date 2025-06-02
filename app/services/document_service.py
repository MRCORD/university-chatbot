# =======================
# app/services/document_service.py
# =======================
import asyncio
from typing import List, Optional, BinaryIO
import structlog
from pathlib import Path
import tempfile
import os

from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.interfaces.storage_provider import StorageProvider
from app.services.embedding_service import EmbeddingService
from app.utils.document_processing import DocumentProcessor
from app.models.document import (
    DocumentType, ProcessingStatus, DocumentResponse, 
    DocumentSearchRequest, DocumentSearchResponse, DocumentChunkResponse
)
from app.core.exceptions import AppException

logger = structlog.get_logger()


class DocumentService:
    """Enhanced service for managing documents with real processing and search."""
    
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
        self.processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    
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
            # Validate file type
            if not filename.lower().endswith('.pdf'):
                raise AppException("Only PDF files are supported", status_code=400)
            
            # Generate storage path
            storage_path = f"documents/{document_type.value}/{filename}"
            
            # Upload to storage
            storage_url = await self.storage.upload_file(
                bucket="official-documents",
                file_path=storage_path,
                file=file,
                content_type="application/pdf"
            )
            
            # Get file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            # Create document record
            document_data = {
                'filename': filename,
                'original_filename': filename,
                'document_type': document_type.value,
                'storage_bucket': 'official-documents',
                'storage_path': storage_path,
                'storage_url': storage_url,
                'file_size_bytes': file_size,
                'faculty': faculty,
                'academic_year': academic_year,
                'uploaded_by': uploaded_by,
                'processing_status': ProcessingStatus.PENDING.value,
                'metadata': {}
            }
            
            document = await self.document_repo.create(document_data)
            
            # Trigger background processing
            asyncio.create_task(self._process_document_background(
                document['id'], 
                storage_path
            ))
            
            logger.info("Document uploaded successfully", 
                       document_id=document['id'],
                       filename=filename)
            
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
        """Search documents using vector similarity - REAL IMPLEMENTATION."""
        try:
            logger.info("Document search request", 
                       query=request.query, 
                       limit=request.limit)
            
            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(request.query)
            
            # Prepare filters
            filters = {}
            if request.document_type:
                filters['document_type'] = request.document_type.value
            if request.faculty:
                filters['faculty'] = request.faculty
            
            # Perform vector search
            search_results = await self.vector_repo.vector_search(
                query_vector=query_embedding,
                similarity_threshold=request.similarity_threshold,
                limit=request.limit,
                document_type=request.document_type.value if request.document_type else None,
                faculty=request.faculty
            )
            
            # Convert results to response format
            chunks = []
            for result in search_results:
                try:
                    # Get document metadata
                    document_data = await self.document_repo.get_by_id(result['document_id'])
                    if not document_data:
                        logger.warning("Document not found for chunk", 
                                     document_id=result['document_id'])
                        continue
                    
                    # Create document response
                    document_response = DocumentResponse(
                        id=document_data['id'],
                        filename=document_data['filename'],
                        original_filename=document_data['original_filename'],
                        document_type=DocumentType(document_data['document_type']),
                        storage_url=document_data.get('storage_url'),
                        file_size_bytes=document_data.get('file_size_bytes'),
                        faculty=document_data.get('faculty'),
                        academic_year=document_data.get('academic_year'),
                        processing_status=ProcessingStatus(document_data['processing_status']),
                        metadata=document_data.get('metadata', {}),
                        created_at=document_data['created_at']
                    )
                    
                    # Create chunk response
                    chunk_response = DocumentChunkResponse(
                        id=result['id'],
                        content=result['content'],
                        page_number=result.get('page_number'),
                        section_title=result.get('section_title'),
                        similarity_score=result.get('similarity_score', 0.0),
                        document=document_response
                    )
                    
                    chunks.append(chunk_response)
                    
                except Exception as e:
                    logger.warning("Error processing search result", 
                                 result_id=result.get('id'), 
                                 error=str(e))
                    continue
            
            logger.info("Document search completed", 
                       query=request.query,
                       results_found=len(chunks))
            
            return DocumentSearchResponse(
                query=request.query,
                chunks=chunks,
                total_found=len(chunks)
            )
            
        except Exception as e:
            logger.error("Document search failed", 
                        query=request.query, 
                        error=str(e))
            # Return empty results instead of failing
            return DocumentSearchResponse(
                query=request.query,
                chunks=[],
                total_found=0
            )
    
    async def _process_document_background(self, document_id: str, storage_path: str):
        """Background task to process uploaded document."""
        try:
            logger.info("Starting document processing", document_id=document_id)
            
            # Update status to processing
            await self.document_repo.update(document_id, {
                'processing_status': ProcessingStatus.PROCESSING.value
            })
            
            # Download file to temporary location
            temp_file_path = await self._download_temp_file(storage_path)
            
            try:
                # Process PDF: extract text and create chunks
                chunks = await self.processor.process_pdf(temp_file_path, document_id)
                
                if not chunks:
                    logger.warning("No chunks generated from document", 
                                 document_id=document_id)
                    await self.document_repo.update(document_id, {
                        'processing_status': ProcessingStatus.FAILED.value,
                        'metadata': {'error': 'No text content found in PDF'}
                    })
                    return
                
                # Generate embeddings for all chunks
                chunk_texts = [chunk['content'] for chunk in chunks]
                embeddings = await self.embeddings.embed_texts(chunk_texts)
                
                # Store chunks with embeddings in vector database
                stored_chunks = 0
                for chunk, embedding in zip(chunks, embeddings):
                    try:
                        chunk_data = {
                            'document_id': document_id,
                            'content': chunk['content'],
                            'chunk_index': chunk['chunk_index'],
                            'page_number': chunk.get('page_number'),
                            'character_count': chunk.get('character_count'),
                            'embedding': embedding
                        }
                        
                        await self.vector_repo.create(chunk_data)
                        stored_chunks += 1
                        
                    except Exception as e:
                        logger.warning("Failed to store chunk", 
                                     document_id=document_id,
                                     chunk_index=chunk['chunk_index'],
                                     error=str(e))
                        continue
                
                # Extract document metadata
                pdf_metadata = await self.processor.extract_metadata(temp_file_path)
                
                # Update document status to completed
                await self.document_repo.update(document_id, {
                    'processing_status': ProcessingStatus.COMPLETED.value,
                    'metadata': {
                        'chunks_created': stored_chunks,
                        'total_chunks': len(chunks),
                        'pdf_metadata': pdf_metadata,
                        'processing_completed_at': None  # Will be set by database
                    }
                })
                
                logger.info("Document processing completed successfully",
                           document_id=document_id,
                           chunks_stored=stored_chunks)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error("Document processing failed", 
                        document_id=document_id, 
                        error=str(e))
            
            # Update status to failed
            try:
                await self.document_repo.update(document_id, {
                    'processing_status': ProcessingStatus.FAILED.value,
                    'metadata': {'error': str(e)}
                })
            except Exception as update_error:
                logger.error("Failed to update document status", 
                           document_id=document_id,
                           error=str(update_error))
    
    async def _download_temp_file(self, storage_path: str) -> str:
        """Download file from storage to temporary local file."""
        try:
            # Download file content
            file_content = await self.storage.download_file(
                bucket="official-documents",
                file_path=storage_path
            )
            
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            
            try:
                # Write content to temporary file
                with os.fdopen(temp_fd, 'wb') as temp_file:
                    temp_file.write(file_content)
                
                return temp_path
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
            
        except Exception as e:
            logger.error("Failed to download temp file", 
                        storage_path=storage_path, 
                        error=str(e))
            raise AppException(f"Failed to download file for processing: {str(e)}")
    
    async def get_document_by_id(self, document_id: str) -> Optional[DocumentResponse]:
        """Get document by ID."""
        try:
            document_data = await self.document_repo.get_by_id(document_id)
            if not document_data:
                return None
            
            return DocumentResponse(
                id=document_data['id'],
                filename=document_data['filename'],
                original_filename=document_data['original_filename'],
                document_type=DocumentType(document_data['document_type']),
                storage_url=document_data.get('storage_url'),
                file_size_bytes=document_data.get('file_size_bytes'),
                faculty=document_data.get('faculty'),
                academic_year=document_data.get('academic_year'),
                processing_status=ProcessingStatus(document_data['processing_status']),
                metadata=document_data.get('metadata', {}),
                created_at=document_data['created_at']
            )
            
        except Exception as e:
            logger.error("Error getting document", document_id=document_id, error=str(e))
            raise AppException(f"Failed to get document: {str(e)}")
    
    async def get_processing_status(self, document_id: str) -> ProcessingStatus:
        """Get document processing status."""
        document = await self.get_document_by_id(document_id)
        return document.processing_status if document else ProcessingStatus.FAILED
    
    async def reprocess_document(self, document_id: str) -> bool:
        """Trigger reprocessing of a document."""
        try:
            document_data = await self.document_repo.get_by_id(document_id)
            if not document_data:
                raise AppException("Document not found", status_code=404)
            
            # Delete existing chunks
            await self.vector_repo.delete_by_document_id(document_id)
            
            # Trigger reprocessing
            asyncio.create_task(self._process_document_background(
                document_id, 
                document_data['storage_path']
            ))
            
            return True
            
        except Exception as e:
            logger.error("Error reprocessing document", 
                        document_id=document_id, 
                        error=str(e))
            raise AppException(f"Failed to reprocess document: {str(e)}")