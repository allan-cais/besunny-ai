"""
Enhanced configuration module for BeSunny.ai Python backend.
Handles environment variables, settings, and configuration management with validation.
"""

import os
from typing import List, Optional, Union
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    database_url: str = Field(
        default="sqlite:///./besunny_dev.db",
        description="Database connection URL"
    )
    database_pool_size: int = Field(
        default=20,
        description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=30,
        description="Maximum database connection overflow"
    )
    database_echo: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    
    class Config:
        env_prefix = "DB_"

class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_db: int = Field(
        default=0,
        description="Redis database number"
    )
    redis_max_connections: int = Field(
        default=20,
        description="Maximum Redis connections"
    )
    redis_socket_timeout: int = Field(
        default=5,
        description="Redis socket timeout in seconds"
    )
    
    class Config:
        env_prefix = "REDIS_"

class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-very-long-and-random",
        description="Application secret key for JWT tokens"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration time"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiration time"
    )
    
    class Config:
        env_prefix = "SECURITY_"

class CORSSettings(BaseSettings):
    """CORS configuration settings."""
    
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow CORS credentials"
    )
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed HTTP headers"
    )
    
    class Config:
        env_prefix = "CORS_"
    
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

class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (optional)"
    )
    enable_console_logging: bool = Field(
        default=True,
        description="Enable console logging"
    )
    
    class Config:
        env_prefix = "LOG_"
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()

class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""
    
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    metrics_port: int = Field(
        default=9090,
        description="Metrics server port"
    )
    enable_health_checks: bool = Field(
        default=True,
        description="Enable health check endpoints"
    )
    health_check_interval: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    
    class Config:
        env_prefix = "MONITORING_"

class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = Field(
        default="BeSunny.ai Backend",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes"
    )
    
    # Sub-settings
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database configuration"
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings,
        description="Redis configuration"
    )
    security: SecuritySettings = Field(
        default_factory=SecuritySettings,
        description="Security configuration"
    )
    cors: CORSSettings = Field(
        default_factory=CORSSettings,
        description="CORS configuration"
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging configuration"
    )
    monitoring: MonitoringSettings = Field(
        default_factory=MonitoringSettings,
        description="Monitoring configuration"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from environment variables
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_environments = ["development", "staging", "production", "test"]
        if v.lower() not in valid_environments:
            raise ValueError(f"Invalid environment. Must be one of: {valid_environments}")
        return v.lower()
    
    @validator("port")
    def validate_port(cls, v):
        """Validate port number."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("workers")
    def validate_workers(cls, v):
        """Validate worker count."""
        if v < 1:
            raise ValueError("Workers must be at least 1")
        return v

# Global settings instance - lazy loaded
_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings instance."""
    global _settings_instance
    if _settings_instance is None:
        try:
            _settings_instance = Settings()
            logger.info(f"Configuration loaded for environment: {_settings_instance.environment}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fallback to basic settings
            _settings_instance = Settings()
    return _settings_instance

def is_development() -> bool:
    """Check if running in development mode."""
    return get_settings().environment == "development"

def is_production() -> bool:
    """Check if running in production mode."""
    return get_settings().environment == "production"

def is_staging() -> bool:
    """Check if running in staging mode."""
    return get_settings().environment == "staging"

def is_testing() -> bool:
    """Check if running in testing mode."""
    return get_settings().environment == "test"

def get_database_url() -> str:
    """Get database URL from settings."""
    return get_settings().database.database_url

def get_redis_url() -> str:
    """Get Redis URL from settings."""
    return get_settings().redis.redis_url

def get_secret_key() -> str:
    """Get secret key from settings."""
    return get_settings().security.secret_key

def get_cors_origins() -> List[str]:
    """Get CORS origins from settings."""
    return get_settings().cors.cors_origins

def get_log_level() -> str:
    """Get log level from settings."""
    return get_settings().logging.log_level

# Backward compatibility functions
def get_app_name() -> str:
    """Get application name (backward compatibility)."""
    return get_settings().app_name

def get_app_version() -> str:
    """Get application version (backward compatibility)."""
    return get_settings().app_version

def get_host() -> str:
    """Get server host (backward compatibility)."""
    return get_settings().host

def get_port() -> int:
    """Get server port (backward compatibility)."""
    return get_settings().port

def get_workers() -> int:
    """Get worker count (backward compatibility)."""
    return get_settings().workers

def get_debug() -> bool:
    """Get debug mode (backward compatibility)."""
    return get_settings().debug

def get_cors_allow_credentials() -> bool:
    """Get CORS credentials setting (backward compatibility)."""
    return get_settings().cors.cors_allow_credentials
