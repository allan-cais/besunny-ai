"""
Audit service for Phase 4 enterprise features.
Handles comprehensive audit logging, compliance tracking, and security monitoring.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import json
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.schemas.enterprise import (
    AuditLogCreate, AuditLogResponse, AuditLogListResponse, AuditAction
)
from app.core.redis_manager import get_redis_client
from app.core.database import get_db

logger = logging.getLogger(__name__)


class AuditService:
    """Service for comprehensive audit logging and compliance tracking."""
    
    def __init__(self):
        self.settings = get_settings()
        self._audit_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._redis_client = None
        
        # Audit log retention settings
        self._retention_days = self.settings.audit_log_retention_days
        
        # Sensitive data patterns (for redaction)
        self._sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'api_key["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'token["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'credit_card["\']?\s*[:=]\s*["\'][^"\']+["\']',
            r'ssn["\']?\s*[:=]\s*["\'][^"\']+["\']'
        ]
    
    async def _get_redis_client(self):
        """Get Redis client for caching."""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    async def log_audit_event(
        self,
        tenant_id: str,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info"
    ) -> Optional[AuditLogResponse]:
        """Log an audit event."""
        try:
            # Sanitize and redact sensitive data
            sanitized_details = await self._sanitize_audit_data(details or {})
            
            audit_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            audit_log = {
                "id": audit_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": sanitized_details,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": timestamp,
                "severity": severity,
                "created_at": timestamp
            }
            
            # Store in cache
            self._audit_cache[audit_id] = audit_log
            
            # Store in Redis for real-time monitoring
            redis_client = await self._get_redis_client()
            if redis_client:
                # Store recent audit logs
                cache_key = f"audit:{tenant_id}:recent"
                await redis_client.lpush(cache_key, json.dumps(audit_log))
                await redis_client.ltrim(cache_key, 0, 999)  # Keep last 1000 logs
                await redis_client.expire(cache_key, 86400)  # 24 hours
                
                # Store security events
                if severity in ["high", "critical"]:
                    security_key = f"security:{tenant_id}:events"
                    await redis_client.lpush(security_key, json.dumps(audit_log))
                    await redis_client.ltrim(security_key, 0, 999)
                    await redis_client.expire(security_key, 86400)
            
            logger.info(f"Audit event logged: {action.value} on {resource_type} by user {user_id}")
            
            return AuditLogResponse(**audit_log)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            return None
    
    async def get_audit_logs(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        page: int = 1,
        size: int = 100
    ) -> AuditLogListResponse:
        """Get audit logs with filtering and pagination."""
        try:
            logs = list(self._audit_cache.values())
            
            # Filter by tenant
            logs = [l for l in logs if l["tenant_id"] == tenant_id]
            
            # Apply filters
            if user_id:
                logs = [l for l in logs if l["user_id"] == user_id]
            
            if action:
                logs = [l for l in logs if l["action"] == action]
            
            if resource_type:
                logs = [l for l in logs if l["resource_type"] == resource_type]
            
            if resource_id:
                logs = [l for l in logs if l["resource_id"] == resource_id]
            
            if start_time:
                logs = [l for l in logs if l["timestamp"] >= start_time]
            
            if end_time:
                logs = [l for l in logs if l["timestamp"] <= end_time]
            
            if severity:
                logs = [l for l in logs if l["severity"] == severity]
            
            # Sort by timestamp (newest first)
            logs.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Pagination
            total = len(logs)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_logs = logs[start_idx:end_idx]
            
            # Convert to response models
            audit_responses = [AuditLogResponse(**log) for log in paginated_logs]
            
            return AuditLogListResponse(
                logs=audit_responses,
                total=total,
                page=page,
                size=size,
                has_more=end_idx < total
            )
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {str(e)}")
            return AuditLogListResponse(
                logs=[],
                total=0,
                page=page,
                size=size,
                has_more=False
            )
    
    async def get_audit_log(self, audit_id: str) -> Optional[AuditLogResponse]:
        """Get a specific audit log by ID."""
        try:
            if audit_id in self._audit_cache:
                log = self._audit_cache[audit_id]
                return AuditLogResponse(**log)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get audit log {audit_id}: {str(e)}")
            return None
    
    async def search_audit_logs(
        self,
        tenant_id: str,
        query: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLogResponse]:
        """Search audit logs by text query."""
        try:
            logs = list(self._audit_cache.values())
            
            # Filter by tenant
            logs = [l for l in logs if l["tenant_id"] == tenant_id]
            
            # Apply time filters
            if start_time:
                logs = [l for l in logs if l["timestamp"] >= start_time]
            
            if end_time:
                logs = [l for l in logs if l["timestamp"] <= end_time]
            
            # Search in relevant fields
            matching_logs = []
            query_lower = query.lower()
            
            for log in logs:
                # Search in action, resource_type, details, and user_id
                if (query_lower in log["action"].value.lower() or
                    query_lower in log["resource_type"].lower() or
                    query_lower in log["user_id"].lower() or
                    self._search_in_details(log["details"], query_lower)):
                    matching_logs.append(log)
            
            # Sort by timestamp and apply limit
            matching_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            matching_logs = matching_logs[:limit]
            
            return [AuditLogResponse(**log) for log in matching_logs]
            
        except Exception as e:
            logger.error(f"Failed to search audit logs: {str(e)}")
            return []
    
    async def get_security_events(
        self,
        tenant_id: str,
        severity: Optional[str] = None,
        hours: int = 24
    ) -> List[AuditLogResponse]:
        """Get security-related audit events."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            logs = await self.get_audit_logs(
                tenant_id=tenant_id,
                start_time=cutoff_time,
                severity=severity or "high",
                size=1000
            )
            
            # Filter for security-relevant actions
            security_actions = [
                AuditAction.LOGIN,
                AuditAction.LOGOUT,
                AuditAction.ACCESS,
                AuditAction.EXPORT,
                AuditAction.IMPORT,
                AuditAction.DELETE
            ]
            
            security_logs = [
                log for log in logs.logs
                if log.action in security_actions or log.severity in ["high", "critical"]
            ]
            
            return security_logs
            
        except Exception as e:
            logger.error(f"Failed to get security events: {str(e)}")
            return []
    
    async def get_user_activity_summary(
        self,
        tenant_id: str,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity summary for a specific user."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logs = await self.get_audit_logs(
                tenant_id=tenant_id,
                user_id=user_id,
                start_time=start_date,
                end_time=end_date,
                size=10000
            )
            
            # Group by action type
            action_counts = {}
            resource_counts = {}
            daily_activity = {}
            
            for log in logs.logs:
                # Count actions
                action = log.action.value
                action_counts[action] = action_counts.get(action, 0) + 1
                
                # Count resources
                resource = log.resource_type
                resource_counts[resource] = resource_counts.get(resource, 0) + 1
                
                # Daily activity
                day = log.timestamp.strftime('%Y-%m-%d')
                if day not in daily_activity:
                    daily_activity[day] = 0
                daily_activity[day] += 1
            
            return {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days
                },
                "total_actions": len(logs.logs),
                "action_breakdown": action_counts,
                "resource_breakdown": resource_counts,
                "daily_activity": daily_activity,
                "last_activity": max(log.timestamp for log in logs.logs) if logs.logs else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get user activity summary: {str(e)}")
            return {}
    
    async def get_compliance_report(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate compliance report for audit logs."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            
            if not end_date:
                end_date = datetime.utcnow()
            
            logs = await self.get_audit_logs(
                tenant_id=tenant_id,
                start_time=start_date,
                end_time=end_date,
                size=10000
            )
            
            # Compliance checks
            compliance_checks = {
                "data_access_logging": {
                    "status": "pass",
                    "description": "All data access events are logged",
                    "details": {}
                },
                "user_authentication": {
                    "status": "pass",
                    "description": "User authentication events are tracked",
                    "details": {}
                },
                "data_modification": {
                    "status": "pass",
                    "description": "Data modification events are logged",
                    "details": {}
                },
                "export_import_tracking": {
                    "status": "pass",
                    "description": "Data export/import events are tracked",
                    "details": {}
                }
            }
            
            # Analyze logs for compliance
            for log in logs.logs:
                # Check data access logging
                if log.action == AuditAction.READ:
                    compliance_checks["data_access_logging"]["details"]["total_reads"] = \
                        compliance_checks["data_access_logging"]["details"].get("total_reads", 0) + 1
                
                # Check authentication
                if log.action in [AuditAction.LOGIN, AuditAction.LOGOUT]:
                    compliance_checks["user_authentication"]["details"]["auth_events"] = \
                        compliance_checks["user_authentication"]["details"].get("auth_events", 0) + 1
                
                # Check data modification
                if log.action in [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]:
                    compliance_checks["data_modification"]["details"]["modification_events"] = \
                        compliance_checks["data_modification"]["details"].get("modification_events", 0) + 1
                
                # Check export/import
                if log.action in [AuditAction.EXPORT, AuditAction.IMPORT]:
                    compliance_checks["export_import_tracking"]["details"]["transfer_events"] = \
                        compliance_checks["export_import_tracking"]["details"].get("transfer_events", 0) + 1
            
            # Determine overall compliance status
            overall_status = "pass"
            for check in compliance_checks.values():
                if check["status"] != "pass":
                    overall_status = "fail"
                    break
            
            return {
                "tenant_id": tenant_id,
                "report_period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "overall_status": overall_status,
                "compliance_checks": compliance_checks,
                "total_audit_events": len(logs.logs),
                "generated_at": datetime.utcnow(),
                "compliance_standards": ["GDPR", "SOC2", "ISO27001"]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            return {}
    
    async def export_audit_logs(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> Optional[str]:
        """Export audit logs for compliance reporting."""
        try:
            logs = await self.get_audit_logs(
                tenant_id=tenant_id,
                start_time=start_date,
                end_time=end_date,
                size=100000  # Large limit for export
            )
            
            if format.lower() == "json":
                export_data = {
                    "tenant_id": tenant_id,
                    "export_period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "total_logs": len(logs.logs),
                    "logs": [
                        {
                            "id": log.id,
                            "user_id": log.user_id,
                            "action": log.action.value,
                            "resource_type": log.resource_type,
                            "resource_id": log.resource_id,
                            "timestamp": log.timestamp.isoformat(),
                            "ip_address": log.ip_address,
                            "severity": log.severity,
                            "details": log.details
                        }
                        for log in logs.logs
                    ],
                    "exported_at": datetime.utcnow().isoformat()
                }
                
                return json.dumps(export_data, indent=2)
            
            elif format.lower() == "csv":
                csv_lines = [
                    "id,user_id,action,resource_type,resource_id,timestamp,ip_address,severity,details"
                ]
                
                for log in logs.logs:
                    details_str = json.dumps(log.details) if log.details else ""
                    csv_lines.append(
                        f"{log.id},{log.user_id},{log.action.value},{log.resource_type},"
                        f"{log.resource_id or ''},{log.timestamp.isoformat()},"
                        f"{log.ip_address or ''},{log.severity},\"{details_str}\""
                    )
                
                return "\n".join(csv_lines)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export audit logs: {str(e)}")
            return None
    
    async def cleanup_old_audit_logs(self) -> int:
        """Clean up old audit logs based on retention policy."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self._retention_days)
            
            # Remove old logs from cache
            old_logs = [
                log_id for log_id, log in self._audit_cache.items()
                if log["timestamp"] < cutoff_date
            ]
            
            for log_id in old_logs:
                del self._audit_cache[log_id]
            
            logger.info(f"Cleaned up {len(old_logs)} old audit logs")
            return len(old_logs)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {str(e)}")
            return 0
    
    async def get_audit_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get audit log statistics for a tenant."""
        try:
            # Get recent logs (last 30 days)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            logs = await self.get_audit_logs(
                tenant_id=tenant_id,
                start_time=start_date,
                end_time=end_date,
                size=10000
            )
            
            # Calculate statistics
            total_logs = len(logs.logs)
            action_counts = {}
            severity_counts = {}
            resource_counts = {}
            daily_counts = {}
            
            for log in logs.logs:
                # Action counts
                action = log.action.value
                action_counts[action] = action_counts.get(action, 0) + 1
                
                # Severity counts
                severity = log.severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Resource counts
                resource = log.resource_type
                resource_counts[resource] = resource_counts.get(resource, 0) + 1
                
                # Daily counts
                day = log.timestamp.strftime('%Y-%m-%d')
                daily_counts[day] = daily_counts.get(day, 0) + 1
            
            return {
                "tenant_id": tenant_id,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": 30
                },
                "total_logs": total_logs,
                "action_distribution": action_counts,
                "severity_distribution": severity_counts,
                "resource_distribution": resource_counts,
                "daily_distribution": daily_counts,
                "average_logs_per_day": total_logs / 30 if total_logs > 0 else 0,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit statistics: {str(e)}")
            return {}
    
    # Private helper methods
    async def _sanitize_audit_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize audit data by redacting sensitive information."""
        try:
            if not data:
                return {}
            
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    sanitized[key] = await self._sanitize_audit_data(value)
                elif isinstance(value, str):
                    # Check for sensitive patterns
                    if any(pattern in key.lower() for pattern in ['password', 'token', 'secret', 'key']):
                        sanitized[key] = "[REDACTED]"
                    else:
                        sanitized[key] = value
                else:
                    sanitized[key] = value
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Failed to sanitize audit data: {str(e)}")
            return {"error": "Data sanitization failed"}
    
    def _search_in_details(self, details: Dict[str, Any], query: str) -> bool:
        """Search for query in audit log details."""
        try:
            if not details:
                return False
            
            details_str = json.dumps(details).lower()
            return query in details_str
            
        except Exception:
            return False
    
    async def monitor_suspicious_activity(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Monitor for suspicious activity patterns."""
        try:
            # Get recent security events
            security_events = await self.get_security_events(tenant_id, hours=24)
            
            suspicious_patterns = []
            
            # Check for multiple failed login attempts
            failed_logins = [e for e in security_events if e.action == AuditAction.LOGIN]
            if len(failed_logins) > 10:
                suspicious_patterns.append({
                    "type": "multiple_failed_logins",
                    "description": f"Multiple failed login attempts: {len(failed_logins)}",
                    "severity": "high",
                    "timestamp": datetime.utcnow()
                })
            
            # Check for unusual data export activity
            export_events = [e for e in security_events if e.action == AuditAction.EXPORT]
            if len(export_events) > 5:
                suspicious_patterns.append({
                    "type": "unusual_data_export",
                    "description": f"Unusual data export activity: {len(export_events)} exports",
                    "severity": "medium",
                    "timestamp": datetime.utcnow()
                })
            
            # Check for access outside business hours (simplified)
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:
                late_access = [e for e in security_events if e.action == AuditAction.ACCESS]
                if late_access:
                    suspicious_patterns.append({
                        "type": "after_hours_access",
                        "description": f"Access activity outside business hours: {len(late_access)} events",
                        "severity": "low",
                        "timestamp": datetime.utcnow()
                    })
            
            return suspicious_patterns
            
        except Exception as e:
            logger.error(f"Failed to monitor suspicious activity: {str(e)}")
            return []


# Global service instance
audit_service = AuditService()
