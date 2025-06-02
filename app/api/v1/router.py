# =======================
# app/api/v1/router.py
# =======================
from fastapi import APIRouter

from app.api.v1 import chat, documents, users, complaints

api_router = APIRouter()

# Include all route modules
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

api_router.include_router(
    documents.router,
    prefix="/documents", 
    tags=["documents"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    complaints.router,
    prefix="/complaints",
    tags=["complaints"]
)

