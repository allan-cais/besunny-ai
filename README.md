# Sunny AI - Intelligent Development Environment

A modern, intelligent development environment with an embedded AI assistant powered by n8n webhooks. **Fully client-side - perfect for Netlify deployment!**

## Features

- 🎨 **Modern UI**: Clean, monospace design with dark/light theme support
- 🤖 **AI Assistant**: Real-time chat with n8n webhook integration
- 🔄 **n8n Integration**: Direct webhook calls from the frontend
- 💾 **Local Storage**: Persistent chat history using browser storage
- 📱 **Responsive**: Works on desktop and mobile devices
- ⚡ **Netlify Ready**: No backend servers required

## Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd kirit-askuno
npm install
```

### 2. Environment Configuration

Copy `env.example` to `.env` and configure your n8n webhook URL:

```bash
cp env.example .env
```

Edit `.env`:
```env
VITE_N8N_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-rag-webhook
```

### 3. Start Development

```bash
npm run dev
```

Visit `http://localhost:5173` and click the chat button in the bottom-right corner.

## Project Structure

```
kirit-askuno/
├── src/
│   ├── components/
│   │   ├── AIAssistant.tsx    # AI Chat component (client-side)
│   │   └── ui/                # Shadcn UI components
│   ├── pages/
│   │   └── dashboard.tsx      # Main dashboard
│   └── ...
├── server/                    # Backend (optional, for development)
│   ├── index.ts              # Express server (not needed for production)
│   ├── services/
│   │   └── supabase.ts       # Database service (optional)
│   └── ...
└── ...
```

## AI Assistant Features

### Direct n8n Integration
- Calls n8n webhook directly from the browser
- No backend server required
- Handles JSON responses with `output` field
- Graceful error handling

### Message Management
- Local storage for chat history persistence
- Session management
- Automatic message loading on page refresh

### Netlify Deployment Ready
- Fully static - no server-side code needed
- Environment variables for configuration
- Works with Netlify's serverless functions (if needed)

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Required: Your n8n webhook URL
VITE_N8N_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-rag-webhook

# Optional: Add any other frontend environment variables
# VITE_APP_NAME=Sunny AI
# VITE_DEBUG=true
```

### n8n Webhook Setup

Your n8n workflow should:

1. Accept POST requests with the message data
2. Return a JSON response with an `output` field:

```json
{
  "output": "Hello! I received your message and here's my response."
}
```

**Expected Request Format:**
```json
{
  "message": "User message",
  "sessionId": "session-id",
  "messageId": "message-id",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "metadata": {
    "userAgent": "Mozilla/5.0...",
    "source": "frontend"
  }
}
```

## Development

### Available Scripts

```bash
# Development
npm run dev              # Start development server
npm run build           # Build for production
npm run preview         # Preview production build

# Linting
npm run lint            # Run ESLint
```

### Local Development with Backend (Optional)

If you want to test with a local backend during development:

```bash
# Terminal 1 - Frontend
npm run dev

# Terminal 2 - Backend (optional)
cd server && npm run dev

# Terminal 3 - Mock n8n (optional)
cd server && npm run mock-n8n
```

## Deployment

### Netlify (Recommended)

1. **Connect your repository** to Netlify
2. **Set build settings**:
   - Build command: `npm run build`
   - Publish directory: `dist`
3. **Add environment variables** in Netlify dashboard:
   - `VITE_N8N_WEBHOOK_URL`: Your n8n webhook URL
4. **Deploy!**

### Vercel

1. **Connect your repository** to Vercel
2. **Add environment variables**:
   - `VITE_N8N_WEBHOOK_URL`: Your n8n webhook URL
3. **Deploy!**

### Manual Deployment

```bash
npm run build
# Upload the `dist/` folder to your hosting provider
```

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure your n8n webhook allows requests from your domain
   - Check n8n CORS settings

2. **Webhook Not Responding**:
   - Verify the webhook URL is correct
   - Check n8n workflow is active
   - Test webhook directly with curl

3. **Environment Variables Not Working**:
   - Ensure variables start with `VITE_`
   - Rebuild after changing environment variables
   - Check Netlify/Vercel environment variable settings

### Debug Mode

Enable debug logging by setting:
```env
VITE_DEBUG=true
```

## Architecture

### Client-Side Only
- ✅ No backend server required
- ✅ Works with static hosting (Netlify, Vercel, etc.)
- ✅ Direct n8n webhook integration
- ✅ Local storage for persistence
- ✅ Environment variable configuration

### Optional Backend (Development)
- 🔧 Express server for local development
- 🔧 Supabase integration for production database
- 🔧 Mock n8n webhook for testing
- 🔧 Advanced features like streaming responses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
