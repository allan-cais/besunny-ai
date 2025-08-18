"""
Performance Monitoring Service for BeSunny.ai Python backend.
Tracks system performance, user activity, and provides optimization insights.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import psutil
import json

from ...core.config import get_settings

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Performance metrics data structure."""
    
    def __init__(self, timestamp: Optional[datetime] = None):
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.disk_usage_percent = 0.0
        self.network_io = {"bytes_sent": 0, "bytes_recv": 0}
        self.active_connections = 0
        self.request_count = 0
        self.average_response_time = 0.0
        self.error_rate = 0.0


class UserActivityMetrics:
    """User activity metrics data structure."""
    
    def __init__(self, user_id: str, timestamp: Optional[datetime] = None):
        self.user_id = user_id
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.api_calls = 0
        self.workflows_executed = 0
        self.data_processed = 0
        self.session_duration = 0
        self.features_used = []


class SystemHealthReport:
    """System health report data structure."""
    
    def __init__(self, timestamp: Optional[datetime] = None):
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.overall_health = "healthy"  # healthy, warning, critical
        self.cpu_health = "healthy"
        self.memory_health = "healthy"
        self.disk_health = "healthy"
        self.network_health = "healthy"
        self.recommendations = []
        self.alerts = []


class PerformanceMonitoringService:
    """Service for monitoring system performance and user activity."""
    
    def __init__(self):
        self.settings = get_settings()
        self._initialized = False
        self._metrics_history = []
        self._user_activity = {}
        self._monitoring_task = None
        self._alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'error_rate': 5.0
        }
        
        logger.info("Performance Monitoring Service initialized")
    
    async def initialize(self):
        """Initialize the performance monitoring service."""
        if self._initialized:
            return
        
        try:
            # Start background monitoring
            self._monitoring_task = asyncio.create_task(self._monitor_performance())
            
            self._initialized = True
            logger.info("Performance Monitoring Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Performance Monitoring Service: {e}")
            raise
    
    async def _monitor_performance(self):
        """Background task for monitoring system performance."""
        while True:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                
                # Store metrics in history
                self._metrics_history.append(metrics)
                
                # Keep only last 1000 metrics
                if len(self._metrics_history) > 1000:
                    self._metrics_history = self._metrics_history[-1000:]
                
                # Check for alerts
                alerts = await self._check_alerts(metrics)
                if alerts:
                    await self._send_alerts(alerts)
                
                # Wait before next collection
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Performance monitoring failed: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        try:
            metrics = PerformanceMetrics()
            
            # CPU usage
            metrics.cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics.memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics.disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics.network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            }
            
            # Active connections (estimate)
            try:
                connections = psutil.net_connections()
                metrics.active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            except:
                metrics.active_connections = 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return PerformanceMetrics()
    
    async def _check_alerts(self, metrics: PerformanceMetrics) -> List[str]:
        """Check if any metrics exceed alert thresholds."""
        alerts = []
        
        if metrics.cpu_percent > self._alert_thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self._alert_thresholds['memory_percent']:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_usage_percent > self._alert_thresholds['disk_usage_percent']:
            alerts.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")
        
        return alerts
    
    async def _send_alerts(self, alerts: List[str]):
        """Send performance alerts."""
        for alert in alerts:
            logger.warning(f"PERFORMANCE ALERT: {alert}")
            # In a full implementation, this would send notifications
            # via email, Slack, or other channels
    
    async def get_current_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics."""
        if not self._initialized:
            await self.initialize()
        
        return await self._collect_system_metrics()
    
    async def get_metrics_history(self, hours: int = 24) -> List[PerformanceMetrics]:
        """Get performance metrics history for the specified time period."""
        if not self._initialized:
            await self.initialize()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            metrics for metrics in self._metrics_history
            if metrics.timestamp > cutoff_time
        ]
    
    async def get_system_health(self) -> SystemHealthReport:
        """Get current system health report."""
        if not self._initialized:
            await self.initialize()
        
        current_metrics = await self._collect_system_metrics()
        
        report = SystemHealthReport()
        
        # Assess CPU health
        if current_metrics.cpu_percent < 50:
            report.cpu_health = "healthy"
        elif current_metrics.cpu_percent < 80:
            report.cpu_health = "warning"
        else:
            report.cpu_health = "critical"
        
        # Assess memory health
        if current_metrics.memory_percent < 70:
            report.memory_health = "healthy"
        elif current_metrics.memory_percent < 85:
            report.memory_health = "warning"
        else:
            report.memory_health = "critical"
        
        # Assess disk health
        if current_metrics.disk_usage_percent < 80:
            report.disk_health = "healthy"
        elif current_metrics.disk_usage_percent < 90:
            report.disk_health = "warning"
        else:
            report.disk_health = "critical"
        
        # Overall health assessment
        if any(health == "critical" for health in [report.cpu_health, report.memory_health, report.disk_health]):
            report.overall_health = "critical"
        elif any(health == "warning" for health in [report.cpu_health, report.memory_health, report.disk_health]):
            report.overall_health = "warning"
        else:
            report.overall_health = "healthy"
        
        # Generate recommendations
        if report.cpu_health == "warning":
            report.recommendations.append("Consider scaling CPU resources or optimizing CPU-intensive operations")
        
        if report.memory_health == "warning":
            report.recommendations.append("Monitor memory usage and consider memory optimization or scaling")
        
        if report.disk_health == "warning":
            report.recommendations.append("Consider disk cleanup or storage expansion")
        
        return report
    
    async def track_user_activity(self, user_id: str, activity_type: str, metadata: Dict[str, Any] = None):
        """Track user activity for analytics."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if user_id not in self._user_activity:
                self._user_activity[user_id] = UserActivityMetrics(user_id)
            
            user_metrics = self._user_activity[user_id]
            
            if activity_type == "api_call":
                user_metrics.api_calls += 1
            elif activity_type == "workflow_execution":
                user_metrics.workflows_executed += 1
            elif activity_type == "feature_usage":
                feature = metadata.get('feature', 'unknown')
                if feature not in user_metrics.features_used:
                    user_metrics.features_used.append(feature)
            
            # Update timestamp
            user_metrics.timestamp = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
    
    async def get_user_activity_summary(self, user_id: str) -> Optional[UserActivityMetrics]:
        """Get activity summary for a specific user."""
        if not self._initialized:
            await self.initialize()
        
        return self._user_activity.get(user_id)
    
    async def get_system_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance summary for the specified time period."""
        if not self._initialized:
            await self.initialize()
        
        metrics_history = await self._get_metrics_history(hours)
        
        if not metrics_history:
            return {}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in metrics_history) / len(metrics_history)
        avg_memory = sum(m.memory_percent for m in metrics_history) / len(metrics_history)
        avg_disk = sum(m.disk_usage_percent for m in metrics_history) / len(metrics_history)
        
        # Find peak values
        peak_cpu = max(m.cpu_percent for m in metrics_history)
        peak_memory = max(m.memory_percent for m in metrics_history)
        peak_disk = max(m.disk_usage_percent for m in metrics_history)
        
        return {
            "time_period_hours": hours,
            "metrics_count": len(metrics_history),
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_percent": round(avg_memory, 2),
                "disk_usage_percent": round(avg_disk, 2)
            },
            "peaks": {
                "cpu_percent": round(peak_cpu, 2),
                "memory_percent": round(peak_memory, 2),
                "disk_usage_percent": round(peak_disk, 2)
            },
            "current_status": await self.get_system_health()
        }
    
    async def optimize_system_performance(self) -> Dict[str, Any]:
        """Provide system performance optimization recommendations."""
        if not self._initialized:
            await self.initialize()
        
        current_metrics = await self._collect_system_metrics()
        health_report = await self.get_system_health()
        
        optimization = {
            "timestamp": datetime.now().isoformat(),
            "current_health": health_report.overall_health,
            "recommendations": health_report.recommendations,
            "immediate_actions": [],
            "long_term_actions": []
        }
        
        # Immediate actions based on current metrics
        if current_metrics.cpu_percent > 90:
            optimization["immediate_actions"].append("Scale CPU resources immediately")
        
        if current_metrics.memory_percent > 90:
            optimization["immediate_actions"].append("Scale memory resources immediately")
        
        if current_metrics.disk_usage_percent > 95:
            optimization["immediate_actions"].append("Free up disk space immediately")
        
        # Long-term optimization recommendations
        if current_metrics.cpu_percent > 70:
            optimization["long_term_actions"].append("Implement CPU optimization strategies")
        
        if current_metrics.memory_percent > 80:
            optimization["long_term_actions"].append("Implement memory optimization strategies")
        
        return optimization
    
    async def shutdown(self):
        """Shutdown the performance monitoring service."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self._initialized = False
        logger.info("Performance Monitoring Service shutdown")
