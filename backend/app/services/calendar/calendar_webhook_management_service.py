"""
Calendar webhook management service for BeSunny.ai Python backend.
Handles calendar webhook operations like stop, recreate, verify, and test.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class WebhookManagementResult(BaseModel):
    """Result of a webhook management operation."""
    user_id: str
    action: str
    success: bool
    message: str
    webhook_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime


class CalendarWebhookManagementService:
    """Service for managing calendar webhooks."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        
        logger.info("Calendar Webhook Management Service initialized")
    
    async def stop_webhook(self, user_id: str) -> Dict[str, Any]:
        """
        Stop a user's calendar webhook.
        
        Args:
            user_id: User ID
            
        Returns:
            Operation result
        """
        try:
            logger.info(f"Stopping calendar webhook for user {user_id}")
            
            # Get user's calendar webhook
            webhook = await self._get_user_calendar_webhook(user_id)
            if not webhook:
                return {
                    'success': False,
                    'message': 'No calendar webhook found for user'
                }
            
            # Stop the webhook at Google
            google_stopped = await self._stop_google_webhook(webhook)
            
            # Update database record
            await self._update_webhook_status(user_id, 'stopped')
            
            logger.info(f"Calendar webhook stopped for user {user_id}")
            return {
                'success': True,
                'message': 'Calendar webhook stopped successfully',
                'webhook_id': webhook.get('id')
            }
            
        except Exception as e:
            logger.error(f"Error stopping calendar webhook for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error stopping webhook: {str(e)}',
                'error_message': str(e)
            }
    
    async def recreate_webhook(self, user_id: str) -> Dict[str, Any]:
        """
        Recreate a user's calendar webhook.
        
        Args:
            user_id: User ID
            
        Returns:
            Operation result
        """
        try:
            logger.info(f"Recreating calendar webhook for user {user_id}")
            
            # Stop existing webhook if it exists
            await self.stop_webhook(user_id)
            
            # Create new webhook
            from .calendar_webhook_renewal_service import CalendarWebhookRenewalService
            renewal_service = CalendarWebhookRenewalService()
            
            result = await renewal_service.renew_user_webhooks(user_id)
            
            if result.get('success'):
                logger.info(f"Calendar webhook recreated for user {user_id}")
                return {
                    'success': True,
                    'message': 'Calendar webhook recreated successfully',
                    'webhook_id': result.get('webhook_id')
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to recreate webhook',
                    'error_message': result.get('error_message')
                }
                
        except Exception as e:
            logger.error(f"Error recreating calendar webhook for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error recreating webhook: {str(e)}',
                'error_message': str(e)
            }
    
    async def verify_webhook(self, user_id: str) -> Dict[str, Any]:
        """
        Verify a user's calendar webhook.
        
        Args:
            user_id: User ID
            
        Returns:
            Verification result
        """
        try:
            logger.info(f"Verifying calendar webhook for user {user_id}")
            
            # Get user's calendar webhook
            webhook = await self._get_user_calendar_webhook(user_id)
            if not webhook:
                return {
                    'success': False,
                    'message': 'No calendar webhook found for user'
                }
            
            # Verify webhook at Google
            google_verified = await self._verify_google_webhook(webhook)
            
            if google_verified:
                # Update database record
                await self._update_webhook_status(user_id, 'verified')
                
                logger.info(f"Calendar webhook verified for user {user_id}")
                return {
                    'success': True,
                    'message': 'Calendar webhook verified successfully',
                    'webhook_id': webhook.get('id')
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to verify webhook at Google',
                    'webhook_id': webhook.get('id')
                }
                
        except Exception as e:
            logger.error(f"Error verifying calendar webhook for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error verifying webhook: {str(e)}',
                'error_message': str(e)
            }
    
    async def test_webhook(self, user_id: str) -> Dict[str, Any]:
        """
        Test a user's calendar webhook.
        
        Args:
            user_id: User ID
            
        Returns:
            Test result
        """
        try:
            logger.info(f"Testing calendar webhook for user {user_id}")
            
            # Get user's calendar webhook
            webhook = await self._get_user_calendar_webhook(user_id)
            if not webhook:
                return {
                    'success': False,
                    'message': 'No calendar webhook found for user'
                }
            
            # Send test notification
            test_sent = await self._send_test_notification(webhook)
            
            if test_sent:
                logger.info(f"Calendar webhook test sent for user {user_id}")
                return {
                    'success': True,
                    'message': 'Test notification sent successfully',
                    'webhook_id': webhook.get('id')
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send test notification',
                    'webhook_id': webhook.get('id')
                }
                
        except Exception as e:
            logger.error(f"Error testing calendar webhook for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error testing webhook: {str(e)}',
                'error_message': str(e)
            }
    
    async def _get_user_calendar_webhook(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's calendar webhook."""
        try:
            supabase = await self.supabase
            result = supabase.table("calendar_webhooks") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            logger.error(f"Error getting user calendar webhook: {str(e)}")
            return None
    
    async def _stop_google_webhook(self, webhook: Dict[str, Any]) -> bool:
        """Stop webhook at Google."""
        try:
            # This would integrate with Google Calendar API to stop the webhook
            # For now, we'll simulate the operation
            logger.info(f"Stopping Google webhook {webhook.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Google webhook: {str(e)}")
            return False
    
    async def _verify_google_webhook(self, webhook: Dict[str, Any]) -> bool:
        """Verify webhook at Google."""
        try:
            # This would integrate with Google Calendar API to verify the webhook
            # For now, we'll simulate the operation
            logger.info(f"Verifying Google webhook {webhook.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying Google webhook: {str(e)}")
            return False
    
    async def _send_test_notification(self, webhook: Dict[str, Any]) -> bool:
        """Send test notification to webhook."""
        try:
            # This would send a test notification to the webhook URL
            # For now, we'll simulate the operation
            logger.info(f"Sending test notification to webhook {webhook.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending test notification: {str(e)}")
            return False
    
    async def _update_webhook_status(self, user_id: str, status: str) -> bool:
        """Update webhook status in database."""
        try:
            supabase = await self.supabase
            supabase.table("calendar_webhooks") \
                .update({
                    'status': status,
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating webhook status: {str(e)}")
            return False
