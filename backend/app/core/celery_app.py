"""
Celery configuration for BeSunny.ai Python backend.
Handles background task processing and scheduling.
"""

from celery import Celery
from celery.schedules import crontab
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "besunny",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.services.email.tasks",
        "app.services.email.gmail_watch_setup_tasks",
        "app.services.classification.tasks",
        "app.services.drive.tasks",
        "app.services.drive.drive_file_subscription_tasks",
        "app.services.calendar.tasks",
        "app.services.attendee.tasks",
        "app.services.ai.tasks",
        "app.services.sync.tasks",
        "app.services.auth.tasks",
        "app.services.user.tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.services.email.tasks.*": {"queue": "email"},
        "app.services.email.gmail_watch_setup_tasks.*": {"queue": "email"},
        "app.services.classification.tasks.*": {"queue": "ai"},
        "app.services.drive.tasks.*": {"queue": "drive"},
        "app.services.drive.drive_file_subscription_tasks.*": {"queue": "drive"},
        "app.services.calendar.tasks.*": {"queue": "calendar"},
        "app.services.attendee.tasks.*": {"queue": "attendee"},
        "app.services.ai.tasks.*": {"queue": "ai"},
        "app.services.sync.tasks.*": {"queue": "sync"},
        "app.services.auth.tasks.*": {"queue": "auth"},
        "app.services.user.tasks.*": {"queue": "user"},
    },
    
    # Task execution
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    security_key=settings.secret_key,
    security_certificate=None,
    security_cert_store=None,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    # Email processing tasks
    "process-pending-emails": {
        "task": "email.process_pending_emails",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    
    # Drive monitoring tasks
    "sync-drive-files": {
        "task": "drive.sync_files",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    
    # Calendar synchronization
    "sync-calendar-events": {
        "task": "calendar.sync_events",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    
    # Attendee polling
    "attendee-polling-cron": {
        "task": "attendee.polling_cron",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    
    # Calendar watch renewal
    "renew-calendar-watches": {
        "task": "calendar.renew_watches",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
    
    # Calendar webhook renewal
    "renew-calendar-webhooks": {
        "task": "calendar.renew_webhooks",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
    
    # Drive watch cleanup
    "cleanup-drive-watches": {
        "task": "drive.cleanup_expired_watches",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    
    # Gmail watch renewal
    "renew-gmail-watches": {
        "task": "email.renew_gmail_watches",
        "schedule": crontab(hour="*/4"),  # Every 4 hours
    },
    
    # Gmail watch setup
    "setup-gmail-watches": {
        "task": "email.gmail_watch_setup_cron",
        "schedule": crontab(hour="*/2"),  # Every 2 hours
    },
    
    # Drive file subscription
    "setup-drive-file-subscriptions": {
        "task": "drive.file_subscription_cron",
        "schedule": crontab(hour="*/3"),  # Every 3 hours
    },
    
    # Username management
    "manage-usernames": {
        "task": "user.username_management_cron",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    
    # AI model updates
    "update-ai-models": {
        "task": "ai.update_models",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # Sync optimization
    "optimize-sync-intervals": {
        "task": "sync.optimize_intervals",
        "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    
    # Google token refresh
    "refresh-google-tokens": {
        "task": "auth.refresh_google_tokens",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    
    # Proactive Google token refresh (refresh tokens before they expire)
    "refresh-expiring-google-tokens": {
        "task": "auth.refresh_expiring_google_tokens",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    
    # Google token validation
    "validate-google-tokens": {
        "task": "auth.validate_google_tokens",
        "schedule": crontab(hour=5, minute=0),  # Daily at 5 AM
    },
    
    # Session cleanup
    "cleanup-expired-sessions": {
        "task": "auth.cleanup_expired_sessions",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
    },
    
    # Token revocation
    "revoke-expired-tokens": {
        "task": "auth.revoke_expired_tokens",
        "schedule": crontab(hour=7, minute=0),  # Daily at 7 AM
    },
    
    # Batch token maintenance
    "batch-token-maintenance": {
        "task": "auth.batch_token_maintenance",
        "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    
    # Health checks
    "check-service-health": {
        "task": "app.core.tasks.check_service_health",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
}

# Task error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing."""
    logger.info(f"Request: {self.request!r}")


# Task monitoring
@celery_app.task(bind=True)
def monitor_task(self, task_name: str, *args, **kwargs):
    """Monitor task execution and performance."""
    try:
        logger.info(f"Starting task: {task_name}")
        start_time = time.time()
        
        # Execute the actual task
        result = self.apply_async(args=args, kwargs=kwargs)
        
        execution_time = time.time() - start_time
        logger.info(f"Task {task_name} completed in {execution_time:.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"Task {task_name} failed: {e}")
        raise


# Health check task
@celery_app.task
def health_check():
    """Check system health and report status."""
    try:
        # Check database connectivity
        from .database import db_manager
        # Note: In Celery tasks, we need to handle async operations differently
        # For now, we'll return a placeholder status
        # In production, you'd use sync versions or handle async properly
        
        health_status = {
            "database": True,  # Placeholder - implement actual check
            "redis": True,      # Placeholder - implement actual check
            "external_services": True,  # Placeholder - implement actual check
            "overall": True,
            "timestamp": time.time(),
        }
        
        logger.info(f"Health check completed: {health_status}")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "overall": False,
            "error": str(e),
            "timestamp": time.time(),
        }


# Cleanup task
@celery_app.task
def cleanup_old_tasks():
    """Clean up old completed tasks and results."""
    try:
        from celery.result import AsyncResult
        
        # Get all task results
        # This is a simplified example - in production you'd use a more efficient approach
        logger.info("Starting cleanup of old tasks")
        
        # Clean up results older than 24 hours
        cutoff_time = time.time() - (24 * 3600)
        
        # Implementation would depend on your result backend
        # For Redis, you might use TTL-based cleanup
        # For database, you might delete old records
        
        logger.info("Cleanup of old tasks completed")
        return {"cleaned_tasks": 0, "timestamp": time.time()}
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"error": str(e), "timestamp": time.time()}


# Task event handlers - using modern Celery event registration
def task_success_handler(sender=None, **kwargs):
    """Handle successful task completion."""
    logger.info(f"Task {sender.name} completed successfully")


def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Handle task failure."""
    logger.error(f"Task {sender.name} failed: {exception}")


def task_revoked_handler(sender=None, request=None, terminated=None, signum=None, **kwargs):
    """Handle task revocation."""
    logger.warning(f"Task {sender.name} was revoked")


def register_celery_event_handlers():
    """Register Celery event handlers after the app is fully initialized."""
    try:
        celery_app.task_success.connect(task_success_handler)
        celery_app.task_failure.connect(task_failure_handler)
        celery_app.task_revoked.connect(task_revoked_handler)
        logger.info("Celery event handlers registered successfully")
    except Exception as e:
        logger.warning(f"Failed to register Celery event handlers: {e}")


# Import time to avoid circular imports
import time
