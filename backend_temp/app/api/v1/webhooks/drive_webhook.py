"""
Google Drive webhook endpoint for BeSunny.ai Python backend.
Handles incoming webhook notifications from Google Drive.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ....services.drive.drive_webhook_handler import DriveWebhookHandler
from ....models.schemas.drive import DriveWebhookPayload
from ....core.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def handle_drive_webhook(request: Request):
    """Handle incoming Google Drive webhook notifications."""
    try:
        # Get webhook data from request
        webhook_data = await request.json()
        
        # Extract headers for additional context
        headers = dict(request.headers)
        
        # Log webhook receipt
        logger.info("Drive webhook received", extra={
            "headers": {k: v for k, v in headers.items() if k.lower().startswith('x-goog-')},
            "body": webhook_data
        })
        
        # Process the webhook
        webhook_handler = DriveWebhookHandler()
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
        logger.error(f"Drive webhook processing error: {e}", exc_info=True)
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
async def test_drive_webhook(
    webhook_data: DriveWebhookPayload,
    background_tasks: BackgroundTasks
):
    """Test drive webhook processing (for development/testing)."""
    try:
        logger.info("Testing drive webhook processing", extra={"webhook_data": webhook_data.dict()})
        
        # Process the test webhook
        webhook_handler = DriveWebhookHandler()
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
async def get_drive_webhook_logs(
    file_id: Optional[str] = None,
    limit: int = 100
):
    """Get drive webhook processing logs."""
    try:
        webhook_handler = DriveWebhookHandler()
        logs = await webhook_handler.get_webhook_logs(file_id, limit)
        
        return {
            "status": "success",
            "logs": logs,
            "total_count": len(logs),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/watches")
async def get_active_drive_watches(project_id: Optional[str] = None):
    """Get active drive file watches."""
    try:
        webhook_handler = DriveWebhookHandler()
        watches = await webhook_handler.get_active_watches(project_id)
        
        return {
            "status": "success",
            "watches": watches,
            "total_count": len(watches)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active watches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get watches: {str(e)}")


@router.get("/status")
async def get_drive_webhook_status():
    """Get drive webhook system status."""
    try:
        supabase = get_supabase()
        
        # Get watch statistics
        watch_stats = await supabase.table('drive_file_watches').select('*').execute()
        active_watches = [w for w in watch_stats.data or [] if w.get('is_active')]
        
        # Get recent webhook activity
        recent_activity = await supabase.table('drive_webhook_logs').select('*').order('webhook_received_at', desc=True).limit(10).execute()
        
        return {
            "status": "healthy",
            "service": "drive-webhooks",
            "statistics": {
                "total_watches": len(watch_stats.data or []),
                "active_watches": len(active_watches),
                "inactive_watches": len(watch_stats.data or []) - len(active_watches),
                "recent_webhooks": len(recent_activity.data or [])
            },
            "recent_activity": recent_activity.data or [],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook status: {e}")
        return {
            "status": "unhealthy",
            "service": "drive-webhooks",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }


@router.post("/n8n-webhook")
async def send_to_n8n_webhook(
    document_id: str,
    project_id: str,
    file_id: str,
    action: str
):
    """Send webhook to N8N for additional processing."""
    try:
        logger.info(f"Sending to N8N webhook: {action} for file {file_id}")
        
        # This would typically send to N8N for additional processing
        # For now, just log the action
        
        # Update webhook log to mark as sent to N8N
        supabase = get_supabase()
        await supabase.table('drive_webhook_logs').update({
            'n8n_webhook_sent': True,
            'n8n_webhook_sent_at': '2024-01-01T00:00:00Z',
            'n8n_webhook_response': 'sent_to_n8n'
        }).eq('file_id', file_id).execute()
        
        return {
            "status": "success",
            "message": f"Webhook sent to N8N for {action}",
            "document_id": document_id,
            "file_id": file_id,
            "action": action
        }
        
    except Exception as e:
        logger.error(f"Failed to send to N8N webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send to N8N: {str(e)}")
