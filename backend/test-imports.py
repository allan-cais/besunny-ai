#!/usr/bin/env python3
"""
Test script to check which imports are working and which are failing.
This helps identify missing dependencies.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test various imports to see what's working."""
    print("🧪 Testing imports...")
    print("=" * 50)
    
    # Test basic Python modules
    try:
        import os
        print("✅ os - OK")
    except ImportError as e:
        print(f"❌ os - FAILED: {e}")
    
    try:
        import sys
        print("✅ sys - OK")
    except ImportError as e:
        print(f"❌ sys - FAILED: {e}")
    
    try:
        import pathlib
        print("✅ pathlib - OK")
    except ImportError as e:
        print(f"❌ pathlib - FAILED: {e}")
    
    # Test FastAPI and related
    try:
        import fastapi
        print("✅ fastapi - OK")
    except ImportError as e:
        print(f"❌ fastapi - FAILED: {e}")
    
    try:
        import uvicorn
        print("✅ uvicorn - OK")
    except ImportError as e:
        print(f"❌ uvicorn - FAILED: {e}")
    
    try:
        import pydantic
        print("✅ pydantic - OK")
    except ImportError as e:
        print(f"❌ pydantic - FAILED: {e}")
    
    # Test database related
    try:
        import sqlalchemy
        print("✅ sqlalchemy - OK")
    except ImportError as e:
        print(f"❌ sqlalchemy - FAILED: {e}")
    
    try:
        import psycopg2
        print("✅ psycopg2 - OK")
    except ImportError as e:
        print(f"❌ psycopg2 - FAILED: {e}")
    
    # Test Supabase
    try:
        import supabase
        print("✅ supabase - OK")
    except ImportError as e:
        print(f"❌ supabase - FAILED: {e}")
    
    try:
        from supabase import create_client
        print("✅ supabase.create_client - OK")
    except ImportError as e:
        print(f"❌ supabase.create_client - FAILED: {e}")
    
    # Test other dependencies
    try:
        import redis
        print("✅ redis - OK")
    except ImportError as e:
        print(f"❌ redis - FAILED: {e}")
    
    try:
        import httpx
        print("✅ httpx - OK")
    except ImportError as e:
        print(f"❌ httpx - FAILED: {e}")
    
    try:
        import structlog
        print("✅ structlog - OK")
    except ImportError as e:
        print(f"❌ structlog - FAILED: {e}")
    
    print("\n" + "=" * 50)
    print("Import test completed!")

if __name__ == "__main__":
    test_imports()
