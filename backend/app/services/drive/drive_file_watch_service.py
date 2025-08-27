"""
Google Drive File Watch Management Service
Handles setting up and managing file watches for real-time updates.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json

from ...core.supabase_config import get_supabase_service_client
from ...services.email.gmail_service import GmailService

logger = logging.getLogger(__name__)

class DriveFileWatchService:
    """Service for managing Google Drive file watches."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
        self.gmail_service = GmailService()
        self.master_email = "ai@besunny.ai"
        
    async def setup_file_watch(self, file_id: str, file_name: str, username: str) -> Optional[str]:
        """
        Set up a Google Drive file watch for real-time updates.
        
        Args:
            file_id: Google Drive file ID
            file_name: Name of the file
            username: Username associated with the file
            
        Returns:
            Watch ID if successful, None otherwise
        """
        try:
            logger.info(f"Setting up Drive file watch for {file_name} (ID: {file_id})")
            
            # Check if watch already exists
            existing_watch = await self._get_existing_watch(file_id)
            if existing_watch:
                logger.info(f"Watch already exists for file {file_id}")
                return existing_watch['id']
            
            # Set up the file watch using Gmail service credentials
            watch_response = await self._create_drive_watch(file_id)
            if not watch_response:
                logger.error(f"Failed to create Drive watch for file {file_id}")
                return None
            
            # Store watch information in database
            watch_id = await self._store_file_watch(file_id, file_name, username, watch_response)
            
            if watch_id:
                logger.info(f"Successfully set up Drive file watch: {watch_id}")
                
                # Update email processing log to indicate Drive watch is active
                await self._update_processing_log_drive_watch(file_id, watch_id)
                
                return watch_id
            else:
                logger.error(f"Failed to store file watch information for {file_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error setting up file watch for {file_id}: {e}")
            return None
    
    async def _get_existing_watch(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Check if a watch already exists for the file."""
        try:
            result = self.supabase.table('drive_file_watches').select('*').eq('file_id', file_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing watch for {file_id}: {e}")
            return None
    
    async def _create_drive_watch(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Create a Google Drive file watch."""
        try:
            # Use the Gmail service credentials to access Drive API
            drive_service = self.gmail_service._build_drive_service()
            
            if not drive_service:
                logger.error("Failed to build Drive service")
                return None
            
            # Set up the watch
            watch_request = {
                'id': f"drive-watch-{file_id}-{datetime.now().timestamp()}",
                'type': 'web_hook',
                'address': f"{self._get_webhook_url()}/api/v1/drive/webhook",
                'expiration': (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
            }
            
            watch = drive_service.files().watch(
                fileId=file_id,
                body=watch_request
            ).execute()
            
            logger.info(f"Drive watch created: {watch.get('id')}")
            return watch
            
        except Exception as e:
            logger.error(f"Error creating Drive watch: {e}")
            return None
    
    def _get_webhook_url(self) -> str:
        """Get the webhook base URL for Drive notifications."""
        # This should come from your environment configuration
        # For now, using a placeholder
        return "https://backend-staging-6085.up.railway.app"
    
    async def _store_file_watch(self, file_id: str, file_name: str, username: str, watch_response: Dict[str, Any]) -> Optional[str]:
        """Store file watch information in database."""
        try:
            watch_data = {
                'file_id': file_id,
                'file_name': file_name,
                'username': username,
                'watch_id': watch_response.get('id'),
                'webhook_url': watch_response.get('address'),
                'expiration': watch_response.get('expiration'),
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('drive_file_watches').insert(watch_data).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception("No watch ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing file watch: {e}")
            raise
    
    async def _update_processing_log_drive_watch(self, file_id: str, watch_id: str):
        """Update email processing log to indicate Drive watch is active."""
        try:
            # Find the processing log entry for this file
            result = self.supabase.table('email_processing_logs').select('*').eq('gmail_message_id', file_id).execute()
            
            if result.data:
                log_entry = result.data[0]
                
                # Update the log entry
                self.supabase.table('email_processing_logs').update({
                    'n8n_webhook_sent': True,
                    'n8n_webhook_response': f"Drive watch active: {watch_id}",
                    'updated_at': datetime.now().isoformat()
                }).eq('id', log_entry['id']).execute()
                
                logger.info(f"Updated processing log {log_entry['id']} with Drive watch info")
                
        except Exception as e:
            logger.error(f"Error updating processing log: {e}")
    
    async def renew_file_watch(self, watch_id: str) -> bool:
        """Renew an expiring file watch."""
        try:
            logger.info(f"Renewing Drive file watch: {watch_id}")
            
            # Get watch information
            watch_info = await self._get_watch_by_id(watch_id)
            if not watch_info:
                logger.error(f"Watch {watch_id} not found")
                return False
            
            # Create new watch
            new_watch = await self._create_drive_watch(watch_info['file_id'])
            if not new_watch:
                return False
            
            # Update watch information
            await self._update_watch(watch_id, new_watch)
            
            logger.info(f"Successfully renewed watch {watch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error renewing watch {watch_id}: {e}")
            return False
    
    async def _get_watch_by_id(self, watch_id: str) -> Optional[Dict[str, Any]]:
        """Get watch information by watch ID."""
        try:
            result = self.supabase.table('drive_file_watches').select('*').eq('watch_id', watch_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting watch {watch_id}: {e}")
            return None
    
    async def _update_watch(self, watch_id: str, new_watch: Dict[str, Any]):
        """Update watch information with new watch details."""
        try:
            self.supabase.table('drive_file_watches').update({
                'watch_id': new_watch.get('id'),
                'expiration': new_watch.get('expiration'),
                'updated_at': datetime.now().isoformat()
            }).eq('watch_id', watch_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating watch {watch_id}: {e}")
    
    async def get_active_watches(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active file watches, optionally filtered by username."""
        try:
            query = self.supabase.table('drive_file_watches').select('*').eq('status', 'active')
            
            if username:
                query = query.eq('username', username)
            
            result = query.execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting active watches: {e}")
            return []
    
    async def deactivate_watch(self, watch_id: str) -> bool:
        """Deactivate a file watch."""
        try:
            logger.info(f"Deactivating Drive file watch: {watch_id}")
            
            # Update status in database
            self.supabase.table('drive_file_watches').update({
                'status': 'inactive',
                'updated_at': datetime.now().isoformat()
            }).eq('watch_id', watch_id).execute()
            
            logger.info(f"Successfully deactivated watch {watch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating watch {watch_id}: {e}")
            return False
    
    async def cleanup_expired_watches(self) -> int:
        """Clean up expired file watches."""
        try:
            logger.info("Cleaning up expired Drive file watches")
            
            # Get expired watches
            current_time = datetime.now().isoformat()
            result = self.supabase.table('drive_file_watches').select('*').lt('expiration', current_time).eq('status', 'active').execute()
            
            expired_count = 0
            for watch in result.data or []:
                try:
                    await self.deactivate_watch(watch['watch_id'])
                    expired_count += 1
                except Exception as e:
                    logger.error(f"Error cleaning up watch {watch['watch_id']}: {e}")
            
            logger.info(f"Cleaned up {expired_count} expired watches")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired watches: {e}")
            return 0
