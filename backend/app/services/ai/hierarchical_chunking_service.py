"""
Hierarchical Chunking Service
Creates multiple levels of chunks for different retrieval needs.
"""

import logging
import tiktoken
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...core.config import get_settings
from .semantic_chunking_service import SemanticChunkingService

logger = logging.getLogger(__name__)

class HierarchicalChunkingService:
    """Service for creating hierarchical chunks at multiple levels of detail."""
    
    def __init__(self):
        self.settings = get_settings()
        self.semantic_chunker = SemanticChunkingService()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Hierarchical levels configuration
        self.levels = {
            'document': {
                'max_tokens': 2000,
                'overlap': 200,
                'description': 'Full document level chunks for broad context'
            },
            'section': {
                'max_tokens': 800,
                'overlap': 100,
                'description': 'Section level chunks for topic-specific retrieval'
            },
            'paragraph': {
                'max_tokens': 400,
                'overlap': 50,
                'description': 'Paragraph level chunks for precise information'
            },
            'sentence': {
                'max_tokens': 200,
                'overlap': 25,
                'description': 'Sentence level chunks for fact-based queries'
            }
        }
    
    async def create_hierarchical_chunks(self, text: str, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create multiple levels of chunks for different retrieval needs."""
        try:
            logger.info(f"Creating hierarchical chunks for content type: {content.get('type', 'unknown')}")
            
            all_chunks = []
            
            # Create chunks at each level
            for level_name, config in self.levels.items():
                level_chunks = await self._create_level_chunks(text, content, level_name, config)
                all_chunks.extend(level_chunks)
                logger.info(f"Created {len(level_chunks)} chunks at {level_name} level")
            
            # Post-process to remove duplicates and optimize
            optimized_chunks = self._optimize_hierarchical_chunks(all_chunks)
            
            logger.info(f"Total hierarchical chunks created: {len(optimized_chunks)}")
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"Error in hierarchical chunking: {e}")
            # Fallback to semantic chunking
            return await self.semantic_chunker.create_semantic_chunks(text, content)
    
    async def _create_level_chunks(self, text: str, content: Dict[str, Any], level: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks at a specific level."""
        try:
            # Tokenize the content
            tokens = self.tokenizer.encode(text)
            
            if len(tokens) <= config['max_tokens']:
                # Content fits in one chunk at this level
                return [self._create_single_level_chunk(text, content, level, config)]
            
            chunks = []
            start = 0
            
            while start < len(tokens):
                # Calculate chunk end position
                end = min(start + config['max_tokens'], len(tokens))
                
                # Try to find a good semantic boundary
                if end < len(tokens):
                    end = self._find_level_boundary(tokens, start, end, level)
                
                # Extract chunk tokens
                chunk_tokens = tokens[start:end]
                chunk_text = self.tokenizer.decode(chunk_tokens).strip()
                
                # Skip chunks that are too small
                if len(chunk_tokens) >= config['max_tokens'] * 0.3:  # At least 30% of max size
                    chunk = self._create_level_chunk(
                        chunk_text, content, level, config, 
                        start, end, len(chunk_tokens)
                    )
                    chunks.append(chunk)
                
                # Move to next chunk with overlap
                start = max(start + config['max_tokens'] - config['overlap'], end - config['overlap'])
                
                # Break if we've covered most of the content
                if start >= len(tokens) - config['overlap']:
                    break
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error creating {level} level chunks: {e}")
            return []
    
    def _create_level_chunk(self, text: str, content: Dict[str, Any], level: str, config: Dict[str, Any], 
                          start: int, end: int, token_count: int) -> Dict[str, Any]:
        """Create a single chunk at a specific level."""
        
        # Add level-specific context enrichment
        enriched_text = self._enrich_level_context(text, content, level)
        
        return {
            'text': enriched_text,
            'original_text': text,
            'level': level,
            'start_token': start,
            'end_token': end,
            'token_count': token_count,
            'chunk_type': f'hierarchical_{level}',
            'source_type': content.get('type', 'unknown'),
            'description': config['description'],
            'context_summary': self._generate_level_summary(text, level),
            'chunk_quality': self._calculate_level_quality(text, token_count, level),
            'hierarchical_metadata': self._create_hierarchical_metadata(content, level)
        }
    
    def _create_single_level_chunk(self, text: str, content: Dict[str, Any], level: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single chunk when content fits at this level."""
        token_count = len(self.tokenizer.encode(text))
        enriched_text = self._enrich_level_context(text, content, level)
        
        return {
            'text': enriched_text,
            'original_text': text,
            'level': level,
            'start_token': 0,
            'end_token': token_count,
            'token_count': token_count,
            'chunk_type': f'hierarchical_{level}_single',
            'source_type': content.get('type', 'unknown'),
            'description': config['description'],
            'context_summary': self._generate_level_summary(text, level),
            'chunk_quality': self._calculate_level_quality(text, token_count, level),
            'hierarchical_metadata': self._create_hierarchical_metadata(content, level)
        }
    
    def _find_level_boundary(self, tokens: List[int], start: int, max_end: int, level: str) -> int:
        """Find the best boundary for a specific level."""
        text = self.tokenizer.decode(tokens[start:max_end])
        
        # Level-specific boundary patterns
        if level == 'document':
            patterns = [
                r'\n\n+',  # Double newlines
                r'\.\s*\n',  # Period + newline
                r'!\s*\n',   # Exclamation + newline
                r'\?\s*\n',  # Question + newline
            ]
        elif level == 'section':
            patterns = [
                r'\n+',      # Newlines
                r'\.\s+',    # Period + space
                r';\s+',     # Semicolon + space
                r':\s+',     # Colon + space
            ]
        elif level == 'paragraph':
            patterns = [
                r'\.\s+',    # Period + space
                r'!\s+',     # Exclamation + space
                r'\?\s+',    # Question + space
                r';\s+',     # Semicolon + space
            ]
        else:  # sentence level
            patterns = [
                r'\.\s+',    # Period + space
                r'!\s+',     # Exclamation + space
                r'\?\s+',    # Question + space
            ]
        
        best_boundary = max_end
        best_position = 0
        
        for pattern in patterns:
            import re
            matches = list(re.finditer(pattern, text))
            if matches:
                # Find the last match that's not too close to the start
                for match in reversed(matches):
                    position = match.end()
                    if position > len(text) * 0.3:  # At least 30% into the chunk
                        # Convert character position back to token position
                        char_start = 0
                        for i, token in enumerate(tokens[start:max_end]):
                            if char_start >= position:
                                best_boundary = start + i
                                break
                            char_start += len(self.tokenizer.decode([token]))
                        break
                if best_boundary < max_end:
                    break
        
        return best_boundary
    
    def _enrich_level_context(self, text: str, content: Dict[str, Any], level: str) -> str:
        """Enrich chunk with level-specific context."""
        
        # Base document context
        doc_context = f"Document: {content.get('title', 'Unknown')}\n"
        doc_context += f"Author: {content.get('author', 'Unknown')}\n"
        doc_context += f"Date: {content.get('date', 'Unknown')}\n"
        doc_context += f"Type: {content.get('type', 'unknown')}\n"
        doc_context += f"Level: {level.upper()}\n"
        
        # Level-specific context
        if level == 'document':
            doc_context += f"Scope: Full document overview\n"
        elif level == 'section':
            doc_context += f"Scope: Section-level content\n"
        elif level == 'paragraph':
            doc_context += f"Scope: Paragraph-level detail\n"
        else:  # sentence
            doc_context += f"Scope: Sentence-level precision\n"
        
        # Add hierarchical metadata
        hierarchical_info = self._create_hierarchical_metadata(content, level)
        doc_context += f"Hierarchical Info: {hierarchical_info}\n"
        
        return f"{doc_context}\n{text}"
    
    def _create_hierarchical_metadata(self, content: Dict[str, Any], level: str) -> str:
        """Create metadata specific to hierarchical level."""
        metadata_parts = []
        
        # Add level-specific information
        if level == 'document':
            metadata_parts.append("Full document context")
            if 'sections' in content:
                metadata_parts.append(f"Sections: {len(content['sections'])}")
        
        elif level == 'section':
            metadata_parts.append("Section-level detail")
            if 'section_headers' in content:
                metadata_parts.append(f"Headers: {content['section_headers']}")
        
        elif level == 'paragraph':
            metadata_parts.append("Paragraph-level detail")
        
        else:  # sentence
            metadata_parts.append("Sentence-level precision")
        
        # Add content-specific metadata
        if content.get('type') == 'email':
            metadata_parts.append("Email thread context")
        elif content.get('type') == 'meeting':
            metadata_parts.append("Meeting transcript context")
        elif content.get('type') == 'document':
            metadata_parts.append("Document structure context")
        
        return ", ".join(metadata_parts)
    
    def _generate_level_summary(self, text: str, level: str) -> str:
        """Generate summary appropriate for the level."""
        if level == 'document':
            return text[:200] + "..." if len(text) > 200 else text
        elif level == 'section':
            return text[:150] + "..." if len(text) > 150 else text
        elif level == 'paragraph':
            return text[:100] + "..." if len(text) > 100 else text
        else:  # sentence
            return text[:50] + "..." if len(text) > 50 else text
    
    def _calculate_level_quality(self, text: str, token_count: int, level: str) -> float:
        """Calculate quality score for a level-specific chunk."""
        quality_score = 0.0
        
        # Level-appropriate length score
        level_config = self.levels[level]
        optimal_tokens = level_config['max_tokens']
        
        if token_count >= optimal_tokens * 0.5:  # At least 50% of optimal
            quality_score += 0.4
        elif token_count >= optimal_tokens * 0.3:  # At least 30% of optimal
            quality_score += 0.3
        else:
            quality_score += 0.2
        
        # Content richness score
        word_count = len(text.split())
        if word_count > 10:
            quality_score += 0.3
        
        # Level-specific completeness score
        if level in ['document', 'section']:
            if text.endswith(('.', '!', '?')) or '\n' in text:
                quality_score += 0.2
        else:  # paragraph or sentence
            if text.endswith(('.', '!', '?')):
                quality_score += 0.2
        
        # Entity/term richness
        import re
        key_terms = re.findall(r'\b[A-Z][a-z]+\b', text)
        if len(key_terms) > 1:
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _optimize_hierarchical_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and optimize hierarchical chunks."""
        if not chunks:
            return chunks
        
        # Remove exact duplicates
        seen_texts = set()
        unique_chunks = []
        
        for chunk in chunks:
            chunk_text = chunk['original_text']
            if chunk_text not in seen_texts:
                seen_texts.add(chunk_text)
                unique_chunks.append(chunk)
        
        # Sort by level priority and quality
        level_priority = {'document': 1, 'section': 2, 'paragraph': 3, 'sentence': 4}
        
        unique_chunks.sort(key=lambda x: (
            level_priority.get(x['level'], 5),
            -x.get('chunk_quality', 0)
        ))
        
        return unique_chunks
