#!/usr/bin/env python3
"""
Check if Gmail API is enabled in the Google Cloud project.
"""

import os
import sys
import json
import base64

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import get_settings
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def check_gmail_api():
    """Check if Gmail API is enabled."""
    print("🔍 Checking Gmail API Status...")
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
        client_id = key_data.get('client_id')
        
        print(f"   Service Account Email: {service_account_email}")
        print(f"   Client ID: {client_id}")
        
        # Set environment variable for Google Cloud client
        with open('temp_key.json', 'w') as f:
            json.dump(key_data, f)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'temp_key.json'
        
        try:
            # Test authentication
            credentials, project = default()
            print(f"✅ Google Cloud authentication successful")
            print(f"   Authenticated as: {credentials.service_account_email}")
            
            # Check if Gmail API is enabled by trying to build the service
            print(f"\n🔧 Checking Gmail API availability...")
            
            try:
                # Try to build Gmail service
                gmail_service = build('gmail', 'v1', credentials=credentials)
                print(f"✅ Gmail API service built successfully")
                
                # Try to list users (this will fail if API not enabled)
                try:
                    users = gmail_service.users().list().execute()
                    print(f"✅ Gmail API is enabled and accessible")
                    print(f"   Users found: {len(users.get('users', []))}")
                    
                except HttpError as e:
                    print(f"❌ Gmail API access failed: {e}")
                    print(f"   HTTP Status: {e.resp.status}")
                    print(f"   Error: {e.content}")
                    
                    if "403" in str(e.resp.status):
                        print(f"\n🔒 This suggests a permissions issue!")
                        print(f"   The Gmail API might not be enabled for your project")
                        print(f"   Or there might be a domain-wide delegation issue")
                    
                except Exception as e:
                    print(f"❌ Unexpected Gmail API error: {e}")
                    
            except Exception as e:
                print(f"❌ Failed to build Gmail service: {e}")
                print(f"   This usually means the Gmail API is not enabled")
                print(f"   Go to Google Cloud Console > APIs & Services > Library")
                print(f"   Search for 'Gmail API' and enable it")
                
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Clean up temporary file
            if os.path.exists('temp_key.json'):
                os.remove('temp_key.json')
        
        print("\n" + "=" * 60)
        print("Gmail API check complete!")
        
    except Exception as e:
        print(f"❌ Error during check: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_gmail_api()
