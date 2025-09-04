"""
Gmail webhook handler for processing virtual email addresses.
Receives emails sent to ai+{username}@besunny.ai and processes them.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status
import logging
import json
import base64
from datetime import datetime
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ....services.email import EmailProcessingService
from ....core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/gmail")
async def handle_gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Handle Gmail push notification webhook.
    
    This endpoint receives notifications when emails arrive at the monitored
    Gmail account (inbound@besunny.ai) and processes any emails sent to
    virtual email addresses (ai+{username}@besunny.ai).
    """
    try:
        logger.info("=== GMAIL WEBHOOK RECEIVED ===")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request URL: {request.url}")
        # Verify the webhook is from Gmail (can be disabled for testing)
        settings = get_settings()
        if getattr(settings, 'verify_gmail_webhooks', True):
            if not await _verify_gmail_webhook(request):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Gmail webhook signature"
                )
        else:
            logger.info("Gmail webhook verification disabled for testing")
        
        # Parse the webhook payload
        webhook_data = await request.json()
        logger.info(f"Received Gmail webhook: {webhook_data}")
        
        # Handle different webhook payload formats
        if 'message' in webhook_data:
            # Pub/Sub format
            message_data = webhook_data.get('message', {})
            if not message_data:
                return {"status": "no_message_data", "message": "No message data in webhook"}
            
            # Get the email message ID
            message_id = message_data.get('data')
            if not message_id:
                return {"status": "no_message_id", "message": "No message ID in webhook"}
            
            # Decode the base64 message ID
            try:
                decoded_message_id = base64.urlsafe_b64decode(message_id + '=' * (-len(message_id) % 4))
                decoded_data = decoded_message_id.decode('utf-8')
                
                # Try to parse the decoded data as JSON
                try:
                    parsed_data = json.loads(decoded_data)
                    if 'emailAddress' in parsed_data and 'historyId' in parsed_data:
                        # This is a Gmail history notification
                        email_address = parsed_data.get('emailAddress')
                        history_id = parsed_data.get('historyId')
                        logger.info(f"Gmail history notification for {email_address}, history ID: {history_id}")
                        gmail_message_id = f"history_{history_id}"
                    else:
                        # This is a regular message ID
                        gmail_message_id = decoded_data
                except json.JSONDecodeError:
                    # Not JSON, treat as regular message ID
                    gmail_message_id = decoded_data
                    
            except Exception as e:
                logger.error(f"Failed to decode message ID: {e}")
                return {"status": "decode_error", "message": "Failed to decode message ID"}
        
        elif 'emailAddress' in webhook_data and 'historyId' in webhook_data:
            # Direct Gmail webhook format
            email_address = webhook_data.get('emailAddress')
            history_id = webhook_data.get('historyId')
            
            logger.info(f"Gmail webhook for {email_address}, history ID: {history_id}")
            
            # For now, we'll process recent messages instead of specific history
            # This is a simplified approach - in production you'd want to process the specific history
            gmail_message_id = f"history_{history_id}"
            
        else:
            return {"status": "invalid_payload", "message": "Invalid webhook payload format"}
        
        # Process the email in the background
        background_tasks.add_task(
            _process_gmail_message,
            gmail_message_id
        )
        
        return {
            "status": "success",
            "message": "Email queued for processing",
            "gmail_message_id": gmail_message_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling Gmail webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(e)}"
        )


@router.post("/gmail-test")
async def test_gmail_webhook() -> Dict[str, Any]:
    """Test endpoint for Gmail webhook functionality."""
    return {
        "status": "success",
        "message": "Gmail webhook endpoint is working",
        "timestamp": datetime.utcnow().isoformat()
    }


async def _verify_gmail_webhook(request: Request) -> bool:
    """Verify that the webhook is from Google Pub/Sub using JWT verification."""
    try:
        # Get the authorization header
        auth_header = request.headers.get('authorization')
        if not auth_header:
            logger.warning("No authorization header in Gmail webhook")
            return False
        
        # Extract the JWT token from the Bearer token
        if not auth_header.startswith('Bearer '):
            logger.warning("Invalid authorization header format")
            return False
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Verify the JWT token
        try:
            # Decode the JWT header to get the key ID
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            if not kid:
                logger.warning("No key ID in JWT header")
                return False
            
            # Get the public key from Google
            public_key = await _get_google_public_key(kid)
            if not public_key:
                logger.warning(f"Could not retrieve public key for kid: {kid}")
                return False
            
            # Verify the JWT token
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=f"projects/{get_settings().google_project_id}/topics/gmail-notifications",
                issuer="https://accounts.google.com"
            )
            
            logger.info("Gmail webhook JWT verification passed")
            return True
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error verifying Gmail webhook: {e}")
        return False


