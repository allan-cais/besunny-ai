"""
User API endpoints for BeSunny.ai Python backend.
Handles username management and user utility functions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Import required modules
from ...services.user.username_service import UsernameService
from ...core.security import get_current_user_from_supabase_token
from ...models.schemas.user import User

router = APIRouter()


@router.get("/health")
async def user_api_health():
    """Health check for user API."""
    return {
        "status": "healthy",
        "service": "user-api",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/test")
async def user_api_test():
    """Test endpoint for user API - no authentication required."""
    return {
        "status": "success",
        "message": "User API is working correctly",
        "timestamp": "2024-01-01T00:00:00Z",
        "features": [
            "username_setup",
            "gmail_watch_integration",
            "virtual_email_generation"
        ]
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
    request: UsernameRequest,
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """
    Set username for the current user.
    
    Args:
        request: Username setting request
        current_user: Current authenticated user
        
    Returns:
        Username setting result
    """
    try:
        username = request.username
        
        # Use the UsernameService to actually set the username
        service = UsernameService()
        result = await service.set_username(current_user.id, username)
        
        if result.get('success'):
            return UsernameResponse(
                success=True,
                username=result.get('username'),
                virtual_email=result.get('virtual_email'),
                gmail_watch_setup=result.get('gmail_watch_setup')
            )
        else:
            return UsernameResponse(
                success=False,
                error_message=result.get('error', 'Failed to set username')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting username: {str(e)}"
        )


@router.get("/username/validate/{username}", response_model=UsernameValidationResponse)
async def validate_username(
    username: str,
    current_user: dict = Depends(get_current_user_from_supabase_token)
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
        
        # Validate format
        is_valid = service._validate_username(username)
        
        if not is_valid:
            return UsernameValidationResponse(
                is_valid=False,
                is_available=False,
                error_message="Invalid username format"
            )
        
        # Check availability
        is_available = not await service._is_username_taken(username, current_user.id)
        
        # Generate suggestions if username is taken
        suggestions = None
        if not is_available:
            suggestions = [
                f"{username}1",
                f"{username}2", 
                f"{username}_{current_user.id[:8]}",
                f"{username}2024"
            ]
        
        return UsernameValidationResponse(
            is_valid=True,
            is_available=is_available,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating username: {str(e)}"
        )


@router.get("/username/generate", response_model=UsernameResponse)
async def generate_username(
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """
    Generate a username from the user's email.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Generated username result
    """
    try:
        service = UsernameService()
        username = service._generate_username_from_email(current_user.email)
        
        if username:
            # Check if generated username is available
            is_available = not await service._is_username_taken(username, current_user.id)
            
            if is_available:
                virtual_email = service._generate_virtual_email(username)
                return UsernameResponse(
                    success=True,
                    username=username,
                    virtual_email=virtual_email
                )
            else:
                # Try with variations
                for i in range(1, 10):
                    variation = f"{username}{i}"
                    if not await service._is_username_taken(variation, current_user.id):
                        virtual_email = service._generate_virtual_email(variation)
                        return UsernameResponse(
                            success=True,
                            username=variation,
                            virtual_email=virtual_email
                        )
                
                return UsernameResponse(
                    success=False,
                    error_message="Could not generate available username"
                )
        else:
            return UsernameResponse(
                success=False,
                error_message="Could not generate username from email"
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
        None (simplified for testing)
        
    Returns:
        Username status information
    """
    try:
        # Simplified version for testing - will be replaced with full functionality
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
