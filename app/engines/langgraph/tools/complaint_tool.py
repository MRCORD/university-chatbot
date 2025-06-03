# =======================
# app/engines/langgraph/tools/complaint_tool.py
# =======================
"""
Complaint tool for integrating ComplaintService with LangGraph workflows.

This tool wraps the existing ComplaintService to provide standardized
complaint submission and processing functionality for LangGraph workflows.
"""

from typing import Optional, Dict, Any
import structlog

from app.services.complaint_service import ComplaintService
from app.models.complaint import (
    ComplaintSubmissionRequest, ComplaintCategory, ComplaintPriority, ComplaintStatus
)
from app.engines.langgraph.tools.base_tool import BaseTool, ToolExecutionError
from app.engines.langgraph.state.schemas import ToolType, ComplaintSubmissionResult

logger = structlog.get_logger()


class ComplaintTool(BaseTool):
    """
    Tool for complaint submission and processing operations.
    
    This tool wraps the ComplaintService to provide complaint handling
    capabilities within LangGraph workflows, with standardized
    error handling and result formatting.
    """
    
    def __init__(self, complaint_service: ComplaintService):
        """
        Initialize the complaint tool.
        
        Args:
            complaint_service: Instance of ComplaintService
        """
        super().__init__(complaint_service, "ComplaintTool")
        self.complaint_service = complaint_service
    
    @property
    def tool_type(self) -> ToolType:
        """Return the tool type for complaint operations."""
        return ToolType.COMPLAINT
    
    async def execute(self, **kwargs) -> ComplaintSubmissionResult:
        """
        Execute complaint submission operation.
        
        This method should not be called directly. Use submit_complaint()
        or other specific methods instead.
        
        Args:
            **kwargs: Complaint parameters
            
        Returns:
            ComplaintSubmissionResult with submission results
        """
        # Delegate to submit_complaint as the primary operation
        return await self.submit_complaint(**kwargs)
    
    async def submit_complaint(
        self,
        title: str,
        description: str,
        user_id: Optional[str] = None,
        category: Optional[ComplaintCategory] = None,
        is_anonymous: bool = True,
        conversation_id: Optional[str] = None
    ) -> ComplaintSubmissionResult:
        """
        Submit a new complaint.
        
        Args:
            title: Brief title for the complaint
            description: Detailed description of the issue
            user_id: Optional user ID (required if not anonymous)
            category: Optional complaint category (auto-detected if not provided)
            is_anonymous: Whether to submit anonymously (default: True)
            conversation_id: Optional conversation context
            
        Returns:
            ComplaintSubmissionResult with submission details
            
        Raises:
            ToolExecutionError: If complaint submission fails
        """
        try:
            # Validate input parameters
            if not title or not title.strip():
                raise ToolExecutionError(
                    "Complaint title cannot be empty",
                    error_type="invalid_input",
                    details={'title': title}
                )
            
            if not description or not description.strip():
                raise ToolExecutionError(
                    "Complaint description cannot be empty",
                    error_type="invalid_input",
                    details={'description': description[:100]}
                )
            
            if not is_anonymous and not user_id:
                raise ToolExecutionError(
                    "User ID is required for non-anonymous complaints",
                    error_type="invalid_input",
                    details={'is_anonymous': is_anonymous, 'user_id': user_id}
                )
            
            # Auto-generate title if too generic
            title = title.strip()
            if len(title) < 5 or title.lower() in ['problema', 'issue', 'error', 'queja']:
                title = self._generate_title_from_description(description.strip())
            
            # Auto-detect category if not provided
            if not category:
                category = self._detect_category(description.strip())
            
            logger.info("Submitting complaint",
                       title=title[:50],
                       description_length=len(description),
                       category=category.value,
                       is_anonymous=is_anonymous,
                       user_id=user_id)
            
            # Create complaint submission request
            complaint_request = ComplaintSubmissionRequest(
                title=title,
                description=description.strip(),
                category=category,
                is_anonymous=is_anonymous,
                user_id=user_id if not is_anonymous else None,
                conversation_id=conversation_id
            )
            
            # Submit complaint using ComplaintService
            complaint_response = await self.complaint_service.submit_complaint(complaint_request)
            
            # Create result data
            result_data = {
                'id': complaint_response.id,
                'title': complaint_response.title,
                'category': complaint_response.category.value,
                'priority': complaint_response.priority.value,
                'status': complaint_response.status.value,
                'is_anonymous': complaint_response.is_anonymous,
                'created_at': complaint_response.created_at.isoformat() if complaint_response.created_at else None,
                'short_id': complaint_response.id[:8] if complaint_response.id else None
            }
            
            logger.info("Complaint submitted successfully",
                       complaint_id=complaint_response.id,
                       title=title[:50],
                       category=category.value)
            
            return ComplaintSubmissionResult(
                tool_type=ToolType.COMPLAINT,
                success=True,
                data=result_data,
                sources=[],
                confidence=1.0,
                complaint_id=complaint_response.id,
                title=complaint_response.title,
                category=complaint_response.category.value,
                priority=complaint_response.priority.value
            )
            
        except ToolExecutionError:
            # Re-raise tool execution errors
            raise
            
        except Exception as e:
            logger.error("Complaint submission failed",
                        title=title[:50] if 'title' in locals() else 'unknown',
                        error=str(e),
                        exc_info=True)
            
            raise ToolExecutionError(
                f"Complaint submission failed: {str(e)}",
                error_type="service_error",
                details={
                    'title': title if 'title' in locals() else None,
                    'description_length': len(description) if 'description' in locals() else 0,
                    'exception_type': type(e).__name__
                },
                recoverable=True
            )
    
    async def submit_quick_complaint(
        self,
        user_message: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> ComplaintSubmissionResult:
        """
        Submit a complaint from a user message with auto-generated title and category.
        
        This is a convenience method for submitting complaints directly from
        chat messages without requiring structured input.
        
        Args:
            user_message: The user's complaint message
            user_id: Optional user ID
            conversation_id: Optional conversation context
            
        Returns:
            ComplaintSubmissionResult with submission details
        """
        try:
            if not user_message or not user_message.strip():
                raise ToolExecutionError(
                    "User message cannot be empty",
                    error_type="invalid_input",
                    details={'user_message': user_message}
                )
            
            message = user_message.strip()
            
            # Generate title from first sentence or first 50 characters
            title = self._generate_title_from_description(message)
            
            # Auto-detect category
            category = self._detect_category(message)
            
            logger.info("Submitting quick complaint from user message",
                       title=title[:50],
                       message_length=len(message),
                       category=category.value)
            
            # Use the standard submit_complaint method
            return await self.submit_complaint(
                title=title,
                description=message,
                user_id=user_id,
                category=category,
                is_anonymous=user_id is None,
                conversation_id=conversation_id
            )
            
        except ToolExecutionError:
            raise
            
        except Exception as e:
            logger.error("Quick complaint submission failed",
                        message_length=len(user_message) if user_message else 0,
                        error=str(e))
            
            raise ToolExecutionError(
                f"Quick complaint submission failed: {str(e)}",
                error_type="service_error",
                details={
                    'user_message_length': len(user_message) if user_message else 0,
                    'exception_type': type(e).__name__
                },
                recoverable=True
            )
    
    def _generate_title_from_description(self, description: str) -> str:
        """
        Generate a complaint title from the description.
        
        Args:
            description: Complaint description
            
        Returns:
            Generated title
        """
        # Take first sentence or first 50 characters
        sentences = description.split('.')
        first_sentence = sentences[0].strip()
        
        if len(first_sentence) > 5 and len(first_sentence) <= 100:
            return first_sentence
        elif len(description) <= 50:
            return description
        else:
            return description[:47] + "..."
    
    def _detect_category(self, text: str) -> ComplaintCategory:
        """
        Auto-detect complaint category from text content.
        
        Args:
            text: Complaint text
            
        Returns:
            Detected ComplaintCategory
        """
        text_lower = text.lower()
        
        # Academic-related keywords
        academic_keywords = [
            'califica', 'nota', 'examen', 'profesor', 'clase', 'curso', 
            'materia', 'horario', 'aula', 'laboratorio'
        ]
        
        # Administrative keywords
        admin_keywords = [
            'matricula', 'inscripción', 'registro', 'documento', 'certificado',
            'trámite', 'pago', 'beca', 'admisión'
        ]
        
        # Technology keywords
        tech_keywords = [
            'sistema', 'plataforma', 'internet', 'wifi', 'computadora',
            'aplicación', 'página', 'login', 'contraseña'
        ]
        
        # Infrastructure keywords
        infra_keywords = [
            'edificio', 'aula', 'baño', 'biblioteca', 'cafetería',
            'estacionamiento', 'ascensor', 'aire acondicionado'
        ]
        
        # Services keywords
        services_keywords = [
            'atención', 'servicio', 'personal', 'secretaría', 'ventanilla',
            'información', 'ayuda'
        ]
        
        # Financial keywords
        financial_keywords = [
            'pago', 'dinero', 'costo', 'precio', 'beca', 'financiamiento',
            'cuota', 'mensualidad'
        ]
        
        # Check which category has the most matches
        category_scores = {
            ComplaintCategory.ACADEMIC: sum(1 for keyword in academic_keywords if keyword in text_lower),
            ComplaintCategory.ADMINISTRATIVE: sum(1 for keyword in admin_keywords if keyword in text_lower),
            ComplaintCategory.TECHNOLOGY: sum(1 for keyword in tech_keywords if keyword in text_lower),
            ComplaintCategory.INFRASTRUCTURE: sum(1 for keyword in infra_keywords if keyword in text_lower),
            ComplaintCategory.SERVICES: sum(1 for keyword in services_keywords if keyword in text_lower),
            ComplaintCategory.FINANCIAL: sum(1 for keyword in financial_keywords if keyword in text_lower)
        }
        
        # Return category with highest score, default to OTHER
        best_category = max(category_scores, key=category_scores.get)
        
        if category_scores[best_category] > 0:
            logger.debug("Category detected",
                        category=best_category.value,
                        score=category_scores[best_category],
                        text_sample=text[:50])
            return best_category
        else:
            return ComplaintCategory.OTHER
    
    async def health_check(self) -> bool:
        """
        Check if the complaint service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Check if the service has required methods
            required_methods = ['submit_complaint', 'get_public_complaints']
            for method in required_methods:
                if not hasattr(self.complaint_service, method):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning("Complaint service health check failed", error=str(e))
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
                'submit_complaint',
                'submit_quick_complaint'
            ],
            'supported_categories': [cat.value for cat in ComplaintCategory],
            'features': {
                'anonymous_submission': True,
                'auto_category_detection': True,
                'auto_title_generation': True,
                'conversation_context': True
            },
            'validation': {
                'min_title_length': 5,
                'min_description_length': 10,
                'max_title_length': 200,
                'max_description_length': 2000
            }
        }