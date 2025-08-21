"""
Google OAuth service for BeSunny.ai Python backend.
Clean, minimal, and production-ready implementation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class OAuthTokens(BaseModel):
    """OAuth token information."""
    access_token: str
    refresh_token: str
    expires_in: int


class UserInfo(BaseModel):
    """Google user information."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    verified_email: bool = False


class GoogleOAuthService:
    """Streamlined Google OAuth service for production use."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.client_id = self.settings.google_client_id
        self.client_secret = self.settings.google_client_secret
        self.redirect_uri = self.settings.google_login_redirect_uri
        
        # Optimized HTTP client with connection pooling
        self.http_client = httpx.AsyncClient(
            timeout=10.0,  # Reduced timeout for better UX
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
        )
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning("Google OAuth not fully configured")
    
    async def handle_oauth_callback(self, code: str) -> Dict[str, Any]:
        """Handle OAuth callback efficiently."""
        try:
            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(code)
            if not tokens:
                return {'success': False, 'error': 'Token exchange failed'}
            
            # Get user info
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}
            
            # Create/update user and return
            user_id = await self._upsert_user(user_info)
            if not user_id:
                return {'success': False, 'error': 'User creation failed'}
            
            return {
                'success': True,
                'user_id': user_id,
                'email': user_info.email,
                'name': user_info.name,
                'picture': user_info.picture
            }
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return {'success': False, 'error': 'OAuth processing failed'}
    
    async def _exchange_code_for_tokens(self, code: str) -> Optional[OAuthTokens]:
        """Exchange authorization code for tokens."""
        try:
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': self.redirect_uri,
                    'grant_type': 'authorization_code'
                },
                timeout=8.0
            )
            response.raise_for_status()
            
            data = response.json()
            return OAuthTokens(
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token', ''),
                expires_in=data.get('expires_in', 3600)
            )
            
        except httpx.TimeoutException:
            logger.error("Token exchange timeout")
            return None
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return None
    
    async def _get_user_info(self, access_token: str) -> Optional[UserInfo]:
        """Get user info from Google."""
        try:
            response = await self.http_client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=5.0
            )
            response.raise_for_status()
            
            data = response.json()
            return UserInfo(
                id=data['id'],
                email=data['email'],
                name=data.get('name', ''),
                picture=data.get('picture'),
                verified_email=data.get('verified_email', False)
            )
            
        except httpx.TimeoutException:
            logger.error("User info request timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    async def _upsert_user(self, user_info: UserInfo) -> Optional[str]:
        """Create or update user efficiently."""
        try:
            # Check if user exists
            result = self.supabase.table("users").select("id").eq("email", user_info.email).execute()
            
            if result.data:
                # Update existing user
                user_id = result.data[0]['id']
                self.supabase.table("users").update({
                    'name': user_info.name,
                    'picture': user_info.picture,
                    'updated_at': datetime.now().isoformat()
                }).eq("id", user_id).execute()
                return user_id
            else:
                # Create new user
                result = self.supabase.table("users").insert({
                    'email': user_info.email,
                    'name': user_info.name,
                    'picture': user_info.picture,
                    'google_id': user_info.id,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }).execute()
                
                if result.data:
                    return result.data[0]['id']
                return None
                
        except Exception as e:
            logger.error(f"User upsert failed: {e}")
            return None
    
    async def close(self):
        """Clean up HTTP client."""
        await self.http_client.aclose()
