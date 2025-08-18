"""
Gmail polling service for BeSunny.ai Python backend.
Handles Gmail monitoring, virtual email detection, and email processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel
import base64
import email
import re

from ...core.database import get_supabase
from ...core.config import get_settings
from ...models.schemas.email import Email, VirtualEmail

logger = logging.getLogger(__name__)


class GmailPollingResult(BaseModel):
    """Result of a Gmail polling operation."""
    user_email: str
    messages_processed: int
    virtual_emails_detected: int
    documents_created: int
    processing_time_ms: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime


class VirtualEmailDetection(BaseModel):
    """Virtual email detection result."""
    message_id: str
    to_emails: List[str]
    cc_emails: List[str]
    virtual_emails: List[Dict[str, Any]]
    confidence_score: float
    detected_at: datetime


class GmailPollingService:
    """Service for polling and monitoring Gmail accounts."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        
        logger.info("Gmail Polling Service initialized")
    
    async def poll_gmail_for_user(self, user_email: str) -> Dict[str, Any]:
        """
        Poll Gmail for a specific user.
        
        Args:
            user_email: User's Gmail address
            
        Returns:
            Polling results and metrics
        """
        start_time = datetime.now()
        
        try:
            # Get user ID from email
            user_id = await self._get_user_id_from_email(user_email)
            if not user_id:
                return {
                    'success': False,
                    'error': 'User not found',
                    'user_email': user_email
                }
            
            # Get user's Google credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'No Google credentials found',
                    'user_email': user_email
                }
            
            # Create Gmail API service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get last sync time
            last_sync = await self._get_last_gmail_sync(user_id)
            
            # Get messages since last sync
            messages = await self._get_gmail_messages(service, user_email, last_sync)
            
            # Process messages
            messages_processed = 0
            virtual_emails_detected = 0
            documents_created = 0
            
            for message in messages:
                try:
                    # Check for virtual emails
                    virtual_emails = await self._check_for_virtual_emails(
                        message.get('to', []), 
                        message.get('cc', [])
                    )
                    
                    if virtual_emails:
                        virtual_emails_detected += 1
                        await self._process_virtual_email_detection(
                            user_email, message['id'], virtual_emails
                        )
                    
                    # Process email content
                    email_result = await self._process_email_message(message, user_id)
                    if email_result and email_result.get('document_created'):
                        documents_created += 1
                    
                    messages_processed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process Gmail message: {e}")
                    continue
            
            # Update last sync time
            await self._update_last_gmail_sync(user_id)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            # Create polling result
            result = GmailPollingResult(
                user_email=user_email,
                messages_processed=messages_processed,
                virtual_emails_detected=virtual_emails_detected,
                documents_created=documents_created,
                processing_time_ms=processing_time,
                success=True,
                timestamp=datetime.now()
            )
            
            # Store result
            await self._store_polling_result(result)
            
            logger.info(f"Gmail polling completed for {user_email}: {messages_processed} messages processed, {virtual_emails_detected} virtual emails detected")
            
            return {
                'success': True,
                'user_email': user_email,
                'messages_processed': messages_processed,
                'virtual_emails_detected': virtual_emails_detected,
                'documents_created': documents_created,
                'processing_time_ms': processing_time
            }
            
        except HttpError as e:
            error_message = f"Gmail API error: {e}"
            logger.error(error_message)
            
            result = GmailPollingResult(
                user_email=user_email,
                messages_processed=0,
                virtual_emails_detected=0,
                documents_created=0,
                processing_time_ms=(datetime.now() - start_time).microseconds // 1000,
                success=False,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            await self._store_polling_result(result)
            
            return {
                'success': False,
                'error': error_message,
                'user_email': user_email
            }
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(f"Gmail polling failed for {user_email}: {error_message}")
            
            result = GmailPollingResult(
                user_email=user_email,
                messages_processed=0,
                virtual_emails_detected=0,
                documents_created=0,
                processing_time_ms=(datetime.now() - start_time).microseconds // 1000,
                success=False,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            await self._store_polling_result(result)
            
            return {
                'success': False,
                'error': error_message,
                'user_email': user_email
            }
    
    async def process_virtual_email_detection(self, user_email: str, message_id: str, 
                                           virtual_emails: List[Dict[str, Any]]) -> None:
        """
        Process virtual email detection for a Gmail message.
        
        Args:
            user_email: User's Gmail address
            message_id: Gmail message ID
            virtual_emails: List of detected virtual emails
        """
        try:
            # Create virtual email detection record
            detection_data = {
                'user_email': user_email,
                'message_id': message_id,
                'virtual_emails': virtual_emails,
                'detected_at': datetime.now().isoformat(),
                'status': 'detected'
            }
            
            self.supabase.table("virtual_email_detections").insert(detection_data).execute()
            
            # Create documents for each virtual email
            for virtual_email in virtual_emails:
                await self._create_virtual_email_document(user_email, message_id, virtual_email)
            
            logger.info(f"Processed virtual email detection for message {message_id}: {len(virtual_emails)} virtual emails")
            
        except Exception as e:
            logger.error(f"Failed to process virtual email detection: {e}")
    
    async def check_for_virtual_emails(self, to_emails: List[str], 
                                     cc_emails: List[str]) -> List[Dict[str, Any]]:
        """
        Check if any of the email addresses are virtual emails.
        
        Args:
            to_emails: List of "to" email addresses
            cc_emails: List of "cc" email addresses
            
        Returns:
            List of detected virtual emails
        """
        try:
            all_emails = to_emails + cc_emails
            virtual_emails = []
            
            for email_addr in all_emails:
                if email_addr:
                    # Check if this is a virtual email
                    is_virtual = await self._is_virtual_email(email_addr)
                    if is_virtual:
                        virtual_emails.append({
                            'email': email_addr,
                            'type': 'virtual',
                            'detected_at': datetime.now().isoformat()
                        })
            
            return virtual_emails
            
        except Exception as e:
            logger.error(f"Failed to check for virtual emails: {e}")
            return []
    
    async def extract_email_addresses(self, headers: List[Dict[str, Any]], 
                                    header_name: str) -> List[str]:
        """
        Extract email addresses from Gmail headers.
        
        Args:
            headers: List of Gmail headers
            header_name: Header name to extract from (e.g., 'To', 'Cc')
            
        Returns:
            List of email addresses
        """
        try:
            email_addresses = []
            
            for header in headers:
                if header.get('name') == header_name:
                    value = header.get('value', '')
                    
                    # Extract email addresses using regex
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    emails = re.findall(email_pattern, value)
                    
                    email_addresses.extend(emails)
            
            return list(set(email_addresses))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to extract email addresses: {e}")
            return []
    
    async def smart_gmail_polling(self, user_email: str) -> Dict[str, Any]:
        """
        Smart Gmail polling that optimizes based on user activity and email patterns.
        
        Args:
            user_email: User's Gmail address
            
        Returns:
            Smart polling results
        """
        try:
            # Get Gmail activity metrics
            metrics = await self._get_gmail_activity_metrics(user_email)
            
            # Determine if we should poll based on metrics
            should_poll = await self._should_poll_gmail(user_email, metrics)
            
            if not should_poll:
                return {
                    'skipped': True,
                    'reason': 'Smart polling optimization',
                    'next_poll_in_minutes': metrics.get('next_poll_interval', 30),
                    'user_email': user_email
                }
            
            # Execute polling
            result = await self.poll_gmail_for_user(user_email)
            
            # Update activity metrics
            await self._update_gmail_activity_metrics(user_email, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Smart Gmail polling failed for {user_email}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_email': user_email
            }
    
    # Private helper methods
    
    async def _get_user_id_from_email(self, user_email: str) -> Optional[str]:
        """Get user ID from email address."""
        try:
            result = self.supabase.table("users") \
                .select("id") \
                .eq("email", user_email) \
                .single() \
                .execute()
            
            return result.data.get('id') if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get user ID for email {user_email}: {e}")
            return None
    
    async def _get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for a user."""
        try:
            result = self.supabase.table("google_credentials") \
                .select("access_token, refresh_token, token_uri, client_id, client_secret, scopes") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                cred_data = result.data
                return Credentials(
                    token=cred_data['access_token'],
                    refresh_token=cred_data['refresh_token'],
                    token_uri=cred_data['token_uri'],
                    client_id=cred_data['client_id'],
                    client_secret=cred_data['client_secret'],
                    scopes=cred_data['scopes']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {e}")
            return None
    
    async def _get_last_gmail_sync(self, user_id: str) -> Optional[str]:
        """Get last Gmail sync time for a user."""
        try:
            result = self.supabase.table("gmail_sync_states") \
                .select("last_sync_at") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data.get('last_sync_at') if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get last Gmail sync for user {user_id}: {e}")
            return None
    
    async def _get_gmail_messages(self, service, user_email: str, 
                                 last_sync: Optional[str]) -> List[Dict[str, Any]]:
        """Get Gmail messages since last sync."""
        try:
            if last_sync:
                # Get messages since last sync
                last_sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                query = f'after:{int(last_sync_time.timestamp())}'
            else:
                # First sync - get messages from last 7 days
                week_ago = datetime.now() - timedelta(days=7)
                query = f'after:{int(week_ago.timestamp())}'
            
            # Get message IDs
            response = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()
            
            messages = response.get('messages', [])
            
            # Get full message details
            full_messages = []
            for msg in messages:
                try:
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['To', 'Cc', 'From', 'Subject', 'Date']
                    ).execute()
                    
                    # Extract email addresses
                    headers = message.get('payload', {}).get('headers', [])
                    to_emails = self._extract_email_addresses(headers, 'To')
                    cc_emails = self._extract_email_addresses(headers, 'Cc')
                    
                    full_messages.append({
                        'id': msg['id'],
                        'to': to_emails,
                        'cc': cc_emails,
                        'headers': headers,
                        'internalDate': message.get('internalDate')
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to get message {msg['id']}: {e}")
                    continue
            
            return full_messages
            
        except Exception as e:
            logger.error(f"Failed to get Gmail messages: {e}")
            return []
    
    async def _extract_email_addresses(self, headers: List[Dict[str, Any]], 
                                     header_name: str) -> List[str]:
        """Extract email addresses from Gmail headers."""
        try:
            email_addresses = []
            
            for header in headers:
                if header.get('name') == header_name:
                    value = header.get('value', '')
                    
                    # Extract email addresses using regex
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    emails = re.findall(email_pattern, value)
                    
                    email_addresses.extend(emails)
            
            return list(set(email_addresses))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to extract email addresses: {e}")
            return []
    
    async def _is_virtual_email(self, email_addr: str) -> bool:
        """Check if an email address is a virtual email."""
        try:
            # Check if this email exists in our virtual emails table
            result = self.supabase.table("virtual_emails") \
                .select("id") \
                .eq("email", email_addr) \
                .eq("status", "active") \
                .single() \
                .execute()
            
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Failed to check if {email_addr} is virtual: {e}")
            return False
    
    async def _process_email_message(self, message: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        """Process a Gmail message."""
        try:
            # Extract message content
            message_id = message['id']
            to_emails = message.get('to', [])
            cc_emails = message.get('cc', [])
            
            # Check for virtual emails
            virtual_emails = await self._check_for_virtual_emails(to_emails, cc_emails)
            
            # Create email record
            email_data = {
                'message_id': message_id,
                'user_id': user_id,
                'to_emails': to_emails,
                'cc_emails': cc_emails,
                'has_virtual_emails': len(virtual_emails) > 0,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("emails").insert(email_data).execute()
            
            # If virtual emails detected, create documents
            document_created = False
            if virtual_emails:
                for virtual_email in virtual_emails:
                    doc_result = await self._create_virtual_email_document(
                        user_id, message_id, virtual_email
                    )
                    if doc_result:
                        document_created = True
            
            return {
                'email_id': result.data[0]['id'] if result.data else None,
                'document_created': document_created,
                'virtual_emails_count': len(virtual_emails)
            }
            
        except Exception as e:
            logger.error(f"Failed to process email message: {e}")
            return None
    
    async def _create_virtual_email_document(self, user_id: str, message_id: str, 
                                           virtual_email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a document from a virtual email."""
        try:
            # Create document record
            document_data = {
                'user_id': user_id,
                'source_type': 'virtual_email',
                'source_id': message_id,
                'title': f"Email from {virtual_email.get('email', 'Unknown')}",
                'content': f"Virtual email detected: {virtual_email.get('email')}",
                'metadata': {
                    'virtual_email': virtual_email,
                    'message_id': message_id,
                    'detected_at': virtual_email.get('detected_at')
                },
                'status': 'pending_classification',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table("documents").insert(document_data).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to create virtual email document: {e}")
            return None
    
    async def _update_last_gmail_sync(self, user_id: str):
        """Update last Gmail sync time for a user."""
        try:
            sync_data = {
                'user_id': user_id,
                'last_sync_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("gmail_sync_states").upsert(sync_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to update last Gmail sync: {e}")
    
    async def _store_polling_result(self, result: GmailPollingResult):
        """Store Gmail polling result in database."""
        try:
            result_data = result.dict()
            result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            self.supabase.table("gmail_polling_results").insert(result_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store Gmail polling result: {e}")
    
    async def _get_gmail_activity_metrics(self, user_email: str) -> Dict[str, Any]:
        """Get Gmail activity metrics for smart polling."""
        try:
            result = self.supabase.table("gmail_activity_metrics") \
                .select("*") \
                .eq("user_email", user_email) \
                .single() \
                .execute()
            
            if result.data:
                return result.data
            
            # Return default metrics
            return {
                'change_frequency': 'medium',
                'next_poll_interval': 30,
                'last_activity_at': None,
                'emails_last_24h': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get Gmail activity metrics: {e}")
            return {
                'change_frequency': 'medium',
                'next_poll_interval': 30,
                'last_activity_at': None,
                'emails_last_24h': 0
            }
    
    async def _should_poll_gmail(self, user_email: str, metrics: Dict[str, Any]) -> bool:
        """Determine if Gmail should be polled based on smart metrics."""
        try:
            # Check if enough time has passed since last poll
            last_sync = await self._get_last_gmail_sync_by_email(user_email)
            if last_sync:
                time_since_last_sync = datetime.now() - last_sync
                next_poll_interval = timedelta(minutes=metrics.get('next_poll_interval', 30))
                
                if time_since_last_sync < next_poll_interval:
                    return False
            
            # Check if user has recent email activity
            last_activity = metrics.get('last_activity_at')
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                time_since_last_activity = datetime.now() - last_activity_time
                
                # If user has recent email activity, poll more frequently
                if time_since_last_activity < timedelta(hours=2):
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to determine if Gmail should be polled: {e}")
            return True
    
    async def _update_gmail_activity_metrics(self, user_email: str, result: Dict[str, Any]):
        """Update Gmail activity metrics based on polling results."""
        try:
            # Calculate change frequency based on results
            messages_processed = result.get('messages_processed', 0)
            virtual_emails_detected = result.get('virtual_emails_detected', 0)
            
            if messages_processed == 0:
                change_frequency = 'low'
                next_poll_interval = 60  # 1 hour
            elif messages_processed <= 10:
                change_frequency = 'medium'
                next_poll_interval = 30  # 30 minutes
            else:
                change_frequency = 'high'
                next_poll_interval = 15  # 15 minutes
            
            # Update metrics
            metrics_data = {
                'user_email': user_email,
                'change_frequency': change_frequency,
                'next_poll_interval': next_poll_interval,
                'last_activity_at': datetime.now().isoformat() if messages_processed > 0 else None,
                'emails_last_24h': messages_processed,
                'virtual_emails_last_24h': virtual_emails_detected,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("gmail_activity_metrics").upsert(metrics_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to update Gmail activity metrics: {e}")
    
    async def _get_last_gmail_sync_by_email(self, user_email: str) -> Optional[datetime]:
        """Get last Gmail sync time by email address."""
        try:
            user_id = await self._get_user_id_from_email(user_email)
            if not user_id:
                return None
            
            result = self.supabase.table("gmail_sync_states") \
                .select("last_sync_at") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data and result.data.get('last_sync_at'):
                return datetime.fromisoformat(result.data['last_sync_at'].replace('Z', '+00:00'))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last Gmail sync by email: {e}")
            return None
