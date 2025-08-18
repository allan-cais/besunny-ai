"""
Core attendee service for BeSunny.ai Python backend.
Handles meeting bot management, transcript retrieval, and chat functionality.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.calendar import MeetingBot, MeetingBotRequest, MeetingBotResponse

logger = logging.getLogger(__name__)


class BotStatus(BaseModel):
    """Bot status information."""
    bot_id: str
    status: str
    meeting_id: str
    meeting_url: Optional[str]
    is_recording: bool
    is_paused: bool
    created_at: datetime
    updated_at: datetime


class TranscriptData(BaseModel):
    """Transcript information."""
    bot_id: str
    meeting_id: str
    transcript_text: str
    participants: List[str]
    duration_minutes: int
    created_at: datetime


class ChatMessage(BaseModel):
    """Chat message structure."""
    id: str
    bot_id: str
    message: str
    from_user: str
    to_user: str
    timestamp: datetime
    message_type: str = "text"


class ParticipantEvent(BaseModel):
    """Participant event information."""
    bot_id: str
    participant_id: str
    event_type: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class AttendeeService:
    """Core service for attendee and meeting bot operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.attendee_api_base_url = self.settings.attendee_api_base_url
        self.attendee_api_key = self.settings.master_attendee_api_key
        
        # HTTP client for external API calls
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.attendee_api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info("Attendee Service initialized")
    
    async def poll_all_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Poll all meetings for a user to get current status.
        
        Args:
            user_id: User ID to poll meetings for
            
        Returns:
            List of meeting status information
        """
        try:
            # Get user's active meeting bots
            bots = await self._get_user_meeting_bots(user_id)
            if not bots:
                logger.info(f"No active meeting bots found for user {user_id}")
                return []
            
            # Poll each bot for current status
            meeting_statuses = []
            for bot in bots:
                try:
                    status = await self.get_bot_status(bot['bot_id'])
                    if status:
                        meeting_statuses.append(status)
                except Exception as e:
                    logger.error(f"Failed to poll bot {bot['bot_id']}: {e}")
                    continue
            
            logger.info(f"Successfully polled {len(meeting_statuses)} meetings for user {user_id}")
            return meeting_statuses
            
        except Exception as e:
            logger.error(f"Failed to poll all meetings for user {user_id}: {e}")
            return []
    
    async def send_bot_to_meeting(self, options: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Send a bot to a meeting.
        
        Args:
            options: Bot configuration options
            user_id: User ID requesting the bot
            
        Returns:
            Bot deployment result
        """
        try:
            # Validate options
            required_fields = ['meeting_url', 'meeting_time', 'project_id']
            for field in required_fields:
                if field not in options:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create bot deployment request
            deployment_data = {
                "meeting_url": options['meeting_url'],
                "meeting_time": options['meeting_time'],
                "project_id": options['project_id'],
                "user_id": user_id,
                "bot_config": options.get('bot_config', {}),
                "recording_enabled": options.get('recording_enabled', True),
                "transcript_enabled": options.get('transcript_enabled', True)
            }
            
            # Call attendee API to deploy bot
            response = await self.http_client.post(
                f"{self.attendee_api_base_url}/deploy-bot",
                json=deployment_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Store bot information in database
            await self._store_meeting_bot(
                bot_id=result['bot_id'],
                user_id=user_id,
                project_id=options['project_id'],
                meeting_url=options['meeting_url'],
                meeting_time=options['meeting_time'],
                status='deployed'
            )
            
            logger.info(f"Bot deployed successfully for user {user_id}, bot ID: {result['bot_id']}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error deploying bot: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to deploy bot for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_bot_status(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a meeting bot.
        
        Args:
            bot_id: Bot ID to check status for
            
        Returns:
            Bot status information or None if failed
        """
        try:
            response = await self.http_client.get(
                f"{self.attendee_api_base_url}/bot-status/{bot_id}"
            )
            response.raise_for_status()
            
            status_data = response.json()
            
            # Update bot status in database
            await self._update_bot_status(bot_id, status_data)
            
            return status_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting bot status: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get bot status for {bot_id}: {e}")
            return None
    
    async def get_transcript(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transcript for a meeting bot.
        
        Args:
            bot_id: Bot ID to get transcript for
            
        Returns:
            Transcript data or None if failed
        """
        try:
            response = await self.http_client.get(
                f"{self.attendee_api_base_url}/transcript/{bot_id}"
            )
            response.raise_for_status()
            
            transcript_data = response.json()
            
            # Store transcript in database
            await self._store_transcript(bot_id, transcript_data)
            
            return transcript_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting transcript: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get transcript for bot {bot_id}: {e}")
            return None
    
    async def auto_schedule_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Automatically schedule bots for upcoming meetings.
        
        Args:
            user_id: User ID to auto-schedule for
            
        Returns:
            List of scheduled bot results
        """
        try:
            # Get user's upcoming meetings
            upcoming_meetings = await self._get_upcoming_meetings(user_id)
            if not upcoming_meetings:
                logger.info(f"No upcoming meetings found for user {user_id}")
                return []
            
            # Check which meetings need bots
            meetings_needing_bots = []
            for meeting in upcoming_meetings:
                has_bot = await self._meeting_has_bot(meeting['id'])
                if not has_bot and meeting.get('auto_bot_enabled', True):
                    meetings_needing_bots.append(meeting)
            
            # Auto-schedule bots for eligible meetings
            scheduled_results = []
            for meeting in meetings_needing_bots:
                try:
                    bot_options = {
                        'meeting_url': meeting.get('meeting_url'),
                        'meeting_time': meeting['start_time'],
                        'project_id': meeting.get('project_id'),
                        'bot_config': {
                            'auto_join': True,
                            'recording_enabled': True,
                            'transcript_enabled': True
                        }
                    }
                    
                    result = await self.send_bot_to_meeting(bot_options, user_id)
                    if result.get('success'):
                        scheduled_results.append({
                            'meeting_id': meeting['id'],
                            'bot_id': result.get('bot_id'),
                            'status': 'scheduled'
                        })
                    
                except Exception as e:
                    logger.error(f"Failed to auto-schedule bot for meeting {meeting['id']}: {e}")
                    continue
            
            logger.info(f"Auto-scheduled {len(scheduled_results)} bots for user {user_id}")
            return scheduled_results
            
        except Exception as e:
            logger.error(f"Failed to auto-schedule bots for user {user_id}: {e}")
            return []
    
    async def get_chat_messages(self, bot_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get chat messages for a meeting bot.
        
        Args:
            bot_id: Bot ID to get messages for
            limit: Maximum number of messages to return
            
        Returns:
            List of chat messages
        """
        try:
            response = await self.http_client.get(
                f"{self.attendee_api_base_url}/chat-messages/{bot_id}",
                params={"limit": limit}
            )
            response.raise_for_status()
            
            messages = response.json()
            
            # Store messages in database for caching
            await self._store_chat_messages(bot_id, messages)
            
            return messages
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting chat messages: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Failed to get chat messages for bot {bot_id}: {e}")
            return []
    
    async def send_chat_message(self, bot_id: str, message: str, to: str, 
                               from_user: str = "system") -> Optional[Dict[str, Any]]:
        """
        Send a chat message through a meeting bot.
        
        Args:
            bot_id: Bot ID to send message through
            message: Message content
            to: Recipient of the message
            from_user: Sender of the message
            
        Returns:
            Message send result or None if failed
        """
        try:
            message_data = {
                "bot_id": bot_id,
                "message": message,
                "to": to,
                "from": from_user,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = await self.http_client.post(
                f"{self.attendee_api_base_url}/send-chat",
                json=message_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Store message in database
            await self._store_chat_message(bot_id, message_data, result.get('message_id'))
            
            logger.info(f"Chat message sent successfully through bot {bot_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending chat message: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to send chat message through bot {bot_id}: {e}")
            return None
    
    async def get_participant_events(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get participant events for a meeting bot.
        
        Args:
            bot_id: Bot ID to get events for
            
        Returns:
            List of participant events
        """
        try:
            response = await self.http_client.get(
                f"{self.attendee_api_base_url}/participant-events/{bot_id}"
            )
            response.raise_for_status()
            
            events = response.json()
            
            # Store events in database
            await self._store_participant_events(bot_id, events)
            
            return events
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting participant events: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Failed to get participant events for bot {bot_id}: {e}")
            return []
    
    async def pause_recording(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Pause recording for a meeting bot.
        
        Args:
            bot_id: Bot ID to pause recording for
            
        Returns:
            Pause result or None if failed
        """
        try:
            response = await self.http_client.post(
                f"{self.attendee_api_base_url}/pause-recording/{bot_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Update bot status in database
            await self._update_bot_status(bot_id, {"is_recording": False})
            
            logger.info(f"Recording paused for bot {bot_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error pausing recording: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to pause recording for bot {bot_id}: {e}")
            return None
    
    async def resume_recording(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume recording for a meeting bot.
        
        Args:
            bot_id: Bot ID to resume recording for
            
        Returns:
            Resume result or None if failed
        """
        try:
            response = await self.http_client.post(
                f"{self.attendee_api_base_url}/resume-recording/{bot_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Update bot status in database
            await self._update_bot_status(bot_id, {"is_recording": True})
            
            logger.info(f"Recording resumed for bot {bot_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error resuming recording: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to resume recording for bot {bot_id}: {e}")
            return None
    
    # Private helper methods
    
    async def _get_user_meeting_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all meeting bots for a user."""
        try:
            result = self.supabase.table("meeting_bots").select("*").eq("user_id", user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get meeting bots for user {user_id}: {e}")
            return []
    
    async def _store_meeting_bot(self, bot_id: str, user_id: str, project_id: str, 
                                meeting_url: str, meeting_time: str, status: str):
        """Store meeting bot information in database."""
        try:
            bot_data = {
                "bot_id": bot_id,
                "user_id": user_id,
                "project_id": project_id,
                "meeting_url": meeting_url,
                "meeting_time": meeting_time,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("meeting_bots").upsert(bot_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store meeting bot {bot_id}: {e}")
    
    async def _update_bot_status(self, bot_id: str, status_data: Dict[str, Any]):
        """Update bot status in database."""
        try:
            update_data = {
                "status": status_data.get('status'),
                "is_recording": status_data.get('is_recording', False),
                "is_paused": status_data.get('is_paused', False),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("meeting_bots").update(update_data).eq("bot_id", bot_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update bot status for {bot_id}: {e}")
    
    async def _store_transcript(self, bot_id: str, transcript_data: Dict[str, Any]):
        """Store transcript data in database."""
        try:
            transcript_record = {
                "bot_id": bot_id,
                "meeting_id": transcript_data.get('meeting_id'),
                "transcript_text": transcript_data.get('transcript_text', ''),
                "participants": transcript_data.get('participants', []),
                "duration_minutes": transcript_data.get('duration_minutes', 0),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("meeting_transcripts").upsert(transcript_record).execute()
            
        except Exception as e:
            logger.error(f"Failed to store transcript for bot {bot_id}: {e}")
    
    async def _get_upcoming_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming meetings for a user."""
        try:
            # This would integrate with the calendar service
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Failed to get upcoming meetings for user {user_id}: {e}")
            return []
    
    async def _meeting_has_bot(self, meeting_id: str) -> bool:
        """Check if a meeting already has a bot assigned."""
        try:
            result = self.supabase.table("meeting_bots").select("bot_id").eq("meeting_id", meeting_id).execute()
            return len(result.data) > 0 if result.data else False
        except Exception as e:
            logger.error(f"Failed to check if meeting {meeting_id} has bot: {e}")
            return False
    
    async def _store_chat_messages(self, bot_id: str, messages: List[Dict[str, Any]]):
        """Store chat messages in database."""
        try:
            for message in messages:
                message_record = {
                    "bot_id": bot_id,
                    "message_id": message.get('id'),
                    "message": message.get('message'),
                    "from_user": message.get('from_user'),
                    "to_user": message.get('to_user'),
                    "timestamp": message.get('timestamp'),
                    "message_type": message.get('message_type', 'text')
                }
                
                self.supabase.table("chat_messages").upsert(message_record).execute()
                
        except Exception as e:
            logger.error(f"Failed to store chat messages for bot {bot_id}: {e}")
    
    async def _store_chat_message(self, bot_id: str, message_data: Dict[str, Any], message_id: str):
        """Store a single chat message in database."""
        try:
            message_record = {
                "bot_id": bot_id,
                "message_id": message_id,
                "message": message_data.get('message'),
                "from_user": message_data.get('from_user'),
                "to_user": message_data.get('to_user'),
                "timestamp": message_data.get('timestamp'),
                "message_type": "text"
            }
            
            self.supabase.table("chat_messages").upsert(message_record).execute()
            
        except Exception as e:
            logger.error(f"Failed to store chat message for bot {bot_id}: {e}")
    
    async def _store_participant_events(self, bot_id: str, events: List[Dict[str, Any]]):
        """Store participant events in database."""
        try:
            for event in events:
                event_record = {
                    "bot_id": bot_id,
                    "participant_id": event.get('participant_id'),
                    "event_type": event.get('event_type'),
                    "timestamp": event.get('timestamp'),
                    "metadata": event.get('metadata', {})
                }
                
                self.supabase.table("participant_events").upsert(event_record).execute()
                
        except Exception as e:
            logger.error(f"Failed to store participant events for bot {bot_id}: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()
