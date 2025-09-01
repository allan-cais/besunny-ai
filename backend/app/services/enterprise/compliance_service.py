"""
Compliance service for Phase 4 enterprise features.
Handles compliance standards, reporting, and regulatory requirements.
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
    ComplianceReportCreate, ComplianceReportUpdate, ComplianceReportResponse,
    ComplianceReportListResponse, ComplianceStandard
)
from app.core.redis_manager import get_redis_client
from app.core.database import get_db

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for managing compliance standards and reporting."""
    
    def __init__(self):
        self.settings = get_settings()
        self._compliance_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._redis_client = None
        
        # Compliance framework definitions
        self._compliance_frameworks = {
            ComplianceStandard.GDPR: {
                "name": "General Data Protection Regulation",
                "description": "EU data protection and privacy regulation",
                "requirements": [
                    "data_processing_consent",
                    "data_subject_rights",
                    "data_breach_notification",
                    "privacy_by_design",
                    "data_minimization",
                    "storage_limitation"
                ],
                "assessment_frequency": "quarterly",
                "reporting_requirements": ["incident_reports", "privacy_impact_assessments"]
            },
            ComplianceStandard.SOC2: {
                "name": "SOC 2 Type II",
                "description": "Service Organization Control 2 certification",
                "requirements": [
                    "security",
                    "availability",
                    "processing_integrity",
                    "confidentiality",
                    "privacy"
                ],
                "assessment_frequency": "annually",
                "reporting_requirements": ["control_tests", "audit_reports"]
            },
            ComplianceStandard.HIPAA: {
                "name": "Health Insurance Portability and Accountability Act",
                "description": "US healthcare data protection regulation",
                "requirements": [
                    "privacy_rule",
                    "security_rule",
                    "breach_notification_rule",
                    "administrative_safeguards",
                    "physical_safeguards",
                    "technical_safeguards"
                ],
                "assessment_frequency": "annually",
                "reporting_requirements": ["risk_assessments", "incident_reports"]
            },
            ComplianceStandard.ISO27001: {
                "name": "ISO 27001 Information Security Management",
                "description": "International information security standard",
                "requirements": [
                    "information_security_policy",
                    "risk_assessment",
                    "access_control",
                    "incident_management",
                    "business_continuity",
                    "compliance"
                ],
                "assessment_frequency": "annually",
                "reporting_requirements": ["internal_audits", "management_reviews"]
            },
            ComplianceStandard.CCPA: {
                "name": "California Consumer Privacy Act",
                "description": "California consumer privacy regulation",
                "requirements": [
                    "consumer_rights",
                    "data_disclosure",
                    "opt_out_rights",
                    "data_sales_prohibition",
                    "enforcement_mechanisms"
                ],
                "assessment_frequency": "annually",
                "reporting_requirements": ["privacy_notices", "consumer_requests"]
            }
        }
    
    async def _get_redis_client(self):
        """Get Redis client for caching."""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    async def create_compliance_report(
        self,
        tenant_id: str,
        standard: ComplianceStandard,
        report_type: str,
        report_date: datetime,
        status: str = "pending",
        findings: Optional[List[Dict[str, Any]]] = None,
        recommendations: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ComplianceReportResponse]:
        """Create a new compliance report."""
        try:
            report_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            compliance_report = {
                "id": report_id,
                "tenant_id": tenant_id,
                "standard": standard,
                "report_type": report_type,
                "report_date": report_date,
                "status": status,
                "findings": findings or [],
                "recommendations": recommendations or [],
                "metadata": metadata or {},
                "created_at": timestamp,
                "updated_at": timestamp
            }
            
            # Store in cache
            self._compliance_cache[report_id] = compliance_report
            
            # Store in Redis for real-time monitoring
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"compliance:{tenant_id}:{standard.value}"
                await redis_client.setex(
                    cache_key,
                    86400,  # 24 hours
                    json.dumps(compliance_report)
                )
            
            logger.info(f"Created compliance report {report_id} for {standard.value}")
            
            return ComplianceReportResponse(**compliance_report)
            
        except Exception as e:
            logger.error(f"Failed to create compliance report: {str(e)}")
            return None
    
    async def get_compliance_report(self, report_id: str) -> Optional[ComplianceReportResponse]:
        """Get compliance report by ID."""
        try:
            if report_id in self._compliance_cache:
                report = self._compliance_cache[report_id]
                return ComplianceReportResponse(**report)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get compliance report {report_id}: {str(e)}")
            return None
    
    async def update_compliance_report(
        self,
        report_id: str,
        report_data: ComplianceReportUpdate
    ) -> Optional[ComplianceReportResponse]:
        """Update compliance report."""
        try:
            if report_id not in self._compliance_cache:
                return None
            
            report = self._compliance_cache[report_id]
            
            # Update fields
            for field, value in report_data.dict(exclude_unset=True).items():
                if value is not None:
                    report[field] = value
            
            report["updated_at"] = datetime.utcnow()
            
            logger.info(f"Updated compliance report {report_id}")
            
            return ComplianceReportResponse(**report)
            
        except Exception as e:
            logger.error(f"Failed to update compliance report {report_id}: {str(e)}")
            return None
    
    async def list_compliance_reports(
        self,
        tenant_id: str,
        standard: Optional[ComplianceStandard] = None,
        status: Optional[str] = None,
        report_type: Optional[str] = None,
        page: int = 1,
        size: int = 100
    ) -> ComplianceReportListResponse:
        """List compliance reports with filtering and pagination."""
        try:
            reports = list(self._compliance_cache.values())
            
            # Filter by tenant
            reports = [r for r in reports if r["tenant_id"] == tenant_id]
            
            # Apply filters
            if standard:
                reports = [r for r in reports if r["standard"] == standard]
            
            if status:
                reports = [r for r in reports if r["status"] == status]
            
            if report_type:
                reports = [r for r in reports if r["report_type"] == report_type]
            
            # Sort by report date (newest first)
            reports.sort(key=lambda x: x["report_date"], reverse=True)
            
            # Pagination
            total = len(reports)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_reports = reports[start_idx:end_idx]
            
            # Convert to response models
            report_responses = [ComplianceReportResponse(**report) for report in paginated_reports]
            
            return ComplianceReportListResponse(
                reports=report_responses,
                total=total,
                page=page,
                size=size,
                has_more=end_idx < total
            )
            
        except Exception as e:
            logger.error(f"Failed to list compliance reports: {str(e)}")
            return ComplianceReportListResponse(
                reports=[],
                total=0,
                page=page,
                size=size,
                has_more=False
            )
    
    async def get_compliance_status(
        self,
        tenant_id: str,
        standard: ComplianceStandard
    ) -> Dict[str, Any]:
        """Get current compliance status for a specific standard."""
        try:
            # Get latest compliance report
            reports = await self.list_compliance_reports(
                tenant_id=tenant_id,
                standard=standard,
                size=1
            )
            
            if not reports.reports:
                return {
                    "tenant_id": tenant_id,
                    "standard": standard.value,
                    "status": "not_assessed",
                    "last_assessment": None,
                    "next_assessment": None,
                    "compliance_score": 0,
                    "requirements": self._compliance_frameworks[standard]["requirements"]
                }
            
            latest_report = reports.reports[0]
            
            # Calculate compliance score based on findings
            total_requirements = len(self._compliance_frameworks[standard]["requirements"])
            failed_requirements = len([f for f in latest_report.findings if f.get("severity") == "critical"])
            compliance_score = max(0, ((total_requirements - failed_requirements) / total_requirements) * 100)
            
            # Determine next assessment date
            framework = self._compliance_frameworks[standard]
            if framework["assessment_frequency"] == "quarterly":
                next_assessment = latest_report.report_date + timedelta(days=90)
            elif framework["assessment_frequency"] == "annually":
                next_assessment = latest_report.report_date + timedelta(days=365)
            else:
                next_assessment = latest_report.report_date + timedelta(days=90)
            
            return {
                "tenant_id": tenant_id,
                "standard": standard.value,
                "status": latest_report.status,
                "last_assessment": latest_report.report_date,
                "next_assessment": next_assessment,
                "compliance_score": compliance_score,
                "requirements": framework["requirements"],
                "findings_count": len(latest_report.findings),
                "recommendations_count": len(latest_report.recommendations)
            }
            
        except Exception as e:
            logger.error(f"Failed to get compliance status: {str(e)}")
            return {}
    
    async def get_compliance_overview(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive compliance overview for a tenant."""
        try:
            overview = {
                "tenant_id": tenant_id,
                "overall_compliance_score": 0,
                "standards": {},
                "critical_findings": [],
                "upcoming_assessments": [],
                "last_updated": datetime.utcnow()
            }
            
            total_score = 0
            standards_count = 0
            
            # Check each compliance standard
            for standard in ComplianceStandard:
                status = await self.get_compliance_status(tenant_id, standard)
                if status:
                    overview["standards"][standard.value] = status
                    total_score += status.get("compliance_score", 0)
                    standards_count += 1
                    
                    # Track critical findings
                    if status.get("status") == "fail":
                        overview["critical_findings"].append({
                            "standard": standard.value,
                            "status": status.get("status"),
                            "compliance_score": status.get("compliance_score", 0)
                        })
                    
                    # Track upcoming assessments
                    next_assessment = status.get("next_assessment")
                    if next_assessment and next_assessment <= datetime.utcnow() + timedelta(days=30):
                        overview["upcoming_assessments"].append({
                            "standard": standard.value,
                            "due_date": next_assessment,
                            "days_remaining": (next_assessment - datetime.utcnow()).days
                        })
            
            # Calculate overall compliance score
            if standards_count > 0:
                overview["overall_compliance_score"] = total_score / standards_count
            
            return overview
            
        except Exception as e:
            logger.error(f"Failed to get compliance overview: {str(e)}")
            return {}
    
    async def run_compliance_assessment(
        self,
        tenant_id: str,
        standard: ComplianceStandard,
        assessment_type: str = "automated"
    ) -> Dict[str, Any]:
        """Run a compliance assessment for a specific standard."""
        try:
            framework = self._compliance_frameworks[standard]
            requirements = framework["requirements"]
            
            # Run automated checks (placeholder)
            findings = []
            recommendations = []
            
            # Simulate automated compliance checks
            for requirement in requirements:
                # This would run actual compliance checks
                # For now, simulate random results
                import random
                if random.random() < 0.1:  # 10% chance of finding
                    severity = random.choice(["low", "medium", "high", "critical"])
                    findings.append({
                        "requirement": requirement,
                        "severity": severity,
                        "description": f"Compliance gap found in {requirement}",
                        "evidence": f"Automated check failed for {requirement}",
                        "timestamp": datetime.utcnow()
                    })
                    
                    # Generate recommendations
                    if severity in ["high", "critical"]:
                        recommendations.append(f"Implement controls for {requirement}")
            
            # Determine overall status
            critical_findings = [f for f in findings if f["severity"] == "critical"]
            high_findings = [f for f in findings if f["severity"] == "high"]
            
            if critical_findings:
                status = "fail"
            elif high_findings:
                status = "in_progress"
            else:
                status = "pass"
            
            # Create compliance report
            report = await self.create_compliance_report(
                tenant_id=tenant_id,
                standard=standard,
                report_type=assessment_type,
                report_date=datetime.utcnow(),
                status=status,
                findings=findings,
                recommendations=recommendations
            )
            
            return {
                "assessment_id": str(uuid.uuid4()),
                "standard": standard.value,
                "status": status,
                "findings_count": len(findings),
                "critical_findings_count": len(critical_findings),
                "high_findings_count": len(high_findings),
                "recommendations_count": len(recommendations),
                "report_id": report.id if report else None,
                "completed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to run compliance assessment: {str(e)}")
            return {}
    
    async def generate_compliance_report(
        self,
        tenant_id: str,
        standard: ComplianceStandard,
        format: str = "json"
    ) -> Optional[str]:
        """Generate a compliance report in the specified format."""
        try:
            # Get compliance status
            status = await self.get_compliance_status(tenant_id, standard)
            
            # Get latest compliance report
            reports = await self.list_compliance_reports(
                tenant_id=tenant_id,
                standard=standard,
                size=1
            )
            
            latest_report = reports.reports[0] if reports.reports else None
            
            # Prepare report data
            report_data = {
                "tenant_id": tenant_id,
                "standard": standard.value,
                "framework_info": self._compliance_frameworks[standard],
                "compliance_status": status,
                "latest_assessment": latest_report.dict() if latest_report else None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            if format.lower() == "json":
                return json.dumps(report_data, indent=2)
            
            elif format.lower() == "html":
                # Generate HTML report
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Compliance Report - {standard.value}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                        .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                        .pass {{ background-color: #d4edda; color: #155724; }}
                        .fail {{ background-color: #f8d7da; color: #721c24; }}
                        .in_progress {{ background-color: #fff3cd; color: #856404; }}
                        .requirement {{ margin: 10px 0; padding: 10px; border-left: 3px solid #007bff; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Compliance Report - {standard.value}</h1>
                        <p>Tenant: {tenant_id}</p>
                        <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="status {status.get('status', 'unknown')}">
                        <h2>Overall Status: {status.get('status', 'Unknown')}</h2>
                        <p>Compliance Score: {status.get('compliance_score', 0):.1f}%</p>
                    </div>
                    
                    <h2>Requirements</h2>
                    {''.join([f'<div class="requirement"><strong>{req}</strong></div>' for req in status.get('requirements', [])])}
                    
                    {f'<h2>Latest Assessment</h2><p>Date: {latest_report.report_date.strftime("%Y-%m-%d")}</p>' if latest_report else ''}
                    
                    {f'<h2>Findings</h2>{len(latest_report.findings)} findings identified' if latest_report and latest_report.findings else ''}
                    
                    {f'<h2>Recommendations</h2>{len(latest_report.recommendations)} recommendations provided' if latest_report and latest_report.recommendations else ''}
                </body>
                </html>
                """
                return html_content
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            return None
    
    async def get_compliance_timeline(
        self,
        tenant_id: str,
        standard: ComplianceStandard,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """Get compliance assessment timeline for a standard."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            reports = await self.list_compliance_reports(
                tenant_id=tenant_id,
                standard=standard,
                size=1000
            )
            
            # Filter by date range
            timeline_reports = [
                r for r in reports.reports
                if start_date <= r.report_date <= end_date
            ]
            
            # Sort by date
            timeline_reports.sort(key=lambda x: x.report_date)
            
            timeline = []
            for report in timeline_reports:
                timeline.append({
                    "date": report.report_date,
                    "status": report.status,
                    "report_type": report.report_type,
                    "findings_count": len(report.findings),
                    "critical_findings": len([f for f in report.findings if f.get("severity") == "critical"]),
                    "report_id": report.id
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get compliance timeline: {str(e)}")
            return []
    
    async def get_compliance_metrics(
        self,
        tenant_id: str,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """Get compliance metrics over time."""
        try:
            end_date = datetime.utcnow()
            
            if period == "monthly":
                start_date = end_date - timedelta(days=30)
            elif period == "quarterly":
                start_date = end_date - timedelta(days=90)
            elif period == "annually":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            metrics = {
                "tenant_id": tenant_id,
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "standards_assessed": 0,
                "overall_compliance_score": 0,
                "assessments_completed": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 0,
                "standards_status": {}
            }
            
            # Get metrics for each standard
            for standard in ComplianceStandard:
                status = await self.get_compliance_status(tenant_id, standard)
                if status:
                    metrics["standards_assessed"] += 1
                    metrics["overall_compliance_score"] += status.get("compliance_score", 0)
                    
                    # Track findings by severity
                    if status.get("status") == "fail":
                        metrics["critical_findings"] += 1
                    elif status.get("status") == "in_progress":
                        metrics["high_findings"] += 1
                    
                    metrics["standards_status"][standard.value] = status.get("status", "unknown")
            
            # Calculate average compliance score
            if metrics["standards_assessed"] > 0:
                metrics["overall_compliance_score"] /= metrics["standards_assessed"]
            
            # Get assessment count
            all_reports = await self.list_compliance_reports(
                tenant_id=tenant_id,
                size=10000
            )
            
            period_reports = [
                r for r in all_reports.reports
                if start_date <= r.report_date <= end_date
            ]
            
            metrics["assessments_completed"] = len(period_reports)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get compliance metrics: {str(e)}")
            return {}
    
    async def cleanup_old_compliance_reports(self, days_to_keep: int = 1095) -> int:
        """Clean up old compliance reports (default: 3 years)."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Remove old reports from cache
            old_reports = [
                report_id for report_id, report in self._compliance_cache.items()
                if report["report_date"] < cutoff_date
            ]
            
            for report_id in old_reports:
                del self._compliance_cache[report_id]
            
            logger.info(f"Cleaned up {len(old_reports)} old compliance reports")
            return len(old_reports)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old compliance reports: {str(e)}")
            return 0


# Global service instance
compliance_service = ComplianceService()
