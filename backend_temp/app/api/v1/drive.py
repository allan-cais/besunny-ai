"""
Google Drive API endpoints for BeSunny.ai Python backend.
Provides REST API for Drive operations and webhook handling.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ...services.drive import DriveService, DriveWebhookHandler, DrivePollingService, DrivePollingCronService
from ...models.schemas.drive import (
    DriveWatchRequest,
    DriveWatchResponse,
    DriveFileListResponse,
    DriveWebhookLog,
    DriveFile
)
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


@router.post("/watch", response_model=DriveWatchResponse)
async def setup_file_watch(
    request: DriveWatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Set up a file watch for a Google Drive file."""
    try:
        drive_service = DriveService()
        
        # Set up the file watch
        watch_id = await drive_service.setup_file_watch(
            file_id=request.file_id,
            project_id=request.project_id,
            user_id=current_user.id
        )
        
        if watch_id:
            return DriveWatchResponse(
                success=True,
                watch_id=watch_id,
                message="File watch set up successfully"
            )
        else:
            return DriveWatchResponse(
                success=False,
                message="Failed to set up file watch"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set up file watch: {str(e)}")


@router.get("/files/project/{project_id}", response_model=DriveFileListResponse)
async def list_project_files(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """List all Drive files associated with a project."""
    try:
        drive_service = DriveService()
        
        files = await drive_service.list_project_files(
            project_id=project_id,
            user_id=current_user.id
        )
        
        return DriveFileListResponse(
            files=files,
            total_count=len(files),
            next_page_token=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list project files: {str(e)}")


@router.get("/files/{file_id}", response_model=DriveFile)
async def get_file_metadata(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get metadata for a specific Drive file."""
    try:
        drive_service = DriveService()
        
        file_metadata = await drive_service.get_file_metadata(
            file_id=file_id,
            user_id=current_user.id
        )
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        return file_metadata
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")


@router.get("/watches/active", response_model=List[dict])
async def get_active_watches(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get active file watches for the current user."""
    try:
        webhook_handler = DriveWebhookHandler()
        
        watches = await webhook_handler.get_active_watches(project_id=project_id)
        
        # Filter watches by user (this would need to be implemented in the service)
        # For now, return all watches
        return watches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active watches: {str(e)}")


@router.get("/webhooks/logs", response_model=List[DriveWebhookLog])
async def get_webhook_logs(
    file_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get webhook processing logs."""
    try:
        webhook_handler = DriveWebhookHandler()
        
        logs = await webhook_handler.get_webhook_logs(
            file_id=file_id,
            limit=limit
        )
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook logs: {str(e)}")


@router.post("/webhook")
async def handle_drive_webhook(request: Request):
    """Handle incoming Google Drive webhook notifications."""
    try:
        # Get webhook data
        webhook_data = await request.json()
        
        # Process the webhook
        webhook_handler = DriveWebhookHandler()
        success = await webhook_handler.process_webhook(webhook_data)
        
        if success:
            return JSONResponse(content={"status": "success"}, status_code=200)
        else:
            return JSONResponse(content={"status": "error"}, status_code=500)
            
    except Exception as e:
        # Log the error but return 200 to Google (they don't retry on 4xx/5xx)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)


@router.post("/sync/{user_id}")
async def trigger_drive_sync(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger a manual Drive sync for a user."""
    try:
        # Only allow users to sync their own data
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Can only sync own data")
        
        drive_service = DriveService()
        
        # Add sync task to background queue
        background_tasks.add_task(drive_service.process_file_changes, user_id)
        
        return {"message": "Drive sync triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger Drive sync: {str(e)}")


@router.post("/cleanup/expired-watches")
async def cleanup_expired_watches(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Clean up expired file watches."""
    try:
        drive_service = DriveService()
        
        # Add cleanup task to background queue
        background_tasks.add_task(drive_service.cleanup_expired_watches)
        
        return {"message": "Expired watches cleanup triggered successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")


@router.get("/status/{user_id}")
async def get_drive_sync_status(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get Drive sync status for a user."""
    try:
        # Only allow users to check their own status
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Can only check own status")
        
        # This would need to be implemented in the DriveService
        # For now, return a placeholder response
        return {
            "user_id": user_id,
            "service_type": "drive",
            "last_sync_at": None,
            "sync_frequency": "normal",
            "change_frequency": "medium",
            "is_active": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.post("/cron/execute")
async def execute_drive_polling_cron(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Execute drive polling cron job (admin only)."""
    try:
        # Check if user is admin (you may need to implement this check)
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = DrivePollingCronService()
        
        # Add cron execution to background queue
        background_tasks.add_task(cron_service.execute_polling_cron)
        
        return {"message": "Drive polling cron job triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger cron job: {str(e)}")


@router.post("/cron/batch-poll")
async def execute_batch_drive_polling(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Execute batch drive polling for all active files (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = DrivePollingCronService()
        
        # Add batch polling to background queue
        background_tasks.add_task(cron_service.poll_all_active_files)
        
        return {"message": "Batch drive polling triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger batch polling: {str(e)}")


@router.get("/cron/metrics")
async def get_drive_cron_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get drive cron job metrics (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = DrivePollingCronService()
        metrics = await cron_service.get_cron_job_metrics()
        
        return metrics.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cron metrics: {str(e)}")


@router.post("/poll/{file_id}")
async def poll_drive_file(
    file_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Poll a specific Drive file for changes."""
    try:
        polling_service = DrivePollingService()
        
        result = await polling_service.poll_drive_for_file(
            file_id=file_id,
            document_id=document_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll Drive file: {str(e)}")


@router.post("/smart-poll/{file_id}")
async def smart_drive_polling(
    file_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Execute smart Drive polling for a file."""
    try:
        polling_service = DrivePollingService()
        
        result = await polling_service.smart_drive_polling(
            file_id=file_id,
            document_id=document_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute smart polling: {str(e)}")
