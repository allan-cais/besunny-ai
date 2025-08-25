"""
Attendee polling cron service for BeSunny.ai Python backend.
Handles periodic polling of attendee bots and virtual email attendee processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from celery import Celery

from ...core.database import get_supabase
from ...core.config import get_settings
from ...core.celery_app import celery_app
from .attendee_service import AttendeeService
from .virtual_email_attendee_service import VirtualEmailAttendeeService

logger = logging.getLogger(__name__)


class AttendeePollingCron:
    """Cron service for attendee bot polling and virtual email processing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.attendee_service = AttendeeService()
        self.virtual_email_service = VirtualEmailAttendeeService()
        
        logger.info("Attendee Polling Cron Service initialized")
    
    async def run_virtual_email_processing_cron(self) -> Dict[str, Any]:
        """
        Run the virtual email attendee processing cron job.
        
        This job:
        1. Finds calendar events with virtual email attendees
        2. Auto-schedules attendee bots for meetings
        3. Updates meeting records with bot information
        
        Returns:
            Cron job execution results
        """
        start_time = datetime.now()
        execution_id = f"virtual_email_cron_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting virtual email processing cron job {execution_id}")
            
            # Get all users with usernames (who can have virtual emails)
            users = await self._get_users_with_usernames()
            
            if not users:
                return {
                    'execution_id': execution_id,
                    'success': True,
                    'message': 'No users with usernames found',
                    'users_processed': 0,
                    'meetings_processed': 0,
                    'bots_scheduled': 0,
                    'execution_time_ms': 0
                }
            
            total_meetings_processed = 0
            total_bots_scheduled = 0
            user_results = []
            
            # Process each user's calendar for virtual email attendees
            for user in users:
                try:
                    user_result = await self._process_user_virtual_emails(user)
                    user_results.append(user_result)
                    
                    total_meetings_processed += user_result.get('meetings_processed', 0)
                    total_bots_scheduled += user_result.get('bots_scheduled', 0)
                    
                except Exception as e:
                    logger.error(f"Failed to process virtual emails for user {user['id']}: {e}")
                    user_results.append({
                        'user_id': user['id'],
                        'username': user.get('username'),
                        'success': False,
                        'error': str(e)
                    })
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log cron execution
            await self._log_cron_execution(
                execution_id, 'virtual_email_processing', len(users), 
                total_meetings_processed, total_bots_scheduled, execution_time, 'completed'
            )
            
            return {
                'execution_id': execution_id,
                'success': True,
                'message': f'Processed {len(users)} users, {total_meetings_processed} meetings, {total_bots_scheduled} bots scheduled',
                'users_processed': len(users),
                'meetings_processed': total_meetings_processed,
                'bots_scheduled': total_bots_scheduled,
                'execution_time_ms': round(execution_time, 2),
                'user_results': user_results
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Virtual email processing cron job failed: {e}")
            
            # Log failed execution
            await self._log_cron_execution(
                execution_id, 'virtual_email_processing', 0, 0, 0, execution_time, 'failed', str(e)
            )
            
            return {
                'execution_id': execution_id,
                'success': False,
                'error': str(e),
                'execution_time_ms': round(execution_time, 2)
            }
    
    async def _process_user_virtual_emails(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Process virtual emails for a specific user."""
        try:
            user_id = user['id']
            username = user.get('username')
            
            logger.info(f"Processing virtual emails for user {user_id} (username: {username})")
            
            # Get upcoming meetings with virtual email attendees
            activity_result = await self.virtual_email_service.get_virtual_email_activity(user_id, days=7)
            
            meetings = activity_result.get('meetings', [])
            meetings_processed = 0
            bots_scheduled = 0
            
            # Process each meeting that needs a bot
            for meeting in meetings:
                if meeting.get('bot_status') == 'pending':
                    try:
                        # Fetch the calendar event from Google Calendar
                        event_data = await self._fetch_calendar_event(meeting.get('google_calendar_event_id'), user_id)
                        
                        if event_data:
                            # Process the event for virtual email attendees
                            result = await self.virtual_email_service.process_calendar_event_for_virtual_emails(event_data)
                            
                            if result.get('processed'):
                                meetings_processed += 1
                                bots_scheduled += result.get('bots_scheduled', 0)
                                
                                logger.info(f"Processed meeting {meeting['id']} for user {user_id}, scheduled {result.get('bots_scheduled', 0)} bots")
                        
                    except Exception as e:
                        logger.error(f"Failed to process meeting {meeting.get('id')} for user {user_id}: {e}")
                        continue
            
            return {
                'user_id': user_id,
                'username': username,
                'success': True,
                'meetings_processed': meetings_processed,
                'bots_scheduled': bots_scheduled,
                'total_meetings': len(meetings)
            }
            
        except Exception as e:
            logger.error(f"Failed to process virtual emails for user {user.get('id')}: {e}")
            return {
                'user_id': user.get('id'),
                'username': user.get('username'),
                'success': False,
                'error': str(e)
            }
    
    async def _fetch_calendar_event(self, event_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch calendar event data from Google Calendar."""
        try:
            # This would integrate with the Google Calendar service
            # For now, we'll return None and implement this later
            logger.info(f"Would fetch calendar event {event_id} for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch calendar event {event_id}: {e}")
            return None
    
    async def _get_users_with_usernames(self) -> List[Dict[str, Any]]:
        """Get all users who have usernames set."""
        try:
            result = await self.supabase.table('users').select('id, username, email').not_.is_('username', None).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get users with usernames: {e}")
            return []
    
    async def _log_cron_execution(self, execution_id: str, job_type: str, users_processed: int, 
                                 meetings_processed: int, bots_scheduled: int, execution_time_ms: float, 
                                 status: str, error_message: Optional[str] = None):
        """Log cron job execution details."""
        try:
            log_data = {
                'execution_id': execution_id,
                'job_type': job_type,
                'users_processed': users_processed,
                'meetings_processed': meetings_processed,
                'bots_scheduled': bots_scheduled,
                'execution_time_ms': execution_time_ms,
                'status': status,
                'error_message': error_message,
                'executed_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('cron_execution_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log cron execution: {e}")
    
    async def run_attendee_bot_polling_cron(self) -> Dict[str, Any]:
        """
        Run the attendee bot polling cron job.
        
        This job:
        1. Polls all active attendee bots for status updates
        2. Retrieves transcripts and chat messages
        3. Updates meeting records with latest information
        
        Returns:
            Cron job execution results
        """
        start_time = datetime.now()
        execution_id = f"attendee_polling_cron_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting attendee bot polling cron job {execution_id}")
            
            # Get all active attendee bots
            active_bots = await self._get_active_attendee_bots()
            
            if not active_bots:
                return {
                    'execution_id': execution_id,
                    'success': True,
                    'message': 'No active attendee bots found',
                    'bots_processed': 0,
                    'execution_time_ms': 0
                }
            
            bots_processed = 0
            bot_results = []
            
            # Poll each bot for updates
            for bot in active_bots:
                try:
                    bot_result = await self._poll_bot_for_updates(bot)
                    bot_results.append(bot_result)
                    
                    if bot_result.get('success'):
                        bots_processed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to poll bot {bot.get('bot_id')}: {e}")
                    bot_results.append({
                        'bot_id': bot.get('bot_id'),
                        'success': False,
                        'error': str(e)
                    })
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log cron execution
            await self._log_cron_execution(
                execution_id, 'attendee_bot_polling', 0, 0, 0, execution_time, 'completed'
            )
            
            return {
                'execution_id': execution_id,
                'success': True,
                'message': f'Polled {len(active_bots)} bots, {bots_processed} successfully updated',
                'bots_processed': bots_processed,
                'total_bots': len(active_bots),
                'execution_time_ms': round(execution_time, 2),
                'bot_results': bot_results
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Attendee bot polling cron job failed: {e}")
            
            # Log failed execution
            await self._log_cron_execution(
                execution_id, 'attendee_bot_polling', 0, 0, 0, execution_time, 'failed', str(e)
            )
            
            return {
                'execution_id': execution_id,
                'success': False,
                'error': str(e),
                'execution_time_ms': round(execution_time, 2)
            }
    
    async def _get_active_attendee_bots(self) -> List[Dict[str, Any]]:
        """Get all active attendee bots."""
        try:
            result = await self.supabase.table('meeting_bots').select('*').eq('status', 'active').execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get active attendee bots: {e}")
            return []
    
    async def _poll_bot_for_updates(self, bot: Dict[str, Any]) -> Dict[str, Any]:
        """Poll a specific bot for updates."""
        try:
            bot_id = bot['bot_id']
            
            # Get bot status
            status_result = await self.attendee_service.get_bot_status(bot_id)
            
            if not status_result:
                return {
                    'bot_id': bot_id,
                    'success': False,
                    'error': 'Failed to get bot status'
                }
            
            # Get transcript if available
            transcript_result = await self.attendee_service.get_transcript(bot_id)
            
            # Get chat messages
            chat_messages = await self.attendee_service.get_chat_messages(bot_id)
            
            # Update bot record with latest information
            await self._update_bot_record(bot_id, status_result, transcript_result, chat_messages)
            
            return {
                'bot_id': bot_id,
                'success': True,
                'status_updated': True,
                'transcript_updated': transcript_result is not None,
                'chat_messages_count': len(chat_messages) if chat_messages else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to poll bot {bot.get('bot_id')}: {e}")
            return {
                'bot_id': bot.get('bot_id'),
                'success': False,
                'error': str(e)
            }
    
    async def _update_bot_record(self, bot_id: str, status_data: Dict[str, Any], 
                                transcript_data: Optional[Dict[str, Any]], chat_messages: List[Dict[str, Any]]):
        """Update bot record with latest information."""
        try:
            update_data = {
                'status': status_data.get('status'),
                'is_recording': status_data.get('is_recording', False),
                'is_paused': status_data.get('is_paused', False),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add transcript information if available
            if transcript_data:
                update_data['transcript_retrieved_at'] = datetime.now().isoformat()
                update_data['transcript_duration_seconds'] = transcript_data.get('duration_minutes', 0) * 60
            
            await self.supabase.table('meeting_bots').update(update_data).eq('bot_id', bot_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update bot record {bot_id}: {e}")


    # Additional methods for tasks compatibility
    async def execute_polling_cron(self) -> Dict[str, Any]:
        """Execute the main polling cron job."""
        try:
            # Run both cron jobs
            virtual_email_result = await self.run_virtual_email_processing_cron()
            bot_polling_result = await self.run_attendee_bot_polling_cron()
            
            return {
                'virtual_email_processing': virtual_email_result,
                'attendee_bot_polling': bot_polling_result,
                'success': True
            }
        except Exception as e:
            logger.error(f"Execute polling cron failed: {e}")
            return {'success': False, 'error': str(e)}

    async def poll_all_user_meetings(self, user_id: str) -> Dict[str, Any]:
        """Poll all meetings for a specific user."""
        try:
            # Get user's calendar events
            user = await self._get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Process virtual emails for this user
            result = await self._process_user_virtual_emails(user)
            return result
        except Exception as e:
            logger.error(f"Poll all user meetings failed for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def poll_all_active_meetings(self) -> Dict[str, Any]:
        """Poll all active meetings for all users."""
        try:
            users = await self._get_users_with_usernames()
            if not users:
                return {'success': True, 'message': 'No users found', 'meetings_processed': 0}
            
            total_meetings_processed = 0
            for user in users:
                try:
                    result = await self._process_user_virtual_emails(user)
                    total_meetings_processed += result.get('meetings_processed', 0)
                except Exception as e:
                    logger.error(f"Failed to process user {user['id']}: {e}")
            
            return {
                'success': True,
                'total_meetings_processed': total_meetings_processed,
                'users_processed': len(users)
            }
        except Exception as e:
            logger.error(f"Poll all active meetings failed: {e}")
            return {'success': False, 'error': str(e)}

    async def auto_schedule_user_bots(self, user_id: str) -> Dict[str, Any]:
        """Auto-schedule bots for a specific user."""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Process virtual emails for this user (which includes bot scheduling)
            result = await self._process_user_virtual_emails(user)
            return result
        except Exception as e:
            logger.error(f"Auto-schedule user bots failed for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def auto_schedule_all_bots(self) -> Dict[str, Any]:
        """Auto-schedule bots for all users."""
        try:
            users = await self._get_users_with_usernames()
            if not users:
                return {'success': True, 'message': 'No users found', 'bots_scheduled': 0}
            
            total_bots_scheduled = 0
            for user in users:
                try:
                    result = await self._process_user_virtual_emails(user)
                    total_bots_scheduled += result.get('bots_scheduled', 0)
                except Exception as e:
                    logger.error(f"Failed to process user {user['id']}: {e}")
            
            return {
                'success': True,
                'total_bots_scheduled': total_bots_scheduled,
                'users_processed': len(users)
            }
        except Exception as e:
            logger.error(f"Auto-schedule all bots failed: {e}")
            return {'success': False, 'error': str(e)}

    async def cleanup_completed_meetings(self) -> Dict[str, Any]:
        """Clean up completed meetings and transcripts."""
        try:
            # This is a placeholder implementation
            # You can implement actual cleanup logic here
            logger.info("Cleanup completed meetings called")
            return {
                'success': True,
                'message': 'Cleanup completed meetings placeholder',
                'meetings_cleaned': 0
            }
        except Exception as e:
            logger.error(f"Cleanup completed meetings failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            result = await self.supabase.table('users').select('*').eq('id', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None


# Celery tasks for cron jobs
@celery_app.task
def run_virtual_email_processing_cron():
    """Celery task to run virtual email processing cron job."""
    try:
        cron_service = AttendeePollingCron()
        result = asyncio.run(cron_service.run_virtual_email_processing_cron())
        return result
    except Exception as e:
        logger.error(f"Virtual email processing cron task failed: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task
def run_attendee_bot_polling_cron():
    """Celery task to run attendee bot polling cron job."""
    try:
        cron_service = AttendeePollingCron()
        result = asyncio.run(cron_service.run_attendee_bot_polling_cron())
        return result
    except Exception as e:
        logger.error(f"Attendee bot polling cron task failed: {e}")
        return {'success': False, 'error': str(e)}
