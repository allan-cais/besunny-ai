"""
Google OAuth service for BeSunny.ai Python backend.
Handles Google OAuth authentication, user creation, and session management.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
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
    token_type: str
    expires_in: int
    scope: str


class UserInfo(BaseModel):
    """Google user information."""
    id: str
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str
    verified_email: bool
    locale: str


class UserSession(BaseModel):
    """User session information."""
    session_id: str
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime


class GoogleOAuthService:
    """Service for Google OAuth authentication and user management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.client_id = self.settings.google_client_id
        self.client_secret = self.settings.google_client_secret
        self.redirect_uri = self.settings.google_login_redirect_uri
        
        # HTTP client for Google API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("Google OAuth Service initialized")
    
    async def handle_oauth_callback(self, code: str) -> Dict[str, Any]:
        """
        Handle OAuth callback with authorization code.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            OAuth callback result
        """
        try:
            logger.info("Processing OAuth callback")
            
            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(code)
            if not tokens:
                return {
                    'success': False,
                    'error': 'Failed to exchange code for tokens'
                }
            
            # Get user information
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                return {
                    'success': False,
                    'error': 'Failed to get user information'
                }
            
            # Create or update user
            user_id = await self._create_or_update_user(user_info, tokens)
            if not user_id:
                return {
                    'success': False,
                    'error': 'Failed to create or update user'
                }
            
            # Create user session
            session = await self._create_user_session(user_id, tokens)
            if not session:
                return {
                    'success': False,
                    'error': 'Failed to create user session'
                }
            
            logger.info(f"OAuth callback completed successfully for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'user_info': user_info.dict(),
                'session': session.dict(),
                'access_token': tokens.access_token
            }
            
        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def exchange_code_for_tokens(self, code: str) -> Optional[OAuthTokens]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            OAuth tokens or None if failed
        """
        try:
            # Prepare token exchange request
            token_data = {
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            # Exchange code for tokens
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data
            )
            response.raise_for_status()
            
            token_response = response.json()
            
            # Create OAuth tokens object
            tokens = OAuthTokens(
                access_token=token_response['access_token'],
                refresh_token=token_response['refresh_token'],
                token_type=token_response['token_type'],
                expires_in=token_response['expires_in'],
                scope=token_response['scope']
            )
            
            logger.info("Successfully exchanged code for tokens")
            return tokens
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error exchanging code for tokens: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[UserInfo]:
        """
        Get user information from Google using access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            User information or None if failed
        """
        try:
            # Get user info from Google
            headers = {'Authorization': f'Bearer {access_token}'}
            response = await self.http_client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers
            )
            response.raise_for_status()
            
            user_data = response.json()
            
            # Create user info object
            user_info = UserInfo(
                id=user_data['id'],
                email=user_data['email'],
                name=user_data['name'],
                given_name=user_data.get('given_name', ''),
                family_name=user_data.get('family_name', ''),
                picture=user_data.get('picture', ''),
                verified_email=user_data.get('verified_email', False),
                locale=user_data.get('locale', 'en')
            )
            
            logger.info(f"Retrieved user info for {user_info.email}")
            return user_info
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting user info: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    async def create_or_update_user(self, user_info: UserInfo, tokens: OAuthTokens) -> Optional[str]:
        """
        Create or update user in database.
        
        Args:
            user_info: Google user information
            tokens: OAuth tokens
            
        Returns:
            User ID or None if failed
        """
        try:
            # Check if user already exists
            existing_user = await self._get_user_by_google_id(user_info.id)
            
            if existing_user:
                # Update existing user
                user_id = await self._update_user(existing_user['id'], user_info, tokens)
                logger.info(f"Updated existing user {user_id}")
            else:
                # Create new user
                user_id = await self._create_user(user_info, tokens)
                logger.info(f"Created new user {user_id}")
            
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to create or update user: {e}")
            return None
    
    async def create_user_session(self, user_id: str, tokens: OAuthTokens) -> Optional[UserSession]:
        """
        Create user session with OAuth tokens.
        
        Args:
            user_id: User ID
            tokens: OAuth tokens
            
        Returns:
            User session or None if failed
        """
        try:
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=tokens.expires_in)
            
            # Create session data
            session_data = {
                'session_id': f"session_{user_id}_{int(datetime.now().timestamp())}",
                'user_id': user_id,
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            # Store session in database
            result = self.supabase.table("user_sessions").insert(session_data).execute()
            
            if result.data:
                session = UserSession(
                    session_id=session_data['session_id'],
                    user_id=user_id,
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    expires_at=expires_at,
                    created_at=datetime.now()
                )
                
                logger.info(f"Created user session {session.session_id}")
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New tokens or None if failed
        """
        try:
            # Prepare token refresh request
            token_data = {
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }
            
            # Refresh access token
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data
            )
            response.raise_for_status()
            
            token_response = response.json()
            
            # Update session with new access token
            await self._update_session_access_token(refresh_token, token_response['access_token'])
            
            logger.info("Successfully refreshed access token")
            
            return {
                'access_token': token_response['access_token'],
                'expires_in': token_response['expires_in'],
                'token_type': token_response['token_type']
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error refreshing access token: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return None
    
    async def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """Clean up expired user sessions."""
        try:
            logger.info("Starting cleanup of expired sessions")
            
            # Get expired sessions
            expired_sessions = await self._get_expired_sessions()
            if not expired_sessions:
                return {
                    'total_sessions': 0,
                    'cleaned_sessions': 0,
                    'message': 'No expired sessions found'
                }
            
            cleaned_count = 0
            
            for session in expired_sessions:
                try:
                    success = await self._delete_session(session['session_id'])
                    if success:
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to delete expired session {session['session_id']}: {e}")
                    continue
            
            logger.info(f"Session cleanup completed: {cleaned_count} cleaned")
            
            return {
                'total_sessions': len(expired_sessions),
                'cleaned_sessions': cleaned_count,
                'success_rate': cleaned_count / len(expired_sessions) if expired_sessions else 0
            }
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            return {
                'error': str(e),
                'total_sessions': 0,
                'cleaned_sessions': 0
            }
    
    async def _get_expired_sessions(self) -> List[Dict[str, Any]]:
        """Get all expired user sessions."""
        try:
            # Get sessions that are expired or will expire soon
            now = datetime.now()
            soon_expiry = now + timedelta(hours=1)  # Sessions expiring within 1 hour
            
            result = self.supabase.table("user_sessions") \
                .select("user_id, session_id, expires_at") \
                .eq("is_active", True) \
                .not_.is_("expires_at", None) \
                .lte("expires_at", soon_expiry.isoformat()) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get expired sessions: {e}")
            return []
    
    async def _get_expired_tokens(self) -> List[Dict[str, Any]]:
        """Get all expired Google OAuth tokens."""
        try:
            # Get tokens that are expired or will expire soon
            now = datetime.now()
            soon_expiry = now + timedelta(hours=1)  # Tokens expiring within 1 hour
            
            result = self.supabase.table("google_credentials") \
                .select("user_id, access_token, created_at, updated_at") \
                .not_.is_("refresh_token", None) \
                .execute()
            
            expired_tokens = []
            for token in result.data:
                # Check if token needs refresh
                # This is a simplified check - in production you'd store expiration time
                updated_at = datetime.fromisoformat(token['updated_at'].replace('Z', '+00:00'))
                if updated_at < now - timedelta(hours=1):  # Assume 1 hour expiration
                    expired_tokens.append(token)
            
            return expired_tokens
            
        except Exception as e:
            logger.error(f"Failed to get expired tokens: {e}")
            return []
    
    async def _delete_session(self, session_id: str) -> bool:
        """Delete a user session."""
        try:
            result = self.supabase.table("user_sessions") \
                .delete() \
                .eq("session_id", session_id) \
                .execute()
            
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate Google access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate token with Google
            headers = {'Authorization': f'Bearer {access_token}'}
            response = await self.http_client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to validate token: {e}")
            return False
    
    async def revoke_tokens(self, user_id: str) -> bool:
        """
        Revoke user's OAuth tokens.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user's refresh token
            refresh_token = await self._get_user_refresh_token(user_id)
            if not refresh_token:
                logger.warning(f"No refresh token found for user {user_id}")
                return False
            
            # Revoke token with Google
            token_data = {'token': refresh_token}
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/revoke',
                data=token_data
            )
            
            if response.status_code == 200:
                # Remove user session
                await self._remove_user_session(user_id)
                
                # Clear user credentials
                await self._clear_user_credentials(user_id)
                
                logger.info(f"Successfully revoked tokens for user {user_id}")
                return True
            else:
                logger.error(f"Failed to revoke tokens: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to revoke tokens: {e}")
            return False
    
    # Private helper methods
    
    async def _get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID."""
        try:
            result = self.supabase.table("users") \
                .select("*") \
                .eq("google_id", google_id) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get user by Google ID: {e}")
            return None
    
    async def _create_user(self, user_info: UserInfo, tokens: OAuthTokens) -> Optional[str]:
        """Create new user."""
        try:
            # Create user data
            user_data = {
                'google_id': user_info.id,
                'email': user_info.email,
                'name': user_info.name,
                'given_name': user_info.given_name,
                'family_name': user_info.family_name,
                'picture': user_info.picture,
                'verified_email': user_info.verified_email,
                'locale': user_info.locale,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert user
            result = self.supabase.table("users").insert(user_data).execute()
            
            if result.data:
                user_id = result.data[0]['id']
                
                # Store Google credentials
                await self._store_google_credentials(user_id, tokens)
                
                return user_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    async def _update_user(self, user_id: str, user_info: UserInfo, tokens: OAuthTokens) -> Optional[str]:
        """Update existing user."""
        try:
            # Update user data
            update_data = {
                'name': user_info.name,
                'given_name': user_info.given_name,
                'family_name': user_info.family_name,
                'picture': user_info.picture,
                'verified_email': user_info.verified_email,
                'locale': user_info.locale,
                'updated_at': datetime.now().isoformat()
            }
            
            # Update user
            result = self.supabase.table("users") \
                .update(update_data) \
                .eq("id", user_id) \
                .execute()
            
            if result.data:
                # Update Google credentials
                await self._update_google_credentials(user_id, tokens)
                
                return user_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return None
    
    async def _store_google_credentials(self, user_id: str, tokens: OAuthTokens):
        """Store Google credentials for user."""
        try:
            credentials_data = {
                'user_id': user_id,
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'token_type': tokens.token_type,
                'expires_in': tokens.expires_in,
                'scope': tokens.scope,
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("google_credentials").upsert(credentials_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store Google credentials: {e}")
    
    async def _update_google_credentials(self, user_id: str, tokens: OAuthTokens):
        """Update Google credentials for user."""
        try:
            update_data = {
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'expires_in': tokens.expires_in,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("google_credentials") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update Google credentials: {e}")
    
    async def _update_session_access_token(self, refresh_token: str, new_access_token: str):
        """Update session with new access token."""
        try:
            update_data = {
                'access_token': new_access_token,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("user_sessions") \
                .update(update_data) \
                .eq("refresh_token", refresh_token) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update session access token: {e}")
    
    async def _get_user_refresh_token(self, user_id: str) -> Optional[str]:
        """Get user's refresh token."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("refresh_token") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data.get('refresh_token') if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get user refresh token: {e}")
            return None
    
    async def _remove_user_session(self, user_id: str):
        """Remove user session."""
        try:
            self.supabase.table("user_sessions") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to remove user session: {e}")
    
    async def _clear_user_credentials(self, user_id: str):
        """Clear user's Google credentials."""
        try:
            self.supabase.table("google_credentials") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to clear user credentials: {e}")
    
    async def get_user_info_from_stored_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Google user information using stored credentials.
        
        Args:
            user_id: User ID to get info for
            
        Returns:
            Google user info or None if failed
        """
        try:
            # Get user's stored credentials
            result = self.supabase.table("google_credentials") \
                .select("access_token") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if not result.data or not result.data.get('access_token'):
                logger.warning(f"No stored credentials found for user {user_id}")
                return None
            
            access_token = result.data['access_token']
            
            # Get user info from Google
            user_info = await self._get_user_info(access_token)
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user info from stored credentials for user {user_id}: {e}")
            return None
    
    async def revoke_user_oauth_tokens(self, user_id: str) -> bool:
        """
        Revoke user's OAuth tokens.
        
        Args:
            user_id: User ID to revoke tokens for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user's stored credentials
            result = self.supabase.table("google_credentials") \
                .select("access_token, refresh_token") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if not result.data:
                logger.warning(f"No stored credentials found for user {user_id}")
                return True  # Consider it successful if no credentials to revoke
            
            access_token = result.data.get('access_token')
            refresh_token = result.data.get('refresh_token')
            
            # Revoke access token if available
            if access_token:
                try:
                    await self._revoke_token(access_token)
                    logger.info(f"Revoked access token for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to revoke access token for user {user_id}: {e}")
            
            # Revoke refresh token if available
            if refresh_token:
                try:
                    await self._revoke_token(refresh_token)
                    logger.info(f"Revoked refresh token for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to revoke refresh token for user {user_id}: {e}")
            
            # Clear stored credentials
            await self._clear_user_credentials(user_id)
            
            # Remove user session
            await self._remove_user_session(user_id)
            
            logger.info(f"Successfully revoked all OAuth tokens for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke OAuth tokens for user {user_id}: {e}")
            return False
    
    async def _revoke_token(self, token: str):
        """
        Revoke a specific token with Google.
        
        Args:
            token: Token to revoke
        """
        try:
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': token}
            )
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Failed to revoke token with Google: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()
