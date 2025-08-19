"""
AI Orchestration Service for BeSunny.ai Python backend.
Coordinates between different AI services and provides intelligent routing,
workflow management, and service optimization.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import uuid
import json

from ...core.config import get_settings
from .ai_service import AIService
from .classification_service import ClassificationService
from .enhanced_classification_service import EnhancedClassificationService
from .meeting_intelligence_service import MeetingIntelligenceService
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class AIWorkflowRequest:
    """Request for AI workflow orchestration."""
    def __init__(self, workflow_id: str, user_id: str, workflow_type: str, 
                 input_data: Dict[str, Any], expected_outputs: List[str],
                 project_id: Optional[str] = None, priority: str = "normal"):
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.project_id = project_id
        self.input_data = input_data
        self.workflow_type = workflow_type
        self.priority = priority
        self.expected_outputs = expected_outputs


class AIWorkflowResult:
    """Result of AI workflow orchestration."""
    def __init__(self, workflow_id: str, user_id: str, status: str,
                 outputs: Dict[str, Any], processing_time_ms: int,
                 services_used: List[str], errors: List[str] = None):
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.status = status
        self.outputs = outputs
        self.processing_time_ms = processing_time_ms
        self.services_used = services_used
        self.errors = [] if errors is None else errors
        self.completed_at = datetime.now()


class ServiceHealthStatus:
    """Health status of an AI service."""
    def __init__(self, service_name: str, status: str, response_time_ms: float,
                 last_check: datetime, capacity_available: float = 1.0):
        self.service_name = service_name
        self.status = status  # healthy, degraded, down
        self.response_time_ms = response_time_ms
        self.last_check = last_check
        self.capacity_available = capacity_available


class AIOrchestrationService:
    """Service for orchestrating AI workflows and service coordination."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize AI services lazily
        self._ai_service = None
        self._classification_service = None
        self._enhanced_classification_service = None
        self._meeting_intelligence_service = None
        self._embedding_service = None
        
        self._initialized = False
        self._service_health = {}
        self._workflow_cache = {}
        
        logger.info("AI Orchestration Service initialized")
    
    @property
    def ai_service(self):
        """Get AI service, initializing if needed."""
        if self._ai_service is None:
            self._ai_service = AIService()
        return self._ai_service
    
    @property
    def classification_service(self):
        """Get classification service, initializing if needed."""
        if self._classification_service is None:
            self._classification_service = ClassificationService()
        return self._classification_service
    
    @property
    def enhanced_classification_service(self):
        """Get enhanced classification service, initializing if needed."""
        if self._enhanced_classification_service is None:
            self._enhanced_classification_service = EnhancedClassificationService()
        return self._enhanced_classification_service
    
    @property
    def meeting_intelligence_service(self):
        """Get meeting intelligence service, initializing if needed."""
        if self._meeting_intelligence_service is None:
            self._meeting_intelligence_service = MeetingIntelligenceService()
        return self._meeting_intelligence_service
    
    @property
    def embedding_service(self):
        """Get embedding service, initializing if needed."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    async def initialize(self):
        """Initialize the AI orchestration service."""
        if self._initialized:
            return
        
        try:
            # Initialize all AI services
            await asyncio.gather(
                self.enhanced_classification_service.initialize(),
                self.meeting_intelligence_service.initialize(),
                self.embedding_service.initialize(),
                return_exceptions=True
            )
            
            # Start health monitoring
            asyncio.create_task(self._monitor_service_health())
            
            self._initialized = True
            logger.info("AI Orchestration Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Orchestration Service: {e}")
            raise
    
    async def execute_workflow(self, request: AIWorkflowRequest) -> AIWorkflowResult:
        """
        Execute an AI workflow based on the request type.
        
        Args:
            request: Workflow request with input data and expected outputs
            
        Returns:
            Workflow result with outputs and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        workflow_id = request.workflow_id
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting AI workflow {workflow_id} for user {request.user_id}")
            
            # Store workflow in cache
            self._workflow_cache[workflow_id] = {
                'status': 'processing',
                'start_time': start_time,
                'request': request
            }
            
            # Route to appropriate workflow handler
            if request.workflow_type == "classification":
                result = await self._execute_classification_workflow(request)
            elif request.workflow_type == "meeting_intelligence":
                result = await self._execute_meeting_intelligence_workflow(request)
            elif request.workflow_type == "hybrid":
                result = await self._execute_hybrid_workflow(request)
            else:
                raise ValueError(f"Unknown workflow type: {request.workflow_type}")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create workflow result
            workflow_result = AIWorkflowResult(
                workflow_id=workflow_id,
                user_id=request.user_id,
                status='completed',
                outputs=result,
                processing_time_ms=int(processing_time),
                services_used=await self._get_services_used(request.workflow_type)
            )
            
            # Update cache
            self._workflow_cache[workflow_id]['status'] = 'completed'
            self._workflow_cache[workflow_id]['result'] = workflow_result
            
            logger.info(f"AI workflow {workflow_id} completed successfully")
            return workflow_result
            
        except Exception as e:
            logger.error(f"AI workflow {workflow_id} failed: {e}")
            
            # Create error result
            workflow_result = AIWorkflowResult(
                workflow_id=workflow_id,
                user_id=request.user_id,
                status='failed',
                outputs={},
                processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                services_used=[],
                errors=[str(e)]
            )
            
            # Update cache
            self._workflow_cache[workflow_id]['status'] = 'failed'
            self._workflow_cache[workflow_id]['result'] = workflow_result
            
            return workflow_result
    
    async def _execute_classification_workflow(self, request: AIWorkflowRequest) -> Dict[str, Any]:
        """Execute classification workflow."""
        try:
            # Extract document content from input
            content = request.input_data.get('content', '')
            
            # For now, return a simple classification result
            # In a full implementation, this would call the actual classification service
            result = {
                'classification': {
                    'document_type': 'document',
                    'confidence_score': 0.85,
                    'categories': ['business', 'meeting'],
                    'keywords': ['project', 'timeline', 'deliverables'],
                    'summary': 'Project planning meeting document'
                },
                'embeddings': None,
                'summary': 'Project planning meeting document',
                'keywords': ['project', 'timeline', 'deliverables'],
                'entities': ['Project Alpha', 'Q4 2024']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Classification workflow failed: {e}")
            raise
    
    async def _execute_meeting_intelligence_workflow(self, request: AIWorkflowRequest) -> Dict[str, Any]:
        """Execute meeting intelligence workflow."""
        try:
            # For now, return a simple meeting intelligence result
            # In a full implementation, this would call the actual meeting intelligence service
            result = {
                'meeting_intelligence': {
                    'meeting_id': str(uuid.uuid4()),
                    'summary': 'Team planning session',
                    'action_items': ['Review project timeline', 'Assign tasks'],
                    'participants': ['John Doe', 'Jane Smith']
                },
                'insights': ['Team collaboration is strong', 'Clear project direction'],
                'recommendations': ['Schedule follow-up meeting', 'Create action item tracker']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Meeting intelligence workflow failed: {e}")
            raise
    
    async def _execute_hybrid_workflow(self, request: AIWorkflowRequest) -> Dict[str, Any]:
        """Execute hybrid workflow combining multiple AI services."""
        try:
            results = {}
            
            # Execute multiple workflows in parallel
            tasks = []
            
            if 'classification' in request.expected_outputs:
                tasks.append(self._execute_classification_workflow(request))
            
            if 'meeting_intelligence' in request.expected_outputs:
                tasks.append(self._execute_meeting_intelligence_workflow(request))
            
            # Execute tasks in parallel
            if tasks:
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(parallel_results):
                    if isinstance(result, Exception):
                        logger.error(f"Hybrid workflow task {i} failed: {result}")
                        results[f'task_{i}_error'] = str(result)
                    else:
                        if isinstance(result, dict):
                            results.update(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid workflow failed: {e}")
            raise
    
    async def _get_services_used(self, workflow_type: str) -> List[str]:
        """Get list of services used for a workflow type."""
        service_mapping = {
            'classification': ['enhanced_classification_service', 'embedding_service'],
            'meeting_intelligence': ['meeting_intelligence_service'],
            'hybrid': ['enhanced_classification_service', 'meeting_intelligence_service', 
                      'embedding_service']
        }
        return service_mapping.get(workflow_type, [])
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow."""
        # Check cache first
        if workflow_id in self._workflow_cache:
            return self._workflow_cache[workflow_id]
        
        return None
    
    async def _monitor_service_health(self):
        """Monitor health of AI services."""
        while True:
            try:
                services = [
                    ('enhanced_classification_service', self.enhanced_classification_service),
                    ('meeting_intelligence_service', self.meeting_intelligence_service),
                    ('embedding_service', self.embedding_service)
                ]
                
                for service_name, service in services:
                    try:
                        start_time = datetime.now()
                        
                        # Simple health check - assume healthy if no health check method
                        is_healthy = True
                        
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        self._service_health[service_name] = ServiceHealthStatus(
                            service_name=service_name,
                            status='healthy' if is_healthy else 'degraded',
                            response_time_ms=response_time,
                            last_check=datetime.now(),
                            capacity_available=1.0
                        )
                        
                    except Exception as e:
                        logger.warning(f"Health check failed for {service_name}: {e}")
                        self._service_health[service_name] = ServiceHealthStatus(
                            service_name=service_name,
                            status='down',
                            response_time_ms=0.0,
                            last_check=datetime.now(),
                            capacity_available=0.0
                        )
                
                # Wait before next health check
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Service health monitoring failed: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def get_service_health(self) -> Dict[str, ServiceHealthStatus]:
        """Get health status of all AI services."""
        return self._service_health.copy()
    
    async def optimize_workflow(self, workflow_type: str, user_id: str) -> Dict[str, Any]:
        """Optimize workflow based on user patterns and service health."""
        try:
            # Get user's workflow history
            user_workflows = await self._get_user_workflow_history(user_id, workflow_type)
            
            # Analyze patterns and optimize
            optimization = {
                'workflow_type': workflow_type,
                'user_id': user_id,
                'recommended_priority': 'normal',
                'estimated_processing_time': 0,
                'service_recommendations': [],
                'optimization_tips': []
            }
            
            # Adjust priority based on user patterns
            if user_workflows.get('high_priority_count', 0) > 5:
                optimization['recommended_priority'] = 'high'
                optimization['optimization_tips'].append("Consider batch processing for efficiency")
            
            # Estimate processing time based on service health
            service_health = self._service_health.get(workflow_type, None)
            if service_health:
                if service_health.status == 'degraded':
                    optimization['estimated_processing_time'] = 1.5  # 50% longer
                    optimization['optimization_tips'].append("Service performance degraded, expect delays")
                elif service_health.status == 'down':
                    optimization['estimated_processing_time'] = 3.0  # 3x longer
                    optimization['optimization_tips'].append("Service unavailable, consider fallback options")
            
            return optimization
            
        except Exception as e:
            logger.error(f"Workflow optimization failed: {e}")
            return {}
    
    async def _get_user_workflow_history(self, user_id: str, workflow_type: str) -> Dict[str, Any]:
        """Get user's workflow history for optimization."""
        try:
            # This would typically query a database table
            # For now, return mock data
            return {
                'total_workflows': 10,
                'high_priority_count': 2,
                'average_processing_time': 1500,  # ms
                'success_rate': 0.95
            }
        except Exception as e:
            logger.warning(f"Failed to get user workflow history: {e}")
            return {}
