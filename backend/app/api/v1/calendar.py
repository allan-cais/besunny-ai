"""
Google Calendar API endpoints for BeSunny.ai Python backend.
Handles calendar operations, webhooks, and synchronization.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.security import get_current_user
from ...services.calendar.calendar_service import CalendarService
from ...services.calendar.calendar_webhook_management_service import CalendarWebhookManagementService
from ...services.calendar.calendar_webhook_handler import CalendarWebhookHandler
from ...services.calendar.calendar_polling_service import CalendarPollingService
from ...services.calendar.calendar_monitoring_service import CalendarMonitoringService

router = APIRouter(prefix="/calendar", tags=["calendar"])


class CalendarSyncRequest(BaseModel):
    """Request model for calendar sync operations."""
    force_sync: bool = False
    sync_range_days: int = 30


class WebhookHealthRequest(BaseModel):
    """Request model for webhook health checks."""
    user_id: str


@router.post("/sync/{user_id}")
async def sync_calendar(
    user_id: str,
    request: CalendarSyncRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Synchronize calendar for a specific user."""
    try:
        # Check if user is authorized to sync for the specified user_id
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to sync for this user")
        
        service = CalendarService()
        result = await service.sync_calendar_events(
            user_id=user_id,
            sync_range_days=request.sync_range_days
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "events_synced": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/setup/{user_id}")
async def setup_calendar_webhook(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Set up calendar webhook for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to setup webhook for this user")
        
        service = CalendarService()
        webhook_id = await service.setup_calendar_webhook(user_id)
        
        if webhook_id:
            return {
                "success": True,
                "webhook_id": webhook_id,
                "message": "Calendar webhook setup successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to setup calendar webhook")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/stop/{user_id}")
async def stop_calendar_webhook(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop calendar webhook for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to stop webhook for this user")
        
        service = CalendarWebhookManagementService()
        result = await service.stop_webhook(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/recreate/{user_id}")
async def recreate_calendar_webhook(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Recreate calendar webhook for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to recreate webhook for this user")
        
        service = CalendarWebhookManagementService()
        result = await service.recreate_webhook(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/verify/{user_id}")
async def verify_calendar_webhook(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify calendar webhook for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to verify webhook for this user")
        
        service = CalendarWebhookManagementService()
        result = await service.verify_webhook(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/test/{user_id}")
async def test_calendar_webhook(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test calendar webhook for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to test webhook for this user")
        
        service = CalendarWebhookManagementService()
        result = await service.test_webhook(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/health/{user_id}")
async def get_webhook_health(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get webhook health status for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to check webhook health for this user")
        
        service = CalendarWebhookManagementService()
        result = await service.health_check_webhook(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/auto-fix/{user_id}")
async def auto_fix_webhook(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Automatically fix webhook issues for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to auto-fix webhook for this user")
        
        service = CalendarWebhookManagementService()
        result = await service.auto_fix_webhook(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/metrics/{user_id}")
async def get_webhook_metrics(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get webhook processing metrics for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to get webhook metrics for this user")
        
        service = CalendarWebhookHandler()
        result = await service.get_webhook_health_metrics(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poll/{user_id}")
async def poll_calendar(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Poll calendar for changes for a specific user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to poll calendar for this user")
        
        service = CalendarPollingService()
        result = await service.smart_calendar_polling(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meetings/{user_id}")
async def get_user_meetings(
    user_id: str,
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by meeting status"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get meetings for a specific user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to get meetings for this user")
        
        service = CalendarService()
        meetings = await service.get_user_meetings(
            user_id=user_id,
            project_id=project_id,
            status=status
        )
        
        return meetings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{user_id}")
async def get_calendar_status(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive calendar status for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to get calendar status for this user")
        
        # Get webhook health
        webhook_service = CalendarWebhookManagementService()
        webhook_health = await webhook_service.health_check_webhook(user_id)
        
        # Get webhook metrics
        handler_service = CalendarWebhookHandler()
        webhook_metrics = await handler_service.get_webhook_health_metrics(user_id)
        
        # Get last sync time
        supabase = await get_supabase()
        sync_result = await supabase.table("calendar_sync_states") \
            .select("last_sync_at") \
            .eq("user_id", user_id) \
            .single() \
            .execute()
        
        last_sync = sync_result.data.get('last_sync_at') if sync_result.data else None
        
        # Get meeting count
        meetings_result = await supabase.table("meetings") \
            .select("id", count="exact") \
            .eq("user_id", user_id) \
            .execute()
        
        total_meetings = meetings_result.count if meetings_result.count else 0
        
        return {
            "user_id": user_id,
            "webhook_health": webhook_health,
            "webhook_metrics": webhook_metrics,
            "last_sync": last_sync,
            "total_meetings": total_meetings,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/notify")
async def receive_calendar_webhook(
    userId: str = Query(..., description="User ID from webhook"),
    webhook_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Receive and process calendar webhook notifications from Google."""
    try:
        if not webhook_data:
            raise HTTPException(status_code=400, detail="No webhook data received")
        
        # Add user ID to webhook data
        webhook_data['user_id'] = userId
        
        # Process webhook
        handler = CalendarWebhookHandler()
        success = await handler.process_webhook(webhook_data)
        
        if success:
            return {
                "success": True,
                "message": "Webhook processed successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to process webhook")
            
    except Exception as e:
        # logger.error(f"Error processing calendar webhook: {e}") # This line was removed from the new_code, so it's removed here.
        raise HTTPException(status_code=500, detail=str(e))


# Monitoring endpoints
@router.get("/monitoring/health/{user_id}")
async def get_calendar_health(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed calendar health metrics for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to get calendar health for this user")
        
        service = CalendarMonitoringService()
        result = await service.monitor_user_calendar(user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/alerts/{user_id}")
async def get_calendar_alerts(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of alerts to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get calendar alerts for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to get calendar alerts for this user")
        
        service = CalendarMonitoringService()
        alerts = await service.get_user_alerts(user_id, limit)
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_calendar_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Resolve a calendar alert."""
    try:
        service = CalendarMonitoringService()
        success = await service.resolve_alert(alert_id)
        
        if success:
            return {
                "success": True,
                "message": "Alert resolved successfully",
                "alert_id": alert_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to resolve alert")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/execute")
async def execute_calendar_monitoring(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute comprehensive calendar monitoring for all users (admin only)."""
    try:
        # Check if user is admin (you may need to implement this check)
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        service = CalendarMonitoringService()
        result = await service.monitor_all_calendars()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
