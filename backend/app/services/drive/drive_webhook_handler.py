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
            
            # Check if this is an email alias watch
            if watch.get('watch_type') == 'email_alias':
                # Use the email alias drive service for processing
                await self._handle_email_alias_file_change(payload.file_id, watch.get('user_id'))
            else:
                # Use the standard file change handling
                await self._handle_standard_file_change(payload, watch)
                
        except Exception as e:
            logger.error(f"Failed to handle file change: {e}")
    
    async def _handle_email_alias_file_change(self, file_id: str, user_id: Optional[str]):
        """Handle file change for email alias workflow."""
        try:
            if not user_id:
                logger.warning(f"No user_id available for email alias file change: {file_id}")
                return
            
            # Import and use the email alias drive service
            from .email_alias_drive_service import EmailAliasDriveService
            
            drive_service = EmailAliasDriveService()
            result = await drive_service.handle_file_update(file_id, user_id)
            
            if result['success']:
                logger.info(f"Email alias file change handled successfully: {result['message']}")
            else:
                logger.error(f"Failed to handle email alias file change: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error handling email alias file change: {e}")
    
    async def _handle_standard_file_change(self, payload: DriveWebhookPayload, watch: Dict[str, Any]):
        """Handle standard file change notification."""
        try:
            # Get document information
            doc_result = await self.supabase.table('documents').select('*').eq('file_id', payload.file_id).single().execute()
            
            if doc_result.data:
                # Update document metadata with latest file information
                await self._update_document_metadata(doc_result.data['id'], payload.file_id, watch.get('user_id'))
                
                # Trigger re-vectorization workflow for the updated file
                await self._trigger_revectorization_workflow(doc_result.data['id'], payload.file_id, watch.get('user_id'))
                
                logger.info(f"Updated document {doc_result.data['id']} for file change and triggered re-vectorization")
            else:
                # Create new document entry
                await self._create_document_from_file(payload.file_id, watch['project_id'], watch.get('user_id'))
                
        except Exception as e:
            logger.error(f"Failed to handle standard file change: {e}")
    
    async def _update_document_metadata(self, document_id: str, file_id: str, user_id: Optional[str]):
        """Update document metadata with latest file information."""
        try:
            # Get latest file metadata from Google Drive
            if user_id:
                file_metadata = await self._get_latest_file_metadata(file_id, user_id)
                
                if file_metadata:
                    # Update document with new metadata
                    update_data = {
                        'last_synced_at': datetime.now().isoformat(),
                        'status': 'updated',
                        'title': file_metadata.get('name', f'Drive File {file_id}'),
                        'file_size': str(file_metadata.get('size', 0)),
                        'drive_metadata': file_metadata,
                        'last_modified_at': file_metadata.get('modifiedTime'),
                        'update_count': self.supabase.rpc('increment_update_count', {'doc_id': document_id})
                    }
                    
                    await self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
                    
                    logger.info(f"Updated document {document_id} with latest Drive metadata")
                else:
                    logger.warning(f"Could not retrieve latest metadata for file {file_id}")
            else:
                logger.warning(f"No user_id available for updating document {document_id}")
                
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
    
    async def _get_latest_file_metadata(self, file_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get latest file metadata from Google Drive API."""
        try:
            # Import drive service here to avoid circular imports
            from ...drive.drive_service import DriveService
            
            drive_service = DriveService()
            
            # Get file metadata
            file_metadata = await drive_service.get_file_metadata(file_id, user_id)
            
            if file_metadata:
                return {
                    'id': file_metadata.id,
                    'name': file_metadata.name,
                    'mimeType': file_metadata.mime_type,
                    'size': file_metadata.size,
                    'modifiedTime': file_metadata.modified_time,
                    'parents': file_metadata.parents,
                    'webViewLink': file_metadata.web_view_link,
                    'lastChecked': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest Drive file metadata for file {file_id}: {e}")
            return None
    
    async def _trigger_revectorization_workflow(self, document_id: str, file_id: str, user_id: Optional[str]):
        """Trigger re-vectorization workflow for updated file."""
        try:
            # TODO: This will be implemented when the re-vectorization workflow is built
            # For now, we'll log the event and prepare the payload
            
            # Get document details for the workflow
            doc_result = await self.supabase.table('documents').select('*').eq('id', document_id).single().execute()
            
            if doc_result.data:
                # Prepare re-vectorization payload
                revectorization_payload = {
                    'document_id': document_id,
                    'file_id': file_id,
                    'user_id': user_id,
                    'project_id': doc_result.data.get('project_id'),
                    'file_name': doc_result.data.get('title'),
                    'file_type': doc_result.data.get('mimetype'),
                    'trigger_type': 'drive_file_update',
                    'triggered_at': datetime.now().isoformat(),
                    'file_url': doc_result.data.get('drive_url'),
                    'metadata': doc_result.data.get('drive_metadata', {})
                }
                
                # Log the re-vectorization trigger
                await self._log_revectorization_trigger(document_id, file_id, revectorization_payload)
                
                # TODO: Send to re-vectorization service/workflow
                # await self._send_to_revectorization_service(revectorization_payload)
                
                logger.info(f"Re-vectorization workflow triggered for document {document_id}, file {file_id}")
            else:
                logger.warning(f"Could not retrieve document {document_id} for re-vectorization workflow")
                
        except Exception as e:
            logger.error(f"Failed to trigger re-vectorization workflow: {e}")
    
    async def _log_revectorization_trigger(self, document_id: str, file_id: str, payload: Dict[str, Any]):
        """Log re-vectorization trigger event."""
        try:
            log_data = {
                'document_id': document_id,
                'file_id': file_id,
                'event_type': 'revectorization_triggered',
                'payload': payload,
                'triggered_at': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            await self.supabase.table('drive_webhook_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log re-vectorization trigger: {e}")
    
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
