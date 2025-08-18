"""
Tests for AI services in BeSunny.ai Python backend.
Tests all AI services including enhanced classification, auto scheduling, and document workflows.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any

from ..services.ai.ai_service import AIService, AIProcessingResult
from ..services.ai.enhanced_classification_service import (
    EnhancedClassificationService,
    EnhancedClassificationRequest,
    EnhancedClassificationResult
)
from ..services.ai.auto_schedule_bots_service import (
    AutoScheduleBotsService,
    BotSchedulingResult
)
from ..services.ai.document_workflow_service import (
    DocumentWorkflowService,
    DocumentWorkflow,
    WorkflowExecution,
    WorkflowStep
)


class TestAIService:
    """Test cases for the core AI service."""
    
    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing."""
        with patch('app.services.ai.ai_service.get_settings') as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            mock_settings.return_value.openai_model = "gpt-3.5-turbo"
            mock_settings.return_value.openai_max_tokens = 1000
            return AIService()
    
    @pytest.mark.asyncio
    async def test_generate_bot_configuration(self, ai_service):
        """Test bot configuration generation."""
        # Mock OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"bot_name": "Test Bot", "description": "Test description"}'
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 100
        
        with patch.object(ai_service.client.chat.completions, 'create', return_value=mock_response):
            result = await ai_service.generate_bot_configuration("Test meeting context")
            
            assert result.success is True
            assert result.result["bot_name"] == "Test Bot"
            assert result.result["description"] == "Test description"
    
    @pytest.mark.asyncio
    async def test_analyze_document_sentiment(self, ai_service):
        """Test document sentiment analysis."""
        # Mock OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"sentiment": "positive", "confidence": 0.9}'
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 50
        
        with patch.object(ai_service.client.chat.completions, 'create', return_value=mock_response):
            result = await ai_service.analyze_document_sentiment("Test content")
            
            assert result.success is True
            assert result.result["sentiment"] == "positive"
            assert result.result["confidence"] == 0.9


class TestEnhancedClassificationService:
    """Test cases for the enhanced classification service."""
    
    @pytest.fixture
    def enhanced_service(self):
        """Create enhanced classification service instance for testing."""
        with patch('app.services.ai.enhanced_classification_service.get_settings') as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            return EnhancedClassificationService()
    
    @pytest.fixture
    def mock_request(self):
        """Create mock classification request."""
        return EnhancedClassificationRequest(
            document_id="test-doc-123",
            content="Test document content for classification",
            user_id="test-user-123",
            classification_workflow="standard",
            priority="normal"
        )
    
    @pytest.mark.asyncio
    async def test_classify_document_enhanced(self, enhanced_service, mock_request):
        """Test enhanced document classification."""
        # Mock dependencies
        with patch.object(enhanced_service.classification_service, 'classify_document') as mock_classify:
            mock_classify.return_value = Mock(
                document_id="test-doc-123",
                document_type="document",
                confidence_score=0.95,
                categories=["test"],
                keywords=["test", "document"],
                summary="Test summary",
                entities={},
                sentiment=None,
                processing_time_ms=100,
                model_used="gpt-3.5-turbo",
                classification_source="ai",
                metadata={}
            )
            
            with patch.object(enhanced_service.ai_service, 'analyze_document_sentiment') as mock_sentiment:
                mock_sentiment.return_value = AIProcessingResult(
                    success=True,
                    result={"sentiment": "positive"},
                    processing_time_ms=50,
                    model_used="gpt-3.5-turbo"
                )
                
                result = await enhanced_service.classify_document_enhanced(mock_request)
                
                assert result.workflow_status == "completed"
                assert result.document_type == "document"
                assert result.confidence_score == 0.95
                assert result.sentiment == "positive"
    
    @pytest.mark.asyncio
    async def test_process_classification_batch(self, enhanced_service):
        """Test batch classification processing."""
        # Mock batch data
        batch_data = {
            'batch_id': 'test-batch-123',
            'user_id': 'test-user-123',
            'documents': [
                EnhancedClassificationRequest(
                    document_id="doc-1",
                    content="Content 1",
                    user_id="test-user-123"
                ),
                EnhancedClassificationRequest(
                    document_id="doc-2",
                    content="Content 2",
                    user_id="test-user-123"
                )
            ]
        }
        
        # Mock classification results
        with patch.object(enhanced_service, 'classify_document_enhanced') as mock_classify:
            mock_classify.return_value = Mock(
                workflow_status="completed",
                dict=lambda: {"status": "completed"}
            )
            
            result = await enhanced_service.process_classification_batch(batch_data)
            
            assert result.status == "completed"
            assert result.success_count == 2
            assert result.error_count == 0


