"""
Google Drive webhook handler for BeSunny.ai Python backend.
Processes incoming webhook notifications from Google Drive.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json

from ...core.database import get_supabase
from ...models.schemas.drive import DriveWebhookPayload

logger = logging.getLogger(__name__)


class DriveWebhookHandler:
    """Handles incoming Google Drive webhook notifications."""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming Drive webhook data."""
        try:
            # Parse webhook payload
            payload = DriveWebhookPayload(**webhook_data)
            
            # Log webhook receipt
            await self._log_webhook_receipt(payload)
            
            # Process based on resource state
            if payload.resource_state == 'change':
                await self._handle_file_change(payload)
            elif payload.resource_state == 'trash':
                await self._handle_file_deletion(payload)
            else:
                logger.info(f"Unhandled resource state: {payload.resource_state}")
            
            # Mark webhook as processed
            await self._mark_webhook_processed(payload)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Drive webhook: {e}")
            return False
    
    async def _handle_file_change(self, payload: DriveWebhookPayload):
        """Handle file change notification."""
        try:
            # Get file watch information
            watch_result = await self.supabase.table('drive_file_watches').select('*').eq('file_id', payload.file_id).eq('is_active', True).single().execute()
            
            if not watch_result.data:
                logger.warning(f"No active watch found for file {payload.file_id}")
                return
            
            watch = watch_result.data
            
            # Get document information
            doc_result = await self.supabase.table('documents').select('*').eq('file_id', payload.file_id).single().execute()
            
            if doc_result.data:
                # Update document metadata
                await self.supabase.table('documents').update({
                    'last_synced_at': datetime.now().isoformat(),
                    'status': 'updated'
                }).eq('id', doc_result.data['id']).execute()
                
                logger.info(f"Updated document {doc_result.data['id']} for file change")
            else:
                # Create new document entry
                await self._create_document_from_file(payload.file_id, watch['project_id'], watch.get('user_id'))
                
        except Exception as e:
            logger.error(f"Failed to handle file change: {e}")
    
    async def _handle_file_deletion(self, payload: DriveWebhookPayload):
        """Handle file deletion notification."""
        try:
            # Mark document as deleted
            await self.supabase.table('documents').update({
                'status': 'deleted',
                'last_synced_at': datetime.now().isoformat()
            }).eq('file_id', payload.file_id).execute()
            
            # Mark watch as inactive
            await self.supabase.table('drive_file_watches').update({
                'is_active': False
            }).eq('file_id', payload.file_id).execute()
            
            logger.info(f"Marked file {payload.file_id} as deleted")
            
        except Exception as e:
            logger.error(f"Failed to handle file deletion: {e}")
    
    async def _create_document_from_file(self, file_id: str, project_id: str, user_id: Optional[str]):
        """Create a new document entry from a Drive file."""
        try:
            # Basic document data
            doc_data = {
                'file_id': file_id,
                'type': 'document',
                'status': 'active',
                'project_id': project_id,
                'created_by': user_id,
                'created_at': datetime.now().isoformat(),
                'last_synced_at': datetime.now().isoformat()
            }
            
            # Insert document
            result = await self.supabase.table('documents').insert(doc_data).execute()
            
            if result.data:
                logger.info(f"Created new document {result.data[0]['id']} for file {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to create document from file: {e}")
    
    async def _log_webhook_receipt(self, payload: DriveWebhookPayload):
        """Log webhook receipt in database."""
        try:
            log_data = {
                'file_id': payload.file_id,
                'channel_id': payload.channel_id,
                'resource_id': payload.resource_id,
                'resource_state': payload.resource_state,
                'webhook_received_at': datetime.now().isoformat(),
                'n8n_webhook_sent': False  # Will be sent to N8N later
            }
            
            await self.supabase.table('drive_webhook_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log webhook receipt: {e}")
    
    async def _mark_webhook_processed(self, payload: DriveWebhookPayload):
        """Mark webhook as processed."""
        try:
            await self.supabase.table('drive_webhook_logs').update({
                'n8n_webhook_sent': True,
                'n8n_webhook_sent_at': datetime.now().isoformat()
            }).eq('file_id', payload.file_id).eq('webhook_received_at', datetime.now().isoformat()).execute()
            
        except Exception as e:
            logger.error(f"Failed to mark webhook as processed: {e}")
    
    async def get_webhook_logs(self, file_id: Optional[str] = None, limit: int = 100) -> list:
        """Get webhook processing logs."""
        try:
            query = self.supabase.table('drive_webhook_logs').select('*').order('webhook_received_at', desc=True).limit(limit)
            
            if file_id:
                query = query.eq('file_id', file_id)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get webhook logs: {e}")
            return []
    
    async def get_active_watches(self, project_id: Optional[str] = None) -> list:
        """Get active file watches."""
        try:
            query = self.supabase.table('drive_file_watches').select('*').eq('is_active', True)
            
            if project_id:
                query = query.eq('project_id', project_id)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get active watches: {e}")
            return []
