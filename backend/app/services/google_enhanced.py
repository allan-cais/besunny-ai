"""
Enhanced Google services integration for advanced Drive API, Calendar intelligence, and OAuth management.
"""

from typing import Dict, List, Optional, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import asyncio
import logging
from datetime import datetime, timedelta
import json

from ..core.config import get_settings
from ..core.redis_manager import get_redis, cache_result

logger = logging.getLogger(__name__)


class EnhancedGoogleDriveService:
    """Enhanced Google Drive service with advanced features."""
    
    def __init__(self):
        self.settings = get_settings()
        self._service = None
    
    async def get_service(self, credentials_dict: dict):
        """Get Drive service with credentials."""
        try:
            creds = Credentials.from_authorized_user_info(credentials_dict)
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            self._service = build('drive', 'v3', credentials=creds)
            return self._service
        except Exception as e:
            logger.error(f"Failed to build Drive service: {e}")
            raise
    
    @cache_result(expire=300, key_prefix="drive")
    async def list_files_advanced(
        self, 
        credentials_dict: dict, 
        folder_id: str = None,
        query: str = None,
        fields: str = "nextPageToken, files(id, name, mimeType, size, modifiedTime, parents, webViewLink, permissions)",
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Advanced file listing with caching and filtering."""
        service = await self.get_service(credentials_dict)
        
        query_parts = ["trashed=false"]
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if query:
            query_parts.append(query)
        
        full_query = " and ".join(query_parts)
        
        try:
            results = service.files().list(
                q=full_query,
                pageSize=page_size,
                fields=fields,
                orderBy="modifiedTime desc"
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            logger.error(f"Failed to list Drive files: {e}")
            raise
    
    async def get_file_metadata(self, credentials_dict: dict, file_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed file metadata."""
        service = await self.get_service(credentials_dict)
        
        try:
            file = service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, createdTime, parents, webViewLink, permissions, owners, shared, description, capabilities"
            ).execute()
            
            return file
        except Exception as e:
            logger.error(f"Failed to get file metadata for {file_id}: {e}")
            return None
    
    async def watch_file_changes(
        self, 
        credentials_dict: dict, 
        file_id: str, 
        webhook_url: str,
        expiration: datetime = None
    ) -> Optional[Dict[str, Any]]:
        """Set up file change notifications."""
        service = await self.get_service(credentials_dict)
        
        if not expiration:
            expiration = datetime.utcnow() + timedelta(hours=24)
        
        try:
            channel = {
                'id': f"besunny-{file_id}-{int(datetime.utcnow().timestamp())}",
                'type': 'web_hook',
                'address': webhook_url,
                'expiration': expiration.isoformat() + 'Z'
            }
            
            result = service.files().watch(
                fileId=file_id,
                body=channel
            ).execute()
            
            return result
        except Exception as e:
            logger.error(f"Failed to watch file {file_id}: {e}")
            return None


class EnhancedGoogleCalendarService:
    """Enhanced Google Calendar service with intelligence features."""
    
    def __init__(self):
        self.settings = get_settings()
        self._service = None
    
    async def get_service(self, credentials_dict: dict):
        """Get Calendar service with credentials."""
        try:
            creds = Credentials.from_authorized_user_info(credentials_dict)
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            self._service = build('calendar', 'v3', credentials=creds)
            return self._service
        except Exception as e:
            logger.error(f"Failed to build Calendar service: {e}")
            raise
    
    @cache_result(expire=300, key_prefix="calendar")
    async def get_calendar_events_enhanced(
        self, 
        credentials_dict: dict, 
        calendar_id: str = 'primary',
        time_min: datetime = None,
        time_max: datetime = None,
        max_results: int = 100,
        single_events: bool = True,
        order_by: str = 'startTime'
    ) -> List[Dict[str, Any]]:
        """Enhanced calendar events with advanced filtering."""
        service = await self.get_service(credentials_dict)
        
        if not time_min:
            time_min = datetime.utcnow()
        if not time_max:
            time_max = time_min + timedelta(days=30)
        
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=single_events,
                orderBy=order_by,
                fields="items(id, summary, description, start, end, attendees, organizer, location, conferenceData, reminders, transparency, visibility, recurringEventId, originalStartTime)"
            ).execute()
            
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            raise
    
    async def create_meeting_with_bot(
        self, 
        credentials_dict: dict, 
        summary: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        bot_email: str,
        calendar_id: str = 'primary'
    ) -> Optional[Dict[str, Any]]:
        """Create a meeting with bot attendee."""
        service = await self.get_service(credentials_dict)
        
        # Add bot to attendees
        all_attendees = [{"email": email} for email in attendees]
        all_attendees.append({"email": bot_email})
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': all_attendees,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        try:
            event = service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return event
        except Exception as e:
            logger.error(f"Failed to create meeting: {e}")
            return None


class GoogleOAuthManager:
    """Enhanced OAuth token management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis = None
    
    async def get_redis(self):
        """Get Redis client."""
        if not self.redis:
            self.redis = await get_redis()
        return self.redis
    
    async def store_credentials(self, user_id: str, credentials_dict: dict) -> bool:
        """Store OAuth credentials securely."""
        redis_client = await self.get_redis()
        
        # Store with expiration (tokens typically expire in 1 hour)
        return await redis_client.set_session(
            f"google_oauth:{user_id}",
            credentials_dict,
            expire=3600
        )
    
    async def get_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored OAuth credentials."""
        redis_client = await self.get_redis()
        
        return await redis_client.get_session(f"google_oauth:{user_id}")
    
    async def refresh_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth credentials."""
        credentials_dict = await self.get_credentials(user_id)
        if not credentials_dict:
            return None
        
        try:
            creds = Credentials.from_authorized_user_info(credentials_dict)
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                
                # Update stored credentials
                new_credentials = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                
                await self.store_credentials(user_id, new_credentials)
                return new_credentials
            
            return credentials_dict
            
        except RefreshError as e:
            logger.error(f"Failed to refresh credentials for user {user_id}: {e}")
            # Remove invalid credentials
            redis_client = await self.get_redis()
            await redis_client.delete_session(f"google_oauth:{user_id}")
            return None
        except Exception as e:
            logger.error(f"Error refreshing credentials for user {user_id}: {e}")
            return None
    
    async def revoke_credentials(self, user_id: str) -> bool:
        """Revoke OAuth credentials."""
        redis_client = await self.get_redis()
        return await redis_client.delete_session(f"google_oauth:{user_id}")


# Global service instances
drive_service = EnhancedGoogleDriveService()
calendar_service = EnhancedGoogleCalendarService()
oauth_manager = GoogleOAuthManager()


async def get_enhanced_drive_service() -> EnhancedGoogleDriveService:
    """Dependency for enhanced Drive service."""
    return drive_service


async def get_enhanced_calendar_service() -> EnhancedGoogleCalendarService:
    """Dependency for enhanced Calendar service."""
    return calendar_service


async def get_google_oauth_manager() -> GoogleOAuthManager:
    """Dependency for Google OAuth manager."""
    return oauth_manager
