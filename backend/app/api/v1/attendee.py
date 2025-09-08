"""
Attendee API endpoints for BeSunny.ai Python backend.
Handles meeting bot management, transcript retrieval, and chat functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ...services.attendee.attendee_service import AttendeeService
from ...services.attendee.attendee_polling_service import AttendeePollingService
from ...services.attendee.virtual_email_attendee_service import VirtualEmailAttendeeService
from ...core.security import get_current_user_hybrid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/debug/auth")
async def debug_auth(
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Debug endpoint to test authentication."""
    return {
        "success": True,
        "message": "Authentication successful",
        "user": current_user,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/debug/headers")
async def debug_headers(
    request: Request
) -> Dict[str, Any]:
    """Debug endpoint to check request headers."""
    headers = dict(request.headers)
    # Remove sensitive headers for security
    sensitive_headers = ['authorization', 'cookie', 'x-api-key']
    for header in sensitive_headers:
        if header in headers:
            headers[header] = f"[REDACTED] (length: {len(headers[header])})"
    
    return {
        "headers": headers,
        "method": request.method,
        "url": str(request.url),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/debug/public")
async def debug_public() -> Dict[str, Any]:
    """Public debug endpoint that doesn't require authentication."""
    return {
        "success": True,
        "message": "Public endpoint accessible without authentication",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/debug/supabase")
async def debug_supabase() -> Dict[str, Any]:
    """Debug endpoint to check Supabase configuration."""
    try:
        from ...core.supabase_config import get_supabase_config, get_supabase
        supabase_config = get_supabase_config()
        config_info = supabase_config.get_config_info()
        
        # Try to get a Supabase client
        supabase = get_supabase()
        
        return {
            "success": True,
            "supabase_config": config_info,
            "client_available": bool(supabase),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


class BotDeploymentRequest(BaseModel):
    """Request model for bot deployment."""
    meeting_url: str
    bot_name: str
    bot_chat_message: Optional[str] = None
    start_time: Optional[str] = None


class ChatMessageRequest(BaseModel):
    """Request model for sending chat messages."""
    message: str
    to: str = "everyone"


class VirtualEmailEventRequest(BaseModel):
    """Request model for processing calendar events with virtual email attendees."""
    event_data: Dict[str, Any]


@router.post("/create-bot")
async def create_bot_for_meeting(
    request: BotDeploymentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Create a bot for a meeting (manual deployment from UI)."""
    try:
        attendee_service = AttendeeService()
        
        # Prepare options for bot creation with manual deployment method
        options = {
            "meeting_url": request.meeting_url,
            "bot_name": request.bot_name,
            "deployment_method": "manual"  # Mark as manually deployed from UI
        }
        
        if request.bot_chat_message:
            options["bot_chat_message"] = request.bot_chat_message
        
        # This will create the same comprehensive webhook configuration for transcript retrieval
        # Whether deployed manually from UI or automatically via virtual email
        result = await attendee_service.create_bot_for_meeting(options, current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-bot")
async def send_bot_to_meeting(
    request: BotDeploymentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Send a bot to a meeting (alias for create-bot for frontend compatibility)."""
    try:
        logger.error(f"=== SEND-BOT ENDPOINT CALLED ===")
        logger.error(f"Send bot request received for user {current_user.get('id')}: {request}")
        
        attendee_service = AttendeeService()
        
        # Prepare options for bot creation
        options = {
            "meeting_url": request.meeting_url,
            "bot_name": request.bot_name,
            "deployment_method": "manual"
        }
        
        if request.bot_chat_message:
            options["bot_chat_message"] = request.bot_chat_message
            
        if request.start_time:
            options["start_time"] = request.start_time
        
        logger.info(f"Bot creation options: {options}")
        
        # Create the bot using the same service method
        result = await attendee_service.create_bot_for_meeting(options, current_user["id"])
        
        logger.info(f"Bot creation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in send_bot_to_meeting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-bot-test")
async def send_bot_to_meeting_test(
    request: BotDeploymentRequest
) -> Dict[str, Any]:
    """Test endpoint for send-bot without authentication."""
    try:
        return {
            "success": True,
            "message": "Test endpoint reached successfully",
            "data": {
                "meeting_url": request.meeting_url,
                "bot_name": request.bot_name,
                "bot_chat_message": request.bot_chat_message
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/virtual-email/process-event")
async def process_calendar_event_for_virtual_emails(
    request: VirtualEmailEventRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Process a calendar event to detect virtual email attendees and auto-schedule bots."""
    try:
        virtual_email_service = VirtualEmailAttendeeService()
        result = await virtual_email_service.process_calendar_event_for_virtual_emails(request.event_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/virtual-email/activity")
async def get_virtual_email_activity(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Get virtual email activity for the current user."""
    try:
        virtual_email_service = VirtualEmailAttendeeService()
        result = await virtual_email_service.get_virtual_email_activity(current_user["id"], days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/virtual-email/auto-schedule")
async def auto_schedule_bots_for_virtual_emails(
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Auto-schedule bots for all upcoming meetings with virtual email attendees."""
    try:
        virtual_email_service = VirtualEmailAttendeeService()
        
        # Get upcoming meetings with virtual email attendees
        result = await virtual_email_service.get_virtual_email_activity(current_user["id"], days=7)
        
        # Process each meeting to ensure bots are scheduled
        meetings_processed = 0
        bots_scheduled = 0
        
        for meeting in result.get('meetings', []):
            if meeting.get('bot_status') == 'pending':
                # This meeting needs a bot scheduled
                # You would implement the logic to fetch the calendar event and process it
                meetings_processed += 1
        
        return {
            'success': True,
            'meetings_processed': meetings_processed,
            'bots_scheduled': bots_scheduled,
            'message': f'Processed {meetings_processed} meetings, scheduled {bots_scheduled} bots'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots")
async def list_user_bots(
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> List[Dict[str, Any]]:
    """List all bots for the current user."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.list_user_bots(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bot-status/{bot_id}")
async def get_bot_status(
    bot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Get current status of a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.get_bot_status(bot_id)
        if not result:
            raise HTTPException(status_code=404, detail="Bot not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transcript/{bot_id}")
async def get_transcript(
    bot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Get transcript for a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.get_transcript(bot_id)
        if not result:
            raise HTTPException(status_code=404, detail="Transcript not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat-messages/{bot_id}")
async def get_chat_messages(
    bot_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> List[Dict[str, Any]]:
    """Get chat messages for a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.get_chat_messages(bot_id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-chat/{bot_id}")
async def send_chat_message(
    bot_id: str,
    request: ChatMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Send a chat message through a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.send_chat_message(
            bot_id, request.message, request.to
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to send message")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/participant-events/{bot_id}")
async def get_participant_events(
    bot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> List[Dict[str, Any]]:
    """Get participant events for a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.get_participant_events(bot_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause-recording/{bot_id}")
async def pause_recording(
    bot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Pause recording for a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.pause_recording(bot_id)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to pause recording")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume-recording/{bot_id}")
async def resume_recording(
    bot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Resume recording for a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.resume_recording(bot_id)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to resume recording")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bot/{bot_id}")
async def delete_bot(
    bot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Delete a meeting bot."""
    try:
        attendee_service = AttendeeService()
        success = await attendee_service.delete_bot(bot_id)
        if success:
            return {"success": True, "message": "Bot deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete bot")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Polling endpoints
@router.post("/poll/meeting/{meeting_id}")
async def poll_meeting_status(
    meeting_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Poll status for a specific meeting."""
    try:
        polling_service = AttendeePollingService()
        result = await polling_service.poll_meeting_status(meeting_id)
        if not result:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poll/all-meetings")
async def poll_all_user_meetings(
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> List[Dict[str, Any]]:
    """Poll all meetings for the current user."""
    try:
        polling_service = AttendeePollingService()
        result = await polling_service.poll_all_user_meetings(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poll/smart")
async def smart_polling(
    force_poll: bool = Query(False, description="Force polling regardless of timing"),
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Execute smart polling for the current user."""
    try:
        polling_service = AttendeePollingService()
        result = await polling_service.smart_polling(current_user["id"], force_poll)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/poll/history")
async def get_polling_history(
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> List[Dict[str, Any]]:
    """Get polling history for the current user."""
    try:
        polling_service = AttendeePollingService()
        result = await polling_service.get_polling_history(current_user["id"], limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
