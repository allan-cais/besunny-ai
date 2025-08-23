"""
Webhook handlers for BeSunny.ai Python backend.
Handles incoming webhook notifications from various services.
"""

from fastapi import APIRouter

from . import calendar_webhook, drive_webhook, gmail_webhook, attendee_webhook

# Create webhooks router
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Include all webhook routers
router.include_router(calendar_webhook.router, prefix="/calendar", tags=["calendar-webhooks"])
router.include_router(drive_webhook.router, prefix="/drive", tags=["drive-webhooks"])
router.include_router(gmail_webhook.router, prefix="/gmail", tags=["gmail-webhooks"])
router.include_router(attendee_webhook.router, prefix="/attendee", tags=["attendee-webhooks"])

# Health check endpoint
@router.get("/health")
async def webhooks_health_check():
    """Webhooks health check."""
    return {
        "status": "healthy",
        "service": "webhooks",
        "endpoints": [
            "/calendar",
            "/drive", 
            "/gmail",
            "/attendee"
        ],
        "timestamp": "2024-01-01T00:00:00Z"
    }
