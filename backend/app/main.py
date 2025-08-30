"""
Main FastAPI application for BeSunny.ai Python backend.
Optimized for maximum efficiency and reliability.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import logging
import structlog
import os
from pathlib import Path

from app.core.config import get_settings, is_development

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global health status
_health_status = {
    "startup_time": time.time(),
    "last_check": time.time(),
    "services": {}
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - lightweight and efficient."""
    logger.info("Starting BeSunny.ai Python Backend")
    
    try:
        # Initialize Supabase client
        try:
            from app.core.supabase_config import get_supabase_config
            supabase_config = get_supabase_config()
            if supabase_config.initialize():
                logger.info("Supabase client initialized successfully")
                _health_status["services"]["supabase"] = "initialized"
            else:
                logger.warning("Supabase client initialization failed")
                _health_status["services"]["supabase"] = "failed"
        except Exception as e:
            logger.error(f"Supabase initialization error: {e}")
            _health_status["services"]["supabase"] = "error"
        
        # Start background token refresh task
        try:
            # Create a simple background task that runs every 5 minutes
            asyncio.create_task(_run_token_refresh_background())
            logger.info("Background token refresh task started successfully")
            _health_status["services"]["token_refresh"] = "started"
        except Exception as e:
            logger.warning(f"Background token refresh task failed to start: {e}")
            _health_status["services"]["token_refresh"] = "failed"
        
        # Mark startup as successful
        _health_status["startup_time"] = time.time()
        _health_status["last_check"] = time.time()
        _health_status["services"]["startup"] = "completed"
        
        logger.info("Application startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        _health_status["services"]["startup"] = "failed"
        raise
    
    finally:
        logger.info("Shutting down BeSunny.ai Python Backend")
        
        # Stop background services
        try:
            # Cancel any running background tasks
            for task in asyncio.all_tasks():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            logger.info("Background tasks cancelled")
        except Exception as e:
            logger.error(f"Error stopping background tasks: {e}")
        
        _health_status["services"]["shutdown"] = "completed"

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
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.cors_origins == "*" else settings.cors_origins.split(","),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for production
    if not is_development():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]
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
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Only log in development or if explicitly enabled
            if is_development():
                logger.info(
                    "Request completed",
                    method=request.method,
                    url=str(request.url),
                    status_code=response.status_code,
                    process_time=process_time,
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=process_time,
            )
            raise
    
    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    # Include API routers
    try:
        from .api.v1 import router as api_v1_router
    except ImportError:
        # Fallback for direct execution
        from app.api.v1 import router as api_v1_router
    app.include_router(api_v1_router, prefix="/api/v1")
    
    # Mount static files if they exist
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================
    
    async def _run_token_refresh_background():
        """Simple background task that refreshes tokens every 5 minutes."""
        try:
            while True:
                try:
                    # Call the token refresh function
                    from app.services.auth.simple_token_refresh import refresh_expiring_tokens
                    result = await refresh_expiring_tokens()
                    
                    if result.get('success'):
                        logger.info("Background token refresh completed successfully")
                    else:
                        logger.warning(f"Background token refresh failed: {result.get('message', 'Unknown error')}")
                    
                    # Wait 5 minutes before next refresh
                    await asyncio.sleep(300)
                    
                except Exception as e:
                    logger.error(f"Background token refresh error: {e}")
                    # Wait 1 minute before retrying
                    await asyncio.sleep(60)
                    
        except asyncio.CancelledError:
            logger.info("Background token refresh task cancelled")
        except Exception as e:
            logger.error(f"Background token refresh task failed: {e}")
    
    # ============================================================================
    # OPTIMIZED HEALTH CHECK ENDPOINTS
    # ============================================================================
    
    @app.get("/health")
    async def health_check():
        """Lightweight health check endpoint - always responds quickly."""
        current_time = time.time()
        _health_status["last_check"] = current_time
        
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": current_time,
            "uptime": current_time - _health_status["startup_time"],
            "environment": settings.environment,
            "message": "Backend is operational"
        }
    
    @app.get("/health/status")
    async def health_status():
        """Detailed health status endpoint."""
        current_time = time.time()
        _health_status["last_check"] = current_time
        
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": current_time,
            "uptime": current_time - _health_status["startup_time"],
            "environment": settings.environment,
            "services": _health_status["services"],
            "message": "Backend is operational"
        }
    
    @app.get("/health/ready")
    async def health_ready():
        """Readiness probe for Kubernetes/container orchestration."""
        return {
            "status": "ready",
            "timestamp": time.time(),
            "message": "Backend is ready to receive traffic"
        }
    
    @app.get("/health/live")
    async def health_live():
        """Liveness probe for Kubernetes/container orchestration."""
        return {
            "status": "alive",
            "timestamp": time.time(),
            "message": "Backend is alive and running"
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic information."""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "operational",
            "docs": "/docs" if is_development() else None,
            "health": "/health",
            "timestamp": time.time()
        }
    
    # Frontend integration test endpoint
    @app.get("/api/frontend-test")
    async def frontend_test():
        """Frontend integration test endpoint."""
        return {
            "status": "success",
            "message": "Frontend integration test successful",
            "backend": "python",
            "timestamp": time.time()
        }
    
    # Authentication test endpoint
    @app.get("/api/auth-test")
    async def auth_test():
        """Test endpoint to verify authentication is working."""
        return {
            "status": "success",
            "message": "Authentication test endpoint accessible",
            "backend": "python",
            "timestamp": time.time()
        }
    
    # Background service status endpoint
    @app.get("/api/background-services/status")
    async def background_services_status():
        """Get status of background services."""
        try:
            from app.services.auth.simple_token_refresh import get_service_status
            service_status = await get_service_status()
            return {
                "status": "success",
                "background_services": {
                    "token_refresh": service_status
                },
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    # Manual token refresh trigger endpoint
    @app.post("/api/background-services/refresh-tokens")
    async def manual_token_refresh():
        """Manually trigger token refresh."""
        try:
            from app.services.auth.simple_token_refresh import refresh_expiring_tokens
            result = await refresh_expiring_tokens()
            return {
                "status": "success",
                "result": result,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    logger.info("FastAPI application configured successfully")
    return app

# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=is_development(),
        workers=settings.workers if not is_development() else 1,
        log_level=settings.log_level.lower(),
    )
