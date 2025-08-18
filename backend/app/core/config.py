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
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)
    
    # Database
    database_url: str = Field(default="sqlite:///./besunny_dev.db")
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=30)
    
    # Supabase
    supabase_url: str = Field(default="https://placeholder.supabase.co")
    supabase_service_role_key: str = Field(default="placeholder-service-role-key")
    supabase_anon_key: str = Field(default="placeholder-anon-key")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_db: int = Field(default=0)
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production-very-long-and-random")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    
    # OpenAI
    openai_api_key: str = Field(default="sk-placeholder-openai-api-key")
    openai_model: str = Field(default="gpt-4")
    openai_max_tokens: int = Field(default=1000)
    
    # Google APIs
    google_client_id: str = Field(default="placeholder-google-client-id")
    google_client_secret: str = Field(default="placeholder-google-client-secret")
    google_project_id: str = Field(default="placeholder-google-project-id")
    google_login_redirect_uri: str = Field(default="http://localhost:3000/oauth-callback")
    
    # Pinecone
    pinecone_api_key: str = Field(default="placeholder-pinecone-api-key")
    pinecone_environment: str = Field(default="placeholder-environment")
    pinecone_index_name: str = Field(default="besunny-documents")
    
    # N8N Integration
    n8n_webhook_url: Optional[str] = Field(default=None)
    n8n_api_key: Optional[str] = Field(default=None)
    n8n_classification_webhook_url: Optional[str] = Field(default=None)
    
    # Attendee Integration
    attendee_api_key: Optional[str] = Field(default=None)
    attendee_base_url: str = Field(default="https://app.attendee.dev")
    
    # Email Processing
    email_processing_batch_size: int = Field(default=100)
    email_processing_timeout: int = Field(default=300)
    
    # Virtual Email
    virtual_email_domain: str = Field(default="virtual.besunny.ai")
    
    # Drive Monitoring
    drive_webhook_timeout: int = Field(default=60)
    drive_polling_interval: int = Field(default=300)
    
    # Calendar Integration
    calendar_webhook_timeout: int = Field(default=60)
    calendar_sync_interval: int = Field(default=600)
    webhook_base_url: str = Field(default="http://localhost:8000")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=3600)
    
    # Enterprise Features - Phase 4
    enable_multi_tenancy: bool = Field(default=False)
    enable_billing: bool = Field(default=False)
    enable_compliance: bool = Field(default=False)
    enable_audit_logging: bool = Field(default=True)
    audit_log_retention_days: int = Field(default=2555)  # 7 years
    
    # Business Intelligence
    enable_bi_dashboard: bool = Field(default=True)
    bi_cache_ttl: int = Field(default=3600)
    enable_predictive_analytics: bool = Field(default=True)
    ml_model_update_frequency: str = Field(default="weekly")
    
    # Workflow Automation
    enable_workflow_engine: bool = Field(default=True)
    workflow_execution_timeout: int = Field(default=300)
    max_concurrent_workflows: int = Field(default=100)
    enable_business_rules_engine: bool = Field(default=True)
    
    # Billing & Usage
    enable_usage_tracking: bool = Field(default=True)
    enable_billing_integration: bool = Field(default=False)
    billing_provider: str = Field(default="stripe")
    usage_aggregation_interval: str = Field(default="hourly")
    
    # Performance & Scaling
    enable_auto_scaling: bool = Field(default=True)
    min_instances: int = Field(default=2)
    max_instances: int = Field(default=20)
    cpu_threshold_percent: int = Field(default=70)
    memory_threshold_percent: int = Field(default=80)
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            if v.strip() == "":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif v is None:
            return ["*"]
        return v
    
    @validator("database_url", pre=True)
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            return "sqlite:///./besunny_dev.db"
        return v
    
    @validator("supabase_url", pre=True)
    def validate_supabase_url(cls, v):
        """Validate Supabase URL format."""
        if not v:
            return "https://placeholder.supabase.co"
        if not v.startswith("https://"):
            return "https://placeholder.supabase.co"
        return v
    
    @validator("openai_api_key", pre=True)
    def validate_openai_api_key(cls, v):
        """Validate OpenAI API key format."""
        if not v or not v.startswith("sk-"):
            return "sk-placeholder-openai-api-key"
        return v
    
    @validator("pinecone_api_key", pre=True)
    def validate_pinecone_api_key(cls, v):
        """Validate Pinecone API key format."""
        if not v:
            return "placeholder-pinecone-api-key"
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance - only create when needed
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def is_development() -> bool:
    """Check if running in development mode."""
    return get_settings().debug or os.getenv("ENVIRONMENT") == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return os.getenv("ENVIRONMENT") == "production"


def is_testing() -> bool:
    """Check if running in testing mode."""
    return os.getenv("ENVIRONMENT") == "testing"
