"""Tests for advanced caching and performance optimization system."""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

import pytest


class TestMemoryCache:
    """Test L1 in-memory cache functionality."""
    
    def test_memory_cache_initialization(self):
        """Test memory cache initialization."""
        from stratmaster_api.clients.advanced_cache import MemoryCache
        
        cache = MemoryCache(max_size=100, default_ttl=600)
        
        assert cache.max_size == 100
        assert cache.default_ttl == 600
        assert len(cache._cache) == 0
        assert cache.metrics.hits == 0
        assert cache.metrics.misses == 0
    
    def test_memory_cache_basic_operations(self):
        """Test basic memory cache operations."""
        from stratmaster_api.clients.advanced_cache import MemoryCache
        
        cache = MemoryCache()
        
        # Test set and get
        assert cache.set("key1", "value1", ttl=300)
        value = cache.get("key1")
        assert value == "value1"
        assert cache.metrics.hits == 1
        assert cache.metrics.sets == 1
        
        # Test cache miss
        missing = cache.get("nonexistent")
        assert missing is None
        assert cache.metrics.misses == 1
    
    def test_memory_cache_ttl_expiration(self):
        """Test TTL expiration in memory cache."""
        from stratmaster_api.clients.advanced_cache import MemoryCache, CacheEntry
        from unittest.mock import patch
        
        cache = MemoryCache()
        
        # Mock datetime for testing expiration
        with patch('stratmaster_api.clients.advanced_cache.datetime') as mock_datetime:
            now = datetime.now()
            mock_datetime.now.return_value = now
            
            # Set a value with short TTL
            cache.set("expired_key", "value", ttl=1)
            
            # Advance time past TTL
            mock_datetime.now.return_value = now + timedelta(seconds=2)
            
            # Should return None for expired key
            value = cache.get("expired_key")
            assert value is None
            
            # Key should be evicted from cache
            assert "expired_key" not in cache._cache
    
    def test_memory_cache_lru_eviction(self):
        """Test LRU eviction in memory cache."""
        from stratmaster_api.clients.advanced_cache import MemoryCache
        
        cache = MemoryCache(max_size=2)  # Small cache for testing
        
        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache._cache) == 2
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Add third key - should evict key2 (LRU)
        cache.set("key3", "value3")
        assert len(cache._cache) == 2
        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Newly added
    
    def test_memory_cache_tag_invalidation(self):
        """Test tag-based invalidation."""
        from stratmaster_api.clients.advanced_cache import MemoryCache
        
        cache = MemoryCache()
        
        # Set values with different tags
        cache.set("user:1", "data1", tags=["user", "tenant:a"])
        cache.set("user:2", "data2", tags=["user", "tenant:b"])
        cache.set("config:1", "data3", tags=["config", "tenant:a"])
        
        # Clear by user tag
        cleared = cache.clear_by_tags(["user"])
        assert cleared == 2  # Two user entries cleared
        
        # Only config entry should remain
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("config:1") == "data3"


