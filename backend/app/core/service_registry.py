"""
Service Registry for microservice architecture.
Handles service discovery, health checks, and load balancing.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import json
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    """Service type enumeration."""
    API_GATEWAY = "api_gateway"
    DOCUMENT_PROCESSING = "document_processing"
    AI_CLASSIFICATION = "ai_classification"
    ANALYTICS = "analytics"
    INTEGRATION = "integration"
    EMAIL_PROCESSING = "email_processing"
    DRIVE_MONITORING = "drive_monitoring"
    CALENDAR_SYNC = "calendar_sync"
    ATTENDEE_BOT = "attendee_bot"
    CACHE = "cache"
    QUEUE = "queue"


@dataclass
class ServiceInfo:
    """Service information container."""
    service_id: str
    service_type: ServiceType
    name: str
    version: str
    host: str
    port: int
    health_endpoint: str
    status: ServiceStatus
    last_health_check: datetime
    metadata: Dict[str, Any]
    load_balancer_weight: float = 1.0
    circuit_breaker_failures: int = 0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: timedelta = timedelta(minutes=5)


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, timeout: timedelta = timedelta(minutes=5)):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_failure(self):
        """Record a service failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def record_success(self):
        """Record a service success."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if self.last_failure_time and datetime.utcnow() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def reset(self):
        """Reset the circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"


