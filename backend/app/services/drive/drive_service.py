"""
Google Drive service for BeSunny.ai Python backend.
Handles file monitoring, webhook setup, and Drive API operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.drive import (
    DriveFile,
    DriveFileWatch,
    DriveWebhookPayload,
    DriveFileChange
)

logger = logging.getLogger(__name__)


class DriveService:
    """Main service for Google Drive operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
    
    async def setup_file_watch(self, file_id: str, project_id: Optional[str], user_id: str) -> Optional[str]:
        """Set up a file watch for a specific Drive file."""
        try:
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No Google credentials found for user {user_id}")
                return None
            
            # Create Drive API service
            service = build('drive', 'v3', credentials=credentials)
            
            # Create file watch
            watch_request = {
                'id': f"watch_{file_id}_{int(datetime.now().timestamp())}",
                'type': 'web_hook',
                'address': f"{self.settings.webhook_base_url}/api/v1/drive/webhook",
                'expiration': (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
            }
            
            # Create the watch
            watch = service.files().watch(fileId=file_id, body=watch_request).execute()
            
            # Store watch information in database
            await self._store_file_watch(
                file_id=file_id,
                channel_id=watch['id'],
                resource_id=watch['resourceId'],
                expiration=watch['expiration'],
                project_id=project_id,
                user_id=user_id
            )
            
            logger.info(f"File watch created for file {file_id}")
            return watch['id']
            
        except HttpError as e:
            logger.error(f"Failed to create file watch for {file_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error setting up file watch: {e}")
            return None
    
    async def setup_file_watch_for_email_alias(self, file_id: str, user_id: str, document_id: str) -> Optional[str]:
        """Set up a file watch specifically for email alias workflow."""
        try:
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No Google credentials found for user {user_id}")
                return None
            
            # Create Drive API service
            service = build('drive', 'v3', credentials=credentials)
            
            # Create file watch
            watch_request = {
                'id': f"email_alias_watch_{file_id}_{int(datetime.now().timestamp())}",
                'type': 'web_hook',
                'address': f"{self.settings.webhook_base_url}/api/v1/drive/webhook",
                'expiration': (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
            }
            
            # Create the watch
            watch = service.files().watch(fileId=file_id, body=watch_request).execute()
            
            # Store watch information in database with email alias context
            await self._store_email_alias_file_watch(
                file_id=file_id,
                channel_id=watch['id'],
                resource_id=watch['resourceId'],
                expiration=watch['expiration'],
                user_id=user_id,
                document_id=document_id
            )
            
            logger.info(f"Email alias file watch created for file {file_id}")
            return watch['id']
            
        except HttpError as e:
            logger.error(f"Failed to create email alias file watch for {file_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error setting up email alias file watch: {e}")
            return None
    
    async def process_file_changes(self, user_id: str) -> List[DriveFileChange]:
        """Process file changes for a user by polling Drive API."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return []
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Get changes since last sync
            last_sync = await self._get_last_sync_time(user_id, 'drive')
            
            # Get changes
            changes = service.changes().list(
                pageToken=last_sync,
                spaces='drive'
            ).execute()
            
            file_changes = []
            for change in changes.get('changes', []):
                if 'file' in change:
                    file_change = DriveFileChange(
                        file_id=change['fileId'],
                        change_type='update' if change.get('removed') else 'modify',
                        timestamp=datetime.now(),
                        file_metadata=change.get('file', {})
                    )
                    file_changes.append(file_change)
            
            # Update sync token
            if 'newStartPageToken' in changes:
                await self._update_sync_token(user_id, 'drive', changes['newStartPageToken'])
            
            return file_changes
            
        except Exception as e:
            logger.error(f"Failed to process file changes for user {user_id}: {e}")
            return []
    
    async def get_file_metadata(self, file_id: str, user_id: str) -> Optional[DriveFile]:
        """Get metadata for a specific Drive file."""
        try:
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return None
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Get file metadata
            file = service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,modifiedTime,parents,webViewLink'
            ).execute()
            
            return DriveFile(
                id=file['id'],
                name=file['name'],
                mime_type=file['mimeType'],
                size=file.get('size'),
                modified_time=file['modifiedTime'],
                parents=file.get('parents', []),
                web_view_link=file.get('webViewLink')
            )
            
        except HttpError as e:
            logger.error(f"Failed to get file metadata for {file_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file metadata: {e}")
            return None
    
    async def list_project_files(self, project_id: str, user_id: str) -> List[DriveFile]:
        """List all Drive files associated with a project."""
        try:
            # Get files from database that are linked to this project
            result = await self.supabase.table('documents').select('*').eq('project_id', project_id).eq('type', 'document').execute()
            
            files = []
            for doc in result.data:
                if doc.get('file_id'):
                    file_metadata = await self.get_file_metadata(doc['file_id'], user_id)
                    if file_metadata:
                        files.append(file_metadata)
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list project files for project {project_id}: {e}")
            return []
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            result = await self.supabase.table('google_credentials').select('*').eq('user_id', user_id).single().execute()
            
            if result.data:
                cred_data = result.data
                return Credentials(
                    token=cred_data['access_token'],
                    refresh_token=cred_data['refresh_token'],
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=self.settings.google_client_id,
                    client_secret=self.settings.google_client_secret,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    async def _store_file_watch(self, file_id: str, channel_id: str, resource_id: str, 
                               expiration: str, project_id: str, user_id: str):
        """Store file watch information in database."""
        try:
            watch_data = {
                'file_id': file_id,
                'channel_id': channel_id,
                'resource_id': resource_id,
                'expiration': expiration,
                'project_id': project_id,
                'is_active': True
            }
            
            await self.supabase.table('drive_file_watches').insert(watch_data).execute()
            logger.info(f"File watch stored for file {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to store file watch: {e}")
    
    async def _store_email_alias_file_watch(self, file_id: str, channel_id: str, resource_id: str, 
                                          expiration: str, user_id: str, document_id: str):
        """Store email alias file watch information in database."""
        try:
            watch_data = {
                'file_id': file_id,
                'channel_id': channel_id,
                'resource_id': resource_id,
                'expiration': expiration,
                'project_id': None,  # Will be assigned by classification agent
                'user_id': user_id,
                'document_id': document_id,
                'watch_type': 'email_alias',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('drive_file_watches').insert(watch_data).execute()
            logger.info(f"Email alias file watch stored for file {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to store email alias file watch: {e}")
    
    async def _get_last_sync_time(self, user_id: str, service_type: str) -> Optional[str]:
        """Get last sync time for a service."""
        try:
            result = await self.supabase.table('user_sync_states').select('last_sync_at').eq('user_id', user_id).eq('service_type', service_type).single().execute()
            
            if result.data:
                return result.data['last_sync_at']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last sync time: {e}")
            return None
    
    async def _update_sync_token(self, user_id: str, service_type: str, sync_token: str):
        """Update sync token for a service."""
        try:
            await self.supabase.table('user_sync_states').upsert({
                'user_id': user_id,
                'service_type': service_type,
                'last_sync_at': datetime.now().isoformat(),
                'is_active': True
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to update sync token: {e}")
    
    async def cleanup_expired_watches(self):
        """Clean up expired file watches."""
        try:
            # Get expired watches
            result = await self.supabase.table('drive_file_watches').select('*').lt('expiration', datetime.now().isoformat()).eq('is_active', True).execute()
            
            for watch in result.data:
                try:
                    # Mark as inactive
                    await self.supabase.table('drive_file_watches').update({'is_active': False}).eq('id', watch['id']).execute()
                    logger.info(f"Marked expired watch {watch['id']} as inactive")
                except Exception as e:
                    logger.error(f"Failed to update expired watch {watch['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired watches: {e}")

    async def get_file_content_for_classification(self, file_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get file content and metadata for classification agent."""
        try:
            # Get file metadata
            file_metadata = await self.get_file_metadata(file_id, user_id)
            if not file_metadata:
                return None
            
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.error(f"No Google credentials found for user {user_id}")
                return None
            
            # Create Drive API service
            service = build('drive', 'v3', credentials=credentials)
            
            # Prepare classification payload
            classification_data = {
                'file_id': file_id,
                'file_name': file_metadata.name,
                'file_type': file_metadata.mime_type,
                'file_size': file_metadata.size,
                'modified_time': file_metadata.modified_time,
                'web_view_link': file_metadata.web_view_link,
                'parents': file_metadata.parents,
                'metadata': file_metadata.__dict__,
                'retrieved_at': datetime.now().isoformat()
            }
            
            # For text-based files, try to get content
            if file_metadata.mime_type.startswith('text/') or file_metadata.mime_type in [
                'application/json', 'application/xml', 'application/javascript'
            ]:
                try:
                    # Download file content
                    file_content = service.files().get_media(fileId=file_id).execute()
                    classification_data['file_content'] = file_content.decode('utf-8')
                    classification_data['content_type'] = 'text'
                except Exception as e:
                    logger.warning(f"Could not download text content for file {file_id}: {e}")
                    classification_data['content_type'] = 'metadata_only'
            
            # For Google Docs, try to export as text
            elif file_metadata.mime_type in [
                'application/vnd.google-apps.document',
                'application/vnd.google-apps.spreadsheet',
                'application/vnd.google-apps.presentation'
            ]:
                try:
                    # Export as plain text
                    export_mime = 'text/plain'
                    if file_metadata.mime_type == 'application/vnd.google-apps.spreadsheet':
                        export_mime = 'text/csv'
                    
                    file_content = service.files().export_media(
                        fileId=file_id, 
                        mimeType=export_mime
                    ).execute()
                    
                    classification_data['file_content'] = file_content.decode('utf-8')
                    classification_data['content_type'] = 'exported_text'
                except Exception as e:
                    logger.warning(f"Could not export content for Google Doc {file_id}: {e}")
                    classification_data['content_type'] = 'metadata_only'
            else:
                classification_data['content_type'] = 'metadata_only'
            
            return classification_data
            
        except Exception as e:
            logger.error(f"Failed to get file content for classification: {e}")
            return None
