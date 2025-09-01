"""
Master OAuth service for ai@besunny.ai account.
Handles OAuth authentication, token refresh, and credential management.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...core.config import get_settings
from ...core.supabase_config import get_supabase_service_client

logger = logging.getLogger(__name__)


class MasterOAuthService:
    """Service for managing OAuth authentication for the master ai@besunny.ai account."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_service_client()
        self.master_email = "ai@besunny.ai"
    
    async def get_valid_credentials(self) -> Optional[Credentials]:
        """Get valid OAuth credentials for the master account, refreshing if needed."""
        try:
            # Get stored credentials from database
            stored_creds = await self._get_stored_credentials()
            if not stored_creds:
                logger.warning("No stored OAuth credentials found for master account")
                return None
            
            # Create credentials object
            credentials = Credentials(
                token=stored_creds.get('access_token'),
                refresh_token=stored_creds.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
                scopes=[
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.modify',
                    'https://www.googleapis.com/auth/gmail.watch'
                ]
            )
            
            # Check if credentials need refresh
            if credentials.expired and credentials.refresh_token:
                logger.info("Refreshing expired OAuth credentials...")
                try:
                    credentials.refresh(Request())
                    # Update stored credentials with new access token
                    await self._update_access_token(credentials.token)
                    logger.info("OAuth credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Failed to refresh OAuth credentials: {e}")
                    return None
            
            if not credentials.valid:
                logger.error("OAuth credentials are not valid after refresh")
                return None
            
            logger.info("Valid OAuth credentials obtained for master account")
            return credentials
            
        except Exception as e:
            logger.error(f"Error getting valid OAuth credentials: {e}")
            return None
    
    async def setup_initial_oauth(self, auth_code: str, redirect_uri: str) -> bool:
        """Set up initial OAuth for the master account using authorization code."""
        try:
            from google_auth_oauthlib.flow import Flow
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=[
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.modify',
                    'https://www.googleapis.com/auth/gmail.watch'
                ]
            )
            
            # Exchange auth code for tokens
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # Store credentials in database
            await self._store_credentials(credentials)
            
            logger.info("Initial OAuth setup completed for master account")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup initial OAuth: {e}")
            return False
    
    async def setup_gmail_watch(self) -> Optional[str]:
        """Set up Gmail watch for the master account to receive notifications."""
        try:
            credentials = await self.get_valid_credentials()
            if not credentials:
                logger.error("No valid OAuth credentials available for Gmail watch setup")
                return None
            
            # Create Gmail API service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create watch request
            watch_request = {
                'labelIds': ['INBOX'],
                'topicName': f"projects/{self.settings.google_project_id}/topics/gmail-notifications",
                'labelFilterAction': 'include'
            }
            
            # Create the watch
            watch = service.users().watch(userId=self.master_email, body=watch_request).execute()
            
            # Store watch information
            watch_id = await self._store_gmail_watch(watch)
            
            logger.info(f"Gmail watch setup successful for master account: {watch_id}")
            return watch_id
            
        except Exception as e:
            logger.error(f"Failed to setup Gmail watch: {e}")
            return None
    
    async def _get_stored_credentials(self) -> Optional[Dict[str, Any]]:
        """Get stored OAuth credentials from database."""
        try:
            result = self.supabase.table('master_oauth_credentials') \
                .select('*') \
                .eq('email', self.master_email) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting stored credentials: {e}")
            return None
    
    async def _store_credentials(self, credentials: Credentials) -> bool:
        """Store OAuth credentials in database."""
        try:
            cred_data = {
                'email': self.master_email,
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                'scopes': json.dumps(credentials.scopes),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Upsert credentials
            result = self.supabase.table('master_oauth_credentials') \
                .upsert(cred_data) \
                .execute()
            
            if result.data:
                logger.info("OAuth credentials stored successfully")
                return True
            else:
                logger.error("Failed to store OAuth credentials")
                return False
                
        except Exception as e:
            logger.error(f"Error storing OAuth credentials: {e}")
            return False
    
    async def _update_access_token(self, new_access_token: str) -> bool:
        """Update stored access token after refresh."""
        try:
            result = self.supabase.table('master_oauth_credentials') \
                .update({
                    'access_token': new_access_token,
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq('email', self.master_email) \
                .execute()
            
            if result.data:
                logger.info("Access token updated successfully")
                return True
            else:
                logger.error("Failed to update access token")
                return False
                
        except Exception as e:
            logger.error(f"Error updating access token: {e}")
            return False
    
    async def _store_gmail_watch(self, watch_response: Dict[str, Any]) -> str:
        """Store Gmail watch information in database."""
        try:
            watch_data = {
                'email': self.master_email,
                'history_id': watch_response.get('historyId'),
                'expiration': watch_response.get('expiration'),
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('gmail_watches') \
                .insert(watch_data) \
                .execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception("Failed to store Gmail watch")
                
        except Exception as e:
            logger.error(f"Error storing Gmail watch: {e}")
            raise
