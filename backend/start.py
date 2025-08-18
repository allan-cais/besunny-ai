#!/usr/bin/env python3
"""
Simple startup script for Railway deployment.
This script provides a minimal way to start the backend without complex dependencies.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main startup function."""
    try:
        # Set default environment variables if not present
        os.environ.setdefault('ENVIRONMENT', 'production')
        os.environ.setdefault('DEBUG', 'false')
        os.environ.setdefault('HOST', '0.0.0.0')
        os.environ.setdefault('PORT', '8000')
        os.environ.setdefault('WORKERS', '1')
        os.environ.setdefault('LOG_LEVEL', 'INFO')
        os.environ.setdefault('SECRET_KEY', 'railway-staging-secret-key')
        os.environ.setdefault('CORS_ORIGINS', '*')
        os.environ.setdefault('CORS_ALLOW_CREDENTIALS', 'false')
        
        # Import and run uvicorn
        import uvicorn
        from app.main import app
        
        port = int(os.environ.get('PORT', 8000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🚀 Starting BeSunny.ai Backend on {host}:{port}")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This usually means some dependencies are missing.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
