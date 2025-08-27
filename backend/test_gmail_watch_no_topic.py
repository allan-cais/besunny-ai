#!/usr/bin/env python3
"""
Test Gmail watch setup without PubSub topic.
"""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.email.gmail_service import GmailService

async def test_gmail_watch_no_topic():
    """Test Gmail watch without PubSub topic."""
    print("🔍 Testing Gmail watch without PubSub topic...")
    
    try:
        # Initialize Gmail service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            print("❌ Gmail service not ready")
            return
        
        print("✅ Gmail service ready")
        
        # Test watch setup without topic (polling mode)
        print("📧 Testing watch setup without PubSub topic...")
        
        try:
            watch_id = await gmail_service.setup_watch(None)
            if watch_id:
                print(f"✅ Gmail watch setup successful: {watch_id}")
                print("   This means Gmail watch works in polling mode!")
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
    asyncio.run(test_gmail_watch_no_topic())
