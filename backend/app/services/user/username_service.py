"""
Username service for BeSunny.ai Python backend.
Handles username management and virtual email setup.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class UsernameResult(BaseModel):
    """Result of a username operation."""
    user_id: str
    username: str
    success: bool
    virtual_email: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime


class BatchUsernameResult(BaseModel):
    """Result of a batch username operation."""
    total_users: int
    successful_operations: int
    failed_operations: int
    skipped_operations: int
    results: List[UsernameResult]
    total_processing_time_ms: int
    timestamp: datetime


class UsernameService:
    """Service for managing usernames and virtual email setup."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        
        logger.info("Username Service initialized")
    
    async def execute_cron(self) -> Dict[str, Any]:
        """
        Execute the main username management cron job.
        
        Returns:
            Execution results and metrics
        """
        execution_id = f"username_management_cron_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting username management cron execution {execution_id}")
            
            # Get all users without usernames
            users_without_usernames = await self._get_users_without_usernames()
            if not users_without_usernames:
                logger.info("No users need username setup")
                return await self._create_cron_result(
                    execution_id, start_time, 0, 0, 0, 0, "completed", None
                )
            
            # Execute username setup for each user
            successful_operations = 0
            failed_operations = 0
            skipped_operations = 0
            total_processing_time = 0
            
            for user in users_without_usernames:
                try:
                    user_start_time = datetime.now()
                    
                    # Check if user already has a username
                    if user.get('username'):
                        skipped_operations += 1
                        logger.info(f"User {user['email']} already has username: {user['username']}")
                        continue
                    
                    # Generate username from email
                    username = self._generate_username_from_email(user['email'])
                    if not username:
                        failed_operations += 1
                        logger.warning(f"Could not generate username for user {user['email']}")
                        continue
                    
                    # Set username for user
                    result = await self.set_username(user['id'], username)
                    
                    user_processing_time = (datetime.now() - user_start_time).microseconds // 1000
                    total_processing_time += user_processing_time
                    
                    if result and result.get('success'):
                        successful_operations += 1
                        logger.info(f"User {user['email']} username setup completed successfully")
                    else:
                        failed_operations += 1
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        logger.warning(f"User {user['email']} username setup failed: {error_msg}")
                        
                except Exception as e:
                    failed_operations += 1
                    logger.error(f"Error setting username for user {user['email']}: {str(e)}")
                    continue
            
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            
            return await self._create_cron_result(
                execution_id, start_time, len(users_without_usernames), 
                successful_operations, failed_operations, total_processing_time, 
                "completed", None
            )
                
        except Exception as e:
            end_time = datetime.now()
            total_processing_time = (end_time - start_time).microseconds // 1000
            logger.error(f"Username management cron execution failed: {str(e)}", exc_info=True)
            
            return await self._create_cron_result(
                execution_id, start_time, 0, 0, 0, total_processing_time, 
                "failed", str(e)
            )
    
    async def set_username(self, user_id: str, username: str) -> Dict[str, Any]:
        """
        Set username for a specific user.
        
        Args:
            user_id: User ID
            username: Username to set
            
        Returns:
            Username setting result
        """
        try:
            logger.info(f"Setting username '{username}' for user {user_id}")
            
            # Validate username
            if not self._validate_username(username):
                return {
                    'success': False,
                    'error': 'Invalid username format'
                }
            
            # Check if username is already taken
            if await self._is_username_taken(username, user_id):
                return {
                    'success': False,
                    'error': 'Username already taken'
                }
            
            # Generate virtual email
            virtual_email = self._generate_virtual_email(username)
            
            # Update user record
            update_data = {
                'username': username,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("users") \
                .update(update_data) \
                .eq("id", user_id) \
                .execute()
            
            logger.info(f"Username '{username}' set successfully for user {user_id}")
            return {
                'success': True,
                'username': username,
                'virtual_email': virtual_email
            }
            
        except Exception as e:
            logger.error(f"Error setting username for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_username_from_email(self, email: str) -> Optional[str]:
        """Generate username from email address."""
        try:
            if not email or '@' not in email:
                return None
            
            # Extract local part of email
            local_part = email.split('@')[0]
            
            # Remove special characters and convert to lowercase
            username = ''.join(c for c in local_part if c.isalnum() or c in '._-')
            username = username.lower()
            
            # Ensure username is not too long
            if len(username) > 30:
                username = username[:30]
            
            # Ensure username is not empty
            if not username:
                return None
            
            return username
            
        except Exception as e:
            logger.error(f"Error generating username from email {email}: {str(e)}")
            return None
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format."""
        if not username:
            return False
        
        # Username should be 3-30 characters
        if len(username) < 3 or len(username) > 30:
            return False
        
        # Username should only contain alphanumeric characters, dots, underscores, and hyphens
        if not all(c.isalnum() or c in '._-' for c in username):
            return False
        
        # Username should not start or end with dot, underscore, or hyphen
        if username[0] in '._-' or username[-1] in '._-':
            return False
        
        return True
    
    async def _is_username_taken(self, username: str, exclude_user_id: str = None) -> bool:
        """Check if username is already taken by another user."""
        try:
            query = self.supabase.table("users") \
                .select("id") \
                .eq("username", username)
            
            if exclude_user_id:
                query = query.neq("id", exclude_user_id)
            
            result = query.execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking if username is taken: {str(e)}")
            return False
    
    def _generate_virtual_email(self, username: str) -> str:
        """Generate virtual email address for username."""
        try:
            # Use the configured domain or default to a placeholder
            domain = getattr(self.settings, 'virtual_email_domain', 'virtual.besunny.ai')
            return f"{username}@{domain}"
            
        except Exception as e:
            logger.error(f"Error generating virtual email: {str(e)}")
            return f"{username}@virtual.besunny.ai"
    
    async def _get_users_without_usernames(self) -> List[Dict[str, Any]]:
        """Get all users without usernames."""
        try:
            result = self.supabase.table("users") \
                .select("id, email, username") \
                .is_("username", None) \
                .execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting users without usernames: {str(e)}")
            return []
    
    async def _create_cron_result(
        self, 
        execution_id: str, 
        start_time: datetime, 
        total_users: int, 
        successful_operations: int, 
        failed_operations: int, 
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
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'total_processing_time_ms': total_processing_time,
            'status': status,
            'error_message': error_message
        }
