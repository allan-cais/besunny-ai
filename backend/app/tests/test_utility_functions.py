"""
Tests for Phase 7: Utility Functions
Tests username management, Gmail watch setup, and Drive file subscription services.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

from ..services.user.username_service import UsernameService
from ..services.email.gmail_watch_setup_service import GmailWatchSetupService
from ..services.drive.drive_file_subscription_service import DriveFileSubscriptionService


class TestUsernameService:
    """Test username management functionality."""
    
    @pytest.fixture
    def username_service(self):
        """Create a UsernameService instance for testing."""
        with patch('app.services.user.username_service.get_supabase') as mock_supabase, \
             patch('app.services.user.username_service.get_settings') as mock_settings:
            
            mock_settings.return_value.virtual_email_domain = "test.besunny.ai"
            service = UsernameService()
            service.supabase = Mock()
            return service
    
    def test_validate_username_valid(self, username_service):
        """Test username validation with valid usernames."""
        valid_usernames = ["john", "john_doe", "john.doe", "john-doe", "john123"]
        
        for username in valid_usernames:
            assert username_service._validate_username(username) is True
    
    def test_validate_username_invalid(self, username_service):
        """Test username validation with invalid usernames."""
        invalid_usernames = ["", "ab", "a" * 31, ".john", "john.", "_john", "john_", "-john", "john-"]
        
        for username in invalid_usernames:
            assert username_service._validate_username(username) is False
    
    def test_generate_username_from_email(self, username_service):
        """Test username generation from email addresses."""
        test_cases = [
            ("john.doe@example.com", "john.doe"),
            ("JOHN@EXAMPLE.COM", "john"),
            ("user+tag@domain.com", "user+tag"),
            ("user@domain.com", "user"),
            ("", None),
            ("invalid-email", None)
        ]
        
        for email, expected in test_cases:
            result = username_service._generate_username_from_email(email)
            assert result == expected
    
    def test_generate_virtual_email(self, username_service):
        """Test virtual email generation."""
        username = "testuser"
        expected = "testuser@test.besunny.ai"
        
        result = username_service._generate_virtual_email(username)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_set_username_success(self, username_service):
        """Test successful username setting."""
        user_id = "user-123"
        username = "testuser"
        
        # Mock username availability check
        username_service._is_username_taken = AsyncMock(return_value=False)
        
        # Mock database update
        mock_result = Mock()
        mock_result.data = {"id": user_id, "username": username}
        username_service.supabase.table().update().eq().execute.return_value = mock_result
        
        result = await username_service.set_username(user_id, username)
        
        assert result["success"] is True
        assert result["username"] == username
        assert result["virtual_email"] == "testuser@test.besunny.ai"
    
    @pytest.mark.asyncio
    async def test_set_username_already_taken(self, username_service):
        """Test username setting when username is already taken."""
        user_id = "user-123"
        username = "existinguser"
        
        # Mock username availability check
        username_service._is_username_taken = AsyncMock(return_value=True)
        
        result = await username_service.set_username(user_id, username)
        
        assert result["success"] is False
        assert "already taken" in result["error"]
    
    @pytest.mark.asyncio
    async def test_set_username_invalid_format(self, username_service):
        """Test username setting with invalid format."""
        user_id = "user-123"
        username = ".invalid"
        
        result = await username_service.set_username(user_id, username)
        
        assert result["success"] is False
        assert "Invalid username format" in result["error"]


class TestGmailWatchSetupService:
    """Test Gmail watch setup functionality."""
    
    @pytest.fixture
    def gmail_watch_service(self):
        """Create a GmailWatchSetupService instance for testing."""
        with patch('app.services.email.gmail_watch_setup_service.get_supabase') as mock_supabase, \
             patch('app.services.email.gmail_watch_setup_service.get_settings') as mock_settings:
            
            service = GmailWatchSetupService()
            service.supabase = Mock()
            service.gmail_service = Mock()
            return service
    
    def test_is_watch_active_valid(self, gmail_watch_service):
        """Test watch activity validation with valid expiration."""
        future_time = datetime.now() + timedelta(hours=2)
        watch = {
            "is_active": True,
            "expiration": future_time
        }
        
        assert gmail_watch_service._is_watch_active(watch) is True
    
    def test_is_watch_active_expired(self, gmail_watch_service):
        """Test watch activity validation with expired watch."""
        past_time = datetime.now() - timedelta(hours=1)
        watch = {
            "is_active": True,
            "expiration": past_time
        }
        
        assert gmail_watch_service._is_watch_active(watch) is False
    
    def test_is_watch_active_inactive(self, gmail_watch_service):
        """Test watch activity validation with inactive watch."""
        future_time = datetime.now() + timedelta(hours=2)
        watch = {
            "is_active": False,
            "expiration": future_time
        }
        
        assert gmail_watch_service._is_watch_active(watch) is False
    
    @pytest.mark.asyncio
    async def test_setup_gmail_watch_success(self, gmail_watch_service):
        """Test successful Gmail watch setup."""
        user_id = "user-123"
        user_email = "test@example.com"
        
        # Mock credentials retrieval
        mock_credentials = {"access_token": "token123", "refresh_token": "refresh123"}
        gmail_watch_service._get_user_credentials = AsyncMock(return_value=mock_credentials)
        
        # Mock watch creation
        mock_watch_result = {
            "success": True,
            "watch_id": "watch123",
            "history_id": "history123",
            "expiration": datetime.now() + timedelta(hours=24)
        }
        gmail_watch_service._create_gmail_watch = AsyncMock(return_value=mock_watch_result)
        
        # Mock database operations
        gmail_watch_service._upsert_gmail_watch = AsyncMock(return_value=True)
        
        result = await gmail_watch_service.setup_gmail_watch(user_id, user_email)
        
        assert result["success"] is True
        assert result["watch_id"] == "watch123"
        assert result["expiration"] == mock_watch_result["expiration"]
    
    @pytest.mark.asyncio
    async def test_setup_gmail_watch_no_credentials(self, gmail_watch_service):
        """Test Gmail watch setup without credentials."""
        user_id = "user-123"
        user_email = "test@example.com"
        
        # Mock credentials retrieval failure
        gmail_watch_service._get_user_credentials = AsyncMock(return_value=None)
        
        result = await gmail_watch_service.setup_gmail_watch(user_id, user_email)
        
        assert result["success"] is False
        assert "No Google credentials found" in result["error"]


class TestDriveFileSubscriptionService:
    """Test Drive file subscription functionality."""
    
    @pytest.fixture
    def drive_subscription_service(self):
        """Create a DriveFileSubscriptionService instance for testing."""
        with patch('app.services.drive.drive_file_subscription_service.get_supabase') as mock_supabase, \
             patch('app.services.drive.drive_file_subscription_service.get_settings') as mock_settings:
            
            service = DriveFileSubscriptionService()
            service.supabase = Mock()
            service.drive_service = Mock()
            return service
    
    def test_is_watch_active_valid(self, drive_subscription_service):
        """Test watch activity validation with valid expiration."""
        future_time = datetime.now() + timedelta(hours=2)
        watch = {
            "is_active": True,
            "expiration": future_time
        }
        
        assert drive_subscription_service._is_watch_active(watch) is True
    
    def test_is_watch_active_expired(self, drive_subscription_service):
        """Test watch activity validation with expired watch."""
        past_time = datetime.now() - timedelta(hours=1)
        watch = {
            "is_active": True,
            "expiration": past_time
        }
        
        assert drive_subscription_service._is_watch_active(watch) is False
    
    @pytest.mark.asyncio
    async def test_subscribe_to_file_success(self, drive_subscription_service):
        """Test successful file subscription."""
        user_id = "user-123"
        document_id = "doc-123"
        file_id = "file-123"
        
        # Mock credentials retrieval
        mock_credentials = {"access_token": "token123", "refresh_token": "refresh123"}
        drive_subscription_service._get_user_credentials = AsyncMock(return_value=mock_credentials)
        
        # Mock watch creation
        mock_watch_result = {
            "success": True,
            "channel_id": "channel123",
            "resource_id": "resource123",
            "expiration": datetime.now() + timedelta(hours=24)
        }
        drive_subscription_service._create_file_watch = AsyncMock(return_value=mock_watch_result)
        
        # Mock project ID retrieval
        drive_subscription_service._get_document_project_id = AsyncMock(return_value="project-123")
        
        # Mock database operations
        drive_subscription_service._upsert_file_watch = AsyncMock(return_value=True)
        
        result = await drive_subscription_service.subscribe_to_file(user_id, document_id, file_id)
        
        assert result["success"] is True
        assert result["channel_id"] == "channel123"
        assert result["resource_id"] == "resource123"
        assert result["expiration"] == mock_watch_result["expiration"]
    
    @pytest.mark.asyncio
    async def test_subscribe_to_file_no_credentials(self, drive_subscription_service):
        """Test file subscription without credentials."""
        user_id = "user-123"
        document_id = "doc-123"
        file_id = "file-123"
        
        # Mock credentials retrieval failure
        drive_subscription_service._get_user_credentials = AsyncMock(return_value=None)
        
        result = await drive_subscription_service.subscribe_to_file(user_id, document_id, file_id)
        
        assert result["success"] is False
        assert "No Google credentials found" in result["error"]


class TestUtilityFunctionsIntegration:
    """Integration tests for utility functions."""
    
    @pytest.mark.asyncio
    async def test_full_username_workflow(self):
        """Test complete username management workflow."""
        with patch('app.services.user.username_service.get_supabase') as mock_supabase, \
             patch('app.services.user.username_service.get_settings') as mock_settings:
            
            mock_settings.return_value.virtual_email_domain = "test.besunny.ai"
            service = UsernameService()
            service.supabase = Mock()
            
            # Mock database operations
            mock_result = Mock()
            mock_result.data = {"id": "user-123", "username": "testuser"}
            service.supabase.table().update().eq().execute.return_value = mock_result
            
            # Test username generation and setting
            email = "john.doe@example.com"
            username = service._generate_username_from_email(email)
            assert username == "john.doe"
            
            # Mock username availability check
            service._is_username_taken = AsyncMock(return_value=False)
            
            # Test username setting
            result = await service.set_username("user-123", username)
            assert result["success"] is True
            assert result["username"] == username
            assert result["virtual_email"] == "john.doe@test.besunny.ai"
    
    @pytest.mark.asyncio
    async def test_gmail_watch_lifecycle(self):
        """Test complete Gmail watch lifecycle."""
        with patch('app.services.email.gmail_watch_setup_service.get_supabase') as mock_supabase, \
             patch('app.services.email.gmail_watch_setup_service.get_settings') as mock_settings:
            
            service = GmailWatchSetupService()
            service.supabase = Mock()
            service.gmail_service = Mock()
            
            # Mock all dependencies
            mock_credentials = {"access_token": "token123", "refresh_token": "refresh123"}
            service._get_user_credentials = AsyncMock(return_value=mock_credentials)
            
            mock_watch_result = {
                "success": True,
                "watch_id": "watch123",
                "history_id": "history123",
                "expiration": datetime.now() + timedelta(hours=24)
            }
            service._create_gmail_watch = AsyncMock(return_value=mock_watch_result)
            service._upsert_gmail_watch = AsyncMock(return_value=True)
            
            # Test watch setup
            result = await service.setup_gmail_watch("user-123", "test@example.com")
            assert result["success"] is True
            
            # Test watch status
            mock_existing_watch = {
                "is_active": True,
                "expiration": datetime.now() + timedelta(hours=2)
            }
            service._get_existing_watch = AsyncMock(return_value=mock_existing_watch)
            
            assert service._is_watch_active(mock_existing_watch) is True
    
    @pytest.mark.asyncio
    async def test_drive_subscription_lifecycle(self):
        """Test complete Drive file subscription lifecycle."""
        with patch('app.services.drive.drive_file_subscription_service.get_supabase') as mock_supabase, \
             patch('app.services.drive.drive_file_subscription_service.get_settings') as mock_settings:
            
            service = DriveFileSubscriptionService()
            service.supabase = Mock()
            service.drive_service = Mock()
            
            # Mock all dependencies
            mock_credentials = {"access_token": "token123", "refresh_token": "refresh123"}
            service._get_user_credentials = AsyncMock(return_value=mock_credentials)
            
            mock_watch_result = {
                "success": True,
                "channel_id": "channel123",
                "resource_id": "resource123",
                "expiration": datetime.now() + timedelta(hours=24)
            }
            service._create_file_watch = AsyncMock(return_value=mock_watch_result)
            service._get_document_project_id = AsyncMock(return_value="project-123")
            service._upsert_file_watch = AsyncMock(return_value=True)
            
            # Test file subscription
            result = await service.subscribe_to_file("user-123", "doc-123", "file-123")
            assert result["success"] is True
            
            # Test watch status
            mock_existing_watch = {
                "is_active": True,
                "expiration": datetime.now() + timedelta(hours=2)
            }
            service._get_existing_file_watch = AsyncMock(return_value=mock_existing_watch)
            
            assert service._is_watch_active(mock_existing_watch) is True


if __name__ == "__main__":
    pytest.main([__file__])
