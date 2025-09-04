"""
Gmail watch management endpoints.
This allows re-establishing Gmail watches when they expire.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime

from ....services.email.gmail_service import GmailService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/re-establish-watch")
async def re_establish_gmail_watch() -> Dict[str, Any]:
    """
    Re-establish Gmail watch for the master account.
    This should be called when webhooks stop working due to expired watch.
    """
    try:
        logger.info("Re-establishing Gmail watch...")
        
        # Initialize Gmail service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            raise HTTPException(
                status_code=500,
                detail="Gmail service not ready - check service account configuration"
            )
        
        # Re-establish watch with the correct topic name
        topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
        watch_response = await gmail_service.setup_watch(topic_name)
        
        if watch_response:
            logger.info(f"Gmail watch re-established successfully: {watch_response}")
            return {
                "status": "success",
                "message": "Gmail watch re-established successfully",
                "watch_id": watch_response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.error("Gmail watch setup returned None")
            raise HTTPException(
                status_code=500,
                detail="Failed to re-establish Gmail watch - setup returned None"
            )
            
    except Exception as e:
        logger.error(f"Error re-establishing Gmail watch: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-establish Gmail watch: {str(e)}"
        )


@router.get("/watch-status")
async def get_gmail_watch_status() -> Dict[str, Any]:
    """
    Check current Gmail watch status.
    """
    try:
        logger.info("Checking Gmail watch status...")
        
        # Initialize Gmail service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            return {
                "status": "error",
                "message": "Gmail service not ready",
                "gmail_ready": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Check if we can access Gmail
        try:
            profile = gmail_service.gmail_service.users().getProfile(
                userId=gmail_service.master_email
            ).execute()
            
            return {
                "status": "success",
                "message": "Gmail service is ready",
                "gmail_ready": True,
                "email_address": profile.get('emailAddress'),
                "messages_total": profile.get('messagesTotal'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Gmail access error: {str(e)}",
                "gmail_ready": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error checking Gmail watch status: {e}")
        return {
            "status": "error",
            "message": f"Error checking Gmail status: {str(e)}",
            "gmail_ready": False,
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/test-watch")
async def test_gmail_watch() -> Dict[str, Any]:
    """
    Test Gmail watch establishment without database storage.
    This is a simpler test to see if the Gmail API call works.
    """
    try:
        logger.info("Testing Gmail watch establishment...")
        
        # Initialize Gmail service
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            raise HTTPException(
                status_code=500,
                detail="Gmail service not ready - check service account configuration"
            )
        
        # Try to establish watch directly with Gmail API
        topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
        
        watch_request = {
            'labelIds': ['INBOX'],
            'labelFilterAction': 'include',
            'topicName': topic_name
        }
        
        logger.info(f"Watch request: {watch_request}")
        
        # Make the Gmail API call directly
        watch = gmail_service.gmail_service.users().watch(
            userId=gmail_service.master_email, 
            body=watch_request
        ).execute()
        
        logger.info(f"Gmail watch API call successful: {watch}")
        
        return {
            "status": "success",
            "message": "Gmail watch test successful",
            "watch_response": watch,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing Gmail watch: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Gmail watch test failed: {str(e)}"
        )
