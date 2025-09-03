"""
Email schemas for BeSunny.ai Python backend.
Defines data models for email processing and management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class GmailMessage(BaseModel):
    """Gmail message structure."""
    id: str = Field(..., description="Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")
    label_ids: List[str] = Field(default_factory=list, description="Gmail label IDs")
    snippet: str = Field(..., description="Message snippet")
    history_id: str = Field(..., description="Gmail history ID")
    internal_date: str = Field(..., description="Internal date")
    payload: 'GmailPayload' = Field(..., description="Message payload")
    size_estimate: int = Field(..., description="Size estimate")


class GmailPayload(BaseModel):
    """Gmail message payload."""
    part_id: str = Field(..., description="Part ID")
    mime_type: str = Field(..., description="MIME type")
    filename: Optional[str] = Field(None, description="Filename")
    headers: List['GmailHeader'] = Field(..., description="Message headers")
    body: Optional['GmailBody'] = Field(None, description="Message body")
    parts: Optional[List['GmailPayload']] = Field(..., description="Message parts")


class GmailHeader(BaseModel):
    """Gmail message header."""
    name: str = Field(..., description="Header name")
    value: str = Field(..., description="Header value")


class GmailBody(BaseModel):
    """Gmail message body."""
    attachment_id: Optional[str] = Field(None, description="Attachment ID")
    size: int = Field(..., description="Body size")
    data: Optional[str] = Field(None, description="Body data")


class GmailNotification(BaseModel):
    """Gmail push notification payload."""
    message: Dict[str, Any] = Field(..., description="Gmail message data")
    subscription: str = Field(..., description="Subscription identifier")


class GmailWebhookPayload(BaseModel):
    """Gmail webhook notification payload."""
    email_address: str = Field(..., description="Gmail address that received the notification")
    history_id: str = Field(..., description="Gmail history ID for the change")
    message_id: Optional[str] = Field(None, description="Gmail message ID if available")
    thread_id: Optional[str] = Field(None, description="Gmail thread ID if available")
    resource_state: str = Field("change", description="State of the resource")
    resource_uri: Optional[str] = Field(None, description="Resource URI")
    state: Optional[str] = Field(None, description="Webhook state")
    expiration: Optional[str] = Field(None, description="Webhook expiration time")


class GmailHistory(BaseModel):
    """Gmail history response."""
    history_id: str = Field(..., description="Gmail history ID")
    messages_added: Optional[List[Dict[str, Any]]] = Field(None, description="Messages added")
    messages_deleted: Optional[List[Dict[str, Any]]] = Field(None, description="Messages deleted")
    labels_added: Optional[List[Dict[str, Any]]] = Field(None, description="Labels added")
    labels_removed: Optional[List[Dict[str, Any]]] = Field(None, description="Labels removed")


class EmailProcessingResult(BaseModel):
    """Result of email processing."""
    success: bool = Field(..., description="Whether processing was successful")
    message: str = Field(..., description="Processing message")
    gmail_message_id: Optional[str] = Field(None, description="Gmail message ID")
    document_id: Optional[str] = Field(None, description="Created document ID")
    project_id: Optional[str] = Field(None, description="Assigned project ID")
    error_details: Optional[str] = Field(None, description="Error details if failed")


class EmailListResponse(BaseModel):
    """Response containing a list of emails."""
    emails: List[Dict[str, Any]] = Field(..., description="List of emails")
    total_count: int = Field(..., description="Total number of emails")
    limit: int = Field(..., description="Number of emails returned")
    offset: int = Field(..., description="Number of emails skipped")


class EmailStats(BaseModel):
    """Email statistics."""
    total_emails: int = Field(0, description="Total number of emails")
    processed_emails: int = Field(0, description="Number of processed emails")
    failed_emails: int = Field(0, description="Number of failed emails")
    emails_by_project: Dict[str, int] = Field(default_factory=dict, description="Email count by project")


class Email(BaseModel):
    """Basic email model."""
    id: str = Field(..., description="Email ID")
    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Email sender")
    recipients: List[str] = Field(..., description="Email recipients")
    content: str = Field(..., description="Email content")
    timestamp: datetime = Field(..., description="Email timestamp")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    status: str = Field(default="unprocessed", description="Processing status")


class VirtualEmail(BaseModel):
    """Virtual email model for project-specific email addresses."""
    id: str = Field(..., description="Virtual email ID")
    email_address: str = Field(..., description="Virtual email address")
    project_id: str = Field(..., description="Associated project ID")
    is_active: bool = Field(default=True, description="Whether the virtual email is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")


class ClassificationPayload(BaseModel):
    """Payload for document classification."""
    document_id: str = Field(..., description="Document ID to classify")
    user_id: str = Field(..., description="User ID who owns the document")
    type: str = Field(..., description="Document type (email, drive, etc.)")
    source: str = Field(..., description="Document source (gmail, drive, etc.)")
    title: str = Field(..., description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    received_at: Optional[str] = Field(None, description="Document received timestamp")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class DocumentCreate(BaseModel):
    """Document creation from email."""
    id: Optional[str] = Field(None, description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    source: str = Field("email", description="Document source")
    source_id: str = Field(..., description="Source ID (Gmail message ID)")
    author: Optional[str] = Field(None, description="Document author")
    received_at: Optional[str] = Field(None, description="Document received timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class Project(BaseModel):
    """Project information."""
    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class User(BaseModel):
    """User information."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: Optional[str] = Field(None, description="Username")


# Forward references for circular imports
GmailPayload.model_rebuild()
GmailBody.model_rebuild()