async def _get_google_public_key(kid: str) -> Optional[str]:
    """Get Google's public key for JWT verification."""
    try:
        # Google's public key endpoint
        url = "https://www.googleapis.com/oauth2/v3/certs"
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to fetch Google public keys: {response.status_code}")
            return None
        
        keys_data = response.json()
        
        # Find the key with matching kid
        for key in keys_data.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to PEM format
                return _jwk_to_pem(key)
        
        logger.warning(f"Public key not found for kid: {kid}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching Google public key: {e}")
        return None


def _jwk_to_pem(jwk: Dict[str, Any]) -> str:
    """Convert JWK to PEM format for JWT verification."""
    try:
        # Extract the key components
        n = base64.urlsafe_b64decode(jwk['n'] + '==')
        e = base64.urlsafe_b64decode(jwk['e'] + '==')
        
        # Convert to integers
        n_int = int.from_bytes(n, 'big')
        e_int = int.from_bytes(e, 'big')
        
        # Create RSA public key
        public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
        
        # Serialize to PEM format
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error converting JWK to PEM: {e}")
        return None


async def _process_gmail_message(gmail_message_id: str) -> None:
    """Process a Gmail message in the background."""
    try:
        logger.info(f"Processing Gmail message: {gmail_message_id}")
        
        # Handle history ID format
        if gmail_message_id.startswith('history_'):
            await _process_gmail_history(gmail_message_id)
            return
        
        # Check if we've already processed this Gmail message
        from ....core.supabase_config import get_supabase_service_client
        supabase = get_supabase_service_client()
        if supabase:
            existing_doc = supabase.table('documents').select('id').eq('source_id', gmail_message_id).eq('source', 'gmail').execute()
            if existing_doc.data and len(existing_doc.data) > 0:
                logger.info(f"Gmail message {gmail_message_id} already processed, skipping")
                return
        
        # Get the email service
        email_service = EmailProcessingService()
        
        # Fetch the full message from Gmail
        raw_gmail_message = await _fetch_gmail_message(gmail_message_id)
        if not raw_gmail_message:
            logger.error(f"Failed to fetch Gmail message: {gmail_message_id}")
            return
        
        # Check if this is a virtual email
        to_header = _get_header_value(raw_gmail_message.get('payload', {}).get('headers', []), 'to')
        if not to_header or not _is_virtual_email(to_header):
            logger.info(f"Message {gmail_message_id} is not a virtual email: {to_header}")
            return
        
        # Convert raw Gmail API response to GmailMessage format
        gmail_message = _convert_to_gmail_message(raw_gmail_message)
        if not gmail_message:
            logger.error(f"Failed to convert email to GmailMessage format")
            return
        
        # Process the virtual email
        result = await email_service.process_inbound_email(gmail_message)
        
        if result.success:
            logger.info(f"Successfully processed virtual email {gmail_message_id}: {result.message}")
        else:
            logger.error(f"Failed to process virtual email {gmail_message_id}: {result.message}")
            
    except Exception as e:
        logger.error(f"Error processing Gmail message {gmail_message_id}: {e}")


