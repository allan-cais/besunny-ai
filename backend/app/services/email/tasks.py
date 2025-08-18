"""
Celery tasks for email services.
Handles scheduled email processing and maintenance tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .gmail_polling_cron import GmailPollingCronService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="email.polling_cron")
def gmail_polling_cron(self):
    """Execute Gmail polling cron job."""
    try:
        logger.info("Starting Gmail polling cron job")
        start_time = datetime.now()
        
        # Create service instance
        service = GmailPollingCronService()
        
        # Run the cron job
        result = asyncio.run(service.execute_polling_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Gmail polling cron completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Gmail polling cron failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="email.process_pending_emails")
def process_pending_emails(self):
    """Process pending emails for all users."""
    try:
        logger.info("Starting pending email processing")
        start_time = datetime.now()
        
        # Create service instance
        service = GmailPollingCronService()
        
        # Process pending emails
        result = asyncio.run(service.process_pending_emails())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Pending email processing completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pending email processing failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="email.sync_gmail")
def sync_gmail(self, user_id: str = None):
    """Sync Gmail for a specific user or all users."""
    try:
        logger.info(f"Starting Gmail sync for user: {user_id or 'all'}")
        start_time = datetime.now()
        
        # Create service instance
        service = GmailPollingCronService()
        
        if user_id:
            # Sync specific user
            result = asyncio.run(service.poll_all_active_gmail_accounts_for_user(user_id))
        else:
            # Sync all users
            result = asyncio.run(service.poll_all_active_gmail_accounts())
        
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


@shared_task(bind=True, name="email.renew_gmail_watches")
def renew_gmail_watches(self):
    """Renew expired Gmail watches."""
    try:
        logger.info("Starting Gmail watch renewal")
        start_time = datetime.now()
        
        # Create service instance
        service = GmailPollingCronService()
        
        # Renew watches
        result = asyncio.run(service.renew_expired_watches())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Gmail watch renewal completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Gmail watch renewal failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
