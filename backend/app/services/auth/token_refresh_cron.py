"""
Cron-based token refresh service for Google OAuth tokens.
This service runs on a schedule to refresh tokens before they expire.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from ...core.supabase_config import get_supabase
from .google_token_service import GoogleTokenService

logger = logging.getLogger(__name__)


class TokenRefreshCronService:
    """Cron-based service for refreshing Google OAuth tokens."""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.token_service = GoogleTokenService()
        
    async def refresh_expiring_tokens(self):
        """Refresh tokens that are about to expire (called by cron)."""
        try:
            logger.info("Starting scheduled token refresh")
            
            # Get tokens that will expire within the next 15 minutes
            expiring_tokens = await self._get_expiring_tokens()
            
            if not expiring_tokens:
                logger.info("No tokens need refresh at this time")
                return {
                    'success': True,
                    'tokens_refreshed': 0,
                    'message': 'No tokens need refresh'
                }
            
            logger.info(f"Found {len(expiring_tokens)} tokens that need refresh")
            
            refreshed_count = 0
            failed_count = 0
            
            for token_info in expiring_tokens:
                try:
                    success = await self._refresh_single_token(token_info)
                    if success:
                        refreshed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to refresh token for user {token_info['user_id']}: {e}")
                    failed_count += 1
            
            logger.info(f"Token refresh completed: {refreshed_count} refreshed, {failed_count} failed")
            
            return {
                'success': True,
                'tokens_refreshed': refreshed_count,
                'tokens_failed': failed_count,
                'total_processed': len(expiring_tokens),
                'message': f'Refreshed {refreshed_count} tokens, {failed_count} failed'
            }
            
        except Exception as e:
            logger.error(f"Error in scheduled token refresh: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Token refresh failed'
            }
    
    async def _get_expiring_tokens(self) -> List[Dict]:
        """Get tokens that will expire within the next 15 minutes."""
        try:
            # Calculate the threshold time (15 minutes from now)
            threshold_time = datetime.utcnow() + timedelta(minutes=15)
            
            # Query for tokens that will expire soon
            result = self.supabase.table("google_credentials").select("*").execute()
            
            expiring_tokens = []
            for row in result.data:
                if row.get('expires_at') and row.get('refresh_token'):
                    try:
                        expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
                        if expires_at <= threshold_time:
                            expiring_tokens.append(row)
                    except (ValueError, TypeError):
                        # Skip rows with invalid date format
                        continue
            
            return expiring_tokens
            
        except Exception as e:
            logger.error(f"Error getting expiring tokens: {e}")
            return []
    
    async def _refresh_single_token(self, token_info: Dict) -> bool:
        """Refresh a single user's token."""
        try:
            user_id = token_info['user_id']
            logger.info(f"Refreshing token for user {user_id}")
            
            # Use the token service to refresh
            result = await self.token_service.refresh_user_tokens(user_id)
            
            if result and result.get('success'):
                logger.info(f"Successfully refreshed token for user {user_id}")
                return True
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result'
                logger.warning(f"Token refresh failed for user {user_id}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing token for user {token_info.get('user_id', 'unknown')}: {e}")
            return False
    
    async def get_service_stats(self) -> Dict:
        """Get statistics about the token refresh service."""
        try:
            # Get total tokens
            result = self.supabase.table("google_credentials").select("user_id, expires_at").execute()
            total_tokens = len(result.data) if result.data else 0
            
            # Get expiring tokens
            expiring_tokens = await self._get_expiring_tokens()
            expiring_count = len(expiring_tokens)
            
            return {
                'total_tokens': total_tokens,
                'expiring_soon': expiring_count,
                'last_check': datetime.utcnow().isoformat(),
                'service_type': 'cron'
            }
            
        except Exception as e:
            logger.error(f"Error getting service stats: {e}")
            return {
                'error': str(e),
                'service_type': 'cron'
            }


# Global service instance
_cron_service: TokenRefreshCronService = None


def get_token_refresh_cron_service() -> TokenRefreshCronService:
    """Get the global cron service instance."""
    global _cron_service
    if _cron_service is None:
        _cron_service = TokenRefreshCronService()
    return _cron_service


async def run_token_refresh_cron():
    """Run the token refresh cron job."""
    service = get_token_refresh_cron_service()
    return await service.refresh_expiring_tokens()
