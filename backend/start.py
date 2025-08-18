#!/usr/bin/env python3
"""
Main startup script for BeSunny.ai Backend
This is the single entry point for starting the application.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def set_environment():
    """Set environment variables for the application."""
    # Application settings
    os.environ.setdefault("APP_NAME", "BeSunny.ai Backend")
    os.environ.setdefault("APP_VERSION", "1.0.0")
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("DEBUG", "false")
    
    # Server settings
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("WORKERS", "1")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
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
    try:
        # Set environment variables
        set_environment()
        
        # Import and run uvicorn
        import uvicorn
        
        # Fix Python path for relative imports
        import sys
        from pathlib import Path
        
        # Add the backend directory to Python path so relative imports work
        backend_dir = Path(__file__).parent
        sys.path.insert(0, str(backend_dir))
        
        # Now import the app with relative imports working
        from app.main import app
        
        port = int(os.environ.get('PORT', 8000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🚀 Starting BeSunny.ai Backend on {host}:{port}")
        print(f"📊 Environment: {os.environ.get('ENVIRONMENT', 'unknown')}")
        print(f"🔧 Debug mode: {os.environ.get('DEBUG', 'unknown')}")
        print(f"🌐 CORS origins: {os.environ.get('CORS_ORIGINS', 'unknown')}")
        print(f"📝 Version: {os.environ.get('APP_VERSION', 'unknown')}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
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
