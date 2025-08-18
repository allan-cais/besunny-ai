"""
Celery tasks for drive services.
Handles scheduled drive synchronization and maintenance tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .drive_polling_cron import DrivePollingCronService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="drive.polling_cron")
def drive_polling_cron(self):
    """Execute drive polling cron job."""
    try:
        logger.info("Starting drive polling cron job")
        start_time = datetime.now()
        
        # Create service instance
        service = DrivePollingCronService()
        
        # Run the cron job
        result = asyncio.run(service.execute_polling_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Drive polling cron completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Drive polling cron failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="drive.sync_files")
def sync_drive_files(self, user_id: str = None):
    """Sync drive files for a specific user or all users."""
    try:
        logger.info(f"Starting drive sync for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = DrivePollingCronService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.poll_all_active_files_for_user(user_id))
        else:
            # Sync all users
            result = asyncio.run(service.poll_all_active_files())
        
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


@shared_task(bind=True, name="drive.cleanup_expired_watches")
def cleanup_expired_drive_watches(self):
    """Clean up expired drive file watches."""
    try:
        logger.info("Starting drive watch cleanup")
        start_time = datetime.now()
        
        # Create service instance
        service = DrivePollingCronService()
        
        # Run the cleanup
        result = asyncio.run(service.cleanup_expired_watches())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Drive watch cleanup completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Drive watch cleanup failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
