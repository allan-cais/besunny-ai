"""
Meeting classification API endpoints.
Handles manual classification of meeting transcripts.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

from ...core.database import get_supabase
from ...core.security import get_current_user
from ...services.attendee.classification_service import ClassificationService
from ...services.attendee.vector_embedding_service import VectorEmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()

class ManualClassificationRequest(BaseModel):
    bot_id: str
    project_id: str

class ClassificationResponse(BaseModel):
    success: bool
    message: str
    project_id: str = None
    error: str = None

@router.get("/unclassified")
async def get_unclassified_meetings(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get meetings that need manual classification."""
    try:
        classification_service = ClassificationService()
        meetings = await classification_service.get_unclassified_meetings(current_user['id'])
        
        return meetings
        
    except Exception as e:
        logger.error(f"Error fetching unclassified meetings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unclassified meetings")

@router.post("/classify", response_model=ClassificationResponse)
async def manually_classify_meeting(
    request: ManualClassificationRequest,
    current_user: dict = Depends(get_current_user)
) -> ClassificationResponse:
    """Manually classify a meeting transcript to a project."""
    try:
        classification_service = ClassificationService()
        
        # Perform manual classification
        result = await classification_service.manual_classify_meeting(
            bot_id=request.bot_id,
            project_id=request.project_id,
            user_id=current_user['id']
        )
        
        if result.get('success'):
            # Trigger vector embedding processing
            embedding_service = VectorEmbeddingService()
            embedding_result = await embedding_service.reprocess_meeting_transcript(
                bot_id=request.bot_id,
                project_id=request.project_id,
                user_id=current_user['id']
            )
            
            if embedding_result.get('success'):
                return ClassificationResponse(
                    success=True,
                    message="Meeting classified and processed successfully",
                    project_id=request.project_id
                )
            else:
                return ClassificationResponse(
                    success=False,
                    error=f"Classification successful but processing failed: {embedding_result.get('error')}"
                )
        else:
            return ClassificationResponse(
                success=False,
                error=result.get('error', 'Classification failed')
            )
            
    except Exception as e:
        logger.error(f"Error in manual classification: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify meeting")

@router.get("/projects")
async def get_user_projects(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get user's projects for classification."""
    try:
        supabase = get_supabase()
        result = supabase.table('projects').select('id, name, description').eq('user_id', current_user['id']).execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"Error fetching user projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")
