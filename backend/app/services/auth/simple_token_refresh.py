"""
Simple token refresh function.
This actually refreshes Google OAuth tokens when called.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from ...core.supabase_config import get_supabase
from .google_token_service import GoogleTokenService

logger = logging.getLogger(__name__)


async def refresh_expiring_tokens() -> dict:
    """Refresh tokens that are about to expire."""
    try:
        current_time = datetime.utcnow()
        
        logger.info("Starting token refresh for expiring tokens")
        
        # Get Supabase client
        supabase = get_supabase()
        
        # Get ALL tokens that have refresh tokens (refresh them all to be safe)
        result = supabase.table("google_credentials").select("*").execute()
        
        if not result.data:
            logger.info("No Google credentials found")
            return {
                'success': True,
                'message': 'No tokens to refresh',
                'timestamp': current_time.isoformat(),
                'tokens_refreshed': 0
            }
        
        # Get all tokens that have refresh tokens
        tokens_to_refresh = []
        for row in result.data:
            if row.get('refresh_token'):
                tokens_to_refresh.append(row)
        
        if not tokens_to_refresh:
            logger.info("No tokens with refresh tokens found")
            return {
                'success': True,
                'message': 'No tokens with refresh tokens found',
                'timestamp': current_time.isoformat(),
                'tokens_refreshed': 0
            }
        
        logger.info(f"Found {len(tokens_to_refresh)} tokens to refresh")
        
        # Initialize token service
        token_service = GoogleTokenService()
        
        refreshed_count = 0
        failed_count = 0
        
        for token_info in tokens_to_refresh:
            try:
                user_id = token_info['user_id']
                logger.info(f"Refreshing token for user {user_id}")
                
                # Use the token service to refresh
                result = await token_service.refresh_user_tokens(user_id)
                
                if result and result.get('success'):
                    logger.info(f"Successfully refreshed token for user {user_id}")
                    refreshed_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result'
                    logger.warning(f"Token refresh failed for user {user_id}: {error_msg}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error refreshing token for user {token_info.get('user_id', 'unknown')}: {e}")
                failed_count += 1
        
        logger.info(f"Token refresh completed: {refreshed_count} refreshed, {failed_count} failed")
        
        return {
            'success': True,
            'message': f'Refreshed {refreshed_count} tokens, {failed_count} failed',
            'timestamp': current_time.isoformat(),
            'tokens_refreshed': refreshed_count,
            'tokens_failed': failed_count,
            'total_processed': len(tokens_to_refresh)
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Token refresh failed'
        }


async def get_service_status() -> dict:
    """Get the current status."""
    return {
        'is_running': True,
        'last_check': datetime.utcnow().isoformat(),
        'service_type': 'simple_function'
    }
