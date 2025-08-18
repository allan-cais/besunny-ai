"""
Core AI service for BeSunny.ai Python backend.
Provides OpenAI integration and AI processing capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from openai import AsyncOpenAI
from pydantic import BaseModel

from ...core.config import get_settings
from ...models.schemas.document import DocumentType, ClassificationSource

logger = logging.getLogger(__name__)


class AIProcessingResult(BaseModel):
    """Result of AI processing operation."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: int
    model_used: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None


class DocumentAnalysisResult(BaseModel):
    """Result of document analysis."""
    document_type: DocumentType
    confidence_score: float
    categories: List[str]
    keywords: List[str]
    summary: Optional[str] = None
    entities: List[Dict[str, Any]] = None
    sentiment: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    processing_time_ms: int


class AIService:
    """Core AI service for document processing and analysis."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model
        self.max_tokens = self.settings.openai_max_tokens
        
        # Rate limiting semaphore
        self._rate_limit_semaphore = asyncio.Semaphore(5)
        
        logger.info(f"AI Service initialized with model: {self.model}")
    
    async def classify_document(
        self, 
        content: str, 
        project_context: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> AIProcessingResult:
        """
        Classify a document using AI.
        
        Args:
            content: Document content to classify
            project_context: Optional project context for better classification
            user_preferences: Optional user preferences for classification
            
        Returns:
            AIProcessingResult with classification details
        """
        start_time = datetime.now()
        
        try:
            async with self._rate_limit_semaphore:
                system_prompt = self._build_classification_prompt(project_context, user_preferences)
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content[:4000]}  # Limit content length
                    ],
                    temperature=0.1,
                    max_tokens=200,
                    response_format={"type": "json_object"}
                )
                
                processing_time = (datetime.now() - start_time).microseconds // 1000
                
                # Parse response
                result_content = response.choices[0].message.content
                result = self._parse_classification_response(result_content)
                
                return AIProcessingResult(
                    success=True,
                    result=result,
                    processing_time_ms=processing_time,
                    model_used=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    cost_estimate=self._estimate_cost(response.usage.total_tokens if response.usage else 0)
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Document classification failed: {str(e)}")
            
            return AIProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model
            )
    
    async def analyze_document_content(
        self, 
        content: str, 
        analysis_type: str = "comprehensive"
    ) -> AIProcessingResult:
        """
        Perform comprehensive document content analysis.
        
        Args:
            content: Document content to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            AIProcessingResult with analysis details
        """
        start_time = datetime.now()
        
        try:
            async with self._rate_limit_semaphore:
                system_prompt = self._build_analysis_prompt(analysis_type)
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content[:4000]}
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )
                
                processing_time = (datetime.now() - start_time).microseconds // 1000
                
                result_content = response.choices[0].message.content
                result = self._parse_analysis_response(result_content)
                
                return AIProcessingResult(
                    success=True,
                    result=result,
                    processing_time_ms=processing_time,
                    model_used=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    cost_estimate=self._estimate_cost(response.usage.total_tokens if response.usage else 0)
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Document analysis failed: {str(e)}")
            
            return AIProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model
            )
    
    async def generate_document_summary(
        self, 
        content: str, 
        max_length: int = 200,
        summary_type: str = "general"
    ) -> AIProcessingResult:
        """
        Generate a document summary using AI.
        
        Args:
            content: Document content to summarize
            max_length: Maximum length of summary
            summary_type: Type of summary to generate
            
        Returns:
            AIProcessingResult with summary
        """
        start_time = datetime.now()
        
        try:
            async with self._rate_limit_semaphore:
                system_prompt = f"""
                You are an expert document summarizer. Generate a {summary_type} summary 
                of the following document in {max_length} characters or less.
                
                Focus on key points, main ideas, and important details.
                Return only the summary text, no additional formatting.
                """
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content[:4000]}
                    ],
                    temperature=0.3,
                    max_tokens=max_length
                )
                
                processing_time = (datetime.now() - start_time).microseconds // 1000
                
                summary = response.choices[0].message.content.strip()
                
                return AIProcessingResult(
                    success=True,
                    result={"summary": summary, "length": len(summary)},
                    processing_time_ms=processing_time,
                    model_used=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    cost_estimate=self._estimate_cost(response.usage.total_tokens if response.usage else 0)
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Summary generation failed: {str(e)}")
            
            return AIProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model
            )
    
    async def extract_entities(
        self, 
        content: str, 
        entity_types: Optional[List[str]] = None
    ) -> AIProcessingResult:
        """
        Extract named entities from document content.
        
        Args:
            content: Document content to analyze
            entity_types: Types of entities to extract
            
        Returns:
            AIProcessingResult with extracted entities
        """
        start_time = datetime.now()
        
        try:
            async with self._rate_limit_semaphore:
                if entity_types is None:
                    entity_types = ["people", "organizations", "locations", "dates", "money"]
                
                system_prompt = f"""
                Extract named entities from the following document content.
                Focus on these entity types: {', '.join(entity_types)}
                
                Return a JSON object with the following structure:
                {{
                    "entities": {{
                        "people": ["list of people"],
                        "organizations": ["list of organizations"],
                        "locations": ["list of locations"],
                        "dates": ["list of dates"],
                        "money": ["list of monetary amounts"]
                    }}
                }}
                """
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content[:4000]}
                    ],
                    temperature=0.1,
                    max_tokens=300,
                    response_format={"type": "json_object"}
                )
                
                processing_time = (datetime.now() - start_time).microseconds // 1000
                
                result_content = response.choices[0].message.content
                result = self._parse_entity_response(result_content)
                
                return AIProcessingResult(
                    success=True,
                    result=result,
                    processing_time_ms=processing_time,
                    model_used=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    cost_estimate=self._estimate_cost(response.usage.total_tokens if response.usage else 0)
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Entity extraction failed: {str(e)}")
            
            return AIProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model
            )
    
    def _build_classification_prompt(
        self, 
        project_context: Optional[str], 
        user_preferences: Optional[Dict[str, Any]]
    ) -> str:
        """Build the system prompt for document classification."""
        base_prompt = """
        You are an expert document classifier for the BeSunny.ai platform.
        
        Classify the following document into one of these categories:
        - email: Email communications, messages, correspondence
        - document: General documents, reports, articles, text files
        - spreadsheet: Data tables, financial reports, analytics, CSV files
        - presentation: Slides, decks, visual presentations, PowerPoint files
        - image: Images, diagrams, charts, visual content
        - folder: Directory structures, file organization
        - meeting_transcript: Meeting recordings, transcripts, conversation logs
        
        Consider the content, format, and context when classifying.
        Return a JSON object with the following structure:
        {
            "document_type": "category_name",
            "confidence_score": 0.95,
            "categories": ["primary_category", "secondary_category"],
            "keywords": ["key", "words", "extracted"],
            "reasoning": "Brief explanation of classification decision"
        }
        """
        
        if project_context:
            base_prompt += f"\n\nProject Context: {project_context}"
        
        if user_preferences:
            base_prompt += f"\n\nUser Preferences: {user_preferences}"
        
        return base_prompt
    
    def _build_analysis_prompt(self, analysis_type: str) -> str:
        """Build the system prompt for document analysis."""
        if analysis_type == "comprehensive":
            return """
            Perform comprehensive analysis of the following document.
            
            Return a JSON object with:
            {
                "summary": "Brief summary of the document",
                "key_points": ["list", "of", "key", "points"],
                "topics": ["main", "topics", "covered"],
                "sentiment": "positive/negative/neutral",
                "language": "detected language",
                "complexity": "simple/medium/complex",
                "recommendations": ["list", "of", "recommendations"]
            }
            """
        else:
            return """
            Analyze the following document content.
            
            Return a JSON object with analysis results.
            """
    
    def _parse_classification_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the classification response from OpenAI."""
        try:
            import json
            result = json.loads(response_content)
            
            # Validate required fields
            required_fields = ["document_type", "confidence_score", "categories", "keywords"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing required field in classification response: {field}")
                    result[field] = None if field != "confidence_score" else 0.0
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
            return {
                "document_type": "document",
                "confidence_score": 0.0,
                "categories": ["unknown"],
                "keywords": [],
                "error": "Failed to parse response"
            }
    
    def _parse_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the analysis response from OpenAI."""
        try:
            import json
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return {"error": "Failed to parse response"}
    
    def _parse_entity_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the entity extraction response from OpenAI."""
        try:
            import json
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse entity response: {e}")
            return {"error": "Failed to parse response"}
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate the cost of OpenAI API usage."""
        # Rough cost estimates (these should be updated based on current pricing)
        if self.model.startswith("gpt-4"):
            return (tokens / 1000) * 0.03  # $0.03 per 1K tokens
        elif self.model.startswith("gpt-3.5"):
            return (tokens / 1000) * 0.002  # $0.002 per 1K tokens
        else:
            return 0.0
    
    async def generate_bot_configuration(self, meeting_context: str) -> AIProcessingResult:
        """
        Generate bot configuration for a meeting using AI.
        
        Args:
            meeting_context: Meeting context and details
            
        Returns:
            AIProcessingResult with bot configuration
        """
        start_time = datetime.now()
        
        try:
            async with self._rate_limit_semaphore:
                system_prompt = """
                You are an AI assistant that generates optimal bot configurations for meeting transcription.
                
                Based on the meeting context, generate a JSON configuration with:
                {
                    "bot_name": "Appropriate bot name",
                    "description": "Bot description",
                    "transcription_enabled": true/false,
                    "summary_enabled": true/false,
                    "action_items_enabled": true/false,
                    "participant_tracking": true/false,
                    "chat_message": "Custom greeting message",
                    "auto_join": true/false,
                    "notification_preferences": {
                        "transcript_ready": true/false,
                        "summary_ready": true/false,
                        "action_items_ready": true/false
                    }
                }
                
                Consider the meeting type, duration, and context when generating the configuration.
                """
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": meeting_context}
                    ],
                    temperature=0.3,
                    max_tokens=300,
                    response_format={"type": "json_object"}
                )
                
                processing_time = (datetime.now() - start_time).microseconds // 1000
                
                # Parse response
                result_content = response.choices[0].message.content
                result = self._parse_bot_config_response(result_content)
                
                return AIProcessingResult(
                    success=True,
                    result=result,
                    processing_time_ms=processing_time,
                    model_used=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    cost_estimate=self._estimate_cost(response.usage.total_tokens) if response.usage else None
                )
                
        except Exception as e:
            logger.error(f"Bot configuration generation failed: {e}")
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return AIProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model
            )
    
    def _parse_bot_config_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the bot configuration response from OpenAI."""
        try:
            import json
            result = json.loads(response_content)
            
            # Set defaults for missing fields
            defaults = {
                "bot_name": "Sunny AI Notetaker",
                "description": "AI-powered meeting notetaker",
                "transcription_enabled": True,
                "summary_enabled": True,
                "action_items_enabled": True,
                "participant_tracking": True,
                "chat_message": "Hi, I'm here to transcribe this meeting!",
                "auto_join": True,
                "notification_preferences": {
                    "transcript_ready": True,
                    "summary_ready": True,
                    "action_items_ready": True
                }
            }
            
            # Merge with defaults
            for key, default_value in defaults.items():
                if key not in result:
                    result[key] = default_value
                elif key == "notification_preferences" and isinstance(result[key], dict):
                    for pref_key, pref_default in default_value.items():
                        if pref_key not in result[key]:
                            result[key][pref_key] = pref_default
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse bot configuration response: {e}")
            return defaults
    
    async def analyze_document_sentiment(self, content: str) -> AIProcessingResult:
        """
        Analyze document sentiment using AI.
        
        Args:
            content: Document content to analyze
            
        Returns:
            AIProcessingResult with sentiment analysis
        """
        start_time = datetime.now()
        
        try:
            async with self._rate_limit_semaphore:
                system_prompt = """
                Analyze the sentiment of the following document content.
                
                Return a JSON object with:
                {
                    "sentiment": "positive/negative/neutral",
                    "confidence": 0.95,
                    "key_phrases": ["phrase1", "phrase2"],
                    "emotional_tone": "professional/friendly/formal",
                    "reasoning": "Brief explanation of sentiment classification"
                }
                """
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content[:3000]}  # Limit content length
                    ],
                    temperature=0.1,
                    max_tokens=200,
                    response_format={"type": "json_object"}
                )
                
                processing_time = (datetime.now() - start_time).microseconds // 1000
                
                # Parse response
                result_content = response.choices[0].message.content
                result = self._parse_sentiment_response(result_content)
                
                return AIProcessingResult(
                    success=True,
                    result=result,
                    processing_time_ms=processing_time,
                    model_used=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    cost_estimate=self._estimate_cost(response.usage.total_tokens) if response.usage else None
                )
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return AIProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model
            )
    
    def _parse_sentiment_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the sentiment analysis response from OpenAI."""
        try:
            import json
            result = json.loads(response_content)
            
            # Set defaults for missing fields
            defaults = {
                "sentiment": "neutral",
                "confidence": 0.5,
                "key_phrases": [],
                "emotional_tone": "neutral",
                "reasoning": "Unable to determine sentiment"
            }
            
            # Merge with defaults
            for key, default_value in defaults.items():
                if key not in result:
                    result[key] = default_value
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse sentiment response: {e}")
            return defaults
    
    async def close(self):
        """Close the AI service and clean up resources."""
        # OpenAI client doesn't need explicit cleanup
        logger.info("AI Service closed")
