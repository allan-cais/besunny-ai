"""
Gmail polling cron service for BeSunny.ai Python backend.
Handles scheduled email monitoring and batch operations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .gmail_polling_service import GmailPollingService

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


class GmailPollingCronService:
    """Service for executing scheduled Gmail monitoring operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.polling_service = GmailPollingService()
        
        logger.info("Gmail Polling Cron Service initialized")
    
    async def execute_polling_cron(self) -> Dict[str, Any]:
        """
        Execute the main Gmail polling cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"gmail_cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting Gmail polling cron execution {execution_id}")
            
            # Get all active users with Gmail integration
            active_users = await self._get_active_users_with_gmail()
            if not active_users:
                logger.info("No active users with Gmail integration found")
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
                    
                    # Execute polling for user
                    result = await self.polling_service.poll_gmail_for_user(user['email'])
                    
                    user_processing_time = (datetime.now() - user_start_time).microseconds // 1000
                    total_processing_time += user_processing_time
                    
                    if result and result.get('success'):
                        successful_polls += 1
                        logger.info(f"User {user['email']} Gmail polling completed successfully")
                    else:
                        failed_polls += 1
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        logger.warning(f"User {user['email']} Gmail polling failed: {error_msg}")
                        
                except Exception as e:
                    failed_polls += 1
                    logger.error(f"Error polling Gmail for user {user['email']}: {str(e)}")
                    continue
            
            # Record execution metrics
            await self._record_cron_metrics(execution_id, successful_polls, failed_polls, total_processing_time)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).microseconds // 1000
            
            logger.info(f"Gmail polling cron execution {execution_id} completed: "
                       f"{successful_polls} successful, {failed_polls} failed, "
                       f"total time: {total_time}ms")
            
            return await self._create_cron_result(
                execution_id, start_time, len(active_users), 
                successful_polls, failed_polls, total_time, "completed", None
            )
            
        except Exception as e:
            end_time = datetime.now()
            total_time = (end_time - start_time).microseconds // 1000
            
            logger.error(f"Gmail polling cron execution {execution_id} failed: {str(e)}")
            
            return await self._create_cron_result(
                execution_id, start_time, 0, 0, 0, total_time, "failed", str(e)
            )
    
    async def poll_all_active_gmail_accounts(self) -> Dict[str, Any]:
        """
        Poll all active Gmail accounts for all users.
        
        Returns:
            Batch polling results
        """
        try:
            logger.info("Starting batch Gmail polling for all active users")
            
            # Get all active users with Gmail integration
            active_users = await self._get_active_users_with_gmail()
            if not active_users:
                return {
                    'success': True,
                    'message': 'No active users with Gmail integration found',
                    'total_users': 0,
                    'results': []
                }
            
            results = []
            total_messages_processed = 0
            total_virtual_emails_detected = 0
            total_documents_created = 0
            
            for user in active_users:
                try:
                    # Execute polling for user
                    result = await self.polling_service.poll_gmail_for_user(user['email'])
                    
                    if result:
                        results.append({
                            'user_email': user['email'],
                            'success': result.get('success', False),
                            'result': result,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        if result.get('messages_processed'):
                            total_messages_processed += result['messages_processed']
                        if result.get('virtual_emails_detected'):
                            total_virtual_emails_detected += result['virtual_emails_detected']
                        if result.get('documents_created'):
                            total_documents_created += result['documents_created']
                            
                except Exception as e:
                    logger.error(f"Error in batch Gmail polling for user {user['email']}: {str(e)}")
                    results.append({
                        'user_email': user['email'],
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            return {
                'success': True,
                'total_users': len(active_users),
                'total_messages_processed': total_messages_processed,
                'total_virtual_emails_detected': total_virtual_emails_detected,
                'total_documents_created': total_documents_created,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch Gmail polling failed: {str(e)}")
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
            
            logger.info(f"Gmail cron results processed: {successful_executions}/{total_executions} successful "
                       f"({summary['success_rate']:.1f}% success rate)")
            
            return {
                'success': True,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing Gmail cron results: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_active_users_with_gmail(self) -> List[Dict[str, Any]]:
        """Get all active users with Gmail integration."""
        try:
            # Query users with active Gmail integration
            response = await self.supabase.table('users').select(
                'id, email, google_credentials, gmail_watches'
            ).eq('is_active', True).not_.is_('google_credentials', 'null').execute()
            
            if response.data:
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting active users with Gmail: {str(e)}")
            return []
    
    async def _create_cron_result(self, execution_id: str, start_time: datetime, 
                                 total_users: int, successful_polls: int, 
                                 failed_polls: int, total_processing_time: int,
                                 status: str, error_message: Optional[str]) -> Dict[str, Any]:
        """Create a cron execution result."""
        end_time = datetime.now()
        
        result = CronExecutionResult(
            execution_id=execution_id,
            start_time=start_time,
            end_time=end_time,
            total_users=total_users,
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
            await self.supabase.table('gmail_cron_results').insert(result.dict()).execute()
        except Exception as e:
            logger.error(f"Error storing Gmail cron result: {str(e)}")
    
    async def _store_cron_summary(self, summary: Dict[str, Any]) -> None:
        """Store cron summary in database."""
        try:
            await self.supabase.table('gmail_cron_summaries').insert({
                'summary_data': summary,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error storing Gmail cron summary: {str(e)}")
    
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
            
            await self.supabase.table('gmail_cron_metrics').insert(metrics).execute()
            
        except Exception as e:
            logger.error(f"Error recording Gmail cron metrics: {str(e)}")
    
    async def get_cron_job_metrics(self) -> CronJobMetrics:
        """Get metrics for Gmail polling cron jobs."""
        try:
            # Query recent cron results
            response = await self.supabase.table('gmail_cron_results').select(
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
            logger.error(f"Error getting Gmail cron job metrics: {str(e)}")
            return CronJobMetrics(
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                average_processing_time_ms=0.0,
                last_execution=None,
                last_success=None,
                last_failure=None
            )
    
    async def renew_expired_watches(self) -> Dict[str, Any]:
        """Renew expired Gmail watches."""
        try:
            logger.info("Starting Gmail watch renewal")
            
            # Get expired watches
            expired_watches = await self._get_expired_watches()
            if not expired_watches:
                return {
                    'total_watches': 0,
                    'renewed_watches': 0,
                    'message': 'No expired watches found'
                }
            
            renewed_count = 0
            
            for watch in expired_watches:
                try:
                    success = await self._renew_watch(watch['user_email'])
                    if success:
                        renewed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to renew watch for {watch['user_email']}: {e}")
                    continue
            
            logger.info(f"Gmail watch renewal completed: {renewed_count} renewed")
            
            return {
                'total_watches': len(expired_watches),
                'renewed_watches': renewed_count,
                'success_rate': renewed_count / len(expired_watches) if expired_watches else 0
            }
            
        except Exception as e:
            logger.error(f"Gmail watch renewal failed: {e}")
            return {
                'error': str(e),
                'total_watches': 0,
                'renewed_watches': 0
            }
    
    async def _get_expired_watches(self) -> List[Dict[str, Any]]:
        """Get expired Gmail watches."""
        try:
            result = self.supabase.table("gmail_watches") \
                .select("user_email") \
                .lt("expiration", datetime.now().isoformat()) \
                .eq("is_active", True) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get expired watches: {e}")
            return []
    
    async def _renew_watch(self, user_email: str) -> bool:
        """Renew a Gmail watch for a user."""
        try:
            # Get user credentials
            user_credentials = await self._get_user_credentials(user_email)
            if not user_credentials:
                logger.warning(f"No credentials found for user {user_email}")
                return False
            
            # Create new watch
            watch_result = await self._create_gmail_watch(user_email, user_credentials)
            if watch_result:
                # Update watch record
                await self._update_watch_record(user_email, watch_result)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to renew watch for {user_email}: {e}")
            return False
    
    async def _get_user_credentials(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Get user's Google credentials."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("access_token, refresh_token") \
                .eq("google_email", user_email) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for {user_email}: {e}")
            return None
    
    async def _create_gmail_watch(self, user_email: str, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new Gmail watch."""
        try:
            # This would integrate with Gmail API to create a new watch
            # For now, return a mock result
            return {
                'historyId': 'mock_history_id',
                'expiration': (datetime.now() + timedelta(hours=7)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create Gmail watch for {user_email}: {e}")
            return None
    
    async def _update_watch_record(self, user_email: str, watch_result: Dict[str, Any]):
        """Update Gmail watch record in database."""
        try:
            update_data = {
                'history_id': watch_result.get('historyId'),
                'expiration': watch_result.get('expiration'),
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("gmail_watches") \
                .update(update_data) \
                .eq("user_email", user_email) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update watch record for {user_email}: {e}")
    
    async def process_pending_emails(self) -> Dict[str, Any]:
        """Process pending emails for all users."""
        try:
            logger.info("Starting pending email processing")
            
            # Get pending emails
            pending_emails = await self._get_pending_emails()
            if not pending_emails:
                return {
                    'total_emails': 0,
                    'processed_emails': 0,
                    'message': 'No pending emails found'
                }
            
            processed_count = 0
            
            for email in pending_emails:
                try:
                    success = await self._process_single_email(email)
                    if success:
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process email {email['id']}: {e}")
                    continue
            
            logger.info(f"Pending email processing completed: {processed_count} processed")
            
            return {
                'total_emails': len(pending_emails),
                'processed_emails': processed_count,
                'success_rate': processed_count / len(pending_emails) if pending_emails else 0
            }
            
        except Exception as e:
            logger.error(f"Pending email processing failed: {e}")
            return {
                'error': str(e),
                'total_emails': 0,
                'processed_emails': 0
            }
    
    async def _get_pending_emails(self) -> List[Dict[str, Any]]:
        """Get pending emails that need processing."""
        try:
            result = self.supabase.table("email_processing_logs") \
                .select("id, gmail_message_id, inbound_address, sender, subject") \
                .eq("status", "pending") \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get pending emails: {e}")
            return []
    
    async def _process_single_email(self, email: Dict[str, Any]) -> bool:
        """Process a single pending email."""
        try:
            # Update status to processing
            await self._update_email_status(email['id'], 'processing')
            
            # Process the email (this would integrate with your email processing logic)
            # For now, just mark as processed
            success = await self._mark_email_processed(email['id'])
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to process email {email['id']}: {e}")
            # Mark as failed
            await self._update_email_status(email['id'], 'failed')
            return False
    
    async def _update_email_status(self, email_id: str, status: str):
        """Update email processing status."""
        try:
            update_data = {
                'status': status,
                'processed_at': datetime.now().isoformat() if status == 'processed' else None
            }
            
            self.supabase.table("email_processing_logs") \
                .update(update_data) \
                .eq("id", email_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update email status: {e}")
    
    async def _mark_email_processed(self, email_id: str) -> bool:
        """Mark email as processed."""
        try:
            update_data = {
                'status': 'processed',
                'processed_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("email_processing_logs") \
                .update(update_data) \
                .eq("id", email_id) \
                .execute()
            
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Failed to mark email as processed: {e}")
            return False
    
    async def poll_all_active_gmail_accounts_for_user(self, user_id: str) -> Dict[str, Any]:
        """Poll Gmail for a specific user."""
        try:
            logger.info(f"Starting Gmail polling for user: {user_id}")
            
            # Get user's email
            user_email = await self._get_user_email(user_id)
            if not user_email:
                return {
                    'success': False,
                    'error': 'User email not found',
                    'user_id': user_id
                }
            
            # Poll Gmail for the user
            result = await self.poll_all_active_gmail_accounts()
            
            return {
                'success': True,
                'user_id': user_id,
                'user_email': user_email,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Gmail polling failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }
    
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user's email address."""
        try:
            result = self.supabase.table("users") \
                .select("email") \
                .eq("id", user_id) \
                .single() \
                .execute()
            
            return result.data.get('email') if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get user email for {user_id}: {e}")
            return None
