"""
Attendee webhook endpoint for BeSunny.ai Python backend.
Handles incoming webhook notifications from Attendee.dev API.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
import hmac
import hashlib
import base64
import json
from datetime import datetime

from ....services.attendee.attendee_webhook_handler import AttendeeWebhookHandler
from ....core.database import get_supabase
from ....core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{user_id}")
async def handle_attendee_webhook(
    user_id: str,
    request: Request
):
    """Handle incoming Attendee webhook notifications."""
    try:
        # Get webhook data from request
        webhook_data = await request.json()
        
        # Extract headers for signature verification
        headers = dict(request.headers)
        signature = headers.get("X-Webhook-Signature")
        
        # Log webhook receipt
        logger.info(f"Attendee webhook received for user {user_id}", extra={
            "webhook_data": webhook_data,
            "signature": signature
        })
        
        # Verify webhook signature if configured
        settings = get_settings()
        if settings.attendee_webhook_secret:
            if not await _verify_webhook_signature(webhook_data, signature, user_id):
                logger.warning(f"Invalid webhook signature for user {user_id}")
                # Return 200 to prevent retries, but log the issue
                return JSONResponse(
                    content={"status": "error", "message": "Invalid signature"},
                    status_code=200
                )
        else:
            logger.info(f"Webhook secret not configured - skipping signature validation for user {user_id}")
        
        # Process the webhook
        webhook_handler = AttendeeWebhookHandler()
        success = await webhook_handler.process_webhook(webhook_data, user_id)
        
        if success:
            return JSONResponse(
                content={"status": "success", "message": "Webhook processed successfully"},
                status_code=200
            )
        else:
            # Return 200 to Attendee even on failure (they don't retry on 4xx/5xx)
            return JSONResponse(
                content={"status": "error", "message": "Webhook processing failed"},
                status_code=200
            )
            
    except Exception as e:
        logger.error(f"Attendee webhook processing error for user {user_id}: {e}", exc_info=True)
        # Always return 200 to Attendee to prevent retries
        return JSONResponse(
            content={
                "status": "error", 
                "message": "Internal server error",
                "error": str(e)
            },
            status_code=200
        )


@router.get("/{user_id}/verify")
async def verify_webhook_endpoint(user_id: str):
    """Verify webhook endpoint is accessible."""
    return {
        "status": "active",
        "user_id": user_id,
        "endpoint": f"/api/v1/webhooks/attendee/{user_id}",
        "timestamp": datetime.now().isoformat()
    }


async def _verify_webhook_signature(payload: Dict[str, Any], signature: Optional[str], user_id: str) -> bool:
    """Verify webhook signature using HMAC-SHA256 as per Attendee.dev documentation."""
    try:
        if not signature:
            logger.warning(f"No webhook signature provided for user {user_id}")
            return False
        
        # Get webhook secret from settings
        settings = get_settings()
        webhook_secret = settings.attendee_webhook_secret
        
        if not webhook_secret:
            logger.warning("No webhook secret configured - webhook signature validation disabled")
            return True  # Allow webhook to proceed if no secret is configured
        
        # Create canonical JSON string with sorted keys (as per documentation)
        canonical_payload = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        
        # Decode the base64 secret
        secret_decoded = base64.b64decode(webhook_secret)
        
        # Create the signature using HMAC-SHA256
        expected_signature = base64.b64encode(
            hmac.new(secret_decoded, canonical_payload.encode('utf-8'), hashlib.sha256).digest()
        ).decode('utf-8')
        
        # Compare signatures using constant-time comparison
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(f"Webhook signature mismatch for user {user_id}")
            logger.debug(f"Expected: {expected_signature}")
            logger.debug(f"Received: {signature}")
            logger.debug(f"Canonical payload: {canonical_payload}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False
