#!/usr/bin/env python3
"""
Test script to verify Pub/Sub topic access and permissions.
"""

import asyncio
import os
import sys
import logging

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from google.cloud import pubsub_v1
from app.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pubsub_access():
    """Test Pub/Sub topic access and permissions."""
    print("🔍 Testing Pub/Sub topic access...")
    
    try:
        # Get settings
        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"   Project ID: {settings.google_project_id}")
        
        # Get service account key
        service_account_key = settings.google_service_account_key_base64
        if not service_account_key:
            print("❌ GOOGLE_SERVICE_ACCOUNT_KEY_BASE64 not set")
            return
        
        print("✅ Service account key available")
        
        # Set environment variable for Google Cloud client
        import base64
        import json
        import tempfile
        
        # Decode and save to temporary file
        key_data = json.loads(base64.b64decode(service_account_key))
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(key_data, f)
            key_file = f.name
        
        # Set environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_file
        
        try:
            # Test Pub/Sub client
            print("\n🔧 Testing Pub/Sub client...")
            publisher = pubsub_v1.PublisherClient()
            subscriber = pubsub_v1.SubscriberClient()
            
            # Test topic access
            topic_path = publisher.topic_path(settings.google_project_id, 'gmail-notifications')
            print(f"   Topic path: {topic_path}")
            
            # Try to get topic info
            try:
                topic = publisher.get_topic(request={"topic": topic_path})
                print(f"✅ Topic exists: {topic.name}")
                print(f"   Message storage policy: {topic.message_storage_policy}")
            except Exception as e:
                print(f"❌ Topic access error: {e}")
                print(f"   This might mean the topic doesn't exist or permissions are wrong")
                return
            
            # Test publishing a test message
            print("\n📤 Testing message publishing...")
            try:
                message_data = "Test message from service account".encode("utf-8")
                future = publisher.publish(topic_path, data=message_data)
                message_id = future.result()
                print(f"✅ Message published successfully: {message_id}")
            except Exception as e:
                print(f"❌ Message publishing failed: {e}")
                print(f"   This means the service account doesn't have publish permissions")
                return
            
            # Test subscription access (if subscription exists)
            print("\n📥 Testing subscription access...")
            subscription_path = subscriber.subscription_path(settings.google_project_id, 'gmail-notifications-sub')
            try:
                subscription = subscriber.get_subscription(request={"subscription": subscription_path})
                print(f"✅ Subscription exists: {subscription.name}")
                print(f"   Push endpoint: {subscription.push_config.push_endpoint}")
            except Exception as e:
                print(f"⚠️  Subscription not found: {e}")
                print(f"   This is okay - you can create it later")
            
            print("\n🎉 Pub/Sub access test completed successfully!")
            print("   Your service account can publish to the topic")
            print("   Gmail watch should now work properly")
            
        finally:
            # Clean up temporary file
            os.unlink(key_file)
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pubsub_access()
