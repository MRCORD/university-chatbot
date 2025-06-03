# =======================
# app/services/complaint_service.py
# =======================
from typing import List, Optional
import structlog

from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.user_repository import UserRepository
from app.models.complaint import (
    ComplaintSubmissionRequest, ComplaintResponse, ComplaintListResponse,
    ComplaintCategory, ComplaintPriority, ComplaintStatus, UrgencyLevel
)
from app.core.exceptions import AppException

logger = structlog.get_logger()


class ComplaintService:
    """Service for complaint management."""
    
    def __init__(
        self,
        complaint_repo: ComplaintRepository,
        user_repo: UserRepository
    ):
        self.complaint_repo = complaint_repo
        self.user_repo = user_repo
    
    async def submit_complaint(self, request: ComplaintSubmissionRequest) -> ComplaintResponse:
        """Submit a new complaint."""
        try:
            # Validate user exists if not anonymous
            if not request.is_anonymous and request.user_id:
                user = await self.user_repo.get_by_id(request.user_id)
                if not user:
                    raise AppException("User not found", status_code=404)
            
            # Create complaint data
            complaint_data = {
                'title': request.title,
                'description': request.description,
                'category': request.category.value,
                'priority': ComplaintPriority.MEDIUM.value,  # Default priority
                'status': ComplaintStatus.SUBMITTED.value,
                'urgency_level': UrgencyLevel.NORMAL.value,  # Default urgency
                'is_anonymous': request.is_anonymous,
                'user_id': request.user_id if not request.is_anonymous else None,
                'conversation_id': request.conversation_id,
                'upvotes': 0,
                'view_count': 0,
                'ai_generated_tags': [],  # TODO: Extract tags with AI
                'similar_complaint_ids': [],  # Initialize as empty list
                'ai_extraction_metadata': {}
            }
            
            complaint = await self.complaint_repo.create(complaint_data)
            
            return ComplaintResponse(
                id=complaint['id'],
                title=complaint['title'],
                description=complaint['description'],
                category=ComplaintCategory(complaint['category']),
                priority=ComplaintPriority(complaint['priority']),
                status=ComplaintStatus(complaint['status']),
                urgency_level=UrgencyLevel(complaint['urgency_level']),
                affected_service=complaint.get('affected_service'),
                suggested_department=complaint.get('suggested_department'),
                ai_generated_tags=complaint.get('ai_generated_tags', []),
                upvotes=complaint['upvotes'],
                view_count=complaint['view_count'],
                is_anonymous=complaint['is_anonymous'],
                similar_complaint_ids=complaint.get('similar_complaint_ids') or [],
                resolved_at=complaint.get('resolved_at'),
                created_at=complaint['created_at']
            )
            
        except Exception as e:
            logger.error("Error submitting complaint", error=str(e))
            raise AppException(f"Failed to submit complaint: {str(e)}")
    
    async def get_public_complaints(
        self, 
        limit: int = 50, 
        category: Optional[str] = None
    ) -> ComplaintListResponse:
        """Get public complaints for dashboard."""
        try:
            complaints = await self.complaint_repo.get_public_complaints(limit, category)
            
            complaint_responses = [
                ComplaintResponse(
                    id=complaint['id'],
                    title=complaint['title'],
                    description=complaint['description'],
                    category=ComplaintCategory(complaint['category']),
                    priority=ComplaintPriority(complaint['priority']),
                    status=ComplaintStatus(complaint['status']),
                    urgency_level=UrgencyLevel(complaint['urgency_level']),
                    affected_service=complaint.get('affected_service'),
                    suggested_department=complaint.get('suggested_department'),
                    ai_generated_tags=complaint.get('ai_generated_tags', []),
                    upvotes=complaint['upvotes'],
                    view_count=complaint['view_count'],
                    is_anonymous=complaint['is_anonymous'],
                    similar_complaint_ids=complaint.get('similar_complaint_ids') or [],
                    resolved_at=complaint.get('resolved_at'),
                    created_at=complaint['created_at']
                )
                for complaint in complaints
            ]
            
            return ComplaintListResponse(
                complaints=complaint_responses,
                total=len(complaint_responses)
            )
            
        except Exception as e:
            logger.error("Error getting public complaints", error=str(e))
            raise AppException(f"Failed to get complaints: {str(e)}")


