"""
Enhanced database module for BeSunny.ai Python backend.
Handles database connections, connection pooling, and Supabase integration.
"""

import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
import asyncio

from .config import get_settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize database connections and session maker."""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:  # Double-check pattern
                return
            
            try:
                logger.info("Initializing database connections...")
                
                # Create async engine with connection pooling
                self.engine = create_async_engine(
                    self.settings.database.database_url,
                    echo=self.settings.database.database_echo,
                    poolclass=QueuePool,
                    pool_size=self.settings.database.database_pool_size,
                    max_overflow=self.settings.database.database_max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    pool_timeout=30,
                    pool_reset_on_return='commit',
                )
                
                # Create session maker
                self.async_session_maker = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False,
                )
                
                # Test connection
                async with self.engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                
                self._initialized = True
                logger.info(f"Database initialized successfully with pool size {self.settings.database.database_pool_size}")
                
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                self._initialized = False
                raise
    
    async def close(self) -> None:
        """Close database connections."""
        if not self._initialized:
            return
        
        async with self._lock:
            if not self._initialized:
                return
            
            try:
                if self.engine:
                    await self.engine.dispose()
                    logger.info("Database engine disposed")
                
                self._initialized = False
                logger.info("Database connections closed")
                
            except Exception as e:
                logger.error(f"Error closing database connections: {e}")
                raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self._initialized:
            await self.initialize()
        
        if not self.async_session_maker:
            raise RuntimeError("Database not initialized")
        
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            if not self.engine:
                return False
            
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """Get database connection information."""
        if not self.engine:
            return {"status": "not_initialized"}
        
        try:
            pool = self.engine.pool
            return {
                "status": "healthy" if self._initialized else "not_initialized",
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "database_url": self.settings.database.database_url,
                "pool_size_config": self.settings.database.database_pool_size,
                "max_overflow_config": self.settings.database.database_max_overflow,
            }
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {"status": "error", "error": str(e)}

# Global database manager instance - lazy loaded
_db_manager_instance: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """Get database manager instance."""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async for session in get_db_manager().get_session():
        yield session

async def init_db() -> None:
    """Initialize database on startup."""
    try:
        await get_db_manager().initialize()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise - allow application to continue without database
        logger.warning("Application will continue without database functionality")

async def close_db() -> None:
    """Close database on shutdown."""
    try:
        await get_db_manager().close()
        logger.info("Database shutdown completed successfully")
    except Exception as e:
        logger.error(f"Database shutdown failed: {e}")

async def health_check_db() -> bool:
    """Health check for database."""
    try:
        return await get_db_manager().health_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def get_db_info() -> dict:
    """Get database information."""
    try:
        return await get_db_manager().get_connection_info()
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"status": "error", "error": str(e)}

# Database event listeners for debugging
def setup_debug_listeners():
    """Setup debug event listeners if debug mode is enabled."""
    try:
        if get_settings().debug:
            @event.listens_for(Base, "before_insert", propagate=True)
            def before_insert(mapper, connection, target):
                logger.debug(f"Inserting {target.__class__.__name__}: {target}")
            
            @event.listens_for(Base, "before_update", propagate=True)
            def before_update(mapper, connection, target):
                logger.debug(f"Updating {target.__class__.__name__}: {target}")
            
            @event.listens_for(Base, "before_delete", propagate=True)
            def before_delete(mapper, connection, target):
                logger.debug(f"Deleting {target.__class__.__name__}: {target}")
                
            logger.info("Database debug listeners enabled")
    except Exception as e:
        logger.warning(f"Could not setup debug listeners: {e}")

# Setup debug listeners when module is imported
setup_debug_listeners()

# Backward compatibility functions
async def get_database_health() -> bool:
    """Get database health (backward compatibility)."""
    return await health_check_db()

async def get_database_status() -> dict:
    """Get database status (backward compatibility)."""
    return await get_db_info()

# Supabase compatibility function
def get_supabase():
    """Get Supabase client (backward compatibility)."""
    from .supabase_config import get_supabase_client
    return get_supabase_client()
