#!/usr/bin/env python3
"""
Test script for complete email notification flow
Tests sending email to ai+allan@besunny.ai and monitoring for notifications
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.email.gmail_service import GmailService

async def test_email_notification_flow():
    """Test the complete email notification flow."""
    print("🔍 Testing Complete Email Notification Flow...")
    print("=" * 60)
    
    try:
        # Step 1: Initialize Gmail service
        print("\n1️⃣ Initializing Gmail service...")
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            print("   ❌ Gmail service not ready")
            return
        
        print("   ✅ Gmail service ready")
        print(f"   📧 Master email: {gmail_service.master_email}")
        
        # Step 2: Check current inbox status
        print("\n2️⃣ Checking current inbox status...")
        try:
            profile = gmail_service.gmail_service.users().getProfile(userId=gmail_service.master_email).execute()
            print(f"   📊 Total messages: {profile.get('messagesTotal', 'Unknown')}")
            print(f"   📊 Total threads: {profile.get('threadsTotal', 'Unknown')}")
        except Exception as e:
            print(f"   ⚠️  Could not get profile: {e}")
        
        # Step 3: Send test email to alias
        print("\n3️⃣ Sending test email to ai+allan@besunny.ai...")
        print("   📤 This will test the alias routing and notification system")
        print("   ⏳ You'll need to send an email manually to ai+allan@besunny.ai")
        print("   📧 Or use Gmail's 'Send mail as' feature to test")
        
        # Step 4: Monitor for new messages
        print("\n4️⃣ Monitoring for new messages...")
        print("   🔍 Checking for new messages every 10 seconds...")
        print("   📱 Press Ctrl+C to stop monitoring")
        
        last_message_count = 0
        start_time = datetime.now()
        
        try:
            while True:
                # Get current message count
                try:
                    profile = gmail_service.gmail_service.users().getProfile(userId=gmail_service.master_email).execute()
                    current_count = profile.get('messagesTotal', 0)
                    
                    if current_count > last_message_count:
                        print(f"\n   🎉 NEW MESSAGE DETECTED!")
                        print(f"   📊 Previous count: {last_message_count}")
                        print(f"   📊 Current count: {current_count}")
                        print(f"   📊 New messages: {current_count - last_message_count}")
                        
                        # Get the latest messages
                        try:
                            messages = gmail_service.gmail_service.users().messages().list(
                                userId=gmail_service.master_email,
                                maxResults=5
                            ).execute()
                            
                            if messages.get('messages'):
                                print(f"   📧 Latest message IDs:")
                                for msg in messages['messages'][:3]:
                                    print(f"      - {msg['id']}")
                                
                                # Get details of the first new message
                                latest_msg = messages['messages'][0]
                                msg_details = gmail_service.gmail_service.users().messages().get(
                                    userId=gmail_service.master_email,
                                    id=latest_msg['id']
                                ).execute()
                                
                                headers = msg_details.get('payload', {}).get('headers', [])
                                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                                from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                                to_email = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
                                
                                print(f"   📧 Latest message details:")
                                print(f"      Subject: {subject}")
                                print(f"      From: {from_email}")
                                print(f"      To: {to_email}")
                                print(f"      Snippet: {msg_details.get('snippet', 'No snippet')}")
                        
                        except Exception as e:
                            print(f"   ⚠️  Could not get message details: {e}")
                        
                        last_message_count = current_count
                    
                    # Show status
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"   ⏱️  Monitoring... {elapsed:.0f}s elapsed | Messages: {current_count}", end='\r')
                    
                except Exception as e:
                    print(f"   ⚠️  Error checking messages: {e}")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\n\n   🛑 Monitoring stopped by user")
        
        print("\n5️⃣ Test completed!")
        print("   📧 If you sent a test email, check if it was detected above")
        print("   🔍 Check the Railway logs for webhook processing")
        print("   📊 Check the database for stored email records")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_email_notification_flow())
