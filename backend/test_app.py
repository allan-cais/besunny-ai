#!/usr/bin/env python3
"""
Minimal test app for Railway deployment.
This app only has a health endpoint to test basic functionality.
"""

from fastapi import FastAPI
import time

app = FastAPI(title="BeSunny.ai Test Backend")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "BeSunny.ai Test Backend is running",
        "timestamp": time.time(),
        "status": "healthy"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "BeSunny.ai Test Backend",
        "timestamp": time.time(),
        "message": "Backend is running successfully"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Test Backend on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
