"""
Contextual Retrieval Service
Implements contextual embeddings and BM25 for improved RAG retrieval performance.
Based on Anthropic's Contextual Retrieval research.
"""

import logging
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
from collections import Counter

from ...core.config import get_settings

logger = logging.getLogger(__name__)

class ContextualRetrievalService:
    """Service for contextual retrieval using contextual embeddings and BM25."""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url if hasattr(self.settings, 'openai_base_url') else None
        )
        
        # BM25 parameters
        self.k1 = 1.2
        self.b = 0.75
        
        # Document frequency tracking for BM25
        self.doc_freq = {}
        self.total_docs = 0
        
    async def create_contextual_chunks(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create contextual chunks with enhanced context for better retrieval.
        
        Args:
            content: The content to chunk and contextualize
            
        Returns:
            List of contextual chunks
        """
        try:
            # Extract the best content
            content_text = self._extract_best_content(content)
            if not content_text:
                logger.warning("No content found for contextual chunking")
                return []
            
            # Create base chunks using semantic chunking
            from .semantic_chunking_service import SemanticChunkingService
            semantic_chunker = SemanticChunkingService()
            base_chunks = await semantic_chunker.create_semantic_chunks(content_text, content)
            
            # Add contextual information to each chunk
            contextual_chunks = []
            for i, chunk in enumerate(base_chunks):
                try:
                    # Generate contextual summary for this chunk
                    context_summary = await self._generate_chunk_context(
                        content_text, 
                        chunk['text'], 
                        content
                    )
                    
                    # Create contextual chunk
                    contextual_chunk = {
                        **chunk,
                        'text': f"{context_summary}\n\n{chunk['text']}",
                        'context_summary': context_summary,
                        'original_text': chunk['text'],
                        'chunk_index': i
                    }
                    contextual_chunks.append(contextual_chunk)
                    
                except Exception as e:
                    logger.error(f"Error creating contextual chunk {i}: {e}")
                    # Fallback to original chunk
                    contextual_chunks.append(chunk)
            
            logger.info(f"Created {len(contextual_chunks)} contextual chunks")
            return contextual_chunks
            
        except Exception as e:
            logger.error(f"Error creating contextual chunks: {e}")
            return []
    
    async def _generate_chunk_context(self, full_document: str, chunk_text: str, content: Dict[str, Any]) -> str:
        """Generate contextual summary for a chunk using Claude/GPT."""
        try:
            # Truncate full document to avoid token limits
            max_doc_length = self.settings.contextual_chunk_max_length
            truncated_doc = full_document[:max_doc_length] if len(full_document) > max_doc_length else full_document
            
            # Create context prompt
            context_prompt = f"""
<document>
{truncated_doc}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk_text}
</chunk>

Please give a short, succinct context to situate this chunk within the overall document for the purposes of improving search retrieval. Focus on:
- What project this relates to
- What type of content this is (email, document, meeting)
- Key people, dates, or entities mentioned
- The purpose or context of this information

