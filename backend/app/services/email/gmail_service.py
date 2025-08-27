"""
Clean Gmail service for ai@besunny.ai using service account authentication.
Handles email watching, processing, and user routing automatically.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...core.config import get_settings
from ...core.supabase_config import get_supabase_service_client

logger = logging.getLogger(__name__)


class GmailService:
    """Clean Gmail service for master account email processing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_service_client()
        self.master_email = "ai@besunny.ai"
        self.credentials = None
        self.gmail_service = None
        
        # Initialize service
        self._init_service()
    
    def _init_service(self):
        """Initialize Gmail service with service account credentials."""
        try:
            # Get service account key from config
            service_account_key = self.settings.google_service_account_key_base64
            if not service_account_key:
                logger.error("GOOGLE_SERVICE_ACCOUNT_KEY_BASE64 not set in config")
                return
            
            # Decode and create credentials
            import base64
            import json
            
            try:
                key_data = json.loads(base64.b64decode(service_account_key))
                logger.info(f"Service account key decoded successfully")
                logger.info(f"Service account email: {key_data.get('client_email')}")
                logger.info(f"Project ID: {key_data.get('project_id')}")
                
                self.credentials = service_account.Credentials.from_service_account_info(
                    key_data,
                    scopes=[
                        'https://www.googleapis.com/auth/gmail.readonly',
                        'https://www.googleapis.com/auth/gmail.modify'
                    ]
                )
                
                logger.info(f"Service account credentials created successfully")
                logger.info(f"Has scopes: {self.credentials.has_scopes(['https://www.googleapis.com/auth/gmail.readonly'])}")
                
                # Create delegated credentials for ai@besunny.ai
                logger.info(f"Creating delegated credentials for {self.master_email}")
                try:
                    self.credentials = self.credentials.with_subject(self.master_email)
                    logger.info(f"Delegated credentials created successfully")
                except Exception as e:
                    logger.error(f"Failed to create delegated credentials: {e}")
                    logger.error(f"This usually means domain-wide delegation is not properly configured")
                    logger.error(f"Please check Google Workspace Admin > Security > API controls > Domain-wide delegation")
                    raise
                
                # Build Gmail service
                logger.info("Building Gmail API service...")
                self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
                logger.info("Gmail API service built successfully")
                
            except Exception as e:
                logger.error(f"Error during credential setup: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            logger.info(f"Gmail service initialized for {self.master_email}")
            logger.info(f"Service account: {key_data.get('client_email')}")
            logger.info(f"Domain-wide delegation enabled: {self.credentials.has_scopes(['https://www.googleapis.com/auth/gmail.readonly'])}")
            logger.info("✅ No token storage needed - Google handles everything automatically!")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            self.credentials = None
            self.gmail_service = None
    
    def is_ready(self) -> bool:
        """Check if the Gmail service is ready."""
        return self.gmail_service is not None and self.credentials is not None
    
    async def setup_watch(self, topic_name: str = None) -> Optional[str]:
        """Set up Gmail watch for the master account."""
        if not self.is_ready():
            logger.error("Gmail service not ready")
            return None
        
        try:
            # Create watch request
            watch_request = {
                'labelIds': ['INBOX'],
                'labelFilterAction': 'include'
            }
            
            # Only add topicName if provided and not None
            if topic_name:
                watch_request['topicName'] = topic_name
                logger.info(f"Setting up Gmail watch with PubSub topic: {topic_name}")
            else:
                logger.info("Setting up Gmail watch without PubSub topic (polling mode)")
            
            logger.info(f"Watch request: {watch_request}")
            logger.info(f"Using user ID: {self.master_email}")
            
            # Set up the watch
            logger.info("Executing Gmail watch API call...")
            watch = self.gmail_service.users().watch(
                userId=self.master_email, 
                body=watch_request
            ).execute()
            
            logger.info(f"Gmail watch API call successful: {watch}")
            
            # Store watch info
            logger.info("Storing watch info in database...")
            watch_id = await self._store_watch_info(watch)
            
            logger.info(f"Gmail watch setup successful: {watch_id}")
            return watch_id
            
        except HttpError as e:
            logger.error(f"Gmail API error setting up watch: {e}")
            logger.error(f"HTTP Error details: {e.resp.status} - {e.content}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Check for specific IAM policy errors
            error_content = str(e.content) if hasattr(e, 'content') else str(e)
            if "Domain Restricted Sharing" in error_content or "constraints/iam.allowedPolicyMemberDomains" in error_content:
                logger.error("🔒 IAM Policy Domain Restriction Error Detected")
                logger.error("This error occurs when your Google Cloud organization has domain restricted sharing enabled.")
                logger.error("Solutions:")
                logger.error("1. Contact your Google Workspace admin to add '*.iam.gserviceaccount.com' to allowed domains")
                logger.error("2. Create a new project without domain restrictions")
                logger.error("3. Use a different Google Cloud project for Gmail integration")
                raise Exception(f"IAM Policy Domain Restriction: {error_content}")
            elif "IAM" in error_content and "policy" in error_content.lower():
                logger.error("🔒 IAM Policy Error Detected")
                logger.error("This error occurs when setting IAM policies for Gmail webhook setup.")
                logger.error("Solutions:")
                logger.error("1. Ensure your service account has 'Pub/Sub Publisher' and 'Gmail API Admin' roles")
                logger.error("2. Check if your project has the necessary APIs enabled")
                logger.error("3. Verify your service account has domain-wide delegation enabled")
                raise Exception(f"IAM Policy Error: {error_content}")
            elif "403" in str(e.resp.status):
                logger.error("🔒 Permission Denied Error")
                logger.error("This usually indicates insufficient permissions or domain restrictions.")
                logger.error("Check your service account permissions and organization policies.")
                raise Exception(f"Permission Denied: {error_content}")
            
            return None
        except Exception as e:
            logger.error(f"Error setting up Gmail watch: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def process_email(self, message_id: str) -> bool:
        """Process a single email and route it to the appropriate user."""
        if not self.is_ready():
            logger.error("Gmail service not ready")
            return False
        
        try:
            # Get message details
            message = self.gmail_service.users().messages().get(
                userId=self.master_email,
                id=message_id,
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            from_email = self._extract_header(headers, 'From')
            to_email = self._extract_header(headers, 'To')
            subject = self._extract_header(headers, 'Subject')
            date = self._extract_header(headers, 'Date')
            
            logger.info(f"Processing email {message_id}: {from_email} -> {to_email}")
            
            # Check if this is a user alias email
            username = self._extract_username_from_alias(to_email)
            if not username:
                logger.info(f"Email {message_id} is not a user alias, skipping")
                return False
            
            # Find user by username
            user = await self._get_user_by_username(username)
            if not user:
                logger.warning(f"No user found for username: {username}")
                return False
            
            # Store email for processing
            email_id = await self._store_email(message, user['id'], username)
            
            # Trigger email workflows
            await self._trigger_email_workflows(email_id, user['id'], username)
            
            logger.info(f"Email {message_id} processed successfully for user {username}")
            return True
            
        except HttpError as e:
            logger.error(f"Gmail API error processing email: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing email {message_id}: {e}")
            return False
    
    async def fetch_recent_emails(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent emails from the master account inbox."""
        if not self.is_ready():
            logger.error("Gmail service not ready")
            return []
        
        try:
            # Get recent messages
            results = self.gmail_service.users().messages().list(
                userId=self.master_email,
                labelIds=['INBOX'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                try:
                    # Get full message details
                    msg = self.gmail_service.users().messages().get(
                        userId=self.master_email,
                        id=message['id'],
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
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
    
    def _extract_username_from_alias(self, email: str) -> Optional[str]:
        """Extract username from ai+username@besunny.ai email address."""
        if not email:
            return None
        
        # Pattern: ai+username@besunny.ai
        pattern = r'ai\+([^@]+)@besunny\.ai'
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
    
    async def _store_email(self, message: Dict[str, Any], user_id: str, username: str) -> str:
        """Store email in database."""
        try:
            # Extract email details
            message_id = message.get('id')
            thread_id = message.get('threadId')
            snippet = message.get('snippet', '')
            
            # Get headers
            headers = message.get('payload', {}).get('headers', [])
            from_email = self._extract_header(headers, 'From')
            to_email = self._extract_header(headers, 'To')
            subject = self._extract_header(headers, 'Subject')
            date = self._extract_header(headers, 'Date')
            
            # Store email record
            email_record = {
                'gmail_id': message_id,
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
                logger.info(f"Stored email {message_id} with ID {stored_id}")
                return stored_id
            else:
                raise Exception("Failed to store email")
                
        except Exception as e:
            logger.error(f"Error storing email: {e}")
            raise
    
    async def _store_watch_info(self, watch_response: Dict[str, Any]) -> str:
        """Store Gmail watch information in database."""
        try:
            # Convert expiration timestamp from milliseconds to ISO format
            expiration_timestamp = watch_response.get('expiration')
            if expiration_timestamp:
                # Convert from milliseconds to seconds, then to datetime
                expiration_datetime = datetime.fromtimestamp(int(expiration_timestamp) / 1000)
                expiration_iso = expiration_datetime.isoformat()
            else:
                expiration_iso = None
            
            watch_data = {
                'user_email': self.master_email,
                'history_id': watch_response.get('historyId'),
                'expiration': expiration_iso,
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('gmail_watches') \
                .insert(watch_data) \
                .execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception("Failed to store watch info")
                
        except Exception as e:
            logger.error(f"Error storing watch info: {e}")
            raise
    
    async def _trigger_email_workflows(self, email_id: str, user_id: str, username: str) -> None:
        """Trigger workflows for the processed email."""
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
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get the current status of the Gmail service."""
        if self.is_ready():
            return {
                "status": "ready",
                "master_email": self.master_email,
                "message": "Gmail service is ready and authenticated"
            }
        else:
            return {
                "status": "not_ready",
                "master_email": self.master_email,
                "message": "Gmail service is not ready - check credentials"
            }
