"""
Transcript service for fetching meeting transcripts from Attendee.dev API.
Handles transcript retrieval and storage in the meeting_bots table.
"""

import logging
import httpx
from typing import Optional, Dict, Any
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class TranscriptService:
    """Service for handling meeting transcript operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.attendee_api_key = self.settings.attendee_api_key
        self.attendee_base_url = "https://api.attendee.dev"
        
        if not self.attendee_api_key:
            raise ValueError("Attendee API key not configured")
    
    async def fetch_transcript(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch transcript for a specific bot from Attendee.dev API.
        
        Args:
            bot_id: The bot ID from Attendee.dev
            
        Returns:
            Dict containing transcript data or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.attendee_base_url}/api/v1/bots/{bot_id}/transcript",
                    headers={
                        "Authorization": f"Token {self.attendee_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    transcript_data = response.json()
                    logger.info(f"Successfully fetched transcript for bot {bot_id}")
                    return transcript_data
                elif response.status_code == 404:
                    logger.warning(f"Transcript not found for bot {bot_id}")
                    return None
                else:
                    logger.error(f"Failed to fetch transcript for bot {bot_id}: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching transcript for bot {bot_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for bot {bot_id}: {str(e)}")
            return None
    
    def extract_transcript_text(self, transcript_data: Dict[str, Any]) -> str:
        """
        Extract transcript text from Attendee.dev API response.
        
        Args:
            transcript_data: Raw transcript data from API
            
        Returns:
            Formatted transcript text
        """
        try:
            # Handle different possible response formats
            if isinstance(transcript_data, dict):
                # Check for common transcript fields
                if 'transcript' in transcript_data:
                    return str(transcript_data['transcript'])
                elif 'text' in transcript_data:
                    return str(transcript_data['text'])
                elif 'content' in transcript_data:
                    return str(transcript_data['content'])
                elif 'data' in transcript_data and isinstance(transcript_data['data'], dict):
                    # Nested data structure
                    return self.extract_transcript_text(transcript_data['data'])
                else:
                    # Try to extract from the entire response
                    return str(transcript_data)
            elif isinstance(transcript_data, str):
                return transcript_data
            else:
                logger.warning(f"Unexpected transcript data format: {type(transcript_data)}")
                return str(transcript_data)
                
        except Exception as e:
            logger.error(f"Error extracting transcript text: {str(e)}")
            return str(transcript_data) if transcript_data else ""
    
    async def store_transcript(self, supabase, bot_id: str, transcript_text: str) -> bool:
        """
        Store transcript in the meeting_bots table.
        
        Args:
            supabase: Supabase client instance
            bot_id: The bot ID
            transcript_text: The transcript text to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = supabase.table('meeting_bots').update({
                'transcript': transcript_text,
                'updated_at': 'now()'
            }).eq('bot_id', bot_id).execute()
            
            if result.data:
                logger.info(f"Successfully stored transcript for bot {bot_id}")
                return True
            else:
                logger.error(f"Failed to store transcript for bot {bot_id}: No rows updated")
                return False
                
        except Exception as e:
            logger.error(f"Error storing transcript for bot {bot_id}: {str(e)}")
            return False
    
    async def process_ended_bot(self, supabase, bot_id: str) -> bool:
        """
        Complete workflow for processing an ended bot: fetch and store transcript.
        
        Args:
            supabase: Supabase client instance
            bot_id: The bot ID that has ended
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch transcript from Attendee.dev
            transcript_data = await self.fetch_transcript(bot_id)
            if not transcript_data:
                logger.warning(f"No transcript data available for bot {bot_id}")
                return False
            
            # Extract transcript text
            transcript_text = self.extract_transcript_text(transcript_data)
            if not transcript_text.strip():
                logger.warning(f"Empty transcript text for bot {bot_id}")
                return False
            
            # Store transcript in database
            success = await self.store_transcript(supabase, bot_id, transcript_text)
            if success:
                logger.info(f"Successfully processed ended bot {bot_id} with transcript")
                return True
            else:
                logger.error(f"Failed to store transcript for bot {bot_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing ended bot {bot_id}: {str(e)}")
            return False
