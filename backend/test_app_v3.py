#!/usr/bin/env python3
"""
Test app v3 - Adding configuration system back
This app includes the config loading from main.py but skips complex services
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import os
from typing import Optional

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings:
    """Basic settings class for the test app."""
    
    def __init__(self):
        self.app_name: str = "BeSunny.ai Backend v3"
        self.app_version: str = "1.0.0"
        self.environment: str = os.environ.get('ENVIRONMENT', 'production')
        self.debug: bool = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.host: str = os.environ.get('HOST', '0.0.0.0')
        self.port: int = int(os.environ.get('PORT', 8000))
        self.workers: int = int(os.environ.get('WORKERS', '1'))
        self.log_level: str = os.environ.get('LOG_LEVEL', 'INFO')
        self.secret_key: str = os.environ.get('SECRET_KEY', 'test-secret-key')
        self.cors_origins: list = os.environ.get('CORS_ORIGINS', '*').split(',')
        self.cors_allow_credentials: bool = os.environ.get('CORS_ALLOW_CREDENTIALS', 'false').lower() == 'true'
        
        # Log configuration
        logger.info(f"Configuration loaded:")
        logger.info(f"  App: {self.app_name} v{self.app_version}")
        logger.info(f"  Environment: {self.environment}")
        logger.info(f"  Debug: {self.debug}")
        logger.info(f"  Host: {self.host}")
        logger.info(f"  Port: {self.port}")
        logger.info(f"  Workers: {self.workers}")
        logger.info(f"  Log Level: {self.log_level}")
        logger.info(f"  CORS Origins: {self.cors_origins}")
        logger.info(f"  CORS Credentials: {self.cors_allow_credentials}")

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

def is_development() -> bool:
    """Check if running in development mode."""
    return get_settings().environment == 'development'

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Python backend services for BeSunny.ai ecosystem",
        docs_url="/docs" if is_development() else None,
        redoc_url="/redoc" if is_development() else None,
        openapi_url="/openapi.json" if is_development() else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url}"
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url} - {response.status_code} ({process_time:.3f}s)"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url} - Error: {str(e)} ({process_time:.3f}s)"
            )
            raise
    
    # Add exception handlers
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        settings = get_settings()
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "timestamp": time.time(),
            "message": "Backend is running successfully with configuration system"
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        settings = get_settings()
        return {
            "message": f"Welcome to {settings.app_name}",
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "environment": settings.environment,
            "debug": settings.debug,
            "note": "Configuration system loaded - no complex services yet"
        }
    
    # Configuration endpoint (for debugging)
    @app.get("/config")
    async def get_config():
        """Get current configuration (development only)."""
        if not is_development():
            return {"message": "Configuration endpoint not available in production"}
        
        settings = get_settings()
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug,
            "host": settings.host,
            "port": settings.port,
            "workers": settings.workers,
            "log_level": settings.log_level,
            "cors_origins": settings.cors_origins,
            "cors_allow_credentials": settings.cors_allow_credentials
        }
    
    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    print(f"🚀 Starting {settings.app_name} on {settings.host}:{settings.port}")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"📝 Log level: {settings.log_level}")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True
    )
