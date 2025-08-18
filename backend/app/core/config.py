"""
Configuration management for BeSunny.ai Python backend.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    database_url: str = Field(default="postgresql+asyncpg://user:pass@localhost/dbname", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")

class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")

class Settings(PydanticBaseSettings):
    """Main application settings."""
    app_name: str = Field(default="BeSunny.ai Backend", env="APP_NAME")
    app_version: str = Field(default="17.0.0", env="APP_VERSION")
    environment: str = Field(default="production", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=False, env="CORS_ALLOW_CREDENTIALS")
    
    # Database
    database: DatabaseSettings = DatabaseSettings()
    
    # Redis
    redis: RedisSettings = RedisSettings()
    
    # Supabase
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

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
