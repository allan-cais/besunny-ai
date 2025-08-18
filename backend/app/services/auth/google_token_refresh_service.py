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
            update_data = {
                'access_token': new_tokens['access_token'],
                'expires_in': new_tokens['expires_in'],
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("google_credentials") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update credentials for user {user_id}: {e}")
    
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
            soon_expiry = now + timedelta(hours=1)  # Refresh tokens expiring within 1 hour
            
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
