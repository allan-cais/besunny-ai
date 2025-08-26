#!/usr/bin/env python3
"""
Test Gmail watch setup functionality.
"""

import asyncio
import os
import sys
import logging

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.email.gmail_service import GmailService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gmail_watch_setup():
    """Test Gmail watch setup functionality."""
    print("🔍 Testing Gmail watch setup...")
    
    try:
        # Initialize Gmail service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            print("❌ Gmail service not ready")
            return
        
        print("✅ Gmail service ready")
        
        # Test with a simple topic name first
        topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
        print(f"📧 Testing watch setup with topic: {topic_name}")
        
        try:
            watch_id = await gmail_service.setup_watch(topic_name)
            if watch_id:
                print(f"✅ Gmail watch setup successful: {watch_id}")
            else:
                print("❌ Gmail watch setup failed - no watch ID returned")
        except Exception as e:
            print(f"❌ Gmail watch setup error: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gmail_watch_setup())
