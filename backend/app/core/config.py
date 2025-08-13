"""
Core configuration module for BeSunny.ai Python backend.
Handles environment variables, settings, and configuration management.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "BeSunny.ai Python Backend"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # Google APIs
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_project_id: str = Field(..., env="GOOGLE_PROJECT_ID")
    
    # Pinecone
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_environment: str = Field(..., env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="besunny-documents", env="PINECONE_INDEX_NAME")
    
    # N8N Integration
    n8n_webhook_url: Optional[str] = Field(default=None, env="N8N_CLASSIFICATION_WEBHOOK_URL")
    n8n_api_key: Optional[str] = Field(default=None, env="N8N_API_KEY")
    
    # Attendee Integration
    attendee_api_key: Optional[str] = Field(default=None, env="ATTENDEE_API_KEY")
    attendee_base_url: str = Field(default="https://app.attendee.dev", env="ATTENDEE_BASE_URL")
    
    # Email Processing
    email_processing_batch_size: int = Field(default=100, env="EMAIL_PROCESSING_BATCH_SIZE")
    email_processing_timeout: int = Field(default=300, env="EMAIL_PROCESSING_TIMEOUT")
    
    # Drive Monitoring
    drive_webhook_timeout: int = Field(default=60, env="DRIVE_WEBHOOK_TIMEOUT")
    drive_polling_interval: int = Field(default=300, env="DRIVE_POLLING_INTERVAL")
    
    # Calendar Integration
    calendar_webhook_timeout: int = Field(default=60, env="CALENDAR_WEBHOOK_TIMEOUT")
    calendar_sync_interval: int = Field(default=600, env="CALENDAR_SYNC_INTERVAL")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("database_url", pre=True)
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL is required")
        return v
    
    @validator("supabase_url", pre=True)
    def validate_supabase_url(cls, v):
        """Validate Supabase URL format."""
        if not v:
            raise ValueError("Supabase URL is required")
        if not v.startswith("https://"):
            raise ValueError("Supabase URL must use HTTPS")
        return v
    
    @validator("openai_api_key", pre=True)
    def validate_openai_api_key(cls, v):
        """Validate OpenAI API key format."""
        if not v:
            raise ValueError("OpenAI API key is required")
        if not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v
    
    @validator("pinecone_api_key", pre=True)
    def validate_pinecone_api_key(cls, v):
        """Validate Pinecone API key format."""
        if not v:
            raise ValueError("Pinecone API key is required")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def is_development() -> bool:
    """Check if running in development mode."""
    return settings.debug or os.getenv("ENVIRONMENT") == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return os.getenv("ENVIRONMENT") == "production"


def is_testing() -> bool:
    """Check if running in testing mode."""
    return os.getenv("ENVIRONMENT") == "testing"
