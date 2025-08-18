"""
Gmail Watch API endpoints for BeSunny.ai Python backend.
Handles Gmail webhook setup and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ...services.email.gmail_watch_setup_service import GmailWatchSetupService
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


class GmailWatchRequest(BaseModel):
    """Gmail watch setup request."""
    user_email: Optional[str] = None


class GmailWatchResponse(BaseModel):
    """Gmail watch setup response."""
    success: bool
    watch_id: Optional[str] = None
    expiration: Optional[str] = None
    error_message: Optional[str] = None


class GmailWatchStatusResponse(BaseModel):
    """Gmail watch status response."""
    has_active_watch: bool
    watch_details: Optional[Dict[str, Any]] = None
    expiration: Optional[str] = None
    is_expired: bool


@router.post("/setup", response_model=GmailWatchResponse)
async def setup_gmail_watch(
    request: GmailWatchRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set up Gmail watch for the current user.
    
    Args:
        request: Gmail watch setup request
        current_user: Current authenticated user
        
    Returns:
        Gmail watch setup result
    """
    try:
        service = GmailWatchSetupService()
        
        # Use provided email or current user's email
        user_email = request.user_email or current_user.email
        
        result = await service.setup_gmail_watch(current_user.id, user_email)
        
        if result.get('success'):
            return GmailWatchResponse(
                success=True,
                watch_id=result.get('watch_id'),
                expiration=result.get('expiration').isoformat() if result.get('expiration') else None
            )
        else:
            return GmailWatchResponse(
                success=False,
                error_message=result.get('error', 'Unknown error')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up Gmail watch: {str(e)}"
        )


@router.get("/status", response_model=GmailWatchStatusResponse)
async def get_gmail_watch_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get Gmail watch status for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Gmail watch status information
    """
    try:
        service = GmailWatchSetupService()
        
        # Get existing watch
        existing_watch = await service._get_existing_watch(current_user.email)
        
        if existing_watch and service._is_watch_active(existing_watch):
            return GmailWatchStatusResponse(
                has_active_watch=True,
                watch_details=existing_watch,
                expiration=existing_watch.get('expiration'),
                is_expired=False
            )
        else:
            return GmailWatchStatusResponse(
                has_active_watch=False,
                watch_details=existing_watch if existing_watch else None,
                expiration=existing_watch.get('expiration') if existing_watch else None,
                is_expired=True if existing_watch else False
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Gmail watch status: {str(e)}"
        )


@router.delete("/remove")
async def remove_gmail_watch(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Remove Gmail watch for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Removal result
    """
    try:
        service = GmailWatchSetupService()
        
        # Get existing watch
        existing_watch = await service._get_existing_watch(current_user.email)
        
        if not existing_watch:
            return {
                "success": True,
                "message": "No active Gmail watch found"
            }
        
        # Deactivate watch in database
        watch_data = {
            'user_email': current_user.email,
            'is_active': False,
            'updated_at': datetime.now().isoformat()
        }
        
        await service._upsert_gmail_watch(watch_data)
        
        return {
            "success": True,
            "message": "Gmail watch removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing Gmail watch: {str(e)}"
        )


@router.post("/renew")
async def renew_gmail_watch(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Renew Gmail watch for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Renewal result
    """
    try:
        service = GmailWatchSetupService()
        
        # Check if user has Google credentials
        credentials = await service._get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Google credentials found for user"
            )
        
        # Set up new watch
        result = await service.setup_gmail_watch(current_user.id, current_user.email)
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Gmail watch renewed successfully",
                "watch_id": result.get('watch_id'),
                "expiration": result.get('expiration').isoformat() if result.get('expiration') else None
            }
        else:
            return {
                "success": False,
                "error_message": result.get('error', 'Unknown error')
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error renewing Gmail watch: {str(e)}"
        )
