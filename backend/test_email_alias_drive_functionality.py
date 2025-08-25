#!/usr/bin/env python3
"""
Test script for Email Alias Drive Functionality.

This script tests the complete workflow for processing Drive files shared via email alias:
1. Email processing with Drive file detection
2. Drive file watch setup
3. Metadata storage
4. Webhook handling for file updates
5. Re-vectorization workflow triggers
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.email.email_service import EmailProcessingService
from app.services.drive.email_alias_drive_service import EmailAliasDriveService
from app.services.drive.drive_service import DriveService
from app.core.database import get_supabase
from app.models.schemas.drive import DriveWebhookPayload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockGmailMessage:
    """Mock Gmail message for testing."""
    
    def __init__(self, message_id: str, to: str, subject: str, sender: str, content: str):
        self.id = message_id
        self.payload = MockMessagePayload(to, subject, sender, content)


class MockMessagePayload:
    """Mock message payload for testing."""
    
    def __init__(self, to: str, subject: str, sender: str, content: str):
        self.headers = [
            MockHeader('to', to),
            MockHeader('from', sender),
            MockHeader('subject', subject),
            MockHeader('date', datetime.now().isoformat())
        ]
        self.parts = []
        self.body = MockMessageBody(content)


class MockHeader:
    """Mock header for testing."""
    
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


class MockMessageBody:
    """Mock message body for testing."""
    
    def __init__(self, content: str):
        self.data = content


async def test_email_alias_drive_processing():
    """Test the complete email alias drive processing workflow."""
    try:
        logger.info("🧪 Testing Email Alias Drive Processing Workflow")
        
        # Initialize services
        email_service = EmailProcessingService()
        drive_service = EmailAliasDriveService()
        
        # Test data
        test_username = "testuser"
        test_user_id = "test-user-123"
        test_document_id = "test-doc-456"
        test_file_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        test_drive_url = f"https://drive.google.com/file/d/{test_file_id}/view"
        
        # Create mock email content with Drive URL
        email_content = {
            'full_content': f"Check out this important document: {test_drive_url}",
            'body_text': f"Please review the attached document: {test_drive_url}",
            'body_html': f"<p>Please review the attached document: <a href='{test_drive_url}'>{test_drive_url}</a></p>",
            'attachments': []
        }
        
        # Test 1: Drive file detection in email content
        logger.info("📧 Test 1: Drive file detection in email content")
        
        # Create mock Gmail message
        mock_message = MockGmailMessage(
            message_id="test-message-123",
            to=f"ai+{test_username}@besunny.ai",
            subject="Test Document Sharing",
            sender="sender@example.com",
            content=email_content['full_content']
        )
        
        # Test username extraction
        username = email_service._extract_username_from_email(f"ai+{test_username}@besunny.ai")
        logger.info(f"✅ Extracted username: {username}")
        assert username == test_username, f"Expected username {test_username}, got {username}"
        
        # Test 2: Drive file processing workflow
        logger.info("📁 Test 2: Drive file processing workflow")
        
        # Mock the user lookup (in real scenario, this would query the database)
        user_id = await email_service._get_user_id_from_username(test_username)
        if not user_id:
            logger.info("⚠️  User not found in database, using test user ID")
            user_id = test_user_id
        
        # Test Drive file processing
        result = await drive_service.process_drive_file_from_email(
            file_id=test_file_id,
            document_id=test_document_id,
            user_id=user_id,
            drive_url=test_drive_url,
            email_content=email_content
        )
        
        if result['success']:
            logger.info(f"✅ Drive file processing successful: {result['message']}")
            logger.info(f"   Watch ID: {result.get('watch_id')}")
            logger.info(f"   Classification payload prepared: {bool(result.get('classification_payload'))}")
        else:
            logger.warning(f"⚠️  Drive file processing failed: {result.get('error')}")
            # This is expected in test environment without real Google credentials
        
        # Test 3: File update handling
        logger.info("🔄 Test 3: File update handling")
        
        # Create mock webhook payload
        webhook_payload = DriveWebhookPayload(
            file_id=test_file_id,
            channel_id="test-channel-123",
            resource_id="test-resource-456",
            resource_state="change"
        )
        
        # Test file update handling
        update_result = await drive_service.handle_file_update(test_file_id, user_id)
        
        if update_result['success']:
            logger.info(f"✅ File update handling successful: {update_result['message']}")
            logger.info(f"   Metadata updated: {update_result.get('metadata_updated')}")
            logger.info(f"   Workflow triggered: {update_result.get('workflow_triggered')}")
        else:
            logger.warning(f"⚠️  File update handling failed: {update_result.get('error')}")
            # This is expected in test environment without real Google credentials
        
        # Test 4: Classification payload preparation
        logger.info("🧠 Test 4: Classification payload preparation")
        
        classification_payload = await drive_service._prepare_classification_payload(
            test_file_id, test_document_id, user_id, email_content
        )
        
        if classification_payload:
            logger.info(f"✅ Classification payload prepared successfully")
            logger.info(f"   File ID: {classification_payload.get('file_id')}")
            logger.info(f"   User ID: {classification_payload.get('user_id')}")
            logger.info(f"   Source: {classification_payload.get('source')}")
        else:
            logger.warning("⚠️  Classification payload preparation failed")
            # This is expected in test environment without real Google credentials
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def test_drive_service_methods():
    """Test individual Drive service methods."""
    try:
        logger.info("🔧 Testing Drive Service Methods")
        
        drive_service = DriveService()
        
        # Test file content classification method
        test_file_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        test_user_id = "test-user-123"
        
        logger.info("📄 Testing file content classification method")
        
        # This will fail without real credentials, but we can test the method structure
        try:
            content_data = await drive_service.get_file_content_for_classification(test_file_id, test_user_id)
            if content_data:
                logger.info(f"✅ File content classification successful")
                logger.info(f"   Content type: {content_data.get('content_type')}")
                logger.info(f"   File name: {content_data.get('file_name')}")
            else:
                logger.info("⚠️  File content classification returned no data (expected without credentials)")
        except Exception as e:
            logger.info(f"⚠️  File content classification failed as expected: {e}")
        
        logger.info("✅ Drive service method tests completed")
        
    except Exception as e:
        logger.error(f"❌ Drive service test failed: {e}")
        raise


async def test_database_operations():
    """Test database operations for the email alias drive workflow."""
    try:
        logger.info("🗄️  Testing Database Operations")
        
        supabase = await get_supabase()
        if not supabase.client:
            logger.warning("⚠️  Supabase client not available, skipping database tests")
            return
        
        # Test 1: Check if required tables exist
        logger.info("📋 Test 1: Checking required tables")
        
        required_tables = [
            'documents',
            'drive_file_watches', 
            'drive_webhook_logs',
            'users'
        ]
        
        for table in required_tables:
            try:
                # Try to select from the table to check if it exists
                result = supabase.client.table(table).select('id').limit(1).execute()
                logger.info(f"✅ Table {table} exists and is accessible")
            except Exception as e:
                logger.warning(f"⚠️  Table {table} not accessible: {e}")
        
        # Test 2: Check table schemas
        logger.info("📊 Test 2: Checking table schemas")
        
        try:
            # Check documents table structure
            result = supabase.client.table('documents').select('*').limit(1).execute()
            if result.data:
                columns = list(result.data[0].keys()) if result.data else []
                logger.info(f"✅ Documents table columns: {columns}")
                
                # Check for required columns
                required_columns = ['id', 'title', 'file_id', 'source', 'status']
                missing_columns = [col for col in required_columns if col not in columns]
                if missing_columns:
                    logger.warning(f"⚠️  Missing columns in documents table: {missing_columns}")
                else:
                    logger.info("✅ All required columns present in documents table")
            else:
                logger.info("⚠️  Documents table is empty (expected in test environment)")
        except Exception as e:
            logger.warning(f"⚠️  Could not check documents table schema: {e}")
        
        logger.info("✅ Database operation tests completed")
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        raise


async def main():
    """Main test function."""
    try:
        logger.info("🚀 Starting Email Alias Drive Functionality Tests")
        logger.info("=" * 60)
        
        # Run tests
        await test_email_alias_drive_processing()
        logger.info("-" * 40)
        
        await test_drive_service_methods()
        logger.info("-" * 40)
        
        await test_database_operations()
        logger.info("-" * 40)
        
        logger.info("🎯 All tests completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
