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
from ...core.security import get_current_user_from_supabase_token, security
from ...models.schemas.user import User

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify the backend is accessible."""
    return {"message": "Projects API is working!", "timestamp": datetime.now().isoformat()}


@router.get("/test-user")
async def test_user_endpoint(
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Test endpoint to verify user authentication and show user data."""
    return {
        "message": "User authentication successful!",
        "user_data": current_user,
        "user_id": current_user.get("id"),
        "email": current_user.get("email"),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/test-auth")
async def test_auth(
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Test endpoint to verify authentication is working."""
    return {
        "message": "Authentication successful!",
        "user_id": current_user.get("id"),
        "email": current_user.get("email"),
        "username": current_user.get("username")
    }


@router.get("/test-token")
async def test_token(
    credentials = Depends(security)
):
    """Test endpoint to debug token issues."""
    try:
        token = credentials.credentials
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 Token Debug - Token length: {len(token) if token else 0}")
        logger.info(f"🔍 Token Debug - Token start: {token[:50] if token else 'None'}...")
        logger.info(f"🔍 Token Debug - Token end: ...{token[-50:] if token else 'None'}")
        
        # Try to decode the JWT without verification
        try:
            import jwt
            from jose import jwt as jose_jwt
            # Try both libraries
            try:
                unverified_payload = jwt.decode(token, options={"verify_signature": False})
                logger.info(f"🔍 Token Debug - PyJWT unverified payload: {unverified_payload}")
            except:
                try:
                    unverified_payload = jose_jwt.decode(token, options={"verify_signature": False})
                    logger.info(f"🔍 Token Debug - Python-Jose unverified payload: {unverified_payload}")
                except Exception as e:
                    logger.error(f"🔍 Token Debug - Both JWT libraries failed: {e}")
        except Exception as e:
            logger.error(f"🔍 Token Debug - JWT decode error: {e}")
        
        return {
            "message": "Token received",
            "token_length": len(token) if token else 0,
            "token_start": token[:50] if token else None,
            "token_end": token[-50:] if token else None
        }
        
    except Exception as e:
        logger.error(f"🔍 Token Debug - Exception: {e}", exc_info=True)
        return {"error": str(e)}


@router.post("/", response_model=Project)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Create a new project."""
    try:
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 Project Creation Debug - current_user: {current_user}")
        logger.info(f"🔍 Project Creation Debug - current_user type: {type(current_user)}")
        logger.info(f"🔍 Project Creation Debug - current_user keys: {list(current_user.keys()) if isinstance(current_user, dict) else 'Not a dict'}")
        
        # Validate current_user
        if not current_user or not isinstance(current_user, dict):
            logger.error(f"🔍 Project Creation Debug - Invalid current_user: {current_user}")
            raise HTTPException(status_code=400, detail="Invalid user data")
        
        user_id = current_user.get("id")
        if not user_id:
            logger.error(f"🔍 Project Creation Debug - No user_id in current_user: {current_user}")
            raise HTTPException(status_code=400, detail="User ID not found")
        
        logger.info(f"🔍 Project Creation Debug - User ID: {user_id}")
        
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            logger.error("🔍 Project Creation Debug - Supabase service client not available")
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Add user and creation metadata
        project_data = project.dict()
        project_data['created_by'] = user_id  # Use 'created_by' instead of 'user_id'
        project_data['created_at'] = datetime.now().isoformat()
        project_data['updated_at'] = datetime.now().isoformat()
        
        logger.info(f"🔍 Project Creation Debug - project_data: {project_data}")
        
        # Insert project
        logger.info("🔍 Project Creation Debug - Attempting to insert project into database")
        result = await supabase.table('projects').insert(project_data).execute()
        logger.info(f"🔍 Project Creation Debug - Database result: {result}")
        
        if result.data:
            logger.info(f"🔍 Project Creation Debug - Project created successfully: {result.data[0]}")
            return Project(**result.data[0])
        else:
            logger.error(f"🔍 Project Creation Debug - No data returned from database: {result}")
            raise HTTPException(status_code=500, detail="Failed to create project - no data returned")
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"🔍 Project Creation Debug - Unexpected exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    limit: int = Query(100, description="Number of projects to return"),
    offset: int = Query(0, description="Number of projects to skip"),
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """List projects for the current user."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Get projects - ALWAYS filter by user first for security
        query = supabase.table('projects').select('*').eq('created_by', current_user.get('id'))
        
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Get a specific project by ID."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Get project - ALWAYS filter by user first for security
        result = await supabase.table('projects').select('*').eq('id', project_id).eq('created_by', current_user.get("id")).single().execute()
        
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Update a specific project."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if project exists and belongs to user
        existing_result = await supabase.table('projects').select('id').eq('id', project_id).eq('created_by', current_user.get("id")).single().execute()
        
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Delete a specific project."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if project exists and belongs to user
        existing_result = await supabase.table('projects').select('id').eq('id', project_id).eq('created_by', current_user.get("id")).single().execute()
        
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Get statistics for a specific project."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if project exists and belongs to user
        project_result = await supabase.table('projects').select('id').eq('id', project_id).eq('created_by', current_user.get("id")).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get document count for this project
        docs_result = await supabase.table('documents').select('id', count='exact').eq('project_id', project_id).eq('created_by', current_user.get("id")).execute()
        document_count = docs_result.count or 0
        
        # Get documents by type
        type_result = await supabase.table('documents').select('type').eq('project_id', project_id).eq('created_by', current_user.get("id")).execute()
        type_counts = {}
        for doc in type_result.data or []:
            doc_type = doc.get('type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Get documents by status
        status_result = await supabase.table('documents').select('status').eq('project_id', project_id).eq('created_by', current_user.get("id")).execute()
        status_counts = {}
        for doc in status_result.data or []:
            doc_status = doc.get('status', 'unknown')
            status_counts[doc_status] = status_counts.get(doc_status, 0) + 1
        
        # Get meeting count for this project
        meetings_result = await supabase.table('meetings').select('id', count='exact').eq('project_id', project_id).eq('created_by', current_user.get("id")).execute()
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Get all documents for a specific project."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if project exists and belongs to user
        project_result = await supabase.table('projects').select('id').eq('id', project_id).eq('created_by', current_user.get("id")).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get documents for project - ALWAYS filter by user first for security
        query = supabase.table('documents').select('*').eq('created_by', current_user.get("id")).eq('project_id', project_id)
        
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Get all meetings for a specific project."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if project exists and belongs to user
        project_result = await supabase.table('projects').select('id').eq('id', project_id).eq('created_by', current_user.get("id")).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get meetings for project - ALWAYS filter by user first for security
        query = supabase.table('meetings').select('*').eq('created_by', current_user.get("id")).eq('project_id', project_id)
        
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
    current_user: dict = Depends(get_current_user_from_supabase_token)
):
    """Get overview statistics for all user projects."""
    try:
        # Use service role client to bypass RLS policies
        from ...core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Get total project count
        projects_result = await supabase.table('projects').select('id', count='exact').eq('created_by', current_user.get("id")).execute()
        total_projects = projects_result.count or 0
        
        # Get total document count
        docs_result = await supabase.table('documents').select('id', count='exact').eq('created_by', current_user.get("id")).execute()
        total_documents = docs_result.count or 0
        
        # Get total meeting count
        meetings_result = await supabase.table('meetings').select('id', count='exact').eq('created_by', current_user.get("id")).execute()
        total_meetings = meetings_result.count or 0
        
        # Get unclassified document count
        unclassified_result = await supabase.table('documents').select('id', count='exact').eq('created_by', current_user.get("id")).is_('project_id', None).execute()
        unclassified_documents = unclassified_result.count or 0
        
        return {
            "total_projects": total_projects,
            "total_documents": total_documents,
            "total_meetings": total_meetings,
            "unclassified_documents": unclassified_documents
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects overview: {str(e)}")
