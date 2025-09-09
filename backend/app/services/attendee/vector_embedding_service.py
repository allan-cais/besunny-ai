"""
Vector embedding service for meeting transcripts.
Handles processing of meeting transcripts through the vector embedding pipeline.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...core.database import get_supabase

logger = logging.getLogger(__name__)

class VectorEmbeddingService:
    """Service for processing meeting transcripts through vector embedding pipeline."""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def process_meeting_transcript(
        self,
        bot_id: str,
        transcript: str,
        project_id: str,
        user_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process meeting transcript through vector embedding pipeline.
        
        Args:
            bot_id: The bot ID
            transcript: The meeting transcript text
            project_id: The classified project ID
            user_id: The user ID
            metadata: Additional bot metadata
            
        Returns:
            Dict with processing result
        """
        try:
            logger.info(f"Processing vector embedding for bot {bot_id} with project {project_id}")
            
            # Create document record for the transcript
            document_id = await self._create_document_record(
                bot_id=bot_id,
                transcript=transcript,
                project_id=project_id,
                user_id=user_id,
                metadata=metadata
            )
            
            if not document_id:
                return {"success": False, "error": "Failed to create document record"}
            
            # Process through embedding pipeline
            embedding_result = await self._process_embeddings(
                document_id=document_id,
                content=transcript,
                project_id=project_id,
                user_id=user_id,
                metadata=metadata
            )
            
            if embedding_result.get('success'):
                # Update bot record to mark as processed
                await self._mark_bot_processed(bot_id, document_id)
                
                logger.info(f"Vector embedding completed for bot {bot_id}")
                return {
                    "success": True,
                    "document_id": document_id,
                    "message": "Transcript processed successfully"
                }
            else:
                logger.error(f"Vector embedding failed for bot {bot_id}: {embedding_result.get('error')}")
                return {
                    "success": False,
                    "error": embedding_result.get('error', 'Embedding processing failed')
                }
                
        except Exception as e:
            logger.error(f"Error processing vector embedding for bot {bot_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_document_record(
        self,
        bot_id: str,
        transcript: str,
        project_id: str,
        user_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Create document record for the transcript."""
        try:
            # Extract meeting details from metadata
            meeting_title = metadata.get('meeting_title', f'Meeting Transcript - {bot_id}')
            meeting_url = metadata.get('meeting_url', '')
            bot_name = metadata.get('bot_name', '')
            
            # Create document record
            document_data = {
                "user_id": user_id,
                "project_id": project_id,
                "title": meeting_title,
                "content": transcript,
                "source": "meeting_transcript",
                "file_type": "transcript",
                "file_name": f"{meeting_title}.txt",
                "file_size": len(transcript.encode('utf-8')),
                "metadata": {
                    "bot_id": bot_id,
                    "meeting_url": meeting_url,
                    "bot_name": bot_name,
                    "deployment_method": metadata.get('deployment_method', ''),
                    "transcript_length": len(transcript),
                    "processed_at": datetime.now().isoformat()
                },
                "status": "pending_embedding",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table('documents').insert(document_data).execute()
            
            if result.data:
                document_id = result.data[0]['id']
                logger.info(f"Created document record {document_id} for bot {bot_id}")
                return document_id
            else:
                logger.error(f"Failed to create document record for bot {bot_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating document record for bot {bot_id}: {e}")
            return None
    
    async def _process_embeddings(
        self,
        document_id: str,
        content: str,
        project_id: str,
        user_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process document through embedding pipeline."""
        try:
            # Use existing embedding service
            from ...services.ai.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            
            # Process document for embeddings
            result = await embedding_service.process_document(
                document_id=document_id,
                content=content,
                project_id=project_id,
                user_id=user_id,
                metadata=metadata
            )
            
            if result.get('success'):
                # Update document status
                await self._update_document_status(document_id, 'embedded')
                return {"success": True}
            else:
                # Update document status to failed
                await self._update_document_status(document_id, 'embedding_failed')
                return {"success": False, "error": result.get('error', 'Embedding failed')}
                
        except Exception as e:
            logger.error(f"Error processing embeddings for document {document_id}: {e}")
            await self._update_document_status(document_id, 'embedding_failed')
            return {"success": False, "error": str(e)}
    
    async def _update_document_status(self, document_id: str, status: str):
        """Update document processing status."""
        try:
            self.supabase.table('documents').update({
                'status': status,
                'updated_at': datetime.now().isoformat()
            }).eq('id', document_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating document status for {document_id}: {e}")
    
    async def _mark_bot_processed(self, bot_id: str, document_id: str):
        """Mark bot as processed in vector embedding pipeline."""
        try:
            self.supabase.table('meeting_bots').update({
                'vector_processed': True,
                'document_id': document_id,
                'updated_at': datetime.now().isoformat()
            }).eq('bot_id', bot_id).execute()
            
        except Exception as e:
            logger.error(f"Error marking bot {bot_id} as processed: {e}")
    
    async def reprocess_meeting_transcript(
        self,
        bot_id: str,
        project_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Reprocess a meeting transcript with a new project classification.
        Used when user manually classifies a meeting.
        
        Args:
            bot_id: The bot ID
            project_id: The new project ID
            user_id: The user ID
            
        Returns:
            Dict with processing result
        """
        try:
            logger.info(f"Reprocessing meeting transcript for bot {bot_id} with project {project_id}")
            
            # Get bot data
            bot_result = self.supabase.table('meeting_bots').select('*').eq('bot_id', bot_id).eq('user_id', user_id).single().execute()
            
            if not bot_result.data:
                return {"success": False, "error": "Bot not found"}
            
            bot_data = bot_result.data
            transcript = bot_data.get('transcript', '')
            metadata = bot_data.get('metadata', {})
            
            if not transcript.strip():
                return {"success": False, "error": "No transcript available"}
            
            # Update bot with new project
            self.supabase.table('meeting_bots').update({
                'project_id': project_id,
                'needs_manual_classification': False,
                'updated_at': datetime.now().isoformat()
            }).eq('bot_id', bot_id).execute()
            
            # Process through vector embedding pipeline
            result = await self.process_meeting_transcript(
                bot_id=bot_id,
                transcript=transcript,
                project_id=project_id,
                user_id=user_id,
                metadata=metadata
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error reprocessing meeting transcript for bot {bot_id}: {e}")
            return {"success": False, "error": str(e)}
