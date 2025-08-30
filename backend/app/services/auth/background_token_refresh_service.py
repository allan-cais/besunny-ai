"""
Background service for automatic Google OAuth token refresh.
This service runs continuously to ensure tokens are refreshed before they expire.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text

from ...core.supabase_config import get_supabase
from ...core.config import get_settings
from .google_token_service import GoogleTokenService

logger = logging.getLogger(__name__)


class BackgroundTokenRefreshService:
    """Service for automatically refreshing Google OAuth tokens in the background."""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.token_service = GoogleTokenService()
        self.settings = get_settings()
        self.is_running = False
        self.refresh_interval = 300  # Check every 5 minutes
        self.early_refresh_threshold = 600  # Refresh tokens 10 minutes before expiry
        
    async def start(self):
        """Start the background token refresh service."""
        if self.is_running:
            logger.warning("Background token refresh service is already running")
            return
            
        self.is_running = True
        logger.info("Starting background token refresh service")
        
        try:
            while self.is_running:
                await self._refresh_expiring_tokens()
                await asyncio.sleep(self.refresh_interval)
        except Exception as e:
            logger.error(f"Background token refresh service error: {e}")
            self.is_running = False
            raise
        finally:
            self.is_running = False
            logger.info("Background token refresh service stopped")
    
    async def stop(self):
        """Stop the background token refresh service."""
        self.is_running = False
        logger.info("Stopping background token refresh service")
    
    async def run_once(self):
        """Run token refresh once without blocking."""
        try:
            await self._refresh_expiring_tokens()
            return True
        except Exception as e:
            logger.error(f"Single token refresh run failed: {e}")
            return False
    
    async def _refresh_expiring_tokens(self):
        """Refresh tokens that are about to expire."""
        try:
            # Get tokens that will expire within the threshold
            expiring_tokens = await self._get_expiring_tokens()
            
            if not expiring_tokens:
                return
                
            logger.info(f"Found {len(expiring_tokens)} tokens that need refresh")
            
            for token_info in expiring_tokens:
                try:
                    await self._refresh_single_token(token_info)
                except Exception as e:
                    logger.error(f"Failed to refresh token for user {token_info['user_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in _refresh_expiring_tokens: {e}")
    
    async def _get_expiring_tokens(self) -> List[Dict]:
        """Get tokens that will expire within the threshold time."""
        try:
            # Calculate the threshold time
            threshold_time = datetime.utcnow() + timedelta(seconds=self.early_refresh_threshold)
            
            # Query for tokens that will expire soon
            query = text("""
                SELECT user_id, access_token, refresh_token, expires_at, scope
                FROM google_credentials 
                WHERE expires_at <= :threshold_time 
                AND refresh_token IS NOT NULL 
                AND refresh_token != ''
            """)
            
            result = self.supabase.table("google_credentials").select("*").execute()
            
            expiring_tokens = []
            for row in result.data:
                if row.get('expires_at'):
                    expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
                    if expires_at <= threshold_time:
                        expiring_tokens.append(row)
            
            return expiring_tokens
            
        except Exception as e:
            logger.error(f"Error getting expiring tokens: {e}")
            return []
    
    async def _refresh_single_token(self, token_info: Dict):
        """Refresh a single user's token."""
        try:
            user_id = token_info['user_id']
            logger.info(f"Refreshing token for user {user_id}")
            
            # Use the token service to refresh
            result = await self.token_service.refresh_user_tokens(user_id)
            
            if result and result.get('success'):
                logger.info(f"Successfully refreshed token for user {user_id}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result'
                logger.warning(f"Token refresh failed for user {user_id}: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error refreshing token for user {token_info.get('user_id', 'unknown')}: {e}")
    
    async def get_service_status(self) -> Dict:
        """Get the current status of the background service."""
        return {
            'is_running': self.is_running,
            'refresh_interval': self.refresh_interval,
            'early_refresh_threshold': self.early_refresh_threshold,
            'last_check': datetime.utcnow().isoformat()
        }


# Global service instance
_background_service: Optional[BackgroundTokenRefreshService] = None


async def get_background_token_refresh_service() -> BackgroundTokenRefreshService:
    """Get the global background token refresh service instance."""
    global _background_service
    if _background_service is None:
        _background_service = BackgroundTokenRefreshService()
    return _background_service


async def start_background_token_refresh():
    """Start the background token refresh service."""
    service = await get_background_token_refresh_service()
    
    # Start the service as a background task
    async def run_service():
        try:
            await service.start()
        except Exception as e:
            logger.error(f"Background token refresh service error: {e}")
    
    # Return the task so it can be managed by the caller
    return asyncio.create_task(run_service())


async def stop_background_token_refresh():
    """Stop the background token refresh service."""
    global _background_service
    if _background_service:
        await _background_service.stop()
        _background_service = None
