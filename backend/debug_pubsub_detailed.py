#!/usr/bin/env python3
"""
Detailed Pub/Sub debug script to identify exact issues.
"""

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

def debug_pubsub_detailed():
    """Detailed Pub/Sub debugging."""
    print("🔍 Detailed Pub/Sub Debug...")
    
    try:
        # Get settings
        settings = get_settings()
        print(f"✅ Settings loaded")
        print(f"   Project ID: {settings.google_project_id}")
        
        # Get service account key
        service_account_key = settings.google_service_account_key_base64
        if not service_account_key:
            print("❌ No service account key")
            return
        
        print("✅ Service account key available")
        
        # Decode and save to temporary file
        import base64
        import json
        import tempfile
        
        key_data = json.loads(base64.b64decode(service_account_key))
        print(f"   Service Account: {key_data.get('client_email')}")
        print(f"   Project ID: {key_data.get('project_id')}")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(key_data, f)
            key_file = f.name
        
        # Set environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_file
        
        try:
            # Test different Pub/Sub operations
            print("\n🔧 Testing Pub/Sub operations...")
            
            # 1. Test basic client creation
            try:
                publisher = pubsub_v1.PublisherClient()
                subscriber = pubsub_v1.SubscriberClient()
                print("✅ Pub/Sub clients created successfully")
            except Exception as e:
                print(f"❌ Failed to create clients: {e}")
                return
            
            # 2. Test project access
            project_path = f"projects/{settings.google_project_id}"
            print(f"\n📁 Testing project access: {project_path}")
            
            try:
                # Try to list topics in the project
                topics = list(publisher.list_topics(request={"project": project_path}))
                print(f"✅ Project access successful")
                print(f"   Found {len(topics)} topics:")
                for topic in topics:
                    print(f"     - {topic.name}")
            except Exception as e:
                print(f"❌ Project access failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                return
            
            # 3. Test specific topic access
            topic_path = f"{project_path}/topics/gmail-notifications"
            print(f"\n📧 Testing topic access: {topic_path}")
            
            try:
                topic = publisher.get_topic(request={"topic": topic_path})
                print(f"✅ Topic access successful")
                print(f"   Topic name: {topic.name}")
                print(f"   Message storage policy: {topic.message_storage_policy}")
            except Exception as e:
                print(f"❌ Topic access failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                print(f"   This suggests the topic doesn't exist or permissions are wrong")
                
                # Try to create the topic
                print(f"\n🔄 Attempting to create topic...")
                try:
                    topic = publisher.create_topic(request={"name": topic_path})
                    print(f"✅ Topic created successfully: {topic.name}")
                except Exception as create_error:
                    print(f"❌ Topic creation failed: {create_error}")
                    return
            
            # 4. Test publishing
            print(f"\n📤 Testing message publishing...")
            try:
                message_data = "Test message from service account".encode("utf-8")
                future = publisher.publish(topic_path, data=message_data)
                message_id = future.result()
                print(f"✅ Message published successfully: {message_id}")
            except Exception as e:
                print(f"❌ Message publishing failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                return
            
            print("\n🎉 All Pub/Sub tests passed!")
            print("   Your service account has full access to the topic")
            
        finally:
            # Clean up
            os.unlink(key_file)
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
            
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pubsub_detailed()
