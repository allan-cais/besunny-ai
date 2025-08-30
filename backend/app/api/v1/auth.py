"""
Authentication API endpoints for BeSunny.ai Python backend.
Handles Google OAuth, token management, and user authentication.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

from ...core.security import get_current_user, get_current_user_from_supabase_token, security_manager, get_current_user_hybrid
from ...services.auth.google_oauth_service import GoogleOAuthService
from ...services.auth.google_token_service import GoogleTokenService
from ...models.schemas.user import UserResponse, Token, TokenData
from ...core.config import get_settings
from ...models.schemas.user import User

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
oauth_service = GoogleOAuthService()
token_service = GoogleTokenService()
settings = get_settings()


@router.get("/health")
async def auth_health_check():
    """Health check for auth service."""
    return {"status": "healthy", "service": "auth"}


@router.get("/test-supabase")
async def test_supabase_config():
    """Test endpoint to verify Supabase configuration."""
    try:
        from ...core.supabase_config import get_supabase_config, get_supabase
        
        config = get_supabase_config()
        config_info = config.get_config_info()
        
        # Try to get Supabase client
        supabase = get_supabase()
        client_available = bool(supabase)
        
        return {
            "status": "success",
            "config": config_info,
            "client_available": client_available,
            "message": "Supabase configuration test completed"
        }
    except Exception as e:
        logger.error(f"Supabase config test failed: {e}")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Supabase configuration test failed"
        }


@router.post("/google/oauth/callback", response_model=Dict[str, Any])
async def handle_google_oauth_callback(request: Request):
    """Handle Google OAuth callback efficiently."""
    try:
        # Get the authorization code from the request body
        body = await request.json()
        code = body.get('code')
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        # Process the OAuth callback
        result = await oauth_service.handle_oauth_callback(code)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'OAuth callback failed')
            )
        
        # Return success response with proper headers
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth processing failed"
        )


@router.post("/google/oauth/refresh", response_model=Dict[str, Any])
async def refresh_google_oauth_tokens(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_supabase_token)
):
    logger.info(f"🚨 ALERT: refresh_google_oauth_tokens endpoint called with user_id: {user_id}")
    logger.info(f"🚨 ALERT: current_user: {current_user}")
    """
    Refresh Google OAuth tokens for a user.
    
    This endpoint refreshes expired Google OAuth tokens and:
    1. Validates the current user's session
    2. Refreshes the Google OAuth tokens
    3. Updates the stored credentials
    4. Returns the new token information
    """
    try:
        logger.info(f"🚨 ALERT: Inside try block for user {user_id}")
        
        # Verify the user is requesting their own tokens
        if current_user.get('id') != user_id:
            logger.error(f"🔍 DEBUG: User ID mismatch - current_user: {current_user.get('id')}, requested: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot refresh tokens for another user"
            )
        
        logger.info(f"🔍 DEBUG: Starting token refresh for user {user_id}")
        
        # Refresh the user's tokens
        result = await token_service.refresh_user_tokens(user_id)
        
        logger.info(f"🔍 DEBUG: token_service.refresh_user_tokens returned: {result}")
        
        if not result:
            logger.error(f"🔍 DEBUG: token_service.refresh_user_tokens returned None")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh tokens"
            )
        
        # Check if the token refresh actually succeeded
        if not result.get('success', False):
            error_message = result.get('error', 'Unknown error during token refresh')
            error_code = result.get('error_code', 'UNKNOWN')
            logger.error(f"🔍 DEBUG: Token refresh failed for user {user_id}: {error_message} (code: {error_code})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token refresh failed: {error_message}"
            )
        
        logger.info(f"🔍 DEBUG: Successfully refreshed tokens for user {user_id}")
        return {
            'success': True,
            'tokens': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 DEBUG: Unexpected error in refresh_google_oauth_tokens: {e}")
        import traceback
        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@router.get("/google/user-info", response_model=Dict[str, Any])
async def get_google_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get Google user information for the authenticated user.
    
    This endpoint retrieves the current user's Google profile information and:
    1. Validates the current user's session
    2. Retrieves Google user info using stored credentials
    3. Returns the user's Google profile data
    """
    try:
        user_id = current_user.get('id')
        logger.info(f"Getting Google user info for user {user_id}")
        
        # Get user info from Google
        user_info = await oauth_service.get_user_info_from_stored_credentials(user_id)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Google user info not found"
            )
        
        logger.info(f"Successfully retrieved Google user info for user {user_id}")
        return {
            'success': True,
            'user_info': user_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting user info"
        )


