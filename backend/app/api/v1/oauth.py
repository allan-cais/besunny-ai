"""
OAuth setup endpoints for master account authentication.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ...core.security import get_current_user_from_supabase_token
from ...services.email.master_oauth_service import MasterOAuthService

router = APIRouter()


class OAuthSetupRequest(BaseModel):
    """Request model for OAuth setup."""
    auth_code: str
    redirect_uri: str


class OAuthSetupResponse(BaseModel):
    """Response model for OAuth setup."""
    success: bool
    message: str
    watch_id: str = None


@router.post("/setup", response_model=OAuthSetupResponse)
async def setup_master_oauth(
    request: OAuthSetupRequest,
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """Set up OAuth authentication for the master ai@besunny.ai account."""
    try:
        # Only allow admin users to set up OAuth
        # TODO: Add proper admin role checking
        if not current_user.get("email"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to setup OAuth"
            )
        
        oauth_service = MasterOAuthService()
        
        # Set up OAuth with the provided authorization code
        oauth_success = await oauth_service.setup_initial_oauth(
            request.auth_code,
            request.redirect_uri
        )
        
        if not oauth_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup OAuth authentication"
            )
        
        # Set up Gmail watch for email monitoring
        watch_id = await oauth_service.setup_gmail_watch()
        
        if not watch_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth setup successful but Gmail watch setup failed"
            )
        
        return OAuthSetupResponse(
            success=True,
            message="OAuth authentication and Gmail watch setup completed successfully",
            watch_id=watch_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up OAuth: {str(e)}"
        )


@router.get("/status")
async def get_oauth_status(
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """Get the current OAuth status for the master account."""
    try:
        oauth_service = MasterOAuthService()
        
        # Check if we have valid credentials
        credentials = await oauth_service.get_valid_credentials()
        
        if credentials and credentials.valid:
            return {
                "status": "authenticated",
                "message": "OAuth authentication is active and valid",
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None
            }
        else:
            return {
                "status": "unauthenticated",
                "message": "No valid OAuth credentials found",
                "expires_at": None
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking OAuth status: {str(e)}"
        )
