"""
Document schemas for BeSunny.ai Python backend.
Defines data models for document management operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    ACTIVE = "active"
    UPDATED = "updated"
    DELETED = "deleted"
    ERROR = "error"
    PROCESSING = "processing"
    CLASSIFIED = "classified"


class DocumentType(str, Enum):
    """Document type enumeration."""
    EMAIL = "email"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    IMAGE = "image"
    FOLDER = "folder"
    MEETING_TRANSCRIPT = "meeting_transcript"


class ClassificationSource(str, Enum):
    """Classification source enumeration."""
    AI = "ai"
    AUTO = "auto"
    SYSTEM = "system"
    MANUAL = "manual"
    USER = "user"


class DocumentMetadata(BaseModel):
    """Document metadata information."""
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")
    language: Optional[str] = Field(None, description="Document language")
    page_count: Optional[int] = Field(None, description="Number of pages")
    extracted_text: Optional[str] = Field(None, description="Extracted text content")
    confidence_score: Optional[float] = Field(None, description="Classification confidence score")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    summary: Optional[str] = Field(None, description="Document summary")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Named entities")
    
    # AI Processing Results
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI analysis results")
    sentiment: Optional[str] = Field(None, description="Document sentiment")
    topics: Optional[List[str]] = Field(None, description="Identified topics")
    complexity: Optional[str] = Field(None, description="Content complexity level")
    
    # Vector Embedding Information
    vector_dimensions: Optional[int] = Field(None, description="Vector embedding dimensions")
    embedding_model: Optional[str] = Field(None, description="Model used for embeddings")
    chunks_count: Optional[int] = Field(None, description="Number of text chunks created")
    
    # Processing Information
    processing_time_ms: Optional[int] = Field(None, description="AI processing time in milliseconds")
    model_used: Optional[str] = Field(None, description="AI model used for processing")
    processing_cost: Optional[float] = Field(None, description="Estimated processing cost")


class DocumentChunk(BaseModel):
    """Document chunk for vector storage and processing."""
    id: str = Field(..., description="Chunk ID")
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., description="Chunk position in document")
    text: str = Field(..., description="Chunk text content")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    created_at: Optional[datetime] = Field(None, description="Chunk creation timestamp")


class AIProcessingResult(BaseModel):
    """AI processing result for a document."""
    success: bool = Field(..., description="Whether processing was successful")
    document_type: DocumentType = Field(..., description="Classified document type")
    confidence_score: float = Field(..., description="Classification confidence")
    categories: List[str] = Field(..., description="Document categories")
    keywords: List[str] = Field(..., description="Extracted keywords")
    summary: Optional[str] = Field(None, description="Generated summary")
    entities: Optional[Dict[str, Any]] = Field(None, description="Extracted entities")
    sentiment: Optional[str] = Field(None, description="Document sentiment")
    topics: Optional[List[str]] = Field(None, description="Identified topics")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(..., description="AI model used")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class Document(BaseModel):
    """Document model."""
    id: str = Field(..., description="Document ID")
    title: Optional[str] = Field(None, description="Document title")
    summary: Optional[str] = Field(None, description="Document summary")
    author: Optional[str] = Field(None, description="Document author")
    file_id: Optional[str] = Field(None, description="Google Drive file ID")
    file_size: Optional[str] = Field(None, description="File size")
    source: Optional[str] = Field(None, description="Document source")
    source_id: Optional[str] = Field(None, description="Source ID")
    type: DocumentType = Field(DocumentType.DOCUMENT, description="Document type")
    status: DocumentStatus = Field(DocumentStatus.ACTIVE, description="Document status")
    classification_source: ClassificationSource = Field(ClassificationSource.MANUAL, description="Classification source")
    watch_active: bool = Field(False, description="Whether file watch is active")
    transcript_duration_seconds: Optional[int] = Field(None, description="Transcript duration in seconds")
    transcript_metadata: Optional[Dict[str, Any]] = Field(None, description="Transcript metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="User ID who created the document")
    received_at: Optional[datetime] = Field(None, description="When document was received")
    last_synced_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    knowledge_space_id: Optional[str] = Field(None, description="Associated knowledge space ID")
    meeting_id: Optional[str] = Field(None, description="Associated meeting ID")
    metadata: Optional[DocumentMetadata] = Field(None, description="Document metadata")
    
    # AI Processing Fields
    ai_processed: bool = Field(False, description="Whether document has been processed by AI")
    ai_processing_result: Optional[AIProcessingResult] = Field(None, description="AI processing results")
    last_ai_processed: Optional[datetime] = Field(None, description="Last AI processing timestamp")
    
    # Vector Search Fields
    vector_search_enabled: bool = Field(True, description="Whether document is available for vector search")
    similarity_score: Optional[float] = Field(None, description="Similarity score from search")
    
    # Enhanced Fields
    tags: Optional[List[str]] = Field(None, description="Document tags")
    priority: Optional[str] = Field(None, description="Document priority")
    expiration_date: Optional[datetime] = Field(None, description="Document expiration date")


class DocumentCreate(BaseModel):
    """Document creation request."""
    title: Optional[str] = Field(None, description="Document title")
    summary: Optional[str] = Field(None, description="Document summary")
    author: Optional[str] = Field(None, description="Document author")
    file_id: Optional[str] = Field(None, description="Google Drive file ID")
    file_size: Optional[str] = Field(None, description="File size")
    source: Optional[str] = Field(None, description="Document source")
    source_id: Optional[str] = Field(None, description="Source ID")
    type: DocumentType = Field(DocumentType.DOCUMENT, description="Document type")
    status: DocumentStatus = Field(DocumentStatus.ACTIVE, description="Document status")
    classification_source: ClassificationSource = Field(ClassificationSource.MANUAL, description="Classification source")
    watch_active: bool = Field(False, description="Whether file watch is active")
    transcript_duration_seconds: Optional[int] = Field(None, description="Transcript duration in seconds")
    transcript_metadata: Optional[Dict[str, Any]] = Field(None, description="Transcript metadata")
    received_at: Optional[datetime] = Field(None, description="When document was received")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    knowledge_space_id: Optional[str] = Field(None, description="Associated knowledge space ID")
    meeting_id: Optional[str] = Field(None, description="Associated meeting ID")
    metadata: Optional[DocumentMetadata] = Field(None, description="Document metadata")
    
    # AI Processing Options
    enable_ai_processing: bool = Field(True, description="Whether to enable AI processing")
    ai_processing_type: Optional[str] = Field("comprehensive", description="Type of AI processing to perform")
    
    # Vector Search Options
    enable_vector_search: bool = Field(True, description="Whether to enable vector search")
    chunk_size: Optional[int] = Field(1000, description="Text chunk size for embeddings")
    chunk_overlap: Optional[int] = Field(200, description="Overlap between chunks")


class DocumentUpdate(BaseModel):
    """Document update request."""
    title: Optional[str] = Field(None, description="Document title")
    summary: Optional[str] = Field(None, description="Document summary")
    author: Optional[str] = Field(None, description="Document author")
    file_id: Optional[str] = Field(None, description="Google Drive file ID")
    file_size: Optional[str] = Field(None, description="File size")
    source: Optional[str] = Field(None, description="Document source")
    source_id: Optional[str] = Field(None, description="Source ID")
    type: Optional[DocumentType] = Field(None, description="Document type")
    status: Optional[DocumentStatus] = Field(None, description="Document status")
    classification_source: Optional[ClassificationSource] = Field(None, description="Classification source")
    watch_active: Optional[bool] = Field(None, description="Whether file watch is active")
    transcript_duration_seconds: Optional[int] = Field(None, description="Transcript duration in seconds")
    transcript_metadata: Optional[Dict[str, Any]] = Field(None, description="Transcript metadata")
    received_at: Optional[datetime] = Field(None, description="When document was received")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    knowledge_space_id: Optional[str] = Field(None, description="Associated knowledge space ID")
    meeting_id: Optional[str] = Field(None, description="Associated meeting ID")
    metadata: Optional[DocumentMetadata] = Field(None, description="Document metadata")
    
    # AI Processing Updates
    ai_processing_result: Optional[AIProcessingResult] = Field(None, description="Updated AI processing results")
    last_ai_processed: Optional[datetime] = Field(None, description="Last AI processing timestamp")
    
    # Enhanced Fields
    tags: Optional[List[str]] = Field(None, description="Document tags")
    priority: Optional[str] = Field(None, description="Document priority")
    expiration_date: Optional[datetime] = Field(None, description="Document expiration date")


class DocumentListResponse(BaseModel):
    """Response containing a list of documents."""
    documents: List[Document] = Field(..., description="List of documents")
    total_count: int = Field(..., description="Total number of documents")
    limit: int = Field(..., description="Number of documents returned")
    offset: int = Field(..., description="Number of documents skipped")


class DocumentSearchRequest(BaseModel):
    """Document search request."""
    query: str = Field(..., description="Search query")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    status: Optional[DocumentStatus] = Field(None, description="Filter by status")
    limit: int = Field(100, description="Number of results to return")
    offset: int = Field(0, description="Number of results to skip")
    
    # AI Processing Filters
    ai_processed: Optional[bool] = Field(None, description="Filter by AI processing status")
    classification_source: Optional[ClassificationSource] = Field(None, description="Filter by classification source")
    
    # Vector Search Options
    use_vector_search: bool = Field(True, description="Whether to use vector similarity search")
    similarity_threshold: float = Field(0.7, description="Minimum similarity score for vector search")
    
    # Enhanced Filters
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    priority: Optional[str] = Field(None, description="Filter by priority")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range filter")


class DocumentSearchResponse(BaseModel):
    """Document search response."""
    documents: List[Document] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of matching documents")
    query: str = Field(..., description="Search query used")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")
    
    # Search Metadata
    search_type: str = Field(..., description="Type of search performed")
    search_time_ms: Optional[int] = Field(None, description="Search execution time")
    vector_search_used: bool = Field(False, description="Whether vector search was used")
    similarity_scores: Optional[List[float]] = Field(None, description="Similarity scores for results")


class DocumentBatchUpdateRequest(BaseModel):
    """Batch document update request."""
    document_ids: List[str] = Field(..., description="List of document IDs to update")
    updates: DocumentUpdate = Field(..., description="Updates to apply to all documents")
    
    # Batch Processing Options
    enable_ai_reprocessing: bool = Field(False, description="Whether to reprocess documents with AI")
    update_vector_embeddings: bool = Field(False, description="Whether to update vector embeddings")


class DocumentBatchUpdateResponse(BaseModel):
    """Batch document update response."""
    success: bool = Field(..., description="Whether batch update was successful")
    documents_updated: int = Field(..., description="Number of documents updated")
    message: str = Field(..., description="Response message")
    
    # Processing Results
    ai_reprocessed: Optional[int] = Field(None, description="Number of documents AI reprocessed")
    embeddings_updated: Optional[int] = Field(None, description="Number of vector embeddings updated")


class DocumentImportRequest(BaseModel):
    """Document import request."""
    source: str = Field(..., description="Import source")
    source_config: Dict[str, Any] = Field(..., description="Source configuration")
    project_id: Optional[str] = Field(None, description="Target project ID")
    metadata: Optional[DocumentMetadata] = Field(None, description="Document metadata")
    
    # Import Options
    enable_ai_processing: bool = Field(True, description="Whether to enable AI processing on import")
    enable_vector_search: bool = Field(True, description="Whether to enable vector search on import")
    chunk_size: Optional[int] = Field(1000, description="Text chunk size for embeddings")


class DocumentImportResponse(BaseModel):
    """Document import response."""
    success: bool = Field(..., description="Whether import was successful")
    documents_imported: int = Field(..., description="Number of documents imported")
    message: str = Field(..., description="Response message")
    imported_documents: List[Document] = Field(..., description="List of imported documents")
    
    # Processing Results
    ai_processed: Optional[int] = Field(None, description="Number of documents AI processed")
    embeddings_created: Optional[int] = Field(None, description="Number of vector embeddings created")


class DocumentChunkResponse(BaseModel):
    """Response containing document chunks."""
    document_id: str = Field(..., description="Parent document ID")
    chunks: List[DocumentChunk] = Field(..., description="List of document chunks")
    total_chunks: int = Field(..., description="Total number of chunks")
    chunk_size: int = Field(..., description="Size of each chunk")
    overlap: int = Field(..., description="Overlap between chunks")


class VectorSearchRequest(BaseModel):
    """Vector similarity search request."""
    query: str = Field(..., description="Search query")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    top_k: int = Field(10, description="Number of top results to return")
    similarity_threshold: float = Field(0.7, description="Minimum similarity score")
    
    # Advanced Search Options
    use_hybrid_search: bool = Field(True, description="Whether to combine vector and keyword search")
    include_metadata: bool = Field(True, description="Whether to include chunk metadata in results")
    filter_by_date: Optional[Dict[str, datetime]] = Field(None, description="Date range filter")


class VectorSearchResponse(BaseModel):
    """Vector similarity search response."""
    query: str = Field(..., description="Search query used")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_time_ms: int = Field(..., description="Search execution time")
    
    # Search Metadata
    vector_search_used: bool = Field(True, description="Whether vector search was used")
    similarity_scores: List[float] = Field(..., description="Similarity scores for results")
    query_embedding: Optional[List[float]] = Field(None, description="Query vector embedding")
