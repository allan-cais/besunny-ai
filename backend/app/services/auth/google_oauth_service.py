"""
Google OAuth service for BeSunny.ai Python backend.
Clean, minimal, and production-ready implementation.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class OAuthTokens(BaseModel):
    """OAuth token information."""
    access_token: str
    refresh_token: str
    expires_in: int


class UserInfo(BaseModel):
    """Google user information."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    verified_email: bool = False


class GoogleOAuthService:
    """Streamlined Google OAuth service for production use."""
    
    def __init__(self):
        self.settings = get_settings()
        # Use service role client to bypass RLS for OAuth operations
        from ...core.supabase_config import get_supabase_service_client
        self.supabase = get_supabase_service_client()
        if not self.supabase:
            # Fallback to regular client if service role not available
            from ...core.supabase_config import get_supabase_client
            self.supabase = get_supabase_client()
            logger.warning("Using regular Supabase client - OAuth operations may fail due to RLS")
        
        self.client_id = self.settings.google_client_id
        self.client_secret = self.settings.google_client_secret
        self.redirect_uri = self.settings.google_login_redirect_uri
        
        # Optimized HTTP client with connection pooling
        self.http_client = httpx.AsyncClient(
            timeout=10.0,  # Reduced timeout for better UX
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
        )
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning("Google OAuth not fully configured")
    
    async def handle_oauth_callback(self, code: str) -> Dict[str, Any]:
        """Handle OAuth callback efficiently."""
        try:
            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(code)
            if not tokens:
                return {'success': False, 'error': 'Token exchange failed'}
            
            # Get user info
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}
            
            # Create/update user and return
            user_id = await self._upsert_user(user_info)
            if not user_id:
                return {'success': False, 'error': 'User creation failed'}
            
            # Store Google credentials in database
            credentials_stored = await self._store_google_credentials(
                user_id, tokens, user_info
            )
            if not credentials_stored:
                logger.warning(f"Failed to store credentials for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'email': user_info.email,
                'name': user_info.name,
                'picture': user_info.picture
            }
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return {'success': False, 'error': 'OAuth processing failed'}
    
    async def handle_workspace_oauth_callback(self, code: str, user_id: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle Google Workspace OAuth callback for extended scopes."""
        try:
            # Exchange code for tokens with workspace scopes using the correct redirect URI
            tokens = await self._exchange_code_for_tokens(code, redirect_uri)
            if not tokens:
                return {'success': False, 'error': 'Token exchange failed'}
            
            # Get user info to verify the account
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}
            
            # Store workspace credentials in database (separate from login credentials)
            credentials_stored = await self._store_workspace_credentials(
                user_id, tokens, user_info
            )
            if not credentials_stored:
                return {'success': False, 'error': 'Failed to store workspace credentials'}
            
            return {
                'success': True,
                'user_id': user_id,
                'email': user_info.email,
                'name': user_info.name,
                'picture': user_info.picture,
                'message': 'Google Workspace connected successfully'
            }
            
        except Exception as e:
            logger.error(f"Workspace OAuth callback error: {e}")
            return {'success': False, 'error': 'Workspace OAuth processing failed'}
    
    async def _exchange_code_for_tokens(self, code: str, redirect_uri: Optional[str] = None) -> Optional[OAuthTokens]:
        """Exchange authorization code for tokens."""
        try:
            # Use provided redirect_uri or fall back to default
            final_redirect_uri = redirect_uri or self.redirect_uri
            
            if not final_redirect_uri:
                logger.error("No redirect URI provided for token exchange")
                return None
            
            logger.info(f"Exchanging OAuth code for tokens with redirect_uri: {final_redirect_uri}")
            
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': final_redirect_uri,
                    'grant_type': 'authorization_code'
                },
                timeout=8.0
            )
            
            if not response.is_success:
                error_text = response.text
                logger.error(f"Google OAuth token exchange failed with status {response.status_code}: {error_text}")
                return None
                
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully exchanged OAuth code for tokens. Scopes: {data.get('scope', 'N/A')}")
            
            return OAuthTokens(
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token', ''),
                expires_in=data.get('expires_in', 3600)
            )
            
        except httpx.TimeoutException:
            logger.error("Token exchange timeout")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token exchange: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return None
    
    async def _get_user_info(self, access_token: str) -> Optional[UserInfo]:
        """Get user info from Google."""
        try:
            response = await self.http_client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=5.0
            )
            response.raise_for_status()
            
            data = response.json()
            return UserInfo(
                id=data['id'],
                email=data['email'],
                name=data.get('name', ''),
                picture=data.get('picture'),
                verified_email=data.get('verified_email', False)
            )
            
        except httpx.TimeoutException:
            logger.error("User info request timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    async def _upsert_user(self, user_info: UserInfo) -> Optional[str]:
        """Create or update user efficiently."""
        try:
            # Check if user exists
            result = self.supabase.table("users").select("id").eq("email", user_info.email).execute()
            
            if result.data:
                # Update existing user
                user_id = result.data[0]['id']
                self.supabase.table("users").update({
                    'name': user_info.name,
                    'created_at': datetime.now().isoformat()
                }).eq("id", user_id).execute()
                return user_id
            else:
                # Create new user
                result = self.supabase.table("users").insert({
                    'id': str(uuid.uuid4()),  # Generate UUID for id
                    'email': user_info.email,
                    'name': user_info.name,
                    'created_at': datetime.now().isoformat()
                }).execute()
                
                if result.data:
                    return result.data[0]['id']
                return None
                
        except Exception as e:
            logger.error(f"User upsert failed: {e}")
            return None
    
    async def _store_google_credentials(self, user_id: str, tokens: OAuthTokens, user_info: UserInfo) -> bool:
        """Store Google OAuth credentials in database."""
        try:
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=tokens.expires_in)
            
            # Prepare credentials data
            credentials_data = {
                'user_id': user_id,
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'token_type': 'Bearer',
                'expires_at': expires_at.isoformat(),
                'scope': 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
                'google_email': user_info.email,
                'google_user_id': user_info.id,
                'google_name': user_info.name,
                'google_picture': user_info.picture,
                'login_provider': True,  # This is a login provider
                'login_created_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if credentials already exist
            existing = self.supabase.table("google_credentials").select("id").eq("user_id", user_id).execute()
            
            if existing.data:
                # Update existing credentials
                self.supabase.table("google_credentials").update(credentials_data).eq("user_id", user_id).execute()
                logger.info(f"Updated Google credentials for user {user_id}")
            else:
                # Insert new credentials
                self.supabase.table("google_credentials").insert(credentials_data).execute()
                logger.info(f"Stored new Google credentials for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store Google credentials for user {user_id}: {e}")
            return False
    
    async def _store_workspace_credentials(self, user_id: str, tokens: OAuthTokens, user_info: UserInfo) -> bool:
        """Store Google Workspace OAuth credentials in database."""
        try:
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=tokens.expires_in)
            
            # Prepare workspace credentials data
            credentials_data = {
                'user_id': user_id,
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'token_type': 'Bearer',
                'expires_at': expires_at.isoformat(),
                'scope': 'https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/calendar',
                'google_email': user_info.email,
                'google_user_id': user_info.id,
                'google_name': user_info.name,
                'google_picture': user_info.picture,
                'login_provider': False,  # This is NOT a login provider, it's workspace integration
                'login_created_at': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if workspace credentials already exist
            existing = self.supabase.table("google_credentials").select("id").eq("user_id", user_id).eq("login_provider", False).execute()
            
            if existing.data:
                # Update existing workspace credentials
                self.supabase.table("google_credentials").update(credentials_data).eq("user_id", user_id).eq("login_provider", False).execute()
                logger.info(f"Updated Google workspace credentials for user {user_id}")
            else:
                # Insert new workspace credentials
                self.supabase.table("google_credentials").insert(credentials_data).execute()
                logger.info(f"Stored new Google workspace credentials for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store Google workspace credentials for user {user_id}: {e}")
            return False
    
    async def close(self):
        """Clean up HTTP client."""
        await self.http_client.aclose()
