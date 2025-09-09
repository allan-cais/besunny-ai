"""
Documents API endpoints
Handles document management, manual project assignment, and vector embedding.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from ...services.ai.vector_embedding_service import VectorEmbeddingService
from ...core.supabase_config import get_supabase_service_client
from ...core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

class ProjectAssignmentRequest(BaseModel):
    """Request model for manually assigning a document to a project."""
    document_id: str
    project_id: str

class DocumentSearchRequest(BaseModel):
    """Request model for searching documents using vector similarity."""
    query: str
    project_id: Optional[str] = None
    limit: int = 10

class DocumentResponse(BaseModel):
    """Response model for document data."""
    id: str
    title: str
    content: str
    source: str
    project_id: Optional[str]
    author: Optional[str]
    created_at: str
    updated_at: str

@router.get("/unclassified", response_model=List[DocumentResponse])
async def get_unclassified_documents(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get unclassified documents for the current user."""
    try:
        supabase = get_supabase_service_client()
        
        # Get documents without project_id for the current user
        result = supabase.table('documents').select('*').eq('user_id', current_user['id']).is_('project_id', 'null').order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        if not result.data:
            return []
        
        documents = []
        for doc in result.data:
            documents.append(DocumentResponse(
                id=doc['id'],
                title=doc.get('title', doc.get('subject', 'Untitled')),
                content=doc.get('content', ''),
                source=doc.get('source', 'unknown'),
                project_id=doc.get('project_id'),
                author=doc.get('author'),
                created_at=doc['created_at'],
                updated_at=doc['updated_at']
            ))
        
        return documents
        
    except Exception as e:
        logger.error(f"Error fetching unclassified documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unclassified documents")

@router.post("/assign-project")
async def assign_document_to_project(
    request: ProjectAssignmentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually assign a document to a project and trigger vector embedding."""
    try:
        supabase = get_supabase_service_client()
        
        # Verify document exists and belongs to user
        doc_result = supabase.table('documents').select('*').eq('id', request.document_id).eq('user_id', current_user['id']).execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_result.data[0]
        
        # Verify project exists and belongs to user
        project_result = supabase.table('projects').select('*').eq('id', request.project_id).eq('user_id', current_user['id']).execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update document with project_id
        update_result = supabase.table('documents').update({
            'project_id': request.project_id,
            'updated_at': 'now()'
        }).eq('id', request.document_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update document")
        
        # Trigger vector embedding in background
        background_tasks.add_task(
            _embed_manually_assigned_document,
            document,
            request.project_id,
            current_user['id']
        )
        
        logger.info(f"Document {request.document_id} assigned to project {request.project_id} for user {current_user['id']}")
        
        return {
            "success": True,
            "message": "Document assigned to project successfully",
            "document_id": request.document_id,
            "project_id": request.project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning document to project: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign document to project")

@router.post("/search")
async def search_documents(
    request: DocumentSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search documents using vector similarity."""
    try:
        vector_service = VectorEmbeddingService()
        
        # Perform vector search
        search_results = await vector_service.search_similar_content(
            query=request.query,
            user_id=current_user['id'],
            project_id=request.project_id,
            limit=request.limit
        )
        
        # Format results
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                'id': result['id'],
                'score': result['score'],
                'content_type': result['content_type'],
                'source_id': result['source_id'],
                'project_id': result['project_id'],
                'author': result['author'],
                'date': result['date'],
                'subject': result['subject'],
                'chunk_text': result['chunk_text'],
                'chunk_index': result['chunk_index'],
                'total_chunks': result['total_chunks'],
                'metadata': result['metadata']
            })
        
        return {
            "query": request.query,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to search documents")

@router.get("/stats")
async def get_document_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get document statistics for the current user."""
    try:
        supabase = get_supabase_service_client()
        vector_service = VectorEmbeddingService()
        
        # Get document counts by source
        doc_stats = supabase.table('documents').select('source').eq('user_id', current_user['id']).execute()
        
        source_counts = {}
        total_documents = 0
        classified_documents = 0
        unclassified_documents = 0
        
        for doc in doc_stats.data:
            source = doc.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
            total_documents += 1
        
        # Get classified vs unclassified counts
        classified_result = supabase.table('documents').select('id').eq('user_id', current_user['id']).not_.is_('project_id', 'null').execute()
        classified_documents = len(classified_result.data) if classified_result.data else 0
        unclassified_documents = total_documents - classified_documents
        
        # Get vector embedding stats
        embedding_stats = await vector_service.get_embedding_stats(current_user['id'])
        
        return {
            "total_documents": total_documents,
            "classified_documents": classified_documents,
            "unclassified_documents": unclassified_documents,
            "source_breakdown": source_counts,
            "vector_embeddings": embedding_stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching document stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch document statistics")

async def _embed_manually_assigned_document(
    document: Dict[str, Any],
    project_id: str,
    user_id: str
):
    """Background task to embed manually assigned document."""
    try:
        vector_service = VectorEmbeddingService()
        
        # Prepare content for embedding
        content = {
            'type': document.get('source', 'unknown'),
            'source_id': document['id'],
            'author': document.get('author', ''),
            'date': document.get('created_at', ''),
            'subject': document.get('subject', ''),
            'content_text': document.get('content', ''),
            'metadata': {
                'document_id': document['id'],
                'user_id': user_id,
                'manually_assigned': True
            }
        }
        
        # Embed the content
        embedding_result = await vector_service.embed_manually_assigned_content(
            content=content,
            project_id=project_id,
            user_id=user_id
        )
        
        logger.info(f"Manual assignment embedding completed: {embedding_result}")
        
    except Exception as e:
        logger.error(f"Error in background embedding for manual assignment: {e}")

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a document and its associated vectors."""
    try:
        supabase = get_supabase_service_client()
        
        # Verify document exists and belongs to user
        doc_result = supabase.table('documents').select('*').eq('id', document_id).eq('user_id', current_user['id']).execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_result.data[0]
        
        # Delete vectors from Pinecone first
        try:
            vector_service = VectorEmbeddingService()
            await vector_service.delete_document_vectors(document_id, current_user['id'])
            logger.info(f"Deleted vectors for document {document_id}")
        except Exception as e:
            logger.warning(f"Failed to delete vectors for document {document_id}: {e}")
            # Continue with document deletion even if vector deletion fails
        
        # Delete document from database
        delete_result = supabase.table('documents').delete().eq('id', document_id).eq('user_id', current_user['id']).execute()
        
        if not delete_result.data:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
        logger.info(f"Document {document_id} deleted successfully for user {current_user['id']}")
        
        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")
