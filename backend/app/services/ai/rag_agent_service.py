"""
RAG Agent Service
Conversational RAG agent that queries Supabase and Pinecone to answer user questions
about project-specific data (emails, Drive files, meeting transcripts).
"""

import logging
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import openai
from pinecone import Pinecone

from ...core.supabase_config import get_supabase_service_client
from ...core.config import get_settings

logger = logging.getLogger(__name__)

class RAGAgentService:
    """RAG agent service for intelligent project data querying."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_service_client()
        
        # Initialize OpenAI client for chat completions
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url if hasattr(self.settings, 'openai_base_url') else None
        )
        
        # Initialize Pinecone client
        self.pinecone = Pinecone(api_key=self.settings.pinecone_api_key)
        self.index_name = self.settings.pinecone_vector_store
        
        # RAG Agent system prompt
        self.rag_prompt = """You are Sunny, the AI assistant for video production teams.

Role
- Act like a senior producer. Use the project database (from Pinecone and Supabase) as your source of truth.
- You may connect related facts and give concise suggestions, but never present a suggestion as fact.

Guidelines
- Context: You are already inside the project. Only surface details relevant to the question.
- Ambiguity: If the question is broad, list 2–4 likely interpretations, then continue with the best fit.
- Conflicts: Prefer the most recent or authoritative source; note older ones as superseded in "Conflict notes."
- Versions: Prefer the latest document version; if needed, add "Version notes."
- Suggestions: Use this label only when making a recommendation or interpreting beyond explicit text.

Formatting
- Use the inverted pyramid - the most important information comes first, followed by details in descending order of importance. Use bullets or sections only if they clarify.
- Always add citations: numbered superscripts (¹ ² ³) placed immediately after claims.
- At the end, include a "Sources" section, formatted as: [1] Title - Date (Source Type).
- Keep responses concise, clear, and easy to scan.

