"""
RAG Agent API endpoints
Handles conversational queries about project data using the RAG agent service.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...services.ai.rag_agent_service import RAGAgentService
from ...core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

class RAGQueryRequest(BaseModel):
    """Request model for RAG agent queries."""
    question: str
    project_id: str

class ProjectSummaryRequest(BaseModel):
    """Request model for project summary requests."""
    project_id: str

@router.post("/query")
async def query_project_data(
    request: RAGQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Query project data using the RAG agent."""
    try:
        print(f"=== RAG API ENDPOINT DEBUG ===")
        print(f"Request project_id: {request.project_id}")
        print(f"Current user id: {current_user['id']}")
        print(f"Question: {request.question}")
        print("=" * 50)
        
        rag_service = RAGAgentService()
        
        # Create streaming response
        async def generate_response():
            async for chunk in rag_service.query_project_data(
                user_question=request.question,
                project_id=request.project_id,
                user_id=current_user['id']
            ):
                yield f"data: {chunk}\n\n"
            
            # Send end signal
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process RAG query")

@router.get("/project-summary/{project_id}")
async def get_project_summary(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a summary of project data for the RAG agent."""
    try:
        rag_service = RAGAgentService()
        
        summary = await rag_service.get_project_summary(
            project_id=project_id,
            user_id=current_user['id']
        )
        
        return {
            "project_id": project_id,
            "summary": summary,
            "user_id": current_user['id']
        }
        
    except Exception as e:
        logger.error(f"Error getting project summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project summary")

@router.get("/query")
async def query_project_data_get(
    question: str,
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """GET endpoint for RAG agent queries (fallback for debugging)."""
    try:
        # Convert GET parameters to POST request format
        request = RAGQueryRequest(question=question, project_id=project_id)
        return await query_project_data(request, current_user)
    except Exception as e:
        logger.error(f"Error in RAG GET query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process RAG query")

@router.get("/health")
async def rag_agent_health():
    """Health check for the RAG agent service."""
    try:
        rag_service = RAGAgentService()
        return {
            "status": "healthy",
            "service": "rag_agent",
            "message": "RAG agent service is operational"
        }
    except Exception as e:
        logger.error(f"RAG agent health check failed: {e}")
        raise HTTPException(status_code=500, detail="RAG agent service unhealthy")
