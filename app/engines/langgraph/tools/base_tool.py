# =======================
# app/engines/langgraph/tools/base_tool.py
# =======================
"""
Base tool interface for LangGraph service integration.

This module defines the abstract base class that all tools must implement,
ensuring consistent interfaces, error handling, and monitoring across
all service integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import structlog
from datetime import datetime

from app.engines.langgraph.state.schemas import ToolResult, ToolType

logger = structlog.get_logger()


class ToolExecutionError(Exception):
    """
    Custom exception for tool execution failures.
    
    This exception provides structured error information that can be
    used to create detailed ToolResult error responses.
    """
    
    def __init__(
        self,
        message: str,
        error_type: str = "execution_error",
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()


class BaseTool(ABC):
    """
    Abstract base class for all LangGraph tools.
    
    This class provides the common interface and utilities that all tools
    must implement. It handles timing, logging, error handling, and result
    standardization.
    """
    
    def __init__(self, service: Any, tool_name: str):
        """
        Initialize the tool with a service instance.
        
        Args:
            service: The underlying service instance (DocumentService, etc.)
            tool_name: Human-readable name for this tool
        """
        self.service = service
        self.tool_name = tool_name
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._last_execution_time = None
        
        logger.info("Tool initialized", tool_name=tool_name, service_type=type(service).__name__)
    
    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        """Return the ToolType for this tool."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        This method must be implemented by all concrete tools.
        It should handle the specific logic for interacting with
        the underlying service and return a ToolResult.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution results or error information
        """
        pass
    
    async def execute_with_monitoring(self, **kwargs) -> ToolResult:
        """
        Execute the tool with automatic timing and error handling.
        
        This wrapper method provides consistent monitoring, logging,
        and error handling for all tool executions.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution results or error information
        """
        start_time = time.time()
        execution_id = self._execution_count + 1
        
        logger.info("Tool execution started", 
                   tool_name=self.tool_name,
                   execution_id=execution_id,
                   parameters=self._sanitize_params(kwargs))
        
        try:
            # Execute the actual tool logic
            result = await self.execute(**kwargs)
            
            # Update execution metrics
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, success=True)
            
            # Add execution metadata to result
            if hasattr(result, 'execution_time'):
                result.execution_time = execution_time
            
            logger.info("Tool execution completed",
                       tool_name=self.tool_name,
                       execution_id=execution_id,
                       execution_time=execution_time,
                       success=result.success,
                       confidence=result.confidence)
            
            return result
            
        except ToolExecutionError as e:
            # Handle known tool errors
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, success=False)
            
            logger.error("Tool execution failed",
                        tool_name=self.tool_name,
                        execution_id=execution_id,
                        error_type=e.error_type,
                        error_message=e.message,
                        execution_time=execution_time,
                        recoverable=e.recoverable)
            
            return ToolResult.error_result(
                tool_type=self.tool_type,
                error_type=e.error_type,
                error_message=e.message,
                error_details={
                    **e.details,
                    'execution_time': execution_time,
                    'execution_id': execution_id,
                    'recoverable': e.recoverable
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, success=False)
            
            logger.error("Tool execution failed with unexpected error",
                        tool_name=self.tool_name,
                        execution_id=execution_id,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        execution_time=execution_time,
                        exc_info=True)
            
            return ToolResult.error_result(
                tool_type=self.tool_type,
                error_type="unexpected_error",
                error_message=f"Unexpected error in {self.tool_name}: {str(e)}",
                error_details={
                    'exception_type': type(e).__name__,
                    'execution_time': execution_time,
                    'execution_id': execution_id,
                    'recoverable': True  # Assume recoverable for unexpected errors
                }
            )
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the underlying service.
        
        Returns:
            True if the service is healthy, False otherwise
        """
        try:
            # Try to access the service to check if it's available
            if hasattr(self.service, 'health_check'):
                return await self.service.health_check()
            elif hasattr(self.service, 'ping'):
                return await self.service.ping()
            else:
                # Basic check - see if service is not None
                return self.service is not None
                
        except Exception as e:
            logger.warning("Tool health check failed",
                          tool_name=self.tool_name,
                          error=str(e))
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get execution metrics for this tool.
        
        Returns:
            Dictionary with execution statistics
        """
        return {
            'tool_name': self.tool_name,
            'tool_type': self.tool_type.value,
            'execution_count': self._execution_count,
            'total_execution_time': self._total_execution_time,
            'average_execution_time': (
                self._total_execution_time / self._execution_count 
                if self._execution_count > 0 else 0.0
            ),
            'last_execution_time': self._last_execution_time,
            'service_type': type(self.service).__name__
        }
    
    def reset_metrics(self):
        """Reset execution metrics."""
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._last_execution_time = None
        
        logger.info("Tool metrics reset", tool_name=self.tool_name)
    
    def _update_metrics(self, execution_time: float, success: bool):
        """Update internal execution metrics."""
        self._execution_count += 1
        self._total_execution_time += execution_time
        self._last_execution_time = execution_time
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize parameters for logging (remove sensitive data).
        
        Args:
            params: Raw parameters dictionary
            
        Returns:
            Sanitized parameters safe for logging
        """
        sanitized = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Log only first 100 characters of string values
                sanitized[key] = value[:100] + "..." if len(value) > 100 else value
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, (list, dict)):
                # Log only the type and length for complex structures
                sanitized[key] = f"{type(value).__name__}(len={len(value)})"
            else:
                sanitized[key] = f"{type(value).__name__}"
        
        return sanitized
    
    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}(name={self.tool_name}, service={type(self.service).__name__})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return (
            f"{self.__class__.__name__}("
            f"tool_name='{self.tool_name}', "
            f"tool_type={self.tool_type.value}, "
            f"service={type(self.service).__name__}, "
            f"executions={self._execution_count})"
        )


class ToolRegistry:
    """
    Registry for managing multiple tools.
    
    This class provides a centralized way to manage and access
    all available tools in the system.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, name: str, tool: BaseTool):
        """Register a tool with the registry."""
        self._tools[name] = tool
        logger.info("Tool registered", tool_name=name, tool_type=tool.tool_type.value)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_tools_by_type(self, tool_type: ToolType) -> Dict[str, BaseTool]:
        """Get all tools of a specific type."""
        return {
            name: tool for name, tool in self._tools.items()
            if tool.tool_type == tool_type
        }
    
    def list_tools(self) -> Dict[str, str]:
        """List all registered tools."""
        return {
            name: tool.tool_type.value 
            for name, tool in self._tools.items()
        }
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health checks on all registered tools."""
        results = {}
        for name, tool in self._tools.items():
            results[name] = await tool.health_check()
        return results
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all registered tools."""
        return {
            name: tool.get_metrics() 
            for name, tool in self._tools.items()
        }