"""
Enhanced AI Classification Service for BeSunny.ai Python backend.
Provides advanced document classification capabilities with workflow management,
batch processing, and intelligent categorization.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.document import DocumentType, ClassificationSource
from .ai_service import AIService, AIProcessingResult
from .classification_service import ClassificationService

logger = logging.getLogger(__name__)


class EnhancedClassificationRequest(BaseModel):
    """Enhanced request for document classification."""
    document_id: str
    content: str
    project_id: Optional[str] = None
    user_id: str
    classification_workflow: str = "standard"  # standard, advanced, custom
    priority: str = "normal"  # low, normal, high, urgent
    metadata: Optional[Dict[str, Any]] = None
    force_reclassification: bool = False


class EnhancedClassificationResult(BaseModel):
    """Enhanced result of document classification."""
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
    workflow_status: str = "completed"
    next_steps: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class ClassificationWorkflow(BaseModel):
    """Classification workflow definition."""
    workflow_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    is_active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class ClassificationBatch(BaseModel):
    """Batch classification operation."""
    batch_id: str
    user_id: str
    project_id: Optional[str] = None
    documents: List[EnhancedClassificationRequest]
    workflow: str = "standard"
    priority: str = "normal"
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = datetime.now()
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[List[EnhancedClassificationResult]] = None
    error_count: int = 0
    success_count: int = 0


class EnhancedClassificationService:
    """Enhanced service for advanced document classification using AI."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.ai_service = AIService()
        self.classification_service = ClassificationService()
        self._initialized = False
        
        logger.info("Enhanced Classification Service initialized")
    
    async def initialize(self):
        """Initialize the enhanced classification service."""
        if self._initialized:
            return
        
        try:
            await self.classification_service.initialize()
            self._initialized = True
            logger.info("Enhanced classification service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced classification service: {e}")
            raise
    
    async def classify_document_enhanced(
        self, 
        request: EnhancedClassificationRequest
    ) -> EnhancedClassificationResult:
        """
        Perform enhanced classification of a single document.
        
        Args:
            request: Enhanced classification request
            
        Returns:
            EnhancedClassificationResult with comprehensive classification details
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting enhanced classification for document {request.document_id}")
            
            # Initialize if needed
            await self.initialize()
            
            # Perform base classification
            base_request = ClassificationRequest(
                document_id=request.document_id,
                content=request.content,
                project_id=request.project_id,
                user_preferences=request.metadata,
                force_reclassification=request.force_reclassification
            )
            
            base_result = await self.classification_service.classify_document(base_request)
            
            if not base_result:
                raise Exception("Base classification failed")
            
            # Enhance with additional AI analysis
            enhanced_result = await self._enhance_classification_result(
                base_result, request, request.content
            )
            
            # Apply workflow processing
            workflow_result = await self._apply_classification_workflow(
                enhanced_result, request.classification_workflow
            )
            
            # Generate recommendations and next steps
            recommendations = await self._generate_classification_recommendations(
                workflow_result, request
            )
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return EnhancedClassificationResult(
                document_id=workflow_result.document_id,
                document_type=workflow_result.document_type,
                confidence_score=workflow_result.confidence_score,
                categories=workflow_result.categories,
                keywords=workflow_result.keywords,
                summary=workflow_result.summary,
                entities=workflow_result.entities,
                sentiment=workflow_result.sentiment,
                processing_time_ms=processing_time,
                model_used=workflow_result.model_used,
                classification_source=workflow_result.classification_source,
                metadata=workflow_result.metadata,
                workflow_status="completed",
                next_steps=recommendations.get('next_steps', []),
                recommendations=recommendations.get('recommendations', [])
            )
            
        except Exception as e:
            logger.error(f"Enhanced classification failed for document {request.document_id}: {e}")
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return EnhancedClassificationResult(
                document_id=request.document_id,
                document_type=DocumentType.DOCUMENT,
                confidence_score=0.0,
                categories=["unknown"],
                keywords=[],
                processing_time_ms=processing_time,
                model_used="unknown",
                workflow_status="failed",
                error_message=str(e)
            )
    
    async def process_classification_batch(
        self, 
        batch: ClassificationBatch
    ) -> ClassificationBatch:
        """
        Process a batch of documents for classification.
        
        Args:
            batch: Batch classification operation
            
        Returns:
            Updated batch with results
        """
        try:
            logger.info(f"Processing classification batch {batch.batch_id}")
            
            # Update batch status
            batch.status = "processing"
            batch.started_at = datetime.now()
            
            # Process documents
            results = []
            error_count = 0
            success_count = 0
            
            for doc_request in batch.documents:
                try:
                    result = await self.classify_document_enhanced(doc_request)
                    results.append(result)
                    
                    if result.workflow_status == "completed":
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to classify document {doc_request.document_id}: {e}")
                    error_count += 1
                    
                    # Create error result
                    error_result = EnhancedClassificationResult(
                        document_id=doc_request.document_id,
                        document_type=DocumentType.DOCUMENT,
                        confidence_score=0.0,
                        categories=["error"],
                        keywords=[],
                        processing_time_ms=0,
                        model_used="unknown",
                        workflow_status="failed",
                        error_message=str(e)
                    )
                    results.append(error_result)
            
            # Update batch with results
            batch.results = results
            batch.error_count = error_count
            batch.success_count = success_count
            batch.status = "completed"
            batch.completed_at = datetime.now()
            
            # Store batch results
            await self._store_batch_results(batch)
            
            logger.info(f"Batch {batch.batch_id} completed: {success_count} success, {error_count} errors")
            
            return batch
            
        except Exception as e:
            logger.error(f"Batch processing failed for batch {batch.batch_id}: {e}")
            batch.status = "failed"
            batch.completed_at = datetime.now()
            return batch
    
    async def create_classification_workflow(
        self, 
        workflow: ClassificationWorkflow
    ) -> bool:
        """
        Create a new classification workflow.
        
        Args:
            workflow: Workflow definition
            
        Returns:
            True if workflow created successfully
        """
        try:
            workflow_data = workflow.dict()
            workflow_data['id'] = str(uuid.uuid4())
            workflow_data['created_at'] = datetime.now().isoformat()
            workflow_data['updated_at'] = datetime.now().isoformat()
            
            result = await self.supabase.table('classification_workflows').insert(workflow_data).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to create classification workflow: {e}")
            return False
    
    async def get_classification_workflows(self, user_id: str) -> List[ClassificationWorkflow]:
        """
        Get classification workflows for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of classification workflows
        """
        try:
            result = await self.supabase.table('classification_workflows').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            
            workflows = []
            for workflow_data in result.data or []:
                workflow = ClassificationWorkflow(**workflow_data)
                workflows.append(workflow)
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get classification workflows: {e}")
            return []
    
    async def _enhance_classification_result(
        self, 
        base_result: EnhancedClassificationResult, 
        request: EnhancedClassificationRequest,
        content: str
    ) -> EnhancedClassificationResult:
        """Enhance base classification result with additional AI analysis."""
        try:
            # Perform sentiment analysis
            sentiment_result = await self.ai_service.analyze_document_sentiment(content)
            if sentiment_result.success:
                base_result.sentiment = sentiment_result.result.get('sentiment')
            
            # Extract additional entities
            entity_result = await self.ai_service.extract_entities(content)
            if entity_result.success:
                base_result.entities = entity_result.result
            
            # Generate enhanced summary
            summary_result = await self.ai_service.generate_document_summary(content)
            if summary_result.success:
                base_result.summary = summary_result.result.get('summary')
            
            return base_result
            
        except Exception as e:
            logger.error(f"Failed to enhance classification result: {e}")
            return base_result
    
    async def _apply_classification_workflow(
        self, 
        result: EnhancedClassificationResult, 
        workflow_type: str
    ) -> EnhancedClassificationResult:
        """Apply classification workflow processing."""
        try:
            if workflow_type == "advanced":
                # Apply advanced workflow steps
                result = await self._apply_advanced_workflow(result)
            elif workflow_type == "custom":
                # Apply custom workflow steps
                result = await self._apply_custom_workflow(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply classification workflow: {e}")
            return result
    
    async def _apply_advanced_workflow(self, result: EnhancedClassificationResult) -> EnhancedClassificationResult:
        """Apply advanced classification workflow."""
        try:
            # Enhance categories with hierarchical classification
            if result.categories:
                enhanced_categories = []
                for category in result.categories:
                    # Add parent categories
                    parent_categories = await self._get_parent_categories(category)
                    enhanced_categories.extend(parent_categories)
                    enhanced_categories.append(category)
                
                result.categories = list(set(enhanced_categories))  # Remove duplicates
            
            # Add confidence intervals
            if result.confidence_score > 0.8:
                result.metadata = result.metadata or {}
                result.metadata['confidence_level'] = "high"
            elif result.confidence_score > 0.6:
                result.metadata = result.metadata or {}
                result.metadata['confidence_level'] = "medium"
            else:
                result.metadata = result.metadata or {}
                result.metadata['confidence_level'] = "low"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply advanced workflow: {e}")
            return result
    
    async def _apply_custom_workflow(self, result: EnhancedClassificationResult) -> EnhancedClassificationResult:
        """Apply custom classification workflow."""
        try:
            # Apply user-defined workflow rules
            # This would integrate with a workflow engine or rule system
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply custom workflow: {e}")
            return result
    
    async def _generate_classification_recommendations(
        self, 
        result: EnhancedClassificationResult, 
        request: EnhancedClassificationRequest
    ) -> Dict[str, List[str]]:
        """Generate recommendations and next steps based on classification."""
        try:
            recommendations = []
            next_steps = []
            
            # Generate recommendations based on document type
            if result.document_type == DocumentType.EMAIL:
                recommendations.append("Consider setting up email automation rules")
                next_steps.append("Review email classification accuracy")
                next_steps.append("Set up email routing based on classification")
            
            elif result.document_type == DocumentType.MEETING_TRANSCRIPT:
                recommendations.append("Extract action items and key decisions")
                next_steps.append("Generate meeting summary")
                next_steps.append("Create follow-up tasks")
            
            elif result.document_type == DocumentType.DOCUMENT:
                recommendations.append("Consider document versioning strategy")
                next_steps.append("Set up document review workflow")
                next_steps.append("Implement document approval process")
            
            # Add confidence-based recommendations
            if result.confidence_score < 0.7:
                recommendations.append("Low confidence classification - consider manual review")
                next_steps.append("Review and correct classification")
                next_steps.append("Provide feedback to improve AI model")
            
            return {
                'recommendations': recommendations,
                'next_steps': next_steps
            }
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return {
                'recommendations': [],
                'next_steps': []
            }
    
    async def _get_parent_categories(self, category: str) -> List[str]:
        """Get parent categories for hierarchical classification."""
        # This would integrate with a taxonomy or ontology system
        # For now, return basic parent categories
        category_hierarchy = {
            'business': ['corporate', 'professional'],
            'technical': ['engineering', 'development'],
            'creative': ['design', 'marketing'],
            'financial': ['accounting', 'budgeting'],
            'legal': ['compliance', 'contracts']
        }
        
        for parent, children in category_hierarchy.items():
            if category in children:
                return [parent]
        
        return []
    
    async def _store_batch_results(self, batch: ClassificationBatch) -> bool:
        """Store batch classification results."""
        try:
            # Store batch metadata
            batch_data = {
                'id': batch.batch_id,
                'user_id': batch.user_id,
                'project_id': batch.project_id,
                'workflow': batch.workflow,
                'priority': batch.priority,
                'status': batch.status,
                'created_at': batch.created_at.isoformat(),
                'started_at': batch.started_at.isoformat() if batch.started_at else None,
                'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                'error_count': batch.error_count,
                'success_count': batch.success_count
            }
            
            await self.supabase.table('classification_batches').upsert(batch_data).execute()
            
            # Store individual results
            for result in batch.results or []:
                result_data = {
                    'batch_id': batch.batch_id,
                    'document_id': result.document_id,
                    'classification_result': result.dict(),
                    'created_at': datetime.now().isoformat()
                }
                
                await self.supabase.table('classification_results').insert(result_data).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store batch results: {e}")
            return False
