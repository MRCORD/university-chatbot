# =======================
# app/services/conversation_service.py
# =======================
from typing import Optional, List, Dict, Any
import structlog
from uuid import uuid4

from app.repositories.conversation_repository import ConversationRepository
from app.engines.factory import ConversationEngineFactory
from app.services.document_service import DocumentService
from app.models.conversation import (
    ChatRequest, ChatResponse, ConversationResponse, 
    MessageResponse, MessageRole, MessageType, ConversationType
)
from app.core.exceptions import AppException

logger = structlog.get_logger()


class ConversationService:
    """Service for managing conversations and chat interactions."""
    
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        engine_factory: ConversationEngineFactory,
        document_service: DocumentService
    ):
        self.conversation_repo = conversation_repo
        self.engine_factory = engine_factory
        self.document_service = document_service
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Process a chat message and return AI response."""
        try:
            # Get or create conversation
            conversation_id = request.conversation_id
            if not conversation_id:
                conversation_id = await self._create_conversation(
                    request.user_id, 
                    request.conversation_type or ConversationType.GENERAL
                )
            
            # Store user message
            user_message = await self._store_message(
                conversation_id,
                MessageRole.USER,
                request.message,
                MessageType.TEXT
            )
            
            # Get conversation engine
            engine = self.engine_factory.get_engine("langgraph")
            
            # For now, simple response - we'll implement LangGraph later
            response_text = f"I received your message: '{request.message}'. I'm still learning about UP documents!"
            
            # Store assistant response
            assistant_message = await self._store_message(
                conversation_id,
                MessageRole.ASSISTANT,
                response_text,
                MessageType.TEXT,
                metadata={"engine": "langgraph", "sources": []}
            )
            
            return ChatResponse(
                conversation_id=conversation_id,
                message=MessageResponse(
                    id=assistant_message['id'],
                    role=MessageRole.ASSISTANT,
                    content=response_text,
                    message_type=MessageType.TEXT,
                    metadata=assistant_message.get('metadata', {}),
                    created_at=assistant_message['created_at']
                ),
                sources=[],
                confidence_score=0.8,
                suggested_actions=["Ask about specific procedures", "Upload a document"]
            )
            
        except Exception as e:
            logger.error("Error processing chat message", error=str(e), request=request.dict())
            raise AppException(f"Failed to process message: {str(e)}")
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[ConversationResponse]:
        """Get user's conversation history."""
        try:
            conversations = await self.conversation_repo.get_user_conversations(
                user_id, limit
            )
            return [
                ConversationResponse(
                    id=conv['id'],
                    title=conv.get('title'),
                    conversation_type=ConversationType(conv['conversation_type']),
                    status=conv['status'],
                    engine_used=conv['engine_used'],
                    messages=[],  # Will load separately if needed
                    metadata=conv.get('metadata', {}),
                    created_at=conv['created_at'],
                    updated_at=conv.get('updated_at')
                )
                for conv in conversations
            ]
        except Exception as e:
            logger.error("Error getting user conversations", user_id=user_id, error=str(e))
            raise AppException(f"Failed to get conversations: {str(e)}")
    
    async def get_conversation_with_messages(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get conversation with all messages."""
        # Implementation would load conversation and messages
        # For now, return None
        return None
    
    async def _create_conversation(self, user_id: str, conversation_type: ConversationType) -> str:
        """Create a new conversation."""
        conversation_data = {
            'user_id': user_id,
            'conversation_type': conversation_type.value,
            'engine_used': 'langgraph',
            'status': 'active',
            'metadata': {}
        }
        
        conversation = await self.conversation_repo.create(conversation_data)
        return conversation['id']
    
    async def _store_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        message_type: MessageType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a message in the conversation."""
        from app.repositories.base import BaseRepository
        
        # For now, create a simple message repository inline
        # In full implementation, this would be injected
        message_repo = BaseRepository(self.conversation_repo.db, 'messages')
        
        message_data = {
            'conversation_id': conversation_id,
            'role': role.value,
            'content': content,
            'message_type': message_type.value,
            'metadata': metadata or {}
        }
        
        return await message_repo.create(message_data)


