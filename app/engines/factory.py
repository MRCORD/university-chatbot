# =======================
# app/engines/factory.py - Updated for Modular LangGraph Engine
# =======================
"""
Factory for creating conversation engines with real modular LangGraph implementation.

Simple factory that creates the modular LangGraph engine with proper dependency injection.
Follows KISS principle - clean setup, clear dependencies.
"""

from typing import Dict, Any, List
import structlog

from app.interfaces.conversation_engine import ConversationEngine
from app.core.config import Settings
from app.core.exceptions import AppException

logger = structlog.get_logger()


class ConversationEngineFactory:
    """
    Simple factory for creating conversation engines.
    
    Now creates real modular LangGraph engines with full functionality.
    """
    
    def __init__(self, settings: Settings, container):
        self.settings = settings
        self.container = container
        self._engines: Dict[str, ConversationEngine] = {}
    
    def get_engine(self, engine_type: str) -> ConversationEngine:
        """
        Get conversation engine by type.
        
        Args:
            engine_type: Type of engine to create
            
        Returns:
            ConversationEngine instance
        """
        if engine_type not in self._engines:
            self._engines[engine_type] = self._create_engine(engine_type)
        return self._engines[engine_type]
    
    def _create_engine(self, engine_type: str) -> ConversationEngine:
        """
        Create engine instance with real implementations.
        
        Args:
            engine_type: Type of engine to create
            
        Returns:
            ConversationEngine instance
        """
        try:
            if engine_type == "langgraph":
                return self._create_modular_langgraph_engine()
            elif engine_type == "mock":
                return self._create_mock_engine()
            else:
                logger.warning(f"Unknown engine type: {engine_type}, falling back to mock")
                return self._create_mock_engine()
                
        except Exception as e:
            logger.error(f"Failed to create {engine_type} engine", error=str(e))
            logger.info("Falling back to mock engine")
            return self._create_mock_engine()
    
    def _create_modular_langgraph_engine(self) -> ConversationEngine:
        """
        Create real modular LangGraph engine with all dependencies.
        
        Returns:
            ModularLangGraphEngine instance
        """
        try:
            # Import the modular engine
            from app.engines.langgraph import ModularLangGraphEngine
            
            # Gather services from container
            services = self._get_services()
            providers = self._get_providers()
            
            # Validate critical dependencies
            self._validate_dependencies(services, providers)
            
            # Create modular engine
            engine = ModularLangGraphEngine(
                services=services,
                providers=providers
            )
            
            logger.info("Modular LangGraph engine created successfully",
                       services=list(services.keys()),
                       providers=list(providers.keys()),
                       llm_provider=self.settings.LANGGRAPH_LLM_PROVIDER,
                       model=self.settings.LANGGRAPH_MODEL)
            
            return engine
            
        except ImportError as e:
            logger.warning("LangGraph dependencies not available", error=str(e))
            raise AppException("LangGraph not installed. Install with: pip install langgraph langchain-core")
        
        except Exception as e:
            logger.error("Failed to create modular LangGraph engine", error=str(e))
            raise AppException(f"Modular LangGraph engine creation failed: {str(e)}")
    
    def _get_services(self) -> Dict[str, Any]:
        """
        Get all required services from container.
        
        Returns:
            Dictionary of service instances
        """
        services = {}
        
        try:
            # Get document service
            document_service = self.container.get_document_service()
            if document_service:
                services['document_service'] = document_service
                logger.debug("Document service loaded")
            else:
                logger.warning("Document service not available")
        except Exception as e:
            logger.warning("Failed to get document service", error=str(e))
        
        try:
            # Get complaint service
            complaint_service = self.container.get_complaint_service()
            if complaint_service:
                services['complaint_service'] = complaint_service
                logger.debug("Complaint service loaded")
            else:
                logger.warning("Complaint service not available")
        except Exception as e:
            logger.warning("Failed to get complaint service", error=str(e))
        
        return services
    
    def _get_providers(self) -> Dict[str, Any]:
        """
        Get all required providers from container.
        
        Returns:
            Dictionary of provider instances
        """
        providers = {}
        
        try:
            # Get LLM provider
            llm_provider = self.container.get_llm_provider()
            if llm_provider:
                providers['llm_provider'] = llm_provider
                logger.debug("LLM provider loaded", 
                           provider=llm_provider.get_provider_name())
            else:
                logger.warning("LLM provider not available")
        except Exception as e:
            logger.warning("Failed to get LLM provider", error=str(e))
        
        try:
            # Get embedding service (if needed)
            embedding_service = self.container.get_embedding_service()
            if embedding_service:
                providers['embedding_service'] = embedding_service
                logger.debug("Embedding service loaded")
        except Exception as e:
            logger.warning("Failed to get embedding service", error=str(e))
        
        return providers
    
    def _validate_dependencies(self, services: Dict[str, Any], providers: Dict[str, Any]):
        """
        Validate that critical dependencies are available.
        
        Args:
            services: Available services
            providers: Available providers
            
        Raises:
            AppException: If critical dependencies are missing
        """
        # Check for LLM provider (critical for intent classification)
        if 'llm_provider' not in providers:
            raise AppException("LLM provider is required but not available")
        
        # Warn about missing services (degraded functionality)
        if 'document_service' not in services:
            logger.warning("Document service not available - document search will be disabled")
        
        if 'complaint_service' not in services:
            logger.warning("Complaint service not available - complaint processing will be disabled")
        
        logger.info("Dependency validation completed",
                   services_available=list(services.keys()),
                   providers_available=list(providers.keys()))
    
    def _create_mock_engine(self) -> ConversationEngine:
        """
        Create mock engine for testing/fallback.
        
        Returns:
            MockConversationEngine instance
        """
        from app.engines.base import MockConversationEngine
        
        logger.info("Created mock conversation engine")
        return MockConversationEngine()
    
    def get_available_engines(self) -> List[str]:
        """
        Get list of available engine types.
        
        Returns:
            List of available engine type names
        """
        available = ["mock"]  # Always available
        
        try:
            # Check if LangGraph is available
            import langgraph
            available.append("langgraph")
        except ImportError:
            pass
        
        # Check for required services
        try:
            if self.container.get_llm_provider():
                logger.debug("LLM provider available for engines")
        except Exception:
            logger.warning("LLM provider not available - engine functionality will be limited")
        
        return available
    
    def switch_engine(self, new_engine_type: str) -> bool:
        """
        Switch to a different engine type.
        
        Args:
            new_engine_type: Engine type to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
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
            
            logger.info(f"Switched conversation engine",
                       old_engine=self.settings.CONVERSATION_ENGINE,
                       new_engine=new_engine_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to {new_engine_type} engine", 
                        error=str(e))
            return False
    
    async def health_check_all_engines(self) -> Dict[str, Any]:
        """
        Check health of all available engines.
        
        Returns:
            Dictionary with health status of all engines
        """
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
            "engine_health": results,
            "factory_info": {
                "cached_engines": list(self._engines.keys()),
                "settings": {
                    "llm_provider": self.settings.LANGGRAPH_LLM_PROVIDER,
                    "model": self.settings.LANGGRAPH_MODEL
                }
            }
        }
    
    def get_engine_info(self, engine_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific engine.
        
        Args:
            engine_type: Engine type to get info for
            
        Returns:
            Dictionary with engine information
        """
        try:
            engine = self.get_engine(engine_type)
            
            if hasattr(engine, '_get_metrics'):
                metrics = engine._get_metrics()
            else:
                metrics = {}
            
            return {
                "engine_type": engine_type,
                "engine_class": type(engine).__name__,
                "available": True,
                "metrics": metrics
            }
            
        except Exception as e:
            return {
                "engine_type": engine_type,
                "engine_class": "Unknown",
                "available": False,
                "error": str(e)
            }