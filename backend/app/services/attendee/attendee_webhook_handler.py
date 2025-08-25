"""
Attendee webhook handler for BeSunny.ai Python backend.
Processes incoming webhook notifications from Attendee.dev API.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from ...core.database import get_supabase
from ...models.schemas.calendar import Meeting

logger = logging.getLogger(__name__)


class AttendeeWebhookHandler:
    """Handles incoming Attendee webhook notifications."""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    async def process_webhook(self, webhook_data: Dict[str, Any], user_id: str) -> bool:
        """Process incoming Attendee webhook data."""
        try:
            # Extract webhook metadata
            webhook_id = webhook_data.get('idempotency_key')
            trigger = webhook_data.get('trigger')
            bot_id = webhook_data.get('bot_id')
            
            # Log webhook receipt
            await self._log_webhook_receipt(webhook_id, trigger, bot_id, user_id, webhook_data)
            
            # Process based on trigger type
            if trigger == 'bot.state_change':
                await self._handle_bot_state_change(webhook_data, user_id)
            elif trigger == 'transcript.update':
                await self._handle_transcript_update(webhook_data, user_id)
            elif trigger == 'chat_messages.update':
                await self._handle_chat_message_update(webhook_data, user_id)
            elif trigger == 'participant_events.join_leave':
                await self._handle_participant_event(webhook_data, user_id)
            else:
                logger.info(f"Unhandled webhook trigger: {trigger}")
            
            # Mark webhook as processed
            await self._mark_webhook_processed(webhook_id, user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Attendee webhook: {e}")
            return False
    
    async def _handle_bot_state_change(self, webhook_data: Dict[str, Any], user_id: str):
        """Handle bot state change webhook."""
        try:
            data = webhook_data.get('data', {})
            new_state = data.get('new_state')
            old_state = data.get('old_state')
            event_type = data.get('event_type')
            bot_id = webhook_data.get('bot_id')
            
            logger.info(f"Bot state change: {old_state} -> {new_state}, event_type: {event_type}, bot_id: {bot_id}")
            
            # Check if meeting has ended and recording is available
            # Based on Attendee.dev webhook documentation: https://docs.attendee.dev/guides/webhooks
            if (event_type == 'post_processing_completed' and 
                new_state == 'ended' and 
                old_state == 'post_processing'):
                
                logger.info(f"Meeting ended and recording available for bot {bot_id}")
                
                # Trigger transcript retrieval
                await self._retrieve_final_transcript(bot_id, user_id)
                
                # Update meeting status to completed
                await self._update_meeting_status(bot_id, 'completed')
                
            # Handle other state changes
            elif new_state == 'joined':
                logger.info(f"Bot {bot_id} joined the meeting")
                await self._update_meeting_status(bot_id, 'bot_joined')
                
            elif new_state == 'recording':
                logger.info(f"Bot {bot_id} started recording")
                await self._update_meeting_status(bot_id, 'transcribing')
                
            elif new_state == 'post_processing':
                logger.info(f"Bot {bot_id} finished recording, processing transcript")
                await self._update_meeting_status(bot_id, 'post_processing')
            
            # Update bot status in database
            await self._update_bot_status(bot_id, {
                'status': new_state,
                'last_state_change': data.get('created_at'),
                'event_type': event_type,
                'event_sub_type': data.get('event_sub_type')
            })
            
        except Exception as e:
            logger.error(f"Failed to handle bot state change: {e}")
    
    async def _handle_transcript_update(self, webhook_data: Dict[str, Any], user_id: str):
        """Handle transcript update webhook."""
        try:
            data = webhook_data.get('data', {})
            bot_id = webhook_data.get('bot_id')
            
            if not bot_id:
                logger.warning("No bot_id in transcript update webhook")
                return
            
            # Extract transcript data
            speaker_name = data.get('speaker_name')
            speaker_uuid = data.get('speaker_uuid')
            timestamp_ms = data.get('timestamp_ms')
            duration_ms = data.get('duration_ms')
            transcript_text = data.get('transcription', {}).get('transcript', '')
            
            logger.info(f"Transcript update for bot {bot_id}: {speaker_name} - {transcript_text[:50]}...")
            
            # Store transcript segment
            await self._store_transcript_segment(
                bot_id=bot_id,
                speaker_name=speaker_name,
                speaker_uuid=speaker_uuid,
                timestamp_ms=timestamp_ms,
                duration_ms=duration_ms,
                transcript_text=transcript_text,
                user_id=user_id
            )
            
            # Update meeting with latest transcript
            await self._update_meeting_transcript(bot_id, user_id)
            
        except Exception as e:
            logger.error(f"Failed to handle transcript update: {e}")
    
    async def _handle_chat_message_update(self, webhook_data: Dict[str, Any], user_id: str):
        """Handle chat message update webhook."""
        try:
            data = webhook_data.get('data', {})
            bot_id = webhook_data.get('bot_id')
            
            if not bot_id:
                logger.warning("No bot_id in chat message update webhook")
                return
            
            # Extract chat message data
            message_id = data.get('id')
            message_text = data.get('text')
            sender_name = data.get('sender_name')
            sender_uuid = data.get('sender_uuid')
            timestamp = data.get('timestamp')
            to_recipient = data.get('to')
            
            logger.info(f"Chat message update for bot {bot_id}: {sender_name} -> {to_recipient}: {message_text[:50]}...")
            
            # Store chat message
            await self._store_chat_message(
                bot_id=bot_id,
                message_id=message_id,
                message_text=message_text,
                sender_name=sender_name,
                sender_uuid=sender_uuid,
                timestamp=timestamp,
                to_recipient=to_recipient,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Failed to handle chat message update: {e}")
    
    async def _handle_participant_event(self, webhook_data: Dict[str, Any], user_id: str):
        """Handle participant event webhook."""
        try:
            data = webhook_data.get('data', {})
            bot_id = webhook_data.get('bot_id')
            
            if not bot_id:
                logger.warning("No bot_id in participant event webhook")
                return
            
            # Extract participant event data
            event_id = data.get('id')
            participant_name = data.get('participant_name')
            participant_uuid = data.get('participant_uuid')
            event_type = data.get('event_type')  # 'join' or 'leave'
            timestamp_ms = data.get('timestamp_ms')
            
            logger.info(f"Participant event for bot {bot_id}: {participant_name} {event_type}")
            
            # Store participant event
            await self._store_participant_event(
                bot_id=bot_id,
                event_id=event_id,
                participant_name=participant_name,
                participant_uuid=participant_uuid,
                event_type=event_type,
                timestamp_ms=timestamp_ms,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Failed to handle participant event: {e}")
    
    async def _handle_meeting_completed(self, bot_id: str, user_id: str):
        """Handle meeting completion when bot state changes to 'ended'."""
        try:
            logger.info(f"Meeting completed for bot {bot_id}")
            
            # Update meeting status
            await self._update_meeting_status(bot_id, 'completed', user_id)
            
            # Fetch final transcript from Attendee API
            # This would be done by the main service, not here
            # We just mark it as ready for processing
            
        except Exception as e:
            logger.error(f"Failed to handle meeting completion: {e}")
    
    # Private helper methods
    
    async def _log_webhook_receipt(self, webhook_id: str, trigger: str, bot_id: str, user_id: str, webhook_data: Dict[str, Any]):
        """Log webhook receipt in database."""
        try:
            log_record = {
                "webhook_id": webhook_id,
                "user_id": user_id,
                "bot_id": bot_id,
                "trigger": trigger,
                "webhook_data": webhook_data,
                "received_at": datetime.now().isoformat(),
                "processed": False
            }
            
            self.supabase.table("attendee_webhook_logs").insert(log_record).execute()
            
        except Exception as e:
            logger.error(f"Failed to log webhook receipt: {e}")
    
    async def _mark_webhook_processed(self, webhook_id: str, user_id: str):
        """Mark webhook as processed in database."""
        try:
            self.supabase.table("attendee_webhook_logs").update({
                "processed": True,
                "processed_at": datetime.now().isoformat()
            }).eq("webhook_id", webhook_id).eq("user_id", user_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to mark webhook as processed: {e}")
    
    async def _update_bot_status(self, bot_id: str, status_data: Dict[str, Any]):
        """Update bot status in database."""
        try:
            update_data = {
                "status": status_data.get('status'),
                "last_state_change": status_data.get('last_state_change'),
                "event_type": status_data.get('event_type'),
                "updated_at": datetime.now().isoformat()
            }
            
            self.supabase.table("meeting_bots").update(update_data).eq("bot_id", bot_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update bot status for {bot_id}: {e}")
    
    async def _store_transcript_segment(self, bot_id: str, speaker_name: str, speaker_uuid: str, 
                                      timestamp_ms: int, duration_ms: int, transcript_text: str, user_id: str):
        """Store transcript segment in database."""
        try:
            segment_record = {
                "bot_id": bot_id,
                "user_id": user_id,
                "speaker_name": speaker_name,
                "speaker_uuid": speaker_uuid,
                "timestamp_ms": timestamp_ms,
                "duration_ms": duration_ms,
                "transcript_text": transcript_text,
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase.table("transcript_segments").insert(segment_record).execute()
            
        except Exception as e:
            logger.error(f"Failed to store transcript segment: {e}")
    
    async def _update_meeting_transcript(self, bot_id: str, user_id: str):
        """Update meeting with latest transcript information."""
        try:
            # Get all transcript segments for this bot
            result = self.supabase.table("transcript_segments").select("*").eq("bot_id", bot_id).order("timestamp_ms").execute()
            
            if result.data:
                # Combine all segments into full transcript
                full_transcript = " ".join([seg['transcript_text'] for seg in result.data])
                
                # Get unique speakers
                speakers = list(set([seg['speaker_name'] for seg in result.data if seg['speaker_name']]))
                
                # Update meeting record
                update_data = {
                    "transcript": full_transcript,
                    "transcript_speakers": speakers,
                    "transcript_segments": result.data,
                    "transcript_retrieved_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                # Find meeting by bot_id and update
                self.supabase.table("meetings").update(update_data).eq("attendee_bot_id", bot_id).execute()
                
        except Exception as e:
            logger.error(f"Failed to update meeting transcript: {e}")
    
    async def _store_chat_message(self, bot_id: str, message_id: str, message_text: str, 
                                 sender_name: str, sender_uuid: str, timestamp: str, 
                                 to_recipient: str, user_id: str):
        """Store chat message in database."""
        try:
            message_record = {
                "bot_id": bot_id,
                "user_id": user_id,
                "message_id": message_id,
                "message": message_text,
                "sender_name": sender_name,
                "sender_uuid": sender_uuid,
                "timestamp": timestamp,
                "to_recipient": to_recipient,
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase.table("chat_messages").upsert(message_record).execute()
            
        except Exception as e:
            logger.error(f"Failed to store chat message: {e}")
    
    async def _store_participant_event(self, bot_id: str, event_id: str, participant_name: str, 
                                     participant_uuid: str, event_type: str, timestamp_ms: int, user_id: str):
        """Store participant event in database."""
        try:
            event_record = {
                "bot_id": bot_id,
                "user_id": user_id,
                "event_id": event_id,
                "participant_name": participant_name,
                "participant_uuid": participant_uuid,
                "event_type": event_type,
                "timestamp_ms": timestamp_ms,
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase.table("participant_events").insert(event_record).execute()
            
        except Exception as e:
            logger.error(f"Failed to store participant event: {e}")
    
    async def _update_meeting_status(self, bot_id: str, status: str, user_id: str):
        """Update meeting status in database."""
        try:
            update_data = {
                "bot_status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            # Find meeting by bot_id and update
            self.supabase.table("meetings").update(update_data).eq("attendee_bot_id", bot_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update meeting status: {e}")

    async def _retrieve_final_transcript(self, bot_id: str, user_id: str):
        """Retrieve final transcript when meeting ends."""
        try:
            logger.info(f"Retrieving final transcript for bot {bot_id}")
            
            # Get transcript from Attendee.dev API
            transcript_data = await self.attendee_service.get_transcript(bot_id)
            
            if transcript_data:
                # Store transcript in database
                await self._store_transcript(bot_id, transcript_data)
                
                # Update meeting record with transcript
                await self._update_meeting_transcript(bot_id, transcript_data)
                
                # TODO: Send to classification agent for project association
                # await self._send_to_classification_agent(bot_id, transcript_data, user_id)
                
                # TODO: Process through vector embedding workflow
                # await self._process_vector_embedding(bot_id, transcript_data, user_id)
                
                logger.info(f"Final transcript retrieved and stored for bot {bot_id}")
                
                # Mark transcript as ready for future processing
                await self._mark_transcript_ready_for_processing(bot_id)
                
            else:
                logger.warning(f"No transcript data received for bot {bot_id}")
                
        except Exception as e:
            logger.error(f"Failed to retrieve final transcript for bot {bot_id}: {e}")
    
    async def _update_meeting_status(self, bot_id: str, status: str):
        """Update meeting status based on bot state changes."""
        try:
            # Find meeting by bot ID
            meeting_result = await self.supabase.table('meetings').select('id').eq('attendee_bot_id', bot_id).single().execute()
            
            if meeting_result.data:
                meeting_id = meeting_result.data['id']
                
                # Update meeting status
                await self.supabase.table('meetings').update({
                    'bot_status': status,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', meeting_id).execute()
                
                logger.info(f"Updated meeting {meeting_id} status to {status}")
            else:
                logger.warning(f"No meeting found for bot {bot_id}")
                
        except Exception as e:
            logger.error(f"Failed to update meeting status for bot {bot_id}: {e}")
    
    async def _update_meeting_transcript(self, bot_id: str, transcript_data: Dict[str, Any]):
        """Update meeting record with transcript information."""
        try:
            # Find meeting by bot ID
            meeting_result = await self.supabase.table('meetings').select('id').eq('attendee_bot_id', bot_id).single().execute()
            
            if meeting_result.data:
                meeting_id = meeting_result.data['id']
                
                # Extract transcript information
                transcript_text = transcript_data.get('transcript_text', '')
                participants = transcript_data.get('participants', [])
                duration_minutes = transcript_data.get('duration_minutes', 0)
                
                # Update meeting with transcript
                update_data = {
                    'transcript': transcript_text,
                    'transcript_participants': participants,
                    'transcript_duration_seconds': duration_minutes * 60,
                    'transcript_retrieved_at': datetime.now().isoformat(),
                    'bot_status': 'completed',
                    'updated_at': datetime.now().isoformat()
                }
                
                await self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
                
                logger.info(f"Updated meeting {meeting_id} with transcript data")
            else:
                logger.warning(f"No meeting found for bot {bot_id}")
                
        except Exception as e:
            logger.error(f"Failed to update meeting transcript for bot {bot_id}: {e}")
    
    async def _mark_transcript_ready_for_processing(self, bot_id: str):
        """Mark transcript as ready for future classification and embedding processing."""
        try:
            # Find meeting by bot ID
            meeting_result = await self.supabase.table('meetings').select('id').eq('attendee_bot_id', bot_id).single().execute()
            
            if meeting_result.data:
                meeting_id = meeting_result.data['id']
                
                # Mark transcript as ready for future processing workflows
                await self.supabase.table('meetings').update({
                    'transcript_ready_for_classification': True,
                    'transcript_ready_for_embedding': True,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', meeting_id).execute()
                
                logger.info(f"Marked meeting {meeting_id} transcript as ready for future processing")
            else:
                logger.warning(f"No meeting found for bot {bot_id}")
                
        except Exception as e:
            logger.error(f"Failed to mark transcript ready for processing for bot {bot_id}: {e}")
