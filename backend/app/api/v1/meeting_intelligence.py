"""
Meeting Intelligence API endpoints for BeSunny.ai Python backend.
Provides AI-powered meeting transcript analysis and attendee bot integration.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import time

from ...services.ai.meeting_intelligence_service import (
    MeetingIntelligenceService,
    MeetingTranscript,
    MeetingIntelligenceResult,
    ActionItem,
    AttendeeBotConfig
)
from ...core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/transcripts/analyze", response_model=MeetingIntelligenceResult)
async def analyze_meeting_transcript(
    transcript: MeetingTranscript,
    project_context: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze a meeting transcript using AI.
    
    This endpoint performs comprehensive analysis of meeting transcripts including:
    - Executive summary generation
    - Key points extraction
    - Action item identification
    - Decision tracking
    - Sentiment analysis
    - Participant analysis
    """
    try:
        meeting_intelligence_service = MeetingIntelligenceService()
        await meeting_intelligence_service.initialize()
        
        # Perform transcript analysis
        result = await meeting_intelligence_service.analyze_meeting_transcript(
            transcript=transcript,
            project_context=project_context
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Meeting transcript analysis failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Meeting transcript analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/transcripts/action-items")
async def extract_action_items(
    transcript: MeetingTranscript,
    current_user: dict = Depends(get_current_user)
):
    """
    Extract action items from meeting transcript.
    
    This endpoint identifies and extracts actionable items from meeting
    conversations including assignments, deadlines, and follow-up tasks.
    """
    try:
        meeting_intelligence_service = MeetingIntelligenceService()
        await meeting_intelligence_service.initialize()
        
        # Extract action items
        action_items = await meeting_intelligence_service.extract_action_items_from_transcript(transcript)
        
        return {
            "meeting_id": transcript.meeting_id,
            "action_items": action_items,
            "total_action_items": len(action_items),
            "extraction_status": "success"
        }
        
    except Exception as e:
        logger.error(f"Action item extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Action item extraction failed: {str(e)}")


@router.post("/transcripts/summary")
async def generate_meeting_summary(
    transcript: MeetingTranscript,
    summary_type: str = "comprehensive",
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a meeting summary using AI.
    
    This endpoint creates concise summaries of meeting content with
    configurable detail levels and focus areas.
    """
    try:
        meeting_intelligence_service = MeetingIntelligenceService()
        await meeting_intelligence_service.initialize()
        
        # Generate summary
        summary = await meeting_intelligence_service.generate_meeting_summary(
            transcript=transcript,
            summary_type=summary_type
        )
        
        return {
            "meeting_id": transcript.meeting_id,
            "summary": summary,
            "summary_type": summary_type,
            "generation_status": "success"
        }
        
    except Exception as e:
        logger.error(f"Meeting summary generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/transcripts/sentiment")
async def analyze_meeting_sentiment(
    transcript: MeetingTranscript,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze sentiment throughout the meeting.
    
    This endpoint provides detailed sentiment analysis including:
    - Overall meeting sentiment
    - Participant-specific sentiments
    - Sentiment timeline
    - Emotional tone identification
    """
    try:
        meeting_intelligence_service = MeetingIntelligenceService()
        await meeting_intelligence_service.initialize()
        
        # Analyze sentiment
        sentiment_analysis = await meeting_intelligence_service.analyze_meeting_sentiment(transcript)
        
        return {
            "meeting_id": transcript.meeting_id,
            "sentiment_analysis": sentiment_analysis,
            "analysis_status": "success"
        }
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


@router.get("/search")
async def search_meeting_content(
    query: str,
    project_id: Optional[str] = None,
    meeting_ids: Optional[List[str]] = None,
    top_k: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Search for specific content within meeting transcripts.
    
    This endpoint uses vector similarity search to find relevant
    meeting content based on semantic queries.
    """
    try:
        meeting_intelligence_service = MeetingIntelligenceService()
        await meeting_intelligence_service.initialize()
        
        # Search meeting content
        search_results = await meeting_intelligence_service.search_meeting_content(
            query=query,
            project_id=project_id,
            meeting_ids=meeting_ids,
            top_k=top_k
        )
        
        return {
            "query": query,
            "search_results": search_results,
            "total_results": len(search_results),
            "project_id": project_id,
            "meeting_ids": meeting_ids,
            "search_status": "success"
        }
        
    except Exception as e:
        logger.error(f"Meeting content search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/transcripts/process-batch")
async def process_transcripts_batch(
    transcripts: List[MeetingTranscript],
    project_context: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Process multiple meeting transcripts in batch.
    
    This endpoint handles batch processing of transcripts for efficient
    analysis operations across multiple meetings.
    """
    try:
        meeting_intelligence_service = MeetingIntelligenceService()
        await meeting_intelligence_service.initialize()
        
        processed_transcripts = []
        total_action_items = 0
        
        for transcript in transcripts:
            try:
                # Analyze transcript
                result = await meeting_intelligence_service.analyze_meeting_transcript(
                    transcript=transcript,
                    project_context=project_context
                )
                
                if result and result.summary:
                    processed_transcripts.append({
                        "meeting_id": transcript.meeting_id,
                        "status": "success",
                        "summary": result.summary,
                        "action_items_count": len(result.summary.action_items),
                        "confidence_score": result.confidence_score
                    })
                    total_action_items += len(result.summary.action_items)
                else:
                    processed_transcripts.append({
                        "meeting_id": transcript.meeting_id,
                        "status": "failed",
                        "error": "Analysis returned no results"
                    })
                    
            except Exception as e:
                processed_transcripts.append({
                    "meeting_id": transcript.meeting_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "total_transcripts": len(transcripts),
            "successful_processing": len([t for t in processed_transcripts if t["status"] == "success"]),
            "failed_processing": len([t for t in processed_transcripts if t["status"] == "failed"]),
            "total_action_items": total_action_items,
            "results": processed_transcripts
        }
        
    except Exception as e:
        logger.error(f"Batch transcript processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.post("/bots/configure")
async def configure_attendee_bot(
    bot_config: AttendeeBotConfig,
    current_user: dict = Depends(get_current_user)
):
    """
    Configure attendee bot behavior for meetings.
    
    This endpoint allows users to customize how the AI attendee bot
    behaves during meetings including recording, transcription, and analysis settings.
    """
    try:
        # Store bot configuration (this would typically save to database)
        # For now, return the configuration as confirmation
        
        return {
            "message": "Attendee bot configuration updated successfully",
            "bot_config": bot_config.dict(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Bot configuration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bot configuration failed: {str(e)}")


@router.get("/bots/status")
async def get_attendee_bot_status(
    meeting_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of attendee bots.
    
    This endpoint provides information about attendee bot status
    including active meetings, recording status, and processing progress.
    """
    try:
        # This would typically query the database for bot status
        # For now, return mock data structure
        
        bot_status = {
            "active_bots": 3,
            "total_meetings": 15,
            "recording_meetings": 2,
            "processing_transcripts": 1,
            "completed_analyses": 12,
            "meeting_details": [
                {
                    "meeting_id": "meeting_123",
                    "bot_name": "Sunny AI Notetaker",
                    "status": "recording",
                    "start_time": "2024-01-01T10:00:00Z",
                    "participants": 5
                }
            ]
        }
        
        if meeting_id:
            # Filter for specific meeting
            meeting_bots = [b for b in bot_status["meeting_details"] if b["meeting_id"] == meeting_id]
            bot_status["meeting_details"] = meeting_bots
        
        return bot_status
        
    except Exception as e:
        logger.error(f"Bot status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.post("/meetings/{meeting_id}/reanalyze")
async def reanalyze_meeting(
    meeting_id: str,
    transcript: MeetingTranscript,
    project_context: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Reanalyze an existing meeting transcript.
    
    This endpoint allows reanalysis of meeting transcripts when
    improved AI models or analysis techniques become available.
    """
    try:
        meeting_intelligence_service = MeetingIntelligenceService()
        await meeting_intelligence_service.initialize()
        
        # Reanalyze transcript
        result = await meeting_intelligence_service.analyze_meeting_transcript(
            transcript=transcript,
            project_context=project_context
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Meeting reanalysis failed")
        
        return {
            "meeting_id": meeting_id,
            "reanalysis_result": result,
            "status": "success",
            "message": "Meeting transcript reanalyzed successfully"
        }
        
    except Exception as e:
        logger.error(f"Meeting reanalysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reanalysis failed: {str(e)}")


@router.get("/analytics")
async def get_meeting_analytics(
    project_id: Optional[str] = None,
    time_range: str = "30d",
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics about meeting intelligence.
    
    This endpoint provides insights into meeting analysis performance,
    action item trends, and participant engagement metrics.
    """
    try:
        # This would typically query the database for analytics
        # For now, return mock data structure
        
        analytics = {
            "time_range": time_range,
            "total_meetings": 45,
            "total_participants": 180,
            "total_action_items": 156,
            "average_meeting_duration": 45,
            "sentiment_distribution": {
                "positive": 0.6,
                "neutral": 0.3,
                "negative": 0.1
            },
            "action_item_completion_rate": 0.78,
            "top_topics": [
                "Project Planning",
                "Status Updates",
                "Technical Discussion",
                "Decision Making"
            ],
            "participant_engagement": {
                "high": 12,
                "medium": 18,
                "low": 15
            }
        }
        
        if project_id:
            # Filter for specific project
            analytics["project_id"] = project_id
            analytics["project_meetings"] = 15
        
        return analytics
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.get("/health")
async def meeting_intelligence_health_check():
    """
    Lightweight health check for meeting intelligence service.
    
    This endpoint verifies that the meeting intelligence services
    are properly configured without initializing heavy services.
    """
    try:
        # Check if required configuration is available
        from ...core.config import get_settings
        settings = get_settings()
        
        has_openai_key = bool(settings.openai_api_key)
        has_model_config = bool(settings.openai_model)
        
        if has_openai_key and has_model_config:
            return {
                "status": "healthy",
                "service": "meeting_intelligence",
                "configuration": "valid",
                "model": settings.openai_model,
                "message": "Meeting intelligence service is properly configured",
                "timestamp": time.time()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "meeting_intelligence",
                    "error": "Missing required configuration",
                    "missing": {
                        "openai_api_key": not has_openai_key,
                        "openai_model": not has_model_config
                    },
                    "timestamp": time.time()
                }
            )
        
    except Exception as e:
        logger.error(f"Meeting intelligence health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "meeting_intelligence",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@router.get("/models")
async def get_available_meeting_models(current_user: dict = Depends(get_current_user)):
    """
    Get available AI models for meeting intelligence.
    
    This endpoint provides information about available AI models
    and their capabilities for meeting analysis.
    """
    try:
        # Define available models for meeting intelligence
        available_models = {
            "gpt-4": {
                "name": "GPT-4",
                "capabilities": [
                    "transcript_analysis",
                    "action_item_extraction",
                    "sentiment_analysis",
                    "summary_generation",
                    "decision_tracking"
                ],
                "recommended_for": "complex_meetings",
                "performance": "excellent"
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "capabilities": [
                    "transcript_analysis",
                    "action_item_extraction",
                    "summary_generation"
                ],
                "recommended_for": "standard_meetings",
                "performance": "good"
            }
        }
        
        return {
            "available_models": available_models,
            "current_model": "gpt-4",
            "model_selection": "Automatic based on meeting complexity and requirements"
        }
        
    except Exception as e:
        logger.error(f"Model information retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model information failed: {str(e)}")
