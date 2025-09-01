"""
Calendar polling service for BeSunny.ai Python backend.
Handles Google Calendar synchronization, event processing, and smart polling.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.calendar import CalendarEvent, Meeting

logger = logging.getLogger(__name__)


class CalendarPollingResult(BaseModel):
    """Result of a calendar polling operation."""
    user_id: str
    calendar_id: str
    events_processed: int
    events_created: int
    events_updated: int
    events_deleted: int
    meetings_detected: int
    processing_time_ms: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime


class SmartPollingMetrics(BaseModel):
    """Metrics for smart polling optimization."""
    user_id: str
    last_poll_at: datetime
    change_frequency: str  # 'low', 'medium', 'high'
    next_poll_interval: int  # minutes
    events_since_last_poll: int
    meetings_since_last_poll: int
    virtual_emails_detected: int


class CalendarPollingService:
    """Service for polling and synchronizing Google Calendar data."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        
        logger.info("Calendar Polling Service initialized")
    
    async def poll_calendar_for_user(self, user_id: str, calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        Poll calendar for a specific user.
        
        Args:
            user_id: User ID to poll calendar for
            calendar_id: Calendar ID to poll (default: primary)
            
        Returns:
            Polling results and metrics
        """
        start_time = datetime.now()
        
        try:
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'No Google credentials found',
                    'user_id': user_id,
                    'calendar_id': calendar_id
                }
            
            # Create Calendar API service
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get last sync time
            last_sync = await self._get_last_sync_time(user_id, calendar_id)
            
            # Get changes since last sync
            changes = await self._get_calendar_changes(service, calendar_id, last_sync)
            
            # Process changes
            events_created = 0
            events_updated = 0
            events_deleted = 0
            meetings_detected = 0
            
            for change in changes:
                try:
                    if change.get('removed'):
                        # Event was deleted
                        result = await self._handle_deleted_event(
                            change['eventId'], user_id, calendar_id
                        )
                        if result:
                            events_deleted += 1
                    else:
                        # Event was created or updated
                        event = change.get('event', {})
                        if event:
                            result = await self._process_calendar_event(
                                event, user_id, credentials
                            )
                            if result:
                                if result.get('action') == 'created':
                                    events_created += 1
                                elif result.get('action') == 'updated':
                                    events_updated += 1
                                
                                if result.get('is_meeting'):
                                    meetings_detected += 1
                                    
                except Exception as e:
                    logger.error(f"Failed to process calendar change: {e}")
                    continue
            
            # Update last sync time
            await self._update_last_sync_time(user_id, calendar_id)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            # Create polling result
            result = CalendarPollingResult(
                user_id=user_id,
                calendar_id=calendar_id,
                events_processed=len(changes),
                events_created=events_created,
                events_updated=events_updated,
                events_deleted=events_deleted,
                meetings_detected=meetings_detected,
                processing_time_ms=processing_time,
                success=True,
                timestamp=datetime.now()
            )
            
            # Store result
            await self._store_polling_result(result)
            
            logger.info(f"Calendar polling completed for user {user_id}: {events_created} created, {events_updated} updated, {events_deleted} deleted")
            
            return {
                'success': True,
                'user_id': user_id,
                'calendar_id': calendar_id,
                'events_processed': len(changes),
                'events_created': events_created,
                'events_updated': events_updated,
                'events_deleted': events_deleted,
                'meetings_detected': meetings_detected,
                'processing_time_ms': processing_time
            }
            
        except HttpError as e:
            error_message = f"Google Calendar API error: {e}"
            logger.error(error_message)
            
            result = CalendarPollingResult(
                user_id=user_id,
                calendar_id=calendar_id,
                events_processed=0,
                events_created=0,
                events_updated=0,
                events_deleted=0,
                meetings_detected=0,
                processing_time_ms=(datetime.now() - start_time).microseconds // 1000,
                success=False,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            await self._store_polling_result(result)
            
            return {
                'success': False,
                'error': error_message,
                'user_id': user_id,
                'calendar_id': calendar_id
            }
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(f"Calendar polling failed for user {user_id}: {error_message}")
            
            result = CalendarPollingResult(
                user_id=user_id,
                calendar_id=calendar_id,
                events_processed=0,
                events_created=0,
                events_updated=0,
                events_deleted=0,
                meetings_detected=0,
                processing_time_ms=(datetime.now() - start_time).microseconds // 1000,
                success=False,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            await self._store_polling_result(result)
            
            return {
                'success': False,
                'error': error_message,
                'user_id': user_id,
                'calendar_id': calendar_id
            }
    
    async def process_calendar_event(self, event: Dict[str, Any], user_id: str, 
                                   credentials: Credentials) -> Optional[Dict[str, Any]]:
        """
        Process a single calendar event.
        
        Args:
            event: Calendar event data
            user_id: User ID
            credentials: Google credentials
            
        Returns:
            Processing result or None if failed
        """
        try:
            event_id = event.get('id')
            if not event_id:
                logger.warning("Calendar event missing ID")
                return None
            
            # Check if event already exists
            existing_event = await self._get_existing_event(event_id, user_id)
            
            # Extract meeting URL if present
            meeting_url = await self._extract_meeting_url(event)
            
            # Determine if this is a meeting
            is_meeting = await self._is_meeting_event(event, meeting_url)
            
            # Create or update event
            if existing_event:
                # Update existing event
                updated_event = await self._update_calendar_event(
                    event_id, event, user_id, meeting_url, is_meeting
                )
                action = 'updated'
            else:
                # Create new event
                created_event = await self._create_calendar_event(
                    event, user_id, meeting_url, is_meeting
                )
                action = 'created'
            
            # If this is a meeting, create or update meeting record
            if is_meeting:
                await self._handle_meeting_event(event, user_id, meeting_url)
            
            return {
                'action': action,
                'event_id': event_id,
                'is_meeting': is_meeting,
                'meeting_url': meeting_url
            }
            
        except Exception as e:
            logger.error(f"Failed to process calendar event: {e}")
            return None
    
    async def handle_deleted_event(self, event_id: str, user_id: str, 
                                 calendar_id: str) -> Optional[Dict[str, Any]]:
        """
        Handle a deleted calendar event.
        
        Args:
            event_id: ID of deleted event
            user_id: User ID
            calendar_id: Calendar ID
            
        Returns:
            Deletion result or None if failed
        """
        try:
            # Mark event as deleted in database
            await self._mark_event_deleted(event_id, user_id)
            
            # Check if this was a meeting and handle accordingly
            meeting = await self._get_meeting_by_event_id(event_id)
            if meeting:
                await self._handle_meeting_deletion(meeting['id'], user_id)
            
            logger.info(f"Handled deletion of calendar event {event_id} for user {user_id}")
            
            return {
                'event_id': event_id,
                'deleted': True,
                'meeting_handled': meeting is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to handle deleted event {event_id}: {e}")
            return None
    
    async def extract_meeting_url(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Extract meeting URL from calendar event.
        
        Args:
            event: Calendar event data
            
        Returns:
            Meeting URL or None if not found
        """
        try:
            # Check various fields for meeting URLs
            url_fields = ['hangoutLink', 'conferenceData', 'description', 'location']
            
            for field in url_fields:
                if field in event:
                    value = event[field]
                    
                    if field == 'hangoutLink' and value:
                        return value
                    
                    elif field == 'conferenceData' and value:
                        conference_data = value.get('conferenceData', {})
                        entry_points = conference_data.get('entryPoints', [])
                        
                        for entry_point in entry_points:
                            if entry_point.get('entryPointType') == 'video':
                                return entry_point.get('uri')
                    
                    elif field in ['description', 'location'] and value:
                        # Look for common meeting URL patterns
                        import re
                        url_patterns = [
                            r'https?://meet\.google\.com/[a-zA-Z0-9\-_]+',
                            r'https?://zoom\.us/j/[0-9]+',
                            r'https?://teams\.microsoft\.com/l/meetup-join/[^\\s]+',
                            r'https?://discord\.gg/[a-zA-Z0-9]+'
                        ]
                        
                        for pattern in url_patterns:
                            match = re.search(pattern, value)
                            if match:
                                return match.group(0)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract meeting URL: {e}")
            return None
    
    async def smart_calendar_polling(self, user_id: str) -> Dict[str, Any]:
        """
        Smart calendar polling that optimizes based on user activity and change patterns.
        
        Args:
            user_id: User ID to poll for
            
        Returns:
            Smart polling results
        """
        try:
            # Get smart polling metrics
            metrics = await self._get_smart_polling_metrics(user_id)
            
            # Determine if we should poll based on metrics
            should_poll = await self._should_poll_calendar(user_id, metrics)
            
            if not should_poll:
                return {
                    'skipped': True,
                    'reason': 'Smart polling optimization',
                    'next_poll_in_minutes': metrics.next_poll_interval,
                    'user_id': user_id
                }
            
            # Execute polling
            result = await self.poll_calendar_for_user(user_id)
            
            # Update smart polling metrics
            await self._update_smart_polling_metrics(user_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Smart calendar polling failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }
    
    # Private helper methods
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("access_token, refresh_token, token_uri, client_id, client_secret, scopes") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                cred_data = result.data
                return Credentials(
                    token=cred_data['access_token'],
                    refresh_token=cred_data['refresh_token'],
                    token_uri=cred_data['token_uri'],
                    client_id=cred_data['client_id'],
                    client_secret=cred_data['client_secret'],
                    scopes=cred_data['scopes']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    async def _get_last_sync_time(self, user_id: str, calendar_id: str) -> Optional[str]:
        """Get last sync time for a user's calendar."""
        try:
            result = self.supabase.table("calendar_sync_states") \
                .select("last_sync_at") \
                .eq("user_id", user_id) \
                .eq("calendar_id", calendar_id) \
                .single() \
                .execute()
            
            return result.data.get('last_sync_at') if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get last sync time for user {user_id}: {e}")
            return None
    
    async def _get_calendar_changes(self, service, calendar_id: str, 
                                  last_sync: Optional[str]) -> List[Dict[str, Any]]:
        """Get calendar changes since last sync."""
        try:
            if last_sync:
                # Use sync token if available
                sync_token = await self._get_sync_token(calendar_id)
                if sync_token:
                    try:
                        changes = service.events().list(
                            calendarId=calendar_id,
                            syncToken=sync_token,
                            singleEvents=True,
                            showDeleted=True
                        ).execute()
                        
                        # Store new sync token
                        await self._update_sync_token(calendar_id, changes.get('nextSyncToken'))
                        
                        return changes.get('items', [])
                        
                    except HttpError as e:
                        if e.resp.status == 410:
                            # Sync token expired, fall back to time-based polling
                            logger.info(f"Sync token expired for calendar {calendar_id}, falling back to time-based polling")
                            return await self._get_changes_by_time(service, calendar_id, last_sync)
                        else:
                            logger.error(f"Google API error with sync token: {e}")
                            return await self._get_changes_by_time(service, calendar_id, last_sync)
                else:
                    # No sync token, use time-based polling
                    return await self._get_changes_by_time(service, calendar_id, last_sync)
            else:
                # First sync - get events from last 30 days
                return await self._get_changes_by_time(service, calendar_id, None)
            
        except Exception as e:
            logger.error(f"Failed to get calendar changes: {e}")
            return []
    
    async def _get_changes_by_time(self, service, calendar_id: str, last_sync: Optional[str]) -> List[Dict[str, Any]]:
        """Get calendar changes using time-based polling."""
        try:
            if last_sync:
                # Use last sync time
                time_min = last_sync
            else:
                # First sync - get events from last 30 days
                time_min = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
            
            time_max = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'
            
            changes = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                showDeleted=True,
                orderBy='startTime'
            ).execute()
            
            return changes.get('items', [])
            
        except Exception as e:
            logger.error(f"Failed to get changes by time: {e}")
            return []
    
    async def _update_sync_token(self, calendar_id: str, sync_token: Optional[str]):
        """Update sync token for a calendar."""
        try:
            if sync_token:
                # Update sync token in database
                await self.supabase.table("calendar_sync_states") \
                    .upsert({
                        'calendar_id': calendar_id,
                        'sync_token': sync_token,
                        'updated_at': datetime.now().isoformat()
                    }) \
                    .execute()
                
                logger.info(f"Updated sync token for calendar {calendar_id}")
                
        except Exception as e:
            logger.error(f"Failed to update sync token for calendar {calendar_id}: {e}")
    
    async def _get_existing_event(self, event_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get existing calendar event from database."""
        try:
            result = self.supabase.table("calendar_events") \
                .select("*") \
                .eq("event_id", event_id) \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get existing event {event_id}: {e}")
            return None
    
    async def _is_meeting_event(self, event: Dict[str, Any], meeting_url: Optional[str]) -> bool:
        """Determine if a calendar event is a meeting."""
        try:
            # Check if event has meeting URL
            if meeting_url:
                return True
            
            # Check event type
            event_type = event.get('eventType', 'default')
            if event_type in ['outOfOffice', 'focusTime']:
                return False
            
            # Check if event has attendees
            attendees = event.get('attendees', [])
            if len(attendees) > 1:
                return True
            
            # Check if event has conference data
            if event.get('conferenceData'):
                return True
            
            # Check event title/keywords
            title = event.get('summary', '').lower()
            meeting_keywords = ['meeting', 'call', 'sync', 'standup', 'review', 'planning']
            if any(keyword in title for keyword in meeting_keywords):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to determine if event is meeting: {e}")
            return False
    
    async def _create_calendar_event(self, event: Dict[str, Any], user_id: str, 
                                   meeting_url: Optional[str], is_meeting: bool) -> Optional[Dict[str, Any]]:
        """Create a new calendar event in database."""
        try:
            event_data = {
                'event_id': event.get('id'),
                'user_id': user_id,
                'calendar_id': event.get('organizer', {}).get('email', 'primary'),
                'title': event.get('summary', ''),
                'description': event.get('description', ''),
                'start_time': event.get('start', {}).get('dateTime'),
                'end_time': event.get('end', {}).get('dateTime'),
                'location': event.get('location', ''),
                'meeting_url': meeting_url,
                'is_meeting': is_meeting,
                'attendees': event.get('attendees', []),
                'status': event.get('status', 'confirmed'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("calendar_events").insert(event_data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None
    
    async def _update_calendar_event(self, event_id: str, event: Dict[str, Any], 
                                   user_id: str, meeting_url: Optional[str], 
                                   is_meeting: bool) -> Optional[Dict[str, Any]]:
        """Update an existing calendar event in database."""
        try:
            update_data = {
                'title': event.get('summary', ''),
                'description': event.get('description', ''),
                'start_time': event.get('start', {}).get('dateTime'),
                'end_time': event.get('end', {}).get('dateTime'),
                'location': event.get('location', ''),
                'meeting_url': meeting_url,
                'is_meeting': is_meeting,
                'attendees': event.get('attendees', []),
                'status': event.get('status', 'confirmed'),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("calendar_events") \
                .update(update_data) \
                .eq("event_id", event_id) \
                .eq("user_id", user_id) \
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to update calendar event: {e}")
            return None
    
    async def _handle_meeting_event(self, event: Dict[str, Any], user_id: str, 
                                  meeting_url: Optional[str]):
        """Handle creation/update of a meeting event."""
        try:
            # Create or update meeting record
            meeting_data = {
                'event_id': event.get('id'),
                'user_id': user_id,
                'title': event.get('summary', ''),
                'start_time': event.get('start', {}).get('dateTime'),
                'end_time': event.get('end', {}).get('dateTime'),
                'meeting_url': meeting_url,
                'attendees': event.get('attendees', []),
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("meetings").upsert(meeting_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to handle meeting event: {e}")
    
    async def _mark_event_deleted(self, event_id: str, user_id: str):
        """Mark a calendar event as deleted."""
        try:
            self.supabase.table("calendar_events") \
                .update({'status': 'cancelled', 'updated_at': datetime.now().isoformat()}) \
                .eq("event_id", event_id) \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to mark event as deleted: {e}")
    
    async def _get_meeting_by_event_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get meeting record by event ID."""
        try:
            result = self.supabase.table("meetings") \
                .select("*") \
                .eq("event_id", event_id) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get meeting by event ID: {e}")
            return None
    
    async def _handle_meeting_deletion(self, meeting_id: str, user_id: str):
        """Handle deletion of a meeting."""
        try:
            self.supabase.table("meetings") \
                .update({'status': 'cancelled', 'updated_at': datetime.now().isoformat()}) \
                .eq("id", meeting_id) \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to handle meeting deletion: {e}")
    
    async def _update_last_sync_time(self, user_id: str, calendar_id: str):
        """Update last sync time for a user's calendar."""
        try:
            sync_data = {
                'user_id': user_id,
                'calendar_id': calendar_id,
                'last_sync_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("calendar_sync_states").upsert(sync_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to update last sync time: {e}")
    
    async def _store_polling_result(self, result: CalendarPollingResult):
        """Store calendar polling result in database."""
        try:
            result_data = result.dict()
            result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            self.supabase.table("calendar_polling_results").insert(result_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store calendar polling result: {e}")
    
    async def _get_smart_polling_metrics(self, user_id: str) -> SmartPollingMetrics:
        """Get smart polling metrics for a user."""
        try:
            result = self.supabase.table("user_sync_states") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                data = result.data
                return SmartPollingMetrics(
                    user_id=user_id,
                    last_poll_at=datetime.fromisoformat(data['last_sync_at'].replace('Z', '+00:00')) if data.get('last_sync_at') else datetime.now(),
                    change_frequency=data.get('change_frequency', 'medium'),
                    next_poll_interval=data.get('next_poll_interval', 30),
                    events_since_last_poll=data.get('events_since_last_poll', 0),
                    meetings_since_last_poll=data.get('meetings_since_last_poll', 0),
                    virtual_emails_detected=data.get('virtual_emails_detected', 0)
                )
            
            # Return default metrics
            return SmartPollingMetrics(
                user_id=user_id,
                last_poll_at=datetime.now(),
                change_frequency='medium',
                next_poll_interval=30,
                events_since_last_poll=0,
                meetings_since_last_poll=0,
                virtual_emails_detected=0
            )
            
        except Exception as e:
            logger.error(f"Failed to get smart polling metrics for user {user_id}: {e}")
            return SmartPollingMetrics(
                user_id=user_id,
                last_poll_at=datetime.now(),
                change_frequency='medium',
                next_poll_interval=30,
                events_since_last_poll=0,
                meetings_since_last_poll=0,
                virtual_emails_detected=0
            )
    
    async def _should_poll_calendar(self, user_id: str, metrics: SmartPollingMetrics) -> bool:
        """Determine if calendar should be polled based on smart metrics."""
        try:
            # Check if enough time has passed since last poll
            time_since_last_poll = datetime.now() - metrics.last_poll_at
            if time_since_last_poll < timedelta(minutes=metrics.next_poll_interval):
                return False
            
            # Check if user has recent activity
            last_activity = await self._get_user_last_activity(user_id)
            if last_activity:
                time_since_activity = datetime.now() - last_activity
                if time_since_activity < timedelta(minutes=15):
                    return False
            
            # Check if user has active meetings coming up
            upcoming_meetings = await self._get_upcoming_meetings(user_id)
            if upcoming_meetings:
                # If user has meetings in next 2 hours, poll more frequently
                next_meeting_time = upcoming_meetings[0].get('start_time')
                if next_meeting_time:
                    meeting_time = datetime.fromisoformat(next_meeting_time.replace('Z', '+00:00'))
                    time_until_meeting = meeting_time - datetime.now()
                    if time_until_meeting < timedelta(hours=2):
                        return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to determine if calendar should be polled: {e}")
            return True
    
    async def _get_upcoming_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's upcoming meetings."""
        try:
            now = datetime.now()
            two_hours_from_now = now + timedelta(hours=2)
            
            result = await self.supabase.table("meetings") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("status", "confirmed") \
                .gte("start_time", now.isoformat()) \
                .lte("start_time", two_hours_from_now.isoformat()) \
                .order("start_time", asc=True) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get upcoming meetings for user {user_id}: {e}")
            return []
    
    async def _update_smart_polling_metrics(self, user_id: str, result: Dict[str, Any]):
        """Update smart polling metrics based on polling results."""
        try:
            # Calculate change frequency based on results
            total_changes = result.get('events_created', 0) + result.get('events_updated', 0) + result.get('events_deleted', 0)
            
            # Get user's meeting schedule pattern
            meeting_pattern = await self._analyze_meeting_pattern(user_id)
            
            # Adjust polling interval based on changes and patterns
            if total_changes == 0:
                if meeting_pattern == 'high_activity':
                    change_frequency = 'medium'
                    next_poll_interval = 30  # 30 minutes for active users
                else:
                    change_frequency = 'low'
                    next_poll_interval = 60  # 1 hour for low activity
            elif total_changes <= 5:
                change_frequency = 'medium'
                next_poll_interval = 20  # 20 minutes
            else:
                change_frequency = 'high'
                next_poll_interval = 10  # 10 minutes for high activity
            
            # Update metrics
            metrics_data = {
                'user_id': user_id,
                'last_sync_at': datetime.now().isoformat(),
                'change_frequency': change_frequency,
                'next_poll_interval': next_poll_interval,
                'events_since_last_poll': total_changes,
                'meetings_since_last_poll': result.get('meetings_detected', 0),
                'updated_at': datetime.now().isoformat()
            }
            
            await self.supabase.table("user_sync_states").upsert(metrics_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to update smart polling metrics: {e}")
    
    async def _analyze_meeting_pattern(self, user_id: str) -> str:
        """Analyze user's meeting pattern to determine activity level."""
        try:
            # Get meetings from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            
            result = await self.supabase.table("meetings") \
                .select("start_time, end_time") \
                .eq("user_id", user_id) \
                .eq("status", "confirmed") \
                .gte("start_time", week_ago.isoformat()) \
                .execute()
            
            if not result.data:
                return 'low_activity'
            
            meetings = result.data
            total_meetings = len(meetings)
            
            # Calculate average meetings per day
            avg_meetings_per_day = total_meetings / 7
            
            if avg_meetings_per_day >= 5:
                return 'high_activity'
            elif avg_meetings_per_day >= 2:
                return 'medium_activity'
            else:
                return 'low_activity'
                
        except Exception as e:
            logger.error(f"Failed to analyze meeting pattern for user {user_id}: {e}")
            return 'medium_activity'
    
    async def _get_user_last_activity(self, user_id: str) -> Optional[datetime]:
        """Get user's last activity timestamp."""
        try:
            result = self.supabase.table("user_activity_logs") \
                .select("timestamp") \
                .eq("user_id", user_id) \
                .order("timestamp", desc=True) \
                .limit(1) \
                .single() \
                .execute()
            
            if result.data and result.data.get('timestamp'):
                return datetime.fromisoformat(result.data['timestamp'].replace('Z', '+00:00'))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last activity for user {user_id}: {e}")
            return None
