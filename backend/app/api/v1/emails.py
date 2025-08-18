"""
Emails API endpoints for BeSunny.ai Python backend.
Provides REST API for email processing and management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status

from ...services.email import EmailProcessingService, GmailPollingService, GmailPollingCronService
from ...models.schemas.email import (
    GmailMessage,
    EmailProcessingResult,
    EmailListResponse,
    EmailStats
)
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


@router.post("/process", response_model=List[EmailProcessingResult])
async def process_inbound_emails(
    messages: List[GmailMessage],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Process multiple inbound email messages."""
    try:
        email_service = EmailProcessingService()
        
        # Process emails in background
        background_tasks.add_task(email_service.process_inbound_emails, messages)
        
        # Return immediate response
        return [
            EmailProcessingResult(
                success=True,
                message="Email queued for processing",
                gmail_message_id=msg.id
            )
            for msg in messages
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process emails: {str(e)}")


@router.post("/process-inbound")
async def process_inbound_email(
    email_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process an inbound email and create a document.
    
    Args:
        email_data: Email data from Gmail
        current_user: Current authenticated user
        
    Returns:
        Processing result
    """
    try:
        from ...services.email.process_inbound_emails_service import ProcessInboundEmailsService
        
        service = ProcessInboundEmailsService()
        
        result = await service.process_inbound_email(email_data, current_user.id)
        
        if result.get('success'):
            return {
                'success': True,
                'message': result.get('message'),
                'document_id': result.get('document_id'),
                'classification_result': result.get('classification_result')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error_message', 'Failed to process email')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing email: {str(e)}"
        )


@router.post("/process-batch")
async def process_batch_emails(
    emails: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process multiple inbound emails in batch.
    
    Args:
        emails: List of email data
        current_user: Current authenticated user
        
    Returns:
        Batch processing results
    """
    try:
        from ...services.email.process_inbound_emails_service import ProcessInboundEmailsService
        
        service = ProcessInboundEmailsService()
        
        results = await service.process_batch_emails(emails, current_user.id)
        
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful
        
        return {
            'success': True,
            'message': f'Batch processing completed: {successful} successful, {failed} failed',
            'total_emails': len(emails),
            'successful': successful,
            'failed': failed,
            'results': results
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch emails: {str(e)}"
        )


@router.get("/", response_model=EmailListResponse)
async def list_emails(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    limit: int = Query(100, description="Number of emails to return"),
    offset: int = Query(0, description="Number of emails to skip"),
    current_user: User = Depends(get_current_user)
):
    """List emails for the current user."""
    try:
        # This would query the documents table for email type documents
        # For now, return empty response
        return EmailListResponse(
            emails=[],
            total_count=0,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list emails: {str(e)}")


@router.get("/stats", response_model=EmailStats)
async def get_email_stats(
    current_user: User = Depends(get_current_user)
):
    """Get email statistics for the current user."""
    try:
        # This would calculate stats from the documents table
        # For now, return placeholder stats
        return EmailStats(
            total_emails=0,
            processed_emails=0,
            failed_emails=0,
            emails_by_project={}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email stats: {str(e)}")


@router.get("/processing-logs")
async def get_email_processing_logs(
    limit: int = Query(100, description="Number of logs to return"),
    current_user: User = Depends(get_current_user)
):
    """Get email processing logs for the current user."""
    try:
        # This would query the email_processing_logs table
        # For now, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing logs: {str(e)}")


@router.post("/setup-watch")
async def setup_email_watch(
    current_user: User = Depends(get_current_user)
):
    """Set up Gmail watch for the current user."""
    try:
        # This would set up Gmail push notifications
        # For now, return success message
        return {"message": "Email watch setup initiated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup email watch: {str(e)}")


@router.get("/watch-status")
async def get_email_watch_status(
    current_user: User = Depends(get_current_user)
):
    """Get Gmail watch status for the current user."""
    try:
        # This would query the gmail_watches table
        # For now, return placeholder status
        return {
            "is_active": False,
            "last_poll_at": None,
            "expiration": None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get watch status: {str(e)}")


@router.post("/cron/execute")
async def execute_gmail_polling_cron(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Execute Gmail polling cron job (admin only)."""
    try:
        # Check if user is admin (you may need to implement this check)
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = GmailPollingCronService()
        
        # Add cron execution to background queue
        background_tasks.add_task(cron_service.execute_polling_cron)
        
        return {"message": "Gmail polling cron job triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger cron job: {str(e)}")


@router.post("/cron/batch-poll")
async def execute_batch_gmail_polling(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Execute batch Gmail polling for all active users (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = GmailPollingCronService()
        
        # Add batch polling to background queue
        background_tasks.add_task(cron_service.poll_all_active_gmail_accounts)
        
        return {"message": "Batch Gmail polling triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger batch polling: {str(e)}")


@router.get("/cron/metrics")
async def get_gmail_cron_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get Gmail cron job metrics (admin only)."""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cron_service = GmailPollingCronService()
        metrics = await cron_service.get_cron_job_metrics()
        
        return metrics.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cron metrics: {str(e)}")


@router.post("/poll/{user_email}")
async def poll_gmail_for_user(
    user_email: str,
    current_user: User = Depends(get_current_user)
):
    """Poll Gmail for a specific user."""
    try:
        # Only allow users to poll their own Gmail
        if current_user.email != user_email:
            raise HTTPException(status_code=403, detail="Can only poll your own Gmail")
        
        polling_service = GmailPollingService()
        
        result = await polling_service.poll_gmail_for_user(user_email)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll Gmail: {str(e)}")


@router.post("/smart-poll/{user_email}")
async def smart_gmail_polling(
    user_email: str,
    current_user: User = Depends(get_current_user)
):
    """Execute smart Gmail polling for a user."""
    try:
        # Only allow users to poll their own Gmail
        if current_user.email != user_email:
            raise HTTPException(status_code=403, detail="Can only poll your own Gmail")
        
        polling_service = GmailPollingService()
        
        result = await polling_service.smart_gmail_polling(user_email)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute smart polling: {str(e)}")
