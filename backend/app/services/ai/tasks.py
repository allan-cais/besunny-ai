"""
Celery tasks for AI services in BeSunny.ai Python backend.
Handles background processing of AI operations including classification, workflows, and bot scheduling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from celery import Celery

from ...core.celery_app import celery_app
# from .enhanced_classification_service import EnhancedClassificationService
from .auto_schedule_bots_service import AutoScheduleBotsService
from .document_workflow_service import DocumentWorkflowService
from .ai_service import AIService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="ai.classify_document_enhanced")
def classify_document_enhanced_task(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task for enhanced document classification.
    
    Args:
        request_data: Enhanced classification request data
        
    Returns:
        Classification result
    """
    try:
        logger.info(f"Starting enhanced classification task for document {request_data.get('document_id')}")
        
        # Create service instance
        service = EnhancedClassificationService()
        
        # Run classification asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(service.classify_document_enhanced(request_data))
            return result.dict()
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Enhanced classification task failed: {e}")
        self.retry(countdown=60, max_retries=3)
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.process_classification_batch")
def process_classification_batch_task(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task for batch document classification.
    
    Args:
        batch_data: Batch classification data
        
    Returns:
        Batch processing result
    """
    try:
        logger.info(f"Starting batch classification task for batch {batch_data.get('batch_id')}")
        
        # Create service instance
        service = EnhancedClassificationService()
        
        # Run batch processing asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(service.process_classification_batch(batch_data))
            return result.dict()
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Batch classification task failed: {e}")
        self.retry(countdown=120, max_retries=2)
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.auto_schedule_user_bots")
def auto_schedule_user_bots_task(self, user_id: str) -> Dict[str, Any]:
    """
    Background task for auto-scheduling user bots.
    
    Args:
        user_id: User ID to schedule bots for
        
    Returns:
        Scheduling result
    """
    try:
        logger.info(f"Starting auto-schedule bots task for user {user_id}")
        
        # Create service instance
        service = AutoScheduleBotsService()
        
        # Run auto-scheduling asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(service.auto_schedule_user_bots(user_id))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Auto-schedule bots task failed: {e}")
        self.retry(countdown=300, max_retries=2)
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.schedule_meeting_bot")
def schedule_meeting_bot_task(self, meeting_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Background task for scheduling a single meeting bot.
    
    Args:
        meeting_data: Meeting data
        user_id: User ID
        
    Returns:
        Bot scheduling result
    """
    try:
        logger.info(f"Starting meeting bot scheduling task for meeting {meeting_data.get('id')}")
        
        # Create service instance
        service = AutoScheduleBotsService()
        
        # Run bot scheduling asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(service.schedule_meeting_bot(meeting_data, user_id))
            return result.dict()
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Meeting bot scheduling task failed: {e}")
        self.retry(countdown=60, max_retries=3)
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.execute_document_workflow")
def execute_document_workflow_task(self, workflow_id: str, document_id: str, user_id: str, project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Background task for executing document workflows.
    
    Args:
        workflow_id: Workflow ID to execute
        document_id: Document ID to process
        user_id: User ID
        project_id: Optional project ID
        
    Returns:
        Workflow execution result
    """
    try:
        logger.info(f"Starting document workflow execution task for workflow {workflow_id}")
        
        # Create service instance
        service = DocumentWorkflowService()
        
        # Run workflow execution asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(service.execute_workflow(
                workflow_id=workflow_id,
                document_id=document_id,
                user_id=user_id,
                project_id=project_id
            ))
            return result.dict()
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Document workflow execution task failed: {e}")
        self.retry(countdown=120, max_retries=2)
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.process_ai_analysis")
def process_ai_analysis_task(self, content: str, analysis_type: str, user_id: str, document_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Background task for AI document analysis.
    
    Args:
        content: Document content to analyze
        analysis_type: Type of analysis to perform
        user_id: User ID
        document_id: Optional document ID
        
    Returns:
        Analysis result
    """
    try:
        logger.info(f"Starting AI analysis task for analysis type: {analysis_type}")
        
        # Create service instance
        service = AIService()
        
        # Run analysis asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if analysis_type == "sentiment":
                result = loop.run_until_complete(service.analyze_document_sentiment(content))
            elif analysis_type == "entities":
                result = loop.run_until_complete(service.extract_entities(content))
            elif analysis_type == "summary":
                result = loop.run_until_complete(service.generate_document_summary(content))
            else:
                result = loop.run_until_complete(service.analyze_document_content(content))
            
            return result.dict()
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"AI analysis task failed: {e}")
        self.retry(countdown=60, max_retries=3)
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.generate_bot_configuration")
def generate_bot_configuration_task(self, meeting_context: str, user_id: str) -> Dict[str, Any]:
    """
    Background task for generating bot configurations.
    
    Args:
        meeting_context: Meeting context for bot configuration
        user_id: User ID
        
    Returns:
        Bot configuration result
    """
    try:
        logger.info(f"Starting bot configuration generation task for user {user_id}")
        
        # Create service instance
        service = AIService()
        
        # Run configuration generation asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(service.generate_bot_configuration(meeting_context))
            return result.dict()
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Bot configuration generation task failed: {e}")
        self.retry(countdown=60, max_retries=3)
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.cleanup_expired_workflows")
def cleanup_expired_workflows_task(self) -> Dict[str, Any]:
    """
    Background task for cleaning up expired workflow executions.
    
    Returns:
        Cleanup result
    """
    try:
        logger.info("Starting expired workflows cleanup task")
        
        # Create service instance
        service = DocumentWorkflowService()
        
        # Run cleanup asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # This would implement cleanup logic for expired workflows
            # For now, just log the task execution
            logger.info("Expired workflows cleanup task completed")
            return {"status": "completed", "message": "Cleanup task executed"}
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Workflow cleanup task failed: {e}")
        return {"error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="ai.monitor_ai_processing")
def monitor_ai_processing_task(self) -> Dict[str, Any]:
    """
    Background task for monitoring AI processing performance and costs.
    
    Returns:
        Monitoring result
    """
    try:
        logger.info("Starting AI processing monitoring task")
        
        # This would implement monitoring logic for:
        # - Processing times
        # - Token usage
        # - Cost tracking
        # - Error rates
        # - Performance metrics
        
        logger.info("AI processing monitoring task completed")
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_processing_time": 0,
                "total_cost": 0.0
            }
        }
        
    except Exception as e:
        logger.error(f"AI processing monitoring task failed: {e}")
        return {"error": str(e), "status": "failed"}


