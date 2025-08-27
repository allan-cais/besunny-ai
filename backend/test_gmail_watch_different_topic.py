#!/usr/bin/env python3
"""
Test Gmail watch setup with different topic names.
"""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.email.gmail_service import GmailService

async def test_gmail_watch_different_topics():
    """Test Gmail watch with different topic names."""
    print("🔍 Testing Gmail watch with different topic names...")
    
    try:
        # Initialize Gmail service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            print("❌ Gmail service not ready")
            return
        
        print("✅ Gmail service ready")
        
        # Test different topic names
        topic_names = [
            "projects/sunny-ai-468016/topics/gmail-notifications",
            "projects/sunny-ai-468016/topics/gmail-watch",
            "projects/sunny-ai-468016/topics/email-notifications",
            "projects/sunny-ai-468016/topics/gmail-push",
            "projects/sunny-ai-468016/topics/notifications"
        ]
        
        for topic_name in topic_names:
            print(f"\n📧 Testing topic: {topic_name}")
            
            try:
                watch_id = await gmail_service.setup_watch(topic_name)
                if watch_id:
                    print(f"✅ SUCCESS! Gmail watch setup successful: {watch_id}")
                    print(f"   Working topic: {topic_name}")
                    return watch_id
                else:
                    print(f"❌ Failed - no watch ID returned")
            except Exception as e:
                print(f"❌ Error: {e}")
                if "403" in str(e):
                    print(f"   Permission denied - topic exists but Gmail can't publish to it")
                elif "404" in str(e):
                    print(f"   Topic not found")
                elif "400" in str(e):
                    print(f"   Bad request - topic format issue")
                else:
                    print(f"   Unknown error type")
            
        print("\n❌ All topic names failed")
        return None
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_gmail_watch_different_topics())
