# OpenAI Agentic SDK Integration

## Overview

This implementation replaces the external n8n webhook with an internal OpenAI agentic SDK integration that processes project onboarding data directly within the app using a Supabase Edge Function.

## Architecture

### Before (n8n Webhook)
```
User Input → CreateProjectDialog → Supabase Project Creation → n8n Webhook → OpenAI API → Database Update
```

### After (Internal AI Integration)
```
User Input → CreateProjectDialog → Supabase Project Creation → Edge Function → OpenAI API → Database Update → Real-time UI Update
```

## Components

### 1. Edge Function: `project-onboarding-ai`

**Location**: `supabase/functions/project-onboarding-ai/`

**Purpose**: Processes project onboarding data using OpenAI's agentic SDK and returns structured metadata.

**Key Features**:
- Uses OpenAI GPT-4o-mini model
- Processes the same JSON payload as the previous n8n workflow
- Updates both `projects` and `project_metadata` tables
- Returns structured metadata for immediate use

**Dependencies**:
```json
{
  "imports": {
    "openai": "npm:openai@4.28.0"
  }
}
```

### 2. Frontend Integration

**Updated Components**:
- `CreateProjectDialog.tsx` - Calls edge function instead of webhook
- `project.tsx` - Displays AI-generated metadata with real-time updates
- `supabase.ts` - Added `processProjectOnboarding` helper method

**Real-time Features**:
- Live AI processing status indicator
- Automatic UI updates when AI processing completes
- Displays structured metadata (categories, tags, keywords, etc.)

## Implementation Details

### Edge Function Flow

1. **Authentication**: Validates JWT token from frontend
2. **Input Processing**: Parses project onboarding summary JSON
3. **AI Processing**: Sends structured prompt to OpenAI GPT-4o-mini
4. **Response Parsing**: Extracts JSON metadata from AI response
5. **Database Update**: Updates project with AI-generated metadata
6. **Response**: Returns success/error status to frontend

### AI Prompt Structure

The edge function uses a comprehensive prompt that:

1. **Defines the AI's role** as an intelligent assistant for structuring project metadata
2. **Specifies input format** with all project onboarding fields
3. **Defines output schema** matching the database structure
4. **Provides context** about the data's use in classification agents
5. **Includes fallback instructions** for missing or unclear data

### Database Schema

The AI generates metadata for these fields:

```sql
-- Core project fields
name (TEXT)
description (TEXT)
status (TEXT) -- default: "in_progress"
notes (TEXT)

-- Classification metadata
normalized_tags (TEXT[]) -- lowercased, snake_case keywords
categories (TEXT[]) -- inferred e.g. ["Video Production"]
reference_keywords (TEXT[]) -- key phrases for classification

-- Advanced metadata
entity_patterns (JSONB) -- people, locations, emails
classification_signals (JSONB) -- shoot dates, location, deliverable types

-- Tracking fields
pinecone_document_count (INTEGER, default 0)
last_classification_at (TIMESTAMP, null)
classification_feedback (JSONB, default null)
```

### Real-time Updates

The project page implements real-time updates using Supabase's real-time subscriptions:

1. **Initial Load**: Fetches project with all metadata fields
2. **AI Processing Check**: Shows loading indicator if metadata is missing
3. **Real-time Subscription**: Listens for project updates
4. **Automatic UI Update**: Updates display when AI processing completes

## Deployment

### Prerequisites

1. **Supabase CLI**: `npm install -g supabase`
2. **OpenAI API Key**: Valid API key with GPT-4o-mini access
3. **Supabase Project**: Configured with edge functions enabled

### Deployment Steps

1. **Deploy Edge Function**:
   ```bash
   ./deploy-ai-function.sh
   ```

