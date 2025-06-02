# =======================
# app/api/v1/chat.py
# =======================
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.core.dependencies import get_conversation_service
from app.services.conversation_service import ConversationService
from app.models.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationListResponse
)

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> ChatResponse:
    """Process a chat message and return AI response."""
    try:
        response = await conversation_service.process_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    user_id: str,
    limit: int = 20,
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> ConversationListResponse:
    """Get user's conversation history."""
    try:
        conversations = await conversation_service.get_user_conversations(user_id, limit)
        return ConversationListResponse(conversations=conversations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> ConversationResponse:
    """Get specific conversation with messages."""
    try:
        conversation = await conversation_service.get_conversation_with_messages(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

