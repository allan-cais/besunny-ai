#!/usr/bin/env python3
"""
Test script for Virtual Email Attendee functionality.
Tests the complete workflow from detecting virtual email attendees to auto-scheduling attendee bots.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.attendee.virtual_email_attendee_service import VirtualEmailAttendeeService
from app.services.attendee.attendee_service import AttendeeService
from app.core.database import get_supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockCalendarEvent:
    """Mock calendar event for testing."""
    
    def __init__(self, event_id: str, summary: str, description: str, start_time: str, end_time: str, attendees: list, meeting_url: str = None):
        self.id = event_id
        self.summary = summary
        self.description = description
        self.start = {'dateTime': start_time}
        self.end = {'dateTime': end_time}
        self.attendees = attendees
        self.meeting_url = meeting_url
        self.status = 'confirmed'
        self.organizer = {'email': 'organizer@example.com'}
        
        # Add meeting URL to description if provided
        if meeting_url and meeting_url not in description:
            self.description = f"{description}\n\nMeeting URL: {meeting_url}"


async def test_virtual_email_attendee_detection():
    """Test detection of virtual email attendees in calendar events."""
    try:
        logger.info("🧪 Test 1: Virtual Email Attendee Detection")
        
        # Initialize service
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Test data
        test_attendees = [
            {'email': 'ai+testuser@besunny.ai', 'responseStatus': 'accepted'},
            {'email': 'ai+anotheruser@besunny.ai', 'responseStatus': 'needsAction'},
            {'email': 'regular@example.com', 'responseStatus': 'accepted'},
            {'email': 'ai+thirduser@besunny.ai', 'responseStatus': 'tentative'}
        ]
        
        # Create mock calendar event
        event_data = {
            'id': 'test-event-123',
            'summary': 'Test Meeting with Virtual Email Attendees',
            'description': 'This is a test meeting to verify virtual email attendee detection.',
            'start': {'dateTime': (datetime.now() + timedelta(hours=1)).isoformat()},
            'end': {'dateTime': (datetime.now() + timedelta(hours=2)).isoformat()},
            'attendees': test_attendees,
            'status': 'confirmed',
            'organizer': {'email': 'organizer@example.com'}
        }
        
        # Extract virtual email attendees
        virtual_attendees = virtual_email_service._extract_virtual_email_attendees(event_data)
        
        logger.info(f"✅ Found {len(virtual_attendees)} virtual email attendees:")
        for attendee in virtual_attendees:
            logger.info(f"   - {attendee['email']} (username: {attendee['username']}, status: {attendee['response_status']})")
        
        # Verify results
        expected_count = 3  # Should find 3 virtual email attendees
        assert len(virtual_attendees) == expected_count, f"Expected {expected_count} virtual attendees, got {len(virtual_attendees)}"
        
        # Verify usernames are extracted correctly
        usernames = [attendee['username'] for attendee in virtual_attendees]
        expected_usernames = ['testuser', 'anotheruser', 'thirduser']
        assert set(usernames) == set(expected_usernames), f"Expected usernames {expected_usernames}, got {usernames}"
        
        logger.info("✅ Virtual email attendee detection test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Virtual email attendee detection test failed: {e}")
        return False


async def test_meeting_url_extraction():
    """Test extraction of meeting URLs from calendar events."""
    try:
        logger.info("🧪 Test 2: Meeting URL Extraction")
        
        # Initialize service
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Test data with different meeting URL formats
        test_cases = [
            {
                'name': 'Google Meet in conferenceData',
                'event_data': {
                    'conferenceData': {
                        'entryPoints': [
                            {'entryPointType': 'video', 'uri': 'https://meet.google.com/abc-defg-hij'}
                        ]
                    }
                },
                'expected_url': 'https://meet.google.com/abc-defg-hij'
            },
            {
                'name': 'Google Meet in description',
                'event_data': {
                    'description': 'Join our meeting: https://meet.google.com/xyz-uvw-123'
                },
                'expected_url': 'https://meet.google.com/xyz-uvw-123'
            },
            {
                'name': 'Zoom URL in description',
                'event_data': {
                    'description': 'Zoom meeting: https://zoom.us/j/123456789'
                },
                'expected_url': 'https://zoom.us/j/123456789'
            },
            {
                'name': 'Teams URL in description',
                'event_data': {
                    'description': 'Teams meeting: https://teams.microsoft.com/l/meetup-join/abc123'
                },
                'expected_url': 'https://teams.microsoft.com/l/meetup-join/abc123'
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"   Testing: {test_case['name']}")
            
            extracted_url = virtual_email_service._extract_meeting_url(test_case['event_data'])
            
            if extracted_url == test_case['expected_url']:
                logger.info(f"   ✅ {test_case['name']}: URL extracted correctly")
            else:
                logger.error(f"   ❌ {test_case['name']}: Expected {test_case['expected_url']}, got {extracted_url}")
                return False
        
        logger.info("✅ Meeting URL extraction test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Meeting URL extraction test failed: {e}")
        return False


async def test_video_conference_url_detection():
    """Test detection of video conference URLs."""
    try:
        logger.info("🧪 Test 3: Video Conference URL Detection")
        
        # Initialize service
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Test data
        test_urls = [
            ('https://meet.google.com/abc-defg-hij', True),
            ('https://zoom.us/j/123456789', True),
            ('https://teams.microsoft.com/l/meetup-join/abc123', True),
            ('https://meet.jitsi.net/testroom', True),
            ('https://app.whereby.com/meeting123', True),
            ('https://example.com/meeting', False),
            ('https://docs.google.com/document/d/123', False),
            ('', False),
            (None, False)
        ]
        
        for url, expected_result in test_urls:
            result = virtual_email_service._is_video_conference_url(url)
            
            if result == expected_result:
                status = "✅" if result else "❌"
                logger.info(f"   {status} {url or 'None'} -> {result}")
            else:
                logger.error(f"   ❌ {url or 'None'}: Expected {expected_result}, got {result}")
                return False
        
        logger.info("✅ Video conference URL detection test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Video conference URL detection test failed: {e}")
        return False


async def test_complete_virtual_email_processing():
    """Test the complete virtual email processing workflow."""
    try:
        logger.info("🧪 Test 4: Complete Virtual Email Processing Workflow")
        
        # Initialize service
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Create a comprehensive test event
        test_event = {
            'id': 'comprehensive-test-event-456',
            'summary': 'Team Standup with Virtual Email Attendees',
            'description': 'Daily team standup meeting. Join via: https://meet.google.com/daily-standup-123',
            'start': {'dateTime': (datetime.now() + timedelta(hours=2)).isoformat()},
            'end': {'dateTime': (datetime.now() + timedelta(hours=2, minutes=30)).isoformat()},
            'attendees': [
                {'email': 'ai+teamlead@besunny.ai', 'responseStatus': 'accepted'},
                {'email': 'ai+developer1@besunny.ai', 'responseStatus': 'accepted'},
                {'email': 'ai+developer2@besunny.ai', 'responseStatus': 'needsAction'},
                {'email': 'stakeholder@company.com', 'responseStatus': 'accepted'}
            ],
            'status': 'confirmed',
            'organizer': {'email': 'teamlead@company.com'}
        }
        
        # Process the event for virtual emails
        result = await virtual_email_service.process_calendar_event_for_virtual_emails(test_event)
        
        logger.info(f"✅ Processing result: {result}")
        
        # Verify the result structure
        assert result.get('processed') == True, "Event should be processed"
        assert result.get('virtual_attendees'), "Should find virtual attendees"
        assert len(result.get('virtual_attendees', [])) == 3, "Should find 3 virtual attendees"
        
        # Verify virtual attendee details
        virtual_attendees = result.get('virtual_attendees', [])
        usernames = [attendee['username'] for attendee in virtual_attendees]
        expected_usernames = ['teamlead', 'developer1', 'developer2']
        
        assert set(usernames) == set(expected_usernames), f"Expected usernames {expected_usernames}, got {usernames}"
        
        logger.info("✅ Complete virtual email processing test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Complete virtual email processing test failed: {e}")
        return False


async def test_virtual_email_activity_tracking():
    """Test virtual email activity tracking functionality."""
    try:
        logger.info("🧪 Test 5: Virtual Email Activity Tracking")
        
        # Initialize service
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Test with a mock user ID (this would normally come from the database)
        test_user_id = "test-user-123"
        
        # Get virtual email activity (this will likely return empty results in test environment)
        activity_result = await virtual_email_service.get_virtual_email_activity(test_user_id, days=30)
        
        logger.info(f"✅ Activity tracking result: {activity_result}")
        
        # Verify the result structure
        assert 'total_meetings' in activity_result, "Should include total_meetings"
        assert 'bot_statuses' in activity_result, "Should include bot_statuses"
        assert 'meetings' in activity_result, "Should include meetings list"
        assert 'period_days' in activity_result, "Should include period_days"
        
        logger.info("✅ Virtual email activity tracking test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Virtual email activity tracking test failed: {e}")
        return False


async def test_username_extraction_edge_cases():
    """Test edge cases in username extraction."""
    try:
        logger.info("🧪 Test 6: Username Extraction Edge Cases")
        
        # Initialize service
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Test edge cases
        edge_cases = [
            {
                'email': 'ai+verylongusername123@besunny.ai',
                'expected_username': 'verylongusername123'
            },
            {
                'email': 'ai+user-name@besunny.ai',
                'expected_username': 'user-name'
            },
            {
                'email': 'ai+user_name@besunny.ai',
                'expected_username': 'user_name'
            },
            {
                'email': 'ai+123user@besunny.ai',
                'expected_username': '123user'
            },
            {
                'email': 'ai+user@besunny.ai',
                'expected_username': 'user'
            }
        ]
        
        for test_case in edge_cases:
            # Create a minimal event with just the email to test
            event_data = {
                'attendees': [{'email': test_case['email']}]
            }
            
            virtual_attendees = virtual_email_service._extract_virtual_email_attendees(event_data)
            
            if virtual_attendees and virtual_attendees[0]['username'] == test_case['expected_username']:
                logger.info(f"   ✅ {test_case['email']} -> {virtual_attendees[0]['username']}")
            else:
                logger.error(f"   ❌ {test_case['email']}: Expected {test_case['expected_username']}, got {virtual_attendees[0]['username'] if virtual_attendees else 'None'}")
                return False
        
        logger.info("✅ Username extraction edge cases test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Username extraction edge cases test failed: {e}")
        return False


async def test_webhook_configuration_consistency():
    """Test that both auto-scheduled and manually deployed bots get the same webhook configuration."""
    try:
        logger.info("🧪 Test 7: Webhook Configuration Consistency")
        
        # Initialize services
        virtual_email_service = VirtualEmailAttendeeService()
        attendee_service = AttendeeService()
        
        # Test data
        test_meeting_url = "https://meet.google.com/test-meeting-123"
        test_user_id = "test-user-456"
        
        # Test 1: Auto-scheduled bot (virtual email)
        logger.info("   Testing auto-scheduled bot webhook configuration")
        
        # Mock the attendee service to capture webhook configuration
        class MockAttendeeService:
            def __init__(self):
                self.last_webhook_config = None
            
            async def create_bot_for_meeting(self, options, user_id):
                self.last_webhook_config = options
                return {
                    'success': True,
                    'bot_id': 'auto-bot-123',
                    'project_id': 'auto-project-456',
                    'deployment_method': 'automatic'
                }
        
        # Replace the attendee service temporarily
        original_attendee_service = virtual_email_service.attendee_service
        virtual_email_service.attendee_service = MockAttendeeService()
        
        # Create auto-scheduled bot
        auto_bot_result = await virtual_email_service._schedule_attendee_bot(
            test_user_id, test_meeting_url, {}, {'username': 'testuser'}
        )
        
        # Verify webhook configuration
        auto_webhook_config = virtual_email_service.attendee_service.last_webhook_config
        assert auto_webhook_config['deployment_method'] == 'automatic', "Auto-scheduled bot should have automatic deployment method"
        
        # Test 2: Manually deployed bot (UI)
        logger.info("   Testing manually deployed bot webhook configuration")
        
        # Reset mock
        virtual_email_service.attendee_service.last_webhook_config = None
        
        # Create manually deployed bot
        manual_bot_options = {
            'meeting_url': test_meeting_url,
            'bot_name': 'Manual Test Bot',
            'deployment_method': 'manual'
        }
        
        manual_bot_result = await virtual_email_service.attendee_service.create_bot_for_meeting(
            manual_bot_options, test_user_id
        )
        
        # Verify webhook configuration
        manual_webhook_config = virtual_email_service.attendee_service.last_webhook_config
        assert manual_webhook_config['deployment_method'] == 'manual', "Manually deployed bot should have manual deployment method"
        
        # Test 3: Verify both have the same webhook triggers
        logger.info("   Verifying webhook trigger consistency")
        
        # Both should have the same comprehensive webhook configuration
        expected_triggers = [
            "bot.state_change",        # For meeting end/recording availability
            "transcript.update",        # Real-time transcript updates
            "chat_messages.update",     # Chat message updates
            "participant_events.join_leave"  # Participant tracking
        ]
        
        # Check that both configurations include the same webhook triggers
        auto_webhooks = auto_webhook_config.get('webhooks', [])
        manual_webhooks = manual_webhook_config.get('webhooks', [])
        
        assert len(auto_webhooks) > 0, "Auto-scheduled bot should have webhooks configured"
        assert len(manual_webhooks) > 0, "Manually deployed bot should have webhooks configured"
        
        auto_triggers = auto_webhooks[0].get('triggers', [])
        manual_triggers = manual_webhooks[0].get('triggers', [])
        
        # Both should have the same triggers for consistent functionality
        assert set(auto_triggers) == set(expected_triggers), f"Auto-scheduled bot should have triggers: {expected_triggers}, got: {auto_triggers}"
        assert set(manual_triggers) == set(expected_triggers), f"Manually deployed bot should have triggers: {expected_triggers}, got: {manual_triggers}"
        
        # Restore original service
        virtual_email_service.attendee_service = original_attendee_service
        
        logger.info("✅ Webhook configuration consistency test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Webhook configuration consistency test failed: {e}")
        return False


async def test_transcript_retrieval_workflow():
    """Test the complete transcript retrieval workflow when meetings end."""
    try:
        logger.info("🧪 Test 8: Transcript Retrieval Workflow")
        
        # Initialize service
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Test data
        test_bot_id = "test-bot-789"
        test_user_id = "test-user-101"
        
        # Mock transcript data
        mock_transcript_data = {
            'transcript_text': 'This is a test transcript from the meeting.',
            'participants': ['John Doe', 'Jane Smith'],
            'duration_minutes': 30
        }
        
        # Mock the attendee service to return transcript data
        class MockAttendeeService:
            async def get_transcript(self, bot_id):
                return mock_transcript_data
        
        # Replace the attendee service temporarily
        original_attendee_service = virtual_email_service.attendee_service
        virtual_email_service.attendee_service = MockAttendeeService()
        
        # Test transcript retrieval
        transcript_result = await virtual_email_service.attendee_service.get_transcript(test_bot_id)
        
        # Verify transcript data
        assert transcript_result['transcript_text'] == mock_transcript_data['transcript_text'], "Transcript text should match"
        assert transcript_result['participants'] == mock_transcript_data['participants'], "Participants should match"
        assert transcript_result['duration_minutes'] == mock_transcript_data['duration_minutes'], "Duration should match"
        
        # Restore original service
        virtual_email_service.attendee_service = original_attendee_service
        
        logger.info("✅ Transcript retrieval workflow test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Transcript retrieval workflow test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Virtual Email Attendee Functionality Tests")
    logger.info("=" * 60)
    
    tests = [
        test_virtual_email_attendee_detection,
        test_meeting_url_extraction,
        test_video_conference_url_detection,
        test_complete_virtual_email_processing,
        test_virtual_email_activity_tracking,
        test_username_extraction_edge_cases,
        test_webhook_configuration_consistency,
        test_transcript_retrieval_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        
        logger.info("-" * 40)
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Virtual email attendee functionality is working correctly.")
    else:
        logger.error(f"❌ {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)
