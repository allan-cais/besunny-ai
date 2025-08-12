# API Reference Documentation

## Overview

This document provides a comprehensive reference for all APIs, data models, and integration points in the BeSunny.ai platform. It covers both the current implementation and planned future endpoints.

## Base URLs

### Development
- **Frontend**: `http://localhost:5173`
- **Backend**: `http://localhost:8000`
- **Supabase**: `https://your-project.supabase.co`

### Production
- **Frontend**: `https://yourdomain.com`
- **Backend**: `https://api.yourdomain.com`
- **Supabase**: `https://your-project.supabase.co`

## Authentication

### JWT Token Format
```typescript
interface JWTPayload {
  sub: string;           // User ID
  email: string;         // User email
  exp: number;           // Expiration timestamp
  iat: number;           // Issued at timestamp
  aud: string;           // Audience
  role: string;          // User role
}
```

### Authentication Headers
```http
Authorization: Bearer <jwt_token>
```

### Token Refresh
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "string"
}
```

## Core API Endpoints

### User Management

#### Get Current User
```http
GET /api/v1/users/me
Authorization: Bearer <token>

Response:
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "username": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Update User Profile
```http
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "string",
  "username": "string"
}

Response:
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "username": "string",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Project Management

#### List Projects
```http
GET /api/v1/projects
Authorization: Bearer <token>
Query Parameters:
  - page: number (default: 1)
  - limit: number (default: 20)
  - search: string (optional)
  - status: string (optional)

Response:
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "status": "active|archived",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "document_count": 0,
      "meeting_count": 0
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### Create Project
```http
POST /api/v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "settings": {
    "auto_classification": true,
    "notification_preferences": {
      "email": true,
      "push": false
    }
  }
}

Response:
{
  "id": "string",
  "name": "string",
  "description": "string",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Get Project Details
```http
GET /api/v1/projects/{project_id}
Authorization: Bearer <token>

Response:
{
  "id": "string",
  "name": "string",
  "description": "string",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "statistics": {
    "document_count": 0,
    "meeting_count": 0,
    "total_storage": 0,
    "last_activity": "2024-01-01T00:00:00Z"
  },
  "settings": {
    "auto_classification": true,
    "notification_preferences": {
      "email": true,
      "push": false
    }
  }
}
```

### Document Management

#### List Documents
```http
GET /api/v1/documents
Authorization: Bearer <token>
Query Parameters:
  - project_id: string (optional)
  - type: string (optional)
  - status: string (optional)
  - page: number (default: 1)
  - limit: number (default: 20)
  - search: string (optional)
  - sort_by: string (default: "created_at")
  - sort_order: "asc"|"desc" (default: "desc")

Response:
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "type": "email|document|spreadsheet|presentation|image",
      "status": "pending|processing|classified|error",
      "project_id": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "metadata": {
        "file_size": 0,
        "mime_type": "string",
        "confidence_score": 0.95
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### Upload Document
```http
POST /api/v1/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
  - file: File
  - project_id: string (optional)
  - title: string (optional)
  - description: string (optional)

Response:
{
  "id": "string",
  "title": "string",
  "type": "string",
  "status": "pending",
  "project_id": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "upload_url": "string"
}
```

#### Get Document Details
```http
GET /api/v1/documents/{document_id}
Authorization: Bearer <token>

Response:
{
  "id": "string",
  "title": "string",
  "type": "string",
  "status": "string",
  "project_id": "string",
  "content": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "metadata": {
    "file_size": 0,
    "mime_type": "string",
    "confidence_score": 0.95,
    "extracted_text": "string",
    "language": "string"
  },
  "classification_result": {
    "document_type": "string",
    "confidence_score": 0.95,
    "categories": ["string"],
    "keywords": ["string"],
    "summary": "string"
  }
}
```

#### Classify Document
```http
POST /api/v1/documents/{document_id}/classify
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": "string",
  "force_reclassification": false
}

Response:
{
  "job_id": "string",
  "status": "queued",
  "estimated_completion": "2024-01-01T00:05:00Z"
}
```

### Meeting Management

#### List Meetings
```http
GET /api/v1/meetings
Authorization: Bearer <token>
Query Parameters:
  - project_id: string (optional)
  - status: string (optional)
  - date_from: string (optional)
  - date_to: string (optional)
  - page: number (default: 1)
  - limit: number (default: 20)

Response:
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "start_time": "2024-01-01T10:00:00Z",
      "end_time": "2024-01-01T11:00:00Z",
      "status": "scheduled|in_progress|completed|cancelled",
      "project_id": "string",
      "bot_status": "not_scheduled|scheduled|joined|transcribing|completed",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### Create Meeting
```http
POST /api/v1/meetings
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "string",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T11:00:00Z",
  "project_id": "string",
  "description": "string",
  "attendees": ["string"],
  "bot_enabled": true
}

