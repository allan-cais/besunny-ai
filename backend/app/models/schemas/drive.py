"""
Google Drive service schemas for BeSunny.ai Python backend.
Defines data models for Drive operations and webhook handling.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DriveFile(BaseModel):
    """Google Drive file metadata."""
    id: str = Field(..., description="Google Drive file ID")
    name: str = Field(..., description="File name")
    mime_type: str = Field(..., description="MIME type of the file")
    size: Optional[str] = Field(None, description="File size in bytes")
    modified_time: str = Field(..., description="Last modification time")
    parents: List[str] = Field(default_factory=list, description="Parent folder IDs")
    web_view_link: Optional[str] = Field(None, description="Web view link for the file")


class DriveFileWatch(BaseModel):
    """Google Drive file watch configuration."""
    id: str = Field(..., description="Watch ID")
    file_id: str = Field(..., description="Google Drive file ID being watched")
    channel_id: str = Field(..., description="Channel ID for the watch")
    resource_id: str = Field(..., description="Resource ID for the watch")
    expiration: str = Field(..., description="Watch expiration time")
    project_id: str = Field(..., description="Project ID associated with the file")
    is_active: bool = Field(True, description="Whether the watch is active")
    last_poll_at: Optional[datetime] = Field(None, description="Last time the watch was polled")
    last_webhook_received: Optional[datetime] = Field(None, description="Last webhook received time")
    webhook_failures: int = Field(0, description="Number of webhook failures")
    created_at: datetime = Field(default_factory=datetime.now, description="Watch creation time")


class DriveWebhookPayload(BaseModel):
    """Google Drive webhook notification payload."""
    file_id: str = Field(..., description="Google Drive file ID")
    channel_id: str = Field(..., description="Channel ID for the webhook")
    resource_id: str = Field(..., description="Resource ID for the webhook")
    resource_state: str = Field(..., description="State of the resource (change, trash, etc.)")
    resource_uri: Optional[str] = Field(None, description="Resource URI")
    state: Optional[str] = Field(None, description="Webhook state")
    expiration: Optional[str] = Field(None, description="Webhook expiration time")


class DriveFileChange(BaseModel):
    """Google Drive file change notification."""
    file_id: str = Field(..., description="Google Drive file ID")
    change_type: str = Field(..., description="Type of change (modify, delete, etc.)")
    timestamp: datetime = Field(..., description="When the change occurred")
    file_metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")


class DriveWatchRequest(BaseModel):
    """Request to set up a file watch."""
    file_id: str = Field(..., description="Google Drive file ID to watch")
    project_id: str = Field(..., description="Project ID to associate with the file")
    user_id: str = Field(..., description="User ID setting up the watch")


class DriveWatchResponse(BaseModel):
    """Response from setting up a file watch."""
    success: bool = Field(..., description="Whether the watch was set up successfully")
    watch_id: Optional[str] = Field(None, description="Watch ID if successful")
    message: str = Field(..., description="Response message")


class DriveFileListResponse(BaseModel):
    """Response containing a list of Drive files."""
    files: List[DriveFile] = Field(..., description="List of Drive files")
    total_count: int = Field(..., description="Total number of files")
    next_page_token: Optional[str] = Field(None, description="Next page token for pagination")


class DriveWebhookLog(BaseModel):
    """Log entry for Drive webhook processing."""
    id: str = Field(..., description="Log entry ID")
    file_id: str = Field(..., description="Google Drive file ID")
    channel_id: str = Field(..., description="Channel ID")
    resource_id: str = Field(..., description="Resource ID")
    resource_state: str = Field(..., description="Resource state")
    webhook_received_at: datetime = Field(..., description="When webhook was received")
    n8n_webhook_sent: bool = Field(False, description="Whether webhook was sent to N8N")
    n8n_webhook_sent_at: Optional[datetime] = Field(None, description="When webhook was sent to N8N")
    n8n_webhook_response: Optional[str] = Field(None, description="N8N webhook response")
    error_message: Optional[str] = Field(None, description="Error message if any")
    created_at: datetime = Field(default_factory=datetime.now, description="Log entry creation time")


class DriveSyncStatus(BaseModel):
    """Drive synchronization status for a user."""
    user_id: str = Field(..., description="User ID")
    service_type: str = Field("drive", description="Service type")
    last_sync_at: Optional[datetime] = Field(None, description="Last sync time")
    sync_frequency: str = Field("normal", description="Sync frequency")
    change_frequency: str = Field("medium", description="Change frequency")
    is_active: bool = Field(True, description="Whether sync is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Status creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Status update time")
