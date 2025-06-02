"""Main API router configuration."""

from fastapi import APIRouter

from app.api.v1 import chat, documents, complaints, users

api_router = APIRouter()

# Include all route modules
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["complaints"])
api_router.include_router(users.router, prefix="/users", tags=["users"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "university-chatbot"}
