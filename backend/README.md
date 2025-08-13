# BeSunny.ai Python Backend

A robust Python backend service for the BeSunny.ai ecosystem, providing enhanced AI capabilities, data processing, and microservice architecture.

## 🚀 Features

- **FastAPI-based REST API** with async support
- **AI Document Classification** using OpenAI GPT models
- **Google Services Integration** (Drive, Calendar, Gmail)
- **Vector Embeddings** with Pinecone for RAG capabilities
- **Real-time Updates** via WebSocket connections
- **Background Processing** with Celery task queue
- **Supabase Integration** for database and authentication
- **Attendee Meeting Bot** integration
- **Comprehensive Monitoring** and health checks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Python API    │    │   External      │
│   (React/TS)    │◄──►│   Gateway       │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supabase      │    │   Python        │    │   AI/ML         │
│   (Auth/DB)     │    │   Microservices │    │   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Supabase account and project
- OpenAI API key
- Google Cloud Platform account
- Pinecone account

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd python-backend
```

### 2. Set Up Environment Variables

```bash
cp env.example .env
# Edit .env with your actual values
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```

### 5. Run Locally

```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Run the application
uvicorn app.main:app --reload
```

## 🔧 Configuration

### Environment Variables

Key configuration variables in `.env`:

- **Database**: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- **AI Services**: `OPENAI_API_KEY`, `PINECONE_API_KEY`
- **Google APIs**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- **Security**: `SECRET_KEY`, `ALGORITHM`

### Database Setup

The application automatically creates database tables on startup. For production, use Alembic migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## 🚀 Quick Start

### 1. Start Services

```bash
docker-compose up -d
```

### 2. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **API Base**: http://localhost:8000/api/v1

### 3. Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API health
curl http://localhost:8000/api/v1/health
```

## 📚 API Endpoints

### Core Endpoints

- **`/api/v1/documents`** - Document management
- **`/api/v1/projects`** - Project management
- **`/api/v1/emails`** - Email processing
- **`/api/v1/drive`** - Google Drive integration
- **`/api/v1/calendar`** - Calendar integration
- **`/api/v1/classification`** - AI classification
- **`/api/v1/attendee`** - Meeting bot integration

### WebSocket Endpoints

- **`/ws/documents/{document_id}`** - Document status updates
- **`/ws/notifications`** - User notifications
- **`/ws/processing`** - Processing status updates

## 🔌 Services

### 1. Email Processing Service

Processes incoming emails and automatically classifies them:

```python
from app.services.email import EmailProcessingService

service = EmailProcessingService()
await service.process_inbound_email(email_data)
```

### 2. Document Classification Service

AI-powered document classification using OpenAI:

```python
from app.services.classification import DocumentClassificationService

service = DocumentClassificationService()
result = await service.classify_document(content, project_context)
```

### 3. Google Drive Integration

Monitors file changes and processes new documents:

```python
from app.services.drive import DriveMonitoringService

service = DriveMonitoringService()
await service.setup_file_watch(file_id, user_id)
```

### 4. Vector Embeddings Service

Manages document embeddings for semantic search:

```python
from app.services.vector import VectorEmbeddingService

service = VectorEmbeddingService()
embeddings = await service.create_embeddings(text)
```

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest app/tests/test_email_service.py

# With coverage
pytest --cov=app --cov-report=html
```

### Test Configuration

Tests use a separate test database and mock external services. See `pytest.ini` for configuration.

## 📊 Monitoring

### Health Checks

- **`/health`** - Basic health check
- **`/api/v1/health`** - API health status
- **`/metrics`** - Prometheus metrics (if enabled)

### Logging

Structured logging with JSON format:

```python
import structlog

logger = structlog.get_logger()
logger.info("Processing document", document_id="123", status="started")
```

### Metrics

Prometheus metrics for:
- Request counts and response times
- Database connection status
- Background task performance
- External API calls

## 🚀 Deployment

### Production Deployment

1. **Build Docker Image**
   ```bash
   docker build -t besunny-backend:latest .
   ```

2. **Environment Configuration**
   - Set `ENVIRONMENT=production`
   - Configure production database URLs
   - Set secure `SECRET_KEY`

3. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests.

## 🔒 Security

### Authentication

- JWT-based authentication
- Supabase integration for user management
- Role-based access control

### Data Protection

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting

### API Security

- CORS configuration
- Request validation
- Error handling without information leakage

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -r requirements.txt[dev]`
4. Make changes and add tests
5. Run linting: `black . && isort . && flake8`
6. Submit a pull request

### Code Style

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

## 🔄 Migration from Supabase Edge Functions

This Python backend replaces the following Supabase edge functions:

- `process-inbound-emails` → Email processing service
- `gmail-polling-service` → Gmail integration service
- `drive-webhook-handler` → Drive monitoring service
- `calendar-webhook-public` → Calendar integration service
- `attendee-service` → Attendee integration service

See the migration guide in `/docs` for detailed porting instructions.

## 🗺️ Roadmap

### Phase 1: Foundation (Q1 2024)
- ✅ Basic infrastructure setup
- 🔄 Email processing service
- 🔄 Document classification
- 🔄 Google Drive integration

### Phase 2: AI Enhancement (Q2 2024)
- 📋 Vector embeddings
- 📋 RAG implementation
- 📋 Advanced analytics

### Phase 3: Microservices (Q3 2024)
- 📋 Service decomposition
- 📋 Advanced scalability
- 📋 Enterprise features

---

**Built with ❤️ by the BeSunny.ai team**
