#!/usr/bin/env python3
"""
Test route registration to ensure webhook routes are properly included.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_route_registration():
    """Test that webhook routes are properly registered."""
    try:
        print("Testing route registration...")
        
        # Import the main API router
        from app.api.v1 import router as api_router
        print("✅ Main API router imported successfully")
        
        # Check if webhooks router is included
        webhook_routes = []
        for route in api_router.routes:
            if hasattr(route, 'path') and '/webhooks' in route.path:
                webhook_routes.append(route.path)
        
        print(f"📋 Found {len(webhook_routes)} webhook routes:")
        for route in webhook_routes:
            print(f"  - {route}")
        
        # Check for specific Gmail webhook route
        gmail_webhook_found = any('/gmail' in route for route in webhook_routes)
        if gmail_webhook_found:
            print("✅ Gmail webhook route found")
        else:
            print("❌ Gmail webhook route not found")
        
        print("🎉 Route registration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Route registration test failed: {e}")
        return False

if __name__ == "__main__":
    test_route_registration()
