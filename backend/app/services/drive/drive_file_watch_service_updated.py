"""
Drive File Watch Service - Updated with Unified Webhook Tracking
Manages Google Drive file watches for real-time updates.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json

from ...core.supabase_config import get_supabase_service_client
from ...services.webhook.webhook_tracking_service import WebhookTrackingService

logger = logging.getLogger(__name__)

class DriveFileWatchService:
    """Service for managing Google Drive file watches."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
        self.webhook_tracker = WebhookTrackingService()
        self.master_email = "ai@besunny.ai"
        
    async def setup_file_watch(self, file_id: str, document_id: Optional[str] = None, project_id: Optional[str] = None) -> Optional[str]:
        """
        Set up a Google Drive file watch for real-time updates.
        
        Args:
            file_id: Google Drive file ID
            document_id: Optional document ID to link the watch to
            project_id: Optional project ID to link the watch to
            
        Returns:
            Watch ID if successful, None otherwise
        """
        try:
            logger.info(f"Setting up Drive file watch for {file_id}")
            
            # Check if watch already exists
            existing_watch = await self._get_existing_watch(file_id)
            if existing_watch:
                logger.info(f"Watch already exists for {file_id}: {existing_watch['id']}")
                return existing_watch['id']
            
            # Create Drive watch
            watch_response = await self._create_drive_watch(file_id)
            if not watch_response:
                logger.error(f"Failed to create Drive watch for {file_id}")
                return None
            
            # Store watch information in database
            watch_id = await self._store_file_watch(file_id, document_id, project_id, watch_response)
            
            if watch_id:
                logger.info(f"Successfully set up Drive file watch: {watch_id}")
                
                # Track webhook setup success
                await self.webhook_tracker.track_webhook_activity(
                    service="drive",
                    webhook_type="file_watch_created",
                    success=True
                )
                
                # Update email processing log to indicate Drive watch is active
                await self._update_processing_log_drive_watch(file_id, watch_id)
                
                return watch_id
            else:
                logger.error(f"Failed to store Drive watch for {file_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error setting up Drive file watch: {e}")
            
            # Track webhook setup failure
            await self.webhook_tracker.track_webhook_activity(
                service="drive",
                webhook_type="file_watch_creation_failed",
                success=False,
                error_message=str(e)
            )
            
            return None
    
    async def _get_existing_watch(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Check if a watch already exists for this file."""
        try:
            result = self.supabase.table('drive_file_watches').select('*').eq('file_id', file_id).eq('is_active', True).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing watch: {e}")
            return None
    
    async def _create_drive_watch(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Create a Google Drive file watch."""
        try:
            # This would integrate with Google Drive API
            # For now, we'll simulate the watch creation
            logger.info(f"Creating Drive watch for file {file_id}")
            
            # Simulated watch response
            watch_response = {
                'id': f"watch_{file_id}_{datetime.now().timestamp()}",
                'address': self._get_webhook_url(),
                'expiration': (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            logger.info(f"Drive watch created: {watch_response['id']}")
            return watch_response
            
        except Exception as e:
            logger.error(f"Error creating Drive watch: {e}")
            return None
    
    def _get_webhook_url(self) -> str:
        """Get the webhook URL for Drive notifications."""
        return "https://backend-staging-6085.up.railway.app"
    
    async def _store_file_watch(self, file_id: str, document_id: Optional[str], project_id: Optional[str], watch_response: Dict[str, Any]) -> Optional[str]:
        """Store file watch information in database."""
        try:
            watch_data = {
                'file_id': file_id,
                'document_id': document_id,
                'project_id': project_id,
                'channel_id': watch_response.get('id'),
                'resource_id': file_id,  # For now, using file_id as resource_id
                'expiration': watch_response.get('expiration'),
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'last_webhook_received_at': None,
                'last_poll_at': None,
                'webhook_failures': 0
            }
            
            result = self.supabase.table('drive_file_watches').insert(watch_data).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception("No watch ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing file watch: {e}")
            return None
    
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
                
                # Also log in drive_webhook_logs for detailed tracking
                await self._log_drive_webhook_event(
                    document_id=log_entry.get('document_id'),
                    project_id=log_entry.get('project_id'),
                    file_id=file_id,
                    channel_id=watch_id,
                    resource_id=file_id,
                    resource_state='watch_created',
                    webhook_received_at=datetime.now().isoformat(),
                    n8n_webhook_sent=True,
                    n8n_webhook_response=f"Drive watch active: {watch_id}",
                    n8n_webhook_sent_at=datetime.now().isoformat(),
                    error_message=None
                )
                
        except Exception as e:
            logger.error(f"Error updating processing log: {e}")
    
    async def _log_drive_webhook_event(
        self,
        document_id: Optional[str],
        project_id: Optional[str],
        file_id: str,
        channel_id: str,
        resource_id: str,
        resource_state: str,
        webhook_received_at: str,
        n8n_webhook_sent: bool,
        n8n_webhook_response: Optional[str],
        n8n_webhook_sent_at: Optional[str],
        error_message: Optional[str]
    ):
        """Log Drive webhook events in drive_webhook_logs table."""
        try:
            log_data = {
                'document_id': document_id,
                'project_id': project_id,
                'file_id': file_id,
                'channel_id': channel_id,
                'resource_id': resource_id,
                'resource_state': resource_state,
                'webhook_received_at': webhook_received_at,
                'n8n_webhook_sent': n8n_webhook_sent,
                'n8n_webhook_response': n8n_webhook_response,
                'n8n_webhook_sent_at': n8n_webhook_sent_at,
                'error_message': error_message,
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('drive_webhook_logs').insert(log_data).execute()
            logger.info(f"Drive webhook event logged: {resource_state} for file {file_id}")
            
        except Exception as e:
            logger.warning(f"Could not log Drive webhook event: {e}")
    
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
            
            # Track successful renewal
            await self.webhook_tracker.track_webhook_activity(
                service="drive",
                webhook_type="file_watch_renewed",
                success=True
            )
            
            logger.info(f"Successfully renewed watch {watch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error renewing watch {watch_id}: {e}")
            
            # Track renewal failure
            await self.webhook_tracker.track_webhook_activity(
                service="drive",
                webhook_type="file_watch_renewal_failed",
                success=False,
                error_message=str(e)
            )
            
            return False
    
    async def _get_watch_by_id(self, watch_id: str) -> Optional[Dict[str, Any]]:
        """Get watch information by watch ID."""
        try:
            result = self.supabase.table('drive_file_watches').select('*').eq('channel_id', watch_id).execute()
            
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
                'channel_id': new_watch.get('id'),
                'expiration': new_watch.get('expiration'),
                'updated_at': datetime.now().isoformat()
            }).eq('channel_id', watch_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating watch {watch_id}: {e}")
    
    async def get_active_watches(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active file watches, optionally filtered by username."""
        try:
            query = self.supabase.table('drive_file_watches').select('*').eq('is_active', True)
            
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
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq('channel_id', watch_id).execute()
            
            # Track deactivation
            await self.webhook_tracker.track_webhook_activity(
                service="drive",
                webhook_type="file_watch_deactivated",
                success=True
            )
            
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
            result = self.supabase.table('drive_file_watches').select('*').lt('expiration', current_time).eq('is_active', True).execute()
            
            expired_count = 0
            for watch in result.data or []:
                try:
                    await self.deactivate_watch(watch['channel_id'])
                    expired_count += 1
                except Exception as e:
                    logger.error(f"Error cleaning up watch {watch['channel_id']}: {e}")
            
            logger.info(f"Cleaned up {expired_count} expired watches")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired watches: {e}")
            return 0