class ServiceRegistry:
    """Central service registry for microservice architecture."""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.service_types: Dict[ServiceType, List[str]] = {}
        self.health_checkers: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.load_balancers: Dict[ServiceType, List[str]] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the service registry."""
        if self._running:
            return
        
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Service registry started")
    
    async def stop(self):
        """Stop the service registry."""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Service registry stopped")
    
    def register_service(
        self,
        service_id: str,
        service_type: ServiceType,
        name: str,
        version: str,
        host: str,
        port: int,
        health_endpoint: str = "/health",
        metadata: Dict[str, Any] = None,
        load_balancer_weight: float = 1.0
    ) -> ServiceInfo:
        """Register a new service."""
        if service_id in self.services:
            raise ValueError(f"Service {service_id} already registered")
        
        service_info = ServiceInfo(
            service_id=service_id,
            service_type=service_type,
            name=name,
            version=version,
            host=host,
            port=port,
            health_endpoint=health_endpoint,
            status=ServiceStatus.STARTING,
            last_health_check=datetime.utcnow(),
            metadata=metadata or {},
            load_balancer_weight=load_balancer_weight
        )
        
        self.services[service_id] = service_info
        
        # Add to service type index
        if service_type not in self.service_types:
            self.service_types[service_type] = []
        self.service_types[service_type].append(service_id)
        
        # Add to load balancer
        if service_type not in self.load_balancers:
            self.load_balancers[service_type] = []
        self.load_balancers[service_type].append(service_id)
        
        # Initialize circuit breaker
        self.circuit_breakers[service_id] = CircuitBreaker(
            failure_threshold=service_info.circuit_breaker_threshold,
            timeout=service_info.circuit_breaker_timeout
        )
        
        logger.info(f"Service registered: {service_id} ({name} v{version})")
        return service_info
    
    def unregister_service(self, service_id: str) -> bool:
        """Unregister a service."""
        if service_id not in self.services:
            return False
        
        service_info = self.services[service_id]
        
        # Remove from service type index
        if service_info.service_type in self.service_types:
            self.service_types[service_info.service_type].remove(service_id)
            if not self.service_types[service_info.service_type]:
                del self.service_types[service_info.service_type]
        
        # Remove from load balancer
        if service_info.service_type in self.load_balancers:
            self.load_balancers[service_info.service_type].remove(service_id)
            if not self.load_balancers[service_info.service_type]:
                del self.load_balancers[service_info.service_type]
        
        # Remove circuit breaker
        if service_id in self.circuit_breakers:
            del self.circuit_breakers[service_id]
        
        # Remove service
        del self.services[service_id]
        
        logger.info(f"Service unregistered: {service_id}")
        return True
    
    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get service information by ID."""
        return self.services.get(service_id)
    
    def get_services_by_type(self, service_type: ServiceType) -> List[ServiceInfo]:
        """Get all services of a specific type."""
        service_ids = self.service_types.get(service_type, [])
        return [self.services[service_id] for service_id in service_ids if service_id in self.services]
    
    def get_healthy_services_by_type(self, service_type: ServiceType) -> List[ServiceInfo]:
        """Get healthy services of a specific type."""
        services = self.get_services_by_type(service_type)
        return [s for s in services if s.status == ServiceStatus.HEALTHY]
    
    def select_service_for_load_balancing(self, service_type: ServiceType) -> Optional[ServiceInfo]:
        """Select a service for load balancing using weighted round-robin."""
        healthy_services = self.get_healthy_services_by_type(service_type)
        if not healthy_services:
            return None
        
        # Simple weighted round-robin selection
        total_weight = sum(s.load_balancer_weight for s in healthy_services)
        if total_weight == 0:
            return healthy_services[0] if healthy_services else None
        
        # For now, return the first healthy service
        # In a production environment, you'd implement proper weighted round-robin
        return healthy_services[0]
    
    def update_service_status(self, service_id: str, status: ServiceStatus):
        """Update service status."""
        if service_id in self.services:
            self.services[service_id].status = status
            self.services[service_id].last_health_check = datetime.utcnow()
            
            if status == ServiceStatus.HEALTHY:
                self.circuit_breakers[service_id].record_success()
            else:
                self.circuit_breakers[service_id].record_failure()
    
    def register_health_checker(self, service_id: str, checker: Callable):
        """Register a custom health checker for a service."""
        self.health_checkers[service_id] = checker
    
    async def check_service_health(self, service_id: str) -> bool:
        """Check the health of a specific service."""
        if service_id not in self.services:
            return False
        
        service_info = self.services[service_id]
        circuit_breaker = self.circuit_breakers[service_id]
        
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker is open for service {service_id}")
            return False
        
        try:
            # Use custom health checker if available
            if service_id in self.health_checkers:
                is_healthy = await self.health_checkers[service_id](service_info)
            else:
                # Default HTTP health check
                is_healthy = await self._default_health_check(service_info)
            
            if is_healthy:
                self.update_service_status(service_id, ServiceStatus.HEALTHY)
                return True
            else:
                self.update_service_status(service_id, ServiceStatus.UNHEALTHY)
                return False
                
        except Exception as e:
            logger.error(f"Health check failed for service {service_id}: {e}")
            self.update_service_status(service_id, ServiceStatus.UNHEALTHY)
            return False
    
    async def _default_health_check(self, service_info: ServiceInfo) -> bool:
        """Default HTTP health check implementation."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"http://{service_info.host}:{service_info.port}{service_info.health_endpoint}"
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Default health check failed for {service_info.service_id}: {e}")
            return False
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while self._running:
            try:
                # Check all services
                for service_id in list(self.services.keys()):
                    await self.check_service_health(service_id)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get the current status of the service registry."""
        return {
            "total_services": len(self.services),
            "services_by_type": {
                service_type.value: len(services)
                for service_type, services in self.service_types.items()
            },
            "healthy_services": len([s for s in self.services.values() if s.status == ServiceStatus.HEALTHY]),
            "unhealthy_services": len([s for s in self.services.values() if s.status == ServiceStatus.UNHEALTHY]),
            "circuit_breakers": {
                service_id: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
                }
                for service_id, cb in self.circuit_breakers.items()
            }
        }


# Global service registry instance
service_registry = ServiceRegistry()


async def get_service_registry() -> ServiceRegistry:
    """Dependency for getting service registry."""
    return service_registry


async def start_service_registry():
    """Start the service registry."""
    await service_registry.start()


async def stop_service_registry():
    """Stop the service registry."""
    await service_registry.stop()
