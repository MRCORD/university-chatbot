# Provider-Agnostic Engine Architecture Replication Guide

## 🎯 Overview

This guide provides a step-by-step blueprint for replicating a **provider-agnostic conversational AI engine architecture** using **LangGraph** as the current implementation. The architecture is designed to be **vendor-independent**, **modular**, and **easily extensible**.

## 🏗️ Architecture Philosophy

### Core Principles
1. **Provider Agnosticism**: Any conversation engine can be swapped without changing business logic
2. **Interface-Driven Design**: All components implement well-defined contracts
3. **Dependency Injection**: Services and providers are injected, not hardcoded
4. **Single Responsibility**: Each component has one clear purpose
5. **Modular Structure**: Components can be developed, tested, and replaced independently

### Why This Matters
- **Future-Proof**: Easy adoption of new AI technologies
- **Vendor Independence**: No lock-in to specific providers
- **Maintainable**: Clear separation of concerns
- **Testable**: Mock any component for testing
- **Scalable**: Components can be scaled independently

## 📁 Directory Structure Blueprint

```
your-project/
├── app/
│   ├── engines/                    # 🎯 CORE: All conversation engines
│   │   ├── __init__.py
│   │   ├── base.py                 # Base classes and interfaces
│   │   ├── factory.py              # Engine factory (DI container)
│   │   └── langgraph/              # LangGraph implementation
│   │       ├── __init__.py
│   │       ├── engine.py           # Main LangGraph engine coordinator
│   │       ├── nodes/              # Workflow processing nodes
│   │       │   ├── __init__.py
│   │       │   ├── classification.py
│   │       │   ├── document_search.py
│   │       │   ├── response_formatting.py
│   │       │   └── [other_nodes].py
│   │       ├── state/              # State management
│   │       │   ├── __init__.py
│   │       │   ├── conversation_state.py
│   │       │   └── state_manager.py
│   │       ├── tools/              # Service integration tools
│   │       │   ├── __init__.py
│   │       │   ├── document_tools.py
│   │       │   ├── user_tools.py
│   │       │   └── [service]_tools.py
│   │       ├── utils/              # LangGraph-specific utilities
│   │       │   ├── __init__.py
│   │       │   └── helpers.py
│   │       └── workflows/          # Workflow orchestration
│   │           ├── __init__.py
│   │           ├── chat_workflow.py
│   │           └── base_workflow.py
│   ├── interfaces/                 # 🎯 CORE: Provider-agnostic contracts
│   │   ├── __init__.py
│   │   ├── conversation_engine.py  # Main engine interface
│   │   ├── query_types.py          # Query type definitions
│   │   └── response_models.py      # Response data models
│   ├── services/                   # 🎯 CORE: Business logic services
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   ├── user_service.py
│   │   └── [domain]_service.py
│   ├── providers/                  # 🎯 CORE: External service providers
│   │   ├── __init__.py
│   │   ├── llm/                    # LLM providers (OpenAI, Anthropic, etc.)
│   │   ├── database/               # Database providers
│   │   └── storage/                # Storage providers
│   └── models/                     # Data models
│       ├── __init__.py
│       └── [domain]_models.py
├── tests/
│   ├── unit/
│   │   ├── test_engines/
│   │   └── test_services/
│   └── integration/
│       └── test_workflows/
├── requirements.txt
└── pyproject.toml
```

## 🔧 Step-by-Step Implementation Guide

### Phase 1: Core Interfaces (Foundation)

#### 1.1 Create Base Interfaces

**File: `app/interfaces/conversation_engine.py`**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class QueryType(Enum):
    """Supported query types - extend as needed"""
    DOCUMENT_QA = "document_qa"
    GENERAL_INFO = "general_info"
    COMPLAINT = "complaint"
    PROCEDURE = "procedure"
    UNKNOWN = "unknown"

@dataclass
class ConversationContext:
    """User context and session information"""
    user_id: str
    session_id: str
    message: str
    history: list = None
    metadata: Dict[str, Any] = None

@dataclass
class ConversationResponse:
    """Standardized response format"""
    response: str
    query_type: QueryType
    confidence: float
    sources: list = None
    metadata: Dict[str, Any] = None
    suggestions: list = None

