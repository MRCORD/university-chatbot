"""Chat API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide

from app.core.container import Container
from app.models.conversation import ConversationCreate, ConversationResponse, MessageCreate
from app.services.conversation_service import ConversationService

router = APIRouter()


@router.post("/message", response_model=ConversationResponse)
@inject
async def send_message(
    message: MessageCreate,
    conversation_service: ConversationService = Depends(Provide[Container.conversation_service])
):
    """Send a message to the chatbot and get a response."""
    try:
        response = await conversation_service.process_message(message)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/conversation", response_model=ConversationResponse)
@inject
async def create_conversation(
    conversation: ConversationCreate,
    conversation_service: ConversationService = Depends(Provide[Container.conversation_service])
):
    """Create a new conversation."""
    try:
        response = await conversation_service.create_conversation(conversation)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating conversation: {str(e)}"
        )


@router.get("/conversation/{conversation_id}")
@inject
async def get_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(Provide[Container.conversation_service])
):
    """Get conversation history by ID."""
    try:
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation: {str(e)}"
        )
