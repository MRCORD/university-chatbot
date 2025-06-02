# =======================
# app/api/v1/complaints.py
# =======================
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.dependencies import get_complaint_service
from app.services.complaint_service import ComplaintService
from app.models.complaint import (
    ComplaintSubmissionRequest, ComplaintResponse, ComplaintListResponse
)

router = APIRouter()

@router.post("/", response_model=ComplaintResponse)
async def submit_complaint(
    request: ComplaintSubmissionRequest,
    complaint_service: ComplaintService = Depends(get_complaint_service)
) -> ComplaintResponse:
    """Submit a new complaint."""
    try:
        complaint = await complaint_service.submit_complaint(request)
        return complaint
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit complaint: {str(e)}")

@router.get("/", response_model=ComplaintListResponse)
async def get_public_complaints(
    limit: int = Query(default=50, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    complaint_service: ComplaintService = Depends(get_complaint_service)
) -> ComplaintListResponse:
    """Get public complaints for dashboard."""
    try:
        complaints = await complaint_service.get_public_complaints(limit, category)
        return complaints
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get complaints: {str(e)}")

@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: str,
    complaint_service: ComplaintService = Depends(get_complaint_service)
) -> ComplaintResponse:
    """Get specific complaint by ID."""
    try:
        # Implementation would call complaint_service.get_by_id
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get complaint: {str(e)}")

@router.post("/{complaint_id}/upvote")
async def upvote_complaint(
    complaint_id: str,
    user_id: str,
    complaint_service: ComplaintService = Depends(get_complaint_service)
):
    """Upvote a complaint."""
    try:
        # Implementation would call complaint_service.upvote
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upvote: {str(e)}")

