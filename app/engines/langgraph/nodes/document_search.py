# =======================
# app/engines/langgraph/nodes/document_search.py - SIMPLE VERSION
# =======================
"""
Document search node for LangGraph workflows.

Simple node that searches documents using DocumentTool.
Follows KISS principle - one job, do it well: RETRIEVAL ONLY.
"""

import structlog

from app.engines.langgraph.nodes.base_node import BaseNode
from app.engines.langgraph.state.conversation_state import ConversationState, StateManager

logger = structlog.get_logger()


class DocumentSearchNode(BaseNode):
    """
    Searches documents for relevant content.
    
    Simple responsibility:
    1. Take user message (question)
    2. Call DocumentTool to search
    3. Return raw search results
    
    That's it. KISS - answer generation happens elsewhere.
    """
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """
        Search documents and return raw results.
        
        Args:
            state: Current conversation state
            
        Returns:
            State updated with raw search results
        """
        self._log_start(state)
        
        try:
            # Get user message for search
            user_message = state.get('user_message', '')
            
            if not user_message:
                StateManager.update_tool_result(
                    state,
                    tool_type="document",
                    tool_result={'error': 'No search query provided'},
                    success=False
                )
                self._log_complete(state, success=False)
                return state
            
            # Get document tool
            document_tool = self.tools.get('document')
            if not document_tool:
                StateManager.update_tool_result(
                    state,
                    tool_type="document", 
                    tool_result={'error': 'Document search not available'},
                    success=False
                )
                self._log_complete(state, success=False)
                return state
            
            # Search documents using tool
            search_result = await document_tool.search_documents(
                query=user_message,
                limit=3,  # Keep it simple - top 3 results
                similarity_threshold=0.6
            )
            
            # Update state with RAW search results (no answer generation here)
            if search_result.success and search_result.data.get('chunks'):
                chunks = search_result.data['chunks']
                
                StateManager.update_tool_result(
                    state,
                    tool_type="document",
                    tool_result={
                        'type': 'document_search',
                        'query': user_message,
                        'chunks': chunks,  # Raw chunks for answer generation
                        'chunks_found': len(chunks),
                        'best_similarity': search_result.best_similarity
                    },
                    success=True,
                    sources=search_result.sources
                )
            else:
                # No relevant documents found
                StateManager.update_tool_result(
                    state,
                    tool_type="document",
                    tool_result={
                        'type': 'no_documents_found',
                        'query': user_message,
                        'message': 'No documents found'
                    },
                    success=False
                )
            
            self._log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Document search failed: {str(e)}"
            self._log_error(state, error_msg)
            
            StateManager.update_tool_result(
                state,
                tool_type="document",
                tool_result={'error': error_msg},
                success=False
            )
            StateManager.add_error(state, "document_search_error", error_msg)
            
            return state