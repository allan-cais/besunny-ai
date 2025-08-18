"""
Minimal service registry module for testing imports
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Service types enum
class ServiceType(str, Enum):
    """Service type enumeration."""
    AI = "ai"
    EMAIL = "email"
    DRIVE = "drive"
    CALENDAR = "calendar"
    ATTENDEE = "attendee"
    SYNC = "sync"

class ServiceRegistry:
    """Service registry for managing microservices."""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self._initialized = False
    
    async def start(self):
        """Start the service registry."""
        self._initialized = True
        logger.info("Service registry started")
    
    async def stop(self):
        """Stop the service registry."""
        self._initialized = False
        logger.info("Service registry stopped")
    
    def register_service(self, name: str, service: Any, service_type: ServiceType):
        """Register a service."""
        self.services[name] = {"service": service, "type": service_type}
        logger.info(f"Registered service: {name} ({service_type})")
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name."""
        return self.services.get(name, {}).get("service") if name in self.services else None

# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None

def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry

async def start_service_registry():
    """Start service registry."""
    registry = get_service_registry()
    await registry.start()
    logger.info("Service registry startup - minimal implementation")
    return True

async def stop_service_registry():
    """Stop service registry."""
    registry = get_service_registry()
    await registry.stop()
    logger.info("Service registry shutdown - minimal implementation")
    return True
