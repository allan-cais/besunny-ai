"""
Security module for BeSunny.ai Python backend.
Handles JWT tokens, password hashing, and authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()


class SecurityManager:
    """Security utilities for authentication and authorization."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.secret_key, 
            algorithm=self.settings.algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.settings.secret_key, 
                algorithms=[self.settings.algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT token verification failed: {e}")
            return None
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        # Refresh tokens have longer expiration
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.secret_key, 
            algorithm=self.settings.algorithm
        )
        return encoded_jwt


# Global security manager instance
security_manager = SecurityManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency to get current authenticated user from JWT token."""
    try:
        token = credentials.credentials
        payload = security_manager.verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # In a real implementation, you would fetch user from database here
        # For now, we'll return the payload
        return {
            "id": user_id,
            "email": payload.get("email"),
            "username": payload.get("username"),
            "permissions": payload.get("permissions", []),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_from_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency to get current authenticated user from Supabase token."""
    try:
        token = credentials.credentials
        
        # Validate the Supabase token by making a request to Supabase
        from .supabase_config import get_supabase
        supabase = get_supabase()
        
        # Use the token to get user info from Supabase
        response = supabase.auth.get_user(token)
        
        if response.error or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = response.user
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.user_metadata.get("username"),
            "permissions": user.user_metadata.get("permissions", []),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supabase authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_hybrid(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency to get current authenticated user from either JWT or Supabase token."""
    try:
        token = credentials.credentials
        
        # First try to validate as JWT token
        try:
            payload = security_manager.verify_token(token)
            if payload and payload.get("sub"):
                return {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "username": payload.get("username"),
                    "permissions": payload.get("permissions", []),
                }
        except Exception:
            pass
        
        # If JWT validation fails, try Supabase token
        try:
            from .supabase_config import get_supabase
            supabase = get_supabase()
            
            response = supabase.auth.get_user(token)
            
            if response.error or not response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user = response.user
            
            return {
                "id": user.id,
                "email": user.email,
                "username": user.user_metadata.get("username"),
                "permissions": user.user_metadata.get("permissions", []),
            }
            
        except Exception as e:
            logger.error(f"Supabase token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Dependency to get current active user."""
    if not current_user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Dependency to get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = security_manager.verify_token(token)
        
        if payload is None:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # In a real implementation, you would fetch user from database here
        # For now, we'll return the payload
        return {
            "id": user_id,
            "email": payload.get("email"),
            "username": payload.get("username"),
            "permissions": payload.get("permissions", []),
        }
        
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_dependency(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_dependency


def require_role(role: str):
    """Decorator to require specific role."""
    def role_dependency(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    return role_dependency


class RateLimiter:
    """Simple rate limiting implementation."""
    
    def __init__(self):
        self.settings = get_settings()
        self._requests = {}  # In production, use Redis
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limits."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.settings.rate_limit_window)
        
        # Clean old requests
        if identifier in self._requests:
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > window_start
            ]
        else:
            self._requests[identifier] = []
        
        # Check if under limit
        if len(self._requests[identifier]) < self.settings.rate_limit_requests:
            self._requests[identifier].append(now)
            return True
        
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(identifier: str = None):
    """Decorator for rate limiting endpoints."""
    def rate_limit_dependency(
        current_user: dict = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        # Use user ID or IP address as identifier
        rate_id = identifier or current_user.get("id", "anonymous")
        
        if not rate_limiter.is_allowed(rate_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return current_user
    
    return rate_limit_dependency


# Utility functions for external use
def hash_password(password: str) -> str:
    """Hash a password."""
    return security_manager.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return security_manager.verify_password(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create an access token."""
    return security_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: dict) -> str:
    """Create a refresh token."""
    return security_manager.create_refresh_token(data)
