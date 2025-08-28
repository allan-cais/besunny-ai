"""
Classification schemas for BeSunny.ai Python backend.
Provides data models for AI-powered document classification requests and results.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .document import DocumentType, ClassificationSource


class ClassificationPriority(str, Enum):
    """Priority levels for classification requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ClassificationWorkflow(str, Enum):
    """Classification workflow types."""
    STANDARD = "standard"
    ADVANCED = "advanced"
    CUSTOM = "custom"


class ClassificationRequest(BaseModel):
    """Request for document classification."""
    document_id: str = Field(..., description="Unique identifier for the document")
    content: str = Field(..., description="Document content to classify")
    project_id: Optional[str] = Field(None, description="Optional project ID for context")
    user_id: str = Field(..., description="User ID requesting classification")
    document_type: Optional[DocumentType] = Field(None, description="Expected document type")
    classification_workflow: ClassificationWorkflow = Field(ClassificationWorkflow.STANDARD, description="Classification workflow to use")
    priority: ClassificationPriority = Field(ClassificationPriority.NORMAL, description="Classification priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for classification")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User-specific classification preferences")
    force_reclassification: bool = Field(False, description="Force reclassification even if already classified")


class ClassificationResult(BaseModel):
    """Result of document classification."""
    document_id: str = Field(..., description="Document ID that was classified")
    document_type: DocumentType = Field(..., description="Detected document type")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    project_id: Optional[str] = Field(None, description="Matched project ID")
    categories: List[str] = Field(default_factory=list, description="Detected categories")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    summary: Optional[str] = Field(None, description="Generated content summary")
    entities: Optional[Dict[str, Any]] = Field(None, description="Extracted entities")
    sentiment: Optional[str] = Field(None, description="Content sentiment analysis")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(..., description="AI model used for classification")
    classification_source: ClassificationSource = Field(ClassificationSource.AI, description="Source of classification")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional classification metadata")
    classification_notes: Optional[str] = Field(None, description="Notes about classification decision")
    created_at: datetime = Field(default_factory=datetime.now, description="When classification was performed")


class BatchClassificationRequest(BaseModel):
    """Request for batch document classification."""
    documents: List[ClassificationRequest] = Field(..., description="List of documents to classify")
    user_id: str = Field(..., description="User ID requesting batch classification")
    project_id: Optional[str] = Field(None, description="Optional project ID for context")
    workflow: ClassificationWorkflow = Field(ClassificationWorkflow.STANDARD, description="Classification workflow to use")
    priority: ClassificationPriority = Field(ClassificationPriority.NORMAL, description="Classification priority")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User-specific classification preferences")
    batch_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional batch metadata")


class BatchClassificationResult(BaseModel):
    """Result of batch document classification."""
    batch_id: str = Field(..., description="Unique batch identifier")
    user_id: str = Field(..., description="User ID who requested classification")
    project_id: Optional[str] = Field(None, description="Project ID if applicable")
    status: str = Field(..., description="Batch processing status")
    total_documents: int = Field(..., description="Total number of documents in batch")
    processed_documents: int = Field(..., description="Number of successfully processed documents")
    failed_documents: int = Field(..., description="Number of failed document classifications")
    results: List[ClassificationResult] = Field(..., description="Individual classification results")
    processing_time_ms: int = Field(..., description="Total batch processing time in milliseconds")
    created_at: datetime = Field(default_factory=datetime.now, description="When batch was created")
    completed_at: Optional[datetime] = Field(None, description="When batch processing completed")
    error_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of any errors encountered")


class ClassificationHistory(BaseModel):
    """Classification history record."""
    id: str = Field(..., description="Unique history record ID")
    document_id: str = Field(..., description="Document ID")
    user_id: str = Field(..., description="User ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    classification_result: ClassificationResult = Field(..., description="Classification result")
    created_at: datetime = Field(..., description="When classification was performed")
    updated_at: Optional[datetime] = Field(None, description="When record was last updated")


class ClassificationMetrics(BaseModel):
    """Classification performance metrics."""
    user_id: str = Field(..., description="User ID")
    total_classifications: int = Field(..., description="Total number of classifications")
    successful_classifications: int = Field(..., description="Number of successful classifications")
    failed_classifications: int = Field(..., description="Number of failed classifications")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Classification success rate")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score")
    average_processing_time_ms: float = Field(..., description="Average processing time in milliseconds")
    total_processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    model_usage: Dict[str, int] = Field(default_factory=dict, description="Usage count by AI model")
    period_start: datetime = Field(..., description="Start of metrics period")
    period_end: datetime = Field(..., description="End of metrics period")
