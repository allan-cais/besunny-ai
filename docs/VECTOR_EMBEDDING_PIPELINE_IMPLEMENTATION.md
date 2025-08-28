# Vector Embedding Pipeline Implementation

## 🎯 **Overview**

The Vector Embedding Pipeline is the "second cog" in the BeSunny.ai content processing system, extending the Classification Agent by storing classified content in a Pinecone vector database for semantic search and retrieval.

## 🏗️ **Architecture Decision: Single Namespace with Metadata**

**Chosen Approach:** Single Pinecone namespace with `project_id` as metadata
- **Rationale:** Enables cross-project search while maintaining clean separation
- **Benefits:** Simpler management, better resource utilization, future flexibility
- **Implementation:** All vectors stored in one index with rich metadata filtering

## 🔄 **Complete Flow**

### **1. Automatic Classification + Embedding**
```
Content Arrives → Classification Agent → Vector Embedding → Pinecone Storage
     ↓                    ↓                    ↓              ↓
  Email/Drive/      AI Classification    Chunking +      Vector DB
  Transcript         (Confidence ≥0.5)    Embedding      with Metadata
```

### **2. Unclassified Content Handling**
```
Content Arrives → Classification Agent → No Embedding → Unclassified Dashboard
     ↓                    ↓                    ↓              ↓
  Email/Drive/      AI Classification    Skipped        Manual Assignment
  Transcript         (Confidence <0.5)   (No project)   Available
```

### **3. Manual Assignment + Embedding**
```
User Assigns → Document Update → Vector Embedding → Pinecone Storage
     ↓              ↓                    ↓              ↓
  Project ID      Database Update    Chunking +      Vector DB
  Selection       (project_id set)    Embedding      with Metadata
```

## 🧩 **Core Components**

### **VectorEmbeddingService** (`backend/app/services/ai/vector_embedding_service.py`)

#### **Key Features:**
- **Automatic Index Management:** Creates/connects to Pinecone index
- **Smart Chunking:** 1000-token chunks with 200-token overlap
- **Rich Metadata:** Comprehensive content and classification metadata
- **Error Handling:** Graceful fallbacks for embedding failures
- **Activity Logging:** Tracks all embedding operations

#### **Methods:**
```python
# Core embedding for classified content
async def embed_classified_content(content, classification_result, user_id)

# Manual assignment embedding
async def embed_manually_assigned_content(content, project_id, user_id)

# Vector similarity search
async def search_similar_content(query, user_id, project_id=None, limit=10)

# Statistics and monitoring
async def get_embedding_stats(user_id)
```

### **Classification Service Integration** (`backend/app/services/ai/classification_service.py`)

#### **Automatic Triggering:**
```python
# After successful classification, automatically trigger embedding
if processed_result.get('project_id') and not processed_result.get('unclassified', True):
    await self._update_document_project(content, processed_result['project_id'])
    
    # Send to vector embedding pipeline for classified content
    try:
        embedding_result = await self.vector_service.embed_classified_content(
            content=content,
            classification_result=processed_result,
            user_id=user_id
        )
        logger.info(f"Vector embedding completed: {embedding_result.get('chunks_created', 0)} chunks created")
    except Exception as e:
        logger.error(f"Vector embedding failed: {e}")
```

### **Documents API** (`backend/app/api/v1/documents.py`)

#### **Endpoints:**
- **`GET /documents/unclassified`** - Fetch unclassified documents
- **`POST /documents/assign-project`** - Manual project assignment
- **`POST /documents/search`** - Vector similarity search
- **`GET /documents/stats`** - Document and embedding statistics

#### **Manual Assignment Flow:**
```python
@router.post("/assign-project")
async def assign_document_to_project(
    request: ProjectAssignmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    background_tasks: BackgroundTasks
):
    # Update document with project_id
    # Trigger background vector embedding
    background_tasks.add_task(
        _embed_manually_assigned_document,
        document,
        request.project_id,
        current_user['id']
    )
```

## 📊 **Data Flow & Storage**

