"""
Observability system for distributed tracing, metrics collection, and log aggregation.
"""

from typing import Dict, Any, Optional, List
import time
import logging
import structlog
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import asyncio
import json
from dataclasses import dataclass, asdict
from enum import Enum

from .config import get_settings

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str]
    timestamp: datetime
    description: str = ""


@dataclass
class TraceSpan:
    """Trace span data structure."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]


@dataclass
class LogEntry:
    """Log entry data structure."""
    timestamp: datetime
    level: LogLevel
    message: str
    service: str
    trace_id: Optional[str]
    span_id: Optional[str]
    user_id: Optional[str]
    metadata: Dict[str, Any]


class MetricsCollector:
    """Metrics collection and aggregation."""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.summaries: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    async def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        async with self._lock:
            key = self._get_metric_key(name, labels)
            if key not in self.counters:
                self.counters[key] = 0
            self.counters[key] += value
            
            # Update metric
            self.metrics[key] = Metric(
                name=name,
                value=float(self.counters[key]),
                metric_type=MetricType.COUNTER,
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
    
    async def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric."""
        async with self._lock:
            key = self._get_metric_key(name, labels)
            self.gauges[key] = value
            
            # Update metric
            self.metrics[key] = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
    
    async def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value."""
        async with self._lock:
            key = self._get_metric_key(name, labels)
            if key not in self.histograms:
                self.histograms[key] = []
            self.histograms[key].append(value)
            
            # Update metric with current count
            self.metrics[key] = Metric(
                name=name,
                value=len(self.histograms[key]),
                metric_type=MetricType.HISTOGRAM,
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
    
    async def record_summary(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a summary value."""
        async with self._lock:
            key = self._get_metric_key(name, labels)
            if key not in self.summaries:
                self.summaries[key] = []
            self.summaries[key].append(value)
            
            # Update metric with current count
            self.metrics[key] = Metric(
                name=name,
                value=len(self.summaries[key]),
                metric_type=MetricType.SUMMARY,
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
    
    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Generate metric key from name and labels."""
        if not labels:
            return name
        
        label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{name}[{label_str}]"
    
    async def get_metrics(self) -> List[Metric]:
        """Get all current metrics."""
        async with self._lock:
            return list(self.metrics.values())
    
    async def get_metrics_by_type(self, metric_type: MetricType) -> List[Metric]:
        """Get metrics by type."""
        async with self._lock:
            return [m for m in self.metrics.values() if m.metric_type == metric_type]
    
    async def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[Metric]:
        """Get a specific metric."""
        key = self._get_metric_key(name, labels)
        return self.metrics.get(key)
    
    async def reset_metrics(self):
        """Reset all metrics."""
        async with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.summaries.clear()


class TraceCollector:
    """Distributed tracing collection."""
    
    def __init__(self):
        self.traces: Dict[str, List[TraceSpan]] = {}
        self.spans: Dict[str, TraceSpan] = {}
        self._lock = asyncio.Lock()
    
    async def start_span(
        self, 
        trace_id: str, 
        span_id: str, 
        operation_name: str, 
        parent_span_id: Optional[str] = None,
        tags: Dict[str, Any] = None
    ) -> TraceSpan:
        """Start a new trace span."""
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            end_time=None,
            tags=tags or {},
            logs=[]
        )
        
        async with self._lock:
            self.spans[span_id] = span
            
            if trace_id not in self.traces:
                self.traces[trace_id] = []
            self.traces[trace_id].append(span)
        
        return span
    
    async def end_span(self, span_id: str, tags: Dict[str, Any] = None):
        """End a trace span."""
        async with self._lock:
            if span_id in self.spans:
                span = self.spans[span_id]
                span.end_time = datetime.utcnow()
                if tags:
                    span.tags.update(tags)
    
    async def add_span_log(self, span_id: str, message: str, metadata: Dict[str, Any] = None):
        """Add a log entry to a span."""
        async with self._lock:
            if span_id in self.spans:
                span = self.spans[span_id]
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": message,
                    "metadata": metadata or {}
                }
                span.logs.append(log_entry)
    
    async def add_span_tag(self, span_id: str, key: str, value: Any):
        """Add a tag to a span."""
        async with self._lock:
            if span_id in self.spans:
                span = self.spans[span_id]
                span.tags[key] = value
    
    async def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace."""
        return self.traces.get(trace_id, [])
    
    async def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """Get a specific span."""
        return self.spans.get(span_id)
    
    async def get_traces(self) -> Dict[str, List[TraceSpan]]:
        """Get all traces."""
        return self.traces.copy()


class LogAggregator:
    """Log aggregation and management."""
    
    def __init__(self):
        self.logs: List[LogEntry] = []
        self._lock = asyncio.Lock()
        self._max_logs = 10000  # Keep last 10k logs in memory
    
    async def add_log(
        self,
        level: LogLevel,
        message: str,
        service: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Add a log entry."""
        log_entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            service=service,
            trace_id=trace_id,
            span_id=span_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        async with self._lock:
            self.logs.append(log_entry)
            
            # Keep only the last max_logs entries
            if len(self.logs) > self._max_logs:
                self.logs = self.logs[-self._max_logs:]
    
    async def get_logs(
        self,
        level: Optional[LogLevel] = None,
        service: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Get filtered logs."""
        async with self._lock:
            filtered_logs = self.logs
            
            if level:
                filtered_logs = [log for log in filtered_logs if log.level == level]
            
            if service:
                filtered_logs = [log for log in filtered_logs if log.service == service]
            
            if trace_id:
                filtered_logs = [log for log in filtered_logs if log.trace_id == trace_id]
            
            if user_id:
                filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
            
            if since:
                filtered_logs = [log for log in filtered_logs if log.timestamp >= since]
            
            # Return most recent logs first
            return sorted(filtered_logs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    async def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics."""
        async with self._lock:
            if not self.logs:
                return {}
            
            levels = {}
            services = {}
            
            for log in self.logs:
                levels[log.level] = levels.get(log.level, 0) + 1
                services[log.service] = services.get(log.service, 0) + 1
            
            return {
                "total_logs": len(self.logs),
                "logs_by_level": levels,
                "logs_by_service": services,
                "oldest_log": min(log.timestamp for log in self.logs).isoformat(),
                "newest_log": max(log.timestamp for log in self.logs).isoformat()
            }


class ObservabilityManager:
    """Main observability manager."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.traces = TraceCollector()
        self.logs = LogAggregator()
        self.settings = get_settings()
        self._initialized = False
    
    async def initialize(self):
        """Initialize observability system."""
        if self._initialized:
            return
        
        # Configure structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self._initialized = True
        logger.info("Observability system initialized")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_metrics": len(await self.metrics.get_metrics()),
                "total_traces": len(self.traces.traces),
                "total_logs": len(self.logs.logs)
            },
            "components": {
                "metrics_collector": "healthy",
                "trace_collector": "healthy",
                "log_aggregator": "healthy"
            }
        }
    
    async def export_metrics_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        metrics = await self.metrics.get_metrics()
        prometheus_lines = []
        
        for metric in metrics:
            # Format labels
            labels_str = ""
            if metric.labels:
                labels_str = "{" + ",".join([f'{k}="{v}"' for k, v in metric.labels.items()]) + "}"
            
            # Add metric description as comment
            if metric.description:
                prometheus_lines.append(f"# HELP {metric.name} {metric.description}")
            
            # Add metric value
            prometheus_lines.append(f"{metric.name}{labels_str} {metric.value}")
        
        return "\n".join(prometheus_lines)


# Global observability manager instance
observability_manager = ObservabilityManager()


async def get_observability() -> ObservabilityManager:
    """Dependency for getting observability manager."""
    return observability_manager


async def init_observability() -> None:
    """Initialize observability on startup."""
    await observability_manager.initialize()


# Tracing decorator
def trace_operation(operation_name: str = None):
    """Decorator for tracing function operations."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate trace and span IDs
            import uuid
            trace_id = str(uuid.uuid4())
            span_id = str(uuid.uuid4())
            
            # Get operation name
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Start span
            observability = await get_observability()
            span = await observability.traces.start_span(
                trace_id=trace_id,
                span_id=span_id,
                operation_name=op_name,
                tags={
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs)
                }
            )
            
            try:
                # Execute function
                start_time = time.time()
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Add execution time tag
                await observability.traces.add_span_tag(span_id, "execution_time_ms", execution_time * 1000)
                
                # End span
                await observability.traces.end_span(span_id, {"status": "success"})
                
                return result
                
            except Exception as e:
                # Add error information
                await observability.traces.add_span_tag(span_id, "status", "error")
                await observability.traces.add_span_tag(span_id, "error", str(e))
                await observability.traces.add_span_tag(span_id, "error_type", type(e).__name__)
                
                # End span
                await observability.traces.end_span(span_id)
                
                # Re-raise exception
                raise
        
        return wrapper
    return decorator


# Metrics decorator
def record_metric(metric_name: str, metric_type: MetricType = MetricType.COUNTER, labels: Dict[str, str] = None):
    """Decorator for recording metrics."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            observability = await get_observability()
            
            try:
                # Execute function
                start_time = time.time()
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record metrics
                if metric_type == MetricType.COUNTER:
                    await observability.metrics.increment_counter(metric_name, 1, labels)
                elif metric_type == MetricType.GAUGE:
                    await observability.metrics.set_gauge(metric_name, execution_time * 1000, labels)
                elif metric_type == MetricType.HISTOGRAM:
                    await observability.metrics.record_histogram(metric_name, execution_time * 1000, labels)
                
                return result
                
            except Exception as e:
                # Record error metric
                error_labels = (labels or {}).copy()
                error_labels["status"] = "error"
                await observability.metrics.increment_counter(f"{metric_name}_errors", 1, error_labels)
                raise
        
        return wrapper
    return decorator
