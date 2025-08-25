#!/usr/bin/env python3
"""
Test basic imports to identify any import issues.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_basic_imports():
    """Test basic imports."""
    try:
        print("Testing basic imports...")
        
        # Test core imports
        from app.core.config import get_settings
        print("✅ Core config import successful")
        
        from app.core.database import get_supabase
        print("✅ Database import successful")
        
        # Test model imports
        from app.models.schemas.email import GmailMessage, EmailProcessingResult
        print("✅ Email schema imports successful")
        
        # Test service imports
        from app.services.email.email_service import EmailProcessingService
        print("✅ Email service import successful")
        
        print("🎉 All basic imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    test_basic_imports()
