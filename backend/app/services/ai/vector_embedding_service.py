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
        
        # Chunking configuration
        self.max_chunk_tokens = 1000  # OpenAI recommends 1000 tokens for good embeddings
        self.chunk_overlap = 200  # Overlap to maintain context
    
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
            chunks = self._create_content_chunks(content)
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
    
    def _create_content_chunks(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create text chunks from content for embedding."""
        try:
            # Try multiple content fields to get the full email content
            content_text = (
                content.get('full_content', '') or 
                content.get('content_text', '') or 
                content.get('body_text', '') or 
                content.get('body_html', '') or 
                content.get('summary', '') or 
                ''
            )
            
            if not content_text:
                logger.warning("No content found for chunking - available fields: %s", list(content.keys()))
                return []
            
            logger.info(f"Content for chunking - Type: {content.get('type', 'unknown')}, Length: {len(content_text)}, Preview: {content_text[:200]}...")
            
            # Tokenize the content
            tokens = self.tokenizer.encode(content_text)
            
            if len(tokens) <= self.max_chunk_tokens:
                # Content fits in single chunk
                return [{
                    'text': content_text,
                    'start_token': 0,
                    'end_token': len(tokens),
                    'token_count': len(tokens)
                }]
            
            # Create overlapping chunks
            chunks = []
            start = 0
            
            while start < len(tokens):
                end = min(start + self.max_chunk_tokens, len(tokens))
                
                # Decode tokens back to text for this chunk
                chunk_tokens = tokens[start:end]
                chunk_text = self.tokenizer.decode(chunk_tokens)
                
                chunks.append({
                    'text': chunk_text,
                    'start_token': start,
                    'end_token': end,
                    'token_count': len(chunk_tokens)
                })
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                
                # Ensure we don't create tiny overlapping chunks
                if start >= len(tokens) - self.chunk_overlap:
                    break
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error creating content chunks: {e}")
            return []
    
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
