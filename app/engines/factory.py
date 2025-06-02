# =======================
# app/engines/factory.py
# =======================
from typing import Dict, Any
import structlog

from app.interfaces.conversation_engine import ConversationEngine
from app.core.config import Settings
from app.core.exceptions import AppException

logger = structlog.get_logger()


class ConversationEngineFactory:
    """Factory for creating conversation engines with real implementations."""
    
    def __init__(self, settings: Settings, container):
        self.settings = settings
        self.container = container
        self._engines: Dict[str, ConversationEngine] = {}
    
    def get_engine(self, engine_type: str) -> ConversationEngine:
        """Get conversation engine by type."""
        if engine_type not in self._engines:
            self._engines[engine_type] = self._create_engine(engine_type)
        return self._engines[engine_type]
    
    def _create_engine(self, engine_type: str) -> ConversationEngine:
        """Create engine instance with real implementations."""
        try:
            if engine_type == "langgraph":
                return self._create_langgraph_engine()
            elif engine_type == "mock":
                return self._create_mock_engine()
            else:
                logger.warning(f"Unknown engine type: {engine_type}, falling back to mock")
                return self._create_mock_engine()
                
        except Exception as e:
            logger.error(f"Failed to create {engine_type} engine", error=str(e))
            logger.info("Falling back to mock engine")
            return self._create_mock_engine()
    
    def _create_langgraph_engine(self) -> ConversationEngine:
        """Create real LangGraph engine with all dependencies."""
        try:
            # Import here to avoid circular imports and handle missing dependencies
            from app.engines.langgraph_engine import SimpleLangGraphEngine
            
            # Get required services from container
            document_service = self.container.get_document_service()
            complaint_service = self.container.get_complaint_service()
            llm_provider = self.container.get_llm_provider()
            
            # Validate dependencies
            if not document_service:
                raise AppException("DocumentService not available")
            if not complaint_service:
                raise AppException("ComplaintService not available") 
            if not llm_provider:
                raise AppException("LLM Provider not available")
            
            # Create LangGraph engine
            engine = SimpleLangGraphEngine(
                document_service=document_service,
                complaint_service=complaint_service,
                llm_provider=llm_provider
            )
            
            logger.info("LangGraph engine created successfully",
                       llm_provider=self.settings.LANGGRAPH_LLM_PROVIDER,
                       model=self.settings.LANGGRAPH_MODEL)
            
            return engine
            
        except ImportError as e:
            logger.warning("LangGraph dependencies not available", error=str(e))
            raise AppException("LangGraph not installed. Install with: pip install langgraph")
        except Exception as e:
            logger.error("Failed to create LangGraph engine", error=str(e))
            raise AppException(f"LangGraph engine creation failed: {str(e)}")
    
    def _create_mock_engine(self) -> ConversationEngine:
        """Create mock engine for testing/fallback."""
        from app.engines.base import MockConversationEngine
        
        logger.info("Created mock conversation engine")
        return MockConversationEngine()
    
    def _create_openai_engine(self) -> ConversationEngine:
        """Create direct OpenAI engine (future implementation)."""
        # This would be a simpler engine that uses OpenAI directly
        # without LangGraph for scenarios where LangGraph is overkill
        raise AppException("OpenAI direct engine not implemented yet")
    
    def _create_anthropic_engine(self) -> ConversationEngine:
        """Create direct Anthropic engine (future implementation)."""
        # This would use Claude directly for conversations
        raise AppException("Anthropic direct engine not implemented yet")
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engine types."""
        available = ["mock"]  # Always available
        
        try:
            # Check if LangGraph is available
            import langgraph
            available.append("langgraph")
        except ImportError:
            pass
        
        # Check for other dependencies as needed
        if self.settings.OPENAI_API_KEY:
            available.append("openai_direct")
        
        if self.settings.ANTHROPIC_API_KEY:
            available.append("anthropic_direct")
        
        return available
    
    def switch_engine(self, new_engine_type: str) -> bool:
        """Switch to a different engine type."""
        try:
            # Validate engine type is available
            available_engines = self.get_available_engines()
            if new_engine_type not in available_engines:
                logger.error(f"Engine type {new_engine_type} not available",
                           available=available_engines)
                return False
            
            # Clear cached engine to force recreation
            if new_engine_type in self._engines:
                del self._engines[new_engine_type]
            
            # Test creation
            test_engine = self._create_engine(new_engine_type)
            
            # Update settings (this would need proper settings persistence)
            # For now, just log the change
            logger.info(f"Switched conversation engine",
                       old_engine=self.settings.CONVERSATION_ENGINE,
                       new_engine=new_engine_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to {new_engine_type} engine", 
                        error=str(e))
            return False
    
    async def health_check_all_engines(self) -> Dict[str, Any]:
        """Check health of all available engines."""
        results = {}
        available_engines = self.get_available_engines()
        
        for engine_type in available_engines:
            try:
                engine = self.get_engine(engine_type)
                health = await engine.health_check()
                results[engine_type] = {
                    "status": "healthy",
                    "details": health
                }
            except Exception as e:
                results[engine_type] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return {
            "available_engines": available_engines,
            "current_engine": self.settings.CONVERSATION_ENGINE,
            "engine_health": results
        }