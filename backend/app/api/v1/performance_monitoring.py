"""
Performance Monitoring API endpoints for BeSunny.ai Python backend.
Provides system health monitoring, performance metrics, and optimization insights.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging

from ...services.enterprise.performance_monitoring_service import PerformanceMonitoringService
from ...core.security import get_current_user
from ...models.schemas.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["Performance Monitoring"])

# Initialize the performance monitoring service
performance_service = PerformanceMonitoringService()


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    current_user: User = Depends(get_current_user)
):
    """
    Get current system health status.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        System health report with recommendations
    """
    try:
        health_report = await performance_service.get_system_health()
        
        return {
            "success": True,
            "timestamp": health_report.timestamp.isoformat(),
            "overall_health": health_report.overall_health,
            "component_health": {
                "cpu": health_report.cpu_health,
                "memory": health_report.memory_health,
                "disk": health_report.disk_health,
                "network": health_report.network_health
            },
            "recommendations": health_report.recommendations,
            "alerts": health_report.alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/metrics/current", response_model=Dict[str, Any])
async def get_current_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get current system performance metrics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current performance metrics
    """
    try:
        metrics = await performance_service.get_current_metrics()
        
        return {
            "success": True,
            "timestamp": metrics.timestamp.isoformat(),
            "metrics": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_usage_percent": metrics.disk_usage_percent,
                "network_io": metrics.network_io,
                "active_connections": metrics.active_connections,
                "request_count": metrics.request_count,
                "average_response_time": metrics.average_response_time,
                "error_rate": metrics.error_rate
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get current metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current metrics: {str(e)}")


@router.get("/metrics/history", response_model=Dict[str, Any])
async def get_metrics_history(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance metrics history.
    
    Args:
        hours: Number of hours to look back (1-168)
        current_user: Current authenticated user
        
    Returns:
        Performance metrics history
    """
    try:
        metrics_history = await performance_service.get_metrics_history(hours)
        
        return {
            "success": True,
            "time_period_hours": hours,
            "metrics_count": len(metrics_history),
            "metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "disk_usage_percent": m.disk_usage_percent,
                    "network_io": m.network_io,
                    "active_connections": m.active_connections
                }
                for m in metrics_history
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics history: {str(e)}")


@router.get("/metrics/summary", response_model=Dict[str, Any])
async def get_performance_summary(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance summary with averages and peaks.
    
    Args:
        hours: Number of hours to look back (1-168)
        current_user: Current authenticated user
        
    Returns:
        Performance summary with statistics
    """
    try:
        summary = await performance_service.get_system_performance_summary(hours)
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")


@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_system_performance(
    current_user: User = Depends(get_current_user)
):
    """
    Get system performance optimization recommendations.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Optimization recommendations and actions
    """
    try:
        optimization = await performance_service.optimize_system_performance()
        
        return {
            "success": True,
            "optimization": optimization
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization recommendations: {str(e)}")


@router.post("/activity/track", response_model=Dict[str, Any])
async def track_user_activity(
    activity_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Track user activity for analytics.
    
    Args:
        activity_type: Type of activity (api_call, workflow_execution, feature_usage)
        metadata: Additional activity metadata
        current_user: Current authenticated user
        
    Returns:
        Activity tracking confirmation
    """
    try:
        await performance_service.track_user_activity(
            user_id=current_user.id,
            activity_type=activity_type,
            metadata=metadata or {}
        )
        
        current_metrics = await performance_service.get_current_metrics()
        return {
            "success": True,
            "message": "Activity tracked successfully",
            "user_id": current_user.id,
            "activity_type": activity_type,
            "timestamp": current_metrics.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to track user activity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track user activity: {str(e)}")


@router.get("/activity/summary", response_model=Dict[str, Any])
async def get_user_activity_summary(
    current_user: User = Depends(get_current_user)
):
    """
    Get activity summary for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User activity summary
    """
    try:
        activity_summary = await performance_service.get_user_activity_summary(current_user.id)
        
        if not activity_summary:
            return {
                "success": True,
                "user_id": current_user.id,
                "message": "No activity data available",
                "activity": {
                    "api_calls": 0,
                    "workflows_executed": 0,
                    "data_processed": 0,
                    "session_duration": 0,
                    "features_used": []
                }
            }
        
        return {
            "success": True,
            "user_id": current_user.id,
            "activity": {
                "api_calls": activity_summary.api_calls,
                "workflows_executed": activity_summary.workflows_executed,
                "data_processed": activity_summary.data_processed,
                "session_duration": activity_summary.session_duration,
                "features_used": activity_summary.features_used,
                "last_activity": activity_summary.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user activity summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user activity summary: {str(e)}")


@router.get("/alerts", response_model=Dict[str, Any])
async def get_system_alerts(
    current_user: User = Depends(get_current_user)
):
    """
    Get current system alerts and warnings.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        System alerts and warnings
    """
    try:
        # Get current metrics to check for alerts
        current_metrics = await performance_service.get_current_metrics()
        health_report = await performance_service.get_system_health()
        
        alerts = []
        
        # Check for critical conditions
        if current_metrics.cpu_percent > 90:
            alerts.append({
                "level": "critical",
                "component": "CPU",
                "message": f"Critical CPU usage: {current_metrics.cpu_percent:.1f}%",
                "timestamp": current_metrics.timestamp.isoformat()
            })
        elif current_metrics.cpu_percent > 80:
            alerts.append({
                "level": "warning",
                "component": "CPU",
                "message": f"High CPU usage: {current_metrics.cpu_percent:.1f}%",
                "timestamp": current_metrics.timestamp.isoformat()
            })
        
        if current_metrics.memory_percent > 90:
            alerts.append({
                "level": "critical",
                "component": "Memory",
                "message": f"Critical memory usage: {current_metrics.memory_percent:.1f}%",
                "timestamp": current_metrics.timestamp.isoformat()
            })
        elif current_metrics.memory_percent > 85:
            alerts.append({
                "level": "warning",
                "component": "Memory",
                "message": f"High memory usage: {current_metrics.memory_percent:.1f}%",
                "timestamp": current_metrics.timestamp.isoformat()
            })
        
        if current_metrics.disk_usage_percent > 95:
            alerts.append({
                "level": "critical",
                "component": "Disk",
                "message": f"Critical disk usage: {current_metrics.disk_usage_percent:.1f}%",
                "timestamp": current_metrics.timestamp.isoformat()
            })
        elif current_metrics.disk_usage_percent > 90:
            alerts.append({
                "level": "warning",
                "component": "Disk",
                "message": f"High disk usage: {current_metrics.disk_usage_percent:.1f}%",
                "timestamp": current_metrics.timestamp.isoformat()
            })
        
        return {
            "success": True,
            "overall_health": health_report.overall_health,
            "alerts_count": len(alerts),
            "alerts": alerts,
            "timestamp": current_metrics.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system alerts: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_monitoring_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get performance monitoring service status.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Monitoring service status
    """
    try:
        return {
            "success": True,
            "service": "Performance Monitoring Service",
            "status": "active" if performance_service._initialized else "inactive",
            "features": [
                "System metrics collection",
                "Performance monitoring",
                "Health reporting",
                "User activity tracking",
                "Optimization recommendations",
                "Alert management"
            ],
            "endpoints": [
                "/health",
                "/metrics/current",
                "/metrics/history",
                "/metrics/summary",
                "/optimize",
                "/activity/track",
                "/activity/summary",
                "/alerts",
                "/status"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")
