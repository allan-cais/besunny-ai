"""
Configuration management for BeSunny.ai Python backend.
Optimized for maximum efficiency and reliability.
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    database_url: str = Field(default="", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")

class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    redis_url: str = Field(default="", env="REDIS_URL")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")

class Settings(BaseSettings):
    """Main application settings - optimized for efficiency."""
    app_name: str = Field(default="BeSunny.ai Backend", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="production", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS - optimized for production
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=False, env="CORS_ALLOW_CREDENTIALS")
    
    # Database
    database: DatabaseSettings = DatabaseSettings()
    
    # Redis
    redis: RedisSettings = RedisSettings()
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Supabase
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")
    
    # OpenAI - essential for AI services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # Google OAuth
    google_client_id: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    google_project_id: Optional[str] = Field(default=None, env="GOOGLE_PROJECT_ID")
    google_login_redirect_uri: Optional[str] = Field(default=None, env="GOOGLE_LOGIN_REDIRECT_URI")
    google_service_account_key_path: Optional[str] = Field(default=None, env="GOOGLE_SERVICE_ACCOUNT_KEY_PATH")
    google_service_account_key_base64: Optional[str] = Field(default=None, env="GOOGLE_SERVICE_ACCOUNT_KEY_BASE64")
    
    # Pinecone - vector database
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_vector_store: str = Field(default="sunny", env="PINECONE_VECTOR_STORE")
    pinecone_host_url: str = Field(default="https://sunny-wws6cxq.svc.aped-4627-b74a.pinecone.io", env="PINECONE_HOST_URL")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: Optional[str] = Field(default=None, env="PINECONE_INDEX_NAME")
    
    # Embedding settings
    embedding_base_url: str = Field(default="https://api.openai.com/v1", env="EMBEDDING_BASE_URL")
    embedding_api_key: Optional[str] = Field(default=None, env="EMBEDDING_API_KEY")
    embedding_model_choice: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL_CHOICE")
    
    # Webhook settings
    webhook_base_url: str = Field(default="https://backend-staging-6085.up.railway.app", env="WEBHOOK_BASE_URL")
    base_url: str = Field(default="https://backend-staging-6085.up.railway.app", env="BASE_URL")
    n8n_classification_webhook_url: Optional[str] = Field(default=None, env="N8N_CLASSIFICATION_WEBHOOK_URL")
    n8n_drivesync_webhook_url: Optional[str] = Field(default=None, env="N8N_DRIVESYNC_WEBHOOK_URL")
    
    # Gmail webhook verification (temporarily disable for debugging)
    verify_gmail_webhooks: bool = Field(default=False, env="VERIFY_GMAIL_WEBHOOKS")
    
    # Gmail email processing settings
    gmail_mark_processed_action: str = Field(default="read_then_archive", env="GMAIL_MARK_PROCESSED_ACTION")
    
    # Attendee service settings
    attendee_api_base_url: Optional[str] = Field(default=None, env="ATTENDEE_API_BASE_URL")
    master_attendee_api_key: Optional[str] = Field(default=None, env="MASTER_ATTENDEE_API_KEY")
    
    # Performance settings
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Health check settings
    health_check_timeout: int = Field(default=5, env="HEALTH_CHECK_TIMEOUT")
    
    # Rate limiting settings
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    
    # Enterprise settings
    audit_log_retention_days: int = Field(default=90, env="AUDIT_LOG_RETENTION_DAYS")
    bi_cache_ttl: int = Field(default=3600, env="BI_CACHE_TTL")
    enable_multi_tenancy: bool = Field(default=True, env="ENABLE_MULTI_TENANCY")
    max_tenants_per_instance: int = Field(default=1000, env="MAX_TENANTS_PER_INSTANCE")
    workflow_execution_timeout: int = Field(default=300, env="WORKFLOW_EXECUTION_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def is_development() -> bool:
    """Check if running in development mode."""
    return get_settings().environment.lower() == "development"

def is_production() -> bool:
    """Check if running in production mode."""
    return get_settings().environment.lower() == "production"

def is_testing() -> bool:
    """Check if running in testing mode."""
    return get_settings().environment.lower() == "testing"

def get_cors_origins() -> List[str]:
    """Get CORS origins as a list."""
    cors_origins = get_settings().cors_origins
    if cors_origins == "*":
        return ["*"]
    return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
