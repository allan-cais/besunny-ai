"""
Clean Gmail API endpoints for email watching and processing.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Header, Request
import logging
from datetime import datetime

from ...core.security import get_current_user_from_supabase_token
from ...services.email.gmail_service import GmailService
from ...services.email.email_processing_service import EmailProcessingService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/watch/setup")
async def setup_gmail_watch(
    background_tasks: BackgroundTasks,
    x_admin_token: str = Header(None)
) -> Dict[str, Any]:
    """Set up Gmail watch for the master account."""
    logger.info("=" * 50)
    logger.info("GMAIL WATCH SETUP ENDPOINT CALLED")
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
        
        # Now that PubSub is working, set up the actual Gmail watch
        try:
            # Get topic name from environment or use default
            topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
            
            # Set up the watch
            watch_id = await gmail_service.setup_watch(topic_name)
            if not watch_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to setup Gmail watch - check service configuration"
                )
            
            return {
                "status": "success",
                "message": "Gmail watch setup successful! 🎉",
                "master_email": gmail_service.master_email,
                "watch_id": watch_id,
                "topic_name": topic_name,
                "note": "Gmail watch is now active and will receive real-time email notifications",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error testing Gmail connectivity: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Check for specific IAM policy errors
            if "Domain Restricted Sharing" in error_msg or "constraints/iam.allowedPolicyMemberDomains" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "IAM Policy Domain Restriction Error",
                        "message": "Your Google Cloud organization has domain restricted sharing enabled. This prevents setting up Gmail API webhooks.",
                        "solution": "Contact your Google Workspace admin to add '*.iam.gserviceaccount.com' to the allowed domains in the organization policy, or create a new project without domain restrictions.",
                        "technical_details": error_msg,
                        "request_id": "7710829603618251089" if "7710829603618251089" in error_msg else None
                    }
                )
            elif "IAM" in error_msg and "policy" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "IAM Policy Error",
                        "message": "Unable to set IAM policies for Gmail webhook setup.",
                        "solution": "Ensure your service account has the necessary permissions: 'Pub/Sub Publisher' and 'Gmail API Admin' roles.",
                        "technical_details": error_msg
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Gmail service error: {error_msg}"
                )
        
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
        
        # Process the email directly (not in background for now)
        try:
            success = await gmail_service.process_email(message_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process email"
                )
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process email: {str(e)}"
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
    request: Request
) -> Dict[str, str]:
    """
    Handle Gmail webhook notifications from Pub/Sub.
    This endpoint receives push notifications when emails arrive.
    """
    logger.info("=" * 50)
    logger.info("GMAIL WEBHOOK ENDPOINT CALLED")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info("=" * 50)
    
    try:
        # Get the webhook payload from the request
        webhook_data = await request.json()
        logger.info(f"Received Gmail webhook: {webhook_data}")
        
        # Initialize email processing service
        email_processor = EmailProcessingService()
        
        # Process the webhook and store email data
        processing_result = await email_processor.process_gmail_webhook(webhook_data)
        
        if processing_result.get("status") == "success":
            logger.info(f"Email processing successful: {processing_result.get('message')}")
            return {
                "status": "success",
                "message": processing_result.get("message"),
                "total_processed": processing_result.get("total_processed", 0),
                "successful": processing_result.get("successful", 0),
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.warning(f"Email processing completed with issues: {processing_result.get('message')}")
            return {
                "status": "partial_success",
                "message": processing_result.get("message"),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        # Log error but don't fail the webhook
        logger.error(f"Error processing Gmail webhook: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        return {"status": "error", "error": str(e)}


@router.get("/webhook-test")
async def test_webhook_endpoint() -> Dict[str, str]:
    """Test endpoint to verify webhook routing is working."""
    logger.info("Webhook test endpoint called")
    return {"status": "webhook_routing_working", "message": "Webhook endpoint is accessible"}

@router.get("/test-gmail-connection")
async def test_gmail_connection(
    x_admin_token: str = Header(None)
) -> Dict[str, Any]:
    """Test endpoint to verify Gmail service can connect to Gmail API."""
    try:
        logger.info("=" * 50)
        logger.info("TEST GMAIL CONNECTION ENDPOINT CALLED")
        
        # Check for admin token
        if not x_admin_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin token required - use X-Admin-Token header"
            )
        
        # Validate admin token (simplified for now)
        try:
            import base64
            import json
            decoded_bytes = base64.b64decode(x_admin_token)
            decoded_string = decoded_bytes.decode('utf-8')
            token_data = json.loads(decoded_string)
            
            if not (token_data.get("is_admin") and token_data.get('email') in ["ai@besunny.ai", "admin@besunny.ai"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid admin token - insufficient privileges"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid admin token format: {str(e)}"
            )
        
        # Test Gmail service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            return {
                "status": "error",
                "message": "Gmail service not ready",
                "details": "Service account credentials or configuration issue",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        
        # Try to get Gmail profile to test connection
        try:
            profile = gmail_service.gmail_service.users().getProfile(userId=gmail_service.master_email).execute()
            return {
                "status": "success",
                "message": "Gmail API connection successful",
                "email": profile.get('emailAddress'),
                "messages_total": profile.get('messagesTotal'),
                "threads_total": profile.get('threadsTotal'),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Gmail API connection failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in test-gmail-connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
