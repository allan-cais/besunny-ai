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
    meeting_time: str
    project_id: str
    bot_config: Optional[Dict[str, Any]] = {}
    recording_enabled: bool = True
    transcript_enabled: bool = True


class ChatMessageRequest(BaseModel):
    """Request model for sending chat messages."""
    message: str
    to: str
    from_user: str = "system"


class AutoScheduleRequest(BaseModel):
    """Request model for auto-scheduling bots."""
    force_schedule: bool = False


@router.post("/poll-all")
async def poll_all_meetings(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Poll all meetings for the current user."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.poll_all_meetings(current_user["id"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-bot")
async def send_bot_to_meeting(
    request: BotDeploymentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send a bot to a meeting."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.send_bot_to_meeting(
            request.dict(), current_user["id"]
        )
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


@router.post("/auto-schedule")
async def auto_schedule_bots(
    request: AutoScheduleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Automatically schedule bots for upcoming meetings."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.auto_schedule_bots(current_user["id"])
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


@router.post("/send-chat")
async def send_chat_message(
    bot_id: str,
    request: ChatMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send a chat message through a meeting bot."""
    try:
        attendee_service = AttendeeService()
        result = await attendee_service.send_chat_message(
            bot_id, request.message, request.to, request.from_user
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
