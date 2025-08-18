"""
Minimal service registry module for testing imports
"""

import logging

logger = logging.getLogger(__name__)

async def start_service_registry():
    """Start service registry."""
    logger.info("Service registry startup - minimal implementation")
    return True

async def stop_service_registry():
    """Stop service registry."""
    logger.info("Service registry shutdown - minimal implementation")
    return True
