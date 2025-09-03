"""
Main email processing service for BeSunny.ai Python backend.
Ports functionality from the Supabase edge function process-inbound-emails.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re
import base64
import uuid
from fastapi import HTTPException

from ...core.database import get_supabase
from ...core.supabase_config import get_supabase_service_client
from ...core.config import get_settings
# from ...services.classification import DocumentClassificationService  # Will be implemented in future version
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
        # self.classification_service = DocumentClassificationService()  # Will be implemented in future version
    
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
            cc_header = self._get_header_value(gmail_message.payload.headers, 'cc')
            bcc_header = self._get_header_value(gmail_message.payload.headers, 'bcc')
            date_header = self._get_header_value(gmail_message.payload.headers, 'date')
            
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
                    gmail_message_id=gmail_message.id,
                    inbound_address=to_header,
                    extracted_username=username,
                    subject=subject_header,
                    sender=from_header,
                    status='user_not_found',
                    error_message=f"User not found for username: {username}"
                )
                
                return EmailProcessingResult(
                    success=False,
                    message=f"User not found for username: {username}"
                )
            
            # Extract email content (body and attachments)
            email_content = await self._extract_email_content(gmail_message)
            
            # Create document with enhanced metadata
            document_id = await self._create_document_from_email(
                user.id,
                gmail_message,
                subject_header or 'No Subject',
                from_header or 'Unknown Sender',
                email_content,
                {
                    'cc': cc_header,
                    'bcc': bcc_header,
                    'date': date_header,
                    'message_id': gmail_message.id,
                    'thread_id': getattr(gmail_message, 'threadId', None),
                    'labels': getattr(gmail_message, 'labelIds', []),
                    'has_attachments': bool(getattr(gmail_message.payload, 'parts', []) if gmail_message.payload else [])
                }
            )
            
            # Get the created document
            document = await self._get_document(document_id)
            
            if not document:
                raise Exception("Failed to retrieve created document")
            
            # Get active projects for the user
            projects = await self._get_active_projects_for_user(user.id)
            
            # Build classification payload
            classification_payload = self._build_classification_payload(
                document, user, projects, email_content
            )
            
            # Send to classification service (to be implemented)
            classification_result = await self._initiate_classification_agent(
                classification_payload
            )
            
            # Update document with classification result
            if classification_result and isinstance(classification_result, dict) and classification_result.get('classified_project_id'):
                await self._update_document_project(
                    document_id, 
                    classification_result['classified_project_id']
                )
                
                # Update project classification tracking
                await self._update_project_classification_tracking(
                    classification_result['classified_project_id']
                )
            
            # Check for Drive file sharing and set up automatic Drive watch
            await self._handle_drive_file_sharing(
                gmail_message, document_id, to_header, username, email_content
            )
            
            # Log the processing
            await self._log_email_processing(
                user_id=user.id,
                gmail_message_id=gmail_message.id,
                inbound_address=to_header,
                extracted_username=username,
                subject=subject_header,
                sender=from_header,
                status='processed',
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
                gmail_message_id=gmail_message.id,
                inbound_address=self._get_header_value(gmail_message.payload.headers, 'to') or 'unknown',
                extracted_username=self._extract_username_from_email(
                    self._get_header_value(gmail_message.payload.headers, 'to') or ''
                ),
                subject=self._get_header_value(gmail_message.payload.headers, 'subject'),
                sender=self._get_header_value(gmail_message.payload.headers, 'from'),
                status='failed',
                error_message=str(e)
            )
            
            return EmailProcessingResult(
                success=False,
                message=f"Error processing email: {str(e)}"
            )
    
    def _get_header_value(self, headers: List[Any], name: str) -> Optional[str]:
        """Get header value by name."""
        header = next((h for h in headers if h.name.lower() == name.lower()), None)
        return header.value if header else None
    
    def _extract_username_from_email(self, email: str) -> Optional[str]:
        """Extract username from email address."""
        if not email:
            logger.warning("No email provided for username extraction")
            return None
        
        logger.info(f"Extracting username from email: '{email}'")
        
        # Extract the part before @
        parts = email.split('@')
        if len(parts) != 2:
            logger.warning(f"Invalid email format: '{email}'")
            return None
        
        local_part = parts[0]
        logger.info(f"Local part of email: '{local_part}'")
        
        # Check if it contains a plus sign (plus-addressing)
        if '+' in local_part:
            plus_parts = local_part.split('+')
            if len(plus_parts) >= 2:
                username = plus_parts[1]  # Return the part after the plus sign
                logger.info(f"Extracted username: '{username}'")
                return username
        
        logger.warning(f"No plus-addressing found in email: '{email}'")
        return None
    
    async def _extract_email_content(self, gmail_message: GmailMessage) -> Dict[str, Any]:
        """Extract full email content including body and attachments."""
        try:
            logger.info(f"Extracting email content for message {gmail_message.id}")
            content = {
                'body_text': '',
                'body_html': '',
                'attachments': [],
                'full_content': ''
            }
            
            # Extract content from payload
            if hasattr(gmail_message, 'payload') and gmail_message.payload:
                logger.info(f"Payload type: {type(gmail_message.payload)}")
                payload_content = self._extract_payload_content(gmail_message.payload)
                logger.info(f"Payload content type: {type(payload_content)}")
                content.update(payload_content)
            
            # Fallback to snippet if no body content found
            if not content['body_text'] and not content['body_html']:
                content['body_text'] = gmail_message.snippet or ''
            
            # Combine all text content for full content
            content['full_content'] = f"{content['body_text']} {content['body_html']}".strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting email content: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'body_text': gmail_message.snippet or '',
                'body_html': '',
                'attachments': [],
                'full_content': gmail_message.snippet or ''
            }
    
    def _extract_payload_content(self, payload: Any, depth: int = 0) -> Dict[str, Any]:
        """Recursively extract content from Gmail message payload."""
        if depth > 10:  # Prevent infinite recursion
            return {}
        
        content = {
            'body_text': '',
            'body_html': '',
            'attachments': []
        }
        
        try:
            # Handle multipart messages
            if payload.mime_type == 'multipart/alternative' or payload.mime_type == 'multipart/mixed':
                if hasattr(payload, 'parts') and payload.parts:
                    for part in payload.parts:
                        part_content = self._extract_payload_content(part, depth + 1)
                        content['body_text'] += part_content.get('body_text', '')
                        content['body_html'] += part_content.get('body_html', '')
                        content['attachments'].extend(part_content.get('attachments', []))
            
            # Handle text content
            elif payload.mime_type == 'text/plain':
                if hasattr(payload, 'body') and payload.body and hasattr(payload.body, 'data'):
                    try:
                        decoded_data = base64.urlsafe_b64decode(payload.body.data + '=' * (-len(payload.body.data) % 4))
                        content['body_text'] = decoded_data.decode('utf-8', errors='ignore')
                    except Exception as e:
                        logger.warning(f"Failed to decode text content: {e}")
            
            elif payload.mime_type == 'text/html':
                if hasattr(payload, 'body') and payload.body and hasattr(payload.body, 'data'):
                    try:
                        decoded_data = base64.urlsafe_b64decode(payload.body.data + '=' * (-len(payload.body.data) % 4))
                        content['body_text'] = decoded_data.decode('utf-8', errors='ignore')
                    except Exception as e:
                        logger.warning(f"Failed to decode HTML content: {e}")
            
            # Handle attachments
            elif payload.mime_type and not payload.mime_type.startswith('text/'):
                if hasattr(payload, 'filename') and payload.filename:
                    attachment_info = {
                        'filename': payload.filename,
                        'mime_type': payload.mime_type,
                        'size': getattr(payload.body, 'size', 0) if hasattr(payload, 'body') else 0,
                        'attachment_id': getattr(payload.body, 'attachment_id', None) if hasattr(payload, 'body') else None
                    }
                    content['attachments'].append(attachment_info)
            
            # Recursively process parts
            if hasattr(payload, 'parts') and payload.parts:
                for part in payload.parts:
                    part_content = self._extract_payload_content(part, depth + 1)
                    content['body_text'] += part_content.get('body_text', '')
                    content['body_html'] += part_content.get('body_html', '')
                    content['attachments'].extend(part_content.get('attachments', []))
                    
        except Exception as e:
            logger.error(f"Error extracting payload content at depth {depth}: {e}")
        
        return content
    
    async def _find_user_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        try:
            # Use service role client to bypass RLS policies
            supabase = get_supabase_service_client()
            if not supabase:
                raise Exception("Supabase service client not available")
            
            logger.info(f"Looking up user with username: '{username}'")
            
            # Query users table directly
            result = supabase.table('users').select('id, username, email').eq('username', username).execute()
            
            logger.info(f"User lookup result: {result.data}")
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                logger.info(f"Found user: {user_data}")
                return User(
                    id=user_data['id'],
                    username=user_data.get('username'),
                    email=user_data.get('email')
                )
            
            logger.warning(f"No user found with username: '{username}'")
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by username {username}: {e}")
            return None
    
    async def _create_document_from_email(
        self, 
        user_id: str, 
        gmail_message: GmailMessage,
        subject: str,
        sender: str,
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Create a document record from email."""
        try:
            supabase = get_supabase()
            if not supabase:
                raise Exception("Supabase client not available")
            
            # Create document record
            result = supabase.table('documents').insert({
                'id': str(uuid.uuid4()),  # Generate UUID for document ID
                'project_id': None,  # Will be assigned by classification service
                'source': 'gmail',
                'source_id': gmail_message.id,
                'title': subject or 'No Subject',
                'author': sender,
                'received_at': datetime.fromtimestamp(
                    int(gmail_message.internal_date) / 1000
                ).isoformat(),
                'created_by': user_id,
                'summary': content.get('full_content', content.get('body_text', '')) # Use full_content for summary
                # Note: metadata and mimetype fields removed as they don't exist in documents table schema
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
            supabase = get_supabase()
            if not supabase:
                raise Exception("Supabase client not available")
            
            result = supabase.table('documents').select('*').eq('id', document_id).execute()
            
            if result.data:
                doc_data = result.data[0]
                # Add default metadata since documents table doesn't have metadata column
                doc_data['metadata'] = {}
                return DocumentCreate(**doc_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    async def _get_active_projects_for_user(self, user_id: str) -> List[Project]:
        """Get active projects for user."""
        try:
            supabase = get_supabase()
            if not supabase:
                raise Exception("Supabase client not available")
            
            result = supabase.table('projects').select(
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
        projects: List[Project],
        content: Dict[str, Any]
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
            content=content['full_content'], # Use full_content for classification
            metadata={
                'gmail_message_id': document.source_id,
                'filename': document.title,
                'mimetype': getattr(document, 'mimetype', None),  # Handle missing mimetype field
                'notification_type': None,
                'metadata': document.metadata # Include all metadata
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
            supabase = get_supabase()
            if not supabase:
                raise Exception("Supabase client not available")
            
            supabase.table('documents').update({
                'project_id': project_id
            }).eq('id', document_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating document project: {e}")
            raise
    
    async def _update_project_classification_tracking(self, project_id: str):
        """Update project classification tracking."""
        try:
            supabase = get_supabase()
            if not supabase:
                raise Exception("Supabase client not available")
            
            supabase.table('projects').update({
                'last_classification_at': datetime.utcnow().isoformat(),
                'pinecone_document_count': supabase.rpc('increment_pinecone_count', {'project_id': project_id})
            }).eq('id', project_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating project classification tracking: {e}")
            raise
    
    async def _handle_drive_file_sharing(
        self, 
        gmail_message: GmailMessage, 
        document_id: str, 
        to_header: str, 
        username: str,
        email_content: Dict[str, Any]
    ):
        """Handle Drive file sharing in emails."""
        try:
            # Import the email alias drive service
            from ...services.drive.email_alias_drive_service import EmailAliasDriveService
            
            drive_service = EmailAliasDriveService()
            
            # Check for Drive URLs in email content
            full_content = email_content.get('full_content', '') + ' ' + email_content.get('body_text', '') + ' ' + email_content.get('body_html', '')
            drive_url_pattern = r'https://drive\.google\.com/[^\s]+'
            drive_urls = re.findall(drive_url_pattern, full_content)
            
            if drive_urls:
                logger.info(f"Found Drive URLs in virtual email: {len(drive_urls)} URLs")
                
                # Extract file IDs from Drive URLs and process them
                for drive_url in drive_urls:
                    file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', drive_url)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        logger.info(f"Processing Drive file from email alias: {file_id}")
                        
                        # Get user ID from username
                        user_id = await self._get_user_id_from_username(username)
                        if user_id:
                            # Process the Drive file using the email alias service
                            result = await drive_service.process_drive_file_from_email(
                                file_id=file_id,
                                document_id=document_id,
                                user_id=user_id,
                                drive_url=drive_url,
                                email_content=email_content
                            )
                            
                            if result['success']:
                                logger.info(f"Drive file {file_id} processed successfully: {result['message']}")
                            else:
                                logger.error(f"Failed to process Drive file {file_id}: {result['error']}")
                        else:
                            logger.warning(f"Could not find user for username: {username}")
            
            # Also check for Drive file attachments
            for attachment in email_content.get('attachments', []):
                if attachment.get('mime_type', '').startswith('application/vnd.google-apps.drive-sdk'):
                    file_id = attachment.get('attachment_id')
                    if file_id:
                        logger.info(f"Processing Drive attachment from email alias: {file_id}")
                        
                        # Get user ID from username
                        user_id = await self._get_user_id_from_username(username)
                        if user_id:
                            # Process the Drive attachment using the email alias service
                            result = await drive_service.process_drive_file_from_email(
                                file_id=file_id,
                                document_id=document_id,
                                user_id=user_id,
                                drive_url=None,
                                email_content=email_content
                            )
                            
                            if result['success']:
                                logger.info(f"Drive attachment {file_id} processed successfully: {result['message']}")
                            else:
                                logger.error(f"Failed to process Drive attachment {file_id}: {result['error']}")
                        else:
                            logger.warning(f"Could not find user for username: {username}")
                        
        except Exception as e:
            logger.error(f"Error handling Drive file sharing: {e}")
    
    async def _get_user_id_from_username(self, username: str) -> Optional[str]:
        """Get user ID from username."""
        try:
            supabase = get_supabase()
            if not supabase:
                return None
            
            result = supabase.table('users').select('id').eq('username', username).single().execute()
            
            if result.data:
                return result.data['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user ID from username {username}: {e}")
            return None
    
    async def _setup_drive_file_watch(self, file_id: str, document_id: str, user_id: str, drive_url: Optional[str]):
        """Set up Drive file watch for monitoring changes."""
        try:
            # Import drive service here to avoid circular imports
            from ...services.drive.drive_service import DriveService
            
            drive_service = DriveService()
            
            # Set up email alias-specific file watch
            watch_id = await drive_service.setup_file_watch_for_email_alias(
                file_id=file_id,
                user_id=user_id,
                document_id=document_id
            )
            
            if watch_id:
                logger.info(f"Drive watch set up successfully for file {file_id}: {watch_id}")
                
                # Update document with file watch information
                await self._update_document_with_drive_info(document_id, file_id, watch_id, drive_url)
            else:
                logger.warning(f"Failed to set up Drive watch for file {file_id}")
                
        except Exception as e:
            logger.error(f"Error setting up Drive watch for file {file_id}: {e}")
    
    async def _store_drive_file_metadata(self, file_id: str, document_id: str, user_id: str, drive_url: Optional[str]):
        """Store Drive file metadata in the documents table."""
        try:
            supabase = get_supabase()
            if not supabase:
                return
            
            # Get file metadata from Google Drive API
            file_metadata = await self._get_drive_file_metadata(file_id, user_id)
            
            if file_metadata:
                # Update document with Drive file information
                update_data = {
                    'file_id': file_id,
                    'source': 'drive_shared',
                    'source_id': file_id,
                    'title': file_metadata.get('name', f'Drive File {file_id}'),
                    'file_size': str(file_metadata.get('size', 0)),
                    'last_synced_at': datetime.utcnow().isoformat()
                    # Note: mimetype, drive_url, and drive_metadata fields removed as they don't exist in documents table schema
                }
                
                supabase.table('documents').update(update_data).eq('id', document_id).execute()
                
                logger.info(f"Updated document {document_id} with Drive file metadata")
            else:
                logger.warning(f"Could not retrieve metadata for Drive file {file_id}")
                
        except Exception as e:
            logger.error(f"Error storing Drive file metadata for file {file_id}: {e}")
    
    async def _get_drive_file_metadata(self, file_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Google Drive API."""
        try:
            # Import drive service here to avoid circular imports
            from ...services.drive.drive_service import DriveService
            
            drive_service = DriveService()
            
            # Get file metadata
            file_metadata = await drive_service.get_file_metadata(file_id, user_id)
            
            if file_metadata:
                return {
                    'id': file_metadata.id,
                    'name': file_metadata.name,
                    'mimeType': file_metadata.mime_type,
                    'size': file_metadata.size,
                    'modifiedTime': file_metadata.modified_time,
                    'parents': file_metadata.parents,
                    'webViewLink': file_metadata.web_view_link
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Drive file metadata for file {file_id}: {e}")
            return None
    
    async def _update_document_with_drive_info(self, document_id: str, file_id: str, watch_id: str, drive_url: Optional[str]):
        """Update document with Drive file watch information."""
        try:
            supabase = get_supabase()
            if not supabase:
                return
            
            update_data = {
                'watch_active': True,
                'drive_watch_id': watch_id,
                'drive_file_id': file_id,
                'drive_url': drive_url,
                'last_synced_at': datetime.utcnow().isoformat()
            }
            
            supabase.table('documents').update(update_data).eq('id', document_id).execute()
            
            logger.info(f"Updated document {document_id} with Drive watch information")
            
        except Exception as e:
            logger.error(f"Error updating document with Drive info: {e}")
    
    async def _log_email_processing(
        self,
        user_id: Optional[str] = None,
        gmail_message_id: Optional[str] = None,
        inbound_address: Optional[str] = None,
        extracted_username: Optional[str] = None,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        status: Optional[str] = None,
        document_id: Optional[str] = None,
        classification_success: Optional[bool] = None,
        error_message: Optional[str] = None
    ):
        """Log email processing activity."""
        try:
            # Use service role client to bypass RLS policies for logging
            supabase = get_supabase_service_client()
            if not supabase:
                logger.warning("Supabase service client not available for logging")
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
            
            supabase.table('email_processing_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging email processing: {e}")
