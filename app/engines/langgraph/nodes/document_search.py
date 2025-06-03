# =======================
# app/engines/langgraph/nodes/document_search.py
# =======================
"""
Document search node for LangGraph workflows.

Simple node that searches documents using DocumentTool.
Follows KISS principle - one job, do it well.
"""

import structlog

from app.engines.langgraph.nodes.base_node import BaseNode
from app.engines.langgraph.state.conversation_state import ConversationState, StateManager

logger = structlog.get_logger()


class DocumentSearchNode(BaseNode):
    """
    Searches documents for answers to user questions.
    
    Simple responsibility:
    1. Take user message (question)
    2. Call DocumentTool to search
    3. Update state with search results
    
    That's it. KISS.
    """
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """
        Search documents and update state with results.
        
        Args:
            state: Current conversation state
            
        Returns:
            State updated with search results
        """
        self._log_start(state)
        
        try:
            # Get user message for search
            user_message = state.get('user_message', '')
            
            if not user_message:
                # No message to search
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
                # No document tool available
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
                limit=3,  # Keep it simple - just top 3 results
                similarity_threshold=0.7
            )
            
            # Update state with search results
            if search_result.success and search_result.data.get('content'):
                # Found relevant documents
                StateManager.update_tool_result(
                    state,
                    tool_type="document",
                    tool_result={
                        'type': 'document_search',
                        'content': search_result.data['content'],
                        'chunks_found': search_result.chunks_found,
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
                        'message': 'No encontré información específica sobre eso en los documentos de UP.'
                    },
                    success=False
                )
            
            self._log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Document search failed: {str(e)}"
            self._log_error(state, error_msg)
            
            # Update state with error
            StateManager.update_tool_result(
                state,
                tool_type="document",
                tool_result={'error': error_msg},
                success=False
            )
            StateManager.add_error(state, "document_search_error", error_msg)
            
            return state