class TestMultiTierCacheClient:
    """Test multi-tier cache client."""
    
    @pytest.mark.asyncio
    async def test_cache_client_initialization(self):
        """Test cache client initialization."""
        from stratmaster_api.clients.advanced_cache import MultiTierCacheClient
        
        with patch('stratmaster_api.clients.advanced_cache.aioredis') as mock_redis:
            mock_redis.from_url.return_value = AsyncMock()
            
            client = MultiTierCacheClient(memory_cache_size=500)
            await client.connect()
            
            assert client.memory_cache.max_size == 500
            assert client.redis_enabled
    
    @pytest.mark.asyncio
    async def test_cache_client_memory_only_fallback(self):
        """Test cache client with Redis unavailable."""
        from stratmaster_api.clients.advanced_cache import MultiTierCacheClient
        
        # Simulate Redis unavailable
        with patch('stratmaster_api.clients.advanced_cache.aioredis', None):
            client = MultiTierCacheClient()
            await client.connect()
            
            assert not client.redis_enabled
            assert client.redis_client is None
    
    @pytest.mark.asyncio
    async def test_multi_tier_get_memory_hit(self):
        """Test multi-tier get with memory cache hit."""
        from stratmaster_api.clients.advanced_cache import MultiTierCacheClient
        
        client = MultiTierCacheClient()
        await client.connect()
        
        # Populate memory cache directly
        test_key = client._make_key("test", "key1")
        client.memory_cache.set(test_key, "cached_value")
        
        # Should hit memory cache
        value, cache_level = await client.get("key1", "test")
        assert value == "cached_value"
        assert cache_level == "memory"
    
    @pytest.mark.asyncio
    async def test_multi_tier_get_redis_hit(self):
        """Test multi-tier get with Redis cache hit."""
        from stratmaster_api.clients.advanced_cache import MultiTierCacheClient
        
        with patch('stratmaster_api.clients.advanced_cache.aioredis') as mock_redis:
            # Setup mock Redis client
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.get.return_value = json.dumps("redis_value")
            
            client = MultiTierCacheClient()
            await client.connect()
            
            # Should hit Redis cache and populate memory
            value, cache_level = await client.get("key1", "test")
            assert value == "redis_value"
            assert cache_level == "redis"
            
            # Memory cache should now contain the value
            test_key = client._make_key("test", "key1")
            memory_value = client.memory_cache.get(test_key)
            assert memory_value == "redis_value"
    
    @pytest.mark.asyncio
    async def test_multi_tier_set(self):
        """Test multi-tier set operation."""
        from stratmaster_api.clients.advanced_cache import MultiTierCacheClient
        
        with patch('stratmaster_api.clients.advanced_cache.aioredis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.setex.return_value = True
            mock_client.sadd.return_value = 1
            mock_client.expire.return_value = True
            
            client = MultiTierCacheClient()
            await client.connect()
            
            # Set value with tags
            success = await client.set("key1", "value1", "test", ttl=600, tags=["tag1"])
            assert success
            
            # Should be in memory cache
            test_key = client._make_key("test", "key1")
            memory_value = client.memory_cache.get(test_key)
            assert memory_value == "value1"
            
            # Should have called Redis
            mock_client.setex.assert_called_once()
            mock_client.sadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_decorator(self):
        """Test async function caching decorator."""
        from stratmaster_api.clients.advanced_cache import MultiTierCacheClient
        
        client = MultiTierCacheClient()
        await client.connect()
        
        call_count = 0
        
        @client.cache_async("test_func", ttl=300)
        async def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate work
            return x + y
        
        # First call should execute function
        result1 = await expensive_function(5, 3)
        assert result1 == 8
        assert call_count == 1
        
        # Second call should hit cache
        result2 = await expensive_function(5, 3)
        assert result2 == 8
        assert call_count == 1  # Function not called again
        
        # Different arguments should execute function again
        result3 = await expensive_function(10, 2)
        assert result3 == 12
        assert call_count == 2


class TestPerformanceProfilingMiddleware:
    """Test performance profiling middleware."""
    
    @pytest.mark.asyncio
    async def test_performance_middleware_timing(self):
        """Test that middleware correctly times requests."""
        from stratmaster_api.middleware.performance_cache import PerformanceProfilingMiddleware
        from fastapi import Request, Response
        from unittest.mock import AsyncMock
        
        # Mock app
        async def mock_app(request):
            await asyncio.sleep(0.1)  # Simulate processing time
            return Response(content="test response", status_code=200)
        
        middleware = PerformanceProfilingMiddleware(mock_app, performance_budget_ms=50)
        
        # Mock request
        mock_request = AsyncMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        response = await middleware.dispatch(mock_request, mock_app)
        
        # Check response headers
        assert "X-Process-Time" in response.headers
        assert "X-Request-ID" in response.headers
        
        # Process time should be > 100ms
        process_time = float(response.headers["X-Process-Time"])
        assert process_time > 100
        
        # Should have performance warning (exceeded 50ms budget)
        assert response.headers.get("X-Performance-Warning") == "true"
    
    def test_performance_middleware_stats_collection(self):
        """Test performance statistics collection."""
        from stratmaster_api.middleware.performance_cache import PerformanceProfilingMiddleware
        
        middleware = PerformanceProfilingMiddleware(None)
        
        # Simulate some requests
        middleware._update_endpoint_stats("/api/test", 150.0, True)
        middleware._update_endpoint_stats("/api/test", 200.0, True)
        middleware._update_endpoint_stats("/api/test", 100.0, False)
        
        report = middleware.get_performance_report()
        
        assert "/api/test" in report
        endpoint_stats = report["/api/test"]
        
        assert endpoint_stats["total_requests"] == 3
        assert endpoint_stats["successful_requests"] == 2
        assert endpoint_stats["success_rate"] == 2/3
        assert endpoint_stats["avg_time_ms"] == 150.0  # (150+200+100)/3
        assert endpoint_stats["min_time_ms"] == 100.0
        assert endpoint_stats["max_time_ms"] == 200.0


class TestResponseCachingMiddleware:
    """Test response caching middleware."""
    
    def test_cacheable_request_detection(self):
        """Test detection of cacheable requests."""
        from stratmaster_api.middleware.performance_cache import ResponseCachingMiddleware
        from fastapi import Request
        from unittest.mock import Mock
        
        middleware = ResponseCachingMiddleware(None)
        
        # Mock cacheable request
        cacheable_request = Mock(spec=Request)
        cacheable_request.method = "GET"
        cacheable_request.url.path = "/performance/metrics"
        cacheable_request.headers = {}
        
        assert middleware._is_cacheable_request(cacheable_request)
        
        # Mock non-cacheable request (POST)
        non_cacheable_request = Mock(spec=Request)
        non_cacheable_request.method = "POST"
        non_cacheable_request.url.path = "/performance/metrics"
        non_cacheable_request.headers = {}
        
        assert not middleware._is_cacheable_request(non_cacheable_request)
        
        # Mock request with no-cache header
        no_cache_request = Mock(spec=Request)
        no_cache_request.method = "GET"
        no_cache_request.url.path = "/performance/metrics"
        no_cache_request.headers = {"cache-control": "no-cache"}
        
        assert not middleware._is_cacheable_request(no_cache_request)
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        from stratmaster_api.middleware.performance_cache import ResponseCachingMiddleware
        from fastapi import Request
        from unittest.mock import Mock
        
        middleware = ResponseCachingMiddleware(None)
        
        # Mock request
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/performance/metrics"
        mock_request.url.query = "tenant_id=123"
        mock_request.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip"
        }
        
        key1 = middleware._generate_cache_key(mock_request)
        
        # Same request should generate same key
        key2 = middleware._generate_cache_key(mock_request)
        assert key1 == key2
        
        # Different query should generate different key
        mock_request.url.query = "tenant_id=456"
        key3 = middleware._generate_cache_key(mock_request)
        assert key1 != key3
    
    def test_ttl_calculation(self):
        """Test TTL calculation for different endpoints."""
        from stratmaster_api.middleware.performance_cache import ResponseCachingMiddleware
        from fastapi import Request, Response
        from unittest.mock import Mock
        
        middleware = ResponseCachingMiddleware(None, default_ttl=300)
        
        # Performance endpoint should have shorter TTL
        perf_request = Mock(spec=Request)
        perf_request.url.path = "/performance/metrics"
        
        perf_response = Mock(spec=Response)
        perf_response.headers = {}
        
        perf_ttl = middleware._calculate_ttl(perf_request, perf_response)
        assert perf_ttl == 60
        
        # Strategy endpoint should have longer TTL
        strategy_request = Mock(spec=Request)
        strategy_request.url.path = "/strategy/generate"
        
        strategy_response = Mock(spec=Response)
        strategy_response.headers = {}
        
        strategy_ttl = middleware._calculate_ttl(strategy_request, strategy_response)
        assert strategy_ttl == 900
        
        # Response with explicit cache-control should respect it
        explicit_response = Mock(spec=Response)
        explicit_response.headers = {"cache-control": "max-age=120"}
        
        explicit_ttl = middleware._calculate_ttl(perf_request, explicit_response)
        assert explicit_ttl == 120  # min(120, 300)


