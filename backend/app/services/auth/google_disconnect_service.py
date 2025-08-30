"""
Google disconnect service for BeSunny.ai Python backend.
Handles disconnecting Google accounts and revoking tokens.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class DisconnectResult(BaseModel):
    """Result of a Google disconnect operation."""
    user_id: str
    success: bool
    message: str
    tokens_revoked: bool
    credentials_removed: bool
    error_message: Optional[str] = None
    timestamp: datetime


class GoogleDisconnectService:
    """Service for disconnecting Google accounts and revoking tokens."""
    
    def __init__(self):
        self.settings = get_settings()
        # Use service role client to bypass RLS policies
        from ...core.database import get_supabase_service_client
        self.supabase = get_supabase_service_client()
        
        print(f"🔍 Disconnect Debug - Service initialized with settings: {self.settings}")
        print(f"🔍 Disconnect Debug - Supabase client type: {type(self.supabase)}")
        print(f"🔍 Disconnect Debug - Supabase client: {self.supabase}")
        print(f"🔍 Disconnect Debug - Using service role client: {self.supabase is not None}")
        
        logger.info("Google Disconnect Service initialized")
    
    async def disconnect_google_account(self, user_id: str) -> Dict[str, Any]:
        """
        Disconnect a user's Google account and revoke all tokens.
        
        Args:
            user_id: User ID to disconnect
            
        Returns:
            Disconnect result
        """
        try:
            print(f"🔍 Disconnect Debug - Starting disconnect for user_id: {user_id}")
            print(f"🔍 Disconnect Debug - User ID type: {type(user_id)}")
            print(f"🔍 Disconnect Debug - User ID value: {user_id}")
            
            # Get user's Google credentials
            print(f"🔍 Disconnect Debug - About to call _get_user_credentials")
            credentials = await self._get_user_credentials(user_id)
            print(f"🔍 Disconnect Debug - _get_user_credentials returned: {credentials}")
            
            if not credentials:
                print(f"🔍 Disconnect Debug - No credentials found, returning early")
                return {
                    'success': True,
                    'message': 'No Google credentials found to disconnect',
                    'tokens_revoked': False,
                    'credentials_removed': False
                }
            
            # Revoke access token at Google
            access_token_revoked = False
            if credentials.get('access_token'):
                access_token_revoked = await self._revoke_token_at_google(credentials['access_token'])
            
            # Revoke refresh token at Google
            refresh_token_revoked = False
            if credentials.get('refresh_token'):
                refresh_token_revoked = await self._revoke_token_at_google(credentials['refresh_token'])
            
            # Soft delete credentials and maintain audit trail
            credentials_removed = await self._remove_google_credentials(user_id)
            
            # Remove all related webhooks and watches
            await self._cleanup_google_integrations(user_id)
            
            logger.info(f"Google account disconnected successfully for user {user_id}")
            return {
                'success': True,
                'message': 'Google account disconnected successfully - credentials deactivated and audit trail maintained',
                'tokens_revoked': access_token_revoked or refresh_token_revoked,
                'credentials_removed': credentials_removed
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting Google account for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error disconnecting Google account: {str(e)}',
                'tokens_revoked': False,
                'credentials_removed': False,
                'error_message': str(e)
            }
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's Google credentials."""
        try:
            print(f"🔍 Disconnect Debug - Looking for credentials for user_id: {user_id}")
            
            # Check database connection details
            print(f"🔍 Disconnect Debug - Supabase URL: {self.supabase.supabase_url}")
            print(f"🔍 Disconnect Debug - Supabase project ID: {self.supabase.supabase_url.split('//')[1].split('.')[0] if self.supabase.supabase_url else 'Unknown'}")
            
            # Check if table exists and get its structure
            try:
                # Try to get table info
                table_info = self.supabase.table("google_credentials").select("count").limit(1).execute()
                print(f"🔍 Disconnect Debug - Table exists and accessible: {table_info is not None}")
                
                # Try to get a sample row to see the structure
                sample_row = self.supabase.table("google_credentials").select("*").limit(1).execute()
                if sample_row.data:
                    print(f"🔍 Disconnect Debug - Sample row keys: {list(sample_row.data[0].keys())}")
                    print(f"🔍 Disconnect Debug - Sample row: {sample_row.data[0]}")
                else:
                    print(f"🔍 Disconnect Debug - No sample rows found")
                    
            except Exception as e:
                print(f"🔍 Disconnect Debug - Table access error: {e}")
                return None
            
            # First, let's see what's in the table
            all_credentials = self.supabase.table("google_credentials") \
                .select("user_id, status, google_email") \
                .execute()
            print(f"🔍 Disconnect Debug - All credentials in table: {all_credentials.data}")
            print(f"🔍 Disconnect Debug - Credentials count: {len(all_credentials.data) if all_credentials.data else 0}")
            
            # Let's also try to see what happens if we query without any filters
            try:
                raw_query = self.supabase.table("google_credentials").select("*").execute()
                print(f"🔍 Disconnect Debug - Raw query result: {raw_query.data}")
                print(f"🔍 Disconnect Debug - Raw query count: {len(raw_query.data) if raw_query.data else 0}")
            except Exception as e:
                print(f"🔍 Disconnect Debug - Raw query error: {e}")
            
            # Now try to get the specific user's credentials
            result = self.supabase.table("google_credentials") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                print(f"🔍 Disconnect Debug - Found credentials: {result.data}")
                return result.data
            return None
            
        except Exception as e:
            print(f"🔍 Disconnect Debug - Error getting user credentials: {str(e)}")
            print(f"🔍 Disconnect Debug - Error type: {type(e)}")
            print(f"🔍 Disconnect Debug - Error details: {e}")
            return None
    
    async def _revoke_token_at_google(self, token: str) -> bool:
        """Revoke a token at Google's OAuth endpoint."""
        try:
            response = await self._make_google_request(
                'https://oauth2.googleapis.com/revoke',
                method='POST',
                data={'token': token}
            )
            
            if response and response.get('status') == 200:
                logger.info("Token revoked successfully at Google")
                return True
            else:
                logger.warning(f"Failed to revoke token at Google: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking token at Google: {str(e)}")
            return False
    
    async def _remove_google_credentials(self, user_id: str) -> bool:
        """Soft delete Google credentials and maintain audit trail."""
        try:
            # Get current credentials for audit trail
            current_credentials = self.supabase.table("google_credentials") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if not current_credentials.data:
                logger.info(f"No Google credentials found for user {user_id}")
                return True
            
            # Create audit record before soft delete
            audit_data = {
                "user_id": user_id,
                "action": "disconnect",
                "previous_status": "connected",
                "disconnected_at": datetime.now().isoformat(),
                "had_access_token": bool(current_credentials.data.get('access_token')),
                "had_refresh_token": bool(current_credentials.data.get('refresh_token')),
                "scope": current_credentials.data.get('scope'),
                "metadata": current_credentials.data
            }
            
            # Insert audit record
            self.supabase.table("google_credentials_audit") \
                .insert(audit_data) \
                .execute()
            
            # Soft delete: mark as inactive instead of hard delete
            result = self.supabase.table("google_credentials") \
                .update({
                    "status": "disconnected",
                    "disconnected_at": datetime.now().isoformat(),
                    "access_token": None,
                    "refresh_token": None,
                    "expires_at": None,
                    "updated_at": datetime.now().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info(f"Google credentials soft deleted for user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error soft deleting Google credentials: {str(e)}")
            return False
    
    async def _cleanup_google_integrations(self, user_id: str) -> None:
        """Clean up all Google integrations for a user."""
        try:
            # Remove calendar webhooks
            await self._remove_calendar_webhooks(user_id)
            
            # Remove drive file watches
            await self._remove_drive_file_watches(user_id)
            
            # Remove Gmail watches
            await self._remove_gmail_watches(user_id)
            
            logger.info(f"Google integrations cleaned up for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up Google integrations: {str(e)}")
    
    async def _remove_calendar_webhooks(self, user_id: str) -> None:
        """Remove calendar webhooks for a user."""
        try:
            self.supabase.table("calendar_webhooks") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            
            logger.info(f"Calendar webhooks removed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error removing calendar webhooks: {str(e)}")
    
    async def _remove_drive_file_watches(self, user_id: str) -> None:
        """Remove drive file watches for a user."""
        try:
            # Get user's documents and remove associated watches
            documents = await self._get_user_documents(user_id)
            
            for doc in documents:
                if doc.get('file_id'):
                    self.supabase.table("drive_file_watches") \
                        .delete() \
                        .eq("file_id", doc['file_id']) \
                        .execute()
            
            logger.info(f"Drive file watches removed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error removing drive file watches: {str(e)}")
    
    async def _remove_gmail_watches(self, user_id: str) -> None:
        """Remove Gmail watches for a user."""
        try:
            self.supabase.table("gmail_watches") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            
            logger.info(f"Gmail watches removed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error removing Gmail watches: {str(e)}")
    
    async def _get_user_documents(self, user_id: str) -> list:
        """Get user's documents."""
        try:
            result = self.supabase.table("documents") \
                .select("id, file_id") \
                .eq("created_by", user_id) \
                .not_.is_("file_id", None) \
                .execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting user documents: {str(e)}")
            return []
    
    async def _make_google_request(self, url: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make a request to Google's API."""
        try:
            # Use requests as the primary HTTP client
            import requests
            
            if method.upper() == 'POST':
                response = requests.post(url, data=data or {})
            else:
                response = requests.get(url)
            
            return {
                'status': response.status_code,
                'data': response.text
            }
                
        except Exception as e:
            logger.error(f"Error making Google request: {str(e)}")
            return None
