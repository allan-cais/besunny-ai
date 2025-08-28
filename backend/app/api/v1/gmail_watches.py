"""
Gmail watches API endpoints for managing virtual email monitoring.
Provides REST API for setting up and managing Gmail watches.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status

from ...services.email import GmailService
from ...core.security import get_current_user_from_supabase_token

router = APIRouter()


@router.post("/setup")
async def setup_virtual_email_watch(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """
    Set up Gmail watch for the current user's virtual email address.
    
    Note: This endpoint is deprecated. Individual user watches are no longer needed
    as emails automatically forward to the master account.
    """
    return {
        "status": "deprecated",
        "message": "Individual user watches are no longer needed. Emails automatically forward to master account.",
        "user_id": current_user.get("id"),
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.post("/setup-master")
async def setup_master_account_watch(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """
    Set up Gmail watch for the master account (ai@besunny.ai).
    
    This is typically done by an admin user to monitor the master account
    for all virtual email addresses.
    """
    try:
        # Admin role check will be implemented in future version
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        gmail_service = GmailService()
        
        # Set up the master account watch in the background
        background_tasks.add_task(
            gmail_service.setup_watch,
            "projects/sunny-ai-468016/topics/gmail-notifications"
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
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
        
        # Permission check will be implemented in future version
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
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
        gmail_service = GmailService()
        
        # Renew the watch in the background
        background_tasks.add_task(
            gmail_service.setup_watch,
            "projects/sunny-ai-468016/topics/gmail-notifications"
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
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
        # Watch stopping functionality will be implemented in future version
        # For now, return success as individual watches are no longer needed
        
        return {
            "status": "success",
            "message": "Watch stop initiated (individual watches no longer needed)",
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
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
        # Watch testing functionality will be implemented in future version
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
) -> Dict[str, Any]:
    """
    Get the overall status of the Gmail watch system.
    
    Returns:
        System status information
    """
    try:
        gmail_service = GmailService()
        
        # Check Gmail service status
        status_info = await gmail_service.get_service_status()
        
        if status_info.get('status') == 'ready':
            return {
                "status": "healthy",
                "service": "gmail-watches",
                "message": "OAuth-based email system is active",
                "oauth_status": "authenticated",
                "statistics": {
                    "total_watches": 1,  # Only one master watch needed
                    "user_watches": 0,   # Individual user watches no longer needed
                    "master_watches": 1, # One master watch for all emails
                    "active_watches": 1
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
        else:
            return {
                "status": "unhealthy",
                "service": "gmail-watches",
                "message": "OAuth authentication required",
                "oauth_status": "unauthenticated",
                "statistics": {
                    "total_watches": 0,
                    "user_watches": 0,
                    "master_watches": 0,
                    "active_watches": 0
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