class ConversationEngine(ABC):
    """Provider-agnostic conversation engine interface"""
    
    @abstractmethod
    async def process_query(self, context: ConversationContext) -> ConversationResponse:
        """Main entry point for processing user messages"""
        pass
    
    @abstractmethod
    async def initialize_documents(self, document_paths: list) -> bool:
        """Initialize document knowledge base"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Engine health monitoring"""
        pass
```

**File: `app/interfaces/query_types.py`**
```python
from enum import Enum
from typing import Dict, Any

class QueryType(Enum):
    """Centralized query type definitions"""
    DOCUMENT_QA = "document_qa"
    GENERAL_INFO = "general_info"
    COMPLAINT = "complaint"
    PROCEDURE = "procedure"
    UNKNOWN = "unknown"

# Query type metadata for routing decisions
QUERY_TYPE_METADATA: Dict[QueryType, Dict[str, Any]] = {
    QueryType.DOCUMENT_QA: {
        "requires_search": True,
        "requires_llm": True,
        "priority": "high"
    },
    QueryType.COMPLAINT: {
        "requires_search": False,
        "requires_llm": True,
        "priority": "urgent"
    },
    QueryType.GENERAL_INFO: {
        "requires_search": False,
        "requires_llm": True,
        "priority": "normal"
    }
}
```

#### 1.2 Create Engine Factory

**File: `app/engines/factory.py`**
```python
from typing import Dict, Any, Optional
from app.interfaces.conversation_engine import ConversationEngine
from app.engines.base import MockConversationEngine

class ConversationEngineFactory:
    """Factory for creating conversation engines with dependency injection"""
    
    _engines: Dict[str, ConversationEngine] = {}
    
    @classmethod
    def create_engine(
        cls, 
        engine_type: str,
        services: Dict[str, Any],
        providers: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> ConversationEngine:
        """
        Create and configure a conversation engine
        
        Args:
            engine_type: Type of engine ('langgraph', 'langchain', 'mock')
            services: Business logic services (document, user, etc.)
            providers: External providers (LLM, database, etc.)
            config: Additional configuration
        """
        
        if engine_type in cls._engines:
            return cls._engines[engine_type]
        
        engine = cls._create_engine_instance(engine_type, services, providers, config)
        cls._engines[engine_type] = engine
        return engine
    
    @classmethod
    def _create_engine_instance(
        cls,
        engine_type: str,
        services: Dict[str, Any],
        providers: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> ConversationEngine:
        """Internal engine creation logic"""
        
        if engine_type == "langgraph":
            from app.engines.langgraph.engine import ModularLangGraphEngine
            return ModularLangGraphEngine(services, providers, config)
        
        elif engine_type == "mock":
            return MockConversationEngine()
        
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
    
    @classmethod
    def get_available_engines(cls) -> list:
        """Get list of available engine types"""
        return ["langgraph", "mock"]
```

#### 1.3 Create Base Classes

**File: `app/engines/base.py`**
```python
from app.interfaces.conversation_engine import (
    ConversationEngine, 
    ConversationContext, 
    ConversationResponse,
    QueryType
)
from typing import Dict, Any

class MockConversationEngine(ConversationEngine):
    """Mock implementation for testing and development"""
    
    async def process_query(self, context: ConversationContext) -> ConversationResponse:
        return ConversationResponse(
            response=f"Mock response to: {context.message}",
            query_type=QueryType.GENERAL_INFO,
            confidence=0.5,
            sources=[],
            metadata={"engine": "mock"}
        )
    
    async def initialize_documents(self, document_paths: list) -> bool:
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "engine": "mock"}
```

### Phase 2: LangGraph Implementation

#### 2.1 State Management

**File: `app/engines/langgraph/state/conversation_state.py`**
```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from app.interfaces.query_types import QueryType

@dataclass
class ConversationState:
    """Central state object that flows through LangGraph workflow"""
    
    # Input data
    user_id: str
    session_id: str
    message: str
    
    # Processing results
    query_type: Optional[QueryType] = None
    intent_confidence: float = 0.0
    retrieved_documents: List[Dict[str, Any]] = field(default_factory=list)
    context_summary: str = ""
    
    # Response data
    response: str = ""
    response_confidence: float = 0.0
    sources: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Metadata
    processing_steps: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step_name: str) -> None:
        """Track processing steps for debugging"""
        self.processing_steps.append(step_name)
    
    def add_error(self, error: str) -> None:
        """Track errors during processing"""
        self.errors.append(error)
