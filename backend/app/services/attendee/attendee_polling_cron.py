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
    
    async def monitor_calendar_bot_workflow(
        self, 
        bot_id: str, 
        meeting_id: str, 
        user_id: str, 
        document_id: str, 
        username: str
    ) -> Dict[str, Any]:
        """
        Monitor a calendar bot and process transcript when meeting ends.
        
        This workflow:
        1. Waits for webhook notification that bot has ended
        2. Retrieves transcript when available
        3. Stores transcript in documents table
        4. Sends through classification agent
        5. Sends through vector embedding pipeline
        
        Args:
            bot_id: The bot ID to monitor
            meeting_id: The meeting ID
            user_id: The user ID
            document_id: The original email document ID
            username: The username
            
        Returns:
            Workflow execution results
        """
        try:
            logger.info(f"Starting calendar bot workflow for bot {bot_id}, meeting {meeting_id}")
            
            # Step 1: Wait for webhook notification that bot has ended
            ended_webhook = await self._wait_for_bot_ended_webhook(bot_id, user_id, max_wait_minutes=60)
            
            if not ended_webhook:
                return {
                    'success': False,
                    'error': 'Bot ended webhook not received within timeout period',
                    'bot_id': bot_id,
                    'meeting_id': meeting_id
                }
            
            # Step 2: Get transcript when bot is ended
            transcript_data = await self.attendee_service.get_transcript(bot_id)
            
            if not transcript_data:
                return {
                    'success': False,
                    'error': 'No transcript available for ended bot',
                    'bot_id': bot_id,
                    'meeting_id': meeting_id
                }
            
            # Step 3: Store transcript in documents table
            transcript_document_id = await self._store_transcript_document(
                transcript_data, bot_id, meeting_id, user_id, username
            )
            
            if not transcript_document_id:
                return {
                    'success': False,
                    'error': 'Failed to store transcript document',
                    'bot_id': bot_id,
                    'meeting_id': meeting_id
                }
            
            # Step 4: Send through classification agent
            classification_result = await self._classify_transcript(
                transcript_data, transcript_document_id, user_id, username
            )
            
            # Step 5: Send through vector embedding pipeline
            embedding_result = await self._embed_transcript(
                transcript_data, classification_result, transcript_document_id, user_id
            )
            
            # Step 6: Update meeting record with transcript information
            await self._update_meeting_with_transcript(
                meeting_id, transcript_data, transcript_document_id, classification_result
            )
            
            logger.info(f"Calendar bot workflow completed for bot {bot_id}")
            
            return {
                'success': True,
                'bot_id': bot_id,
                'meeting_id': meeting_id,
                'transcript_document_id': transcript_document_id,
                'classification_result': classification_result,
                'embedding_result': embedding_result,
                'message': 'Calendar bot workflow completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Calendar bot workflow failed for bot {bot_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bot_id': bot_id,
                'meeting_id': meeting_id
            }
    
    async def _wait_for_bot_ended_webhook(self, bot_id: str, user_id: str, max_wait_minutes: int = 60) -> Optional[Dict[str, Any]]:
        """Wait for webhook notification that bot has ended."""
        try:
            logger.info(f"Waiting for bot ended webhook for bot {bot_id} (max wait: {max_wait_minutes} minutes)")
            
            # Check for existing ended webhook first
            ended_webhook = await self._check_for_ended_webhook(bot_id, user_id)
            if ended_webhook:
                logger.info(f"Found existing ended webhook for bot {bot_id}")
                return ended_webhook
            
            # Wait for webhook notification with periodic checks
            max_attempts = max_wait_minutes * 2  # Check every 30 seconds
            for attempt in range(max_attempts):
                logger.info(f"Checking for bot ended webhook (attempt {attempt + 1}/{max_attempts})")
                
                ended_webhook = await self._check_for_ended_webhook(bot_id, user_id)
                if ended_webhook:
                    logger.info(f"Bot {bot_id} ended webhook received")
                    return ended_webhook
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
            
            logger.warning(f"Bot {bot_id} ended webhook not received within {max_wait_minutes} minutes")
            return None
            
        except Exception as e:
            logger.error(f"Error waiting for bot ended webhook: {e}")
            return None
    
    async def _check_for_ended_webhook(self, bot_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if there's an ended webhook for the bot."""
        try:
            # Query attendee_webhook_logs for bot.state_change webhooks with ended status
            result = await self.supabase.table('attendee_webhook_logs').select('*').eq('bot_id', bot_id).eq('user_id', user_id).eq('trigger', 'bot.state_change').order('received_at', desc=True).execute()
            
            if not result.data:
                return None
            
            # Check each webhook for ended status
            for webhook_log in result.data:
                webhook_data = webhook_log.get('webhook_data', {})
                
                # Check if the webhook indicates the bot has ended
                if self._is_bot_ended_webhook(webhook_data):
                    logger.info(f"Found ended webhook for bot {bot_id}: {webhook_log['id']}")
                    return webhook_log
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for ended webhook: {e}")
            return None
    
    def _is_bot_ended_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Check if webhook data indicates bot has ended."""
        try:
            # Check various possible fields that might indicate bot ended
            status = webhook_data.get('status', '').lower()
            event_type = webhook_data.get('event_type', '').lower()
            state = webhook_data.get('state', '').lower()
            
            # Check for ended status indicators
            ended_indicators = ['ended', 'completed', 'finished', 'stopped']
            
            if status in ended_indicators or event_type in ended_indicators or state in ended_indicators:
                return True
            
            # Check for specific bot state changes
            if event_type == 'bot.state_change':
                new_state = webhook_data.get('new_state', '').lower()
                if new_state in ended_indicators:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking bot ended webhook: {e}")
            return False
    
    async def _store_transcript_document(
        self, 
        transcript_data: Dict[str, Any], 
        bot_id: str, 
        meeting_id: str, 
        user_id: str, 
        username: str
    ) -> Optional[str]:
        """Store transcript in documents table."""
        try:
            # Extract transcript text
            transcript_text = transcript_data.get('transcript', '')
            if not transcript_text:
                logger.warning(f"No transcript text found for bot {bot_id}")
                return None
            
            # Create document record
            document_data = {
                'title': f'Meeting Transcript - {username}',
                'summary': transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text,
                'author': f'Bot {bot_id}',
                'received_at': datetime.now().isoformat(),
                'source': 'attendee_bot',
                'source_id': bot_id,
                'type': 'transcript',
                'status': 'processed',
                'created_at': datetime.now().isoformat(),
                'created_by': username,
                'project_id': None,  # Will be assigned by classification
                'knowledge_space_id': None,
                'metadata': {
                    'bot_id': bot_id,
                    'meeting_id': meeting_id,
                    'transcript_duration': transcript_data.get('duration_minutes', 0),
                    'participants': transcript_data.get('participants', []),
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            result = await self.supabase.table('documents').insert(document_data).execute()
            
            if result.data:
                document_id = result.data[0]['id']
                logger.info(f"Transcript document stored: {document_id}")
                return document_id
            else:
                logger.error("No document ID returned from transcript insert")
                return None
                
        except Exception as e:
            logger.error(f"Error storing transcript document: {e}")
            return None
    
    async def _classify_transcript(
        self, 
        transcript_data: Dict[str, Any], 
        document_id: str, 
        user_id: str, 
        username: str
    ) -> Dict[str, Any]:
        """Send transcript through classification agent."""
        try:
            from ...services.ai.classification_service import ClassificationService
            
            classification_service = ClassificationService()
            
            # Prepare content for classification
            content = {
                'type': 'transcript',
                'source_id': document_id,
                'author': f'Bot for {username}',
                'date': datetime.now().isoformat(),
                'subject': f'Meeting Transcript - {username}',
                'content_text': transcript_data.get('transcript', ''),
                'metadata': {
                    'bot_id': transcript_data.get('bot_id'),
                    'meeting_id': transcript_data.get('meeting_id'),
                    'duration_minutes': transcript_data.get('duration_minutes', 0),
                    'participants': transcript_data.get('participants', [])
                }
            }
            
            # Classify the transcript
            classification_result = await classification_service.classify_content(
                content=content,
                user_id=user_id
            )
            
            logger.info(f"Transcript classified for {username}: {classification_result.get('project_id', 'unclassified')}")
            return classification_result
            
        except Exception as e:
            logger.error(f"Error classifying transcript: {e}")
            return {
                'project_id': '',
                'confidence': 0.0,
                'unclassified': True,
                'error': str(e)
            }
    
    async def _embed_transcript(
        self, 
        transcript_data: Dict[str, Any], 
        classification_result: Dict[str, Any], 
        document_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Send transcript through vector embedding pipeline."""
        try:
            from ...services.ai.vector_embedding_service import VectorEmbeddingService
            
            vector_service = VectorEmbeddingService()
            
            # Prepare content for embedding
            content = {
                'type': 'transcript',
                'source_id': document_id,
                'author': f'Bot for {transcript_data.get("username", "unknown")}',
                'date': datetime.now().isoformat(),
                'subject': f'Meeting Transcript',
                'content_text': transcript_data.get('transcript', ''),
                'metadata': {
                    'bot_id': transcript_data.get('bot_id'),
                    'meeting_id': transcript_data.get('meeting_id'),
                    'duration_minutes': transcript_data.get('duration_minutes', 0),
                    'participants': transcript_data.get('participants', [])
                }
            }
            
            # Embed the content
            embedding_result = await vector_service.embed_classified_content(
                content=content,
                classification_result=classification_result,
                user_id=user_id
            )
            
            logger.info(f"Transcript embedded: {embedding_result.get('embedded', False)}")
            return embedding_result
            
        except Exception as e:
            logger.error(f"Error embedding transcript: {e}")
            return {
                'embedded': False,
                'error': str(e)
            }
    
    async def _update_meeting_with_transcript(
        self, 
        meeting_id: str, 
        transcript_data: Dict[str, Any], 
        document_id: str, 
        classification_result: Dict[str, Any]
    ):
        """Update meeting record with transcript information."""
        try:
            update_data = {
                'transcript': transcript_data.get('transcript', ''),
                'transcript_url': transcript_data.get('transcript_url'),
                'transcript_retrieved_at': datetime.now().isoformat(),
                'transcript_duration_seconds': transcript_data.get('duration_minutes', 0) * 60,
                'transcript_participants': transcript_data.get('participants', []),
                'transcript_processing_status': 'completed',
                'project_id': classification_result.get('project_id') if not classification_result.get('unclassified') else None,
                'updated_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
            logger.info(f"Meeting {meeting_id} updated with transcript information")
            
        except Exception as e:
            logger.error(f"Error updating meeting with transcript: {e}")


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
