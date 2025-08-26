"""
Clean Gmail API endpoints for email watching and processing.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Header

from ...core.security import get_current_user_from_supabase_token
from ...services.email.gmail_service import GmailService

router = APIRouter()


@router.post("/watch/setup")
async def setup_gmail_watch(
    background_tasks: BackgroundTasks,
    x_admin_token: str = Header(None)
) -> Dict[str, Any]:
    """Set up Gmail watch for the master account."""
    logger.info("=" * 50)
    logger.info("GMAIL WATCH SETUP ENDPOINT CALLED")
    logger.info(f"Current user: {current_user}")
    logger.info(f"Admin token header: {x_admin_token}")
    logger.info("=" * 50)
    
    try:
        # Check for admin token
        if not x_admin_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin token required - use X-Admin-Token header"
            )
        
        # Validate admin token
        admin_emails = ["ai@besunny.ai", "admin@besunny.ai"]
        try:
            import base64
            import json
            
            # Decode the token
            decoded_bytes = base64.b64decode(x_admin_token)
            decoded_string = decoded_bytes.decode('utf-8')
            token_data = json.loads(decoded_string)
            
            logger.info(f"Decoded admin token data: {token_data}")
            
            if token_data.get("is_admin") and token_data.get("email") in admin_emails:
                logger.info(f"Admin access granted via token for {token_data.get('email')}")
            else:
                logger.warning(f"Admin token validation failed: is_admin={token_data.get('is_admin')}, email={token_data.get('email')}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid admin token - insufficient privileges"
                )
        except Exception as e:
            logger.error(f"Error processing admin token: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid admin token format: {str(e)}"
            )
        
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gmail service not ready - check service account configuration"
            )
        
        # Get topic name from environment or use default
        topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
        
        # Set up the watch in the background
        background_tasks.add_task(
            gmail_service.setup_watch,
            topic_name
        )
        
        return {
            "status": "success",
            "message": "Gmail watch setup initiated for master account",
            "master_email": gmail_service.master_email,
            "topic_name": topic_name,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup Gmail watch: {str(e)}"
        )


@router.post("/watch/process")
async def process_email(
    message_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """Process a specific email message."""
    try:
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gmail service not ready"
            )
        
        # Process the email in the background
        background_tasks.add_task(
            gmail_service.process_email,
            message_id
        )
        
        return {
            "status": "success",
            "message": "Email processing initiated",
            "message_id": message_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email: {str(e)}"
        )


@router.get("/emails/recent")
async def get_recent_emails(
    max_results: int = 50,
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """Get recent emails from the master account inbox."""
    try:
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gmail service not ready"
            )
        
        emails = await gmail_service.fetch_recent_emails(max_results)
        
        return {
            "status": "success",
            "emails": emails,
            "count": len(emails),
            "max_results": max_results,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent emails: {str(e)}"
        )


@router.get("/test-auth")
async def test_authentication(
    x_admin_token: str = Header(None)
) -> Dict[str, Any]:
    """Test endpoint to verify admin token is working."""
    try:
        logger.info("=" * 50)
        logger.info("TEST AUTH ENDPOINT CALLED")
        logger.info(f"Admin token header: {x_admin_token}")
        
        if not x_admin_token:
            logger.warning("No admin token provided")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin token required - use X-Admin-Token header"
            )
        
        # Simple validation - just check if token exists
        logger.info("Admin token provided, returning success")
        
        return {
            "status": "success",
            "message": "Admin authentication working (basic check)",
            "token_received": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in test-auth: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/ping")
async def ping() -> Dict[str, Any]:
    """Simple ping endpoint to test if the router is working."""
    return {
        "status": "success",
        "message": "Gmail router is working",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/status")
async def get_gmail_service_status(
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """Get the current status of the Gmail service."""
    try:
        gmail_service = GmailService()
        status_info = await gmail_service.get_service_status()
        
        return {
            "service": "gmail",
            "timestamp": "2024-01-01T00:00:00Z",
            **status_info
        }
        
    except Exception as e:
        return {
            "service": "gmail",
            "status": "error",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }


@router.post("/webhook")
async def gmail_webhook(
    request: Dict[str, Any]
) -> Dict[str, str]:
    """
    Handle Gmail webhook notifications from Pub/Sub.
    This endpoint receives push notifications when emails arrive.
    """
    try:
        # Extract message data from Pub/Sub
        message_data = request.get('message', {})
        data = message_data.get('data', '')
        
        if not data:
            return {"status": "no_data"}
        
        # Decode base64 data
        import base64
        import json
        
        decoded_data = json.loads(base64.b64decode(data).decode('utf-8'))
        
        # Check if this is for our master account
        email_address = decoded_data.get('emailAddress')
        if email_address != 'ai@besunny.ai':
            return {"status": "wrong_account", "email": email_address}
        
        # Get history ID for processing
        history_id = decoded_data.get('historyId')
        if not history_id:
            return {"status": "no_history_id"}
        
        # TODO: Process the history to get new messages
        # For now, just acknowledge receipt
        
        return {
            "status": "received",
            "email": email_address,
            "history_id": history_id,
            "message": "Webhook received, processing will be implemented"
        }
        
    except Exception as e:
        # Log error but don't fail the webhook
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing Gmail webhook: {e}")
        
        return {"status": "error", "error": str(e)}
