"""
Embeddings API endpoints for BeSunny.ai Python backend.
Provides access to vector embedding services including generation, storage, and similarity search.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging

from ...services.ai.embedding_service import (
    EmbeddingService,
    EmbeddingResult,
    VectorSearchResult,
    DocumentChunk
)
from ...core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=EmbeddingResult)
async def generate_embeddings(
    texts: List[str],
    metadata: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate vector embeddings for text content.
    
    This endpoint creates vector embeddings using sentence-transformers
    for semantic search and similarity matching.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Generate embeddings
        result = await embedding_service.generate_embeddings(
            texts=texts,
            metadata=metadata
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/store")
async def store_document_chunks(
    chunks: List[DocumentChunk],
    current_user: dict = Depends(get_current_user)
):
    """
    Store document chunks with embeddings in the vector database.
    
    This endpoint stores document chunks along with their vector embeddings
    for future similarity search and retrieval.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Store chunks
        success = await embedding_service.store_document_chunks(chunks)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store document chunks")
        
        return {
            "message": f"Successfully stored {len(chunks)} document chunks",
            "chunks_stored": len(chunks),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Document chunk storage failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")


@router.get("/search")
async def search_similar_documents(
    query: str,
    project_id: Optional[str] = None,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
    current_user: dict = Depends(get_current_user)
):
    """
    Search for similar documents using vector similarity.
    
    This endpoint performs semantic search using vector embeddings
    to find documents with similar content to the query.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Search for similar documents
        result = await embedding_service.search_similar_documents(
            query=query,
            project_id=project_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Search failed: {result.error_message}")
        
        return {
            "query": query,
            "results": result.results,
            "total_results": result.total_results,
            "project_id": project_id,
            "similarity_threshold": similarity_threshold,
            "search_time_ms": result.search_time_ms
        }
        
    except Exception as e:
        logger.error(f"Similar document search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/similar-chunks")
async def find_similar_chunks(
    chunk_embedding: List[float],
    document_id: str,
    top_k: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """
    Find similar chunks within the same document.
    
    This endpoint identifies chunks with similar content within
    a specific document using vector similarity.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Find similar chunks
        result = await embedding_service.find_similar_chunks(
            chunk_embedding=chunk_embedding,
            document_id=document_id,
            top_k=top_k
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Similar chunk search failed: {result.error_message}")
        
        return {
            "document_id": document_id,
            "results": result.results,
            "total_results": result.total_results,
            "search_time_ms": result.search_time_ms
        }
        
    except Exception as e:
        logger.error(f"Similar chunk search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document_vectors(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete all vectors for a specific document.
    
    This endpoint removes all vector embeddings associated with
    a document when it's deleted or updated.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Delete vectors
        success = await embedding_service.delete_document_vectors(document_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete document vectors")
        
        return {
            "message": f"Successfully deleted vectors for document {document_id}",
            "document_id": document_id,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Vector deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/stats")
async def get_index_statistics(current_user: dict = Depends(get_current_user)):
    """
    Get statistics about the vector index.
    
    This endpoint provides information about the vector database
    including total vectors, dimensions, and index health.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Get index stats
        stats = await embedding_service.get_index_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=f"Failed to get index stats: {stats['error']}")
        
        return {
            "index_statistics": stats,
            "service_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Index statistics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Statistics failed: {str(e)}")


@router.post("/chunk-document")
async def chunk_document_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 25,
    current_user: dict = Depends(get_current_user)
):
    """
    Split document text into overlapping chunks.
    
    This endpoint processes long documents by splitting them into
    manageable chunks for vector embedding and storage.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Chunk document
        chunks = await embedding_service.chunk_document(
            text=text,
            chunk_size=chunk_size,
            overlap=overlap
        )
        
        return {
            "original_text_length": len(text),
            "chunks_created": len(chunks),
            "chunk_size": chunk_size,
            "overlap": overlap,
            "chunks": chunks
        }
        
    except Exception as e:
        logger.error(f"Document chunking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chunking failed: {str(e)}")


@router.post("/chunk-analyze")
async def analyze_chunking_quality(
    text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze the quality of chunking for a given text.
    
    This endpoint provides detailed analytics about how text would be chunked,
    including quality scores, overlap analysis, and optimization suggestions.
    """
    try:
        from ...services.ai.vector_embedding_service import VectorEmbeddingService
        
        vector_service = VectorEmbeddingService()
        
        # Create content dict for analysis
        content = {
            'full_content': text,
            'type': 'document'
        }
        
        # Get optimized chunks with full metadata
        chunks = vector_service._create_content_chunks(content)
        
        # Analyze chunk quality
        total_chunks = len(chunks)
        avg_quality = sum(chunk.get('quality_score', 0) for chunk in chunks) / total_chunks if total_chunks > 0 else 0
        avg_length = sum(len(chunk['text']) for chunk in chunks) / total_chunks if total_chunks > 0 else 0
        avg_tokens = sum(chunk.get('token_count', 0) for chunk in chunks) / total_chunks if total_chunks > 0 else 0
        
        # Calculate overlap percentage
        total_text_length = len(text)
        chunked_text_length = sum(len(chunk['text']) for chunk in chunks)
        overlap_percentage = ((chunked_text_length - total_text_length) / total_text_length * 100) if total_text_length > 0 else 0
        
        # Quality distribution
        quality_distribution = {
            'high_quality': len([c for c in chunks if c.get('quality_score', 0) > 0.7]),
            'medium_quality': len([c for c in chunks if 0.4 <= c.get('quality_score', 0) <= 0.7]),
            'low_quality': len([c for c in chunks if c.get('quality_score', 0) < 0.4])
        }
        
        return {
            "original_text_length": total_text_length,
            "chunks_created": total_chunks,
            "average_quality_score": round(avg_quality, 3),
            "average_chunk_length": round(avg_length, 1),
            "average_tokens_per_chunk": round(avg_tokens, 1),
            "overlap_percentage": round(overlap_percentage, 2),
            "quality_distribution": quality_distribution,
            "chunks": [
                {
                    "chunk_id": chunk.get('chunk_id', f'chunk_{i}'),
                    "text_preview": chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                    "length": len(chunk['text']),
                    "token_count": chunk.get('token_count', 0),
                    "quality_score": round(chunk.get('quality_score', 0), 3),
                    "chunk_type": chunk.get('chunk_type', 'unknown')
                }
                for i, chunk in enumerate(chunks)
            ]
        }
        
    except Exception as e:
        logger.error(f"Chunk analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/batch-process")
async def batch_process_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = 512,
    overlap: int = 25,
    current_user: dict = Depends(get_current_user)
):
    """
    Process multiple documents in batch for vector storage.
    
    This endpoint handles batch processing of documents including
    chunking, embedding generation, and storage.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        processed_documents = []
        total_chunks = 0
        
        for doc in documents:
            try:
                # Chunk document
                chunks = await embedding_service.chunk_document(
                    text=doc.get("content", ""),
                    chunk_size=chunk_size,
                    overlap=overlap
                )
                
                # Generate embeddings for chunks
                embeddings_result = await embedding_service.generate_embeddings(chunks)
                
                if embeddings_result.success:
                    # Create document chunks
                    document_chunks = []
                    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings_result.embeddings)):
                        chunk = DocumentChunk(
                            id=f"{doc.get('id', 'unknown')}_{i}",
                            document_id=doc.get("id", "unknown"),
                            chunk_index=i,
                            text=chunk_text,
                            embedding=embedding,
                            metadata={
                                "chunk_size": len(chunk_text),
                                "chunk_index": i,
                                "project_id": doc.get("project_id"),
                                "document_title": doc.get("title", "Unknown")
                            },
                            project_id=doc.get("project_id")
                        )
                        document_chunks.append(chunk)
                    
                    # Store chunks
                    if document_chunks:
                        await embedding_service.store_document_chunks(document_chunks)
                        total_chunks += len(document_chunks)
                    
                    processed_documents.append({
                        "document_id": doc.get("id"),
                        "status": "success",
                        "chunks_created": len(chunks),
                        "embeddings_generated": len(embeddings_result.embeddings)
                    })
                    
                else:
                    processed_documents.append({
                        "document_id": doc.get("id"),
                        "status": "failed",
                        "error": embeddings_result.error_message
                    })
                    
            except Exception as e:
                processed_documents.append({
                    "document_id": doc.get("id"),
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "total_documents": len(documents),
            "successful_processing": len([d for d in processed_documents if d["status"] == "success"]),
            "failed_processing": len([d for d in processed_documents if d["status"] == "failed"]),
            "total_chunks_created": total_chunks,
            "results": processed_documents
        }
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get("/health")
async def embedding_service_health_check():
    """
    Health check for embedding service.
    
    This endpoint verifies that the embedding services are functioning properly
    and can process vector operations.
    """
    try:
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        # Test basic functionality
        test_result = await embedding_service.generate_embeddings("Test text")
        
        if test_result.success:
            return {
                "status": "healthy",
                "service": "embeddings",
                "model": embedding_service.model_name,
                "vector_dimensions": test_result.vector_dimensions,
                "pinecone_index": "operational"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "embeddings",
                    "error": test_result.error_message
                }
            )
        
    except Exception as e:
        logger.error(f"Embedding service health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "embeddings",
                "error": str(e)
            }
        )


@router.get("/models")
async def get_available_embedding_models(current_user: dict = Depends(get_current_user)):
    """
    Get available embedding models and their capabilities.
    
    This endpoint provides information about available embedding models
    and their supported features.
    """
    try:
        # Define available embedding models
        available_models = {
            "all-MiniLM-L6-v2": {
                "name": "all-MiniLM-L6-v2",
                "dimensions": 384,
                "language": "multilingual",
                "performance": "fast",
                "quality": "good",
                "recommended_for": "general_purpose"
            },
            "all-mpnet-base-v2": {
                "name": "all-mpnet-base-v2",
                "dimensions": 768,
                "language": "multilingual",
                "performance": "medium",
                "quality": "excellent",
                "recommended_for": "high_quality"
            },
            "paraphrase-multilingual-MiniLM-L12-v2": {
                "name": "paraphrase-multilingual-MiniLM-L12-v2",
                "dimensions": 384,
                "language": "multilingual",
                "performance": "fast",
                "quality": "good",
                "recommended_for": "multilingual"
            }
        }
        
        return {
            "available_models": available_models,
            "current_model": "all-MiniLM-L6-v2",
            "model_selection": "Automatic based on use case and performance requirements"
        }
        
    except Exception as e:
        logger.error(f"Model information retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model information failed: {str(e)}")
