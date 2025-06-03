# =======================
# app/engines/langgraph/state/schemas.py
# =======================
"""
Pydantic schemas for LangGraph state validation and serialization.

This module provides strongly-typed schemas for all data structures
used in the LangGraph workflow, ensuring data integrity and providing
clear API contracts between workflow components.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import structlog

logger = structlog.get_logger()


class IntentType(str, Enum):
    """Supported intent types for conversation classification."""
    QUESTION = "pregunta"          # Document-related questions
    COMPLAINT = "queja"            # Problem reports or complaints
    GENERAL = "conversacion"       # General conversation/greetings
    UNKNOWN = "desconocido"        # Unclassifiable input


class ToolType(str, Enum):
    """Types of tools available for workflow execution."""
    DOCUMENT = "document"          # Document search tool
    COMPLAINT = "complaint"        # Complaint submission tool
    LLM = "llm"                   # Direct LLM interaction tool


class ProcessingStep(str, Enum):
    """Workflow processing steps for tracking progress."""
    INITIALIZED = "initialized"
    INTENT_CLASSIFIED = "intent_classified"
    TOOL_EXECUTING = "tool_executing"
    TOOL_EXECUTED = "tool_executed"
    RESPONSE_FORMATTING = "response_formatting"
    RESPONSE_FORMATTED = "response_formatted"
    COMPLETED = "completed"
    FAILED = "failed"


class IntentClassificationResult(BaseModel):
    """Result of intent classification operation."""
    
    intent: IntentType = Field(..., description="Classified intent type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    reasoning: Optional[str] = Field(None, description="Human-readable reasoning for classification")
    
    # Metadata
    model_used: Optional[str] = Field(None, description="LLM model used for classification")
    processing_time: Optional[float] = Field(None, description="Time taken for classification")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is a valid probability."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolResult(BaseModel):
    """Base result model for tool execution."""
    
    tool_type: ToolType = Field(..., description="Type of tool that was executed")
    success: bool = Field(..., description="Whether tool execution succeeded")
    data: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific result data")
    sources: List[str] = Field(default_factory=list, description="Source documents or references")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Result confidence score")
    
    # Error information
    error_type: Optional[str] = Field(None, description="Error type if execution failed")
    error_message: Optional[str] = Field(None, description="Human-readable error message")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    # Metadata
    execution_time: Optional[float] = Field(None, description="Tool execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is a valid probability."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    @classmethod
    def success_result(
        cls,
        tool_type: ToolType,
        data: Dict[str, Any],
        sources: Optional[List[str]] = None,
        confidence: float = 1.0
    ) -> 'ToolResult':
        """Create a successful tool result."""
        return cls(
            tool_type=tool_type,
            success=True,
            data=data,
            sources=sources or [],
            confidence=confidence
        )
    
    @classmethod
    def error_result(
        cls,
        tool_type: ToolType,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> 'ToolResult':
        """Create a failed tool result."""
        return cls(
            tool_type=tool_type,
            success=False,
            data={},
            sources=[],
            confidence=0.0,
            error_type=error_type,
            error_message=error_message,
            error_details=error_details or {}
        )


class DocumentSearchResult(ToolResult):
    """Specialized result for document search operations."""
    
    tool_type: Literal[ToolType.DOCUMENT] = Field(default=ToolType.DOCUMENT)
    
    # Document-specific fields
    query: Optional[str] = Field(None, description="Original search query")
    chunks_found: int = Field(default=0, description="Number of document chunks found")
    best_similarity: float = Field(default=0.0, description="Highest similarity score")
    documents_searched: int = Field(default=0, description="Number of documents searched")
    
    @validator('data')
    def validate_document_data(cls, v):
        """Validate document search result data structure."""
        if 'content' not in v and 'chunks' not in v:
            logger.warning("Document search result missing content or chunks")
        return v


class ComplaintSubmissionResult(ToolResult):
    """Specialized result for complaint submission operations."""
    
    tool_type: Literal[ToolType.COMPLAINT] = Field(default=ToolType.COMPLAINT)
    
    # Complaint-specific fields
    complaint_id: Optional[str] = Field(None, description="Generated complaint ID")
    title: Optional[str] = Field(None, description="Complaint title")
    category: Optional[str] = Field(None, description="Auto-assigned complaint category")
    priority: Optional[str] = Field(None, description="Auto-assigned priority level")
    
    @validator('data')
    def validate_complaint_data(cls, v):
        """Validate complaint submission result data structure."""
        if 'id' not in v:
            logger.warning("Complaint submission result missing complaint ID")
        return v


class GeneralChatResult(ToolResult):
    """Specialized result for general chat/LLM operations."""
    
    tool_type: Literal[ToolType.LLM] = Field(default=ToolType.LLM)
    
    # LLM-specific fields
    model_used: Optional[str] = Field(None, description="LLM model used for generation")
    tokens_used: Optional[int] = Field(None, description="Number of tokens consumed")
    temperature: Optional[float] = Field(None, description="Temperature setting used")
    
    @validator('data')
    def validate_chat_data(cls, v):
        """Validate general chat result data structure."""
        if 'response' not in v and 'message' not in v:
            logger.warning("General chat result missing response or message")
        return v


class WorkflowError(BaseModel):
    """Error information for workflow failures."""
    
    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Human-readable error message")
    processing_step: ProcessingStep = Field(..., description="Step where error occurred")
    
    # Error context
    user_message: Optional[str] = Field(None, description="Original user message that caused error")
    intent: Optional[IntentType] = Field(None, description="Intent that was being processed")
    tool_type: Optional[ToolType] = Field(None, description="Tool that failed")
    
    # Technical details
    exception_type: Optional[str] = Field(None, description="Python exception type")
    stack_trace: Optional[str] = Field(None, description="Stack trace for debugging")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Additional error context")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recoverable: bool = Field(default=True, description="Whether error is recoverable")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationMetrics(BaseModel):
    """Metrics for conversation processing performance."""
    
    # Timing metrics
    total_processing_time: float = Field(..., description="Total time for entire workflow")
    classification_time: Optional[float] = Field(None, description="Time for intent classification")
    tool_execution_time: Optional[float] = Field(None, description="Time for tool execution")
    formatting_time: Optional[float] = Field(None, description="Time for response formatting")
    
    # Quality metrics
    intent_confidence: float = Field(default=0.0, description="Intent classification confidence")
    response_confidence: float = Field(default=0.0, description="Final response confidence")
    sources_found: int = Field(default=0, description="Number of sources found")
    
    # Workflow metrics
    processing_step: ProcessingStep = Field(..., description="Final processing step reached")
    success: bool = Field(..., description="Whether workflow completed successfully")
    retries: int = Field(default=0, description="Number of retries attempted")
    
    # User context
    user_id: str = Field(..., description="User who initiated the conversation")
    conversation_id: Optional[str] = Field(None, description="Conversation session ID")
    message_length: int = Field(..., description="Length of user message")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    engine_version: Optional[str] = Field(None, description="LangGraph engine version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Type unions for flexible result handling
AnyToolResult = Union[DocumentSearchResult, ComplaintSubmissionResult, GeneralChatResult, ToolResult]

# Export schemas for external use
__all__ = [
    # Enums
    'IntentType',
    'ToolType', 
    'ProcessingStep',
    
    # Result models
    'IntentClassificationResult',
    'ToolResult',
    'DocumentSearchResult',
    'ComplaintSubmissionResult', 
    'GeneralChatResult',
    
    # Error and metrics
    'WorkflowError',
    'ConversationMetrics',
    
    # Type unions
    'AnyToolResult'
]