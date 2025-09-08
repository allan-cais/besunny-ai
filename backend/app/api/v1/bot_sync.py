"""
Bot synchronization API endpoints for BeSunny.ai Python backend.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
import logging

from ...core.security import get_current_user_hybrid
from ...services.attendee.bot_sync_service import BotSyncService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync-bot-status")
async def sync_bot_status(
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Sync bot status from meeting_bots table to meetings table."""
    try:
        bot_sync_service = BotSyncService()
        result = await bot_sync_service.sync_bot_status_to_meetings(current_user["id"])
        
        return {
            "success": True,
            "message": f"Synced {result.get('synced', 0)} bots",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to sync bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meetings-with-bot-status")
async def get_meetings_with_bot_status(
    unassigned_only: bool = True,
    future_only: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Get meetings for the user with their associated bot status."""
    try:
        bot_sync_service = BotSyncService()
        meetings = await bot_sync_service.get_user_meetings_with_bot_status(
            current_user["id"], 
            unassigned_only=unassigned_only, 
            future_only=future_only
        )
        
        return {
            "success": True,
            "meetings": meetings,
            "count": len(meetings)
        }
        
    except Exception as e:
        logger.error(f"Failed to get meetings with bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meeting/{meeting_id}/with-bot-status")
async def get_meeting_with_bot_status(
    meeting_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_hybrid)
) -> Dict[str, Any]:
    """Get a specific meeting with its associated bot status."""
    try:
        bot_sync_service = BotSyncService()
        meeting = await bot_sync_service.get_meeting_with_bot_status(meeting_id, current_user["id"])
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return {
            "success": True,
            "meeting": meeting
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting with bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
