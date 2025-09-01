"""
Celery tasks for calendar services.
Handles scheduled calendar synchronization and maintenance tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .calendar_polling_cron import CalendarPollingCronService
from .calendar_watch_renewal_service import CalendarWatchRenewalService
from .calendar_webhook_renewal_service import CalendarWebhookRenewalService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="calendar.polling_cron")
def calendar_polling_cron(self):
    """Execute calendar polling cron job."""
    try:
        logger.info("Starting calendar polling cron job")
        start_time = datetime.now()
        
        # Create service instance
        service = CalendarPollingCronService()
        
        # Run the cron job
        result = asyncio.run(service.execute_polling_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Calendar polling cron completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Calendar polling cron failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="calendar.renew_watches")
def renew_calendar_watches(self):
    """Renew expired calendar watches."""
    try:
        logger.info("Starting calendar watch renewal")
        start_time = datetime.now()
        
        # Create service instance
        service = CalendarWatchRenewalService()
        
        # Run the renewal cron job
        result = asyncio.run(service.execute_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Calendar watch renewal completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Calendar watch renewal failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="calendar.renew_webhooks")
def renew_calendar_webhooks(self):
    """Renew expired calendar webhooks."""
    try:
        logger.info("Starting calendar webhook renewal")
        start_time = datetime.now()
        
        # Create service instance
        service = CalendarWebhookRenewalService()
        
        # Run the renewal cron job
        result = asyncio.run(service.execute_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Calendar webhook renewal completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Calendar webhook renewal failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="calendar.sync_events")
def sync_calendar_events(self, user_id: str = None):
    """Sync calendar events for a specific user or all users."""
    try:
        logger.info(f"Starting calendar sync for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = CalendarPollingCronService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.poll_all_active_calendars_for_user(user_id))
        else:
            # Sync all users
            result = asyncio.run(service.poll_all_active_calendars())
        
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
