"""
AI Orchestration API endpoints for BeSunny.ai Python backend.
Provides workflow execution, status checking, and service health monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import uuid
import logging

from ...services.ai.ai_orchestration_service import (
    AIOrchestrationService, 
    AIWorkflowRequest, 
    AIWorkflowResult
)
from ...core.security import get_current_user
from ...models.schemas.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-orchestration", tags=["AI Orchestration"])

# Initialize the AI orchestration service
ai_orchestration_service = AIOrchestrationService()


@router.post("/workflows", response_model=Dict[str, Any])
async def create_workflow(
    workflow_type: str,
    input_data: Dict[str, Any],
    expected_outputs: List[str],
    project_id: Optional[str] = None,
    priority: str = "normal",
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Create and execute an AI workflow.
    
    Args:
        workflow_type: Type of workflow (classification, meeting_intelligence, hybrid)
        input_data: Input data for the workflow
        expected_outputs: List of expected output types
        project_id: Optional project ID
        priority: Workflow priority (low, normal, high, urgent)
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        
    Returns:
        Workflow execution result
    """
    try:
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Create workflow request
        request = AIWorkflowRequest(
            workflow_id=workflow_id,
            user_id=current_user.id,
            workflow_type=workflow_type,
            input_data=input_data,
            expected_outputs=expected_outputs,
            project_id=project_id,
            priority=priority
        )
        
        # Execute workflow
        result = await ai_orchestration_service.execute_workflow(request)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "status": result.status,
            "result": result.outputs,
            "processing_time_ms": result.processing_time_ms,
            "services_used": result.services_used,
            "errors": result.errors
        }
        
    except Exception as e:
        logger.error(f"Workflow creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow creation failed: {str(e)}")


@router.get("/workflows/{workflow_id}/status", response_model=Dict[str, Any])
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a workflow.
    
    Args:
        workflow_id: Workflow ID to check
        current_user: Current authenticated user
        
    Returns:
        Workflow status information
    """
    try:
        status = await ai_orchestration_service.get_workflow_status(workflow_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


@router.get("/services/health", response_model=Dict[str, Any])
async def get_service_health(
    current_user: User = Depends(get_current_user)
):
    """
    Get health status of all AI services.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Service health information
    """
    try:
        health_status = await ai_orchestration_service.get_service_health()
        
        return {
            "success": True,
            "services": {
                service_name: {
                    "status": status.status,
                    "response_time_ms": status.response_time_ms,
                    "last_check": status.last_check.isoformat(),
                    "capacity_available": status.capacity_available
                }
                for service_name, status in health_status.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get service health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service health: {str(e)}")


@router.post("/workflows/optimize", response_model=Dict[str, Any])
async def optimize_workflow(
    workflow_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get optimization recommendations for a workflow type.
    
    Args:
        workflow_type: Type of workflow to optimize
        current_user: Current authenticated user
        
    Returns:
        Optimization recommendations
    """
    try:
        optimization = await ai_orchestration_service.optimize_workflow(
            workflow_type=workflow_type,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "optimization": optimization
        }
        
    except Exception as e:
        logger.error(f"Workflow optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow optimization failed: {str(e)}")


@router.post("/workflows/batch", response_model=Dict[str, Any])
async def execute_batch_workflows(
    workflows: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
):
    """
    Execute multiple workflows in batch.
    
    Args:
        workflows: List of workflow definitions
        current_user: Current authenticated user
        
    Returns:
        Batch execution results
    """
    try:
        results = []
        
        for workflow_def in workflows:
            workflow_id = str(uuid.uuid4())
            
            request = AIWorkflowRequest(
                workflow_id=workflow_id,
                user_id=current_user.id,
                workflow_type=workflow_def.get('workflow_type', 'classification'),
                input_data=workflow_def.get('input_data', {}),
                expected_outputs=workflow_def.get('expected_outputs', []),
                project_id=workflow_def.get('project_id'),
                priority=workflow_def.get('priority', 'normal')
            )
            
            result = await ai_orchestration_service.execute_workflow(request)
            results.append({
                "workflow_id": workflow_id,
                "status": result.status,
                "processing_time_ms": result.processing_time_ms,
                "errors": result.errors
            })
        
        return {
            "success": True,
            "batch_id": str(uuid.uuid4()),
            "total_workflows": len(workflows),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch workflow execution failed: {str(e)}")


@router.get("/workflows/types", response_model=Dict[str, Any])
async def get_workflow_types(
    current_user: User = Depends(get_current_user)
):
    """
    Get available workflow types and their descriptions.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Available workflow types
    """
    try:
        workflow_types = {
            "classification": {
                "description": "Document classification and analysis",
                "inputs": ["content", "document_type", "workflow", "priority"],
                "outputs": ["classification", "embeddings", "summary", "keywords", "entities"],
                "estimated_time": "2-5 seconds"
            },
            "meeting_intelligence": {
                "description": "Meeting transcript analysis and insights",
                "inputs": ["meeting_data", "transcript", "participants"],
                "outputs": ["meeting_intelligence", "insights", "recommendations"],
                "estimated_time": "5-10 seconds"
            },
            "hybrid": {
                "description": "Combined workflow using multiple AI services",
                "inputs": ["content", "workflow_type", "expected_outputs"],
                "outputs": ["multiple_service_outputs"],
                "estimated_time": "5-15 seconds"
            }
        }
        
        return {
            "success": True,
            "workflow_types": workflow_types
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow types: {str(e)}")


@router.delete("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def cancel_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running workflow.
    
    Args:
        workflow_id: Workflow ID to cancel
        current_user: Current authenticated user
        
    Returns:
        Cancellation result
    """
    try:
        # For now, just return success
        # In a full implementation, this would actually cancel the workflow
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow cancellation requested",
            "note": "Full cancellation implementation pending"
        }
        
    except Exception as e:
        logger.error(f"Workflow cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow cancellation failed: {str(e)}")
