"""
Calendar webhook management service for BeSunny.ai Python backend.
Handles calendar webhook operations like stop, recreate, verify, and test.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
            google_stopped = await self._stop_google_webhook(webhook, user_id)
            
            if google_stopped:
                # Update database record
                await self._update_webhook_status(user_id, 'stopped')
                
                logger.info(f"Calendar webhook stopped for user {user_id}")
                return {
                    'success': True,
                    'message': 'Calendar webhook stopped successfully',
                    'webhook_id': webhook.get('id')
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to stop webhook at Google',
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
            google_verified = await self._verify_google_webhook(webhook, user_id)
            
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
            test_sent = await self._send_test_notification(webhook, user_id)
            
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
    
    async def health_check_webhook(self, user_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive health check on user's calendar webhook.
        
        Args:
            user_id: User ID
            
        Returns:
            Health check result
        """
        try:
            logger.info(f"Performing health check on calendar webhook for user {user_id}")
            
            webhook = await self._get_user_calendar_webhook(user_id)
            if not webhook:
                return {
                    'success': False,
                    'message': 'No calendar webhook found for user',
                    'health_status': 'missing'
                }
            
            health_checks = []
            
            # Check if webhook is active in database
            if webhook.get('is_active'):
                health_checks.append('database_active')
            else:
                health_checks.append('database_inactive')
            
            # Check if webhook exists at Google
            google_exists = await self._check_google_webhook_exists(webhook, user_id)
            if google_exists:
                health_checks.append('google_exists')
            else:
                health_checks.append('google_missing')
            
            # Check webhook expiration
            expiration_time = webhook.get('expiration_time')
            if expiration_time:
                expires_at = datetime.fromisoformat(expiration_time.replace('Z', '+00:00'))
                if expires_at > datetime.now() + timedelta(hours=1):
                    health_checks.append('not_expiring_soon')
                else:
                    health_checks.append('expiring_soon')
            else:
                health_checks.append('no_expiration')
            
            # Determine overall health status
            if 'google_missing' in health_checks or 'database_inactive' in health_checks:
                health_status = 'unhealthy'
            elif 'expiring_soon' in health_checks:
                health_status = 'warning'
            else:
                health_status = 'healthy'
            
            return {
                'success': True,
                'webhook_id': webhook.get('id'),
                'health_status': health_status,
                'health_checks': health_checks,
                'message': f'Webhook health check completed: {health_status}'
            }
            
        except Exception as e:
            logger.error(f"Error performing health check for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error performing health check: {str(e)}',
                'error_message': str(e)
            }
    
    async def auto_fix_webhook(self, user_id: str) -> Dict[str, Any]:
        """
        Automatically fix webhook issues for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Auto-fix result
        """
        try:
            logger.info(f"Attempting to auto-fix webhook for user {user_id}")
            
            # Perform health check first
            health_result = await self.health_check_webhook(user_id)
            if not health_result.get('success'):
                return health_result
            
            health_status = health_result.get('health_status')
            if health_status == 'healthy':
                return {
                    'success': True,
                    'message': 'Webhook is healthy, no fixes needed',
                    'webhook_id': health_result.get('webhook_id')
                }
            
            # Attempt to fix based on health status
            if health_status == 'unhealthy':
                # Recreate the webhook
                return await self.recreate_webhook(user_id)
            elif health_status == 'warning':
                # Renew the webhook
                from .calendar_webhook_renewal_service import CalendarWebhookRenewalService
                renewal_service = CalendarWebhookRenewalService()
                return await renewal_service.renew_user_webhooks(user_id)
            else:
                return {
                    'success': False,
                    'message': f'Unknown health status: {health_status}'
                }
                
        except Exception as e:
            logger.error(f"Error auto-fixing webhook for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error auto-fixing webhook: {str(e)}',
                'error_message': str(e)
            }
    
    # Private helper methods
    
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
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            result = await self.supabase.table("google_credentials") \
                .select("access_token, refresh_token, token_uri, client_id, client_secret, scopes") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                cred_data = result.data
                return Credentials(
                    token=cred_data['access_token'],
                    refresh_token=cred_data['refresh_token'],
                    token_uri=cred_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=cred_data.get('client_id', self.settings.google_client_id),
                    client_secret=cred_data.get('client_secret', self.settings.google_client_secret),
                    scopes=cred_data.get('scopes', ['https://www.googleapis.com/auth/calendar.readonly'])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    async def _stop_google_webhook(self, webhook: Dict[str, Any], user_id: str) -> bool:
        """Stop webhook at Google."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No credentials found for user {user_id}")
                return False
            
            service = build('calendar', 'v3', credentials=credentials)
            webhook_id = webhook.get('webhook_id')
            
            if not webhook_id:
                logger.warning(f"No webhook ID found for user {user_id}")
                return False
            
            # Stop the webhook using Google Calendar API
            service.stop(
                id=webhook_id
            ).execute()
            
            logger.info(f"Successfully stopped Google webhook {webhook_id} for user {user_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                # Webhook already doesn't exist, consider it stopped
                logger.info(f"Webhook {webhook.get('webhook_id')} already stopped for user {user_id}")
                return True
            else:
                logger.error(f"Google API error stopping webhook: {e}")
                return False
        except Exception as e:
            logger.error(f"Error stopping Google webhook: {str(e)}")
            return False
    
    async def _verify_google_webhook(self, webhook: Dict[str, Any], user_id: str) -> bool:
        """Verify webhook at Google."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No credentials found for user {user_id}")
                return False
            
            service = build('calendar', 'v3', credentials=credentials)
            webhook_id = webhook.get('webhook_id')
            
            if not webhook_id:
                logger.warning(f"No webhook ID found for user {user_id}")
                return False
            
            # Try to get webhook info from Google
            try:
                service.stop(
                    id=webhook_id
                ).execute()
                
                # If we can stop it, it exists, so recreate it
                await self._recreate_google_webhook(webhook, user_id)
                return True
                
            except HttpError as e:
                if e.resp.status == 404:
                    # Webhook doesn't exist, recreate it
                    return await self._recreate_google_webhook(webhook, user_id)
                else:
                    logger.error(f"Google API error verifying webhook: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error verifying Google webhook: {str(e)}")
            return False
    
    async def _recreate_google_webhook(self, webhook: Dict[str, Any], user_id: str) -> bool:
        """Recreate webhook at Google."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No credentials found for user {user_id}")
                return False
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Create new webhook
            webhook_url = f"{self.settings.base_url}/api/v1/calendar/webhook/notify?userId={user_id}"
            channel_id = f"calendar-watch-{user_id}-{int(datetime.now().timestamp())}"
            expiration = datetime.now() + timedelta(days=7)
            
            watch_request = {
                'id': channel_id,
                'type': 'web_hook',
                'address': webhook_url,
                'params': {
                    'userId': user_id,
                },
                'expiration': expiration.isoformat() + 'Z',
            }
            
            result = service.events().watch(
                calendarId='primary',
                body=watch_request
            ).execute()
            
            # Update database with new webhook info
            await self._update_webhook_info(
                user_id, 
                result.get('id'), 
                result.get('resourceId'), 
                result.get('expiration')
            )
            
            logger.info(f"Successfully recreated Google webhook for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recreating Google webhook: {str(e)}")
            return False
    
    async def _check_google_webhook_exists(self, webhook: Dict[str, Any], user_id: str) -> bool:
        """Check if webhook exists at Google."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return False
            
            service = build('calendar', 'v3', credentials=credentials)
            webhook_id = webhook.get('webhook_id')
            
            if not webhook_id:
                return False
            
            # Try to stop the webhook - if it exists, this will succeed
            try:
                service.stop(id=webhook_id).execute()
                # Recreate it since we just stopped it
                await self._recreate_google_webhook(webhook, user_id)
                return True
            except HttpError as e:
                if e.resp.status == 404:
                    return False
                else:
                    logger.error(f"Google API error checking webhook: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking Google webhook: {str(e)}")
            return False
    
    async def _send_test_notification(self, webhook: Dict[str, Any], user_id: str) -> bool:
        """Send test notification to webhook."""
        try:
            # Create a test calendar event to trigger webhook
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No credentials found for user {user_id}")
                return False
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Create a test event
            test_event = {
                'summary': 'Webhook Test Event',
                'description': 'This is a test event to verify webhook functionality',
                'start': {
                    'dateTime': (datetime.now() + timedelta(minutes=5)).isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (datetime.now() + timedelta(minutes=10)).isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
            }
            
            # Insert test event
            event = service.events().insert(
                calendarId='primary',
                body=test_event
            ).execute()
            
            # Wait a moment for webhook to process
            await asyncio.sleep(2)
            
            # Delete test event
            service.events().delete(
                calendarId='primary',
                eventId=event['id']
            ).execute()
            
            logger.info(f"Test notification sent for webhook {webhook.get('id')}")
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
    
    async def _update_webhook_info(self, user_id: str, webhook_id: str, resource_id: str, expiration: str) -> bool:
        """Update webhook information in database."""
        try:
            supabase = await self.supabase
            supabase.table("calendar_webhooks") \
                .update({
                    'webhook_id': webhook_id,
                    'resource_id': resource_id,
                    'expiration_time': expiration,
                    'is_active': True,
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating webhook info: {str(e)}")
            return False
