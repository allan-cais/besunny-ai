"""
Business Rules service for Phase 4 enterprise features.
Handles business rule engine, rule evaluation, and automated decision making.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import json
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.schemas.enterprise import (
    BusinessRuleCreate, BusinessRuleUpdate, BusinessRuleResponse, BusinessRuleListResponse
)
from app.core.redis_manager import get_redis_client
from app.core.database import get_db

logger = logging.getLogger(__name__)


class BusinessRulesService:
    """Service for business rules engine and automated decision making."""
    
    def __init__(self):
        self.settings = get_settings()
        self._rules_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._redis_client = None
        
        # Rule evaluation engine
        self._rule_engine = BusinessRuleEngine()
        
        # Default rule templates
        self._default_templates = {
            "data_classification": {
                "name": "Data Classification Rules",
                "description": "Automated data classification based on content and metadata",
                "rule_type": "classification",
                "conditions": [
                    {"field": "file_type", "operator": "in", "value": ["pdf", "doc", "txt"]},
                    {"field": "file_size", "operator": ">", "value": 1024}
                ],
                "actions": [
                    {"type": "classify", "parameters": {"category": "document"}},
                    {"type": "notify", "parameters": {"recipient": "admin"}}
                ]
            },
            "access_control": {
                "name": "Access Control Rules",
                "description": "Automated access control based on user roles and data sensitivity",
                "rule_type": "access_control",
                "conditions": [
                    {"field": "user_role", "operator": "==", "value": "admin"},
                    {"field": "data_sensitivity", "operator": "in", "value": ["high", "critical"]}
                ],
                "actions": [
                    {"type": "grant_access", "parameters": {"permission": "read"}},
                    {"type": "log_access", "parameters": {"audit": True}}
                ]
            },
            "compliance_checking": {
                "name": "Compliance Checking Rules",
                "description": "Automated compliance validation for data processing",
                "rule_type": "compliance",
                "conditions": [
                    {"field": "data_type", "operator": "==", "value": "personal"},
                    {"field": "processing_purpose", "operator": "in", "value": ["analytics", "marketing"]}
                ],
                "actions": [
                    {"type": "check_consent", "parameters": {"required": True}},
                    {"type": "apply_retention", "parameters": {"period_days": 365}}
                ]
            }
        }
    
    async def _get_redis_client(self):
        """Get Redis client for caching."""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    async def create_business_rule(
        self,
        tenant_id: str,
        rule_data: BusinessRuleCreate,
        created_by: str
    ) -> Optional[BusinessRuleResponse]:
        """Create a new business rule."""
        try:
            rule_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            # Validate rule syntax
            if not self._rule_engine.validate_rule(rule_data.conditions, rule_data.actions):
                raise ValueError("Invalid rule syntax")
            
            business_rule = {
                "id": rule_id,
                "tenant_id": tenant_id,
                "name": rule_data.name,
                "description": rule_data.description,
                "rule_type": rule_data.rule_type,
                "conditions": rule_data.conditions,
                "actions": rule_data.actions,
                "priority": rule_data.priority,
                "is_active": rule_data.is_active,
                "metadata": rule_data.metadata,
                "created_by": created_by,
                "created_at": timestamp,
                "updated_at": timestamp
            }
            
            # Store in cache
            self._rules_cache[rule_id] = business_rule
            
            # Store in Redis for caching
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"business_rule:{tenant_id}:{rule_id}"
                await redis_client.setex(
                    cache_key,
                    self._cache_ttl,
                    json.dumps(business_rule)
                )
            
            logger.info(f"Created business rule {rule_id}: {rule_data.name}")
            
            return BusinessRuleResponse(**business_rule)
            
        except Exception as e:
            logger.error(f"Failed to create business rule: {str(e)}")
            return None
    
    async def get_business_rule(self, rule_id: str) -> Optional[BusinessRuleResponse]:
        """Get business rule by ID."""
        try:
            if rule_id in self._rules_cache:
                rule = self._rules_cache[rule_id]
                return BusinessRuleResponse(**rule)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get business rule {rule_id}: {str(e)}")
            return None
    
    async def update_business_rule(
        self,
        rule_id: str,
        rule_data: BusinessRuleUpdate
    ) -> Optional[BusinessRuleResponse]:
        """Update business rule."""
        try:
            if rule_id not in self._rules_cache:
                return None
            
            rule = self._rules_cache[rule_id]
            
            # Validate updated rule syntax
            if rule_data.conditions is not None or rule_data.actions is not None:
                conditions = rule_data.conditions if rule_data.conditions is not None else rule["conditions"]
                actions = rule_data.actions if rule_data.actions is not None else rule["actions"]
                
                if not self._rule_engine.validate_rule(conditions, actions):
                    raise ValueError("Invalid rule syntax")
            
            # Update fields
            for field, value in rule_data.dict(exclude_unset=True).items():
                if value is not None:
                    rule[field] = value
            
            rule["updated_at"] = datetime.utcnow()
            
            # Update Redis cache
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"business_rule:{rule['tenant_id']}:{rule_id}"
                await redis_client.setex(
                    cache_key,
                    self._cache_ttl,
                    json.dumps(rule)
                )
            
            logger.info(f"Updated business rule {rule_id}")
            
            return BusinessRuleResponse(**rule)
            
        except Exception as e:
            logger.error(f"Failed to update business rule {rule_id}: {str(e)}")
            return None
    
    async def list_business_rules(
        self,
        tenant_id: str,
        rule_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 20
    ) -> BusinessRuleListResponse:
        """List business rules with filtering and pagination."""
        try:
            rules = list(self._rules_cache.values())
            
            # Filter by tenant
            rules = [r for r in rules if r["tenant_id"] == tenant_id]
            
            # Apply filters
            if rule_type:
                rules = [r for r in rules if r["rule_type"] == rule_type]
            
            if is_active is not None:
                rules = [r for r in rules if r["is_active"] == is_active]
            
            # Sort by priority and updated_at
            rules.sort(key=lambda x: (x["priority"], x["updated_at"]), reverse=True)
            
            # Pagination
            total = len(rules)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_rules = rules[start_idx:end_idx]
            
            # Convert to response models
            rule_responses = [BusinessRuleResponse(**r) for r in paginated_rules]
            
            return BusinessRuleListResponse(
                rules=rule_responses,
                total=total,
                page=page,
                size=size,
                has_more=end_idx < total
            )
            
        except Exception as e:
            logger.error(f"Failed to list business rules: {str(e)}")
            return BusinessRuleListResponse(
                rules=[],
                total=0,
                page=page,
                size=size,
                has_more=False
            )
    
    async def delete_business_rule(self, rule_id: str) -> bool:
        """Delete a business rule."""
        try:
            if rule_id not in self._rules_cache:
                return False
            
            rule = self._rules_cache[rule_id]
            tenant_id = rule["tenant_id"]
            
            # Remove from cache
            del self._rules_cache[rule_id]
            
            # Remove from Redis
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"business_rule:{tenant_id}:{rule_id}"
                await redis_client.delete(cache_key)
            
            logger.info(f"Deleted business rule {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete business rule {rule_id}: {str(e)}")
            return False
    
    async def create_rule_from_template(
        self,
        tenant_id: str,
        template_name: str,
        customizations: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> Optional[BusinessRuleResponse]:
        """Create a business rule from a predefined template."""
        try:
            if template_name not in self._default_templates:
                raise ValueError(f"Unknown template: {template_name}")
            
            template = self._default_templates[template_name]
            
            # Apply customizations
            name = customizations.get("name", template["name"]) if customizations else template["name"]
            description = customizations.get("description", template["description"]) if customizations else template["description"]
            conditions = customizations.get("conditions", template["conditions"]) if customizations else template["conditions"]
            actions = customizations.get("actions", template["actions"]) if customizations else template["actions"]
            
            rule_data = BusinessRuleCreate(
                name=name,
                description=description,
                rule_type=template["rule_type"],
                conditions=conditions,
                actions=actions,
                priority=100,
                is_active=True,
                metadata={"template": template_name}
            )
            
            return await self.create_business_rule(tenant_id, rule_data, created_by)
            
        except Exception as e:
            logger.error(f"Failed to create rule from template: {str(e)}")
            return None
    
    async def evaluate_rules(
        self,
        tenant_id: str,
        context: Dict[str, Any],
        rule_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate business rules against a given context."""
        try:
            # Get applicable rules
            rules = await self.list_business_rules(tenant_id, size=1000)
            applicable_rules = [r for r in rules.rules if r.is_active]
            
            if rule_types:
                applicable_rules = [r for r in applicable_rules if r.rule_type in rule_types]
            
            # Sort by priority (highest first)
            applicable_rules.sort(key=lambda x: x.priority, reverse=True)
            
            # Evaluate rules
            evaluation_results = []
            executed_actions = []
            
            for rule in applicable_rules:
                try:
                    # Check if rule conditions are met
                    conditions_met = self._rule_engine.evaluate_conditions(rule.conditions, context)
                    
                    if conditions_met:
                        # Execute rule actions
                        action_results = await self._execute_rule_actions(rule.actions, context)
                        
                        evaluation_results.append({
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "rule_type": rule.rule_type,
                            "conditions_met": True,
                            "actions_executed": action_results,
                            "evaluated_at": datetime.utcnow()
                        })
                        
                        executed_actions.extend(action_results)
                        
                        # Check if rule should stop further evaluation
                        if rule.metadata.get("stop_on_match", False):
                            break
                    else:
                        evaluation_results.append({
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "rule_type": rule.rule_type,
                            "conditions_met": False,
                            "actions_executed": [],
                            "evaluated_at": datetime.utcnow()
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to evaluate rule {rule.id}: {str(e)}")
                    evaluation_results.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "rule_type": rule.rule_type,
                        "conditions_met": False,
                        "actions_executed": [],
                        "error": str(e),
                        "evaluated_at": datetime.utcnow()
                    })
            
            return {
                "tenant_id": tenant_id,
                "context": context,
                "rules_evaluated": len(evaluation_results),
                "rules_matched": len([r for r in evaluation_results if r["conditions_met"]]),
                "actions_executed": len(executed_actions),
                "evaluation_results": evaluation_results,
                "executed_actions": executed_actions,
                "evaluated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate rules: {str(e)}")
            return {
                "tenant_id": tenant_id,
                "context": context,
                "error": str(e),
                "evaluated_at": datetime.utcnow()
            }
    
    async def _execute_rule_actions(
        self,
        actions: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute rule actions."""
        try:
            action_results = []
            
            for action in actions:
                try:
                    action_type = action.get("type")
                    parameters = action.get("parameters", {})
                    
                    # Execute action based on type
                    if action_type == "classify":
                        result = await self._execute_classify_action(parameters, context)
                    elif action_type == "notify":
                        result = await self._execute_notify_action(parameters, context)
                    elif action_type == "grant_access":
                        result = await self._execute_grant_access_action(parameters, context)
                    elif action_type == "log_access":
                        result = await self._execute_log_access_action(parameters, context)
                    elif action_type == "check_consent":
                        result = await self._execute_check_consent_action(parameters, context)
                    elif action_type == "apply_retention":
                        result = await self._execute_apply_retention_action(parameters, context)
                    else:
                        result = {
                            "action_type": action_type,
                            "status": "unknown",
                            "message": f"Unknown action type: {action_type}"
                        }
                    
                    action_results.append({
                        "action": action,
                        "result": result,
                        "executed_at": datetime.utcnow()
                    })
                    
                except Exception as e:
                    action_results.append({
                        "action": action,
                        "result": {
                            "status": "failed",
                            "error": str(e)
                        },
                        "executed_at": datetime.utcnow()
                    })
            
            return action_results
            
        except Exception as e:
            logger.error(f"Failed to execute rule actions: {str(e)}")
            return []
    
    async def _execute_classify_action(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute classification action."""
        try:
            category = parameters.get("category", "unknown")
            
            # Simulate classification
            classification_id = str(uuid.uuid4())
            
            return {
                "action_type": "classify",
                "status": "completed",
                "classification_id": classification_id,
                "category": category,
                "confidence": 0.95,
                "method": "rule_based"
            }
            
        except Exception as e:
            return {"action_type": "classify", "status": "failed", "error": str(e)}
    
    async def _execute_notify_action(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute notification action."""
        try:
            recipient = parameters.get("recipient", "admin")
            message = f"Business rule triggered: {context.get('rule_name', 'Unknown')}"
            
            # Simulate notification
            notification_id = str(uuid.uuid4())
            
            return {
                "action_type": "notify",
                "status": "completed",
                "notification_id": notification_id,
                "recipient": recipient,
                "message": message,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"action_type": "notify", "status": "failed", "error": str(e)}
    
    async def _execute_grant_access_action(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute grant access action."""
        try:
            permission = parameters.get("permission", "read")
            user_id = context.get("user_id", "unknown")
            
            # Simulate access grant
            access_id = str(uuid.uuid4())
            
            return {
                "action_type": "grant_access",
                "status": "completed",
                "access_id": access_id,
                "user_id": user_id,
                "permission": permission,
                "granted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"action_type": "grant_access", "status": "failed", "error": str(e)}
    
    async def _execute_log_access_action(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute log access action."""
        try:
            audit = parameters.get("audit", True)
            
            # Simulate access logging
            log_id = str(uuid.uuid4())
            
            return {
                "action_type": "log_access",
                "status": "completed",
                "log_id": log_id,
                "audit_enabled": audit,
                "logged_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"action_type": "log_access", "status": "failed", "error": str(e)}
    
    async def _execute_check_consent_action(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute check consent action."""
        try:
            required = parameters.get("required", True)
            
            # Simulate consent check
            consent_id = str(uuid.uuid4())
            consent_given = True  # Mock result
            
            return {
                "action_type": "check_consent",
                "status": "completed",
                "consent_id": consent_id,
                "consent_given": consent_given,
                "required": required,
                "checked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"action_type": "check_consent", "status": "failed", "error": str(e)}
    
    async def _execute_apply_retention_action(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute apply retention action."""
        try:
            period_days = parameters.get("period_days", 365)
            
            # Simulate retention application
            retention_id = str(uuid.uuid4())
            expiry_date = datetime.utcnow() + timedelta(days=period_days)
            
            return {
                "action_type": "apply_retention",
                "status": "completed",
                "retention_id": retention_id,
                "period_days": period_days,
                "expiry_date": expiry_date.isoformat(),
                "applied_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"action_type": "apply_retention", "status": "failed", "error": str(e)}
    
    async def get_rule_analytics(self, tenant_id: str) -> Dict[str, Any]:
        """Get analytics about business rule usage and performance."""
        try:
            rules = await self.list_business_rules(tenant_id, size=1000)
            
            # Calculate analytics
            total_rules = len(rules.rules)
            active_rules = len([r for r in rules.rules if r.is_active])
            
            # Count by rule type
            type_counts = {}
            for rule in rules.rules:
                rule_type = rule.rule_type
                type_counts[rule_type] = type_counts.get(rule_type, 0) + 1
            
            # Priority distribution
            priority_counts = {}
            for rule in rules.rules:
                priority = rule.priority
                priority_range = f"{(priority // 100) * 100}-{((priority // 100) * 100) + 99}"
                priority_counts[priority_range] = priority_counts.get(priority_range, 0) + 1
            
            return {
                "tenant_id": tenant_id,
                "total_rules": total_rules,
                "active_rules": active_rules,
                "inactive_rules": total_rules - active_rules,
                "rule_type_distribution": type_counts,
                "priority_distribution": priority_counts,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get rule analytics: {str(e)}")
            return {}
    
    async def test_rule(
        self,
        rule_id: str,
        test_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a business rule with sample context."""
        try:
            rule = await self.get_business_rule(rule_id)
            if not rule:
                return {"error": "Rule not found"}
            
            # Evaluate rule conditions
            conditions_met = self._rule_engine.evaluate_conditions(rule.conditions, test_context)
            
            # Simulate action execution
            actions_executed = []
            if conditions_met:
                actions_executed = await self._execute_rule_actions(rule.actions, test_context)
            
            return {
                "rule_id": rule_id,
                "rule_name": rule.name,
                "test_context": test_context,
                "conditions_met": conditions_met,
                "actions_executed": actions_executed,
                "test_result": "passed" if conditions_met else "failed",
                "tested_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to test rule {rule_id}: {str(e)}")
            return {"error": str(e)}


class BusinessRuleEngine:
    """Engine for evaluating business rule conditions."""
    
    def __init__(self):
        self.operators = {
            "==": self._equals,
            "!=": self._not_equals,
            ">": self._greater_than,
            ">=": self._greater_than_or_equal,
            "<": self._less_than,
            "<=": self._less_than_or_equal,
            "in": self._in_list,
            "not_in": self._not_in_list,
            "contains": self._contains,
            "not_contains": self._not_contains,
            "regex": self._regex_match,
            "exists": self._exists,
            "not_exists": self._not_exists
        }
    
    def validate_rule(self, conditions: List[Dict[str, Any]], actions: List[Dict[str, Any]]) -> bool:
        """Validate rule syntax."""
        try:
            # Validate conditions
            for condition in conditions:
                if not self._validate_condition(condition):
                    return False
            
            # Validate actions
            for action in actions:
                if not self._validate_action(action):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_condition(self, condition: Dict[str, Any]) -> bool:
        """Validate a single condition."""
        required_fields = ["field", "operator", "value"]
        
        # Check required fields
        for field in required_fields:
            if field not in condition:
                return False
        
        # Check operator validity
        if condition["operator"] not in self.operators:
            return False
        
        return True
    
    def _validate_action(self, action: Dict[str, Any]) -> bool:
        """Validate a single action."""
        required_fields = ["type"]
        
        # Check required fields
        for field in required_fields:
            if field not in action:
                return False
        
        return True
    
    def evaluate_conditions(self, conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against context."""
        try:
            if not conditions:
                return True
            
            # All conditions must be met (AND logic)
            for condition in conditions:
                if not self._evaluate_condition(condition, context):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to evaluate conditions: {str(e)}")
            return False
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        try:
            field = condition["field"]
            operator = condition["operator"]
            expected_value = condition["value"]
            
            # Get actual value from context
            actual_value = self._get_nested_value(context, field)
            
            # Apply operator
            if operator in self.operators:
                return self.operators[operator](actual_value, expected_value)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to evaluate condition: {str(e)}")
            return False
    
    def _get_nested_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from context using dot notation."""
        try:
            keys = field_path.split(".")
            value = context
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return value
            
        except Exception:
            return None
    
    # Operator implementations
    def _equals(self, actual: Any, expected: Any) -> bool:
        return actual == expected
    
    def _not_equals(self, actual: Any, expected: Any) -> bool:
        return actual != expected
    
    def _greater_than(self, actual: Any, expected: Any) -> bool:
        try:
            return float(actual) > float(expected)
        except (ValueError, TypeError):
            return False
    
    def _greater_than_or_equal(self, actual: Any, expected: Any) -> bool:
        try:
            return float(actual) >= float(expected)
        except (ValueError, TypeError):
            return False
    
    def _less_than(self, actual: Any, expected: Any) -> bool:
        try:
            return float(actual) < float(expected)
        except (ValueError, TypeError):
            return False
    
    def _less_than_or_equal(self, actual: Any, expected: Any) -> bool:
        try:
            return float(actual) <= float(expected)
        except (ValueError, TypeError):
            return False
    
    def _in_list(self, actual: Any, expected: Any) -> bool:
        if isinstance(expected, list):
            return actual in expected
        return False
    
    def _not_in_list(self, actual: Any, expected: Any) -> bool:
        if isinstance(expected, list):
            return actual not in expected
        return True
    
    def _contains(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, str) and isinstance(expected, str):
            return expected in actual
        return False
    
    def _not_contains(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, str) and isinstance(expected, str):
            return expected not in actual
        return True
    
    def _regex_match(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, str) and isinstance(expected, str):
            try:
                return bool(re.search(expected, actual))
            except re.error:
                return False
        return False
    
    def _exists(self, actual: Any, expected: Any) -> bool:
        return actual is not None
    
    def _not_exists(self, actual: Any, expected: Any) -> bool:
        return actual is None


# Global service instance
business_rules_service = BusinessRulesService()
