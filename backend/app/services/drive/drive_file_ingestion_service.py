"""
Google Drive File Content Ingestion Service
Handles ingesting and updating Drive file content when files change.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

from ...core.supabase_config import get_supabase_service_client
from ...services.email.gmail_service import GmailService

logger = logging.getLogger(__name__)

class DriveFileIngestionService:
    """Service for ingesting and updating Google Drive file content."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
        self.gmail_service = GmailService()
        
    async def ingest_drive_file(self, file_id: str, username: str) -> Dict[str, Any]:
        """
        Ingest a Google Drive file and store its content.
        
        Args:
            file_id: Google Drive file ID
            username: Username associated with the file
            
        Returns:
            Dict with ingestion results
        """
        try:
            logger.info(f"Starting Drive file ingestion for {file_id}")
            
            # Get file metadata from Drive
            file_metadata = await self._get_file_metadata(file_id)
            if not file_metadata:
                return {"status": "error", "message": "Failed to get file metadata"}
            
            # Get file content based on type
            file_content = await self._get_file_content(file_id, file_metadata)
            if not file_content:
                return {"status": "error", "message": "Failed to get file content"}
            
            # Update document with new content
            document_id = await self._update_document_content(file_id, file_metadata, file_content)
            
            if document_id:
                logger.info(f"Successfully ingested Drive file {file_id}")
                return {
                    "status": "success",
                    "message": "File ingested successfully",
                    "document_id": document_id,
                    "file_name": file_metadata.get('name'),
                    "file_size": file_metadata.get('size'),
                    "last_modified": file_metadata.get('modifiedTime')
                }
            else:
                return {"status": "error", "message": "Failed to update document"}
                
        except Exception as e:
            logger.error(f"Error ingesting Drive file {file_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Google Drive."""
        try:
            drive_service = self.gmail_service._build_drive_service()
            if not drive_service:
                return None
            
            file = drive_service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,modifiedTime,createdTime,webViewLink,webContentLink'
            ).execute()
            
            return file
            
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_id}: {e}")
            return None
    
    async def _get_file_content(self, file_id: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get file content based on file type."""
        try:
            mime_type = metadata.get('mimeType', '')
            
            if 'google-apps' in mime_type:
                # Google Docs, Sheets, Slides
                return await self._get_google_apps_content(file_id, mime_type)
            elif 'text/' in mime_type or mime_type in ['application/json', 'application/xml']:
                # Text files
                return await self._get_text_file_content(file_id)
            elif 'image/' in mime_type:
                # Image files
                return await self._get_image_file_content(file_id, metadata)
            else:
                # Other file types
                return await self._get_generic_file_content(file_id, metadata)
                
        except Exception as e:
            logger.error(f"Error getting file content for {file_id}: {e}")
            return None
    
    async def _get_google_apps_content(self, file_id: str, mime_type: str) -> Dict[str, Any]:
        """Get content from Google Apps (Docs, Sheets, Slides)."""
        try:
            drive_service = self.gmail_service._build_drive_service()
            if not drive_service:
                return {"content": "Failed to build Drive service", "type": "error"}
            
            if 'document' in mime_type:
                # Google Docs
                content = drive_service.files().export(
                    fileId=file_id,
                    mimeType='text/plain'
                ).execute()
                return {"content": content.decode('utf-8'), "type": "google_doc"}
                
            elif 'spreadsheet' in mime_type:
                # Google Sheets
                content = drive_service.files().export(
                    fileId=file_id,
                    mimeType='text/csv'
                ).execute()
                return {"content": content.decode('utf-8'), "type": "google_sheet"}
                
            elif 'presentation' in mime_type:
                # Google Slides
                content = drive_service.files().export(
                    fileId=file_id,
                    mimeType='text/plain'
                ).execute()
                return {"content": content.decode('utf-8'), "type": "google_slide"}
                
            else:
                return {"content": "Unsupported Google Apps type", "type": "unsupported"}
                
        except Exception as e:
            logger.error(f"Error getting Google Apps content for {file_id}: {e}")
            return {"content": f"Error: {str(e)}", "type": "error"}
    
    async def _get_text_file_content(self, file_id: str) -> Dict[str, Any]:
        """Get content from text files."""
        try:
            drive_service = self.gmail_service._build_drive_service()
            if not drive_service:
                return {"content": "Failed to build Drive service", "type": "error"}
            
            content = drive_service.files().get_media(fileId=file_id).execute()
            return {"content": content.decode('utf-8'), "type": "text"}
            
        except Exception as e:
            logger.error(f"Error getting text file content for {file_id}: {e}")
            return {"content": f"Error: {str(e)}", "type": "error"}
    
    async def _get_image_file_content(self, file_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get content from image files."""
        try:
            # For images, we store metadata and links rather than content
            return {
                "content": f"Image file: {metadata.get('name', 'Unknown')}",
                "type": "image",
                "image_metadata": {
                    "name": metadata.get('name'),
                    "size": metadata.get('size'),
                    "mime_type": metadata.get('mimeType'),
                    "web_view_link": metadata.get('webViewLink'),
                    "web_content_link": metadata.get('webContentLink')
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting image file content for {file_id}: {e}")
            return {"content": f"Error: {str(e)}", "type": "error"}
    
    async def _get_generic_file_content(self, file_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get content from generic files."""
        try:
            # For generic files, store metadata and links
            return {
                "content": f"File: {metadata.get('name', 'Unknown')}",
                "type": "generic",
                "file_metadata": {
                    "name": metadata.get('name'),
                    "size": metadata.get('size'),
                    "mime_type": metadata.get('mimeType'),
                    "web_view_link": metadata.get('webViewLink'),
                    "web_content_link": metadata.get('webContentLink')
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting generic file content for {file_id}: {e}")
            return {"content": f"Error: {str(e)}", "type": "error"}
    
    async def _update_document_content(self, file_id: str, metadata: Dict[str, Any], content: Dict[str, Any]) -> Optional[str]:
        """Update document with new Drive file content."""
        try:
            # Find the existing document
            result = self.supabase.table('documents').select('id').eq('source_id', file_id).execute()
            
            if not result.data:
                logger.warning(f"No document found for file {file_id}")
                return None
            
            document_id = result.data[0]['id']
            
            # Update the document with new content
            update_data = {
                'summary': content.get('content', 'No content available'),
                'file_size': str(metadata.get('size', 'unknown')),
                'last_synced_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Update transcript metadata with new content info
            current_metadata = await self._get_current_metadata(document_id)
            if current_metadata:
                current_metadata['drive_file_info']['last_ingested'] = datetime.now().isoformat()
                current_metadata['drive_file_info']['content_type'] = content.get('type')
                current_metadata['drive_file_info']['file_size'] = str(metadata.get('size', 'unknown'))
                current_metadata['drive_file_info']['last_modified'] = metadata.get('modifiedTime')
                
                # Add content-specific metadata
                if content.get('type') == 'image':
                    current_metadata['drive_file_info']['image_metadata'] = content.get('image_metadata')
                elif content.get('type') == 'generic':
                    current_metadata['drive_file_info']['file_metadata'] = content.get('file_metadata')
                
                update_data['transcript_metadata'] = current_metadata
            
            # Update the document
            self.supabase.table('documents').update(update_data).eq('id', document_id).execute()
            
            logger.info(f"Updated document {document_id} with new Drive file content")
            return document_id
            
        except Exception as e:
            logger.error(f"Error updating document content for {file_id}: {e}")
            return None
    
    async def _get_current_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get current transcript metadata for a document."""
        try:
            result = self.supabase.table('documents').select('transcript_metadata').eq('id', document_id).execute()
            
            if result.data and result.data[0].get('transcript_metadata'):
                return result.data[0]['transcript_metadata']
            return None
            
        except Exception as e:
            logger.error(f"Error getting current metadata for document {document_id}: {e}")
            return None
    
    async def process_drive_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Drive webhook notification and re-ingest file content."""
        try:
            logger.info("Processing Drive webhook notification")
            
            # Extract file information from webhook
            file_id = webhook_data.get('fileId')
            if not file_id:
                return {"status": "error", "message": "No file ID in webhook"}
            
            # Get username from the document
            username = await self._get_username_from_file(file_id)
            if not username:
                return {"status": "error", "message": "No username found for file"}
            
            # Re-ingest the file content
            result = await self.ingest_drive_file(file_id, username)
            
            if result.get("status") == "success":
                logger.info(f"Successfully processed Drive webhook for file {file_id}")
                
                # Update email processing log
                await self._update_processing_log_drive_update(file_id, result)
                
                return result
            else:
                logger.error(f"Failed to process Drive webhook for file {file_id}")
                return result
                
        except Exception as e:
            logger.error(f"Error processing Drive webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _get_username_from_file(self, file_id: str) -> Optional[str]:
        """Get username associated with a file from the database."""
        try:
            # Check virtual email detections table
            result = self.supabase.table('virtual_email_detections').select('username').eq('gmail_message_id', file_id).execute()
            
            if result.data:
                return result.data[0].get('username')
            
            # Check documents table
            doc_result = self.supabase.table('documents').select('transcript_metadata').eq('source_id', file_id).execute()
            
            if doc_result.data and doc_result.data[0].get('transcript_metadata'):
                metadata = doc_result.data[0]['transcript_metadata']
                if metadata.get('drive_file_info', {}).get('username'):
                    return metadata['drive_file_info']['username']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting username for file {file_id}: {e}")
            return None
    
    async def _update_processing_log_drive_update(self, file_id: str, result: Dict[str, Any]):
        """Update email processing log with Drive update information."""
        try:
            # Find the processing log entry for this file
            log_result = self.supabase.table('email_processing_logs').select('*').eq('gmail_message_id', file_id).execute()
            
            if log_result.data:
                log_entry = log_result.data[0]
                
                # Update the log entry
                self.supabase.table('email_processing_logs').update({
                    'n8n_webhook_response': f"Drive file updated: {result.get('message', 'Unknown')}",
                    'updated_at': datetime.now().isoformat()
                }).eq('id', log_entry['id']).execute()
                
                logger.info(f"Updated processing log {log_entry['id']} with Drive update info")
                
        except Exception as e:
            logger.error(f"Error updating processing log: {e}")
