"""
Redis manager for caching, session management, and pub/sub messaging.
"""

from typing import Optional, Any, Dict, List, Union
import redis.asyncio as redis
import json
import pickle
import logging
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .config import get_settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection and operation manager."""
    
    def __init__(self):
        self.settings = get_settings()
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub_client: Optional[redis.Redis] = None
        self._initialized = False
        self._connection_pool: Optional[redis.ConnectionPool] = None
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._initialized:
            return
        
        try:
            # Create connection pool
            self._connection_pool = redis.ConnectionPool.from_url(
                self.settings.redis_url,
                decode_responses=False,  # Keep binary for pickle support
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Create main client
            self._redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Create pubsub client
            self._pubsub_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._redis_client.ping()
            
            self._initialized = True
            logger.info("Redis initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self._redis_client:
            await self._redis_client.close()
        if self._pubsub_client:
            await self._pubsub_client.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        
        self._initialized = False
        logger.info("Redis connections closed")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        return self._redis_client
    
    @property
    def pubsub(self) -> redis.Redis:
        """Get Redis pubsub client."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        return self._pubsub_client
    
    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            if not self._redis_client:
                return False
            
            await self._redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    # Cache operations
    async def set_cache(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None,
        use_pickle: bool = False
    ) -> bool:
        """Set cache value."""
        try:
            if use_pickle:
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = json.dumps(value).encode('utf-8')
            
            if expire:
                return await self.client.setex(key, expire, serialized_value)
            else:
                return await self.client.set(key, serialized_value)
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False
    
    async def get_cache(
        self, 
        key: str, 
        use_pickle: bool = False
    ) -> Optional[Any]:
        """Get cache value."""
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            
            if use_pickle:
                return pickle.loads(value)
            else:
                return json.loads(value.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Delete cache key."""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def exists_cache(self, key: str) -> bool:
        """Check if cache key exists."""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    async def expire_cache(self, key: str, seconds: int) -> bool:
        """Set cache expiration."""
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            return False
    
    # Session management
    async def set_session(
        self, 
        session_id: str, 
        data: Dict[str, Any], 
        expire: int = 3600
    ) -> bool:
        """Set session data."""
        return await self.set_cache(f"session:{session_id}", data, expire)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return await self.get_cache(f"session:{session_id}")
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        return await self.delete_cache(f"session:{session_id}")
    
    async def extend_session(self, session_id: str, expire: int = 3600) -> bool:
        """Extend session expiration."""
        return await self.expire_cache(f"session:{session_id}", expire)
    
    # Rate limiting
    async def increment_rate_limit(self, key: str, expire: int = 3600) -> int:
        """Increment rate limit counter."""
        try:
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, expire)
            results = await pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Failed to increment rate limit for key {key}: {e}")
            return 0
    
    async def get_rate_limit(self, key: str) -> int:
        """Get current rate limit count."""
        try:
            value = await self.client.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Failed to get rate limit for key {key}: {e}")
            return 0
    
    # Pub/Sub messaging
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel."""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            elif not isinstance(message, str):
                message = str(message)
            
            return await self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Failed to publish to channel {channel}: {e}")
            return 0
    
    async def subscribe(self, channel: str):
        """Subscribe to channel."""
        try:
            pubsub = self.pubsub.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            raise
    
    async def listen_messages(self, channel: str, callback: callable):
        """Listen for messages on a channel."""
        try:
            pubsub = await self.subscribe(channel)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                    except json.JSONDecodeError:
                        data = message["data"].decode('utf-8')
                    
                    await callback(channel, data)
            
        except Exception as e:
            logger.error(f"Failed to listen to channel {channel}: {e}")
            raise
        finally:
            if pubsub:
                await pubsub.close()
    
    # Distributed locking
    async def acquire_lock(
        self, 
        lock_name: str, 
        timeout: int = 10, 
        expire: int = 30
    ) -> bool:
        """Acquire a distributed lock."""
        try:
            lock_key = f"lock:{lock_name}"
            lock_value = f"{datetime.utcnow().timestamp()}"
            
            # Try to set the lock
            result = await self.client.set(lock_key, lock_value, ex=expire, nx=True)
            return result is True
            
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_name}: {e}")
            return False
    
    async def release_lock(self, lock_name: str) -> bool:
        """Release a distributed lock."""
        try:
            lock_key = f"lock:{lock_name}"
            return await self.delete_cache(lock_key)
        except Exception as e:
            logger.error(f"Failed to release lock {lock_name}: {e}")
            return False
    
    # Queue operations
    async def push_to_queue(self, queue_name: str, item: Any) -> bool:
        """Push item to queue."""
        try:
            if isinstance(item, (dict, list)):
                item = json.dumps(item)
            elif not isinstance(item, str):
                item = str(item)
            
            result = await self.client.lpush(f"queue:{queue_name}", item)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to push to queue {queue_name}: {e}")
            return False
    
    async def pop_from_queue(self, queue_name: str, timeout: int = 0) -> Optional[Any]:
        """Pop item from queue."""
        try:
            if timeout > 0:
                result = await self.client.brpop(f"queue:{queue_name}", timeout)
                if result:
                    item = result[1]
                else:
                    return None
            else:
                item = await self.client.rpop(f"queue:{queue_name}")
            
            if item is None:
                return None
            
            try:
                return json.loads(item.decode('utf-8'))
            except json.JSONDecodeError:
                return item.decode('utf-8')
                
        except Exception as e:
            logger.error(f"Failed to pop from queue {queue_name}: {e}")
            return None
    
    async def get_queue_length(self, queue_name: str) -> int:
        """Get queue length."""
        try:
            return await self.client.llen(f"queue:{queue_name}")
        except Exception as e:
            logger.error(f"Failed to get queue length for {queue_name}: {e}")
            return 0
    
    # Cache statistics
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = await self.client.info()
            return {
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    if not redis_manager._initialized:
        await redis_manager.initialize()
    return redis_manager.client


async def get_redis() -> RedisManager:
    """Dependency for getting Redis manager."""
    return redis_manager


async def init_redis() -> None:
    """Initialize Redis on startup."""
    await redis_manager.initialize()


async def close_redis() -> None:
    """Close Redis on shutdown."""
    await redis_manager.close()


@asynccontextmanager
async def redis_lock(lock_name: str, timeout: int = 10, expire: int = 30):
    """Context manager for distributed locking."""
    redis_client = await get_redis()
    
    if await redis_client.acquire_lock(lock_name, timeout, expire):
        try:
            yield
        finally:
            await redis_client.release_lock(lock_name)
    else:
        raise RuntimeError(f"Failed to acquire lock: {lock_name}")


# Cache decorator
def cache_result(expire: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            redis_client = await get_redis()
            cached_result = await redis_client.get_cache(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.set_cache(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator
