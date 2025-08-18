"""
Business Intelligence service for Phase 4 enterprise features.
Handles dashboards, analytics, and data visualization.
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
    BIDashboardCreate, BIDashboardUpdate, BIDashboardResponse, BIDashboardListResponse
)
from app.core.redis_manager import get_redis_client
from app.core.database import get_db

logger = logging.getLogger(__name__)


class BusinessIntelligenceService:
    """Service for business intelligence and analytics dashboards."""
    
    def __init__(self):
        self.settings = get_settings()
        self._dashboard_cache = {}
        self._cache_ttl = self.settings.bi_cache_ttl
        self._redis_client = None
        
        # Default dashboard templates
        self._default_templates = {
            "executive_summary": {
                "name": "Executive Summary",
                "description": "High-level business metrics and KPIs",
                "widgets": [
                    {"type": "metric", "title": "Total Users", "metric": "user_count"},
                    {"type": "metric", "title": "Active Projects", "metric": "project_count"},
                    {"type": "chart", "title": "User Growth", "chart_type": "line", "data_source": "user_growth"},
                    {"type": "chart", "title": "Project Distribution", "chart_type": "pie", "data_source": "project_distribution"}
                ]
            },
            "operational_metrics": {
                "name": "Operational Metrics",
                "description": "Day-to-day operational performance indicators",
                "widgets": [
                    {"type": "metric", "title": "Documents Processed", "metric": "documents_processed"},
                    {"type": "metric", "title": "AI Processing Time", "metric": "ai_processing_time"},
                    {"type": "chart", "title": "Processing Volume", "chart_type": "bar", "data_source": "processing_volume"},
                    {"type": "chart", "title": "Error Rates", "chart_type": "line", "data_source": "error_rates"}
                ]
            },
            "financial_overview": {
                "name": "Financial Overview",
                "description": "Revenue, costs, and financial performance metrics",
                "widgets": [
                    {"type": "metric", "title": "Monthly Revenue", "metric": "monthly_revenue"},
                    {"type": "metric", "title": "Customer Count", "metric": "customer_count"},
                    {"type": "chart", "title": "Revenue Trend", "chart_type": "line", "data_source": "revenue_trend"},
                    {"type": "chart", "title": "Customer Growth", "chart_type": "area", "data_source": "customer_growth"}
                ]
            }
        }
    
    async def _get_redis_client(self):
        """Get Redis client for caching."""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    async def create_dashboard(
        self,
        tenant_id: str,
        dashboard_data: BIDashboardCreate,
        created_by: str
    ) -> Optional[BIDashboardResponse]:
        """Create a new BI dashboard."""
        try:
            dashboard_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            dashboard = {
                "id": dashboard_id,
                "tenant_id": tenant_id,
                "name": dashboard_data.name,
                "description": dashboard_data.description,
                "dashboard_type": dashboard_data.dashboard_type,
                "widgets": dashboard_data.widgets,
                "filters": dashboard_data.filters,
                "refresh_interval": dashboard_data.refresh_interval,
                "is_public": dashboard_data.is_public,
                "metadata": dashboard_data.metadata,
                "created_by": created_by,
                "created_at": timestamp,
                "updated_at": timestamp
            }
            
            # Store in cache
            self._dashboard_cache[dashboard_id] = dashboard
            
            # Store in Redis for caching
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"dashboard:{tenant_id}:{dashboard_id}"
                await redis_client.setex(
                    cache_key,
                    self._cache_ttl,
                    json.dumps(dashboard)
                )
            
            logger.info(f"Created BI dashboard {dashboard_id}: {dashboard_data.name}")
            
            return BIDashboardResponse(**dashboard)
            
        except Exception as e:
            logger.error(f"Failed to create BI dashboard: {str(e)}")
            return None
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[BIDashboardResponse]:
        """Get dashboard by ID."""
        try:
            if dashboard_id in self._dashboard_cache:
                dashboard = self._dashboard_cache[dashboard_id]
                return BIDashboardResponse(**dashboard)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get dashboard {dashboard_id}: {str(e)}")
            return None
    
    async def update_dashboard(
        self,
        dashboard_id: str,
        dashboard_data: BIDashboardUpdate
    ) -> Optional[BIDashboardResponse]:
        """Update dashboard."""
        try:
            if dashboard_id not in self._dashboard_cache:
                return None
            
            dashboard = self._dashboard_cache[dashboard_id]
            
            # Update fields
            for field, value in dashboard_data.dict(exclude_unset=True).items():
                if value is not None:
                    dashboard[field] = value
            
            dashboard["updated_at"] = datetime.utcnow()
            
            # Update Redis cache
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"dashboard:{dashboard['tenant_id']}:{dashboard_id}"
                await redis_client.setex(
                    cache_key,
                    self._cache_ttl,
                    json.dumps(dashboard)
                )
            
            logger.info(f"Updated BI dashboard {dashboard_id}")
            
            return BIDashboardResponse(**dashboard)
            
        except Exception as e:
            logger.error(f"Failed to update dashboard {dashboard_id}: {str(e)}")
            return None
    
    async def list_dashboards(
        self,
        tenant_id: str,
        dashboard_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        page: int = 1,
        size: int = 20
    ) -> BIDashboardListResponse:
        """List dashboards with filtering and pagination."""
        try:
            dashboards = list(self._dashboard_cache.values())
            
            # Filter by tenant
            dashboards = [d for d in dashboards if d["tenant_id"] == tenant_id]
            
            # Apply filters
            if dashboard_type:
                dashboards = [d for d in dashboards if d["dashboard_type"] == dashboard_type]
            
            if is_public is not None:
                dashboards = [d for d in dashboards if d["is_public"] == is_public]
            
            # Sort by updated_at (newest first)
            dashboards.sort(key=lambda x: x["updated_at"], reverse=True)
            
            # Pagination
            total = len(dashboards)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_dashboards = dashboards[start_idx:end_idx]
            
            # Convert to response models
            dashboard_responses = [BIDashboardResponse(**d) for d in paginated_dashboards]
            
            return BIDashboardListResponse(
                dashboards=dashboard_responses,
                total=total,
                page=page,
                size=size,
                has_more=end_idx < total
            )
            
        except Exception as e:
            logger.error(f"Failed to list dashboards: {str(e)}")
            return BIDashboardListResponse(
                dashboards=[],
                total=0,
                page=page,
                size=size,
                has_more=False
            )
    
    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard."""
        try:
            if dashboard_id not in self._dashboard_cache:
                return False
            
            dashboard = self._dashboard_cache[dashboard_id]
            tenant_id = dashboard["tenant_id"]
            
            # Remove from cache
            del self._dashboard_cache[dashboard_id]
            
            # Remove from Redis
            redis_client = await self._get_redis_client()
            if redis_client:
                cache_key = f"dashboard:{tenant_id}:{dashboard_id}"
                await redis_client.delete(cache_key)
            
            logger.info(f"Deleted BI dashboard {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete dashboard {dashboard_id}: {str(e)}")
            return False
    
    async def create_dashboard_from_template(
        self,
        tenant_id: str,
        template_name: str,
        customizations: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> Optional[BIDashboardResponse]:
        """Create a dashboard from a predefined template."""
        try:
            if template_name not in self._default_templates:
                raise ValueError(f"Unknown template: {template_name}")
            
            template = self._default_templates[template_name]
            
            # Apply customizations
            name = customizations.get("name", template["name"]) if customizations else template["name"]
            description = customizations.get("description", template["description"]) if customizations else template["description"]
            widgets = customizations.get("widgets", template["widgets"]) if customizations else template["widgets"]
            
            dashboard_data = BIDashboardCreate(
                name=name,
                description=description,
                dashboard_type=template_name,
                widgets=widgets,
                filters={},
                refresh_interval=300,
                is_public=False,
                metadata={"template": template_name}
            )
            
            return await self.create_dashboard(tenant_id, dashboard_data, created_by)
            
        except Exception as e:
            logger.error(f"Failed to create dashboard from template: {str(e)}")
            return None
    
    async def get_dashboard_data(
        self,
        dashboard_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get data for dashboard widgets."""
        try:
            dashboard = await self.get_dashboard(dashboard_id)
            if not dashboard:
                return {}
            
            # Apply filters
            applied_filters = filters or {}
            if dashboard.filters:
                applied_filters.update(dashboard.filters)
            
            # Get data for each widget
            widget_data = {}
            for widget in dashboard.widgets:
                widget_id = widget.get("id", str(uuid.uuid4()))
                data_source = widget.get("data_source")
                
                if data_source:
                    widget_data[widget_id] = await self._get_widget_data(
                        data_source, applied_filters, widget
                    )
                else:
                    widget_data[widget_id] = {"error": "No data source specified"}
            
            return {
                "dashboard_id": dashboard_id,
                "tenant_id": dashboard.tenant_id,
                "filters_applied": applied_filters,
                "widget_data": widget_data,
                "generated_at": datetime.utcnow(),
                "cache_ttl": self._cache_ttl
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {str(e)}")
            return {}
    
    async def _get_widget_data(
        self,
        data_source: str,
        filters: Dict[str, Any],
        widget: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get data for a specific widget."""
        try:
            # This would integrate with actual data sources
            # For now, return mock data based on data source
            
            if data_source == "user_growth":
                return await self._get_user_growth_data(filters)
            elif data_source == "project_distribution":
                return await self._get_project_distribution_data(filters)
            elif data_source == "processing_volume":
                return await self._get_processing_volume_data(filters)
            elif data_source == "error_rates":
                return await self._get_error_rates_data(filters)
            elif data_source == "revenue_trend":
                return await self._get_revenue_trend_data(filters)
            elif data_source == "customer_growth":
                return await self._get_customer_growth_data(filters)
            else:
                return {"error": f"Unknown data source: {data_source}"}
                
        except Exception as e:
            logger.error(f"Failed to get widget data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_user_growth_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user growth data for charts."""
        try:
            # Mock data - in production, this would query the database
            days = filters.get("days", 30)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Generate mock data points
            data_points = []
            current_date = start_date
            user_count = 100  # Starting user count
            
            while current_date <= end_date:
                # Simulate growth with some randomness
                import random
                growth = random.randint(0, 5)
                user_count += growth
                
                data_points.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "users": user_count,
                    "growth": growth
                })
                
                current_date += timedelta(days=1)
            
            return {
                "type": "line_chart",
                "data": data_points,
                "x_axis": "date",
                "y_axis": "users",
                "metadata": {
                    "total_users": user_count,
                    "period_days": days,
                    "average_daily_growth": sum(p["growth"] for p in data_points) / len(data_points)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user growth data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_project_distribution_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get project distribution data for pie charts."""
        try:
            # Mock data - in production, this would query the database
            project_types = ["Document Processing", "AI Analysis", "Meeting Transcription", "Data Integration", "Custom Workflows"]
            
            data_points = []
            total_projects = 0
            
            for project_type in project_types:
                # Simulate project counts
                import random
                count = random.randint(5, 50)
                data_points.append({
                    "category": project_type,
                    "count": count,
                    "percentage": 0  # Will be calculated below
                })
                total_projects += count
            
            # Calculate percentages
            for point in data_points:
                point["percentage"] = round((point["count"] / total_projects) * 100, 1)
            
            return {
                "type": "pie_chart",
                "data": data_points,
                "total_projects": total_projects,
                "metadata": {
                    "project_types": len(project_types),
                    "largest_category": max(data_points, key=lambda x: x["count"])["category"]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get project distribution data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_processing_volume_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get processing volume data for bar charts."""
        try:
            # Mock data - in production, this would query the database
            days = filters.get("days", 7)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            data_points = []
            current_date = start_date
            
            while current_date <= end_date:
                # Simulate daily processing volume
                import random
                volume = random.randint(100, 1000)
                
                data_points.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "volume": volume,
                    "status": "completed"
                })
                
                current_date += timedelta(days=1)
            
            return {
                "type": "bar_chart",
                "data": data_points,
                "x_axis": "date",
                "y_axis": "volume",
                "metadata": {
                    "total_volume": sum(p["volume"] for p in data_points),
                    "average_daily_volume": sum(p["volume"] for p in data_points) / len(data_points),
                    "period_days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing volume data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_error_rates_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get error rates data for line charts."""
        try:
            # Mock data - in production, this would query the database
            days = filters.get("days", 30)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            data_points = []
            current_date = start_date
            
            while current_date <= end_date:
                # Simulate error rates
                import random
                error_rate = round(random.uniform(0.1, 2.5), 2)
                
                data_points.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "error_rate": error_rate,
                    "status": "monitored"
                })
                
                current_date += timedelta(days=1)
            
            return {
                "type": "line_chart",
                "data": data_points,
                "x_axis": "date",
                "y_axis": "error_rate",
                "metadata": {
                    "average_error_rate": round(sum(p["error_rate"] for p in data_points) / len(data_points), 2),
                    "max_error_rate": max(p["error_rate"] for p in data_points),
                    "min_error_rate": min(p["error_rate"] for p in data_points),
                    "period_days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get error rates data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_revenue_trend_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get revenue trend data for line charts."""
        try:
            # Mock data - in production, this would query the database
            months = filters.get("months", 12)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            data_points = []
            current_date = start_date
            monthly_revenue = 5000  # Starting revenue
            
            while current_date <= end_date:
                # Simulate monthly revenue growth
                import random
                growth_rate = random.uniform(0.05, 0.15)  # 5-15% monthly growth
                monthly_revenue *= (1 + growth_rate)
                
                data_points.append({
                    "month": current_date.strftime("%Y-%m"),
                    "revenue": round(monthly_revenue, 2),
                    "growth_rate": round(growth_rate * 100, 1)
                })
                
                current_date += timedelta(days=30)
            
            return {
                "type": "line_chart",
                "data": data_points,
                "x_axis": "month",
                "y_axis": "revenue",
                "metadata": {
                    "total_revenue": sum(p["revenue"] for p in data_points),
                    "average_monthly_revenue": sum(p["revenue"] for p in data_points) / len(data_points),
                    "growth_trend": "positive" if data_points[-1]["revenue"] > data_points[0]["revenue"] else "negative"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get revenue trend data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_customer_growth_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get customer growth data for area charts."""
        try:
            # Mock data - in production, this would query the database
            months = filters.get("months", 12)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            data_points = []
            current_date = start_date
            customer_count = 50  # Starting customer count
            
            while current_date <= end_date:
                # Simulate customer growth
                import random
                new_customers = random.randint(2, 8)
                customer_count += new_customers
                
                data_points.append({
                    "month": current_date.strftime("%Y-%m"),
                    "customers": customer_count,
                    "new_customers": new_customers
                })
                
                current_date += timedelta(days=30)
            
            return {
                "type": "area_chart",
                "data": data_points,
                "x_axis": "month",
                "y_axis": "customers",
                "metadata": {
                    "total_customers": customer_count,
                    "total_new_customers": sum(p["new_customers"] for p in data_points),
                    "average_monthly_growth": sum(p["new_customers"] for p in data_points) / len(data_points)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get customer growth data: {str(e)}")
            return {"error": str(e)}
    
    async def export_dashboard(
        self,
        dashboard_id: str,
        format: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Export dashboard data in the specified format."""
        try:
            dashboard_data = await self.get_dashboard_data(dashboard_id, filters)
            dashboard = await self.get_dashboard(dashboard_id)
            
            if not dashboard_data or not dashboard:
                return None
            
            if format.lower() == "json":
                export_data = {
                    "dashboard": {
                        "id": dashboard.id,
                        "name": dashboard.name,
                        "description": dashboard.description,
                        "type": dashboard.dashboard_type
                    },
                    "data": dashboard_data,
                    "exported_at": datetime.utcnow().isoformat()
                }
                
                return json.dumps(export_data, indent=2)
            
            elif format.lower() == "csv":
                # Export widget data as CSV
                csv_lines = ["widget_id,data_type,data_points"]
                
                for widget_id, widget_data in dashboard_data.get("widget_data", {}).items():
                    if "data" in widget_data:
                        data_points = widget_data["data"]
                        if isinstance(data_points, list) and data_points:
                            # Export first few data points
                            for i, point in enumerate(data_points[:10]):
                                csv_lines.append(f"{widget_id}_{i},{widget_data.get('type', 'unknown')},{json.dumps(point)}")
                
                return "\n".join(csv_lines)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export dashboard: {str(e)}")
            return None
    
    async def get_dashboard_analytics(self, tenant_id: str) -> Dict[str, Any]:
        """Get analytics about dashboard usage."""
        try:
            dashboards = await self.list_dashboards(tenant_id, size=1000)
            
            # Calculate analytics
            total_dashboards = len(dashboards.dashboards)
            public_dashboards = len([d for d in dashboards.dashboards if d.is_public])
            private_dashboards = total_dashboards - public_dashboards
            
            # Count by type
            type_counts = {}
            for dashboard in dashboards.dashboards:
                dashboard_type = dashboard.dashboard_type
                type_counts[dashboard_type] = type_counts.get(dashboard_type, 0) + 1
            
            # Most common widget types
            widget_types = {}
            for dashboard in dashboards.dashboards:
                for widget in dashboard.widgets:
                    widget_type = widget.get("type", "unknown")
                    widget_types[widget_type] = widget_types.get(widget_type, 0) + 1
            
            return {
                "tenant_id": tenant_id,
                "total_dashboards": total_dashboards,
                "public_dashboards": public_dashboards,
                "private_dashboards": private_dashboards,
                "dashboard_types": type_counts,
                "widget_types": widget_types,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard analytics: {str(e)}")
            return {}


# Global service instance
bi_service = BusinessIntelligenceService()