class TestCacheInvalidation:
    """Test cache invalidation functionality."""
    
    @pytest.mark.asyncio
    async def test_tag_based_invalidation(self):
        """Test invalidation by tags."""
        from stratmaster_api.clients.advanced_cache import MultiTierCacheClient
        
        with patch('stratmaster_api.clients.advanced_cache.aioredis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.smembers.return_value = ["key1", "key2"]
            
            client = MultiTierCacheClient()
            await client.connect()
            
            # Set some values with tags
            await client.set("key1", "value1", tags=["user", "tenant:123"])
            await client.set("key2", "value2", tags=["user"])
            await client.set("key3", "value3", tags=["config"])
            
            # Invalidate by user tag
            invalidated = await client.invalidate_by_tags(["user"])
            
            # Should have called Redis for tag invalidation
            mock_client.smembers.assert_called()
            mock_client.delete.assert_called()
            
            # Memory cache should have cleared tagged entries
            assert invalidated >= 2  # At least the memory cache entries
    
    @pytest.mark.asyncio
    async def test_endpoint_pattern_invalidation(self):
        """Test invalidation by endpoint pattern."""
        from stratmaster_api.middleware.performance_cache import invalidate_cache_by_endpoint
        
        with patch('stratmaster_api.middleware.performance_cache.get_multi_tier_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.invalidate_by_tags.return_value = 5
            mock_get_cache.return_value = mock_cache
            
            # Invalidate strategy endpoints
            count = await invalidate_cache_by_endpoint("/strategy/generate")
            
            assert count == 5
            mock_cache.invalidate_by_tags.assert_called_with(["strategy"])


class TestCachePerformanceOptimization:
    """Test cache performance optimizations."""
    
    def test_cache_metrics_tracking(self):
        """Test cache metrics collection."""
        from stratmaster_api.clients.advanced_cache import CacheMetrics
        
        metrics = CacheMetrics()
        
        # Simulate cache operations
        metrics.hits = 80
        metrics.misses = 20
        metrics.sets = 100
        metrics.total_latency_ms = 500.0
        
        assert metrics.hit_rate == 0.8  # 80/100
        assert metrics.avg_latency_ms == 2.5  # 500/(80+20+100)
    
    def test_performance_percentile_calculations(self):
        """Test performance percentile calculations."""
        times = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        
        def calculate_percentiles(times_list):
            if not times_list:
                return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}
            
            sorted_times = sorted(times_list)
            length = len(sorted_times)
            
            return {
                "p50": sorted_times[int(length * 0.5)],
                "p95": sorted_times[int(length * 0.95)],
                "p99": sorted_times[int(length * 0.99)],
                "avg": sum(sorted_times) / length,
            }
        
        percentiles = calculate_percentiles(times)
        
        assert percentiles["p50"] == 60.0  # 50th percentile
        assert percentiles["p95"] == 100.0  # 95th percentile 
        assert percentiles["avg"] == 55.0    # Average


class TestFeatureFlags:
    """Test caching feature flag functionality."""
    
    def test_response_cache_v2_feature_flag(self):
        """Test response cache v2 feature flag."""
        from stratmaster_api.clients.advanced_cache import is_response_cache_v2_enabled
        
        # Test disabled by default
        with patch.dict(os.environ, {}, clear=True):
            assert not is_response_cache_v2_enabled()
        
        # Test enabled when set
        with patch.dict(os.environ, {"ENABLE_RESPONSE_CACHE_V2": "true"}):
            assert is_response_cache_v2_enabled()
    
    def test_edge_cache_hints_feature_flag(self):
        """Test edge cache hints feature flag."""
        from stratmaster_api.clients.advanced_cache import is_edge_cache_hints_enabled
        
        # Test disabled by default  
        with patch.dict(os.environ, {}, clear=True):
            assert not is_edge_cache_hints_enabled()
        
        # Test enabled when set
        with patch.dict(os.environ, {"ENABLE_EDGE_CACHE_HINTS": "true"}):
            assert is_edge_cache_hints_enabled()