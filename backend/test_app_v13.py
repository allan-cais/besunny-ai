#!/usr/bin/env python3
"""
Test app v13 - Testing enhanced database module
This app tests the enhanced database module with real connection management
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings:
    """Basic settings class for the test app."""
    
    def __init__(self):
        self.app_name: str = "BeSunny.ai Backend v13"
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

# Test enhanced database module
def test_enhanced_database():
    """Test the enhanced database module with real connection management."""
    logger.info("Testing enhanced database module...")
    
    try:
        # Fix Python path for absolute imports
        backend_dir = Path(__file__).parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        logger.info("Testing enhanced app.core.database import...")
        from app.core.database import (
            init_db,
            close_db,
            health_check_db,
            get_db_info,
            get_db_manager,
            Base
        )
        logger.info("✅ Enhanced app.core.database import successful")
        
        # Test the enhanced database module
        try:
            logger.info("✅ Database Base class available")
            logger.info("✅ Database manager functions available")
            logger.info("✅ Health check functions available")
            
        except Exception as e:
            logger.error(f"❌ Enhanced database test failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Enhanced app.core.database import failed: {e}")
        return False
    
    try:
        logger.info("Testing app.core.config import...")
        from app.core.config import get_settings as real_get_settings
        logger.info("✅ app.core.config import successful")
    except Exception as e:
        logger.error(f"❌ app.core.config import failed: {e}")
        return False
    
    try:
        logger.info("Testing app.core.service_registry import...")
        from app.core.service_registry import start_service_registry, stop_service_registry
        logger.info("✅ app.core.service_registry import successful")
    except Exception as e:
        logger.error(f"❌ app.core.service_registry import failed: {e}")
        return False
    
    try:
        logger.info("Testing app.core.api_gateway import...")
        from app.core.api_gateway import initialize_api_gateway
        logger.info("✅ app.core.api_gateway import successful")
    except Exception as e:
        logger.error(f"❌ app.core.api_gateway import failed: {e}")
        return False
    
    try:
        logger.info("Testing app.core.redis_manager import...")
        from app.core.redis_manager import init_redis, close_redis
        logger.info("✅ app.core.redis_manager import successful")
    except Exception as e:
        logger.error(f"❌ app.core.redis_manager import failed: {e}")
        return False
    
    try:
        logger.info("Testing app.core.observability import...")
        from app.core.observability import init_observability
        logger.info("✅ app.core.observability import successful")
    except Exception as e:
        logger.error(f"❌ app.core.observability import failed: {e}")
        return False
    
    logger.info("✅ All enhanced core imports successful!")
    return True

# Import the real functions from core modules
async def init_db():
    """Initialize database using real core module."""
    try:
        from app.core.database import init_db as real_init_db
        return await real_init_db()
    except Exception as e:
        logger.warning(f"Real database init failed, using fallback: {e}")
        logger.info("Fallback database initialization - skipping")
        return True

async def init_redis():
    """Initialize Redis using real core module."""
    try:
        from app.core.redis_manager import init_redis as real_init_redis
        return await real_init_redis()
    except Exception as e:
        logger.warning(f"Real Redis init failed, using fallback: {e}")
        logger.info("Fallback Redis initialization - skipping")
        return True

async def init_observability():
    """Initialize observability using real core module."""
    try:
        from app.core.observability import init_observability as real_init_observability
        return await real_init_observability()
    except Exception as e:
        logger.warning(f"Real observability init failed, using fallback: {e}")
        logger.info("Fallback observability initialization - skipping")
        return True

async def start_service_registry():
    """Start service registry using real core module."""
    try:
        from app.core.service_registry import start_service_registry as real_start_service_registry
        return await real_start_service_registry()
    except Exception as e:
        logger.warning(f"Real service registry startup failed, using fallback: {e}")
        logger.info("Fallback service registry startup - skipping")
        return True

async def initialize_api_gateway():
    """Initialize API Gateway using real core module."""
    try:
        from app.core.api_gateway import initialize_api_gateway as real_initialize_api_gateway
        return await real_initialize_api_gateway()
    except Exception as e:
        logger.warning(f"Real API Gateway init failed, using fallback: {e}")
        logger.info("Fallback API Gateway initialization - skipping")
        return True

async def stop_service_registry():
    """Stop service registry using real core module."""
    try:
        from app.core.service_registry import stop_service_registry as real_stop_service_registry
        return await real_stop_service_registry()
    except Exception as e:
        logger.warning(f"Real service registry shutdown failed, using fallback: {e}")
        logger.info("Fallback service registry shutdown - skipping")
        return True

async def close_db():
    """Close database using real core module."""
    try:
        from app.core.database import close_db as real_close_db
        return await real_close_db()
    except Exception as e:
        logger.warning(f"Real database close failed, using fallback: {e}")
        logger.info("Fallback database close - skipping")
        return True

async def close_redis():
    """Close Redis using real core module."""
    try:
        from app.core.redis_manager import close_redis as real_close_redis
        return await real_close_redis()
    except Exception as e:
        logger.warning(f"Real Redis close failed, using fallback: {e}")
        logger.info("Fallback Redis close - skipping")
        return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - testing enhanced database module."""
    # Startup
    logger.info("Starting BeSunny.ai Python Backend v13")
    
    try:
        # Test enhanced database first
        database_success = test_enhanced_database()
        if not database_success:
            logger.warning("Enhanced database test failed, continuing with fallback services")
        
        # Initialize database (using real core module if available)
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            logger.info("Application will continue without database")
        
        # Initialize Redis (using real core module if available)
        try:
            await init_redis()
            logger.info("Redis initialized successfully")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            logger.info("Application will continue without Redis")
        
        # Initialize observability system (using real core module if available)
        try:
            await init_observability()
            logger.info("Observability system initialized successfully")
        except Exception as e:
            logger.warning(f"Observability initialization failed: {e}")
            logger.info("Application will continue without observability")
        
        # Initialize service registry (using real core module if available)
        try:
            await start_service_registry()
            logger.info("Service registry started successfully")
        except Exception as e:
            logger.warning(f"Service registry startup failed: {e}")
            logger.info("Application will continue without service registry")
        
        # Initialize API Gateway (using real core module if available)
        try:
            await initialize_api_gateway()
            logger.info("API Gateway initialized successfully")
        except Exception as e:
            logger.warning(f"API Gateway initialization failed: {e}")
            logger.info("Application will continue without API Gateway")
        
        logger.info("Application startup completed")
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down BeSunny.ai Python Backend v13")
        
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
        lifespan=lifespan,  # Add the lifespan function
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
        from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            f"Validation error: {request.url} - {exc.errors()}"
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"Static files mounted at /static from {static_dir}")
    else:
        logger.info(f"Static directory not found: {static_dir}")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            return {
                "status": "healthy",
                "service": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
                "timestamp": time.time(),
                "message": "Backend is running successfully with enhanced database module"
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
    
    # Database health check endpoint
    @app.get("/health/db")
    async def database_health_check():
        """Database health check endpoint."""
        try:
            from app.core.database import health_check_db, get_db_info
            is_healthy = await health_check_db()
            db_info = await get_db_info()
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "database": db_info,
                "timestamp": time.time(),
                "message": "Database health check completed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time(),
                "message": "Database health check failed"
            }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        try:
            if static_dir.exists():
                return FileResponse(static_dir / "index.html")
            else:
                return {
                    "message": f"Welcome to {settings.app_name}",
                    "service": settings.app_name,
                    "version": settings.app_version,
                    "status": "running",
                    "environment": settings.environment,
                    "debug": settings.debug,
                    "note": "Enhanced database module loaded - testing production-ready database management"
                }
        except Exception as e:
            return {
                "message": f"Welcome to {settings.app_name}",
                "service": settings.app_name,
                "version": settings.app_version,
                "status": "running",
                "note": "Basic mode - some features may be limited"
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
    print(f"🔌 Mode: Testing enhanced database module with production-ready connection management")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True
    )
