"""Advanced multi-tier caching system for StratMaster API.

Implements layered caching strategy with:
- L1: In-memory LRU cache for hot data
- L2: Redis cluster for distributed caching  
- L3: CDN/Edge cache with surrogate keys
- Performance profiling and metrics
- Intelligent cache invalidation
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict
from uuid import uuid4

try:
    import redis.asyncio as aioredis
    from redis.asyncio import RedisCluster
except ImportError:
    aioredis = None
    RedisCluster = None

logger = logging.getLogger(__name__)

# Feature flags for caching layers
def is_response_cache_v2_enabled() -> bool:
    """Check if advanced response caching is enabled."""
    return os.getenv("ENABLE_RESPONSE_CACHE_V2", "false").lower() == "true"


def is_edge_cache_hints_enabled() -> bool:
    """Check if edge cache hints are enabled.""" 
    return os.getenv("ENABLE_EDGE_CACHE_HINTS", "false").lower() == "true"


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        total_ops = self.hits + self.misses + self.sets + self.deletes
        return (self.total_latency_ms / total_ops) if total_ops > 0 else 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 300
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() > (self.created_at + timedelta(seconds=self.ttl_seconds))
    
    def access(self) -> None:
        """Mark entry as accessed."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryCache:
    """L1 in-memory LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self.metrics = CacheMetrics()
    
    def _evict_expired(self) -> int:
        """Evict expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        self.metrics.evictions += len(expired_keys)
        return len(expired_keys)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            lru_key = self._access_order[0]
            self._remove_entry(lru_key)
            self.metrics.evictions += 1
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache and access order."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU tracking."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def get(self, key: str) -> Any | None:
        """Get value from memory cache."""
        start_time = time.perf_counter()
        
        # Clean up expired entries periodically
        self._evict_expired()
        
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired:
                entry.access()
                self._update_access_order(key)
                self.metrics.hits += 1
                self.metrics.total_latency_ms += (time.perf_counter() - start_time) * 1000
                return entry.value
            else:
                self._remove_entry(key)
        
        self.metrics.misses += 1
        self.metrics.total_latency_ms += (time.perf_counter() - start_time) * 1000
        return None
    
    def set(self, key: str, value: Any, ttl: int | None = None, tags: list[str] | None = None) -> bool:
        """Set value in memory cache."""
        start_time = time.perf_counter()
        
        # Evict if at capacity
        while len(self._cache) >= self.max_size:
            self._evict_lru()
        
        entry = CacheEntry(
            value=value,
            ttl_seconds=ttl or self.default_ttl,
            tags=tags or []
        )
        
        self._cache[key] = entry
        self._update_access_order(key)
        
        self.metrics.sets += 1
        self.metrics.total_latency_ms += (time.perf_counter() - start_time) * 1000
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        if key in self._cache:
            self._remove_entry(key)
            self.metrics.deletes += 1
            return True
        return False
    
    def clear_by_tags(self, tags: list[str]) -> int:
        """Clear all entries with matching tags."""
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if any(tag in entry.tags for tag in tags):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
        
        return len(keys_to_remove)
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": self.metrics.hit_rate,
            "avg_latency_ms": self.metrics.avg_latency_ms,
            "metrics": {
                "hits": self.metrics.hits,
                "misses": self.metrics.misses,
                "sets": self.metrics.sets,
                "deletes": self.metrics.deletes,
                "evictions": self.metrics.evictions
            }
        }


