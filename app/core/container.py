"""Dependency injection container configuration."""

from dependency_injector import containers, providers

from app.core.config import settings
from app.providers.database.supabase_provider import SupabaseProvider
from app.providers.storage.supabase_storage_provider import SupabaseStorageProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.providers.llm.anthropic_provider import AnthropicProvider
from app.providers.llm.mistral_provider import MistralProvider
from app.engines.factory import ConversationEngineFactory
from app.repositories.user_repository import UserRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.vector_repository import VectorRepository
from app.services.user_service import UserService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.complaint_service import ComplaintService
from app.services.embedding_service import EmbeddingService


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    config.from_pydantic(settings)
    
    # Database providers
    database_provider = providers.Singleton(
        SupabaseProvider,
        url=config.SUPABASE_URL,
        key=config.SUPABASE_KEY
    )
    
    # Storage providers
    storage_provider = providers.Singleton(
        SupabaseStorageProvider,
        url=config.SUPABASE_URL,
        key=config.SUPABASE_KEY
    )
    
    # LLM providers
    openai_provider = providers.Singleton(
        OpenAIProvider,
        api_key=config.OPENAI_API_KEY
    )
    
    anthropic_provider = providers.Singleton(
        AnthropicProvider,
        api_key=config.ANTHROPIC_API_KEY
    )
    
    mistral_provider = providers.Singleton(
        MistralProvider,
        api_key=config.MISTRAL_API_KEY
    )
    
    # Conversation engine factory
    conversation_engine_factory = providers.Singleton(
        ConversationEngineFactory,
        openai_provider=openai_provider,
        anthropic_provider=anthropic_provider,
        mistral_provider=mistral_provider
    )
    
    # Repositories
    user_repository = providers.Singleton(
        UserRepository,
        database_provider=database_provider
    )
    
    conversation_repository = providers.Singleton(
        ConversationRepository,
        database_provider=database_provider
    )
    
    document_repository = providers.Singleton(
        DocumentRepository,
        database_provider=database_provider
    )
    
    complaint_repository = providers.Singleton(
        ComplaintRepository,
        database_provider=database_provider
    )
    
    vector_repository = providers.Singleton(
        VectorRepository,
        database_provider=database_provider
    )
    
    # Services
    embedding_service = providers.Singleton(
        EmbeddingService,
        openai_provider=openai_provider
    )
    
    user_service = providers.Singleton(
        UserService,
        user_repository=user_repository
    )
    
    conversation_service = providers.Singleton(
        ConversationService,
        conversation_repository=conversation_repository,
        conversation_engine_factory=conversation_engine_factory,
        vector_repository=vector_repository
    )
    
    document_service = providers.Singleton(
        DocumentService,
        document_repository=document_repository,
        storage_provider=storage_provider,
        embedding_service=embedding_service
    )
    
    complaint_service = providers.Singleton(
        ComplaintService,
        complaint_repository=complaint_repository
    )
