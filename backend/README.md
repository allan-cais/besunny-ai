# BeSunny.ai Python Backend

A modern, FastAPI-based backend service for the BeSunny.ai platform, providing AI orchestration, user management, and comprehensive API endpoints.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip or poetry
- Redis (optional, for caching and background tasks)
- PostgreSQL (optional, for persistent storage)

### Installation

1. **Clone and navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start the server:**
   ```bash
   python start.py
   ```

The server will start on `http://localhost:8000` by default.

## 🏗️ Architecture

### Core Components
- **FastAPI Application** (`app/main.py`) - Main application entry point
- **API Gateway** (`app/core/api_gateway.py`) - Centralized API management
- **Service Registry** (`app/core/service_registry.py`) - Service discovery and management
- **Database Layer** (`app/core/database/`) - Database connection and models
- **Redis Manager** (`app/core/redis_manager.py`) - Redis connection and caching

### API Structure
- **v1 API** (`app/api/v1/`) - Main API endpoints
- **WebSocket Support** (`app/api/websockets/`) - Real-time communication
- **AI Services** (`app/services/ai/`) - AI orchestration and services
- **Authentication** (`app/services/auth/`) - OAuth and user management
- **Calendar Integration** (`app/services/calendar/`) - Google Calendar integration
- **Drive Integration** (`app/services/drive/`) - Google Drive file management
- **Email Services** (`app/services/email/`) - Gmail integration and processing

## 🔧 Configuration

### Environment Variables
Key environment variables (see `env.example` for complete list):

- `ENVIRONMENT` - Application environment (development/production)
- `DEBUG` - Enable debug mode
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key

### Database Setup
The backend supports both PostgreSQL (via SQLAlchemy) and Supabase. Database initialization is handled automatically on startup.

## 📚 API Documentation

Once the server is running, you can access:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`
- **Health check**: `http://localhost:8000/health`

## 🧪 Testing

Run the test suite:
```bash
pytest
```

## 🚀 Deployment

### Railway Deployment
The backend is configured for Railway deployment with the `start.py` script as the entry point.

### Docker Deployment
Use the provided Dockerfile for containerized deployment:
```bash
# From project root
docker build -f Dockerfile.backend -t besunny-backend:latest .
docker run -p 8000:8000 besunny-backend:latest

# Or use Docker Compose (recommended)
docker-compose up backend
```

## 🔍 Monitoring

The backend includes comprehensive logging and monitoring:
- Structured logging with structlog
- Health check endpoints
- Performance metrics
- Error tracking and reporting

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass before submitting

## 📄 License

This project is part of the BeSunny.ai platform.
