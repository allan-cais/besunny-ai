"""
Meeting Intelligence service for BeSunny.ai Python backend.
Provides AI-powered analysis of meeting transcripts and attendee bot integration.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel

from .ai_service import AIService, AIProcessingResult
from .embedding_service import EmbeddingService
from ...models.schemas.document import DocumentType, ClassificationSource
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class TranscriptSegment(BaseModel):
    """Individual transcript segment with speaker and timestamp."""
    start_time: float
    end_time: float
    speaker: str
    text: str
    confidence: Optional[float] = None


class MeetingTranscript(BaseModel):
    """Complete meeting transcript."""
    meeting_id: str
    transcript_id: str
    language: str = "en-US"
    duration_seconds: int
    participants: List[str]
    segments: List[TranscriptSegment]
    metadata: Optional[Dict[str, Any]] = None


class ActionItem(BaseModel):
    """Action item extracted from meeting transcript."""
    text: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    category: Optional[str] = None
    confidence_score: float
    timestamp: float
    speaker: str


class MeetingSummary(BaseModel):
    """AI-generated meeting summary."""
    executive_summary: str
    key_points: List[str]
    action_items: List[ActionItem]
    decisions_made: List[str]
    next_steps: List[str]
    participants_summary: Dict[str, str]
    sentiment_overall: str
    topics_discussed: List[str]
    meeting_outcome: str


class MeetingIntelligenceResult(BaseModel):
    """Result of meeting intelligence analysis."""
    meeting_id: str
    summary: MeetingSummary
    processing_time_ms: int
    model_used: str
    confidence_score: float
    metadata: Optional[Dict[str, Any]] = None


class AttendeeBotConfig(BaseModel):
    """Configuration for attendee bot behavior."""
    bot_name: str = "Sunny AI Notetaker"
    join_message: str = "Hi, I'm here to transcribe this meeting!"
    recording_enabled: bool = True
    transcription_enabled: bool = True
    summary_enabled: bool = True
    action_item_extraction: bool = True
    sentiment_analysis: bool = True
    custom_instructions: Optional[str] = None


class MeetingIntelligenceService:
    """Service for AI-powered meeting analysis and intelligence."""
    
    def __init__(self):
        self.settings = get_settings()
        self.ai_service = AIService()
        self.embedding_service = EmbeddingService()
        self._initialized = False
        
        logger.info("Meeting Intelligence Service initialized")
    
    async def initialize(self):
        """Initialize the meeting intelligence service."""
        if self._initialized:
            return
        
        try:
            await self.embedding_service.initialize()
            self._initialized = True
            logger.info("Meeting Intelligence service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize meeting intelligence service: {e}")
            raise
    
    async def analyze_meeting_transcript(
        self, 
        transcript: MeetingTranscript,
        project_context: Optional[str] = None
    ) -> MeetingIntelligenceResult:
        """
        Perform comprehensive analysis of a meeting transcript.
        
        Args:
            transcript: Meeting transcript to analyze
            project_context: Optional project context for better analysis
            
        Returns:
            MeetingIntelligenceResult with comprehensive analysis
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            # Combine all transcript text for analysis
            full_text = self._combine_transcript_text(transcript)
            
            # Generate meeting summary
            summary_result = await self._generate_meeting_summary(
                transcript, full_text, project_context
            )
            
            # Extract action items
            action_items = await self._extract_action_items(transcript, full_text)
            
            # Analyze sentiment
            sentiment = await self._analyze_meeting_sentiment(full_text)
            
            # Extract key decisions
            decisions = await self._extract_decisions(full_text)
            
            # Generate next steps
            next_steps = await self._generate_next_steps(full_text, action_items)
            
            # Create comprehensive summary
            meeting_summary = MeetingSummary(
                executive_summary=summary_result.get("summary", ""),
                key_points=summary_result.get("key_points", []),
                action_items=action_items,
                decisions_made=decisions,
                next_steps=next_steps,
                participants_summary=await self._analyze_participants(transcript),
                sentiment_overall=sentiment,
                topics_discussed=summary_result.get("topics", []),
                meeting_outcome=summary_result.get("outcome", "completed")
            )
            
            # Store transcript embeddings for future search
            await self._store_transcript_embeddings(transcript)
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return MeetingIntelligenceResult(
                meeting_id=transcript.meeting_id,
                summary=meeting_summary,
                processing_time_ms=processing_time,
                model_used=self.ai_service.model,
                confidence_score=0.85,  # Base confidence score
                metadata={
                    "participants_count": len(transcript.participants),
                    "segments_count": len(transcript.segments),
                    "duration_minutes": transcript.duration_seconds / 60,
                    "language": transcript.language
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Meeting transcript analysis failed: {str(e)}")
            
            # Return basic result with error
            return MeetingIntelligenceResult(
                meeting_id=transcript.meeting_id,
                summary=MeetingSummary(
                    executive_summary="Analysis failed",
                    key_points=[],
                    action_items=[],
                    decisions_made=[],
                    next_steps=[],
                    participants_summary={},
                    sentiment_overall="neutral",
                    topics_discussed=[],
                    meeting_outcome="analysis_failed"
                ),
                processing_time_ms=processing_time,
                model_used="unknown",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def extract_action_items_from_transcript(
        self, 
        transcript: MeetingTranscript
    ) -> List[ActionItem]:
        """
        Extract action items from meeting transcript.
        
        Args:
            transcript: Meeting transcript to analyze
            
        Returns:
            List of extracted action items
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            full_text = self._combine_transcript_text(transcript)
            
            system_prompt = """
            Extract action items from the following meeting transcript.
            
            Look for:
            - Tasks that need to be completed
            - Assignments given to specific people
            - Deadlines mentioned
            - Follow-up actions required
            
            Return a JSON array of action items with this structure:
            [
                {
                    "text": "Action item description",
                    "assignee": "Person responsible (if mentioned)",
                    "due_date": "Due date if mentioned",
                    "priority": "low/medium/high",
                    "category": "Category of action item",
                    "confidence_score": 0.95,
                    "timestamp": 120.5,
                    "speaker": "Speaker who mentioned it"
                }
            ]
            """
            
            response = await self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text[:4000]}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result_content = response.choices[0].message.content
            action_items_data = self._parse_action_items_response(result_content)
            
            # Convert to ActionItem objects
            action_items = []
            for item_data in action_items_data:
                # Find the speaker and timestamp for this action item
                speaker, timestamp = self._find_action_item_context(
                    item_data.get("text", ""), transcript
                )
                
                action_item = ActionItem(
                    text=item_data.get("text", ""),
                    assignee=item_data.get("assignee"),
                    due_date=item_data.get("due_date"),
                    priority=item_data.get("priority", "medium"),
                    category=item_data.get("category"),
                    confidence_score=item_data.get("confidence_score", 0.8),
                    timestamp=timestamp,
                    speaker=speaker
                )
                action_items.append(action_item)
            
            return action_items
            
        except Exception as e:
            logger.error(f"Action item extraction failed: {str(e)}")
            return []
    
    async def generate_meeting_summary(
        self, 
        transcript: MeetingTranscript,
        summary_type: str = "comprehensive"
    ) -> str:
        """
        Generate a meeting summary.
        
        Args:
            transcript: Meeting transcript to summarize
            summary_type: Type of summary to generate
            
        Returns:
            Generated summary text
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            full_text = self._combine_transcript_text(transcript)
            
            system_prompt = f"""
            Generate a {summary_type} summary of the following meeting transcript.
            
            Include:
            - Key discussion points
            - Important decisions made
            - Action items assigned
            - Overall meeting outcome
            
            Format the summary in a clear, professional manner.
            """
            
            response = await self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text[:4000]}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Meeting summary generation failed: {str(e)}")
            return "Failed to generate meeting summary."
    
    async def analyze_meeting_sentiment(
        self, 
        transcript: MeetingTranscript
    ) -> Dict[str, Any]:
        """
        Analyze sentiment throughout the meeting.
        
        Args:
            transcript: Meeting transcript to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            full_text = self._combine_transcript_text(transcript)
            
            system_prompt = """
            Analyze the sentiment of the following meeting transcript.
            
            Return a JSON object with:
            {
                "overall_sentiment": "positive/negative/neutral/mixed",
                "sentiment_score": 0.75,
                "emotional_tones": ["professional", "collaborative", "tense"],
                "participant_sentiments": {
                    "participant_name": "positive/negative/neutral"
                },
                "sentiment_timeline": [
                    {
                        "time_range": "0-15 minutes",
                        "sentiment": "positive",
                        "key_events": ["description of what happened"]
                    }
                ]
            }
            """
            
            response = await self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text[:4000]}
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            result_content = response.choices[0].message.content
            return self._parse_sentiment_response(result_content)
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.5,
                "emotional_tones": [],
                "participant_sentiments": {},
                "sentiment_timeline": []
            }
    
    async def search_meeting_content(
        self, 
        query: str,
        project_id: Optional[str] = None,
        meeting_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for specific content within meeting transcripts.
        
        Args:
            query: Search query
            project_id: Optional project ID to filter results
            meeting_ids: Optional list of meeting IDs to search within
            top_k: Number of top results to return
            
        Returns:
            List of search results with meeting context
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use vector search to find relevant content
            search_result = await self.embedding_service.search_similar_documents(
                query=query,
                project_id=project_id,
                top_k=top_k
            )
            
            if not search_result.success:
                return []
            
            # Filter results to only include meeting transcripts
            meeting_results = []
            for result in search_result.results or []:
                metadata = result.get("metadata", {})
                if metadata.get("document_type") == "meeting_transcript":
                    if not meeting_ids or metadata.get("meeting_id") in meeting_ids:
                        meeting_results.append({
                            "meeting_id": metadata.get("meeting_id"),
                            "score": result.get("score"),
                            "text": metadata.get("text", ""),
                            "timestamp": metadata.get("timestamp"),
                            "speaker": metadata.get("speaker")
                        })
            
            return meeting_results
            
        except Exception as e:
            logger.error(f"Meeting content search failed: {str(e)}")
            return []
    
    def _combine_transcript_text(self, transcript: MeetingTranscript) -> str:
        """Combine all transcript segments into a single text."""
        combined_text = ""
        for segment in transcript.segments:
            combined_text += f"[{segment.start_time:.1f}s] {segment.speaker}: {segment.text}\n"
        return combined_text
    
    async def _generate_meeting_summary(
        self, 
        transcript: MeetingTranscript, 
        full_text: str,
        project_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive meeting summary."""
        try:
            system_prompt = f"""
            Analyze this meeting transcript and provide a comprehensive summary.
            
            Return a JSON object with:
            {{
                "summary": "Executive summary of the meeting",
                "key_points": ["list", "of", "key", "points"],
                "topics": ["main", "topics", "discussed"],
                "outcome": "Overall meeting outcome and conclusion"
            }}
            
            {f"Project Context: {project_context}" if project_context else ""}
            """
            
            response = await self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text[:4000]}
                ],
                temperature=0.3,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            result_content = response.choices[0].message.content
            return self._parse_summary_response(result_content)
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {
                "summary": "Failed to generate summary",
                "key_points": [],
                "topics": [],
                "outcome": "unknown"
            }
    
    async def _extract_action_items(
        self, 
        transcript: MeetingTranscript, 
        full_text: str
    ) -> List[ActionItem]:
        """Extract action items from transcript."""
        return await self.extract_action_items_from_transcript(transcript)
    
    async def _analyze_meeting_sentiment(self, full_text: str) -> str:
        """Analyze overall meeting sentiment."""
        try:
            system_prompt = """
            Determine the overall sentiment of this meeting transcript.
            Return only one word: positive, negative, neutral, or mixed.
            """
            
            response = await self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text[:2000]}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            return response.choices[0].message.content.strip().lower()
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return "neutral"
    
    async def _extract_decisions(self, full_text: str) -> List[str]:
        """Extract decisions made during the meeting."""
        try:
            system_prompt = """
            Extract decisions made during this meeting.
            Return a JSON array of decision strings.
            """
            
            response = await self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text[:2000]}
                ],
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result_content = response.choices[0].message.content
            decisions_data = self._parse_decisions_response(result_content)
            return decisions_data
            
        except Exception as e:
            logger.error(f"Decision extraction failed: {str(e)}")
            return []
    
    async def _generate_next_steps(
        self, 
        full_text: str, 
        action_items: List[ActionItem]
    ) -> List[str]:
        """Generate next steps based on meeting content and action items."""
        try:
            system_prompt = """
            Based on this meeting transcript and action items, suggest next steps.
            Return a JSON array of next step strings.
            """
            
            context = f"Action Items: {[item.text for item in action_items]}\n\nTranscript: {full_text[:2000]}"
            
            response = await self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result_content = response.choices[0].message.content
            next_steps_data = self._parse_next_steps_response(result_content)
            return next_steps_data
            
        except Exception as e:
            logger.error(f"Next steps generation failed: {str(e)}")
            return []
    
    async def _analyze_participants(self, transcript: MeetingTranscript) -> Dict[str, str]:
        """Analyze participant contributions and roles."""
        try:
            participant_analysis = {}
            
            for participant in transcript.participants:
                # Count segments and calculate speaking time
                participant_segments = [s for s in transcript.segments if s.speaker == participant]
                speaking_time = sum(s.end_time - s.start_time for s in participant_segments)
                
                # Analyze contribution type
                if speaking_time > transcript.duration_seconds * 0.3:
                    role = "primary_speaker"
                elif speaking_time > transcript.duration_seconds * 0.1:
                    role = "active_participant"
                else:
                    role = "listener"
                
                participant_analysis[participant] = role
            
            return participant_analysis
            
        except Exception as e:
            logger.error(f"Participant analysis failed: {str(e)}")
            return {}
    
    async def _store_transcript_embeddings(self, transcript: MeetingTranscript):
        """Store transcript embeddings for future search."""
        try:
            # Create embeddings for transcript segments
            for segment in transcript.segments:
                embedding_result = await self.embedding_service.generate_embeddings(segment.text)
                if embedding_result.success:
                    # Store in vector database for search
                    chunk = {
                        "id": f"{transcript.meeting_id}_{segment.start_time}",
                        "values": embedding_result.embeddings[0],
                        "metadata": {
                            "document_type": "meeting_transcript",
                            "meeting_id": transcript.meeting_id,
                            "transcript_id": transcript.transcript_id,
                            "text": segment.text,
                            "speaker": segment.speaker,
                            "timestamp": segment.start_time,
                            "duration": segment.end_time - segment.start_time
                        }
                    }
                    
                    # Store in Pinecone
                    self.embedding_service.pinecone_index.upsert(vectors=[chunk])
            
            logger.info(f"Stored embeddings for {len(transcript.segments)} transcript segments")
            
        except Exception as e:
            logger.error(f"Failed to store transcript embeddings: {e}")
    
    def _find_action_item_context(
        self, 
        action_text: str, 
        transcript: MeetingTranscript
    ) -> tuple[str, float]:
        """Find the speaker and timestamp for an action item."""
        # Simple heuristic: find the segment that contains the action item text
        for segment in transcript.segments:
            if action_text.lower() in segment.text.lower():
                return segment.speaker, segment.start_time
        
        # Fallback to first speaker and timestamp
        if transcript.segments:
            return transcript.segments[0].speaker, transcript.segments[0].start_time
        
        return "unknown", 0.0
    
    def _parse_action_items_response(self, response_content: str) -> List[Dict[str, Any]]:
        """Parse action items response from AI."""
        try:
            import json
            data = json.loads(response_content)
            return data.get("action_items", [])
        except json.JSONDecodeError:
            return []
    
    def _parse_summary_response(self, response_content: str) -> Dict[str, Any]:
        """Parse summary response from AI."""
        try:
            import json
            return json.loads(response_content)
        except json.JSONDecodeError:
            return {
                "summary": "Failed to parse summary",
                "key_points": [],
                "topics": [],
                "outcome": "unknown"
            }
    
    def _parse_sentiment_response(self, response_content: str) -> Dict[str, Any]:
        """Parse sentiment response from AI."""
        try:
            import json
            return json.loads(response_content)
        except json.JSONDecodeError:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.5,
                "emotional_tones": [],
                "participant_sentiments": {},
                "sentiment_timeline": []
            }
    
    def _parse_decisions_response(self, response_content: str) -> List[str]:
        """Parse decisions response from AI."""
        try:
            import json
            data = json.loads(response_content)
            return data.get("decisions", [])
        except json.JSONDecodeError:
            return []
    
    def _parse_next_steps_response(self, response_content: str) -> List[str]:
        """Parse next steps response from AI."""
        try:
            import json
            data = json.loads(response_content)
            return data.get("next_steps", [])
        except json.JSONDecodeError:
            return []
    
    async def close(self):
        """Close the meeting intelligence service and clean up resources."""
        await self.embedding_service.close()
        self._initialized = False
        logger.info("Meeting Intelligence Service closed")
