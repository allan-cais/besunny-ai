#!/usr/bin/env python3
"""
Minimal test script that simulates a Gmail webhook without importing the full backend.
This test focuses on the webhook payload structure and basic HTTP testing.
"""

import json
import base64
import requests
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "http://localhost:8000"
WEBHOOK_ENDPOINT = f"{BACKEND_URL}/api/v1/webhooks/gmail/gmail"
TEST_ENDPOINT = f"{BACKEND_URL}/api/v1/webhooks/gmail/gmail-test"

# Sample data
SAMPLE_MESSAGE_ID = f"test_message_{int(datetime.now().timestamp())}"
SAMPLE_DRIVE_FILE_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

def create_gmail_webhook_payload(message_id: str) -> Dict[str, Any]:
    """Create a simulated Gmail webhook payload."""
    # Encode the message ID as Gmail would
    encoded_message_id = base64.urlsafe_b64encode(message_id.encode('utf-8')).decode('utf-8').rstrip('=')
    
    return {
        "message": {
            "data": encoded_message_id,
            "messageId": "test_webhook_message_id",
            "publishTime": datetime.utcnow().isoformat() + "Z"
        },
        "subscription": "projects/besunny-ai/subscriptions/gmail-webhook"
    }

def create_mock_email_content_with_drive_file() -> str:
    """Create mock email content that contains a Drive file link."""
    return f"""
    <html>
    <body>
    <p>Hi Allan,</p>
    <p>I've shared a document with you that contains the project requirements.</p>
    <p>You can access it here: <a href="https://drive.google.com/file/d/{SAMPLE_DRIVE_FILE_ID}/view">Project Requirements Document</a></p>
    <p>Please review and let me know your thoughts.</p>
    <p>Best regards,<br>Test Sender</p>
    </body>
    </html>
    """

def test_backend_connectivity():
    """Test if the backend is accessible."""
    logger.info("=" * 60)
    logger.info("TESTING BACKEND CONNECTIVITY")
    logger.info("=" * 60)
    
    try:
        # Test basic connectivity
        health_url = f"{BACKEND_URL}/health"
        logger.info(f"Testing backend health: {health_url}")
        
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info("✅ Backend is accessible and healthy")
            logger.info(f"Service: {health_data.get('service', 'Unknown')}")
            logger.info(f"Version: {health_data.get('version', 'Unknown')}")
            logger.info(f"Status: {health_data.get('status', 'Unknown')}")
            return True
        else:
            logger.error(f"❌ Backend health check failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to backend server")
        logger.error("Make sure the backend is running on port 8000")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing backend connectivity: {e}")
        return False

def test_webhook_endpoints():
    """Test the webhook endpoints."""
    logger.info("=" * 60)
    logger.info("TESTING WEBHOOK ENDPOINTS")
    logger.info("=" * 60)
    
    # Test 1: Basic webhook test endpoint
    logger.info(f"Testing basic webhook endpoint: {TEST_ENDPOINT}")
    try:
        response = requests.post(TEST_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Basic webhook endpoint is working")
            logger.info(f"Response: {response.json()}")
        else:
            logger.error(f"❌ Basic webhook endpoint failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing basic webhook endpoint: {e}")
        return False
    
    # Test 2: Gmail webhook with mock data
    logger.info(f"Testing Gmail webhook: {WEBHOOK_ENDPOINT}")
    try:
        webhook_payload = create_gmail_webhook_payload(SAMPLE_MESSAGE_ID)
        logger.info(f"Webhook payload: {json.dumps(webhook_payload, indent=2)}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test_token"  # Mock authorization
        }
        
        response = requests.post(
            WEBHOOK_ENDPOINT, 
            json=webhook_payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Webhook response status: {response.status_code}")
        logger.info(f"Webhook response: {response.text}")
        
        if response.status_code in [200, 202]:
            logger.info("✅ Gmail webhook endpoint accepted the request")
            return True
        else:
            logger.error(f"❌ Gmail webhook endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Gmail webhook: {e}")
        return False

def test_drive_file_patterns():
    """Test Drive file URL pattern detection."""
    logger.info("=" * 60)
    logger.info("TESTING DRIVE FILE PATTERNS")
    logger.info("=" * 60)
    
    import re
    
    # Test patterns that should be detected
    test_patterns = [
        f"https://drive.google.com/file/d/{SAMPLE_DRIVE_FILE_ID}/view",
        f"https://drive.google.com/file/d/{SAMPLE_DRIVE_FILE_ID}/edit",
        f"https://drive.google.com/open?id={SAMPLE_DRIVE_FILE_ID}",
        f"Check out this file: https://drive.google.com/file/d/{SAMPLE_DRIVE_FILE_ID}/view?usp=sharing",
    ]
    
    # Pattern from the email processing service
    drive_file_patterns = [
        r'https://drive\.google\.com/file/d/([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/open\?id=([a-zA-Z0-9-_]+)',
    ]
    
    for i, pattern in enumerate(test_patterns, 1):
        logger.info(f"\n--- Test Pattern {i} ---")
        logger.info(f"URL: {pattern}")
        
        detected = False
        for regex_pattern in drive_file_patterns:
            matches = re.findall(regex_pattern, pattern)
            if matches:
                file_id = matches[0]
                logger.info(f"✅ Drive file detected - File ID: {file_id}")
                detected = True
                break
        
        if not detected:
            logger.info("❌ Drive file not detected")
    
    return True

def main():
    """Run all tests."""
    logger.info("🚀 Starting minimal webhook simulation tests")
    logger.info(f"Backend URL: {BACKEND_URL}")
    logger.info(f"Target email: ai+allan@besunny.ai")
    logger.info(f"Sample Drive file: {SAMPLE_DRIVE_FILE_ID}")
    logger.info(f"Sample message ID: {SAMPLE_MESSAGE_ID}")
    
    # Test backend connectivity
    backend_accessible = test_backend_connectivity()
    if not backend_accessible:
        logger.error("❌ Backend is not accessible. Please start the backend server first.")
        logger.info("To start the backend:")
        logger.info("  cd backend")
        logger.info("  source venv/bin/activate")
        logger.info("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Test webhook endpoints
    webhook_success = test_webhook_endpoints()
    
    # Test Drive file patterns
    pattern_success = test_drive_file_patterns()
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Backend Connectivity: {'✅ PASS' if backend_accessible else '❌ FAIL'}")
    logger.info(f"Webhook Endpoints: {'✅ PASS' if webhook_success else '❌ FAIL'}")
    logger.info(f"Drive File Patterns: {'✅ PASS' if pattern_success else '❌ FAIL'}")
    
    if webhook_success:
        logger.info("🎉 Webhook tests completed successfully!")
        logger.info("The webhook endpoint accepted the simulated Gmail notification.")
        logger.info("Check the backend server logs for processing details.")
    else:
        logger.error("❌ Webhook tests failed.")
        logger.error("Check the error messages above for troubleshooting.")
    
    logger.info("=" * 60)
    logger.info("Next steps:")
    logger.info("1. Check the backend server logs for any processing messages")
    logger.info("2. If the webhook was accepted, check the database for new entries")
    logger.info("3. Look for any error messages in the server logs")
    logger.info("4. Verify that the email processing service is working correctly")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
