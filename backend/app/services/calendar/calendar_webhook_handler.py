"""
Google Calendar webhook handler for BeSunny.ai Python backend.
Processes incoming webhook notifications from Google Calendar.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.calendar import CalendarWebhookPayload
from ...services.attendee import AttendeeService

logger = logging.getLogger(__name__)


class CalendarWebhookHandler:
    """Handles incoming Google Calendar webhook notifications."""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.settings = get_settings()
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.attendee_service = AttendeeService()
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming Calendar webhook data."""
        try:
            # Parse webhook payload
            payload = CalendarWebhookPayload(**webhook_data)
            
            # Log webhook receipt
            await self._log_webhook_receipt(payload)
            
            # Process based on resource state
            if payload.resource_state == 'change':
                await self._handle_calendar_change(payload)
            elif payload.resource_state == 'trash':
                await self._handle_calendar_deletion(payload)
            else:
                logger.info(f"Unhandled resource state: {payload.resource_state}")
            
            # Mark webhook as processed
            await self._mark_webhook_processed(payload)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Calendar webhook: {e}")
            return False
    
    async def _handle_calendar_change(self, payload: CalendarWebhookPayload):
        """Handle calendar change notification."""
        try:
            # Get webhook information
            webhook_result = await self.supabase.table('calendar_webhooks').select('*').eq('webhook_id', payload.webhook_id).eq('is_active', True).single().execute()
            
            if not webhook_result.data:
                logger.warning(f"No active webhook found for {payload.webhook_id}")
                return
            
            webhook = webhook_result.data
            user_id = webhook['user_id']
            
            # Fetch actual event data from Google Calendar
            event_data = await self._fetch_event_from_google(payload.event_id, user_id)
            if not event_data:
                logger.warning(f"Failed to fetch event {payload.event_id} from Google Calendar")
                return
            
            # Check if event already exists
            existing_meeting = await self._get_meeting_by_event_id(payload.event_id)
            
            if existing_meeting:
                # Update existing meeting
                await self._update_meeting_from_event(existing_meeting['id'], event_data, user_id)
                logger.info(f"Updated meeting {existing_meeting['id']} for calendar change")
                
                # Check for virtual email attendees and auto-schedule bots
                await self._process_virtual_email_attendees(existing_meeting['id'], event_data)
            else:
                # Create new meeting entry
                meeting_id = await self._create_meeting_from_event(event_data, user_id)
                logger.info(f"Created new meeting for calendar event {payload.event_id}")
                
                # Check for virtual email attendees and auto-schedule bots
                if meeting_id:
                    await self._process_virtual_email_attendees(meeting_id, event_data)
            
            # Update webhook last received time
            await self._update_webhook_last_received(payload.webhook_id)
            
        except Exception as e:
            logger.error(f"Failed to handle calendar change: {e}")
            # Implement retry logic for failed webhook processing
            await self._schedule_webhook_retry(payload, 'change')
    
    async def _handle_calendar_deletion(self, payload: CalendarWebhookPayload):
        """Handle calendar deletion notification."""
        try:
            # Get webhook information
            webhook_result = await self.supabase.table('calendar_webhooks').select('*').eq('webhook_id', payload.webhook_id).eq('is_active', True).single().execute()
            
            if not webhook_result.data:
                logger.warning(f"No active webhook found for {payload.webhook_id}")
                return
            
            webhook = webhook_result.data
            user_id = webhook['user_id']
            
            # Mark meeting as deleted
            await self.supabase.table('meetings').update({
                'status': 'cancelled',
                'bot_status': 'failed',
                'updated_at': datetime.now().isoformat(),
                'deleted_at': datetime.now().isoformat()
            }).eq('google_calendar_event_id', payload.event_id).eq('user_id', user_id).execute()
            
            logger.info(f"Marked meeting for event {payload.event_id} as cancelled due to deletion")
            
            # Update webhook last received time
            await self._update_webhook_last_received(payload.webhook_id)
            
        except Exception as e:
            logger.error(f"Failed to handle calendar deletion: {e}")
            # Implement retry logic for failed webhook processing
            await self._schedule_webhook_retry(payload, 'deletion')
    
    async def _fetch_event_from_google(self, event_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch event details from Google Calendar API."""
        for attempt in range(self.max_retries):
            try:
                credentials = await self._get_user_credentials(user_id)
                if not credentials:
                    logger.error(f"No credentials found for user {user_id}")
                    return None
                
                service = build('calendar', 'v3', credentials=credentials)
                
                # Fetch event with all necessary fields
                event = service.events().get(
                    calendarId='primary',
                    eventId=event_id,
                    fields='id,summary,description,start,end,location,attendees,organizer,conferenceData,reminders,transparency,visibility,recurringEventId,originalStartTime,created,updated,status'
                ).execute()
                
                logger.info(f"Successfully fetched event {event_id} from Google Calendar")
                return event
                
            except HttpError as e:
                if e.resp.status == 404:
                    logger.warning(f"Event {event_id} not found in Google Calendar")
                    return None
                elif e.resp.status == 403:
                    logger.error(f"Access denied to Google Calendar for user {user_id}")
                    return None
                elif e.resp.status >= 500:
                    # Server error, retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Failed to fetch event {event_id} after {self.max_retries} attempts")
                        return None
                else:
                    logger.error(f"Google Calendar API error: {e}")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching event {event_id}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    return None
        
        return None
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            result = await self.supabase.table("google_credentials").select(
                "access_token, refresh_token, token_uri, client_id, client_secret, scopes"
            ).eq("user_id", user_id).single().execute()
            
            if result.data:
                cred_data = result.data
                return Credentials(
                    token=cred_data['access_token'],
                    refresh_token=cred_data['refresh_token'],
                    token_uri=cred_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=cred_data.get('client_id', self.settings.google_client_id),
                    client_secret=cred_data.get('client_secret', self.settings.google_client_secret),
                    scopes=cred_data.get('scopes', ['https://www.googleapis.com/auth/calendar.readonly'])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    async def _get_meeting_by_event_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get meeting record by event ID."""
        try:
            result = await self.supabase.table('meetings').select('*').eq('google_calendar_event_id', event_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to get meeting by event ID {event_id}: {e}")
            return None
    
    async def _create_meeting_from_event(self, event_data: Dict[str, Any], user_id: str):
        """Create a new meeting from calendar event data."""
        try:
            # Extract meeting URL
            meeting_url = self._extract_meeting_url(event_data)
            
            # Determine if this is a meeting
            is_meeting = self._is_meeting_event(event_data, meeting_url)
            
            # Create meeting record
            meeting_data = {
                'user_id': user_id,
                'google_calendar_event_id': event_data['id'],
                'title': event_data.get('summary', 'No Title'),
                'description': event_data.get('description', ''),
                'start_time': self._parse_google_datetime(event_data['start']),
                'end_time': self._parse_google_datetime(event_data['end']),
                'location': event_data.get('location', ''),
                'meeting_url': meeting_url,
                'attendees': event_data.get('attendees', []),
                'organizer': event_data.get('organizer', {}).get('email', ''),
                'status': event_data.get('status', 'confirmed'),
                'is_meeting': is_meeting,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = await self.supabase.table('meetings').insert(meeting_data).execute()
            if result.data:
                meeting_id = result.data[0]['id']
                logger.info(f"Created new meeting {meeting_id} for event {event_data['id']}")
                return meeting_id
            else:
                logger.error(f"Failed to create meeting for event {event_data['id']}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to create meeting from event {event_data.get('id')}: {e}")
            return None
    
    async def _update_meeting_from_event(self, meeting_id: str, event_data: Dict[str, Any], user_id: str):
        """Update existing meeting from calendar event data."""
        try:
            # Extract meeting URL
            meeting_url = self._extract_meeting_url(event_data)
            
            # Determine if this is a meeting
            is_meeting = self._is_meeting_event(event_data, meeting_url)
            
            # Update meeting record
            update_data = {
                'title': event_data.get('summary', 'No Title'),
                'description': event_data.get('description', ''),
                'start_time': self._parse_google_datetime(event_data['start']),
                'end_time': self._parse_google_datetime(event_data['end']),
                'location': event_data.get('location', ''),
                'meeting_url': meeting_url,
                'attendees': event_data.get('attendees', []),
                'organizer': event_data.get('organizer', {}).get('email', ''),
                'status': event_data.get('status', 'confirmed'),
                'is_meeting': is_meeting,
                'updated_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
            logger.info(f"Updated meeting {meeting_id} from event {event_data['id']}")
            
        except Exception as e:
            logger.error(f"Failed to update meeting {meeting_id} from event {event_data.get('id')}: {e}")
    
    def _extract_meeting_url(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Extract meeting URL from calendar event."""
        try:
            # Check for Google Meet URL in conferenceData
            if event_data.get('conferenceData', {}).get('entryPoints'):
                for entry_point in event_data['conferenceData']['entryPoints']:
                    if entry_point.get('entryPointType') == 'video':
                        return entry_point.get('uri')
            
            # Check for Google Meet URL in description
            if event_data.get('description'):
                import re
                meet_regex = r'https://meet\.google\.com/[a-z-]+'
                match = re.search(meet_regex, event_data['description'])
                if match:
                    return match.group(0)
            
            # Check for other video conferencing URLs
            video_urls = [
                r'https://zoom\.us/j/\d+',
                r'https://teams\.microsoft\.com/l/meetup-join/[^\\s]+',
                r'https://meet\.google\.com/[a-z-]+',
            ]
            
            if event_data.get('description'):
                for pattern in video_urls:
                    match = re.search(pattern, event_data['description'])
                    if match:
                        return match.group(0)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract meeting URL: {e}")
            return None
    
    def _is_meeting_event(self, event_data: Dict[str, Any], meeting_url: Optional[str]) -> bool:
        """Determine if a calendar event is a meeting."""
        try:
            # Check if event has meeting URL
            if meeting_url:
                return True
            
            # Check event type
            event_type = event_data.get('eventType', 'default')
            if event_type in ['outOfOffice', 'focusTime']:
                return False
            
            # Check if event has attendees
            attendees = event_data.get('attendees', [])
            if len(attendees) > 1:
                return True
            
            # Check if event has conference data
            if event_data.get('conferenceData'):
                return True
            
            # Check event title/keywords
            title = event_data.get('summary', '').lower()
            meeting_keywords = ['meeting', 'call', 'sync', 'standup', 'review', 'planning']
            if any(keyword in title for keyword in meeting_keywords):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to determine if event is meeting: {e}")
            return False
    
    def _parse_google_datetime(self, datetime_obj: Dict[str, Any]) -> str:
        """Parse Google Calendar datetime object to ISO string."""
        try:
            if 'dateTime' in datetime_obj:
                return datetime_obj['dateTime']
            elif 'date' in datetime_obj:
                # Convert date to datetime at start of day
                date_str = datetime_obj['date']
                return f"{date_str}T00:00:00Z"
            else:
                return datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Failed to parse Google datetime: {e}")
            return datetime.now().isoformat()
    
    async def _schedule_webhook_retry(self, payload: CalendarWebhookPayload, action_type: str):
        """Schedule a retry for failed webhook processing."""
        try:
            retry_data = {
                'webhook_id': payload.webhook_id,
                'event_id': payload.event_id,
                'action_type': action_type,
                'retry_count': 0,
                'max_retries': 3,
                'next_retry_at': (datetime.now() + timedelta(minutes=5)).isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('webhook_retry_queue').insert(retry_data).execute()
            logger.info(f"Scheduled retry for webhook {payload.webhook_id}, event {payload.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule webhook retry: {e}")
    
    async def _update_webhook_last_received(self, webhook_id: str):
        """Update webhook last received timestamp."""
        try:
            await self.supabase.table('calendar_webhooks').update({
                'last_webhook_received': datetime.now().isoformat()
            }).eq('webhook_id', webhook_id).execute()
        except Exception as e:
            logger.error(f"Failed to update webhook last received time: {e}")
    
    async def _log_webhook_receipt(self, payload: CalendarWebhookPayload):
        """Log webhook receipt in database."""
        try:
            log_data = {
                'webhook_id': payload.webhook_id,
                'event_id': payload.event_id,
                'resource_state': payload.resource_state,
                'resource_uri': payload.resource_uri,
                'state': payload.state,
                'expiration': payload.expiration,
                'webhook_received_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('calendar_webhook_logs').insert(log_data).execute()
            logger.info(f"Calendar webhook logged for event {payload.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to log webhook receipt: {e}")
    
    async def _mark_webhook_processed(self, payload: CalendarWebhookPayload):
        """Mark webhook as processed."""
        try:
            # Update the webhook log to mark as processed
            await self.supabase.table('calendar_webhook_logs').update({
                'processed_at': datetime.now().isoformat(),
                'processing_status': 'completed'
            }).eq('webhook_id', payload.webhook_id).eq('event_id', payload.event_id).execute()
            
            logger.info(f"Calendar webhook processed for event {payload.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to mark webhook as processed: {e}")
    
    async def get_webhook_logs(self, webhook_id: Optional[str] = None, limit: int = 100) -> list:
        """Get webhook processing logs."""
        try:
            query = self.supabase.table('calendar_webhook_logs').select('*').order('created_at', desc=True).limit(limit)
            
            if webhook_id:
                query = query.eq('webhook_id', webhook_id)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get webhook logs: {e}")
            return []
    
    async def get_active_webhooks(self, user_id: Optional[str] = None) -> list:
        """Get active calendar webhooks."""
        try:
            query = self.supabase.table('calendar_webhooks').select('*').eq('is_active', True)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get active webhooks: {e}")
            return []
    
    async def get_webhook_health_metrics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get webhook health metrics."""
        try:
            # Get webhook processing statistics
            logs_query = self.supabase.table('calendar_webhook_logs').select('*')
            if user_id:
                logs_query = logs_query.eq('user_id', user_id)
            
            logs_result = await logs_query.execute()
            logs = logs_result.data or []
            
            # Calculate metrics
            total_webhooks = len(logs)
            processed_webhooks = len([log for log in logs if log.get('processing_status') == 'completed'])
            failed_webhooks = len([log for log in logs if log.get('processing_status') == 'failed'])
            
            # Calculate processing time
            processing_times = []
            for log in logs:
                if log.get('processed_at') and log.get('webhook_received_at'):
                    try:
                        received = datetime.fromisoformat(log['webhook_received_at'].replace('Z', '+00:00'))
                        processed = datetime.fromisoformat(log['processed_at'].replace('Z', '+00:00'))
                        processing_time = (processed - received).total_seconds()
                        processing_times.append(processing_time)
                    except:
                        continue
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            return {
                'total_webhooks': total_webhooks,
                'processed_webhooks': processed_webhooks,
                'failed_webhooks': failed_webhooks,
                'success_rate': (processed_webhooks / total_webhooks * 100) if total_webhooks > 0 else 0,
                'average_processing_time_seconds': round(avg_processing_time, 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get webhook health metrics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _process_virtual_email_attendees(self, meeting_id: str, event_data: Dict[str, Any]):
        """Process virtual email attendees and auto-schedule bots if needed."""
        try:
            # Extract attendees from event
            attendees = event_data.get('attendees', [])
            if not attendees:
                return
            
            # Look for virtual email attendees (ai+{username}@besunny.ai)
            virtual_email_pattern = r'ai\+([^@]+)@besunny\.ai'
            virtual_attendees = []
            
            for attendee in attendees:
                if isinstance(attendee, dict) and attendee.get('email'):
                    email = attendee['email']
                    match = re.search(virtual_email_pattern, email)
                    if match:
                        username = match.group(1)
                        virtual_attendees.append({
                            'email': email,
                            'username': username,
                            'response_status': attendee.get('responseStatus', 'needsAction')
                        })
            
            if not virtual_attendees:
                return
            
            logger.info(f"Found {len(virtual_attendees)} virtual email attendees for meeting {meeting_id}")
            
            # Process each virtual email attendee
            for virtual_attendee in virtual_attendees:
                await self._auto_schedule_bot_for_virtual_email(meeting_id, virtual_attendee, event_data)
                
        except Exception as e:
            logger.error(f"Failed to process virtual email attendees for meeting {meeting_id}: {e}")
    
    async def _auto_schedule_bot_for_virtual_email(self, meeting_id: str, virtual_attendee: Dict[str, Any], event_data: Dict[str, Any]):
        """Auto-schedule a bot for a meeting with a virtual email attendee."""
        try:
            username = virtual_attendee['username']
            virtual_email = virtual_attendee['email']
            
            # Find user by username
            user_result = await self.supabase.table('users').select('id').eq('username', username).single().execute()
            if not user_result.data:
                logger.warning(f"User not found for username: {username}")
                return
            
            user_id = user_result.data['id']
            
            # Check if meeting already has a bot for this user
            existing_bot = await self._check_existing_bot(meeting_id, user_id)
            if existing_bot:
                logger.info(f"Bot already exists for meeting {meeting_id} and user {user_id}")
                return
            
            # Extract meeting URL
            meeting_url = self._extract_meeting_url(event_data)
            if not meeting_url:
                logger.warning(f"No meeting URL found for event {event_data.get('id')}")
                return
            
            # Check if this is a Google Meet or other video conference
            if not self._is_video_conference_url(meeting_url):
                logger.info(f"Meeting URL {meeting_url} is not a video conference, skipping bot scheduling")
                return
            
            # Auto-schedule bot using Attendee.dev API
            bot_result = await self._schedule_attendee_bot(meeting_id, user_id, meeting_url, event_data)
            
            if bot_result.get('success'):
                logger.info(f"Successfully auto-scheduled bot for meeting {meeting_id} with virtual email {virtual_email}")
                
                # Update meeting record to mark as auto-scheduled
                await self._update_meeting_auto_scheduled(meeting_id, user_id, virtual_email, bot_result)
            else:
                logger.error(f"Failed to auto-schedule bot for meeting {meeting_id}: {bot_result.get('error')}")
                
        except Exception as e:
            logger.error(f"Failed to auto-schedule bot for virtual email attendee: {e}")
    
    async def _schedule_attendee_bot(self, meeting_id: str, user_id: str, meeting_url: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an attendee bot for a meeting."""
        try:
            # Prepare bot configuration
            bot_options = {
                'meeting_url': meeting_url,
                'bot_name': 'Sunny AI Notetaker',
                'bot_chat_message': 'Hi, I\'m here to transcribe this meeting!'
            }
            
            # Create bot using Attendee service
            result = await self.attendee_service.create_bot_for_meeting(bot_options, user_id)
            
            if result.get('success'):
                # Store bot information in meetings table
                await self._store_meeting_bot_info(meeting_id, user_id, result)
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to schedule attendee bot: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _store_meeting_bot_info(self, meeting_id: str, user_id: str, bot_result: Dict[str, Any]):
        """Store bot information in the meetings table."""
        try:
            update_data = {
                'attendee_bot_id': bot_result.get('bot_id'),
                'bot_status': 'bot_scheduled',
                'bot_deployment_method': 'automatic',
                'auto_scheduled_via_email': True,
                'virtual_email_attendee': f"ai+{user_id}@besunny.ai",  # This will be updated with actual username
                'bot_configuration': {
                    'provider': 'attendee',
                    'bot_id': bot_result.get('bot_id'),
                    'project_id': bot_result.get('project_id'),
                    'auto_scheduled': True
                },
                'updated_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to store meeting bot info: {e}")
    
    async def _update_meeting_auto_scheduled(self, meeting_id: str, user_id: str, virtual_email: str, bot_result: Dict[str, Any]):
        """Update meeting record to mark as auto-scheduled."""
        try:
            # Get username for the virtual email
            username_match = re.search(r'ai\+([^@]+)@besunny\.ai', virtual_email)
            username = username_match.group(1) if username_match else 'unknown'
            
            update_data = {
                'auto_scheduled_via_email': True,
                'virtual_email_attendee': virtual_email,
                'bot_deployment_method': 'automatic',
                'bot_status': 'bot_scheduled',
                'attendee_bot_id': bot_result.get('bot_id'),
                'bot_configuration': {
                    'provider': 'attendee',
                    'bot_id': bot_result.get('bot_id'),
                    'project_id': bot_result.get('project_id'),
                    'auto_scheduled': True,
                    'scheduled_for_user': user_id,
                    'username': username
                },
                'updated_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update meeting auto-scheduled status: {e}")
    
    async def _check_existing_bot(self, meeting_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if a meeting already has a bot for a specific user."""
        try:
            result = await self.supabase.table('meetings').select(
                'attendee_bot_id, bot_status, bot_configuration'
            ).eq('id', meeting_id).eq('user_id', user_id).single().execute()
            
            if result.data and result.data.get('attendee_bot_id'):
                return result.data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check existing bot: {e}")
            return None
    
    def _is_video_conference_url(self, url: str) -> bool:
        """Check if a URL is a video conference URL."""
        if not url:
            return False
        
        video_patterns = [
            r'https://meet\.google\.com/[a-z-]+',
            r'https://zoom\.us/j/\d+',
            r'https://teams\.microsoft\.com/l/meetup-join/[^\s]+',
            r'https://meet\.jitsi\.net/[^\s]+',
            r'https://app\.whereby\.com/[^\s]+'
        ]
        
        for pattern in video_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
