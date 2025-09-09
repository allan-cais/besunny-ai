"""
Webhook processor API endpoints.
Handles webhook processing and bot state management.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import logging

from ...core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/start")
async def start_webhook_processor(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start the webhook processor service."""
    try:
        from ...services.attendee.webhook_processor_service import webhook_processor_service
        
        if webhook_processor_service.is_running:
            return {
                "success": False,
                "message": "Webhook processor service is already running"
            }
        
        # Start the service in background
        background_tasks.add_task(webhook_processor_service.start)
        
        return {
            "success": True,
            "message": "Webhook processor service started"
        }
        
    except Exception as e:
        logger.error(f"Error starting webhook processor: {e}")
        raise HTTPException(status_code=500, detail="Failed to start webhook processor")

@router.post("/stop")
async def stop_webhook_processor(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop the webhook processor service."""
    try:
        from ...services.attendee.webhook_processor_service import webhook_processor_service
        
        await webhook_processor_service.stop()
        
        return {
            "success": True,
            "message": "Webhook processor service stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping webhook processor: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop webhook processor")

@router.get("/status")
async def get_webhook_processor_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get webhook processor service status."""
    try:
        from ...services.attendee.webhook_processor_service import webhook_processor_service
        
        status = await webhook_processor_service.get_service_status()
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook processor status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get webhook processor status")

@router.post("/process-once")
async def process_webhook_logs_once(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Process webhook logs once (manual trigger)."""
    try:
        from ...services.attendee.webhook_processor_service import webhook_processor_service
        
        processed_count = await webhook_processor_service.process_webhook_logs_once()
        
        return {
            "success": True,
            "processed_count": processed_count,
            "message": f"Processed {processed_count} webhook logs"
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook logs")

@router.get("/summary")
async def get_webhook_logs_summary(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get webhook logs summary."""
    try:
        from ...services.attendee.webhook_processor_service import webhook_processor_service
        
        summary = await webhook_processor_service.get_webhook_logs_summary()
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook logs summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get webhook logs summary")

@router.get("/bot-status-summary")
async def get_bot_status_summary(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get bot status summary for the current user."""
    try:
        from ...services.attendee.bot_state_service import BotStateService
        
        bot_state_service = BotStateService()
        status_summary = await bot_state_service.get_bot_status_summary(current_user['id'])
        
        return {
            "success": True,
            "bot_status_summary": status_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting bot status summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot status summary")
