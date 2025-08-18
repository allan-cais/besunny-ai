"""
Attendee polling service for BeSunny.ai Python backend.
Handles meeting status polling and batch operations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from .attendee_service import AttendeeService

logger = logging.getLogger(__name__)


class PollingResult(BaseModel):
    """Result of a polling operation."""
    bot_id: str
    meeting_id: str
    status: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime
    processing_time_ms: int


class BatchPollingResult(BaseModel):
    """Result of a batch polling operation."""
    total_bots: int
    successful_polls: int
    failed_polls: int
    results: List[PollingResult]
    total_processing_time_ms: int
    timestamp: datetime


class AttendeePollingService:
    """Service for polling attendee and meeting bot status."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.attendee_service = AttendeeService()
        
        logger.info("Attendee Polling Service initialized")
    
    async def poll_meeting_status(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll status for a specific meeting.
        
        Args:
            meeting_id: Meeting ID to poll status for
            
        Returns:
            Meeting status information or None if failed
        """
        try:
            # Get meeting bot for this meeting
            bot = await self._get_meeting_bot(meeting_id)
            if not bot:
                logger.warning(f"No bot found for meeting {meeting_id}")
                return None
            
            # Poll bot status
            start_time = datetime.now()
            status = await self.attendee_service.get_bot_status(bot['bot_id'])
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            if status:
                result = PollingResult(
                    bot_id=bot['bot_id'],
                    meeting_id=meeting_id,
                    status=status.get('status', 'unknown'),
                    success=True,
                    timestamp=datetime.now(),
                    processing_time_ms=processing_time
                )
                
                # Store polling result
                await self._store_polling_result(result)
                
                return {
                    'meeting_id': meeting_id,
                    'bot_id': bot['bot_id'],
                    'status': status,
                    'polling_result': result.dict()
                }
            else:
                result = PollingResult(
                    bot_id=bot['bot_id'],
                    meeting_id=meeting_id,
                    status='unknown',
                    success=False,
                    error_message='Failed to get bot status',
                    timestamp=datetime.now(),
                    processing_time_ms=processing_time
                )
                
                await self._store_polling_result(result)
                return None
                
        except Exception as e:
            logger.error(f"Failed to poll meeting status for {meeting_id}: {e}")
            return None
    
    async def poll_all_user_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Poll all meetings for a specific user.
        
        Args:
            user_id: User ID to poll meetings for
            
        Returns:
            List of meeting status results
        """
        try:
            # Get all user's meetings
            meetings = await self._get_user_meetings(user_id)
            if not meetings:
                logger.info(f"No meetings found for user {user_id}")
                return []
            
            # Poll each meeting
            results = []
            for meeting in meetings:
                try:
                    result = await self.poll_meeting_status(meeting['id'])
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Failed to poll meeting {meeting['id']}: {e}")
                    continue
            
            logger.info(f"Successfully polled {len(results)} meetings for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to poll all user meetings for {user_id}: {e}")
            return []
    
    async def handle_polling_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process and analyze polling results.
        
        Args:
            results: List of polling results to process
            
        Returns:
            Analysis of polling results
        """
        try:
            if not results:
                return {
                    'total_meetings': 0,
                    'successful_polls': 0,
                    'failed_polls': 0,
                    'status_summary': {},
                    'recommendations': []
                }
            
            # Analyze results
            total_meetings = len(results)
            successful_polls = len([r for r in results if r.get('status')])
            failed_polls = total_meetings - successful_polls
            
            # Status summary
            status_summary = {}
            for result in results:
                status = result.get('status', {}).get('status', 'unknown')
                status_summary[status] = status_summary.get(status, 0) + 1
            
            # Generate recommendations
            recommendations = []
            if failed_polls > 0:
                recommendations.append(f"Investigate {failed_polls} failed polls")
            
            if status_summary.get('error', 0) > 0:
                recommendations.append("Check bot configurations for failed bots")
            
            if status_summary.get('offline', 0) > 0:
                recommendations.append("Some bots appear to be offline")
            
            return {
                'total_meetings': total_meetings,
                'successful_polls': successful_polls,
                'failed_polls': failed_polls,
                'status_summary': status_summary,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to handle polling results: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def smart_polling(self, user_id: str, force_poll: bool = False) -> Dict[str, Any]:
        """
        Smart polling that considers meeting timing and user activity.
        
        Args:
            user_id: User ID to poll for
            force_poll: Force polling regardless of timing
            
        Returns:
            Smart polling results
        """
        try:
            # Check if user has recent activity
            last_activity = await self._get_user_last_activity(user_id)
            if not force_poll and last_activity:
                # Only poll if enough time has passed since last activity
                time_since_activity = datetime.now() - last_activity
                if time_since_activity < timedelta(minutes=15):
                    logger.info(f"User {user_id} has recent activity, skipping poll")
                    return {
                        'skipped': True,
                        'reason': 'Recent activity detected',
                        'last_activity': last_activity.isoformat()
                    }
            
            # Get meetings that need polling
            meetings_to_poll = await self._get_meetings_needing_polling(user_id)
            if not meetings_to_poll:
                logger.info(f"No meetings need polling for user {user_id}")
                return {
                    'total_meetings': 0,
                    'meetings_polled': 0,
                    'skipped': False
                }
            
            # Poll meetings
            results = []
            for meeting in meetings_to_poll:
                try:
                    result = await self.poll_meeting_status(meeting['id'])
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Failed to poll meeting {meeting['id']}: {e}")
                    continue
            
            # Update user activity
            await self._update_user_activity(user_id, 'polling')
            
            # Handle results
            analysis = await self.handle_polling_results(results)
            
            return {
                'total_meetings': len(meetings_to_poll),
                'meetings_polled': len(results),
                'skipped': False,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Smart polling failed for user {user_id}: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_polling_history(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get polling history for a user.
        
        Args:
            user_id: User ID to get history for
            limit: Maximum number of records to return
            
        Returns:
            List of polling history records
        """
        try:
            result = self.supabase.table("polling_history") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("timestamp", desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get polling history for user {user_id}: {e}")
            return []
    
    # Private helper methods
    
    async def _get_meeting_bot(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get meeting bot for a specific meeting."""
        try:
            result = self.supabase.table("meeting_bots") \
                .select("*") \
                .eq("meeting_id", meeting_id) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get meeting bot for meeting {meeting_id}: {e}")
            return None
    
    async def _get_user_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all meetings for a user."""
        try:
            result = self.supabase.table("meetings") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("status", "active") \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get user meetings for {user_id}: {e}")
            return []
    
    async def _get_meetings_needing_polling(self, user_id: str) -> List[Dict[str, Any]]:
        """Get meetings that need polling based on timing and status."""
        try:
            # Get meetings that haven't been polled recently or have active bots
            now = datetime.now()
            cutoff_time = now - timedelta(minutes=30)
            
            result = self.supabase.table("meetings") \
                .select("*, meeting_bots(*)") \
                .eq("user_id", user_id) \
                .eq("status", "active") \
                .or_(f"last_polled_at.is.null,last_polled_at.lt.{cutoff_time.isoformat()}") \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get meetings needing polling for user {user_id}: {e}")
            return []
    
    async def _get_user_last_activity(self, user_id: str) -> Optional[datetime]:
        """Get user's last activity timestamp."""
        try:
            result = self.supabase.table("user_activity_logs") \
                .select("timestamp") \
                .eq("user_id", user_id) \
                .order("timestamp", desc=True) \
                .limit(1) \
                .single() \
                .execute()
            
            if result.data and result.data.get('timestamp'):
                return datetime.fromisoformat(result.data['timestamp'].replace('Z', '+00:00'))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last activity for user {user_id}: {e}")
            return None
    
    async def _update_user_activity(self, user_id: str, activity_type: str):
        """Update user activity log."""
        try:
            activity_data = {
                "user_id": user_id,
                "activity_type": activity_type,
                "timestamp": datetime.now().isoformat()
            }
            
            self.supabase.table("user_activity_logs").insert(activity_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to update user activity for {user_id}: {e}")
    
    async def _store_polling_result(self, result: PollingResult):
        """Store polling result in database."""
        try:
            result_data = result.dict()
            result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            self.supabase.table("polling_history").insert(result_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store polling result: {e}")