@router.post("/google/session", response_model=Dict[str, Any])
async def create_google_session(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new Google OAuth session for a user.
    
    This endpoint creates a new OAuth session and:
    1. Validates the current user's session
    2. Creates a new Google OAuth session
    3. Returns session information
    """
    try:
        # Verify the user is creating their own session
        if current_user.get('id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create session for another user"
            )
        
        logger.info(f"Creating Google OAuth session for user {user_id}")
        
        # Create a new session
        session = await oauth_service.create_user_session(user_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create session"
            )
        
        logger.info(f"Successfully created session for user {user_id}")
        return {
            'success': True,
            'session': session
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session creation error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during session creation"
        )


@router.post("/google/token/exchange", response_model=Dict[str, Any])
async def exchange_google_token(
    refresh_token: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Exchange a Google refresh token for new access token.
    
    This endpoint exchanges a refresh token for a new access token and:
    1. Validates the current user's session
    2. Exchanges the refresh token
    3. Returns the new token information
    """
    try:
        logger.info("Exchanging Google refresh token")
        
        # Exchange the refresh token
        result = await token_service.exchange_token(refresh_token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange token"
            )
        
        logger.info("Successfully exchanged Google refresh token")
        return {
            'success': True,
            'tokens': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token exchange"
        )


@router.post("/google/workspace/oauth/callback", response_model=Dict[str, Any])
async def handle_google_workspace_oauth_callback(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
):
    """
    Handle Google Workspace OAuth callback for extended scopes.
    
    This endpoint handles OAuth callbacks for workspace integration with:
    - Gmail access (gmail.modify)
    - Drive access (drive)
    - Calendar access (calendar)
    """
    try:
        logger.info(f"🔍 OAuth Debug - API Endpoint Called for user: {current_user.get('id')}")
        logger.info(f"🔍 OAuth Debug - Request method: {request.method}")
        logger.info(f"🔍 OAuth Debug - Request headers: {dict(request.headers)}")
        logger.info(f"🔍 OAuth Debug - Authorization header: {request.headers.get('authorization', 'NOT_FOUND')}")
        
        # Get the authorization code, redirect URI, and Supabase access token from the request body
        body = await request.json()
        logger.info(f"🔍 OAuth Debug - Request Body: {body}")
        
        code = body.get('code')
        redirect_uri = body.get('redirect_uri')
        supabase_access_token = body.get('supabase_access_token')
        
        logger.info(f"🔍 OAuth Debug - Extracted Values: code={bool(code)}, redirect_uri={redirect_uri}, has_token={bool(supabase_access_token)}")
        logger.info(f"🔍 OAuth Debug - Code length: {len(code) if code else 0}")
        logger.info(f"🔍 OAuth Debug - Token length: {len(supabase_access_token) if supabase_access_token else 0}")
        
        if not code:
            logger.error("🔍 OAuth Debug - Missing authorization code")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        if not redirect_uri:
            logger.error("🔍 OAuth Debug - Missing redirect URI")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Redirect URI is required"
            )
        
        if not supabase_access_token:
            logger.error("🔍 OAuth Debug - Missing Supabase access token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supabase access token is required for workspace OAuth"
            )
        
        logger.info(f"🔍 OAuth Debug - Calling OAuth service with: user_id={current_user['id']}, redirect_uri={redirect_uri}")
        
        # Process the workspace OAuth callback with authenticated Supabase client
        result = await oauth_service.handle_workspace_oauth_callback(
            code, current_user['id'], redirect_uri, supabase_access_token
        )
        
        logger.info(f"🔍 OAuth Debug - OAuth service result: {result}")
        
        if not result.get('success'):
            logger.error(f"🔍 OAuth Debug - OAuth service failed: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Workspace OAuth callback failed')
            )
        
        logger.info(f"🔍 OAuth Debug - OAuth service succeeded for user: {current_user['id']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 OAuth Debug - Unexpected error: {e}")
        import traceback
        logger.error(f"🔍 OAuth Debug - Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workspace OAuth processing failed"
        )


