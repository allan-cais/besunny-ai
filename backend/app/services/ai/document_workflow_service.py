"""
AI-Powered Document Workflow Service for BeSunny.ai Python backend.
Manages document processing pipelines, automation workflows, and intelligent routing.
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
from .enhanced_classification_service import EnhancedClassificationService

logger = logging.getLogger(__name__)


class WorkflowStep(BaseModel):
    """Individual workflow step definition."""
    step_id: str
    name: str
    description: str
    step_type: str  # classification, analysis, routing, approval, notification
    order: int
    is_required: bool = True
    is_conditional: bool = False
    condition: Optional[str] = None
    action: Dict[str, Any]
    timeout_seconds: Optional[int] = None
    retry_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentWorkflow(BaseModel):
    """Document processing workflow definition."""
    workflow_id: str
    name: str
    description: str
    document_types: List[DocumentType]
    project_id: Optional[str] = None
    user_id: str
    steps: List[WorkflowStep]
    is_active: bool = True
    priority: str = "normal"  # low, normal, high, urgent
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class WorkflowExecution(BaseModel):
    """Workflow execution instance."""
    execution_id: str
    workflow_id: str
    document_id: str
    user_id: str
    project_id: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed, paused
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowStepResult(BaseModel):
    """Result of a workflow step execution."""
    step_id: str
    step_name: str
    status: str  # success, failed, skipped, timeout
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: int
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None


class DocumentWorkflowService:
    """Service for AI-powered document workflow management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.ai_service = AIService()
        self.enhanced_classification_service = EnhancedClassificationService()
        
        logger.info("Document Workflow Service initialized")
    
    async def create_workflow(self, workflow: DocumentWorkflow) -> bool:
        """
        Create a new document workflow.
        
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
            
            # Validate workflow steps
            if not await self._validate_workflow_steps(workflow.steps):
                raise Exception("Invalid workflow steps")
            
            result = await self.supabase.table('document_workflows').insert(workflow_data).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return False
    
    async def execute_workflow(
        self, 
        workflow_id: str, 
        document_id: str, 
        user_id: str,
        project_id: Optional[str] = None
    ) -> WorkflowExecution:
        """
        Execute a document workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            document_id: ID of the document to process
            user_id: ID of the user executing the workflow
            project_id: Optional project ID
            
        Returns:
            WorkflowExecution instance
        """
        try:
            # Get workflow definition
            workflow = await self._get_workflow(workflow_id)
            if not workflow:
                raise Exception(f"Workflow {workflow_id} not found")
            
            # Create execution instance
            execution = WorkflowExecution(
                execution_id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                document_id=document_id,
                user_id=user_id,
                project_id=project_id,
                status="pending"
            )
            
            # Store execution record
            await self._store_execution(execution)
            
            # Execute workflow asynchronously
            asyncio.create_task(self._execute_workflow_steps(execution, workflow))
            
            return execution
            
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            raise
    
    async def get_workflow_executions(
        self, 
        user_id: str, 
        status: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[WorkflowExecution]:
        """
        Get workflow executions for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            project_id: Optional project filter
            
        Returns:
            List of workflow executions
        """
        try:
            query = self.supabase.table('workflow_executions').select('*').eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status)
            
            if project_id:
                query = query.eq('project_id', project_id)
            
            result = await query.execute()
            
            executions = []
            for execution_data in result.data or []:
                execution = WorkflowExecution(**execution_data)
                executions.append(execution)
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get workflow executions: {e}")
            return []
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """
        Pause a workflow execution.
        
        Args:
            execution_id: Execution ID to pause
            
        Returns:
            True if paused successfully
        """
        try:
            await self.supabase.table('workflow_executions').update({
                'status': 'paused',
                'updated_at': datetime.now().isoformat()
            }).eq('id', execution_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause workflow: {e}")
            return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """
        Resume a paused workflow execution.
        
        Args:
            execution_id: Execution ID to resume
            
        Returns:
            True if resumed successfully
        """
        try:
            # Get execution and workflow
            execution = await self._get_execution(execution_id)
            if not execution or execution.status != 'paused':
                return False
            
            workflow = await self._get_workflow(execution.workflow_id)
            if not workflow:
                return False
            
            # Resume execution
            asyncio.create_task(self._execute_workflow_steps(execution, workflow))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            return False
    
    async def _execute_workflow_steps(
        self, 
        execution: WorkflowExecution, 
        workflow: DocumentWorkflow
    ):
        """Execute workflow steps sequentially."""
        try:
            # Update execution status
            execution.status = "running"
            execution.started_at = datetime.now()
            await self._update_execution(execution)
            
            # Execute steps in order
            for step in sorted(workflow.steps, key=lambda x: x.order):
                try:
                    # Check if execution was paused
                    current_execution = await self._get_execution(execution.execution_id)
                    if current_execution.status == 'paused':
                        logger.info(f"Workflow {execution.execution_id} paused at step {step.step_id}")
                        return
                    
                    # Execute step
                    step_result = await self._execute_workflow_step(step, execution)
                    execution.step_results[step.step_id] = step_result
                    execution.current_step = step.step_id
                    
                    # Update execution
                    await self._update_execution(execution)
                    
                    # Check step result
                    if step_result.status == 'failed' and step.is_required:
                        execution.status = 'failed'
                        execution.error_message = f"Required step {step.name} failed: {step_result.error_message}"
                        execution.completed_at = datetime.now()
                        await self._update_execution(execution)
                        return
                    
                    # Add delay between steps
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Step {step.step_id} execution failed: {e}")
                    step_result = WorkflowStepResult(
                        step_id=step.step_id,
                        step_name=step.name,
                        status='failed',
                        error_message=str(e),
                        processing_time_ms=0
                    )
                    execution.step_results[step.step_id] = step_result
                    
                    if step.is_required:
                        execution.status = 'failed'
                        execution.error_message = f"Required step {step.name} failed: {str(e)}"
                        execution.completed_at = datetime.now()
                        await self._update_execution(execution)
                        return
            
            # Workflow completed successfully
            execution.status = 'completed'
            execution.completed_at = datetime.now()
            await self._update_execution(execution)
            
            logger.info(f"Workflow {execution.execution_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            await self._update_execution(execution)
    
    async def _execute_workflow_step(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution
    ) -> WorkflowStepResult:
        """Execute a single workflow step."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing workflow step: {step.name}")
            
            if step.step_type == 'classification':
                result = await self._execute_classification_step(step, execution)
            elif step.step_type == 'analysis':
                result = await self._execute_analysis_step(step, execution)
            elif step.step_type == 'routing':
                result = await self._execute_routing_step(step, execution)
            elif step.step_type == 'approval':
                result = await self._execute_approval_step(step, execution)
            elif step.step_type == 'notification':
                result = await self._execute_notification_step(step, execution)
            else:
                raise Exception(f"Unknown step type: {step.step_type}")
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return WorkflowStepResult(
                step_id=step.step_id,
                step_name=step.name,
                status='success',
                result=result,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return WorkflowStepResult(
                step_id=step.step_id,
                step_name=step.name,
                status='failed',
                error_message=str(e),
                processing_time_ms=processing_time
            )
    
    async def _execute_classification_step(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute a classification workflow step."""
        try:
            # Get document content
            document = await self._get_document(execution.document_id)
            if not document:
                raise Exception("Document not found")
            
            # Perform classification
            classification_request = {
                'document_id': execution.document_id,
                'content': document.get('content', ''),
                'project_id': execution.project_id,
                'user_id': execution.user_id,
                'classification_workflow': step.action.get('workflow_type', 'standard'),
                'priority': step.action.get('priority', 'normal')
            }
            
            result = await self.enhanced_classification_service.classify_document_enhanced(
                classification_request
            )
            
            return {
                'classification_result': result.dict(),
                'document_type': result.document_type,
                'confidence_score': result.confidence_score,
                'categories': result.categories
            }
            
        except Exception as e:
            logger.error(f"Classification step failed: {e}")
            raise
    
    async def _execute_analysis_step(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute an analysis workflow step."""
        try:
            # Get document content
            document = await self._get_document(execution.document_id)
            if not document:
                raise Exception("Document not found")
            
            # Perform analysis based on step configuration
            analysis_type = step.action.get('analysis_type', 'comprehensive')
            
            if analysis_type == 'sentiment':
                result = await self.ai_service.analyze_document_sentiment(document.get('content', ''))
            elif analysis_type == 'entities':
                result = await self.ai_service.extract_entities(document.get('content', ''))
            elif analysis_type == 'summary':
                result = await self.ai_service.generate_document_summary(document.get('content', ''))
            else:
                result = await self.ai_service.analyze_document_content(document.get('content', ''))
            
            if not result.success:
                raise Exception(f"Analysis failed: {result.error_message}")
            
            return {
                'analysis_type': analysis_type,
                'result': result.result,
                'model_used': result.model_used
            }
            
        except Exception as e:
            logger.error(f"Analysis step failed: {e}")
            raise
    
    async def _execute_routing_step(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute a routing workflow step."""
        try:
            # Get routing rules from step action
            routing_rules = step.action.get('rules', [])
            
            # Apply routing logic based on previous step results
            routing_result = await self._apply_routing_rules(routing_rules, execution)
            
            return {
                'routing_result': routing_result,
                'rules_applied': len(routing_rules)
            }
            
        except Exception as e:
            logger.error(f"Routing step failed: {e}")
            raise
    
    async def _execute_approval_step(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute an approval workflow step."""
        try:
            # Create approval request
            approval_data = {
                'workflow_execution_id': execution.execution_id,
                'document_id': execution.document_id,
                'user_id': execution.user_id,
                'approver_id': step.action.get('approver_id'),
                'approval_type': step.action.get('approval_type', 'manual'),
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            # Store approval request
            result = await self.supabase.table('workflow_approvals').insert(approval_data).execute()
            
            return {
                'approval_id': result.data[0]['id'] if result.data else None,
                'status': 'pending'
            }
            
        except Exception as e:
            logger.error(f"Approval step failed: {e}")
            raise
    
    async def _execute_notification_step(
        self, 
        step: WorkflowStep, 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute a notification workflow step."""
        try:
            # Get notification configuration
            notification_config = step.action.get('notification', {})
            
            # Send notification based on configuration
            notification_result = await self._send_notification(notification_config, execution)
            
            return {
                'notification_sent': notification_result,
                'recipients': notification_config.get('recipients', [])
            }
            
        except Exception as e:
            logger.error(f"Notification step failed: {e}")
            raise
    
    async def _apply_routing_rules(
        self, 
        rules: List[Dict[str, Any]], 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Apply routing rules to determine document destination."""
        try:
            routing_result = {
                'destination': 'default',
                'reason': 'No rules matched',
                'rules_evaluated': len(rules)
            }
            
            for rule in rules:
                if await self._evaluate_routing_rule(rule, execution):
                    routing_result['destination'] = rule.get('destination', 'default')
                    routing_result['reason'] = rule.get('reason', 'Rule matched')
                    break
            
            return routing_result
            
        except Exception as e:
            logger.error(f"Routing rule evaluation failed: {e}")
            return {'destination': 'error', 'reason': str(e)}
    
    async def _evaluate_routing_rule(
        self, 
        rule: Dict[str, Any], 
        execution: WorkflowExecution
    ) -> bool:
        """Evaluate if a routing rule matches the current execution context."""
        try:
            condition_type = rule.get('condition_type')
            
            if condition_type == 'document_type':
                document = await self._get_document(execution.document_id)
                return document.get('type') == rule.get('value')
            
            elif condition_type == 'classification_confidence':
                # Check classification confidence from previous step
                classification_step = rule.get('depends_on_step')
                if classification_step in execution.step_results:
                    result = execution.step_results[classification_step]
                    confidence = result.get('result', {}).get('confidence_score', 0)
                    return confidence >= rule.get('value', 0)
            
            elif condition_type == 'project_id':
                return execution.project_id == rule.get('value')
            
            return False
            
        except Exception as e:
            logger.error(f"Rule evaluation failed: {e}")
            return False
    
    async def _send_notification(
        self, 
        config: Dict[str, Any], 
        execution: WorkflowExecution
    ) -> bool:
        """Send notification based on configuration."""
        try:
            # This would integrate with your notification system
            # For now, just log the notification
            logger.info(f"Notification would be sent: {config}")
            return True
            
        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return False
    
    async def _validate_workflow_steps(self, steps: List[WorkflowStep]) -> bool:
        """Validate workflow steps configuration."""
        try:
            if not steps:
                return False
            
            # Check for required fields
            for step in steps:
                if not step.step_id or not step.name or not step.step_type:
                    return False
            
            # Check for duplicate step IDs
            step_ids = [step.step_id for step in steps]
            if len(step_ids) != len(set(step_ids)):
                return False
            
            # Check for valid step types
            valid_types = ['classification', 'analysis', 'routing', 'approval', 'notification']
            for step in steps:
                if step.step_type not in valid_types:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Workflow validation failed: {e}")
            return False
    
    async def _get_workflow(self, workflow_id: str) -> Optional[DocumentWorkflow]:
        """Get workflow by ID."""
        try:
            result = await self.supabase.table('document_workflows').select('*').eq('id', workflow_id).execute()
            
            if result.data:
                return DocumentWorkflow(**result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get workflow: {e}")
            return None
    
    async def _get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        try:
            result = await self.supabase.table('workflow_executions').select('*').eq('id', execution_id).execute()
            
            if result.data:
                return WorkflowExecution(**result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get execution: {e}")
            return None
    
    async def _get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        try:
            result = await self.supabase.table('documents').select('*').eq('id', document_id).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    async def _store_execution(self, execution: WorkflowExecution):
        """Store workflow execution record."""
        try:
            execution_data = execution.dict()
            execution_data['created_at'] = execution.created_at.isoformat()
            execution_data['updated_at'] = execution.updated_at.isoformat()
            
            await self.supabase.table('workflow_executions').insert(execution_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
    
    async def _update_execution(self, execution: WorkflowExecution):
        """Update workflow execution record."""
        try:
            execution_data = execution.dict()
            execution_data['updated_at'] = datetime.now().isoformat()
            
            await self.supabase.table('workflow_executions').update(execution_data).eq('id', execution.execution_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update execution: {e}")
