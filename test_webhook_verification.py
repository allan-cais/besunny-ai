#!/usr/bin/env python3
"""
Test script to verify Gmail webhook JWT verification is working.
"""

import requests
import json

def test_webhook_without_auth():
    """Test webhook without authorization header."""
    print("Testing webhook without authorization header...")
    
    url = "https://backend-production-298a.up.railway.app/api/v1/webhooks/gmail/gmail"
    
    response = requests.post(url, json={"test": "data"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 401:
        print("✅ Correctly rejected webhook without auth")
    else:
        print("❌ Should have rejected webhook without auth")

def test_webhook_with_invalid_auth():
    """Test webhook with invalid authorization header."""
    print("\nTesting webhook with invalid authorization header...")
    
    url = "https://backend-production-298a.up.railway.app/api/v1/webhooks/gmail/gmail"
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = requests.post(url, json={"test": "data"}, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 401:
        print("✅ Correctly rejected webhook with invalid auth")
    else:
        print("❌ Should have rejected webhook with invalid auth")

def main():
    print("🔍 Testing Gmail Webhook JWT Verification")
    print("=" * 50)
    
    test_webhook_without_auth()
    test_webhook_with_invalid_auth()
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Deploy the updated webhook handler to production")
    print("2. Test with a real Gmail webhook")
    print("3. If verification fails, temporarily disable with VERIFY_GMAIL_WEBHOOKS=false")
    print("=" * 50)

if __name__ == "__main__":
    main()
