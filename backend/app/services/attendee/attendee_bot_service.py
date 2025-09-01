"""
Attendee Bot Service - Updated to integrate with existing meetings table and unified webhook tracking
Handles attendee bot webhooks and transcript ingestion for calendar invitations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

from ...core.supabase_config import get_supabase_service_client
from ...services.webhook.webhook_tracking_service import WebhookTrackingService

logger = logging.getLogger(__name__)

class AttendeeBotService:
    """Service for managing attendee bots and transcript ingestion."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
        self.webhook_tracker = WebhookTrackingService()
        
    async def process_meeting_ended_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook notification that a meeting has ended and transcript is ready.
        
        Args:
            webhook_data: Webhook payload from attendee service
            
        Returns:
            Dict with processing results
        """
        try:
            logger.info("Processing attendee bot meeting ended webhook")
            
            # Track webhook receipt
            await self.webhook_tracker.track_webhook_activity(
                service="attendee_bot",
                webhook_type="meeting_ended",
                success=True
            )
            
            # Extract meeting information from webhook
            meeting_id = webhook_data.get('meeting_id')
            username = webhook_data.get('username')
            transcript_url = webhook_data.get('transcript_url')
            meeting_duration = webhook_data.get('meeting_duration')
            
            if not all([meeting_id, username, transcript_url]):
                # Track missing data error
                await self.webhook_tracker.track_webhook_activity(
                    service="attendee_bot",
                    webhook_type="meeting_ended_missing_data",
                    success=False,
                    error_message="Missing required webhook data"
                )
                return {"status": "error", "message": "Missing required webhook data"}
            
            # Find the original calendar invitation document
            document_id = await self._find_calendar_invitation_document(username, meeting_id)
            if not document_id:
                # Track document not found error
                await self.webhook_tracker.track_webhook_activity(
                    service="attendee_bot",
                    webhook_type="meeting_ended_document_not_found",
                    success=False,
                    error_message="Calendar invitation document not found"
                )
                return {"status": "error", "message": "Calendar invitation document not found"}
            
            # Ingest the transcript
            transcript_result = await self._ingest_meeting_transcript(
                meeting_id, username, transcript_url, meeting_duration, document_id
            )
            
            if transcript_result.get("status") == "success":
                logger.info(f"Successfully processed meeting transcript for {username}")
                
                # Track successful transcript processing
                await self.webhook_tracker.track_webhook_activity(
                    service="attendee_bot",
                    webhook_type="transcript_processing_complete",
                    success=True
                )
                
                # Update attendee bot status
                await self._update_attendee_bot_status(meeting_id, "completed")
                
                # Update email processing log
                await self._update_processing_log_transcript_complete(document_id, transcript_result)
                
                return transcript_result
            else:
                logger.error(f"Failed to process meeting transcript for {username}")
                
                # Track transcript processing failure
                await self.webhook_tracker.track_webhook_activity(
                    service="attendee_bot",
                    webhook_type="transcript_processing_failed",
                    success=False,
                    error_message=transcript_result.get("message")
                )
                
                return transcript_result
                
        except Exception as e:
            logger.error(f"Error processing attendee bot webhook: {e}")
            
            # Track webhook processing error
            await self.webhook_tracker.track_webhook_activity(
                service="attendee_bot",
                webhook_type="meeting_ended_processing_error",
                success=False,
                error_message=str(e)
            )
            
            return {"status": "error", "message": str(e)}
    
    async def _find_calendar_invitation_document(self, username: str, meeting_id: str) -> Optional[str]:
        """Find the calendar invitation document for a user and meeting."""
        try:
            # First, try to find the meeting in the meetings table
            meeting_result = self.supabase.table('meetings').select('id, title, virtual_email_attendee').eq('virtual_email_attendee', f'ai+{username}@besunny.ai').execute()
            
            if meeting_result.data:
                # Found the meeting, now look for the corresponding document
                meeting = meeting_result.data[0]
                result = self.supabase.table('documents').select('id').eq('source', 'attendee_bot').eq('type', 'calendar_invitation').eq('title', meeting['title']).execute()
                
                if result.data:
                    return result.data[0]['id']
            
            # Fallback: look for calendar invitation documents for this user
            result = self.supabase.table('documents').select('id').eq('source', 'attendee_bot').eq('type', 'calendar_invitation').execute()
            
            if result.data:
                # For now, return the first match - in production you'd want more sophisticated matching
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding calendar invitation document: {e}")
            return None
    
    async def _ingest_meeting_transcript(
        self, 
        meeting_id: str, 
        username: str, 
        transcript_url: str, 
        meeting_duration: Optional[str],
        original_document_id: str
    ) -> Dict[str, Any]:
        """Ingest meeting transcript and store it in meetings table and documents table."""
        try:
            logger.info(f"Starting transcript ingestion for meeting {meeting_id}")
            
            # Fetch transcript content from URL
            transcript_content = await self._fetch_transcript_content(transcript_url)
            if not transcript_content:
                return {"status": "error", "message": "Failed to fetch transcript content"}
            
            # Store transcript in both meetings table and documents table
            transcript_document_id = await self._store_transcript_document(
                meeting_id, username, transcript_content, meeting_duration, original_document_id
            )
            
            if transcript_document_id:
                logger.info(f"Successfully stored transcript document: {transcript_document_id}")
                return {
                    "status": "success",
                    "message": "Transcript ingested successfully",
                    "transcript_document_id": transcript_document_id,
                    "meeting_id": meeting_id,
                    "username": username
                }
            else:
                return {"status": "error", "message": "Failed to store transcript document"}
                
        except Exception as e:
            logger.error(f"Error ingesting meeting transcript: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _fetch_transcript_content(self, transcript_url: str) -> Optional[str]:
        """Fetch transcript content from the provided URL."""
        try:
            # This would integrate with your transcript service
            # For now, we'll simulate fetching content
            logger.info(f"Fetching transcript content from: {transcript_url}")
            
            # In production, you'd make an HTTP request to fetch the transcript
            # For now, return simulated content
            simulated_transcript = f"""
            Meeting Transcript
            URL: {transcript_url}
            Fetched at: {datetime.now().isoformat()}
            
            This is a simulated transcript. In production, this would contain the actual meeting content.
            """
            
            return simulated_transcript
            
        except Exception as e:
            logger.error(f"Error fetching transcript content: {e}")
            return None
    
    async def _store_transcript_document(
        self, 
        meeting_id: str, 
        username: str, 
        transcript_content: str, 
        meeting_duration: Optional[str],
        original_document_id: str
    ) -> Optional[str]:
        """Store meeting transcript in meetings table and documents table."""
        try:
            # First, update the meetings table with transcript data
            meeting_update_data = {
                'transcript': transcript_content,
                'transcript_retrieved_at': datetime.now().isoformat(),
                'transcript_summary': transcript_content[:500] + "..." if len(transcript_content) > 500 else transcript_content,
                'transcript_processing_status': 'completed',
                'bot_status': 'completed',
                'updated_at': datetime.now().isoformat()
            }
            
            # Find the meeting to update
            meeting_result = self.supabase.table('meetings').select('id').eq('virtual_email_attendee', f'ai+{username}@besunny.ai').execute()
            
            if meeting_result.data:
                meeting_id_db = meeting_result.data[0]['id']
                
                # Update the meeting with transcript data
                self.supabase.table('meetings').update(meeting_update_data).eq('id', meeting_id_db).execute()
                logger.info(f"Updated meeting {meeting_id_db} with transcript data")
                
                # Also store in documents table for consistency
                transcript_data = {
                    'title': f"Meeting Transcript - {meeting_id}",
                    'summary': transcript_content[:500] + "..." if len(transcript_content) > 500 else transcript_content,
                    'author': username,
                    'received_at': datetime.now().isoformat(),
                    'source': 'attendee_bot',
                    'source_id': meeting_id,
                    'type': 'meeting_transcript',
                    'status': 'completed',
                    'created_at': datetime.now().isoformat(),
                    'created_by': username,
                    'project_id': None,  # Will be assigned later
                    'knowledge_space_id': None,  # Will be assigned later
                    'transcript_metadata': {
                        'meeting_id': meeting_id,
                        'username': meeting_id_db,
                        'meeting_duration': meeting_duration,
                        'original_document_id': original_document_id,
                        'transcript_url': f"meeting_{meeting_id}",
                        'ingested_at': datetime.now().isoformat()
                    }
                }
                
                result = self.supabase.table('documents').insert(transcript_data).execute()
                
                if result.data:
                    return result.data[0]['id']
                else:
                    raise Exception("No transcript document ID returned from database insert")
            else:
                logger.warning(f"No meeting found for user {username}")
                return None
                
        except Exception as e:
            logger.error(f"Error storing transcript document: {e}")
            return None
    
    async def _update_attendee_bot_status(self, meeting_id: str, status: str):
        """Update attendee bot status in the meetings table."""
        try:
            # Update the meetings table with bot status
            self.supabase.table('meetings').update({
                'bot_status': status,
                'updated_at': datetime.now().isoformat()
            }).eq('virtual_email_attendee', f'ai+{username}@besunny.ai').execute()
            
            logger.info(f"Updated attendee bot status to {status} for meeting {meeting_id}")
                
        except Exception as e:
            logger.error(f"Error updating attendee bot status: {e}")
    
    async def _update_processing_log_transcript_complete(self, document_id: str, transcript_result: Dict[str, Any]):
        """Update email processing log to indicate transcript is complete."""
        try:
            # Find the processing log entry for this document
            result = self.supabase.table('email_processing_logs').select('*').eq('document_id', document_id).execute()
            
            if result.data:
                log_entry = result.data[0]
                
                # Update the log entry
                self.supabase.table('email_processing_logs').update({
                    'n8n_webhook_sent': True,
                    'n8n_webhook_response': f"Transcript completed: {transcript_result.get('transcript_document_id')}",
                    'updated_at': datetime.now().isoformat()
                }).eq('id', log_entry['id']).execute()
                
                logger.info(f"Updated processing log {log_entry['id']} with transcript completion")
                
        except Exception as e:
            logger.error(f"Error updating processing log: {e}")
    
    async def get_attendee_bot_status(self, username: str) -> List[Dict[str, Any]]:
        """Get status of attendee bots for a specific user from meetings table."""
        try:
            # Get attendee bot information from meetings table
            result = self.supabase.table('meetings').select('*').eq('virtual_email_attendee', f'ai+{username}@besunny.ai').execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting attendee bot status: {e}")
            return []
    
    async def get_meeting_transcripts(self, username: str) -> List[Dict[str, Any]]:
        """Get meeting transcripts for a specific user from meetings table."""
        try:
            # Get transcript data from meetings table
            result = self.supabase.table('meetings').select('*').eq('virtual_email_attendee', f'ai+{username}@besunny.ai').not_.is_('transcript', 'null').execute()
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting meeting transcripts: {e}")
            return []
