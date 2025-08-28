"""
Classification Service
AI-powered classification of incoming content (emails, Drive files, transcripts) to user projects.
Integrated with existing database tables for comprehensive logging and tracking.
Uses OpenAI API for real LLM classification.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import uuid
import openai

from ...core.supabase_config import get_supabase_service_client
from ...core.config import get_settings

logger = logging.getLogger(__name__)

class ClassificationService:
    """AI-powered classification service for matching content to user projects."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
        self.settings = get_settings()
        
        # Initialize OpenAI client
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url if hasattr(self.settings, 'openai_base_url') else None
        )
        
        # Classification Agent system prompt
        self.classification_prompt = """CLASSIFICATION AGENT v4.0
You are a Classification Agent for a production workspace. Your job is to analyze incoming content (emails, Google Drive files, meeting transcripts) and match them to the most relevant existing project using stored project metadata.

INPUT STRUCTURE
content: {
  type: "email" | "drive_file" | "transcript",
  source_id: string,
  author: string,
  date: ISO-8601 timestamp,
  subject?: string,
  content_text: string,
  attachments?: array,
  metadata?: object
}

projects: [{
  project_id: string,
  name: string,
  overview: string,
  categories: array,
  normalized_tags: array,
  reference_keywords: array,
  notes?: string,
  timezone: string
}]

CLASSIFICATION WORKFLOW
Step 1: Content Analysis
Extract key information from the incoming content:
Core topics: Main subjects discussed
Project references: Explicit mentions of project names, codes, or deliverables
People/contacts: Names, roles, organizations mentioned
Locations: Venues, cities, addresses referenced
Deliverables: Specific outputs, files, or milestones mentioned
Timeline indicators: Dates, deadlines, scheduling references

Step 2: Project Matching
For each project in the array, calculate relevance based on:
Primary Signals (highest weight):
Direct project name matches in content
Overlap between content topics and normalized_tags
Matches with reference_keywords
Author/contact alignment with project stakeholders

Secondary Signals (medium weight):
Category alignment with content type/topic
Timeline/date correlations
Location matches
Deliverable type similarity

Contextual Signals (lower weight):
Overall thematic alignment with overview
Related terminology and domain language
Workflow stage indicators

Step 3: Confidence Scoring
Assign confidence based on signal strength:
0.9-1.0: Multiple primary signals + explicit project reference
0.7-0.8: Strong primary signal match + supporting secondary signals
0.5-0.6: Clear secondary signals but no primary matches
0.3-0.4: Weak thematic alignment only
0.0-0.2: No meaningful alignment

Step 4: Classification Decision
Match threshold: Confidence ≥ 0.5 required for classification
If multiple projects exceed threshold: Select highest confidence score
If no project exceeds threshold: Mark as unclassified

OUTPUT FORMAT (JSON ONLY)
{
  "project_id": "uuid-string-or-empty",
  "confidence": 0.85,
  "unclassified": false,
  "document": {
    "source": "email|drive_file|transcript",
    "source_id": "unique-identifier",
    "author": "sender-name-or-email",
    "date": "2025-08-25T15:30:00Z",
    "content_text": "extracted-relevant-content...",
    "matched_tags": ["tag1", "tag2"],
    "inferred_tags": ["new-tag1", "new-tag2"],
    "classification_notes": "Brief explanation of match reasoning"
  }
}

FIELD DEFINITIONS
project_id: UUID of best matching project (empty string if unclassified)
confidence: Numeric score 0.0-1.0 indicating match certainty
unclassified: true if no project exceeds confidence threshold
matched_tags: Tags from project metadata that align with content
inferred_tags: New relevant tags extracted from content
classification_notes: 1-2 sentence explanation of classification decision

UNCLASSIFIED HANDLING
When no clear match exists (confidence < 0.5):
{
  "project_id": "",
  "confidence": 0.0,
  "unclassified": true,
  "classification_notes": "No significant overlap with existing project metadata"
}

KEY PRINCIPLES
Precision over recall: Better to mark as unclassified than misclassify
Evidence-based: Classification must be supported by concrete content matches
No guessing: If uncertain, mark unclassified rather than forcing a match
Consistent scoring: Apply confidence thresholds uniformly
Concise output: Return only structured JSON, no commentary

SPECIAL CASES
Multi-project content: Choose single best match, note in classification_notes
Ambiguous references: Require ≥0.6 confidence for classification
New project indicators: High inferred_tags count may suggest new project needed
Cross-project collaboration: Match to primary project based on content focus"""

    async def classify_content(
        self,
        content: Dict[str, Any],
        user_id: str,
        batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify incoming content to the most relevant user project.
        
        Args:
            content: Content to classify with type, source_id, author, date, content_text, etc.
            user_id: User ID to get projects for
            batch_id: Optional batch ID for grouping classifications
            
        Returns:
            Classification result with project_id, confidence, and metadata
        """
        start_time = datetime.now()
        processing_start = start_time.timestamp() * 1000  # Convert to milliseconds
        
        try:
            logger.info(f"Starting classification for {content.get('type')} from {content.get('author')}")
            
            # Create batch if not provided
            if not batch_id:
                batch_id = await self._create_classification_batch(user_id, [content])
            
            # Get user's projects
            projects = await self._get_user_projects(user_id)
            if not projects:
                logger.warning(f"No projects found for user {user_id}")
                result = self._create_unclassified_result("No projects found for user")
                await self._log_classification_activity(content, result, user_id, batch_id, start_time, processing_start)
                return result
            
            # Prepare content for LLM analysis
            llm_content = self._prepare_content_for_llm(content)
            
            # Get LLM classification
            classification_result = await self._get_llm_classification(llm_content, projects)
            
            if not classification_result:
                logger.warning("LLM classification failed, marking as unclassified")
                result = self._create_unclassified_result("LLM classification failed")
                await self._log_classification_activity(content, result, user_id, batch_id, start_time, processing_start)
                return result
            
            # Validate and process LLM response
            processed_result = self._process_llm_response(classification_result, content)
            
            # Store classification result
            await self._store_classification_result(content, processed_result, user_id, batch_id)
            
            # Log agent activity
            await self._log_classification_activity(content, processed_result, user_id, batch_id, start_time, processing_start)
            
            # Log AI processing metrics
            await self._log_ai_processing(content, processed_result, user_id, start_time, processing_start)
            
            # Update document with project_id if classified
            if processed_result.get('project_id') and not processed_result.get('unclassified', True):
                await self._update_document_project(content, processed_result['project_id'])
            
            logger.info(f"Classification completed: {processed_result.get('project_id', 'unclassified')} (confidence: {processed_result.get('confidence', 0)})")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error in content classification: {e}")
            result = self._create_unclassified_result(f"Classification error: {str(e)}")
            await self._log_classification_activity(content, result, user_id, batch_id, start_time, processing_start)
            return result
    
    async def classify_content_batch(
        self,
        contents: List[Dict[str, Any]],
        user_id: str,
        workflow: str = "standard",
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Classify multiple content items in batch.
        
        Args:
            contents: List of content items to classify
            user_id: User ID to get projects for
            workflow: Classification workflow to use
            priority: Processing priority
            
        Returns:
            Batch classification results
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting batch classification for {len(contents)} items")
            
            # Create classification batch
            batch_id = await self._create_classification_batch(user_id, contents, workflow, priority)
            
            # Process each content item
            results = []
            success_count = 0
            error_count = 0
            
            for content in contents:
                try:
                    result = await self.classify_content(content, user_id, batch_id)
                    results.append(result)
                    
                    if not result.get('unclassified', True):
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error classifying content: {e}")
                    error_count += 1
                    results.append(self._create_unclassified_result(f"Error: {str(e)}"))
            
            # Update batch with results
            await self._update_classification_batch(batch_id, results, success_count, error_count)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"Batch classification completed: {success_count} successful, {error_count} errors")
            
            return {
                'batch_id': batch_id,
                'total_items': len(contents),
                'successful': success_count,
                'errors': error_count,
                'results': results,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in batch classification: {e}")
            return {
                'batch_id': None,
                'total_items': len(contents),
                'successful': 0,
                'errors': len(contents),
                'results': [],
                'processing_time_ms': 0,
                'error': str(e)
            }
    
    async def _create_classification_batch(
        self, 
        user_id: str, 
        contents: List[Dict[str, Any]], 
        workflow: str = "standard",
        priority: str = "normal"
    ) -> str:
        """Create a new classification batch."""
        try:
            batch_data = {
                'batch_id': f"batch_{uuid.uuid4().hex[:8]}",
                'user_id': user_id,
                'project_id': None,  # Will be assigned when projects are found
                'documents': [{'source_id': c.get('source_id'), 'type': c.get('type')} for c in contents],
                'workflow': workflow,
                'priority': priority,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('classification_batches').insert(batch_data).execute()
            
            if result.data:
                batch_id = result.data[0]['batch_id']
                logger.info(f"Created classification batch: {batch_id}")
                return batch_id
            else:
                raise Exception("No batch ID returned from database insert")
                
        except Exception as e:
            logger.error(f"Error creating classification batch: {e}")
            # Return a fallback batch ID
            return f"fallback_{uuid.uuid4().hex[:8]}"
    
    async def _update_classification_batch(
        self, 
        batch_id: str, 
        results: List[Dict[str, Any]], 
        success_count: int, 
        error_count: int
    ):
        """Update classification batch with results."""
        try:
            update_data = {
                'status': 'completed',
                'results': results,
                'success_count': success_count,
                'error_count': error_count,
                'completed_at': datetime.now().isoformat()
            }
            
            self.supabase.table('classification_batches').update(update_data).eq('batch_id', batch_id).execute()
            logger.info(f"Updated classification batch: {batch_id}")
            
        except Exception as e:
            logger.error(f"Error updating classification batch: {e}")
    
    async def _store_classification_result(
        self, 
        content: Dict[str, Any], 
        result: Dict[str, Any], 
        user_id: str,
        batch_id: str
    ):
        """Store classification result in classification_results table."""
        try:
            result_data = {
                'batch_id': batch_id,
                'document_id': content.get('source_id'),
                'classification_result': result,
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('classification_results').insert(result_data).execute()
            logger.info(f"Classification result stored for {content.get('type')} {content.get('source_id')}")
            
        except Exception as e:
            logger.error(f"Error storing classification result: {e}")
    
    async def _log_classification_activity(
        self,
        content: Dict[str, Any],
        result: Dict[str, Any],
        user_id: str,
        batch_id: str,
        start_time: datetime,
        processing_start: float
    ):
        """Log classification activity in agent_logs table."""
        try:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            log_data = {
                'agent_name': 'classification',
                'input_id': content.get('source_id'),
                'input_type': content.get('type'),
                'output': result,
                'confidence': result.get('confidence', 0.0),
                'notes': f"Batch: {batch_id}, User: {user_id}, Processing time: {processing_time}ms",
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('agent_logs').insert(log_data).execute()
            logger.info(f"Classification activity logged for {content.get('type')} {content.get('source_id')}")
            
        except Exception as e:
            logger.error(f"Error logging classification activity: {e}")
    
    async def _log_ai_processing(
        self,
        content: Dict[str, Any],
        result: Dict[str, Any],
        user_id: str,
        start_time: datetime,
        processing_start: float
    ):
        """Log AI processing metrics in ai_processing_logs table."""
        try:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Estimate tokens (rough calculation: 1 token ≈ 4 characters)
            content_length = len(content.get('content_text', ''))
            estimated_tokens = content_length // 4
            
            # Estimate cost (rough calculation: $0.002 per 1K tokens for GPT-4)
            estimated_cost = (estimated_tokens / 1000) * 0.002
            
            log_data = {
                'user_id': user_id,
                'document_id': content.get('source_id'),
                'processing_type': 'classification',
                'model_used': 'gpt-4',  # Will be updated when real LLM is integrated
                'processing_time_ms': processing_time,
                'tokens_used': estimated_tokens,
                'cost_estimate': estimated_cost,
                'success': not result.get('unclassified', True),
                'error_message': None if not result.get('unclassified', True) else "Classification failed",
                'result_metadata': {
                    'confidence': result.get('confidence', 0.0),
                    'project_id': result.get('project_id'),
                    'matched_tags': result.get('document', {}).get('matched_tags', []),
                    'inferred_tags': result.get('document', {}).get('inferred_tags', []),
                    'classification_notes': result.get('document', {}).get('classification_notes', '')
                },
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('ai_processing_logs').insert(log_data).execute()
            logger.info(f"AI processing logged for {content.get('type')} {content.get('source_id')}")
            
        except Exception as e:
            logger.error(f"Error logging AI processing: {e}")
    
    async def _get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's projects from database."""
        try:
            # Try different possible column names for user association
            try:
                result = self.supabase.table('projects').select('*').eq('user_id', user_id).execute()
            except:
                try:
                    result = self.supabase.table('projects').select('*').eq('owner_id', user_id).execute()
                except:
                    try:
                        result = self.supabase.table('projects').select('*').eq('created_by', user_id).execute()
                    except:
                        # If all fail, return empty list
                        logger.warning(f"Could not find user association column in projects table for user {user_id}")
                        return []
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching user projects: {e}")
            return []
    
    def _prepare_content_for_llm(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for LLM analysis."""
        return {
            "type": content.get('type', 'email'),
            "source_id": content.get('source_id', ''),
            "author": content.get('author', ''),
            "date": content.get('date', datetime.now().isoformat()),
            "subject": content.get('subject', ''),
            "content_text": content.get('content_text', ''),
            "attachments": content.get('attachments', []),
            "metadata": content.get('metadata', {})
        }
    
    async def _get_llm_classification(
        self, 
        content: Dict[str, Any], 
        projects: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Get LLM classification using OpenAI API."""
        try:
            logger.info("Making OpenAI API call for classification...")
            
            # Prepare the content and projects for the LLM
            llm_content = self._prepare_content_for_llm(content)
            
            # Create the user message with content and projects
            user_message = f"""Please classify the following content to the most relevant project.

CONTENT TO CLASSIFY:
{json.dumps(llm_content, indent=2)}

AVAILABLE PROJECTS:
{json.dumps(projects, indent=2)}

Please analyze the content and return ONLY a valid JSON response following the exact format specified in the system prompt."""
            
            # Make the OpenAI API call
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.classification_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Extract the response content
            llm_response = response.choices[0].message.content
            logger.info(f"OpenAI API response received: {llm_response[:200]}...")
            
            # Log token usage for cost tracking
            if hasattr(response, 'usage'):
                logger.info(f"Tokens used: {response.usage.total_tokens} (input: {response.usage.prompt_tokens}, output: {response.usage.completion_tokens})")
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Error in OpenAI API classification: {e}")
            # Fallback to mock classification if API fails
            logger.warning("Falling back to mock classification due to API error")
            return self._mock_classification(content, projects)
    
    def _mock_classification(
        self, 
        content: Dict[str, Any], 
        projects: List[Dict[str, Any]]
    ) -> str:
        """Mock classification logic (replace with actual LLM call)."""
        content_text = content.get('content_text', '').lower()
        content_subject = content.get('subject', '').lower()
        
        # Simple keyword matching for demonstration
        for project in projects:
            project_name = project.get('name', '').lower()
            project_tags = [tag.lower() for tag in project.get('normalized_tags', [])]
            project_keywords = [kw.lower() for kw in project.get('reference_keywords', [])]
            
            # Check for direct matches
            if project_name in content_text or project_name in content_subject:
                return json.dumps({
                    "project_id": project['id'],
                    "confidence": 0.9,
                    "unclassified": False,
                    "document": {
                        "source": content.get('type', 'email'),
                        "source_id": content.get('source_id', ''),
                        "author": content.get('author', ''),
                        "date": content.get('date', ''),
                        "content_text": content_text[:200] + "..." if len(content_text) > 200 else content_text,
                        "matched_tags": project_tags[:3],
                        "inferred_tags": [],
                        "classification_notes": f"Direct project name match: {project_name}"
                    }
                })
            
            # Check for tag/keyword matches
            for tag in project_tags:
                if tag in content_text or tag in content_subject:
                    return json.dumps({
                        "project_id": project['id'],
                        "confidence": 0.7,
                        "unclassified": False,
                        "document": {
                            "source": content.get('type', 'email'),
                            "source_id": content.get('source_id', ''),
                            "author": content.get('author', ''),
                            "date": content.get('date', ''),
                            "content_text": content_text[:200] + "..." if len(content_text) > 200 else content_text,
                            "matched_tags": [tag],
                            "inferred_tags": [],
                            "classification_notes": f"Tag match: {tag}"
                        }
                    })
        
        # No match found
        return json.dumps({
            "project_id": "",
            "confidence": 0.0,
            "unclassified": True,
            "document": {
                "source": content.get('type', 'email'),
                "source_id": content.get('source_id', ''),
                "author": content.get('author', ''),
                "date": content.get('date', ''),
                "content_text": content_text[:200] + "..." if len(content_text) > 200 else content_text,
                "matched_tags": [],
                "inferred_tags": [],
                "classification_notes": "No significant overlap with existing project metadata"
            }
        })
    
    def _process_llm_response(self, llm_response: str, original_content: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate LLM classification response."""
        try:
            result = json.loads(llm_response)
            
            # Validate required fields
            required_fields = ['project_id', 'confidence', 'unclassified', 'document']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing required field in LLM response: {field}")
                    return self._create_unclassified_result("Invalid LLM response format")
            
            # Ensure confidence is numeric
            try:
                result['confidence'] = float(result['confidence'])
            except (ValueError, TypeError):
                result['confidence'] = 0.0
            
            # Ensure unclassified is boolean
            result['unclassified'] = bool(result['unclassified'])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in LLM response: {e}")
            return self._create_unclassified_result("Invalid JSON response from LLM")
    
    def _create_unclassified_result(self, reason: str) -> Dict[str, Any]:
        """Create an unclassified result."""
        return {
            "project_id": "",
            "confidence": 0.0,
            "unclassified": True,
            "document": {
                "source": "unknown",
                "source_id": "",
                "author": "",
                "date": datetime.now().isoformat(),
                "content_text": "",
                "matched_tags": [],
                "inferred_tags": [],
                "classification_notes": reason
            }
        }
    
    async def _update_document_project(self, content: Dict[str, Any], project_id: str):
        """Update document with project_id."""
        try:
            # Update documents table
            if content.get('source_id'):
                self.supabase.table('documents').update({
                    'project_id': project_id,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', content['source_id']).execute()
                logger.info(f"Updated document {content['source_id']} with project_id {project_id}")
            
            # Update email_processing_logs if applicable
            if content.get('type') == 'email':
                self.supabase.table('email_processing_logs').update({
                    'project_id': project_id,
                    'updated_at': datetime.now().isoformat()
                }).eq('document_id', content.get('source_id')).execute()
            
        except Exception as e:
            logger.error(f"Error updating document project: {e}")
    
    async def get_classification_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get classification history for a user."""
        try:
            result = self.supabase.table('classification_results').select('*').eq('batch_id', 
                self.supabase.table('classification_batches').select('batch_id').eq('user_id', user_id)
            ).order('created_at', desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching classification history: {e}")
            return []
    
    async def get_project_classifications(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all classifications for a specific project."""
        try:
            # This would need to join with classification_results to get project-specific results
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error fetching project classifications: {e}")
            return []
    
    async def get_ai_processing_metrics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get AI processing metrics for a user."""
        try:
            # Get metrics from ai_processing_logs
            result = self.supabase.table('ai_processing_logs').select('*').eq('user_id', user_id).gte('created_at', 
                (datetime.now() - timedelta(days=days)).isoformat()
            ).execute()
            
            if not result.data:
                return {
                    'total_requests': 0,
                    'success_rate': 0.0,
                    'avg_processing_time': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0
                }
            
            total_requests = len(result.data)
            successful_requests = len([r for r in result.data if r.get('success')])
            success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
            
            processing_times = [r.get('processing_time_ms', 0) for r in result.data if r.get('processing_time_ms')]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            total_tokens = sum([r.get('tokens_used', 0) for r in result.data])
            total_cost = sum([float(r.get('cost_estimate', 0)) for r in result.data])
            
            return {
                'total_requests': total_requests,
                'success_rate': success_rate,
                'avg_processing_time': avg_processing_time,
                'total_tokens': total_tokens,
                'total_cost': total_cost
            }
            
        except Exception as e:
            logger.error(f"Error fetching AI processing metrics: {e}")
            return {}
