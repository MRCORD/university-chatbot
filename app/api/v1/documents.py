# =======================
# app/api/v1/documents.py
# =======================
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from typing import Optional

from app.core.dependencies import get_document_service
from app.services.document_service import DocumentService
from app.models.document import (
    DocumentType, DocumentResponse, DocumentSearchRequest, DocumentSearchResponse
)

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    faculty: Optional[str] = Form(None),
    academic_year: Optional[str] = Form(None),
    uploaded_by: str = Form(...),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """Upload a new document."""
    try:
        if not file.filename or not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        document = await document_service.upload_document(
            file=file.file,
            filename=file.filename,
            document_type=document_type,
            uploaded_by=uploaded_by,
            faculty=faculty,
            academic_year=academic_year
        )
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentSearchResponse:
    """Search documents using vector similarity."""
    try:
        results = await document_service.search_documents(request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """Get document by ID."""
    try:
        # Implementation would call document_service.get_by_id
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

