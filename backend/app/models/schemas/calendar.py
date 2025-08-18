"""
Google Calendar service schemas for BeSunny.ai Python backend.
Defines data models for Calendar operations and webhook handling.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """Google Calendar event."""
    id: str = Field(..., description="Calendar event ID")
    summary: str = Field(..., description="Event summary/title")
    description: str = Field("", description="Event description")
    start_time: str = Field(..., description="Event start time")
    end_time: str = Field(..., description="Event end time")
    attendees: List[Dict[str, Any]] = Field(default_factory=list, description="Event attendees")
    meeting_url: Optional[str] = Field(None, description="Meeting URL (e.g., Google Meet)")
    created: Optional[str] = Field(None, description="Event creation time")
    updated: Optional[str] = Field(None, description="Event last update time")


class CalendarWebhook(BaseModel):
    """Google Calendar webhook configuration."""
    id: str = Field(..., description="Webhook ID")
    user_id: str = Field(..., description="User ID")
    google_calendar_id: str = Field(..., description="Google Calendar ID")
    webhook_id: str = Field(..., description="Webhook ID from Google")
    resource_id: str = Field(..., description="Resource ID from Google")
    sync_token: Optional[str] = Field(None, description="Sync token for incremental sync")
    expiration_time: str = Field(..., description="Webhook expiration time")
    is_active: bool = Field(True, description="Whether the webhook is active")
    last_poll_at: Optional[datetime] = Field(None, description="Last time the webhook was polled")
    last_webhook_received: Optional[datetime] = Field(None, description="Last webhook received time")
    created_at: datetime = Field(default_factory=datetime.now, description="Webhook creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Webhook update time")


class CalendarWebhookPayload(BaseModel):
    """Google Calendar webhook notification payload."""
    webhook_id: str = Field(..., description="Webhook ID")
    event_id: str = Field(..., description="Calendar event ID")
    resource_state: str = Field(..., description="State of the resource (change, trash, etc.)")
    resource_uri: Optional[str] = Field(None, description="Resource URI")
    state: Optional[str] = Field(None, description="Webhook state")
    expiration: Optional[str] = Field(None, description="Webhook expiration time")


class Meeting(BaseModel):
    """Meeting record from calendar events."""
    id: str = Field(..., description="Meeting ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Meeting title")
    description: str = Field("", description="Meeting description")
    start_time: str = Field(..., description="Meeting start time")
    end_time: str = Field(..., description="Meeting end time")
    meeting_url: Optional[str] = Field(None, description="Meeting URL")
    google_calendar_event_id: str = Field(..., description="Google Calendar event ID")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    attendee_bot_id: Optional[str] = Field(None, description="Attendee bot ID")
    bot_name: str = Field("Sunny AI Notetaker", description="Bot name")
    bot_status: str = Field("pending", description="Bot status")
    event_status: str = Field("needsAction", description="Event status")
    bot_configuration: Optional[Dict[str, Any]] = Field(None, description="Bot configuration")
    bot_deployment_method: str = Field("manual", description="Bot deployment method")
    bot_chat_message: str = Field("Hi, I'm here to transcribe this meeting!", description="Bot chat message")
    auto_bot_notification_sent: bool = Field(False, description="Whether auto bot notification was sent")
    auto_scheduled_via_email: bool = Field(False, description="Whether auto scheduled via email")
    virtual_email_attendee: Optional[str] = Field(None, description="Virtual email attendee")
    transcript: Optional[str] = Field(None, description="Meeting transcript")
    transcript_url: Optional[str] = Field(None, description="Transcript URL")
    transcript_audio_url: Optional[str] = Field(None, description="Transcript audio URL")
    transcript_recording_url: Optional[str] = Field(None, description="Transcript recording URL")
    transcript_summary: Optional[str] = Field(None, description="Transcript summary")
    transcript_duration_seconds: Optional[int] = Field(None, description="Transcript duration in seconds")
    transcript_language: str = Field("en-US", description="Transcript language")
    transcript_metadata: Optional[Dict[str, Any]] = Field(None, description="Transcript metadata")
    transcript_participants: Optional[Dict[str, Any]] = Field(None, description="Transcript participants")
    transcript_speakers: Optional[Dict[str, Any]] = Field(None, description="Transcript speakers")
    transcript_segments: Optional[Dict[str, Any]] = Field(None, description="Transcript segments")
    transcript_retrieved_at: Optional[datetime] = Field(None, description="When transcript was retrieved")
    last_polled_at: Optional[datetime] = Field(None, description="Last poll time")
    next_poll_time: Optional[datetime] = Field(None, description="Next poll time")
    created_at: datetime = Field(default_factory=datetime.now, description="Meeting creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Meeting update time")


class MeetingBot(BaseModel):
    """Meeting bot configuration."""
    id: str = Field(..., description="Bot ID")
    name: str = Field(..., description="Bot name")
    description: str = Field("", description="Bot description")
    avatar_url: Optional[str] = Field(None, description="Bot avatar URL")
    provider: str = Field(..., description="Bot provider")
    provider_bot_id: str = Field(..., description="Provider bot ID")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Bot settings")
    is_active: bool = Field(True, description="Whether the bot is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Bot creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Bot update time")
    user_id: str = Field(..., description="User ID who owns the bot")


class CalendarSyncRequest(BaseModel):
    """Request to sync calendar events."""
    user_id: str = Field(..., description="User ID to sync")
    calendar_id: str = Field("primary", description="Calendar ID to sync")
    sync_range_days: int = Field(30, description="Number of days to sync")


class CalendarSyncResponse(BaseModel):
    """Response from calendar sync operation."""
    success: bool = Field(..., description="Whether sync was successful")
    events_synced: int = Field(..., description="Number of events synced")
    message: str = Field(..., description="Response message")


class CalendarWebhookRequest(BaseModel):
    """Request to set up a calendar webhook."""
    user_id: str = Field(..., description="User ID setting up the webhook")
    calendar_id: str = Field("primary", description="Calendar ID to watch")


class CalendarWebhookResponse(BaseModel):
    """Response from setting up a calendar webhook."""
    success: bool = Field(..., description="Whether webhook was set up successfully")
    webhook_id: Optional[str] = Field(None, description="Webhook ID if successful")
    message: str = Field(..., description="Response message")


class MeetingListResponse(BaseModel):
    """Response containing a list of meetings."""
    meetings: List[Meeting] = Field(..., description="List of meetings")
    total_count: int = Field(..., description="Total number of meetings")
    next_page_token: Optional[str] = Field(None, description="Next page token for pagination")


class MeetingBotRequest(BaseModel):
    """Request to schedule a meeting bot."""
    meeting_id: str = Field(..., description="Meeting ID to schedule bot for")
    bot_config: Dict[str, Any] = Field(..., description="Bot configuration")


class MeetingBotResponse(BaseModel):
    """Response from scheduling a meeting bot."""
    success: bool = Field(..., description="Whether bot was scheduled successfully")
    message: str = Field(..., description="Response message")


class CalendarSyncLog(BaseModel):
    """Log entry for calendar sync operations."""
    id: str = Field(..., description="Log entry ID")
    user_id: str = Field(..., description="User ID")
    sync_type: str = Field(..., description="Sync type")
    status: str = Field(..., description="Sync status")
    sync_range_start: Optional[datetime] = Field(None, description="Sync range start")
    sync_range_end: Optional[datetime] = Field(None, description="Sync range end")
    events_processed: int = Field(0, description="Number of events processed")
    meetings_created: int = Field(0, description="Number of meetings created")
    meetings_updated: int = Field(0, description="Number of meetings updated")
    meetings_deleted: int = Field(0, description="Number of meetings deleted")
    duration_ms: Optional[int] = Field(None, description="Sync duration in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if any")
    created_at: datetime = Field(default_factory=datetime.now, description="Log entry creation time")
