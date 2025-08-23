"""
Tests for Attendee service integration.
Tests bot creation, webhook handling, and transcript processing.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.attendee.attendee_service import AttendeeService
from app.services.attendee.attendee_webhook_handler import AttendeeWebhookHandler


class TestAttendeeService:
    """Test cases for AttendeeService."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        mock_settings = Mock()
        mock_settings.attendee_api_base_url = "https://app.attendee.dev"
        mock_settings.master_attendee_api_key = "test_api_key"
        mock_settings.webhook_base_url = "https://test.com"
        return mock_settings
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client for testing."""
        mock_supabase = Mock()
        mock_supabase.table.return_value = Mock()
        return mock_supabase
    
    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock()
        mock_client.get = AsyncMock()
        mock_client.delete = AsyncMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_create_bot_for_meeting_success(self, mock_settings, mock_supabase, mock_http_client):
        """Test successful bot creation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "bot_123",
            "project_id": "proj_456"
        }
        mock_response.raise_for_status.return_value = None
        mock_http_client.post.return_value = mock_response
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_service.get_settings', return_value=mock_settings), \
             patch('app.services.attendee.attendee_service.get_supabase', return_value=mock_supabase), \
             patch('httpx.AsyncClient', return_value=mock_http_client):
            
            service = AttendeeService()
            
            # Test bot creation
            result = await service.create_bot_for_meeting({
                "meeting_url": "https://zoom.us/j/123",
                "bot_name": "Test Bot"
            }, "user_123")
            
            assert result["success"] is True
            assert result["bot_id"] == "bot_123"
            assert result["project_id"] == "proj_456"
            
            # Verify API call was made correctly
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            assert call_args[0][0] == "https://app.attendee.dev/api/v1/bots"
            
            # Verify webhook configuration
            request_data = call_args[1]["json"]
            assert request_data["meeting_url"] == "https://zoom.us/j/123"
            assert request_data["bot_name"] == "Test Bot"
            assert "webhooks" in request_data
            assert len(request_data["webhooks"]) == 1
            assert request_data["webhooks"][0]["triggers"] == [
                "bot.state_change",
                "transcript.update",
                "chat_messages.update",
                "participant_events.join_leave"
            ]
    
    @pytest.mark.asyncio
    async def test_create_bot_for_meeting_missing_fields(self, mock_settings, mock_supabase):
        """Test bot creation with missing required fields."""
        with patch('app.services.attendee.attendee_service.get_settings', return_value=mock_settings), \
             patch('app.services.attendee.attendee_service.get_supabase', return_value=mock_supabase):
            
            service = AttendeeService()
            
            # Test with missing meeting_url
            result = await service.create_bot_for_meeting({
                "bot_name": "Test Bot"
            }, "user_123")
            
            assert result["success"] is False
            assert "Missing required field: meeting_url" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_bot_for_meeting_api_error(self, mock_settings, mock_supabase, mock_http_client):
        """Test bot creation with API error."""
        # Mock API error
        mock_http_client.post.side_effect = Exception("API Error")
        
        with patch('app.services.attendee.attendee_service.get_settings', return_value=mock_settings), \
             patch('app.services.attendee.attendee_service.get_supabase', return_value=mock_supabase), \
             patch('httpx.AsyncClient', return_value=mock_http_client):
            
            service = AttendeeService()
            
            result = await service.create_bot_for_meeting({
                "meeting_url": "https://zoom.us/j/123",
                "bot_name": "Test Bot"
            }, "user_123")
            
            assert result["success"] is False
            assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_bot_status_success(self, mock_settings, mock_supabase, mock_http_client):
        """Test successful bot status retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "bot_123",
            "status": "recording",
            "is_recording": True
        }
        mock_response.raise_for_status.return_value = None
        mock_http_client.get.return_value = mock_response
        
        # Mock database operations
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_service.get_settings', return_value=mock_settings), \
             patch('app.services.attendee.attendee_service.get_supabase', return_value=mock_supabase), \
             patch('httpx.AsyncClient', return_value=mock_http_client):
            
            service = AttendeeService()
            
            result = await service.get_bot_status("bot_123")
            
            assert result["id"] == "bot_123"
            assert result["status"] == "recording"
            assert result["is_recording"] is True
    
    @pytest.mark.asyncio
    async def test_delete_bot_success(self, mock_settings, mock_supabase, mock_http_client):
        """Test successful bot deletion."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_http_client.delete.return_value = mock_response
        
        # Mock database operations
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_service.get_settings', return_value=mock_settings), \
             patch('app.services.attendee.attendee_service.get_supabase', return_value=mock_supabase), \
             patch('httpx.AsyncClient', return_value=mock_http_client):
            
            service = AttendeeService()
            
            result = await service.delete_bot("bot_123")
            
            assert result is True