class TestAutoScheduleBotsService:
    """Test cases for the auto schedule bots service."""
    
    @pytest.fixture
    def auto_schedule_service(self):
        """Create auto schedule bots service instance for testing."""
        with patch('app.services.ai.auto_schedule_bots_service.get_settings') as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            return AutoScheduleBotsService()
    
    @pytest.fixture
    def mock_meeting(self):
        """Create mock meeting data."""
        return {
            'id': 'meeting-123',
            'title': 'Test Meeting',
            'description': 'Test meeting description',
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'project_id': 'project-123',
            'user_id': 'user-123'
        }
    
    @pytest.mark.asyncio
    async def test_auto_schedule_user_bots(self, auto_schedule_service):
        """Test auto-scheduling bots for a user."""
        # Mock upcoming meetings
        with patch.object(auto_schedule_service, '_get_upcoming_meetings') as mock_get_meetings:
            mock_get_meetings.return_value = [
                {'id': 'meeting-1', 'title': 'Meeting 1'},
                {'id': 'meeting-2', 'title': 'Meeting 2'}
            ]
            
            with patch.object(auto_schedule_service, '_schedule_meeting_bot') as mock_schedule:
                mock_schedule.return_value = Mock(success=True)
                
                result = await auto_schedule_service.auto_schedule_user_bots('user-123')
                
                assert result['success'] is True
                assert result['meetings_processed'] == 2
                assert result['bots_scheduled'] == 2
    
    @pytest.mark.asyncio
    async def test_schedule_meeting_bot(self, auto_schedule_service, mock_meeting):
        """Test scheduling a bot for a specific meeting."""
        # Mock bot configuration generation
        with patch.object(auto_schedule_service, '_generate_bot_configuration') as mock_config:
            mock_config.return_value = {
                'bot_name': 'Test Bot',
                'description': 'Test description',
                'transcription_enabled': True
            }
            
            # Mock database operations
            with patch.object(auto_schedule_service.supabase.table, 'insert') as mock_insert:
                mock_insert.return_value.execute.return_value.data = [{'id': 'bot-123'}]
                
                with patch.object(auto_schedule_service.supabase.table, 'update') as mock_update:
                    mock_update.return_value.eq.return_value.execute.return_value = Mock()
                    
                    result = await auto_schedule_service.schedule_meeting_bot(mock_meeting, 'user-123')
                    
                    assert result.success is True
                    assert result.bot_id == 'bot-123'
                    assert result.bot_name == 'Test Bot'


