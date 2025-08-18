"""
Google Calendar API endpoints for BeSunny.ai Python backend.
Provides REST API for Calendar operations and webhook handling.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query, status
from pydantic import BaseModel

from ...services.calendar import (
    CalendarService, 
    CalendarWebhookHandler, 
    CalendarPollingService, 
    CalendarPollingCronService,
    CalendarWatchRenewalService,
    CalendarWebhookRenewalService
)
from ...models.schemas.calendar import (
    CalendarSyncRequest,
    CalendarSyncResponse,
    CalendarWebhookRequest,
    CalendarWebhookResponse,
    MeetingListResponse,
    MeetingBotRequest,
    MeetingBotResponse,
    Meeting
)
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


class CalendarPollingRequest(BaseModel):
    """Request model for calendar polling operations."""
    force_poll: bool = False
    calendar_id: str = "primary"


@router.post("/webhook", response_model=dict)
async def setup_calendar_webhook(
    request: CalendarWebhookRequest,
    current_user: User = Depends(get_current_user)
):
    """Set up a webhook for a Google Calendar."""
    try:
        # Only allow users to set up webhooks for themselves
        if current_user.id != request.user_id:
            raise HTTPException(status_code=403, detail="Can only set up webhooks for yourself")
        
        calendar_service = CalendarService()
        
        # Set up the calendar webhook
        webhook_id = await calendar_service.setup_calendar_webhook(
            user_id=request.user_id,
            calendar_id=request.calendar_id
        )
        
        if webhook_id:
            return CalendarWebhookResponse(
                success=True,
                webhook_id=webhook_id,
                message="Calendar webhook set up successfully"
            )
        else:
            return CalendarWebhookResponse(
                success=False,
                message="Failed to set up calendar webhook"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set up calendar webhook: {str(e)}")


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_calendar_events(
    request: CalendarSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Sync calendar events for a user."""
    try:
        # Only allow users to sync their own calendar
        if current_user.id != request.user_id:
            raise HTTPException(status_code=403, detail="Can only sync your own calendar")
        
        calendar_service = CalendarService()
        
        # Add sync task to background queue
        background_tasks.add_task(
            calendar_service.sync_calendar_events,
            request.user_id,
            request.calendar_id,
            request.sync_range_days
        )
        
        return CalendarSyncResponse(
            success=True,
            events_synced=0,  # Will be updated when sync completes
            message="Calendar sync triggered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger calendar sync: {str(e)}")


