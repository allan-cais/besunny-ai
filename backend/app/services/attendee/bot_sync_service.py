"""
Bot synchronization service for BeSunny.ai Python backend.
Syncs bot status between meeting_bots and meetings tables.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...core.database import get_supabase

logger = logging.getLogger(__name__)


class BotSyncService:
    """Service for synchronizing bot status between meeting_bots and meetings tables."""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def sync_bot_status_to_meetings(self, user_id: str) -> Dict[str, Any]:
        """
        Sync bot status from meeting_bots table to meetings table.
        This ensures the meetings table has the latest bot information.
        """
        try:
            # Get all meeting bots for the user
            meeting_bots = await self._get_user_meeting_bots(user_id)
            
            if not meeting_bots:
                return {"success": True, "synced": 0, "message": "No meeting bots found"}
            
            synced_count = 0
            errors = []
            
            for bot in meeting_bots:
                try:
                    # Find the corresponding meeting by meeting_url
                    meeting = await self._find_meeting_by_url(bot['meeting_url'], user_id)
                    
                    if meeting:
                        # Update the meeting with bot information
                        await self._update_meeting_with_bot_info(meeting['id'], bot)
                        synced_count += 1
                        logger.info(f"Synced bot {bot['bot_id']} to meeting {meeting['id']}")
                    else:
                        logger.warning(f"No meeting found for bot {bot['bot_id']} with URL {bot['meeting_url']}")
                        
                except Exception as e:
                    error_msg = f"Failed to sync bot {bot['bot_id']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                "success": True,
                "synced": synced_count,
                "total_bots": len(meeting_bots),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to sync bot status: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_meeting_with_bot_status(self, meeting_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a meeting with its associated bot status from meeting_bots table.
        """
        try:
            # Get the meeting
            meeting_result = await self.supabase.table('meetings').select('*').eq('id', meeting_id).eq('user_id', user_id).single().execute()
            
            if not meeting_result.data:
                return None
            
            meeting = meeting_result.data
            
            # If meeting has a meeting_url, try to find the bot
            if meeting.get('meeting_url'):
                bot = await self._find_bot_by_url(meeting['meeting_url'], user_id)
                if bot:
                    # Merge bot information into meeting data
                    meeting.update({
                        'attendee_bot_id': bot['bot_id'],
                        'bot_status': bot['status'],
                        'bot_name': bot['bot_name'],
                        'bot_deployment_method': bot['deployment_method'],
                        'bot_metadata': bot.get('metadata', {}),
                        'bot_created_at': bot['created_at'],
                        'bot_updated_at': bot['updated_at']
                    })
            
            return meeting
            
        except Exception as e:
            logger.error(f"Failed to get meeting with bot status: {e}")
            return None
    
    async def get_user_meetings_with_bot_status(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all meetings for a user with their associated bot status.
        """
        try:
            # Get all meetings for the user
            meetings_result = await self.supabase.table('meetings').select('*').eq('user_id', user_id).order('start_time', desc=True).execute()
            
            if not meetings_result.data:
                return []
            
            meetings = meetings_result.data
            
            # Get all meeting bots for the user
            meeting_bots = await self._get_user_meeting_bots(user_id)
            
            # Create a lookup map by meeting_url
            bot_lookup = {bot['meeting_url']: bot for bot in meeting_bots if bot.get('meeting_url')}
            
            # Merge bot information into meetings
            for meeting in meetings:
                if meeting.get('meeting_url') and meeting['meeting_url'] in bot_lookup:
                    bot = bot_lookup[meeting['meeting_url']]
                    meeting.update({
                        'attendee_bot_id': bot['bot_id'],
                        'bot_status': bot['status'],
                        'bot_name': bot['bot_name'],
                        'bot_deployment_method': bot['deployment_method'],
                        'bot_metadata': bot.get('metadata', {}),
                        'bot_created_at': bot['created_at'],
                        'bot_updated_at': bot['updated_at']
                    })
            
            return meetings
            
        except Exception as e:
            logger.error(f"Failed to get user meetings with bot status: {e}")
            return []
    
    # Private helper methods
    
    async def _get_user_meeting_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all meeting bots for a user."""
        try:
            result = await self.supabase.table('meeting_bots').select('*').eq('user_id', user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get user meeting bots: {e}")
            return []
    
    async def _find_meeting_by_url(self, meeting_url: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a meeting by meeting_url and user_id."""
        try:
            result = await self.supabase.table('meetings').select('*').eq('meeting_url', meeting_url).eq('user_id', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to find meeting by URL: {e}")
            return None
    
    async def _find_bot_by_url(self, meeting_url: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a bot by meeting_url and user_id."""
        try:
            result = await self.supabase.table('meeting_bots').select('*').eq('meeting_url', meeting_url).eq('user_id', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to find bot by URL: {e}")
            return None
    
    async def _update_meeting_with_bot_info(self, meeting_id: str, bot: Dict[str, Any]):
        """Update a meeting with bot information."""
        try:
            update_data = {
                'attendee_bot_id': bot['bot_id'],
                'bot_status': bot['status'],
                'bot_name': bot['bot_name'],
                'bot_deployment_method': bot['deployment_method'],
                'bot_configuration': {
                    'provider': 'attendee',
                    'bot_id': bot['bot_id'],
                    'project_id': bot.get('attendee_project_id'),
                    'deployment_method': bot['deployment_method'],
                    'metadata': bot.get('metadata', {})
                },
                'updated_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update meeting with bot info: {e}")
            raise
