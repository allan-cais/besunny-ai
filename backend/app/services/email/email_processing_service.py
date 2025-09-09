"""
Email Processing Service
Handles complete email processing flow including Drive file detection, calendar invitations, and AI classification.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

from ...core.supabase_config import get_supabase_service_client
from ...core.config import get_settings
from ..drive.drive_file_watch_service import DriveFileWatchService
from ..ai.classification_service import ClassificationService

logger = logging.getLogger(__name__)

class EmailProcessingService:
    """Service for processing incoming emails and detecting special content types."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
        self.settings = get_settings()
        self.drive_watch_service = DriveFileWatchService()
        self.classification_service = ClassificationService()
        
        # Email patterns for detection
        self.drive_file_patterns = [
            r'https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
            r'https://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
            r'https://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)',
            r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)',
            r'https://docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)'
        ]
        
        self.calendar_patterns = [
            r'https://meet\.google\.com/([a-zA-Z0-9_-]+)',
            r'https://calendar\.google\.com/event\?action=TEMPLATE',
            r'When: ([^\\n]+)',
            r'Where: ([^\\n]+)',
            r'Google Meet joining info'
        ]
    
    async def process_email(
        self,
        email_data: Dict[str, Any],
        username: str
    ) -> Dict[str, Any]:
        """
        Process a single email through the complete workflow.
        
        Args:
            email_data: Email data from Gmail API
            username: Username extracted from email alias
            
        Returns:
            Processing result with document ID and metadata
        """
        try:
            logger.info(f"Processing email for user {username}: {email_data.get('subject', 'No subject')}")
            
            # Step 1: Store email processing log
            log_entry = await self._store_email_processing_log(email_data, username)
            
            # Step 2: Store virtual email detection
            detection_entry = await self._store_virtual_email_detection(email_data, username)
            
            # Step 3: Detect content type and extract metadata
            content_type = await self._detect_content_type(email_data)
            logger.info(f"Detected content type: {content_type}")
            
            # Step 4: Store in documents table with appropriate source
            document_id = await self._store_email_document(email_data, username, content_type)
            
            # Step 5: Handle special content types BEFORE classification
            if content_type['type'] == 'drive_file':
                logger.info("Handling drive file sharing")
                await self._handle_drive_file_sharing(email_data, username, document_id)
            elif content_type['type'] == 'calendar_invitation':
                logger.info("Handling calendar invitation")
                try:
                    await self._handle_calendar_invitation(email_data, username, document_id)
                    logger.info("Calendar invitation handling completed successfully")
                except Exception as e:
                    logger.error(f"Calendar invitation handling failed, but continuing with email processing: {e}")
            else:
                logger.info(f"No special content handling for type: {content_type['type']}")
            
            # Step 6: AI Classification to user projects (after special content handling)
            # Make classification non-blocking for calendar invitations
            classification_result = None
            try:
                classification_result = await self._classify_email_to_projects(email_data, username, document_id)
                logger.info("Classification completed successfully")
            except Exception as e:
                logger.error(f"Classification failed, but continuing with email processing: {e}")
                classification_result = {'error': str(e)}
            
            # Step 7: Update processing log with completion
            await self._update_processing_log_complete(log_entry['id'], document_id, classification_result)
            
            logger.info(f"Email processing completed for {username}: {document_id}")
            
            return {
                'success': True,
                'document_id': document_id,
                'content_type': content_type['type'],
                'classification': classification_result,
                'username': username
            }
            
        except Exception as e:
            logger.error(f"Error processing email for {username}: {e}")
            return {
                'success': False,
                'error': str(e),
                'username': username
            }
    
    async def process_gmail_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Gmail webhook data and extract email information.
        
        Args:
            webhook_data: Raw webhook data from Gmail
            
        Returns:
            Processing result with status and message
        """
        try:
            logger.info(f"Processing Gmail webhook: {webhook_data}")
            
            # Extract message data from webhook
            message_data = webhook_data.get('message', {})
            if not message_data:
                return {
                    "status": "error",
                    "message": "No message data in webhook",
                    "total_processed": "0",
                    "successful": "0"
                }
            
            # Get the email message ID
            message_id = message_data.get('data')
            if not message_id:
                return {
                    "status": "error", 
                    "message": "No message ID in webhook",
                    "total_processed": "0",
                    "successful": "0"
                }
            
            # Decode the base64 message ID
            import base64
            try:
                decoded_message_id = base64.urlsafe_b64decode(message_id + '=' * (-len(message_id) % 4))
                gmail_message_id = decoded_message_id.decode('utf-8')
                logger.info(f"Decoded Gmail message ID: {gmail_message_id}")
            except Exception as e:
                logger.error(f"Failed to decode message ID: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to decode message ID: {str(e)}",
                    "total_processed": "0",
                    "successful": "0"
                }
            
            # For now, just log the webhook receipt and return success
            # The actual email processing will be handled by the Gmail service
            # when it polls for new messages or processes the message ID
            
            logger.info(f"Gmail webhook processed successfully for message: {gmail_message_id}")
            
            return {
                "status": "success",
                "message": f"Webhook processed for message {gmail_message_id}",
                "total_processed": "1",
                "successful": "1",
                "gmail_message_id": gmail_message_id
            }
            
        except Exception as e:
            logger.error(f"Error processing Gmail webhook: {e}")
            return {
                "status": "error",
                "message": f"Webhook processing error: {str(e)}",
                "total_processed": "0",
                "successful": "0"
            }
    
    async def _detect_content_type(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect the type of content in the email."""
        try:
            content_text = email_data.get('content', '')
            subject = email_data.get('subject', '')
            full_text = f"{subject} {content_text}".lower()
            
            # Check for Drive file sharing
            drive_info = await self._detect_drive_file_sharing(email_data)
            if drive_info:
                return {
                    'type': 'drive_file',
                    'metadata': drive_info,
                    'confidence': 0.9
                }
            
            # Check for calendar invitation
            calendar_info = await self._detect_calendar_invitation(email_data)
            if calendar_info:
                logger.info(f"Calendar invitation detected with metadata: {calendar_info}")
                return {
                    'type': 'calendar_invitation',
                    'metadata': calendar_info,
                    'confidence': 0.8
                }
            else:
                logger.info("No calendar invitation detected")
            
            # Default to normal email
            return {
                'type': 'email',
                'metadata': {},
                'confidence': 1.0
            }
            
        except Exception as e:
            logger.error(f"Error detecting content type: {e}")
            return {'type': 'email', 'metadata': {}, 'confidence': 0.0}
    
    async def _detect_drive_file_sharing(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect if email contains Google Drive file sharing."""
        try:
            content_text = email_data.get('content', '')
            subject = email_data.get('subject', '')
            full_text = f"{subject} {content_text}"
            
            for pattern in self.drive_file_patterns:
                matches = re.findall(pattern, full_text)
                if matches:
                    file_id = matches[0]
                    file_metadata = await self._extract_drive_file_metadata(file_id, full_text)
                    return file_metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting Drive file sharing: {e}")
            return None
    
    async def _extract_drive_file_metadata(self, file_id: str, content_text: str) -> Dict[str, Any]:
        """Extract metadata about the shared Drive file."""
        try:
            # Extract filename from content if possible
            filename_match = re.search(r'([^\\/\\n]+\.(doc|docx|pdf|txt|sheet|slides))', content_text, re.IGNORECASE)
            filename = filename_match.group(1) if filename_match else f"file_{file_id}"
            
            # Extract Google Meet URLs if present
            meet_urls = re.findall(r'https://meet\.google\.com/([a-zA-Z0-9_-]+)', content_text)
            
            return {
                'file_id': file_id,
                'filename': filename,
                'file_url': f"https://drive.google.com/file/d/{file_id}",
                'meet_urls': meet_urls,
                'detected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting Drive file metadata: {e}")
            return {'file_id': file_id, 'filename': f"file_{file_id}"}
    
    async def _detect_calendar_invitation(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect if email is a calendar invitation."""
        try:
            content_text = email_data.get('content', '')
            subject = email_data.get('subject', '')
            full_text = f"{subject} {content_text}"
            
            logger.info(f"Checking for calendar invitation in email: {subject}")
            logger.info(f"Content preview: {content_text[:200]}...")
            
            # Check for calendar invitation patterns
            has_meet_url = bool(re.search(r'https://meet\.google\.com/', full_text))
            has_when = bool(re.search(r'When:', full_text))
            has_where = bool(re.search(r'Where:', full_text))
            
            logger.info(f"Calendar detection - Meet URL: {has_meet_url}, When: {has_when}, Where: {has_where}")
            
            if has_meet_url or (has_when and has_where):
                logger.info("Calendar invitation detected, extracting metadata")
                calendar_info = await self._extract_calendar_invitation_metadata(full_text)
                logger.info(f"Calendar metadata extracted: {calendar_info}")
                return calendar_info
            else:
                logger.info("No calendar invitation patterns found")
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting calendar invitation: {e}")
            return None
    
    async def _extract_calendar_invitation_metadata(self, content_text: str) -> Dict[str, Any]:
        """Extract metadata from calendar invitation."""
        try:
            logger.info(f"Extracting calendar metadata from content: {content_text[:300]}...")
            
            # Extract Google Meet URLs
            meet_urls = re.findall(r'https://meet\.google\.com/([a-zA-Z0-9_-]+)', content_text)
            logger.info(f"Found meet URLs: {meet_urls}")
            
            # Extract event title from subject or content
            event_title = "Calendar Invitation"  # Default
            
            # Extract meeting time information
            meeting_time = {}
            when_match = re.search(r'When: ([^\\n]+)', content_text)
            if when_match:
                meeting_time['when'] = when_match.group(1).strip()
                logger.info(f"Found meeting time: {meeting_time['when']}")
            
            # Extract organizer information
            organizer = "Unknown"  # Default
            
            metadata = {
                'event_title': event_title,
                'meet_urls': meet_urls,
                'meeting_time': meeting_time,
                'organizer': organizer,
                'detected_at': datetime.now().isoformat()
            }
            
            logger.info(f"Extracted calendar metadata: {metadata}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting calendar invitation metadata: {e}")
            return {'event_title': 'Calendar Invitation'}
    
    async def _store_email_document(
        self, 
        email_data: Dict[str, Any], 
        username: str, 
        content_type: Dict[str, Any]
    ) -> str:
        """Store email in documents table with appropriate source."""
        try:
            # Determine source based on content type
            if content_type['type'] == 'drive_file':
                source = 'google_drive'
            elif content_type['type'] == 'calendar_invitation':
                source = 'attendee_bot'
            else:
                source = 'email'
            
            document_data = {
                'title': email_data.get('subject', 'No Subject'),
                'summary': email_data.get('content', '')[:500] + "..." if len(email_data.get('content', '')) > 500 else email_data.get('content', ''),
                'author': email_data.get('from', username),
                'received_at': email_data.get('date', datetime.now().isoformat()),
                'source': source,
                'source_id': email_data.get('id', ''),
                'type': content_type['type'],
                'status': 'processed',
                'created_at': datetime.now().isoformat(),
                'created_by': username,
                'project_id': None,  # Will be assigned by classification
                'knowledge_space_id': None,  # Will be assigned later
                'metadata': {
                    'email_id': email_data.get('id'),
                    'content_type': content_type,
                    'username': username,
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            result = self.supabase.table('documents').insert(document_data).execute()
            
            if result.data:
                document_id = result.data[0]['id']
                logger.info(f"Email document stored: {document_id} (source: {source})")
                return document_id
            else:
                raise Exception("No document ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing email document: {e}")
            raise
    
    async def _handle_drive_file_sharing(
        self, 
        email_data: Dict[str, Any], 
        username: str, 
        document_id: str
    ):
        """Handle Drive file sharing by setting up file watch."""
        try:
            drive_info = await self._detect_drive_file_sharing(email_data)
            if drive_info:
                # Set up Drive file watch
                watch_id = await self.drive_watch_service.setup_file_watch(
                    file_id=drive_info['file_id'],
                    document_id=document_id,
                    project_id=None  # Will be assigned by classification
                )
                
                if watch_id:
                    logger.info(f"Drive file watch set up: {watch_id}")
                    # Update processing log to indicate Drive watch is active
                    await self._update_processing_log_drive_watch(drive_info['file_id'], watch_id)
                else:
                    logger.warning("Failed to set up Drive file watch")
                    
        except Exception as e:
            logger.error(f"Error handling Drive file sharing: {e}")
    
    async def _handle_calendar_invitation(
        self, 
        email_data: Dict[str, Any], 
        username: str, 
        document_id: str
    ):
        """Handle calendar invitation by setting up attendee bot and initiating full workflow."""
        try:
            logger.info(f"Handling calendar invitation for {username}, document {document_id}")
            calendar_info = await self._detect_calendar_invitation(email_data)
            logger.info(f"Calendar info from handler: {calendar_info}")
            
            if calendar_info and calendar_info.get('meet_urls'):
                # Get the first Google Meet URL
                meet_url = calendar_info['meet_urls'][0]
                logger.info(f"Found Google Meet URL: {meet_url}")
                
                # Get user ID for the username
                user_id = await self._get_user_id_by_username(username)
                if not user_id:
                    logger.error(f"User not found for username: {username}")
                    return
                
                logger.info(f"Found user ID: {user_id}")
                
                # Set up attendee bot and initiate full workflow
                try:
                    await self._initiate_calendar_bot_workflow(
                        calendar_info, username, user_id, document_id, meet_url
                    )
                    logger.info(f"Calendar invitation workflow initiated successfully for {username}")
                except Exception as bot_error:
                    logger.error(f"Bot workflow failed for {username}, but calendar invitation was detected: {bot_error}")
                    # Don't re-raise the error - we want email processing to continue
            else:
                logger.warning("No Google Meet URL found in calendar invitation")
                    
        except Exception as e:
            logger.error(f"Error handling calendar invitation: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't re-raise the error - we want email processing to continue
    
    async def _setup_attendee_bot(self, calendar_info: Dict[str, Any], username: str, document_id: str) -> Optional[str]:
        """Set up an attendee bot for a calendar invitation using existing tables."""
        try:
            logger.info(f"Setting up attendee bot for user {username} and event {calendar_info.get('event_title')}")
            
            # Create a meeting record in the meetings table
            meeting_data = {
                'user_id': None,  # Will be linked when user is found
                'project_id': None,  # Will be assigned later
                'google_calendar_event_id': None,  # Will be updated when calendar sync is implemented
                'title': calendar_info.get('event_title'),
                'description': f"Calendar invitation for {username}",
                'meeting_url': calendar_info.get('meet_urls', [None])[0] if calendar_info.get('meet_urls') else None,
                'start_time': None,  # Will be parsed from calendar_info.meeting_time
                'end_time': None,  # Will be calculated based on duration
                'attendee_bot_id': None,  # Will be assigned when bot is created
                'bot_name': f"AttendeeBot_{username}",
                'bot_chat_message': f"Bot scheduled for {username}",
                'transcript': None,  # Will be populated when transcript is ready
                'transcript_url': None,  # Will be updated when transcript is available
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'event_status': 'confirmed',
                'bot_status': 'pending',
                'transcript_retrieved_at': None,
                'transcript_summary': None,
                'transcript_duration_seconds': None,
                'next_poll_time': None,
                'bot_configuration': {
                    'username': username,
                    'event_title': calendar_info.get('event_title'),
                    'meet_urls': calendar_info.get('meet_urls', []),
                    'meeting_time': calendar_info.get('meeting_time', {}),
                    'organizer': calendar_info.get('organizer'),
                    'document_id': document_id,
                    'setup_method': 'calendar_invitation_email'
                },
                'last_polled_at': None,
                'transcript_metadata': None,
                'bot_deployment_message': f"Bot scheduled via email invitation for {username}",
                'auto_scheduled_via_calendar': False,
                'virtual_email_attendee': f'ai+{username}@besunny.ai',
                'auto_bot_notification': True,
                'transcript_participants': None,
                'transcript_speakers': None,
                'transcript_segments': None,
                'transcript_audio_url': None,
                'transcript_recording_url': None,
                'transcript_language': None,
                'transcript_processing_status': 'pending',
                'transcript_quality_score': None,
                'transcript_confidence_score': None
            }
            
            try:
                result = self.supabase.table('meetings').insert(meeting_data).execute()
                if result.data:
                    meeting_id = result.data[0]['id']
                    logger.info(f"Meeting {meeting_id} created for {username}")
                    
                    # Also log the bot scheduling operation
                    await self._log_bot_scheduling(username, meeting_id, None, 'calendar_invite', meeting_data['bot_configuration'], True)
                    
                    return meeting_id
                else:
                    logger.warning("No meeting ID returned from database insert")
                    return None
            except Exception as e:
                logger.error(f"Could not store meeting in meetings table: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error setting up attendee bot: {e}")
            return None
    
    async def _log_bot_scheduling(self, username: str, meeting_id: str, bot_id: Optional[str], scheduling_type: str, bot_configuration: Dict[str, Any], success: bool):
        """Log bot scheduling operation in bot_scheduling_logs table."""
        try:
            log_data = {
                'user_id': None,  # Will be linked when user is found
                'meeting_id': meeting_id,
                'bot_id': bot_id,
                'scheduling_type': scheduling_type,
                'bot_configuration': bot_configuration,
                'success': success,
                'error_message': None if success else "Bot scheduling failed",
                'processing_time_ms': None,  # Could be calculated if needed
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('bot_scheduling_logs').insert(log_data).execute()
            logger.info(f"Bot scheduling logged for meeting {meeting_id}")
            
        except Exception as e:
            logger.warning(f"Could not log bot scheduling: {e}")
    
    async def _classify_email_to_projects(
        self, 
        email_data: Dict[str, Any], 
        username: str, 
        document_id: str
    ) -> Dict[str, Any]:
        """Classify email to user projects using AI classification."""
        try:
            # Get user ID from username
            user_result = self.supabase.table('users').select('id').eq('username', username).execute()
            if not user_result.data:
                logger.warning(f"User not found for username: {username}")
                return self._create_unclassified_result("User not found")
            
            user_id = user_result.data[0]['id']
            
            # Prepare content for classification
            classification_content = {
                'type': 'email',
                'source_id': document_id,
                'author': email_data.get('from', username),
                'date': email_data.get('date', datetime.now().isoformat()),
                'subject': email_data.get('subject', ''),
                'content_text': email_data.get('content', ''),
                'attachments': email_data.get('attachments', []),
                'metadata': {
                    'email_id': email_data.get('id'),
                    'username': username,
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            # Get AI classification
            classification_result = await self.classification_service.classify_content(
                content=classification_content,
                user_id=user_id
            )
            
            logger.info(f"Email classified for {username}: {classification_result.get('project_id', 'unclassified')} (confidence: {classification_result.get('confidence', 0)})")
            return classification_result
            
        except Exception as e:
            logger.error(f"Error classifying email to projects: {e}")
            return self._create_unclassified_result(f"Classification error: {str(e)}")
    
    def _create_unclassified_result(self, reason: str) -> Dict[str, Any]:
        """Create an unclassified result."""
        return {
            "project_id": "",
            "confidence": 0.0,
            "unclassified": True,
            "document": {
                "source": "email",
                "source_id": "",
                "author": "",
                "date": datetime.now().isoformat(),
                "content_text": "",
                "matched_tags": [],
                "inferred_tags": [],
                "classification_notes": reason
            }
        }
    
    async def _store_email_processing_log(self, email_data: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Store email processing log entry."""
        try:
            log_data = {
                'gmail_message_id': email_data.get('id'),
                'inbound_address': email_data.get('to'),
                'extracted_username': username,
                'subject': email_data.get('subject'),
                'sender': email_data.get('from'),
                'received_at': email_data.get('date', datetime.now().isoformat()),
                'processed_at': datetime.now().isoformat(),
                'status': 'success',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('email_processing_logs').insert(log_data).execute()
            
            if result.data:
                log_entry = result.data[0]
                logger.info(f"Email processing log created: {log_entry['id']}")
                return log_entry
            else:
                raise Exception("No log entry ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing email processing log: {e}")
            raise
    
    async def _store_virtual_email_detection(self, email_data: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Store virtual email detection entry."""
        try:
            detection_data = {
                'virtual_email': f'ai+{username}@besunny.ai',
                'username': username,
                'gmail_message_id': email_data.get('id'),
                'email_type': 'alias',
                'detected_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('virtual_email_detections').insert(detection_data).execute()
            
            if result.data:
                detection_entry = result.data[0]
                logger.info(f"Virtual email detection stored: {detection_entry['id']}")
                return detection_entry
            else:
                raise Exception("No detection entry ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing virtual email detection: {e}")
            raise
    
    async def _update_processing_log_complete(
        self, 
        log_id: str, 
        document_id: str, 
        classification_result: Dict[str, Any]
    ):
        """Update processing log to indicate completion."""
        try:
            update_data = {
                'status': 'success',
                'document_id': document_id,
                'project_id': classification_result.get('project_id') if not classification_result.get('unclassified') else None
            }
            
            self.supabase.table('email_processing_logs').update(update_data).eq('id', log_id).execute()
            logger.info(f"Processing log {log_id} updated to completed")
            
        except Exception as e:
            logger.error(f"Error updating processing log: {e}")
    
    async def _update_processing_log_drive_watch(self, file_id: str, watch_id: str):
        """Update processing log with Drive watch information."""
        try:
            # Find the log entry for this file
            result = self.supabase.table('email_processing_logs').select('*').eq('document_id', file_id).execute()
            
            if result.data:
                log_entry = result.data[0]
                
                self.supabase.table('email_processing_logs').update({
                    'drive_watch_id': watch_id,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', log_entry['id']).execute()
                
                logger.info(f"Updated processing log {log_entry['id']} with Drive watch info")
                
        except Exception as e:
            logger.error(f"Error updating processing log: {e}")
    
    async def _get_user_id_by_username(self, username: str) -> Optional[str]:
        """Get user ID by username."""
        try:
            result = self.supabase.table('users').select('id').eq('username', username).single().execute()
            return result.data['id'] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user ID for username {username}: {e}")
            return None
    
    async def _initiate_calendar_bot_workflow(
        self, 
        calendar_info: Dict[str, Any], 
        username: str, 
        user_id: str, 
        document_id: str, 
        meet_url: str
    ):
        """Initiate the complete calendar bot workflow: schedule bot, poll status, get transcript, classify, and embed."""
        try:
            logger.info(f"Starting calendar bot workflow for {username} with meet URL: {meet_url}")
            logger.info(f"Calendar info: {calendar_info}")
            logger.info(f"User ID: {user_id}, Document ID: {document_id}")
            
            # Step 1: Schedule the attendee bot
            logger.info("Calling _schedule_calendar_bot...")
            bot_result = await self._schedule_calendar_bot(meet_url, username, user_id, calendar_info)
            logger.info(f"Bot scheduling result: {bot_result}")
            
            if not bot_result.get('success'):
                logger.error(f"Failed to schedule bot for {username}: {bot_result.get('error')}")
                return
            
            bot_id = bot_result.get('bot_id')
            meeting_id = bot_result.get('meeting_id')
            
            # Step 2: Bot will be processed via webhook when it ends
            # No need for background monitoring - webhook will handle transcript processing
            
            logger.info(f"Calendar bot workflow started for {username}, bot_id: {bot_id}, meeting_id: {meeting_id}")
            
        except Exception as e:
            logger.error(f"Error initiating calendar bot workflow: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _schedule_calendar_bot(
        self, 
        meet_url: str, 
        username: str, 
        user_id: str, 
        calendar_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule an attendee bot for a calendar invitation."""
        try:
            logger.info(f"Scheduling calendar bot for meet_url: {meet_url}, username: {username}, user_id: {user_id}")
            
            from ..attendee.attendee_service import AttendeeService
            
            attendee_service = AttendeeService()
            
            # Check for existing meeting with same Google Meet URL
            logger.info("Checking for existing meeting...")
            existing_meeting = await self._find_existing_meeting_by_url(meet_url, user_id)
            
            if existing_meeting:
                logger.info(f"Found existing meeting {existing_meeting['id']} for URL {meet_url}")
                
                # Check if meeting already has a bot
                if existing_meeting.get('attendee_bot_id'):
                    logger.info(f"Meeting {existing_meeting['id']} already has bot {existing_meeting['attendee_bot_id']}")
                    return {
                        'success': True,
                        'bot_id': existing_meeting['attendee_bot_id'],
                        'meeting_id': existing_meeting['id'],
                        'existing_meeting': True
                    }
                
                # Schedule bot for existing meeting
                bot_result = await self._schedule_bot_for_existing_meeting(
                    meet_url, username, user_id, existing_meeting, attendee_service
                )
                
                if bot_result.get('success'):
                    return {
                        'success': True,
                        'bot_id': bot_result.get('bot_id'),
                        'meeting_id': existing_meeting['id'],
                        'existing_meeting': True
                    }
                else:
                    return {
                        'success': False,
                        'error': bot_result.get('error', 'Failed to schedule bot for existing meeting')
                    }
            
            # No existing meeting found, create new meeting and schedule bot
            logger.info(f"No existing meeting found for URL {meet_url}, creating new meeting")
            
            # Prepare bot options
            bot_options = {
                'meeting_url': meet_url,
                'bot_name': f'Sunny AI Notetaker ({username})',
                'bot_chat_message': {
                    'message': f'Hi, I\'m here to transcribe this meeting for {username}!',
                    'to': 'everyone'
                }
            }
            
            # Create the bot
            bot_result = await attendee_service.create_bot_for_meeting(bot_options, user_id)
            
            if bot_result.get('success'):
                # Store meeting record
                meeting_id = await self._store_calendar_meeting(
                    meet_url, username, user_id, bot_result, calendar_info
                )
                
                return {
                    'success': True,
                    'bot_id': bot_result.get('bot_id'),
                    'meeting_id': meeting_id,
                    'existing_meeting': False
                }
            else:
                return {
                    'success': False,
                    'error': bot_result.get('error', 'Failed to create bot')
                }
                
        except Exception as e:
            logger.error(f"Error scheduling calendar bot: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _store_calendar_meeting(
        self, 
        meet_url: str, 
        username: str, 
        user_id: str, 
        bot_result: Dict[str, Any], 
        calendar_info: Dict[str, Any]
    ) -> str:
        """Store calendar meeting record in meetings table."""
        try:
            meeting_data = {
                'user_id': user_id,
                'project_id': None,  # Will be assigned by classification
                'google_calendar_event_id': None,
                'title': calendar_info.get('event_title', 'Calendar Invitation'),
                'description': f"Calendar invitation for {username}",
                'meeting_url': meet_url,
                'start_time': None,  # Could be parsed from calendar_info
                'end_time': None,
                'attendee_bot_id': bot_result.get('bot_id'),
                'bot_name': bot_result.get('bot_name', f'Sunny AI Notetaker ({username})'),
                'bot_chat_message': bot_result.get('bot_chat_message', ''),
                'transcript': None,
                'transcript_url': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'event_status': 'confirmed',
                'bot_status': 'scheduled',
                'transcript_retrieved_at': None,
                'transcript_summary': None,
                'transcript_duration_seconds': None,
                'next_poll_time': None,
                'bot_configuration': {
                    'username': username,
                    'event_title': calendar_info.get('event_title'),
                    'meet_urls': calendar_info.get('meet_urls', []),
                    'meeting_time': calendar_info.get('meeting_time', {}),
                    'organizer': calendar_info.get('organizer'),
                    'setup_method': 'calendar_invitation_email'
                },
                'last_polled_at': None,
                'transcript_metadata': None,
                'bot_deployment_message': f"Bot scheduled via email invitation for {username}",
                'auto_scheduled_via_calendar': False,
                'virtual_email_attendee': f'ai+{username}@besunny.ai',
                'auto_bot_notification': True,
                'transcript_participants': None,
                'transcript_speakers': None,
                'transcript_segments': None,
                'transcript_audio_url': None,
                'transcript_recording_url': None,
                'transcript_language': None,
                'transcript_processing_status': 'pending',
                'transcript_quality_score': None,
                'transcript_confidence_score': None
            }
            
            result = self.supabase.table('meetings').insert(meeting_data).execute()
            
            if result.data:
                meeting_id = result.data[0]['id']
                logger.info(f"Calendar meeting stored: {meeting_id}")
                return meeting_id
            else:
                raise Exception("No meeting ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing calendar meeting: {e}")
            raise
    
    async def _find_existing_meeting_by_url(self, meet_url: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Find existing meeting by Google Meet URL and user ID."""
        try:
            result = self.supabase.table('meetings').select('*').eq('meeting_url', meet_url).eq('user_id', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            # No meeting found is not an error, just return None
            if "No rows found" in str(e) or "PGRST116" in str(e):
                return None
            logger.error(f"Error finding existing meeting by URL: {e}")
            return None
    
    async def _schedule_bot_for_existing_meeting(
        self, 
        meet_url: str, 
        username: str, 
        user_id: str, 
        existing_meeting: Dict[str, Any], 
        attendee_service
    ) -> Dict[str, Any]:
        """Schedule a bot for an existing meeting."""
        try:
            logger.info(f"Scheduling bot for existing meeting {existing_meeting['id']}")
            
            # Prepare bot options
            bot_options = {
                'meeting_url': meet_url,
                'bot_name': f'Sunny AI Notetaker ({username})',
                'bot_chat_message': {
                    'message': f'Hi, I\'m here to transcribe this meeting for {username}!',
                    'to': 'everyone'
                }
            }
            
            # Create the bot
            bot_result = await attendee_service.create_bot_for_meeting(bot_options, user_id)
            
            if bot_result.get('success'):
                # Update existing meeting with bot information
                await self._update_existing_meeting_with_bot(
                    existing_meeting['id'], bot_result, username
                )
                
                return {
                    'success': True,
                    'bot_id': bot_result.get('bot_id')
                }
            else:
                return {
                    'success': False,
                    'error': bot_result.get('error', 'Failed to create bot')
                }
                
        except Exception as e:
            logger.error(f"Error scheduling bot for existing meeting: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _update_existing_meeting_with_bot(
        self, 
        meeting_id: str, 
        bot_result: Dict[str, Any], 
        username: str
    ):
        """Update existing meeting record with bot information."""
        try:
            update_data = {
                'attendee_bot_id': bot_result.get('bot_id'),
                'bot_name': bot_result.get('bot_name', f'Sunny AI Notetaker ({username})'),
                'bot_chat_message': bot_result.get('bot_chat_message', ''),
                'bot_status': 'scheduled',
                'bot_deployment_method': 'automatic',
                'auto_scheduled_via_email': True,
                'virtual_email_attendee': f'ai+{username}@besunny.ai',
                'bot_configuration': {
                    'username': username,
                    'setup_method': 'calendar_invitation_email',
                    'bot_id': bot_result.get('bot_id'),
                    'scheduled_at': datetime.now().isoformat()
                },
                'updated_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
            logger.info(f"Updated existing meeting {meeting_id} with bot information")
            
        except Exception as e:
            logger.error(f"Error updating existing meeting with bot: {e}")
            raise
    
