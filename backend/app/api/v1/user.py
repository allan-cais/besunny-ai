"""
User API endpoints for BeSunny.ai Python backend.
Handles username management and user utility functions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Temporarily comment out complex dependencies for testing
# from ...services.user.username_service import UsernameService
# from ...core.security import get_current_user_from_supabase_token
# from ...models.schemas.user import User

router = APIRouter()


@router.get("/health")
async def user_api_health():
    """Health check for user API."""
    return {
        "status": "healthy",
        "service": "user-api",
        "timestamp": "2024-01-01T00:00:00Z"
    }


class UsernameRequest(BaseModel):
    """Username setting request."""
    username: str


class UsernameResponse(BaseModel):
    """Username setting response."""
    success: bool
    username: Optional[str] = None
    virtual_email: Optional[str] = None
    gmail_watch_setup: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class UsernameValidationResponse(BaseModel):
    """Username validation response."""
    is_valid: bool
    is_available: bool
    suggestions: Optional[list] = None
    error_message: Optional[str] = None


@router.post("/username/set", response_model=UsernameResponse)
async def set_username(
    request: UsernameRequest
) -> Dict[str, Any]:
    """
    Set username for the current user.
    
    Args:
        request: Username setting request
        
    Returns:
        Username setting result
    """
    try:
        # Temporarily simplified for testing
        return UsernameResponse(
            success=True,
            username=request.username,
            virtual_email=f"{request.username}@virtual.besunny.ai",
            gmail_watch_setup={"success": True, "message": "Gmail watch setup successful"}
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting username: {str(e)}"
        )


@router.get("/username/validate/{username}", response_model=UsernameValidationResponse)
async def validate_username(
    username: str
) -> Dict[str, Any]:
    """
    Validate username format and availability.
    
    Args:
        username: Username to validate
        current_user: Current authenticated user
        
    Returns:
        Username validation result
    """
    try:
        service = UsernameService()
        
        # Temporarily simplified for testing
        is_valid = len(username) >= 3 and username.isalnum()
        
        return UsernameValidationResponse(
            is_valid=is_valid,
            is_available=is_valid,
            suggestions=["testuser1", "testuser2"] if not is_valid else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating username: {str(e)}"
        )


@router.get("/username/generate", response_model=UsernameResponse)
async def generate_username() -> Dict[str, Any]:
    """
    Generate a username from the user's email.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Generated username result
    """
    try:
        # Temporarily simplified for testing
        username = "testuser"
        virtual_email = f"{username}@virtual.besunny.ai"
        
        return UsernameResponse(
            success=True,
            username=username,
            virtual_email=virtual_email
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating username: {str(e)}"
        )


@router.get("/username/status", response_model=Dict[str, Any])
async def get_username_status() -> Dict[str, Any]:
    """
    Get current username status for the user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Username status information
    """
    try:
        # Temporarily simplified for testing
        return {
            "has_username": False,
            "username": None,
            "virtual_email": None,
            "email": "test@example.com"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting username status: {str(e)}"
        )
