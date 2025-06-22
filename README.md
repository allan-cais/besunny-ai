# Sunny AI - Intelligent Development Environment

A modern, intelligent development environment with an embedded AI assistant powered by n8n webhooks and real-time streaming chat.

## Features

- 🎨 **Modern UI**: Clean, monospace design with dark/light theme support
- 🤖 **AI Assistant**: Real-time chat with streaming responses
- 🔄 **n8n Integration**: Flexible backend powered by n8n workflows
- 💾 **Message Storage**: Persistent chat history with Supabase
- 📱 **Responsive**: Works on desktop and mobile devices
- ⚡ **Real-time**: Server-Sent Events for smooth streaming

## Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd kirit-askuno
npm install
```

### 2. Backend Setup

```bash
cd server
npm install
cp env.example .env
```

Edit `server/.env` and configure:
```env
N8N_WEBHOOK_URL=http://localhost:3002/webhook/chat  # For testing with mock
PORT=3001
```

### 3. Start Development Servers

**Option A: Full Stack (Recommended)**
```bash
npm run dev:full
```

**Option B: Separate Terminals**
```bash
# Terminal 1 - Frontend
npm run dev

# Terminal 2 - Backend
cd server && npm run dev

# Terminal 3 - Mock n8n (for testing)
cd server && npm run mock-n8n
```

### 4. Test the Setup

Visit `http://localhost:5173` and click the chat button in the bottom-right corner.

## Project Structure

```
kirit-askuno/
├── src/
│   ├── components/
│   │   ├── AIAssistant.tsx    # AI Chat component
│   │   └── ui/                # Shadcn UI components
│   ├── pages/
│   │   └── dashboard.tsx      # Main dashboard
│   └── ...
├── server/
│   ├── index.ts              # Main Express server
│   ├── services/
│   │   └── supabase.ts       # Database service
│   ├── mock-n8n.js           # Mock webhook for testing
│   └── test-api.js           # API test script
└── ...
```

## AI Assistant Features

### Real-time Streaming
- Server-Sent Events (SSE) for smooth text streaming
- Preserves scroll position during streaming
- Graceful error handling and fallbacks

### Message Management
- Unique session IDs for conversation tracking
- Message persistence with Supabase
- Chat history retrieval

### n8n Integration
- Flexible webhook-based architecture
- Support for both streaming and non-streaming responses
- Easy integration with any LLM via n8n workflows

## API Endpoints

### POST /api/chat
Send a message and receive streaming response.

```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello, how are you?',
    sessionId: 'user-session-123',
    messageId: 'msg-456'
  })
});

// Handle streaming response
const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  // Process streaming data
}
```

### GET /api/chat/:sessionId
Retrieve chat history for a session.

### GET /api/health
Health check endpoint.

## Configuration

### Environment Variables

**Frontend** (Vite automatically loads `.env`):
```env
VITE_API_URL=http://localhost:3001
```

**Backend** (`server/.env`):
```env
PORT=3001
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/chat
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Supabase Setup (Optional)

If using Supabase for message storage:

```sql
-- Create chat_messages table
CREATE TABLE chat_messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

## Development

### Available Scripts

```bash
# Frontend
npm run dev              # Start frontend only
npm run build           # Build for production
npm run preview         # Preview production build

# Backend
npm run start:server    # Start production backend
cd server && npm run dev # Start development backend

# Full Stack
npm run dev:full        # Start both frontend and backend
npm run build:all       # Build both frontend and backend

# Testing
cd server && npm run mock-n8n  # Start mock n8n webhook
cd server && npm run test      # Test API endpoints
```

### Testing

1. **Start mock n8n webhook**:
   ```bash
   cd server && npm run mock-n8n
   ```

2. **Test API endpoints**:
   ```bash
   cd server && npm run test
   ```

3. **Manual testing**:
   - Open `http://localhost:5173`
   - Click the chat button
   - Send a message and watch the streaming response

## Production Deployment

### Frontend (Netlify/Vercel)
```bash
npm run build
# Deploy dist/ folder
```

### Backend (Railway/Render/Heroku)
```bash
cd server
npm run build
npm start
```

### Environment Variables for Production
- Set `N8N_WEBHOOK_URL` to your production n8n instance
- Configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` for production database
- Update `VITE_API_URL` to point to your production backend

## Troubleshooting

### Common Issues

1. **Chat not working**:
   - Check if backend is running on port 3001
   - Verify n8n webhook URL is correct
   - Check browser console for errors

2. **Streaming not working**:
   - Ensure n8n supports streaming responses
   - Check CORS settings
   - Verify proxy configuration in `vite.config.ts`

3. **Supabase connection issues**:
   - Verify credentials in `server/.env`
   - Check if tables exist
   - Ensure proper permissions

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=true
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
