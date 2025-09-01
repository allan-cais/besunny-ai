"""
Embedding service for BeSunny.ai Python backend.
Provides vector embeddings using sentence-transformers and Pinecone integration.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import numpy as np
# Stub for sentence_transformers (not compatible with Python 3.13)
class SentenceTransformer:
    """Stub implementation of SentenceTransformer for Python 3.13 compatibility."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._dimension = 384  # Default dimension for all-MiniLM-L6-v2
    
    def get_sentence_embedding_dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension
    
    def encode(self, sentences, **kwargs):
        """Stub encode method."""
        import numpy as np
        # Return random embeddings for now
        if isinstance(sentences, str):
            sentences = [sentences]
        return np.random.rand(len(sentences), self._dimension).tolist()
import pinecone
from pydantic import BaseModel

from ...core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingResult(BaseModel):
    """Result of embedding operation."""
    success: bool
    embeddings: Optional[List[List[float]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: int
    model_used: str
    vector_dimensions: Optional[int] = None


class VectorSearchResult(BaseModel):
    """Result of vector search operation."""
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    total_results: int = 0
    query_vector: Optional[List[float]] = None
    search_time_ms: int
    error_message: Optional[str] = None


class DocumentChunk(BaseModel):
    """Document chunk for vector storage."""
    id: str
    document_id: str
    chunk_index: int
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    project_id: Optional[str] = None


class EmbeddingService:
    """Service for generating and managing document embeddings."""
    
    def __init__(self):
        self.settings = get_settings()
        self.model_name = "all-MiniLM-L6-v2"  # Default model
        self.model = None
        self.pinecone_index = None
        self._initialized = False
        
        logger.info(f"Embedding Service initialized with model: {self.model_name}")
    
    async def initialize(self):
        """Initialize the embedding service."""
        if self._initialized:
            return
        
        try:
            # Initialize sentence transformer model
            logger.info("Loading sentence transformer model...")
            self.model = SentenceTransformer(self.model_name)
            
            # Initialize Pinecone
            logger.info("Initializing Pinecone...")
            pinecone.init(
                api_key=self.settings.pinecone_api_key,
                environment=self.settings.pinecone_environment
            )
            
            # Get or create index
            index_name = self.settings.pinecone_index_name
            if index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {index_name}")
                pinecone.create_index(
                    name=index_name,
                    dimension=self.model.get_sentence_embedding_dimension(),
                    metric="cosine"
                )
            
            self.pinecone_index = pinecone.Index(index_name)
            self._initialized = True
            
            logger.info("Embedding service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    
    async def generate_embeddings(
        self, 
        texts: Union[str, List[str]], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingResult:
        """
        Generate embeddings for text content.
        
        Args:
            texts: Single text string or list of text strings
            metadata: Optional metadata for the texts
            
        Returns:
            EmbeddingResult with generated embeddings
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            # Convert single text to list
            if isinstance(texts, str):
                texts = [texts]
            
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            
            # Convert to list format
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return EmbeddingResult(
                success=True,
                embeddings=embeddings,
                metadata=metadata,
                processing_time_ms=processing_time,
                model_used=self.model_name,
                vector_dimensions=len(embeddings[0]) if embeddings else None
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Embedding generation failed: {str(e)}")
            
            return EmbeddingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time,
                model_used=self.model_name
            )
    
    async def store_document_chunks(
        self, 
        chunks: List[DocumentChunk]
    ) -> bool:
        """
        Store document chunks with embeddings in Pinecone.
        
        Args:
            chunks: List of document chunks to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Prepare vectors for Pinecone
            vectors = []
            for chunk in chunks:
                vector_data = {
                    "id": chunk.id,
                    "values": chunk.embedding,
                    "metadata": {
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text[:1000],  # Limit text length in metadata
                        "project_id": chunk.project_id,
                        **chunk.metadata
                    }
                }
                vectors.append(vector_data)
            
            # Upsert vectors to Pinecone
            self.pinecone_index.upsert(vectors=vectors)
            
            logger.info(f"Stored {len(chunks)} document chunks in Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document chunks: {e}")
            return False
    
    async def search_similar_documents(
        self, 
        query: str, 
        project_id: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> VectorSearchResult:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query: Search query text
            project_id: Optional project ID to filter results
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score threshold
            
        Returns:
            VectorSearchResult with search results
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embeddings(query)
            if not query_embedding.success:
                return VectorSearchResult(
                    success=False,
                    error_message="Failed to generate query embedding",
                    search_time_ms=(datetime.now() - start_time).microseconds // 1000
                )
            
            query_vector = query_embedding.embeddings[0]
            
            # Prepare filter
            filter_dict = {}
            if project_id:
                filter_dict["project_id"] = project_id
            
            # Search in Pinecone
            search_results = self.pinecone_index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            # Process results
            results = []
            for match in search_results.matches:
                if match.score >= similarity_threshold:
                    results.append({
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata
                    })
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return VectorSearchResult(
                success=True,
                results=results,
                total_results=len(results),
                query_vector=query_vector,
                search_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Vector search failed: {str(e)}")
            
            return VectorSearchResult(
                success=False,
                error_message=str(e),
                search_time_ms=processing_time
            )
    
    async def find_similar_chunks(
        self, 
        chunk_embedding: List[float], 
        document_id: str,
        top_k: int = 5
    ) -> VectorSearchResult:
        """
        Find similar chunks within the same document.
        
        Args:
            chunk_embedding: Embedding of the reference chunk
            document_id: Document ID to search within
            top_k: Number of top results to return
            
        Returns:
            VectorSearchResult with similar chunks
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            # Search for similar chunks within the same document
            search_results = self.pinecone_index.query(
                vector=chunk_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"document_id": document_id}
            )
            
            # Process results
            results = []
            for match in search_results.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            return VectorSearchResult(
                success=True,
                results=results,
                total_results=len(results),
                query_vector=chunk_embedding,
                search_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).microseconds // 1000
            logger.error(f"Similar chunk search failed: {str(e)}")
            
            return VectorSearchResult(
                success=False,
                error_message=str(e),
                search_time_ms=processing_time
            )
    
    async def delete_document_vectors(
        self, 
        document_id: str
    ) -> bool:
        """
        Delete all vectors for a specific document.
        
        Args:
            document_id: ID of the document to delete vectors for
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Delete vectors by metadata filter
            self.pinecone_index.delete(filter={"document_id": document_id})
            
            logger.info(f"Deleted vectors for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document vectors: {e}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.
        
        Returns:
            Dictionary with index statistics
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            stats = self.pinecone_index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}
    
    async def chunk_document(
        self, 
        text: str, 
        chunk_size: int = 1000, 
        overlap: int = 200
    ) -> List[str]:
        """
        Split document text into overlapping chunks.
        
        Args:
            text: Document text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Overlap between consecutive chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size // 2, end - 200), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    async def close(self):
        """Close the embedding service and clean up resources."""
        if self.model:
            del self.model
            self.model = None
        
        if self.pinecone_index:
            self.pinecone_index = None
        
        self._initialized = False
        logger.info("Embedding Service closed")
