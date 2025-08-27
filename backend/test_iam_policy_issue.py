#!/usr/bin/env python3
"""
Diagnostic script to identify IAM policy domain restriction issues.
"""

import asyncio
import os
import sys
import logging
import json
import base64

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import get_settings
from google.cloud import pubsub_v1
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_iam_policy_issue():
    """Test for IAM policy domain restriction issues."""
    print("🔍 Testing for IAM Policy Domain Restriction Issues...")
    print("=" * 60)
    
    try:
        # Get settings
        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"   Project ID: {settings.google_project_id}")
        
        # Check service account key
        service_account_key = settings.google_service_account_key_base64
        if not service_account_key:
            print("❌ GOOGLE_SERVICE_ACCOUNT_KEY_BASE64 not set")
            return
        
        print("✅ Service account key available")
        
        # Decode and analyze service account key
        try:
            key_data = json.loads(base64.b64decode(service_account_key))
            print(f"✅ Service account key decoded successfully")
            print(f"   Service Account Email: {key_data.get('client_email')}")
            print(f"   Project ID: {key_data.get('project_id')}")
            print(f"   Private Key ID: {key_data.get('private_key_id')}")
            
            # Check if project IDs match
            if key_data.get('project_id') != settings.google_project_id:
                print("⚠️  WARNING: Project ID mismatch!")
                print(f"   Key file project: {key_data.get('project_id')}")
                print(f"   Config project: {settings.google_project_id}")
            
        except Exception as e:
            print(f"❌ Failed to decode service account key: {e}")
            return
        
        # Test Google Cloud authentication
        print("\n🔧 Testing Google Cloud authentication...")
        try:
            # Set environment variable for Google Cloud client
            with open('temp_key.json', 'w') as f:
                json.dump(key_data, f)
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'temp_key.json'
            
            # Test default credentials
            credentials, project = default()
            print(f"✅ Google Cloud authentication successful")
            print(f"   Authenticated as: {credentials.service_account_email}")
            print(f"   Project: {project}")
            
        except DefaultCredentialsError as e:
            print(f"❌ Google Cloud authentication failed: {e}")
            print("   This suggests a service account permission issue")
            return
        except Exception as e:
            print(f"❌ Unexpected authentication error: {e}")
            return
        
        # Test Pub/Sub access
        print("\n🔧 Testing Pub/Sub access...")
        try:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(settings.google_project_id, "gmail-notifications")
            
            # Try to get topic info (this will fail if IAM policy blocks access)
            print(f"   Testing access to topic: {topic_path}")
            
            # This will fail with IAM policy error if domain restricted sharing is enabled
            topic = publisher.get_topic(request={"topic": topic_path})
            print(f"✅ Pub/Sub topic access successful")
            print(f"   Topic: {topic.name}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Pub/Sub access failed: {error_msg}")
            
            # Check for specific IAM policy errors
            if "Domain Restricted Sharing" in error_msg or "constraints/iam.allowedPolicyMemberDomains" in error_msg:
                print("\n🔒 IAM POLICY DOMAIN RESTRICTION DETECTED!")
                print("=" * 50)
                print("This is the exact issue you're experiencing.")
                print("\nSOLUTIONS:")
                print("1. Update Organization Policy (Recommended):")
                print("   - Go to Google Cloud Console > IAM & Admin > Organization Policies")
                print("   - Find 'constraints/iam.allowedPolicyMemberDomains'")
                print("   - Add '*.iam.gserviceaccount.com' to allowed domains")
                print("\n2. Create New Project (Quick Fix):")
                print("   - Create a new project without domain restrictions")
                print("   - Update your configuration to use the new project ID")
                print("\n3. Contact Organization Admin:")
                print("   - Request permission to modify organization policies")
                print("   - Or request them to add the required domains")
                
            elif "IAM" in error_msg and "policy" in error_msg.lower():
                print("\n🔒 IAM POLICY ERROR DETECTED!")
                print("This is a different IAM policy issue.")
                print("Check your service account permissions and roles.")
                
            elif "403" in error_msg:
                print("\n🔒 PERMISSION DENIED!")
                print("This usually indicates insufficient permissions.")
                print("Ensure your service account has the necessary roles.")
                
        finally:
            # Clean up temporary file
            if os.path.exists('temp_key.json'):
                os.remove('temp_key.json')
        
        print("\n" + "=" * 60)
        print("Diagnostic complete!")
        
    except Exception as e:
        print(f"❌ Error during diagnostic: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_iam_policy_issue()