### **Content Chunking Strategy**
- **Chunk Size:** 1000 tokens (OpenAI recommendation)
- **Overlap:** 200 tokens (maintains context)
- **Tokenizer:** `tiktoken` with `cl100k_base` encoding
- **Smart Boundaries:** Respects natural text boundaries

### **Vector Metadata Structure**
```json
{
  "user_id": "uuid",
  "project_id": "uuid",
  "content_type": "email|drive_file|transcript",
  "source_id": "document_id",
  "chunk_index": 0,
  "total_chunks": 3,
  "author": "sender@example.com",
  "date": "2025-08-27T15:30:00Z",
  "subject": "Project Update",
  "confidence": 0.85,
  "matched_tags": ["project", "update"],
  "inferred_tags": ["deadline", "milestone"],
  "classification_notes": "Strong match to project metadata",
  "embedded_at": "2025-08-27T15:30:00Z"
}
```

### **Source-Specific Metadata**
```python
# Email metadata
if content.get('type') == 'email':
    metadata.update({
        'email_id': content.get('metadata', {}).get('email_id', ''),
        'inbound_address': content.get('metadata', {}).get('inbound_address', ''),
        'attachments': content.get('attachments', [])
    })

# Drive file metadata
elif content.get('type') == 'drive_file':
    metadata.update({
        'drive_file_id': content.get('metadata', {}).get('drive_file_id', ''),
        'drive_url': content.get('metadata', {}).get('drive_url', ''),
        'file_type': content.get('metadata', {}).get('file_type', ''),
        'file_size': content.get('metadata', {}).get('file_size', 0)
    })

# Transcript metadata
elif content.get('type') == 'transcript':
    metadata.update({
        'meeting_id': content.get('metadata', {}).get('meeting_id', ''),
        'meeting_url': content.get('metadata', {}).get('meeting_url', ''),
        'duration_minutes': content.get('metadata', {}).get('duration_minutes', 0),
        'attendees': content.get('metadata', {}).get('attendees', [])
    })
```

## 🔍 **Search & Retrieval**

### **Vector Search Capabilities**
```python
async def search_similar_content(query, user_id, project_id=None, limit=10):
    # Generate query embedding
    query_embedding = await self.openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        encoding_format="float"
    )
    
    # Build filters
    filter_dict = {'user_id': user_id}
    if project_id:
        filter_dict['project_id'] = project_id
    
    # Search Pinecone with filters
    search_results = self.index.query(
        vector=query_embedding.data[0].embedding,
        filter=filter_dict,
        top_k=limit,
        include_metadata=True
    )
```

### **Search Features**
- **User Isolation:** All searches filtered by `user_id`
- **Project Filtering:** Optional `project_id` filtering
- **Semantic Similarity:** Cosine similarity scoring
- **Rich Results:** Full metadata with chunk information
- **Configurable Limits:** Adjustable result counts

## 🎨 **Frontend Integration**

### **UnclassifiedDocuments Component** (`frontend/src/components/dashboard/UnclassifiedDocuments.tsx`)

#### **Features:**
- **Real-time Display:** Shows all unclassified documents
- **Source Visualization:** Icons and colors for different content types
- **Project Selection:** Dropdown with project names and descriptions
- **Manual Assignment:** One-click project assignment
- **Auto-refresh:** Removes assigned documents automatically

#### **UI Elements:**
- **Source Badges:** Color-coded by content type
- **Project Selector:** Dropdown with project overviews
- **Assignment Button:** Triggers embedding pipeline
- **Loading States:** Visual feedback during operations
- **Empty State:** Helpful message when no unclassified content

## 🚀 **Deployment & Configuration**

### **Environment Variables**
```bash
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=besunny_ai_vectors
PINECONE_ENVIRONMENT=us-east-1

# OpenAI Configuration (for embeddings)
OPENAI_API_KEY=your_openai_api_key
```

### **Dependencies**
```txt
# Vector database
pinecone>=2.2.0

# Tokenization
tiktoken>=0.5.0

# OpenAI embeddings
openai>=1.0.0
```

### **Pinecone Index Configuration**
- **Dimension:** 1536 (OpenAI text-embedding-3-small)
- **Metric:** Cosine similarity
- **Spec:** Serverless (AWS, us-east-1)
- **Auto-creation:** Index created automatically if not exists

