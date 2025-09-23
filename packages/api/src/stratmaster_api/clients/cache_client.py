"""Redis caching client for performance optimization."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

try:
    import redis
    import redis.asyncio as aioredis
except ImportError:
    redis = None
    aioredis = None


class CacheClient:
    """Redis cache client with async support."""

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        """Initialize cache client.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.default_ttl = default_ttl
        self.client: Optional[aioredis.Redis] = None
        self.enabled = redis is not None

    async def connect(self):
        """Connect to Redis."""
        if not self.enabled:
            logger.warning("Redis not available, caching disabled")
            return

        try:
            self.client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None

    def _make_key(self, prefix: str, *args: Any) -> str:
        """Generate cache key from prefix and arguments."""
        # Create a hash of the arguments for consistent key generation
        key_data = json.dumps(args, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value is not None:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.client:
            return False

        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern."""
        if not self.client:
            return False

        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return False

    def cache_result(self, prefix: str, ttl: Optional[int] = None):
        """Decorator to cache function results."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.client:
                    return await func(*args, **kwargs)

                # Generate cache key
                cache_key = self._make_key(prefix, args, kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result

                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                logger.debug(f"Cache set for {cache_key}")
                return result

            return wrapper
        return decorator


# Global cache client instance
_cache_client: Optional[CacheClient] = None


async def get_cache_client() -> CacheClient:
    """Get the global cache client instance."""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
        await _cache_client.connect()
    return _cache_client


async def close_cache_client():
    """Close the global cache client instance."""
    global _cache_client
    if _cache_client:
        await _cache_client.disconnect()
        _cache_client = None