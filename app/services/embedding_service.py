# =======================
# app/services/embedding_service.py
# =======================
from typing import List
import structlog

from app.interfaces.llm_provider import LLMProvider
from app.core.exceptions import AppException

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, provider: LLMProvider, model: str = "text-embedding-ada-002"):
        self.provider = provider
        self.model = model
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_texts([text])
        return embeddings[0]
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            return await self.provider.generate_embeddings(texts)
        except Exception as e:
            logger.error("Error generating embeddings", error=str(e))
            raise AppException(f"Failed to generate embeddings: {str(e)}")


