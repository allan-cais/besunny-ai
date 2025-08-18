"""
Celery tasks for Gmail watch setup services.
Handles scheduled Gmail webhook setup and management tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .gmail_watch_setup_service import GmailWatchSetupService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="email.gmail_watch_setup_cron")
def gmail_watch_setup_cron(self):
    """Execute Gmail watch setup cron job."""
    try:
        logger.info("Starting Gmail watch setup cron job")
        start_time = datetime.now()
        
        # Create service instance
        service = GmailWatchSetupService()
        
        # Run the cron job
        result = asyncio.run(service.execute_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Gmail watch setup cron completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Gmail watch setup cron failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="email.setup_gmail_watch")
def setup_gmail_watch(self, user_id: str, user_email: str):
    """Set up Gmail watch for a specific user."""
    try:
        logger.info(f"Setting up Gmail watch for user {user_email}")
        start_time = datetime.now()
        
        # Create service instance
        service = GmailWatchSetupService()
        
        # Setup Gmail watch
        result = asyncio.run(service.setup_gmail_watch(user_id, user_email))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Gmail watch setup completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Gmail watch setup failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
