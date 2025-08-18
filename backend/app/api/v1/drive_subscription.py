"""
Drive File Subscription API endpoints for BeSunny.ai Python backend.
Handles Google Drive file monitoring setup and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ...services.drive.drive_file_subscription_service import DriveFileSubscriptionService
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


class DriveSubscriptionRequest(BaseModel):
    """Drive file subscription request."""
    file_id: str
    document_id: str


class DriveSubscriptionResponse(BaseModel):
    """Drive file subscription response."""
    success: bool
    channel_id: Optional[str] = None
    resource_id: Optional[str] = None
    expiration: Optional[str] = None
    error_message: Optional[str] = None


class DriveSubscriptionStatusResponse(BaseModel):
    """Drive file subscription status response."""
    has_active_watch: bool
    watch_details: Optional[Dict[str, Any]] = None
    expiration: Optional[str] = None
    is_expired: bool
    document_info: Optional[Dict[str, Any]] = None


@router.post("/subscribe", response_model=DriveSubscriptionResponse)
async def subscribe_to_drive_file(
    request: DriveSubscriptionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Subscribe to file changes for a specific document.
    
    Args:
        request: Drive file subscription request
        current_user: Current authenticated user
        
    Returns:
        Subscription result
    """
    try:
        service = DriveFileSubscriptionService()
        
        result = await service.subscribe_to_file(
            user_id=current_user.id,
            document_id=request.document_id,
            file_id=request.file_id
        )
        
        if result.get('success'):
            return DriveSubscriptionResponse(
                success=True,
                channel_id=result.get('channel_id'),
                resource_id=result.get('resource_id'),
                expiration=result.get('expiration').isoformat() if result.get('expiration') else None
            )
        else:
            return DriveSubscriptionResponse(
                success=False,
                error_message=result.get('error', 'Unknown error')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subscribing to drive file: {str(e)}"
        )


@router.get("/status/{file_id}", response_model=DriveSubscriptionStatusResponse)
async def get_drive_subscription_status(
    file_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get drive file subscription status for a specific file.
    
    Args:
        file_id: Google Drive file ID
        current_user: Current authenticated user
        
    Returns:
        Subscription status information
    """
    try:
        service = DriveFileSubscriptionService()
        
        # Get existing watch
        existing_watch = await service._get_existing_file_watch(file_id)
        
        # Get document info
        document_info = None
        if existing_watch and existing_watch.get('document_id'):
            document_info = await service._get_document_info(existing_watch['document_id'])
        
        if existing_watch and service._is_watch_active(existing_watch):
            return DriveSubscriptionStatusResponse(
                has_active_watch=True,
                watch_details=existing_watch,
                expiration=existing_watch.get('expiration'),
                is_expired=False,
                document_info=document_info
            )
        else:
            return DriveSubscriptionStatusResponse(
                has_active_watch=False,
                watch_details=existing_watch if existing_watch else None,
                expiration=existing_watch.get('expiration') if existing_watch else None,
                is_expired=True if existing_watch else False,
                document_info=document_info
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting drive subscription status: {str(e)}"
        )


@router.delete("/unsubscribe/{file_id}")
async def unsubscribe_from_drive_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Unsubscribe from file changes for a specific file.
    
    Args:
        file_id: Google Drive file ID
        current_user: Current authenticated user
        
    Returns:
        Unsubscription result
    """
    try:
        service = DriveFileSubscriptionService()
        
        # Get existing watch
        existing_watch = await service._get_existing_file_watch(file_id)
        
        if not existing_watch:
            return {
                "success": True,
                "message": "No active file watch found"
            }
        
        # Verify user owns the document
        if existing_watch.get('document_id'):
            document_info = await service._get_document_info(existing_watch['document_id'])
            if document_info and document_info.get('created_by') != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to manage this file watch"
                )
        
        # Deactivate watch in database
        watch_data = {
            'file_id': file_id,
            'is_active': False,
            'updated_at': datetime.now().isoformat()
        }
        
        await service._upsert_file_watch(watch_data)
        
        return {
            "success": True,
            "message": "File watch removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unsubscribing from drive file: {str(e)}"
        )


@router.post("/renew/{file_id}")
async def renew_drive_subscription(
    file_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Renew drive file subscription for a specific file.
    
    Args:
        file_id: Google Drive file ID
        current_user: Current authenticated user
        
    Returns:
        Renewal result
    """
    try:
        service = DriveFileSubscriptionService()
        
        # Get existing watch to find document info
        existing_watch = await service._get_existing_file_watch(file_id)
        if not existing_watch or not existing_watch.get('document_id'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existing file watch found"
            )
        
        # Verify user owns the document
        document_info = await service._get_document_info(existing_watch['document_id'])
        if document_info and document_info.get('created_by') != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage this file watch"
            )
        
        # Check if user has Google credentials
        credentials = await service._get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Google credentials found for user"
            )
        
        # Set up new subscription
        result = await service.subscribe_to_file(
            user_id=current_user.id,
            document_id=existing_watch['document_id'],
            file_id=file_id
        )
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Drive file subscription renewed successfully",
                "channel_id": result.get('channel_id'),
                "resource_id": result.get('resource_id'),
                "expiration": result.get('expiration').isoformat() if result.get('expiration') else None
            }
        else:
            return {
                "success": False,
                "error_message": result.get('error', 'Unknown error')
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error renewing drive file subscription: {str(e)}"
        )


@router.get("/list")
async def list_user_drive_subscriptions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all drive file subscriptions for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of user's drive subscriptions
    """
    try:
        service = DriveFileSubscriptionService()
        
        # Get all documents owned by user that have file IDs
        user_documents = await service._get_user_documents_with_files(current_user.id)
        
        subscriptions = []
        for doc in user_documents:
            if doc.get('file_id'):
                watch = await service._get_existing_file_watch(doc['file_id'])
                if watch:
                    subscriptions.append({
                        'document_id': doc['id'],
                        'document_title': doc.get('title'),
                        'file_id': doc['file_id'],
                        'watch_active': watch.get('is_active', False),
                        'expiration': watch.get('expiration'),
                        'last_poll_at': watch.get('last_poll_at'),
                        'last_webhook_received': watch.get('last_webhook_received')
                    })
        
        return {
            "success": True,
            "subscriptions": subscriptions,
            "total_count": len(subscriptions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing drive subscriptions: {str(e)}"
        )
