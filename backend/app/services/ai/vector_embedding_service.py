"""
Vector Embedding Service
Handles chunking, embedding, and storing content in Pinecone vector database.
Integrates with classification results to store project-specific metadata.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import tiktoken
import openai
from pinecone import Pinecone, ServerlessSpec

from ...core.supabase_config import get_supabase_service_client
from ...core.config import get_settings
from .semantic_chunking_service import SemanticChunkingService
from .hierarchical_chunking_service import HierarchicalChunkingService

logger = logging.getLogger(__name__)

class VectorEmbeddingService:
    """Service for embedding content into Pinecone vector database."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_service_client()
        
        # Initialize OpenAI client for embeddings
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.embedding_api_key or self.settings.openai_api_key,
            base_url=self.settings.embedding_base_url
        )
        
        # Initialize Pinecone client
        self.pinecone = Pinecone(api_key=self.settings.pinecone_api_key)
        self.index_name = self.settings.pinecone_vector_store
        
        # Get or create Pinecone index
        self.index = self._get_or_create_index()
        
        # Tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize advanced chunking services
        self.semantic_chunker = SemanticChunkingService()
        self.hierarchical_chunker = HierarchicalChunkingService()
        
        # Use config values for chunking parameters
        self.max_chunk_tokens = self.settings.max_chunk_tokens
        self.min_chunk_tokens = self.settings.min_chunk_tokens
        self.chunk_overlap = self.settings.chunk_overlap
        self.max_chunk_characters = 2000  # Character limit as fallback
    
    def _get_or_create_index(self):
        """Get existing index or create new one if it doesn't exist."""
        try:
            # Check if index exists
            if self.index_name not in self.pinecone.list_indexes().names():
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                
                # Create index with serverless spec
                self.pinecone.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding model dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
                # Wait for index to be ready
                while not self.pinecone.describe_index(self.index_name).status['ready']:
                    import time
                    time.sleep(1)
                
                logger.info(f"Pinecone index {self.index_name} created successfully")
            else:
                logger.info(f"Using existing Pinecone index: {self.index_name}")
            
            return self.pinecone.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Error setting up Pinecone index: {e}")
            raise
    
    async def embed_classified_content(
        self,
        content: Dict[str, Any],
        classification_result: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Embed classified content into Pinecone vector database.
        
        Args:
            content: The content to embed (email, Drive file, transcript)
            classification_result: Result from classification service
            user_id: ID of the user who owns the content
            
        Returns:
            Embedding result with metadata
        """
        try:
            # Skip embedding if content is unclassified
            if classification_result.get('unclassified', True):
                logger.info(f"Skipping embedding for unclassified content: {content.get('source_id', 'unknown')}")
                return {
                    'embedded': False,
                    'reason': 'Content not classified to a project',
                    'chunks_created': 0
                }
            
            project_id = classification_result.get('project_id')
            if not project_id:
                logger.warning(f"No project_id found in classification result for content: {content.get('source_id', 'unknown')}")
                return {
                    'embedded': False,
                    'reason': 'No project_id in classification result',
                    'chunks_created': 0
                }
            
            # Create content chunks
            chunks = await self._create_content_chunks(content)
            logger.info(f"Created {len(chunks)} chunks for content: {content.get('source_id', 'unknown')}")
            
            # Generate embeddings for each chunk
            embeddings = []
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding_response = await self.openai_client.embeddings.create(
                        model=self.settings.embedding_model_choice,
                        input=chunk['text'],
                        encoding_format="float"
                    )
                    
                    embedding_vector = embedding_response.data[0].embedding
                    
                    # Create metadata for the chunk
                    metadata = {
                        'user_id': user_id,
                        'project_id': project_id,
                        'content_type': content.get('type', 'unknown'),
                        'source_id': content.get('source_id', ''),
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'author': content.get('author', ''),
                        'date': content.get('date', ''),
                        'subject': content.get('subject', ''),
                        'chunk_text': chunks[i]['text'],  # Add the actual chunk text content
                        'confidence': classification_result.get('confidence', 0.0),
                        'matched_tags': classification_result.get('document', {}).get('matched_tags', []),
                        'inferred_tags': classification_result.get('document', {}).get('inferred_tags', []),
                        'classification_notes': classification_result.get('document', {}).get('classification_notes', ''),
                        'embedded_at': datetime.now().isoformat()
                    }
                    
                    # Add source-specific metadata
                    if content.get('type') == 'email':
                        metadata.update({
                            'email_id': content.get('metadata', {}).get('email_id', ''),
                            'inbound_address': content.get('metadata', {}).get('inbound_address', ''),
                            'attachments': content.get('attachments', [])
                        })
                    elif content.get('type') == 'drive_file':
                        metadata.update({
                            'drive_file_id': content.get('metadata', {}).get('drive_file_id', ''),
                            'drive_url': content.get('metadata', {}).get('drive_url', ''),
                            'file_type': content.get('metadata', {}).get('file_type', ''),
                            'file_size': content.get('metadata', {}).get('file_size', 0)
                        })
                    elif content.get('type') == 'transcript':
                        metadata.update({
                            'meeting_id': content.get('metadata', {}).get('meeting_id', ''),
                            'meeting_url': content.get('metadata', {}).get('meeting_url', ''),
                            'duration_minutes': content.get('metadata', {}).get('duration_minutes', 0),
                            'attendees': content.get('metadata', {}).get('attendees', [])
                        })
                    
                    embeddings.append({
                        'id': f"{content.get('source_id', '')}_chunk_{i}_{uuid.uuid4().hex[:8]}",
                        'values': embedding_vector,
                        'metadata': metadata
                    })
                    
                except Exception as e:
                    logger.error(f"Error generating embedding for chunk {i}: {e}")
                    continue
            
            if not embeddings:
                logger.error("No embeddings generated for any chunks")
                return {
                    'embedded': False,
                    'reason': 'Failed to generate embeddings for chunks',
                    'chunks_created': 0
                }
            
            # Store embeddings in Pinecone
            self.index.upsert(vectors=embeddings)
            logger.info(f"Successfully stored {len(embeddings)} embeddings in Pinecone")
            
            # Debug: Log what content was embedded
            for i, emb in enumerate(embeddings):
                chunk_text = emb['metadata'].get('chunk_text', '')
                print(f"=== EMBEDDED CHUNK {i+1}/{len(embeddings)} ===")
                print(f"Length: {len(chunk_text)}")
                print(f"Preview: {chunk_text[:200]}...")
                print(f"Full content: {chunk_text}")
                print("=" * 50)
            
            # Log embedding activity
            await self._log_embedding_activity(content, classification_result, user_id, len(embeddings))
            
            return {
                'embedded': True,
                'chunks_created': len(embeddings),
                'project_id': project_id,
                'confidence': classification_result.get('confidence', 0.0),
                'embedding_ids': [emb['id'] for emb in embeddings]
            }
            
        except Exception as e:
            logger.error(f"Error in content embedding: {e}")
            return {
                'embedded': False,
                'reason': f'Embedding error: {str(e)}',
                'chunks_created': 0
            }
    
    async def delete_document_vectors(self, document_id: str, user_id: str) -> bool:
        """
        Delete all vectors associated with a document from Pinecone.
        
        Args:
            document_id: The document ID to delete vectors for
            user_id: The user ID for security
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Deleting vectors for document {document_id}")
            
            # Query Pinecone to find all vectors with this document_id
            query_response = self.index.query(
                vector=[0] * 1536,  # Dummy vector for querying by metadata
                top_k=10000,  # Large number to get all matches
                include_metadata=True,
                filter={
                    "document_id": document_id,
                    "user_id": user_id
                }
            )
            
            if not query_response.matches:
                logger.info(f"No vectors found for document {document_id}")
                return True
            
            # Extract vector IDs to delete
            vector_ids = [match.id for match in query_response.matches]
            logger.info(f"Found {len(vector_ids)} vectors to delete for document {document_id}")
            
            # Delete vectors from Pinecone
            if vector_ids:
                self.index.delete(ids=vector_ids)
                logger.info(f"Successfully deleted {len(vector_ids)} vectors for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document vectors: {e}")
            return False
    
    async def _create_content_chunks(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create optimized text chunks from content for embedding."""
        try:
            # Get the best available content
            content_text = self._extract_best_content(content)
            
            if not content_text:
                logger.warning("No content found for chunking - available fields: %s", list(content.keys()))
                return []
            
            logger.info(f"Chunking content - Type: {content.get('type', 'unknown')}, Length: {len(content_text)} chars")
            
            # Clean and preprocess content
            cleaned_text = self._preprocess_content(content_text)
            
            # Use advanced semantic chunking
            chunks = await self.semantic_chunker.create_semantic_chunks(cleaned_text, content)
            
            # Post-process chunks to ensure quality
            optimized_chunks = self._optimize_chunks(chunks)
            
            logger.info(f"Created {len(optimized_chunks)} optimized chunks")
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"Error creating content chunks: {e}")
            return []
    
    def _extract_best_content(self, content: Dict[str, Any]) -> str:
        """Extract the best available content for chunking."""
        # Priority order for content extraction
        content_fields = [
            'full_content',
            'content_text', 
            'body_text',
            'body_html',
            'summary'
        ]
        
        for field in content_fields:
            text = content.get(field, '').strip()
            if text and len(text) > 50:  # Ensure meaningful content
                return text
        
        return ''
    
    def _preprocess_content(self, text: str) -> str:
        """Clean and preprocess content for better chunking."""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove email headers and footers
        text = re.sub(r'^.*?Subject:.*?\n', '', text, flags=re.MULTILINE | re.DOTALL)
        text = re.sub(r'From:.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'To:.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'Date:.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'Message-ID:.*?\n', '', text, flags=re.MULTILINE)
        
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up line breaks
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _create_semantic_chunks(self, text: str, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks with semantic boundary detection."""
        # Tokenize the content
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= self.max_chunk_tokens:
            return [{
                'text': text,
                'start_token': 0,
                'end_token': len(tokens),
                'token_count': len(tokens),
                'chunk_type': 'single',
                'source_type': content.get('type', 'unknown')
            }]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Calculate chunk end position
            end = min(start + self.max_chunk_tokens, len(tokens))
            
            # Try to find a good semantic boundary
            if end < len(tokens):
                end = self._find_semantic_boundary(tokens, start, end)
            
            # Extract chunk tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens).strip()
            
            # Skip chunks that are too small
            if len(chunk_tokens) >= self.min_chunk_tokens:
                chunks.append({
                    'text': chunk_text,
                    'start_token': start,
                    'end_token': end,
                    'token_count': len(chunk_tokens),
                    'chunk_type': 'semantic',
                    'source_type': content.get('type', 'unknown')
                })
            
            # Move to next chunk with minimal overlap
            # Use the actual end position to calculate next start, ensuring minimal overlap
            start = max(start + self.max_chunk_tokens - self.chunk_overlap, end - self.chunk_overlap)
            
            # Break if we've covered most of the content
            if start >= len(tokens) - self.chunk_overlap:
                break
        
        return chunks
    
    def _find_semantic_boundary(self, tokens: List[int], start: int, max_end: int) -> int:
        """Find the best semantic boundary for chunking."""
        # Look for sentence boundaries within the chunk
        text = self.tokenizer.decode(tokens[start:max_end])
        
        # Priority order for boundary detection
        boundary_patterns = [
            r'\.\s+',  # Period followed by space
            r'!\s+',   # Exclamation followed by space
            r'\?\s+',  # Question mark followed by space
            r'\.\n',   # Period followed by newline
            r';\s+',   # Semicolon followed by space
            r':\s+',   # Colon followed by space
            r',\s+',   # Comma followed by space
        ]
        
        best_boundary = max_end
        best_position = 0
        
        for pattern in boundary_patterns:
            import re
            matches = list(re.finditer(pattern, text))
            if matches:
                # Find the last match that's not too close to the start
                for match in reversed(matches):
                    position = match.end()
                    if position > len(text) * 0.3:  # At least 30% into the chunk
                        # Convert character position back to token position
                        char_start = start
                        for i, token in enumerate(tokens[start:max_end]):
                            if char_start >= position:
                                best_boundary = start + i
                                break
                            char_start += len(self.tokenizer.decode([token]))
                        break
                if best_boundary < max_end:
                    break
        
        return best_boundary
    
    def _optimize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process chunks to ensure quality and remove redundancy."""
        if not chunks:
            return chunks
        
        optimized = []
        seen_texts = set()
        
        for i, chunk in enumerate(chunks):
            # Skip if chunk is too similar to previous chunks
            chunk_text = chunk['text']
            if self._is_duplicate_chunk(chunk_text, seen_texts):
                continue
            
            # Add chunk metadata
            chunk['chunk_id'] = f"chunk_{i}_{hash(chunk_text) % 10000}"
            chunk['quality_score'] = self._calculate_chunk_quality(chunk)
            
            # Only include high-quality chunks
            if chunk['quality_score'] > 0.3:
                optimized.append(chunk)
                seen_texts.add(chunk_text[:100])  # Store first 100 chars for deduplication
        
        return optimized
    
    def _is_duplicate_chunk(self, text: str, seen_texts: set) -> bool:
        """Check if chunk is too similar to previously seen chunks."""
        text_preview = text[:100]
        for seen in seen_texts:
            if self._calculate_similarity(text_preview, seen) > 0.8:
                return True
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity for deduplication."""
        if not text1 or not text2:
            return 0.0
        
        # Simple Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_chunk_quality(self, chunk: Dict[str, Any]) -> float:
        """Calculate quality score for a chunk."""
        text = chunk['text']
        score = 0.0
        
        # Length score (prefer chunks that are not too short or too long)
        length_score = min(1.0, len(text) / 500)  # Optimal around 500 chars
        score += length_score * 0.3
        
        # Content richness (variety of words)
        words = text.split()
        if len(words) > 10:
            unique_words = len(set(word.lower() for word in words))
            richness_score = unique_words / len(words)
            score += richness_score * 0.3
        
        # Sentence structure (prefer chunks with complete sentences)
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        if sentence_count > 0:
            structure_score = min(1.0, sentence_count / 5)  # Optimal around 5 sentences
            score += structure_score * 0.2
        
        # Avoid chunks that are mostly whitespace or special characters
        alpha_chars = sum(1 for c in text if c.isalpha())
        if len(text) > 0:
            alpha_ratio = alpha_chars / len(text)
            score += alpha_ratio * 0.2
        
        return min(1.0, score)
    
    async def embed_manually_assigned_content(
        self,
        content: Dict[str, Any],
        project_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Embed content that was manually assigned to a project by the user.
        
        Args:
            content: The content to embed
            project_id: Project ID manually assigned by user
            user_id: ID of the user who owns the content
            
        Returns:
            Embedding result
        """
        try:
            # Create a mock classification result for manually assigned content
            classification_result = {
                'project_id': project_id,
                'confidence': 1.0,  # High confidence for manual assignment
                'unclassified': False,
                'document': {
                    'matched_tags': [],
                    'inferred_tags': [],
                    'classification_notes': 'Manually assigned by user'
                }
            }
            
            # Use the standard embedding flow
            return await self.embed_classified_content(content, classification_result, user_id)
            
        except Exception as e:
            logger.error(f"Error embedding manually assigned content: {e}")
            return {
                'embedded': False,
                'reason': f'Manual assignment embedding error: {str(e)}',
                'chunks_created': 0
            }
    
    async def search_similar_content(
        self,
        query: str,
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using vector similarity.
        
        Args:
            query: Search query text
            user_id: ID of the user to search within
            project_id: Optional project ID to filter results
            limit: Maximum number of results to return
            
        Returns:
            List of similar content with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.openai_client.embeddings.create(
                model=self.settings.embedding_model_choice,
                input=query,
                encoding_format="float"
            )
            
            query_vector = query_embedding.data[0].embedding
            
            # Build filter for search
            filter_dict = {'user_id': user_id}
            if project_id:
                filter_dict['project_id'] = project_id
            
            # Search Pinecone
            search_results = self.index.query(
                vector=query_vector,
                filter=filter_dict,
                top_k=limit,
                include_metadata=True
            )
            
            # Process and return results
            results = []
            for match in search_results.matches:
                results.append({
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata,
                    'content_type': match.metadata.get('content_type', 'unknown'),
                    'source_id': match.metadata.get('source_id', ''),
                    'project_id': match.metadata.get('project_id', ''),
                    'author': match.metadata.get('author', ''),
                    'date': match.metadata.get('date', ''),
                    'subject': match.metadata.get('subject', ''),
                    'chunk_text': match.metadata.get('chunk_text', ''),
                    'chunk_index': match.metadata.get('chunk_index', 0),
                    'total_chunks': match.metadata.get('total_chunks', 1)
                })
            
            logger.info(f"Vector search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def _log_embedding_activity(
        self,
        content: Dict[str, Any],
        classification_result: Dict[str, Any],
        user_id: str,
        chunks_created: int
    ):
        """Log embedding activity for monitoring and analytics."""
        try:
            # Log to agent_logs table
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
            
        except Exception as e:
            logger.error(f"Error logging embedding activity: {e}")
    
    async def get_embedding_stats(self, user_id: str) -> Dict[str, Any]:
        """Get embedding statistics for a user."""
        try:
            # Query Pinecone for user's embeddings
            filter_dict = {'user_id': user_id}
            
            # Get index stats
            index_stats = self.index.describe_index_stats(filter=filter_dict)
            
            return {
                'total_vectors': index_stats.total_vector_count,
                'user_vectors': index_stats.namespaces.get('default', {}).vector_count if hasattr(index_stats, 'namespaces') else 0,
                'index_dimension': index_stats.dimension,
                'index_metric': index_stats.metric
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {}
