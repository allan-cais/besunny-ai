# Python Backend Frontend Integration Guide

## Overview

This document describes the complete integration between the Python backend and React frontend for BeSunny.ai. The integration provides seamless fallback between Python backend services and existing Supabase edge functions, ensuring reliability and performance.

## Architecture

### Integration Pattern

The integration follows a **hybrid approach** where:

1. **Python Backend** is the primary service for new functionality
2. **Supabase Edge Functions** serve as fallback for reliability
3. **Automatic failover** ensures service continuity
4. **Feature flags** control which backend to use

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │────│  Hybrid Service  │────│  Python Backend │
│                 │    │   Layer          │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Supabase Edge    │
                       │ Functions        │
                       │ (Fallback)       │
                       └──────────────────┘
```

### Key Components

- **`PythonBackendAPI`**: Direct API client for Python backend
- **`HybridCalendarService`**: Service that automatically chooses backend
- **`usePythonBackend`**: React hook for backend status management
- **`PythonBackendStatus`**: UI component showing connection status
- **`PythonBackendIntegrationTest`**: Comprehensive testing component

## Frontend Integration

### 1. Configuration

Add Python backend configuration to your `.env.local`:

```bash
# Python Backend Configuration
VITE_PYTHON_BACKEND_URL=http://localhost:8000
VITE_PYTHON_BACKEND_TIMEOUT=30000
VITE_PYTHON_BACKEND_RETRIES=3
VITE_PYTHON_BACKEND_RETRY_DELAY=1000
VITE_ENABLE_PYTHON_BACKEND=true
```

### 2. Using the Hybrid Service

Replace direct calendar service calls with the hybrid service:

```typescript
// Before (Supabase only)
import { calendarService } from '@/lib/calendar';

// After (Hybrid - Python backend + Supabase fallback)
import { hybridCalendarService as calendarService } from '@/lib/hybrid-calendar-service';

// Usage remains the same
const meetings = await calendarService.getCurrentWeekMeetings();
```

### 3. Backend Status Monitoring

Use the Python backend hook to monitor connection status:

```typescript
import { usePythonBackend } from '@/hooks/use-python-backend';

function MyComponent() {
  const { status, isFeatureEnabled } = usePythonBackend();
  
  if (status.isConnected && isFeatureEnabled('calendar')) {
    // Use Python backend features
  } else {
    // Fall back to Supabase
  }
}
```

### 4. Status Display

Add the status indicator to your UI:

```typescript
import PythonBackendStatus from '@/components/PythonBackendStatus';

// Simple status badge
<PythonBackendStatus />

// Detailed status card
<PythonBackendStatus showDetails={true} />
```

## Backend Integration

### 1. Environment Configuration

Configure the Python backend with proper webhook URLs:

```bash
# Backend .env
WEBHOOK_BASE_URL=http://localhost:8000
CALENDAR_WEBHOOK_TIMEOUT=60
CALENDAR_SYNC_INTERVAL=600
```

### 2. API Endpoints

The Python backend provides these key endpoints:

#### Calendar API
- `POST /api/v1/calendar/webhook` - Setup calendar webhook
- `POST /api/v1/calendar/sync` - Trigger calendar sync
- `GET /api/v1/calendar/meetings` - Get user meetings
- `GET /api/v1/calendar/meetings/{id}` - Get meeting details
- `POST /api/v1/calendar/meetings/{id}/bot` - Schedule meeting bot

#### Documents API
- `GET /api/v1/documents` - List documents
- `POST /api/v1/documents` - Create document
- `GET /api/v1/documents/{id}` - Get document
- `PUT /api/v1/documents/{id}` - Update document
- `DELETE /api/v1/documents/{id}` - Delete document

#### Projects API
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### 3. Authentication

The Python backend uses JWT tokens from Supabase:

```typescript
// Frontend automatically sets auth token
const { setAuthToken } = usePythonBackend();

// Token is automatically managed when user logs in/out
```

## Service Integration Examples

### Calendar Service

```typescript
// Automatic backend selection
const meetings = await hybridCalendarService.getCurrentWeekMeetings();

