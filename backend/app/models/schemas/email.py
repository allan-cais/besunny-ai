"""
Email-related Pydantic schemas for BeSunny.ai Python backend.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class GmailMessagePayload(BaseModel):
    """Gmail message payload structure."""
    partId: str
    mimeType: str
    filename: Optional[str] = None
    headers: List[Dict[str, str]]
    body: Dict[str, Any]
    parts: Optional[List['GmailMessagePayload']] = None


class GmailMessage(BaseModel):
    """Gmail message structure."""
    id: str
    threadId: str
    labelIds: List[str]
    snippet: str
    historyId: str
    internalDate: str
    payload: GmailMessagePayload


class EmailProcessingResult(BaseModel):
    """Result of email processing."""
    success: bool
    message: str
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    gmail_message_id: Optional[str] = None
    classification_result: Optional['ClassificationResult'] = None


class ClassificationPayload(BaseModel):
    """Payload for document classification."""
    document_id: str
    user_id: str
    type: str  # 'email' or 'drive_notification'
    source: str
    title: str
    author: str
    received_at: str
    content: str
    metadata: Dict[str, Any]
    project_metadata: List[Dict[str, Any]]


# Update forward references
GmailMessagePayload.model_rebuild()
GmailMessage.model_rebuild()
EmailProcessingResult.model_rebuild()
ClassificationPayload.model_rebuild()
