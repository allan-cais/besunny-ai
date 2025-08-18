"""
Documents API endpoints for BeSunny.ai Python backend.
Provides REST API for document management operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from ...core.supabase_config import get_supabase_client
from ...models.schemas.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentListResponse,
    DocumentStatus
)
from ...core.security import get_current_user
from ...models.schemas.user import User

router = APIRouter()


@router.post("/", response_model=Document)
async def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new document."""
    try:
        supabase = get_supabase_client()
        
        # Add user and creation metadata
        doc_data = document.dict()
        doc_data['created_by'] = current_user.id
        doc_data['created_at'] = datetime.now().isoformat()
        doc_data['updated_at'] = datetime.now().isoformat()
        
        # Insert document
        result = await supabase.table('documents').insert(doc_data).execute()
        
        if result.data:
            return Document(**result.data[0])
        else:
            raise HTTPException(status_code=500, detail="Failed to create document")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    current_user: User = Depends(get_current_user)
):
    """List documents for the current user."""
    try:
        supabase = get_supabase_client()
        
        # Start with base query - ALWAYS filter by user first for security
        query = supabase.table('documents').select('*').eq('created_by', current_user.id)
        
        # Apply additional filters
        if project_id:
            query = query.eq('project_id', project_id)
        
        if document_type:
            query = query.eq('type', document_type)
        
        if status:
            query = query.eq('status', status)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
        
        result = await query.execute()
        
        return DocumentListResponse(
            documents=result.data or [],
            total_count=len(result.data or []),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID."""
    try:
        supabase = get_supabase_client()
        
        # Get document - ALWAYS filter by user first for security
        result = await supabase.table('documents').select('*').eq('id', document_id).eq('created_by', current_user.id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return Document(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a specific document."""
    try:
        supabase = get_supabase()
        
        # Check if document exists and belongs to user
        existing_result = await supabase.table('documents').select('id').eq('id', document_id).eq('created_by', current_user.id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update document
        update_data = document_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.now().isoformat()
        
        result = await supabase.table('documents').update(update_data).eq('id', document_id).execute()
        
        if result.data:
            return Document(**result.data[0])
        else:
            raise HTTPException(status_code=500, detail="Failed to update document")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific document."""
    try:
        supabase = get_supabase()
        
        # Check if document exists and belongs to user
        existing_result = await supabase.table('documents').select('id').eq('id', document_id).eq('created_by', current_user.id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete document
        await supabase.table('documents').delete().eq('id', document_id).execute()
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/project/{project_id}", response_model=DocumentListResponse)
async def get_project_documents(
    project_id: str,
    limit: int = Query(100, description="Number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    current_user: User = Depends(get_current_user)
):
    """Get all documents for a specific project."""
    try:
        supabase = get_supabase()
        
        # Get documents for project - ALWAYS filter by user first for security
        query = supabase.table('documents').select('*').eq('created_by', current_user.id).eq('project_id', project_id)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
        
        result = await query.execute()
        
        return DocumentListResponse(
            documents=result.data or [],
            total_count=len(result.data or []),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project documents: {str(e)}")


@router.get("/unclassified", response_model=DocumentListResponse)
async def get_unclassified_documents(
    limit: int = Query(100, description="Number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    current_user: User = Depends(get_current_user)
):
    """Get unclassified documents (no project assigned)."""
    try:
        supabase = get_supabase()
        
        # Get unclassified documents - ALWAYS filter by user first for security
        query = supabase.table('documents').select('*').eq('created_by', current_user.id).is_('project_id', None)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
        
        result = await query.execute()
        
        return DocumentListResponse(
            documents=result.data or [],
            total_count=len(result.data or []),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unclassified documents: {str(e)}")


@router.post("/{document_id}/assign-project")
async def assign_document_to_project(
    document_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Assign a document to a project."""
    try:
        supabase = get_supabase()
        
        # Check if document exists and belongs to user
        existing_result = await supabase.table('documents').select('id').eq('id', document_id).eq('created_by', current_user.id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if project exists and belongs to user
        project_result = await supabase.table('projects').select('id').eq('id', project_id).eq('user_id', current_user.id).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update document with project assignment
        result = await supabase.table('documents').update({
            'project_id': project_id,
            'updated_at': datetime.now().isoformat()
        }).eq('id', document_id).execute()
        
        if result.data:
            return {"message": "Document assigned to project successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to assign document to project")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign document to project: {str(e)}")


@router.post("/{document_id}/remove-project")
async def remove_document_from_project(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a document from its assigned project."""
    try:
        supabase = get_supabase()
        
        # Check if document exists and belongs to user
        existing_result = await supabase.table('documents').select('id').eq('id', document_id).eq('created_by', current_user.id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove project assignment
        result = await supabase.table('documents').update({
            'project_id': None,
            'updated_at': datetime.now().isoformat()
        }).eq('id', document_id).execute()
        
        if result.data:
            return {"message": "Document removed from project successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to remove document from project")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove document from project: {str(e)}")


@router.get("/stats/summary")
async def get_document_stats(
    current_user: User = Depends(get_current_user)
):
    """Get document statistics for the current user."""
    try:
        supabase = get_supabase()
        
        # Get total document count
        total_result = await supabase.table('documents').select('id', count='exact').eq('created_by', current_user.id).execute()
        total_count = total_result.count or 0
        
        # Get documents by type
        type_result = await supabase.table('documents').select('type').eq('created_by', current_user.id).execute()
        type_counts = {}
        for doc in type_result.data or []:
            doc_type = doc.get('type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Get documents by status
        status_result = await supabase.table('documents').select('status').eq('created_by', current_user.id).execute()
        status_counts = {}
        for doc in status_result.data or []:
            doc_status = doc.get('status', 'unknown')
            status_counts[doc_status] = status_counts.get(doc_status, 0) + 1
        
        # Get unclassified count
        unclassified_result = await supabase.table('documents').select('id', count='exact').eq('created_by', current_user.id).is_('project_id', None).execute()
        unclassified_count = unclassified_result.count or 0
        
        return {
            "total_documents": total_count,
            "by_type": type_counts,
            "by_status": status_counts,
            "unclassified": unclassified_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document stats: {str(e)}")
