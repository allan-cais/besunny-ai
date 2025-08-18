#!/usr/bin/env python3
"""
Startup script for BeSunny.ai Backend v17
Sets environment variables and starts the server
"""

import os
import sys
import subprocess

def set_environment():
    """Set environment variables for the application."""
    # Application settings
    os.environ.setdefault("APP_NAME", "BeSunny.ai Backend")
    os.environ.setdefault("APP_VERSION", "17.0.0")
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("DEBUG", "false")
    
    # Server settings
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("WORKERS", "1")
    
    # Security
    os.environ.setdefault("SECRET_KEY", "railway-staging-secret-key-change-in-production")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    
    # CORS
    os.environ.setdefault("CORS_ORIGINS", "*")
    os.environ.setdefault("CORS_ALLOW_CREDENTIALS", "false")
    
    # Database defaults
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/dbname")
    os.environ.setdefault("DATABASE_ECHO", "false")
    os.environ.setdefault("DATABASE_POOL_SIZE", "5")
    os.environ.setdefault("DATABASE_MAX_OVERFLOW", "10")
    
    # Redis defaults
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("REDIS_MAX_CONNECTIONS", "10")
    
    # Supabase defaults
    os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "placeholder-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder-key")

def main():
    """Main startup function."""
    print("🚀 Starting BeSunny.ai Backend v17...")
    
    # Set environment variables
    set_environment()
    
    # Import and run the test app
    try:
        from test_app_v17 import start_server
        start_server()
    except ImportError as e:
        print(f"❌ Failed to import test_app_v17: {e}")
        print("💡 Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
