"""
Simple admin endpoints for testing and setup.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

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
    # TODO: Replace with proper authentication later
    admin_credentials = {
        "ai@besunny.ai": "HardWork2025!",
        "admin@besunny.ai": "HardWork2025!"
    }
    
    if request.email in admin_credentials and request.password == admin_credentials[request.email]:
        # For now, return a simple token for testing
        # TODO: Implement proper JWT generation later
        import base64
        import json
        
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
