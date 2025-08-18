"""
Celery tasks for user services.
Handles scheduled username management and virtual email setup tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .username_service import UsernameService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="user.username_management_cron")
def username_management_cron(self):
    """Execute username management cron job."""
    try:
        logger.info("Starting username management cron job")
        start_time = datetime.now()
        
        # Create service instance
        service = UsernameService()
        
        # Run the cron job
        result = asyncio.run(service.execute_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Username management cron completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Username management cron failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="user.set_username")
def set_username(self, user_id: str, username: str):
    """Set username for a specific user."""
    try:
        logger.info(f"Setting username '{username}' for user {user_id}")
        start_time = datetime.now()
        
        # Create service instance
        service = UsernameService()
        
        # Set username
        result = asyncio.run(service.set_username(user_id, username))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Username setting completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Username setting failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
