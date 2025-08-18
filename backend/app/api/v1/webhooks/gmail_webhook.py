"""
Gmail webhook endpoint for BeSunny.ai Python backend.
Handles incoming webhook notifications from Gmail.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ....services.email.gmail_webhook_handler import GmailWebhookHandler
from ....models.schemas.email import GmailWebhookPayload, GmailNotification
from ....core.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def handle_gmail_webhook(request: Request):
    """Handle incoming Gmail webhook notifications."""
    try:
        # Get webhook data from request
        webhook_data = await request.json()
        
        # Extract headers for additional context
        headers = dict(request.headers)
        
        # Log webhook receipt
        logger.info("Gmail webhook received", extra={
            "headers": {k: v for k, v in headers.items() if k.lower().startswith('x-goog-')},
            "body": webhook_data
        })
        
        # Process the webhook
        webhook_handler = GmailWebhookHandler()
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
        logger.error(f"Gmail webhook processing error: {e}", exc_info=True)
        # Always return 200 to Google to prevent retries
        return JSONResponse(
            content={
                "status": "error", 
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=200
        )


@router.post("/push")
async def handle_gmail_push_notification(request: Request):
    """Handle Gmail push notifications (Pub/Sub format)."""
    try:
        # Get notification data from request
        notification_data = await request.json()
        
        # Log notification receipt
        logger.info("Gmail push notification received", extra={"notification_data": notification_data})
        
        # Process the push notification
        webhook_handler = GmailWebhookHandler()
        success = await webhook_handler.process_push_notification(notification_data)
        
        if success:
            return JSONResponse(
                content={"status": "success", "message": "Push notification processed successfully"},
                status_code=200
            )
        else:
            return JSONResponse(
                content={"status": "error", "message": "Push notification processing failed"},
                status_code=500
            )
            
    except Exception as e:
        logger.error(f"Gmail push notification processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process push notification: {str(e)}")


@router.post("/test")
async def test_gmail_webhook(
    webhook_data: GmailWebhookPayload,
    background_tasks: BackgroundTasks
):
    """Test Gmail webhook processing (for development/testing)."""
    try:
        logger.info("Testing Gmail webhook processing", extra={"webhook_data": webhook_data.dict()})
        
        # Process the test webhook
        webhook_handler = GmailWebhookHandler()
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


@router.post("/test-push")
async def test_gmail_push_notification(
    notification_data: GmailNotification,
    background_tasks: BackgroundTasks
):
    """Test Gmail push notification processing (for development/testing)."""
    try:
        logger.info("Testing Gmail push notification processing", extra={"notification_data": notification_data.dict()})
        
        # Process the test push notification
        webhook_handler = GmailWebhookHandler()
        success = await webhook_handler.process_push_notification(notification_data.dict())
        
        if success:
            return {
                "status": "success",
                "message": "Test push notification processed successfully",
                "notification_data": notification_data.dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Test push notification processing failed")
            
    except Exception as e:
        logger.error(f"Test push notification processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Test push notification failed: {str(e)}")


@router.get("/logs")
async def get_gmail_webhook_logs(
    email_address: Optional[str] = None,
    limit: int = 100
):
    """Get Gmail webhook processing logs."""
    try:
        webhook_handler = GmailWebhookHandler()
        logs = await webhook_handler.get_webhook_logs(email_address, limit)
        
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
async def get_active_gmail_watches(user_id: Optional[str] = None):
    """Get active Gmail watches."""
    try:
        webhook_handler = GmailWebhookHandler()
        watches = await webhook_handler.get_active_watches(user_id)
        
        return {
            "status": "success",
            "watches": watches,
            "total_count": len(watches)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active watches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get watches: {str(e)}")


@router.get("/status")
async def get_gmail_webhook_status():
    """Get Gmail webhook system status."""
    try:
        supabase = get_supabase()
        
        # Get watch statistics
        watch_stats = await supabase.table('gmail_watches').select('*').execute()
        active_watches = [w for w in watch_stats.data or [] if w.get('is_active')]
        
        # Get recent webhook activity
        recent_activity = await supabase.table('gmail_watches').select('*').order('updated_at', desc=True).limit(10).execute()
        
        return {
            "status": "healthy",
            "service": "gmail-webhooks",
            "statistics": {
                "total_watches": len(watch_stats.data or []),
                "active_watches": len(active_watches),
                "inactive_watches": len(watch_stats.data or []) - len(active_watches)
            },
            "recent_activity": recent_activity.data or [],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook status: {e}")
        return {
            "status": "unhealthy",
            "service": "gmail-webhooks",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }


@router.post("/virtual-email-detection")
async def process_virtual_email_detection(
    user_email: str,
    message_id: str,
    virtual_emails: list
):
    """Process virtual email detection results."""
    try:
        logger.info(f"Processing virtual email detection for {user_email}")
        
        # Process the virtual email detection
        webhook_handler = GmailWebhookHandler()
        await webhook_handler._process_virtual_email_detection(user_email, message_id, virtual_emails)
        
        return {
            "status": "success",
            "message": "Virtual email detection processed successfully",
            "user_email": user_email,
            "message_id": message_id,
            "virtual_emails_count": len(virtual_emails)
        }
        
    except Exception as e:
        logger.error(f"Failed to process virtual email detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process detection: {str(e)}")


@router.post("/n8n-classification")
async def send_to_n8n_classification(
    document_id: str,
    gmail_message_id: str,
    action: str = "classify_email"
):
    """Send document to N8N for classification."""
    try:
        logger.info(f"Sending to N8N classification webhook: {action} for document {document_id}")
        
        # This would typically send to N8N for classification
        # For now, just log the action
        
        return {
            "status": "success",
            "message": f"Document sent to N8N for {action}",
            "document_id": document_id,
            "gmail_message_id": gmail_message_id,
            "action": action
        }
        
    except Exception as e:
        logger.error(f"Failed to send to N8N classification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send to N8N: {str(e)}")
