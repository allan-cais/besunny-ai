"""
Email processing service for BeSunny.ai Python backend.
Handles email ingestion, classification, and processing.
"""

from .email_service import EmailProcessingService
from .gmail_polling_service import GmailPollingService as GmailService
from .gmail_polling_service import GmailPollingService
from .gmail_polling_cron import GmailPollingCronService
from .gmail_watch_service import GmailWatchService

__all__ = [
    "EmailProcessingService",
    "GmailService",
    "GmailPollingService",
    "GmailPollingCronService",
    "GmailWatchService",
]
