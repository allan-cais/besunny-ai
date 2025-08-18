"""
Process inbound emails service for BeSunny.ai Python backend.
Handles incoming email processing, classification, and document creation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class GmailMessage(BaseModel):
    """Gmail message structure."""
    id: str
    thread_id: str
    label_ids: List[str]
    snippet: str
    history_id: str
    internal_date: str
    payload: Dict[str, Any]


class ProcessInboundEmailsResult(BaseModel):
    """Result of processing inbound emails."""
    message_id: str
    success: bool
    document_id: Optional[str] = None
    project_id: Optional[str] = None
    message: str
    error_message: Optional[str] = None
    timestamp: datetime


class ProcessInboundEmailsService:
    """Service for processing inbound emails."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        
        logger.info("Process Inbound Emails Service initialized")
    
    async def process_inbound_email(self, email_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Process an inbound email and create a document.
        
        Args:
            email_data: Email data from Gmail
            user_id: User ID who owns the email
            
        Returns:
            Processing result
        """
        try:
            logger.info(f"Processing inbound email {email_data.get('id')} for user {user_id}")
            
            # Extract email content and metadata
            email_content = await self._extract_email_content(email_data)
            if not email_content:
                return {
                    'success': False,
                    'message': 'Failed to extract email content',
                    'error_message': 'Could not extract email content'
                }
            
            # Create document record
            document_id = await self._create_document_record(email_content, user_id)
            if not document_id:
                return {
                    'success': False,
                    'message': 'Failed to create document record',
                    'error_message': 'Could not create document record'
                }
            
            # Send to classification service
            classification_result = await self._send_to_classification(document_id, email_content, user_id)
            
            # Set up file monitoring if needed
            if email_data.get('attachments'):
                await self._setup_file_monitoring(document_id, user_id, email_data)
            
            logger.info(f"Email {email_data.get('id')} processed successfully")
            return {
                'success': True,
                'message': 'Email processed successfully',
                'document_id': document_id,
                'classification_result': classification_result
            }
            
        except Exception as e:
            logger.error(f"Error processing inbound email: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing email: {str(e)}',
                'error_message': str(e)
            }
    
    async def _extract_email_content(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract content and metadata from email data."""
        try:
            # Extract basic email information
            email_id = email_data.get('id')
            thread_id = email_data.get('threadId')
            snippet = email_data.get('snippet', '')
            
            # Extract headers
            headers = {}
            if email_data.get('payload', {}).get('headers'):
                for header in email_data['payload']['headers']:
                    headers[header.get('name', '').lower()] = header.get('value', '')
            
            # Extract body content
            body_content = await self._extract_body_content(email_data.get('payload', {}))
            
            # Extract attachments
            attachments = await self._extract_attachments(email_data.get('payload', {}))
            
            return {
                'id': email_id,
                'thread_id': thread_id,
                'snippet': snippet,
                'headers': headers,
                'body_content': body_content,
                'attachments': attachments,
                'received_at': email_data.get('internalDate'),
                'labels': email_data.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Error extracting email content: {str(e)}")
            return None
    
    async def _extract_body_content(self, payload: Dict[str, Any]) -> str:
        """Extract body content from email payload."""
        try:
            body_content = ""
            
            # Handle multipart messages
            if payload.get('parts'):
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        if part.get('body', {}).get('data'):
                            import base64
                            body_content = base64.b64decode(part['body']['data']).decode('utf-8')
                            break
                    elif part.get('mimeType') == 'text/html':
                        if part.get('body', {}).get('data'):
                            import base64
                            body_content = base64.b64decode(part['body']['data']).decode('utf-8')
                            break
            else:
                # Single part message
                if payload.get('body', {}).get('data'):
                    import base64
                    body_content = base64.b64decode(payload['body']['data']).decode('utf-8')
            
            return body_content
            
        except Exception as e:
            logger.error(f"Error extracting body content: {str(e)}")
            return ""
    
    async def _extract_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachment information from email payload."""
        try:
            attachments = []
            
            if payload.get('parts'):
                for part in payload['parts']:
                    if part.get('filename') and part.get('mimeType') != 'text/plain' and part.get('mimeType') != 'text/html':
                        attachments.append({
                            'filename': part.get('filename'),
                            'mime_type': part.get('mimeType'),
                            'size': part.get('body', {}).get('size', 0),
                            'part_id': part.get('partId')
                        })
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error extracting attachments: {str(e)}")
            return []
    
    async def _create_document_record(self, email_content: Dict[str, Any], user_id: str) -> Optional[str]:
        """Create a document record for the email."""
        try:
            supabase = await self.supabase
            
            # Extract email details
            subject = email_content['headers'].get('subject', 'No Subject')
            from_email = email_content['headers'].get('from', 'Unknown')
            to_email = email_content['headers'].get('to', '')
            cc_email = email_content['headers'].get('cc', '')
            
            # Create document data
            document_data = {
                'title': subject,
                'author': from_email,
                'source': 'gmail',
                'source_id': email_content['id'],
                'summary': email_content['snippet'],
                'content': email_content['body_content'],
                'received_at': email_content['received_at'],
                'created_by': user_id,
                'metadata': {
                    'thread_id': email_content['thread_id'],
                    'to': to_email,
                    'cc': cc_email,
                    'labels': email_content['labels'],
                    'attachments': email_content['attachments']
                }
            }
            
            # Insert document
            result = supabase.table("documents") \
                .insert(document_data) \
                .execute()
            
            if result.data:
                document_id = result.data[0]['id']
                logger.info(f"Document created with ID: {document_id}")
                return document_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating document record: {str(e)}")
            return None
    
    async def _send_to_classification(self, document_id: str, email_content: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Send document to classification service."""
        try:
            from ...services.classification import DocumentClassificationService
            
            classification_service = DocumentClassificationService()
            
            # Prepare classification request
            classification_request = {
                'document_id': document_id,
                'user_id': user_id,
                'type': 'email',
                'source': 'gmail',
                'title': email_content['headers'].get('subject', 'No Subject'),
                'author': email_content['headers'].get('from', 'Unknown'),
                'received_at': email_content['received_at'],
                'content': email_content['body_content'],
                'metadata': {
                    'gmail_message_id': email_content['id'],
                    'thread_id': email_content['thread_id'],
                    'attachments': email_content['attachments']
                }
            }
            
            # Classify document
            result = await classification_service.classify_document(classification_request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending to classification: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _setup_file_monitoring(self, document_id: str, user_id: str, email_data: Dict[str, Any]) -> None:
        """Set up file monitoring for attachments."""
        try:
            # This would integrate with the drive file subscription service
            # to monitor any attached files for changes
            logger.info(f"Setting up file monitoring for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error setting up file monitoring: {str(e)}")
    
    async def process_batch_emails(self, emails: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """
        Process multiple inbound emails in batch.
        
        Args:
            emails: List of email data
            user_id: User ID who owns the emails
            
        Returns:
            List of processing results
        """
        try:
            logger.info(f"Processing batch of {len(emails)} emails for user {user_id}")
            
            results = []
            for email in emails:
                result = await self.process_inbound_email(email, user_id)
                results.append(result)
            
            logger.info(f"Batch processing completed for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch emails: {str(e)}")
            return []