Tone
- Conversational and practical, like a teammate.
- If asked for detail, provide it. If asked for a single fact, return it plainly.
- Be transparent about uncertainty."""
    
    async def query_project_data(
        self,
        user_question: str,
        project_id: str,
        user_id: str,
        session_id: str = None,
        max_results: int = 10
    ) -> AsyncGenerator[str, None]:
        """
        Query project data and generate streaming RAG response.
        
        Args:
            user_question: User's question about the project
            project_id: ID of the project to query
            user_id: ID of the user asking the question
            session_id: Optional session ID for conversation memory
            max_results: Maximum number of results to retrieve
            
        Yields:
            Streaming response text
        """
        try:
            print(f"=== RAG AGENT DEBUG ===")
            print(f"Received project_id: {project_id}")
            print(f"Received user_id: {user_id}")
            print(f"Received question: {user_question}")
            print("=" * 50)
            
            logger.info(f"RAG query for project {project_id}: {user_question}")
            
            # Step 1: Get project information
            project_info = await self._get_project_info(project_id, user_id)
            if not project_info:
                yield "I couldn't find information about this project. Please check if the project exists and you have access to it."
                return
            
            # Step 1.5: Create or get chat session if session_id is provided
            conversation_history = []
            if session_id:
                # Ensure chat session exists
                actual_session_id = await self.create_or_get_chat_session(session_id, user_id, project_id)
                if not actual_session_id:
                    yield "I encountered an error setting up the chat session. Please try again."
                    return
                
                # Get conversation history
                conversation_history = await self._get_conversation_history(actual_session_id, user_id)
                print(f"=== CONVERSATION HISTORY DEBUG ===")
                print(f"Session ID: {actual_session_id}")
                print(f"History messages found: {len(conversation_history)}")
                for i, msg in enumerate(conversation_history[-3:]):  # Show last 3 messages
                    print(f"History {i+1}: {msg.get('role', 'unknown')} - {msg.get('message', '')[:50]}...")
                print("=" * 50)
                
                # Step 1.6: Extract entities and context from conversation history
                conversation_context = self._extract_conversation_context(conversation_history, user_question)
                print(f"=== CONVERSATION CONTEXT DEBUG ===")
                print(f"Extracted context: {conversation_context}")
                print("=" * 50)
            
            # Step 2: Retrieve relevant context from Supabase
            supabase_context = await self._retrieve_supabase_context(
                project_id, user_id, user_question, max_results
            )
            print(f"=== SUPABASE CONTEXT DEBUG ===")
            print(f"Supabase context items found: {len(supabase_context)}")
            for i, item in enumerate(supabase_context[:3]):  # Show first 3 items
                print(f"Supabase item {i+1}: {item.get('type', 'unknown')} - {item.get('title', 'no title')[:50]}...")
            print("=" * 50)
            
            # Step 3: Retrieve relevant context from Pinecone
            pinecone_context = await self._retrieve_pinecone_context(
                project_id, user_id, user_question, max_results
            )
            
            # Step 4: Combine and rank context
            combined_context = self._combine_and_rank_context(
                supabase_context, pinecone_context, user_question
            )
            
            if not combined_context:
                yield "I couldn't find any relevant information in your project data to answer this question. "
                yield "Try asking about specific emails, documents, or meetings, or check if your data has been properly ingested and classified."
                return
            
            # Step 5: Generate streaming response using OpenAI
            actual_session_id = session_id if session_id else None
            async for chunk in self._generate_streaming_response(
                user_question, project_info, combined_context, conversation_history, actual_session_id, user_id
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            yield f"I encountered an error while processing your question: {str(e)}. Please try again."
    
    async def _get_project_info(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get basic project information."""
        try:
            result = self.supabase.table('projects').select('*').eq('id', project_id).eq('created_by', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error getting project info: {e}")
            return None
    
    async def _get_conversation_history(self, session_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            # Get recent messages from the session, ordered by timestamp
            result = self.supabase.table('chat_messages').select('*').eq('bot_id', session_id).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            if not result.data:
                return []
            
            # Convert to conversation format and reverse to get chronological order
            messages = []
            for msg in reversed(result.data):
                # Determine role based on sender_name or other indicators
                role = "user"
                if msg.get('sender_name') and 'assistant' in msg.get('sender_name', '').lower():
                    role = "assistant"
                elif msg.get('sender_name') and 'bot' in msg.get('sender_name', '').lower():
                    role = "assistant"
                
                messages.append({
                    'role': role,
                    'message': msg.get('message', ''),
                    'timestamp': msg.get('created_at', ''),
                    'sender_name': msg.get('sender_name', '')
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def _extract_conversation_context(self, conversation_history: List[Dict[str, Any]], current_question: str) -> Dict[str, Any]:
        """Extract relevant context and entities from conversation history."""
        try:
            context = {
                'mentioned_people': set(),
                'mentioned_projects': set(),
                'mentioned_dates': set(),
                'recent_topics': [],
                'pronoun_references': {}
            }
            
            # Extract entities from recent conversation
            for msg in conversation_history[-5:]:  # Last 5 messages
                message_text = msg.get('message', '').lower()
                
                # Simple entity extraction (you could enhance this with NLP libraries)
                # Look for common patterns
                import re
                
                # Extract names (capitalized words that might be names)
                names = re.findall(r'\b[A-Z][a-z]+\b', msg.get('message', ''))
                context['mentioned_people'].update(names)
                
                # Extract project references
                if 'project' in message_text:
                    context['mentioned_projects'].add('current_project')
                
                # Extract dates
                dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+ \d{1,2},? \d{4}\b', msg.get('message', ''))
                context['mentioned_dates'].update(dates)
                
                # Track recent topics
                if len(msg.get('message', '')) > 10:
                    context['recent_topics'].append(msg.get('message', '')[:100])
            
            # Convert sets to lists for JSON serialization
            context['mentioned_people'] = list(context['mentioned_people'])
            context['mentioned_projects'] = list(context['mentioned_projects'])
            context['mentioned_dates'] = list(context['mentioned_dates'])
            
            # Handle pronoun references
            current_question_lower = current_question.lower()
            if 'his' in current_question_lower or 'her' in current_question_lower or 'their' in current_question_lower:
                # Look for the most recently mentioned person
                if context['mentioned_people']:
                    context['pronoun_references']['his/her/their'] = context['mentioned_people'][-1]
            
            if 'it' in current_question_lower:
                # Look for recently mentioned projects or topics
                if context['mentioned_projects']:
                    context['pronoun_references']['it'] = context['mentioned_projects'][-1]
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting conversation context: {e}")
            return {}
    
    async def create_or_get_chat_session(self, session_id: str, user_id: str, project_id: str) -> str:
        """Create or get existing chat session."""
        try:
            # First, try to get existing session
            existing_session = self.supabase.table('chat_sessions').select('id').eq('id', session_id).single().execute()
            
            if existing_session.data:
                logger.info(f"Using existing chat session {session_id}")
                return session_id
            
            # Create new session if it doesn't exist
            session_data = {
                'id': session_id,
                'user_id': user_id,
                'project_id': project_id,
                'started_at': datetime.now().isoformat(),
                'name': f"Project Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
            
            result = self.supabase.table('chat_sessions').insert(session_data).execute()
            
            if result.data:
                logger.info(f"Created new chat session {session_id}")
                return session_id
            else:
                logger.error(f"Failed to create chat session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating/getting chat session: {e}")
            return None
    
    async def save_assistant_response(self, session_id: str, user_id: str, response: str) -> bool:
        """Save assistant response to chat history."""
        try:
            # Save the assistant's response to the chat_messages table
            message_data = {
                'bot_id': session_id,  # This will be the chat_sessions.id
                'user_id': user_id,
                'message': response,
                'sender_name': 'Sunny AI Assistant',
                'sender_uuid': 'assistant',
                'timestamp': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('chat_messages').insert(message_data).execute()
            
            if result.data:
                logger.info(f"Saved assistant response to session {session_id}")
                return True
            else:
                logger.error(f"Failed to save assistant response to session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving assistant response: {e}")
            return False
    
    async def save_user_message(self, session_id: str, user_id: str, message: str) -> bool:
        """Save user message to chat history."""
        try:
            # Save the user's message to the chat_messages table
            message_data = {
                'bot_id': session_id,  # This will be the chat_sessions.id
                'user_id': user_id,
                'message': message,
                'sender_name': 'User',
                'sender_uuid': user_id,
                'timestamp': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('chat_messages').insert(message_data).execute()
            
            if result.data:
                logger.info(f"Saved user message to session {session_id}")
                return True
            else:
                logger.error(f"Failed to save user message to session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving user message: {e}")
            return False
    
    async def update_session_end_time(self, session_id: str) -> bool:
        """Update the session end time."""
        try:
            result = self.supabase.table('chat_sessions').update({
                'ended_at': datetime.now().isoformat()
            }).eq('id', session_id).execute()
            
            if result.data:
                logger.info(f"Updated session end time for {session_id}")
                return True
            else:
                logger.error(f"Failed to update session end time for {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session end time: {e}")
            return False
    
    async def _retrieve_supabase_context(
        self, 
        project_id: str, 
        user_id: str, 
        query: str, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from Supabase tables."""
        try:
            context_items = []
            
            # Query documents table
            docs_result = self.supabase.table('documents').select('*').eq('project_id', project_id).eq('created_by', user_id).order('created_at', desc=True).limit(max_results).execute()
            if docs_result.data:
                for doc in docs_result.data:
                    context_items.append({
                        'type': 'document',
                        'source': doc.get('source', 'unknown'),
                        'title': doc.get('title', doc.get('subject', 'Untitled')),
                        'content': doc.get('content', ''),
                        'author': doc.get('author', ''),
                        'created_at': doc.get('created_at', ''),
                        'metadata': {
                            'document_id': doc.get('id'),
                            'source_type': doc.get('source'),
                            'file_type': doc.get('file_type'),
                            'file_size': doc.get('file_size')
                        }
                    })
            
            # Query email_processing_logs table (if it has data)
            try:
                emails_result = self.supabase.table('email_processing_logs').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(max_results).execute()
                if emails_result.data:
                    for email in emails_result.data:
                        context_items.append({
                            'type': 'email',
                            'source': 'email',
                            'title': email.get('subject', 'No Subject'),
                            'content': f"From: {email.get('sender', 'Unknown')}\nSubject: {email.get('subject', 'No Subject')}\nReceived: {email.get('received_at', 'Unknown')}",
                            'author': email.get('sender', 'Unknown'),
                            'created_at': email.get('created_at', ''),
                            'metadata': {
                                'email_id': email.get('gmail_message_id'),
                                'inbound_address': email.get('inbound_address'),
                                'extracted_username': email.get('extracted_username')
                            }
                        })
            except Exception as e:
                # Table might not have project_id column or be empty
                logger.debug(f"Email processing logs not available: {e}")
                pass
            
            # Query meetings table
            meetings_result = self.supabase.table('meetings').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(max_results).execute()
            if meetings_result.data:
                for meeting in meetings_result.data:
                    context_items.append({
                        'type': 'meeting',
                        'source': 'attendee_bot',
                        'title': meeting.get('title', 'Untitled Meeting'),
                        'content': meeting.get('description', '') or meeting.get('notes', ''),
                        'author': 'Meeting Attendee',
                        'created_at': meeting.get('created_at', ''),
                        'metadata': {
                            'meeting_id': meeting.get('id'),
                            'start_time': meeting.get('start_time'),
                            'end_time': meeting.get('end_time'),
                            'meeting_url': meeting.get('meeting_url')
                        }
                    })
            
            return context_items
            
        except Exception as e:
            logger.error(f"Error retrieving Supabase context: {e}")
            return []
    
    async def _retrieve_pinecone_context(
        self, 
        project_id: str, 
        user_id: str, 
        query: str, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from Pinecone vector database."""
        try:
            # Generate query embedding
            query_embedding = await self.openai_client.embeddings.create(
                model=self.settings.embedding_model_choice,
                input=query,
                encoding_format="float"
            )
            
            query_vector = query_embedding.data[0].embedding
            
            # Search Pinecone with project filter
            filter_dict = {
                'user_id': user_id,
                'project_id': project_id
            }
            
            print(f"=== PINECONE SEARCH DEBUG ===")
            print(f"Searching with user_id: {user_id}")
            print(f"Searching with project_id: {project_id}")
            print(f"Filter dict: {filter_dict}")
            print(f"Index name: {self.index_name}")
            
            # First, let's try a search without filters to see if there's any data at all
            print("=== TESTING PINECONE WITHOUT FILTERS ===")
            test_results = self.pinecone.Index(self.index_name).query(
                vector=query_vector,
                top_k=5,
                include_metadata=True
            )
            print(f"Total matches without filter: {len(test_results.matches)}")
            if test_results.matches:
                print("Sample metadata from unfiltered search:")
                for i, match in enumerate(test_results.matches[:2]):
                    print(f"Match {i+1} metadata: {match.metadata}")
            print("=" * 50)
            
            # Now try with filters
            search_results = self.pinecone.Index(self.index_name).query(
                vector=query_vector,
                filter=filter_dict,
                top_k=max_results,
                include_metadata=True
            )
            
            context_items = []
            print(f"=== PINECONE SEARCH RESULTS ===")
            print(f"Query: {query[:100]}...")
            print(f"Matches found: {len(search_results.matches)}")
            
            for i, match in enumerate(search_results.matches):
                chunk_text = match.metadata.get('chunk_text', '')
                print(f"--- MATCH {i+1} ---")
                print(f"Score: {match.score:.3f}")
                print(f"Content length: {len(chunk_text)}")
                print(f"Preview: {chunk_text[:200]}...")
                print(f"Full content: {chunk_text}")
                print("-" * 30)
                
                context_items.append({
                    'type': 'vector_chunk',
                    'source': match.metadata.get('content_type', 'unknown'),
                    'title': match.metadata.get('subject', 'Vector Chunk'),
                    'content': chunk_text,
                    'author': match.metadata.get('author', 'Unknown'),
                    'created_at': match.metadata.get('embedded_at', ''),
                    'metadata': {
                        'similarity_score': match.score,
                        'chunk_index': match.metadata.get('chunk_index', 0),
                        'total_chunks': match.metadata.get('total_chunks', 1),
                        'source_id': match.metadata.get('source_id', ''),
                        'matched_tags': match.metadata.get('matched_tags', []),
                        'inferred_tags': match.metadata.get('inferred_tags', [])
                    }
                })
            
            print(f"Returning {len(context_items)} context items from Pinecone")
            print("=" * 50)
            return context_items
            
        except Exception as e:
            logger.error(f"Error retrieving Pinecone context: {e}")
            return []
    
    def _combine_and_rank_context(
        self, 
        supabase_context: List[Dict[str, Any]], 
        pinecone_context: List[Dict[str, Any]], 
        query: str
    ) -> List[Dict[str, Any]]:
        """Combine and rank context from both sources."""
        try:
            all_context = []
            
            # Add Supabase context with base relevance score
            for item in supabase_context:
                item['relevance_score'] = 0.5  # Base score for structured data
                all_context.append(item)
            
            # Add Pinecone context with similarity scores
            for item in pinecone_context:
                # Normalize similarity score to 0-1 range
                similarity = item['metadata'].get('similarity_score', 0)
                item['relevance_score'] = max(0.1, min(1.0, similarity))
                all_context.append(item)
            
            # Sort by relevance score (highest first)
            all_context.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Limit total context items
            max_total_context = 20
            return all_context[:max_total_context]
            
        except Exception as e:
            logger.error(f"Error combining context: {e}")
            return []
    
    async def _generate_streaming_response(
        self, 
        user_question: str, 
        project_info: Dict[str, Any], 
        context: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]] = None,
        session_id: str = None,
        user_id: str = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI."""
        try:
            # Format context for the prompt
            context_text = self._format_context_for_prompt(context)
            
            # Prepare the system prompt with context
            conversation_context_text = ""
            if conversation_history:
                conversation_context_text = f"""

Conversation Context:
Recent conversation history is available. Pay attention to:
- Previously mentioned people, projects, and topics
- Pronoun references (e.g., "his" refers to the most recently mentioned person)
- Context from earlier in the conversation
- Maintain continuity with previous responses

Use this context to provide more coherent and contextually aware responses."""
            
            system_prompt = f"""{self.rag_prompt}

Current Project Context:
Project ID: {project_info.get('id', 'Unknown')}
Project Name: {project_info.get('name', 'Unknown Project')}
User Question: {user_question}

Project Database:
{context_text}{conversation_context_text}

Provide a helpful, accurate response grounded in the project database."""
            
            # Debug logging to see the full system prompt
            print(f"=== SYSTEM PROMPT DEBUG ===")
            print(f"System prompt length: {len(system_prompt)}")
            print(f"First 1000 chars of system prompt:")
            print(system_prompt[:1000])
            print("=" * 50)
            
            # Prepare messages array with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages to avoid token limits
                    messages.append({
                        "role": msg['role'],
                        "content": msg['message']
                    })
            
            # Add current user question
            messages.append({"role": "user", "content": user_question})
            
            print(f"=== OPENAI MESSAGES DEBUG ===")
            print(f"Total messages: {len(messages)}")
            print(f"System prompt length: {len(system_prompt)}")
            print(f"Conversation history messages: {len(conversation_history) if conversation_history else 0}")
            print("=" * 50)
            
            # Create chat completion with streaming
            stream = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Stream the response and collect it for saving
            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Save the complete response to chat history if session_id is provided
            if session_id and full_response.strip():
                # This will run after the streaming is complete
                # Note: In a real implementation, you might want to save this in a background task
                try:
                    await self.save_assistant_response(session_id, user_id, full_response)
                except Exception as e:
                    logger.error(f"Failed to save assistant response: {e}")
                    
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"I encountered an error while generating a response: {str(e)}"
    
    def _format_context_for_prompt(self, context: List[Dict[str, Any]]) -> str:
        """Format context items for the prompt."""
        try:
            if not context:
                return "No relevant context found."
            
            formatted_items = []
            for i, item in enumerate(context, 1):
                source_type = item.get('source', 'unknown').replace('_', ' ').title()
                title = item.get('title', 'Untitled')
                # Increase content length limit to 1000 characters to preserve more context
                content = item.get('content', '')[:1000] + "..." if len(item.get('content', '')) > 1000 else item.get('content', '')
                author = item.get('author', 'Unknown')
                date = item.get('created_at', 'Unknown')
                relevance = item.get('relevance_score', 0)
                
                formatted_item = f"""
{i}. [{source_type}] {title}
   Author: {author}
   Date: {date}
   Relevance: {relevance:.2f}
   Content: {content}
"""
                formatted_items.append(formatted_item)
            
            formatted_context = "\n".join(formatted_items)
            
            # Debug logging to see what context is being sent to the AI model
            print(f"=== FORMATTED CONTEXT FOR AI MODEL ===")
            print(f"Total context items: {len(context)}")
            print(f"Formatted context length: {len(formatted_context)}")
            print(f"First 500 chars of formatted context:")
            print(formatted_context[:500])
            print("=" * 50)
            
            return formatted_context
            
        except Exception as e:
            logger.error(f"Error formatting context: {e}")
            return "Error formatting context."
    
    async def get_project_summary(self, project_id: str, user_id: str) -> str:
        """Get a brief summary of the project based on available data."""
        try:
            # Get basic project info
            project_info = await self._get_project_info(project_id, user_id)
            if not project_info:
                return "Project not found or access denied."
            
            # Get recent activity counts
            docs_count = 0
            emails_count = 0
            meetings_count = 0
            
            try:
                docs_result = self.supabase.table('documents').select('id', count='exact').eq('project_id', project_id).eq('created_by', user_id).execute()
                docs_count = docs_result.count or 0
            except:
                pass
            
            try:
                emails_result = self.supabase.table('email_processing_logs').select('id', count='exact').eq('project_id', project_id).execute()
                emails_count = emails_result.count or 0
            except Exception as e:
                # Table might not have project_id column or be empty
                logger.debug(f"Email processing logs count not available: {e}")
                emails_count = 0
            
            try:
                meetings_result = self.supabase.table('meetings').select('id', count='exact').eq('project_id', project_id).execute()
                meetings_count = meetings_result.count or 0
            except:
                pass
            
            summary = f"Project '{project_info.get('name', 'Unknown')}' contains {docs_count} documents, {emails_count} emails, and {meetings_count} meetings."
            
            if project_info.get('overview'):
                summary += f"\n\nOverview: {project_info.get('overview')}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting project summary: {e}")
            return "Unable to generate project summary."
