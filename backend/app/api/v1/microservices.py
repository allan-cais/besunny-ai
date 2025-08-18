"""
Microservice architecture API endpoints.
Provides service registry, API gateway, and observability endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...core.service_registry import get_service_registry, ServiceRegistry, ServiceType
from ...core.api_gateway import get_api_gateway, APIGateway
from ...core.observability import get_observability, ObservabilityManager
from ...core.redis_manager import get_redis, RedisManager

router = APIRouter(prefix="/microservices", tags=["Microservices"])


@router.get("/registry/status")
async def get_service_registry_status(
    registry: ServiceRegistry = Depends(get_service_registry)
) -> Dict[str, Any]:
    """Get the current status of the service registry."""
    return await registry.get_registry_status()


@router.get("/registry/services")
async def get_registered_services(
    service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
    registry: ServiceRegistry = Depends(get_service_registry)
) -> Dict[str, Any]:
    """Get all registered services or filter by type."""
    if service_type:
        services = registry.get_services_by_type(service_type)
        return {
            "service_type": service_type.value,
            "count": len(services),
            "services": [
                {
                    "service_id": s.service_id,
                    "name": s.name,
                    "version": s.version,
                    "status": s.status.value,
                    "host": s.host,
                    "port": s.port,
                    "last_health_check": s.last_health_check.isoformat(),
                    "load_balancer_weight": s.load_balancer_weight
                }
                for s in services
            ]
        }
    else:
        all_services = list(registry.services.values())
        return {
            "total_services": len(all_services),
            "services": [
                {
                    "service_id": s.service_id,
                    "service_type": s.service_type.value,
                    "name": s.name,
                    "version": s.version,
                    "status": s.status.value,
                    "host": s.host,
                    "port": s.port,
                    "last_health_check": s.last_health_check.isoformat()
                }
                for s in all_services
            ]
        }


@router.get("/registry/services/{service_id}")
async def get_service_details(
    service_id: str,
    registry: ServiceRegistry = Depends(get_service_registry)
) -> Dict[str, Any]:
    """Get detailed information about a specific service."""
    service = registry.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {
        "service_id": service.service_id,
        "service_type": service.service_type.value,
        "name": service.name,
        "version": service.version,
        "status": service.status.value,
        "host": service.host,
        "port": service.port,
        "health_endpoint": service.health_endpoint,
        "last_health_check": service.last_health_check.isoformat(),
        "metadata": service.metadata,
        "load_balancer_weight": service.load_balancer_weight
    }


@router.post("/registry/services/{service_id}/health-check")
async def trigger_service_health_check(
    service_id: str,
    registry: ServiceRegistry = Depends(get_service_registry)
) -> Dict[str, Any]:
    """Manually trigger a health check for a specific service."""
    service = registry.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    is_healthy = await registry.check_service_health(service_id)
    
    return {
        "service_id": service_id,
        "health_check_result": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/gateway/status")
async def get_api_gateway_status(
    gateway: APIGateway = Depends(get_api_gateway)
) -> Dict[str, Any]:
    """Get the current status of the API Gateway."""
    return await gateway.get_gateway_status()


@router.get("/gateway/routing-rules")
async def get_gateway_routing_rules(
    gateway: APIGateway = Depends(get_api_gateway)
) -> Dict[str, Any]:
    """Get the current routing rules configured in the API Gateway."""
    return {
        "routing_rules": gateway.routing_rules,
        "total_rules": len(gateway.routing_rules)
    }


@router.get("/observability/health")
async def get_observability_health(
    observability: ObservabilityManager = Depends(get_observability)
) -> Dict[str, Any]:
    """Get the overall health of the observability system."""
    return await observability.get_system_health()


@router.get("/observability/metrics")
async def get_observability_metrics(
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    observability: ObservabilityManager = Depends(get_observability)
) -> Dict[str, Any]:
    """Get collected metrics."""
    if metric_type:
        from ...core.observability import MetricType
        try:
            metric_type_enum = MetricType(metric_type)
            metrics = await observability.metrics.get_metrics_by_type(metric_type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
    else:
        metrics = await observability.metrics.get_metrics()
    
    return {
        "total_metrics": len(metrics),
        "metrics": [
            {
                "name": m.name,
                "value": m.value,
                "type": m.metric_type.value,
                "labels": m.labels,
                "timestamp": m.timestamp.isoformat(),
                "description": m.description
            }
            for m in metrics
        ]
    }


@router.get("/observability/metrics/prometheus")
async def get_metrics_prometheus(
    observability: ObservabilityManager = Depends(get_observability)
) -> str:
    """Get metrics in Prometheus format."""
    return await observability.export_metrics_prometheus()


@router.get("/observability/traces")
async def get_observability_traces(
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    observability: ObservabilityManager = Depends(get_observability)
) -> Dict[str, Any]:
    """Get trace information."""
    if trace_id:
        spans = await observability.traces.get_trace(trace_id)
        return {
            "trace_id": trace_id,
            "spans": [
                {
                    "span_id": s.span_id,
                    "operation_name": s.operation_name,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "tags": s.tags,
                    "logs_count": len(s.logs)
                }
                for s in spans
            ]
        }
    else:
        traces = await observability.traces.get_traces()
        return {
            "total_traces": len(traces),
            "traces": [
                {
                    "trace_id": trace_id,
                    "spans_count": len(spans)
                }
                for trace_id, spans in traces.items()
            ]
        }


@router.get("/observability/logs")
async def get_observability_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    service: Optional[str] = Query(None, description="Filter by service"),
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    observability: ObservabilityManager = Depends(get_observability)
) -> Dict[str, Any]:
    """Get log entries with filtering."""
    from ...core.observability import LogLevel
    
    # Convert level string to enum if provided
    level_enum = None
    if level:
        try:
            level_enum = LogLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid log level: {level}")
    
    logs = await observability.logs.get_logs(
        level=level_enum,
        service=service,
        trace_id=trace_id,
        user_id=user_id,
        limit=limit
    )
    
    return {
        "total_logs": len(logs),
        "logs": [
            {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level.value,
                "message": log.message,
                "service": log.service,
                "trace_id": log.trace_id,
                "span_id": log.span_id,
                "user_id": log.user_id,
                "metadata": log.metadata
            }
            for log in logs
        ]
    }


@router.get("/observability/logs/stats")
async def get_log_statistics(
    observability: ObservabilityManager = Depends(get_observability)
) -> Dict[str, Any]:
    """Get log statistics."""
    return await observability.logs.get_log_stats()


@router.get("/cache/status")
async def get_cache_status(
    redis: RedisManager = Depends(get_redis)
) -> Dict[str, Any]:
    """Get Redis cache status and statistics."""
    try:
        stats = await redis.get_cache_stats()
        health = await redis.health_check()
        
        return {
            "status": "healthy" if health else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "redis_stats": stats,
            "health_check": health
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/cache/keys")
async def get_cache_keys(
    pattern: str = Query("*", description="Redis key pattern"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of keys to return"),
    redis: RedisManager = Depends(get_redis)
) -> Dict[str, Any]:
    """Get cache keys matching a pattern."""
    try:
        # Note: This is a simplified implementation
        # In production, you'd want to implement proper key scanning
        return {
            "pattern": pattern,
            "message": "Key scanning not implemented in this version",
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache keys: {e}")


@router.delete("/cache/keys/{key}")
async def delete_cache_key(
    key: str,
    redis: RedisManager = Depends(get_redis)
) -> Dict[str, Any]:
    """Delete a specific cache key."""
    try:
        success = await redis.delete_cache(key)
        return {
            "key": key,
            "deleted": success,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete cache key: {e}")


@router.post("/cache/clear")
async def clear_cache(
    redis: RedisManager = Depends(get_redis)
) -> Dict[str, Any]:
    """Clear all cache entries."""
    try:
        # Note: This is a simplified implementation
        # In production, you'd want to implement proper cache clearing
        return {
            "message": "Cache clearing not implemented in this version",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")


@router.get("/health/comprehensive")
async def get_comprehensive_health(
    registry: ServiceRegistry = Depends(get_service_registry),
    gateway: APIGateway = Depends(get_api_gateway),
    observability: ObservabilityManager = Depends(get_observability),
    redis: RedisManager = Depends(get_redis)
) -> Dict[str, Any]:
    """Get comprehensive health status of all microservice components."""
    try:
        registry_status = await registry.get_registry_status()
        gateway_status = await gateway.get_gateway_status()
        observability_health = await observability.get_system_health()
        redis_health = await redis.health_check()
        
        # Determine overall health
        overall_status = "healthy"
        if not redis_health:
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "service_registry": registry_status,
                "api_gateway": gateway_status,
                "observability": observability_health,
                "redis_cache": {
                    "status": "healthy" if redis_health else "unhealthy",
                    "health_check": redis_health
                }
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
