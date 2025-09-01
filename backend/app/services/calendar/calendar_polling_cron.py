"""
Calendar polling cron service for BeSunny.ai Python backend.
Handles scheduled calendar synchronization and batch operations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .calendar_polling_service import CalendarPollingService

logger = logging.getLogger(__name__)


class CronExecutionResult(BaseModel):
    """Result of a cron job execution."""
    execution_id: str
    start_time: datetime
    end_time: datetime
    total_users: int
    successful_syncs: int
    failed_syncs: int
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


class CalendarPollingCronService:
    """Service for executing scheduled calendar synchronization operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.polling_service = CalendarPollingService()
        
        logger.info("Calendar Polling Cron Service initialized")
    
    async def execute_polling_cron(self) -> Dict[str, Any]:
        """
        Execute the main calendar polling cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"calendar_cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting calendar polling cron execution {execution_id}")
            
            # Get all active users with calendar integration
            active_users = await self._get_active_users_with_calendar()
            if not active_users:
                logger.info("No active users with calendar integration found")
                return await self._create_cron_result(
                    execution_id, start_time, 0, 0, 0, 0, "completed", None
                )
            
            # Execute sync for each user
            successful_syncs = 0
            failed_syncs = 0
            total_processing_time = 0
            
            for user in active_users:
                try:
                    user_start_time = datetime.now()
                    
                    # Execute smart polling for user
                    result = await self.polling_service.smart_calendar_polling(user['id'])
                    
                    user_processing_time = (datetime.now() - user_start_time).microseconds // 1000
                    total_processing_time += user_processing_time
                    
                    if result and not result.get('skipped'):
                        if result.get('error'):
                            failed_syncs += 1
                            logger.warning(f"User {user['id']} calendar sync failed: {result.get('error')}")
                        else:
                            successful_syncs += 1
                            logger.info(f"User {user['id']} calendar sync completed successfully")
                    else:
                        logger.info(f"User {user['id']} calendar sync skipped: {result.get('reason', 'Unknown')}")
                        
                except Exception as e:
                    failed_syncs += 1
                    logger.error(f"Error syncing calendar for user {user['id']}: {str(e)}")
                    continue
            
            # Record execution metrics
            await self._record_cron_metrics(execution_id, successful_syncs, failed_syncs, total_processing_time)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).microseconds // 1000
            
            logger.info(f"Calendar polling cron execution {execution_id} completed: "
                       f"{successful_syncs} successful, {failed_syncs} failed, "
                       f"total time: {total_time}ms")
            
            return await self._create_cron_result(
                execution_id, start_time, len(active_users), 
                successful_syncs, failed_syncs, total_time, "completed", None
            )
            
        except Exception as e:
            end_time = datetime.now()
            total_time = (end_time - start_time).microseconds // 1000
            
            logger.error(f"Calendar polling cron execution {execution_id} failed: {str(e)}")
            
            return await self._create_cron_result(
                execution_id, start_time, 0, 0, 0, total_time, "failed", str(e)
            )
    
    async def poll_all_active_calendars(self) -> Dict[str, Any]:
        """
        Poll all active calendars for all users.
        
        Returns:
            Batch polling results
        """
        try:
            logger.info("Starting batch calendar polling for all active users")
            
            # Get all active users with calendar integration
            active_users = await self._get_active_users_with_calendar()
            if not active_users:
                return {
                    'success': True,
                    'message': 'No active users with calendar integration found',
                    'total_users': 0,
                    'results': []
                }
            
            results = []
            total_events_processed = 0
            total_meetings_detected = 0
            
            for user in active_users:
                try:
                    # Execute smart polling for user
                    result = await self.polling_service.smart_calendar_polling(user['id'])
                    
                    if result and not result.get('skipped'):
                        results.append({
                            'user_id': user['id'],
                            'success': not result.get('error'),
                            'result': result,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        if result.get('events_processed'):
                            total_events_processed += result['events_processed']
                        if result.get('meetings_detected'):
                            total_meetings_detected += result['meetings_detected']
                            
                except Exception as e:
                    logger.error(f"Error in batch calendar polling for user {user['id']}: {str(e)}")
                    results.append({
                        'user_id': user['id'],
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            return {
                'success': True,
                'total_users': len(active_users),
                'total_events_processed': total_events_processed,
                'total_meetings_detected': total_meetings_detected,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch calendar polling failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def handle_cron_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process and handle cron execution results.
        
        Args:
            results: List of cron execution results
            
        Returns:
            Processed results summary
        """
        try:
            if not results:
                return {
                    'success': True,
                    'message': 'No cron results to process',
                    'summary': {}
                }
            
            # Calculate summary statistics
            total_executions = len(results)
            successful_executions = sum(1 for r in results if r.get('status') == 'completed')
            failed_executions = total_executions - successful_executions
            
            total_processing_time = sum(r.get('total_processing_time_ms', 0) for r in results)
            average_processing_time = total_processing_time / total_executions if total_executions > 0 else 0
            
            # Group by status
            status_counts = {}
            for result in results:
                status = result.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Identify patterns in failures
            failure_patterns = []
            for result in results:
                if result.get('status') == 'failed':
                    error = result.get('error_message', 'Unknown error')
                    failure_patterns.append({
                        'error': error,
                        'timestamp': result.get('start_time'),
                        'execution_id': result.get('execution_id')
                    })
            
            summary = {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'total_processing_time_ms': total_processing_time,
                'average_processing_time_ms': round(average_processing_time, 2),
                'status_distribution': status_counts,
                'failure_patterns': failure_patterns[:10],  # Top 10 failures
                'last_execution': max((r.get('start_time') for r in results if r.get('start_time')), default=None)
            }
            
            # Store summary in database for monitoring
            await self._store_cron_summary(summary)
            
            logger.info(f"Cron results processed: {successful_executions}/{total_executions} successful "
                       f"({summary['success_rate']:.1f}% success rate)")
            
            return {
                'success': True,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing cron results: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_active_users_with_calendar(self) -> List[Dict[str, Any]]:
        """Get all active users with calendar integration."""
        try:
            # Query users with active calendar integration
            response = await self.supabase.table('users').select(
                'id, email, google_credentials, calendar_webhooks'
            ).eq('is_active', True).not_.is_('google_credentials', 'null').execute()
            
            if response.data:
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting active users with calendar: {str(e)}")
            return []
    
    async def _create_cron_result(self, execution_id: str, start_time: datetime, 
                                 total_users: int, successful_syncs: int, 
                                 failed_syncs: int, total_processing_time: int,
                                 status: str, error_message: Optional[str]) -> Dict[str, Any]:
        """Create a cron execution result."""
        end_time = datetime.now()
        
        result = CronExecutionResult(
            execution_id=execution_id,
            start_time=start_time,
            end_time=end_time,
            total_users=total_users,
            successful_syncs=successful_syncs,
            failed_syncs=failed_syncs,
            total_processing_time_ms=total_processing_time,
            status=status,
            error_message=error_message
        )
        
        # Store result in database
        await self._store_cron_result(result)
        
        return result.dict()
    
    async def _store_cron_result(self, result: CronExecutionResult) -> None:
        """Store cron execution result in database."""
        try:
            await self.supabase.table('calendar_cron_results').insert(result.dict()).execute()
        except Exception as e:
            logger.error(f"Error storing cron result: {str(e)}")
    
    async def _store_cron_summary(self, summary: Dict[str, Any]) -> None:
        """Store cron summary in database."""
        try:
            await self.supabase.table('calendar_cron_summaries').insert({
                'summary_data': summary,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error storing cron summary: {str(e)}")
    
    async def _record_cron_metrics(self, execution_id: str, successful_syncs: int, 
                                  failed_syncs: int, total_processing_time: int) -> None:
        """Record cron job metrics for monitoring."""
        try:
            metrics = {
                'execution_id': execution_id,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'total_processing_time_ms': total_processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.supabase.table('calendar_cron_metrics').insert(metrics).execute()
            
        except Exception as e:
            logger.error(f"Error recording cron metrics: {str(e)}")
    
    async def get_cron_job_metrics(self) -> CronJobMetrics:
        """Get metrics for calendar polling cron jobs."""
        try:
            # Query recent cron results
            response = await self.supabase.table('calendar_cron_results').select(
                '*'
            ).order('start_time', desc=True).limit(100).execute()
            
            if not response.data:
                return CronJobMetrics(
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    average_processing_time_ms=0.0,
                    last_execution=None,
                    last_success=None,
                    last_failure=None
                )
            
            results = response.data
            
            total_executions = len(results)
            successful_executions = sum(1 for r in results if r.get('status') == 'completed')
            failed_executions = total_executions - successful_executions
            
            total_processing_time = sum(r.get('total_processing_time_ms', 0) for r in results)
            average_processing_time = total_processing_time / total_executions if total_executions > 0 else 0
            
            last_execution = max((r.get('start_time') for r in results if r.get('start_time')), default=None)
            
            successful_results = [r for r in results if r.get('status') == 'completed']
            failed_results = [r for r in results if r.get('status') == 'failed']
            
            last_success = max((r.get('start_time') for r in successful_results if r.get('start_time')), default=None)
            last_failure = max((r.get('start_time') for r in failed_results if r.get('start_time')), default=None)
            
            return CronJobMetrics(
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                average_processing_time_ms=round(average_processing_time, 2),
                last_execution=last_execution,
                last_success=last_success,
                last_failure=last_failure
            )
            
        except Exception as e:
            logger.error(f"Error getting cron job metrics: {str(e)}")
            return CronJobMetrics(
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                average_processing_time_ms=0.0,
                last_execution=None,
                last_success=None,
                last_failure=None
            )
    
    async def poll_all_active_calendars_for_user(self, user_id: str) -> Dict[str, Any]:
        """Poll calendar for a specific user."""
        try:
            logger.info(f"Starting calendar polling for user: {user_id}")
            
            # Get user's active calendars
            active_calendars = await self._get_user_active_calendars(user_id)
            if not active_calendars:
                return {
                    'success': True,
                    'message': 'No active calendars found',
                    'user_id': user_id,
                    'calendars_processed': 0
                }
            
            # Poll each calendar
            processed_count = 0
            for calendar_info in active_calendars:
                try:
                    result = await self._poll_single_calendar(calendar_info)
                    if result:
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to poll calendar {calendar_info['id']}: {e}")
                    continue
            
            return {
                'success': True,
                'user_id': user_id,
                'calendars_processed': processed_count,
                'total_calendars': len(active_calendars)
            }
            
        except Exception as e:
            logger.error(f"Calendar polling failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }
    
    async def _get_user_active_calendars(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's active calendars."""
        try:
            result = self.supabase.table("calendar_webhooks") \
                .select("id, google_calendar_id") \
                .eq("user_id", user_id) \
                .eq("is_active", True) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get user active calendars for {user_id}: {e}")
            return []
    
    async def _poll_single_calendar(self, calendar_info: Dict[str, Any]) -> bool:
        """Poll a single calendar for changes."""
        try:
            # This would integrate with your calendar polling logic
            # For now, just return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to poll calendar {calendar_info['id']}: {e}")
            return False
