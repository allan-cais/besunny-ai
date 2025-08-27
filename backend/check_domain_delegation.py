#!/usr/bin/env python3
"""
Check domain-wide delegation configuration for Gmail service account.
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

def check_domain_delegation():
    """Check domain-wide delegation configuration."""
    print("🔍 Checking Domain-Wide Delegation Configuration...")
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
        print(f"   Master Email: ai@besunny.ai")
        
        # Set environment variable for Google Cloud client
        with open('temp_key.json', 'w') as f:
            json.dump(key_data, f)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'temp_key.json'
        
        try:
            # Test authentication
            credentials, project = default()
            print(f"✅ Google Cloud authentication successful")
            print(f"   Authenticated as: {credentials.service_account_email}")
            
            # Test domain-wide delegation
            print(f"\n🔧 Testing domain-wide delegation...")
            
            try:
                # Create delegated credentials for ai@besunny.ai
                delegated_credentials = credentials.with_subject("ai@besunny.ai")
                print(f"✅ Successfully created delegated credentials")
                
                # Test Gmail API access with delegated credentials
                print(f"🔧 Testing Gmail API access...")
                
                gmail_service = build('gmail', 'v1', credentials=delegated_credentials)
                
                # Try to get user profile
                try:
                    profile = gmail_service.users().getProfile(userId="ai@besunny.ai").execute()
                    print(f"✅ Gmail API access successful")
                    print(f"   User: {profile.get('emailAddress')}")
                    print(f"   Messages Total: {profile.get('messagesTotal')}")
                    print(f"   Threads Total: {profile.get('threadsTotal')}")
                    
                except HttpError as e:
                    print(f"❌ Gmail API access failed: {e}")
                    print(f"   HTTP Status: {e.resp.status}")
                    print(f"   Error: {e.content}")
                    
                    if "403" in str(e.resp.status):
                        print(f"\n🔒 This suggests a domain-wide delegation issue!")
                        print(f"   Check Google Workspace Admin > Security > API Controls > Domain-wide Delegation")
                        print(f"   Add Client ID: {client_id}")
                        print(f"   With scopes:")
                        print(f"     https://www.googleapis.com/auth/gmail.readonly")
                        print(f"     https://www.googleapis.com/auth/gmail.modify")
                        print(f"     https://www.googleapis.com/auth/gmail.watch")
                    
                except Exception as e:
                    print(f"❌ Unexpected Gmail API error: {e}")
                    
            except Exception as e:
                print(f"❌ Failed to create delegated credentials: {e}")
                print(f"   This usually means domain-wide delegation is not properly configured")
                
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
        print("Domain delegation check complete!")
        
        # Print next steps
        print(f"\n📋 Next Steps:")
        print(f"1. Go to [Google Workspace Admin](https://admin.google.com/ac/security/api-access)")
        print(f"2. Navigate to Security > API Controls > Domain-wide Delegation")
        print(f"3. Add Client ID: {client_id}")
        print(f"4. Add these OAuth scopes:")
        print(f"   https://www.googleapis.com/auth/gmail.readonly")
        print(f"   https://www.googleapis.com/auth/gmail.modify")
        print(f"   https://www.googleapis.com/auth/gmail.watch")
        
    except Exception as e:
        print(f"❌ Error during check: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_domain_delegation()
