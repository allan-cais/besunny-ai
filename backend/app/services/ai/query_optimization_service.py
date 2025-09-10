"""
Query Optimization Service
Optimizes queries for better retrieval performance.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai

from ...core.config import get_settings

logger = logging.getLogger(__name__)

class QueryOptimizationService:
    """Service for optimizing queries for better retrieval."""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url if hasattr(self.settings, 'openai_base_url') else None
        )
        
        # Query expansion configuration
        self.query_expansion_models = {
            'synonyms': True,
            'related_terms': True,
            'context_aware': True,
            'domain_specific': True
        }
        
        # Domain-specific terms for video production
        self.domain_terms = {
            'video_production': [
                'cinematography', 'editing', 'post-production', 'pre-production',
                'director', 'producer', 'crew', 'equipment', 'lighting', 'sound',
                'script', 'storyboard', 'shot list', 'timeline', 'budget',
                'client', 'stakeholder', 'deliverable', 'review', 'approval'
            ],
            'project_management': [
                'timeline', 'deadline', 'milestone', 'deliverable', 'scope',
                'budget', 'resource', 'team', 'meeting', 'status', 'progress',
                'risk', 'issue', 'stakeholder', 'communication', 'coordination'
            ],
            'creative_process': [
                'concept', 'idea', 'creative', 'design', 'visual', 'aesthetic',
                'brand', 'style', 'tone', 'mood', 'message', 'story',
                'narrative', 'character', 'theme', 'inspiration', 'reference'
            ]
        }
    
    async def optimize_query(self, original_query: str, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize query for better retrieval."""
        try:
            logger.info(f"Optimizing query: {original_query[:100]}...")
            
            # Step 1: Query expansion
            expanded_terms = await self._expand_query_terms(original_query)
            
            # Step 2: Context-aware query modification
            contextual_query = self._add_context_to_query(original_query, project_context)
            
            # Step 3: Multi-query generation
            alternative_queries = await self._generate_alternative_queries(original_query, project_context)
            
            # Step 4: Domain-specific enhancement
            domain_enhanced_query = self._enhance_with_domain_terms(original_query, project_context)
            
            # Step 5: Query intent analysis
            intent_analysis = self._analyze_query_intent(original_query)
            
            # Step 6: Combine all optimizations
            optimized_queries = self._combine_optimizations(
                original_query, expanded_terms, contextual_query, 
                alternative_queries, domain_enhanced_query, intent_analysis
            )
            
            logger.info(f"Generated {len(optimized_queries)} optimized query variants")
            
            return {
                'original': original_query,
                'expanded_terms': expanded_terms,
                'contextual': contextual_query,
                'alternatives': alternative_queries,
                'domain_enhanced': domain_enhanced_query,
                'intent_analysis': intent_analysis,
                'optimized_queries': optimized_queries,
                'recommended_query': optimized_queries[0] if optimized_queries else original_query
            }
            
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return {
                'original': original_query,
                'expanded_terms': [],
                'contextual': original_query,
                'alternatives': [],
                'domain_enhanced': original_query,
                'intent_analysis': {'intent': 'unknown', 'confidence': 0.0},
                'optimized_queries': [original_query],
                'recommended_query': original_query
            }
    
    async def _expand_query_terms(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms."""
        try:
            # Simple synonym expansion using domain knowledge
            expanded_terms = []
            
            # Common synonyms and related terms
            synonym_map = {
                'team': ['crew', 'staff', 'members', 'personnel'],
                'project': ['campaign', 'initiative', 'undertaking', 'effort'],
                'meeting': ['session', 'conference', 'discussion', 'call'],
                'document': ['file', 'paper', 'report', 'memo'],
                'email': ['message', 'correspondence', 'communication'],
                'budget': ['cost', 'expense', 'financial', 'funding'],
                'timeline': ['schedule', 'deadline', 'milestone', 'timeline'],
                'video': ['film', 'content', 'production', 'media'],
                'client': ['customer', 'stakeholder', 'partner'],
                'review': ['feedback', 'evaluation', 'assessment', 'critique']
            }
            
            query_lower = query.lower()
            for term, synonyms in synonym_map.items():
                if term in query_lower:
                    expanded_terms.extend(synonyms)
            
            # Add domain-specific terms
            for domain, terms in self.domain_terms.items():
                for term in terms:
                    if term in query_lower:
                        expanded_terms.extend([t for t in terms if t != term])
            
            # Remove duplicates and return
            return list(set(expanded_terms))
            
        except Exception as e:
            logger.error(f"Error expanding query terms: {e}")
            return []
    
    def _add_context_to_query(self, query: str, project_context: Dict[str, Any]) -> str:
        """Add project context to the query."""
        try:
            contextual_parts = [query]
            
            # Add project name if available
            if 'project_name' in project_context:
                contextual_parts.append(f"for project {project_context['project_name']}")
            
            # Add project type if available
            if 'project_type' in project_context:
                contextual_parts.append(f"related to {project_context['project_type']}")
            
            # Add recent context if available
            if 'recent_topics' in project_context:
                recent_topics = project_context['recent_topics'][:3]  # Last 3 topics
                contextual_parts.append(f"in context of {', '.join(recent_topics)}")
            
            # Add mentioned entities if available
            if 'mentioned_people' in project_context:
                people = project_context['mentioned_people'][:2]  # Last 2 people
                contextual_parts.append(f"involving {', '.join(people)}")
            
            return ' '.join(contextual_parts)
            
        except Exception as e:
            logger.error(f"Error adding context to query: {e}")
            return query
    
    async def _generate_alternative_queries(self, query: str, project_context: Dict[str, Any]) -> List[str]:
        """Generate alternative phrasings of the query."""
        try:
            alternatives = []
            
            # Generate variations using different question words
            question_variations = self._generate_question_variations(query)
            alternatives.extend(question_variations)
            
            # Generate variations using different verb tenses
            tense_variations = self._generate_tense_variations(query)
            alternatives.extend(tense_variations)
            
            # Generate variations using different specificity levels
            specificity_variations = self._generate_specificity_variations(query)
            alternatives.extend(specificity_variations)
            
            # Remove duplicates and return top alternatives
            unique_alternatives = list(set(alternatives))
            return unique_alternatives[:5]  # Return top 5 alternatives
            
        except Exception as e:
            logger.error(f"Error generating alternative queries: {e}")
            return []
    
    def _generate_question_variations(self, query: str) -> List[str]:
        """Generate variations using different question words."""
        variations = []
        
        # Common question word replacements
        question_patterns = [
            (r'^what\s+', 'which '),
            (r'^who\s+', 'what '),
            (r'^when\s+', 'what time '),
            (r'^where\s+', 'in what location '),
            (r'^how\s+', 'what method '),
            (r'^why\s+', 'what reason ')
        ]
        
        for pattern, replacement in question_patterns:
            variation = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
            if variation != query:
                variations.append(variation)
        
        return variations
    
    def _generate_tense_variations(self, query: str) -> List[str]:
        """Generate variations using different verb tenses."""
        variations = []
        
        # Tense variations
        tense_patterns = [
            (r'\b(?:is|are|was|were)\b', 'is'),
            (r'\b(?:will|shall)\b', 'will'),
            (r'\b(?:has|have|had)\b', 'has'),
            (r'\b(?:do|does|did)\b', 'does')
        ]
        
        for pattern, replacement in tense_patterns:
            variation = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
            if variation != query:
                variations.append(variation)
        
        return variations
    
    def _generate_specificity_variations(self, query: str) -> List[str]:
        """Generate variations with different specificity levels."""
        variations = []
        
        # Make more specific
        specific_patterns = [
            (r'\bteam\b', 'project team'),
            (r'\bmeeting\b', 'project meeting'),
            (r'\bdocument\b', 'project document'),
            (r'\bemail\b', 'project email')
        ]
        
        for pattern, replacement in specific_patterns:
            variation = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
            if variation != query:
                variations.append(variation)
        
        # Make more general
        general_patterns = [
            (r'\bproject team\b', 'team'),
            (r'\bproject meeting\b', 'meeting'),
            (r'\bproject document\b', 'document'),
            (r'\bproject email\b', 'email')
        ]
        
        for pattern, replacement in general_patterns:
            variation = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
            if variation != query:
                variations.append(variation)
        
        return variations
    
    def _enhance_with_domain_terms(self, query: str, project_context: Dict[str, Any]) -> str:
        """Enhance query with domain-specific terms."""
        try:
            enhanced_parts = [query]
            
            # Add domain-specific context based on project type
            project_type = project_context.get('project_type', '').lower()
            
            if 'video' in project_type or 'production' in project_type:
                enhanced_parts.append('video production')
            
            if 'marketing' in project_type or 'campaign' in project_type:
                enhanced_parts.append('marketing campaign')
            
            if 'creative' in project_type:
                enhanced_parts.append('creative process')
            
            # Add relevant domain terms based on query content
            query_lower = query.lower()
            
            if any(term in query_lower for term in ['team', 'member', 'person']):
                enhanced_parts.append('crew personnel')
            
            if any(term in query_lower for term in ['meeting', 'call', 'discussion']):
                enhanced_parts.append('collaboration session')
            
            if any(term in query_lower for term in ['document', 'file', 'paper']):
                enhanced_parts.append('project asset')
            
            return ' '.join(enhanced_parts)
            
        except Exception as e:
            logger.error(f"Error enhancing with domain terms: {e}")
            return query
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent behind the query."""
        try:
            query_lower = query.lower()
            
            # Intent patterns
            intent_patterns = {
                'factual': [
                    r'\b(?:what|who|when|where|how many|how much)\b',
                    r'\b(?:is|are|was|were|has|have|had)\b'
                ],
                'procedural': [
                    r'\b(?:how to|how do|how can|how should)\b',
                    r'\b(?:process|procedure|steps|method)\b'
                ],
                'analytical': [
                    r'\b(?:why|why not|reason|cause|effect)\b',
                    r'\b(?:analyze|analysis|compare|contrast)\b'
                ],
                'temporal': [
                    r'\b(?:when|time|schedule|timeline|deadline)\b',
                    r'\b(?:recent|latest|current|previous|next)\b'
                ],
                'relational': [
                    r'\b(?:related|connection|link|associate)\b',
                    r'\b(?:between|among|with|and|or)\b'
                ]
            }
            
            detected_intents = []
            confidence_scores = {}
            
            for intent, patterns in intent_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, query_lower):
                        matches += 1
                
                if matches > 0:
                    detected_intents.append(intent)
                    confidence_scores[intent] = min(matches / len(patterns), 1.0)
            
            # Determine primary intent
            primary_intent = 'factual'  # Default
            if detected_intents:
                primary_intent = max(detected_intents, key=lambda x: confidence_scores.get(x, 0))
            
            return {
                'intent': primary_intent,
                'confidence': confidence_scores.get(primary_intent, 0.0),
                'all_intents': detected_intents,
                'confidence_scores': confidence_scores
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query intent: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'all_intents': [],
                'confidence_scores': {}
            }
    
    def _combine_optimizations(self, original_query: str, expanded_terms: List[str], 
                             contextual_query: str, alternative_queries: List[str],
                             domain_enhanced_query: str, intent_analysis: Dict[str, Any]) -> List[str]:
        """Combine all optimizations into final query variants."""
        try:
            optimized_queries = []
            
            # Add original query
            optimized_queries.append(original_query)
            
            # Add contextual query if different
            if contextual_query != original_query:
                optimized_queries.append(contextual_query)
            
            # Add domain enhanced query if different
            if domain_enhanced_query != original_query:
                optimized_queries.append(domain_enhanced_query)
            
            # Add alternative queries
            optimized_queries.extend(alternative_queries)
            
            # Create intent-specific queries
            intent_queries = self._create_intent_specific_queries(original_query, intent_analysis)
            optimized_queries.extend(intent_queries)
            
            # Create expanded term queries
            if expanded_terms:
                expanded_query = f"{original_query} {' '.join(expanded_terms[:3])}"  # Top 3 terms
                optimized_queries.append(expanded_query)
            
            # Remove duplicates and return
            unique_queries = []
            seen = set()
            for query in optimized_queries:
                if query not in seen:
                    seen.add(query)
                    unique_queries.append(query)
            
            return unique_queries[:8]  # Return top 8 optimized queries
            
        except Exception as e:
            logger.error(f"Error combining optimizations: {e}")
            return [original_query]
    
    def _create_intent_specific_queries(self, query: str, intent_analysis: Dict[str, Any]) -> List[str]:
        """Create queries optimized for specific intents."""
        try:
            intent_queries = []
            primary_intent = intent_analysis.get('intent', 'factual')
            
            if primary_intent == 'factual':
                # Add specificity for factual queries
                intent_queries.append(f"specific details about {query}")
            
            elif primary_intent == 'procedural':
                # Add process context for procedural queries
                intent_queries.append(f"process and steps for {query}")
            
            elif primary_intent == 'analytical':
                # Add analysis context for analytical queries
                intent_queries.append(f"analysis and insights about {query}")
            
            elif primary_intent == 'temporal':
                # Add time context for temporal queries
                intent_queries.append(f"timeline and schedule for {query}")
            
            elif primary_intent == 'relational':
                # Add relationship context for relational queries
                intent_queries.append(f"connections and relationships for {query}")
            
            return intent_queries
            
        except Exception as e:
            logger.error(f"Error creating intent-specific queries: {e}")
            return []
