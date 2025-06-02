# =======================
# app/interfaces/llm_provider.py
# =======================
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text response."""
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Chat completion."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider identifier."""
        pass