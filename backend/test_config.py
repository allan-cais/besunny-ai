#!/usr/bin/env python3
"""
Test script to check current configuration values.
Run this to see what the backend is actually using.
"""

import os
from app.core.config import get_settings

def main():
    print("🔍 Configuration Test")
    print("=" * 50)
    
    # Check environment variables directly
    print("\n📋 Environment Variables:")
    print(f"SECRET_KEY: {os.getenv('SECRET_KEY', 'NOT SET')[:20]}...")
    print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')}")
    print(f"SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY', 'NOT SET')[:20]}...")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'NOT SET')[:20]}...")
    
    # Check settings object
    try:
        settings = get_settings()
        print(f"\n⚙️  Settings Object:")
        print(f"secret_key: {settings.secret_key[:20]}...")
        print(f"supabase_url: {settings.supabase_url}")
        print(f"supabase_anon_key: {settings.supabase_anon_key[:20] if settings.supabase_anon_key else 'None'}...")
        print(f"supabase_service_role_key: {settings.supabase_service_role_key[:20] if settings.supabase_service_role_key else 'None'}...")
    except Exception as e:
        print(f"\n❌ Error getting settings: {e}")

if __name__ == "__main__":
    main()