```

**File: `app/engines/langgraph/state/state_manager.py`**
```python
from app.engines.langgraph.state.conversation_state import ConversationState
from app.interfaces.conversation_engine import ConversationContext

class StateManager:
    """Manages state initialization and transitions"""
    
    @staticmethod
    def initialize_state(context: ConversationContext) -> ConversationState:
        """Initialize state from conversation context"""
        return ConversationState(
            user_id=context.user_id,
            session_id=context.session_id,
            message=context.message,
            metadata=context.metadata or {}
        )
    
    @staticmethod
    def validate_state(state: ConversationState) -> bool:
        """Validate state consistency"""
        required_fields = ['user_id', 'session_id', 'message']
        return all(getattr(state, field) for field in required_fields)
```

#### 2.2 Workflow Nodes

**File: `app/engines/langgraph/nodes/classification.py`**
```python
from app.engines.langgraph.state.conversation_state import ConversationState
from app.interfaces.query_types import QueryType
from typing import Dict, Any

class ClassificationNode:
    """Analyzes user intent and determines query type"""
    
    def __init__(self, llm_provider: Any, config: Dict[str, Any] = None):
        self.llm_provider = llm_provider
        self.config = config or {}
    
    async def process(self, state: ConversationState) -> ConversationState:
        """Classify user intent"""
        state.add_step("classification")
        
        try:
            # Use LLM to classify intent
            classification_result = await self._classify_intent(state.message)
            
            state.query_type = classification_result["query_type"]
            state.intent_confidence = classification_result["confidence"]
            
        except Exception as e:
            state.add_error(f"Classification error: {str(e)}")
            state.query_type = QueryType.UNKNOWN
            state.intent_confidence = 0.0
        
        return state
    
    async def _classify_intent(self, message: str) -> Dict[str, Any]:
        """Internal classification logic"""
        # Implementation depends on your LLM provider
        # This is a simplified example
        
        prompt = f"""
        Classify the following user message into one of these categories:
        - document_qa: Questions about specific information
        - complaint: Problems or issues to report
        - general_info: General inquiries
        - procedure: How-to questions
        
        Message: {message}
        
        Return JSON with 'query_type' and 'confidence' (0-1).
        """
        
        # Call your LLM provider here
        # result = await self.llm_provider.generate(prompt)
        
        # Mock implementation for example
        return {
            "query_type": QueryType.DOCUMENT_QA,
            "confidence": 0.8
        }
```

**File: `app/engines/langgraph/nodes/document_search.py`**
```python
from app.engines.langgraph.state.conversation_state import ConversationState
from typing import Any, Dict

class DocumentSearchNode:
    """Searches documents for relevant information"""
    
    def __init__(self, document_service: Any, config: Dict[str, Any] = None):
        self.document_service = document_service
        self.config = config or {}
    
    async def process(self, state: ConversationState) -> ConversationState:
        """Search for relevant documents"""
        state.add_step("document_search")
        
        try:
            # Only search if this is a document-related query
            if state.query_type in [QueryType.DOCUMENT_QA, QueryType.PROCEDURE]:
                search_results = await self.document_service.search(
                    query=state.message,
                    limit=self.config.get("max_results", 5)
                )
                
                state.retrieved_documents = search_results
                state.context_summary = self._summarize_context(search_results)
            
        except Exception as e:
            state.add_error(f"Document search error: {str(e)}")
        
        return state
    
    def _summarize_context(self, documents: list) -> str:
        """Create summary of retrieved documents"""
        if not documents:
            return ""
        
        summaries = [doc.get("summary", doc.get("content", "")[:200]) for doc in documents]
        return "\n".join(summaries)
```

**File: `app/engines/langgraph/nodes/response_formatting.py`**
```python
from app.engines.langgraph.state.conversation_state import ConversationState
from typing import Any, Dict

