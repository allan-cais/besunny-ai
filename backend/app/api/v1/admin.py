"""
Simple admin endpoints for testing and setup.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import base64
import json

router = APIRouter()


class AdminLoginRequest(BaseModel):
    """Admin login request model."""
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response model."""
    success: bool
    message: str
    token: str = None


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest) -> Dict[str, Any]:
    """Simple admin login for testing purposes."""
    # Proper authentication will be implemented in future version
    admin_credentials = {
        "ai@besunny.ai": "HardWork2025!",
        "admin@besunny.ai": "HardWork2025!"
    }
    
    if request.email in admin_credentials and request.password == admin_credentials[request.email]:
        # For now, return a simple token for testing
        # Proper JWT generation will be implemented in future version
        
        token_data = {
            "email": request.email,
            "is_admin": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Create a simple base64 token
        token = base64.b64encode(json.dumps(token_data).encode()).decode()
        
        return AdminLoginResponse(
            success=True,
            message="Admin login successful",
            token=token
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )


@router.get("/health")
async def admin_health():
    """Health check for admin service."""
    return {"status": "healthy", "service": "admin"}


@router.post("/jwt-token")
async def get_jwt_token(request: AdminLoginRequest) -> Dict[str, Any]:
    """Get a JWT token for testing purposes."""
    # Check credentials
    admin_credentials = {
        "ai@besunny.ai": "HardWork2025!",
        "admin@besunny.ai": "HardWork2025!"
    }
    
    if request.email in admin_credentials and request.password == admin_credentials[request.email]:
        try:
            # Generate a proper JWT token
            from ...core.security import security_manager
            
            token_data = {
                "sub": request.email,
                "email": request.email,
                "is_admin": True
            }
            
            jwt_token = security_manager.create_access_token(data=token_data)
            
            return {
                "success": True,
                "message": "JWT token generated successfully",
                "jwt_token": jwt_token,
                "admin_token": base64.b64encode(json.dumps(token_data).encode()).decode()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to generate JWT token: {str(e)}"
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
