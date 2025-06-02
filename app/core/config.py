# =======================
# app/core/config.py
# =======================
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "University Chatbot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    
    # Supabase
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anonymous key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase service role key")
    
    # Storage Buckets
    DOCUMENTS_BUCKET: str = Field(default="official-documents")
    UPLOADS_BUCKET: str = Field(default="user-uploads")
    PROCESSED_BUCKET: str = Field(default="processed-content")
    
    # AI Providers
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    MISTRAL_API_KEY: Optional[str] = Field(default=None, description="Mistral API key")
    
    # Conversation Engine
    CONVERSATION_ENGINE: str = Field(default="langgraph", description="Active conversation engine")
    LANGGRAPH_LLM_PROVIDER: str = Field(default="openai", description="LLM provider for LangGraph")
    LANGGRAPH_MODEL: str = Field(default="gpt-4o-mini", description="Model for LangGraph")
    
    # Vector Search
    EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002")
    VECTOR_SIMILARITY_THRESHOLD: float = Field(default=0.7)
    MAX_SEARCH_RESULTS: int = Field(default=10)
    CHUNK_SIZE: int = Field(default=1000, description="Text chunk size for embeddings")
    CHUNK_OVERLAP: int = Field(default=200, description="Overlap between chunks")
    
    # Feature Flags
    ENABLE_DOCUMENT_SEARCH: bool = Field(default=True)
    ENABLE_COMPLAINT_PROCESSING: bool = Field(default=True)
    ENABLE_REAL_TIME_UPDATES: bool = Field(default=True)
    
    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()

