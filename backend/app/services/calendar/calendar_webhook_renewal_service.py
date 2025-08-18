"""
Calendar webhook renewal service for BeSunny.ai Python backend.
Handles scheduled calendar webhook renewal and maintenance.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .calendar_service import CalendarService

logger = logging.getLogger(__name__)


class WebhookRenewalResult(BaseModel):
    """Result of a webhook renewal operation."""
    webhook_id: str
    user_id: str
    calendar_id: str
    success: bool
    new_expiration: Optional[datetime] = None
    error_message: Optional[str] = None
    timestamp: datetime


class BatchWebhookRenewalResult(BaseModel):
    """Result of a batch webhook renewal operation."""
    total_webhooks: int
    successful_renewals: int
    failed_renewals: int
    skipped_renewals: int
    results: List[WebhookRenewalResult]
    total_processing_time_ms: int
    timestamp: datetime


class CalendarWebhookRenewalService:
    """Service for renewing expired calendar webhooks."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.calendar_service = CalendarService()
        
        logger.info("Calendar Webhook Renewal Service initialized")
    
    async def execute_cron(self) -> Dict[str, Any]:
        """
        Execute the main calendar webhook renewal cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"calendar_webhook_renewal_cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting calendar webhook renewal cron execution {execution_id}")
            
            # Execute expired webhook renewal
            result = await self.renew_expired_webhooks()
            
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            
            if result and result.get('success'):
                logger.info(f"Calendar webhook renewal cron completed successfully: {result.get('message', '')}")
                return {
                    'execution_id': execution_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'total_webhooks': result.get('total_webhooks', 0),
                    'successful_renewals': result.get('results', []).count(lambda x: x.success),
                    'failed_renewals': result.get('results', []).count(lambda x: not x.success),
                    'total_processing_time_ms': total_processing_time,
                    'status': 'completed',
                    'error_message': None
                }
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result'
                logger.error(f"Calendar webhook renewal cron failed: {error_msg}")
                return {
                    'execution_id': execution_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'total_webhooks': 0,
                    'successful_renewals': 0,
                    'failed_renewals': 0,
                    'total_processing_time_ms': total_processing_time,
                    'status': 'failed',
                    'error_message': error_msg
                }
                
        except Exception as e:
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            logger.error(f"Calendar webhook renewal cron execution failed: {str(e)}", exc_info=True)
            
            return {
                'execution_id': execution_id,
                'start_time': start_time,
                'end_time': end_time,
                'total_webhooks': 0,
                'successful_renewals': 0,
                'failed_renewals': 0,
                'total_processing_time_ms': total_processing_time,
                'status': 'failed',
                'error_message': str(e)
            }

    async def renew_expired_webhooks(self) -> Dict[str, Any]:
        """
        Renew all expired calendar webhooks.
        
        Returns:
            Batch renewal results
        """
        try:
            logger.info("Starting expired calendar webhook renewal")
            
            # Get all expired webhooks
            expired_webhooks = await self._get_expired_webhooks()
            if not expired_webhooks:
                return {
                    'success': True,
                    'message': 'No expired webhooks found',
                    'total_webhooks': 0,
                    'results': []
                }
            
            # Process each expired webhook
            results = []
            successful_renewals = 0
            failed_renewals = 0
            skipped_renewals = 0
            
            for webhook in expired_webhooks:
                try:
                    result = await self._renew_single_webhook(webhook)
                    results.append(result)
                    
                    if result.success:
                        successful_renewals += 1
                    else:
                        failed_renewals += 1
                        
                except Exception as e:
                    logger.error(f"Error renewing webhook {webhook['id']}: {str(e)}")
                    failed_renewals += 1
                    results.append(WebhookRenewalResult(
                        webhook_id=webhook['id'],
                        user_id=webhook['user_id'],
                        calendar_id=webhook['calendar_id'],
                        success=False,
                        error_message=str(e),
                        timestamp=datetime.now()
                    ))
            
            # Update webhook records
            await self._update_webhook_records(results)
            
            total_time = 0  # Calculate actual processing time if needed
            
            logger.info(f"Calendar webhook renewal completed: {successful_renewals} successful, "
                       f"{failed_renewals} failed, {skipped_renewals} skipped")
            
            return {
                'success': True,
                'total_webhooks': len(expired_webhooks),
                'successful_renewals': successful_renewals,
                'failed_renewals': failed_renewals,
                'skipped_renewals': skipped_renewals,
                'results': [r.dict() for r in results],
                'total_processing_time_ms': total_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Calendar webhook renewal failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def renew_user_webhooks(self, user_id: str) -> Dict[str, Any]:
        """
        Renew all calendar webhooks for a specific user.
        
        Args:
            user_id: User ID to renew webhooks for
            
        Returns:
            Renewal results for the user
        """
        try:
            logger.info(f"Starting calendar webhook renewal for user {user_id}")
            
            # Get user's webhooks
            user_webhooks = await self._get_user_webhooks(user_id)
            if not user_webhooks:
                return {
                    'success': True,
                    'message': 'No webhooks found for user',
                    'user_id': user_id,
                    'total_webhooks': 0,
                    'results': []
                }
            
            # Process each webhook
            results = []
            successful_renewals = 0
            failed_renewals = 0
            
            for webhook in user_webhooks:
                try:
                    result = await self._renew_single_webhook(webhook)
                    results.append(result)
                    
                    if result.success:
                        successful_renewals += 1
                    else:
                        failed_renewals += 1
                        
                except Exception as e:
                    logger.error(f"Error renewing webhook {webhook['id']}: {str(e)}")
                    failed_renewals += 1
                    results.append(WebhookRenewalResult(
                        webhook_id=webhook['id'],
                        user_id=webhook['user_id'],
                        calendar_id=webhook['calendar_id'],
                        success=False,
                        error_message=str(e),
                        timestamp=datetime.now()
                    ))
            
            # Update webhook records
            await self._update_webhook_records(results)
            
            logger.info(f"User {user_id} calendar webhook renewal completed: "
                       f"{successful_renewals} successful, {failed_renewals} failed")
            
            return {
                'success': True,
                'user_id': user_id,
                'total_webhooks': len(user_webhooks),
                'successful_renewals': successful_renewals,
                'failed_renewals': failed_renewals,
                'results': [r.dict() for r in results],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"User {user_id} calendar webhook renewal failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
    
    async def handle_renewal_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process and handle renewal results.
        
        Args:
            results: List of renewal results
            
        Returns:
            Processed results summary
        """
        try:
            if not results:
                return {
                    'success': True,
                    'message': 'No renewal results to process',
                    'summary': {}
                }
            
            # Calculate summary statistics
            total_webhooks = len(results)
            successful_renewals = sum(1 for r in results if r.get('success'))
            failed_renewals = total_webhooks - successful_renewals
            
            # Group by status
            status_counts = {}
            for result in results:
                status = 'success' if result.get('success') else 'failed'
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Identify patterns in failures
            failure_patterns = []
            for result in results:
                if not result.get('success'):
                    error = result.get('error_message', 'Unknown error')
                    failure_patterns.append({
                        'error': error,
                        'webhook_id': result.get('webhook_id'),
                        'user_id': result.get('user_id'),
                        'timestamp': result.get('timestamp')
                    })
            
            summary = {
                'total_webhooks': total_webhooks,
                'successful_renewals': successful_renewals,
                'failed_renewals': failed_renewals,
                'success_rate': (successful_renewals / total_webhooks * 100) if total_webhooks > 0 else 0,
                'status_distribution': status_counts,
                'failure_patterns': failure_patterns[:10],  # Top 10 failures
                'last_renewal': max((r.get('timestamp') for r in results if r.get('timestamp')), default=None)
            }
            
            # Store summary in database for monitoring
            await self._store_renewal_summary(summary)
            
            logger.info(f"Webhook renewal results processed: {successful_renewals}/{total_webhooks} successful "
                       f"({summary['success_rate']:.1f}% success rate)")
            
            return {
                'success': True,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook renewal results: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_expired_webhooks(self) -> List[Dict[str, Any]]:
        """Get all expired calendar webhooks."""
        try:
            # Query expired webhooks (expires within next hour or already expired)
            cutoff_time = datetime.now() + timedelta(hours=1)
            
            response = await self.supabase.table('calendar_webhooks').select(
                'id, user_id, calendar_id, expires_at, webhook_url'
            ).lte('expires_at', cutoff_time.isoformat()).execute()
            
            if response.data:
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting expired webhooks: {str(e)}")
            return []
    
    async def _get_user_webhooks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all calendar webhooks for a user."""
        try:
            response = await self.supabase.table('calendar_webhooks').select(
                'id, user_id, calendar_id, expires_at, webhook_url'
            ).eq('user_id', user_id).execute()
            
            if response.data:
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting user webhooks: {str(e)}")
            return []
    
    async def _renew_single_webhook(self, webhook: Dict[str, Any]) -> WebhookRenewalResult:
        """Renew a single calendar webhook."""
        try:
            # Check if webhook is actually expired
            expires_at = datetime.fromisoformat(webhook['expires_at'])
            if expires_at > datetime.now() + timedelta(hours=1):
                return WebhookRenewalResult(
                    webhook_id=webhook['id'],
                    user_id=webhook['user_id'],
                    calendar_id=webhook['calendar_id'],
                    success=True,
                    new_expiration=expires_at,
                    timestamp=datetime.now()
                )
            
            # Renew the webhook using the calendar service
            new_expiration = await self.calendar_service.renew_calendar_webhook(
                webhook_id=webhook['id'],
                user_id=webhook['user_id'],
                calendar_id=webhook['calendar_id']
            )
            
            if new_expiration:
                return WebhookRenewalResult(
                    webhook_id=webhook['id'],
                    user_id=webhook['user_id'],
                    calendar_id=webhook['calendar_id'],
                    success=True,
                    new_expiration=new_expiration,
                    timestamp=datetime.now()
                )
            else:
                return WebhookRenewalResult(
                    webhook_id=webhook['id'],
                    user_id=webhook['user_id'],
                    calendar_id=webhook['calendar_id'],
                    success=False,
                    error_message='Failed to renew webhook',
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error renewing webhook {webhook['id']}: {str(e)}")
            return WebhookRenewalResult(
                webhook_id=webhook['id'],
                user_id=webhook['user_id'],
                calendar_id=webhook['calendar_id'],
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _update_webhook_records(self, results: List[WebhookRenewalResult]) -> None:
        """Update webhook records with renewal results."""
        try:
            for result in results:
                if result.success and result.new_expiration:
                    await self.supabase.table('calendar_webhooks').update({
                        'expires_at': result.new_expiration.isoformat(),
                        'last_renewed_at': datetime.now().isoformat(),
                        'renewal_count': self.supabase.raw('renewal_count + 1')
                    }).eq('id', result.webhook_id).execute()
                    
        except Exception as e:
            logger.error(f"Error updating webhook records: {str(e)}")
    
    async def _store_renewal_summary(self, summary: Dict[str, Any]) -> None:
        """Store renewal summary in database."""
        try:
            await self.supabase.table('calendar_webhook_renewal_summaries').insert({
                'summary_data': summary,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error storing webhook renewal summary: {str(e)}")
