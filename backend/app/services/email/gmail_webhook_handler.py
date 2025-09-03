"""
Gmail webhook handler for BeSunny.ai Python backend.
Processes incoming webhook notifications from Gmail.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json
import base64

from ...core.database import get_supabase
from ...models.schemas.email import GmailWebhookPayload, GmailHistory, GmailNotification
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class GmailWebhookHandler:
    """Handles incoming Gmail webhook notifications."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def _get_supabase_client(self):
        """Get Supabase client."""
        return get_supabase()
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming Gmail webhook data."""
        try:
            # Parse webhook payload
            payload = GmailWebhookPayload(**webhook_data)
            
            # Log webhook receipt
            await self._log_webhook_receipt(payload)
            
            # Process based on resource state
            if payload.resource_state == 'change':
                await self._handle_gmail_change(payload)
            elif payload.resource_state == 'sync':
                await self._handle_gmail_sync(payload)
            else:
                logger.info(f"Unhandled resource state: {payload.resource_state}")
            
            # Mark webhook as processed
            await self._mark_webhook_processed(payload)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Gmail webhook: {e}")
            return False
    
    async def process_push_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Process Gmail push notification (Pub/Sub format)."""
        try:
            # Parse notification payload
            notification = GmailNotification(**notification_data)
            
            # Decode the base64 data
            decoded_data = json.loads(base64.b64decode(notification.message['data']).decode('utf-8'))
            email_address = decoded_data.get('emailAddress')
            history_id = decoded_data.get('historyId')
            
            if not email_address or not history_id:
                logger.error("Missing emailAddress or historyId in notification data")
                return False
            
            # Create webhook payload
            payload = GmailWebhookPayload(
                email_address=email_address,
                history_id=history_id,
                resource_state='change'
            )
            
            # Process the webhook
            return await self.process_webhook(payload.dict())
            
        except Exception as e:
            logger.error(f"Failed to process Gmail push notification: {e}")
            return False
    
    async def _handle_gmail_change(self, payload: GmailWebhookPayload):
        """Handle Gmail change notification."""
        try:
            # Update webhook activity tracking
            supabase = self._get_supabase_client()
            supabase.table('gmail_watches').update({
                'last_webhook_received': datetime.now().isoformat(),
                'webhook_failures': 0,
                'updated_at': datetime.now().isoformat()
            }).eq('user_email', payload.email_address).execute()
            
            # Get Gmail history to see what changed
            history_data = await self._get_gmail_history(payload.email_address, payload.history_id)
            
            if history_data and history_data.messages_added:
                # Process new messages
                for message_info in history_data.messages_added:
                    message_id = message_info['message']['id']
                    await self._process_new_message(payload.email_address, message_id)
                    
            elif history_data and history_data.messages_deleted:
                # Handle deleted messages if needed
                logger.info(f"Messages deleted for {payload.email_address}")
                
            logger.info(f"Processed Gmail change for {payload.email_address}")
            
        except Exception as e:
            logger.error(f"Failed to handle Gmail change: {e}")
            # Increment webhook failure count
            await self._increment_webhook_failures(payload.email_address)
    
    async def _handle_gmail_sync(self, payload: GmailWebhookPayload):
        """Handle Gmail sync notification."""
        try:
            # Update webhook activity tracking
            supabase = self._get_supabase_client()
            supabase.table('gmail_watches').update({
                'last_webhook_received': datetime.now().isoformat(),
                'webhook_failures': 0,
                'updated_at': datetime.now().isoformat()
            }).eq('user_email', payload.email_address).execute()
            
            logger.info(f"Gmail sync completed for {payload.email_address}")
            
        except Exception as e:
            logger.error(f"Failed to handle Gmail sync: {e}")
            await self._increment_webhook_failures(payload.email_address)
    
    async def _get_gmail_history(self, email_address: str, history_id: str) -> Optional[GmailHistory]:
        """Get Gmail history for the specified user and history ID."""
        try:
            # This would typically use Google's Gmail API
            # For now, we'll return None and log the attempt
            logger.info(f"Would fetch Gmail history for {email_address} from {history_id}")
            
            # Gmail API call will be implemented in future iteration
            # This would require Google service account credentials and JWT generation
            # Similar to the existing Gmail polling service
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get Gmail history: {e}")
            return None
    
    async def _process_new_message(self, email_address: str, message_id: str):
        """Process a new Gmail message."""
        try:
            # Check if this is a virtual email detection
            virtual_emails = await self._detect_virtual_emails(email_address, message_id)
            
            if virtual_emails:
                await self._process_virtual_email_detection(email_address, message_id, virtual_emails)
            
            # Create document from email if needed
            await self._create_document_from_email(email_address, message_id)
            
            logger.info(f"Processed new message {message_id} for {email_address}")
            
        except Exception as e:
            logger.error(f"Failed to process new message: {e}")
    
    async def _detect_virtual_emails(self, user_email: str, message_id: str) -> List[Dict[str, Any]]:
        """Detect virtual email addresses in the message."""
        try:
            # This would typically involve fetching the message content
            # and checking for virtual email patterns
            # For now, return empty list
            logger.info(f"Would detect virtual emails in message {message_id} for {user_email}")
            
            # Virtual email detection will be implemented in future iteration
            # This would require fetching the message content via Gmail API
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to detect virtual emails: {e}")
            return []
    
    async def _process_virtual_email_detection(self, user_email: str, message_id: str, virtual_emails: List[Dict[str, Any]]):
        """Process virtual email detection results."""
        try:
            for virtual_email_info in virtual_emails:
                # Record virtual email detection
                detection_data = {
                    'user_id': await self._get_user_id_by_email(user_email),
                    'virtual_email': virtual_email_info['email'],
                    'username': virtual_email_info['username'],
                    'email_type': virtual_email_info['type'],
                    'gmail_message_id': message_id,
                    'created_at': datetime.now().isoformat()
                }
                
                supabase = self._get_supabase_client()
                supabase.table('virtual_email_detections').insert(detection_data).execute()
                
                logger.info(f"Recorded virtual email detection: {virtual_email_info['email']}")
                
        except Exception as e:
            logger.error(f"Failed to process virtual email detection: {e}")
    
    async def _create_document_from_email(self, email_address: str, message_id: str):
        """Create a document entry from an email."""
        try:
            # Check if document already exists
            supabase = self._get_supabase_client()
            existing_doc = supabase.table('documents').select('id').eq('source_id', message_id).single().execute()
            
            if existing_doc.data:
                logger.info(f"Document already exists for message {message_id}")
                return
            
            # Get user ID
            user_id = await self._get_user_id_by_email(email_address)
            if not user_id:
                logger.warning(f"No user found for email {email_address}")
                return
            
            # Create basic document data
            doc_data = {
                'title': f"Email from {message_id}",
                'type': 'email',
                'status': 'active',
                'source': 'gmail',
                'source_id': message_id,
                'created_by': user_id,
                'created_at': datetime.now().isoformat(),
                'last_synced_at': datetime.now().isoformat()
            }
            
            # Insert document
            supabase = self._get_supabase_client()
            supabase.table('documents').insert(doc_data).execute()
            
            if result.data:
                logger.info(f"Created new document {result.data[0]['id']} for message {message_id}")
                
                # Send to N8N webhook for classification
                await self._send_to_n8n_classification(result.data[0]['id'], message_id)
            
        except Exception as e:
            logger.error(f"Failed to create document from email: {e}")
    
    async def _send_to_n8n_classification(self, document_id: str, message_id: str):
        """Send document to N8N for classification."""
        try:
            if not self.settings.n8n_classification_webhook_url:
                logger.warning("N8N classification webhook URL not configured")
                return
            
            # Prepare webhook payload
            webhook_data = {
                'document_id': document_id,
                'gmail_message_id': message_id,
                'action': 'classify_email',
                'timestamp': datetime.now().isoformat()
            }
            
            # Send webhook (this would be an async HTTP call)
            # For now, just log the attempt
            logger.info(f"Would send to N8N classification webhook: {webhook_data}")
            
            # HTTP call to N8N will be implemented in future iteration
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         self.settings.n8n_classification_webhook_url,
            #         json=webhook_data
            #     )
            
        except Exception as e:
            logger.error(f"Failed to send to N8N classification: {e}")
    
    async def _get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID by email address."""
        try:
            supabase = self._get_supabase_client()
            result = supabase.table('users').select('id').eq('email', email).single().execute()
            return result.data['id'] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user ID by email: {e}")
            return None
    
    async def _increment_webhook_failures(self, email_address: str):
        """Increment webhook failure count for the user."""
        try:
            supabase = self._get_supabase_client()
            supabase.table('gmail_watches').update({
                'webhook_failures': supabase.raw('webhook_failures + 1'),
                'updated_at': datetime.now().isoformat()
            }).eq('user_email', email_address).execute()
            
        except Exception as e:
            logger.error(f"Failed to increment webhook failures: {e}")
    
    async def _log_webhook_receipt(self, payload: GmailWebhookPayload):
        """Log webhook receipt in database."""
        try:
            # Check if we have an email_processing_logs table
            # If not, we'll just log to the application logs
            logger.info(f"Gmail webhook received for {payload.email_address}")
            
        except Exception as e:
            logger.error(f"Failed to log webhook receipt: {e}")
    
    async def _mark_webhook_processed(self, payload: GmailWebhookPayload):
        """Mark webhook as processed."""
        try:
            # Update the gmail_watches table to mark as processed
            supabase = self._get_supabase_client()
            supabase.table('gmail_watches').update({
                'last_webhook_received': datetime.now().isoformat(),
                'webhook_failures': 0,
                'updated_at': datetime.now().isoformat()
            }).eq('user_email', payload.email_address).execute()
            
            logger.info(f"Gmail webhook processed for {payload.email_address}")
            
        except Exception as e:
            logger.error(f"Failed to mark webhook as processed: {e}")
    
    async def get_webhook_logs(self, email_address: Optional[str] = None, limit: int = 100) -> list:
        """Get webhook processing logs."""
        try:
            # This would return logs from the gmail_watches table
            supabase = self._get_supabase_client()
            query = supabase.table('gmail_watches').select('*').order('updated_at', desc=True).limit(limit)
            
            if email_address:
                query = query.eq('user_email', email_address)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get webhook logs: {e}")
            return []
    
    async def get_active_watches(self, user_id: Optional[str] = None) -> list:
        """Get active Gmail watches."""
        try:
            supabase = self._get_supabase_client()
            query = supabase.table('gmail_watches').select('*').eq('is_active', True)
            
            if user_id:
                # Join with users table to filter by user_id
                # For now, return all active watches
                pass
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get active watches: {e}")
            return []
