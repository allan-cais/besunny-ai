"""
Drive polling service for BeSunny.ai Python backend.
Handles Google Drive file monitoring, change detection, and n8n integration.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel
import httpx

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.drive import DriveFile, DriveFileWatch

logger = logging.getLogger(__name__)


class DrivePollingResult(BaseModel):
    """Result of a drive polling operation."""
    file_id: str
    document_id: str
    changes_detected: int
    file_updated: bool
    file_deleted: bool
    processing_time_ms: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime


class FileChangeInfo(BaseModel):
    """Information about a file change."""
    file_id: str
    change_type: str  # 'modified', 'deleted', 'created'
    timestamp: datetime
    file_metadata: Optional[Dict[str, Any]] = None
    change_id: Optional[str] = None


class DrivePollingService:
    """Service for polling and monitoring Google Drive files."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.n8n_classification_webhook = self.settings.n8n_classification_webhook_url
        self.n8n_drivesync_webhook = self.settings.n8n_drivesync_webhook_url
        
        # HTTP client for n8n webhooks
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("Drive Polling Service initialized")
    
    async def poll_drive_for_file(self, file_id: str, document_id: str) -> Dict[str, Any]:
        """
        Poll a specific Drive file for changes.
        
        Args:
            file_id: Google Drive file ID
            document_id: Document ID in our system
            
        Returns:
            Polling results and change information
        """
        start_time = datetime.now()
        
        try:
            # Get file watch information
            file_watch = await self._get_file_watch(file_id, document_id)
            if not file_watch:
                return {
                    'success': False,
                    'error': 'No file watch found',
                    'file_id': file_id,
                    'document_id': document_id
                }
            
            # Get user credentials
            user_id = file_watch['user_id']
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'No Google credentials found',
                    'file_id': file_id,
                    'document_id': document_id
                }
            
            # Create Drive API service
            service = build('drive', 'v3', credentials=credentials)
            
            # Check for file changes
            changes = await self._check_file_changes(file_id, service, file_watch)
            
            # Process changes
            file_updated = False
            file_deleted = False
            changes_detected = len(changes)
            
            for change in changes:
                try:
                    if change.change_type == 'deleted':
                        await self._handle_file_deletion(document_id, file_watch['project_id'], file_id)
                        file_deleted = True
                    elif change.change_type == 'modified':
                        await self._handle_file_modification(document_id, file_watch['project_id'], file_id, change)
                        file_updated = True
                        
                except Exception as e:
                    logger.error(f"Failed to process file change: {e}")
                    continue
            
            # Update last poll time
            await self._update_last_poll_time(file_id, document_id)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            # Create polling result
            result = DrivePollingResult(
                file_id=file_id,
                document_id=document_id,
                changes_detected=changes_detected,
                file_updated=file_updated,
                file_deleted=file_deleted,
                processing_time_ms=processing_time,
                success=True,
                timestamp=datetime.now()
            )
            
            # Store result
            await self._store_polling_result(result)
            
            logger.info(f"Drive polling completed for file {file_id}: {changes_detected} changes detected")
            
            return {
                'success': True,
                'file_id': file_id,
                'document_id': document_id,
                'changes_detected': changes_detected,
                'file_updated': file_updated,
                'file_deleted': file_deleted,
                'processing_time_ms': processing_time
            }
            
        except HttpError as e:
            error_message = f"Google Drive API error: {e}"
            logger.error(error_message)
            
            result = DrivePollingResult(
                file_id=file_id,
                document_id=document_id,
                changes_detected=0,
                file_updated=False,
                file_deleted=False,
                processing_time_ms=(datetime.now() - start_time).microseconds // 1000,
                success=False,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            await self._store_polling_result(result)
            
            return {
                'success': False,
                'error': error_message,
                'file_id': file_id,
                'document_id': document_id
            }
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(f"Drive polling failed for file {file_id}: {error_message}")
            
            result = DrivePollingResult(
                file_id=file_id,
                document_id=document_id,
                changes_detected=0,
                file_updated=False,
                file_deleted=False,
                processing_time_ms=(datetime.now() - start_time).microseconds // 1000,
                success=False,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            await self._store_polling_result(result)
            
            return {
                'success': False,
                'error': error_message,
                'file_id': file_id,
                'document_id': document_id
            }
    
    async def check_file_changes(self, file_id: str, access_token: str) -> Dict[str, Any]:
        """
        Check for changes in a specific Drive file.
        
        Args:
            file_id: Google Drive file ID
            access_token: Google access token
            
        Returns:
            Change information
        """
        try:
            # Create Drive API service with access token
            credentials = Credentials(access_token)
            service = build('drive', 'v3', credentials=credentials)
            
            # Get file metadata
            file_metadata = service.files().get(fileId=file_id).execute()
            
            # Get file revisions
            revisions = service.revisions().list(fileId=file_id).execute()
            
            # Check if file has been modified
            last_modified = file_metadata.get('modifiedTime')
            last_revision = revisions.get('revisions', [{}])[-1] if revisions.get('revisions') else {}
            
            changes = []
            if last_revision:
                revision_time = last_revision.get('modifiedTime')
                if revision_time != last_modified:
                    changes.append(FileChangeInfo(
                        file_id=file_id,
                        change_type='modified',
                        timestamp=datetime.now(),
                        file_metadata=file_metadata,
                        change_id=last_revision.get('id')
                    ))
            
            return {
                'file_id': file_id,
                'has_changes': len(changes) > 0,
                'changes': [change.dict() for change in changes],
                'last_modified': last_modified,
                'last_revision': last_revision.get('id') if last_revision else None
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error checking file {file_id}: {e}")
            return {
                'file_id': file_id,
                'has_changes': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Failed to check file changes for {file_id}: {e}")
            return {
                'file_id': file_id,
                'has_changes': False,
                'error': str(e)
            }
    
    async def handle_file_deletion(self, document_id: str, project_id: str, file_id: str) -> None:
        """
        Handle deletion of a Drive file.
        
        Args:
            document_id: Document ID in our system
            project_id: Project ID
            file_id: Google Drive file ID
        """
        try:
            # Mark document as deleted
            await self._mark_document_deleted(document_id)
            
            # Remove file watch
            await self._remove_file_watch(file_id, document_id)
            
            # Send to n8n webhook
            await self._send_to_n8n_webhook(document_id, project_id, file_id, 'deleted')
            
            logger.info(f"Handled deletion of Drive file {file_id} for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle file deletion for {file_id}: {e}")
    
    async def send_to_n8n_webhook(self, document_id: str, project_id: str, 
                                 file_id: str, action: str) -> bool:
        """
        Send file change notification to n8n webhook.
        
        Args:
            document_id: Document ID
            project_id: Project ID
            file_id: Google Drive file ID
            action: Action type (modified, deleted, created)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            webhook_data = {
                'document_id': document_id,
                'project_id': project_id,
                'file_id': file_id,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'source': 'drive_polling_service'
            }
            
            # Choose appropriate webhook based on action
            if action == 'deleted':
                webhook_url = self.n8n_drivesync_webhook
            else:
                webhook_url = self.n8n_classification_webhook
            
            # Send webhook
            response = await self.http_client.post(webhook_url, json=webhook_data)
            response.raise_for_status()
            
            logger.info(f"Successfully sent {action} notification to n8n for file {file_id}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending n8n webhook: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to send n8n webhook for file {file_id}: {e}")
            return False
    
    async def smart_drive_polling(self, file_id: str, document_id: str) -> Dict[str, Any]:
        """
        Smart Drive polling that optimizes based on file activity patterns.
        
        Args:
            file_id: Google Drive file ID
            document_id: Document ID
            
        Returns:
            Smart polling results
        """
        try:
            # Get file activity metrics
            metrics = await self._get_file_activity_metrics(file_id, document_id)
            
            # Determine if we should poll based on metrics
            should_poll = await self._should_poll_drive_file(file_id, document_id, metrics)
            
            if not should_poll:
                return {
                    'skipped': True,
                    'reason': 'Smart polling optimization',
                    'next_poll_in_minutes': metrics.get('next_poll_interval', 30),
                    'file_id': file_id,
                    'document_id': document_id
                }
            
            # Execute polling
            result = await self.poll_drive_for_file(file_id, document_id)
            
            # Update activity metrics
            await self._update_file_activity_metrics(file_id, document_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Smart Drive polling failed for file {file_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_id': file_id,
                'document_id': document_id
            }
    
    # Private helper methods
    
    async def _get_file_watch(self, file_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get file watch information."""
        try:
            result = self.supabase.table("drive_file_watches") \
                .select("*") \
                .eq("file_id", file_id) \
                .eq("document_id", document_id) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get file watch for {file_id}: {e}")
            return None
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("access_token, refresh_token, token_uri, client_id, client_secret, scopes") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                cred_data = result.data
                return Credentials(
                    token=cred_data['access_token'],
                    refresh_token=cred_data['refresh_token'],
                    token_uri=cred_data['token_uri'],
                    client_id=cred_data['client_id'],
                    client_secret=cred_data['client_secret'],
                    scopes=cred_data['scopes']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    async def _check_file_changes(self, file_id: str, service, 
                                file_watch: Dict[str, Any]) -> List[FileChangeInfo]:
        """Check for changes in a Drive file."""
        try:
            changes = []
            
            # Get file metadata
            try:
                file_metadata = service.files().get(fileId=file_id).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    # File was deleted
                    changes.append(FileChangeInfo(
                        file_id=file_id,
                        change_type='deleted',
                        timestamp=datetime.now()
                    ))
                    return changes
                else:
                    raise e
            
            # Check if file has been modified since last poll
            last_poll = file_watch.get('last_poll_at')
            if last_poll:
                last_poll_time = datetime.fromisoformat(last_poll.replace('Z', '+00:00'))
                file_modified = datetime.fromisoformat(file_metadata['modifiedTime'].replace('Z', '+00:00'))
                
                if file_modified > last_poll_time:
                    changes.append(FileChangeInfo(
                        file_id=file_id,
                        change_type='modified',
                        timestamp=file_modified,
                        file_metadata=file_metadata
                    ))
            
            # Check for new revisions
            try:
                revisions = service.revisions().list(fileId=file_id).execute()
                last_revision = file_watch.get('last_revision_id')
                
                if revisions.get('revisions'):
                    current_revision = revisions['revisions'][-1]['id']
                    if current_revision != last_revision:
                        changes.append(FileChangeInfo(
                            file_id=file_id,
                            change_type='modified',
                            timestamp=datetime.now(),
                            file_metadata=file_metadata,
                            change_id=current_revision
                        ))
                        
            except HttpError:
                # Revisions not available for this file type
                pass
            
            return changes
            
        except Exception as e:
            logger.error(f"Failed to check file changes for {file_id}: {e}")
            return []
    
    async def _handle_file_modification(self, document_id: str, project_id: str, 
                                      file_id: str, change: FileChangeInfo):
        """Handle modification of a Drive file."""
        try:
            # Update document metadata
            await self._update_document_metadata(document_id, change.file_metadata)
            
            # Update file watch with new revision
            if change.change_id:
                await self._update_file_watch_revision(file_id, document_id, change.change_id)
            
            # Send to n8n webhook
            await self._send_to_n8n_webhook(document_id, project_id, file_id, 'modified')
            
            logger.info(f"Handled modification of Drive file {file_id} for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle file modification for {file_id}: {e}")
    
    async def _mark_document_deleted(self, document_id: str):
        """Mark a document as deleted."""
        try:
            self.supabase.table("documents") \
                .update({'status': 'deleted', 'updated_at': datetime.now().isoformat()}) \
                .eq("id", document_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to mark document as deleted: {e}")
    
    async def _remove_file_watch(self, file_id: str, document_id: str):
        """Remove file watch for a deleted file."""
        try:
            self.supabase.table("drive_file_watches") \
                .delete() \
                .eq("file_id", file_id) \
                .eq("document_id", document_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to remove file watch: {e}")
    
    async def _update_last_poll_time(self, file_id: str, document_id: str):
        """Update last poll time for a file watch."""
        try:
            self.supabase.table("drive_file_watches") \
                .update({'last_poll_at': datetime.now().isoformat()}) \
                .eq("file_id", file_id) \
                .eq("document_id", document_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update last poll time: {e}")
    
    async def _store_polling_result(self, result: DrivePollingResult):
        """Store drive polling result in database."""
        try:
            result_data = result.dict()
            result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            self.supabase.table("drive_polling_results").insert(result_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store drive polling result: {e}")
    
    async def _update_document_metadata(self, document_id: str, file_metadata: Dict[str, Any]):
        """Update document metadata from Drive file."""
        try:
            update_data = {
                'file_size': file_metadata.get('size'),
                'mime_type': file_metadata.get('mimeType'),
                'last_modified': file_metadata.get('modifiedTime'),
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("documents") \
                .update(update_data) \
                .eq("id", document_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
    
    async def _update_file_watch_revision(self, file_id: str, document_id: str, revision_id: str):
        """Update file watch with new revision ID."""
        try:
            self.supabase.table("drive_file_watches") \
                .update({'last_revision_id': revision_id}) \
                .eq("file_id", file_id) \
                .eq("document_id", document_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update file watch revision: {e}")
    
    async def _get_file_activity_metrics(self, file_id: str, document_id: str) -> Dict[str, Any]:
        """Get file activity metrics for smart polling."""
        try:
            result = self.supabase.table("file_activity_metrics") \
                .select("*") \
                .eq("file_id", file_id) \
                .eq("document_id", document_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            
            # Return default metrics
            return {
                'change_frequency': 'medium',
                'next_poll_interval': 30,
                'last_change_at': None,
                'changes_last_24h': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get file activity metrics: {e}")
            return {
                'change_frequency': 'medium',
                'next_poll_interval': 30,
                'last_change_at': None,
                'changes_last_24h': 0
            }
    
    async def _should_poll_drive_file(self, file_id: str, document_id: str, 
                                    metrics: Dict[str, Any]) -> bool:
        """Determine if Drive file should be polled based on smart metrics."""
        try:
            # Check if enough time has passed since last poll
            last_poll = await self._get_last_poll_time(file_id, document_id)
            if last_poll:
                time_since_last_poll = datetime.now() - last_poll
                next_poll_interval = timedelta(minutes=metrics.get('next_poll_interval', 30))
                
                if time_since_last_poll < next_poll_interval:
                    return False
            
            # Check if file has recent changes
            last_change = metrics.get('last_change_at')
            if last_change:
                last_change_time = datetime.fromisoformat(last_change.replace('Z', '+00:00'))
                time_since_last_change = datetime.now() - last_change_time
                
                # If file changed recently, poll more frequently
                if time_since_last_change < timedelta(hours=1):
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to determine if Drive file should be polled: {e}")
            return True
    
    async def _update_file_activity_metrics(self, file_id: str, document_id: str, 
                                          result: Dict[str, Any]):
        """Update file activity metrics based on polling results."""
        try:
            # Calculate change frequency based on results
            changes_detected = result.get('changes_detected', 0)
            
            if changes_detected == 0:
                change_frequency = 'low'
                next_poll_interval = 60  # 1 hour
            elif changes_detected <= 2:
                change_frequency = 'medium'
                next_poll_interval = 30  # 30 minutes
            else:
                change_frequency = 'high'
                next_poll_interval = 15  # 15 minutes
            
            # Update metrics
            metrics_data = {
                'file_id': file_id,
                'document_id': document_id,
                'change_frequency': change_frequency,
                'next_poll_interval': next_poll_interval,
                'last_change_at': datetime.now().isoformat() if changes_detected > 0 else None,
                'changes_last_24h': changes_detected,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("file_activity_metrics").upsert(metrics_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to update file activity metrics: {e}")
    
    async def _get_last_poll_time(self, file_id: str, document_id: str) -> Optional[datetime]:
        """Get last poll time for a file watch."""
        try:
            result = self.supabase.table("drive_file_watches") \
                .select("last_poll_at") \
                .eq("file_id", file_id) \
                .eq("document_id", document_id) \
                .single() \
                .execute()
            
            if result.data and result.data.get('last_poll_at'):
                return datetime.fromisoformat(result.data['last_poll_at'].replace('Z', '+00:00'))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last poll time: {e}")
            return None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()