Answer only with the succinct context and nothing else.
"""
            
            # Use GPT-4o-mini for cost efficiency
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": context_prompt}],
                max_tokens=self.settings.contextual_summary_max_tokens,
                temperature=self.settings.contextual_temperature
            )
            
            context = response.choices[0].message.content.strip()
            logger.debug(f"Generated context for chunk: {context[:100]}...")
            return context
            
        except Exception as e:
            logger.error(f"Error generating chunk context: {e}")
            # Fallback to basic context
            return f"Content from {content.get('type', 'document')} - {content.get('title', 'Untitled')}"
    
    def _extract_best_content(self, content: Dict[str, Any]) -> str:
        """Extract the best available content for chunking."""
        content_fields = [
            'full_content', 'content_text', 'body_text', 'body_html', 
            'content', 'body', 'text', 'summary', 'description', 'notes'
        ]
        
        for field in content_fields:
            text = content.get(field, '').strip()
            if text and len(text) > 50:
                return text
        
        return ''
    
    async def contextual_bm25_search(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform BM25 search on contextualized documents.
        
        Args:
            query: Search query
            documents: List of documents with contextual content
            
        Returns:
            List of scored results
        """
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query)
            if not keywords:
                return []
            
            # Calculate document frequencies for IDF
            self._calculate_document_frequencies(documents)
            
            # Score each document
            scored_results = []
            for doc in documents:
                # Use contextual text if available, otherwise fallback to original
                search_text = doc.get('text', '')  # This should be the contextual text
                if not search_text:
                    search_text = doc.get('original_text', '')
                
                if search_text:
                    score = self._calculate_bm25_score(search_text, keywords)
                    if score > 0:
                        scored_results.append({
                            'id': doc.get('id', ''),
                            'score': score,
                            'content': search_text,
                            'original_content': doc.get('original_text', ''),
                            'context_summary': doc.get('context_summary', ''),
                            'metadata': doc.get('metadata', {}),
                            'search_type': 'contextual_bm25',
                            'keywords_matched': self._get_matched_keywords(search_text, keywords)
                        })
            
            # Sort by score
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            return scored_results
            
        except Exception as e:
            logger.error(f"Error in contextual BM25 search: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_document_frequencies(self, documents: List[Dict[str, Any]]):
        """Calculate document frequencies for IDF calculation."""
        self.doc_freq = {}
        self.total_docs = len(documents)
        
        for doc in documents:
            text = doc.get('text', '') or doc.get('original_text', '')
            if text:
                words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
                for word in words:
                    self.doc_freq[word] = self.doc_freq.get(word, 0) + 1
    
    def _calculate_bm25_score(self, content: str, keywords: List[str]) -> float:
        """Calculate BM25 score for content against keywords."""
        try:
            if not content or not keywords:
                return 0.0
            
            # Tokenize content
            content_words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
            if not content_words:
                return 0.0
            
            # Calculate term frequencies
            term_freq = Counter(content_words)
            doc_length = len(content_words)
            
            # Calculate average document length
            avg_doc_length = 100  # Simplified assumption
            
            # Calculate BM25 score
            score = 0.0
            for keyword in keywords:
                if keyword in term_freq:
                    tf = term_freq[keyword]
                    
                    # Calculate IDF
                    df = self.doc_freq.get(keyword, 1)
                    idf = math.log((self.total_docs + 1) / (df + 1))
                    
                    # BM25 formula
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / avg_doc_length))
                    
                    score += idf * (numerator / denominator)
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating BM25 score: {e}")
            return 0.0
    
    def _get_matched_keywords(self, content: str, keywords: List[str]) -> List[str]:
        """Get list of keywords that matched in content."""
        content_lower = content.lower()
        matched = [kw for kw in keywords if kw in content_lower]
        return matched
    
    async def hybrid_contextual_search(self, query: str, project_id: str, user_id: str, 
                                     max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining contextual embeddings and contextual BM25.
        
        Args:
            query: Search query
            project_id: Project ID to search within
            user_id: User ID to search within
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        try:
            logger.info(f"Performing hybrid contextual search for query: {query[:100]}...")
            
            # Step 1: Get contextual embeddings from Pinecone
            semantic_results = await self._contextual_semantic_search(query, project_id, user_id)
            logger.info(f"Contextual semantic search returned {len(semantic_results)} results")
            
            # Step 2: Get documents for contextual BM25 search
            documents = await self._get_project_documents(project_id, user_id)
            logger.info(f"Retrieved {len(documents)} documents for BM25 search")
            
            # Step 3: Perform contextual BM25 search
            bm25_results = await self.contextual_bm25_search(query, documents)
            logger.info(f"Contextual BM25 search returned {len(bm25_results)} results")
            
            # Step 4: Combine and rerank results
            combined_results = self._combine_contextual_results(semantic_results, bm25_results)
            logger.info(f"Combined results: {len(combined_results)}")
            
            return combined_results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in hybrid contextual search: {e}")
            return []
    
    async def _contextual_semantic_search(self, query: str, project_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Perform semantic search on contextualized embeddings."""
        try:
            # Generate query embedding
            query_embedding = await self.openai_client.embeddings.create(
                model=self.settings.embedding_model_choice,
                input=query,
                encoding_format="float"
            )
            
            query_vector = query_embedding.data[0].embedding
            
            # Search Pinecone
            from pinecone import Pinecone
            pinecone = Pinecone(api_key=self.settings.pinecone_api_key)
            index = pinecone.Index(self.settings.pinecone_vector_store)
            
            search_results = index.query(
                vector=query_vector,
                filter={
                    'user_id': user_id,
                    'project_id': project_id
                },
                top_k=20,
                include_metadata=True
            )
            
            # Process results
            results = []
            for match in search_results.matches:
                results.append({
                    'id': match.id,
                    'score': match.score,
                    'content': match.metadata.get('chunk_text', ''),
                    'metadata': match.metadata,
                    'search_type': 'contextual_semantic'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in contextual semantic search: {e}")
            return []
    
    async def _get_project_documents(self, project_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a project for BM25 search."""
        try:
            from ...core.supabase_config import get_supabase_service_client
            supabase = get_supabase_service_client()
            
            # Query documents table
            result = supabase.table('documents').select('*').eq('project_id', project_id).execute()
            
            documents = []
            if result.data:
                for doc in result.data:
                    content_text = self._extract_best_content(doc)
                    if content_text:
                        documents.append({
                            'id': doc['id'],
                            'text': content_text,  # This will be contextualized
                            'original_text': content_text,
                            'metadata': doc,
                            'type': doc.get('type', 'document')
                        })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting project documents: {e}")
            return []
    
    def _combine_contextual_results(self, semantic_results: List[Dict[str, Any]], 
                                  bm25_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine semantic and BM25 results with weighted scoring."""
        try:
            # Create a dictionary to store combined results
            combined_results = {}
            
            # Process semantic results
            for result in semantic_results:
                result_id = result['id']
                combined_results[result_id] = {
                    'id': result_id,
                    'semantic_score': result['score'],
                    'bm25_score': 0.0,
                    'combined_score': result['score'] * self.settings.semantic_weight,
                    'content': result.get('content', ''),
                    'metadata': result.get('metadata', {}),
                    'search_types': ['semantic']
                }
            
            # Process BM25 results
            for result in bm25_results:
                result_id = result['id']
                if result_id in combined_results:
                    # Update existing result
                    combined_results[result_id]['bm25_score'] = result['score']
                    combined_results[result_id]['search_types'].append('bm25')
                else:
                    # Add new result
                    combined_results[result_id] = {
                        'id': result_id,
                        'semantic_score': 0.0,
                        'bm25_score': result['score'],
                        'combined_score': result['score'] * self.settings.keyword_weight,
                        'content': result.get('content', ''),
                        'metadata': result.get('metadata', {}),
                        'search_types': ['bm25']
                    }
            
            # Recalculate combined scores
            for result in combined_results.values():
                semantic_score = result['semantic_score']
                bm25_score = result['bm25_score']
                
                # Normalize scores
                normalized_semantic = min(semantic_score, 1.0)
                normalized_bm25 = min(bm25_score, 1.0)
                
                # Calculate weighted combined score
                result['combined_score'] = (
                    normalized_semantic * self.settings.semantic_weight +
                    normalized_bm25 * self.settings.keyword_weight
                )
            
            # Convert to list and sort by combined score
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error combining contextual results: {e}")
            return semantic_results + bm25_results
