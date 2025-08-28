# AI Services Module

This module provides comprehensive AI-powered services for the BeSunny.ai Python backend, including document classification, vector embeddings, and meeting intelligence.

## Overview

The AI Services module consists of four core services:

1. **AI Service** - Core OpenAI integration and AI processing capabilities
2. **Embedding Service** - Vector embeddings and Pinecone integration
3. **Classification Service** - Document classification using AI and embeddings
4. **Meeting Intelligence Service** - Meeting transcript analysis and attendee bot integration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Services Module                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   AI        │  │ Embedding   │  │ Meeting     │        │
│  │ Service     │  │ Service     │  │ Intelligence│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          │                                │
│  ┌─────────────┐         │                                │
│  │Classification│◄────────┘                                │
│  │ Service     │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## Services

### 1. AI Service (`ai_service.py`)

The core AI service that provides OpenAI integration and AI processing capabilities.

**Features:**
- Document classification using GPT models
- Content analysis and summarization
- Entity extraction and sentiment analysis
- Rate limiting and cost estimation
- Configurable model selection

**Key Methods:**
```python
async def classify_document(content: str, project_context: str = None) -> AIProcessingResult
async def analyze_document_content(content: str, analysis_type: str = "comprehensive") -> AIProcessingResult
async def generate_document_summary(content: str, max_length: int = 200) -> AIProcessingResult
async def extract_entities(content: str, entity_types: List[str] = None) -> AIProcessingResult
```

**Usage Example:**
```python
from app.services.ai.ai_service import AIService

ai_service = AIService()
result = await ai_service.classify_document("This is a test document")
if result.success:
    print(f"Document type: {result.result['document_type']}")
    print(f"Confidence: {result.result['confidence_score']}")
```

### 2. Embedding Service (`embedding_service.py`)

Service for generating and managing vector embeddings using sentence-transformers and Pinecone.

**Features:**
- Vector embedding generation using sentence-transformers
- Pinecone vector database integration
- Document chunking and storage
- Similarity search and retrieval
- Automatic index management

**Key Methods:**
```python
async def generate_embeddings(texts: Union[str, List[str]]) -> EmbeddingResult
async def store_document_chunks(chunks: List[DocumentChunk]) -> bool
async def search_similar_documents(query: str, project_id: str = None) -> VectorSearchResult
async def chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]
```

**Usage Example:**
```python
from app.services.ai.embedding_service import EmbeddingService

embedding_service = EmbeddingService()
await embedding_service.initialize()

# Generate embeddings
result = await embedding_service.generate_embeddings("Sample text")
if result.success:
    embedding_vector = result.embeddings[0]
    
# Search similar documents
search_result = await embedding_service.search_similar_documents("query text")
```

### 3. Classification Service (`classification_service.py`)

Service that combines AI classification with vector embeddings for comprehensive document processing.

**Features:**
- AI-powered document classification
- Vector embedding generation and storage
- Batch processing capabilities
- Reclassification support
- Similar document search

**Key Methods:**
```python
async def classify_document(request: ClassificationRequest) -> ClassificationResult
async def classify_documents_batch(request: BatchClassificationRequest) -> BatchClassificationResult
async def reclassify_document(document_id: str, content: str) -> ClassificationResult
async def get_similar_documents(query: str, project_id: str = None) -> List[Dict[str, Any]]
```

**Usage Example:**
```python
from app.services.ai.classification_service import ClassificationService, ClassificationRequest

classification_service = ClassificationService()
await classification_service.initialize()

request = ClassificationRequest(
    document_id="doc-123",
    content="Document content here",
    project_id="project-456"
)

result = await classification_service.classify_document(request)
print(f"Classified as: {result.document_type}")
print(f"Confidence: {result.confidence_score}")
```

### 4. Meeting Intelligence Service (`meeting_intelligence_service.py`)

Service for AI-powered analysis of meeting transcripts and attendee bot integration.

**Features:**
- Meeting transcript analysis
- Action item extraction
- Sentiment analysis
- Participant analysis
- Meeting summarization
- Vector search in transcripts

**Key Methods:**
```python
async def analyze_meeting_transcript(transcript: MeetingTranscript) -> MeetingIntelligenceResult
async def extract_action_items_from_transcript(transcript: MeetingTranscript) -> List[ActionItem]
async def generate_meeting_summary(transcript: MeetingTranscript) -> str
async def search_meeting_content(query: str, project_id: str = None) -> List[Dict[str, Any]]
```

**Usage Example:**
```python
from app.services.ai.meeting_intelligence_service import MeetingIntelligenceService, MeetingTranscript

meeting_service = MeetingIntelligenceService()
await meeting_service.initialize()

# Analyze transcript
result = await meeting_service.analyze_meeting_transcript(transcript)
print(f"Meeting summary: {result.summary.executive_summary}")
print(f"Action items: {len(result.summary.action_items)}")

# Extract action items
action_items = await meeting_service.extract_action_items_from_transcript(transcript)
for item in action_items:
    print(f"Action: {item.text} - Assignee: {item.assignee}")
```

## Configuration

The AI services require the following environment variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000

# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=besunny-documents

