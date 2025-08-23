"""
Attendee API endpoints for BeSunny.ai Python backend.
Handles meeting bot management, transcript retrieval, and chat functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ...services.attendee import AttendeeService, AttendeePollingService
from ...core.security import get_current_user

router = APIRouter()


class BotDeploymentRequest(BaseModel):
    """Request model for bot deployment."""
    meeting_url: str
    bot_name: str
    bot_chat_message: Optional[str] = None


class ChatMessageRequest(BaseModel):
    """Request model for sending chat messages."""
    message: str
    to: str = "everyone"


@router.post("/create-bot")
async def create_bot_for_meeting(
    request: BotDeploymentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a bot for a meeting."""
    try:
        attendee_service = AttendeeService()
        
        # Prepare options for bot creation
        options = {
            "meeting_url": request.meeting_url,
            "bot_name": request.bot_name
        }
        
        if request.bot_chat_message:
            options["bot_chat_message"] = request.bot_chat_message
        
        result = await attendee_service.create_bot_for_meeting(options, current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots")
async def list_user_bots(
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get polling history for the current user."""
    try:
        polling_service = AttendeePollingService()
        result = await polling_service.get_polling_history(current_user["id"], limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
