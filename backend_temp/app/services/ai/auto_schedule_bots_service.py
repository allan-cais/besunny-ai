"""
Auto Schedule Bots Service for BeSunny.ai Python backend.
Handles AI-powered meeting bot scheduling automation and management.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.meeting import Meeting
from .ai_service import AIService

logger = logging.getLogger(__name__)


class BotSchedulingRequest(BaseModel):
    """Request for bot scheduling."""
    meeting_id: str
    user_id: str
    bot_configuration: Optional[Dict[str, Any]] = None
    auto_join: bool = True
    notification_preferences: Optional[Dict[str, Any]] = None


class BotSchedulingResult(BaseModel):
    """Result of bot scheduling operation."""
    meeting_id: str
    bot_id: Optional[str] = None
    bot_name: str
    bot_status: str
    scheduled_at: datetime
    success: bool
    error_message: Optional[str] = None
    estimated_join_time: Optional[datetime] = None
    configuration: Dict[str, Any]


class BatchBotSchedulingRequest(BaseModel):
    """Request for batch bot scheduling."""
    meetings: List[BotSchedulingRequest]
    user_id: str
    priority_strategy: str = "chronological"  # chronological, priority, smart


class BatchBotSchedulingResult(BaseModel):
    """Result of batch bot scheduling operation."""
    total_meetings: int
    successful_schedules: int
    failed_schedules: int
    results: List[BotSchedulingResult]
    processing_time_ms: int
    errors: List[Dict[str, Any]]


class AutoScheduleBotsService:
    """Service for AI-powered meeting bot scheduling automation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        self.ai_service = AIService()
        
        logger.info("Auto Schedule Bots Service initialized")
    
    async def auto_schedule_user_bots(self, user_id: str) -> Dict[str, Any]:
        """
        Automatically schedule bots for all upcoming meetings for a user.
        
        Args:
            user_id: User ID to schedule bots for
            
        Returns:
            Scheduling results summary
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting auto-scheduling for user {user_id}")
            
            # Get upcoming meetings that need bots
            upcoming_meetings = await self._get_upcoming_meetings(user_id)
            
            if not upcoming_meetings:
                return {
                    'success': True,
                    'message': 'No upcoming meetings found that need bots',
                    'meetings_processed': 0,
                    'bots_scheduled': 0
                }
            
            # Schedule bots for each meeting
            scheduling_results = []
            bots_scheduled = 0
            
            for meeting in upcoming_meetings:
                try:
                    result = await self._schedule_meeting_bot(meeting, user_id)
                    scheduling_results.append(result)
                    
                    if result.success:
                        bots_scheduled += 1
                        
                except Exception as e:
                    logger.error(f"Failed to schedule bot for meeting {meeting['id']}: {e}")
                    scheduling_results.append({
                        'meeting_id': meeting['id'],
                        'success': False,
                        'error_message': str(e)
                    })
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return {
                'success': True,
                'meetings_processed': len(upcoming_meetings),
                'bots_scheduled': bots_scheduled,
                'processing_time_ms': processing_time,
                'results': scheduling_results
            }
            
        except Exception as e:
            logger.error(f"Auto-scheduling failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'meetings_processed': 0,
                'bots_scheduled': 0
            }
    
    async def schedule_meeting_bot(self, meeting: Dict[str, Any], user_id: str) -> BotSchedulingResult:
        """
        Schedule a bot for a specific meeting.
        
        Args:
            meeting: Meeting data
            user_id: User ID
            
        Returns:
            BotSchedulingResult with scheduling details
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Scheduling bot for meeting {meeting['id']}")
            
            # Check if meeting already has a bot
            if meeting.get('attendee_bot_id'):
                return BotSchedulingResult(
                    meeting_id=meeting['id'],
                    bot_id=meeting['attendee_bot_id'],
                    bot_name=meeting.get('bot_name', 'Sunny AI Notetaker'),
                    bot_status=meeting.get('bot_status', 'pending'),
                    scheduled_at=datetime.now(),
                    success=True,
                    configuration=meeting.get('bot_configuration', {})
                )
            
            # Generate bot configuration using AI
            bot_config = await self._generate_bot_configuration(meeting)
            
            # Create bot record
            bot_data = {
                'name': bot_config.get('bot_name', 'Sunny AI Notetaker'),
                'description': bot_config.get('description', 'AI-powered meeting notetaker'),
                'provider': 'attendee',
                'provider_bot_id': None,  # Will be set when bot is deployed
                'settings': bot_config,
                'is_active': True,
                'user_id': user_id
            }
            
            # Insert bot record
            bot_result = await self.supabase.table('bots').insert(bot_data).execute()
            
            if not bot_result.data:
                raise Exception("Failed to create bot record")
            
            bot_id = bot_result.data[0]['id']
            
            # Update meeting with bot information
            meeting_update = {
                'attendee_bot_id': bot_id,
                'bot_name': bot_data['name'],
                'bot_status': 'pending',
                'bot_configuration': bot_config,
                'bot_deployment_method': 'auto',
                'bot_chat_message': bot_config.get('chat_message', 'Hi, I\'m here to transcribe this meeting!'),
                'auto_bot_notification_sent': False
            }
            
            await self.supabase.table('meetings').update(meeting_update).eq('id', meeting['id']).execute()
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return BotSchedulingResult(
                meeting_id=meeting['id'],
                bot_id=bot_id,
                bot_name=bot_data['name'],
                bot_status='pending',
                scheduled_at=datetime.now(),
                success=True,
                estimated_join_time=meeting.get('start_time'),
                configuration=bot_config
            )
            
        except Exception as e:
            logger.error(f"Bot scheduling failed for meeting {meeting['id']}: {e}")
            return BotSchedulingResult(
                meeting_id=meeting['id'],
                bot_name='Sunny AI Notetaker',
                bot_status='failed',
                scheduled_at=datetime.now(),
                success=False,
                error_message=str(e),
                configuration={}
            )
    
    async def handle_scheduling_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process and analyze scheduling results.
        
        Args:
            results: List of scheduling results
            
        Returns:
            Analysis of scheduling results
        """
        try:
            total_meetings = len(results)
            successful_schedules = sum(1 for r in results if r.get('success', False))
            failed_schedules = total_meetings - successful_schedules
            
            # Analyze common failure patterns
            failure_analysis = {}
            for result in results:
                if not result.get('success', False):
                    error = result.get('error_message', 'Unknown error')
                    failure_analysis[error] = failure_analysis.get(error, 0) + 1
            
            return {
                'total_meetings': total_meetings,
                'successful_schedules': successful_schedules,
                'failed_schedules': failed_schedules,
                'success_rate': (successful_schedules / total_meetings) * 100 if total_meetings > 0 else 0,
                'failure_analysis': failure_analysis,
                'recommendations': self._generate_recommendations(failure_analysis)
            }
            
        except Exception as e:
            logger.error(f"Failed to handle scheduling results: {e}")
            return {
                'error': str(e),
                'total_meetings': 0,
                'successful_schedules': 0,
                'failed_schedules': 0
            }
    
    async def _get_upcoming_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming meetings that need bots."""
        try:
            # Get meetings in the next 7 days that don't have bots
            start_time = datetime.now()
            end_time = start_time + timedelta(days=7)
            
            result = await self.supabase.table('meetings').select('*').eq('user_id', user_id).gte('start_time', start_time.isoformat()).lte('start_time', end_time.isoformat()).is_('attendee_bot_id', None).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get upcoming meetings: {e}")
            return []
    
    async def _generate_bot_configuration(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bot configuration using AI analysis."""
        try:
            # Use AI to analyze meeting context and generate optimal bot configuration
            meeting_context = f"""
            Meeting: {meeting.get('title', 'Untitled')}
            Description: {meeting.get('description', 'No description')}
            Duration: {meeting.get('start_time')} to {meeting.get('end_time')}
            Project: {meeting.get('project_id', 'No project')}
            """
            
            # Generate configuration using AI service
            ai_result = await self.ai_service.generate_bot_configuration(meeting_context)
            
            if ai_result.success:
                return ai_result.result
            else:
                # Fallback to default configuration
                return self._get_default_bot_configuration(meeting)
                
        except Exception as e:
            logger.error(f"Failed to generate bot configuration: {e}")
            return self._get_default_bot_configuration(meeting)
    
    def _get_default_bot_configuration(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        """Get default bot configuration."""
        return {
            'bot_name': 'Sunny AI Notetaker',
            'description': 'AI-powered meeting notetaker',
            'transcription_enabled': True,
            'summary_enabled': True,
            'action_items_enabled': True,
            'participant_tracking': True,
            'chat_message': 'Hi, I\'m here to transcribe this meeting!',
            'auto_join': True,
            'notification_preferences': {
                'transcript_ready': True,
                'summary_ready': True,
                'action_items_ready': True
            }
        }
    
    def _generate_recommendations(self, failure_analysis: Dict[str, int]) -> List[str]:
        """Generate recommendations based on failure analysis."""
        recommendations = []
        
        if failure_analysis.get('Failed to create bot record', 0) > 0:
            recommendations.append("Check database connectivity and permissions")
        
        if failure_analysis.get('Meeting not found', 0) > 0:
            recommendations.append("Verify meeting data integrity")
        
        if failure_analysis.get('AI service unavailable', 0) > 0:
            recommendations.append("Check OpenAI API key and service status")
        
        if not recommendations:
            recommendations.append("All bot scheduling operations completed successfully")
        
        return recommendations