async def _process_gmail_history(history_id: str) -> None:
    """Process Gmail history by fetching recent messages."""
    try:
        logger.info(f"Processing Gmail history: {history_id}")
        
        # Import the Gmail service
        from ....services.email.gmail_service import GmailService
        
        # Create Gmail service instance
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            logger.error("Gmail service not ready")
            return
        
        # Fetch recent messages
        recent_emails = await gmail_service.fetch_recent_emails(max_results=10)
        
        logger.info(f"Found {len(recent_emails)} recent emails to process")
        
        # Process each email
        for email in recent_emails:
            try:
                # Check if this is a virtual email
                to_header = _get_header_value(email.get('payload', {}).get('headers', []), 'to')
                if to_header and _is_virtual_email(to_header):
                    logger.info(f"Processing virtual email: {to_header}")
                    
                    # Convert raw Gmail API response to GmailMessage format
                    gmail_message = _convert_to_gmail_message(email)
                    if not gmail_message:
                        logger.error(f"Failed to convert email to GmailMessage format")
                        continue
                    
                    # Get the email service
                    email_service = EmailProcessingService()
                    
                    # Process the virtual email
                    result = await email_service.process_inbound_email(gmail_message)
                    
                    if result.success:
                        logger.info(f"Successfully processed virtual email: {result.message}")
                    else:
                        logger.error(f"Failed to process virtual email: {result.message}")
                else:
                    logger.info(f"Skipping non-virtual email: {to_header}")
                    
            except Exception as e:
                logger.error(f"Error processing individual email: {e}")
                continue
        
        logger.info(f"Completed processing Gmail history: {history_id}")
        
    except Exception as e:
        logger.error(f"Error processing Gmail history {history_id}: {e}")


async def _fetch_gmail_message(message_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a Gmail message using the Gmail API."""
    try:
        # Import the Gmail service
        from ....services.email.gmail_service import GmailService
        
        # Create Gmail service instance
        gmail_service = GmailService()
        
        if not gmail_service.is_ready():
            logger.error("Gmail service not ready")
            return None
        
        # Fetch the message
        try:
            message = gmail_service.gmail_service.users().messages().get(
                userId=gmail_service.master_email,
                id=message_id,
                format='full'
            ).execute()
            
            logger.info(f"Successfully fetched Gmail message: {message_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to fetch Gmail message {message_id}: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error fetching Gmail message {message_id}: {e}")
        return None


def _get_header_value(headers: list, name: str) -> Optional[str]:
    """Get header value by name from Gmail message headers."""
    try:
        header = next((h for h in headers if h.get('name', '').lower() == name.lower()), None)
        return header.get('value') if header else None
    except Exception as e:
        logger.error(f"Error getting header value for {name}: {e}")
        return None


def _is_virtual_email(email: str) -> bool:
    """Check if an email address is a virtual email (ai+{username}@besunny.ai)."""
    if not email:
        return False
    
    # Check if it matches the virtual email pattern
    import re
    pattern = r'ai\+[a-zA-Z0-9]+@besunny\.ai'
    return bool(re.match(pattern, email))


def _convert_to_gmail_message(raw_message: Dict[str, Any]) -> Optional[Any]:
    """Convert raw Gmail API response to GmailMessage format."""
    try:
        from ....models.schemas.email import GmailMessage, GmailPayload, GmailHeader, GmailBody
        
        # Extract basic message info
        message_id = raw_message.get('id', '')
        thread_id = raw_message.get('threadId', '')
        label_ids = raw_message.get('labelIds', [])
        snippet = raw_message.get('snippet', '')
        history_id = raw_message.get('historyId', '')
        internal_date = raw_message.get('internalDate', '')
        size_estimate = raw_message.get('sizeEstimate', 0)
        
        # Extract payload
        raw_payload = raw_message.get('payload', {})
        
        # Convert headers
        headers = []
        for header in raw_payload.get('headers', []):
            headers.append(GmailHeader(
                name=header.get('name', ''),
                value=header.get('value', '')
            ))
        
        # Convert body
        raw_body = raw_payload.get('body', {})
        body = None
        if raw_body:
            body = GmailBody(
                attachment_id=raw_body.get('attachmentId'),
                size=raw_body.get('size', 0),
                data=raw_body.get('data')
            )
        
        # Create payload
        payload = GmailPayload(
            part_id=raw_payload.get('partId', ''),
            mime_type=raw_payload.get('mimeType', ''),
            filename=raw_payload.get('filename'),
            headers=headers,
            body=body,
            parts=None  # TODO: Handle parts if needed
        )
        
        # Create GmailMessage
        gmail_message = GmailMessage(
            id=message_id,
            thread_id=thread_id,
            label_ids=label_ids,
            snippet=snippet,
            history_id=history_id,
            internal_date=internal_date,
            payload=payload,
            size_estimate=size_estimate
        )
        
        return gmail_message
        
    except Exception as e:
        logger.error(f"Error converting to GmailMessage: {e}")
        return None
