"""Admin endpoints for cache management and performance monitoring.

Provides administrative endpoints for:
- Cache statistics and performance reports
- Manual cache invalidation
- Performance profiling data
- Cache configuration management
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from ..clients.advanced_cache import get_multi_tier_cache, invalidate_tenant_cache
from ..middleware.performance_cache import (
    get_cache_performance_report, 
    invalidate_cache_by_endpoint,
    is_response_cache_v2_enabled,
    is_edge_cache_hints_enabled
)

logger = logging.getLogger(__name__)


class CacheInvalidationRequest(BaseModel):
    """Request for cache invalidation."""
    tags: list[str] | None = None
    endpoint_pattern: str | None = None
    tenant_id: str | None = None


class CacheInvalidationResponse(BaseModel):
    """Response for cache invalidation."""
    invalidated_count: int
    operation: str
    message: str


class CacheStatsResponse(BaseModel):
    """Response for cache statistics."""
    memory_cache: dict[str, Any]
    performance: dict[str, Any]
    feature_flags: dict[str, bool]
    total_operations: int


# Create admin router
router = APIRouter(prefix="/admin/cache", tags=["Cache Admin"])


@router.get("/status")
async def get_cache_status() -> dict[str, Any]:
    """Get overall cache system status."""
    try:
        cache = await get_multi_tier_cache()
        stats = cache.get_performance_stats()
        
        return {
            "status": "operational",
            "redis_connected": stats.get("redis_enabled", False),
            "memory_cache_size": stats.get("memory_cache", {}).get("size", 0),
            "total_operations": stats.get("total_operations", 0),
            "feature_flags": {
                "response_cache_v2": is_response_cache_v2_enabled(),
                "edge_cache_hints": is_edge_cache_hints_enabled()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get cache status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache status")


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_statistics() -> CacheStatsResponse:
    """Get detailed cache performance statistics."""
    try:
        report = await get_cache_performance_report()
        
        return CacheStatsResponse(
            memory_cache=report["memory_cache"],
            performance=report["performance"],
            feature_flags=report["feature_flags"],
            total_operations=report["cache_efficiency"]["total_operations"]
        )
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")


@router.get("/performance")
async def get_cache_performance_detailed() -> dict[str, Any]:
    """Get detailed cache performance analysis."""
    try:
        cache = await get_multi_tier_cache()
        stats = cache.get_performance_stats()
        
        # Calculate performance insights
        performance = stats.get("performance", {})
        
        insights = {
            "efficiency_analysis": {},
            "performance_trends": {},
            "recommendations": []
        }
        
        # Analyze cache efficiency
        memory_cache = stats.get("memory_cache", {})
        hit_rate = memory_cache.get("hit_rate", 0.0)
        
        if hit_rate < 0.7:
            insights["recommendations"].append(
                "Consider increasing memory cache size - hit rate is below 70%"
            )
        elif hit_rate > 0.9:
            insights["recommendations"].append(
                "Excellent cache hit rate - consider reducing TTL for fresher data"
            )
        
        # Analyze latency performance
        total_get = performance.get("total_get", {})
        avg_latency = total_get.get("avg", 0.0)
        p95_latency = total_get.get("p95", 0.0)
        
        if avg_latency > 10:  # >10ms average
            insights["recommendations"].append(
                "Average cache latency is high - consider optimizing cache key generation"
            )
        
        if p95_latency > 50:  # >50ms p95
            insights["recommendations"].append(
                "P95 latency is concerning - investigate Redis connection performance"
            )
        
        insights["efficiency_analysis"] = {
            "hit_rate": hit_rate,
            "hit_rate_grade": "A" if hit_rate > 0.9 else "B" if hit_rate > 0.7 else "C",
            "avg_latency_ms": avg_latency,
            "latency_grade": "A" if avg_latency < 5 else "B" if avg_latency < 15 else "C"
        }
        
        return {
            "cache_stats": stats,
            "insights": insights,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get detailed performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance data")


@router.post("/invalidate", response_model=CacheInvalidationResponse)
async def invalidate_cache(
    request: CacheInvalidationRequest,
    background_tasks: BackgroundTasks
) -> CacheInvalidationResponse:
    """Manually invalidate cache entries."""
    try:
        total_invalidated = 0
        operations = []
        
        # Invalidate by tags
        if request.tags:
            cache = await get_multi_tier_cache()
            count = await cache.invalidate_by_tags(request.tags)
            total_invalidated += count
            operations.append(f"tags: {', '.join(request.tags)}")
        
        # Invalidate by endpoint pattern
        if request.endpoint_pattern:
            count = await invalidate_cache_by_endpoint(request.endpoint_pattern)
            total_invalidated += count
            operations.append(f"endpoint: {request.endpoint_pattern}")
        
        # Invalidate by tenant ID
        if request.tenant_id:
            count = await invalidate_tenant_cache(request.tenant_id)
            total_invalidated += count
            operations.append(f"tenant: {request.tenant_id}")
        
        if not operations:
            raise HTTPException(
                status_code=400,
                detail="Must specify at least one invalidation method (tags, endpoint_pattern, or tenant_id)"
            )
        
        operation_desc = ", ".join(operations)
        
        logger.info(f"Cache invalidated: {total_invalidated} entries via {operation_desc}")
        
        return CacheInvalidationResponse(
            invalidated_count=total_invalidated,
            operation=operation_desc,
            message=f"Successfully invalidated {total_invalidated} cache entries"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(status_code=500, detail="Cache invalidation failed")


@router.post("/clear")
async def clear_all_cache(
    confirm: bool = Query(False, description="Must be true to confirm cache clearing")
) -> dict[str, Any]:
    """Clear all cache data (requires confirmation)."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear all cache data"
        )
    
    try:
        cache = await get_multi_tier_cache()
        
        # Clear memory cache
        cache.memory_cache._cache.clear()
        cache.memory_cache._access_order.clear()
        
        # Clear Redis cache (if available)
        redis_cleared = False
        if cache.redis_client:
            try:
                await cache.redis_client.flushdb()
                redis_cleared = True
            except Exception as e:
                logger.warning(f"Failed to clear Redis cache: {e}")
        
        logger.warning("ALL CACHE DATA CLEARED - this may impact performance")
        
        return {
            "message": "All cache data cleared",
            "memory_cache_cleared": True,
            "redis_cache_cleared": redis_cleared,
            "warning": "Cache clearing may temporarily impact performance"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/memory/stats")
async def get_memory_cache_stats() -> dict[str, Any]:
    """Get detailed memory cache statistics."""
    try:
        cache = await get_multi_tier_cache()
        memory_stats = cache.memory_cache.get_stats()
        
        # Add additional insights
        size_utilization = memory_stats["size"] / memory_stats["max_size"]
        
        insights = {
            "size_utilization": size_utilization,
            "utilization_grade": (
                "HIGH" if size_utilization > 0.8 else
                "MEDIUM" if size_utilization > 0.5 else
                "LOW"
            ),
            "recommendations": []
        }
        
        if size_utilization > 0.9:
            insights["recommendations"].append("Consider increasing memory cache size")
        elif size_utilization < 0.3:
            insights["recommendations"].append("Memory cache may be oversized")
        
        if memory_stats["hit_rate"] < 0.7:
            insights["recommendations"].append("Low hit rate - review caching strategy")
        
        return {
            "stats": memory_stats,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory cache statistics")


@router.get("/keys/sample")
async def sample_cache_keys(limit: int = Query(10, ge=1, le=100)) -> dict[str, Any]:
    """Get a sample of current cache keys for debugging."""
    try:
        cache = await get_multi_tier_cache()
        
        # Sample from memory cache
        memory_keys = list(cache.memory_cache._cache.keys())[:limit]
        
        # Sample from Redis if available
        redis_keys = []
        if cache.redis_client:
            try:
                redis_keys = await cache.redis_client.keys("*")
                redis_keys = redis_keys[:limit]
            except Exception as e:
                logger.warning(f"Failed to sample Redis keys: {e}")
        
        return {
            "memory_cache_sample": memory_keys,
            "redis_cache_sample": redis_keys,
            "total_memory_keys": len(cache.memory_cache._cache),
            "sample_limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to sample cache keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to sample cache keys")


@router.post("/warmup")
async def warmup_cache(
    background_tasks: BackgroundTasks,
    endpoints: list[str] = Query([], description="Specific endpoints to warm up")
) -> dict[str, str]:
    """Warm up cache with commonly accessed data."""
    def warmup_task():
        """Background task to warm up cache."""
        try:
            # This would implement cache warming logic
            # For now, just log the operation
            logger.info(f"Cache warmup initiated for endpoints: {endpoints or 'all common endpoints'}")
            
            # In a real implementation, this would:
            # 1. Identify commonly accessed endpoints
            # 2. Make internal requests to populate cache
            # 3. Pre-compute expensive operations
            # 4. Load frequently accessed data
            
        except Exception as e:
            logger.error(f"Cache warmup failed: {e}")
    
    background_tasks.add_task(warmup_task)
    
    return {
        "message": "Cache warmup initiated",
        "status": "running_in_background"
    }


@router.get("/config")
async def get_cache_configuration() -> dict[str, Any]:
    """Get current cache configuration."""
    try:
        cache = await get_multi_tier_cache()
        
        config = {
            "memory_cache": {
                "max_size": cache.memory_cache.max_size,
                "default_ttl": cache.memory_cache.default_ttl,
                "current_size": len(cache.memory_cache._cache)
            },
            "redis": {
                "enabled": cache.redis_enabled,
                "connected": cache.redis_client is not None,
                "url": cache.redis_url if cache.redis_enabled else None
            },
            "feature_flags": {
                "response_cache_v2": is_response_cache_v2_enabled(),
                "edge_cache_hints": is_edge_cache_hints_enabled()
            },
            "default_ttl": cache.default_ttl
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get cache configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache configuration")