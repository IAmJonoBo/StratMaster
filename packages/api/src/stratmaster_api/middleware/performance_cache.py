"""FastAPI middleware for performance profiling and advanced caching.

Provides:
- Per-endpoint timing middleware with Prometheus integration
- Response caching middleware with surrogate keys
- CDN/Edge cache hints and invalidation
- Performance budgets and alerting
"""

from __future__ import annotations

import logging
import time
from typing import Any
from collections.abc import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Import advanced cache utilities from clients package (not middleware)
from ..clients.advanced_cache import (
    get_multi_tier_cache,
    is_edge_cache_hints_enabled,
    is_response_cache_v2_enabled,
)

logger = logging.getLogger(__name__)

# Try to import Prometheus metrics
try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True

    # Metrics for caching middleware
    CACHE_HITS = Counter(
        'cache_hits_total', 'Total cache hits', ['endpoint', 'cache_level']
    )
    CACHE_MISSES = Counter('cache_misses_total', 'Total cache misses', ['endpoint'])
    CACHE_OPERATIONS = Counter(
        'cache_operations_total', 'Total cache operations', ['operation', 'status']
    )
    ENDPOINT_LATENCY = Histogram(
        'endpoint_latency_seconds', 'Endpoint response time', ['endpoint', 'method']
    )
    RESPONSE_SIZE_BYTES = Histogram(
        'response_size_bytes', 'Response size in bytes', ['endpoint']
    )
    ACTIVE_REQUESTS = Gauge('active_requests', 'Number of active requests', ['endpoint'])

except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus metrics not available")


class PerformanceProfilingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive performance profiling."""

    def __init__(self, app, performance_budget_ms: int = 2000):
        super().__init__(app)
        self.performance_budget_ms = performance_budget_ms
        self.endpoint_stats = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Profile request processing time."""
        start_time = time.perf_counter()
        endpoint = f"{request.method} {request.url.path}"

        # Track active requests
        if PROMETHEUS_AVAILABLE:
            ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()

        try:
            response = await call_next(request)

            # Calculate timing
            process_time = (time.perf_counter() - start_time) * 1000

            # Update statistics
            self._update_endpoint_stats(endpoint, process_time, True)

            # Record metrics
            if PROMETHEUS_AVAILABLE:
                ENDPOINT_LATENCY.labels(
                    endpoint=endpoint, method=request.method
                ).observe(process_time / 1000)

                # Get response size
                if hasattr(response, 'body'):
                    response_size = len(response.body) if response.body else 0
                    RESPONSE_SIZE_BYTES.labels(endpoint=endpoint).observe(response_size)

            # Add performance headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = str(uuid4())

            # Performance budget warning
            if process_time > self.performance_budget_ms:
                logger.warning(
                    f"Performance budget exceeded: {endpoint} took {process_time:.1f}ms "
                    f"(budget: {self.performance_budget_ms}ms)"
                )
                response.headers["X-Performance-Warning"] = "true"

            return response

        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            self._update_endpoint_stats(endpoint, process_time, False)
            logger.error(f"Request failed after {process_time:.1f}ms: {e}")
            raise

        finally:
            if PROMETHEUS_AVAILABLE:
                ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()

    def _update_endpoint_stats(self, endpoint: str, process_time: float, success: bool):
        """Update endpoint performance statistics."""
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                "total_requests": 0,
                "total_time_ms": 0,
                "successful_requests": 0,
                "max_time_ms": 0,
                "min_time_ms": float('inf')
            }

        stats = self.endpoint_stats[endpoint]
        stats["total_requests"] += 1
        stats["total_time_ms"] += process_time
        stats["max_time_ms"] = max(stats["max_time_ms"], process_time)
        stats["min_time_ms"] = min(stats["min_time_ms"], process_time)

        if success:
            stats["successful_requests"] += 1

    def get_performance_report(self) -> dict[str, Any]:
        """Get comprehensive performance report."""
        report = {}

        for endpoint, stats in self.endpoint_stats.items():
            avg_time = stats["total_time_ms"] / stats["total_requests"]
            success_rate = stats["successful_requests"] / stats["total_requests"]

            report[endpoint] = {
                "total_requests": stats["total_requests"],
                "successful_requests": stats["successful_requests"],
                "success_rate": success_rate,
                "avg_time_ms": avg_time,
                "min_time_ms": stats["min_time_ms"],
                "max_time_ms": stats["max_time_ms"],
                "budget_exceeded_rate": sum(
                    1 for _ in range(stats["total_requests"])
                    if avg_time > self.performance_budget_ms
                ) / stats["total_requests"]
            }

        return report


