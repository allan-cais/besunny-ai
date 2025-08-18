#!/usr/bin/env python3
"""
Test app v2 - Adding basic FastAPI structure back
This app includes the basic app setup from main.py but skips complex services
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="BeSunny.ai Backend v2",
        version="1.0.0",
        description="Python backend services for BeSunny.ai ecosystem"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
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
        return {
            "status": "healthy",
            "service": "BeSunny.ai Backend v2",
            "version": "1.0.0",
            "timestamp": time.time(),
            "message": "Backend is running successfully with basic structure"
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to BeSunny.ai Python Backend v2",
            "service": "BeSunny.ai Backend",
            "version": "1.0.0",
            "status": "running",
            "note": "Basic structure loaded - no complex services yet"
        }
    
    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting BeSunny.ai Backend v2 on {host}:{port}")
    print(f"📊 Environment: {os.environ.get('ENVIRONMENT', 'unknown')}")
    print(f"🔧 Debug mode: {os.environ.get('DEBUG', 'unknown')}")
    
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)
