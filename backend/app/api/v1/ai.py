"""
AI API endpoints for BeSunny.ai Python backend.
Provides access to core AI services including document analysis, summarization, and entity extraction.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import time

from ...services.ai.ai_service import (
    AIService,
    AIProcessingResult,
    DocumentAnalysisResult
)
from ...services.ai.enhanced_classification_service import (
    EnhancedClassificationService,
    EnhancedClassificationRequest,
    EnhancedClassificationResult,
    ClassificationBatch
)
from ...services.ai.auto_schedule_bots_service import (
    AutoScheduleBotsService,
    BotSchedulingRequest,
    BotSchedulingResult,
    BatchBotSchedulingRequest
)
from ...services.ai.document_workflow_service import (
    DocumentWorkflowService,
    DocumentWorkflow,
    WorkflowExecution
)
from ...services.ai.project_onboarding_service import ProjectOnboardingAIService
from ...core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/documents/analyze", response_model=AIProcessingResult)
async def analyze_document_content(
    content: str,
    analysis_type: str = "comprehensive",
    project_context: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze document content using AI.
    
    This endpoint performs comprehensive analysis of document content including:
    - Content categorization
    - Key point extraction
    - Topic identification
    - Sentiment analysis
    - Language detection
    """
    try:
        ai_service = AIService()
        
        # Perform document analysis
        result = await ai_service.analyze_document_content(
            content=content,
            analysis_type=analysis_type
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Document analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/documents/summarize", response_model=AIProcessingResult)
async def generate_document_summary(
    content: str,
    max_length: int = 200,
    summary_type: str = "general",
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a document summary using AI.
    
    This endpoint creates concise summaries of document content with
    configurable length and style preferences.
    """
    try:
        ai_service = AIService()
        
        # Generate summary
        result = await ai_service.generate_document_summary(
            content=content,
            max_length=max_length,
            summary_type=summary_type
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Summary generation failed: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/documents/entities", response_model=AIProcessingResult)
async def extract_entities(
    content: str,
    entity_types: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Extract named entities from document content.
    
    This endpoint identifies and extracts various types of entities including:
    - People names
    - Organizations
    - Locations
    - Dates
    - Monetary amounts
    """
    try:
        ai_service = AIService()
        
        # Extract entities
        result = await ai_service.extract_entities(
            content=content,
            entity_types=entity_types
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Entity extraction failed: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


@router.post("/documents/classify", response_model=AIProcessingResult)
async def classify_document_ai(
    content: str,
    project_context: Optional[str] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Classify a document using AI.
    
    This endpoint performs AI-powered document classification with
    configurable project context and user preferences.
    """
    try:
        ai_service = AIService()
        
        # Add user context
        if user_preferences is None:
            user_preferences = {}
        user_preferences["user_id"] = current_user.get("id")
        
        # Perform classification
        result = await ai_service.classify_document(
            content=content,
            project_context=project_context,
            user_preferences=user_preferences
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Classification failed: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Document classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/documents/analyze/batch")
async def analyze_documents_batch(
    documents: List[Dict[str, Any]],
    analysis_type: str = "comprehensive",
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze multiple documents in batch using AI.
    
    This endpoint processes multiple documents concurrently for efficient
    batch analysis operations.
    """
    try:
        ai_service = AIService()
        
        # Process documents concurrently
        tasks = []
        for doc in documents:
            task = ai_service.analyze_document_content(
                content=doc.get("content", ""),
                analysis_type=analysis_type
            )
            tasks.append(task)
        
        # Execute all analyses concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "document_index": i,
                    "error": str(result)
                })
            elif result.success:
                successful_results.append(result)
            else:
                failed_results.append({
                    "document_index": i,
                    "error": result.error_message
                })
        
        return {
            "total_documents": len(documents),
            "successful_analyses": len(successful_results),
            "failed_analyses": len(failed_results),
            "results": successful_results,
            "errors": failed_results
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.post("/documents/enhance")
async def enhance_document_content(
    content: str,
    enhancement_type: str = "comprehensive",
    current_user: dict = Depends(get_current_user)
):
    """
    Enhance document content using AI.
    
    This endpoint provides various content enhancement capabilities including:
    - Grammar and style improvements
    - Content expansion
    - Formatting optimization
    - Readability improvements
    """
    try:
        ai_service = AIService()
        
        # Define enhancement prompts based on type
        enhancement_prompts = {
            "grammar": "Improve the grammar and style of the following text while maintaining the original meaning:",
            "expand": "Expand and elaborate on the following content to make it more comprehensive:",
            "format": "Reformat the following content to improve readability and structure:",
            "simplify": "Simplify the following content to make it more accessible and easier to understand:",
            "comprehensive": "Enhance the following content by improving grammar, style, structure, and readability:"
        }
        
        prompt = enhancement_prompts.get(enhancement_type, enhancement_prompts["comprehensive"])
        
        # Perform enhancement
        response = await ai_service.client.chat.completions.create(
            model=ai_service.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": content[:4000]}
            ],
            temperature=0.3,
            max_tokens=len(content) + 500
        )
        
        enhanced_content = response.choices[0].message.content.strip()
        
        return {
            "original_content": content,
            "enhanced_content": enhanced_content,
            "enhancement_type": enhancement_type,
            "improvements_made": "Content enhanced for better readability and structure"
        }
        
    except Exception as e:
        logger.error(f"Content enhancement failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content enhancement failed: {str(e)}")


@router.get("/models")
async def get_available_models(current_user: dict = Depends(get_current_user)):
    """
    Get available AI models and their capabilities.
    
    This endpoint provides information about available AI models
    and their supported features.
    """
    try:
        ai_service = AIService()
        
        # Define available models and their capabilities
        available_models = {
            "gpt-4": {
                "name": "GPT-4",
                "capabilities": [
                    "document_classification",
                    "content_analysis",
                    "summarization",
                    "entity_extraction",
                    "sentiment_analysis",
                    "content_enhancement"
                ],
                "max_tokens": 8192,
                "recommended_for": "complex_analysis"
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "capabilities": [
                    "document_classification",
                    "content_analysis",
                    "summarization",
                    "entity_extraction"
                ],
                "max_tokens": 4096,
                "recommended_for": "standard_analysis"
            }
        }
        
        return {
            "available_models": available_models,
            "current_model": ai_service.model,
            "model_config": {
                "max_tokens": ai_service.max_tokens,
                "temperature_range": "0.0 - 1.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Model information retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model information failed: {str(e)}")


@router.get("/health")
async def ai_service_health_check():
    """
    Lightweight health check for AI service.
    
    This endpoint verifies that the AI service configuration
    is valid without initializing heavy services.
    """
    try:
        # Check if OpenAI API key is configured
        from ...core.config import get_settings
        settings = get_settings()
        
        has_openai_key = bool(settings.openai_api_key)
        has_model_config = bool(settings.openai_model)
        
        if has_openai_key and has_model_config:
            return {
                "status": "healthy",
                "service": "ai",
                "configuration": "valid",
                "model": settings.openai_model,
                "message": "AI service is properly configured",
                "timestamp": time.time()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "ai",
                    "error": "Missing required configuration",
                    "missing": {
                        "openai_api_key": not has_openai_key,
                        "openai_model": not has_model_config
                    },
                    "timestamp": time.time()
                }
            )
        
    except Exception as e:
        logger.error(f"AI service health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "ai",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@router.get("/usage")
async def get_ai_usage_stats(
    time_range: str = "24h",
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI service usage statistics.
    
    This endpoint provides usage metrics for AI services including
    token usage, cost estimates, and request counts.
    """
    try:
        # This would typically query a usage tracking database
        # For now, return mock data structure
        
        usage_stats = {
            "time_range": time_range,
            "total_requests": 150,
            "successful_requests": 145,
            "failed_requests": 5,
            "total_tokens_used": 25000,
            "estimated_cost": 0.75,
            "model_breakdown": {
                "gpt-4": {
                    "requests": 100,
                    "tokens": 20000,
                    "cost": 0.60
                },
                "gpt-3.5-turbo": {
                    "requests": 50,
                    "tokens": 5000,
                    "cost": 0.15
                }
            },
            "endpoint_usage": {
                "classification": 60,
                "analysis": 45,
                "summarization": 30,
                "entity_extraction": 15
            }
        }
        
        return usage_stats
        
    except Exception as e:
        logger.error(f"Usage statistics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Usage statistics failed: {str(e)}")


# Import asyncio for batch processing
import asyncio

# Enhanced Classification Endpoints
@router.post("/classification/enhanced", response_model=EnhancedClassificationResult)
async def enhanced_document_classification(
    request: EnhancedClassificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Perform enhanced document classification with AI-powered analysis.
    
    This endpoint provides advanced classification capabilities including:
    - Multi-stage classification workflows
    - Sentiment analysis
    - Entity extraction
    - Intelligent categorization
    - Workflow-based processing
    """
    try:
        enhanced_service = EnhancedClassificationService()
        
        # Ensure user ID matches current user
        if request.user_id != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Cannot classify documents for other users")
        
        result = await enhanced_service.classify_document_enhanced(request)
        
        if result.workflow_status == "failed":
            raise HTTPException(status_code=500, detail=f"Enhanced classification failed: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced classification failed: {str(e)}")


@router.post("/classification/batch", response_model=ClassificationBatch)
async def batch_document_classification(
    batch: ClassificationBatch,
    current_user: dict = Depends(get_current_user)
):
    """
    Process a batch of documents for classification.
    
    This endpoint handles multiple documents in a single request,
    providing efficient batch processing with progress tracking.
    """
    try:
        enhanced_service = EnhancedClassificationService()
        
        # Ensure user ID matches current user
        if batch.user_id != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Cannot process batches for other users")
        
        # Process batch asynchronously
        result = await enhanced_service.process_classification_batch(batch)
        
        return result
        
    except Exception as e:
        logger.error(f"Batch classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch classification failed: {str(e)}")


# Auto Schedule Bots Endpoints
@router.post("/bots/auto-schedule", response_model=Dict[str, Any])
async def auto_schedule_user_bots(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Automatically schedule bots for all upcoming meetings for a user.
    
    This endpoint uses AI to intelligently schedule meeting bots based on:
    - Meeting context and type
    - User preferences
    - Historical patterns
    - Optimal bot configurations
    """
    try:
        # Ensure user can only schedule bots for themselves
        if user_id != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Cannot schedule bots for other users")
        
        auto_schedule_service = AutoScheduleBotsService()
        result = await auto_schedule_service.auto_schedule_user_bots(user_id)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=f"Auto-scheduling failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Auto-scheduling failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auto-scheduling failed: {str(e)}")


@router.post("/bots/schedule-meeting", response_model=BotSchedulingResult)
async def schedule_meeting_bot(
    request: BotSchedulingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Schedule a bot for a specific meeting.
    
    This endpoint schedules a single meeting bot with AI-generated
    configuration based on meeting context and requirements.
    """
    try:
        # Ensure user can only schedule bots for themselves
        if request.user_id != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Cannot schedule bots for other users")
        
        auto_schedule_service = AutoScheduleBotsService()
        result = await auto_schedule_service.schedule_meeting_bot(request.meeting_id, request.user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Bot scheduling failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bot scheduling failed: {str(e)}")


# Document Workflow Endpoints
@router.post("/workflows", response_model=bool)
async def create_document_workflow(
    workflow: DocumentWorkflow,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new document processing workflow.
    
    This endpoint allows users to define custom document processing
    pipelines with multiple steps and conditional logic.
    """
    try:
        # Ensure user ID matches current user
        if workflow.user_id != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Cannot create workflows for other users")
        
        workflow_service = DocumentWorkflowService()
        success = await workflow_service.create_workflow(workflow)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create workflow")
        
        return success
        
    except Exception as e:
        logger.error(f"Workflow creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow creation failed: {str(e)}")


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecution)
async def execute_document_workflow(
    workflow_id: str,
    document_id: str,
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a document processing workflow.
    
    This endpoint starts the execution of a defined workflow
    for a specific document, processing it through all configured steps.
    """
    try:
        workflow_service = DocumentWorkflowService()
        execution = await workflow_service.execute_workflow(
            workflow_id=workflow_id,
            document_id=document_id,
            user_id=current_user.get('id'),
            project_id=project_id
        )
        
        return execution
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/workflows/executions", response_model=List[WorkflowExecution])
async def get_workflow_executions(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get workflow executions for the current user.
    
    This endpoint retrieves workflow execution history and current status
    for monitoring and debugging purposes.
    """
    try:
        workflow_service = DocumentWorkflowService()
        executions = await workflow_service.get_workflow_executions(
            user_id=current_user.get('id'),
            status=status,
            project_id=project_id
        )
        
        return executions
        
    except Exception as e:
        logger.error(f"Failed to get workflow executions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow executions: {str(e)}")


@router.post("/workflows/executions/{execution_id}/pause")
async def pause_workflow_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Pause a workflow execution.
    
    This endpoint allows users to pause running workflows
    for manual intervention or review.
    """
    try:
        workflow_service = DocumentWorkflowService()
        success = await workflow_service.pause_workflow(execution_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to pause workflow")
        
        return {"message": "Workflow paused successfully"}
        
    except Exception as e:
        logger.error(f"Failed to pause workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")


@router.post("/workflows/executions/{execution_id}/resume")
async def resume_workflow_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Resume a paused workflow execution.
    
    This endpoint allows users to resume paused workflows
    from where they left off.
    """
    try:
        workflow_service = DocumentWorkflowService()
        success = await workflow_service.resume_workflow(execution_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to resume workflow")
        
        return {"message": "Workflow resumed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to resume workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")


@router.post("/project-onboarding")
async def process_project_onboarding(
    payload: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Process project onboarding using AI.
    
    This endpoint processes project onboarding data and generates
    AI-powered project metadata including categories, tags, and recommendations.
    """
    try:
        onboarding_service = ProjectOnboardingAIService()
        
        # Extract data from payload
        project_id = payload.get('project_id')
        user_id = payload.get('user_id')
        summary = payload.get('summary', {})
        
        if not project_id or not user_id:
            raise HTTPException(status_code=400, detail="Missing required fields: project_id and user_id")
        
        # Process project onboarding
        result = await onboarding_service.process_project_onboarding(
            project_id=project_id,
            user_id=user_id,
            summary=summary
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Project onboarding failed'))
        
        return result
        
    except Exception as e:
        logger.error(f"Project onboarding failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Project onboarding failed: {str(e)}")