class ResponseFormattingNode:
    """Formats final response using LLM"""
    
    def __init__(self, llm_provider: Any, config: Dict[str, Any] = None):
        self.llm_provider = llm_provider
        self.config = config or {}
    
    async def process(self, state: ConversationState) -> ConversationState:
        """Generate and format final response"""
        state.add_step("response_formatting")
        
        try:
            response_data = await self._generate_response(state)
            
            state.response = response_data["response"]
            state.response_confidence = response_data.get("confidence", 0.8)
            state.suggestions = response_data.get("suggestions", [])
            
        except Exception as e:
            state.add_error(f"Response formatting error: {str(e)}")
            state.response = "I apologize, but I encountered an error processing your request."
            state.response_confidence = 0.1
        
        return state
    
    async def _generate_response(self, state: ConversationState) -> Dict[str, Any]:
        """Generate response based on state"""
        
        prompt = self._build_prompt(state)
        
        # Call your LLM provider here
        # result = await self.llm_provider.generate(prompt)
        
        # Mock implementation
        return {
            "response": f"Based on the available information, here's my response to: {state.message}",
            "confidence": 0.8,
            "suggestions": ["Would you like more details?", "Any other questions?"]
        }
    
    def _build_prompt(self, state: ConversationState) -> str:
        """Build LLM prompt based on state"""
        
        prompt_parts = [
            f"User question: {state.message}",
            f"Query type: {state.query_type.value}",
        ]
        
        if state.retrieved_documents:
            prompt_parts.append(f"Relevant context: {state.context_summary}")
        
        prompt_parts.append("Generate a helpful, natural response.")
        
        return "\n".join(prompt_parts)
```

#### 2.3 Tools Integration

**File: `app/engines/langgraph/tools/document_tools.py`**
```python
from typing import Any, List, Dict

class DocumentTools:
    """Tools for document operations in LangGraph workflows"""
    
    def __init__(self, document_service: Any):
        self.document_service = document_service
    
    async def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        return await self.document_service.search(query=query, limit=limit)
    
    async def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve specific document"""
        return await self.document_service.get_by_id(doc_id)
    
    async def get_similar_documents(self, doc_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar documents"""
        return await self.document_service.find_similar(doc_id, limit)
```

#### 2.4 Workflow Orchestration

**File: `app/engines/langgraph/workflows/chat_workflow.py`**
```python
from typing import Dict, Any
from app.engines.langgraph.state.conversation_state import ConversationState
from app.interfaces.query_types import QueryType

class ChatWorkflow:
    """Main conversation workflow orchestrator"""
    
    def __init__(self, nodes: Dict[str, Any], config: Dict[str, Any] = None):
        self.nodes = nodes
        self.config = config or {}
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """Execute the complete workflow"""
        
        # Step 1: Classification
        state = await self.nodes["classification"].process(state)
        
        # Step 2: Conditional processing based on intent
        if state.query_type in [QueryType.DOCUMENT_QA, QueryType.PROCEDURE]:
            state = await self.nodes["document_search"].process(state)
        elif state.query_type == QueryType.COMPLAINT:
            state = await self.nodes["complaint_processing"].process(state)
        # Add more routing as needed
        
        # Step 3: Response formatting
        state = await self.nodes["response_formatting"].process(state)
        
        return state
    
    def get_workflow_graph(self) -> Dict[str, Any]:
        """Return workflow structure for visualization/debugging"""
        return {
            "nodes": list(self.nodes.keys()),
            "flow": [
                ("classification", "routing"),
                ("routing", "document_search"),
                ("routing", "complaint_processing"),
                ("document_search", "response_formatting"),
                ("complaint_processing", "response_formatting")
            ]
        }
```

#### 2.5 Main LangGraph Engine

**File: `app/engines/langgraph/engine.py`**
```python
from typing import Dict, Any
from app.interfaces.conversation_engine import (
    ConversationEngine, 
    ConversationContext, 
    ConversationResponse
)
from app.engines.langgraph.state.state_manager import StateManager
from app.engines.langgraph.workflows.chat_workflow import ChatWorkflow
from app.engines.langgraph.nodes.classification import ClassificationNode
from app.engines.langgraph.nodes.document_search import DocumentSearchNode
from app.engines.langgraph.nodes.response_formatting import ResponseFormattingNode

