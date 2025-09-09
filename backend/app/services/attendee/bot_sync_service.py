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
    
    def sync_bot_status_to_meetings(self, user_id: str) -> Dict[str, Any]:
        """
        Sync bot status from meeting_bots table to meetings table.
        Simple approach: get all meetings, then get all bots, then match them.
        """
        try:
            logger.info(f"Syncing bot status for user {user_id}")
            
            # Get all meetings for the user
            meetings_result = self.supabase.table('meetings').select('*').eq('user_id', user_id).execute()
            
            if not meetings_result.data:
                return {"success": True, "synced": 0, "message": "No meetings found"}
            
            # Get all bots for the user
            bots_result = self.supabase.table('meeting_bots').select('*').eq('user_id', user_id).execute()
            
            if not bots_result.data:
                return {"success": True, "synced": 0, "message": "No bots found"}
            
            # Create a lookup dictionary for bots by bot_id
            bots_by_id = {bot['bot_id']: bot for bot in bots_result.data}
            
            synced_count = 0
            errors = []
            
            # Process each meeting
            for meeting in meetings_result.data:
                try:
                    attendee_bot_id = meeting.get('attendee_bot_id')
                    if not attendee_bot_id:
                        continue  # Skip meetings without bots
                    
                    # Find the corresponding bot
                    bot = bots_by_id.get(attendee_bot_id)
                    if not bot:
                        logger.warning(f"No bot found for meeting {meeting['id']} with bot_id {attendee_bot_id}")
                        continue
                    
                    # Update the meeting with bot information
                    update_data = {
                        'bot_status': bot['status'],
                        'bot_name': bot['bot_name'],
                        'bot_deployment_method': bot['deployment_method'],
                        'bot_configuration': {
                            'metadata': bot.get('metadata', {}),
                            'created_at': bot['created_at'],
                            'updated_at': bot['updated_at']
                        },
                        'updated_at': bot['updated_at']
                    }
                    
                    # Update the meeting
                    self.supabase.table('meetings').update(update_data).eq('id', meeting['id']).execute()
                    synced_count += 1
                    logger.info(f"Synced bot {bot['bot_id']} to meeting {meeting['id']}")
                    
                except Exception as e:
                    error_msg = f"Failed to sync meeting {meeting['id']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                "success": True,
                "synced": synced_count,
                "errors": errors,
                "message": f"Successfully synced {synced_count} meetings"
            }
            
        except Exception as e:
            logger.error(f"Failed to sync bot status: {e}")
            return {"success": False, "error": str(e)}
    
    def get_meeting_with_bot_status(self, meeting_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a meeting with its associated bot status.
        Simple approach: get meeting, then get bot separately.
        """
        try:
            # Get the meeting
            meeting_result = self.supabase.table('meetings').select('*').eq('id', meeting_id).eq('user_id', user_id).single().execute()
            
            if not meeting_result.data:
                return None
            
            meeting = meeting_result.data
            
            # Get bot information if meeting has a bot
            attendee_bot_id = meeting.get('attendee_bot_id')
            if attendee_bot_id:
                bot_result = self.supabase.table('meeting_bots').select('*').eq('bot_id', attendee_bot_id).execute()
                if bot_result.data and len(bot_result.data) > 0:
                    bot = bot_result.data[0]
                    meeting.update({
                        'bot_status': bot['status'],
                        'bot_name': bot['bot_name'],
                        'bot_deployment_method': bot['deployment_method'],
                        'bot_metadata': bot.get('metadata', {}),
                        'bot_created_at': bot['created_at'],
                        'bot_updated_at': bot['updated_at']
                    })
                else:
                    # Bot ID exists but no bot found
                    meeting.update({
                        'bot_status': None,
                        'bot_name': None,
                        'bot_deployment_method': None,
                        'bot_metadata': None,
                        'bot_created_at': None,
                        'bot_updated_at': None
                    })
            else:
                # No bot associated with this meeting
                meeting.update({
                    'bot_status': 'pending',
                    'bot_name': None,
                    'bot_deployment_method': None,
                    'bot_metadata': {},
                    'bot_created_at': None,
                    'bot_updated_at': None
                })
            
            return meeting
            
        except Exception as e:
            logger.error(f"Failed to get meeting with bot status: {e}")
            return None
    
    def get_user_meetings_with_bot_status(self, user_id: str, unassigned_only: bool = True, future_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get meetings for a user with their associated bot status.
        Simple approach: get meetings, then get bots, then match them.
        """
        try:
            logger.info(f"Getting meetings for user {user_id}, unassigned_only={unassigned_only}, future_only={future_only}")
            
            # Build query for meetings
            query = self.supabase.table('meetings').select('*').eq('user_id', user_id)
            
            # Filter for unassigned meetings (project_id is null)
            if unassigned_only:
                query = query.is_('project_id', 'null')
                logger.info("Applied unassigned filter")
            
            # Filter for future meetings (from now onwards)
            if future_only:
                now = datetime.now().isoformat()
                query = query.gte('start_time', now)
                logger.info(f"Applied future filter from {now}")
            
            # Execute query
            meetings_result = query.order('start_time').execute()
            
            logger.info(f"Backend query returned {len(meetings_result.data) if meetings_result.data else 0} meetings")
            
            if not meetings_result.data:
                logger.info("No meetings found in backend query")
                return []
            
            meetings = meetings_result.data
            
            # Get all bots for the user
            bots_result = self.supabase.table('meeting_bots').select('*').eq('user_id', user_id).execute()
            bots_by_id = {bot['bot_id']: bot for bot in (bots_result.data or [])}
            
            # Process the results to add bot information
            for meeting in meetings:
                attendee_bot_id = meeting.get('attendee_bot_id')
                if attendee_bot_id and attendee_bot_id in bots_by_id:
                    bot = bots_by_id[attendee_bot_id]
                    meeting.update({
                        'bot_status': bot['status'],
                        'bot_name': bot['bot_name'],
                        'bot_deployment_method': bot['deployment_method'],
                        'bot_metadata': bot.get('metadata', {}),
                        'bot_created_at': bot['created_at'],
                        'bot_updated_at': bot['updated_at']
                    })
                else:
                    # No bot or bot not found
                    meeting.update({
                        'bot_status': 'pending',
                        'bot_name': None,
                        'bot_deployment_method': None,
                        'bot_metadata': {},
                        'bot_created_at': None,
                        'bot_updated_at': None
                    })
            
            logger.info(f"Processed {len(meetings)} meetings with bot status")
            return meetings
            
        except Exception as e:
            logger.error(f"Failed to get user meetings with bot status: {e}")
            return []
    
    def _get_user_meeting_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all meeting bots for a user."""
        try:
            result = self.supabase.table('meeting_bots').select('*').eq('user_id', user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get user meeting bots: {e}")
            return []
    
    def _find_meeting_by_url(self, meeting_url: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a meeting by meeting_url and user_id."""
        try:
            result = self.supabase.table('meetings').select('*').eq('meeting_url', meeting_url).eq('user_id', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to find meeting by URL: {e}")
            return None
    
    def _find_bot_by_url(self, meeting_url: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a bot by meeting_url and user_id."""
        try:
            result = self.supabase.table('meeting_bots').select('*').eq('meeting_url', meeting_url).eq('user_id', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to find bot by URL: {e}")
            return None