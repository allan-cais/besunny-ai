#!/usr/bin/env python3
"""
BeSunny.ai Python Backend Startup Script
Optimized for maximum efficiency and reliability
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Main startup function."""
    # Add the app directory to Python path
    app_dir = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_dir))
    
    # Environment configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # Production optimizations
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        reload = False
        workers = max(1, workers)
        log_level = "warning"
    
    print(f"🚀 Starting BeSunny.ai Python Backend")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"👥 Workers: {workers}")
    print(f"📝 Log Level: {log_level}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if workers > 1 else None,
            log_level=log_level,
            access_log=True,
            use_colors=True,
            loop="asyncio",
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
