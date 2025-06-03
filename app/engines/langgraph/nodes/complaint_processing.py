# =======================
# app/engines/langgraph/nodes/complaint_processing.py
# =======================
"""
Complaint processing node for LangGraph workflows.

Simple node that processes complaints using ComplaintTool.
Follows KISS principle - one job, do it well.
"""

import structlog

from app.engines.langgraph.nodes.base_node import BaseNode
from app.engines.langgraph.state.conversation_state import ConversationState, StateManager

logger = structlog.get_logger()


class ComplaintProcessingNode(BaseNode):
    """
    Processes user complaints and submits them.
    
    Simple responsibility:
    1. Take user message (complaint)
    2. Call ComplaintTool to submit complaint
    3. Update state with submission result
    
    That's it. KISS.
    """
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """
        Process complaint and update state with submission result.
        
        Args:
            state: Current conversation state
            
        Returns:
            State updated with complaint submission result
        """
        self._log_start(state)
        
        try:
            # Get user message and info
            user_message = state.get('user_message', '')
            user_id = state.get('user_id')
            conversation_id = state.get('conversation_id')
            
            if not user_message:
                # No message to process as complaint
                StateManager.update_tool_result(
                    state,
                    tool_type="complaint",
                    tool_result={'error': 'No complaint message provided'},
                    success=False
                )
                self._log_complete(state, success=False)
                return state
            
            # Get complaint tool
            complaint_tool = self.tools.get('complaint')
            if not complaint_tool:
                # No complaint tool available
                StateManager.update_tool_result(
                    state,
                    tool_type="complaint",
                    tool_result={'error': 'Complaint processing not available'},
                    success=False
                )
                self._log_complete(state, success=False)
                return state
            
            # Submit complaint using tool (quick submission from chat)
            submission_result = await complaint_tool.submit_quick_complaint(
                user_message=user_message,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # Update state with submission result
            if submission_result.success:
                # Complaint submitted successfully
                StateManager.update_tool_result(
                    state,
                    tool_type="complaint",
                    tool_result={
                        'type': 'complaint_submitted',
                        'complaint_id': submission_result.complaint_id,
                        'short_id': submission_result.data.get('short_id'),
                        'title': submission_result.title,
                        'category': submission_result.category
                    },
                    success=True
                )
            else:
                # Complaint submission failed
                StateManager.update_tool_result(
                    state,
                    tool_type="complaint",
                    tool_result={
                        'type': 'complaint_failed',
                        'error': submission_result.error_message or 'Unknown error'
                    },
                    success=False
                )
            
            self._log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Complaint processing failed: {str(e)}"
            self._log_error(state, error_msg)
            
            # Update state with error
            StateManager.update_tool_result(
                state,
                tool_type="complaint",
                tool_result={'error': error_msg},
                success=False
            )
            StateManager.add_error(state, "complaint_processing_error", error_msg)
            
            return state