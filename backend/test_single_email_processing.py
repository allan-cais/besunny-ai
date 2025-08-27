#!/usr/bin/env python3
"""
Test script showing single email processing (not multiple test emails)
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.email.email_processing_service import EmailProcessingService

async def test_single_email_processing():
    """Test single email processing to show how it works."""
    print("🧪 Testing Single Email Processing...")
    print("=" * 50)
    
    try:
        # Initialize the service
        print("\n1️⃣ Initializing Email Processing Service...")
        email_processor = EmailProcessingService()
        print("   ✅ Service initialized successfully")
        
        # Simulate processing ONE email (like a real webhook would)
        print("\n2️⃣ Simulating Single Email Processing...")
        print("   📧 Processing ONE email: ai+allan@besunny.ai")
        
        # This is what happens when you send ONE email
        single_email = "ai+allan@besunny.ai"
        info = email_processor._extract_virtual_email_info(single_email)
        
        print(f"\n   📊 Results for this ONE email:")
        print(f"      Email Address: {single_email}")
        print(f"      Is Virtual: {info['is_virtual']}")
        print(f"      Username Extracted: {info['username']}")
        print(f"      Master Email: {info['master_email']}")
        
        print(f"\n   🎯 Summary:")
        print(f"      - ONE email processed")
        print(f"      - ONE username extracted: '{info['username']}'")
        print(f"      - Ready for database storage")
        
        print("\n🎉 Single Email Processing Test Complete!")
        print("   This shows how ONE real email would be processed")
        print("   Not multiple test emails!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_single_email_processing())
