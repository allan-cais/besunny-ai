"""
Webhook processor service for processing attendee webhook logs.
Runs as a background service to process webhook notifications and update bot states.
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

from .bot_state_service import BotStateService

logger = logging.getLogger(__name__)

class WebhookProcessorService:
    """Background service for processing webhook logs."""
    
    def __init__(self):
        self.bot_state_service = BotStateService()
        self.is_running = False
        self.process_interval = 30  # seconds
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    async def start(self):
        """Start the webhook processor service."""
        if self.is_running:
            logger.warning("Webhook processor service is already running")
            return
        
        self.is_running = True
        logger.info("Starting webhook processor service")
        
        try:
            while self.is_running:
                try:
                    # Process webhook logs
                    processed_count = await self.bot_state_service.process_webhook_logs()
                    
                    if processed_count > 0:
                        logger.info(f"Processed {processed_count} webhook logs")
                    
                    # Wait before next processing cycle
                    await asyncio.sleep(self.process_interval)
                    
                except Exception as e:
                    logger.error(f"Error in webhook processor cycle: {e}")
                    await asyncio.sleep(self.retry_delay)
                    
        except asyncio.CancelledError:
            logger.info("Webhook processor service cancelled")
        except Exception as e:
            logger.error(f"Fatal error in webhook processor service: {e}")
        finally:
            self.is_running = False
            logger.info("Webhook processor service stopped")
    
    async def stop(self):
        """Stop the webhook processor service."""
        logger.info("Stopping webhook processor service")
        self.is_running = False
    
    async def process_webhook_logs_once(self) -> int:
        """
        Process webhook logs once (for manual triggering).
        
        Returns:
            Number of webhook logs processed
        """
        try:
            return await self.bot_state_service.process_webhook_logs()
        except Exception as e:
            logger.error(f"Error processing webhook logs: {e}")
            return 0
    
    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status.
        
        Returns:
            Dict with service status information
        """
        return {
            "is_running": self.is_running,
            "process_interval": self.process_interval,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "last_check": datetime.now().isoformat()
        }
    
    async def get_webhook_logs_summary(self) -> Dict[str, Any]:
        """
        Get summary of webhook logs.
        
        Returns:
            Dict with webhook logs summary
        """
        try:
            from ...core.database import get_supabase
            supabase = get_supabase()
            
            # Get total webhook logs
            total_result = supabase.table('attendee_webhook_logs').select('id', count='exact').execute()
            total_count = total_result.count or 0
            
            # Get unprocessed webhook logs
            unprocessed_result = supabase.table('attendee_webhook_logs').select('id', count='exact').eq('processed', False).execute()
            unprocessed_count = unprocessed_result.count or 0
            
            # Get webhook logs by trigger type
            trigger_result = supabase.table('attendee_webhook_logs').select('trigger').execute()
            trigger_counts = {}
            for log in trigger_result.data or []:
                trigger = log.get('trigger', 'unknown')
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
            
            # Get recent webhook logs (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            recent_result = supabase.table('attendee_webhook_logs').select('id', count='exact').gte('received_at', yesterday.isoformat()).execute()
            recent_count = recent_result.count or 0
            
            return {
                "total_webhook_logs": total_count,
                "unprocessed_webhook_logs": unprocessed_count,
                "processed_webhook_logs": total_count - unprocessed_count,
                "trigger_counts": trigger_counts,
                "recent_webhook_logs_24h": recent_count,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook logs summary: {e}")
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

# Global service instance
webhook_processor_service = WebhookProcessorService()
