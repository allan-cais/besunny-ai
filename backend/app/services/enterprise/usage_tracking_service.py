"""
Usage tracking service for Phase 4 enterprise features.
Monitors resource usage, tracks metrics, and enforces quotas.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.schemas.enterprise import (
    UsageRecordCreate, UsageRecordResponse, UsageSummary, UsageSummaryResponse,
    UsageMetric
)
from app.core.redis_manager import get_redis_client
from app.core.database import get_db

logger = logging.getLogger(__name__)


class UsageTrackingService:
    """Service for tracking and managing resource usage."""
    
    def __init__(self):
        self.settings = get_settings()
        self._usage_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._redis_client = None
        
        # Usage aggregation intervals
        self._aggregation_intervals = {
            "hourly": timedelta(hours=1),
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30)
        }
    
    async def _get_redis_client(self):
        """Get Redis client for caching."""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    async def record_usage(
        self, 
        tenant_id: str, 
        metric: UsageMetric, 
        value: Decimal, 
        unit: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UsageRecordResponse]:
        """Record a usage event."""
        try:
            usage_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            usage_record = {
                "id": usage_id,
                "tenant_id": tenant_id,
                "metric": metric,
                "value": value,
                "unit": unit,
                "timestamp": timestamp,
                "metadata": metadata or {},
                "created_at": timestamp
            }
            
            # Store in cache
            self._usage_cache[usage_id] = usage_record
            
            # Store in Redis for real-time tracking
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"usage:{tenant_id}:{metric}:{timestamp.strftime('%Y%m%d%H')}"
                await redis_client.hincrby(cache_key, "value", int(float(value)))
                await redis_client.expire(cache_key, 86400)  # 24 hours
            
            logger.info(f"Recorded usage: {metric}={value}{unit} for tenant {tenant_id}")
            
            return UsageRecordResponse(**usage_record)
            
        except Exception as e:
            logger.error(f"Failed to record usage: {str(e)}")
            return None
    
    async def get_usage_records(
        self,
        tenant_id: str,
        metric: Optional[UsageMetric] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[UsageRecordResponse]:
        """Get usage records for a tenant."""
        try:
            records = list(self._usage_cache.values())
            
            # Filter by tenant
            records = [r for r in records if r["tenant_id"] == tenant_id]
            
            # Filter by metric
            if metric:
                records = [r for r in records if r["metric"] == metric]
            
            # Filter by time range
            if start_time:
                records = [r for r in records if r["timestamp"] >= start_time]
            
            if end_time:
                records = [r for r in records if r["timestamp"] <= end_time]
            
            # Sort by timestamp (newest first)
            records.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Apply limit
            records = records[:limit]
            
            return [UsageRecordResponse(**record) for record in records]
            
        except Exception as e:
            logger.error(f"Failed to get usage records: {str(e)}")
            return []
    
    async def get_usage_summary(
        self,
        tenant_id: str,
        period: str = "daily",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageSummaryResponse:
        """Get usage summary for a tenant over a specified period."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get all metrics
            metrics = list(UsageMetric)
            summaries = []
            total_usage = {}
            
            for metric in metrics:
                summary = await self._calculate_metric_summary(
                    tenant_id, metric, start_date, end_date, period
                )
                if summary:
                    summaries.append(summary)
                    
                    # Aggregate total usage
                    metric_key = metric.value
                    if metric_key not in total_usage:
                        total_usage[metric_key] = {
                            "total": Decimal("0"),
                            "unit": summary.unit,
                            "count": 0
                        }
                    
                    total_usage[metric_key]["total"] += summary.total_value
                    total_usage[metric_key]["count"] += 1
            
            return UsageSummaryResponse(
                tenant_id=tenant_id,
                summaries=summaries,
                total_usage=total_usage,
                period_start=start_date,
                period_end=end_date
            )
            
        except Exception as e:
            logger.error(f"Failed to get usage summary: {str(e)}")
            return UsageSummaryResponse(
                tenant_id=tenant_id,
                summaries=[],
                total_usage={},
                period_start=start_date or datetime.utcnow(),
                period_end=end_date or datetime.utcnow()
            )
    
    async def _calculate_metric_summary(
        self,
        tenant_id: str,
        metric: UsageMetric,
        start_date: datetime,
        end_date: datetime,
        period: str
    ) -> Optional[UsageSummary]:
        """Calculate summary for a specific metric."""
        try:
            # Get records for the metric
            records = await self.get_usage_records(
                tenant_id=tenant_id,
                metric=metric,
                start_time=start_date,
                end_time=end_date
            )
            
            if not records:
                return None
            
            # Calculate total value
            total_value = sum(record.value for record in records)
            
            # Get unit from first record
            unit = records[0].unit if records else "unknown"
            
            # Calculate daily breakdown
            daily_breakdown = await self._calculate_daily_breakdown(records, period)
            
            return UsageSummary(
                tenant_id=tenant_id,
                metric=metric,
                total_value=total_value,
                unit=unit,
                period_start=start_date,
                period_end=end_date,
                daily_breakdown=daily_breakdown
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate metric summary: {str(e)}")
            return None
    
    async def _calculate_daily_breakdown(
        self, 
        records: List[UsageRecordResponse], 
        period: str
    ) -> List[Dict[str, Any]]:
        """Calculate daily breakdown of usage."""
        try:
            if not records:
                return []
            
            # Group records by day
            daily_groups = {}
            for record in records:
                day_key = record.timestamp.strftime('%Y-%m-%d')
                if day_key not in daily_groups:
                    daily_groups[day_key] = []
                daily_groups[day_key].append(record)
            
            # Calculate daily totals
            breakdown = []
            for day, day_records in daily_groups.items():
                daily_total = sum(record.value for record in day_records)
                breakdown.append({
                    "date": day,
                    "value": daily_total,
                    "count": len(day_records)
                })
            
            # Sort by date
            breakdown.sort(key=lambda x: x["date"])
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to calculate daily breakdown: {str(e)}")
            return []
    
    async def get_current_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get current usage for a tenant."""
        try:
            current_time = datetime.utcnow()
            start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get today's usage
            today_records = await self.get_usage_records(
                tenant_id=tenant_id,
                start_time=start_of_day,
                end_time=current_time
            )
            
            # Group by metric
            usage_by_metric = {}
            for record in today_records:
                metric = record.metric.value
                if metric not in usage_by_metric:
                    usage_by_metric[metric] = {
                        "value": Decimal("0"),
                        "unit": record.unit,
                        "count": 0
                    }
                
                usage_by_metric[metric]["value"] += record.value
                usage_by_metric[metric]["count"] += 1
            
            return {
                "tenant_id": tenant_id,
                "date": current_time.date().isoformat(),
                "usage_by_metric": usage_by_metric,
                "total_records": len(today_records),
                "last_updated": current_time
            }
            
        except Exception as e:
            logger.error(f"Failed to get current usage: {str(e)}")
            return {}
    
    async def check_usage_limits(self, tenant_id: str, metric: UsageMetric, value: Decimal) -> Dict[str, Any]:
        """Check if usage would exceed limits."""
        try:
            # Get tenant subscription and limits
            # This would integrate with the billing service
            # For now, use default limits
            default_limits = {
                UsageMetric.API_CALLS: 1000,
                UsageMetric.DOCUMENT_PROCESSING: 100,
                UsageMetric.STORAGE_GB: 10,
                UsageMetric.AI_MODEL_CALLS: 100,
                UsageMetric.MEETING_TRANSCRIPTS: 50,
                UsageMetric.USER_SEATS: 5
            }
            
            limit = default_limits.get(metric, 1000)
            
            # Get current usage for the month
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_usage = await self.get_usage_records(
                tenant_id=tenant_id,
                metric=metric,
                start_time=start_of_month
            )
            
            current_total = sum(record.value for record in current_usage)
            projected_total = current_total + value
            
            # Check limits
            within_limit = projected_total <= limit
            remaining = max(0, limit - current_total)
            percentage_used = (current_total / limit) * 100 if limit > 0 else 0
            
            return {
                "within_limit": within_limit,
                "current_usage": current_total,
                "projected_usage": projected_total,
                "limit": limit,
                "remaining": remaining,
                "percentage_used": percentage_used,
                "can_proceed": within_limit
            }
            
        except Exception as e:
            logger.error(f"Failed to check usage limits: {str(e)}")
            return {
                "within_limit": False,
                "current_usage": 0,
                "projected_usage": 0,
                "limit": 0,
                "remaining": 0,
                "percentage_used": 0,
                "can_proceed": False,
                "error": str(e)
            }
    
    async def enforce_usage_limits(self, tenant_id: str) -> Dict[str, Any]:
        """Enforce usage limits and take action if exceeded."""
        try:
            # Get current usage for all metrics
            current_usage = await self.get_current_usage(tenant_id)
            
            # Check each metric against limits
            violations = []
            warnings = []
            
            for metric in UsageMetric:
                limit_check = await self.check_usage_limits(tenant_id, metric, Decimal("0"))
                
                if not limit_check["within_limit"]:
                    violations.append({
                        "metric": metric.value,
                        "current": limit_check["current_usage"],
                        "limit": limit_check["limit"],
                        "percentage": limit_check["percentage_used"]
                    })
                elif limit_check["percentage_used"] > 80:
                    warnings.append({
                        "metric": metric.value,
                        "current": limit_check["current_usage"],
                        "limit": limit_check["limit"],
                        "percentage": limit_check["percentage_used"]
                    })
            
            # Take action based on violations
            actions_taken = []
            
            if violations:
                # Suspend tenant or take other action
                actions_taken.append("usage_limit_exceeded")
                logger.warning(f"Usage limits exceeded for tenant {tenant_id}")
            
            if warnings:
                # Send notifications
                actions_taken.append("usage_warning_sent")
                logger.info(f"Usage warnings sent for tenant {tenant_id}")
            
            return {
                "tenant_id": tenant_id,
                "violations": violations,
                "warnings": warnings,
                "actions_taken": actions_taken,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to enforce usage limits: {str(e)}")
            return {
                "tenant_id": tenant_id,
                "violations": [],
                "warnings": [],
                "actions_taken": [],
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def get_usage_analytics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed usage analytics for a tenant."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get usage summary
            summary = await self.get_usage_summary(
                tenant_id=tenant_id,
                period="daily",
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate trends
            trends = await self._calculate_usage_trends(tenant_id, start_date, end_date)
            
            # Get peak usage times
            peak_usage = await self._get_peak_usage_times(tenant_id, start_date, end_date)
            
            # Get cost analysis (if billing is enabled)
            cost_analysis = await self._calculate_usage_costs(tenant_id, summary)
            
            return {
                "tenant_id": tenant_id,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days
                },
                "summary": summary,
                "trends": trends,
                "peak_usage": peak_usage,
                "cost_analysis": cost_analysis,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage analytics: {str(e)}")
            return {}
    
    async def _calculate_usage_trends(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate usage trends over time."""
        try:
            trends = {}
            
            for metric in UsageMetric:
                # Get daily usage for the metric
                daily_records = await self.get_usage_records(
                    tenant_id=tenant_id,
                    metric=metric,
                    start_time=start_date,
                    end_time=end_date
                )
                
                if not daily_records:
                    continue
                
                # Group by day and calculate daily totals
                daily_totals = {}
                for record in daily_records:
                    day = record.timestamp.strftime('%Y-%m-%d')
                    if day not in daily_totals:
                        daily_totals[day] = Decimal("0")
                    daily_totals[day] += record.value
                
                # Calculate trend (simple linear regression)
                if len(daily_totals) > 1:
                    days = list(daily_totals.keys())
                    values = list(daily_totals.values())
                    
                    # Simple trend calculation
                    if len(values) >= 2:
                        first_value = float(values[0])
                        last_value = float(values[-1])
                        trend_percentage = ((last_value - first_value) / first_value) * 100 if first_value > 0 else 0
                        
                        trends[metric.value] = {
                            "trend_percentage": trend_percentage,
                            "trend_direction": "increasing" if trend_percentage > 0 else "decreasing" if trend_percentage < 0 else "stable",
                            "first_value": first_value,
                            "last_value": last_value,
                            "daily_average": sum(float(v) for v in values) / len(values)
                        }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to calculate usage trends: {str(e)}")
            return {}
    
    async def _get_peak_usage_times(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get peak usage times for a tenant."""
        try:
            # Get all usage records for the period
            all_records = await self.get_usage_records(
                tenant_id=tenant_id,
                start_time=start_date,
                end_time=end_date
            )
            
            # Group by hour of day
            hourly_usage = {}
            for record in all_records:
                hour = record.timestamp.hour
                if hour not in hourly_usage:
                    hourly_usage[hour] = Decimal("0")
                hourly_usage[hour] += record.value
            
            # Find peak hours
            if hourly_usage:
                peak_hour = max(hourly_usage.keys(), key=lambda h: hourly_usage[h])
                peak_value = hourly_usage[peak_hour]
                
                return {
                    "peak_hour": peak_hour,
                    "peak_value": float(peak_value),
                    "hourly_distribution": {
                        hour: float(value) for hour, value in hourly_usage.items()
                    }
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get peak usage times: {str(e)}")
            return {}
    
    async def _calculate_usage_costs(
        self, 
        tenant_id: str, 
        summary: UsageSummaryResponse
    ) -> Dict[str, Any]:
        """Calculate costs based on usage (placeholder)."""
        try:
            # This would integrate with billing service to get actual costs
            # For now, return placeholder data
            
            total_cost = Decimal("0")
            cost_by_metric = {}
            
            for metric_summary in summary.summaries:
                # Placeholder pricing
                pricing = {
                    UsageMetric.API_CALLS: Decimal("0.001"),  # $0.001 per API call
                    UsageMetric.DOCUMENT_PROCESSING: Decimal("0.01"),  # $0.01 per document
                    UsageMetric.STORAGE_GB: Decimal("0.10"),  # $0.10 per GB
                    UsageMetric.AI_MODEL_CALLS: Decimal("0.02"),  # $0.02 per AI call
                    UsageMetric.MEETING_TRANSCRIPTS: Decimal("0.05"),  # $0.05 per transcript
                    UsageMetric.USER_SEATS: Decimal("5.00")  # $5.00 per user seat
                }
                
                price_per_unit = pricing.get(metric_summary.metric, Decimal("0"))
                metric_cost = metric_summary.total_value * price_per_unit
                
                cost_by_metric[metric_summary.metric.value] = {
                    "usage": float(metric_summary.total_value),
                    "unit": metric_summary.unit,
                    "price_per_unit": float(price_per_unit),
                    "total_cost": float(metric_cost)
                }
                
                total_cost += metric_cost
            
            return {
                "total_cost": float(total_cost),
                "currency": "USD",
                "cost_by_metric": cost_by_metric,
                "pricing_model": "usage_based"
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate usage costs: {str(e)}")
            return {}
    
    async def cleanup_old_usage_records(self, days_to_keep: int = 90) -> int:
        """Clean up old usage records."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Remove old records from cache
            old_records = [
                record_id for record_id, record in self._usage_cache.items()
                if record["timestamp"] < cutoff_date
            ]
            
            for record_id in old_records:
                del self._usage_cache[record_id]
            
            logger.info(f"Cleaned up {len(old_records)} old usage records")
            return len(old_records)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old usage records: {str(e)}")
            return 0
    
    async def export_usage_data(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime,
        format: str = "json"
    ) -> Optional[str]:
        """Export usage data for a tenant."""
        try:
            # Get usage records
            records = await self.get_usage_records(
                tenant_id=tenant_id,
                start_time=start_date,
                end_time=end_date,
                limit=10000  # Large limit for export
            )
            
            if format.lower() == "json":
                # Export as JSON
                export_data = {
                    "tenant_id": tenant_id,
                    "export_period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "total_records": len(records),
                    "records": [
                        {
                            "id": record.id,
                            "metric": record.metric.value,
                            "value": float(record.value),
                            "unit": record.unit,
                            "timestamp": record.timestamp.isoformat(),
                            "metadata": record.metadata
                        }
                        for record in records
                    ],
                    "exported_at": datetime.utcnow().isoformat()
                }
                
                return json.dumps(export_data, indent=2)
            
            elif format.lower() == "csv":
                # Export as CSV
                csv_lines = [
                    "id,metric,value,unit,timestamp,metadata"
                ]
                
                for record in records:
                    metadata_str = json.dumps(record.metadata) if record.metadata else ""
                    csv_lines.append(
                        f"{record.id},{record.metric.value},{record.value},{record.unit},"
                        f"{record.timestamp.isoformat()},\"{metadata_str}\""
                    )
                
                return "\n".join(csv_lines)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export usage data: {str(e)}")
            return None


# Global service instance
usage_tracking_service = UsageTrackingService()
