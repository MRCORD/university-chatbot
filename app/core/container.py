# =======================
# app/core/container.py
# =======================
from functools import lru_cache
from typing import Dict, Any

from app.core.config import get_settings
from app.providers.database.supabase_provider import SupabaseProvider
from app.providers.storage.supabase_storage_provider import SupabaseStorageProvider
from app.providers.llm.openai_provider import OpenAIProvider
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
from app.engines.factory import ConversationEngineFactory
from app.interfaces.database_provider import DatabaseProvider
from app.interfaces.storage_provider import StorageProvider


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        self.settings = get_settings()
        self._providers: Dict[str, Any] = {}
        self._repositories: Dict[str, Any] = {}
        self._services: Dict[str, Any] = {}
    
    # Providers
    def get_database_provider(self) -> DatabaseProvider:
        if 'database' not in self._providers:
            self._providers['database'] = SupabaseProvider(
                url=self.settings.SUPABASE_URL,
                key=self.settings.SUPABASE_SERVICE_ROLE_KEY
            )
        return self._providers['database']
    
    def get_storage_provider(self) -> StorageProvider:
        if 'storage' not in self._providers:
            db_provider = self.get_database_provider()
            self._providers['storage'] = SupabaseStorageProvider(db_provider.client)
        return self._providers['storage']
    
    def get_llm_provider(self):
        provider_type = self.settings.LANGGRAPH_LLM_PROVIDER
        if provider_type not in self._providers:
            if provider_type == "openai":
                self._providers[provider_type] = OpenAIProvider(
                    api_key=self.settings.OPENAI_API_KEY
                )
            # Add other providers as needed
        return self._providers[provider_type]
    
    # Repositories
    def get_user_repository(self) -> UserRepository:
        if 'user_repo' not in self._repositories:
            self._repositories['user_repo'] = UserRepository(
                self.get_database_provider()
            )
        return self._repositories['user_repo']
    
    def get_conversation_repository(self) -> ConversationRepository:
        if 'conversation_repo' not in self._repositories:
            self._repositories['conversation_repo'] = ConversationRepository(
                self.get_database_provider()
            )
        return self._repositories['conversation_repo']
    
    def get_document_repository(self) -> DocumentRepository:
        if 'document_repo' not in self._repositories:
            self._repositories['document_repo'] = DocumentRepository(
                self.get_database_provider()
            )
        return self._repositories['document_repo']
    
    def get_complaint_repository(self) -> ComplaintRepository:
        if 'complaint_repo' not in self._repositories:
            self._repositories['complaint_repo'] = ComplaintRepository(
                self.get_database_provider()
            )
        return self._repositories['complaint_repo']
    
    def get_vector_repository(self) -> VectorRepository:
        if 'vector_repo' not in self._repositories:
            self._repositories['vector_repo'] = VectorRepository(
                self.get_database_provider()
            )
        return self._repositories['vector_repo']
    
    # Services
    def get_embedding_service(self) -> EmbeddingService:
        if 'embedding_service' not in self._services:
            self._services['embedding_service'] = EmbeddingService(
                provider=self.get_llm_provider(),
                model=self.settings.EMBEDDING_MODEL
            )
        return self._services['embedding_service']
    
    def get_document_service(self) -> DocumentService:
        if 'document_service' not in self._services:
            self._services['document_service'] = DocumentService(
                document_repo=self.get_document_repository(),
                storage_provider=self.get_storage_provider(),
                embedding_service=self.get_embedding_service(),
                vector_repo=self.get_vector_repository()
            )
        return self._services['document_service']
    
    def get_conversation_service(self) -> ConversationService:
        if 'conversation_service' not in self._services:
            engine_factory = ConversationEngineFactory(self.settings, self)
            self._services['conversation_service'] = ConversationService(
                conversation_repo=self.get_conversation_repository(),
                engine_factory=engine_factory,
                document_service=self.get_document_service()
            )
        return self._services['conversation_service']
    
    def get_user_service(self) -> UserService:
        if 'user_service' not in self._services:
            self._services['user_service'] = UserService(
                self.get_user_repository()
            )
        return self._services['user_service']
    
    def get_complaint_service(self) -> ComplaintService:
        if 'complaint_service' not in self._services:
            self._services['complaint_service'] = ComplaintService(
                complaint_repo=self.get_complaint_repository(),
                user_repo=self.get_user_repository()
            )
        return self._services['complaint_service']


@lru_cache()
def get_container() -> Container:
    """Get cached container instance."""
    return Container()

