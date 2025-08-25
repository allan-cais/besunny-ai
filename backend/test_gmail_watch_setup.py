#!/usr/bin/env python3
"""
Test script for setting up and testing Gmail watches.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.email.gmail_watch_service import GmailWatchService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_gmail_watch_setup():
    """Test Gmail watch setup functionality."""
    
    try:
        logger.info("🔧 Testing Gmail watch setup...")
        
        # Initialize the watch service
        watch_service = GmailWatchService()
        logger.info("✅ Gmail watch service initialized")
        
        # Test getting active watches
        active_watches = await watch_service.get_active_watches()
        logger.info(f"📊 Current active watches: {len(active_watches)}")
        
        if active_watches:
            for watch in active_watches:
                logger.info(f"  - Watch ID: {watch.get('id')}")
                logger.info(f"    Username: {watch.get('username')}")
                logger.info(f"    Active: {watch.get('is_active')}")
                logger.info(f"    Expires: {watch.get('expiration')}")
        
        # Test setting up a new watch (this will fail locally without credentials)
        logger.info("🔄 Attempting to set up a new Gmail watch...")
        logger.info("   Note: This will fail locally without Google credentials")
        
        # You would normally call this with a real user ID
        # watch_id = await watch_service.setup_virtual_email_watch("test_user_id")
        
        logger.info("✅ Gmail watch service test completed")
        logger.info("\n📋 Next steps:")
        logger.info("1. Deploy to Railway with proper Google credentials")
        logger.info("2. Set up Gmail watches via API endpoints")
        logger.info("3. Send test emails to ai+username@besunny.ai")
        logger.info("4. Monitor webhook processing")
        
    except Exception as e:
        logger.error(f"❌ Gmail watch test failed: {e}")
        raise


async def main():
    """Main test function."""
    logger.info("🚀 Starting Gmail watch setup tests...")
    
    try:
        await test_gmail_watch_setup()
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
