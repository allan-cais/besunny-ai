"""
Gmail Watch Scheduler Service
Automatically refreshes Gmail watch before expiration to prevent webhook failures.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .gmail_service import GmailService
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class GmailWatchScheduler:
    """Scheduler for automatic Gmail watch refresh."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.gmail_service = GmailService()
        self.settings = get_settings()
        self.is_running = False
        
    async def start(self):
        """Start the Gmail watch scheduler."""
        try:
            if not self.gmail_service.is_ready():
                logger.error("Gmail service not ready, cannot start watch scheduler")
                return False
            
            # Schedule watch refresh every 6 days (Gmail watches expire after 7 days)
            self.scheduler.add_job(
                self._refresh_gmail_watch,
                trigger=IntervalTrigger(days=6),
                id='gmail_watch_refresh',
                name='Gmail Watch Refresh',
                replace_existing=True
            )
            
            # Also schedule a daily health check
            self.scheduler.add_job(
                self._check_watch_health,
                trigger=IntervalTrigger(hours=24),
                id='gmail_watch_health_check',
                name='Gmail Watch Health Check',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Gmail watch scheduler started successfully")
            logger.info("  - Watch refresh: Every 6 days")
            logger.info("  - Health check: Every 24 hours")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Gmail watch scheduler: {e}")
            return False
    
    async def stop(self):
        """Stop the Gmail watch scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Gmail watch scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping Gmail watch scheduler: {e}")
    
    async def _refresh_gmail_watch(self):
        """Refresh the Gmail watch before expiration."""
        try:
            logger.info("Starting scheduled Gmail watch refresh...")
            
            if not self.gmail_service.is_ready():
                logger.error("Gmail service not ready for watch refresh")
                return
            
            # Re-establish the watch
            topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
            watch_id = await self.gmail_service.setup_watch(topic_name)
            
            if watch_id:
                logger.info(f"Gmail watch refreshed successfully: {watch_id}")
                
                # Log the refresh event
                await self._log_watch_refresh(watch_id, "scheduled_refresh")
            else:
                logger.error("Failed to refresh Gmail watch")
                
        except Exception as e:
            logger.error(f"Error during scheduled Gmail watch refresh: {e}")
    
    async def _check_watch_health(self):
        """Check Gmail watch health and refresh if needed."""
        try:
            logger.info("Performing Gmail watch health check...")
            
            if not self.gmail_service.is_ready():
                logger.warning("Gmail service not ready during health check")
                return
            
            # Check if we can access Gmail
            try:
                profile = self.gmail_service.gmail_service.users().getProfile(
                    userId=self.gmail_service.master_email
                ).execute()
                logger.info(f"Gmail health check passed: {profile.get('emailAddress')}")
                
            except Exception as e:
                logger.warning(f"Gmail health check failed: {e}")
                # Try to refresh the watch
                await self._refresh_gmail_watch()
                
        except Exception as e:
            logger.error(f"Error during Gmail watch health check: {e}")
    
    async def _log_watch_refresh(self, watch_id: str, refresh_type: str):
        """Log watch refresh events."""
        try:
            from ...core.supabase_config import get_supabase_service_client
            supabase = get_supabase_service_client()
            
            if supabase:
                log_data = {
                    'watch_id': watch_id,
                    'refresh_type': refresh_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'success'
                }
                
                supabase.table('gmail_watch_logs').insert(log_data).execute()
                logger.info(f"Watch refresh logged: {refresh_type}")
                
        except Exception as e:
            logger.warning(f"Could not log watch refresh: {e}")
    
    async def force_refresh(self) -> Dict[str, Any]:
        """Manually force a Gmail watch refresh."""
        try:
            logger.info("Starting forced Gmail watch refresh...")
            
            if not self.gmail_service.is_ready():
                return {
                    "status": "error",
                    "message": "Gmail service not ready",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            topic_name = "projects/sunny-ai-468016/topics/gmail-notifications"
            watch_id = await self.gmail_service.setup_watch(topic_name)
            
            if watch_id:
                await self._log_watch_refresh(watch_id, "manual_refresh")
                return {
                    "status": "success",
                    "message": "Gmail watch refreshed successfully",
                    "watch_id": watch_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to refresh Gmail watch",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error during forced Gmail watch refresh: {e}")
            return {
                "status": "error",
                "message": f"Error refreshing Gmail watch: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "is_running": self.is_running,
            "scheduler_running": self.scheduler.running if self.scheduler else False,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ] if self.scheduler else [],
            "timestamp": datetime.utcnow().isoformat()
        }


# Global scheduler instance
gmail_watch_scheduler = GmailWatchScheduler()
