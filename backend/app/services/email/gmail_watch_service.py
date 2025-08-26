"""
Gmail watch service for monitoring virtual email addresses.
Sets up push notifications for emails sent to ai+{username}@besunny.ai.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class GmailWatchService:
    """Service for managing Gmail watches and push notifications."""
    
    def __init__(self):
        self.settings = get_settings()
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        self.supabase = get_supabase_service_client()
        self.webhook_url = f"{self.settings.webhook_base_url}/api/v1/webhooks/gmail"
    
    async def setup_virtual_email_watch(self, user_id: str) -> Optional[str]:
        """Set up Gmail watch for a user's virtual email address."""
        try:
            # Get user's username
            username = self._get_user_username(user_id)
            if not username:
                logger.error(f"No username found for user {user_id}")
                return None
            
            # Get user's Google credentials
            credentials = await self._get_user_google_credentials(user_id)
            if not credentials:
                logger.error(f"No Google credentials found for user {user_id}")
                return None
            
            # Log credentials information for debugging
            logger.info(f"Credentials type: {type(credentials).__name__}")
            logger.info(f"Credentials valid: {credentials.valid}")
            logger.info(f"Credentials expired: {credentials.expired}")
            logger.info(f"Credentials scopes: {credentials.scopes}")
            
            # Create Gmail API service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create watch request
            watch_request = {
                'labelIds': ['INBOX'],  # Watch INBOX for new messages
                'topicName': f"projects/{self.settings.google_project_id}/topics/gmail-notifications",
                'labelFilterAction': 'include'
            }
            
            # Create the watch
            watch = service.users().watch(userId='me', body=watch_request).execute()
            
            # Store watch information in database
            watch_id = await self._store_gmail_watch(
                user_email=f"{username}@virtual.besunny.ai",
                history_id=watch.get('historyId'),
                expiration=watch.get('expiration')
            )
            
            logger.info(f"Gmail watch created for user {username}: {watch_id}")
            return watch_id
            
        except HttpError as e:
            logger.error(f"Failed to create Gmail watch for user {user_id}: {e}")
            logger.error(f"HTTP Error details: {e.resp.status} - {e.content}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error setting up Gmail watch: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            return None
    
    async def setup_master_account_watch(self) -> Optional[str]:
        """Set up Gmail watch for the master account (inbound@besunny.ai)."""
        try:
            # Get master account credentials
            credentials = await self._get_master_account_credentials()
            if not credentials:
                logger.error("No master account credentials found")
                return None
            
            # Create Gmail API service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create watch request for the master account
            watch_request = {
                'labelIds': ['INBOX'],
                'topicName': f"projects/{self.settings.google_project_id}/topics/gmail-notifications",
                'labelFilterAction': 'include'
            }
            
            # Create the watch
            watch = service.users().watch(userId='me', body=watch_request).execute()
            
            # Store master account watch
            watch_id = await self._store_master_gmail_watch(
                history_id=watch.get('historyId'),
                expiration=watch.get('expiration')
            )
            
            logger.info(f"Master account Gmail watch created: {watch_id}")
            return watch_id
            
        except HttpError as e:
            logger.error(f"Failed to create master account Gmail watch: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error setting up master account watch: {e}")
            return None
    
    async def renew_watch(self, watch_id: str) -> bool:
        """Renew an existing Gmail watch before it expires."""
        try:
            # Get watch information
            watch_info = await self._get_gmail_watch(watch_id)
            if not watch_info:
                logger.error(f"Watch {watch_id} not found")
                return False
            
            # Check if renewal is needed
            expiration = datetime.fromisoformat(watch_info['expiration'])
            if datetime.utcnow() + timedelta(hours=1) < expiration:
                logger.info(f"Watch {watch_id} doesn't need renewal yet")
                return True
            
            # Get credentials
            if watch_info.get('is_master_account'):
                credentials = await self._get_master_account_credentials()
            else:
                credentials = await self._get_user_google_credentials(watch_info['user_id'])
            
            if not credentials:
                logger.error(f"No credentials found for watch {watch_id}")
                return False
            
            # Create Gmail API service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Stop existing watch
            try:
                service.users().stop(userId='me').execute()
            except HttpError:
                pass  # Watch may have already expired
            
            # Create new watch
            watch_request = {
                'labelIds': ['INBOX'],
                'topicName': f"projects/{self.settings.google_project_id}/topics/gmail-notifications",
                'labelFilterAction': 'include'
            }
            
            watch = service.users().watch(userId='me', body=watch_request).execute()
            
            # Update watch in database
            self._update_gmail_watch(
                watch_id=watch_id,
                history_id=watch.get('historyId'),
                expiration=watch.get('expiration')
            )
            
            logger.info(f"Successfully renewed Gmail watch {watch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error renewing Gmail watch {watch_id}: {e}")
            return False
    
    async def stop_watch(self, watch_id: str) -> bool:
        """Stop a Gmail watch."""
        try:
            # Get watch information
            watch_info = self._get_gmail_watch(watch_id)
            if not watch_info:
                logger.warning(f"Watch {watch_id} not found for stopping")
                return True
            
            # Get credentials - for now, use master account credentials for all watches
            credentials = await self._get_master_account_credentials()
            
            if credentials:
                # Create Gmail API service and stop watch
                service = build('gmail', 'v1', credentials=credentials)
                try:
                    service.users().stop(userId='me').execute()
                except HttpError:
                    pass  # Watch may have already expired
            
            # Mark watch as inactive in database
            self._deactivate_gmail_watch(watch_id)
            
            logger.info(f"Successfully stopped Gmail watch {watch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Gmail watch {watch_id}: {e}")
            return False
    
    def get_active_watches(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active Gmail watches."""
        try:
            if not self.supabase:
                return []
            
            query = self.supabase.table('gmail_watches').select('*').eq('is_active', True)
            
            if user_email:
                query = query.eq('user_email', user_email)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting active Gmail watches: {e}")
            return []
    
    def _get_user_username(self, user_id: str) -> Optional[str]:
        """Get username for a user."""
        try:
            if not self.supabase:
                return None
            
            result = self.supabase.table('users').select('username').eq('id', user_id).single().execute()
            return result.data.get('username') if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting username for user {user_id}: {e}")
            return None
    
    async def _get_user_google_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            # For now, use the master account credentials
            # TODO: Implement user-specific OAuth credentials
            return await self._get_master_account_credentials()
            
        except Exception as e:
            logger.error(f"Error getting Google credentials for user {user_id}: {e}")
            return None
    
    async def _get_master_account_credentials(self) -> Optional[Credentials]:
        """Get Google credentials for the master account."""
        try:
            from google.oauth2 import service_account
            import json
            import base64
            
            # Try to get base64 encoded key first (for production)
            key_base64 = getattr(self.settings, 'google_service_account_key_base64', None)
            if key_base64:
                try:
                    # Decode base64 and parse JSON
                    key_json = base64.b64decode(key_base64).decode('utf-8')
                    key_data = json.loads(key_json)
                    
                    credentials = service_account.Credentials.from_service_account_info(
                        key_data,
                        scopes=[
                            'https://www.googleapis.com/auth/gmail.readonly',
                            'https://www.googleapis.com/auth/gmail.modify',
                            'https://www.googleapis.com/auth/gmail.watch'
                        ]
                    )
                    
                    # Ensure credentials are valid and have access token
                    if not credentials.valid:
                        logger.info("Refreshing Google service account credentials...")
                        credentials.refresh(None)
                    
                    logger.info("Master account Google credentials loaded from base64")
                    logger.debug(f"Credentials valid: {credentials.valid}, expired: {credentials.expired}")
                    return credentials
                    
                except Exception as e:
                    logger.warning(f"Failed to load base64 credentials: {e}")
            
            # Fallback to file path (for local development)
            key_path = getattr(self.settings, 'google_service_account_key_path', None)
            if key_path:
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        key_path,
                        scopes=[
                            'https://www.googleapis.com/auth/gmail.readonly',
                            'https://www.googleapis.com/auth/gmail.modify',
                            'https://www.googleapis.com/auth/gmail.watch'
                        ]
                    )
                    
                    # Ensure credentials are valid and have access token
                    if not credentials.valid:
                        logger.info("Refreshing Google service account credentials...")
                        credentials.refresh(None)
                    
                    logger.info("Master account Google credentials loaded from file")
                    logger.debug(f"Credentials valid: {credentials.valid}, expired: {credentials.expired}")
                    return credentials
                    
                except Exception as e:
                    logger.warning(f"Failed to load file credentials: {e}")
            
            logger.error("No Google service account credentials configured")
            return None
            
        except Exception as e:
            logger.error(f"Error getting master account credentials: {e}")
            return None
    
    def _store_gmail_watch(
        self, 
        user_email: str, 
        history_id: str, 
        expiration: str
    ) -> str:
        """Store Gmail watch information in database."""
        try:
            if not self.supabase:
                raise Exception("Supabase client not available")
            
            result = self.supabase.table('gmail_watches').insert({
                'user_email': user_email,
                'history_id': history_id,
                'expiration': expiration,
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            if not result.data:
                raise Exception("Failed to store Gmail watch")
            
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error storing Gmail watch: {e}")
            raise
    
    def _store_master_gmail_watch(
        self, 
        history_id: str, 
        expiration: str
    ) -> str:
        """Store master account Gmail watch information in database."""
        try:
            if not self.supabase:
                raise Exception("Supabase client not available")
            
            result = self.supabase.table('gmail_watches').insert({
                'user_email': 'inbound@besunny.ai',  # Master account email
                'history_id': history_id,
                'expiration': expiration,
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            if not result.data:
                raise Exception("Failed to store master Gmail watch")
            
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error storing master Gmail watch: {e}")
            raise
    
    def _get_gmail_watch(self, watch_id: str) -> Optional[Dict[str, Any]]:
        """Get Gmail watch information by ID."""
        try:
            if not self.supabase:
                return None
            
            result = self.supabase.table('gmail_watches').select('*').eq('id', watch_id).single().execute()
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting Gmail watch {watch_id}: {e}")
            return None
    
    def _update_gmail_watch(
        self, 
        watch_id: str, 
        history_id: str, 
        expiration: str
    ) -> None:
        """Update Gmail watch information."""
        try:
            if not self.supabase:
                raise Exception("Supabase client not available")
            
            self.supabase.table('gmail_watches').update({
                'history_id': history_id,
                'expiration': expiration,
                'updated_at': datetime.now().isoformat()
            }).eq('id', watch_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating Gmail watch {watch_id}: {e}")
            raise
    
    def _deactivate_gmail_watch(self, watch_id: str) -> None:
        """Mark a Gmail watch as inactive."""
        try:
            if not self.supabase:
                raise Exception("Supabase client not available")
            
            self.supabase.table('gmail_watches').update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq('id', watch_id).execute()
            
        except Exception as e:
            logger.error(f"Error deactivating Gmail watch {watch_id}: {e}")
            raise