# New calendar polling endpoints
@router.post("/poll")
async def poll_calendar(
    request: CalendarPollingRequest,
    current_user: User = Depends(get_current_user)
):
    """Poll calendar for the current user."""
    try:
        polling_service = CalendarPollingService()
        result = await polling_service.poll_calendar_for_user(
            current_user.id, 
            request.calendar_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll calendar: {str(e)}")


@router.post("/poll/smart")
async def smart_poll_calendar(
    force_poll: bool = Query(False, description="Force polling regardless of timing"),
    current_user: User = Depends(get_current_user)
):
    """Execute smart calendar polling for the current user."""
    try:
        polling_service = CalendarPollingService()
        result = await polling_service.smart_calendar_polling(current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute smart polling: {str(e)}")


@router.get("/poll/history")
async def get_polling_history(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get calendar polling history for the current user."""
    try:
        from ...core.database import get_supabase
        supabase = get_supabase()
        
        # Get polling history from database
        result = supabase.table("calendar_polling_results") \
            .select("*") \
            .eq("user_id", current_user.id) \
            .order("timestamp", desc=True) \
            .limit(limit) \
            .execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get polling history: {str(e)}")


@router.get("/meetings", response_model=MeetingListResponse)
async def get_user_meetings(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get meetings for the current user."""
    try:
        calendar_service = CalendarService()
        
        meetings = await calendar_service.get_user_meetings(
            user_id=current_user.id,
            project_id=project_id,
            status=status
        )
        
        return MeetingListResponse(
            meetings=meetings,
            total_count=len(meetings),
            next_page_token=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user meetings: {str(e)}")


@router.get("/meetings/{meeting_id}", response_model=Meeting)
async def get_meeting_details(
    meeting_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information for a specific meeting."""
    try:
        calendar_service = CalendarService()
        
        # Get meeting from database first
        meeting_result = await calendar_service.get_user_meetings(
            user_id=current_user.id
        )
        
        meeting = next((m for m in meeting_result if m['id'] == meeting_id), None)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return Meeting(**meeting)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get meeting details: {str(e)}")


@router.post("/meetings/{meeting_id}/bot", response_model=MeetingBotResponse)
async def schedule_meeting_bot(
    meeting_id: str,
    request: MeetingBotRequest,
    current_user: User = Depends(get_current_user)
):
    """Schedule a bot to attend a meeting."""
    try:
        calendar_service = CalendarService()
        
        # Schedule the meeting bot
        success = await calendar_service.schedule_meeting_bot(
            meeting_id=meeting_id,
            bot_config=request.bot_config
        )
        
        if success:
            return MeetingBotResponse(
                success=True,
                message="Meeting bot scheduled successfully"
            )
        else:
            return MeetingBotResponse(
                success=False,
                message="Failed to schedule meeting bot"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule meeting bot: {str(e)}")


@router.get("/webhooks/active", response_model=List[dict])
async def get_active_webhooks(
    current_user: User = Depends(get_current_user)
):
    """Get active calendar webhooks for the current user."""
    try:
        webhook_handler = CalendarWebhookHandler()
        
        webhooks = await webhook_handler.get_active_webhooks(user_id=current_user.id)
        return webhooks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active webhooks: {str(e)}")


@router.get("/webhooks/logs", response_model=List[dict])
async def get_webhook_logs(
    webhook_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get webhook processing logs."""
    try:
        webhook_handler = CalendarWebhookHandler()
        
        logs = await webhook_handler.get_webhook_logs(
            webhook_id=webhook_id,
            limit=limit
        )
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook logs: {str(e)}")


@router.post("/webhook")
async def handle_calendar_webhook(request: Request):
    """Handle incoming Google Calendar webhook notifications."""
    try:
        # Get webhook data
        webhook_data = await request.json()
        
        # Process the webhook
        webhook_handler = CalendarWebhookHandler()
        success = await webhook_handler.process_webhook(webhook_data)
        
        if success:
            return {"status": "success"}
        else:
            return {"status": "error"}
            
    except Exception as e:
        # Log the error but return 200 to Google (they don't retry on 4xx/5xx)
        return {"status": "error", "message": str(e)}


@router.post("/cleanup/expired-webhooks")
async def cleanup_expired_webhooks(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Clean up expired calendar webhooks."""
    try:
        calendar_service = CalendarService()
        
        # Add cleanup task to background queue
        background_tasks.add_task(calendar_service.cleanup_expired_webhooks)
        
        return {"message": "Expired webhooks cleanup triggered successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")


@router.get("/status/{user_id}")
async def get_calendar_sync_status(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get calendar sync status for a user."""
    try:
        # Only allow users to check their own status
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Can only check your own status")
        
        # This would need to be implemented in the CalendarService
        # For now, return a placeholder response
        return {
            "user_id": user_id,
            "service_type": "calendar",
            "last_sync_at": None,
            "sync_frequency": "normal",
            "change_frequency": "medium",
            "is_active": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.get("/events/{event_id}")
async def get_calendar_event_details(
    event_id: str,
    calendar_id: str = "primary",
    current_user: User = Depends(get_current_user)
):
    """Get detailed information for a specific calendar event."""
    try:
        calendar_service = CalendarService()
        
        event_details = await calendar_service.get_meeting_details(
            event_id=event_id,
            user_id=current_user.id,
            calendar_id=calendar_id
        )
        
        if not event_details:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return event_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event details: {str(e)}")


@router.post("/cron/execute")
async def execute_calendar_polling_cron(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Execute calendar polling cron job (admin only)."""
    try:
        # Check if user is admin (you may need to implement this check)
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = CalendarPollingCronService()
        
        # Add cron execution to background queue
        background_tasks.add_task(cron_service.execute_polling_cron)
        
        return {"message": "Calendar polling cron job triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger cron job: {str(e)}")


@router.post("/cron/batch-poll")
async def execute_batch_calendar_polling(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Execute batch calendar polling for all active users (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = CalendarPollingCronService()
        
        # Add batch polling to background queue
        background_tasks.add_task(cron_service.poll_all_active_calendars)
        
        return {"message": "Batch calendar polling triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger batch polling: {str(e)}")


@router.get("/cron/metrics")
async def get_calendar_cron_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get calendar cron job metrics (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = CalendarPollingCronService()
        metrics = await cron_service.get_cron_job_metrics()
        
        return metrics.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cron metrics: {str(e)}")


@router.post("/poll/{user_id}")
async def poll_calendar_for_user(
    user_id: str,
    request: CalendarPollingRequest,
    current_user: User = Depends(get_current_user)
):
    """Poll calendar for a specific user."""
    try:
        # Only allow users to poll their own calendar
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Can only poll your own calendar")
        
        polling_service = CalendarPollingService()
        
        result = await polling_service.poll_calendar_for_user(
            user_id=user_id,
            calendar_id=request.calendar_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll calendar: {str(e)}")


@router.post("/smart-poll/{user_id}")
async def smart_calendar_polling(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Execute smart calendar polling for a user."""
    try:
        # Only allow users to poll their own calendar
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Can only poll your own calendar")
        
        polling_service = CalendarPollingService()
        
        result = await polling_service.smart_calendar_polling(user_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute smart polling: {str(e)}")


@router.post("/renewal/expired-watches")
async def renew_expired_calendar_watches(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Renew expired calendar watches (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        renewal_service = CalendarWatchRenewalService()
        
        # Add renewal task to background queue
        background_tasks.add_task(renewal_service.renew_expired_watches)
        
        return {"message": "Expired calendar watch renewal triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger watch renewal: {str(e)}")


@router.post("/renewal/expired-webhooks")
async def renew_expired_calendar_webhooks(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Renew expired calendar webhooks (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        renewal_service = CalendarWebhookRenewalService()
        
        # Add renewal task to background queue
        background_tasks.add_task(renewal_service.renew_expired_webhooks)
        
        return {"message": "Expired calendar webhook renewal triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger webhook renewal: {str(e)}")


@router.post("/renewal/user-watches/{user_id}")
async def renew_user_calendar_watches(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Renew calendar watches for a specific user (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        renewal_service = CalendarWatchRenewalService()
        
        # Add renewal task to background queue
        background_tasks.add_task(renewal_service.renew_user_watches, user_id)
        
        return {"message": f"Calendar watch renewal triggered for user {user_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger user watch renewal: {str(e)}")


@router.post("/renewal/user-webhooks/{user_id}")
async def renew_user_calendar_webhooks(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Renew calendar webhooks for a specific user (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        renewal_service = CalendarWebhookRenewalService()
        
        # Add renewal task to background queue
        background_tasks.add_task(renewal_service.renew_user_webhooks, user_id)
        
        return {"message": f"Calendar webhook renewal triggered for user {user_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger user webhook renewal: {str(e)}")


@router.post("/webhook/stop")
async def stop_calendar_webhook(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Stop user's calendar webhook.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Operation result
    """
    try:
        from ...services.calendar.calendar_webhook_management_service import CalendarWebhookManagementService
        
        service = CalendarWebhookManagementService()
        
        result = await service.stop_webhook(current_user.id)
        
        if result.get('success'):
            return {
                'success': True,
                'message': result.get('message'),
                'webhook_id': result.get('webhook_id')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error_message', 'Failed to stop webhook')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping webhook: {str(e)}"
        )


@router.post("/webhook/recreate")
async def recreate_calendar_webhook(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Recreate user's calendar webhook.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Operation result
    """
    try:
        from ...services.calendar.calendar_webhook_management_service import CalendarWebhookManagementService
        
        service = CalendarWebhookManagementService()
        
        result = await service.recreate_webhook(current_user.id)
        
        if result.get('success'):
            return {
                'success': True,
                'message': result.get('message'),
                'webhook_id': result.get('webhook_id')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error_message', 'Failed to recreate webhook')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recreating webhook: {str(e)}"
        )


@router.post("/webhook/verify")
async def verify_calendar_webhook(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify user's calendar webhook.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Verification result
    """
    try:
        from ...services.calendar.calendar_webhook_management_service import CalendarWebhookManagementService
        
        service = CalendarWebhookManagementService()
        
        result = await service.verify_webhook(current_user.id)
        
        if result.get('success'):
            return {
                'success': True,
                'message': result.get('message'),
                'webhook_id': result.get('webhook_id')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error_message', 'Failed to verify webhook')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying webhook: {str(e)}"
        )


@router.post("/webhook/test")
async def test_calendar_webhook(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test user's calendar webhook.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Test result
    """
    try:
        from ...services.calendar.calendar_webhook_management_service import CalendarWebhookManagementService
        
        service = CalendarWebhookManagementService()
        
        result = await service.test_webhook(current_user.id)
        
        if result.get('success'):
            return {
                'success': True,
                'message': result.get('message'),
                'webhook_id': result.get('webhook_id')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error_message', 'Failed to test webhook')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing webhook: {str(e)}"
        )