## 📈 **Monitoring & Analytics**

### **Embedding Activity Logging**
```python
async def _log_embedding_activity(content, classification_result, user_id, chunks_created):
    log_data = {
        'agent_name': 'vector_embedding',
        'input_id': content.get('source_id', ''),
        'input_type': content.get('type', 'unknown'),
        'output': {
            'chunks_created': chunks_created,
            'project_id': classification_result.get('project_id', ''),
            'confidence': classification_result.get('confidence', 0.0),
            'content_type': content.get('type', 'unknown')
        },
        'confidence': classification_result.get('confidence', 0.0),
        'notes': f'Embedded {chunks_created} chunks into Pinecone',
        'created_at': datetime.now().isoformat()
    }
    
    self.supabase.table('agent_logs').insert(log_data).execute()
```

### **Statistics & Metrics**
- **Total Vectors:** Index-wide vector count
- **User Vectors:** Per-user vector counts
- **Chunk Creation:** Success/failure rates
- **Processing Time:** Embedding performance metrics
- **Error Tracking:** Failed embedding reasons

## 🔮 **Future Enhancements**

### **Planned Features**
1. **Re-vectorization Pipeline:** Update embeddings when content changes
2. **Advanced Filtering:** Date ranges, content types, confidence thresholds
3. **Batch Operations:** Bulk embedding for large datasets
4. **Performance Optimization:** Async batch processing
5. **Analytics Dashboard:** Embedding quality metrics

### **RAG Agent Integration**
- **Query Processing:** Natural language to vector search
- **Context Assembly:** Multi-chunk context building
- **Response Generation:** AI-powered answer synthesis
- **Source Attribution:** Clear document references

## 🧪 **Testing & Validation**

### **Test Script** (`testing/test_vector_embedding_pipeline.py`)

#### **Test Coverage:**
1. **Pinecone Connection:** Index creation and connection
2. **Content Chunking:** Token-based text segmentation
3. **Classification Integration:** Automatic embedding triggers
4. **Unclassified Handling:** Proper skipping of unclassified content
5. **Manual Assignment:** User-initiated embedding
6. **Vector Search:** Similarity search functionality

### **Validation Steps**
```bash
# Run the test suite
cd testing
python test_vector_embedding_pipeline.py

# Expected output:
# ✅ Pinecone index connected successfully
# ✅ Content chunking successful
# ✅ Vector embedding successful
# ✅ Unclassified content correctly skipped
# ✅ Manual assignment embedding successful
# ✅ Vector search successful
```

## 🎯 **Key Benefits**

### **For Users**
- **Seamless Experience:** Automatic classification and embedding
- **Manual Control:** Easy project assignment for unclassified content
- **Rich Search:** Semantic search across all project content
- **Context Preservation:** Maintains document relationships

### **For Developers**
- **Clean Architecture:** Separation of concerns
- **Scalable Design:** Handles large content volumes
- **Error Resilience:** Graceful failure handling
- **Monitoring Ready:** Comprehensive logging and metrics

### **For System**
- **Performance:** Efficient vector storage and retrieval
- **Flexibility:** Easy to extend and modify
- **Reliability:** Robust error handling and recovery
- **Scalability:** Pinecone serverless architecture

## 🔧 **Troubleshooting**

### **Common Issues**
1. **Pinecone Connection:** Check API key and environment
2. **OpenAI Embeddings:** Verify API key and rate limits
3. **Chunking Errors:** Validate content text format
4. **Metadata Issues:** Check database schema compatibility

### **Debug Commands**
```python
# Check Pinecone index status
stats = await vector_service.get_embedding_stats(user_id)
print(f"Index stats: {stats}")

# Test chunking manually
chunks = vector_service._create_content_chunks(test_content)
print(f"Chunks created: {len(chunks)}")

# Verify embedding results
result = await vector_service.embed_classified_content(content, classification, user_id)
print(f"Embedding result: {result}")
```

---

**This implementation provides a robust, scalable, and user-friendly vector embedding pipeline that seamlessly integrates with the classification system while enabling powerful semantic search capabilities for the upcoming RAG agent.**
