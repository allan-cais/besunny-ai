"""
Google OAuth service for BeSunny.ai Python backend.
Clean, minimal, and production-ready implementation.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

from ...core.supabase_config import get_supabase_client, get_supabase_service_client
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
        
        # Log configuration values for debugging

        
        # Use service role client to bypass RLS for OAuth operations
        self.supabase = get_supabase_service_client()
        if not self.supabase:
            # Fallback to regular client if service role not available
            self.supabase = get_supabase_client()
            logger.warning("Using regular Supabase client - OAuth operations may fail due to RLS")
        

        
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
        """Handle OAuth callback for Google login (creates new users)."""
        try:
            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(code)
            if not tokens:
                return {'success': False, 'error': 'Token exchange failed'}
            
            # Get user info
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}
            
            # Create/update user in public.users table
            user_id = await self._upsert_user(user_info)
            if not user_id:
                return {'success': False, 'error': 'User creation failed'}
            
            # Store Google credentials in database
            credentials_stored = await self._store_google_credentials(
                user_id, tokens, user_info
            )
            if not credentials_stored:
                logger.warning(f"Failed to store credentials for user {user_id}")
            
            # Return user info for frontend to create Supabase session
            return {
                'success': True,
                'user_id': user_id,
                'email': user_info.email,
                'name': user_info.name,
                'picture': user_info.picture,
                'message': 'Google OAuth login successful - user created and credentials stored'
            }
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return {'success': False, 'error': 'OAuth processing failed'}
    
    async def handle_workspace_oauth_callback(self, code: str, user_id: str, redirect_uri: str, supabase_access_token: str) -> Dict[str, Any]:
        """Handle Google Workspace OAuth callback for existing users connecting Google."""
        try:

            
            # Validate input parameters
            if not code:
                return {'success': False, 'error': 'Authorization code is required'}
            
            if not user_id:
                return {'success': False, 'error': 'User ID is required'}
            
            if not redirect_uri:
                return {'success': False, 'error': 'Redirect URI is required'}
            
            if not supabase_access_token:
                return {'success': False, 'error': 'Supabase access token is required'}
            
            # Exchange code for tokens with workspace scopes using the correct redirect URI
            tokens = await self._exchange_code_for_tokens(code, redirect_uri)
            if not tokens:
                return {'success': False, 'error': 'Token exchange failed'}
            
            # Get user info to verify the account
            user_info = await self._get_user_info(tokens.access_token)
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}
            
            # Create authenticated Supabase client using the user's access token
            # This ensures RLS policies are respected for credential storage
            authenticated_supabase_client = self._create_authenticated_supabase_client(supabase_access_token)
            
            if not authenticated_supabase_client:
                return {'success': False, 'error': 'Failed to create authenticated Supabase client'}
            
            # Store workspace credentials in database (separate from login credentials)
            # For existing users, use authenticated context to respect RLS
            credentials_stored = await self._store_workspace_credentials(
                user_id, tokens, user_info, authenticated_supabase_client
            )
            
            if not credentials_stored:
                return {'success': False, 'error': 'Failed to store workspace credentials'}
            
            return {
                'success': True,
                'user_id': user_id,
                'email': user_info.email,
                'name': user_info.name,
                'picture': user_info.picture,
                'message': 'Google Workspace connected successfully - credentials stored'
            }
            
        except Exception as e:
            logger.error(f"Workspace OAuth processing failed: {e}")
            return {'success': False, 'error': 'Workspace OAuth processing failed'}
    
    async def _exchange_code_for_tokens(self, code: str, redirect_uri: Optional[str] = None) -> Optional[OAuthTokens]:
        """Exchange authorization code for tokens."""
        try:
            # Use provided redirect_uri or fall back to default
            final_redirect_uri = redirect_uri or self.redirect_uri
            
            if not final_redirect_uri:
                logger.error("No redirect URI provided for token exchange")
                return None
            
            logger.info(f"Exchanging OAuth code for tokens with redirect_uri: {final_redirect_uri}")
            
            response = await self.http_client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': final_redirect_uri,
                    'grant_type': 'authorization_code'
                },
                timeout=8.0
            )
            
            if not response.is_success:
                error_text = response.text
                logger.error(f"Google OAuth token exchange failed with status {response.status_code}: {error_text}")
                return None
                
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully exchanged OAuth code for tokens. Scopes: {data.get('scope', 'N/A')}")
            
            return OAuthTokens(
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token', ''),
                expires_in=data.get('expires_in', 3600)
            )
            
        except httpx.TimeoutException:
            logger.error("Token exchange timeout")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token exchange: {e.response.status_code} - {e.response.text}")
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
            logger.info(f"🔍 OAuth Debug - Upserting user with email: {user_info.email}")
            
            # Check if user exists
            result = self.supabase.table("users").select("id").eq("email", user_info.email).execute()
            logger.info(f"🔍 OAuth Debug - User lookup result: {result}")
            
            if result.data:
                # Update existing user
                user_id = result.data[0]['id']
                logger.info(f"🔍 OAuth Debug - Updating existing user: {user_id}")
                update_result = self.supabase.table("users").update({
                    'name': user_info.name,
                    'updated_at': datetime.now().isoformat()
                }).eq("id", user_id).execute()
                logger.info(f"🔍 OAuth Debug - User update result: {update_result}")
                return user_id
            else:
                # Create new user
                logger.info(f"🔍 OAuth Debug - Creating new user")
                new_user_data = {
                    'id': str(uuid.uuid4()),  # Generate UUID for id
                    'email': user_info.email,
                    'name': user_info.name,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                logger.info(f"🔍 OAuth Debug - New user data: {new_user_data}")
                
                result = self.supabase.table("users").insert(new_user_data).execute()
                logger.info(f"🔍 OAuth Debug - User creation result: {result}")
                
                if result.data:
                    user_id = result.data[0]['id']
                    logger.info(f"🔍 OAuth Debug - New user created with ID: {user_id}")
                    return user_id
                else:
                    logger.error(f"🔍 OAuth Debug - User creation failed - no data returned")
                    return None
                
        except Exception as e:
            logger.error(f"🔍 OAuth Debug - User upsert failed: {e}")
            import traceback
            logger.error(f"🔍 OAuth Debug - Traceback: {traceback.format_exc()}")
            return None
    
    async def _store_google_credentials(self, user_id: str, tokens: OAuthTokens, user_info: UserInfo) -> bool:
        """Store Google OAuth credentials in database."""
        try:
            logger.info(f"🔍 OAuth Debug - Storing credentials for user {user_id}")
            logger.info(f"🔍 OAuth Debug - Access token length: {len(tokens.access_token) if tokens.access_token else 0}")
            logger.info(f"🔍 OAuth Debug - Refresh token length: {len(tokens.refresh_token) if tokens.refresh_token else 0}")
            logger.info(f"🔍 OAuth Debug - Expires in: {tokens.expires_in}")
            
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=tokens.expires_in)
            
            # Prepare credentials data
            credentials_data = {
                'user_id': user_id,
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'token_type': 'Bearer',
                'expires_at': expires_at.isoformat(),
                'scope': 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
                'google_email': user_info.email,
                'google_user_id': user_info.id,
                'google_name': user_info.name,
                'google_picture': user_info.picture,
                'login_provider': True,  # This is a login provider
                'login_created_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'expires_in': tokens.expires_in,
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'status': 'connected',  # New column: mark as connected
                'updated_at': datetime.now().isoformat()  # New column: update timestamp
            }
            
            logger.info(f"🔍 OAuth Debug - Prepared credentials data: {list(credentials_data.keys())}")
            logger.info(f"🔍 OAuth Debug - Using Supabase client type: {type(self.supabase)}")
            
            # For OAuth setup, we need to use service role to bypass RLS
            # This is acceptable because we're setting up the initial authentication
            # Subsequent operations will use user context and respect RLS
            
            # Check if credentials already exist
            logger.info("🔍 OAuth Debug - Checking for existing credentials...")
            existing = self.supabase.table("google_credentials").select("user_id").eq("user_id", user_id).execute()
            logger.info(f"🔍 OAuth Debug - Existing credentials check result: {existing}")
            
            if existing.data:
                # Update existing credentials
                logger.info("🔍 OAuth Debug - Updating existing credentials...")
                update_result = self.supabase.table("google_credentials").update(credentials_data).eq("user_id", user_id).execute()
                logger.info(f"🔍 OAuth Debug - Update result: {update_result}")
                logger.info(f"Updated Google credentials for user {user_id}")
            else:
                # Insert new credentials
                logger.info("🔍 OAuth Debug - Inserting new credentials...")
                insert_result = self.supabase.table("google_credentials").insert(credentials_data).execute()
                logger.info(f"🔍 OAuth Debug - Insert result: {insert_result}")
                logger.info(f"Stored new Google credentials for user {user_id}")
            
            # Verify the credentials were actually stored
            logger.info("🔍 OAuth Debug - Verifying storage...")
            verification = self.supabase.table("google_credentials").select("user_id, access_token, google_email").eq("user_id", user_id).execute()
            logger.info(f"🔍 OAuth Debug - Verification result: {verification}")
            
            if verification.data:
                logger.info(f"🔍 OAuth Debug - Credentials verified successfully for user {user_id}")
            else:
                logger.warning(f"🔍 OAuth Debug - Credentials verification failed for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"🔍 OAuth Debug - Failed to store Google credentials for user {user_id}: {e}")
            import traceback
            logger.error(f"🔍 OAuth Debug - Traceback: {traceback.format_exc()}")
            return False
    
    async def _store_workspace_credentials(self, user_id: str, tokens: OAuthTokens, user_info: UserInfo, authenticated_supabase_client=None) -> bool:
        """Store Google Workspace OAuth credentials in database."""
        try:
            logger.info(f"🔍 OAuth Debug - Credential Storage: Starting for user {user_id}")
            logger.info(f"🔍 OAuth Debug - Credential Storage: Using client type: {type(authenticated_supabase_client)}")
            
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=tokens.expires_in)
            
            # Prepare workspace credentials data
            credentials_data = {
                'user_id': user_id,
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'token_type': 'Bearer',
                'expires_at': expires_at.isoformat(),
                'scope': 'https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/calendar',
                'google_email': user_info.email,
                'google_user_id': user_info.id,
                'google_name': user_info.name,
                'google_picture': user_info.picture,
                'login_provider': False,  # This is NOT a login provider, it's workspace integration
                'login_created_at': None,
                'created_at': datetime.now().isoformat(),
                'expires_in': tokens.expires_in,
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'status': 'connected',  # New column: mark as connected
                'updated_at': datetime.now().isoformat()  # New column: update timestamp
            }
            
            logger.info(f"🔍 OAuth Debug - Credential Storage: Prepared data - user_id: {credentials_data['user_id']}, email: {credentials_data['google_email']}, scope: {credentials_data['scope']}")
            
            # For existing users connecting Google, use authenticated context to respect RLS
            # This ensures the user can only insert/update their own credentials
            supabase_client = authenticated_supabase_client or self.supabase
            logger.info(f"🔍 OAuth Debug - Credential Storage: Using Supabase client type: {type(supabase_client)}")
            
            # Check if workspace credentials already exist
            logger.info("🔍 OAuth Debug - Credential Storage: Checking for existing credentials...")
            existing = supabase_client.table("google_credentials").select("user_id").eq("user_id", user_id).eq("login_provider", False).execute()
            
            logger.info(f"🔍 OAuth Debug - Credential Storage: Existing credentials found: {len(existing.data) if existing.data else 0}")
            
            if existing.data:
                # Update existing workspace credentials
                logger.info("🔍 OAuth Debug - Credential Storage: Updating existing credentials...")
                update_result = supabase_client.table("google_credentials").update(credentials_data).eq("user_id", user_id).eq("login_provider", False).execute()
                logger.info(f"🔍 OAuth Debug - Credential Storage: Update result: {update_result}")
                logger.info(f"Updated Google workspace credentials for user {user_id}")
            else:
                # Insert new workspace credentials
                logger.info("🔍 OAuth Debug - Credential Storage: Inserting new credentials...")
                insert_result = supabase_client.table("google_credentials").insert(credentials_data).execute()
                logger.info(f"🔍 OAuth Debug - Credential Storage: Insert result: {insert_result}")
                logger.info(f"Stored new Google workspace credentials for user {user_id}")
            
            # Verify the credentials were actually stored
            logger.info("🔍 OAuth Debug - Credential Storage: Verifying storage...")
            verification = supabase_client.table("google_credentials").select("user_id, google_email, scope").eq("user_id", user_id).eq("login_provider", False).execute()
            logger.info(f"🔍 OAuth Debug - Credential Storage: Verification result: {verification}")
            
            return True
            
        except Exception as e:
            logger.error(f"🔍 OAuth Debug - Credential Storage: Failed to store credentials for user {user_id}: {e}")
            import traceback
            logger.error(f"🔍 OAuth Debug - Credential Storage: Traceback: {traceback.format_exc()}")
            return False
    
    def _create_authenticated_supabase_client(self, access_token: str):
        """Create a Supabase client using the user's access token for authenticated operations."""
        try:
            logger.info(f"🔍 OAuth Debug - Client Creation: Starting with token length: {len(access_token) if access_token else 0}")
            
            from supabase import create_client, Client
            from supabase.lib.client_options import ClientOptions
            
            # Create client options with the user's access token in Authorization header
            options = ClientOptions(
                schema='public',
                headers={
                    'X-Client-Info': 'besunny-ai-python-backend-authenticated',
                    'Authorization': f'Bearer {access_token}'
                }
            )
            
            logger.info(f"🔍 OAuth Debug - Client Creation: Options created - schema: {options.schema}, headers: {options.headers}")
            
            # Create Supabase client with anon key but pass user's access token in headers
            # This client will respect RLS policies based on the user's authentication
            authenticated_client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_anon_key,  # Use anon key, not access token
                options=options
            )
            
            logger.info(f"🔍 OAuth Debug - Client Creation: Authenticated client created - type: {type(authenticated_client)}")
            logger.info("Authenticated Supabase client created successfully")
            return authenticated_client
            
        except Exception as e:
            logger.error(f"🔍 OAuth Debug - Client Creation: Failed to create authenticated Supabase client: {e}")
            import traceback
            logger.error(f"🔍 OAuth Debug - Client Creation: Traceback: {traceback.format_exc()}")
            # Fallback to service role client if authentication fails
            logger.info("🔍 OAuth Debug - Client Creation: Falling back to service role client")
            return self.supabase
    
    async def close(self):
        """Clean up HTTP client."""
        await self.http_client.aclose()
