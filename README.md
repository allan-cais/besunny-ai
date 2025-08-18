# BeSunny.ai - Full Stack AI Platform

A comprehensive AI-powered platform that integrates Google services, AI orchestration, and intelligent document processing to streamline your workflow.

## 🚀 Features

- **🤖 AI Orchestration** - Intelligent document classification and processing
- **📅 Google Calendar Integration** - Smart scheduling and meeting management
- **📁 Google Drive Integration** - Automated file monitoring and processing
- **📧 Gmail Integration** - Intelligent email classification and organization
- **👥 Attendee Management** - Automated meeting bot integration
- **🔍 Vector Search** - Semantic document search and retrieval
- **📊 Real-time Analytics** - Live insights and performance monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React         │    │   Python        │    │   External      │
│   Frontend      │◄──►│   Backend       │◄──►│   Services      │
│   (TypeScript)  │    │   (FastAPI)     │    │   (Google, AI)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supabase      │    │   Redis         │    │   Vector DB     │
│   (Auth/DB)     │    │   (Cache/Tasks) │    │   (Pinecone)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Docker (optional, for local development)
- Supabase account
- Google Cloud Platform account
- OpenAI API key

### 1. Clone the Repository
```bash
git clone <repository-url>
cd besunny-ai
```

### 2. Frontend Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
# Edit .env with your API keys

# Start the backend
python start.py
```

### 4. Environment Configuration
Create `.env` files in both root and backend directories with:
- Supabase credentials
- Google OAuth credentials
- OpenAI API key
- Other service API keys

## 🔧 Development

### Frontend Development
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```

### Backend Development
```bash
cd backend
python start.py      # Start development server
pytest               # Run tests
black .              # Format code
isort .              # Sort imports
```

### Full Stack Development
```bash
# Start both frontend and backend
./start-fullstack.sh
```

## 📚 API Documentation

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🚀 Deployment

### Railway Deployment (Recommended)
```bash
# Deploy full stack to Railway
./deploy-railway-fullstack.sh
```

### Manual Deployment
```bash
# Build and deploy frontend
./deploy-frontend.sh

# Deploy backend
./deploy-railway-fullstack.sh
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t besunny-ai .
docker run -p 8000:8000 besunny-ai
```

## 🧪 Testing

```bash
# Frontend tests
npm test

# Backend tests
cd backend
pytest

# Full stack tests
./test-fullstack.sh
```

## 📁 Project Structure

```
besunny-ai/
├── src/                    # React frontend source
│   ├── components/         # React components
│   ├── pages/             # Page components
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility libraries
│   └── config/            # Configuration files
├── backend/                # Python backend
│   ├── app/               # FastAPI application
│   ├── services/          # Business logic services
│   ├── models/            # Data models
│   └── tests/             # Backend tests
├── supabase/               # Supabase configuration
├── database/               # Database migrations
└── docs/                   # Documentation
```

## 🔌 Integrations

- **Google Services**: Calendar, Drive, Gmail
- **AI Services**: OpenAI GPT, Vector embeddings
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth + Google OAuth
- **Caching**: Redis
- **Vector DB**: Pinecone

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is part of the BeSunny.ai platform.

## 🆘 Support

- **Documentation**: Check the `/docs` folder
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

---

**Built with ❤️ by the BeSunny.ai team**
