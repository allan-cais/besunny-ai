#!/usr/bin/env python3
"""
Debug script to test Gmail service initialization and identify issues.
"""

import asyncio
import os
import sys
import logging

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import get_settings
from app.services.email.gmail_service import GmailService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gmail_service():
    """Test Gmail service initialization and basic functionality."""
    print("🔍 Testing Gmail service initialization...")
    
    try:
        # Get settings
        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"   Environment: {settings.environment}")
        print(f"   Google Project ID: {settings.google_project_id}")
        print(f"   Service Account Key Base64: {'Set' if settings.google_service_account_key_base64 else 'Not set'}")
        
        if settings.google_service_account_key_base64:
            print(f"   Key length: {len(settings.google_service_account_key_base64)} characters")
        
        # Test Gmail service initialization
        print("\n🔧 Initializing Gmail service...")
        gmail_service = GmailService()
        
        # Check if service is ready
        is_ready = gmail_service.is_ready()
        print(f"   Service ready: {is_ready}")
        
        if is_ready:
            print(f"   Master email: {gmail_service.master_email}")
            print(f"   Credentials: {gmail_service.credentials is not None}")
            print(f"   Gmail service: {gmail_service.gmail_service is not None}")
            
            # Test basic Gmail API call
            print("\n📧 Testing basic Gmail API call...")
            try:
                # Try to get user profile
                profile = gmail_service.gmail_service.users().getProfile(userId=gmail_service.master_email).execute()
                print(f"   ✅ Gmail API working - Email: {profile.get('emailAddress')}")
                print(f"   Messages total: {profile.get('messagesTotal')}")
                print(f"   Threads total: {profile.get('threadsTotal')}")
            except Exception as e:
                print(f"   ❌ Gmail API error: {e}")
                print(f"   Error type: {type(e).__name__}")
        else:
            print("   ❌ Service not ready - check credentials and domain-wide delegation")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gmail_service())