@router.post("/google/token/refresh", response_model=Dict[str, Any])
async def refresh_google_token(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Refresh Google tokens for a specific user.
    
    This endpoint refreshes Google tokens for a user and:
    1. Validates the current user's session
    2. Refreshes the user's Google tokens
    3. Returns the new token information
    """
    try:
        # Verify the user is refreshing their own tokens
        if current_user.get('id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot refresh tokens for another user"
            )
        
        logger.info(f"Refreshing Google tokens for user {user_id}")
        
        # Refresh the user's tokens
        result = await token_service.refresh_user_tokens(user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh tokens"
            )
        
        logger.info(f"Successfully refreshed Google tokens for user {user_id}")
        return {
            'success': True,
            'tokens': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google token refresh error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@router.post("/google/token/validate", response_model=Dict[str, Any])
async def validate_google_token(
    access_token: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Validate a Google access token.
    
    This endpoint validates a Google access token and:
    1. Validates the current user's session
    2. Validates the Google access token
    3. Returns validation results
    """
    try:
        logger.info("Validating Google access token")
        
        # Validate the token
        result = await token_service.validate_token(access_token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to validate token"
            )
        
        logger.info("Successfully validated Google access token")
        return {
            'success': True,
            'validation': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token validation"
        )


@router.post("/google/token/revoke", response_model=Dict[str, Any])
async def revoke_google_tokens(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Revoke Google OAuth tokens for a user.
    
    This endpoint revokes a user's Google OAuth tokens and:
    1. Validates the current user's session
    2. Revokes the user's Google OAuth tokens
    3. Cleans up stored credentials
    4. Returns revocation status
    """
    try:
        # Verify the user is revoking their own tokens
        if current_user.get('id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot revoke tokens for another user"
            )
        
        logger.info(f"Revoking Google OAuth tokens for user {user_id}")
        
        # Revoke the user's tokens
        result = await oauth_service.revoke_user_oauth_tokens(user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to revoke tokens"
            )
        
        logger.info(f"Successfully revoked Google OAuth tokens for user {user_id}")
        return {
            'success': True,
            'message': 'Tokens revoked successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token revocation error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token revocation"
        )


@router.post("/google/disconnect")
async def disconnect_google_account(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Disconnect user's Google account and revoke all tokens.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Disconnect result
    """
    try:
        from ...services.auth.google_disconnect_service import GoogleDisconnectService
        
        service = GoogleDisconnectService()
        
        result = await service.disconnect_google_account(current_user.id)
        
        if result.get('success'):
            return {
                'success': True,
                'message': result.get('message'),
                'tokens_revoked': result.get('tokens_revoked'),
                'credentials_removed': result.get('credentials_removed')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error_message', 'Failed to disconnect Google account')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting Google account: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    This endpoint returns the current user's profile information.
    """
    try:
        return UserResponse(
            id=current_user.get('id'),
            email=current_user.get('email'),
            username=current_user.get('username'),
            created_at=current_user.get('created_at'),
            updated_at=current_user.get('updated_at')
        )
    except Exception as e:
        logger.error(f"Error getting current user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting user info"
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Logout the current user.
    
    This endpoint logs out the current user and:
    1. Invalidates the current session
    2. Cleans up any stored tokens
    3. Returns logout confirmation
    """
    try:
        user_id = current_user.get('id')
        logger.info(f"Logging out user {user_id}")
        
        # Note: In a stateless JWT system, the client should discard the token
        # This endpoint can be used for additional cleanup if needed
        
        logger.info(f"Successfully logged out user {user_id}")
        return {
            'success': True,
            'message': 'Logged out successfully'
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )
