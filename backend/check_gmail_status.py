#!/usr/bin/env python3
"""
Quick status check for Gmail watch and inbox
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.email.gmail_service import GmailService

async def check_gmail_status():
    """Check current Gmail status."""
    print("🔍 Gmail Status Check...")
    print("=" * 40)
    
    try:
        # Initialize service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            print("❌ Gmail service not ready")
            return
        
        print("✅ Gmail service ready")
        print(f"📧 Master email: {gmail_service.master_email}")
        
        # Check inbox stats
        try:
            profile = gmail_service.gmail_service.users().getProfile(userId=gmail_service.master_email).execute()
            print(f"\n📊 Inbox Statistics:")
            print(f"   Total messages: {profile.get('messagesTotal', 'Unknown')}")
            print(f"   Total threads: {profile.get('threadsTotal', 'Unknown')}")
            print(f"   Email address: {profile.get('emailAddress', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  Could not get profile: {e}")
        
        # Check recent messages
        try:
            messages = gmail_service.gmail_service.users().messages().list(
                userId=gmail_service.master_email,
                maxResults=3
            ).execute()
            
            if messages.get('messages'):
                print(f"\n📧 Recent Messages:")
                for i, msg in enumerate(messages['messages'][:3], 1):
                    msg_details = gmail_service.gmail_service.users().messages().get(
                        userId=gmail_service.master_email,
                        id=msg['id']
                    ).execute()
                    
                    headers = msg_details.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                    
                    print(f"   {i}. {subject}")
                    print(f"      From: {from_email}")
                    print(f"      Date: {date}")
                    print(f"      ID: {msg['id']}")
                    print()
            else:
                print("\n📧 No recent messages found")
                
        except Exception as e:
            print(f"⚠️  Could not get recent messages: {e}")
        
        print("\n🎯 Ready for test emails!")
        print("   Send an email to ai+allan@besunny.ai to test notifications")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_gmail_status())
