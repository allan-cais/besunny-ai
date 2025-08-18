"""
Classification service for BeSunny.ai Python backend.
Provides document classification capabilities using AI and vector embeddings.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid
from pydantic import BaseModel

from .ai_service import AIService, AIProcessingResult
from .embedding_service import EmbeddingService, DocumentChunk
from ...models.schemas.document import DocumentType, ClassificationSource, Document, DocumentCreate
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class ClassificationRequest(BaseModel):
    """Request for document classification."""
    document_id: str
    content: str
    project_id: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    force_reclassification: bool = False


class ClassificationResult(BaseModel):
    """Result of document classification."""
    document_id: str
    document_type: DocumentType
    confidence_score: float
    categories: List[str]
    keywords: List[str]
    summary: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None
    processing_time_ms: int
    model_used: str
    classification_source: ClassificationSource = ClassificationSource.AI
    metadata: Optional[Dict[str, Any]] = None


class BatchClassificationRequest(BaseModel):
    """Request for batch document classification."""
    documents: List[ClassificationRequest]
    project_id: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None


class BatchClassificationResult(BaseModel):
    """Result of batch document classification."""
    total_documents: int
    successful_classifications: int
    failed_classifications: int
    results: List[ClassificationResult]
    processing_time_ms: int
    errors: List[Dict[str, Any]]


class ClassificationService:
    """Service for document classification using AI and vector embeddings."""
    
    def __init__(self):
        self.settings = get_settings()
        self.ai_service = AIService()
        self.embedding_service = EmbeddingService()
        self._initialized = False
        
        logger.info("Classification Service initialized")
    
    async def initialize(self):
        """Initialize the classification service."""
        if self._initialized:
            return
        
        try:
            await self.embedding_service.initialize()
            self._initialized = True
            logger.info("Classification service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize classification service: {e}")
            raise
    
    async def classify_document(
        self, 
        request: ClassificationRequest
    ) -> ClassificationResult:
        """
        Classify a single document.
        
        Args:
            request: Classification request with document content
            
        Returns:
            ClassificationResult with classification details
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            # Perform AI classification
            ai_result = await self.ai_service.classify_document(
                content=request.content,
                project_context=request.project_id,
                user_preferences=request.user_preferences
            )
            
            if not ai_result.success:
                raise Exception(f"AI classification failed: {ai_result.error_message}")
            
            # Extract classification data
            classification_data = ai_result.result
            
            # Generate document summary
            summary_result = await self.ai_service.generate_document_summary(
                content=request.content,
                max_length=200
            )
            
            summary = None
            if summary_result.success:
                summary = summary_result.result.get("summary")
            
            # Extract entities
            entities_result = await self.ai_service.extract_entities(request.content)
            entities = None
            if entities_result.success:
                entities = entities_result.result
            
            # Generate embeddings for document chunks
            chunks = await self.embedding_service.chunk_document(request.content)
            
            # Create document chunks with embeddings
            document_chunks = []
            for i, chunk_text in enumerate(chunks):
                embedding_result = await self.embedding_service.generate_embeddings(chunk_text)
                if embedding_result.success:
                    chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=request.document_id,
                        chunk_index=i,
                        text=chunk_text,
                        embedding=embedding_result.embeddings[0],
                        metadata={
                            "chunk_size": len(chunk_text),
                            "chunk_index": i,
                            "project_id": request.project_id
                        },
                        project_id=request.project_id
                    )
                    document_chunks.append(chunk)
            
            # Store chunks in vector database
            if document_chunks:
                await self.embedding_service.store_document_chunks(document_chunks)
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return ClassificationResult(
                document_id=request.document_id,
                document_type=DocumentType(classification_data.get("document_type", "document")),
                confidence_score=classification_data.get("confidence_score", 0.0),
                categories=classification_data.get("categories", []),
                keywords=classification_data.get("keywords", []),
                summary=summary,
                entities=entities,
                sentiment=classification_data.get("sentiment"),
                processing_time_ms=processing_time,
                model_used=ai_result.model_used,
                classification_source=ClassificationSource.AI,
                metadata={
                    "ai_processing_result": ai_result.dict(),
                    "chunks_created": len(document_chunks),
                    "vector_dimensions": embedding_result.vector_dimensions if document_chunks else None
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Document classification failed: {str(e)}")
            
            return ClassificationResult(
                document_id=request.document_id,
                document_type=DocumentType.DOCUMENT,
                confidence_score=0.0,
                categories=["unknown"],
                keywords=[],
                processing_time_ms=processing_time,
                model_used="unknown",
                classification_source=ClassificationSource.SYSTEM,
                metadata={"error": str(e)}
            )
    
    async def classify_documents_batch(
        self, 
        request: BatchClassificationRequest
    ) -> BatchClassificationResult:
        """
        Classify multiple documents in batch.
        
        Args:
            request: Batch classification request
            
        Returns:
            BatchClassificationResult with all classification results
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        results = []
        errors = []
        
        # Process documents concurrently with rate limiting
        semaphore = asyncio.Semaphore(3)  # Limit concurrent classifications
        
        async def classify_single(request_item: ClassificationRequest):
            async with semaphore:
                try:
                    result = await self.classify_document(request_item)
                    return result
                except Exception as e:
                    error_info = {
                        "document_id": request_item.document_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    errors.append(error_info)
                    
                    # Return error result
                    return ClassificationResult(
                        document_id=request_item.document_id,
                        document_type=DocumentType.DOCUMENT,
                        confidence_score=0.0,
                        categories=["error"],
                        keywords=[],
                        processing_time_ms=0,
                        model_used="unknown",
                        classification_source=ClassificationSource.SYSTEM,
                        metadata={"error": str(e)}
                    )
        
        # Create tasks for all documents
        tasks = [classify_single(req) for req in request.documents]
        
        # Execute all classifications concurrently
        classification_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in classification_results:
            if isinstance(result, Exception):
                errors.append({
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                results.append(result)
        
        processing_time = (datetime.now() - start_time).microseconds // 1000
        
        successful = len([r for r in results if r.confidence_score > 0.0])
        failed = len(request.documents) - successful
        
        return BatchClassificationResult(
            total_documents=len(request.documents),
            successful_classifications=successful,
            failed_classifications=failed,
            results=results,
            processing_time_ms=processing_time,
            errors=errors
        )
    
    async def reclassify_document(
        self, 
        document_id: str,
        content: str,
        project_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Reclassify an existing document.
        
        Args:
            document_id: ID of the document to reclassify
            content: Updated document content
            project_id: Optional project ID
            user_preferences: Optional user preferences
            
        Returns:
            ClassificationResult with new classification
        """
        # Delete existing vectors
        await self.embedding_service.delete_document_vectors(document_id)
        
        # Perform new classification
        request = ClassificationRequest(
            document_id=document_id,
            content=content,
            project_id=project_id,
            user_preferences=user_preferences,
            force_reclassification=True
        )
        
        return await self.classify_document(request)
    
    async def get_similar_documents(
        self, 
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find similar documents using vector similarity search.
        
        Args:
            query: Search query
            project_id: Optional project ID to filter results
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar documents with similarity scores
        """
        if not self._initialized:
            await self.initialize()
        
        search_result = await self.embedding_service.search_similar_documents(
            query=query,
            project_id=project_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        if not search_result.success:
            logger.error(f"Similar document search failed: {search_result.error_message}")
            return []
        
        return search_result.results or []
    
    async def get_classification_analytics(
        self, 
        project_id: Optional[str] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics about document classifications.
        
        Args:
            project_id: Optional project ID to filter analytics
            time_range: Optional time range for analytics
            
        Returns:
            Dictionary with classification analytics
        """
        # This would typically query the database for classification statistics
        # For now, return basic analytics from vector index
        
        try:
            index_stats = await self.embedding_service.get_index_stats()
            
            analytics = {
                "total_documents": index_stats.get("total_vector_count", 0),
                "vector_dimensions": index_stats.get("dimension", 0),
                "index_fullness": index_stats.get("index_fullness", 0),
                "namespaces": index_stats.get("namespaces", {}),
                "project_id": project_id,
                "time_range": time_range,
                "timestamp": datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get classification analytics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def update_classification_model(
        self, 
        model_name: str
    ) -> bool:
        """
        Update the classification model.
        
        Args:
            model_name: Name of the new model to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update AI service model
            self.ai_service.model = model_name
            
            # Update embedding service model
            self.embedding_service.model_name = model_name
            await self.embedding_service.initialize()
            
            logger.info(f"Classification model updated to: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update classification model: {e}")
            return False
    
    async def close(self):
        """Close the classification service and clean up resources."""
        await self.ai_service.close()
        await self.embedding_service.close()
        self._initialized = False
        logger.info("Classification Service closed")
    
    async def update_models(self) -> Dict[str, Any]:
        """Update AI models and configurations."""
        try:
            logger.info("Starting AI model updates")
            
            # Check for model updates
            model_updates = await self._check_model_updates()
            if not model_updates:
                return {
                    'success': True,
                    'message': 'No model updates available',
                    'models_updated': 0
                }
            
            # Update models
            updated_count = 0
            for model_info in model_updates:
                try:
                    success = await self._update_single_model(model_info)
                    if success:
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to update model {model_info['name']}: {e}")
                    continue
            
            logger.info(f"AI model updates completed: {updated_count} updated")
            
            return {
                'success': True,
                'message': f'Updated {updated_count} models',
                'models_updated': updated_count,
                'total_models': len(model_updates)
            }
            
        except Exception as e:
            logger.error(f"AI model updates failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'models_updated': 0
            }
    
    async def _check_model_updates(self) -> List[Dict[str, Any]]:
        """Check for available model updates."""
        try:
            # This would integrate with your model update checking logic
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Failed to check model updates: {e}")
            return []
    
    async def _update_single_model(self, model_info: Dict[str, Any]) -> bool:
        """Update a single AI model."""
        try:
            # This would integrate with your model update logic
            # For now, just return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to update model {model_info['name']}: {e}")
            return False
    
    async def classify_documents(self, documents: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """Classify documents using AI."""
        try:
            logger.info(f"Starting AI document classification for user: {user_id}")
            
            # Process documents in batch
            classification_results = await self.classify_documents_batch(
                ClassificationRequest(
                    documents=documents,
                    user_id=user_id
                )
            )
            
            if classification_results.success:
                return {
                    'success': True,
                    'user_id': user_id,
                    'documents_processed': len(documents),
                    'results': classification_results.results
                }
            else:
                return {
                    'success': False,
                    'error': classification_results.error_message,
                    'user_id': user_id,
                    'documents_processed': 0
                }
            
        except Exception as e:
            logger.error(f"AI document classification failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'documents_processed': 0
            }
