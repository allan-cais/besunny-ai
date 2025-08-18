"""
Celery tasks for drive file subscription services.
Handles scheduled Google Drive file monitoring setup and management tasks.
"""

import asyncio
import logging
from celery import shared_task
from datetime import datetime

from .drive_file_subscription_service import DriveFileSubscriptionService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="drive.file_subscription_cron")
def drive_file_subscription_cron(self):
    """Execute drive file subscription cron job."""
    try:
        logger.info("Starting drive file subscription cron job")
        start_time = datetime.now()
        
        # Create service instance
        service = DriveFileSubscriptionService()
        
        # Run the cron job
        result = asyncio.run(service.execute_cron())
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Drive file subscription cron completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Drive file subscription cron failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="drive.subscribe_to_file")
def subscribe_to_file(self, user_id: str, document_id: str, file_id: str):
    """Subscribe to file changes for a specific document."""
    try:
        logger.info(f"Subscribing to file {file_id} for document {document_id}")
        start_time = datetime.now()
        
        # Create service instance
        service = DriveFileSubscriptionService()
        
        # Subscribe to file
        result = asyncio.run(service.subscribe_to_file(user_id, document_id, file_id))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"File subscription completed in {execution_time:.2f}s")
        
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"File subscription failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
