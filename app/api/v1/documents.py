"""Document management API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from dependency_injector.wiring import inject, Provide

from app.core.container import Container
from app.models.document import DocumentResponse, DocumentCreate
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
@inject
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(Provide[Container.document_service])
):
    """Upload and process a document."""
    try:
        document = await document_service.upload_document(file)
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
@inject
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    document_service: DocumentService = Depends(Provide[Container.document_service])
):
    """List all documents."""
    try:
        documents = await document_service.list_documents(skip=skip, limit=limit)
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
@inject
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(Provide[Container.document_service])
):
    """Get document by ID."""
    try:
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )


@router.delete("/{document_id}")
@inject
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(Provide[Container.document_service])
):
    """Delete a document."""
    try:
        success = await document_service.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )
