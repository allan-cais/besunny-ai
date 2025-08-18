"""
Meeting schemas for BeSunny.ai Python backend.
Defines data models for meeting management and intelligence.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Meeting(BaseModel):
    """Basic meeting model."""
    id: str = Field(..., description="Meeting ID")
    title: str = Field(..., description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    start_time: datetime = Field(..., description="Meeting start time")
    end_time: datetime = Field(..., description="Meeting end time")
    attendees: List[str] = Field(default_factory=list, description="Meeting attendees")
    organizer: str = Field(..., description="Meeting organizer")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    status: str = Field(default="scheduled", description="Meeting status")
    location: Optional[str] = Field(None, description="Meeting location")
    meeting_url: Optional[str] = Field(None, description="Meeting URL for virtual meetings")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


class MeetingIntelligence(BaseModel):
    """Meeting intelligence analysis result."""
    meeting_id: str = Field(..., description="Meeting ID")
    summary: str = Field(..., description="Meeting summary")
    action_items: List[str] = Field(default_factory=list, description="Action items from meeting")
    key_decisions: List[str] = Field(default_factory=list, description="Key decisions made")
    participants_summary: Dict[str, str] = Field(default_factory=dict, description="Participant contributions")
    sentiment_score: float = Field(..., description="Overall meeting sentiment score")
    topics_discussed: List[str] = Field(default_factory=list, description="Topics discussed")
    next_steps: List[str] = Field(default_factory=list, description="Next steps identified")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class MeetingSchedule(BaseModel):
    """Meeting schedule information."""
    user_id: str = Field(..., description="User ID")
    calendar_id: str = Field(..., description="Calendar ID")
    available_slots: List[Dict[str, Any]] = Field(default_factory=list, description="Available time slots")
    busy_times: List[Dict[str, Any]] = Field(default_factory=list, description="Busy time periods")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Scheduling preferences")
    timezone: str = Field(default="UTC", description="User timezone")


class MeetingBot(BaseModel):
    """Meeting bot configuration."""
    id: str = Field(..., description="Bot ID")
    name: str = Field(..., description="Bot name")
    description: str = Field(..., description="Bot description")
    capabilities: List[str] = Field(default_factory=list, description="Bot capabilities")
    is_active: bool = Field(default=True, description="Whether the bot is active")
    project_id: str = Field(..., description="Associated project ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
