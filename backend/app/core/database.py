"""
Database configuration and connection management for BeSunny.ai Python backend.
Handles SQLAlchemy async setup, connection pooling, and Supabase integration.
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
import logging

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
    
    async def initialize(self) -> None:
        """Initialize database connections and session maker."""
        if self._initialized:
            return
        
        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                self.settings.database_url,
                echo=self.settings.debug,
                poolclass=QueuePool,
                pool_size=self.settings.database_pool_size,
                max_overflow=self.settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
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
                await conn.execute("SELECT 1")
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")
    
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
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async for session in db_manager.get_session():
        yield session


async def init_db() -> None:
    """Initialize database on startup."""
    await db_manager.initialize()


async def close_db() -> None:
    """Close database on shutdown."""
    await db_manager.close()


# Database event listeners for debugging
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


class SupabaseClient:
    """Supabase client wrapper for direct database access."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client = None
    
    @property
    def client(self):
        """Get Supabase client instance."""
        if not self._client:
            try:
                from supabase import create_client, Client
                self._client = create_client(
                    self.settings.supabase_url,
                    self.settings.supabase_service_role_key
                )
            except ImportError:
                logger.warning("Supabase client not available")
                return None
        return self._client
    
    async def execute_query(self, query: str, params: dict = None) -> dict:
        """Execute raw SQL query on Supabase."""
        if not self.client:
            raise RuntimeError("Supabase client not available")
        
        try:
            # This is a simplified example - in practice you'd use Supabase's query builder
            # or direct PostgreSQL connection for complex queries
            result = self.client.rpc("execute_sql", {
                "query": query,
                "params": params or {}
            })
            return result.data
        except Exception as e:
            logger.error(f"Supabase query execution failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Supabase connection health."""
        try:
            if not self.client:
                return False
            
            # Simple health check query
            result = self.client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False


# Global Supabase client instance
supabase_client = SupabaseClient()


async def get_supabase() -> SupabaseClient:
    """Dependency for getting Supabase client."""
    return supabase_client