// Manual backend selection
if (await hybridCalendarService.isPythonBackendAvailable()) {
  const response = await pythonBackendAPI.getUserMeetings();
  meetings = response.data.meetings;
} else {
  meetings = await supabaseCalendarService.getCurrentWeekMeetings();
}
```

### Document Service

```typescript
// Create document with automatic backend selection
const document = await hybridDocumentService.createDocument({
  title: 'New Document',
  content: 'Document content...',
  type: 'document'
});
```

### Project Service

```typescript
// Get projects with automatic backend selection
const projects = await hybridProjectService.getProjects();
```

## Testing and Debugging

### 1. Integration Test Component

Use the built-in integration test component:

```typescript
import PythonBackendIntegrationTest from '@/components/PythonBackendIntegrationTest';

// Add to your dashboard
<PythonBackendIntegrationTest />
```

### 2. Manual Testing

Test individual services:

```typescript
// Test Python backend health
const health = await pythonBackendAPI.healthCheck();

// Test specific service
const meetings = await pythonBackendAPI.getUserMeetings();
```

### 3. Debug Mode

Enable debug logging:

```typescript
// Check backend status
const { status } = usePythonBackend();
console.log('Backend status:', status);

// Check feature availability
const isCalendarAvailable = isFeatureEnabled('calendar');
console.log('Calendar available:', isCalendarAvailable);
```

## Error Handling

### 1. Automatic Fallback

The hybrid service automatically falls back to Supabase on errors:

```typescript
try {
  // Try Python backend first
  const result = await pythonBackendAPI.getUserMeetings();
  return result.data.meetings;
} catch (error) {
  console.warn('Python backend failed, falling back to Supabase:', error);
  // Fall back to Supabase
  return await supabaseCalendarService.getUserMeetings();
}
```

### 2. Error Monitoring

Monitor backend health:

```typescript
const { status } = usePythonBackend();

useEffect(() => {
  if (status.error) {
    // Log error or show notification
    console.error('Python backend error:', status.error);
  }
}, [status.error]);
```

## Performance Optimization

### 1. Connection Pooling

The Python backend maintains connection pools for optimal performance.

### 2. Caching

Implement caching for frequently accessed data:

```typescript
// Cache backend status
const { status } = usePythonBackend();

// Cache feature availability
const featureCache = useMemo(() => ({
  calendar: isFeatureEnabled('calendar'),
  documents: isFeatureEnabled('documents'),
  // ... other features
}), [status.isConnected]);
```

### 3. Batch Operations

Use batch endpoints when available:

```typescript
// Batch document operations
const documents = await pythonBackendAPI.getDocuments(undefined, 100, 0);
```

## Deployment Considerations

### 1. Environment Variables

Ensure all required environment variables are set:

```bash
# Frontend
VITE_PYTHON_BACKEND_URL=https://your-backend.com
VITE_ENABLE_PYTHON_BACKEND=true

# Backend
WEBHOOK_BASE_URL=https://your-backend.com
CORS_ORIGINS=https://your-frontend.com
```

### 2. CORS Configuration

Configure CORS in the Python backend:

```python
# backend/app/core/config.py
cors_origins: List[str] = Field(
    default=["http://localhost:3000", "https://your-frontend.com"], 
    env="CORS_ORIGINS"
)
```

### 3. Health Checks

Monitor backend health in production:

```typescript
// Periodic health checks
useEffect(() => {
  const interval = setInterval(() => {
    checkConnection();
  }, 5 * 60 * 1000); // Every 5 minutes
  
  return () => clearInterval(interval);
}, [checkConnection]);
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Check `CORS_ORIGINS` configuration
2. **Authentication Failures**: Verify JWT token handling
3. **Connection Timeouts**: Adjust timeout values
4. **Webhook Failures**: Check `WEBHOOK_BASE_URL` configuration

### Debug Steps

1. Check Python backend status in UI
2. Run integration tests
3. Check browser console for errors
4. Verify environment variables
5. Test backend health endpoint directly

### Logs

Enable detailed logging:

```bash
# Backend
LOG_LEVEL=DEBUG

# Frontend
VITE_ENABLE_DEBUG_MODE=true
```

## Future Enhancements

### 1. Service Discovery

Implement automatic service discovery for microservices.

### 2. Load Balancing

Add load balancing between multiple backend instances.

### 3. Circuit Breaker

Implement circuit breaker pattern for better fault tolerance.

### 4. Metrics Collection

Add comprehensive metrics and monitoring.

## Conclusion

The Python backend frontend integration provides a robust, scalable foundation for BeSunny.ai. The hybrid approach ensures reliability while enabling new features and improved performance. The integration is designed to be transparent to end users while providing developers with powerful tools for monitoring and debugging.

For questions or issues, refer to the integration test component or check the backend status indicator in the UI.