class ResponseCachingMiddleware(BaseHTTPMiddleware):
    """Advanced response caching middleware with multi-tier support."""

    def __init__(
        self,
        app,
        cacheable_methods: list[str] | None = None,
        cacheable_paths: list[str] | None = None,
        default_ttl: int = 300
    ):
        super().__init__(app)
        self.cacheable_methods = cacheable_methods or ["GET", "HEAD"]
        self.cacheable_paths = cacheable_paths or ["/performance/", "/strategy/", "/search/"]
        self.default_ttl = default_ttl

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle request caching."""
        if not is_response_cache_v2_enabled():
            return await call_next(request)

        # Check if request is cacheable
        if not self._is_cacheable_request(request):
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        try:
            # Try to get from cache
            cache = await get_multi_tier_cache()
            cached_response, cache_level = await cache.get(cache_key, namespace="responses")

            if cached_response is not None:
                # Cache hit
                if PROMETHEUS_AVAILABLE:
                    endpoint = f"{request.method} {request.url.path}"
                    CACHE_HITS.labels(endpoint=endpoint, cache_level=cache_level).inc()

                logger.debug(f"Cache hit ({cache_level}) for {cache_key}")

                response = Response(
                    content=cached_response["body"],
                    status_code=cached_response["status_code"],
                    headers=cached_response.get("headers", {}),
                    media_type=cached_response.get("media_type")
                )

                # Add cache headers
                response.headers["X-Cache-Status"] = f"HIT-{cache_level.upper()}"
                response.headers["X-Cache-Key"] = cache_key[:16] + "..."

                return response

            # Cache miss - execute request
            response = await call_next(request)

            # Cache the response if it's successful
            if self._is_cacheable_response(response):
                await self._cache_response(cache, cache_key, request, response)

                if PROMETHEUS_AVAILABLE:
                    endpoint = f"{request.method} {request.url.path}"
                    CACHE_MISSES.labels(endpoint=endpoint).inc()
                    CACHE_OPERATIONS.labels(operation="set", status="success").inc()

            # Add cache headers
            response.headers["X-Cache-Status"] = "MISS"
            response.headers["X-Cache-Key"] = cache_key[:16] + "..."

            # Add CDN/Edge cache hints
            if is_edge_cache_hints_enabled():
                self._add_edge_cache_headers(response, request)

            return response

        except Exception as e:
            logger.error(f"Caching middleware error: {e}")
            if PROMETHEUS_AVAILABLE:
                CACHE_OPERATIONS.labels(operation="get", status="error").inc()

            # Return uncached response on error
            return await call_next(request)

    def _is_cacheable_request(self, request: Request) -> bool:
        """Check if request is cacheable."""
        # Check method
        if request.method not in self.cacheable_methods:
            return False

        # Check path
        if not any(request.url.path.startswith(path) for path in self.cacheable_paths):
            return False

        # Check for cache-control headers
        if request.headers.get("cache-control", "").lower() in ["no-cache", "no-store"]:
            return False

        return True

    def _is_cacheable_response(self, response: Response) -> bool:
        """Check if response is cacheable."""
        # Only cache successful responses
        if response.status_code not in [200, 203, 300, 301, 404, 410]:
            return False

        # Check for cache-control headers
        cache_control = response.headers.get("cache-control", "").lower()
        if any(directive in cache_control for directive in ["no-cache", "no-store", "private"]):
            return False

        return True

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        import hashlib

        # Include method, path, query params, and relevant headers
        key_components = [
            request.method,
            str(request.url.path),
            str(request.url.query),
            request.headers.get("accept", ""),
            request.headers.get("accept-encoding", ""),
        ]

        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _cache_response(
        self,
        cache: Any,
        cache_key: str,
        request: Request,
        response: Response
    ) -> None:
        """Cache response with metadata."""
        try:
            # Read response body robustly
            response_body_bytes: bytes = b""
            body_attr = getattr(response, "body", None)
            if body_attr is not None:
                if isinstance(body_attr, (bytes, bytearray)):
                    response_body_bytes = bytes(body_attr)
                elif isinstance(body_attr, memoryview):
                    response_body_bytes = body_attr.tobytes()
                elif isinstance(body_attr, str):
                    response_body_bytes = body_attr.encode("utf-8")
            else:
                body_iter = getattr(response, "body_iterator", None)
                if body_iter is not None:
                    async for chunk in body_iter:
                        response_body_bytes += bytes(chunk)

            # Prepare cache data
            cache_data = {
                "body": response_body_bytes.decode("utf-8") if response_body_bytes else "",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": getattr(response, "media_type", "application/json")
            }

            # Determine TTL based on response
            ttl = self._calculate_ttl(request, response)

            # Generate cache tags
            tags = self._generate_cache_tags(request)

            # Store in cache
            await cache.set(cache_key, cache_data, namespace="responses", ttl=ttl, tags=tags)

            logger.debug(f"Cached response for {cache_key} with TTL {ttl}s")

        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            if PROMETHEUS_AVAILABLE:
                CACHE_OPERATIONS.labels(operation="set", status="error").inc()

    def _calculate_ttl(self, request: Request, response: Response) -> int:
        """Calculate appropriate TTL for response."""
        # Check for explicit cache-control max-age
        cache_control = response.headers.get("cache-control", "")
        if "max-age=" in cache_control:
            try:
                max_age = int(cache_control.split("max-age=")[1].split(",")[0])
                return min(max_age, self.default_ttl)
            except (ValueError, IndexError):
                pass

        # Endpoint-specific TTLs
        path = request.url.path
        if path.startswith("/performance/"):
            return 60  # Performance data changes frequently
        elif path.startswith("/strategy/"):
            return 900  # Strategy data less frequent
        elif path.startswith("/search/"):
            return 300  # Search results moderate frequency

        return self.default_ttl

    def _generate_cache_tags(self, request: Request) -> list[str]:
        """Generate cache tags for invalidation."""
        tags = []

        # Add endpoint-based tags
        if request.url.path.startswith("/strategy/"):
            tags.append("strategy")
        elif request.url.path.startswith("/performance/"):
            tags.append("performance")
        elif request.url.path.startswith("/search/"):
            tags.append("search")

        # Add tenant ID if available (from headers or query params)
        tenant_id = request.headers.get("x-tenant-id") or request.query_params.get("tenant_id")
        if tenant_id:
            tags.append(f"tenant:{tenant_id}")

        return tags

    def _add_edge_cache_headers(self, response: Response, request: Request) -> None:
        """Add CDN/Edge cache headers."""
        # Surrogate-Control for CDN caching
        surrogate_control = []

        # Add max-age for CDN
        if request.url.path.startswith("/performance/"):
            surrogate_control.append("max-age=60")
        else:
            surrogate_control.append("max-age=300")

        # Add stale-while-revalidate for better UX
        surrogate_control.append("stale-while-revalidate=30")

        response.headers["Surrogate-Control"] = ", ".join(surrogate_control)

        # Surrogate keys for purging
        surrogate_keys = []
        if request.url.path.startswith("/strategy/"):
            surrogate_keys.append("strategy")
        elif request.url.path.startswith("/performance/"):
            surrogate_keys.append("performance")

        if surrogate_keys:
            response.headers["Surrogate-Key"] = " ".join(surrogate_keys)

        # Vary header for correct caching
        vary_headers = ["Accept", "Accept-Encoding"]
        if "x-tenant-id" in request.headers:
            vary_headers.append("X-Tenant-ID")

        response.headers["Vary"] = ", ".join(vary_headers)


# Utility functions for cache invalidation
async def invalidate_cache_by_endpoint(endpoint_pattern: str) -> int:
    """Invalidate cache entries for specific endpoint pattern."""
    cache = await get_multi_tier_cache()

    # Map endpoint patterns to tags
    tag_mapping = {
        "/strategy/": ["strategy"],
        "/performance/": ["performance"],
        "/search/": ["search"]
    }

    tags_to_invalidate = []
    for pattern, tags in tag_mapping.items():
        if endpoint_pattern.startswith(pattern):
            tags_to_invalidate.extend(tags)

    if tags_to_invalidate:
        return await cache.invalidate_by_tags(tags_to_invalidate)

    return 0


async def get_cache_performance_report() -> dict[str, Any]:
    """Get comprehensive cache performance report."""
    cache = await get_multi_tier_cache()
    stats = cache.get_performance_stats()

    # Calculate cache efficiency
    memory_stats = stats.get("memory_cache", {})
    hit_rate = memory_stats.get("hit_rate", 0.0)

    # Performance analysis
    performance = stats.get("performance", {})
    total_gets = performance.get("total_get", {})

    return {
        "cache_efficiency": {
            "memory_hit_rate": hit_rate,
            "total_operations": stats.get("total_operations", 0),
            "redis_available": stats.get("redis_enabled", False)
        },
        "performance": {
            "avg_get_latency_ms": total_gets.get("avg", 0.0),
            "p95_get_latency_ms": total_gets.get("p95", 0.0),
            "p99_get_latency_ms": total_gets.get("p99", 0.0)
        },
        "memory_cache": memory_stats,
        "feature_flags": {
            "response_cache_v2": is_response_cache_v2_enabled(),
            "edge_cache_hints": is_edge_cache_hints_enabled()
        }
    }
