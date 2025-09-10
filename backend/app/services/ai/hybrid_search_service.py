"""
Hybrid Search Service
Combines semantic and keyword search for better retrieval performance.
"""

import logging
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
from collections import Counter

from ...core.config import get_settings
from .query_optimization_service import QueryOptimizationService

logger = logging.getLogger(__name__)

class HybridSearchService:
    """Service for hybrid search combining semantic and keyword search."""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url if hasattr(self.settings, 'openai_base_url') else None
        )
        self.query_optimizer = QueryOptimizationService()
        
        # Hybrid search weights
        self.semantic_weight = self.settings.semantic_weight
        self.keyword_weight = self.settings.keyword_weight
        
        # Search configuration
        self.max_semantic_results = 20
        self.max_keyword_results = 20
        self.final_max_results = 10
        
        # BM25 parameters for keyword search
        self.k1 = 1.2
        self.b = 0.75
    
    async def hybrid_search(self, query: str, project_id: str, user_id: str, 
                          max_results: int = 10, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search."""
        try:
            logger.info(f"Performing hybrid search for query: {query[:100]}...")
            
            # Step 1: Optimize the query
            query_optimization = await self.query_optimizer.optimize_query(query, context or {})
            optimized_queries = query_optimization.get('optimized_queries', [query])
            
            # Step 2: Perform semantic search
            semantic_results = await self._semantic_search(optimized_queries, project_id, user_id)
            logger.info(f"Semantic search returned {len(semantic_results)} results")
            
            # Step 3: Perform keyword search
            keyword_results = await self._keyword_search(query, project_id, user_id)
            logger.info(f"Keyword search returned {len(keyword_results)} results")
            
            # Step 4: Combine and rerank results
            combined_results = self._combine_and_rerank(semantic_results, keyword_results)
            logger.info(f"Combined results: {len(combined_results)}")
            
            # Step 5: Apply final filtering and ranking
            final_results = self._apply_final_ranking(combined_results, query, context)
            
            return final_results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to semantic search only
            return await self._fallback_semantic_search(query, project_id, user_id, max_results)
    
    async def _semantic_search(self, queries: List[str], project_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Perform semantic search using multiple query variants."""
        try:
            all_results = []
            
            for query in queries[:3]:  # Use top 3 optimized queries
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
                    top_k=self.max_semantic_results,
                    include_metadata=True
                )
                
                # Process results
                for match in search_results.matches:
                    result = {
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata,
                        'search_type': 'semantic',
                        'query_used': query,
                        'content': match.metadata.get('chunk_text', ''),
                        'source_type': match.metadata.get('content_type', 'unknown'),
                        'chunk_quality': match.metadata.get('chunk_quality', 0.0)
                    }
                    all_results.append(result)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def _keyword_search(self, query: str, project_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Perform keyword search using BM25-style scoring."""
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query)
            
            if not keywords:
                return []
            
            # Get all documents for the project
            from ...core.supabase_config import get_supabase_service_client
            supabase = get_supabase_service_client()
            
            # Query documents table (contains all content types: emails, documents, meetings)
            documents_result = supabase.table('documents').select('*').eq('project_id', project_id).execute()
            
            # Query meetings table for additional metadata
            meetings_result = supabase.table('meetings').select('*').eq('project_id', project_id).execute()
            
            # Combine all content
            all_content = []
            
            # Process documents (contains all content types: emails, documents, meetings)
            if documents_result.data:
                for doc in documents_result.data:
                    content_text = self._extract_content_text(doc)
                    if content_text:
                        # Determine content type and title based on document type
                        doc_type = doc.get('type', 'document')
                        if doc_type == 'email':
                            title = doc.get('title', 'No Subject')  # For emails, title is the subject
                        elif doc_type == 'meeting_transcript':
                            title = doc.get('title', 'Untitled Meeting')
                        else:
                            title = doc.get('title', 'Untitled Document')
                        
                        all_content.append({
                            'id': f"doc_{doc['id']}",
                            'content': content_text,
                            'title': title,
                            'type': doc_type,
                            'metadata': doc
                        })
            
            # Process meetings table for additional metadata (if needed)
            if meetings_result.data:
                for meeting in meetings_result.data:
                    # Only add if not already processed from documents table
                    meeting_id = meeting.get('id')
                    if not any(item['metadata'].get('meeting_id') == meeting_id for item in all_content):
                        content_text = self._extract_content_text(meeting)
                        if content_text:
                            all_content.append({
                                'id': f"meeting_{meeting['id']}",
                                'content': content_text,
                                'title': meeting.get('title', 'Untitled Meeting'),
                                'type': 'meeting',
                                'metadata': meeting
                            })
            
            # Calculate BM25 scores
            scored_results = []
            for item in all_content:
                score = self._calculate_bm25_score(item['content'], keywords)
                if score > 0:
                    scored_results.append({
                        'id': item['id'],
                        'score': score,
                        'content': item['content'],
                        'title': item['title'],
                        'type': item['type'],
                        'metadata': item['metadata'],
                        'search_type': 'keyword',
                        'keywords_matched': self._get_matched_keywords(item['content'], keywords)
                    })
            
            # Sort by score and return top results
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            return scored_results[:self.max_keyword_results]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _extract_content_text(self, item: Dict[str, Any]) -> str:
        """Extract text content from different item types."""
        # Try different content fields in order of preference
        content_fields = [
            'content', 'body', 'text', 'summary', 'description', 'notes',
            'full_content', 'body_text', 'body_html', 'snippet'
        ]
        
        for field in content_fields:
            if field in item and item[field]:
                content = str(item[field]).strip()
                if len(content) > 10:  # Ensure meaningful content
                    return content
        
        # If no direct content field found, try metadata
        if 'metadata' in item and isinstance(item['metadata'], dict):
            for field in content_fields:
                if field in item['metadata'] and item['metadata'][field]:
                    content = str(item['metadata'][field]).strip()
                    if len(content) > 10:
                        return content
        
        return ""
    
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
            
            # Calculate average document length (simplified)
            avg_doc_length = 100  # Simplified assumption
            
            # Calculate BM25 score
            score = 0.0
            for keyword in keywords:
                if keyword in term_freq:
                    tf = term_freq[keyword]
                    idf = math.log(1.0)  # Simplified IDF calculation
                    
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
    
    def _combine_and_rerank(self, semantic_results: List[Dict[str, Any]], 
                          keyword_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine semantic and keyword results with weighted scoring."""
        try:
            # Create a dictionary to store combined results
            combined_results = {}
            
            # Process semantic results
            for result in semantic_results:
                result_id = result['id']
                combined_results[result_id] = {
                    'id': result_id,
                    'semantic_score': result['score'],
                    'keyword_score': 0.0,
                    'combined_score': result['score'] * self.semantic_weight,
                    'metadata': result.get('metadata', {}),
                    'content': result.get('content', ''),
                    'title': result.get('metadata', {}).get('subject', 'Unknown'),
                    'type': result.get('source_type', 'unknown'),
                    'search_types': ['semantic'],
                    'chunk_quality': result.get('chunk_quality', 0.0)
                }
            
            # Process keyword results
            for result in keyword_results:
                result_id = result['id']
                if result_id in combined_results:
                    # Update existing result
                    combined_results[result_id]['keyword_score'] = result['score']
                    combined_results[result_id]['search_types'].append('keyword')
                else:
                    # Add new result
                    combined_results[result_id] = {
                        'id': result_id,
                        'semantic_score': 0.0,
                        'keyword_score': result['score'],
                        'combined_score': result['score'] * self.keyword_weight,
                        'metadata': result.get('metadata', {}),
                        'content': result.get('content', ''),
                        'title': result.get('title', 'Unknown'),
                        'type': result.get('type', 'unknown'),
                        'search_types': ['keyword'],
                        'chunk_quality': 0.0
                    }
            
            # Recalculate combined scores for all results
            for result in combined_results.values():
                semantic_score = result['semantic_score']
                keyword_score = result['keyword_score']
                
                # Normalize scores to 0-1 range
                normalized_semantic = min(semantic_score, 1.0)
                normalized_keyword = min(keyword_score, 1.0)
                
                # Calculate weighted combined score
                result['combined_score'] = (
                    normalized_semantic * self.semantic_weight +
                    normalized_keyword * self.keyword_weight
                )
            
            # Convert to list and sort by combined score
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error combining and reranking results: {e}")
            return semantic_results + keyword_results
    
    def _apply_final_ranking(self, results: List[Dict[str, Any]], 
                           query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply final ranking and filtering to results."""
        try:
            if not results:
                return results
            
            # Apply quality filtering
            quality_filtered = [
                result for result in results 
                if result.get('chunk_quality', 0.0) > 0.3  # Minimum quality threshold
            ]
            
            # Apply relevance boosting
            for result in quality_filtered:
                relevance_boost = self._calculate_relevance_boost(result, query, context)
                result['combined_score'] *= relevance_boost
            
            # Sort by final score
            quality_filtered.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # Remove duplicates based on content similarity
            deduplicated = self._remove_duplicates(quality_filtered)
            
            return deduplicated
            
        except Exception as e:
            logger.error(f"Error applying final ranking: {e}")
            return results
    
    def _calculate_relevance_boost(self, result: Dict[str, Any], query: str, context: Dict[str, Any]) -> float:
        """Calculate relevance boost for a result."""
        try:
            boost = 1.0
            
            # Boost based on content type relevance
            content_type = result.get('type', 'unknown')
            if content_type in ['email', 'meeting']:  # More recent/actionable content
                boost *= 1.2
            
            # Boost based on recency (if available)
            metadata = result.get('metadata', {})
            if 'date' in metadata or 'created_at' in metadata:
                boost *= 1.1  # Slight boost for dated content
            
            # Boost based on query keyword matches
            content = result.get('content', '').lower()
            query_lower = query.lower()
            query_words = query_lower.split()
            
            matches = sum(1 for word in query_words if word in content)
            if matches > 0:
                boost *= (1.0 + matches * 0.1)  # 10% boost per keyword match
            
            # Boost based on context relevance
            if context:
                if 'mentioned_people' in context:
                    people = context['mentioned_people']
                    for person in people:
                        if person.lower() in content:
                            boost *= 1.15  # 15% boost for mentioned people
            
            return min(boost, 2.0)  # Cap boost at 2x
            
        except Exception as e:
            logger.error(f"Error calculating relevance boost: {e}")
            return 1.0
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on content similarity."""
        try:
            if len(results) <= 1:
                return results
            
            unique_results = []
            seen_content = set()
            
            for result in results:
                content = result.get('content', '')
                content_hash = hash(content[:200])  # Use first 200 chars as hash
                
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Error removing duplicates: {e}")
            return results
    
    async def _fallback_semantic_search(self, query: str, project_id: str, user_id: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback to semantic search only if hybrid search fails."""
        try:
            semantic_results = await self._semantic_search([query], project_id, user_id)
            return semantic_results[:max_results]
        except Exception as e:
            logger.error(f"Error in fallback semantic search: {e}")
            return []