class ModularLangGraphEngine(ConversationEngine):
    """Main LangGraph-based conversation engine"""
    
    def __init__(self, services: Dict[str, Any], providers: Dict[str, Any], config: Dict[str, Any] = None):
        self.services = services
        self.providers = providers
        self.config = config or {}
        
        # Initialize components
        self.state_manager = StateManager()
        self.nodes = self._setup_nodes()
        self.workflow = self._setup_workflow()
    
    def _setup_nodes(self) -> Dict[str, Any]:
        """Initialize workflow nodes"""
        return {
            "classification": ClassificationNode(
                llm_provider=self.providers.get("llm"),
                config=self.config.get("classification", {})
            ),
            "document_search": DocumentSearchNode(
                document_service=self.services.get("document"),
                config=self.config.get("document_search", {})
            ),
            "response_formatting": ResponseFormattingNode(
                llm_provider=self.providers.get("llm"),
                config=self.config.get("response_formatting", {})
            )
        }
    
    def _setup_workflow(self) -> ChatWorkflow:
        """Initialize workflow orchestrator"""
        return ChatWorkflow(
            nodes=self.nodes,
            config=self.config.get("workflow", {})
        )
    
    async def process_query(self, context: ConversationContext) -> ConversationResponse:
        """Main query processing entry point"""
        
        # Initialize state
        state = self.state_manager.initialize_state(context)
        
        # Execute workflow
        final_state = await self.workflow.execute(state)
        
        # Convert state to response
        return ConversationResponse(
            response=final_state.response,
            query_type=final_state.query_type,
            confidence=final_state.response_confidence,
            sources=final_state.sources,
            metadata={
                "processing_steps": final_state.processing_steps,
                "errors": final_state.errors,
                **final_state.metadata
            },
            suggestions=final_state.suggestions
        )
    
    async def initialize_documents(self, document_paths: list) -> bool:
        """Initialize document knowledge base"""
        try:
            document_service = self.services.get("document")
            if document_service:
                return await document_service.initialize(document_paths)
            return False
        except Exception:
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Engine health monitoring"""
        health_status = {
            "engine": "langgraph",
            "status": "healthy",
            "components": {}
        }
        
        # Check each component
        for name, node in self.nodes.items():
            try:
                # Add health check method to nodes if needed
                health_status["components"][name] = "healthy"
            except Exception as e:
                health_status["components"][name] = f"error: {str(e)}"
                health_status["status"] = "degraded"
        
        return health_status
```

### Phase 3: Services and Providers

#### 3.1 Service Layer Example

**File: `app/services/document_service.py`**
```python
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class DocumentService(ABC):
    """Abstract document service interface"""
    
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def initialize(self, document_paths: List[str]) -> bool:
        pass

class VectorDocumentService(DocumentService):
    """Vector-based document service implementation"""
    
    def __init__(self, vector_provider: Any, embedding_provider: Any):
        self.vector_provider = vector_provider
        self.embedding_provider = embedding_provider
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents using vector similarity"""
        # Embed the query
        query_embedding = await self.embedding_provider.embed(query)
        
        # Search vector store
        results = await self.vector_provider.similarity_search(
            embedding=query_embedding,
            limit=limit
        )
        
        return results
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        return await self.vector_provider.get_document(doc_id)
    
    async def initialize(self, document_paths: List[str]) -> bool:
        """Initialize vector store with documents"""
        try:
            for path in document_paths:
                await self._process_document(path)
            return True
        except Exception:
            return False
    
    async def _process_document(self, path: str) -> None:
        """Process and store a single document"""
        # Load, chunk, embed, and store document
        pass
```

### Phase 4: Configuration and Deployment

#### 4.1 Configuration Setup

**File: `app/config/engine_config.py`**
```python
import os
from typing import Dict, Any

def get_engine_config() -> Dict[str, Any]:
    """Get engine configuration from environment"""
    return {
        "engine_type": os.getenv("ENGINE_TYPE", "langgraph"),
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "vector_store": os.getenv("VECTOR_STORE", "pinecone"),
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        
        # Engine-specific configs
        "langgraph": {
            "classification": {
                "confidence_threshold": float(os.getenv("CLASSIFICATION_THRESHOLD", "0.7"))
            },
            "document_search": {
                "max_results": int(os.getenv("MAX_SEARCH_RESULTS", "5"))
            },
            "workflow": {
                "timeout": int(os.getenv("WORKFLOW_TIMEOUT", "30"))
            }
        }
    }
```

#### 4.2 Main Application Integration

**File: `app/main.py`**
```python
from app.engines.factory import ConversationEngineFactory
from app.config.engine_config import get_engine_config
from app.interfaces.conversation_engine import ConversationContext

# Initialize services and providers (implement based on your needs)
services = {
    "document": VectorDocumentService(...),
    "user": UserService(...),
    # Add more services
}

