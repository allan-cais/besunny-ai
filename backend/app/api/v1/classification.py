"""
Classification API endpoints for BeSunny.ai Python backend.
Provides AI-powered document classification and analysis capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import time

from ...services.ai.classification_service import (
    ClassificationService,
    ClassificationRequest,
    BatchClassificationRequest,
    ClassificationResult,
    BatchClassificationResult
)
from ...models.schemas.document import DocumentType, ClassificationSource
from ...core.database import get_db
from ...core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/documents/classify", response_model=ClassificationResult)
async def classify_document(
    request: ClassificationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Classify a single document using AI.
    
    This endpoint performs AI-powered document classification including:
    - Document type detection
    - Content categorization
    - Keyword extraction
    - Summary generation
    - Vector embedding creation
    """
    try:
        classification_service = ClassificationService()
        await classification_service.initialize()
        
        # Add user context to request
        request.user_preferences = request.user_preferences or {}
        request.user_preferences["user_id"] = current_user.get("id")
        
        # Perform classification
        result = await classification_service.classify_document(request)
        
        if not result:
            raise HTTPException(status_code=500, detail="Classification failed")
        
        # Add background task for post-processing if needed
        if result.confidence_score > 0.8:
            background_tasks.add_task(
                _post_process_successful_classification,
                result.document_id,
                result.document_type
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Document classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/documents/classify/batch", response_model=BatchClassificationResult)
async def classify_documents_batch(
    request: BatchClassificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Classify multiple documents in batch using AI.
    
    This endpoint processes multiple documents concurrently for efficient
    batch classification operations.
    """
    try:
        classification_service = ClassificationService()
        await classification_service.initialize()
        
        # Add user context to batch request
        if request.user_preferences is None:
            request.user_preferences = {}
        request.user_preferences["user_id"] = current_user.get("id")
        
        # Perform batch classification
        result = await classification_service.classify_documents_batch(request)
        
        if not result:
            raise HTTPException(status_code=500, detail="Batch classification failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Batch classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch classification failed: {str(e)}")


@router.post("/documents/{document_id}/reclassify", response_model=ClassificationResult)
async def reclassify_document(
    document_id: str,
    content: str,
    project_id: Optional[str] = None,
    user_preferences: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Reclassify an existing document using AI.
    
    This endpoint allows reclassification of documents when content changes
    or when improved classification is needed.
    """
    try:
        classification_service = ClassificationService()
        await classification_service.initialize()
        
        # Add user context
        if user_preferences is None:
            user_preferences = {}
        user_preferences["user_id"] = current_user.get("id")
        
        # Perform reclassification
        result = await classification_service.reclassify_document(
            document_id=document_id,
            content=content,
            project_id=project_id,
            user_preferences=user_preferences
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Reclassification failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Document reclassification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reclassification failed: {str(e)}")


@router.get("/documents/similar")
async def find_similar_documents(
    query: str,
    project_id: Optional[str] = None,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
    current_user: dict = Depends(get_current_user)
):
    """
    Find similar documents using vector similarity search.
    
    This endpoint uses AI embeddings to find documents with similar content
    to the provided query.
    """
    try:
        classification_service = ClassificationService()
        await classification_service.initialize()
        
        # Find similar documents
        similar_docs = await classification_service.get_similar_documents(
            query=query,
            project_id=project_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return {
            "query": query,
            "similar_documents": similar_docs,
            "total_results": len(similar_docs),
            "project_id": project_id,
            "similarity_threshold": similarity_threshold
        }
        
    except Exception as e:
        logger.error(f"Similar document search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/analytics")
async def get_classification_analytics(
    project_id: Optional[str] = None,
    time_range: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics about document classifications.
    
    This endpoint provides insights into classification performance,
    document types, and processing statistics.
    """
    try:
        classification_service = ClassificationService()
        await classification_service.initialize()
        
        # Get analytics
        analytics = await classification_service.get_classification_analytics(
            project_id=project_id,
            time_range=time_range
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.put("/model")
async def update_classification_model(
    model_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the classification model.
    
    This endpoint allows administrators to switch between different
    AI models for document classification.
    """
    try:
        # Check if user has admin privileges (implement as needed)
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="Admin privileges required")
        
        classification_service = ClassificationService()
        await classification_service.initialize()
        
        # Update model
        success = await classification_service.update_classification_model(model_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="Model update failed")
        
        return {
            "message": f"Classification model updated to {model_name}",
            "model_name": model_name,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Model update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model update failed: {str(e)}")


@router.get("/health")
async def classification_health_check():
    """
    Lightweight health check for classification service.
    
    This endpoint verifies that the AI classification services
    are properly configured without initializing heavy services.
    """
    try:
        # Check if required configuration is available
        from ...core.config import get_settings
        settings = get_settings()
        
        has_openai_key = bool(settings.openai_api_key)
        has_model_config = bool(settings.openai_model)
        
        if has_openai_key and has_model_config:
            return {
                "status": "healthy",
                "service": "classification",
                "configuration": "valid",
                "model": settings.openai_model,
                "message": "Classification service is properly configured",
                "timestamp": time.time()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "classification",
                    "error": "Missing required configuration",
                    "missing": {
                        "openai_api_key": not has_openai_key,
                        "openai_model": not has_model_config
                    },
                    "timestamp": time.time()
                }
            )
        
    except Exception as e:
        logger.error(f"Classification health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "classification",
                "error": str(e),
                "timestamp": time.time()
            }
        )


async def _post_process_successful_classification(
    document_id: str,
    document_type: DocumentType
):
    """
    Background task for post-processing successful classifications.
    
    This function handles additional processing tasks that can be
    performed asynchronously after successful classification.
    """
    try:
        logger.info(f"Post-processing classification for document {document_id}")
        
        # Add any post-processing logic here:
        # - Update related documents
        # - Trigger notifications
        # - Update analytics
        # - Cache results
        
        logger.info(f"Post-processing completed for document {document_id}")
        
    except Exception as e:
        logger.error(f"Post-processing failed for document {document_id}: {str(e)}")
