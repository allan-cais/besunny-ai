"""
Project schemas for BeSunny.ai Python backend.
Defines data models for project management operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Project(BaseModel):
    """Project model."""
    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    status: Optional[str] = Field(None, description="Project status")
    created_by: str = Field(..., description="User ID who created the project")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    normalized_tags: Optional[List[str]] = Field(None, description="Standardized tags for classification")
    categories: Optional[List[str]] = Field(None, description="High-level project categories")
    reference_keywords: Optional[List[str]] = Field(None, description="Key terms for content matching")
    notes: Optional[str] = Field(None, description="Human-readable project summary")
    classification_signals: Optional[Dict[str, Any]] = Field(None, description="Advanced classification metadata")
    entity_patterns: Optional[Dict[str, Any]] = Field(None, description="People, emails, locations, and organizations")
    pinecone_document_count: Optional[int] = Field(None, description="Number of documents in Pinecone")
    last_classification_at: Optional[datetime] = Field(None, description="Timestamp of most recent classification")
    classification_feedback: Optional[Dict[str, Any]] = Field(None, description="Learning data from classification results")


class ProjectCreate(BaseModel):
    """Project creation request."""
    name: str = Field(..., description="Project name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Project description", max_length=1000)


class ProjectUpdate(BaseModel):
    """Project update request."""
    name: Optional[str] = Field(None, description="Project name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Project description", max_length=1000)


class ProjectListResponse(BaseModel):
    """Response containing a list of projects."""
    projects: List[Project] = Field(..., description="List of projects")
    total_count: int = Field(..., description="Total number of projects")
    limit: int = Field(..., description="Number of projects returned")
    offset: int = Field(..., description="Number of projects skipped")


class ProjectStats(BaseModel):
    """Project statistics."""
    project_id: str = Field(..., description="Project ID")
    document_count: int = Field(0, description="Number of documents in the project")
    meeting_count: int = Field(0, description="Number of meetings in the project")
    documents_by_type: Dict[str, int] = Field(default_factory=dict, description="Document count by type")
    documents_by_status: Dict[str, int] = Field(default_factory=dict, description="Document count by status")


class ProjectWithStats(Project):
    """Project with statistics."""
    stats: ProjectStats = Field(..., description="Project statistics")


class ProjectSearchRequest(BaseModel):
    """Project search request."""
    query: str = Field(..., description="Search query")
    limit: int = Field(100, description="Number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class ProjectSearchResponse(BaseModel):
    """Project search response."""
    projects: List[Project] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of matching projects")
    query: str = Field(..., description="Search query used")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class ProjectBulkOperationRequest(BaseModel):
    """Bulk project operation request."""
    project_ids: List[str] = Field(..., description="List of project IDs to operate on")
    operation: str = Field(..., description="Operation to perform (delete, archive, etc.)")


class ProjectBulkOperationResponse(BaseModel):
    """Bulk project operation response."""
    success: bool = Field(..., description="Whether operation was successful")
    projects_processed: int = Field(..., description="Number of projects processed")
    message: str = Field(..., description="Response message")


class ProjectTemplate(BaseModel):
    """Project template for quick project creation."""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    default_settings: Dict[str, Any] = Field(default_factory=dict, description="Default project settings")
    is_system: bool = Field(False, description="Whether this is a system template")
    created_at: datetime = Field(..., description="Template creation timestamp")


class ProjectImportRequest(BaseModel):
    """Project import request."""
    source: str = Field(..., description="Import source")
    source_config: Dict[str, Any] = Field(..., description="Source configuration")
    template_id: Optional[str] = Field(None, description="Template ID to use")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Project settings")


class ProjectImportResponse(BaseModel):
    """Project import response."""
    success: bool = Field(..., description="Whether import was successful")
    project_id: Optional[str] = Field(None, description="Created project ID")
    message: str = Field(..., description="Response message")
    imported_data: Dict[str, Any] = Field(..., description="Imported data summary")
