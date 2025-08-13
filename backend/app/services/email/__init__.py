"""
Email processing service for BeSunny.ai Python backend.
Handles email ingestion, classification, and processing.
"""

from .email_service import EmailProcessingService
from .gmail_service import GmailService
from .virtual_email_service import VirtualEmailService

__all__ = [
    "EmailProcessingService",
    "GmailService", 
    "VirtualEmailService",
]