providers = {
    "llm": OpenAIProvider(...),
    "vector": PineconeProvider(...),
    # Add more providers
}

# Get configuration
config = get_engine_config()

# Create engine
engine = ConversationEngineFactory.create_engine(
    engine_type=config["engine_type"],
    services=services,
    providers=providers,
    config=config
)

# Use the engine
async def process_message(user_id: str, message: str) -> str:
    context = ConversationContext(
        user_id=user_id,
        session_id=f"{user_id}_session",
        message=message
    )
    
    response = await engine.process_query(context)
    return response.response
```

## 🧪 Testing Strategy

### Unit Tests Structure

```
tests/
├── unit/
│   ├── test_engines/
│   │   ├── test_factory.py
│   │   ├── test_langgraph/
│   │   │   ├── test_nodes/
│   │   │   ├── test_state/
│   │   │   └── test_workflows/
│   └── test_services/
├── integration/
│   ├── test_workflows/
│   └── test_end_to_end/
└── mocks/
    ├── mock_services.py
    └── mock_providers.py
```

### Example Test

**File: `tests/unit/test_engines/test_factory.py`**
```python
import pytest
from app.engines.factory import ConversationEngineFactory

@pytest.mark.asyncio
async def test_create_mock_engine():
    """Test mock engine creation"""
    engine = ConversationEngineFactory.create_engine(
        engine_type="mock",
        services={},
        providers={}
    )
    
    health = await engine.health_check()
    assert health["status"] == "healthy"
    assert health["engine"] == "mock"
```

## 🚀 Extension Guide

### Adding a New Engine (e.g., LangChain)

1. **Create directory structure:**
   ```
   app/engines/langchain/
   ├── __init__.py
   ├── engine.py
   ├── chains/
   └── utils/
   ```

2. **Implement the interface:**
   ```python
   class LangChainEngine(ConversationEngine):
       # Implement all abstract methods
   ```

3. **Register in factory:**
   ```python
   # In factory.py
   elif engine_type == "langchain":
       from app.engines.langchain.engine import LangChainEngine
       return LangChainEngine(services, providers, config)
   ```

### Adding New Query Types

1. **Update enum:**
   ```python
   # In query_types.py
   class QueryType(Enum):
       # ... existing types
       NEW_TYPE = "new_type"
   ```

2. **Create processing node:**
   ```python
   # In nodes/new_type_processing.py
   class NewTypeProcessingNode:
       async def process(self, state: ConversationState) -> ConversationState:
           # Implement processing logic
   ```

3. **Update workflow routing:**
   ```python
   # In chat_workflow.py
   if state.query_type == QueryType.NEW_TYPE:
       state = await self.nodes["new_type_processing"].process(state)
   ```

## 📋 Implementation Checklist

### Phase 1: Foundation ✅
- [ ] Create `interfaces/` directory with base contracts
- [ ] Implement `ConversationEngine` interface
- [ ] Create `ConversationEngineFactory`
- [ ] Add mock implementation for testing

### Phase 2: LangGraph Engine ✅
- [ ] Create `engines/langgraph/` structure
- [ ] Implement state management
- [ ] Create workflow nodes (classification, search, formatting)
- [ ] Build workflow orchestrator
- [ ] Implement main engine class

### Phase 3: Services & Providers ✅
- [ ] Define service interfaces
- [ ] Implement provider-agnostic services
- [ ] Create provider implementations
- [ ] Add configuration management

## 🎯 Key Success Metrics

- **Provider Independence**: Can swap engines without changing business logic
- **Modularity**: Each component can be developed/tested independently
- **Extensibility**: New features can be added without breaking existing code
- **Maintainability**: Clear separation of concerns and well-defined interfaces
- **Testability**: Comprehensive test coverage with mock implementations

## 🤖 LLM Implementation Notes

When using this guide with an LLM assistant:

1. **Start with Phase 1** - Establish the foundation before building specific implementations
2. **Use the directory structure exactly** - This ensures consistency
3. **Implement interfaces first** - This enforces the provider-agnostic pattern
4. **Test each phase** - Ensure each component works before moving to the next
5. **Follow the naming conventions** - This maintains code readability
6. **Use dependency injection** - This is crucial for the agnostic architecture

This guide provides a complete blueprint for replicating a production-ready, provider-agnostic conversational AI engine with LangGraph as the current implementation. 