Response:
{
  "id": "string",
  "title": "string",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T11:00:00Z",
  "status": "scheduled",
  "project_id": "string",
  "bot_status": "scheduled",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get Meeting Details
```http
GET /api/v1/meetings/{meeting_id}
Authorization: Bearer <token>

Response:
{
  "id": "string",
  "title": "string",
  "description": "string",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T11:00:00Z",
  "status": "string",
  "project_id": "string",
  "bot_status": "string",
  "transcript": "string",
  "transcript_summary": "string",
  "transcript_metadata": {
    "duration_seconds": 3600,
    "participant_count": 5,
    "word_count": 5000
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Chat & AI Assistant

#### List Chat Sessions
```http
GET /api/v1/chat/sessions
Authorization: Bearer <token>
Query Parameters:
  - project_id: string (optional)
  - page: number (default: 1)
  - limit: number (default: 20)

Response:
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "project_id": "string",
      "message_count": 0,
      "last_message_at": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### Create Chat Session
```http
POST /api/v1/chat/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "string",
  "project_id": "string"
}

Response:
{
  "id": "string",
  "title": "string",
  "project_id": "string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Send Message
```http
POST /api/v1/chat/sessions/{session_id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "string",
  "context": {
    "project_id": "string",
    "document_ids": ["string"],
    "meeting_ids": ["string"]
  }
}

Response:
{
  "id": "string",
  "session_id": "string",
  "role": "user|assistant",
  "content": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "metadata": {
    "tokens_used": 0,
    "processing_time_ms": 0
  }
}
```

#### Get Chat Messages
```http
GET /api/v1/chat/sessions/{session_id}/messages
Authorization: Bearer <token>
Query Parameters:
  - page: number (default: 1)
  - limit: number (default: 50)

Response:
{
  "data": [
    {
      "id": "string",
      "session_id": "string",
      "role": "user|assistant",
      "content": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "metadata": {
        "tokens_used": 0,
        "processing_time_ms": 0
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 100,
    "pages": 2
  }
}
```

## Data Models

### User Model
```typescript
interface User {
  id: string;
  email: string;
  full_name: string;
  username: string;
  avatar_url?: string;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    notifications: {
      email: boolean;
      push: boolean;
      slack: boolean;
    };
  };
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}
```

### Project Model
```typescript
interface Project {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'deleted';
  settings: {
    auto_classification: boolean;
    notification_preferences: {
      email: boolean;
      push: boolean;
      slack: boolean;
    };
    ai_features: {
      document_classification: boolean;
      meeting_transcription: boolean;
      chat_assistant: boolean;
    };
  };
  created_by: string;
  created_at: string;
  updated_at: string;
  last_activity_at?: string;
}
```

### Document Model
```typescript
interface Document {
  id: string;
  title: string;
  type: 'email' | 'document' | 'spreadsheet' | 'presentation' | 'image';
  status: 'pending' | 'processing' | 'classified' | 'error';
  content: string;
  project_id?: string;
  user_id: string;
  metadata: {
    file_size: number;
    mime_type: string;
    confidence_score?: number;
    extracted_text?: string;
    language?: string;
    page_count?: number;
    source: string;
  };
  classification_result?: {
    document_type: string;
    confidence_score: number;
    categories: string[];
    keywords: string[];
    summary?: string;
    entities?: Array<{
      name: string;
      type: string;
      confidence: number;
    }>;
  };
  created_at: string;
  updated_at: string;
  processed_at?: string;
}
```

### Meeting Model
```typescript
interface Meeting {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  project_id?: string;
  user_id: string;
  bot_status: 'not_scheduled' | 'scheduled' | 'joined' | 'transcribing' | 'completed';
  transcript?: string;
  transcript_summary?: string;
  transcript_metadata?: {
    duration_seconds: number;
    participant_count: number;
    word_count: number;
    segments: Array<{
      speaker: string;
      start_time: number;
      end_time: number;
      text: string;
    }>;
  };
  created_at: string;
  updated_at: string;
}
```

### Chat Message Model
```typescript
interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: {
    tokens_used: number;
    processing_time_ms: number;
    model_used: string;
    context: {
      project_id?: string;
      document_ids?: string[];
      meeting_ids?: string[];
    };
  };
  created_at: string;
}
```

## Error Handling

### Error Response Format
```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
    timestamp: string;
    request_id: string;
  };
}
```

### Common Error Codes
- `AUTHENTICATION_FAILED`: Invalid or expired token
- `AUTHORIZATION_FAILED`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid request data
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_SERVER_ERROR`: Unexpected server error

### Error Response Example
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid project data",
    "details": {
      "name": "Name is required",
      "description": "Description must be less than 500 characters"
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456789"
  }
}
```

## Rate Limiting

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limit Rules
- **Authentication endpoints**: 10 requests per minute
- **Document operations**: 100 requests per minute
- **Chat operations**: 50 requests per minute
- **General API**: 1000 requests per hour

## WebSocket Endpoints

### Real-time Updates
```typescript
// Connect to WebSocket
const ws = new WebSocket('wss://api.yourdomain.com/ws');

// Subscribe to document updates
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'documents',
  project_id: 'project_123'
}));

// Listen for updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Document update:', data);
};
```

### WebSocket Events
```typescript
interface WebSocketEvent {
  type: 'document_updated' | 'meeting_started' | 'chat_message' | 'classification_complete';
  data: any;
  timestamp: string;
}
```

## Integration Webhooks

### Webhook Configuration
```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-domain.com/webhook",
  "events": ["document.classified", "meeting.completed"],
  "secret": "webhook_secret"
}
```

### Webhook Payload Format
```typescript
interface WebhookPayload {
  event: string;
  timestamp: string;
  data: any;
  signature: string;
}
```

### Supported Webhook Events
- `document.uploaded`: New document uploaded
- `document.classified`: Document classification completed
- `meeting.scheduled`: New meeting scheduled
- `meeting.completed`: Meeting transcription completed
- `chat.message`: New chat message
- `project.created`: New project created

## SDKs and Libraries

### JavaScript/TypeScript SDK
```typescript
import { BeSunnyClient } from '@besunny/sdk';

const client = new BeSunnyClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.yourdomain.com'
});

// Use the client
const projects = await client.projects.list();
const document = await client.documents.upload(file, { projectId: 'project_123' });
```

### Python SDK
```python
from besunny import BeSunnyClient

client = BeSunnyClient(
    api_key="your_api_key",
    base_url="https://api.yourdomain.com"
)

# Use the client
projects = client.projects.list()
document = client.documents.upload(file, project_id="project_123")
```

## Testing

### Test Environment
- **Base URL**: `https://api-test.yourdomain.com`
- **Test Database**: Separate test instance
- **Mock Services**: OpenAI, Google APIs mocked

### Test Data
```typescript
// Test user credentials
const testUser = {
  email: 'test@example.com',
  password: 'testpassword123'
};

// Test project data
const testProject = {
  name: 'Test Project',
  description: 'Project for testing purposes'
};
```

## Support and Documentation

### API Documentation
- **Interactive Docs**: Swagger UI at `/docs`
- **OpenAPI Spec**: Available at `/openapi.json`
- **Postman Collection**: Importable collection file

### Support Channels
- **Developer Forum**: community.besunny.ai
- **Email Support**: api-support@besunny.ai
- **Documentation**: docs.besunny.ai
- **Status Page**: status.besunny.ai

This API reference provides comprehensive documentation for all endpoints, data models, and integration points in the BeSunny.ai platform. For additional examples and use cases, refer to the integration guides and SDK documentation.
