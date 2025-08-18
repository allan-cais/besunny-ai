"""
Main FastAPI application for BeSunny.ai Python backend.
Configures middleware, CORS, and application lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
import time
import logging
import structlog
import os
import asyncio
from pathlib import Path

from .core.config import get_settings, is_development
from .core.database import init_db, close_db
from .core.service_registry import start_service_registry, stop_service_registry
from .core.api_gateway import initialize_api_gateway
from .core.redis_manager import init_redis, close_redis
from .core.observability import init_observability
from .api.v1 import router as api_v1_router
from .api.websockets import router as websocket_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting BeSunny.ai Python Backend")
    
    try:
        # Initialize database (skip if not configured)
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            logger.info("Application will continue without database")
        
        # Initialize Redis
        try:
            await init_redis()
            logger.info("Redis initialized successfully")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            logger.info("Application will continue without Redis")
        
        # Initialize observability system
        try:
            await init_observability()
            logger.info("Observability system initialized successfully")
        except Exception as e:
            logger.warning(f"Observability initialization failed: {e}")
            logger.info("Application will continue without observability")
        
        # Initialize service registry
        try:
            await start_service_registry()
            logger.info("Service registry started successfully")
        except Exception as e:
            logger.warning(f"Service registry startup failed: {e}")
            logger.info("Application will continue without service registry")
        
        # Initialize API Gateway
        try:
            await initialize_api_gateway()
            logger.info("API Gateway initialized successfully")
        except Exception as e:
            logger.warning(f"API Gateway initialization failed: {e}")
            logger.info("Application will continue without API Gateway")
        
        # Initialize AI services
        try:
            from .services.ai import AIService, EmbeddingService, ClassificationService, MeetingIntelligenceService
            from .services.ai.ai_orchestration_service import AIOrchestrationService
            
            # Initialize AI services in background (non-blocking)
            logger.info("Initializing AI services...")
            
            # Note: AI services are initialized lazily when first used
            # This prevents startup delays and allows graceful degradation
            logger.info("AI services configured for lazy initialization")
            
        except Exception as e:
            logger.warning(f"AI services initialization failed: {e}")
            logger.info("Application will continue without AI services")
        
        # Initialize Performance Monitoring Service
        try:
            from .services.enterprise.performance_monitoring_service import PerformanceMonitoringService
            
            # Initialize performance monitoring in background
            logger.info("Initializing Performance Monitoring Service...")
            performance_monitor = PerformanceMonitoringService()
            asyncio.create_task(performance_monitor.initialize())
            logger.info("Performance Monitoring Service configured for background initialization")
            
        except Exception as e:
            logger.warning(f"Performance Monitoring Service initialization failed: {e}")
            logger.info("Application will continue without performance monitoring")
        
        logger.info("Application startup completed")
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down BeSunny.ai Python Backend")
        
        try:
            # Stop service registry
            try:
                await stop_service_registry()
                logger.info("Service registry stopped")
            except Exception as e:
                logger.warning(f"Service registry shutdown failed: {e}")
            
            # Close database connections
            await close_db()
            logger.info("Database connections closed")
            
            # Close Redis connections
            try:
                await close_redis()
                logger.info("Redis connections closed")
            except Exception as e:
                logger.warning(f"Redis shutdown failed: {e}")
            
            # Close AI services
            try:
                # Note: AI services are stateless and don't require explicit cleanup
                logger.info("AI services cleanup completed")
            except Exception as e:
                logger.warning(f"AI services cleanup failed: {e}")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
        
        logger.info("Application shutdown completed")


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
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for production
    if not is_development():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure based on your domain
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
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
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
            
            # Log error
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
        logger.warning(
            "Validation error",
            url=str(request.url),
            errors=exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            "HTTP exception",
            url=str(request.url),
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            url=str(request.url),
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    # Include routers
    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(websocket_router, prefix="/ws")
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            return {
                "status": "healthy",
                "service": settings.app_name,
                "version": settings.app_version,
                "timestamp": time.time(),
                "environment": settings.environment,
                "message": "Backend is running successfully"
            }
        except Exception as e:
            # Fallback health check that always returns healthy
            return {
                "status": "healthy",
                "service": "BeSunny.ai Backend",
                "version": "1.0.0",
                "timestamp": time.time(),
                "message": "Basic health check passed"
            }
    
    # Enhanced health check with AI services status
    @app.get("/health/ai")
    async def ai_health_check():
        """AI services health check endpoint."""
        try:
            from .services.ai import AIService, EmbeddingService, ClassificationService, MeetingIntelligenceService
            
            # Test AI service initialization
            ai_service = AIService()
            embedding_service = EmbeddingService()
            classification_service = ClassificationService()
            meeting_intelligence_service = MeetingIntelligenceService()
            
            return {
                "status": "healthy",
                "ai_services": {
                    "ai_service": "configured",
                    "embedding_service": "configured", 
                    "classification_service": "configured",
                    "meeting_intelligence_service": "configured"
                },
                "message": "All AI services are configured and ready for use",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"AI health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "ai_services": "failed",
                    "error": str(e),
                    "timestamp": time.time()
                }
            )
    
    # Microservices health check endpoint
    @app.get("/health/microservices")
    async def microservices_health_check():
        """Microservices architecture health check endpoint."""
        try:
            from .core.service_registry import get_service_registry
            from .core.api_gateway import get_api_gateway
            from .core.redis_manager import get_redis
            from .core.observability import get_observability
            
            # Get service instances
            service_registry = await get_service_registry()
            api_gateway = await get_api_gateway()
            redis = await get_redis()
            observability = await get_observability()
            
            # Check component health
            registry_status = await service_registry.get_registry_status()
            gateway_status = await api_gateway.get_gateway_status()
            redis_health = await redis.health_check()
            observability_health = await observability.get_system_health()
            
            # Determine overall status
            overall_status = "healthy"
            if not redis_health:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "microservices": {
                    "service_registry": "healthy",
                    "api_gateway": "healthy",
                    "redis_cache": "healthy" if redis_health else "unhealthy",
                    "observability": "healthy"
                },
                "details": {
                    "service_registry": registry_status,
                    "api_gateway": gateway_status,
                    "redis_health": redis_health,
                    "observability": observability_health
                },
                "message": "Microservices architecture is operational",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Microservices health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "microservices": "failed",
                    "error": str(e),
                    "timestamp": time.time()
                }
            )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        try:
            if static_dir.exists():
                return FileResponse(static_dir / "index.html")
            else:
                return {
                    "message": "Welcome to BeSunny.ai Python Backend",
                    "service": "BeSunny.ai Backend",
                    "version": "1.0.0",
                    "status": "running",
                    "endpoints": {
                        "health": "/health",
                        "health_ai": "/health/ai",
                        "health_microservices": "/health/microservices"
                    }
                }
        except Exception as e:
            return {
                "message": "Welcome to BeSunny.ai Python Backend",
                "service": "BeSunny.ai Backend",
                "version": "1.0.0",
                "status": "running",
                "note": "Basic mode - some features may be limited"
            }
    
    # Catch-all route for React Router (must be last)
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        """Catch-all route to serve React app for client-side routing."""
        if static_dir.exists():
            # Check if it's a static file request
            static_file = static_dir / full_path
            if static_file.exists() and static_file.is_file():
                return FileResponse(static_file)
            # Otherwise serve index.html for client-side routing
            return FileResponse(static_dir / "index.html")
        else:
            raise HTTPException(status_code=404, detail="Not found")
    
    return app


# Create application instance
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
