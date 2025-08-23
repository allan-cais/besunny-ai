"""
Google token refresh service for BeSunny.ai Python backend.
Handles automated Google token refresh and management.
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
    success: bool
    new_access_token: Optional[str] = None
    expires_in: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime


class BatchRefreshResult(BaseModel):
    """Result of batch token refresh operation."""
    total_users: int
    successful_refreshes: int
    failed_refreshes: int
    results: List[TokenRefreshResult]
    timestamp: datetime


class GoogleTokenRefreshService:
    """Service for automated Google token refresh and management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.client_id = self.settings.google_client_id
        self.client_secret = self.settings.google_client_secret
        
        # HTTP client for Google API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("Google Token Refresh Service initialized")
    
    async def refresh_user_token(self, user_id: str) -> Optional[TokenRefreshResult]:
        """
        Refresh Google OAuth tokens for a specific user.
        
        Args:
            user_id: User ID to refresh tokens for
            
        Returns:
            Token refresh result or None if failed
        """
        try:
            logger.info(f"Refreshing tokens for user {user_id}")
            
            # Get user's stored refresh token
            refresh_token = await self._get_user_refresh_token(user_id)
            if not refresh_token:
                return TokenRefreshResult(
                    user_id=user_id,
                    success=False,
                    error_message="No refresh token found",
                    timestamp=datetime.now()
                )
            
            # Exchange refresh token for new access token
            new_tokens = await self._exchange_refresh_token(refresh_token)
            if not new_tokens:
                return TokenRefreshResult(
                    user_id=user_id,
                    success=False,
                    error_message="Failed to exchange refresh token",
                    timestamp=datetime.now()
                )
            
            # Update stored credentials
            await self._update_user_credentials(user_id, new_tokens)
            
            # Update user sessions
            await self._update_user_sessions(user_id, new_tokens['access_token'])
            
            logger.info(f"Successfully refreshed tokens for user {user_id}")
            
            return TokenRefreshResult(
                user_id=user_id,
                success=True,
                new_access_token=new_tokens['access_token'],
                expires_in=new_tokens['expires_in'],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to refresh tokens for user {user_id}: {e}")
            return TokenRefreshResult(
                user_id=user_id,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def refresh_expired_tokens(self) -> BatchRefreshResult:
        """
        Refresh all expired Google OAuth tokens.
        
        Returns:
            Batch refresh result with summary
        """
        try:
            logger.info("Starting batch token refresh for expired tokens")
            
            # Get all users with expired tokens
            expired_tokens = await self._get_expired_tokens()
            
            if not expired_tokens:
                logger.info("No expired tokens found")
                return BatchRefreshResult(
                    total_users=0,
                    successful_refreshes=0,
                    failed_refreshes=0,
                    results=[],
                    timestamp=datetime.now()
                )
            
            logger.info(f"Found {len(expired_tokens)} users with expired tokens")
            
            # Refresh tokens for each user
            results = []
            successful = 0
            failed = 0
            
            for token_info in expired_tokens:
                user_id = token_info['user_id']
                result = await self.refresh_user_token(user_id)
                results.append(result)
                
                if result.success:
                    successful += 1
                else:
                    failed += 1
                
                # Small delay to avoid overwhelming Google's API
                await asyncio.sleep(0.1)
            
            logger.info(f"Batch token refresh completed: {successful} successful, {failed} failed")
            
            return BatchRefreshResult(
                total_users=len(expired_tokens),
                successful_refreshes=successful,
                failed_refreshes=failed,
                results=results,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Batch token refresh failed: {e}")
            return BatchRefreshResult(
                total_users=0,
                successful_refreshes=0,
                failed_refreshes=1,
                results=[],
                timestamp=datetime.now()
            )
    
    async def refresh_expiring_tokens(self, minutes_before_expiry: int = 15) -> BatchRefreshResult:
        """
        Proactively refresh tokens that are about to expire.
        
        Args:
            minutes_before_expiry: How many minutes before expiry to refresh tokens
            
        Returns:
            Batch refresh result with summary
        """
        try:
            logger.info(f"Starting proactive token refresh for tokens expiring within {minutes_before_expiry} minutes")
            
            # Get tokens that will expire soon
            now = datetime.now()
            soon_expiry = now + timedelta(minutes=minutes_before_expiry)
            
            result = self.supabase.table("google_credentials") \
                .select("user_id, access_token, refresh_token, expires_at") \
                .not_.is_("refresh_token", None) \
                .not_.is_("access_token", None) \
                .not_.is_("expires_at", None) \
                .execute()
            
            expiring_tokens = []
            for token in result.data:
                try:
                    expires_at = token['expires_at']
                    if isinstance(expires_at, str):
                        expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    else:
                        expires_datetime = expires_at
                    
                    # Check if token expires within the specified time
                    if now < expires_datetime <= soon_expiry:
                        expiring_tokens.append(token)
                        logger.info(f"Token for user {token['user_id']} expires at {expires_at}, will refresh proactively")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse expiration time for user {token['user_id']}: {e}")
            
            if not expiring_tokens:
                logger.info("No tokens need proactive refresh")
                return BatchRefreshResult(
                    total_users=0,
                    successful_refreshes=0,
                    failed_refreshes=0,
                    results=[],
                    timestamp=datetime.now()
                )
            
            logger.info(f"Found {len(expiring_tokens)} tokens that need proactive refresh")
            
            # Refresh tokens for each user
            results = []
            successful = 0
            failed = 0
            
            for token_info in expiring_tokens:
                user_id = token_info['user_id']
                result = await self.refresh_user_token(user_id)
                results.append(result)
                
                if result.success:
                    successful += 1
                else:
                    failed += 1
                
                # Small delay to avoid overwhelming Google's API
                await asyncio.sleep(0.1)
            
            logger.info(f"Proactive token refresh completed: {successful} successful, {failed} failed")
            
            return BatchRefreshResult(
                total_users=len(expiring_tokens),
                successful_refreshes=successful,
                failed_refreshes=failed,
                results=results,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Proactive token refresh failed: {e}")
            return BatchRefreshResult(
                total_users=0,
                successful_refreshes=0,
                failed_refreshes=1,
                results=[],
                timestamp=datetime.now()
            )

    async def get_token_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get the current status of a user's Google OAuth tokens.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Token status information
        """
        try:
            result = self.supabase.table("google_credentials") \
                .select("access_token, refresh_token, expires_at, expires_in, updated_at") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if not result.data:
                return {
                    'user_id': user_id,
                    'has_tokens': False,
                    'status': 'no_credentials'
                }
            
            token_data = result.data
            now = datetime.now()
            
            # Check if access token exists
            if not token_data.get('access_token'):
                return {
                    'user_id': user_id,
                    'has_tokens': False,
                    'status': 'no_access_token'
                }
            
            # Check if refresh token exists
            if not token_data.get('refresh_token'):
                return {
                    'user_id': user_id,
                    'has_tokens': True,
                    'status': 'no_refresh_token',
                    'can_refresh': False
                }
            
            # Check expiration
            expires_at = token_data.get('expires_at')
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    else:
                        expires_datetime = expires_at
                    
                    time_until_expiry = expires_datetime - now
                    minutes_until_expiry = time_until_expiry.total_seconds() / 60
                    
                    if expires_datetime <= now:
                        status = 'expired'
                        can_refresh = True
                    elif minutes_until_expiry <= 15:
                        status = 'expiring_soon'
                        can_refresh = True
                    else:
                        status = 'valid'
                        can_refresh = True
                    
                    return {
                        'user_id': user_id,
                        'has_tokens': True,
                        'status': status,
                        'can_refresh': can_refresh,
                        'expires_at': expires_at,
                        'minutes_until_expiry': int(minutes_until_expiry),
                        'updated_at': token_data.get('updated_at')
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to parse expiration time for user {user_id}: {e}")
                    return {
                        'user_id': user_id,
                        'has_tokens': True,
                        'status': 'unknown_expiration',
                        'can_refresh': True,
                        'updated_at': token_data.get('updated_at')
                    }
            
            # Fallback if no expires_at field
            return {
                'user_id': user_id,
                'has_tokens': True,
                'status': 'unknown_expiration',
                'can_refresh': True,
                'updated_at': token_data.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"Failed to get token status for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'has_tokens': False,
                'status': 'error',
                'error': str(e)
            }
    
    async def handle_refresh_results(self, results: List[TokenRefreshResult]) -> Dict[str, Any]:
        """
        Process and handle token refresh results.
        
        Args:
            results: List of token refresh results
            
        Returns:
            Summary of refresh operations
        """
        try:
            total = len(results)
            successful = sum(1 for r in results if r.success)
            failed = total - successful
            
            # Log failed refreshes for investigation
            failed_refreshes = [r for r in results if not r.success]
            if failed_refreshes:
                logger.warning(f"Token refresh failed for {len(failed_refreshes)} users")
                for failed in failed_refreshes:
                    logger.warning(f"User {failed.user_id}: {failed.error_message}")
            
            # Update metrics
            await self._update_refresh_metrics(successful, failed)
            
            return {
                'total_refreshes': total,
                'successful_refreshes': successful,
                'failed_refreshes': failed,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to handle refresh results: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_user_refresh_token(self, user_id: str) -> Optional[str]:
        """Get user's stored refresh token."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("refresh_token") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data.get('refresh_token') if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get refresh token for user {user_id}: {e}")
            return None
    
    async def _exchange_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Exchange refresh token for new access token."""
        try:
            token_data = {
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }
            
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data
            )
            response.raise_for_status()
            
            token_response = response.json()
            
            return {
                'access_token': token_response['access_token'],
                'expires_in': token_response['expires_in'],
                'token_type': token_response['token_type'],
                'scope': token_response.get('scope', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to exchange refresh token: {e}")
            return None
    
    async def _update_user_credentials(self, user_id: str, new_tokens: Dict[str, Any]):
        """Update user's stored Google credentials."""
        try:
            # Calculate new expiration time
            expires_in = new_tokens.get('expires_in', 3600)  # Default to 1 hour
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            update_data = {
                'access_token': new_tokens['access_token'],
                'expires_in': expires_in,
                'expires_at': expires_at.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Updating credentials for user {user_id} - expires at {expires_at.isoformat()}")
            
            result = self.supabase.table("google_credentials") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info(f"Successfully updated credentials for user {user_id}")
            else:
                logger.warning(f"No rows updated for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update credentials for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
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
            logger.error(f"Failed to update sessions for user {user_id}: {e}")
    
    async def _get_expired_tokens(self) -> List[Dict[str, Any]]:
        """Get all expired tokens that need refresh."""
        try:
            # Get tokens that are expired or will expire soon
            now = datetime.now()
            soon_expiry = now + timedelta(minutes=15)  # Refresh tokens expiring within 15 minutes
            
            # Query for tokens that need refresh
            result = self.supabase.table("google_credentials") \
                .select("user_id, access_token, refresh_token, expires_at, expires_in, updated_at") \
                .not_.is_("refresh_token", None) \
                .not_.is_("access_token", None) \
                .execute()
            
            expired_tokens = []
            for token in result.data:
                user_id = token['user_id']
                expires_at = token.get('expires_at')
                updated_at = token.get('updated_at')
                
                # Check if token needs refresh based on expires_at field
                if expires_at:
                    try:
                        # Parse the expiration time
                        if isinstance(expires_at, str):
                            expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        else:
                            expires_datetime = expires_at
                        
                        # Check if token is expired or will expire soon
                        if expires_datetime <= soon_expiry:
                            expired_tokens.append({
                                'user_id': user_id,
                                'expires_at': expires_at,
                                'updated_at': updated_at
                            })
                            logger.info(f"Token for user {user_id} expires at {expires_at}, will refresh")
                            
                    except Exception as e:
                        logger.warning(f"Failed to parse expiration time for user {user_id}: {e}")
                        # Fallback to time-based check
                        if updated_at:
                            try:
                                updated_datetime = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                                # Assume 1 hour expiration if we can't parse expires_at
                                if updated_datetime < now - timedelta(hours=1):
                                    expired_tokens.append({
                                        'user_id': user_id,
                                        'expires_at': expires_at,
                                        'updated_at': updated_at
                                    })
                                    logger.info(f"Token for user {user_id} marked for refresh (fallback method)")
                            except Exception as parse_error:
                                logger.error(f"Failed to parse updated_at for user {user_id}: {parse_error}")
                
                # Fallback: if no expires_at field, use updated_at with assumed expiration
                elif updated_at:
                    try:
                        updated_datetime = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        # Assume 1 hour expiration
                        if updated_datetime < now - timedelta(hours=1):
                            expired_tokens.append({
                                'user_id': user_id,
                                'expires_at': None,
                                'updated_at': updated_at
                            })
                            logger.info(f"Token for user {user_id} marked for refresh (no expires_at field)")
                    except Exception as parse_error:
                        logger.error(f"Failed to parse updated_at for user {user_id}: {parse_error}")
            
            logger.info(f"Found {len(expired_tokens)} tokens that need refresh")
            return expired_tokens
            
        except Exception as e:
            logger.error(f"Failed to get expired tokens: {e}")
            return []
    
    async def _update_refresh_metrics(self, successful: int, failed: int):
        """Update token refresh performance metrics."""
        try:
            # This could be stored in a metrics table or sent to monitoring system
            logger.info(f"Token refresh metrics: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Failed to update refresh metrics: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()
