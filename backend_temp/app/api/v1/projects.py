"""
Projects API endpoints for BeSunny.ai Python backend.
Provides REST API for project management operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from ...core.database import get_supabase
from ...models.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectListResponse,
    ProjectStats
)
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


@router.post("/", response_model=Project)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new project."""
    try:
        supabase = get_supabase()
        
        # Add user and creation metadata
        project_data = project.dict()
        project_data['user_id'] = current_user.id
        project_data['created_at'] = datetime.now().isoformat()
        project_data['updated_at'] = datetime.now().isoformat()
        
        # Insert project
        result = await supabase.table('projects').insert(project_data).execute()
        
        if result.data:
            return Project(**result.data[0])
        else:
            raise HTTPException(status_code=500, detail="Failed to create project")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    limit: int = Query(100, description="Number of projects to return"),
    offset: int = Query(0, description="Number of projects to skip"),
    current_user: User = Depends(get_current_user)
):
    """List projects for the current user."""
    try:
        supabase = get_supabase()
        
        # Get projects - ALWAYS filter by user first for security
        query = supabase.table('projects').select('*').eq('user_id', current_user.id)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
        
        result = await query.execute()
        
        return ProjectListResponse(
            projects=result.data or [],
            total_count=len(result.data or []),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific project by ID."""
    try:
        supabase = get_supabase()
        
        # Get project - ALWAYS filter by user first for security
        result = await supabase.table('projects').select('*').eq('id', project_id).eq('user_id', current_user.id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return Project(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a specific project."""
    try:
        supabase = get_supabase()
        
        # Check if project exists and belongs to user
        existing_result = await supabase.table('projects').select('id').eq('id', project_id).eq('user_id', current_user.id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update project
        update_data = project_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.now().isoformat()
        
        result = await supabase.table('projects').update(update_data).eq('id', project_id).execute()
        
        if result.data:
            return Project(**result.data[0])
        else:
            raise HTTPException(status_code=500, detail="Failed to update project")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific project."""
    try:
        supabase = get_supabase()
        
        # Check if project exists and belongs to user
        existing_result = await supabase.table('projects').select('id').eq('id', project_id).eq('user_id', current_user.id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete project
        await supabase.table('projects').delete().eq('id', project_id).execute()
        
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific project."""
    try:
        supabase = get_supabase()
        
        # Check if project exists and belongs to user
        project_result = await supabase.table('projects').select('id').eq('id', project_id).eq('user_id', current_user.id).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get document count for this project
        docs_result = await supabase.table('documents').select('id', count='exact').eq('project_id', project_id).eq('created_by', current_user.id).execute()
        document_count = docs_result.count or 0
        
        # Get documents by type
        type_result = await supabase.table('documents').select('type').eq('project_id', project_id).eq('created_by', current_user.id).execute()
        type_counts = {}
        for doc in type_result.data or []:
            doc_type = doc.get('type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Get documents by status
        status_result = await supabase.table('documents').select('status').eq('project_id', project_id).eq('created_by', current_user.id).execute()
        status_counts = {}
        for doc in status_result.data or []:
            doc_status = doc.get('status', 'unknown')
            status_counts[doc_status] = status_counts.get(doc_status, 0) + 1
        
        # Get meeting count for this project
        meetings_result = await supabase.table('meetings').select('id', count='exact').eq('project_id', project_id).eq('user_id', current_user.id).execute()
        meeting_count = meetings_result.count or 0
        
        return ProjectStats(
            project_id=project_id,
            document_count=document_count,
            meeting_count=meeting_count,
            documents_by_type=type_counts,
            documents_by_status=status_counts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project stats: {str(e)}")


@router.get("/{project_id}/documents", response_model=List[dict])
async def get_project_documents(
    project_id: str,
    limit: int = Query(100, description="Number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    current_user: User = Depends(get_current_user)
):
    """Get all documents for a specific project."""
    try:
        supabase = get_supabase()
        
        # Check if project exists and belongs to user
        project_result = await supabase.table('projects').select('id').eq('id', project_id).eq('user_id', current_user.id).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get documents for project - ALWAYS filter by user first for security
        query = supabase.table('documents').select('*').eq('created_by', current_user.id).eq('project_id', project_id)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
        
        result = await query.execute()
        return result.data or []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project documents: {str(e)}")


@router.get("/{project_id}/meetings", response_model=List[dict])
async def get_project_meetings(
    project_id: str,
    limit: int = Query(100, description="Number of meetings to return"),
    offset: int = Query(0, description="Number of meetings to skip"),
    current_user: User = Depends(get_current_user)
):
    """Get all meetings for a specific project."""
    try:
        supabase = get_supabase()
        
        # Check if project exists and belongs to user
        project_result = await supabase.table('projects').select('id').eq('id', project_id).eq('user_id', current_user.id).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get meetings for project - ALWAYS filter by user first for security
        query = supabase.table('meetings').select('*').eq('user_id', current_user.id).eq('project_id', project_id)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1).order('start_time', desc=True)
        
        result = await query.execute()
        return result.data or []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project meetings: {str(e)}")


@router.get("/stats/overview")
async def get_projects_overview(
    current_user: User = Depends(get_current_user)
):
    """Get overview statistics for all user projects."""
    try:
        supabase = get_supabase()
        
        # Get total project count
        projects_result = await supabase.table('projects').select('id', count='exact').eq('user_id', current_user.id).execute()
        total_projects = projects_result.count or 0
        
        # Get total document count
        docs_result = await supabase.table('documents').select('id', count='exact').eq('created_by', current_user.id).execute()
        total_documents = docs_result.count or 0
        
        # Get total meeting count
        meetings_result = await supabase.table('meetings').select('id', count='exact').eq('user_id', current_user.id).execute()
        total_meetings = meetings_result.count or 0
        
        # Get unclassified document count
        unclassified_result = await supabase.table('documents').select('id', count='exact').eq('created_by', current_user.id).is_('project_id', None).execute()
        unclassified_documents = unclassified_result.count or 0
        
        return {
            "total_projects": total_projects,
            "total_documents": total_documents,
            "total_meetings": total_meetings,
            "unclassified_documents": unclassified_documents
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects overview: {str(e)}")
