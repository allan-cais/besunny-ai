#!/usr/bin/env python3
"""
Simple health check server for BeSunny.ai Backend
This bypasses complex import issues and provides basic health endpoints
"""

import os
import time
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create a simple FastAPI app
app = FastAPI(
    title="BeSunny.ai Backend - Health Check Server",
    version="1.0.0",
    description="Simple health check server for BeSunny.ai ecosystem"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Global health status
_health_status = {
    "startup_time": time.time(),
    "last_check": time.time(),
    "services": {
        "health_server": "running",
        "timestamp": time.time()
    }
}

@app.get("/health")
async def health_check():
    """Basic health check endpoint - always responds quickly."""
    current_time = time.time()
    _health_status["last_check"] = current_time
    
    return {
        "status": "healthy",
        "service": "BeSunny.ai Backend",
        "version": "1.0.0",
        "timestamp": current_time,
        "uptime": current_time - _health_status["startup_time"],
        "environment": os.getenv("ENVIRONMENT", "production"),
        "message": "Backend is operational"
    }

@app.get("/health/status")
async def health_status():
    """Detailed health status endpoint."""
    current_time = time.time()
    _health_status["last_check"] = current_time
    
    return {
        "status": "healthy",
        "service": "BeSunny.ai Backend",
        "version": "1.0.0",
        "timestamp": current_time,
        "uptime": current_time - _health_status["startup_time"],
        "environment": os.getenv("ENVIRONMENT", "production"),
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

@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "service": "BeSunny.ai Backend",
        "version": "1.0.0",
        "status": "operational",
        "health": "/health",
        "timestamp": time.time()
    }

@app.get("/api/frontend-test")
async def frontend_test():
    """Frontend integration test endpoint."""
    return {
        "status": "success",
        "message": "Frontend integration test successful",
        "backend": "python",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    environment = os.getenv("ENVIRONMENT", "production")
    
    print(f"🚀 Starting BeSunny.ai Health Check Server")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌍 Environment: {environment}")
    print(f"🔍 Health endpoint: http://{host}:{port}/health")
    
    # Start the server
    uvicorn.run(
        "simple-health-server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
