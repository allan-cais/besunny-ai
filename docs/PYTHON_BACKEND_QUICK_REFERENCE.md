# Python Backend Quick Reference

## Overview

This document provides a quick reference for Python backend development within the BeSunny.ai ecosystem. It covers essential patterns, tools, and integration approaches for building scalable Python services that complement the existing React/TypeScript frontend and Supabase infrastructure.

## Python Backend Architecture

### Service Architecture Pattern
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Python API    │    │   External      │
│   (React/TS)    │◄──►│   Gateway       │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supabase      │    │  Python         │    │     AI/ML       │
│   (Auth/DB)     │    │  Microservices  │    │    Services     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Python Services
1. **API Gateway**: FastAPI-based REST API
2. **AI Processing**: OpenAI integration and ML pipelines
3. **Data Processing**: ETL and data transformation
4. **Background Workers**: Celery for async tasks
5. **Integration Services**: Third-party API connectors

## Essential Python Libraries

### Web Framework
```python
# FastAPI - Modern, fast web framework
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

app = FastAPI(title="BeSunny.ai API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database & ORM
```python
# SQLAlchemy - Database ORM
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Async SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Database connection
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)
```

### Authentication & Security
```python
# JWT handling
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token creation
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### AI & Machine Learning
```python
# OpenAI integration
import openai
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

# Document classification
async def classify_document(content: str, project_context: str):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a document classification expert."},
            {"role": "user", "content": f"Classify this document: {content}"}
        ]
    )
    return response.choices[0].message.content

# Vector embeddings
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode("Your text here")
```

### Background Tasks
```python
# Celery for background tasks
from celery import Celery
from celery.schedules import crontab

# Celery configuration
celery_app = Celery(
    "besunny",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Task definition
@celery_app.task
def process_document_async(document_id: str):
    # Process document in background
    pass

# Scheduled tasks
@celery_app.task
def daily_cleanup():
    # Daily maintenance tasks
    pass

# Schedule configuration
celery_app.conf.beat_schedule = {
    'daily-cleanup': {
        'task': 'daily_cleanup',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

## API Design Patterns

### RESTful Endpoints
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/api/v1")

# GET endpoint with pagination
@router.get("/documents/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Document)
    if project_id:
        query = query.where(Document.project_id == project_id)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    return documents

# POST endpoint with validation
@router.post("/documents/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_document = Document(**document.dict(), user_id=current_user.id)
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    return db_document
```

### Dependency Injection
```python
# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Authentication dependency
async def get_current_user(
    token: str = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user
```

### Error Handling
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Custom exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

# Business logic exceptions
class DocumentNotFoundError(Exception):
    pass

class InsufficientPermissionsError(Exception):
    pass

# Exception to HTTP status mapping
@app.exception_handler(DocumentNotFoundError)
async def document_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Document not found"}
    )
```

## Data Models & Schemas

### Pydantic Models
```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class DocumentType(str, Enum):
    EMAIL = "email"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    IMAGE = "image"

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    document_type: DocumentType
    project_id: Optional[str] = None
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title must not be empty')
        return v.strip()

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### Database Models
```python
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    project = relationship("Project", back_populates="documents")
```

## Integration Patterns

### Supabase Integration
```python
import asyncio
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

# Supabase client configuration
supabase: Client = create_client(
    "https://your-project.supabase.co",
    "your-anon-key",
    options=ClientOptions(
        postgrest_client_timeout=10,
        storage_client_timeout=10
    )
)

# Database operations
async def get_user_documents(user_id: str):
    response = supabase.table("documents").select("*").eq("user_id", user_id).execute()
    return response.data

# Real-time subscriptions
async def subscribe_to_documents(user_id: str):
    subscription = supabase.table("documents").on("INSERT", filter=f"user_id=eq.{user_id}").execute()
    return subscription
```

### Google Services Integration
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Google Calendar integration
async def get_calendar_events(credentials_dict: dict, calendar_id: str = 'primary'):
    creds = Credentials.from_authorized_user_info(credentials_dict)
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    service = build('calendar', 'v3', credentials=creds)
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=datetime.utcnow().isoformat() + 'Z',
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

