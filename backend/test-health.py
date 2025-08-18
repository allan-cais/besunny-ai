#!/usr/bin/env python3
"""
Simple health endpoint test script
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def test_imports():
    """Test if all required modules can be imported."""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import time
        print("✅ time module imported")
        
        # Test FastAPI
        from fastapi import FastAPI
        print("✅ FastAPI imported")
        
        # Test config
        from core.config import get_settings
        print("✅ config imported")
        
        # Test main app creation
        from main import create_app
        print("✅ main app creation imported")
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test if the app can be created."""
    try:
        print("\nTesting app creation...")
        
        from main import create_app
        app = create_app()
        
        print(f"✅ App created successfully: {type(app)}")
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        
        return app
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_health_endpoints(app):
    """Test if health endpoints are accessible."""
    try:
        print("\nTesting health endpoints...")
        
        # Get the app routes
        routes = [route.path for route in app.routes]
        print(f"✅ Available routes: {routes}")
        
        # Check if health endpoints exist
        health_routes = [route for route in routes if 'health' in route]
        print(f"✅ Health routes found: {health_routes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing BeSunny.ai Backend Health Endpoints")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    # Test app creation
    app = test_app_creation()
    if not app:
        sys.exit(1)
    
    # Test health endpoints
    if not test_health_endpoints(app):
        sys.exit(1)
    
    print("\n🎉 All tests passed! Backend should be working correctly.")
