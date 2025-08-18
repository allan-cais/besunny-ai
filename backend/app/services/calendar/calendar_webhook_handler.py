"""
Google Calendar webhook handler for BeSunny.ai Python backend.
Processes incoming webhook notifications from Google Calendar.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ...core.database import get_supabase
from ...models.schemas.calendar import CalendarWebhookPayload

logger = logging.getLogger(__name__)


class CalendarWebhookHandler:
    """Handles incoming Google Calendar webhook notifications."""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming Calendar webhook data."""
        try:
            # Parse webhook payload
            payload = CalendarWebhookPayload(**webhook_data)
            
            # Log webhook receipt
            await self._log_webhook_receipt(payload)
            
            # Process based on resource state
            if payload.resource_state == 'change':
                await self._handle_calendar_change(payload)
            elif payload.resource_state == 'trash':
                await self._handle_calendar_deletion(payload)
            else:
                logger.info(f"Unhandled resource state: {payload.resource_state}")
            
            # Mark webhook as processed
            await self._mark_webhook_processed(payload)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Calendar webhook: {e}")
            return False
    
    async def _handle_calendar_change(self, payload: CalendarWebhookPayload):
        """Handle calendar change notification."""
        try:
            # Get webhook information
            webhook_result = await self.supabase.table('calendar_webhooks').select('*').eq('webhook_id', payload.webhook_id).eq('is_active', True).single().execute()
            
            if not webhook_result.data:
                logger.warning(f"No active webhook found for {payload.webhook_id}")
                return
            
            webhook = webhook_result.data
            
            # Get meeting information
            meeting_result = await self.supabase.table('meetings').select('*').eq('google_calendar_event_id', payload.event_id).single().execute()
            
            if meeting_result.data:
                # Update meeting metadata
                await self.supabase.table('meetings').update({
                    'last_synced_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }).eq('id', meeting_result.data['id']).execute()
                
                logger.info(f"Updated meeting {meeting_result.data['id']} for calendar change")
            else:
                # Create new meeting entry (this would need the actual event data)
                logger.info(f"Calendar change detected for new event {payload.event_id}")
                
        except Exception as e:
            logger.error(f"Failed to handle calendar change: {e}")
    
    async def _handle_calendar_deletion(self, payload: CalendarWebhookPayload):
        """Handle calendar deletion notification."""
        try:
            # Mark meeting as deleted
            await self.supabase.table('meetings').update({
                'bot_status': 'failed',
                'updated_at': datetime.now().isoformat()
            }).eq('google_calendar_event_id', payload.event_id).execute()
            
            logger.info(f"Marked meeting for event {payload.event_id} as failed due to deletion")
            
        except Exception as e:
            logger.error(f"Failed to handle calendar deletion: {e}")
    
    async def _log_webhook_receipt(self, payload: CalendarWebhookPayload):
        """Log webhook receipt in database."""
        try:
            log_data = {
                'webhook_id': payload.webhook_id,
                'event_id': payload.event_id,
                'resource_state': payload.resource_state,
                'resource_uri': payload.resource_uri,
                'state': payload.state,
                'expiration': payload.expiration,
                'webhook_received_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('calendar_webhook_logs').insert(log_data).execute()
            logger.info(f"Calendar webhook logged for event {payload.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to log webhook receipt: {e}")
    
    async def _mark_webhook_processed(self, payload: CalendarWebhookPayload):
        """Mark webhook as processed."""
        try:
            # Update the webhook log to mark as processed
            await self.supabase.table('calendar_webhook_logs').update({
                'n8n_webhook_sent': True,
                'n8n_webhook_sent_at': datetime.now().isoformat()
            }).eq('webhook_id', payload.webhook_id).eq('event_id', payload.event_id).execute()
            
            logger.info(f"Calendar webhook processed for event {payload.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to mark webhook as processed: {e}")
    
    async def get_webhook_logs(self, webhook_id: Optional[str] = None, limit: int = 100) -> list:
        """Get webhook processing logs."""
        try:
            query = self.supabase.table('calendar_webhook_logs').select('*').order('created_at', desc=True).limit(limit)
            
            if webhook_id:
                query = query.eq('webhook_id', webhook_id)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get webhook logs: {e}")
            return []
    
    async def get_active_webhooks(self, user_id: Optional[str] = None) -> list:
        """Get active calendar webhooks."""
        try:
            query = self.supabase.table('calendar_webhooks').select('*').eq('is_active', True)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get active webhooks: {e}")
            return []
