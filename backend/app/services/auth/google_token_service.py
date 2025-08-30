"""
Google token service for BeSunny.ai Python backend.
Handles Google token refresh, exchange, and validation.
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


class TokenRefreshResult(BaseModel):
    """Result of token refresh operation."""
    user_id: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime


class TokenValidationResult(BaseModel):
    """Result of token validation operation."""
    token: str
    is_valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    timestamp: datetime


class GoogleTokenService:
    """Service for Google token management and operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.client_id = self.settings.google_client_id
        self.client_secret = self.settings.google_client_secret
        
        # HTTP client for Google API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("Google Token Service initialized")
    
    async def exchange_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Exchange refresh token for new access token.
        
        Args:
            refresh_token: Refresh token to exchange
            
        Returns:
            New token information or None if failed
        """
        try:
            # Prepare token exchange request
            token_data = {
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }
            
            # Exchange refresh token for new access token
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data
            )
            response.raise_for_status()
            
            token_response = response.json()
            
            logger.info("Successfully exchanged refresh token for new access token")
            
            return {
                'access_token': token_response['access_token'],
                'expires_in': token_response['expires_in'],
                'token_type': token_response['token_type'],
                'scope': token_response.get('scope', '')
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error exchanging token: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to exchange token: {e}")
            return None
    
    async def refresh_user_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Refresh tokens for a specific user.
        
        Args:
            user_id: User ID to refresh tokens for
            
        Returns:
            Token refresh result or None if failed
        """
        try:
            # Get user's refresh token
            refresh_token = await self._get_user_refresh_token(user_id)
            if not refresh_token:
                return {
                    'success': False,
                    'error': 'No refresh token found for user'
                }
            
            # Exchange refresh token
            new_tokens = await self.exchange_token(refresh_token)
            if not new_tokens:
                return {
                    'success': False,
                    'error': 'Failed to exchange refresh token'
                }
            
            # Update user's tokens in database
            update_success = await self._update_user_tokens(
                user_id, 
                new_tokens['access_token'], 
                refresh_token,
                new_tokens['expires_in']
            )
            
            if not update_success:
                return {
                    'success': False,
                    'error': 'Failed to update user tokens'
                }
            
            # Update user sessions
            await self._update_user_sessions(user_id, new_tokens['access_token'])
            
            logger.info(f"Successfully refreshed tokens for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'access_token': new_tokens['access_token'],
                'expires_in': new_tokens['expires_in'],
                'token_type': new_tokens['token_type']
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh user tokens: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a Google access token.
        
        Args:
            access_token: Access token to validate
            
        Returns:
            Token validation result or None if failed
        """
        try:
            # First try to get token info
            token_info_response = await self.http_client.get(
                'https://www.googleapis.com/oauth2/v2/tokeninfo',
                params={'access_token': access_token}
            )
            
            if token_info_response.status_code == 200:
                token_info = token_info_response.json()
                return {
                    'is_valid': True,
                    'user_id': token_info.get('user_id'),
                    'expires_at': None,  # Token info doesn't include expiration
                    'scope': token_info.get('scope'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # If token info fails, try to get user info
            user_info_response = await self.http_client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                return {
                    'is_valid': True,
                    'user_id': user_info.get('id'),
                    'expires_at': None,
                    'scope': None,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Token is invalid
            return {
                'is_valid': False,
                'user_id': None,
                'expires_at': None,
                'error_message': 'Token validation failed',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate token: {e}")
            return {
                'is_valid': False,
                'user_id': None,
                'expires_at': None,
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def validate_user_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate Google OAuth tokens for a specific user.
        
        Args:
            user_id: User ID to validate tokens for
            
        Returns:
            Token validation result or None if failed
        """
        try:
            # Get user's stored access token
            result = self.supabase.table("google_credentials") \
                .select("access_token") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if not result.data or not result.data.get('access_token'):
                return {
                    'is_valid': False,
                    'user_id': user_id,
                    'error_message': 'No access token found',
                    'timestamp': datetime.now().isoformat()
                }
            
            access_token = result.data['access_token']
            
            # Validate the token
            validation_result = await self.validate_token(access_token)
            if validation_result:
                validation_result['user_id'] = user_id
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate user tokens for user {user_id}: {e}")
            return {
                'is_valid': False,
                'user_id': user_id,
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def revoke_tokens(self, user_id: str) -> bool:
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User ID to revoke tokens for
            
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
                # Clear user credentials
                await self._clear_user_credentials(user_id)
                
                # Remove user sessions
                await self._remove_user_sessions(user_id)
                
                logger.info(f"Successfully revoked tokens for user {user_id}")
                return True
            else:
                logger.error(f"Failed to revoke tokens: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to revoke tokens: {e}")
            return False
    
    async def get_token_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            Token information or None if failed
        """
        try:
            # Get token info from Google
            headers = {'Authorization': f'Bearer {access_token}'}
            response = await self.http_client.get(
                'https://www.googleapis.com/oauth2/v2/tokeninfo',
                headers=headers
            )
            
            if response.status_code == 200:
                token_info = response.json()
                
                # Add user info if available
                user_response = await self.http_client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers=headers
                )
                
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    token_info['user_info'] = user_info
                
                return token_info
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None
    
    async def batch_refresh_expired_tokens(self) -> Dict[str, Any]:
        """
        Refresh all expired tokens in batch.
        
        Returns:
            Batch refresh results
        """
        try:
            # Get all expired tokens
            expired_tokens = await self._get_expired_tokens()
            
            if not expired_tokens:
                return {
                    'total_tokens': 0,
                    'refreshed_tokens': 0,
                    'failed_tokens': 0,
                    'message': 'No expired tokens found'
                }
            
            refreshed_count = 0
            failed_count = 0
            
            for token_info in expired_tokens:
                try:
                    result = await self.refresh_user_tokens(token_info['user_id'])
                    if result and result.get('success'):
                        refreshed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to refresh token for user {token_info['user_id']}: {e}")
                    failed_count += 1
                    continue
            
            logger.info(f"Batch token refresh completed: {refreshed_count} refreshed, {failed_count} failed")
            
            return {
                'total_tokens': len(expired_tokens),
                'refreshed_tokens': refreshed_count,
                'failed_tokens': failed_count,
                'success_rate': refreshed_count / len(expired_tokens) if expired_tokens else 0
            }
            
        except Exception as e:
            logger.error(f"Batch token refresh failed: {e}")
            return {
                'error': str(e),
                'total_tokens': 0,
                'refreshed_tokens': 0,
                'failed_tokens': 0
            }
    
    # Private helper methods
    
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
    
    async def _update_user_tokens(self, user_id: str, access_token: str, 
                                refresh_token: str, expires_in: int) -> bool:
        """Update user's tokens in database."""
        try:
            # Calculate the actual expiration timestamp
            from datetime import datetime, timedelta
            expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            
            update_data = {
                'access_token': access_token,
                'expires_in': expires_in,
                'expires_at': expires_at,  # Add the missing expires_at field
            }
            
            logger.info(f"Attempting to update tokens for user {user_id}")
            logger.info(f"Update data: {update_data}")
            
            result = self.supabase.table("google_credentials") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()
            
            logger.info(f"Updated tokens for user {user_id}, expires_at: {expires_at}")
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Failed to update user tokens: {e}")
            return False
    
    async def refresh_expired_tokens(self) -> Dict[str, Any]:
        """Refresh all expired tokens."""
        return await self.batch_refresh_expired_tokens()
    
    async def validate_all_tokens(self) -> Dict[str, Any]:
        """Validate all Google tokens and mark invalid ones."""
        try:
            logger.info("Starting validation of all Google tokens")
            
            # Get all tokens
            all_tokens = await self._get_all_tokens()
            if not all_tokens:
                return {
                    'total_tokens': 0,
                    'valid_tokens': 0,
                    'invalid_tokens': 0,
                    'message': 'No tokens found'
                }
            
            valid_count = 0
            invalid_count = 0
            
            for token_info in all_tokens:
                try:
                    is_valid = await self.validate_token(token_info['access_token'])
                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        # Mark token as invalid
                        await self._mark_token_invalid(token_info['user_id'])
                        
                except Exception as e:
                    logger.error(f"Failed to validate token for user {token_info['user_id']}: {e}")
                    invalid_count += 1
                    continue
            
            logger.info(f"Token validation completed: {valid_count} valid, {invalid_count} invalid")
            
            return {
                'total_tokens': len(all_tokens),
                'valid_tokens': valid_count,
                'invalid_tokens': invalid_count,
                'success_rate': valid_count / len(all_tokens) if all_tokens else 0
            }
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return {
                'error': str(e),
                'total_tokens': 0,
                'valid_tokens': 0,
                'invalid_tokens': 0
            }
    
    async def revoke_expired_tokens(self) -> Dict[str, Any]:
        """Revoke expired and invalid Google tokens."""
        try:
            logger.info("Starting revocation of expired tokens")
            
            # Get expired tokens
            expired_tokens = await self._get_expired_tokens()
            if not expired_tokens:
                return {
                    'total_tokens': 0,
                    'revoked_tokens': 0,
                    'message': 'No expired tokens found'
                }
            
            revoked_count = 0
            
            for token_info in expired_tokens:
                try:
                    success = await self.revoke_tokens(token_info['user_id'])
                    if success:
                        revoked_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to revoke token for user {token_info['user_id']}: {e}")
                    continue
            
            logger.info(f"Token revocation completed: {revoked_count} revoked")
            
            return {
                'total_tokens': len(expired_tokens),
                'revoked_tokens': revoked_count,
                'success_rate': revoked_count / len(expired_tokens) if expired_tokens else 0
            }
            
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return {
                'error': str(e),
                'total_tokens': 0,
                'revoked_tokens': 0
            }
    
    async def _get_all_tokens(self) -> List[Dict[str, Any]]:
        """Get all Google tokens."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("user_id, access_token") \
                .not_.is_("access_token", None) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get all tokens: {e}")
            return []
    
    async def _mark_token_invalid(self, user_id: str):
        """Mark a token as invalid."""
        try:
            self.supabase.table("google_credentials") \
                .update({
                    'access_token': None,
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to mark token invalid for user {user_id}: {e}")
    
    async def _update_user_sessions(self, user_id: str, new_access_token: str):
        """Update user sessions with new access token."""
        try:
            update_data = {
                'access_token': new_access_token,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("user_sessions") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update user sessions: {e}")
    
    async def _clear_user_credentials(self, user_id: str):
        """Clear user's Google credentials."""
        try:
            self.supabase.table("google_credentials") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to clear user credentials: {e}")
    
    async def _remove_user_sessions(self, user_id: str):
        """Remove user sessions."""
        try:
            self.supabase.table("user_sessions") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to remove user sessions: {e}")
    
    async def _get_expired_tokens(self) -> List[Dict[str, Any]]:
        """Get all expired tokens."""
        try:
            # Get tokens that are expired or will expire soon
            now = datetime.now()
            soon_expiry = now + timedelta(hours=1)  # Refresh tokens expiring within 1 hour
            
            result = self.supabase.table("google_credentials") \
                .select("user_id, access_token, created_at") \
                .execute()
            
            expired_tokens = []
            for token in result.data:
                # Check if token is expired or will expire soon
                # This is a simplified check - in production you'd store expiration time
                created_at = datetime.fromisoformat(token['created_at'].replace('Z', '+00:00'))
                if created_at < now - timedelta(hours=1):  # Assume 1 hour expiration
                    expired_tokens.append(token)
            
            return expired_tokens
            
        except Exception as e:
            logger.error(f"Failed to get expired tokens: {e}")
            return []
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()
