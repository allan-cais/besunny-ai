"""
Celery tasks for authentication services.
Handles background token refresh, validation, and cleanup operations.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from celery import shared_task

from .google_oauth_service import GoogleOAuthService
from .google_token_service import GoogleTokenService
from .google_token_refresh_service import GoogleTokenRefreshService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="auth.refresh_google_tokens")
def refresh_google_tokens(self, user_id: str = None) -> Dict[str, Any]:
    """
    Refresh Google OAuth tokens for a user or all users.
    
    Args:
        user_id: Specific user ID to refresh, or None for all users
        
    Returns:
        Refresh operation result
    """
    try:
        logger.info(f"Starting Google token refresh task for user: {user_id or 'all'}")
        
        async def _refresh_tokens():
            service = GoogleTokenRefreshService()
            
            if user_id:
                # Refresh tokens for specific user
                result = await service.refresh_user_token(user_id)
                if result:
                    return {
                        'success': True,
                        'user_id': user_id,
                        'result': result.dict() if hasattr(result, 'dict') else result,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'user_id': user_id,
                        'error': 'Failed to refresh tokens',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                # Refresh all expired tokens
                batch_result = await service.refresh_expired_tokens()
                return {
                    'success': True,
                    'batch_result': batch_result.dict() if hasattr(batch_result, 'dict') else batch_result,
                    'timestamp': datetime.now().isoformat()
                }
        
        # Run the async function
        result = asyncio.run(_refresh_tokens())
        
        logger.info(f"Google token refresh task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Google token refresh task failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, name="auth.validate_google_tokens")
def validate_google_tokens(self, user_id: str = None) -> Dict[str, Any]:
    """
    Validate Google OAuth tokens for a user or all users.
    
    Args:
        user_id: Specific user ID to validate, or None for all users
        
    Returns:
        Validation operation result
    """
    try:
        logger.info(f"Starting Google token validation task for user: {user_id or 'all'}")
        
        async def _validate_tokens():
            service = GoogleTokenService()
            
            if user_id:
                # Validate tokens for specific user
                # Get user's access token first
                result = await service.validate_user_tokens(user_id)
                return {
                    'success': True,
                    'user_id': user_id,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Validate all tokens
                all_tokens = await service._get_all_tokens()
                validation_results = []
                
                for token_info in all_tokens:
                    user_id = token_info['user_id']
                    access_token = token_info['access_token']
                    
                    if access_token:
                        validation_result = await service.validate_token(access_token)
                        validation_results.append({
                            'user_id': user_id,
                            'validation': validation_result
                        })
                
                return {
                    'success': True,
                    'total_tokens': len(all_tokens),
                    'validation_results': validation_results,
                    'timestamp': datetime.now().isoformat()
                }
        
        # Run the async function
        result = asyncio.run(_validate_tokens())
        
        logger.info(f"Google token validation task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Google token validation task failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, name="auth.cleanup_expired_sessions")
def cleanup_expired_sessions(self) -> Dict[str, Any]:
    """
    Clean up expired user sessions.
    
    Returns:
        Cleanup operation result
    """
    try:
        logger.info("Starting expired session cleanup task")
        
        async def _cleanup_sessions():
            service = GoogleOAuthService()
            
            # Get expired sessions
            expired_sessions = await service._get_expired_sessions()
            
            if not expired_sessions:
                return {
                    'success': True,
                    'message': 'No expired sessions found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Clean up expired sessions
            cleaned_count = 0
            for session in expired_sessions:
                try:
                    await service._remove_user_session(session['user_id'])
                    cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up session for user {session['user_id']}: {e}")
            
            return {
                'success': True,
                'total_expired': len(expired_sessions),
                'cleaned_count': cleaned_count,
                'timestamp': datetime.now().isoformat()
            }
        
        # Run the async function
        result = asyncio.run(_cleanup_sessions())
        
        logger.info(f"Expired session cleanup task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Expired session cleanup task failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, name="auth.revoke_expired_tokens")
def revoke_expired_tokens(self) -> Dict[str, Any]:
    """
    Revoke expired Google OAuth tokens.
    
    Returns:
        Revocation operation result
    """
    try:
        logger.info("Starting expired token revocation task")
        
        async def _revoke_tokens():
            service = GoogleOAuthService()
            
            # Get expired tokens
            expired_tokens = await service._get_expired_tokens()
            
            if not expired_tokens:
                return {
                    'success': True,
                    'message': 'No expired tokens found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Revoke expired tokens
            revoked_count = 0
            for token_info in expired_tokens:
                try:
                    user_id = token_info['user_id']
                    await service.revoke_user_oauth_tokens(user_id)
                    revoked_count += 1
                except Exception as e:
                    logger.warning(f"Failed to revoke tokens for user {token_info['user_id']}: {e}")
            
            return {
                'success': True,
                'total_expired': len(expired_tokens),
                'revoked_count': revoked_count,
                'timestamp': datetime.now().isoformat()
            }
        
        # Run the async function
        result = asyncio.run(_revoke_tokens())
        
        logger.info(f"Expired token revocation task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Expired token revocation task failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, name="auth.batch_token_maintenance")
def batch_token_maintenance(self) -> Dict[str, Any]:
    """
    Perform comprehensive token maintenance including refresh, validation, and cleanup.
    
    Returns:
        Maintenance operation result
    """
    try:
        logger.info("Starting batch token maintenance task")
        
        async def _maintain_tokens():
            refresh_service = GoogleTokenRefreshService()
            oauth_service = GoogleOAuthService()
            
            # Step 1: Refresh expired tokens
            refresh_result = await refresh_service.refresh_expired_tokens()
            
            # Step 2: Validate all tokens
            token_service = GoogleTokenService()
            all_tokens = await token_service._get_all_tokens()
            validation_results = []
            
            for token_info in all_tokens:
                user_id = token_info['user_id']
                access_token = token_info['access_token']
                
                if access_token:
                    validation_result = await token_service.validate_token(access_token)
                    validation_results.append({
                        'user_id': user_id,
                        'validation': validation_result
                    })
            
            # Step 3: Clean up expired sessions
            expired_sessions = await oauth_service._get_expired_sessions()
            cleaned_sessions = 0
            
            for session in expired_sessions:
                try:
                    await oauth_service._remove_user_session(session['user_id'])
                    cleaned_sessions += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up session for user {session['user_id']}: {e}")
            
            return {
                'success': True,
                'refresh_summary': {
                    'total_users': refresh_result.total_users,
                    'successful_refreshes': refresh_result.successful_refreshes,
                    'failed_refreshes': refresh_result.failed_refreshes
                },
                'validation_summary': {
                    'total_tokens': len(all_tokens),
                    'validation_results': validation_results
                },
                'cleanup_summary': {
                    'expired_sessions': len(expired_sessions),
                    'cleaned_sessions': cleaned_sessions
                },
                'timestamp': datetime.now().isoformat()
            }
        
        # Run the async function
        result = asyncio.run(_maintain_tokens())
        
        logger.info(f"Batch token maintenance task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Batch token maintenance task failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
