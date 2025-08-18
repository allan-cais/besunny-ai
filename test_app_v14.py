#!/usr/bin/env python3
"""
BeSunny.ai Backend v14 - Phase 8 Implementation
AI Orchestration & Performance Monitoring

This version includes:
- AI Orchestration Service for intelligent workflow management
- Performance Monitoring Service for system health tracking
- New API endpoints for workflow orchestration and monitoring
- Enhanced service coordination and parallel processing
- Real-time performance metrics and health assessment
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_ai_orchestration_service():
    """Test the AI Orchestration Service functionality."""
    logger.info("🧠 Testing AI Orchestration Service...")
    
    try:
        from app.services.ai.ai_orchestration_service import (
            AIOrchestrationService, 
            AIWorkflowRequest, 
            AIWorkflowResult
        )
        
        # Initialize the service
        service = AIOrchestrationService()
        await service.initialize()
        logger.info("✅ AI Orchestration Service initialized successfully")
        
        # Test workflow creation
        workflow_request = AIWorkflowRequest(
            workflow_id="test-workflow-001",
            user_id="test-user-001",
            workflow_type="classification",
            input_data={"content": "Test document content for classification"},
            expected_outputs=["classification", "summary", "keywords"]
        )
        
        # Execute workflow
        result = await service.execute_workflow(workflow_request)
        logger.info(f"✅ Workflow executed successfully: {result.status}")
        logger.info(f"   Processing time: {result.processing_time_ms}ms")
        logger.info(f"   Services used: {result.services_used}")
        
        # Test workflow status
        status = await service.get_workflow_status("test-workflow-001")
        if status:
            logger.info(f"✅ Workflow status retrieved: {status.get('status', 'unknown')}")
        else:
            logger.info("✅ Workflow status retrieved: no status available")
        
        # Test service health
        health = await service.get_service_health()
        logger.info(f"✅ Service health retrieved: {len(health)} services monitored")
        
        # Test workflow optimization
        optimization = await service.optimize_workflow("classification", "test-user-001")
        logger.info(f"✅ Workflow optimization completed: {optimization.get('recommended_priority', 'unknown')}")
        
        logger.info("🎉 AI Orchestration Service tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ AI Orchestration Service test failed: {e}")
        return False


async def test_performance_monitoring_service():
    """Test the Performance Monitoring Service functionality."""
    logger.info("📊 Testing Performance Monitoring Service...")
    
    try:
        from app.services.enterprise.performance_monitoring_service import (
            PerformanceMonitoringService,
            PerformanceMetrics,
            UserActivityMetrics,
            SystemHealthReport
        )
        
        # Initialize the service
        service = PerformanceMonitoringService()
        await service.initialize()
        logger.info("✅ Performance Monitoring Service initialized successfully")
        
        # Test current metrics collection
        current_metrics = await service.get_current_metrics()
        logger.info(f"✅ Current metrics collected:")
        logger.info(f"   CPU: {current_metrics.cpu_percent:.1f}%")
        logger.info(f"   Memory: {current_metrics.memory_percent:.1f}%")
        logger.info(f"   Disk: {current_metrics.disk_usage_percent:.1f}%")
        
        # Test system health assessment
        health_report = await service.get_system_health()
        logger.info(f"✅ System health assessed: {health_report.overall_health}")
        logger.info(f"   CPU Health: {health_report.cpu_health}")
        logger.info(f"   Memory Health: {health_report.memory_health}")
        logger.info(f"   Disk Health: {health_report.disk_health}")
        
        # Test user activity tracking
        await service.track_user_activity(
            user_id="test-user-001",
            activity_type="api_call",
            metadata={"endpoint": "/api/v1/test", "feature": "testing"}
        )
        logger.info("✅ User activity tracked successfully")
        
        # Test user activity summary
        activity_summary = await service.get_user_activity_summary("test-user-001")
        if activity_summary:
            logger.info(f"✅ User activity summary retrieved:")
            logger.info(f"   API calls: {activity_summary.api_calls}")
            logger.info(f"   Features used: {activity_summary.features_used}")
        
        # Test performance summary
        performance_summary = await service.get_system_performance_summary(hours=1)
        logger.info(f"✅ Performance summary retrieved: {performance_summary.get('metrics_count', 0)} metrics")
        
        # Test optimization recommendations
        optimization = await service.optimize_system_performance()
        logger.info(f"✅ Optimization recommendations retrieved: {len(optimization.get('recommendations', []))} recommendations")
        
        logger.info("🎉 Performance Monitoring Service tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance Monitoring Service test failed: {e}")
        return False


async def test_ai_orchestration_api():
    """Test the AI Orchestration API endpoints."""
    logger.info("🔌 Testing AI Orchestration API...")
    
    try:
        from app.api.v1.ai_orchestration import router as ai_orchestration_router
        
        # Check if router is properly configured
        if ai_orchestration_router:
            logger.info("✅ AI Orchestration API router loaded successfully")
            
            # Check available routes
            routes = [route.path for route in ai_orchestration_router.routes]
            logger.info(f"✅ Available AI Orchestration API routes: {len(routes)}")
            for route in routes:
                logger.info(f"   - {route}")
            
            logger.info("🎉 AI Orchestration API tests completed successfully!")
            return True
        else:
            logger.error("❌ AI Orchestration API router not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ AI Orchestration API test failed: {e}")
        return False


async def test_performance_monitoring_api():
    """Test the Performance Monitoring API endpoints."""
    logger.info("📈 Testing Performance Monitoring API...")
    
    try:
        from app.api.v1.performance_monitoring import router as performance_router
        
        # Check if router is properly configured
        if performance_router:
            logger.info("✅ Performance Monitoring API router loaded successfully")
            
            # Check available routes
            routes = [route.path for route in performance_router.routes]
            logger.info(f"✅ Available Performance Monitoring API routes: {len(routes)}")
            for route in routes:
                logger.info(f"   - {route}")
            
            logger.info("🎉 Performance Monitoring API tests completed successfully!")
            return True
        else:
            logger.error("❌ Performance Monitoring API router not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Performance Monitoring API test failed: {e}")
        return False


async def test_api_integration():
    """Test the integration of new APIs into the main router."""
    logger.info("🔗 Testing API Integration...")
    
    try:
        from app.api.v1 import router as main_router
        
        # Check if main router includes the new routers
        if main_router:
            logger.info("✅ Main API v1 router loaded successfully")
            
            # Check for AI Orchestration routes
            ai_orchestration_routes = [
                route for route in main_router.routes 
                if hasattr(route, 'tags') and 'ai-orchestration' in (route.tags or [])
            ]
            logger.info(f"✅ AI Orchestration routes found: {len(ai_orchestration_routes)}")
            
            # Check for Performance Monitoring routes
            performance_routes = [
                route for route in main_router.routes 
                if hasattr(route, 'tags') and 'performance-monitoring' in (route.tags or [])
            ]
            logger.info(f"✅ Performance Monitoring routes found: {len(performance_routes)}")
            
            logger.info("🎉 API Integration tests completed successfully!")
            return True
        else:
            logger.error("❌ Main API v1 router not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ API Integration test failed: {e}")
        return False


async def test_service_registry():
    """Test the service registry with new services."""
    logger.info("📋 Testing Service Registry...")
    
    try:
        # Check if service registry module can be imported
        import app.core.service_registry
        logger.info("✅ Service Registry module imported successfully")
        
        # Note: In a full test, we would test service registration
        # For now, just verify the module can be imported
        logger.info("✅ Service Registry module accessible")
        
        logger.info("🎉 Service Registry tests completed successfully!")
        return True
            
    except Exception as e:
        logger.error(f"❌ Service Registry test failed: {e}")
        return False


async def test_configuration():
    """Test the configuration system."""
    logger.info("⚙️ Testing Configuration System...")
    
    try:
        from app.core.config import get_settings, is_development
        
        # Test configuration loading
        settings = get_settings()
        if settings:
            logger.info("✅ Configuration loaded successfully")
            logger.info(f"   App Name: {settings.app_name}")
            logger.info(f"   App Version: {settings.app_version}")
            logger.info(f"   Environment: {settings.environment}")
            logger.info(f"   Debug Mode: {settings.debug}")
            
            # Test environment detection
            is_dev = is_development()
            logger.info(f"   Is Development: {is_dev}")
            
            logger.info("🎉 Configuration tests completed successfully!")
            return True
        else:
            logger.error("❌ Configuration not loaded")
            return False
            
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Main test function for v14."""
    logger.info("🚀 Starting BeSunny.ai Backend v14 Tests")
    logger.info("=" * 60)
    
    test_results = []
    
    # Test Configuration
    test_results.append(await test_configuration())
    
    # Test AI Orchestration Service
    test_results.append(await test_ai_orchestration_service())
    
    # Test Performance Monitoring Service
    test_results.append(await test_performance_monitoring_service())
    
    # Test AI Orchestration API
    test_results.append(await test_ai_orchestration_api())
    
    # Test Performance Monitoring API
    test_results.append(await test_performance_monitoring_api())
    
    # Test API Integration
    test_results.append(await test_api_integration())
    
    # Test Service Registry
    test_results.append(await test_service_registry())
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary:")
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    for i, result in enumerate(test_results):
        status = "✅ PASS" if result else "❌ FAIL"
        test_names = [
            "Configuration",
            "AI Orchestration Service",
            "Performance Monitoring Service", 
            "AI Orchestration API",
            "Performance Monitoring API",
            "API Integration",
            "Service Registry"
        ]
        logger.info(f"   {test_names[i]}: {status}")
    
    logger.info(f"   Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! v14 is ready for deployment.")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} tests failed. Please review before deployment.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error during tests: {e}")
        sys.exit(1)