2. **Set OpenAI API Key**:
   ```bash
   supabase secrets set OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Verify Deployment**:
   ```bash
   supabase functions list
   ```

### Environment Variables

**Required in Supabase**:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for database access

## Usage

### Creating a New Project

1. **User clicks "New Project"** in navigation sidebar
2. **Project onboarding wizard** collects structured data
3. **Project is created** in Supabase immediately
4. **User is redirected** to project page
5. **AI processing starts** in background
6. **Real-time updates** show AI processing status
7. **AI metadata appears** automatically when complete

### Project Page Features

- **AI Processing Status**: Shows loading indicator during processing
- **AI Project Summary**: Displays structured metadata when available
- **Categories**: High-level project classifications
- **Normalized Tags**: Standardized keywords for classification
- **Reference Keywords**: Key phrases for content matching
- **Entity Patterns**: People, locations, and contact information
- **Classification Signals**: Advanced metadata for AI classification

## Error Handling

### Edge Function Errors

- **Authentication failures**: Returns 400 with clear error message
- **OpenAI API errors**: Logs error and returns failure status
- **Database errors**: Logs error and returns failure status
- **Invalid input**: Validates required fields and returns error

### Frontend Error Handling

- **Network errors**: Graceful degradation - project creation continues
- **AI processing failures**: Logged but don't block project creation
- **Real-time connection issues**: Fallback to manual refresh

## Monitoring

### Function Logs

```bash
supabase functions logs project-onboarding-ai
```

### Key Metrics to Monitor

- **Function execution time**: Should be < 10 seconds
- **OpenAI API response time**: Should be < 5 seconds
- **Error rates**: Should be < 5%
- **Database update success rate**: Should be > 95%

## Testing

### Manual Testing

1. **Create new project** through onboarding wizard
2. **Verify project creation** in database
3. **Check AI processing** in function logs
4. **Verify metadata** appears on project page
5. **Test real-time updates** by monitoring network

### Automated Testing

```bash
# Test edge function directly
curl -X POST https://your-project.supabase.co/functions/v1/project-onboarding-ai \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-uuid",
    "user_id": "test-user-uuid",
    "summary": {
      "project_name": "Test Project",
      "overview": "A test project for validation",
      "keywords": ["test", "validation"],
      "deliverables": "Test deliverables",
      "contacts": {
        "internal_lead": "Test Lead",
        "agency_lead": "Test Agency",
        "client_lead": "Test Client"
      },
      "shoot_date": "2024-01-01",
      "location": "Test Location",
      "references": "Test references"
    }
  }'
```

## Benefits

### Performance Improvements

- **Faster response times**: No external webhook delays
- **Reduced latency**: Direct API calls within Supabase infrastructure
- **Better reliability**: No dependency on external n8n service

### User Experience

- **Immediate feedback**: Real-time processing status
- **Seamless integration**: No external service dependencies
- **Better error handling**: Graceful degradation for failures

### Development Benefits

- **Simplified architecture**: One less external dependency
- **Better debugging**: Direct access to function logs
- **Easier testing**: Can test edge function directly
- **Cost optimization**: No external webhook service costs

## Future Enhancements

### Potential Improvements

1. **Caching**: Cache AI responses for similar projects
2. **Batch Processing**: Process multiple projects simultaneously
3. **Custom Models**: Fine-tune models for specific project types
4. **Advanced Classification**: Implement more sophisticated classification logic
5. **Performance Monitoring**: Add detailed metrics and alerting

### Scalability Considerations

- **Rate Limiting**: Implement OpenAI API rate limiting
- **Queue System**: Add background job queue for high-volume processing
- **Caching Layer**: Add Redis caching for frequently accessed metadata
- **Load Balancing**: Distribute processing across multiple function instances

## Troubleshooting

### Common Issues

1. **Function not deploying**: Check Supabase CLI version and project configuration
2. **OpenAI API errors**: Verify API key and quota limits
3. **Database update failures**: Check RLS policies and service role permissions
4. **Real-time not working**: Verify real-time is enabled in Supabase dashboard

### Debug Commands

```bash
# Check function status
supabase functions list

# View function logs
supabase functions logs project-onboarding-ai --follow

# Test function locally
supabase functions serve project-onboarding-ai

# Check database schema
supabase db diff
```

## Migration from n8n

### What Changed

- **Removed**: n8n webhook dependency
- **Added**: Supabase edge function
- **Enhanced**: Real-time UI updates
- **Improved**: Error handling and user feedback

### Migration Steps

1. **Deploy new edge function**
2. **Update frontend code** (already done)
3. **Test new flow** with sample projects
4. **Monitor performance** and error rates
5. **Remove n8n webhook** once confirmed working

### Rollback Plan

If issues arise, you can quickly rollback by:

1. **Reverting frontend changes** to use n8n webhook
2. **Keeping edge function** for future use
3. **No database changes** required for rollback 