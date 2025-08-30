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
        
        # Get tokens that will expire within the next 15 minutes
        threshold_time = current_time + timedelta(minutes=15)
        
        # Query for tokens that will expire soon
        result = supabase.table("google_credentials").select("*").execute()
        
        if not result.data:
            logger.info("No Google credentials found")
            return {
                'success': True,
                'message': 'No tokens to refresh',
                'timestamp': current_time.isoformat(),
                'tokens_refreshed': 0
            }
        
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
        
        if not expiring_tokens:
            logger.info("No tokens need refresh at this time")
            return {
                'success': True,
                'message': 'No tokens need refresh',
                'timestamp': current_time.isoformat(),
                'tokens_refreshed': 0
            }
        
        logger.info(f"Found {len(expiring_tokens)} tokens that need refresh")
        
        # Initialize token service
        token_service = GoogleTokenService()
        
        refreshed_count = 0
        failed_count = 0
        
        for token_info in expiring_tokens:
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
            'total_processed': len(expiring_tokens)
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
