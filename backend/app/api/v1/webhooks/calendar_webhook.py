"""
Google Calendar webhook endpoint for BeSunny.ai Python backend.
Handles incoming webhook notifications from Google Calendar.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ....services.calendar.calendar_webhook_handler import CalendarWebhookHandler
from ....models.schemas.calendar import CalendarWebhookPayload
from ....core.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/verify")
async def verify_webhook_challenge(challenge: str):
    """Verify webhook challenge from Google Calendar."""
    try:
        logger.info(f"Calendar webhook verification challenge: {challenge}")
        return challenge
    except Exception as e:
        logger.error(f"Failed to verify webhook challenge: {e}")
        raise HTTPException(status_code=400, detail="Invalid challenge")


@router.post("/")
async def handle_calendar_webhook(request: Request):
    """Handle incoming Google Calendar webhook notifications."""
    try:
        # Get webhook data from request
        webhook_data = await request.json()
        
        # Extract headers for additional context
        headers = dict(request.headers)
        
        # Log webhook receipt
        logger.info("Calendar webhook received", extra={
            "headers": {k: v for k, v in headers.items() if k.lower().startswith('x-goog-')},
            "body": webhook_data
        })
        
        # Process the webhook
        webhook_handler = CalendarWebhookHandler()
        success = await webhook_handler.process_webhook(webhook_data)
        
        if success:
            return JSONResponse(
                content={"status": "success", "message": "Webhook processed successfully"},
                status_code=200
            )
        else:
            # Return 200 to Google even on failure (they don't retry on 4xx/5xx)
            return JSONResponse(
                content={"status": "error", "message": "Webhook processing failed"},
                status_code=200
            )
            
    except Exception as e:
        logger.error(f"Calendar webhook processing error: {e}", exc_info=True)
        # Always return 200 to Google to prevent retries
        return JSONResponse(
            content={
                "status": "error", 
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=200
        )


@router.post("/test")
async def test_calendar_webhook(
    webhook_data: CalendarWebhookPayload,
    background_tasks: BackgroundTasks
):
    """Test calendar webhook processing (for development/testing)."""
    try:
        logger.info("Testing calendar webhook processing", extra={"webhook_data": webhook_data.dict()})
        
        # Process the test webhook
        webhook_handler = CalendarWebhookHandler()
        success = await webhook_handler.process_webhook(webhook_data.dict())
        
        if success:
            return {
                "status": "success",
                "message": "Test webhook processed successfully",
                "webhook_data": webhook_data.dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Test webhook processing failed")
            
    except Exception as e:
        logger.error(f"Test webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Test webhook failed: {str(e)}")


@router.get("/logs")
async def get_calendar_webhook_logs(
    webhook_id: Optional[str] = None,
    limit: int = 100
):
    """Get calendar webhook processing logs."""
    try:
        webhook_handler = CalendarWebhookHandler()
        logs = await webhook_handler.get_webhook_logs(webhook_id, limit)
        
        return {
            "status": "success",
            "logs": logs,
            "total_count": len(logs),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/active")
async def get_active_calendar_webhooks(user_id: Optional[str] = None):
    """Get active calendar webhooks."""
    try:
        webhook_handler = CalendarWebhookHandler()
        webhooks = await webhook_handler.get_active_webhooks(user_id)
        
        return {
            "status": "success",
            "webhooks": webhooks,
            "total_count": len(webhooks)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active webhooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhooks: {str(e)}")


@router.get("/status")
async def get_calendar_webhook_status():
    """Get calendar webhook system status."""
    try:
        supabase = get_supabase()
        
        # Get webhook statistics
        webhook_stats = await supabase.table('calendar_webhooks').select('*').execute()
        active_webhooks = [w for w in webhook_stats.data or [] if w.get('is_active')]
        
        # Get recent webhook activity
        recent_activity = await supabase.table('calendar_webhooks').select('*').order('updated_at', desc=True).limit(10).execute()
        
        return {
            "status": "healthy",
            "service": "calendar-webhooks",
            "statistics": {
                "total_webhooks": len(webhook_stats.data or []),
                "active_webhooks": len(active_webhooks),
                "inactive_webhooks": len(webhook_stats.data or []) - len(active_webhooks)
            },
            "recent_activity": recent_activity.data or [],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook status: {e}")
        return {
            "status": "unhealthy",
            "service": "calendar-webhooks",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }
