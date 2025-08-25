"""
Email Alias Drive Service for BeSunny.ai Python backend.
Handles Drive file processing specifically for the email alias workflow.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.drive import DriveFile
from .drive_service import DriveService

logger = logging.getLogger(__name__)


class EmailAliasDriveService:
    """Service for handling Drive files in the email alias workflow."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.drive_service = DriveService()
    
    async def process_drive_file_from_email(
        self, 
        file_id: str, 
        document_id: str, 
        user_id: str, 
        drive_url: Optional[str] = None,
        email_content: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a Drive file that was shared via email alias.
        
        This method:
        1. Sets up file watch for monitoring changes
        2. Stores file metadata in documents table
        3. Prepares file for classification agent
        4. Logs the processing event
        """
        try:
            logger.info(f"Processing Drive file {file_id} from email alias for user {user_id}")
            
            # Set up file watch
            watch_id = await self._setup_file_watch(file_id, document_id, user_id)
            if not watch_id:
                raise Exception(f"Failed to set up file watch for {file_id}")
            
            # Store file metadata
            metadata_result = await self._store_file_metadata(file_id, document_id, user_id, drive_url)
            if not metadata_result:
                raise Exception(f"Failed to store metadata for {file_id}")
            
            # Prepare classification payload
            classification_payload = await self._prepare_classification_payload(
                file_id, document_id, user_id, email_content
            )
            
            # Log processing success
            await self._log_processing_success(document_id, file_id, user_id, watch_id)
            
            return {
                'success': True,
                'watch_id': watch_id,
                'document_id': document_id,
                'file_id': file_id,
                'classification_payload': classification_payload,
                'message': f"Drive file {file_id} processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to process Drive file {file_id}: {e}")
            await self._log_processing_error(document_id, file_id, user_id, str(e))
            
            return {
                'success': False,
                'error': str(e),
                'file_id': file_id,
                'message': f"Failed to process Drive file {file_id}"
            }
    
    async def handle_file_update(
        self, 
        file_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle file update notification from Drive webhook.
        
        This method:
        1. Updates document metadata
        2. Triggers re-vectorization workflow
        3. Logs the update event
        """
        try:
            logger.info(f"Handling file update for Drive file {file_id}")
            
            # Get document associated with this file
            document = await self._get_document_by_file_id(file_id)
            if not document:
                raise Exception(f"No document found for file {file_id}")
            
            # Update document metadata
            metadata_updated = await self._update_document_metadata(document['id'], file_id, user_id)
            if not metadata_updated:
                raise Exception(f"Failed to update metadata for document {document['id']}")
            
            # Trigger re-vectorization workflow
            workflow_triggered = await self._trigger_revectorization_workflow(document['id'], file_id, user_id)
            
            # Log update success
            await self._log_update_success(document['id'], file_id, user_id)
            
            return {
                'success': True,
                'document_id': document['id'],
                'file_id': file_id,
                'metadata_updated': metadata_updated,
                'workflow_triggered': workflow_triggered,
                'message': f"File update handled successfully for {file_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to handle file update for {file_id}: {e}")
            await self._log_update_error(file_id, user_id, str(e))
            
            return {
                'success': False,
                'error': str(e),
                'file_id': file_id,
                'message': f"Failed to handle file update for {file_id}"
            }
    
    async def _setup_file_watch(self, file_id: str, document_id: str, user_id: str) -> Optional[str]:
        """Set up file watch for monitoring changes."""
        try:
            watch_id = await self.drive_service.setup_file_watch_for_email_alias(
                file_id=file_id,
                user_id=user_id,
                document_id=document_id
            )
            
            if watch_id:
                logger.info(f"File watch set up successfully for {file_id}: {watch_id}")
                return watch_id
            else:
                logger.error(f"Failed to set up file watch for {file_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error setting up file watch for {file_id}: {e}")
            return None
    
    async def _store_file_metadata(self, file_id: str, document_id: str, user_id: str, drive_url: Optional[str]) -> bool:
        """Store file metadata in documents table."""
        try:
            # Get file metadata from Google Drive
            file_metadata = await self.drive_service.get_file_metadata(file_id, user_id)
            if not file_metadata:
                logger.warning(f"Could not retrieve metadata for file {file_id}")
                return False
            
            # Prepare update data
            update_data = {
                'file_id': file_id,
                'source': 'drive_shared',
                'source_id': file_id,
                'title': file_metadata.name,
                'mimetype': file_metadata.mime_type,
                'file_size': str(file_metadata.size or 0),
                'drive_url': drive_url,
                'drive_metadata': {
                    'id': file_metadata.id,
                    'name': file_metadata.name,
                    'mimeType': file_metadata.mime_type,
                    'size': file_metadata.size,
                    'modifiedTime': file_metadata.modified_time,
                    'parents': file_metadata.parents,
                    'webViewLink': file_metadata.web_view_link
                },
                'last_synced_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Update document
            result = await self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
            
            if result.data:
                logger.info(f"File metadata stored successfully for document {document_id}")
                return True
            else:
                logger.error(f"Failed to store file metadata for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing file metadata for {file_id}: {e}")
            return False
    
    async def _prepare_classification_payload(
        self, 
        file_id: str, 
        document_id: str, 
        user_id: str, 
        email_content: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare payload for classification agent."""
        try:
            # Get file content and metadata for classification
            file_data = await self.drive_service.get_file_content_for_classification(file_id, user_id)
            if not file_data:
                logger.warning(f"Could not get file content for classification: {file_id}")
                return {}
            
            # Get document details
            document = await self._get_document_by_id(document_id)
            if not document:
                logger.warning(f"Could not get document {document_id} for classification")
                return {}
            
            # Build classification payload
            classification_payload = {
                'document_id': document_id,
                'file_id': file_id,
                'user_id': user_id,
                'file_name': file_data.get('file_name'),
                'file_type': file_data.get('file_type'),
                'file_size': file_data.get('file_size'),
                'file_content': file_data.get('file_content'),
                'content_type': file_data.get('content_type'),
                'drive_url': document.get('drive_url'),
                'email_context': email_content,
                'metadata': file_data.get('metadata', {}),
                'created_at': datetime.now().isoformat(),
                'source': 'email_alias_drive'
            }
            
            logger.info(f"Classification payload prepared for file {file_id}")
            return classification_payload
            
        except Exception as e:
            logger.error(f"Error preparing classification payload for {file_id}: {e}")
            return {}
    
    async def _update_document_metadata(self, document_id: str, file_id: str, user_id: str) -> bool:
        """Update document with latest file metadata."""
        try:
            # Get latest file metadata
            file_metadata = await self.drive_service.get_file_metadata(file_id, user_id)
            if not file_metadata:
                logger.warning(f"Could not get latest metadata for file {file_id}")
                return False
            
            # Update document
            update_data = {
                'last_synced_at': datetime.now().isoformat(),
                'status': 'updated',
                'title': file_metadata.name,
                'file_size': str(file_metadata.size or 0),
                'drive_metadata': {
                    'id': file_metadata.id,
                    'name': file_metadata.name,
                    'mimeType': file_metadata.mime_type,
                    'size': file_metadata.size,
                    'modifiedTime': file_metadata.modified_time,
                    'parents': file_metadata.parents,
                    'webViewLink': file_metadata.web_view_link,
                    'lastChecked': datetime.now().isoformat()
                },
                'last_modified_at': file_metadata.modified_time
            }
            
            result = await self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
            
            if result.data:
                logger.info(f"Document metadata updated successfully for {document_id}")
                return True
            else:
                logger.error(f"Failed to update document metadata for {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating document metadata for {document_id}: {e}")
            return False
    
    async def _trigger_revectorization_workflow(self, document_id: str, file_id: str, user_id: str) -> bool:
        """Trigger re-vectorization workflow for updated file."""
        try:
            # TODO: This will be implemented when the re-vectorization workflow is built
            # For now, we'll log the event and prepare the payload
            
            # Get document details
            document = await self._get_document_by_id(document_id)
            if not document:
                logger.warning(f"Could not get document {document_id} for re-vectorization")
                return False
            
            # Prepare re-vectorization payload
            revectorization_payload = {
                'document_id': document_id,
                'file_id': file_id,
                'user_id': user_id,
                'project_id': document.get('project_id'),
                'file_name': document.get('title'),
                'file_type': document.get('mimetype'),
                'trigger_type': 'drive_file_update',
                'triggered_at': datetime.now().isoformat(),
                'file_url': document.get('drive_url'),
                'metadata': document.get('drive_metadata', {})
            }
            
            # Log the re-vectorization trigger
            await self._log_revectorization_trigger(document_id, file_id, revectorization_payload)
            
            # TODO: Send to re-vectorization service/workflow
            # await self._send_to_revectorization_service(revectorization_payload)
            
            logger.info(f"Re-vectorization workflow triggered for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error triggering re-vectorization workflow: {e}")
            return False
    
    async def _get_document_by_file_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get document by file ID."""
        try:
            result = await self.supabase.table('documents').select('*').eq('file_id', file_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error getting document by file ID {file_id}: {e}")
            return None
    
    async def _get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        try:
            result = await self.supabase.table('documents').select('*').eq('id', document_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    async def _log_processing_success(self, document_id: str, file_id: str, user_id: str, watch_id: str):
        """Log successful processing."""
        try:
            log_data = {
                'document_id': document_id,
                'file_id': file_id,
                'user_id': user_id,
                'watch_id': watch_id,
                'event_type': 'drive_file_processed',
                'status': 'success',
                'processed_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('drive_webhook_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging processing success: {e}")
    
    async def _log_processing_error(self, document_id: str, file_id: str, user_id: str, error_message: str):
        """Log processing error."""
        try:
            log_data = {
                'document_id': document_id,
                'file_id': file_id,
                'user_id': user_id,
                'event_type': 'drive_file_processing_error',
                'status': 'error',
                'error_message': error_message,
                'processed_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('drive_webhook_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging processing error: {e}")
    
    async def _log_update_success(self, document_id: str, file_id: str, user_id: str):
        """Log successful update."""
        try:
            log_data = {
                'document_id': document_id,
                'file_id': file_id,
                'user_id': user_id,
                'event_type': 'drive_file_updated',
                'status': 'success',
                'processed_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('drive_webhook_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging update success: {e}")
    
    async def _log_update_error(self, file_id: str, user_id: str, error_message: str):
        """Log update error."""
        try:
            log_data = {
                'file_id': file_id,
                'user_id': user_id,
                'event_type': 'drive_file_update_error',
                'status': 'error',
                'error_message': error_message,
                'processed_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('drive_webhook_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging update error: {e}")
    
    async def _log_revectorization_trigger(self, document_id: str, file_id: str, payload: Dict[str, Any]):
        """Log re-vectorization trigger."""
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
            logger.error(f"Error logging re-vectorization trigger: {e}")
