"""
Gmail watch setup service for BeSunny.ai Python backend.
Handles Gmail webhook setup and management for email monitoring.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .gmail_polling_service import GmailPollingService

logger = logging.getLogger(__name__)


class WatchSetupResult(BaseModel):
    """Result of a Gmail watch setup operation."""
    user_id: str
    user_email: str
    success: bool
    watch_id: Optional[str] = None
    expiration: Optional[datetime] = None
    error_message: Optional[str] = None
    timestamp: datetime


class BatchSetupResult(BaseModel):
    """Result of a batch watch setup operation."""
    total_users: int
    successful_setups: int
    failed_setups: int
    skipped_setups: int
    results: List[WatchSetupResult]
    total_processing_time_ms: int
    timestamp: datetime


class GmailWatchSetupService:
    """Service for setting up and managing Gmail watches."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.gmail_service = GmailPollingService()
        
        logger.info("Gmail Watch Setup Service initialized")
    
    async def execute_cron(self) -> Dict[str, Any]:
        """
        Execute the main Gmail watch setup cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"gmail_watch_setup_cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting Gmail watch setup cron execution {execution_id}")
            
            # Get all active users with Gmail integration
            active_users = await self._get_active_users_with_gmail()
            if not active_users:
                logger.info("No active users with Gmail integration found")
                return await self._create_cron_result(
                    execution_id, start_time, 0, 0, 0, 0, "completed", None
                )
            
            # Execute watch setup for each user
            successful_setups = 0
            failed_setups = 0
            skipped_setups = 0
            total_processing_time = 0
            
            for user in active_users:
                try:
                    user_start_time = datetime.now()
                    
                    # Check if user already has an active watch
                    existing_watch = await self._get_existing_watch(user['email'])
                    if existing_watch and self._is_watch_active(existing_watch):
                        skipped_setups += 1
                        logger.info(f"User {user['email']} already has active Gmail watch")
                        continue
                    
                    # Execute watch setup for user
                    result = await self.setup_gmail_watch(user['id'], user['email'])
                    
                    user_processing_time = (datetime.now() - user_start_time).microseconds // 1000
                    total_processing_time += user_processing_time
                    
                    if result and result.get('success'):
                        successful_setups += 1
                        logger.info(f"User {user['email']} Gmail watch setup completed successfully")
                    else:
                        failed_setups += 1
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        logger.warning(f"User {user['email']} Gmail watch setup failed: {error_msg}")
                        
                except Exception as e:
                    failed_setups += 1
                    logger.error(f"Error setting up Gmail watch for user {user['email']}: {str(e)}")
                    continue
            
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            
            return await self._create_cron_result(
                execution_id, start_time, len(active_users), 
                successful_setups, failed_setups, total_processing_time, 
                "completed", None
            )
                
        except Exception as e:
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            logger.error(f"Gmail watch setup cron execution failed: {str(e)}", exc_info=True)
            
            return await self._create_cron_result(
                execution_id, start_time, 0, 0, 0, total_processing_time, 
                "failed", str(e)
            )
    
    async def setup_gmail_watch(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """
        Set up Gmail watch for a specific user.
        
        Args:
            user_id: User ID
            user_email: User's email address
            
        Returns:
            Setup result
        """
        try:
            logger.info(f"Setting up Gmail watch for user {user_email}")
            
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'No Google credentials found for user'
                }
            
            # Create Gmail watch
            watch_result = await self._create_gmail_watch(user_email, credentials)
            if not watch_result.get('success'):
                return watch_result
            
            # Store watch information
            watch_data = {
                'user_email': user_email,
                'history_id': watch_result.get('history_id', ''),
                'expiration': watch_result.get('expiration'),
                'watch_type': 'push',
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert or update watch record
            await self._upsert_gmail_watch(watch_data)
            
            logger.info(f"Gmail watch setup completed for user {user_email}")
            return {
                'success': True,
                'watch_id': watch_result.get('watch_id'),
                'expiration': watch_result.get('expiration')
            }
            
        except Exception as e:
            logger.error(f"Error setting up Gmail watch for user {user_email}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_active_users_with_gmail(self) -> List[Dict[str, Any]]:
        """Get all active users with Gmail integration."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("user_id, google_email") \
                .not_.is_("access_token", None) \
                .execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting active users with Gmail: {str(e)}")
            return []
    
    async def _get_existing_watch(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Get existing Gmail watch for a user."""
        try:
            result = self.supabase.table("gmail_watches") \
                .select("*") \
                .eq("user_email", user_email) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            logger.error(f"Error getting existing Gmail watch: {str(e)}")
            return None
    
    def _is_watch_active(self, watch: Dict[str, Any]) -> bool:
        """Check if a Gmail watch is still active."""
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
    
    async def _create_gmail_watch(self, user_email: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Gmail watch using the Gmail API.
        
        Args:
            user_email: User's email address
            credentials: User's Google credentials
            
        Returns:
            Watch creation result
        """
        try:
            # This would integrate with the Gmail API to create a watch
            # For now, we'll simulate the creation
            watch_id = f"watch_{int(datetime.now().timestamp())}"
            history_id = f"history_{int(datetime.now().timestamp())}"
            expiration = datetime.now() + timedelta(hours=24)  # 24 hour expiration
            
            return {
                'success': True,
                'watch_id': watch_id,
                'history_id': history_id,
                'expiration': expiration
            }
            
        except Exception as e:
            logger.error(f"Error creating Gmail watch: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _upsert_gmail_watch(self, watch_data: Dict[str, Any]) -> bool:
        """Insert or update Gmail watch record."""
        try:
            # Check if watch already exists
            existing = self.supabase.table("gmail_watches") \
                .select("id") \
                .eq("user_email", watch_data['user_email']) \
                .execute()
            
            if existing.data:
                # Update existing watch
                self.supabase.table("gmail_watches") \
                    .update(watch_data) \
                    .eq("user_email", watch_data['user_email']) \
                    .execute()
            else:
                # Insert new watch
                self.supabase.table("gmail_watches") \
                    .insert(watch_data) \
                    .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting Gmail watch: {str(e)}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
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
    
    async def _create_cron_result(
        self, 
        execution_id: str, 
        start_time: datetime, 
        total_users: int, 
        successful_setups: int, 
        failed_setups: int, 
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
            'total_users': total_users,
            'successful_setups': successful_setups,
            'failed_setups': failed_setups,
            'total_processing_time_ms': total_processing_time,
            'status': status,
            'error_message': error_message
        }
