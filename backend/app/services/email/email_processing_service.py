"""
Complete Email Processing Service for BeSunny.ai
Handles webhook processing, virtual email parsing, and multi-table storage.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import re
from googleapiclient.errors import HttpError

from ...core.supabase_config import get_supabase_service_client
from ...services.email.gmail_service import GmailService

logger = logging.getLogger(__name__)

class EmailProcessingService:
    """Complete email processing service for handling incoming emails."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
        self.gmail_service = GmailService()
        self.master_email = "ai@besunny.ai"
        
    async def process_gmail_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Gmail webhook and store email data in all relevant tables.
        
        Args:
            webhook_data: Raw webhook payload from Gmail
            
        Returns:
            Dict with processing results
        """
        try:
            logger.info("Starting Gmail webhook processing")
            
            # Step 1: Extract message data from webhook
            message_data = webhook_data.get('message', {})
            data = message_data.get('data', '')
            
            if not data:
                logger.warning("No data field in webhook")
                return {"status": "error", "message": "No data field in webhook"}
            
            # Step 2: Decode and parse webhook data
            decoded_data = await self._decode_webhook_data(data)
            if not decoded_data:
                return {"status": "error", "message": "Failed to decode webhook data"}
            
            # Step 3: Extract key information
            email_address = decoded_data.get('emailAddress')
            history_id = decoded_data.get('historyId')
            
            if not email_address or not history_id:
                return {"status": "error", "message": "Missing email address or history ID"}
            
            logger.info(f"Processing webhook for {email_address}, history ID: {history_id}")
            
            # Step 4: Get Gmail history to find new messages
            new_messages = await self._get_gmail_history(email_address, history_id)
            if not new_messages:
                logger.info("No new messages found in history")
                return {"status": "success", "message": "No new messages to process"}
            
            # Step 5: Process each new message
            processing_results = []
            for message_id in new_messages:
                try:
                    result = await self._process_single_email(message_id, email_address)
                    processing_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing message {message_id}: {e}")
                    processing_results.append({
                        "message_id": message_id,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Step 6: Return processing summary
            successful = sum(1 for r in processing_results if r.get("status") == "success")
            total = len(processing_results)
            
            logger.info(f"Email processing complete: {successful}/{total} successful")
            
            return {
                "status": "success",
                "message": f"Processed {total} emails, {successful} successful",
                "total_processed": total,
                "successful": successful,
                "results": processing_results
            }
            
        except Exception as e:
            logger.error(f"Error in process_gmail_webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _decode_webhook_data(self, data: str) -> Optional[Dict[str, Any]]:
        """Decode base64 webhook data."""
        try:
            import base64
            import json
            
            decoded_bytes = base64.b64decode(data)
            decoded_string = decoded_bytes.decode('utf-8')
            return json.loads(decoded_string)
            
        except Exception as e:
            logger.error(f"Failed to decode webhook data: {e}")
            return None
    
    async def _get_gmail_history(self, email_address: str, history_id: str) -> list:
        """Get new messages from Gmail history."""
        try:
            # Get Gmail history to see what changed
            history = self.gmail_service.gmail_service.users().history().list(
                userId=email_address,
                startHistoryId=history_id
            ).execute()
            
            new_message_ids = []
            
            # Extract new message IDs from history
            for history_item in history.get('history', []):
                for message_added in history_item.get('messagesAdded', []):
                    message_id = message_added['message']['id']
                    new_message_ids.append(message_id)
            
            logger.info(f"Found {len(new_message_ids)} new messages in history")
            return new_message_ids
            
        except Exception as e:
            logger.error(f"Error getting Gmail history: {e}")
            return []
    
    async def _process_single_email(self, message_id: str, email_address: str) -> Dict[str, Any]:
        """Process a single email message and store in all relevant tables."""
        try:
            logger.info(f"Processing email {message_id}")
            
            # Step 1: Get full email content from Gmail
            email_content = await self._fetch_email_content(message_id, email_address)
            if not email_content:
                return {"message_id": message_id, "status": "error", "message": "Failed to fetch email content"}
            
            # Step 2: Parse email headers and content
            parsed_email = self._parse_email_content(email_content)
            
            # Step 3: Extract virtual email information
            virtual_email_info = self._extract_virtual_email_info(parsed_email['to'])
            
            # Step 4: Store in email_processing_logs (master level)
            log_id = await self._store_email_processing_log(
                message_id, email_address, parsed_email, virtual_email_info
            )
            
            # Step 5: Store in virtual_email_detections (alias level)
            detection_id = None
            if virtual_email_info['is_virtual']:
                detection_id = await self._store_virtual_email_detection(
                    message_id, virtual_email_info, log_id
                )
            
            # Step 6: Store in documents (content storage)
            document_id = await self._store_email_document(
                message_id, parsed_email, virtual_email_info, log_id
            )
            
            # Step 7: Update processing log with document ID
            if document_id:
                await self._update_processing_log_document_id(log_id, document_id)
            
            logger.info(f"Successfully processed email {message_id}")
            
            return {
                "message_id": message_id,
                "status": "success",
                "log_id": log_id,
                "detection_id": detection_id,
                "document_id": document_id,
                "virtual_email": virtual_email_info['virtual_email'],
                "username": virtual_email_info['username']
            }
            
        except Exception as e:
            logger.error(f"Error processing email {message_id}: {e}")
            return {"message_id": message_id, "status": "error", "error": str(e)}
    
    async def _fetch_email_content(self, message_id: str, email_address: str) -> Optional[Dict[str, Any]]:
        """Fetch full email content from Gmail API."""
        try:
            message = self.gmail_service.gmail_service.users().messages().get(
                userId=email_address,
                id=message_id,
                format='full'
            ).execute()
            
            return message
            
        except HttpError as e:
            logger.error(f"Gmail API error fetching message {message_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None
    
    def _parse_email_content(self, email_content: Dict[str, Any]) -> Dict[str, Any]:
        """Parse email content and extract key information."""
        try:
            payload = email_content.get('payload', {})
            headers = payload.get('headers', [])
            
            # Extract headers
            subject = self._extract_header(headers, 'Subject') or 'No Subject'
            sender = self._extract_header(headers, 'From') or 'Unknown Sender'
            to_address = self._extract_header(headers, 'To') or 'Unknown Recipient'
            date = self._extract_header(headers, 'Date') or datetime.now().isoformat()
            
            # Extract body content
            body = self._extract_email_body(payload)
            
            # Extract snippet
            snippet = email_content.get('snippet', '')
            
            return {
                'subject': subject,
                'sender': sender,
                'to': to_address,
                'date': date,
                'body': body,
                'snippet': snippet,
                'gmail_id': email_content.get('id'),
                'thread_id': email_content.get('threadId'),
                'label_ids': email_content.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Error parsing email content: {e}")
            return {}
    
    def _extract_header(self, headers: list, name: str) -> Optional[str]:
        """Extract header value by name."""
        for header in headers:
            if header.get('name') == name:
                return header.get('value')
        return None
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body content."""
        try:
            if payload.get('body', {}).get('data'):
                import base64
                body_data = payload['body']['data']
                decoded = base64.urlsafe_b64decode(body_data + '=' * (-len(body_data) % 4))
                return decoded.decode('utf-8', errors='ignore')
            
            # Handle multipart messages
            if payload.get('parts'):
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        if part.get('body', {}).get('data'):
                            import base64
                            body_data = part['body']['data']
                            decoded = base64.urlsafe_b64decode(body_data + '=' * (-len(body_data) % 4))
                            return decoded.decode('utf-8', errors='ignore')
            
            return "No readable body content"
            
        except Exception as e:
            logger.error(f"Error extracting email body: {e}")
            return "Error extracting body content"
    
    def _extract_virtual_email_info(self, to_address: str) -> Dict[str, Any]:
        """Extract virtual email information from recipient address."""
        try:
            # Check if this is a virtual email (ai+username@besunny.ai)
            virtual_pattern = r'ai\+([^@]+)@besunny\.ai'
            match = re.match(virtual_pattern, to_address)
            
            if match:
                username = match.group(1)
                return {
                    'is_virtual': True,
                    'virtual_email': to_address,
                    'username': username,
                    'master_email': self.master_email
                }
            else:
                # Check if it's the master account
                if to_address == self.master_email:
                    return {
                        'is_virtual': False,
                        'virtual_email': to_address,
                        'username': None,
                        'master_email': self.master_email
                    }
                else:
                    return {
                        'is_virtual': False,
                        'virtual_email': to_address,
                        'username': None,
                        'master_email': None
                    }
                    
        except Exception as e:
            logger.error(f"Error extracting virtual email info: {e}")
            return {
                'is_virtual': False,
                'virtual_email': to_address,
                'username': None,
                'master_email': None
            }
    
    async def _store_email_processing_log(
        self, 
        message_id: str, 
        email_address: str, 
        parsed_email: Dict[str, Any],
        virtual_email_info: Dict[str, Any]
    ) -> str:
        """Store email processing log in email_processing_logs table."""
        try:
            log_data = {
                'gmail_message_id': message_id,
                'inbound_address': email_address,
                'extracted_username': virtual_email_info.get('username'),
                'subject': parsed_email.get('subject'),
                'sender': parsed_email.get('sender'),
                'received_at': parsed_email.get('date'),
                'processed_at': datetime.now().isoformat(),
                'status': 'success',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('email_processing_logs').insert(log_data).execute()
            
            if result.data:
                log_id = result.data[0]['id']
                logger.info(f"Stored email processing log: {log_id}")
                return log_id
            else:
                raise Exception("No log ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing email processing log: {e}")
            raise
    
    async def _store_virtual_email_detection(
        self, 
        message_id: str, 
        virtual_email_info: Dict[str, Any],
        log_id: str
    ) -> str:
        """Store virtual email detection in virtual_email_detections table."""
        try:
            detection_data = {
                'virtual_email': virtual_email_info['virtual_email'],
                'username': virtual_email_info['username'],
                'gmail_message_id': message_id,
                'email_type': 'alias',
                'detected_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('virtual_email_detections').insert(detection_data).execute()
            
            if result.data:
                detection_id = result.data[0]['id']
                logger.info(f"Stored virtual email detection: {detection_id}")
                return detection_id
            else:
                raise Exception("No detection ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing virtual email detection: {e}")
            raise
    
    async def _store_email_document(
        self, 
        message_id: str, 
        parsed_email: Dict[str, Any],
        virtual_email_info: Dict[str, Any],
        log_id: str
    ) -> str:
        """Store email content in documents table."""
        try:
            document_data = {
                'title': parsed_email.get('subject'),
                'summary': parsed_email.get('snippet'),
                'author': parsed_email.get('sender'),
                'received_at': parsed_email.get('date'),
                'source': 'gmail',
                'source_id': message_id,
                'type': 'email',
                'status': 'received',
                'created_at': datetime.now().isoformat(),
                'created_by': None,  # System created
                'project_id': None,  # Will be assigned later
                'knowledge_space_id': None  # Will be assigned later
            }
            
            result = self.supabase.table('documents').insert(document_data).execute()
            
            if result.data:
                document_id = result.data[0]['id']
                logger.info(f"Stored email document: {document_id}")
                return document_id
            else:
                raise Exception("No document ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error storing email document: {e}")
            raise
    
    async def _update_processing_log_document_id(self, log_id: str, document_id: str):
        """Update processing log with document ID reference."""
        try:
            self.supabase.table('email_processing_logs').update({
                'document_id': document_id,
                'updated_at': datetime.now().isoformat()
            }).eq('id', log_id).execute()
            
            logger.info(f"Updated processing log {log_id} with document ID {document_id}")
            
        except Exception as e:
            logger.error(f"Error updating processing log: {e}")
    
    async def get_processing_status(self, message_id: str) -> Dict[str, Any]:
        """Get processing status for a specific email."""
        try:
            # Check processing log
            log_result = self.supabase.table('email_processing_logs').select('*').eq('gmail_message_id', message_id).execute()
            
            if log_result.data:
                log_entry = log_result.data[0]
                
                # Check virtual email detection
                detection_result = self.supabase.table('virtual_email_detections').select('*').eq('gmail_message_id', message_id).execute()
                
                # Check document
                document_result = self.supabase.table('documents').select('*').eq('source_id', message_id).execute()
                
                return {
                    'message_id': message_id,
                    'processing_log': log_entry,
                    'virtual_email_detection': detection_result.data[0] if detection_result.data else None,
                    'document': document_result.data[0] if document_result.data else None,
                    'status': 'complete' if log_entry and detection_result.data and document_result.data else 'partial'
                }
            else:
                return {
                    'message_id': message_id,
                    'status': 'not_found'
                }
                
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {'status': 'error', 'error': str(e)}
