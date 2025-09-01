"""
Drive polling cron service for BeSunny.ai Python backend.
Handles scheduled drive file monitoring and batch operations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .drive_polling_service import DrivePollingService

logger = logging.getLogger(__name__)


class CronExecutionResult(BaseModel):
    """Result of a cron job execution."""
    execution_id: str
    start_time: datetime
    end_time: datetime
    total_files: int
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


class DrivePollingCronService:
    """Service for executing scheduled drive file monitoring operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.polling_service = DrivePollingService()
        
        logger.info("Drive Polling Cron Service initialized")
    
    async def execute_polling_cron(self) -> Dict[str, Any]:
        """
        Execute the main drive polling cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"drive_cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting drive polling cron execution {execution_id}")
            
            # Get all active file watches
            active_file_watches = await self._get_active_file_watches()
            if not active_file_watches:
                logger.info("No active file watches found")
                return await self._create_cron_result(
                    execution_id, start_time, 0, 0, 0, 0, "completed", None
                )
            
            # Execute polling for each file
            successful_polls = 0
            failed_polls = 0
            total_processing_time = 0
            
            for file_watch in active_file_watches:
                try:
                    file_start_time = datetime.now()
                    
                    # Execute polling for file
                    result = await self.polling_service.poll_drive_for_file(
                        file_id=file_watch['file_id'],
                        document_id=file_watch['document_id']
                    )
                    
                    file_processing_time = (datetime.now() - file_start_time).microseconds // 1000
                    total_processing_time += file_processing_time
                    
                    if result and result.get('success'):
                        successful_polls += 1
                        logger.info(f"File {file_watch['file_id']} polling completed successfully")
                    else:
                        failed_polls += 1
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        logger.warning(f"File {file_watch['file_id']} polling failed: {error_msg}")
                        
                except Exception as e:
                    failed_polls += 1
                    logger.error(f"Error polling file {file_watch['file_id']}: {str(e)}")
                    continue
            
            # Record execution metrics
            await self._record_cron_metrics(execution_id, successful_polls, failed_polls, total_processing_time)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).microseconds // 1000
            
            logger.info(f"Drive polling cron execution {execution_id} completed: "
                       f"{successful_polls} successful, {failed_polls} failed, "
                       f"total time: {total_time}ms")
            
            return await self._create_cron_result(
                execution_id, start_time, len(active_file_watches), 
                successful_polls, failed_polls, total_time, "completed", None
            )
            
        except Exception as e:
            end_time = datetime.now()
            total_time = (end_time - start_time).microseconds // 1000
            
            logger.error(f"Drive polling cron execution {execution_id} failed: {str(e)}")
            
            return await self._create_cron_result(
                execution_id, start_time, 0, 0, 0, total_time, "failed", str(e)
            )
    
    async def poll_all_active_files(self) -> Dict[str, Any]:
        """
        Poll all active files for all users.
        
        Returns:
            Batch polling results
        """
        try:
            logger.info("Starting batch drive polling for all active files")
            
            # Get all active file watches
            active_file_watches = await self._get_active_file_watches()
            if not active_file_watches:
                return {
                    'success': True,
                    'message': 'No active file watches found',
                    'total_files': 0,
                    'results': []
                }
            
            results = []
            total_changes_detected = 0
            total_files_updated = 0
            
            for file_watch in active_file_watches:
                try:
                    # Execute polling for file
                    result = await self.polling_service.poll_drive_for_file(
                        file_id=file_watch['file_id'],
                        document_id=file_watch['document_id']
                    )
                    
                    if result:
                        results.append({
                            'file_id': file_watch['file_id'],
                            'document_id': file_watch['document_id'],
                            'success': result.get('success', False),
                            'result': result,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        if result.get('changes_detected'):
                            total_changes_detected += result['changes_detected']
                        if result.get('file_updated'):
                            total_files_updated += 1
                            
                except Exception as e:
                    logger.error(f"Error in batch drive polling for file {file_watch['file_id']}: {str(e)}")
                    results.append({
                        'file_id': file_watch['file_id'],
                        'document_id': file_watch['document_id'],
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            return {
                'success': True,
                'total_files': len(active_file_watches),
                'total_changes_detected': total_changes_detected,
                'total_files_updated': total_files_updated,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch drive polling failed: {str(e)}")
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
            
            logger.info(f"Drive cron results processed: {successful_executions}/{total_executions} successful "
                       f"({summary['success_rate']:.1f}% success rate)")
            
            return {
                'success': True,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing drive cron results: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_active_file_watches(self) -> List[Dict[str, Any]]:
        """Get all active file watches."""
        try:
            # Query active file watches
            response = await self.supabase.table('drive_file_watches').select(
                'file_id, document_id, user_id, is_active, last_poll_at'
            ).eq('is_active', True).execute()
            
            if response.data:
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting active file watches: {str(e)}")
            return []
    
    async def _create_cron_result(self, execution_id: str, start_time: datetime, 
                                 total_files: int, successful_polls: int, 
                                 failed_polls: int, total_processing_time: int,
                                 status: str, error_message: Optional[str]) -> Dict[str, Any]:
        """Create a cron execution result."""
        end_time = datetime.now()
        
        result = CronExecutionResult(
            execution_id=execution_id,
            start_time=start_time,
            end_time=end_time,
            total_files=total_files,
            successful_polls=successful_polls,
            failed_polls=failed_polls,
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
            await self.supabase.table('drive_cron_results').insert(result.dict()).execute()
        except Exception as e:
            logger.error(f"Error storing drive cron result: {str(e)}")
    
    async def _store_cron_summary(self, summary: Dict[str, Any]) -> None:
        """Store cron summary in database."""
        try:
            await self.supabase.table('drive_cron_summaries').insert({
                'summary_data': summary,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error storing drive cron summary: {str(e)}")
    
    async def _record_cron_metrics(self, execution_id: str, successful_polls: int, 
                                  failed_polls: int, total_processing_time: int) -> None:
        """Record cron job metrics for monitoring."""
        try:
            metrics = {
                'execution_id': execution_id,
                'successful_polls': successful_polls,
                'failed_polls': failed_polls,
                'total_processing_time_ms': total_processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.supabase.table('drive_cron_metrics').insert(metrics).execute()
            
        except Exception as e:
            logger.error(f"Error recording drive cron metrics: {str(e)}")
    
    async def get_cron_job_metrics(self) -> CronJobMetrics:
        """Get metrics for drive polling cron jobs."""
        try:
            # Query recent cron results
            response = await self.supabase.table('drive_cron_results').select(
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
            logger.error(f"Error getting drive cron job metrics: {str(e)}")
            return CronJobMetrics(
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                average_processing_time_ms=0.0,
                last_execution=None,
                last_success=None,
                last_failure=None
            )
    
    async def poll_all_active_files_for_user(self, user_id: str) -> Dict[str, Any]:
        """Poll Drive files for a specific user."""
        try:
            logger.info(f"Starting Drive polling for user: {user_id}")
            
            # Get user's active files
            active_files = await self._get_user_active_files(user_id)
            if not active_files:
                return {
                    'success': True,
                    'message': 'No active files found',
                    'user_id': user_id,
                    'files_processed': 0
                }
            
            # Poll each file
            processed_count = 0
            for file_info in active_files:
                try:
                    result = await self._poll_single_file(file_info)
                    if result:
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to poll file {file_info['file_id']}: {e}")
                    continue
            
            return {
                'success': True,
                'user_id': user_id,
                'files_processed': processed_count,
                'total_files': len(active_files)
            }
            
        except Exception as e:
            logger.error(f"Drive polling failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }
    
    async def _get_user_active_files(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's active Drive files."""
        try:
            result = self.supabase.table("drive_file_watches") \
                .select("file_id, document_id, project_id") \
                .eq("is_active", True) \
                .eq("project_id", None) \
                .execute()
            
            # Filter by user's projects
            user_projects = await self._get_user_projects(user_id)
            if user_projects:
                project_ids = [p['id'] for p in user_projects]
                result = self.supabase.table("drive_file_watches") \
                    .select("file_id, document_id, project_id") \
                    .eq("is_active", True) \
                    .in_("project_id", project_ids) \
                    .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get user active files for {user_id}: {e}")
            return []
    
    async def _get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's projects."""
        try:
            result = self.supabase.table("projects") \
                .select("id") \
                .eq("user_id", user_id) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get user projects for {user_id}: {e}")
            return []
    
    async def _poll_single_file(self, file_info: Dict[str, Any]) -> bool:
        """Poll a single Drive file for changes."""
        try:
            # This would integrate with your Drive polling logic
            # For now, just return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to poll file {file_info['file_id']}: {e}")
            return False
