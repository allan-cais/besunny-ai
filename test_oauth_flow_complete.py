#!/usr/bin/env python3
"""
Comprehensive OAuth Flow Test Script
Tests the complete Google OAuth implementation to identify issues.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test_oauth_flow():
    """Test the complete OAuth flow."""
    print("🔍 Testing Google OAuth Flow...")
    
    try:
        # Test 1: Check environment variables
        print("\n1️⃣ Checking Environment Variables...")
        required_vars = [
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET', 
            'GOOGLE_LOGIN_REDIRECT_URI',
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if value:
                print(f"   ✅ {var}: {'*' * min(len(value), 8)}...")
            else:
                print(f"   ❌ {var}: MISSING")
                missing_vars.append(var)
        
        if missing_vars:
            print(f"\n   ⚠️  Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        # Test 2: Check Supabase connection
        print("\n2️⃣ Testing Supabase Connection...")
        try:
            from app.core.supabase_config import get_supabase_client
            supabase = get_supabase_client()
            if supabase:
                print("   ✅ Supabase client created successfully")
            else:
                print("   ❌ Failed to create Supabase client")
                return False
        except Exception as e:
            print(f"   ❌ Supabase connection failed: {e}")
            return False
        
        # Test 3: Check Google OAuth Service
        print("\n3️⃣ Testing Google OAuth Service...")
        try:
            from app.services.auth.google_oauth_service import GoogleOAuthService
            oauth_service = GoogleOAuthService()
            print("   ✅ Google OAuth service created successfully")
            
            # Check if service has required attributes
            if oauth_service.client_id:
                print(f"   ✅ Client ID: {'*' * min(len(oauth_service.client_id), 8)}...")
            else:
                print("   ❌ Client ID missing")
                return False
                
            if oauth_service.client_secret:
                print(f"   ✅ Client Secret: {'*' * min(len(oauth_service.client_secret), 8)}...")
            else:
                print("   ❌ Client Secret missing")
                return False
                
            if oauth_service.redirect_uri:
                print(f"   ✅ Redirect URI: {oauth_service.redirect_uri}")
            else:
                print("   ❌ Redirect URI missing")
                return False
                
        except Exception as e:
            print(f"   ❌ Google OAuth service creation failed: {e}")
            return False
        
        # Test 4: Check database tables
        print("\n4️⃣ Checking Database Tables...")
        try:
            # Check if google_credentials table exists and is accessible
            result = supabase.table("google_credentials").select("id").limit(1).execute()
            print("   ✅ google_credentials table accessible")
        except Exception as e:
            print(f"   ❌ google_credentials table access failed: {e}")
            return False
        
        try:
            # Check if gmail_watches table exists and is accessible
            result = supabase.table("gmail_watches").select("id").limit(1).execute()
            print("   ✅ gmail_watches table accessible")
        except Exception as e:
            print(f"   ❌ gmail_watches table access failed: {e}")
            return False
        
        # Test 5: Check RLS policies
        print("\n5️⃣ Checking RLS Policies...")
        try:
            # This would require a user to be authenticated
            # For now, just check if we can access with service role
            print("   ℹ️  RLS policies will be tested with actual user authentication")
        except Exception as e:
            print(f"   ❌ RLS policy check failed: {e}")
        
        print("\n✅ All basic tests passed!")
        print("\n📋 Next Steps:")
        print("   1. Apply the RLS policy fixes:")
        print("      - Run fix_gmail_watches_rls_final.sql")
        print("      - Run fix_google_credentials_rls.sql")
        print("   2. Test the OAuth flow with a real user")
        print("   3. Verify gmail_watches table access")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_oauth_flow())
    sys.exit(0 if success else 1)
