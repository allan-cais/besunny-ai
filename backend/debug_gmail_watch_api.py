#!/usr/bin/env python3
"""
Debug script to test Gmail watch setup step by step
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.email.gmail_service import GmailService

async def debug_gmail_watch_setup():
    """Debug Gmail watch setup step by step."""
    print("🔍 Debugging Gmail Watch Setup...")
    
    try:
        # Step 1: Create Gmail service
        print("\n1️⃣ Creating Gmail service...")
        gmail_service = GmailService()
        
        # Step 2: Check if service is ready
        print("\n2️⃣ Checking if service is ready...")
        is_ready = gmail_service.is_ready()
        print(f"   Service ready: {is_ready}")
        
        if not is_ready:
            print("   ❌ Service not ready - stopping here")
            return
        
        # Step 3: Test setup_watch method directly
        print("\n3️⃣ Testing setup_watch method...")
        topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
        print(f"   Topic: {topic_name}")
        
        # Call setup_watch and capture the result
        watch_id = await gmail_service.setup_watch(topic_name)
        print(f"   Watch ID returned: {watch_id}")
        print(f"   Watch ID type: {type(watch_id)}")
        print(f"   Watch ID is None: {watch_id is None}")
        
        if watch_id:
            print("   ✅ SUCCESS: Watch setup returned a valid ID")
        else:
            print("   ❌ FAILURE: Watch setup returned None")
            
    except Exception as e:
        print(f"\n❌ Error during debug: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(debug_gmail_watch_setup())
