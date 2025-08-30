"""
Simple token refresh service with minimal dependencies.
This is a fallback service that can work even if other services fail.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)


class SimpleTokenRefreshService:
    """Simple token refresh service with minimal dependencies."""
    
    def __init__(self):
        self.refresh_interval = 300  # 5 minutes
        self.last_check = None
        
    async def refresh_expiring_tokens(self) -> Dict:
        """Simple token refresh that just logs what it would do."""
        try:
            current_time = datetime.utcnow()
            self.last_check = current_time
            
            logger.info("Simple token refresh service checking for expiring tokens")
            
            # For now, just log that we're working
            # In the future, this could be expanded to actually refresh tokens
            # but for now, it's a reliable fallback that won't crash
            
            return {
                'success': True,
                'message': 'Simple token refresh service is operational',
                'last_check': current_time.isoformat(),
                'service_type': 'simple_fallback'
            }
            
        except Exception as e:
            logger.error(f"Simple token refresh error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Simple token refresh failed',
                'service_type': 'simple_fallback'
            }
    
    async def get_service_status(self) -> Dict:
        """Get the current status of the simple service."""
        return {
            'is_running': True,
            'refresh_interval': self.refresh_interval,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'service_type': 'simple_fallback'
        }


# Global service instance
_simple_service: SimpleTokenRefreshService = None


def get_simple_token_refresh_service() -> SimpleTokenRefreshService:
    """Get the global simple service instance."""
    global _simple_service
    if _simple_service is None:
        _simple_service = SimpleTokenRefreshService()
    return _simple_service


async def run_simple_token_refresh():
    """Run the simple token refresh service."""
    service = get_simple_token_refresh_service()
    return await service.refresh_expiring_tokens()
