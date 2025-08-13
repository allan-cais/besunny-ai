"""
Main email processing service for BeSunny.ai Python backend.
Ports functionality from the Supabase edge function process-inbound-emails.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re
from fastapi import HTTPException

from ...core.database import get_supabase
from ...core.config import get_settings
from ...services.classification import DocumentClassificationService
from ...models.schemas.email import (
    GmailMessage,
    EmailProcessingResult,
    ClassificationPayload,
    DocumentCreate,
    Project,
    User
)

logger = logging.getLogger(__name__)


class EmailProcessingService:
    """Main service for processing inbound emails."""
    
    def __init__(self):
        self.settings = get_settings()
        self.classification_service = DocumentClassificationService()
    
    async def process_inbound_emails(self, messages: List[GmailMessage]) -> List[EmailProcessingResult]:
        """Process multiple inbound email messages."""
        results = []
        
        for message in messages:
            try:
                result = await self.process_inbound_email(message)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process email {message.id}: {e}")
                results.append(EmailProcessingResult(
                    success=False,
                    message=f"Error processing email: {str(e)}",
                    gmail_message_id=message.id
                ))
        
        return results
    
    async def process_inbound_email(self, gmail_message: GmailMessage) -> EmailProcessingResult:
        """Process a single inbound email message."""
        try:
            # Extract email headers
            to_header = self._get_header_value(gmail_message.payload.headers, 'to')
            subject_header = self._get_header_value(gmail_message.payload.headers, 'subject')
            from_header = self._get_header_value(gmail_message.payload.headers, 'from')
            
            if not to_header:
                return EmailProcessingResult(
                    success=False,
                    message="No 'To' header found in email"
                )
            
            # Extract username from the "To" address
            username = self._extract_username_from_email(to_header)
            
            if not username:
                return EmailProcessingResult(
                    success=False,
                    message="No valid username found in email address"
                )
            
            # Find user by username
            user = await self._find_user_by_username(username)
            
            if not user:
                # Log the attempt but don't create a document
                await self._log_email_processing(
                    gmail_message.id,
                    to_header,
                    username,
                    subject_header,
                    from_header,
                    'user_not_found',
                    f"User not found for username: {username}"
                )
                
                return EmailProcessingResult(
                    success=False,
                    message=f"User not found for username: {username}"
                )
            
            # Create document
            document_id = await self._create_document_from_email(
                user.id,
                gmail_message,
                subject_header or 'No Subject',
                from_header or 'Unknown Sender'
            )
            
            # Get the created document
            document = await self._get_document(document_id)
            
            if not document:
                raise Exception("Failed to retrieve created document")
            
            # Get active projects for the user
            projects = await self._get_active_projects_for_user(user.id)
            
            # Build classification payload
            classification_payload = self._build_classification_payload(
                document, user, projects
            )
            
            # Send to classification service
            classification_result = await self.classification_service.classify_document(
                classification_payload
            )
            
            # Update document with classification result
            if classification_result and classification_result.classified_project_id:
                await self._update_document_project(
                    document_id, 
                    classification_result.classified_project_id
                )
                
                # Update project classification tracking
                await self._update_project_classification_tracking(
                    classification_result.classified_project_id
                )
            
            # Check for Drive file sharing and set up automatic Drive watch
            await self._handle_drive_file_sharing(
                gmail_message, document_id, to_header, username
            )
            
            # Log the processing
            await self._log_email_processing(
                user.id,
                gmail_message.id,
                to_header,
                username,
                subject_header,
                from_header,
                'processed',
                document_id=document_id,
                classification_success=bool(classification_result)
            )
            
            return EmailProcessingResult(
                success=True,
                message=f"Email processed successfully for user: {username}",
                user_id=user.id,
                document_id=document_id,
                classification_result=classification_result
            )
            
        except Exception as e:
            logger.error(f"Error processing inbound email: {e}")
            
            # Log the error
            await self._log_email_processing(
                gmail_message.id,
                self._get_header_value(gmail_message.payload.headers, 'to') or 'unknown',
                self._extract_username_from_email(
                    self._get_header_value(gmail_message.payload.headers, 'to') or ''
                ),
                self._get_header_value(gmail_message.payload.headers, 'subject'),
                self._get_header_value(gmail_message.payload.headers, 'from'),
                'failed',
                error_message=str(e)
            )
            
            return EmailProcessingResult(
                success=False,
                message=f"Error processing email: {str(e)}"
            )
    
    def _get_header_value(self, headers: List[Dict[str, str]], name: str) -> Optional[str]:
        """Get header value by name."""
        header = next((h for h in headers if h['name'].lower() == name.lower()), None)
        return header['value'] if header else None
    
    def _extract_username_from_email(self, email: str) -> Optional[str]:
        """Extract username from email address."""
        if not email:
            return None
        
        # Extract the part before @
        parts = email.split('@')
        if len(parts) != 2:
            return None
        
        local_part = parts[0]
        
        # Check if it contains a plus sign (plus-addressing)
        if local_part.includes('+'):
            plus_parts = local_part.split('+')
            if len(plus_parts) >= 2:
                return plus_parts[1]  # Return the part after the plus sign
        
        return None
    
    async def _find_user_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        try:
            supabase = await get_supabase()
            if not supabase.client:
                raise Exception("Supabase client not available")
            
            # Call the get_user_by_username RPC function
            result = supabase.client.rpc('get_user_by_username', {
                'search_username': username
            }).execute()
            
            if result.data:
                user_data = result.data
                return User(
                    id=user_data['user_id'],
                    username=username,
                    email=user_data.get('email')
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by username {username}: {e}")
            return None
    
    async def _create_document_from_email(
        self, 
        user_id: str, 
        gmail_message: GmailMessage,
        subject: str,
        sender: str
    ) -> str:
        """Create a document record from email."""
        try:
            supabase = await get_supabase()
            if not supabase.client:
                raise Exception("Supabase client not available")
            
            # Create document record
            result = supabase.client.table('documents').insert({
                'project_id': None,  # Will be assigned by classification service
                'source': 'gmail',
                'source_id': gmail_message.id,
                'title': subject or 'No Subject',
                'author': sender,
                'received_at': datetime.fromtimestamp(
                    int(gmail_message.internalDate) / 1000
                ).isoformat(),
                'created_by': user_id,
                'summary': gmail_message.snippet or '',
                'mimetype': gmail_message.payload.mimeType or None
            }).execute()
            
            if not result.data:
                raise Exception("Failed to create document")
            
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error creating document from email: {e}")
            raise
    
    async def _get_document(self, document_id: str) -> Optional[DocumentCreate]:
        """Get document by ID."""
        try:
            supabase = await get_supabase()
            if not supabase.client:
                raise Exception("Supabase client not available")
            
            result = supabase.client.table('documents').select('*').eq('id', document_id).execute()
            
            if result.data:
                return DocumentCreate(**result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    async def _get_active_projects_for_user(self, user_id: str) -> List[Project]:
        """Get active projects for user."""
        try:
            supabase = await get_supabase()
            if not supabase.client:
                raise Exception("Supabase client not available")
            
            result = supabase.client.table('projects').select(
                "id, name, description, status, normalized_tags, categories, reference_keywords, notes, classification_signals, entity_patterns, created_by"
            ).eq('created_by', user_id).in_('status', ['active', 'in_progress']).order('last_classification_at', desc=True).execute()
            
            if result.data:
                return [Project(**project) for project in result.data]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting active projects for user {user_id}: {e}")
            return []
    
    def _build_classification_payload(
        self, 
        document: DocumentCreate, 
        user: User, 
        projects: List[Project]
    ) -> ClassificationPayload:
        """Build classification payload for AI processing."""
        return ClassificationPayload(
            document_id=document.id,
            user_id=user.id,
            type='email',
            source='gmail',
            title=document.title,
            author=document.author,
            received_at=document.received_at,
            content=document.summary,
            metadata={
                'gmail_message_id': document.source_id,
                'filename': document.title,
                'mimetype': document.mimetype,
                'notification_type': None
            },
            project_metadata=[
                {
                    'project_id': project.id,
                    'normalized_tags': project.normalized_tags,
                    'categories': project.categories,
                    'reference_keywords': project.reference_keywords,
                    'notes': project.notes,
                    'classification_signals': project.classification_signals,
                    'entity_patterns': project.entity_patterns
                }
                for project in projects
            ]
        )
    
    async def _update_document_project(self, document_id: str, project_id: str):
        """Update document with classified project ID."""
        try:
            supabase = await get_supabase()
            if not supabase.client:
                raise Exception("Supabase client not available")
            
            supabase.client.table('documents').update({
                'project_id': project_id
            }).eq('id', document_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating document project: {e}")
            raise
    
    async def _update_project_classification_tracking(self, project_id: str):
        """Update project classification tracking."""
        try:
            supabase = await get_supabase()
            if not supabase.client:
                raise Exception("Supabase client not available")
            
            supabase.client.table('projects').update({
                'last_classification_at': datetime.utcnow().isoformat(),
                'pinecone_document_count': supabase.client.rpc('increment_pinecone_count', {'project_id': project_id})
            }).eq('id', project_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating project classification tracking: {e}")
            raise
    
    async def _handle_drive_file_sharing(
        self, 
        gmail_message: GmailMessage, 
        document_id: str, 
        to_header: str, 
        username: str
    ):
        """Handle Drive file sharing in emails."""
        try:
            email_content = gmail_message.snippet or ''
            drive_url_pattern = r'https://drive\.google\.com/[^\s]+'
            drive_urls = re.findall(drive_url_pattern, email_content)
            
            if drive_urls:
                logger.info(f"Found Drive URLs in virtual email: {len(drive_urls)} URLs")
                
                # Extract file IDs from Drive URLs and set up watches
                for drive_url in drive_urls:
                    file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', drive_url)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        logger.info(f"Setting up automatic Drive watch for file: {file_id}")
                        
                        # TODO: Implement Drive watch setup
                        # This would call the Drive monitoring service
                        # await self.drive_service.setup_file_watch(file_id, document_id)
                        
        except Exception as e:
            logger.error(f"Error handling Drive file sharing: {e}")
    
    async def _log_email_processing(
        self,
        user_id: Optional[str] = None,
        gmail_message_id: str = None,
        inbound_address: str = None,
        extracted_username: str = None,
        subject: str = None,
        sender: str = None,
        status: str = None,
        document_id: Optional[str] = None,
        classification_success: Optional[bool] = None,
        error_message: Optional[str] = None
    ):
        """Log email processing activity."""
        try:
            supabase = await get_supabase()
            if not supabase.client:
                logger.warning("Supabase client not available for logging")
                return
            
            log_data = {
                'gmail_message_id': gmail_message_id,
                'inbound_address': inbound_address,
                'extracted_username': extracted_username,
                'subject': subject,
                'sender': sender,
                'status': status,
                'processed_at': datetime.utcnow().isoformat(),
            }
            
            if user_id:
                log_data['user_id'] = user_id
            
            if document_id:
                log_data['document_id'] = document_id
            
            if classification_success is not None:
                log_data['classification_success'] = classification_success
            
            if error_message:
                log_data['error_message'] = error_message
            
            supabase.client.table('email_processing_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging email processing: {e}")
