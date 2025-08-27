#!/usr/bin/env python3
"""
Debug script to check Pub/Sub topic permissions and existence.
"""

import os
import sys
import json
import base64

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import get_settings
from google.cloud import pubsub_v1
from google.auth import default

def debug_pubsub_topic():
    """Debug Pub/Sub topic permissions and existence."""
    print("🔍 Debugging Pub/Sub Topic Permissions...")
    print("=" * 60)
    
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
        
        # Decode and analyze service account key
        key_data = json.loads(base64.b64decode(service_account_key))
        service_account_email = key_data.get('client_email')
        print(f"   Service Account Email: {service_account_email}")
        
        # Set environment variable for Google Cloud client
        with open('temp_key.json', 'w') as f:
            json.dump(key_data, f)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'temp_key.json'
        
        try:
            # Test authentication
            credentials, project = default()
            print(f"✅ Google Cloud authentication successful")
            print(f"   Authenticated as: {credentials.service_account_email}")
            print(f"   Project: {project}")
            
            # Create Pub/Sub client
            publisher = pubsub_v1.PublisherClient()
            subscriber = pubsub_v1.SubscriberClient()
            
            topic_name = "gmail-notifications"
            topic_path = publisher.topic_path(settings.google_project_id, topic_name)
            
            print(f"\n🔧 Checking Pub/Sub topic: {topic_path}")
            
            # Check if topic exists
            try:
                topic = publisher.get_topic(request={"topic": topic_path})
                print(f"✅ Topic exists: {topic.name}")
                
                # Check topic permissions
                print(f"\n🔧 Checking topic permissions...")
                
                # Try to publish a test message
                try:
                    future = publisher.publish(topic_path, b"test message")
                    message_id = future.result()
                    print(f"✅ Successfully published test message: {message_id}")
                    
                    # Clean up the test message
                    print("   Cleaning up test message...")
                    
                except Exception as e:
                    print(f"❌ Failed to publish test message: {e}")
                    print(f"   This explains why Gmail watch setup is failing!")
                    
            except Exception as e:
                print(f"❌ Topic does not exist: {e}")
                print(f"   Creating topic...")
                
                try:
                    topic = publisher.create_topic(request={"name": topic_path})
                    print(f"✅ Topic created successfully: {topic.name}")
                except Exception as create_error:
                    print(f"❌ Failed to create topic: {create_error}")
                    return
                    
            # Check if we can subscribe to the topic
            print(f"\n🔧 Testing subscription capabilities...")
            subscription_name = "gmail-notifications-sub"
            subscription_path = subscriber.subscription_path(settings.google_project_id, subscription_name)
            
            try:
                # Try to create a subscription
                subscription = subscriber.create_subscription(
                    request={"name": subscription_path, "topic": topic_path}
                )
                print(f"✅ Successfully created subscription: {subscription.name}")
                
                # Clean up subscription
                subscriber.delete_subscription(request={"subscription": subscription_path})
                print(f"   Cleaned up test subscription")
                
            except Exception as e:
                print(f"❌ Failed to create subscription: {e}")
                
        except Exception as e:
            print(f"❌ Error during Pub/Sub operations: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Clean up temporary file
            if os.path.exists('temp_key.json'):
                os.remove('temp_key.json')
        
        print("\n" + "=" * 60)
        print("Debug complete!")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pubsub_topic()
