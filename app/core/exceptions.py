# =======================
# app/core/exceptions.py
# =======================
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class UnauthorizedException(AppException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class ConversationEngineException(AppException):
    """Conversation engine error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class DocumentProcessingException(AppException):
    """Document processing error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

