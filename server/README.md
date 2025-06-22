# Sunny AI Backend Server

This is the backend server for the Sunny AI chat application. It provides a REST API that integrates with n8n webhooks and Supabase for message storage.

## Features

- **Real-time Chat API**: Handles streaming responses from n8n webhooks
- **Message Storage**: Saves chat messages to Supabase
- **Session Management**: Tracks conversation sessions
- **Error Handling**: Graceful error handling and fallbacks

## Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Environment Configuration**
   Copy `env.example` to `.env` and configure your environment variables:
   ```bash
   cp env.example .env
   ```

   Required environment variables:
   - `N8N_WEBHOOK_URL`: Your n8n webhook URL for chat processing
   - `PORT`: Server port (default: 3001)

   Optional environment variables:
   - `SUPABASE_URL`: Supabase project URL for message storage
   - `SUPABASE_ANON_KEY`: Supabase anonymous key

3. **Development**
   ```bash
   npm run dev
   ```

4. **Production Build**
   ```bash
   npm run build
   npm start
   ```

## API Endpoints

### POST /api/chat
Send a chat message and receive a streaming response.

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "sessionId": "user-session-123",
  "messageId": "msg-456"
}
```

**Response:** Server-Sent Events (SSE) stream with the AI response.

### GET /api/chat/:sessionId
Get chat history for a session.

**Query Parameters:**
- `limit`: Number of messages to return (default: 50)

**Response:**
```json
{
  "messages": [
    {
      "id": "msg-123",
      "sessionId": "user-session-123",
      "role": "user",
      "content": "Hello",
      "createdAt": "2024-01-01T00:00:00.000Z"
    }
  ]
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "supabase": "configured"
}
```

## N8N Integration

The server expects your n8n webhook to:

1. Accept POST requests with the message data
2. Return either:
   - A streaming response (preferred)
   - A complete response that will be simulated as streaming

**Expected Request Format:**
```json
{
  "message": "User message",
  "sessionId": "session-id",
  "messageId": "message-id",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "metadata": {
    "userAgent": "Mozilla/5.0...",
    "ip": "127.0.0.1"
  }
}
```

## Supabase Setup

If you want to use Supabase for message storage, create the following tables:

### chat_messages
```sql
CREATE TABLE chat_messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

### chat_sessions (optional)
```sql
CREATE TABLE chat_sessions (
  id TEXT PRIMARY KEY,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Development

The server is built with:
- **Express.js**: Web framework
- **TypeScript**: Type safety
- **CORS**: Cross-origin resource sharing
- **Supabase**: Database integration

## Troubleshooting

1. **N8N Webhook Not Responding**
   - Check your n8n webhook URL
   - Verify n8n workflow is active
   - Check n8n logs for errors

2. **Supabase Connection Issues**
   - Verify your Supabase credentials
   - Check if tables exist
   - Ensure proper permissions

3. **Streaming Not Working**
   - Check if n8n supports streaming responses
   - Verify CORS settings
   - Check browser console for errors 