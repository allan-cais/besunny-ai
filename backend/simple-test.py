#!/usr/bin/env python3
"""
Simple test to isolate the import issue.
"""

print("🚀 Starting simple import test...")

try:
    print("1. Testing basic Python imports...")
    import os
    import sys
    print("✅ Basic imports OK")
    
    print("2. Testing supabase import...")
    import supabase
    print("✅ Supabase import OK")
    
    print("3. Testing supabase client creation...")
    from supabase import create_client
    print("✅ Supabase create_client OK")
    
    print("4. Testing app import...")
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Try to import the app
    from app.main import app
    print("✅ App import OK")
    
    print("🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"Python path: {sys.path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Other error: {e}")
    sys.exit(1)
