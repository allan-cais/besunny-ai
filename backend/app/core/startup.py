"""
Application startup tasks.
Handles background services and initialization.
"""

import logging
import asyncio
from contextlib import asynccontextmanager

from ..services.attendee.webhook_processor_service import webhook_processor_service

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager for startup and shutdown tasks."""
    # Startup
    logger.info("Starting application services...")
    
    try:
        # Start webhook processor service
        webhook_task = asyncio.create_task(webhook_processor_service.start())
        logger.info("Webhook processor service started")
        
        # Store task reference for cleanup
        app.state.webhook_processor_task = webhook_task
        
    except Exception as e:
        logger.error(f"Error starting application services: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application services...")
    
    try:
        # Stop webhook processor service
        await webhook_processor_service.stop()
        
        # Cancel webhook processor task
        if hasattr(app.state, 'webhook_processor_task'):
            app.state.webhook_processor_task.cancel()
            try:
                await app.state.webhook_processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Application services stopped")
        
    except Exception as e:
        logger.error(f"Error stopping application services: {e}")

async def start_background_services():
    """Start background services manually (for testing or manual startup)."""
    try:
        logger.info("Starting background services...")
        
        # Start webhook processor service
        webhook_task = asyncio.create_task(webhook_processor_service.start())
        logger.info("Background services started")
        
        return webhook_task
        
    except Exception as e:
        logger.error(f"Error starting background services: {e}")
        return None

async def stop_background_services():
    """Stop background services manually."""
    try:
        logger.info("Stopping background services...")
        
        # Stop webhook processor service
        await webhook_processor_service.stop()
        
        logger.info("Background services stopped")
        
    except Exception as e:
        logger.error(f"Error stopping background services: {e}")