class TestDocumentWorkflowService:
    """Test cases for the document workflow service."""
    
    @pytest.fixture
    def workflow_service(self):
        """Create document workflow service instance for testing."""
        with patch('app.services.ai.document_workflow_service.get_settings') as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            return DocumentWorkflowService()
    
    @pytest.fixture
    def mock_workflow(self):
        """Create mock workflow data."""
        return DocumentWorkflow(
            workflow_id="workflow-123",
            name="Test Workflow",
            description="Test workflow description",
            document_types=["document", "email"],
            user_id="user-123",
            steps=[
                WorkflowStep(
                    step_id="step-1",
                    name="Classification",
                    description="Classify document",
                    step_type="classification",
                    order=1,
                    action={"workflow_type": "standard"}
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, workflow_service, mock_workflow):
        """Test workflow creation."""
        # Mock database operation
        with patch.object(workflow_service.supabase.table, 'insert') as mock_insert:
            mock_insert.return_value.execute.return_value.data = [{'id': 'workflow-123'}]
            
            result = await workflow_service.create_workflow(mock_workflow)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_service, mock_workflow):
        """Test workflow execution."""
        # Mock workflow retrieval
        with patch.object(workflow_service, '_get_workflow') as mock_get_workflow:
            mock_get_workflow.return_value = mock_workflow
            
            # Mock execution storage
            with patch.object(workflow_service, '_store_execution') as mock_store:
                mock_store.return_value = None
                
                result = await workflow_service.execute_workflow(
                    workflow_id="workflow-123",
                    document_id="doc-123",
                    user_id="user-123"
                )
                
                assert result.workflow_id == "workflow-123"
                assert result.document_id == "doc-123"
                assert result.user_id == "user-123"
                assert result.status == "pending"
    
    @pytest.mark.asyncio
    async def test_workflow_step_execution(self, workflow_service):
        """Test individual workflow step execution."""
        # Mock step
        step = WorkflowStep(
            step_id="step-1",
            name="Test Step",
            description="Test step description",
            step_type="classification",
            order=1,
            action={"workflow_type": "standard"}
        )
        
        # Mock execution context
        execution = Mock()
        execution.document_id = "doc-123"
        execution.user_id = "user-123"
        execution.project_id = "project-123"
        
        # Mock document retrieval
        with patch.object(workflow_service, '_get_document') as mock_get_doc:
            mock_get_doc.return_value = {'id': 'doc-123', 'content': 'Test content'}
            
            # Mock classification service
            with patch.object(workflow_service.enhanced_classification_service, 'classify_document_enhanced') as mock_classify:
                mock_classify.return_value = Mock(
                    dict=lambda: {"status": "completed"}
                )
                
                result = await workflow_service._execute_workflow_step(step, execution)
                
                assert result.status == "success"
                assert result.step_name == "Test Step"


class TestAIServiceIntegration:
    """Integration tests for AI services."""
    
    @pytest.mark.asyncio
    async def test_full_classification_workflow(self):
        """Test complete classification workflow from request to result."""
        # This would test the full integration between services
        # For now, we'll test the basic flow
        pass
    
    @pytest.mark.asyncio
    async def test_bot_scheduling_integration(self):
        """Test bot scheduling integration with AI configuration."""
        # This would test the integration between bot scheduling and AI configuration
        pass
    
    @pytest.mark.asyncio
    async def test_document_workflow_execution(self):
        """Test complete document workflow execution."""
        # This would test the full workflow execution pipeline
        pass


# Performance tests
class TestAIServicePerformance:
    """Performance tests for AI services."""
    
    @pytest.mark.asyncio
    async def test_classification_performance(self):
        """Test classification service performance."""
        # This would test response times and throughput
        pass
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self):
        """Test batch processing performance."""
        # This would test batch processing efficiency
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_execution_performance(self):
        """Test workflow execution performance."""
        # This would test workflow execution speed
        pass


# Error handling tests
class TestAIServiceErrorHandling:
    """Error handling tests for AI services."""
    
    @pytest.mark.asyncio
    async def test_openai_api_failure(self):
        """Test handling of OpenAI API failures."""
        # This would test error handling when OpenAI API is unavailable
        pass
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        # This would test error handling when database is unavailable
        pass
    
    @pytest.mark.asyncio
    async def test_invalid_workflow_configuration(self):
        """Test handling of invalid workflow configurations."""
        # This would test validation and error handling for workflows
        pass


if __name__ == "__main__":
    pytest.main([__file__])
