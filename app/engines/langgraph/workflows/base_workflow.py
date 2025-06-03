# =======================
# app/engines/langgraph/workflows/base_workflow.py
# =======================
"""
Base workflow interface for LangGraph orchestration.

Simple base class that defines the workflow interface.
Follows KISS principle - minimal interface, no overengineering.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

try:
    from langgraph.graph import StateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    logger.warning("LangGraph not available - workflows will use fallback mode")
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


class BaseWorkflow(ABC):
    """
    Simple base class for all workflows.
    
    Design Principle: KISS
    - Minimal interface
    - Workflows orchestrate nodes
    - Simple, focused responsibility
    """
    
    def __init__(self, nodes: Dict[str, Any]):
        """
        Initialize workflow with node dependencies.
        
        Args:
            nodes: Dictionary of available workflow nodes
        """
        self.nodes = nodes
        self.workflow_name = self.__class__.__name__
        self._compiled_workflow = None
    
    @abstractmethod
    def build_workflow(self):
        """
        Build the workflow graph.
        
        This method defines how nodes are connected and routed.
        Each workflow implementation defines its own routing logic.
        
        Returns:
            Compiled workflow graph (or fallback handler)
        """
        pass
    
    def get_compiled_workflow(self):
        """
        Get the compiled workflow, building it if necessary.
        
        Returns:
            Compiled workflow ready for execution
        """
        if self._compiled_workflow is None:
            self._compiled_workflow = self.build_workflow()
        return self._compiled_workflow
    
    async def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow with initial state.
        
        Args:
            initial_state: Starting state for workflow
            
        Returns:
            Final state after workflow execution
        """
        workflow = self.get_compiled_workflow()
        
        if LANGGRAPH_AVAILABLE and hasattr(workflow, 'ainvoke'):
            # Use LangGraph execution
            return await workflow.ainvoke(initial_state)
        else:
            # Use fallback execution
            return await self._fallback_execution(initial_state)
    
    @abstractmethod
    async def _fallback_execution(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback execution when LangGraph is not available.
        
        Args:
            state: Current state
            
        Returns:
            Final state after manual execution
        """
        pass
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.workflow_name}(nodes={list(self.nodes.keys())})"