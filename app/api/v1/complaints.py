"""Complaint management API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide

from app.core.container import Container
from app.models.complaint import ComplaintCreate, ComplaintResponse, ComplaintUpdate
from app.services.complaint_service import ComplaintService

router = APIRouter()


@router.post("/", response_model=ComplaintResponse)
@inject
async def create_complaint(
    complaint: ComplaintCreate,
    complaint_service: ComplaintService = Depends(Provide[Container.complaint_service])
):
    """Create a new complaint."""
    try:
        response = await complaint_service.create_complaint(complaint)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating complaint: {str(e)}"
        )


@router.get("/", response_model=List[ComplaintResponse])
@inject
async def list_complaints(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    complaint_service: ComplaintService = Depends(Provide[Container.complaint_service])
):
    """List complaints with optional filtering."""
    try:
        complaints = await complaint_service.list_complaints(
            skip=skip, 
            limit=limit, 
            status_filter=status_filter
        )
        return complaints
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing complaints: {str(e)}"
        )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
@inject
async def get_complaint(
    complaint_id: str,
    complaint_service: ComplaintService = Depends(Provide[Container.complaint_service])
):
    """Get complaint by ID."""
    try:
        complaint = await complaint_service.get_complaint(complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint not found"
            )
        return complaint
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving complaint: {str(e)}"
        )


@router.put("/{complaint_id}", response_model=ComplaintResponse)
@inject
async def update_complaint(
    complaint_id: str,
    complaint_update: ComplaintUpdate,
    complaint_service: ComplaintService = Depends(Provide[Container.complaint_service])
):
    """Update complaint status or details."""
    try:
        complaint = await complaint_service.update_complaint(complaint_id, complaint_update)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint not found"
            )
        return complaint
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating complaint: {str(e)}"
        )
