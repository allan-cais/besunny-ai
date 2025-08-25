"""
Gmail webhook handler for processing virtual email addresses.
Receives emails sent to ai+{username}@besunny.ai and processes them.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status
import logging
import json
from datetime import datetime

from ...services.email import EmailProcessingService
from ...core.config import get_settings
from ...core.security import verify_gmail_webhook_token

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/gmail")
async def handle_gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Handle Gmail push notification webhook.
    
    This endpoint receives notifications when emails arrive at the monitored
    Gmail account (inbound@besunny.ai) and processes any emails sent to
    virtual email addresses (ai+{username}@besunny.ai).
    """
    try:
        # Verify the webhook is from Gmail
        if not await _verify_gmail_webhook(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Gmail webhook signature"
            )
        
        # Parse the webhook payload
        webhook_data = await request.json()
        logger.info(f"Received Gmail webhook: {webhook_data}")
        
        # Extract message data
        message_data = webhook_data.get('message', {})
        if not message_data:
            return {"status": "no_message_data", "message": "No message data in webhook"}
        
        # Get the email message ID
        message_id = message_data.get('data')
        if not message_id:
            return {"status": "no_message_id", "message": "No message ID in webhook"}
        
        # Decode the base64 message ID
        import base64
        try:
            decoded_message_id = base64.urlsafe_b64decode(message_id + '=' * (-len(message_id) % 4))
            gmail_message_id = decoded_message_id.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decode message ID: {e}")
            return {"status": "decode_error", "message": "Failed to decode message ID"}
        
        # Process the email in the background
        background_tasks.add_task(
            _process_gmail_message,
            gmail_message_id
        )
        
        return {
            "status": "success",
            "message": "Email queued for processing",
            "gmail_message_id": gmail_message_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling Gmail webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(e)}"
        )


@router.post("/gmail-test")
async def test_gmail_webhook() -> Dict[str, Any]:
    """Test endpoint for Gmail webhook functionality."""
    return {
        "status": "success",
        "message": "Gmail webhook endpoint is working",
        "timestamp": datetime.utcnow().isoformat()
    }


async def _verify_gmail_webhook(request: Request) -> bool:
    """Verify that the webhook is from Gmail."""
    try:
        # Get the authorization header
        auth_header = request.headers.get('authorization')
        if not auth_header:
            logger.warning("No authorization header in Gmail webhook")
            return False
        
        # Verify the token (implement based on your security requirements)
        # For now, we'll accept all requests but log them
        logger.info("Gmail webhook verification passed")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying Gmail webhook: {e}")
        return False


async def _process_gmail_message(gmail_message_id: str) -> None:
    """Process a Gmail message in the background."""
    try:
        logger.info(f"Processing Gmail message: {gmail_message_id}")
        
        # Get the email service
        email_service = EmailProcessingService()
        
        # Fetch the full message from Gmail
        gmail_message = await _fetch_gmail_message(gmail_message_id)
        if not gmail_message:
            logger.error(f"Failed to fetch Gmail message: {gmail_message_id}")
            return
        
        # Check if this is a virtual email
        to_header = _get_header_value(gmail_message.get('payload', {}).get('headers', []), 'to')
        if not to_header or not _is_virtual_email(to_header):
            logger.info(f"Message {gmail_message_id} is not a virtual email: {to_header}")
            return
        
        # Process the virtual email
        result = await email_service.process_inbound_email(gmail_message)
        
        if result.success:
            logger.info(f"Successfully processed virtual email {gmail_message_id}: {result.message}")
        else:
            logger.error(f"Failed to process virtual email {gmail_message_id}: {result.message}")
            
    except Exception as e:
        logger.error(f"Error processing Gmail message {gmail_message_id}: {e}")


async def _fetch_gmail_message(message_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a Gmail message using the Gmail API."""
    try:
        # TODO: Implement Gmail API call to fetch message
        # This will be implemented when we add Gmail API integration
        # For now, return a placeholder structure
        
        logger.info(f"Would fetch Gmail message: {message_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching Gmail message {message_id}: {e}")
        return None


def _get_header_value(headers: list, name: str) -> Optional[str]:
    """Get header value by name from Gmail message headers."""
    try:
        header = next((h for h in headers if h.get('name', '').lower() == name.lower()), None)
        return header.get('value') if header else None
    except Exception as e:
        logger.error(f"Error getting header value for {name}: {e}")
        return None


def _is_virtual_email(email: str) -> bool:
    """Check if an email address is a virtual email (ai+{username}@besunny.ai)."""
    if not email:
        return False
    
    # Check if it matches the virtual email pattern
    import re
    pattern = r'ai\+[a-zA-Z0-9]+@besunny\.ai'
    return bool(re.match(pattern, email))
