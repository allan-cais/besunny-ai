"""
Bot state service for managing meeting bot states.
Handles initial state fetching and webhook processing for bot state changes.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)

class BotStateService:
    """Service for managing bot states and webhook processing."""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.settings = get_settings()
        self.attendee_api_key = self.settings.attendee_api_key
        self.attendee_base_url = "https://api.attendee.dev"
        
        if not self.attendee_api_key:
            raise ValueError("Attendee API key not configured")
    
    async def get_bot_state(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current bot state from Attendee.dev API.
        
        Args:
            bot_id: The bot ID
            
        Returns:
            Dict containing bot state data or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.attendee_base_url}/api/v1/bots/{bot_id}",
                    headers={
                        "Authorization": f"Token {self.attendee_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    bot_data = response.json()
                    logger.info(f"Successfully fetched bot state for {bot_id}: {bot_data.get('state')}")
                    return bot_data
                elif response.status_code == 404:
                    logger.warning(f"Bot {bot_id} not found")
                    return None
                else:
                    logger.error(f"Failed to fetch bot state for {bot_id}: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching bot state for {bot_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching bot state for {bot_id}: {str(e)}")
            return None
    
    async def update_bot_initial_state(self, bot_id: str) -> bool:
        """
        Update bot with initial state after creation.
        Called after bot is created to set initial status to 'scheduled'.
        
        Args:
            bot_id: The bot ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current bot state from API
            bot_data = await self.get_bot_state(bot_id)
            if not bot_data:
                logger.warning(f"No bot data received for {bot_id}, setting to scheduled")
                # If we can't get state, assume it's scheduled
                bot_state = "scheduled"
            else:
                bot_state = bot_data.get('state', 'scheduled')
            
            # Map Attendee.dev states to our internal states
            mapped_state = self._map_bot_state(bot_state)
            
            # Update meeting_bots table
            result = self.supabase.table('meeting_bots').update({
                'status': mapped_state,
                'last_state_change': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).eq('bot_id', bot_id).execute()
            
            if result.data:
                logger.info(f"Updated bot {bot_id} initial state to {mapped_state}")
                return True
            else:
                logger.error(f"Failed to update bot {bot_id} initial state")
                return False
                
        except Exception as e:
            logger.error(f"Error updating bot {bot_id} initial state: {str(e)}")
            return False
    
    def _map_bot_state(self, attendee_state: str) -> str:
        """
        Map Attendee.dev bot states to our internal states.
        
        Args:
            attendee_state: The state from Attendee.dev API
            
        Returns:
            Mapped internal state
        """
        state_mapping = {
            "scheduled": "scheduled",
            "ready": "scheduled",
            "joining": "scheduled",
            "joined_not_recording": "bot_joined",
            "joined_recording": "transcribing",
            "joined_recording_paused": "transcribing",
            "leaving": "transcribing",
            "post_processing": "post_processing",
            "ended": "completed",
            "fatal_error": "error",
            "waiting_room": "scheduled",
            "data_deleted": "completed",
            "joining_breakout_room": "transcribing",
            "leaving_breakout_room": "transcribing"
        }
        
        return state_mapping.get(attendee_state, "scheduled")
    
    async def process_webhook_logs(self) -> int:
        """
        Process unprocessed webhook logs and update bot states.
        
        Returns:
            Number of webhook logs processed
        """
        try:
            # Get unprocessed webhook logs
            result = self.supabase.table('attendee_webhook_logs').select('*').eq('processed', False).order('received_at').execute()
            
            if not result.data:
                return 0
            
            processed_count = 0
            
            for webhook_log in result.data:
                try:
                    success = await self._process_webhook_log(webhook_log)
                    if success:
                        processed_count += 1
                        # Mark as processed
                        await self._mark_webhook_processed(webhook_log['id'])
                except Exception as e:
                    logger.error(f"Error processing webhook log {webhook_log['id']}: {e}")
                    continue
            
            logger.info(f"Processed {processed_count} webhook logs")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing webhook logs: {e}")
            return 0
    
    async def _process_webhook_log(self, webhook_log: Dict[str, Any]) -> bool:
        """
        Process a single webhook log entry.
        
        Args:
            webhook_log: The webhook log entry
            
        Returns:
            True if successful, False otherwise
        """
        try:
            webhook_data = webhook_log.get('webhook_data', {})
            trigger = webhook_log.get('trigger')
            bot_id = webhook_log.get('bot_id')
            
            if not bot_id:
                logger.warning(f"No bot_id in webhook log {webhook_log['id']}")
                return False
            
            # Only process bot state change webhooks
            if trigger != 'bot.state_change':
                logger.info(f"Skipping non-state-change webhook: {trigger}")
                return True  # Mark as processed but don't update bot state
            
            # Extract state change data
            data = webhook_data.get('data', {})
            new_state = data.get('new_state')
            old_state = data.get('old_state')
            event_type = data.get('event_type')
            
            if not new_state:
                logger.warning(f"No new_state in webhook data for bot {bot_id}")
                return False
            
            # Map to internal state
            mapped_state = self._map_bot_state(new_state)
            
            # Update meeting_bots table
            update_data = {
                'status': mapped_state,
                'last_state_change': data.get('created_at', datetime.now().isoformat()),
                'event_type': event_type,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('meeting_bots').update(update_data).eq('bot_id', bot_id).execute()
            
            if result.data:
                logger.info(f"Updated bot {bot_id} state: {old_state} -> {new_state} (mapped to {mapped_state})")
                
                # If bot ended, trigger transcript processing
                if new_state == 'ended':
                    await self._trigger_transcript_processing(bot_id)
                
                return True
            else:
                logger.error(f"Failed to update bot {bot_id} state")
                return False
                
        except Exception as e:
            logger.error(f"Error processing webhook log: {e}")
            return False
    
    async def _trigger_transcript_processing(self, bot_id: str):
        """Trigger transcript processing when bot ends."""
        try:
            # Import here to avoid circular imports
            from .transcript_service import TranscriptService
            transcript_service = TranscriptService()
            
            # Process ended bot: fetch and store transcript
            success = await transcript_service.process_ended_bot(self.supabase, bot_id)
            if success:
                logger.info(f"Transcript processing completed for bot {bot_id}")
            else:
                logger.error(f"Transcript processing failed for bot {bot_id}")
                
        except Exception as e:
            logger.error(f"Error triggering transcript processing for bot {bot_id}: {e}")
    
    async def _mark_webhook_processed(self, webhook_log_id: str):
        """Mark webhook log as processed."""
        try:
            self.supabase.table('attendee_webhook_logs').update({
                'processed': True,
                'processed_at': datetime.now().isoformat()
            }).eq('id', webhook_log_id).execute()
            
        except Exception as e:
            logger.error(f"Error marking webhook log {webhook_log_id} as processed: {e}")
    
    async def get_bot_status_summary(self, user_id: str) -> Dict[str, int]:
        """
        Get summary of bot statuses for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dict with status counts
        """
        try:
            result = self.supabase.table('meeting_bots').select('status').eq('user_id', user_id).execute()
            
            status_counts = {}
            for bot in result.data or []:
                status = bot.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return status_counts
            
        except Exception as e:
            logger.error(f"Error getting bot status summary for user {user_id}: {e}")
            return {}
