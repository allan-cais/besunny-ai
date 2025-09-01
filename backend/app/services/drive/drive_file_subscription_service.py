"""
Drive file subscription service for BeSunny.ai Python backend.
Handles Google Drive file monitoring setup and management.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .drive_polling_service import DrivePollingService

logger = logging.getLogger(__name__)


class FileSubscriptionResult(BaseModel):
    """Result of a file subscription operation."""
    file_id: str
    document_id: str
    project_id: str
    success: bool
    channel_id: Optional[str] = None
    resource_id: Optional[str] = None
    expiration: Optional[datetime] = None
    error_message: Optional[str] = None
    timestamp: datetime


class BatchSubscriptionResult(BaseModel):
    """Result of a batch subscription operation."""
    total_files: int
    successful_subscriptions: int
    failed_subscriptions: int
    skipped_subscriptions: int
    results: List[FileSubscriptionResult]
    total_processing_time_ms: int
    timestamp: datetime


class DriveFileSubscriptionService:
    """Service for setting up and managing Google Drive file monitoring."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.drive_service = DrivePollingService()
        
        logger.info("Drive File Subscription Service initialized")
    
    async def execute_cron(self) -> Dict[str, Any]:
        """
        Execute the main drive file subscription cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"drive_file_subscription_cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting drive file subscription cron execution {execution_id}")
            
            # Get all documents that need file monitoring
            documents_needing_monitoring = await self._get_documents_needing_monitoring()
            if not documents_needing_monitoring:
                logger.info("No documents need file monitoring")
                return await self._create_cron_result(
                    execution_id, start_time, 0, 0, 0, 0, "completed", None
                )
            
            # Execute subscription for each document
            successful_subscriptions = 0
            failed_subscriptions = 0
            skipped_subscriptions = 0
            total_processing_time = 0
            
            for document in documents_needing_monitoring:
                try:
                    doc_start_time = datetime.now()
                    
                    # Check if file already has active monitoring
                    existing_watch = await self._get_existing_file_watch(document['file_id'])
                    if existing_watch and self._is_watch_active(existing_watch):
                        skipped_subscriptions += 1
                        logger.info(f"File {document['file_id']} already has active monitoring")
                        continue
                    
                    # Execute subscription for file
                    result = await self.subscribe_to_file(
                        user_id=document['created_by'],
                        document_id=document['id'],
                        file_id=document['file_id']
                    )
                    
                    doc_processing_time = (datetime.now() - doc_start_time).microseconds // 1000
                    total_processing_time += doc_processing_time
                    
                    if result and result.get('success'):
                        successful_subscriptions += 1
                        logger.info(f"File {document['file_id']} subscription completed successfully")
                    else:
                        failed_subscriptions += 1
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        logger.warning(f"File {document['file_id']} subscription failed: {error_msg}")
                        
                except Exception as e:
                    failed_subscriptions += 1
                    logger.error(f"Error subscribing to file {document['file_id']}: {str(e)}")
                    continue
            
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            
            return await self._create_cron_result(
                execution_id, start_time, len(documents_needing_monitoring), 
                successful_subscriptions, failed_subscriptions, total_processing_time, 
                "completed", None
            )
                
        except Exception as e:
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            logger.error(f"Drive file subscription cron execution failed: {str(e)}", exc_info=True)
            
            return await self._create_cron_result(
                execution_id, start_time, 0, 0, 0, total_processing_time, 
                "failed", str(e)
            )
    
    async def subscribe_to_file(self, user_id: str, document_id: str, file_id: str) -> Dict[str, Any]:
        """
        Subscribe to file changes for a specific document.
        
        Args:
            user_id: User ID
            document_id: Document ID
            file_id: Google Drive file ID
            
        Returns:
            Subscription result
        """
        try:
            logger.info(f"Subscribing to file {file_id} for document {document_id}")
            
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'No Google credentials found for user'
                }
            
            # Create file watch
            watch_result = await self._create_file_watch(file_id, credentials)
            if not watch_result.get('success'):
                return watch_result
            
            # Store watch information
            watch_data = {
                'file_id': file_id,
                'channel_id': watch_result.get('channel_id'),
                'resource_id': watch_result.get('resource_id'),
                'expiration': watch_result.get('expiration'),
                'document_id': document_id,
                'project_id': await self._get_document_project_id(document_id),
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert or update watch record
            await self._upsert_file_watch(watch_data)
            
            logger.info(f"File subscription completed for file {file_id}")
            return {
                'success': True,
                'channel_id': watch_result.get('channel_id'),
                'resource_id': watch_result.get('resource_id'),
                'expiration': watch_result.get('expiration')
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to file {file_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_documents_needing_monitoring(self) -> List[Dict[str, Any]]:
        """Get all documents that need file monitoring."""
        try:
            result = self.supabase.table("documents") \
                .select("id, file_id, created_by, project_id") \
                .not_.is_("file_id", None) \
                .eq("watch_active", True) \
                .execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting documents needing monitoring: {str(e)}")
            return []
    
    async def _get_existing_file_watch(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get existing file watch for a file."""
        try:
            result = self.supabase.table("drive_file_watches") \
                .select("*") \
                .eq("file_id", file_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            logger.error(f"Error getting existing file watch: {str(e)}")
            return None
    
    def _is_watch_active(self, watch: Dict[str, Any]) -> bool:
        """Check if a file watch is still active."""
        if not watch.get('is_active'):
            return False
        
        expiration = watch.get('expiration')
        if not expiration:
            return False
        
        # Parse expiration if it's a string
        if isinstance(expiration, str):
            try:
                expiration = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
            except ValueError:
                return False
        
        # Check if watch expires in the next hour
        return expiration > datetime.now() + timedelta(hours=1)
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's Google credentials."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            logger.error(f"Error getting user credentials: {str(e)}")
            return None
    
    async def _get_document_project_id(self, document_id: str) -> Optional[str]:
        """Get project ID for a document."""
        try:
            result = self.supabase.table("documents") \
                .select("project_id") \
                .eq("id", document_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data.get('project_id')
            return None
            
        except Exception as e:
            logger.error(f"Error getting document project ID: {str(e)}")
            return None
    
    async def _get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document information."""
        try:
            result = self.supabase.table("documents") \
                .select("*") \
                .eq("id", document_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            logger.error(f"Error getting document info: {str(e)}")
            return None
    
    async def _get_user_documents_with_files(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents owned by user that have file IDs."""
        try:
            result = self.supabase.table("documents") \
                .select("id, title, file_id, project_id") \
                .eq("created_by", user_id) \
                .not_.is_("file_id", None) \
                .execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting user documents with files: {str(e)}")
            return []
    
    async def _get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document information."""
        try:
            result = self.supabase.table("documents") \
                .select("*") \
                .eq("id", document_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            logger.error(f"Error getting document info: {str(e)}")
            return None
    
    async def _create_file_watch(self, file_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a file watch using the Google Drive API.
        
        Args:
            file_id: Google Drive file ID
            credentials: User's Google credentials
            
        Returns:
            Watch creation result
        """
        try:
            # This would integrate with the Google Drive API to create a watch
            # For now, we'll simulate the creation
            channel_id = f"channel_{int(datetime.now().timestamp())}"
            resource_id = f"resource_{int(datetime.now().timestamp())}"
            expiration = datetime.now() + timedelta(hours=24)  # 24 hour expiration
            
            return {
                'success': True,
                'channel_id': channel_id,
                'resource_id': resource_id,
                'expiration': expiration
            }
            
        except Exception as e:
            logger.error(f"Error creating file watch: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _upsert_file_watch(self, watch_data: Dict[str, Any]) -> bool:
        """Insert or update file watch record."""
        try:
            # Check if watch already exists
            existing = self.supabase.table("drive_file_watches") \
                .select("id") \
                .eq("file_id", watch_data['file_id']) \
                .execute()
            
            if existing.data:
                # Update existing watch
                self.supabase.table("drive_file_watches") \
                    .update(watch_data) \
                    .eq("file_id", watch_data['file_id']) \
                    .execute()
            else:
                # Insert new watch
                self.supabase.table("drive_file_watches") \
                    .insert(watch_data) \
                    .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting file watch: {str(e)}")
            return False
    
    async def _create_cron_result(
        self, 
        execution_id: str, 
        start_time: datetime, 
        total_files: int, 
        successful_subscriptions: int, 
        failed_subscriptions: int, 
        total_processing_time: int, 
        status: str, 
        error_message: Optional[str]
    ) -> Dict[str, Any]:
        """Create standardized cron execution result."""
        end_time = datetime.now()
        
        return {
            'execution_id': execution_id,
            'start_time': start_time,
            'end_time': end_time,
            'total_files': total_files,
            'successful_subscriptions': successful_subscriptions,
            'failed_subscriptions': failed_subscriptions,
            'total_processing_time_ms': total_processing_time,
            'status': status,
            'error_message': error_message
        }
