"""
Attendee polling cron service for BeSunny.ai Python backend.
Handles scheduled meeting polling and batch operations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .attendee_polling_service import AttendeePollingService

logger = logging.getLogger(__name__)


class CronExecutionResult(BaseModel):
    """Result of a cron job execution."""
    execution_id: str
    start_time: datetime
    end_time: datetime
    total_users: int
    successful_polls: int
    failed_polls: int
    total_processing_time_ms: int
    status: str
    error_message: Optional[str] = None


class CronJobMetrics(BaseModel):
    """Metrics for cron job performance."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_processing_time_ms: float
    last_execution: Optional[datetime]
    last_success: Optional[datetime]
    last_failure: Optional[datetime]


class AttendeePollingCronService:
    """Service for executing scheduled attendee polling operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.polling_service = AttendeePollingService()
        
        logger.info("Attendee Polling Cron Service initialized")
    
    async def execute_polling_cron(self) -> Dict[str, Any]:
        """
        Execute the main polling cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting attendee polling cron execution {execution_id}")
            
            # Get all active users with meeting bots
            active_users = await self._get_active_users_with_bots()
            if not active_users:
                logger.info("No active users with meeting bots found")
                return await self._create_cron_result(
                    execution_id, start_time, 0, 0, 0, 0, "completed", None
                )
            
            # Execute polling for each user
            successful_polls = 0
            failed_polls = 0
            total_processing_time = 0
            
            for user in active_users:
                try:
                    user_start_time = datetime.now()
                    
                    # Execute smart polling for user
                    result = await self.polling_service.smart_polling(user['id'])
                    
                    user_processing_time = (datetime.now() - user_start_time).microseconds // 1000
                    total_processing_time += user_processing_time
                    
                    if result and not result.get('skipped'):
                        if result.get('error'):
                            failed_polls += 1
                            logger.warning(f"User {user['id']} polling failed: {result.get('error')}")
                        else:
                            successful_polls += 1
                            logger.info(f"User {user['id']} polling completed successfully")
                    else:
                        logger.info(f"User {user['id']} polling skipped: {result.get('reason', 'Unknown')}")
                        
                except Exception as e:
                    failed_polls += 1
                    logger.error(f"Failed to poll user {user['id']}: {e}")
                    continue
            
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            
            # Create execution result
            cron_result = await self._create_cron_result(
                execution_id, start_time, len(active_users), 
                successful_polls, failed_polls, total_processing_time, 
                "completed", None
            )
            
            # Update metrics
            await self._update_cron_metrics(execution_id, cron_result)
            
            logger.info(f"Attendee polling cron execution {execution_id} completed successfully")
            return cron_result
            
        except Exception as e:
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            
            error_message = str(e)
            logger.error(f"Attendee polling cron execution {execution_id} failed: {error_message}")
            
            # Create failed execution result
            cron_result = await self._create_cron_result(
                execution_id, start_time, 0, 0, 0, total_processing_time, 
                "failed", error_message
            )
            
            # Update metrics
            await self._update_cron_metrics(execution_id, cron_result)
            
            return cron_result
    
    async def poll_all_active_meetings(self) -> Dict[str, Any]:
        """
        Poll all active meetings across all users.
        
        Returns:
            Batch polling results
        """
        try:
            start_time = datetime.now()
            logger.info("Starting batch polling of all active meetings")
            
            # Get all active meetings
            active_meetings = await self._get_all_active_meetings()
            if not active_meetings:
                logger.info("No active meetings found")
                return {
                    'total_meetings': 0,
                    'meetings_polled': 0,
                    'successful_polls': 0,
                    'failed_polls': 0,
                    'processing_time_ms': 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Poll each meeting
            successful_polls = 0
            failed_polls = 0
            
            for meeting in active_meetings:
                try:
                    result = await self.polling_service.poll_meeting_status(meeting['id'])
                    if result:
                        successful_polls += 1
                    else:
                        failed_polls += 1
                except Exception as e:
                    failed_polls += 1
                    logger.error(f"Failed to poll meeting {meeting['id']}: {e}")
                    continue
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).microseconds // 1000
            
            result = {
                'total_meetings': len(active_meetings),
                'meetings_polled': len(active_meetings),
                'successful_polls': successful_polls,
                'failed_polls': failed_polls,
                'processing_time_ms': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Batch polling completed: {successful_polls} successful, {failed_polls} failed")
            return result
            
        except Exception as e:
            logger.error(f"Batch polling failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def handle_cron_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process and analyze cron job results.
        
        Args:
            results: List of cron job results to process
            
        Returns:
            Analysis of cron job results
        """
        try:
            if not results:
                return {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'average_processing_time': 0,
                    'recommendations': []
                }
            
            # Analyze results
            total_executions = len(results)
            successful_executions = len([r for r in results if r.get('status') == 'completed'])
            failed_executions = total_executions - successful_executions
            
            # Calculate average processing time
            total_processing_time = sum(r.get('total_processing_time_ms', 0) for r in results)
            average_processing_time = total_processing_time / total_executions if total_executions > 0 else 0
            
            # Generate recommendations
            recommendations = []
            if failed_executions > 0:
                recommendations.append(f"Investigate {failed_executions} failed cron executions")
            
            if average_processing_time > 30000:  # 30 seconds
                recommendations.append("Cron job is taking too long, consider optimization")
            
            if failed_executions / total_executions > 0.1:  # More than 10% failure rate
                recommendations.append("High failure rate detected, check system health")
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'average_processing_time': average_processing_time,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to handle cron results: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_cron_metrics(self) -> CronJobMetrics:
        """
        Get performance metrics for the cron job.
        
        Returns:
            Cron job performance metrics
        """
        try:
            # Get recent executions
            result = self.supabase.table("cron_executions") \
                .select("*") \
                .eq("job_type", "attendee_polling") \
                .order("start_time", desc=True) \
                .limit(100) \
                .execute()
            
            executions = result.data if result.data else []
            
            if not executions:
                return CronJobMetrics(
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    average_processing_time_ms=0.0,
                    last_execution=None,
                    last_success=None,
                    last_failure=None
                )
            
            # Calculate metrics
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.get('status') == 'completed'])
            failed_executions = total_executions - successful_executions
            
            # Calculate average processing time
            total_processing_time = sum(e.get('total_processing_time_ms', 0) for e in executions)
            average_processing_time = total_processing_time / total_executions if total_executions > 0 else 0
            
            # Get last execution times
            last_execution = datetime.fromisoformat(executions[0]['start_time'].replace('Z', '+00:00')) if executions else None
            
            last_success = None
            last_failure = None
            
            for execution in executions:
                if execution.get('status') == 'completed' and not last_success:
                    last_success = datetime.fromisoformat(execution['start_time'].replace('Z', '+00:00'))
                elif execution.get('status') == 'failed' and not last_failure:
                    last_failure = datetime.fromisoformat(execution['start_time'].replace('Z', '+00:00'))
                
                if last_success and last_failure:
                    break
            
            return CronJobMetrics(
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                average_processing_time_ms=average_processing_time,
                last_execution=last_execution,
                last_success=last_success,
                last_failure=last_failure
            )
            
        except Exception as e:
            logger.error(f"Failed to get cron metrics: {e}")
            return CronJobMetrics(
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                average_processing_time_ms=0.0,
                last_execution=None,
                last_success=None,
                last_failure=None
            )
    
    # Private helper methods
    
    async def _get_active_users_with_bots(self) -> List[Dict[str, Any]]:
        """Get all active users who have meeting bots."""
        try:
            result = self.supabase.table("users") \
                .select("id, email, created_at") \
                .eq("status", "active") \
                .execute()
            
            users = result.data if result.data else []
            
            # Filter users who have meeting bots
            users_with_bots = []
            for user in users:
                bot_count = await self._get_user_bot_count(user['id'])
                if bot_count > 0:
                    users_with_bots.append(user)
            
            return users_with_bots
            
        except Exception as e:
            logger.error(f"Failed to get active users with bots: {e}")
            return []
    
    async def _get_user_bot_count(self, user_id: str) -> int:
        """Get count of meeting bots for a user."""
        try:
            result = self.supabase.table("meeting_bots") \
                .select("bot_id", count="exact") \
                .eq("user_id", user_id) \
                .eq("status", "active") \
                .execute()
            
            return result.count if result.count else 0
            
        except Exception as e:
            logger.error(f"Failed to get bot count for user {user_id}: {e}")
            return 0
    
    async def _get_all_active_meetings(self) -> List[Dict[str, Any]]:
        """Get all active meetings across all users."""
        try:
            result = self.supabase.table("meetings") \
                .select("id, user_id, title, start_time, end_time, status") \
                .eq("status", "active") \
                .gte("start_time", (datetime.now() - timedelta(days=1)).isoformat()) \
                .lte("end_time", (datetime.now() + timedelta(days=7)).isoformat()) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get all active meetings: {e}")
            return []
    
    async def _create_cron_result(self, execution_id: str, start_time: datetime, 
                                total_users: int, successful_polls: int, 
                                failed_polls: int, total_processing_time: int,
                                status: str, error_message: Optional[str]) -> Dict[str, Any]:
        """Create a cron execution result record."""
        try:
            end_time = datetime.now()
            
            cron_result = {
                'execution_id': execution_id,
                'job_type': 'attendee_polling',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_users': total_users,
                'successful_polls': successful_polls,
                'failed_polls': failed_polls,
                'total_processing_time_ms': total_processing_time,
                'status': status,
                'error_message': error_message,
                'created_at': datetime.now().isoformat()
            }
            
            # Store in database
            self.supabase.table("cron_executions").insert(cron_result).execute()
            
            return cron_result
            
        except Exception as e:
            logger.error(f"Failed to create cron result: {e}")
            return {
                'execution_id': execution_id,
                'status': 'error',
                'error_message': f"Failed to create result: {str(e)}"
            }
    
    async def _update_cron_metrics(self, execution_id: str, cron_result: Dict[str, Any]):
        """Update cron job metrics."""
        try:
            # This could update aggregated metrics tables
            # For now, just log the update
            logger.info(f"Updated cron metrics for execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to update cron metrics: {e}")
    
    async def cleanup_completed_meetings(self) -> Dict[str, Any]:
        """Clean up completed meetings and transcripts."""
        try:
            logger.info("Starting cleanup of completed meetings")
            
            # Get completed meetings
            completed_meetings = await self._get_completed_meetings()
            if not completed_meetings:
                return {
                    'total_meetings': 0,
                    'cleaned_meetings': 0,
                    'message': 'No completed meetings found'
                }
            
            cleaned_count = 0
            
            for meeting in completed_meetings:
                try:
                    success = await self._cleanup_meeting(meeting['id'])
                    if success:
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to cleanup meeting {meeting['id']}: {e}")
                    continue
            
            logger.info(f"Meeting cleanup completed: {cleaned_count} cleaned")
            
            return {
                'total_meetings': len(completed_meetings),
                'cleaned_meetings': cleaned_count,
                'success_rate': cleaned_count / len(completed_meetings) if completed_meetings else 0
            }
            
        except Exception as e:
            logger.error(f"Meeting cleanup failed: {e}")
            return {
                'error': str(e),
                'total_meetings': 0,
                'cleaned_meetings': 0
            }
    
    async def _get_completed_meetings(self) -> List[Dict[str, Any]]:
        """Get completed meetings that can be cleaned up."""
        try:
            result = self.supabase.table("meetings") \
                .select("id, user_id, title, end_time, transcript") \
                .eq("bot_status", "completed") \
                .lt("end_time", (datetime.now() - timedelta(days=30)).isoformat()) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get completed meetings: {e}")
            return []
    
    async def _cleanup_meeting(self, meeting_id: str) -> bool:
        """Clean up a specific meeting."""
        try:
            # Archive transcript data if needed
            # For now, just mark as archived
            update_data = {
                'bot_status': 'archived',
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("meetings") \
                .update(update_data) \
                .eq("id", meeting_id) \
                .execute()
            
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Failed to cleanup meeting {meeting_id}: {e}")
            return False
    
    async def auto_schedule_user_bots(self, user_id: str) -> Dict[str, Any]:
        """Auto-schedule bots for a specific user's meetings."""
        try:
            logger.info(f"Starting auto-schedule bots for user: {user_id}")
            
            # Get user's upcoming meetings
            upcoming_meetings = await self._get_user_upcoming_meetings(user_id)
            if not upcoming_meetings:
                return {
                    'success': True,
                    'message': 'No upcoming meetings found',
                    'user_id': user_id,
                    'scheduled_bots': 0
                }
            
            # Auto-schedule bots for meetings
            scheduled_count = 0
            for meeting in upcoming_meetings:
                if await self._should_auto_schedule_bot(meeting):
                    success = await self._schedule_meeting_bot(meeting, user_id)
                    if success:
                        scheduled_count += 1
            
            return {
                'success': True,
                'message': f'Auto-scheduled {scheduled_count} bots',
                'user_id': user_id,
                'scheduled_bots': scheduled_count,
                'total_meetings': len(upcoming_meetings)
            }
            
        except Exception as e:
            logger.error(f"Auto-schedule bots failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'scheduled_bots': 0
            }
    
    async def auto_schedule_all_bots(self) -> Dict[str, Any]:
        """Auto-schedule bots for all users' meetings."""
        try:
            logger.info("Starting auto-schedule bots for all users")
            
            # Get all active users
            users = await self._get_active_users()
            if not users:
                return {
                    'success': True,
                    'message': 'No active users found',
                    'total_scheduled': 0
                }
            
            # Auto-schedule for each user
            total_scheduled = 0
            for user in users:
                result = await self.auto_schedule_user_bots(user['id'])
                if result.get('success'):
                    total_scheduled += result.get('scheduled_bots', 0)
            
            return {
                'success': True,
                'message': f'Auto-scheduled {total_scheduled} bots total',
                'total_scheduled': total_scheduled,
                'total_users': len(users)
            }
            
        except Exception as e:
            logger.error(f"Auto-schedule all bots failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_scheduled': 0
            }
    
    async def _get_user_upcoming_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's upcoming meetings."""
        try:
            result = self.supabase.table("meetings") \
                .select("*") \
                .eq("user_id", user_id) \
                .gte("start_time", datetime.now().isoformat()) \
                .eq("bot_status", "pending") \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get user upcoming meetings: {e}")
            return []
    
    async def _should_auto_schedule_bot(self, meeting: Dict[str, Any]) -> bool:
        """Determine if a bot should be auto-scheduled for a meeting."""
        # Check if meeting has a URL
        if not meeting.get('meeting_url'):
            return False
        
        # Check if bot is not already scheduled
        if meeting.get('bot_status') != 'pending':
            return False
        
        # Check if meeting is within next 24 hours
        meeting_time = datetime.fromisoformat(meeting['start_time'])
        if meeting_time > datetime.now() + timedelta(days=1):
            return False
        
        return True
    
    async def _schedule_meeting_bot(self, meeting: Dict[str, Any], user_id: str) -> bool:
        """Schedule a bot for a specific meeting."""
        try:
            # Update meeting with bot configuration
            update_data = {
                'bot_status': 'bot_scheduled',
                'bot_deployment_method': 'auto',
                'auto_bot_notification_sent': True,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("meetings") \
                .update(update_data) \
                .eq("id", meeting['id']) \
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to schedule bot for meeting {meeting['id']}: {e}")
            return False
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users."""
        try:
            result = self.supabase.table("users") \
                .select("id") \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []
