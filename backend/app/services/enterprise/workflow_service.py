"""
Workflow service for Phase 4 enterprise features.
Handles workflow automation, execution, and business process management.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.schemas.enterprise import (
    WorkflowDefinitionCreate, WorkflowDefinitionUpdate, WorkflowDefinitionResponse,
    WorkflowDefinitionListResponse, WorkflowExecutionCreate, WorkflowExecutionUpdate,
    WorkflowExecutionResponse, WorkflowExecutionListResponse
)
from app.core.redis_manager import get_redis_client
from app.core.database import get_db

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for workflow automation and business process management."""
    
    def __init__(self):
        self.settings = get_settings()
        self._workflow_cache = {}
        self._execution_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._redis_client = None
        
        # Workflow execution timeout
        self._execution_timeout = self.settings.workflow_execution_timeout
        
        # Default workflow templates
        self._default_templates = {
            "document_processing": {
                "name": "Document Processing Workflow",
                "description": "Automated document processing and classification",
                "triggers": [{"type": "file_upload", "source": "drive"}],
                "steps": [
                    {"id": "extract_text", "type": "text_extraction", "order": 1},
                    {"id": "classify", "type": "ai_classification", "order": 2},
                    {"id": "store_metadata", "type": "database_update", "order": 3},
                    {"id": "notify_user", "type": "notification", "order": 4}
                ],
                "conditions": [
                    {"step": "classify", "condition": "confidence > 0.8", "action": "proceed"},
                    {"step": "classify", "condition": "confidence <= 0.8", "action": "manual_review"}
                ]
            },
            "meeting_scheduling": {
                "name": "Meeting Scheduling Workflow",
                "description": "Automated meeting scheduling and bot deployment",
                "triggers": [{"type": "calendar_event", "source": "google_calendar"}],
                "steps": [
                    {"id": "analyze_event", "type": "event_analysis", "order": 1},
                    {"id": "deploy_bot", "type": "bot_deployment", "order": 2},
                    {"id": "send_notifications", "type": "notification", "order": 3}
                ],
                "conditions": [
                    {"step": "deploy_bot", "condition": "event_type == 'meeting'", "action": "proceed"},
                    {"step": "deploy_bot", "condition": "event_type != 'meeting'", "action": "skip"}
                ]
            },
            "data_sync": {
                "name": "Data Synchronization Workflow",
                "description": "Automated data synchronization across services",
                "triggers": [{"type": "scheduled", "interval": "hourly"}],
                "steps": [
                    {"id": "check_changes", "type": "change_detection", "order": 1},
                    {"id": "sync_data", "type": "data_sync", "order": 2},
                    {"id": "validate_sync", "type": "validation", "order": 3},
                    {"id": "report_status", "type": "reporting", "order": 4}
                ],
                "conditions": [
                    {"step": "sync_data", "condition": "changes_detected > 0", "action": "proceed"},
                    {"step": "sync_data", "condition": "changes_detected == 0", "action": "skip"}
                ]
            }
        }
    
    async def _get_redis_client(self):
        """Get Redis client for caching."""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    async def create_workflow_definition(
        self,
        tenant_id: str,
        workflow_data: WorkflowDefinitionCreate,
        created_by: str
    ) -> Optional[WorkflowDefinitionResponse]:
        """Create a new workflow definition."""
        try:
            workflow_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            workflow = {
                "id": workflow_id,
                "tenant_id": tenant_id,
                "name": workflow_data.name,
                "description": workflow_data.description,
                "version": workflow_data.version,
                "triggers": workflow_data.triggers,
                "steps": workflow_data.steps,
                "conditions": workflow_data.conditions,
                "is_active": workflow_data.is_active,
                "metadata": workflow_data.metadata,
                "created_by": created_by,
                "created_at": timestamp,
                "updated_at": timestamp
            }
            
            # Store in cache
            self._workflow_cache[workflow_id] = workflow
            
            # Store in Redis for caching
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"workflow:{tenant_id}:{workflow_id}"
                await redis_client.setex(
                    cache_key,
                    self._cache_ttl,
                    json.dumps(workflow)
                )
            
            logger.info(f"Created workflow definition {workflow_id}: {workflow_data.name}")
            
            return WorkflowDefinitionResponse(**workflow)
            
        except Exception as e:
            logger.error(f"Failed to create workflow definition: {str(e)}")
            return None
    
    async def get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinitionResponse]:
        """Get workflow definition by ID."""
        try:
            if workflow_id in self._workflow_cache:
                workflow = self._workflow_cache[workflow_id]
                return WorkflowDefinitionResponse(**workflow)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get workflow definition {workflow_id}: {str(e)}")
            return None
    
    async def update_workflow_definition(
        self,
        workflow_id: str,
        workflow_data: WorkflowDefinitionUpdate
    ) -> Optional[WorkflowDefinitionResponse]:
        """Update workflow definition."""
        try:
            if workflow_id not in self._workflow_cache:
                return None
            
            workflow = self._workflow_cache[workflow_id]
            
            # Update fields
            for field, value in workflow_data.dict(exclude_unset=True).items():
                if value is not None:
                    workflow[field] = value
            
            workflow["updated_at"] = datetime.utcnow()
            
            # Update Redis cache
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"workflow:{workflow['tenant_id']}:{workflow_id}"
                await redis_client.setex(
                    cache_key,
                    self._cache_ttl,
                    json.dumps(workflow)
                )
            
            logger.info(f"Updated workflow definition {workflow_id}")
            
            return WorkflowDefinitionResponse(**workflow)
            
        except Exception as e:
            logger.error(f"Failed to update workflow definition {workflow_id}: {str(e)}")
            return None
    
    async def list_workflow_definitions(
        self,
        tenant_id: str,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 20
    ) -> WorkflowDefinitionListResponse:
        """List workflow definitions with filtering and pagination."""
        try:
            workflows = list(self._workflow_cache.values())
            
            # Filter by tenant
            workflows = [w for w in workflows if w["tenant_id"] == tenant_id]
            
            # Apply filters
            if is_active is not None:
                workflows = [w for w in workflows if w["is_active"] == is_active]
            
            # Sort by updated_at (newest first)
            workflows.sort(key=lambda x: x["updated_at"], reverse=True)
            
            # Pagination
            total = len(workflows)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_workflows = workflows[start_idx:end_idx]
            
            # Convert to response models
            workflow_responses = [WorkflowDefinitionResponse(**w) for w in paginated_workflows]
            
            return WorkflowDefinitionListResponse(
                workflows=workflow_responses,
                total=total,
                page=page,
                size=size,
                has_more=end_idx < total
            )
            
        except Exception as e:
            logger.error(f"Failed to list workflow definitions: {str(e)}")
            return WorkflowDefinitionListResponse(
                workflows=[],
                total=0,
                page=page,
                size=size,
                has_more=False
            )
    
    async def delete_workflow_definition(self, workflow_id: str) -> bool:
        """Delete a workflow definition."""
        try:
            if workflow_id not in self._workflow_cache:
                return False
            
            workflow = self._workflow_cache[workflow_id]
            tenant_id = workflow["tenant_id"]
            
            # Check if workflow has active executions
            active_executions = [
                e for e in self._execution_cache.values()
                if e["workflow_id"] == workflow_id and e["status"] in ["pending", "running"]
            ]
            
            if active_executions:
                raise ValueError("Cannot delete workflow with active executions")
            
            # Remove from cache
            del self._workflow_cache[workflow_id]
            
            # Remove from Redis
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"workflow:{tenant_id}:{workflow_id}"
                await redis_client.delete(cache_key)
            
            logger.info(f"Deleted workflow definition {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete workflow definition {workflow_id}: {str(e)}")
            return False
    
    async def create_workflow_from_template(
        self,
        tenant_id: str,
        template_name: str,
        customizations: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> Optional[WorkflowDefinitionResponse]:
        """Create a workflow from a predefined template."""
        try:
            if template_name not in self._default_templates:
                raise ValueError(f"Unknown template: {template_name}")
            
            template = self._default_templates[template_name]
            
            # Apply customizations
            name = customizations.get("name", template["name"]) if customizations else template["name"]
            description = customizations.get("description", template["description"]) if customizations else template["description"]
            triggers = customizations.get("triggers", template["triggers"]) if customizations else template["triggers"]
            steps = customizations.get("steps", template["steps"]) if customizations else template["steps"]
            conditions = customizations.get("conditions", template["conditions"]) if customizations else template["conditions"]
            
            workflow_data = WorkflowDefinitionCreate(
                name=name,
                description=description,
                version="1.0.0",
                triggers=triggers,
                steps=steps,
                conditions=conditions,
                is_active=True,
                metadata={"template": template_name}
            )
            
            return await self.create_workflow_definition(tenant_id, workflow_data, created_by)
            
        except Exception as e:
            logger.error(f"Failed to create workflow from template: {str(e)}")
            return None
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        tenant_id: str
    ) -> Optional[WorkflowExecutionResponse]:
        """Execute a workflow with input data."""
        try:
            workflow = await self.get_workflow_definition(workflow_id)
            if not workflow:
                raise ValueError("Workflow definition not found")
            
            if not workflow.is_active:
                raise ValueError("Workflow is not active")
            
            # Create execution record
            execution_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            execution = {
                "id": execution_id,
                "workflow_id": workflow_id,
                "tenant_id": tenant_id,
                "status": "pending",
                "input_data": input_data,
                "output_data": {},
                "started_at": None,
                "completed_at": None,
                "error_message": None,
                "execution_time_ms": None,
                "metadata": {},
                "created_at": timestamp,
                "updated_at": timestamp
            }
            
            # Store execution record
            self._execution_cache[execution_id] = execution
            
            # Execute workflow asynchronously
            asyncio.create_task(self._execute_workflow_async(execution_id))
            
            logger.info(f"Started workflow execution {execution_id} for workflow {workflow_id}")
            
            return WorkflowExecutionResponse(
                id=execution_id,
                created_at=timestamp,
                updated_at=timestamp,
                workflow=workflow,
                **{k: v for k, v in execution.items() if k not in ["id", "created_at", "updated_at", "workflow_id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to execute workflow: {str(e)}")
            return None
    
    async def _execute_workflow_async(self, execution_id: str):
        """Execute workflow asynchronously."""
        try:
            execution = self._execution_cache[execution_id]
            workflow = await self.get_workflow_definition(execution["workflow_id"])
            
            if not workflow:
                await self._update_execution_status(execution_id, "failed", error_message="Workflow definition not found")
                return
            
            # Update status to running
            await self._update_execution_status(execution_id, "running")
            execution["started_at"] = datetime.utcnow()
            
            # Execute workflow steps
            try:
                result = await self._execute_workflow_steps(workflow, execution)
                execution["output_data"] = result
                await self._update_execution_status(execution_id, "completed")
                execution["completed_at"] = datetime.utcnow()
                
                # Calculate execution time
                if execution["started_at"] and execution["completed_at"]:
                    execution_time = (execution["completed_at"] - execution["started_at"]).total_seconds() * 1000
                    execution["execution_time_ms"] = int(execution_time)
                
            except Exception as e:
                await self._update_execution_status(execution_id, "failed", error_message=str(e))
                execution["error_message"] = str(e)
                execution["completed_at"] = datetime.utcnow()
            
            execution["updated_at"] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to execute workflow async: {str(e)}")
            await self._update_execution_status(execution_id, "failed", error_message=str(e))
    
    async def _execute_workflow_steps(
        self,
        workflow: WorkflowDefinitionResponse,
        execution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute individual workflow steps."""
        try:
            result = {"steps": {}, "final_output": {}}
            input_data = execution["input_data"]
            
            # Sort steps by order
            sorted_steps = sorted(workflow.steps, key=lambda x: x.get("order", 0))
            
            for step in sorted_steps:
                step_id = step["id"]
                step_type = step["type"]
                
                logger.info(f"Executing step {step_id} ({step_type})")
                
                # Execute step
                step_result = await self._execute_step(step, input_data, result)
                result["steps"][step_id] = step_result
                
                # Check conditions
                if not await self._evaluate_conditions(workflow.conditions, step_id, step_result):
                    logger.info(f"Step {step_id} conditions not met, skipping remaining steps")
                    break
                
                # Update input data for next step
                input_data.update(step_result.get("output", {}))
            
            result["final_output"] = input_data
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute workflow steps: {str(e)}")
            raise
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            step_type = step["type"]
            step_id = step["id"]
            
            # Simulate step execution based on type
            if step_type == "text_extraction":
                return await self._execute_text_extraction_step(step, input_data)
            elif step_type == "ai_classification":
                return await self._execute_ai_classification_step(step, input_data)
            elif step_type == "database_update":
                return await self._execute_database_update_step(step, input_data)
            elif step_type == "notification":
                return await self._execute_notification_step(step, input_data)
            elif step_type == "event_analysis":
                return await self._execute_event_analysis_step(step, input_data)
            elif step_type == "bot_deployment":
                return await self._execute_bot_deployment_step(step, input_data)
            elif step_type == "change_detection":
                return await self._execute_change_detection_step(step, input_data)
            elif step_type == "data_sync":
                return await self._execute_data_sync_step(step, input_data)
            elif step_type == "validation":
                return await self._execute_validation_step(step, input_data)
            elif step_type == "reporting":
                return await self._execute_reporting_step(step, input_data)
            else:
                return {
                    "status": "skipped",
                    "message": f"Unknown step type: {step_type}",
                    "output": {}
                }
                
        except Exception as e:
            logger.error(f"Failed to execute step {step.get('id', 'unknown')}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "output": {}
            }
    
    async def _execute_text_extraction_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute text extraction step."""
        try:
            # Simulate text extraction
            file_content = input_data.get("file_content", "")
            extracted_text = file_content if file_content else "Sample extracted text"
            
            return {
                "status": "completed",
                "message": "Text extraction completed",
                "output": {
                    "extracted_text": extracted_text,
                    "text_length": len(extracted_text),
                    "extraction_method": "automated"
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_ai_classification_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute AI classification step."""
        try:
            # Simulate AI classification
            text = input_data.get("extracted_text", "")
            
            # Mock classification logic
            import random
            categories = ["email", "document", "spreadsheet", "presentation"]
            category = random.choice(categories)
            confidence = round(random.uniform(0.7, 0.95), 2)
            
            return {
                "status": "completed",
                "message": "AI classification completed",
                "output": {
                    "category": category,
                    "confidence": confidence,
                    "classification_method": "ai_model"
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_database_update_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database update step."""
        try:
            # Simulate database update
            category = input_data.get("category", "unknown")
            confidence = input_data.get("confidence", 0.0)
            
            # Mock database operation
            record_id = str(uuid.uuid4())
            
            return {
                "status": "completed",
                "message": "Database update completed",
                "output": {
                    "record_id": record_id,
                    "category": category,
                    "confidence": confidence,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_notification_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute notification step."""
        try:
            # Simulate notification sending
            message = f"Workflow step completed: {step.get('id', 'unknown')}"
            
            return {
                "status": "completed",
                "message": "Notification sent",
                "output": {
                    "notification_sent": True,
                    "message": message,
                    "recipients": ["user@example.com"]
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_event_analysis_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute event analysis step."""
        try:
            # Simulate event analysis
            event_title = input_data.get("event_title", "")
            event_type = "meeting" if "meeting" in event_title.lower() else "other"
            
            return {
                "status": "completed",
                "message": "Event analysis completed",
                "output": {
                    "event_type": event_type,
                    "analysis_method": "rule_based",
                    "confidence": 0.9
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_bot_deployment_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute bot deployment step."""
        try:
            # Simulate bot deployment
            event_type = input_data.get("event_type", "other")
            
            if event_type == "meeting":
                bot_id = str(uuid.uuid4())
                return {
                    "status": "completed",
                    "message": "Bot deployed successfully",
                    "output": {
                        "bot_id": bot_id,
                        "deployment_status": "active",
                        "bot_type": "meeting_transcription"
                    }
                }
            else:
                return {
                    "status": "skipped",
                    "message": "Event type does not require bot deployment",
                    "output": {}
                }
                
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_change_detection_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute change detection step."""
        try:
            # Simulate change detection
            import random
            changes_detected = random.randint(0, 10)
            
            return {
                "status": "completed",
                "message": "Change detection completed",
                "output": {
                    "changes_detected": changes_detected,
                    "detection_method": "polling",
                    "last_check": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_data_sync_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data sync step."""
        try:
            changes_detected = input_data.get("changes_detected", 0)
            
            if changes_detected > 0:
                # Simulate data sync
                sync_id = str(uuid.uuid4())
                return {
                    "status": "completed",
                    "message": "Data sync completed",
                    "output": {
                        "sync_id": sync_id,
                        "items_synced": changes_detected,
                        "sync_status": "success"
                    }
                }
            else:
                return {
                    "status": "skipped",
                    "message": "No changes detected, sync skipped",
                    "output": {}
                }
                
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_validation_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute validation step."""
        try:
            # Simulate validation
            items_synced = input_data.get("items_synced", 0)
            validation_passed = items_synced > 0
            
            return {
                "status": "completed",
                "message": "Validation completed",
                "output": {
                    "validation_passed": validation_passed,
                    "validation_method": "automated",
                    "items_validated": items_synced
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _execute_reporting_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute reporting step."""
        try:
            # Simulate reporting
            report_id = str(uuid.uuid4())
            
            return {
                "status": "completed",
                "message": "Report generated",
                "output": {
                    "report_id": report_id,
                    "report_type": "sync_summary",
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "output": {}}
    
    async def _evaluate_conditions(
        self,
        conditions: List[Dict[str, Any]],
        step_id: str,
        step_result: Dict[str, Any]
    ) -> bool:
        """Evaluate workflow conditions for a step."""
        try:
            step_conditions = [c for c in conditions if c.get("step") == step_id]
            
            for condition in step_conditions:
                condition_expr = condition.get("condition", "")
                action = condition.get("action", "proceed")
                
                # Simple condition evaluation (in production, use a proper expression evaluator)
                if "confidence > 0.8" in condition_expr:
                    confidence = step_result.get("output", {}).get("confidence", 0)
                    if confidence <= 0.8:
                        return action == "proceed"
                elif "event_type == 'meeting'" in condition_expr:
                    event_type = step_result.get("output", {}).get("event_type", "")
                    if event_type != "meeting":
                        return action == "proceed"
                elif "changes_detected > 0" in condition_expr:
                    changes_detected = step_result.get("output", {}).get("changes_detected", 0)
                    if changes_detected <= 0:
                        return action == "proceed"
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to evaluate conditions: {str(e)}")
            return True
    
    async def _update_execution_status(
        self,
        execution_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update execution status."""
        try:
            if execution_id in self._execution_cache:
                execution = self._execution_cache[execution_id]
                execution["status"] = status
                execution["updated_at"] = datetime.utcnow()
                
                if error_message:
                    execution["error_message"] = error_message
                
                logger.info(f"Updated execution {execution_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update execution status: {str(e)}")
    
    async def get_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecutionResponse]:
        """Get workflow execution by ID."""
        try:
            if execution_id in self._execution_cache:
                execution = self._execution_cache[execution_id]
                workflow = await self.get_workflow_definition(execution["workflow_id"])
                
                if workflow:
                    return WorkflowExecutionResponse(
                        id=execution_id,
                        created_at=execution["created_at"],
                        updated_at=execution["updated_at"],
                        workflow=workflow,
                        **{k: v for k, v in execution.items() if k not in ["id", "created_at", "updated_at", "workflow_id"]}
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get workflow execution {execution_id}: {str(e)}")
            return None
    
    async def list_workflow_executions(
        self,
        tenant_id: str,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> WorkflowExecutionListResponse:
        """List workflow executions with filtering and pagination."""
        try:
            executions = list(self._execution_cache.values())
            
            # Filter by tenant
            executions = [e for e in executions if e["tenant_id"] == tenant_id]
            
            # Apply filters
            if workflow_id:
                executions = [e for e in executions if e["workflow_id"] == workflow_id]
            
            if status:
                executions = [e for e in executions if e["status"] == status]
            
            # Sort by created_at (newest first)
            executions.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Pagination
            total = len(executions)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_executions = executions[start_idx:end_idx]
            
            # Convert to response models
            execution_responses = []
            for execution in paginated_executions:
                workflow = await self.get_workflow_definition(execution["workflow_id"])
                if workflow:
                    execution_responses.append(WorkflowExecutionResponse(
                        id=execution["id"],
                        created_at=execution["created_at"],
                        updated_at=execution["updated_at"],
                        workflow=workflow,
                        **{k: v for k, v in execution.items() if k not in ["id", "created_at", "updated_at", "workflow_id"]}
                    ))
            
            return WorkflowExecutionListResponse(
                executions=execution_responses,
                total=total,
                page=page,
                size=size,
                has_more=end_idx < total
            )
            
        except Exception as e:
            logger.error(f"Failed to list workflow executions: {str(e)}")
            return WorkflowExecutionListResponse(
                executions=[],
                total=0,
                page=page,
                size=size,
                has_more=False
            )
    
    async def cancel_workflow_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        try:
            execution = await self.get_workflow_execution(execution_id)
            if not execution:
                return False
            
            if execution.status not in ["pending", "running"]:
                raise ValueError("Cannot cancel completed or failed execution")
            
            await self._update_execution_status(execution_id, "cancelled")
            logger.info(f"Cancelled workflow execution {execution_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow execution {execution_id}: {str(e)}")
            return False
    
    async def get_workflow_analytics(self, tenant_id: str) -> Dict[str, Any]:
        """Get analytics about workflow usage and performance."""
        try:
            workflows = await self.list_workflow_definitions(tenant_id, size=1000)
            executions = await self.list_workflow_executions(tenant_id, size=1000)
            
            # Calculate analytics
            total_workflows = len(workflows.workflows)
            active_workflows = len([w for w in workflows.workflows if w.is_active])
            total_executions = len(executions.executions)
            
            # Execution status breakdown
            status_counts = {}
            for execution in executions.executions:
                status = execution.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Performance metrics
            completed_executions = [e for e in executions.executions if e.status == "completed"]
            if completed_executions:
                avg_execution_time = sum(e.execution_time_ms or 0 for e in completed_executions) / len(completed_executions)
                success_rate = (len(completed_executions) / total_executions) * 100 if total_executions > 0 else 0
            else:
                avg_execution_time = 0
                success_rate = 0
            
            return {
                "tenant_id": tenant_id,
                "total_workflows": total_workflows,
                "active_workflows": active_workflows,
                "total_executions": total_executions,
                "execution_status_breakdown": status_counts,
                "performance_metrics": {
                    "average_execution_time_ms": avg_execution_time,
                    "success_rate_percentage": success_rate,
                    "total_completed": len(completed_executions)
                },
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow analytics: {str(e)}")
            return {}


# Global service instance
workflow_service = WorkflowService()
