# =======================
# app/engines/langgraph/tools/llm_tool.py
# =======================
"""
LLM tool for integrating LLMProvider with LangGraph workflows.

This tool wraps the existing LLMProvider to provide standardized
text generation and intent classification functionality for LangGraph workflows.
"""

from typing import List, Dict, Any, Optional
import structlog
import json
import re

from app.interfaces.llm_provider import LLMProvider
from app.engines.langgraph.tools.base_tool import BaseTool, ToolExecutionError
from app.engines.langgraph.state.schemas import (
    ToolType, IntentClassificationResult, GeneralChatResult, IntentType
)

logger = structlog.get_logger()


class LLMTool(BaseTool):
    """
    Tool for LLM-based text generation and classification operations.
    
    This tool wraps the LLMProvider to provide intent classification,
    text generation, and other LLM capabilities within LangGraph workflows.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the LLM tool.
        
        Args:
            llm_provider: Instance of LLMProvider
        """
        super().__init__(llm_provider, "LLMTool")
        self.llm_provider = llm_provider
        
        # Cache for common responses to improve performance
        self._response_cache: Dict[str, str] = {}
        self._cache_max_size = 100
    
    @property
    def tool_type(self) -> ToolType:
        """Return the tool type for LLM operations."""
        return ToolType.LLM
    
    async def execute(self, **kwargs) -> GeneralChatResult:
        """
        Execute LLM generation operation.
        
        This method should not be called directly. Use specific methods
        like classify_intent() or generate_response() instead.
        
        Args:
            **kwargs: LLM parameters
            
        Returns:
            GeneralChatResult with generation results
        """
        # Delegate to generate_response as the primary operation
        return await self.generate_response(**kwargs)
    
    async def classify_intent(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentClassificationResult:
        """
        Classify user intent from message.
        
        Args:
            user_message: User's input message
            conversation_history: Optional previous conversation context
            
        Returns:
            IntentClassificationResult with classification details
            
        Raises:
            ToolExecutionError: If intent classification fails
        """
        try:
            if not user_message or not user_message.strip():
                raise ToolExecutionError(
                    "User message cannot be empty",
                    error_type="invalid_input",
                    details={'user_message': user_message}
                )
            
            message = user_message.strip()
            
            # Build classification prompt
            prompt = self._build_classification_prompt(message, conversation_history)
            
            logger.info("Classifying user intent",
                       message=message[:50],
                       has_history=bool(conversation_history))
            
            # Call LLM for classification
            response = await self.llm_provider.generate_text(
                prompt=prompt,
                max_tokens=50,
                temperature=0.1  # Low temperature for consistent classification
            )
            
            # Parse response
            intent, confidence, reasoning = self._parse_classification_response(response)
            
            logger.info("Intent classification completed",
                       message=message[:50],
                       intent=intent.value,
                       confidence=confidence)
            
            return IntentClassificationResult(
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
                model_used=self.llm_provider.get_provider_name()
            )
            
        except ToolExecutionError:
            raise
            
        except Exception as e:
            logger.error("Intent classification failed",
                        message=user_message[:50] if user_message else 'empty',
                        error=str(e),
                        exc_info=True)
            
            # Fallback to simple keyword-based classification
            fallback_intent = self._fallback_classification(user_message)
            
            logger.warning("Using fallback classification",
                          fallback_intent=fallback_intent.value)
            
            return IntentClassificationResult(
                intent=fallback_intent,
                confidence=0.3,  # Low confidence for fallback
                reasoning="Fallback classification due to LLM error",
                model_used="fallback"
            )
    
    async def generate_response(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        context: Optional[Dict[str, Any]] = None
    ) -> GeneralChatResult:
        """
        Generate text response using LLM.
        
        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            context: Optional context information
            
        Returns:
            GeneralChatResult with generated response
            
        Raises:
            ToolExecutionError: If text generation fails
        """
        try:
            if not prompt or not prompt.strip():
                raise ToolExecutionError(
                    "Prompt cannot be empty",
                    error_type="invalid_input",
                    details={'prompt': prompt}
                )
            
            if max_tokens <= 0 or max_tokens > 1000:
                raise ToolExecutionError(
                    "Max tokens must be between 1 and 1000",
                    error_type="invalid_input",
                    details={'max_tokens': max_tokens}
                )
            
            if not 0.0 <= temperature <= 1.0:
                raise ToolExecutionError(
                    "Temperature must be between 0.0 and 1.0",
                    error_type="invalid_input",
                    details={'temperature': temperature}
                )
            
            prompt_text = prompt.strip()
            
            # Check cache for common prompts
            cache_key = f"{prompt_text[:100]}_{max_tokens}_{temperature}"
            if cache_key in self._response_cache:
                logger.debug("Using cached response", cache_key=cache_key[:50])
                cached_response = self._response_cache[cache_key]
                
                return GeneralChatResult(
                    tool_type=ToolType.LLM,
                    success=True,
                    data={
                        'response': cached_response,
                        'prompt': prompt_text,
                        'cached': True
                    },
                    sources=[],
                    confidence=0.8,
                    model_used=self.llm_provider.get_provider_name(),
                    tokens_used=0,  # Cached response
                    temperature=temperature
                )
            
            logger.info("Generating LLM response",
                       prompt=prompt_text[:50],
                       max_tokens=max_tokens,
                       temperature=temperature)
            
            # Generate response using LLM
            response = await self.llm_provider.generate_text(
                prompt=prompt_text,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if not response or not response.strip():
                raise ToolExecutionError(
                    "LLM returned empty response",
                    error_type="empty_response",
                    details={'prompt': prompt_text[:100]}
                )
            
            response_text = response.strip()
            
            # Cache response if it's good quality
            if len(response_text) > 10 and len(self._response_cache) < self._cache_max_size:
                self._response_cache[cache_key] = response_text
            
            # Estimate tokens used (rough approximation)
            estimated_tokens = len(response_text.split()) + len(prompt_text.split())
            
            logger.info("LLM response generated",
                       prompt=prompt_text[:50],
                       response_length=len(response_text),
                       estimated_tokens=estimated_tokens)
            
            return GeneralChatResult(
                tool_type=ToolType.LLM,
                success=True,
                data={
                    'response': response_text,
                    'prompt': prompt_text,
                    'cached': False
                },
                sources=[],
                confidence=0.8,
                model_used=self.llm_provider.get_provider_name(),
                tokens_used=estimated_tokens,
                temperature=temperature
            )
            
        except ToolExecutionError:
            raise
            
        except Exception as e:
            logger.error("LLM response generation failed",
                        prompt=prompt[:50] if prompt else 'empty',
                        error=str(e),
                        exc_info=True)
            
            raise ToolExecutionError(
                f"LLM response generation failed: {str(e)}",
                error_type="service_error",
                details={
                    'prompt': prompt[:100] if prompt else None,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'exception_type': type(e).__name__
                },
                recoverable=True
            )
    
    async def generate_up_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GeneralChatResult:
        """
        Generate a response specifically for Universidad del Pacífico context.
        
        Args:
            user_message: User's message
            context: Optional conversation context
            
        Returns:
            GeneralChatResult with UP-specific response
        """
        try:
            # Build UP-specific prompt
            prompt = f"""Eres un asistente virtual útil para estudiantes de Universidad del Pacífico (UP) en Lima, Perú.

Responde de manera:
- Amigable y profesional
- Enfocada en estudiantes universitarios
- Específica para el contexto de UP cuando sea posible
- En español claro y natural

Estudiante: {user_message}

Respuesta del asistente de UP:"""
            
            return await self.generate_response(
                prompt=prompt,
                max_tokens=200,
                temperature=0.7,
                context=context
            )
            
        except Exception as e:
            logger.error("UP-specific response generation failed",
                        message=user_message[:50],
                        error=str(e))
            
            # Fallback to simple response
            fallback_response = f"Hola! Soy el asistente de UP. Vi tu mensaje sobre '{user_message[:50]}'. ¿En qué más puedo ayudarte?"
            
            return GeneralChatResult(
                tool_type=ToolType.LLM,
                success=True,
                data={
                    'response': fallback_response,
                    'prompt': user_message,
                    'fallback': True
                },
                sources=[],
                confidence=0.5,
                model_used="fallback"
            )
    
    def _build_classification_prompt(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build prompt for intent classification."""
        
        # Base classification prompt
        prompt = f"""Clasifica este mensaje de un estudiante de Universidad del Pacífico.

Categorías disponibles:
- "pregunta" - Pregunta sobre procedimientos, reglamentos, fechas límite, trámites de UP
- "queja" - Reporte de problemas, issues, quejas sobre servicios de la universidad  
- "conversacion" - Saludos, agradecimientos, conversación general

Mensaje del estudiante: "{message}"

Responde SOLO con el formato JSON:
{{"intent": "pregunta|queja|conversacion", "confidence": 0.0-1.0, "reasoning": "breve explicación"}}

Respuesta JSON:"""

        # Add conversation history if available
        if conversation_history and len(conversation_history) > 0:
            history_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')[:50]}"
                for msg in conversation_history[-3:]  # Last 3 messages
            ])
            
            prompt = f"""Contexto de conversación previa:
{history_text}

{prompt}"""
        
        return prompt
    
    def _parse_classification_response(self, response: str) -> tuple:
        """Parse LLM classification response."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                intent_str = parsed.get('intent', '').lower()
                confidence = float(parsed.get('confidence', 0.5))
                reasoning = parsed.get('reasoning', '')
                
                # Map intent string to enum
                intent_mapping = {
                    'pregunta': IntentType.QUESTION,
                    'queja': IntentType.COMPLAINT,
                    'conversacion': IntentType.GENERAL,
                    'general': IntentType.GENERAL
                }
                
                intent = intent_mapping.get(intent_str, IntentType.UNKNOWN)
                
                return intent, confidence, reasoning
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("Failed to parse classification response JSON",
                          response=response[:100],
                          error=str(e))
        
        # Fallback parsing - look for keywords
        response_lower = response.lower()
        
        if 'pregunta' in response_lower:
            return IntentType.QUESTION, 0.6, "Keyword-based classification"
        elif 'queja' in response_lower:
            return IntentType.COMPLAINT, 0.6, "Keyword-based classification"
        elif 'conversacion' in response_lower:
            return IntentType.GENERAL, 0.6, "Keyword-based classification"
        else:
            return IntentType.UNKNOWN, 0.3, "Unable to parse classification"
    
    def _fallback_classification(self, message: str) -> IntentType:
        """Simple keyword-based classification fallback."""
        if not message:
            return IntentType.UNKNOWN
        
        message_lower = message.lower()
        
        # Question keywords
        question_keywords = [
            'cómo', 'cuándo', 'dónde', 'qué', 'quién', 'por qué',
            'procedimiento', 'trámite', 'registro', 'matrícula'
        ]
        
        # Complaint keywords  
        complaint_keywords = [
            'problema', 'issue', 'error', 'falla', 'no funciona',
            'mal', 'deficiente', 'queja', 'reclamo'
        ]
        
        # Check for question patterns
        if any(keyword in message_lower for keyword in question_keywords):
            return IntentType.QUESTION
        
        # Check for complaint patterns
        if any(keyword in message_lower for keyword in complaint_keywords):
            return IntentType.COMPLAINT
        
        # Default to general conversation
        return IntentType.GENERAL
    
    async def health_check(self) -> bool:
        """
        Check if the LLM provider is healthy.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Test with a simple prompt
            test_response = await self.llm_provider.generate_text(
                prompt="Responde con 'OK' si puedes procesar este mensaje.",
                max_tokens=10,
                temperature=0.0
            )
            
            return bool(test_response and test_response.strip())
            
        except Exception as e:
            logger.warning("LLM provider health check failed", error=str(e))
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about this tool's capabilities.
        
        Returns:
            Dictionary describing tool capabilities
        """
        return {
            'tool_name': self.tool_name,
            'tool_type': self.tool_type.value,
            'operations': [
                'classify_intent',
                'generate_response',
                'generate_up_response'
            ],
            'supported_intents': [intent.value for intent in IntentType],
            'provider': self.llm_provider.get_provider_name(),
            'features': {
                'intent_classification': True,
                'text_generation': True,
                'conversation_context': True,
                'spanish_language': True,
                'up_specific_prompts': True,
                'response_caching': True
            },
            'parameters': {
                'max_tokens_range': '1-1000',
                'temperature_range': '0.0-1.0',
                'cache_size': self._cache_max_size
            }
        }
    
    def clear_cache(self):
        """Clear the response cache."""
        self._response_cache.clear()
        logger.info("LLM response cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self._response_cache),
            'cache_max_size': self._cache_max_size,
            'cache_keys': list(self._response_cache.keys())[:5]  # First 5 keys for debugging
        }