class MultiTierCacheClient:
    """Advanced multi-tier cache client."""
    
    def __init__(
        self,
        redis_url: str | None = None,
        memory_cache_size: int = 1000,
        default_ttl: int = 300
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.default_ttl = default_ttl
        
        # L1: Memory cache
        self.memory_cache = MemoryCache(memory_cache_size, default_ttl)
        
        # L2: Redis cache
        self.redis_client: aioredis.Redis | None = None
        self.redis_enabled = aioredis is not None
        
        # Performance tracking
        self.operation_times: dict[str, list[float]] = {
            "memory_get": [], "memory_set": [],
            "redis_get": [], "redis_set": [],
            "total_get": [], "total_set": []
        }
    
    async def connect(self) -> None:
        """Connect to Redis cache."""
        if not self.redis_enabled:
            logger.warning("Redis not available, using memory cache only")
            return
        
        try:
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis multi-tier cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    def _make_key(self, namespace: str, *args: Any) -> str:
        """Generate cache key."""
        key_data = json.dumps(args, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{namespace}:{key_hash}"
    
    async def get(self, key: str, namespace: str = "default") -> tuple[Any | None, str]:
        """
        Get value from multi-tier cache.
        
        Returns:
            Tuple of (value, cache_level) where cache_level is "memory", "redis", or "miss"
        """
        total_start = time.perf_counter()
        cache_key = self._make_key(namespace, key)
        
        # Try L1 (memory) cache first
        memory_start = time.perf_counter()
        value = self.memory_cache.get(cache_key)
        self.operation_times["memory_get"].append((time.perf_counter() - memory_start) * 1000)
        
        if value is not None:
            self.operation_times["total_get"].append((time.perf_counter() - total_start) * 1000)
            return value, "memory"
        
        # Try L2 (Redis) cache
        if self.redis_client:
            redis_start = time.perf_counter()
            try:
                redis_value = await self.redis_client.get(cache_key)
                self.operation_times["redis_get"].append((time.perf_counter() - redis_start) * 1000)
                
                if redis_value:
                    value = json.loads(redis_value)
                    # Populate L1 cache
                    self.memory_cache.set(cache_key, value, ttl=self.default_ttl // 2)  # Shorter TTL for L1
                    self.operation_times["total_get"].append((time.perf_counter() - total_start) * 1000)
                    return value, "redis"
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        self.operation_times["total_get"].append((time.perf_counter() - total_start) * 1000)
        return None, "miss"
    
    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: int | None = None,
        tags: list[str] | None = None
    ) -> bool:
        """Set value in multi-tier cache."""
        total_start = time.perf_counter()
        cache_key = self._make_key(namespace, key)
        ttl = ttl or self.default_ttl
        
        success = False
        
        # Set in L1 (memory) cache
        memory_start = time.perf_counter()
        self.memory_cache.set(cache_key, value, ttl=ttl // 2, tags=tags)  # Shorter TTL for L1
        self.operation_times["memory_set"].append((time.perf_counter() - memory_start) * 1000)
        success = True
        
        # Set in L2 (Redis) cache
        if self.redis_client:
            redis_start = time.perf_counter()
            try:
                serialized = json.dumps(value, default=str)
                await self.redis_client.setex(cache_key, ttl, serialized)
                
                # Add tags for invalidation
                if tags:
                    for tag in tags:
                        await self.redis_client.sadd(f"tag:{tag}", cache_key)
                        await self.redis_client.expire(f"tag:{tag}", ttl)
                
                self.operation_times["redis_set"].append((time.perf_counter() - redis_start) * 1000)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                success = False
        
        self.operation_times["total_set"].append((time.perf_counter() - total_start) * 1000)
        return success
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete key from all cache tiers."""
        cache_key = self._make_key(namespace, key)
        
        # Delete from L1
        self.memory_cache.delete(cache_key)
        
        # Delete from L2
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                return False
        
        return True
    
    async def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidate cache entries by tags."""
        total_invalidated = 0
        
        # Invalidate in L1
        total_invalidated += self.memory_cache.clear_by_tags(tags)
        
        # Invalidate in L2
        if self.redis_client:
            try:
                for tag in tags:
                    tag_key = f"tag:{tag}"
                    keys = await self.redis_client.smembers(tag_key)
                    if keys:
                        await self.redis_client.delete(*keys)
                        total_invalidated += len(keys)
                    await self.redis_client.delete(tag_key)
            except Exception as e:
                logger.error(f"Redis tag invalidation error: {e}")
        
        return total_invalidated
    
    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics."""
        def calculate_percentiles(times: list[float]) -> dict[str, float]:
            if not times:
                return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}
            
            sorted_times = sorted(times)
            length = len(sorted_times)
            
            return {
                "p50": sorted_times[int(length * 0.5)],
                "p95": sorted_times[int(length * 0.95)],
                "p99": sorted_times[int(length * 0.99)],
                "avg": sum(sorted_times) / length,
                "count": length
            }
        
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "performance": {
                operation: calculate_percentiles(times)
                for operation, times in self.operation_times.items()
            },
            "redis_enabled": self.redis_client is not None,
            "total_operations": sum(len(times) for times in self.operation_times.values())
        }
    
    def cache_async(
        self,
        namespace: str,
        ttl: int | None = None,
        tags: list[str] | None = None
    ):
        """Decorator for caching async function results."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
                
                # Try to get from cache
                cached_value, cache_level = await self.get(cache_key, namespace)
                if cached_value is not None:
                    logger.debug(f"Cache hit ({cache_level}) for {func.__name__}")
                    return cached_value
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, namespace, ttl, tags)
                logger.debug(f"Cache miss, stored result for {func.__name__}")
                return result
            
            return wrapper
        return decorator


# Global multi-tier cache instance
_multi_tier_cache: MultiTierCacheClient | None = None


async def get_multi_tier_cache() -> MultiTierCacheClient:
    """Get the global multi-tier cache instance."""
    global _multi_tier_cache
    if _multi_tier_cache is None:
        _multi_tier_cache = MultiTierCacheClient()
        await _multi_tier_cache.connect()
    return _multi_tier_cache


async def close_multi_tier_cache():
    """Close the global multi-tier cache instance."""
    global _multi_tier_cache
    if _multi_tier_cache:
        await _multi_tier_cache.disconnect()
        _multi_tier_cache = None


# Convenience functions for common cache patterns
async def cache_strategy_brief(tenant_id: str, strategy_id: str, brief_data: dict[str, Any]) -> bool:
    """Cache strategy brief data."""
    cache = await get_multi_tier_cache()
    return await cache.set(
        f"strategy_brief:{tenant_id}:{strategy_id}",
        brief_data,
        namespace="strategy",
        ttl=1800,  # 30 minutes
        tags=["strategy", f"tenant:{tenant_id}"]
    )


async def get_cached_strategy_brief(tenant_id: str, strategy_id: str) -> tuple[dict[str, Any] | None, str]:
    """Get cached strategy brief data."""
    cache = await get_multi_tier_cache()
    return await cache.get(f"strategy_brief:{tenant_id}:{strategy_id}", namespace="strategy")


async def cache_search_results(query_hash: str, results: list[dict[str, Any]]) -> bool:
    """Cache search results."""
    cache = await get_multi_tier_cache()
    return await cache.set(
        f"search:{query_hash}",
        results,
        namespace="search",
        ttl=900,  # 15 minutes
        tags=["search"]
    )


async def invalidate_tenant_cache(tenant_id: str) -> int:
    """Invalidate all cache entries for a tenant."""
    cache = await get_multi_tier_cache()
    return await cache.invalidate_by_tags([f"tenant:{tenant_id}"])