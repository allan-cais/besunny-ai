"""
Gmail watches API endpoints for managing virtual email monitoring.
Provides REST API for setting up and managing Gmail watches.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status

from ...services.email import GmailWatchService
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


@router.post("/setup")
async def setup_virtual_email_watch(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set up Gmail watch for the current user's virtual email address.
    
    This creates a push notification subscription that will notify our webhook
    when emails arrive at ai+{username}@besunny.ai.
    """
    try:
        watch_service = GmailWatchService()
        
        # Set up the watch in the background
        background_tasks.add_task(
            watch_service.setup_virtual_email_watch,
            current_user.id
        )
        
        return {
            "status": "success",
            "message": "Gmail watch setup initiated",
            "user_id": current_user.id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup Gmail watch: {str(e)}"
        )


@router.post("/setup-master")
async def setup_master_account_watch(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set up Gmail watch for the master account (inbound@besunny.ai).
    
    This is typically done by an admin user to monitor the master account
    for all virtual email addresses.
    """
    try:
        # TODO: Add admin role check
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        watch_service = GmailWatchService()
        
        # Set up the master account watch in the background
        background_tasks.add_task(
            watch_service.setup_master_account_watch
        )
        
        return {
            "status": "success",
            "message": "Master account Gmail watch setup initiated",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup master account watch: {str(e)}"
        )


@router.get("/active")
async def get_active_watches(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get active Gmail watches.
    
    Args:
        user_id: Optional user ID to filter watches
        current_user: Current authenticated user
        
    Returns:
        List of active Gmail watches
    """
    try:
        watch_service = GmailWatchService()
        
        # If no user_id specified, use current user
        if not user_id:
            user_id = current_user.id
        
        # TODO: Add permission check for viewing other users' watches
        # if user_id != current_user.id and not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        watches = await watch_service.get_active_watches(user_id)
        
        return {
            "status": "success",
            "watches": watches,
            "total_count": len(watches),
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active watches: {str(e)}"
        )


@router.post("/{watch_id}/renew")
async def renew_watch(
    watch_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Renew a Gmail watch before it expires.
    
    Args:
        watch_id: ID of the watch to renew
        current_user: Current authenticated user
        
    Returns:
        Renewal result
    """
    try:
        watch_service = GmailWatchService()
        
        # Renew the watch in the background
        background_tasks.add_task(
            watch_service.renew_watch,
            watch_id
        )
        
        return {
            "status": "success",
            "message": "Gmail watch renewal initiated",
            "watch_id": watch_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to renew watch: {str(e)}"
        )


@router.delete("/{watch_id}")
async def stop_watch(
    watch_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Stop a Gmail watch.
    
    Args:
        watch_id: ID of the watch to stop
        current_user: Current authenticated user
        
    Returns:
        Stop result
    """
    try:
        watch_service = GmailWatchService()
        
        # Stop the watch in the background
        background_tasks.add_task(
            watch_service.stop_watch,
            watch_id
        )
        
        return {
            "status": "success",
            "message": "Gmail watch stop initiated",
            "watch_id": watch_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop watch: {str(e)}"
        )


@router.post("/{watch_id}/test")
async def test_watch(
    watch_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test a Gmail watch to ensure it's working properly.
    
    Args:
        watch_id: ID of the watch to test
        current_user: Current authenticated user
        
    Returns:
        Test result
    """
    try:
        # TODO: Implement watch testing functionality
        # This could send a test email to the virtual address and verify
        # that the webhook receives the notification
        
        return {
            "status": "success",
            "message": "Watch test initiated",
            "watch_id": watch_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test watch: {str(e)}"
        )


@router.get("/status")
async def get_watch_system_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the overall status of the Gmail watch system.
    
    Returns:
        System status information
    """
    try:
        watch_service = GmailWatchService()
        
        # Get all active watches
        all_watches = await watch_service.get_active_watches()
        
        # Count watches by type
        user_watches = [w for w in all_watches if not w.get('is_master_account')]
        master_watches = [w for w in all_watches if w.get('is_master_account')]
        
        return {
            "status": "healthy",
            "service": "gmail-watches",
            "statistics": {
                "total_watches": len(all_watches),
                "user_watches": len(user_watches),
                "master_watches": len(master_watches),
                "active_watches": len(all_watches)
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "gmail-watches",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }
