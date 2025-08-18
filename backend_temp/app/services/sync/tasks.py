"""
Celery tasks for sync services.
Handles scheduled synchronization and maintenance tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .enhanced_adaptive_sync_service import EnhancedAdaptiveSyncService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="sync.all_services")
def sync_all_services(self, user_id: str = None, force_sync: bool = False):
    """Sync all services for a specific user or all users."""
    try:
        logger.info(f"Starting sync all services for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = EnhancedAdaptiveSyncService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.sync_all_services(user_id, force_sync))
        else:
            # Sync all users
            result = asyncio.run(service.sync_all_users())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Sync all services completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sync all services failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="sync.calendar")
def sync_calendar(self, user_id: str = None, force_sync: bool = False):
    """Sync calendar for a specific user or all users."""
    try:
        logger.info(f"Starting calendar sync for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = EnhancedAdaptiveSyncService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.sync_calendar(user_id, force_sync))
        else:
            # Sync all users
            result = asyncio.run(service.sync_all_calendars())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Calendar sync completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="sync.drive")
def sync_drive(self, user_id: str = None, force_sync: bool = False):
    """Sync drive for a specific user or all users."""
    try:
        logger.info(f"Starting drive sync for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = EnhancedAdaptiveSyncService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.sync_drive(user_id, force_sync))
        else:
            # Sync all users
            result = asyncio.run(service.sync_all_drives())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Drive sync completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Drive sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="sync.gmail")
def sync_gmail(self, user_id: str = None, force_sync: bool = False):
    """Sync Gmail for a specific user or all users."""
    try:
        logger.info(f"Starting Gmail sync for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = EnhancedAdaptiveSyncService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.sync_gmail(user_id, force_sync))
        else:
            # Sync all users
            result = asyncio.run(service.sync_all_gmails())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Gmail sync completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Gmail sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="sync.attendee")
def sync_attendee(self, user_id: str = None, force_sync: bool = False):
    """Sync attendee for a specific user or all users."""
    try:
        logger.info(f"Starting attendee sync for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = EnhancedAdaptiveSyncService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.sync_attendee(user_id, force_sync))
        else:
            # Sync all users
            result = asyncio.run(service.sync_all_attendees())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Attendee sync completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Attendee sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="sync.optimize_intervals")
def optimize_sync_intervals(self):
    """Optimize sync intervals based on user activity patterns."""
    try:
        logger.info("Starting sync interval optimization")
        start_time = datetime.now()
        
        # Create service instance
        service = EnhancedAdaptiveSyncService()
        
        # Optimize intervals
        result = asyncio.run(service.optimize_all_sync_intervals())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Sync interval optimization completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sync interval optimization failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
