"""
Project onboarding AI service for BeSunny.ai Python backend.
Handles AI-powered project metadata generation and OpenAI integration.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from pydantic import BaseModel

from ...core.database import get_supabase_service_client
from ...core.config import get_settings
from ...models.schemas.project import Project

logger = logging.getLogger(__name__)


class ProjectMetadata(BaseModel):
    """AI-generated project metadata."""
    title: str
    description: str
    category: str
    tags: List[str]
    priority: str  # 'low', 'medium', 'high'
    estimated_duration: str
    complexity: str  # 'simple', 'moderate', 'complex'
    required_skills: List[str]
    stakeholders: List[str]
    success_metrics: List[str]
    risks: List[str]
    recommendations: List[str]
    confidence_score: float


class ProjectOnboardingResult(BaseModel):
    """Result of project onboarding AI processing."""
    project_id: str
    user_id: str
    metadata: ProjectMetadata
    processing_time_ms: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime


class ProjectOnboardingAIService:
    """Service for AI-powered project onboarding and metadata generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_service_client()
        self.client = None  # Initialize lazily
        self.model = self.settings.openai_model
        
        # Rate limiting semaphore
        self._rate_limit_semaphore = asyncio.Semaphore(3)
        
        logger.info("Project Onboarding AI Service initialized")
    
    def _get_client(self):
        """Get OpenAI client, initializing if needed."""
        if self.client is None:
            if not self.settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self.client
    
    async def process_project_onboarding(self, project_id: str, user_id: str, 
                                      summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process project onboarding using AI.
        
        Args:
            project_id: Project ID
            user_id: User ID
            summary: Project summary information
            
        Returns:
            Onboarding processing result
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting AI project onboarding for project {project_id}")
            logger.info(f"Summary data: {summary}")
            
            # Generate project metadata using AI
            logger.info("Generating project metadata...")
            metadata = await self.generate_project_metadata(summary)
            
            # Validate generated metadata
            if not await self.validate_metadata(metadata):
                return {
                    'success': False,
                    'error': 'Generated metadata validation failed',
                    'project_id': project_id,
                    'user_id': user_id
                }
            
            # Update project with generated metadata
            update_success = await self.update_project_metadata(project_id, metadata)
            if not update_success:
                return {
                    'success': False,
                    'error': 'Failed to update project metadata',
                    'project_id': project_id,
                    'user_id': user_id
                }
            
            # Create metadata record
            record_success = await self.create_project_metadata_record(project_id, metadata)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            # Create onboarding result
            result = ProjectOnboardingResult(
                project_id=project_id,
                user_id=user_id,
                metadata=metadata,
                processing_time_ms=processing_time,
                success=True,
                timestamp=datetime.now()
            )
            
            # Store result
            await self._store_onboarding_result(result)
            
            logger.info(f"AI project onboarding completed for project {project_id}")
            
            return {
                'success': True,
                'project_id': project_id,
                'user_id': user_id,
                'metadata': metadata.model_dump(),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"AI project onboarding failed for project {project_id}: {error_message}")
            
            # Create failed result
            result = ProjectOnboardingResult(
                project_id=project_id,
                user_id=user_id,
                metadata=ProjectMetadata(
                    title="",
                    description="",
                    category="",
                    tags=[],
                    priority="",
                    estimated_duration="",
                    complexity="",
                    required_skills=[],
                    stakeholders=[],
                    success_metrics=[],
                    risks=[],
                    recommendations=[],
                    confidence_score=0.0
                ),
                processing_time_ms=(datetime.now() - start_time).microseconds // 1000,
                success=False,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            await self._store_onboarding_result(result)
            
            return {
                'success': False,
                'error': error_message,
                'project_id': project_id,
                'user_id': user_id
            }
    
    async def generate_project_metadata(self, summary: Dict[str, Any]) -> ProjectMetadata:
        """
        Generate project metadata using OpenAI.
        
        Args:
            summary: Project summary information
            
        Returns:
            Generated project metadata
        """
        try:
            async with self._rate_limit_semaphore:
                # Build system prompt
                system_prompt = self._build_metadata_generation_prompt(summary)
                
                # Create user message
                user_message = self._build_user_message(summary)
                
                # Call OpenAI API
                response = await self._get_client().chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.3,
                    max_tokens=1000,
                    response_format={"type": "json_object"}
                )
                
                # Parse response
                result_content = response.choices[0].message.content
                metadata_dict = self._parse_metadata_response(result_content)
                
                # Create ProjectMetadata object
                metadata = ProjectMetadata(
                    title=metadata_dict.get('title', ''),
                    description=metadata_dict.get('description', ''),
                    category=metadata_dict.get('category', ''),
                    tags=metadata_dict.get('tags', []),
                    priority=metadata_dict.get('priority', 'medium'),
                    estimated_duration=metadata_dict.get('estimated_duration', ''),
                    complexity=metadata_dict.get('complexity', 'moderate'),
                    required_skills=metadata_dict.get('required_skills', []),
                    stakeholders=metadata_dict.get('stakeholders', []),
                    success_metrics=metadata_dict.get('success_metrics', []),
                    risks=metadata_dict.get('risks', []),
                    recommendations=metadata_dict.get('recommendations', []),
                    confidence_score=metadata_dict.get('confidence_score', 0.8)
                )
                
                logger.info(f"Generated project metadata with confidence score: {metadata.confidence_score}")
                return metadata
                
        except Exception as e:
            logger.error(f"Failed to generate project metadata: {e}")
            raise e
    
    async def validate_metadata(self, metadata: ProjectMetadata) -> bool:
        """
        Validate generated project metadata.
        
        Args:
            metadata: Project metadata to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['title', 'description', 'category', 'priority']
            for field in required_fields:
                if not getattr(metadata, field):
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate priority
            if metadata.priority not in ['low', 'medium', 'high']:
                logger.warning(f"Invalid priority: {metadata.priority}")
                return False
            
            # Validate complexity
            if metadata.complexity not in ['simple', 'moderate', 'complex']:
                logger.warning(f"Invalid complexity: {metadata.complexity}")
                return False
            
            # Validate confidence score
            if not 0.0 <= metadata.confidence_score <= 1.0:
                logger.warning(f"Invalid confidence score: {metadata.confidence_score}")
                return False
            
            # Validate lists are not empty
            if not metadata.tags or not metadata.required_skills:
                logger.warning("Tags and required skills cannot be empty")
                return False
            
            logger.info("Project metadata validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Metadata validation failed: {e}")
            return False
    
    async def update_project_metadata(self, project_id: str, metadata: ProjectMetadata) -> bool:
        """
        Update project with generated metadata.
        
        Args:
            project_id: Project ID
            metadata: Generated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update project record
            update_data = {
                'title': metadata.title,
                'description': metadata.description,
                'category': metadata.category,
                'tags': metadata.tags,
                'priority': metadata.priority,
                'estimated_duration': metadata.estimated_duration,
                'complexity': metadata.complexity,
                'required_skills': metadata.required_skills,
                'stakeholders': metadata.stakeholders,
                'success_metrics': metadata.success_metrics,
                'risks': metadata.risks,
                'recommendations': metadata.recommendations,
                'ai_metadata_generated': True,
                'ai_confidence_score': metadata.confidence_score,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("projects") \
                .update(update_data) \
                .eq("id", project_id) \
                .execute()
            
            if result.data:
                logger.info(f"Updated project {project_id} with AI-generated metadata")
                return True
            else:
                logger.error(f"Failed to update project {project_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update project metadata: {e}")
            return False
    
    async def create_project_metadata_record(self, project_id: str, metadata: ProjectMetadata) -> bool:
        """
        Create a record of the generated metadata.
        
        Args:
            project_id: Project ID
            metadata: Generated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create metadata record
            record_data = {
                'project_id': project_id,
                'metadata': metadata.model_dump(),
                'generated_at': datetime.now().isoformat(),
                'model_used': self.model,
                'confidence_score': metadata.confidence_score
            }
            
            result = self.supabase.table("ai_generated_metadata") \
                .insert(record_data) \
                .execute()
            
            if result.data:
                logger.info(f"Created metadata record for project {project_id}")
                return True
            else:
                logger.error(f"Failed to create metadata record for project {project_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create metadata record: {e}")
            return False
    
    # Private helper methods
    
    def _build_metadata_generation_prompt(self, summary: Dict[str, Any]) -> str:
        """Build system prompt for metadata generation."""
        prompt = """You are an expert project management AI assistant. Your task is to analyze project information and generate comprehensive project metadata.

Generate metadata in the following JSON format:
{
    "title": "Clear, concise project title",
    "description": "Detailed project description (2-3 sentences)",
    "category": "Project category (e.g., 'Software Development', 'Marketing', 'Research', 'Operations')",
    "tags": ["relevant", "tags", "for", "project"],
    "priority": "low|medium|high",
    "estimated_duration": "Estimated project duration (e.g., '2-3 weeks', '3-6 months')",
    "complexity": "simple|moderate|complex",
    "required_skills": ["skill1", "skill2", "skill3"],
    "stakeholders": ["stakeholder1", "stakeholder2"],
    "success_metrics": ["metric1", "metric2", "metric3"],
    "risks": ["risk1", "risk2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "confidence_score": 0.85
}

Guidelines:
- Be specific and actionable
- Consider project scope and context
- Prioritize based on business impact
- Identify realistic risks and mitigation strategies
- Provide practical recommendations
- Set confidence score based on available information quality

Project Summary:
"""
        
        # Add project summary details
        for key, value in summary.items():
            if value:
                prompt += f"{key}: {value}\n"
        
        return prompt
    
    def _build_user_message(self, summary: Dict[str, Any]) -> str:
        """Build user message for metadata generation."""
        message = "Please analyze the following project information and generate comprehensive metadata:\n\n"
        
        # Add structured project information
        if summary.get('name'):
            message += f"Project Name: {summary['name']}\n"
        
        if summary.get('description'):
            message += f"Description: {summary['description']}\n"
        
        if summary.get('goals'):
            message += f"Goals: {summary['goals']}\n"
        
        if summary.get('constraints'):
            message += f"Constraints: {summary['constraints']}\n"
        
        if summary.get('timeline'):
            message += f"Timeline: {summary['timeline']}\n"
        
        if summary.get('budget'):
            message += f"Budget: {summary['budget']}\n"
        
        if summary.get('team_size'):
            message += f"Team Size: {summary['team_size']}\n"
        
        message += "\nPlease generate comprehensive project metadata based on this information."
        
        return message
    
    def _parse_metadata_response(self, response_content: str) -> Dict[str, Any]:
        """Parse OpenAI response into metadata dictionary."""
        try:
            import json
            
            # Try to parse JSON response
            metadata_dict = json.loads(response_content)
            
            # Ensure all required fields are present
            required_fields = [
                'title', 'description', 'category', 'tags', 'priority',
                'estimated_duration', 'complexity', 'required_skills',
                'stakeholders', 'success_metrics', 'risks', 'recommendations',
                'confidence_score'
            ]
            
            for field in required_fields:
                if field not in metadata_dict:
                    # Set default values for missing fields
                    if field == 'tags':
                        metadata_dict[field] = []
                    elif field == 'required_skills':
                        metadata_dict[field] = []
                    elif field == 'stakeholders':
                        metadata_dict[field] = []
                    elif field == 'success_metrics':
                        metadata_dict[field] = []
                    elif field == 'risks':
                        metadata_dict[field] = []
                    elif field == 'recommendations':
                        metadata_dict[field] = []
                    elif field == 'priority':
                        metadata_dict[field] = 'medium'
                    elif field == 'complexity':
                        metadata_dict[field] = 'moderate'
                    elif field == 'confidence_score':
                        metadata_dict[field] = 0.8
                    else:
                        metadata_dict[field] = ''
            
            return metadata_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata response: {e}")
            # Return default metadata structure
            return {
                'title': 'Project Title',
                'description': 'Project description',
                'category': 'General',
                'tags': ['project'],
                'priority': 'medium',
                'estimated_duration': 'TBD',
                'complexity': 'moderate',
                'required_skills': ['general'],
                'stakeholders': ['team'],
                'success_metrics': ['completion'],
                'risks': ['unknown'],
                'recommendations': ['plan carefully'],
                'confidence_score': 0.5
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing metadata response: {e}")
            return {}
    
    async def _store_onboarding_result(self, result: ProjectOnboardingResult):
        """Store onboarding result in database."""
        try:
            result_data = result.model_dump()
            result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            self.supabase.table("project_onboarding_results").insert(result_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store onboarding result: {e}")
    
    async def _validate_metadata(self, metadata: ProjectMetadata) -> bool:
        """Validate generated metadata."""
        return await self.validate_metadata(metadata)
    
    async def auto_schedule_user_bots(self, user_id: str) -> Dict[str, Any]:
        """Auto-schedule bots for a specific user's meetings."""
        try:
            logger.info(f"Starting auto-schedule bots for user: {user_id}")
            
            # Get user's upcoming meetings
            meetings = await self._get_user_upcoming_meetings(user_id)
            if not meetings:
                return {
                    'success': True,
                    'message': 'No upcoming meetings found',
                    'scheduled_bots': 0
                }
            
            # Auto-schedule bots for meetings
            scheduled_count = 0
            for meeting in meetings:
                if await self._should_auto_schedule_bot(meeting):
                    success = await self._schedule_meeting_bot(meeting, user_id)
                    if success:
                        scheduled_count += 1
            
            return {
                'success': True,
                'message': f'Auto-scheduled {scheduled_count} bots',
                'scheduled_bots': scheduled_count,
                'total_meetings': len(meetings)
            }
            
        except Exception as e:
            logger.error(f"Auto-schedule bots failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'scheduled_bots': 0
            }
    
    async def auto_schedule_all_bots(self) -> Dict[str, Any]:
        """Auto-schedule bots for all users' meetings."""
        try:
            logger.info("Starting auto-schedule bots for all users")
            
            # Get all active users
            users = await self._get_active_users()
            if not users:
                return {
                    'success': True,
                    'message': 'No active users found',
                    'total_scheduled': 0
                }
            
            # Auto-schedule for each user
            total_scheduled = 0
            for user in users:
                result = await self.auto_schedule_user_bots(user['id'])
                if result.get('success'):
                    total_scheduled += result.get('scheduled_bots', 0)
            
            return {
                'success': True,
                'message': f'Auto-scheduled {total_scheduled} bots total',
                'total_scheduled': total_scheduled,
                'total_users': len(users)
            }
            
        except Exception as e:
            logger.error(f"Auto-schedule all bots failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_scheduled': 0
            }
    
    async def _get_user_upcoming_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's upcoming meetings."""
        try:
            response = self.supabase.table("meetings") \
                .select("*") \
                .eq("user_id", user_id) \
                .gte("start_time", datetime.now().isoformat()) \
                .eq("bot_status", "pending") \
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to get user meetings: {e}")
            return []
    
    async def _should_auto_schedule_bot(self, meeting: Dict[str, Any]) -> bool:
        """Determine if a bot should be auto-scheduled for a meeting."""
        # Check if meeting has a URL
        if not meeting.get('meeting_url'):
            return False
        
        # Check if bot is not already scheduled
        if meeting.get('bot_status') != 'pending':
            return False
        
        # Check if meeting is within next 24 hours
        meeting_time = datetime.fromisoformat(meeting['start_time'])
        if meeting_time > datetime.now() + timedelta(days=1):
            return False
        
        return True
    
    async def _schedule_meeting_bot(self, meeting: Dict[str, Any], user_id: str) -> bool:
        """Schedule a bot for a specific meeting."""
        try:
            # Update meeting with bot configuration
            update_data = {
                'bot_status': 'bot_scheduled',
                'bot_deployment_method': 'auto',
                'auto_bot_notification_sent': True,
                'updated_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table("meetings") \
                .update(update_data) \
                .eq("id", meeting['id']) \
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Failed to schedule bot for meeting {meeting['id']}: {e}")
            return False
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users."""
        try:
            response = self.supabase.table("users") \
                .select("id") \
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []
