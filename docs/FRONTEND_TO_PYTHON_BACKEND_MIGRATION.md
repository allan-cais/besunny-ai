# Frontend to Python Backend Migration Guide

## Overview

This document outlines the migration process from Supabase edge functions to the new Python backend services for the BeSunny.ai frontend application.

## Migration Status

- ✅ **Completed**: Core service layer creation
- ✅ **Completed**: Python backend services wrapper
- ✅ **Completed**: New React hook (usePythonBackend)
- ✅ **Completed**: Configuration management
- ✅ **Completed**: CreateProjectDialog migration
- ✅ **Completed**: UsernameSetupDialog migration
- ✅ **Completed**: Integrations page migration
- ✅ **Completed**: Attendee service migration
- ✅ **Completed**: API keys service migration
- 🔄 **In Progress**: Component-by-component migration
- ⏳ **Pending**: Testing and validation
- ⏳ **Pending**: Performance optimization

## What Has Been Migrated

### 1. Core Infrastructure

- **Python Backend Services** (`src/lib/python-backend-services.ts`)
  - Comprehensive service layer replacing all Supabase edge function calls
  - Authentication, projects, documents, attendee, calendar, drive, emails, AI services
  - Health checks and microservices status

- **Python Backend Hook** (`src/hooks/use-python-backend.ts`)
  - React hook providing Python backend functionality
  - Automatic authentication token management
  - Fallback to Supabase for unsupported operations

- **Configuration Management** (`src/config/python-backend-config.ts`)
  - Centralized Python backend configuration
  - Environment variable management
  - Service endpoint definitions

### 2. Components Migrated

- **CreateProjectDialog**: Now uses Python backend for project creation and AI processing
- **UsernameSetupDialog**: Uses Python backend for username setup
- **Integrations Page**: Uses Python backend for Google OAuth
- **Attendee Service**: Uses Python backend for bot management
- **API Keys Service**: Uses Python backend for bot deployment

### 3. Services Migrated

- **Project Management**: Create, read, update, delete projects
- **Document Management**: Create, read, update, delete documents
- **AI Services**: Document classification, analysis, project onboarding
- **Attendee Services**: Bot deployment, status checking, transcript retrieval
- **Calendar Services**: Event management, sync, webhook management
- **Drive Services**: File monitoring, subscription management
- **Email Services**: Processing, Gmail watch setup
- **User Services**: Profile management, username setup

## Migration Process

### Phase 1: Infrastructure Setup ✅

1. **Created Python Backend Services Layer**
   - Comprehensive service wrapper for all backend operations
   - Consistent API response format
   - Error handling and retry logic

2. **Created Python Backend Hook**
   - React hook for Python backend integration
   - Automatic authentication management
   - Loading and error state management

3. **Updated Configuration**
   - Environment variable management
   - Service endpoint definitions
   - Feature flags and health checks

### Phase 2: Component Migration 🔄

1. **Updated CreateProjectDialog**
   - Replaced Supabase edge function calls with Python backend
   - Updated project creation flow
   - Integrated AI processing via Python backend

2. **Updated UsernameSetupDialog**
   - Replaced username setup edge function
   - Uses Python backend user service

3. **Updated Integrations Page**
   - Replaced Google OAuth edge function
   - Uses Python backend authentication service

4. **Updated Service Files**
   - Attendee service now uses Python backend
   - API keys service updated for bot deployment

### Phase 3: Testing and Validation ⏳

1. **Unit Testing**
   - Test all migrated components
   - Validate Python backend service calls
   - Error handling verification

2. **Integration Testing**
   - End-to-end workflow testing
   - Authentication flow validation
   - Data consistency verification

3. **Performance Testing**
   - Response time comparison
   - Error rate monitoring
   - Resource usage analysis

### Phase 4: Optimization and Cleanup ⏳

1. **Performance Optimization**
   - Caching strategies
   - Request batching
   - Connection pooling

2. **Code Cleanup**
   - Remove unused Supabase edge function code
   - Update documentation
   - Clean up environment variables

## Environment Variables

### Required for Python Backend

```bash
# Python Backend Configuration
VITE_PYTHON_BACKEND_URL=http://localhost:8000
VITE_PYTHON_BACKEND_TIMEOUT=30000
VITE_PYTHON_BACKEND_RETRIES=3
VITE_PYTHON_BACKEND_RETRY_DELAY=1000
VITE_ENABLE_PYTHON_BACKEND=true

# Supabase (still required for authentication and database)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Optional Configuration

```bash
# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_ERROR_REPORTING=false
VITE_ENABLE_DEBUG_MODE=false

# Polling Configuration
VITE_POLLING_INTERVAL_MS=30000
VITE_MAX_RETRIES=3
VITE_POLLING_RETRY_DELAY_MS=1000

# UI Limits
VITE_MAX_DOCUMENTS_PER_PAGE=50
VITE_MAX_MEETINGS_PER_PAGE=100
VITE_MAX_CHAT_MESSAGES_PER_PAGE=100
```

## API Endpoint Mapping

### Authentication

| Supabase Edge Function | Python Backend Endpoint |
|------------------------|-------------------------|
| `/functions/v1/exchange-google-token` | `/api/v1/auth/google/oauth/callback` |
| `/functions/v1/refresh-google-token` | `/api/v1/auth/google/oauth/refresh` |

### Projects

| Supabase Edge Function | Python Backend Endpoint |
|------------------------|-------------------------|
| `/functions/v1/project-onboarding-ai` | `/api/v1/ai/projects/onboarding` |
| N/A | `/api/v1/projects` (CRUD operations) |

### Attendee Services

| Supabase Edge Function | Python Backend Endpoint |
|------------------------|-------------------------|
| `/functions/v1/attendee-proxy/send-bot` | `/api/v1/attendee/send-bot` |
| `/functions/v1/attendee-service/*` | `/api/v1/attendee/*` |

### User Services

| Supabase Edge Function | Python Backend Endpoint |
|------------------------|-------------------------|
| `/functions/v1/set-username` | `/api/v1/user/set-username` |

## Usage Examples

### Using Python Backend Services

```typescript
import { pythonBackendServices } from '../lib/python-backend-services';

// Set authentication token
pythonBackendServices.setAuthToken(accessToken);

// Create a project
const project = await pythonBackendServices.createProject({
  name: 'My Project',
  description: 'Project description',
  status: 'active'
});

// Process project onboarding with AI
const aiResult = await pythonBackendServices.processProjectOnboarding(payload);
```

### Using Python Backend Hook

```typescript
import { usePythonBackend } from '../hooks/use-python-backend';

const MyComponent = () => {
  const { 
    createProject, 
    getProjects, 
    isLoading, 
    error, 
    isBackendAvailable 
  } = usePythonBackend();

  const handleCreateProject = async () => {
    if (!isBackendAvailable) {
      console.warn('Python backend not available');
      return;
    }

    const project = await createProject(projectData);
    // Handle result
  };

  // Component logic
};
```

## Fallback Strategy

The migration includes a fallback strategy to ensure the application continues to work even when the Python backend is unavailable:

1. **Health Check**: Automatic backend availability detection
2. **Graceful Degradation**: Fallback to Supabase for unsupported operations
3. **Error Handling**: Clear error messages and fallback options
4. **Feature Flags**: Configurable feature enablement

## Testing Checklist

### Component Testing

- [ ] CreateProjectDialog works with Python backend
- [ ] UsernameSetupDialog works with Python backend
- [ ] Integrations page works with Python backend
- [ ] All forms submit correctly
- [ ] Error handling works as expected
- [ ] Loading states display correctly

### Service Testing

- [ ] Python backend services respond correctly
- [ ] Authentication token management works
- [ ] Error handling and retries work
- [ ] Health checks function properly
- [ ] All API endpoints are accessible

### Integration Testing

- [ ] End-to-end project creation flow
- [ ] Google OAuth integration
- [ ] Bot deployment workflow
- [ ] Document processing pipeline
- [ ] User management operations

## Troubleshooting

### Common Issues

1. **Python Backend Not Available**
   - Check backend service is running
   - Verify environment variables
   - Check network connectivity

2. **Authentication Errors**
   - Verify Supabase session is valid
   - Check token expiration
   - Validate backend authentication configuration

3. **API Endpoint Errors**
   - Verify endpoint URLs are correct
   - Check backend service status
   - Validate request payload format

### Debug Mode

Enable debug mode to see detailed logging:

```bash
VITE_ENABLE_DEBUG_MODE=true
```

### Health Check

Check backend health manually:

```typescript
import { pythonBackendServices } from '../lib/python-backend-services';

const health = await pythonBackendServices.checkHealth();
console.log('Backend health:', health);
```

## Next Steps

1. **Complete Component Migration**
   - Migrate remaining components to use Python backend
   - Update all service calls
   - Remove Supabase edge function dependencies

2. **Performance Optimization**
   - Implement caching strategies
   - Optimize request patterns
   - Monitor performance metrics

3. **Feature Enhancement**
   - Add new Python backend features
   - Implement real-time updates
   - Add advanced AI capabilities

4. **Documentation Updates**
   - Update API documentation
   - Create user guides
   - Document new features

## Support

For questions or issues during migration:

1. Check this migration guide
2. Review Python backend API documentation
3. Check backend service logs
4. Contact development team

## Conclusion

The migration to Python backend services provides:

- **Better Performance**: Direct API calls instead of edge function overhead
- **Enhanced Features**: Access to advanced AI and microservices
- **Improved Reliability**: Better error handling and retry logic
- **Scalability**: Microservices architecture for future growth
- **Maintainability**: Centralized service management

The migration is designed to be gradual and safe, with fallback options ensuring the application remains functional throughout the process.
