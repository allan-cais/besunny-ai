"""
Data schemas for BeSunny.ai Python backend.
Defines Pydantic models for API requests and responses.
"""

from .email import *
from .document import *
from .project import *
from .classification import *
from .user import *

__all__ = [
    # Email schemas
    "GmailMessage",
    "EmailProcessingResult",
    "ClassificationPayload",
    
    # Document schemas
    "DocumentCreate",
    "DocumentResponse",
    "DocumentUpdate",
    
    # Project schemas
    "Project",
    "ProjectCreate",
    "ProjectResponse",
    
    # Classification schemas
    "ClassificationResult",
    "ProcessingJob",
    
    # User schemas
    "User",
    "UserCreate",
    "UserResponse",
]