# Service Configuration
ENABLE_AI_PROCESSING=true
ENABLE_VECTOR_SEARCH=true
AI_PROCESSING_BATCH_SIZE=100
```

## API Endpoints

The AI services are exposed through the following API endpoints:

### Classification API (`/api/v1/classification`)
- `POST /documents/classify` - Classify a single document
- `POST /documents/classify/batch` - Batch document classification
- `POST /documents/{id}/reclassify` - Reclassify an existing document
- `GET /documents/similar` - Find similar documents
- `GET /analytics` - Get classification analytics

### AI API (`/api/v1/ai`)
- `POST /documents/analyze` - Analyze document content
- `POST /documents/summarize` - Generate document summary
- `POST /documents/entities` - Extract named entities
- `POST /documents/classify` - AI document classification
- `POST /documents/analyze/batch` - Batch document analysis
- `POST /documents/enhance` - Enhance document content

### Embeddings API (`/api/v1/embeddings`)
- `POST /generate` - Generate vector embeddings
- `POST /store` - Store document chunks
- `GET /search` - Search similar documents
- `GET /similar-chunks` - Find similar chunks
- `DELETE /documents/{id}` - Delete document vectors
- `GET /stats` - Get index statistics

### Meeting Intelligence API (`/api/v1/meeting-intelligence`)
- `POST /transcripts/analyze` - Analyze meeting transcript
- `POST /transcripts/action-items` - Extract action items
- `POST /transcripts/summary` - Generate meeting summary
- `POST /transcripts/sentiment` - Analyze meeting sentiment
- `GET /search` - Search meeting content
- `POST /transcripts/process-batch` - Batch transcript processing

## Data Models

### Core Models

- **AIProcessingResult** - Result of AI processing operations
- **DocumentChunk** - Document chunk with vector embeddings
- **ClassificationRequest/Result** - Document classification data
- **MeetingTranscript** - Meeting transcript structure
- **ActionItem** - Extracted action item from meetings

### Enhanced Document Schema

The document schema has been enhanced to support AI processing:

```python
class Document(BaseModel):
    # ... existing fields ...
    
    # AI Processing Fields
    ai_processed: bool = False
    ai_processing_result: Optional[AIProcessingResult] = None
    last_ai_processed: Optional[datetime] = None
    
    # Vector Search Fields
    vector_search_enabled: bool = True
    similarity_score: Optional[float] = None
    
    # Enhanced Fields
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    expiration_date: Optional[datetime] = None
```

## Performance Considerations

### Rate Limiting
- AI service uses semaphores to limit concurrent OpenAI API calls
- Default limit: 5 concurrent requests
- Configurable through service initialization

### Caching
- Vector embeddings are stored in Pinecone for fast retrieval
- Document chunks are cached to avoid reprocessing
- Search results can be cached for repeated queries

### Batch Processing
- Support for batch document processing
- Concurrent processing with configurable limits
- Progress tracking and error handling

## Error Handling

All services implement comprehensive error handling:

- **API Failures** - Graceful fallback and retry logic
- **Invalid Input** - Input validation and error messages
- **Service Unavailable** - Health checks and status reporting
- **Rate Limits** - Automatic throttling and queue management

## Testing

The AI services include comprehensive test coverage:

```bash
# Run all AI service tests
pytest app/tests/test_ai_services.py -v

# Run specific service tests
pytest app/tests/test_ai_services.py::TestAIService -v
pytest app/tests/test_ai_services.py::TestEmbeddingService -v
pytest app/tests/test_ai_services.py::TestClassificationService -v
pytest app/tests/test_ai_services.py::TestMeetingIntelligenceService -v
```

## Monitoring and Health Checks

Each service provides health check endpoints:

- **Classification Health** - `/api/v1/classification/health`
- **AI Service Health** - `/api/v1/ai/health`
- **Embeddings Health** - `/api/v1/embeddings/health`
- **Meeting Intelligence Health** - `/api/v1/meeting-intelligence/health`

## Future Enhancements

### Planned Features
- **Custom Model Training** - Domain-specific classification models
- **Advanced Analytics** - Processing performance metrics
- **Model Versioning** - A/B testing and model comparison
- **Real-time Processing** - WebSocket-based live processing
- **Multi-language Support** - Enhanced language detection and processing

### Integration Opportunities
- **N8N Workflow Migration** - Convert existing N8N classification workflows
- **Advanced ML Pipeline** - Custom model training and deployment
- **Business Intelligence** - Advanced analytics and reporting
- **Workflow Automation** - Trigger-based AI processing

## Contributing

When contributing to the AI services:

1. **Follow the existing patterns** - Maintain consistency with current service architecture
2. **Add comprehensive tests** - Ensure new features are properly tested
3. **Update documentation** - Keep this README and API docs current
4. **Consider performance** - Optimize for production use cases
5. **Handle errors gracefully** - Implement proper error handling and logging

## Support

For questions or issues with the AI services:

1. Check the test files for usage examples
2. Review the API endpoint documentation
3. Check service health endpoints for status
4. Review logs for detailed error information
5. Consult the main project documentation

---

*This module represents Phase 2 of the Python Backend Integration Roadmap, providing advanced AI capabilities for the BeSunny.ai ecosystem.*
