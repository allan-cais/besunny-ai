"""
Google Calendar service for BeSunny.ai Python backend.
Handles calendar synchronization, webhook setup, and meeting management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.calendar import (
    CalendarEvent,
    CalendarWebhook,
    Meeting,
    MeetingBot
)

logger = logging.getLogger(__name__)


class CalendarService:
    """Main service for Google Calendar operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
    
    async def setup_calendar_webhook(self, user_id: str, calendar_id: str = 'primary') -> Optional[str]:
        """Set up a webhook for a Google Calendar."""
        try:
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No Google credentials found for user {user_id}")
                return None
            
            # Create Calendar API service
            service = build('calendar', 'v3', credentials=credentials)
            
            # Create webhook
            webhook_request = {
                'id': f"webhook_{user_id}_{calendar_id}_{int(datetime.now().timestamp())}",
                'type': 'web_hook',
                'address': f"{self.settings.webhook_base_url}/api/v1/calendar/webhook",
                'expiration': (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
            }
            
            # Create the webhook
            webhook = service.events().watch(
                calendarId=calendar_id,
                body=webhook_request
            ).execute()
            
            # Store webhook information in database
            await self._store_calendar_webhook(
                user_id=user_id,
                calendar_id=calendar_id,
                webhook_id=webhook['id'],
                resource_id=webhook['resourceId'],
                expiration=webhook['expiration']
            )
            
            logger.info(f"Calendar webhook created for user {user_id}, calendar {calendar_id}")
            return webhook['id']
            
        except HttpError as e:
            logger.error(f"Failed to create calendar webhook: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error setting up calendar webhook: {e}")
            return None
    
    async def sync_calendar_events(self, user_id: str, calendar_id: str = 'primary', 
                                 sync_range_days: int = 30) -> List[CalendarEvent]:
        """Sync calendar events for a user."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return []
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Calculate time range
            now = datetime.utcnow()
            time_min = now - timedelta(days=sync_range_days)
            time_max = now + timedelta(days=sync_range_days)
            
            # Get events
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                calendar_event = CalendarEvent(
                    id=event['id'],
                    summary=event.get('summary', 'No Title'),
                    description=event.get('description', ''),
                    start_time=event['start'].get('dateTime') or event['start'].get('date'),
                    end_time=event['end'].get('dateTime') or event['end'].get('date'),
                    attendees=event.get('attendees', []),
                    meeting_url=event.get('hangoutLink'),
                    created=event.get('created'),
                    updated=event.get('updated')
                )
                events.append(calendar_event)
                
                # Create or update meeting in database
                await self._sync_meeting_to_database(calendar_event, user_id)
            
            # Log sync completion
            await self._log_sync_completion(user_id, 'calendar', len(events))
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to sync calendar events for user {user_id}: {e}")
            await self._log_sync_error(user_id, 'calendar', str(e))
            return []
    
    async def get_meeting_details(self, event_id: str, user_id: str, calendar_id: str = 'primary') -> Optional[CalendarEvent]:
        """Get detailed information for a specific meeting."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return None
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get event details
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return CalendarEvent(
                id=event['id'],
                summary=event.get('summary', 'No Title'),
                description=event.get('description', ''),
                start_time=event['start'].get('dateTime') or event['start'].get('date'),
                end_time=event['end'].get('dateTime') or event['end'].get('date'),
                attendees=event.get('attendees', []),
                meeting_url=event.get('hangoutLink'),
                created=event.get('created'),
                updated=event.get('updated')
            )
            
        except HttpError as e:
            logger.error(f"Failed to get meeting details for {event_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting meeting details: {e}")
            return None
    
    async def schedule_meeting_bot(self, meeting_id: str, bot_config: Dict[str, Any]) -> bool:
        """Schedule a bot to attend a meeting."""
        try:
            # Get meeting details
            meeting_result = await self.supabase.table('meetings').select('*').eq('id', meeting_id).single().execute()
            
            if not meeting_result.data:
                logger.error(f"Meeting {meeting_id} not found")
                return False
            
            meeting = meeting_result.data
            
            # Update meeting with bot configuration
            await self.supabase.table('meetings').update({
                'bot_status': 'bot_scheduled',
                'bot_configuration': bot_config,
                'updated_at': datetime.now().isoformat()
            }).eq('id', meeting_id).execute()
            
            logger.info(f"Bot scheduled for meeting {meeting_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule meeting bot: {e}")
            return False
    
    async def get_user_meetings(self, user_id: str, project_id: Optional[str] = None, 
                               status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get meetings for a user, optionally filtered by project and status."""
        try:
            query = self.supabase.table('meetings').select('*').eq('user_id', user_id)
            
            if project_id:
                query = query.eq('project_id', project_id)
            
            if status:
                query = query.eq('bot_status', status)
            
            result = await query.order('start_time', desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get user meetings: {e}")
            return []
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            result = await self.supabase.table('google_credentials').select('*').eq('user_id', user_id).single().execute()
            
            if result.data:
                cred_data = result.data
                return Credentials(
                    token=cred_data['access_token'],
                    refresh_token=cred_data['refresh_token'],
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=self.settings.google_client_id,
                    client_secret=self.settings.google_client_secret,
                    scopes=['https://www.googleapis.com/auth/calendar.readonly']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    async def _store_calendar_webhook(self, user_id: str, calendar_id: str, webhook_id: str, 
                                    resource_id: str, expiration: str):
        """Store calendar webhook information in database."""
        try:
            webhook_data = {
                'user_id': user_id,
                'google_calendar_id': calendar_id,
                'webhook_id': webhook_id,
                'resource_id': resource_id,
                'expiration_time': expiration,
                'is_active': True
            }
            
            await self.supabase.table('calendar_webhooks').upsert(webhook_data).execute()
            logger.info(f"Calendar webhook stored for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to store calendar webhook: {e}")
    
    async def _sync_meeting_to_database(self, calendar_event: CalendarEvent, user_id: str):
        """Sync a calendar event to the meetings table."""
        try:
            # Check if meeting already exists
            existing_result = await self.supabase.table('meetings').select('id').eq('google_calendar_event_id', calendar_event.id).execute()
            
            if existing_result.data:
                # Update existing meeting
                await self.supabase.table('meetings').update({
                    'title': calendar_event.summary,
                    'description': calendar_event.description,
                    'start_time': calendar_event.start_time,
                    'end_time': calendar_event.end_time,
                    'meeting_url': calendar_event.meeting_url,
                    'updated_at': datetime.now().isoformat()
                }).eq('google_calendar_event_id', calendar_event.id).execute()
            else:
                # Create new meeting
                meeting_data = {
                    'user_id': user_id,
                    'title': calendar_event.summary,
                    'description': calendar_event.description,
                    'start_time': calendar_event.start_time,
                    'end_time': calendar_event.end_time,
                    'meeting_url': calendar_event.meeting_url,
                    'google_calendar_event_id': calendar_event.id,
                    'bot_status': 'pending',
                    'event_status': 'needsAction'
                }
                
                await self.supabase.table('meetings').insert(meeting_data).execute()
                
        except Exception as e:
            logger.error(f"Failed to sync meeting to database: {e}")
    
    async def _log_sync_completion(self, user_id: str, service_type: str, items_processed: int):
        """Log successful sync completion."""
        try:
            log_data = {
                'user_id': user_id,
                'sync_type': 'incremental',
                'status': 'completed',
                'events_processed': items_processed,
                'duration_ms': 0,  # Would need to track actual duration
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('calendar_sync_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log sync completion: {e}")
    
    async def _log_sync_error(self, user_id: str, service_type: str, error_message: str):
        """Log sync error."""
        try:
            log_data = {
                'user_id': user_id,
                'sync_type': 'incremental',
                'status': 'failed',
                'error_message': error_message,
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('calendar_sync_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log sync error: {e}")
    
    async def cleanup_expired_webhooks(self):
        """Clean up expired calendar webhooks."""
        try:
            # Get expired webhooks
            result = await self.supabase.table('calendar_webhooks').select('*').lt('expiration_time', datetime.now().isoformat()).eq('is_active', True).execute()
            
            for webhook in result.data:
                try:
                    # Mark as inactive
                    await self.supabase.table('calendar_webhooks').update({'is_active': False}).eq('id', webhook['id']).execute()
                    logger.info(f"Marked expired webhook {webhook['id']} as inactive")
                except Exception as e:
                    logger.error(f"Failed to update expired webhook {webhook['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired webhooks: {e}")
