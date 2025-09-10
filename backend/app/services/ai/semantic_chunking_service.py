"""
Semantic Chunking Service
Advanced chunking using similarity-based splitting and context enrichment.
"""

import logging
import re
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
import tiktoken

from ...core.config import get_settings

logger = logging.getLogger(__name__)

class SemanticChunkingService:
    """Advanced semantic chunking service with similarity-based splitting."""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.embedding_api_key or self.settings.openai_api_key,
            base_url=self.settings.embedding_base_url
        )
        
        # Tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Optimized chunking parameters from config
        self.max_chunk_tokens = self.settings.max_chunk_tokens
        self.min_chunk_tokens = self.settings.min_chunk_tokens
        self.chunk_overlap = self.settings.chunk_overlap
        self.similarity_threshold = self.settings.similarity_threshold
    
    async def create_semantic_chunks(self, text: str, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks using similarity-based splitting."""
        try:
            logger.info(f"Creating semantic chunks for content type: {content.get('type', 'unknown')}")
            
            # Step 1: Split into sentences
            sentences = self._split_into_sentences(text)
            logger.info(f"Split into {len(sentences)} sentences")
            
            if len(sentences) <= 1:
                return [self._create_single_chunk(text, content)]
            
            # Step 2: Generate embeddings for each sentence
            sentence_embeddings = await self._generate_sentence_embeddings(sentences)
            logger.info(f"Generated {len(sentence_embeddings)} sentence embeddings")
            
            # Step 3: Find semantic boundaries
            boundaries = self._find_semantic_boundaries(sentences, sentence_embeddings)
            logger.info(f"Found {len(boundaries)} semantic boundaries")
            
            # Step 4: Create chunks with context enrichment
            chunks = self._create_enriched_chunks(sentences, boundaries, content)
            logger.info(f"Created {len(chunks)} enriched chunks")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in semantic chunking: {e}")
            # Fallback to basic chunking
            return self._create_basic_chunks(text, content)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using advanced patterns."""
        # Clean the text first
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Enhanced sentence splitting patterns
        sentence_patterns = [
            r'(?<=[.!?])\s+(?=[A-Z])',  # Period/exclamation/question + space + capital
            r'(?<=[.!?])\s+(?=")',      # Period + space + quote
            r'(?<=[.!?])\s+(?=\d)',     # Period + space + number
            r'(?<=[.!?])\s+(?=\()',     # Period + space + parenthesis
        ]
        
        sentences = [text]
        for pattern in sentence_patterns:
            new_sentences = []
            for sentence in sentences:
                new_sentences.extend(re.split(pattern, sentence))
            sentences = new_sentences
        
        # Clean and filter sentences
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return sentences
    
    async def _generate_sentence_embeddings(self, sentences: List[str]) -> List[List[float]]:
        """Generate embeddings for each sentence."""
        try:
            # Batch process sentences for efficiency
            batch_size = 50
            all_embeddings = []
            
            for i in range(0, len(sentences), batch_size):
                batch = sentences[i:i + batch_size]
                
                response = await self.openai_client.embeddings.create(
                    model=self.settings.embedding_model_choice,
                    input=batch,
                    encoding_format="float"
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating sentence embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 1536 for _ in sentences]
    
    def _find_semantic_boundaries(self, sentences: List[str], embeddings: List[List[float]]) -> List[int]:
        """Find boundaries where semantic similarity drops significantly."""
        if len(embeddings) < 2:
            return [0, len(sentences)]
        
        boundaries = [0]  # Start with first sentence
        
        for i in range(1, len(embeddings)):
            # Calculate similarity between adjacent sentences
            similarity = self._cosine_similarity(embeddings[i-1], embeddings[i])
            
            # If similarity drops below threshold, it's a boundary
            if similarity < self.similarity_threshold:
                boundaries.append(i)
                logger.debug(f"Semantic boundary found at sentence {i}, similarity: {similarity:.3f}")
        
        boundaries.append(len(sentences))  # End boundary
        
        # Ensure we don't have too many small chunks
        boundaries = self._merge_small_chunks(sentences, boundaries)
        
        return boundaries
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _merge_small_chunks(self, sentences: List[str], boundaries: List[int]) -> List[int]:
        """Merge chunks that are too small."""
        merged_boundaries = [boundaries[0]]
        
        for i in range(1, len(boundaries)):
            start_idx = boundaries[i-1]
            end_idx = boundaries[i]
            
            # Calculate chunk size in tokens
            chunk_text = ' '.join(sentences[start_idx:end_idx])
            chunk_tokens = len(self.tokenizer.encode(chunk_text))
            
            # If chunk is too small and not the last chunk, merge with next
            if chunk_tokens < self.min_chunk_tokens and i < len(boundaries) - 1:
                continue  # Skip this boundary
            else:
                merged_boundaries.append(end_idx)
        
        return merged_boundaries
    
    def _create_enriched_chunks(self, sentences: List[str], boundaries: List[int], content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks with enriched context."""
        chunks = []
        
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            
            # Extract chunk sentences
            chunk_sentences = sentences[start_idx:end_idx]
            chunk_text = ' '.join(chunk_sentences)
            
            # Add context enrichment
            enriched_text = self._enrich_chunk_context(chunk_text, content, start_idx, end_idx, sentences)
            
            # Calculate token count
            token_count = len(self.tokenizer.encode(enriched_text))
            
            chunks.append({
                'text': enriched_text,
                'original_text': chunk_text,
                'start_sentence': start_idx,
                'end_sentence': end_idx,
                'sentence_count': end_idx - start_idx,
                'token_count': token_count,
                'chunk_type': 'semantic',
                'source_type': content.get('type', 'unknown'),
                'context_summary': self._generate_context_summary(chunk_sentences),
                'chunk_quality': self._calculate_chunk_quality(chunk_text, token_count)
            })
        
        return chunks
    
    def _enrich_chunk_context(self, chunk_text: str, content: Dict[str, Any], start_idx: int, end_idx: int, all_sentences: List[str]) -> str:
        """Enrich chunk with surrounding context and metadata."""
        
        # Add document context
        doc_context = f"Document: {content.get('title', 'Unknown')}\n"
        doc_context += f"Author: {content.get('author', 'Unknown')}\n"
        doc_context += f"Date: {content.get('date', 'Unknown')}\n"
        doc_context += f"Type: {content.get('type', 'unknown')}\n"
        
        # Add section context if available
        section_context = self._extract_section_context(content, start_idx, end_idx)
        
        # Add summary of surrounding content
        surrounding_summary = self._generate_surrounding_summary(all_sentences, start_idx, end_idx)
        
        # Add key terms and entities
        key_terms = self._extract_key_terms(chunk_text)
        
        # Combine all context
        enriched_text = f"{doc_context}{section_context}\n{chunk_text}\n\nContext: {surrounding_summary}\nKey Terms: {', '.join(key_terms)}"
        
        return enriched_text
    
    def _extract_section_context(self, content: Dict[str, Any], start_idx: int, end_idx: int) -> str:
        """Extract section context from content metadata."""
        section_context = ""
        
        # Look for section headers or structure
        if 'sections' in content:
            section_context += f"Sections: {', '.join(content['sections'])}\n"
        
        # Add any structural information
        if 'structure' in content:
            section_context += f"Structure: {content['structure']}\n"
        
        return section_context
    
    def _generate_surrounding_summary(self, all_sentences: List[str], start_idx: int, end_idx: int) -> str:
        """Generate summary of surrounding content."""
        # Get context from before and after the chunk
        before_sentences = all_sentences[max(0, start_idx - 3):start_idx]
        after_sentences = all_sentences[end_idx:min(len(all_sentences), end_idx + 3)]
        
        context_parts = []
        
        if before_sentences:
            context_parts.append(f"Previous context: {' '.join(before_sentences[-2:])}")
        
        if after_sentences:
            context_parts.append(f"Following context: {' '.join(after_sentences[:2])}")
        
        return ' '.join(context_parts) if context_parts else "No additional context"
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms and entities from text."""
        # Simple key term extraction
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text.lower())
        
        # Count word frequency
        word_count = {}
        for word in words:
            if len(word) > 3:  # Filter short words
                word_count[word] = word_count.get(word, 0) + 1
        
        # Return top terms
        sorted_terms = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [term for term, count in sorted_terms[:5] if count > 1]
    
    def _generate_context_summary(self, sentences: List[str]) -> str:
        """Generate a summary of the chunk content."""
        if not sentences:
            return "Empty chunk"
        
        # Simple summary: first and last sentence
        if len(sentences) == 1:
            return sentences[0][:100] + "..." if len(sentences[0]) > 100 else sentences[0]
        
        return f"{sentences[0][:50]}...{sentences[-1][:50]}" if len(sentences) > 1 else sentences[0][:100]
    
    def _calculate_chunk_quality(self, chunk_text: str, token_count: int) -> float:
        """Calculate quality score for a chunk."""
        quality_score = 0.0
        
        # Length score (prefer chunks in optimal range)
        if self.min_chunk_tokens <= token_count <= self.max_chunk_tokens:
            quality_score += 0.4
        elif token_count < self.min_chunk_tokens:
            quality_score += 0.2
        else:
            quality_score += 0.3
        
        # Content richness score
        word_count = len(chunk_text.split())
        if word_count > 20:
            quality_score += 0.3
        
        # Sentence completeness score
        if chunk_text.endswith(('.', '!', '?')):
            quality_score += 0.2
        
        # Entity/term richness
        key_terms = self._extract_key_terms(chunk_text)
        if len(key_terms) > 2:
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _create_single_chunk(self, text: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single chunk for short content."""
        token_count = len(self.tokenizer.encode(text))
        
        return {
            'text': text,
            'original_text': text,
            'start_sentence': 0,
            'end_sentence': 1,
            'sentence_count': 1,
            'token_count': token_count,
            'chunk_type': 'single',
            'source_type': content.get('type', 'unknown'),
            'context_summary': text[:100] + "..." if len(text) > 100 else text,
            'chunk_quality': self._calculate_chunk_quality(text, token_count)
        }
    
    def _create_basic_chunks(self, text: str, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to basic chunking if semantic chunking fails."""
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= self.max_chunk_tokens:
            return [self._create_single_chunk(text, content)]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = min(start + self.max_chunk_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens).strip()
            
            if len(chunk_tokens) >= self.min_chunk_tokens:
                chunks.append({
                    'text': chunk_text,
                    'original_text': chunk_text,
                    'start_sentence': start,
                    'end_sentence': end,
                    'sentence_count': 1,
                    'token_count': len(chunk_tokens),
                    'chunk_type': 'basic',
                    'source_type': content.get('type', 'unknown'),
                    'context_summary': chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,
                    'chunk_quality': self._calculate_chunk_quality(chunk_text, len(chunk_tokens))
                })
            
            start = max(start + self.max_chunk_tokens - self.chunk_overlap, end - self.chunk_overlap)
            
            if start >= len(tokens) - self.chunk_overlap:
                break
        
        return chunks
