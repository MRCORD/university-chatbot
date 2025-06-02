# =======================
# app/services/conversation_service.py
# =======================
from typing import Optional, List, Dict, Any
import structlog
from uuid import uuid4

from app.repositories.conversation_repository import ConversationRepository
from app.engines.factory import ConversationEngineFactory
from app.services.document_service import DocumentService
from app.interfaces.conversation_engine import ConversationContext
from app.models.conversation import (
    ChatRequest, ChatResponse, ConversationResponse, 
    MessageResponse, MessageRole, MessageType, ConversationType
)
from app.core.exceptions import AppException

logger = structlog.get_logger()


class ConversationService:
    """Enhanced service for managing conversations with real AI processing."""
    
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
        """Process a chat message using real LangGraph AI engine."""
        try:
            logger.info("Processing chat message", 
                       user_id=request.user_id,
                       message_length=len(request.message),
                       conversation_id=request.conversation_id)
            
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
                MessageType.TEXT,
                metadata=request.context or {}
            )
            
            # Build conversation context
            conversation_history = await self._get_conversation_history(conversation_id)
            
            context = ConversationContext(
                user_id=request.user_id,
                session_id=conversation_id,
                query_type=None,  # Will be determined by engine
                conversation_history=conversation_history,
                user_metadata=request.context or {},
                current_documents=[]  # Could be enhanced to track active documents
            )
            
            # Get AI engine and process query
            engine = self.engine_factory.get_engine("langgraph")
            ai_response = await engine.process_query(request.message, context)
            
            # Store assistant response
            assistant_message = await self._store_message(
                conversation_id,
                MessageRole.ASSISTANT,
                ai_response.response_text,
                MessageType.TEXT,
                metadata={
                    "engine": "langgraph",
                    "query_type": ai_response.query_type.value,
                    "confidence_score": ai_response.confidence_score,
                    "sources": ai_response.sources,
                    "structured_data": ai_response.structured_data,
                    **ai_response.metadata
                }
            )
            
            # Update conversation with latest activity
            await self._update_conversation_activity(conversation_id)
            
            # Create response
            response = ChatResponse(
                conversation_id=conversation_id,
                message=MessageResponse(
                    id=assistant_message['id'],
                    role=MessageRole.ASSISTANT,
                    content=ai_response.response_text,
                    message_type=MessageType.TEXT,
                    metadata=assistant_message.get('metadata', {}),
                    created_at=assistant_message['created_at']
                ),
                sources=ai_response.sources,
                confidence_score=ai_response.confidence_score,
                suggested_actions=ai_response.suggested_actions
            )
            
            logger.info("Chat message processed successfully",
                       conversation_id=conversation_id,
                       query_type=ai_response.query_type.value,
                       confidence=ai_response.confidence_score,
                       sources_count=len(ai_response.sources))
            
            return response
            
        except Exception as e:
            logger.error("Error processing chat message", 
                        error=str(e), 
                        user_id=request.user_id,
                        message=request.message[:100])
            
            # Create fallback response
            fallback_response = ChatResponse(
                conversation_id=conversation_id if 'conversation_id' in locals() else "error",
                message=MessageResponse(
                    id="error",
                    role=MessageRole.ASSISTANT,
                    content="Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?",
                    message_type=MessageType.ERROR,
                    metadata={"error": str(e)},
                    created_at=None
                ),
                sources=[],
                confidence_score=0.0,
                suggested_actions=["Intenta reformular tu pregunta", "Contacta soporte técnico"]
            )
            
            return fallback_response
    
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
            
            conversation_responses = []
            for conv in conversations:
                # Get message count for each conversation
                message_count = await self._get_message_count(conv['id'])
                
                conversation_response = ConversationResponse(
                    id=conv['id'],
                    title=conv.get('title') or self._generate_conversation_title(conv),
                    conversation_type=ConversationType(conv['conversation_type']),
                    status=conv['status'],
                    engine_used=conv['engine_used'],
                    messages=[],  # Not loading messages in list view for performance
                    metadata={
                        **conv.get('metadata', {}),
                        'message_count': message_count
                    },
                    created_at=conv['created_at'],
                    updated_at=conv.get('updated_at')
                )
                
                conversation_responses.append(conversation_response)
            
            logger.info("Retrieved user conversations", 
                       user_id=user_id,
                       conversation_count=len(conversation_responses))
            
            return conversation_responses
            
        except Exception as e:
            logger.error("Error getting user conversations", 
                        user_id=user_id, 
                        error=str(e))
            return []
    
    async def get_conversation_with_messages(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get conversation with all messages."""
        try:
            # Get conversation
            conversation = await self.conversation_repo.get_by_id(conversation_id)
            if not conversation:
                return None
            
            # Get messages
            messages = await self._get_conversation_messages(conversation_id)
            
            conversation_response = ConversationResponse(
                id=conversation['id'],
                title=conversation.get('title') or self._generate_conversation_title(conversation),
                conversation_type=ConversationType(conversation['conversation_type']),
                status=conversation['status'],
                engine_used=conversation['engine_used'],
                messages=messages,
                metadata=conversation.get('metadata', {}),
                created_at=conversation['created_at'],
                updated_at=conversation.get('updated_at')
            )
            
            logger.info("Retrieved conversation with messages", 
                       conversation_id=conversation_id,
                       message_count=len(messages))
            
            return conversation_response
            
        except Exception as e:
            logger.error("Error getting conversation with messages", 
                        conversation_id=conversation_id, 
                        error=str(e))
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
        
        logger.info("Created new conversation", 
                   conversation_id=conversation['id'],
                   user_id=user_id,
                   type=conversation_type.value)
        
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
        
        # Create message repository
        message_repo = BaseRepository(self.conversation_repo.db, 'messages')
        
        message_data = {
            'conversation_id': conversation_id,
            'role': role.value,
            'content': content,
            'message_type': message_type.value,
            'metadata': metadata or {}
        }
        
        message = await message_repo.create(message_data)
        
        logger.debug("Message stored", 
                    conversation_id=conversation_id,
                    role=role.value,
                    content_length=len(content))
        
        return message
    
    async def _get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for context."""
        try:
            from app.repositories.base import BaseRepository
            message_repo = BaseRepository(self.conversation_repo.db, 'messages')
            
            messages = await message_repo.find(
                filters={'conversation_id': conversation_id},
                limit=limit * 2,  # Get more to ensure we have both sides
                order_by='-created_at'
            )
            
            # Convert to simple format for context
            history = []
            for message in reversed(messages):  # Reverse to get chronological order
                history.append({
                    'role': message['role'],
                    'content': message['content']
                })
            
            return history[-limit:]  # Return only the last N messages
            
        except Exception as e:
            logger.error("Error getting conversation history", 
                        conversation_id=conversation_id,
                        error=str(e))
            return []
    
    async def _get_conversation_messages(self, conversation_id: str) -> List[MessageResponse]:
        """Get all messages for a conversation."""
        try:
            from app.repositories.base import BaseRepository
            message_repo = BaseRepository(self.conversation_repo.db, 'messages')
            
            messages = await message_repo.find(
                filters={'conversation_id': conversation_id},
                order_by='created_at'
            )
            
            message_responses = []
            for message in messages:
                message_response = MessageResponse(
                    id=message['id'],
                    role=MessageRole(message['role']),
                    content=message['content'],
                    message_type=MessageType(message['message_type']),
                    metadata=message.get('metadata', {}),
                    created_at=message['created_at']
                )
                message_responses.append(message_response)
            
            return message_responses
            
        except Exception as e:
            logger.error("Error getting conversation messages", 
                        conversation_id=conversation_id,
                        error=str(e))
            return []
    
    async def _get_message_count(self, conversation_id: str) -> int:
        """Get total message count for a conversation."""
        try:
            from app.repositories.base import BaseRepository
            message_repo = BaseRepository(self.conversation_repo.db, 'messages')
            
            messages = await message_repo.find(
                filters={'conversation_id': conversation_id}
            )
            
            return len(messages)
            
        except Exception as e:
            logger.error("Error getting message count", 
                        conversation_id=conversation_id,
                        error=str(e))
            return 0
    
    async def _update_conversation_activity(self, conversation_id: str):
        """Update conversation's last activity timestamp."""
        try:
            await self.conversation_repo.update(conversation_id, {
                'updated_at': None  # Database will set current timestamp
            })
        except Exception as e:
            logger.warning("Failed to update conversation activity", 
                          conversation_id=conversation_id,
                          error=str(e))
    
    def _generate_conversation_title(self, conversation: Dict[str, Any]) -> str:
        """Generate a title for conversation based on type and creation time."""
        conv_type = conversation.get('conversation_type', 'general')
        created_at = conversation.get('created_at')
        
        type_names = {
            'document_qa': 'Consulta de documentos',
            'complaint_submission': 'Reporte de problema',
            'procedure_help': 'Ayuda con procedimientos',
            'general': 'Conversación'
        }
        
        type_name = type_names.get(conv_type, 'Conversación')
        
        if created_at:
            # Format: "Consulta de documentos - 15 Nov"
            try:
                from datetime import datetime
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    dt = created_at
                date_str = dt.strftime("%d %b")
                return f"{type_name} - {date_str}"
            except:
                pass
        
        return type_name
    
    async def health_check(self) -> Dict[str, Any]:
        """Check conversation service health."""
        try:
            # Check engine availability
            engine = self.engine_factory.get_engine("langgraph")
            engine_health = await engine.health_check()
            
            # Check repository connectivity
            repo_health = await self.conversation_repo.health_check()
            
            return {
                "status": "healthy",
                "engine_health": engine_health,
                "repository_health": repo_health,
                "document_service_available": self.document_service is not None
            }
            
        except Exception as e:
            logger.error("Conversation service health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }