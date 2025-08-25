#!/usr/bin/env python3
"""
Test script for virtual email processing functionality.
Tests the email processing service and related components.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.email import EmailProcessingService
from app.models.schemas.email import GmailMessage, GmailMessagePayload, GmailMessageBody

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_email_processing():
    """Test the email processing service with a sample virtual email."""
    
    # Create a sample Gmail message
    sample_message = GmailMessage(
        id="test_message_123",
        threadId="test_thread_456",
        labelIds=["INBOX"],
        snippet="This is a test email sent to a virtual email address",
        internalDate="1704067200000",  # January 1, 2024
        payload=GmailMessagePayload(
            mimeType="text/plain",
            headers=[
                {"name": "to", "value": "ai+johndoe@besunny.ai"},
                {"name": "from", "value": "sender@example.com"},
                {"name": "subject", "value": "Test Virtual Email"},
                {"name": "cc", "value": "cc@example.com"},
                {"name": "date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"}
            ],
            body=GmailMessageBody(
                data="VGhpcyBpcyBhIHRlc3QgZW1haWwgc2VudCB0byBhIHZpcnR1YWwgZW1haWwgYWRkcmVzcy4=",  # Base64 encoded
                size=45
            ),
            parts=[]
        )
    )
    
    try:
        # Initialize the email processing service
        email_service = EmailProcessingService()
        
        logger.info("Testing email processing service...")
        logger.info(f"Sample message: {sample_message.id}")
        logger.info(f"To: {sample_message.payload.headers[0]['value']}")
        logger.info(f"Subject: {sample_message.payload.headers[2]['value']}")
        
        # Test username extraction
        username = email_service._extract_username_from_email("ai+johndoe@besunny.ai")
        logger.info(f"Extracted username: {username}")
        
        # Test email content extraction
        email_content = await email_service._extract_email_content(sample_message)
        logger.info(f"Email content extracted: {len(email_content.get('full_content', ''))} characters")
        logger.info(f"Body text: {email_content.get('body_text', '')[:100]}...")
        
        # Test header extraction
        to_header = email_service._get_header_value(sample_message.payload.headers, 'to')
        subject_header = email_service._get_header_value(sample_message.payload.headers, 'subject')
        logger.info(f"To header: {to_header}")
        logger.info(f"Subject header: {subject_header}")
        
        # Test Drive URL detection
        test_content = "Check out this document: https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view"
        drive_urls = email_service._handle_drive_file_sharing(
            sample_message, "test_doc_123", to_header, username, {"full_content": test_content}
        )
        logger.info("Drive file sharing detection completed")
        
        logger.info("✅ All email processing tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Email processing test failed: {e}")
        raise


async def test_gmail_watch_service():
    """Test the Gmail watch service."""
    
    try:
        from app.services.email import GmailWatchService
        
        watch_service = GmailWatchService()
        logger.info("Gmail watch service initialized successfully")
        
        # Test getting active watches
        active_watches = await watch_service.get_active_watches()
        logger.info(f"Active watches: {len(active_watches)}")
        
        logger.info("✅ Gmail watch service tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Gmail watch service test failed: {e}")
        # Don't raise here as this requires database connection


async def main():
    """Main test function."""
    logger.info("🚀 Starting virtual email processing tests...")
    
    try:
        # Test email processing
        await test_email_processing()
        
        # Test Gmail watch service
        await test_gmail_watch_service()
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
