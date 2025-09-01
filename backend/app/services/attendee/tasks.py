"""
Celery tasks for attendee services.
Handles scheduled meeting polling and bot management tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .attendee_polling_cron import AttendeePollingCron

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="attendee.polling_cron")
def attendee_polling_cron(self):
    """Execute attendee polling cron job."""
    try:
        logger.info("Starting attendee polling cron job")
        start_time = datetime.now()
        
        # Create service instance
        service = AttendeePollingCron()
        
        # Run the cron job
        result = asyncio.run(service.execute_polling_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Attendee polling cron completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Attendee polling cron failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="attendee.poll_meetings")
def poll_all_meetings(self, user_id: str = None):
    """Poll all meetings for a specific user or all users."""
    try:
        logger.info(f"Starting meeting polling for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = AttendeePollingCron()
        
        if user_id:
            # Poll specific user
            result = asyncio.run(service.poll_all_user_meetings(user_id))
        else:
            # Poll all users
            result = asyncio.run(service.poll_all_active_meetings())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Meeting polling completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Meeting polling failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="attendee.auto_schedule_bots")
def auto_schedule_bots(self, user_id: str = None):
    """Auto-schedule bots for meetings."""
    try:
        logger.info(f"Starting auto-schedule bots for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = AttendeePollingCron()
        
        if user_id:
            # Auto-schedule for specific user
            result = asyncio.run(service.auto_schedule_user_bots(user_id))
        else:
            # Auto-schedule for all users
            result = asyncio.run(service.auto_schedule_all_bots())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Auto-schedule bots completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Auto-schedule bots failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="attendee.cleanup_completed_meetings")
def cleanup_completed_meetings(self):
    """Clean up completed meetings and transcripts."""
    try:
        logger.info("Starting cleanup of completed meetings")
        start_time = datetime.now()
        
        # Create service instance
        service = AttendeePollingCron()
        
        # Run cleanup
        result = asyncio.run(service.cleanup_completed_meetings())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Meeting cleanup completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Meeting cleanup failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
