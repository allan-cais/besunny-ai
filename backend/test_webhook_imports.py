#!/usr/bin/env python3
"""
Test webhook imports to ensure they work correctly.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_webhook_imports():
    """Test webhook imports."""
    try:
        print("Testing webhook imports...")
        
        # Test importing the gmail webhook
        from app.api.v1.webhooks.gmail_webhook import router as gmail_router
        print("✅ Gmail webhook import successful")
        
        # Test importing the webhooks module
        from app.api.v1.webhooks import __init__ as webhooks_init
        print("✅ Webhooks init import successful")
        
        # Test importing the main API router
        from app.api.v1 import router as api_router
        print("✅ API v1 router import successful")
        
        print("🎉 All webhook imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Webhook import failed: {e}")
        return False

if __name__ == "__main__":
    test_webhook_imports()