# Task routing configuration
@celery_app.task(bind=True, name="ai.route_ai_tasks")
def route_ai_tasks_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Router task for AI operations based on task type.
    
    Args:
        task_type: Type of AI task to execute
        task_data: Task-specific data
        
    Returns:
        Task execution result
    """
    try:
        logger.info(f"Routing AI task: {task_type}")
        
        if task_type == "enhanced_classification":
            return classify_document_enhanced_task.delay(task_data).get()
        elif task_type == "batch_classification":
            return process_classification_batch_task.delay(task_data).get()
        elif task_type == "auto_schedule_bots":
            return auto_schedule_user_bots_task.delay(task_data.get('user_id')).get()
        elif task_type == "schedule_meeting_bot":
            return schedule_meeting_bot_task.delay(task_data.get('meeting_data'), task_data.get('user_id')).get()
        elif task_type == "execute_workflow":
            return execute_document_workflow_task.delay(
                task_data.get('workflow_id'),
                task_data.get('document_id'),
                task_data.get('user_id'),
                task_data.get('project_id')
            ).get()
        elif task_type == "ai_analysis":
            return process_ai_analysis_task.delay(
                task_data.get('content'),
                task_data.get('analysis_type'),
                task_data.get('user_id'),
                task_data.get('document_id')
            ).get()
        else:
            raise ValueError(f"Unknown AI task type: {task_type}")
            
    except Exception as e:
        logger.error(f"AI task routing failed: {e}")
        return {"error": str(e), "status": "failed"}