class TestAttendeeWebhookHandler:
    """Test cases for AttendeeWebhookHandler."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client for testing."""
        mock_supabase = Mock()
        mock_supabase.table.return_value = Mock()
        return mock_supabase
    
    @pytest.mark.asyncio
    async def test_process_webhook_bot_state_change(self, mock_supabase):
        """Test processing bot state change webhook."""
        webhook_data = {
            "idempotency_key": "webhook_123",
            "trigger": "bot.state_change",
            "bot_id": "bot_123",
            "data": {
                "new_state": "recording",
                "old_state": "created",
                "event_type": "bot_joined"
            }
        }
        
        # Mock database operations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_webhook_handler.get_supabase', return_value=mock_supabase):
            
            handler = AttendeeWebhookHandler()
            
            result = await handler.process_webhook(webhook_data, "user_123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_process_webhook_transcript_update(self, mock_supabase):
        """Test processing transcript update webhook."""
        webhook_data = {
            "idempotency_key": "webhook_123",
            "trigger": "transcript.update",
            "bot_id": "bot_123",
            "data": {
                "speaker_name": "John Doe",
                "speaker_uuid": "speaker_123",
                "timestamp_ms": 1000,
                "duration_ms": 5000,
                "transcription": {
                    "transcript": "Hello, this is a test message."
                }
            }
        }
        
        # Mock database operations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_webhook_handler.get_supabase', return_value=mock_supabase):
            
            handler = AttendeeWebhookHandler()
            
            result = await handler.process_webhook(webhook_data, "user_123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_process_webhook_chat_message(self, mock_supabase):
        """Test processing chat message webhook."""
        webhook_data = {
            "idempotency_key": "webhook_123",
            "trigger": "chat_messages.update",
            "bot_id": "bot_123",
            "data": {
                "id": "msg_123",
                "text": "Hello bot!",
                "sender_name": "Jane Doe",
                "sender_uuid": "sender_123",
                "timestamp": "2024-01-01T12:00:00Z",
                "to": "everyone"
            }
        }
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_webhook_handler.get_supabase', return_value=mock_supabase):
            
            handler = AttendeeWebhookHandler()
            
            result = await handler.process_webhook(webhook_data, "user_123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_process_webhook_participant_event(self, mock_supabase):
        """Test processing participant event webhook."""
        webhook_data = {
            "idempotency_key": "webhook_123",
            "trigger": "participant_events.join_leave",
            "bot_id": "bot_123",
            "data": {
                "id": "event_123",
                "participant_name": "Bob Smith",
                "participant_uuid": "participant_123",
                "event_type": "join",
                "timestamp_ms": 1000
            }
        }
        
        # Mock database operations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_webhook_handler.get_supabase', return_value=mock_supabase):
            
            handler = AttendeeWebhookHandler()
            
            result = await handler.process_webhook(webhook_data, "user_123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_process_webhook_unknown_trigger(self, mock_supabase):
        """Test processing webhook with unknown trigger."""
        webhook_data = {
            "idempotency_key": "webhook_123",
            "trigger": "unknown_trigger",
            "bot_id": "bot_123",
            "data": {}
        }
        
        # Mock database operations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        with patch('app.services.attendee.attendee_webhook_handler.get_supabase', return_value=mock_supabase):
            
            handler = AttendeeWebhookHandler()
            
            result = await handler.process_webhook(webhook_data, "user_123")
            
            assert result is True  # Should still succeed even with unknown trigger


if __name__ == "__main__":
    pytest.main([__file__])
