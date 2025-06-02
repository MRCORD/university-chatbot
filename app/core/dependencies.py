# =======================
# app/core/dependencies.py
# =======================
from fastapi import Depends

from app.core.container import get_container, Container
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.user_service import UserService
from app.services.complaint_service import ComplaintService


def get_conversation_service(
    container: Container = Depends(get_container)
) -> ConversationService:
    """FastAPI dependency for conversation service."""
    return container.get_conversation_service()


def get_document_service(
    container: Container = Depends(get_container)
) -> DocumentService:
    """FastAPI dependency for document service."""
    return container.get_document_service()


def get_user_service(
    container: Container = Depends(get_container)
) -> UserService:
    """FastAPI dependency for user service."""
    return container.get_user_service()


def get_complaint_service(
    container: Container = Depends(get_container)
) -> ComplaintService:
    """FastAPI dependency for complaint service."""
    return container.get_complaint_service()

