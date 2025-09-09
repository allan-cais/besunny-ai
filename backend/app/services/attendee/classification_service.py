"""
Classification service for meeting transcripts.
Handles automatic classification of meeting transcripts to projects.
"""

import logging
from typing import Dict, Any, Optional, List
import json

from ...core.database import get_supabase

logger = logging.getLogger(__name__)

class ClassificationService:
    """Service for classifying meeting transcripts to projects."""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def classify_meeting_transcript(
        self, 
        bot_id: str, 
        transcript: str, 
        metadata: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Classify a meeting transcript to determine the appropriate project.
        
        Args:
            bot_id: The bot ID
            transcript: The meeting transcript text
            metadata: Bot metadata including meeting details
            user_id: The user ID
            
        Returns:
            Dict with classification result including project_id if successful
        """
        try:
            logger.info(f"Starting classification for bot {bot_id}")
            
            # Get user's projects for classification
            projects = await self._get_user_projects(user_id)
            if not projects:
                logger.warning(f"No projects found for user {user_id}")
                return {"success": False, "error": "No projects available for classification"}
            
            # Extract meeting context from metadata
            meeting_context = self._extract_meeting_context(metadata, transcript)
            
            # Perform classification using AI service
            classification_result = await self._perform_ai_classification(
                transcript=transcript,
                meeting_context=meeting_context,
                projects=projects
            )
            
            if classification_result.get('success'):
                project_id = classification_result.get('project_id')
                confidence = classification_result.get('confidence', 0.0)
                
                # Only accept classification if confidence is above threshold
                if confidence >= 0.7:  # 70% confidence threshold
                    logger.info(f"Classification successful for bot {bot_id}: project {project_id} (confidence: {confidence})")
                    return {
                        "success": True,
                        "project_id": project_id,
                        "confidence": confidence,
                        "reasoning": classification_result.get('reasoning', '')
                    }
                else:
                    logger.info(f"Classification confidence too low for bot {bot_id}: {confidence}")
                    return {"success": False, "error": f"Low confidence classification: {confidence}"}
            else:
                logger.warning(f"AI classification failed for bot {bot_id}: {classification_result.get('error')}")
                return {"success": False, "error": classification_result.get('error', 'Classification failed')}
                
        except Exception as e:
            logger.error(f"Error classifying transcript for bot {bot_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's projects for classification."""
        try:
            result = self.supabase.table('projects').select('*').eq('user_id', user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching projects for user {user_id}: {e}")
            return []
    
    def _extract_meeting_context(self, metadata: Dict[str, Any], transcript: str) -> Dict[str, Any]:
        """Extract meeting context from metadata and transcript."""
        try:
            context = {
                "meeting_title": metadata.get('meeting_title', ''),
                "meeting_url": metadata.get('meeting_url', ''),
                "bot_name": metadata.get('bot_name', ''),
                "deployment_method": metadata.get('deployment_method', ''),
                "transcript_length": len(transcript),
                "transcript_preview": transcript[:500] if transcript else "",  # First 500 chars
                "keywords": self._extract_keywords(transcript)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting meeting context: {e}")
            return {}
    
    def _extract_keywords(self, transcript: str) -> List[str]:
        """Extract key terms from transcript for classification."""
        try:
            if not transcript:
                return []
            
            # Simple keyword extraction (can be enhanced with NLP)
            words = transcript.lower().split()
            
            # Filter out common words and extract meaningful terms
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            
            keywords = [word for word in words if len(word) > 3 and word not in stop_words]
            
            # Return top 20 most frequent keywords
            from collections import Counter
            return [word for word, count in Counter(keywords).most_common(20)]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    async def _perform_ai_classification(
        self, 
        transcript: str, 
        meeting_context: Dict[str, Any], 
        projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform AI-based classification using existing AI service."""
        try:
            # Use existing AI service for classification
            from ...services.ai.classification_service import ClassificationService as AIClassificationService
            
            ai_service = AIClassificationService()
            
            # Prepare classification request
            classification_request = {
                "content": transcript,
                "context": meeting_context,
                "projects": projects,
                "classification_type": "meeting_transcript"
            }
            
            # Perform classification
            result = await ai_service.classify_content(classification_request)
            
            if result.get('success'):
                return {
                    "success": True,
                    "project_id": result.get('project_id'),
                    "confidence": result.get('confidence', 0.0),
                    "reasoning": result.get('reasoning', '')
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'AI classification failed')
                }
                
        except Exception as e:
            logger.error(f"Error in AI classification: {e}")
            return {"success": False, "error": str(e)}
    
    async def manual_classify_meeting(
        self, 
        bot_id: str, 
        project_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle manual classification of a meeting by user.
        
        Args:
            bot_id: The bot ID
            project_id: The selected project ID
            user_id: The user ID
            
        Returns:
            Dict with classification result
        """
        try:
            logger.info(f"Manual classification for bot {bot_id} to project {project_id}")
            
            # Update bot with manually selected project
            result = self.supabase.table('meeting_bots').update({
                'project_id': project_id,
                'needs_manual_classification': False,
                'updated_at': 'now()'
            }).eq('bot_id', bot_id).eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"Successfully updated bot {bot_id} with project {project_id}")
                return {
                    "success": True,
                    "project_id": project_id,
                    "message": "Meeting classified successfully"
                }
            else:
                logger.error(f"Failed to update bot {bot_id} with project {project_id}")
                return {
                    "success": False,
                    "error": "Failed to update classification"
                }
                
        except Exception as e:
            logger.error(f"Error in manual classification for bot {bot_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_unclassified_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get meetings that need manual classification.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of unclassified meetings
        """
        try:
            result = self.supabase.table('meeting_bots').select('''
                *,
                meetings!attendee_bot_id(
                    id,
                    title,
                    start_time,
                    end_time,
                    meeting_url
                )
            ''').eq('user_id', user_id).eq('needs_manual_classification', True).is_('project_id', 'null').execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error fetching unclassified meetings for user {user_id}: {e}")
            return []
