"""
Email processing service for handling incoming emails from master account.
Parses +username aliases and routes emails to appropriate users.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re
from email import message_from_string
from email.mime.text import MIMEText

from ...core.config import get_settings
from ...core.supabase_config import get_supabase_service_client
from .master_oauth_service import MasterOAuthService

logger = logging.getLogger(__name__)


class EmailProcessingService:
    """Service for processing incoming emails and routing them to users."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_service_client()
        self.master_oauth = MasterOAuthService()
        self.master_email = "ai@besunny.ai"
    
    async def process_incoming_email(self, email_data: Dict[str, Any]) -> bool:
        """Process an incoming email and route it to the appropriate user."""
        try:
            logger.info(f"Processing incoming email: {email_data.get('id', 'unknown')}")
            
            # Extract email content
            email_content = email_data.get('snippet', '')
            email_headers = email_data.get('payload', {}).get('headers', [])
            
            # Parse email headers
            from_email = self._extract_header(email_headers, 'From')
            to_email = self._extract_header(email_headers, 'To')
            subject = self._extract_header(email_headers, 'Subject')
            
            logger.info(f"Email from: {from_email}, to: {to_email}, subject: {subject}")
            
            # Check if this is a +username email
            username = self._extract_username_from_email(to_email)
            if not username:
                logger.info(f"Email {email_data.get('id')} is not a +username email, skipping")
                return False
            
            # Find user by username
            user = await self._get_user_by_username(username)
            if not user:
                logger.warning(f"No user found for username: {username}")
                return False
            
            # Process and store the email
            email_id = await self._store_incoming_email(email_data, user['id'], username)
            
            # Trigger any necessary workflows (AI processing, notifications, etc.)
            await self._trigger_email_workflows(email_id, user['id'], username)
            
            logger.info(f"Email {email_data.get('id')} processed successfully for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing incoming email: {e}")
            return False
    
    async def fetch_recent_emails(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent emails from the master account inbox."""
        try:
            credentials = await self.master_oauth.get_valid_credentials()
            if not credentials:
                logger.error("No valid OAuth credentials available for email fetching")
                return []
            
            from googleapiclient.discovery import build
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get recent emails from inbox
            results = service.users().messages().list(
                userId=self.master_email,
                labelIds=['INBOX'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                try:
                    # Get full message details
                    msg = service.users().messages().get(
                        userId=self.master_email,
                        id=message['id']
                    ).execute()
                    
                    emails.append(msg)
                    
                except Exception as e:
                    logger.warning(f"Could not fetch message {message['id']}: {e}")
                    continue
            
            logger.info(f"Fetched {len(emails)} recent emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching recent emails: {e}")
            return []
    
    def _extract_username_from_email(self, email: str) -> Optional[str]:
        """Extract username from +username@besunny.ai email address."""
        if not email:
            return None
        
        # Pattern: +username@besunny.ai
        pattern = r'\+([^@]+)@besunny\.ai'
        match = re.search(pattern, email)
        
        if match:
            username = match.group(1)
            logger.info(f"Extracted username '{username}' from email: {email}")
            return username
        
        return None
    
    def _extract_header(self, headers: List[Dict[str, str]], name: str) -> Optional[str]:
        """Extract header value from email headers."""
        for header in headers:
            if header.get('name') == name:
                return header.get('value')
        return None
    
    async def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username from database."""
        try:
            result = self.supabase.table('users') \
                .select('id, username, email') \
                .eq('username', username) \
                .single() \
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def _store_incoming_email(self, email_data: Dict[str, Any], user_id: str, username: str) -> str:
        """Store incoming email in database."""
        try:
            # Extract email details
            email_id = email_data.get('id')
            thread_id = email_data.get('threadId')
            snippet = email_data.get('snippet', '')
            
            # Get email headers
            headers = email_data.get('payload', {}).get('headers', [])
            from_email = self._extract_header(headers, 'From')
            to_email = self._extract_header(headers, 'To')
            subject = self._extract_header(headers, 'Subject')
            date = self._extract_header(headers, 'Date')
            
            # Store email in database
            email_record = {
                'gmail_id': email_id,
                'thread_id': thread_id,
                'user_id': user_id,
                'username': username,
                'from_email': from_email,
                'to_email': to_email,
                'subject': subject,
                'snippet': snippet,
                'date_received': date,
                'is_processed': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('incoming_emails') \
                .insert(email_record) \
                .execute()
            
            if result.data:
                stored_id = result.data[0]['id']
                logger.info(f"Stored incoming email {email_id} with ID {stored_id}")
                return stored_id
            else:
                raise Exception("Failed to store incoming email")
                
        except Exception as e:
            logger.error(f"Error storing incoming email: {e}")
            raise
    
    async def _trigger_email_workflows(self, email_id: str, user_id: str, username: str) -> None:
        """Trigger workflows for the processed email (AI processing, notifications, etc.)."""
        try:
            logger.info(f"Triggering workflows for email {email_id} (user: {username})")
            
            # TODO: Implement email workflows
            # - AI classification and processing
            # - User notifications
            # - Project context updates
            # - Meeting scheduling
            # - Document processing
            
            logger.info(f"Workflows triggered for email {email_id}")
            
        except Exception as e:
            logger.error(f"Error triggering workflows for email {email_id}: {e}")
    
    async def setup_email_monitoring(self) -> bool:
        """Set up email monitoring for the master account."""
        try:
            logger.info("Setting up email monitoring for master account...")
            
            # Set up Gmail watch
            watch_id = await self.master_oauth.setup_gmail_watch()
            if not watch_id:
                logger.error("Failed to setup Gmail watch for email monitoring")
                return False
            
            logger.info(f"Email monitoring setup successful, watch ID: {watch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up email monitoring: {e}")
            return False
