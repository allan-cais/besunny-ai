"""
Virtual Email Attendee Service for BeSunny.ai Python backend.
Handles detection and processing of virtual email attendees (ai+{username}@besunny.ai)
in calendar events and automatically schedules attendee bots.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ...core.database import get_supabase
from ...core.config import get_settings
from .attendee_service import AttendeeService

logger = logging.getLogger(__name__)


class VirtualEmailAttendeeService:
    """Service for handling virtual email attendees and auto-scheduling bots."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.attendee_service = AttendeeService()
        
        logger.info("Virtual Email Attendee Service initialized")
    
    async def process_calendar_event_for_virtual_emails(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a calendar event to detect virtual email attendees and auto-schedule bots.
        
        Args:
            event_data: Google Calendar event data
            
        Returns:
            Processing result with details about virtual email attendees found and bots scheduled
        """
        try:
            # Extract virtual email attendees
            virtual_attendees = self._extract_virtual_email_attendees(event_data)
            
            if not virtual_attendees:
                return {
                    'processed': False,
                    'message': 'No virtual email attendees found',
                    'virtual_attendees': [],
                    'bots_scheduled': 0
                }
            
            logger.info(f"Found {len(virtual_attendees)} virtual email attendees in event {event_data.get('id')}")
            
            # Process each virtual email attendee
            bots_scheduled = 0
            processing_results = []
            
            for attendee in virtual_attendees:
                result = await self._process_virtual_email_attendee(attendee, event_data)
                processing_results.append(result)
                
                if result.get('bot_scheduled'):
                    bots_scheduled += 1
            
            return {
                'processed': True,
                'message': f'Processed {len(virtual_attendees)} virtual email attendees, scheduled {bots_scheduled} bots',
                'virtual_attendees': virtual_attendees,
                'bots_scheduled': bots_scheduled,
                'processing_results': processing_results
            }
            
        except Exception as e:
            logger.error(f"Failed to process calendar event for virtual emails: {e}")
            return {
                'processed': False,
                'error': str(e),
                'virtual_attendees': [],
                'bots_scheduled': 0
            }
    
    def _extract_virtual_email_attendees(self, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract virtual email attendees from calendar event data.
        
        Args:
            event_data: Google Calendar event data
            
        Returns:
            List of virtual email attendee information
        """
        virtual_attendees = []
        
        try:
            attendees = event_data.get('attendees', [])
            if not attendees:
                return virtual_attendees
            
            # Pattern to match ai+{username}@besunny.ai
            virtual_email_pattern = r'ai\+([^@]+)@besunny\.ai'
            
            for attendee in attendees:
                if isinstance(attendee, dict) and attendee.get('email'):
                    email = attendee['email']
                    match = re.search(virtual_email_pattern, email)
                    
                    if match:
                        username = match.group(1)
                        virtual_attendees.append({
                            'email': email,
                            'username': username,
                            'response_status': attendee.get('responseStatus', 'needsAction'),
                            'self': attendee.get('self', False),
                            'organizer': attendee.get('organizer', False)
                        })
            
            return virtual_attendees
            
        except Exception as e:
            logger.error(f"Failed to extract virtual email attendees: {e}")
            return []
    
    async def _process_virtual_email_attendee(self, attendee: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single virtual email attendee and schedule a bot if appropriate.
        
        Args:
            attendee: Virtual email attendee information
            event_data: Google Calendar event data
            
        Returns:
            Processing result for this attendee
        """
        try:
            username = attendee['username']
            virtual_email = attendee['email']
            
            # Find user by username
            user = await self._get_user_by_username(username)
            if not user:
                return {
                    'username': username,
                    'virtual_email': virtual_email,
                    'user_found': False,
                    'bot_scheduled': False,
                    'error': 'User not found'
                }
            
            # Check if this is a video conference event
            meeting_url = self._extract_meeting_url(event_data)
            if not meeting_url or not self._is_video_conference_url(meeting_url):
                return {
                    'username': username,
                    'virtual_email': virtual_email,
                    'user_found': True,
                    'bot_scheduled': False,
                    'reason': 'Not a video conference event'
                }
            
            # Check if bot is already scheduled for this user and meeting
            existing_bot = await self._check_existing_bot(event_data.get('id'), user['id'])
            if existing_bot:
                return {
                    'username': username,
                    'virtual_email': virtual_email,
                    'user_found': True,
                    'bot_scheduled': True,
                    'reason': 'Bot already scheduled',
                    'bot_id': existing_bot.get('attendee_bot_id')
                }
            
            # Schedule attendee bot
            bot_result = await self._schedule_attendee_bot(user['id'], meeting_url, event_data, attendee)
            
            if bot_result.get('success'):
                # Store meeting record with bot information
                meeting_id = await self._store_meeting_with_bot(event_data, user['id'], bot_result, attendee)
                
                return {
                    'username': username,
                    'virtual_email': virtual_email,
                    'user_found': True,
                    'bot_scheduled': True,
                    'bot_id': bot_result.get('bot_id'),
                    'meeting_id': meeting_id,
                    'message': 'Bot scheduled successfully'
                }
            else:
                return {
                    'username': username,
                    'virtual_email': virtual_email,
                    'user_found': True,
                    'bot_scheduled': False,
                    'error': bot_result.get('error', 'Failed to schedule bot')
                }
                
        except Exception as e:
            logger.error(f"Failed to process virtual email attendee {attendee.get('username')}: {e}")
            return {
                'username': attendee.get('username'),
                'virtual_email': attendee.get('email'),
                'user_found': False,
                'bot_scheduled': False,
                'error': str(e)
            }
    
    async def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        try:
            result = await self.supabase.table('users').select('id, email, username').eq('username', username).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None
    
    async def _check_existing_bot(self, event_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if a bot is already scheduled for this event and user."""
        try:
            result = await self.supabase.table('meetings').select(
                'id, attendee_bot_id, bot_status, bot_configuration'
            ).eq('google_calendar_event_id', event_id).eq('user_id', user_id).single().execute()
            
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to check existing bot: {e}")
            return None
    
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
                meet_regex = r'https://meet\.google\.com/[a-z-]+'
                match = re.search(meet_regex, event_data['description'])
                if match:
                    return match.group(0)
            
            # Check for other video conferencing URLs
            video_urls = [
                r'https://zoom\.us/j/\d+',
                r'https://teams\.microsoft\.com/l/meetup-join/[^\s]+',
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
    
    async def _schedule_attendee_bot(self, user_id: str, meeting_url: str, event_data: Dict[str, Any], attendee: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an attendee bot for a meeting."""
        try:
            # Prepare bot configuration with automatic deployment method
            bot_options = {
                'meeting_url': meeting_url,
                'bot_name': 'Sunny AI Notetaker',
                'bot_chat_message': 'Hi, I\'m here to transcribe this meeting!',
                'deployment_method': 'automatic'  # Mark as auto-scheduled for virtual email
            }
            
            # Create bot using Attendee service with comprehensive webhook configuration
            result = await self.attendee_service.create_bot_for_meeting(bot_options, user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to schedule attendee bot: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _store_meeting_with_bot(self, event_data: Dict[str, Any], user_id: str, bot_result: Dict[str, Any], attendee: Dict[str, Any]) -> Optional[str]:
        """Store meeting record with bot information."""
        try:
            meeting_url = self._extract_meeting_url(event_data)
            
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
                'is_meeting': True,
                'attendee_bot_id': bot_result.get('bot_id'),
                'bot_status': 'bot_scheduled',
                'bot_deployment_method': 'automatic',
                'auto_scheduled_via_email': True,
                'virtual_email_attendee': attendee['email'],
                'bot_configuration': {
                    'provider': 'attendee',
                    'bot_id': bot_result.get('bot_id'),
                    'project_id': bot_result.get('project_id'),
                    'auto_scheduled': True,
                    'username': attendee['username']
                },
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = await self.supabase.table('meetings').insert(meeting_data).execute()
            
            if result.data:
                meeting_id = result.data[0]['id']
                logger.info(f"Created meeting {meeting_id} with auto-scheduled bot for virtual email {attendee['email']}")
                return meeting_id
            else:
                logger.error(f"Failed to create meeting for virtual email {attendee['email']}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to store meeting with bot: {e}")
            return None
    
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
    
    async def get_virtual_email_activity(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get virtual email activity for a user."""
        try:
            # Get meetings with virtual email attendees
            result = await self.supabase.table('meetings').select(
                'id, title, start_time, virtual_email_attendee, bot_status, attendee_bot_id'
            ).eq('user_id', user_id).eq('auto_scheduled_via_email', True).gte(
                'created_at', (datetime.now() - timedelta(days=days)).isoformat()
            ).order('created_at', desc=True).execute()
            
            meetings = result.data or []
            
            # Get bot status summary
            bot_statuses = {}
            for meeting in meetings:
                status = meeting.get('bot_status', 'unknown')
                bot_statuses[status] = bot_statuses.get(status, 0) + 1
            
            return {
                'total_meetings': len(meetings),
                'bot_statuses': bot_statuses,
                'meetings': meetings,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get virtual email activity for user {user_id}: {e}")
            return {
                'total_meetings': 0,
                'bot_statuses': {},
                'meetings': [],
                'period_days': days,
                'error': str(e)
            }