# Google Drive integration
async def list_drive_files(credentials_dict: dict, folder_id: str = None):
    creds = Credentials.from_authorized_user_info(credentials_dict)
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    service = build('drive', 'v3', credentials=creds)
    
    query = "trashed=false"
    if folder_id:
        query += f" and '{folder_id}' in parents"
    
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
    ).execute()
    
    return results.get('files', [])
```

### OpenAI Integration
```python
import openai
from openai import AsyncOpenAI
import asyncio

# Async OpenAI client
client = AsyncOpenAI(api_key="your-api-key")

# Document classification
async def classify_document_with_context(content: str, project_context: str):
    system_prompt = f"""
    You are an expert document classifier for the BeSunny.ai platform.
    Project context: {project_context}
    
    Classify the following document into one of these categories:
    - email: Email communications
    - document: General documents, reports, articles
    - spreadsheet: Data tables, financial reports, analytics
    - presentation: Slides, decks, visual presentations
    - image: Images, diagrams, charts
    
    Return only the category name.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content[:4000]}  # Limit content length
        ],
        temperature=0.1,
        max_tokens=50
    )
    
    return response.choices[0].message.content.strip().lower()

# Content summarization
async def summarize_content(content: str, max_length: int = 200):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Summarize the following content in {max_length} characters or less:"},
            {"role": "user", "content": content[:4000]}
        ],
        temperature=0.3,
        max_tokens=max_length
    )
    
    return response.choices[0].message.content
```

## Testing & Development

### Testing Setup
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test client
client = TestClient(app)

# Test fixtures
@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client_with_db(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield client
    app.dependency_overrides.clear()
```

### Environment Configuration
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/dbname"
    
    # Security
    secret_key: str = "your-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External APIs
    openai_api_key: str
    supabase_url: str
    supabase_anon_key: str
    
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Deployment & Production

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Requirements.txt
```txt
# Web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# AI & ML
openai==1.3.7
sentence-transformers==2.2.2

# Background tasks
celery==5.3.4
redis==5.0.1

# Google APIs
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0

# Utilities
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.25.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

### Production Configuration
```python
# Production settings
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BeSunny.ai API",
    version="1.0.0",
    docs_url=None,  # Disable docs in production
    redoc_url=None
)

# Production CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
```

## Performance & Monitoring

### Caching Strategy
```python
import redis
from functools import wraps
import json

# Redis cache
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

def cache_result(expire_time: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire_time, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(expire_time=1800)  # 30 minutes
async def get_user_documents(user_id: str):
    # Expensive database query
    pass
```

### Health Checks
```python
from fastapi import APIRouter
import psutil
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "services": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "openai": await check_openai_health()
        }
    }
```

## Common Patterns & Best Practices

### Async/Await Patterns
```python
# Concurrent API calls
async def fetch_multiple_resources(user_id: str):
    tasks = [
        get_user_documents(user_id),
        get_user_projects(user_id),
        get_user_meetings(user_id)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "documents": results[0] if not isinstance(results[0], Exception) else [],
        "projects": results[1] if not isinstance(results[1], Exception) else [],
        "meetings": results[2] if not isinstance(results[2], Exception) else []
    }

# Rate limiting
import asyncio
from asyncio import Semaphore

# Limit concurrent OpenAI API calls
openai_semaphore = Semaphore(5)

async def limited_openai_call(prompt: str):
    async with openai_semaphore:
        return await classify_document(prompt)
```

### Error Handling & Logging
```python
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Context manager for error handling
@asynccontextmanager
async def error_context(operation: str):
    try:
        yield
    except Exception as e:
        logger.error(f"Error in {operation}: {str(e)}", exc_info=True)
        raise

# Usage
async def process_document_safely(document_id: str):
    async with error_context(f"processing document {document_id}"):
        # Document processing logic
        pass
```

This Python Backend Quick Reference provides the essential patterns, tools, and integration approaches needed to build scalable Python services that integrate seamlessly with the BeSunny.ai ecosystem. Use this as a starting point for implementing Python-based microservices, AI processing pipelines, and data processing workflows.
