# =======================
# app/providers/llm/openai_provider.py
# =======================
import asyncio
from typing import List, Optional, Dict, Any
import structlog

from openai import AsyncOpenAI
from app.interfaces.llm_provider import LLMProvider
from app.core.exceptions import AppException

logger = structlog.get_logger()


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.provider_name = "openai"
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text response."""
        try:
            response = await self.client.completions.create(
                model=kwargs.get('model', 'gpt-3.5-turbo-instruct'),
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error("OpenAI text generation failed", error=str(e))
            raise AppException(f"LLM error: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error("OpenAI embedding generation failed", error=str(e))
            raise AppException(f"LLM error: {str(e)}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Chat completion."""
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get('model', 'gpt-4o-mini'),
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI chat completion failed", error=str(e))
            raise AppException(f"LLM error: {str(e)}")
    
    def get_provider_name(self) -> str:
        """Get provider identifier."""
        return self.provider_name


