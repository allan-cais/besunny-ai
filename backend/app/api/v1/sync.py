"""
Sync API endpoints for BeSunny.ai Python backend.
Handles multi-service synchronization and adaptive sync operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ...services.sync import EnhancedAdaptiveSyncService
from ...core.security import get_current_user

router = APIRouter()


class SyncRequest(BaseModel):
    """Request model for sync operations."""
    force_sync: bool = False
    services: Optional[List[str]] = None  # If None, sync all services


class ServiceSyncRequest(BaseModel):
    """Request model for single service sync."""
    force_sync: bool = False


@router.post("/sync-all/{user_id}")
async def sync_all_services(
    user_id: str,
    request: SyncRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Synchronize all services for a user."""
    try:
        # Check if user is authorized to sync for the specified user_id
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to sync for this user")
        
        sync_service = EnhancedAdaptiveSyncService()
        result = await sync_service.sync_all_services(user_id, request.force_sync)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{service}/{user_id}")
async def sync_single_service(
    service: str,
    user_id: str,
    request: ServiceSyncRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Synchronize a specific service for a user."""
    try:
        # Check if user is authorized to sync for the specified user_id
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to sync for this user")
        
        sync_service = EnhancedAdaptiveSyncService()
        
        # Route to appropriate service sync method
        if service == "calendar":
            result = await sync_service.sync_calendar(user_id, request.force_sync)
        elif service == "drive":
            result = await sync_service.sync_drive(user_id, request.force_sync)
        elif service == "gmail":
            result = await sync_service.sync_gmail(user_id, user_id, request.force_sync)
        elif service == "attendee":
            result = await sync_service.sync_attendee(user_id, request.force_sync)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-activity")
async def record_user_activity(
    activity_type: str = Query(..., description="Type of activity"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Record user activity for sync optimization."""
    try:
        sync_service = EnhancedAdaptiveSyncService()
        await sync_service.record_user_activity(current_user["id"], activity_type)
        return {"success": True, "message": "Activity recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/next-sync/{user_id}")
async def get_next_sync_interval(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get next sync interval for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's sync info")
        
        sync_service = EnhancedAdaptiveSyncService()
        
        # Get user's current sync state
        from ...services.sync import EnhancedAdaptiveSyncService
        user_state = await sync_service._get_user_activity_state(user_id)
        
        if not user_state:
            return {
                "next_sync_in_minutes": 30,
                "change_frequency": "medium",
                "sync_priority": "normal"
            }
        
        return {
            "next_sync_in_minutes": user_state.get("next_sync_interval", 30),
            "change_frequency": user_state.get("change_frequency", "medium"),
            "sync_priority": user_state.get("sync_priority", "normal"),
            "last_sync_at": user_state.get("last_sync_at"),
            "virtual_email_activity": user_state.get("virtual_email_activity", False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-status/{user_id}")
async def get_sync_status(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive sync status for a user."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's sync info")
        
        sync_service = EnhancedAdaptiveSyncService()
        
        # Get user's current sync state
        user_state = await sync_service._get_user_activity_state(user_id)
        
        # Get recent sync results
        from ...core.database import get_supabase
        supabase = get_supabase()
        
        recent_syncs = supabase.table("sync_results") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("timestamp", desc=True) \
            .limit(10) \
            .execute()
        
        sync_history = recent_syncs.data if recent_syncs.data else []
        
        # Calculate sync statistics
        total_syncs = len(sync_history)
        successful_syncs = len([s for s in sync_history if s.get("success")])
        failed_syncs = total_syncs - successful_syncs
        
        # Get service-specific status
        services_status = {}
        for service in ["calendar", "drive", "gmail", "attendee"]:
            service_syncs = [s for s in sync_history if s.get("service") == service]
            if service_syncs:
                last_service_sync = service_syncs[0]
                services_status[service] = {
                    "last_sync": last_service_sync.get("timestamp"),
                    "last_success": last_service_sync.get("success"),
                    "items_processed": last_service_sync.get("items_processed", 0)
                }
            else:
                services_status[service] = {
                    "last_sync": None,
                    "last_success": None,
                    "items_processed": 0
                }
        
        return {
            "user_id": user_id,
            "sync_state": user_state,
            "sync_statistics": {
                "total_syncs": total_syncs,
                "successful_syncs": successful_syncs,
                "failed_syncs": failed_syncs,
                "success_rate": successful_syncs / total_syncs if total_syncs > 0 else 0
            },
            "services_status": services_status,
            "recent_syncs": sync_history[:5]  # Last 5 syncs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force-sync/{user_id}")
async def force_sync_all_services(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Force sync all services for a user regardless of timing."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to sync for this user")
        
        sync_service = EnhancedAdaptiveSyncService()
        result = await sync_service.sync_all_services(user_id, force_sync=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-metrics/{user_id}")
async def get_sync_metrics(
    user_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get sync performance metrics for a user over a specified period."""
    try:
        # Check if user is authorized
        if current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's metrics")
        
        from ...core.database import get_supabase
        from datetime import datetime, timedelta
        
        supabase = get_supabase()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get sync results for the period
        sync_results = supabase.table("sync_results") \
            .select("*") \
            .eq("user_id", user_id) \
            .gte("timestamp", start_date.isoformat()) \
            .lte("timestamp", end_date.isoformat()) \
            .execute()
        
        results = sync_results.data if sync_results.data else []
        
        if not results:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_syncs": 0,
                "average_processing_time": 0,
                "success_rate": 0,
                "service_breakdown": {},
                "daily_trends": []
            }
        
        # Calculate metrics
        total_syncs = len(results)
        successful_syncs = len([r for r in results if r.get("success")])
        success_rate = successful_syncs / total_syncs if total_syncs > 0 else 0
        
        # Calculate average processing time
        processing_times = [r.get("processing_time_ms", 0) for r in results if r.get("processing_time_ms")]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Service breakdown
        service_breakdown = {}
        for result in results:
            service = result.get("service", "unknown")
            if service not in service_breakdown:
                service_breakdown[service] = {
                    "total_syncs": 0,
                    "successful_syncs": 0,
                    "total_items_processed": 0
                }
            
            service_breakdown[service]["total_syncs"] += 1
            if result.get("success"):
                service_breakdown[service]["successful_syncs"] += 1
            
            service_breakdown[service]["total_items_processed"] += result.get("items_processed", 0)
        
        # Calculate success rates for each service
        for service in service_breakdown:
            total = service_breakdown[service]["total_syncs"]
            successful = service_breakdown[service]["successful_syncs"]
            service_breakdown[service]["success_rate"] = successful / total if total > 0 else 0
        
        # Daily trends (simplified)
        daily_trends = []
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            day_results = [r for r in results if r.get("timestamp", "").startswith(date_str)]
            daily_trends.append({
                "date": date_str,
                "total_syncs": len(day_results),
                "successful_syncs": len([r for r in day_results if r.get("success")])
            })
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "success_rate": success_rate,
            "average_processing_time_ms": avg_processing_time,
            "service_breakdown": service_breakdown,
            "daily_trends": daily_trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
