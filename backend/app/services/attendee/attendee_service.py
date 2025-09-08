"""
Core attendee service for BeSunny.ai Python backend.
Handles meeting bot management, transcript retrieval, and chat functionality.
Implements Attendee.dev API according to their official documentation.
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
        self.attendee_api_base_url = self.settings.attendee_api_base_url or "https://app.attendee.dev"
        
        # Try to get API key from settings first, then fallback to direct env var
        self.attendee_api_key = self.settings.master_attendee_api_key
        if not self.attendee_api_key:
            import os
            self.attendee_api_key = os.getenv('ATTENDEE_API_KEY')
            logger.info("Using ATTENDEE_API_KEY from environment variable directly")
        
        # Debug logging for environment variables
        logger.info(f"Attendee API key configured: {bool(self.attendee_api_key)}")
        logger.info(f"Attendee API base URL: {self.attendee_api_base_url}")
        
        if not self.attendee_api_key:
            logger.error("Attendee API key not configured - checking environment variables")
            import os
            logger.error(f"ATTENDEE_API_KEY env var: {bool(os.getenv('ATTENDEE_API_KEY'))}")
            logger.error(f"MASTER_ATTENDEE_API_KEY env var: {bool(os.getenv('MASTER_ATTENDEE_API_KEY'))}")
            raise ValueError("Attendee API key not configured")
        
        # HTTP client for external API calls
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Token {self.attendee_api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info("Attendee Service initialized")
    
    async def create_bot_for_meeting(self, options: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create a bot for a meeting using Attendee.dev API.
        
        Args:
            options: Bot configuration options
            user_id: User ID requesting the bot
            
        Returns:
            Bot creation result
        """
        try:
            # Validate required fields
            required_fields = ['meeting_url', 'bot_name']
            for field in required_fields:
                if field not in options:
                    raise ValueError(f"Missing required field: {field}")
            
            # Get webhook URL for this user
            webhook_url = await self._get_user_webhook_url(user_id)
            
            # Create bot with comprehensive webhook configuration for transcript retrieval
            # Based on Attendee.dev webhook documentation: https://docs.attendee.dev/guides/webhooks
            bot_data = {
                "meeting_url": options['meeting_url'],
                "bot_name": options['bot_name'],
                "webhooks": [
                    {
                        "url": webhook_url,
                        "triggers": [
                            "bot.state_change",        # For meeting end/recording availability
                            "transcript.update",        # Real-time transcript updates during meeting
                            "chat_messages.update",     # Chat message updates in the meeting
                            "participant_events.join_leave"  # Participant join/leave events
                        ]
                    }
                ]
            }
            
            # Add optional bot chat message if provided
            if options.get('bot_chat_message'):
                bot_data["bot_chat_message"] = options['bot_chat_message']
            
            # Add deployment method to track how bot was created
            deployment_method = options.get('deployment_method', 'manual')
            if deployment_method == 'automatic':
                bot_data["metadata"] = {
                    "deployment_method": "automatic",
                    "virtual_email_triggered": True,
                    "created_via": "virtual_email_attendee"
                }
            else:
                bot_data["metadata"] = {
                    "deployment_method": "manual",
                    "created_via": "ui_deployment"
                }
            
            logger.info(f"Creating bot with webhook configuration: {bot_data['webhooks']}")
            
            # Call Attendee.dev API to create bot
            response = await self.http_client.post(
                f"{self.attendee_api_base_url}/api/v1/bots",
                json=bot_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Store bot information in database with deployment method
            await self._store_meeting_bot(
                bot_id=result['id'],
                user_id=user_id,
                meeting_url=options['meeting_url'],
                bot_name=options['bot_name'],
                status='created',
                attendee_project_id=result.get('project_id'),
                deployment_method=deployment_method,
                metadata=bot_data.get('metadata', {})
            )
            
            logger.info(f"Bot created successfully for user {user_id}, bot ID: {result['id']}, deployment: {deployment_method}")
            return {
                "success": True,
                "bot_id": result['id'],
                "project_id": result.get('project_id'),
                "status": "created",
                "deployment_method": deployment_method,
                "webhooks_configured": True
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating bot: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            logger.error(f"Failed to create bot for user {user_id}: {e}")
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
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}"
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
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}/transcript"
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
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}/chat-messages",
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
    
    async def send_chat_message(self, bot_id: str, message: str, to: str = "everyone") -> Optional[Dict[str, Any]]:
        """
        Send a chat message through a meeting bot.
        
        Args:
            bot_id: Bot ID to send message through
            message: Message content
            to: Recipient of the message (default: "everyone")
            
        Returns:
            Message send result or None if failed
        """
        try:
            message_data = {
                "message": message,
                "to": to
            }
            
            response = await self.http_client.post(
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}/chat-messages",
                json=message_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Store message in database
            await self._store_chat_message(bot_id, message_data, result.get('id'))
            
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
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}/participant-events"
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
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}/pause-recording"
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
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}/resume-recording"
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
    
    async def delete_bot(self, bot_id: str) -> bool:
        """
        Delete a meeting bot.
        
        Args:
            bot_id: Bot ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.http_client.delete(
                f"{self.attendee_api_base_url}/api/v1/bots/{bot_id}"
            )
            response.raise_for_status()
            
            # Remove bot from database
            await self._remove_meeting_bot(bot_id)
            
            logger.info(f"Bot {bot_id} deleted successfully")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error deleting bot: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete bot {bot_id}: {e}")
            return False
    
    async def list_user_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all bots for a user.
        
        Args:
            user_id: User ID to list bots for
            
        Returns:
            List of user's bots
        """
        try:
            # Get bots from database first
            db_bots = await self._get_user_meeting_bots(user_id)
            
            # Fetch current status from Attendee API for each bot
            updated_bots = []
            for bot in db_bots:
                try:
                    status = await self.get_bot_status(bot['bot_id'])
                    if status:
                        bot.update(status)
                        updated_bots.append(bot)
                except Exception as e:
                    logger.error(f"Failed to get status for bot {bot['bot_id']}: {e}")
                    updated_bots.append(bot)  # Include bot even if status fetch failed
            
            return updated_bots
            
        except Exception as e:
            logger.error(f"Failed to list bots for user {user_id}: {e}")
            return []
    
    # Private helper methods
    
    async def _get_user_webhook_url(self, user_id: str) -> str:
        """Get webhook URL for a user."""
        webhook_base_url = self.settings.webhook_base_url
        return f"{webhook_base_url}/api/v1/webhooks/attendee/{user_id}"
    
    async def _get_user_meeting_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all meeting bots for a user."""
        try:
            result = self.supabase.table("meeting_bots").select("*").eq("user_id", user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get meeting bots for user {user_id}: {e}")
            return []
    
    async def _store_meeting_bot(self, bot_id: str, user_id: str, meeting_url: str, 
                                bot_name: str, status: str, attendee_project_id: Optional[str] = None,
                                deployment_method: str = 'manual', metadata: Optional[Dict[str, Any]] = None):
        """Store meeting bot information in database."""
        try:
            bot_data = {
                "bot_id": bot_id,
                "user_id": user_id,
                "meeting_url": meeting_url,
                "bot_name": bot_name,
                "status": status,
                "attendee_project_id": attendee_project_id,
                "deployment_method": deployment_method,
                "metadata": metadata,
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
    
    async def _remove_meeting_bot(self, bot_id: str):
        """Remove meeting bot from database."""
        try:
            self.supabase.table("meeting_bots").delete().eq("bot_id", bot_id).execute()
        except Exception as e:
            logger.error(f"Failed to remove meeting bot {bot_id}: {e}")
    
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
