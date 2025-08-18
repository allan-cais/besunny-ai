"""
Tests for authentication services.
Tests Google OAuth, token management, and authentication endpoints.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

from ..services.auth.google_oauth_service import GoogleOAuthService, OAuthTokens, UserInfo
from ..services.auth.google_token_service import GoogleTokenService
from ..services.auth.google_token_refresh_service import GoogleTokenRefreshService


class TestGoogleOAuthService:
    """Test Google OAuth service functionality."""
    
    @pytest.fixture
    def oauth_service(self):
        """Create OAuth service instance for testing."""
        with patch('app.services.auth.google_oauth_service.get_supabase') as mock_supabase:
            with patch('app.services.auth.google_oauth_service.get_settings') as mock_settings:
                mock_settings.return_value.google_client_id = 'test_client_id'
                mock_settings.return_value.google_client_secret = 'test_client_secret'
                mock_settings.return_value.google_login_redirect_uri = 'http://localhost:8000/callback'
                
                service = GoogleOAuthService()
                service.supabase = Mock()
                service.http_client = AsyncMock()
                return service
    
    @pytest.fixture
    def mock_tokens(self):
        """Create mock OAuth tokens."""
        return OAuthTokens(
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_type='Bearer',
            expires_in=3600,
            scope='https://www.googleapis.com/auth/userinfo.email'
        )
    
    @pytest.fixture
    def mock_user_info(self):
        """Create mock user info."""
        return UserInfo(
            id='test_user_id',
            email='test@example.com',
            name='Test User',
            given_name='Test',
            family_name='User',
            picture='https://example.com/picture.jpg',
            verified_email=True,
            locale='en'
        )
    
    @pytest.mark.asyncio
    async def test_handle_oauth_callback_success(self, oauth_service, mock_tokens, mock_user_info):
        """Test successful OAuth callback handling."""
        # Mock the service methods
        oauth_service._exchange_code_for_tokens = AsyncMock(return_value=mock_tokens)
        oauth_service._get_user_info = AsyncMock(return_value=mock_user_info)
        oauth_service._create_or_update_user = AsyncMock(return_value='test_user_id')
        oauth_service._create_user_session = AsyncMock(return_value={'session_id': 'test_session'})
        
        # Test the callback
        result = await oauth_service.handle_oauth_callback('test_auth_code')
        
        assert result['success'] is True
        assert result['user_id'] == 'test_user_id'
        assert result['session'] is not None
    
    @pytest.mark.asyncio
    async def test_handle_oauth_callback_token_exchange_failure(self, oauth_service):
        """Test OAuth callback with token exchange failure."""
        oauth_service._exchange_code_for_tokens = AsyncMock(return_value=None)
        
        result = await oauth_service.handle_oauth_callback('test_auth_code')
        
        assert result['success'] is False
        assert 'Failed to exchange code for tokens' in result['error']
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, oauth_service):
        """Test successful code exchange for tokens."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'https://www.googleapis.com/auth/userinfo.email'
        }
        oauth_service.http_client.post.return_value = mock_response
        
        result = await oauth_service._exchange_code_for_tokens('test_auth_code')
        
        assert result is not None
        assert result.access_token == 'test_access_token'
        assert result.refresh_token == 'test_refresh_token'
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self, oauth_service):
        """Test successful user info retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'test_user_id',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        oauth_service.http_client.get.return_value = mock_response
        
        result = await oauth_service._get_user_info('test_access_token')
        
        assert result is not None
        assert result.id == 'test_user_id'
        assert result.email == 'test@example.com'
    
    @pytest.mark.asyncio
    async def test_create_or_update_user_new_user(self, oauth_service, mock_user_info, mock_tokens):
        """Test creating a new user."""
        oauth_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        oauth_service._create_user = AsyncMock(return_value='new_user_id')
        
        result = await oauth_service._create_or_update_user(mock_user_info, mock_tokens)
        
        assert result == 'new_user_id'
        oauth_service._create_user.assert_called_once_with(mock_user_info, mock_tokens)
    
    @pytest.mark.asyncio
    async def test_create_or_update_user_existing_user(self, oauth_service, mock_user_info, mock_tokens):
        """Test updating an existing user."""
        oauth_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {'id': 'existing_user_id'}
        oauth_service._update_user = AsyncMock(return_value='existing_user_id')
        
        result = await oauth_service._create_or_update_user(mock_user_info, mock_tokens)
        
        assert result == 'existing_user_id'
        oauth_service._update_user.assert_called_once_with('existing_user_id', mock_user_info, mock_tokens)


class TestGoogleTokenService:
    """Test Google token service functionality."""
    
    @pytest.fixture
    def token_service(self):
        """Create token service instance for testing."""
        with patch('app.services.auth.google_token_service.get_supabase') as mock_supabase:
            with patch('app.services.auth.google_token_service.get_settings') as mock_settings:
                mock_settings.return_value.google_client_id = 'test_client_id'
                mock_settings.return_value.google_client_secret = 'test_client_secret'
                
                service = GoogleTokenService()
                service.supabase = Mock()
                service.http_client = AsyncMock()
                return service
    
    @pytest.mark.asyncio
    async def test_exchange_token_success(self, token_service):
        """Test successful token exchange."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 3600,
            'token_type': 'Bearer',
            'scope': 'https://www.googleapis.com/auth/userinfo.email'
        }
        token_service.http_client.post.return_value = mock_response
        
        result = await token_service.exchange_token('test_refresh_token')
        
        assert result is not None
        assert result['access_token'] == 'new_access_token'
        assert result['expires_in'] == 3600
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, token_service):
        """Test successful token validation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'user_id': 'test_user_id',
            'scope': 'https://www.googleapis.com/auth/userinfo.email'
        }
        token_service.http_client.get.return_value = mock_response
        
        result = await token_service.validate_token('test_access_token')
        
        assert result is not None
        assert result['is_valid'] is True
        assert result['user_id'] == 'test_user_id'
    
    @pytest.mark.asyncio
    async def test_validate_user_tokens_success(self, token_service):
        """Test successful user token validation."""
        token_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'access_token': 'test_access_token'
        }
        
        with patch.object(token_service, 'validate_token') as mock_validate:
            mock_validate.return_value = {
                'is_valid': True,
                'user_id': 'test_user_id'
            }
            
            result = await token_service.validate_user_tokens('test_user_id')
            
            assert result is not None
            assert result['is_valid'] is True
            assert result['user_id'] == 'test_user_id'
    
    @pytest.mark.asyncio
    async def test_refresh_user_tokens_success(self, token_service):
        """Test successful user token refresh."""
        token_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'refresh_token': 'test_refresh_token'
        }
        
        with patch.object(token_service, 'exchange_token') as mock_exchange:
            mock_exchange.return_value = {
                'access_token': 'new_access_token',
                'expires_in': 3600
            }
            
            result = await token_service.refresh_user_tokens('test_user_id')
            
            assert result is not None
            assert result['access_token'] == 'new_access_token'
            assert result['expires_in'] == 3600


class TestGoogleTokenRefreshService:
    """Test Google token refresh service functionality."""
    
    @pytest.fixture
    def refresh_service(self):
        """Create token refresh service instance for testing."""
        with patch('app.services.auth.google_token_refresh_service.get_supabase') as mock_supabase:
            with patch('app.services.auth.google_token_refresh_service.get_settings') as mock_settings:
                mock_settings.return_value.google_client_id = 'test_client_id'
                mock_settings.return_value.google_client_secret = 'test_client_secret'
                
                service = GoogleTokenRefreshService()
                service.supabase = Mock()
                service.http_client = AsyncMock()
                return service
    
    @pytest.mark.asyncio
    async def test_refresh_user_token_success(self, refresh_service):
        """Test successful user token refresh."""
        refresh_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'refresh_token': 'test_refresh_token'
        }
        
        with patch.object(refresh_service, '_exchange_refresh_token') as mock_exchange:
            mock_exchange.return_value = {
                'access_token': 'new_access_token',
                'expires_in': 3600,
                'token_type': 'Bearer',
                'scope': 'https://www.googleapis.com/auth/userinfo.email'
            }
            
            result = await refresh_service.refresh_user_token('test_user_id')
            
            assert result is not None
            assert result.success is True
            assert result.new_access_token == 'new_access_token'
            assert result.expires_in == 3600
    
    @pytest.mark.asyncio
    async def test_refresh_user_token_no_refresh_token(self, refresh_service):
        """Test token refresh with no refresh token."""
        refresh_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        result = await refresh_service.refresh_user_token('test_user_id')
        
        assert result is not None
        assert result.success is False
        assert 'No refresh token found' in result.error_message
    
    @pytest.mark.asyncio
    async def test_refresh_expired_tokens_batch(self, refresh_service):
        """Test batch refresh of expired tokens."""
        refresh_service.supabase.table.return_value.select.return_value.not_.return_value.execute.return_value.data = [
            {'user_id': 'user1', 'access_token': 'token1'},
            {'user_id': 'user2', 'access_token': 'token2'}
        ]
        
        with patch.object(refresh_service, 'refresh_user_token') as mock_refresh:
            mock_refresh.side_effect = [
                Mock(success=True, user_id='user1'),
                Mock(success=False, user_id='user2', error_message='Failed')
            ]
            
            result = await refresh_service.refresh_expired_tokens()
            
            assert result is not None
            assert result.total_users == 2
            assert result.successful_refreshes == 1
            assert result.failed_refreshes == 1
    
    @pytest.mark.asyncio
    async def test_handle_refresh_results(self, refresh_service):
        """Test handling of refresh results."""
        from app.services.auth.google_token_refresh_service import TokenRefreshResult
        
        results = [
            TokenRefreshResult(
                user_id='user1',
                success=True,
                new_access_token='token1',
                expires_in=3600,
                timestamp=datetime.now()
            ),
            TokenRefreshResult(
                user_id='user2',
                success=False,
                error_message='Failed',
                timestamp=datetime.now()
            )
        ]
        
        result = await refresh_service.handle_refresh_results(results)
        
        assert result['total_refreshes'] == 2
        assert result['successful_refreshes'] == 1
        assert result['failed_refreshes'] == 1
        assert result['success_rate'] == 50.0


class TestAuthIntegration:
    """Integration tests for authentication services."""
    
    @pytest.mark.asyncio
    async def test_full_oauth_flow(self):
        """Test the complete OAuth flow."""
        # This would test the full integration between services
        # In a real test environment, you'd use test databases and mock external APIs
        pass
    
    @pytest.mark.asyncio
    async def test_token_refresh_workflow(self):
        """Test the complete token refresh workflow."""
        # This would test the full token refresh workflow
        pass


# Test utilities
def create_mock_supabase_response(data: Dict[str, Any]) -> Mock:
    """Create a mock Supabase response."""
    mock_response = Mock()
    mock_response.data = data
    return mock_response


def create_mock_http_response(status_code: int, json_data: Dict[str, Any]) -> Mock:
    """Create a mock HTTP response."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = Mock()
    return mock_response
