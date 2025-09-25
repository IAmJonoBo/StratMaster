"""Lightweight advanced cache utilities used by performance_cache middleware.

This module provides a simple in-memory multi-tier cache facade with a
compatible API for tests. In production, this would wrap Redis and other
backends. Here we keep it minimal but feature-complete for our test needs.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

_CACHE_SINGLETON: MultiTierCache | None = None


def is_response_cache_v2_enabled() -> bool:
    """Feature flag to enable response cache v2 (default: enabled)."""
    return os.getenv("ENABLE_RESPONSE_CACHE_V2", "true").lower() == "true"


def is_edge_cache_hints_enabled() -> bool:
    """Feature flag to enable CDN/Edge cache hints (default: enabled)."""
    return os.getenv("ENABLE_EDGE_CACHE_HINTS", "true").lower() == "true"


async def get_multi_tier_cache() -> MultiTierCache:
    """Return the process-wide cache instance.

    Async for API compatibility with potential async backends.
    """
    global _CACHE_SINGLETON
    if _CACHE_SINGLETON is None:
        _CACHE_SINGLETON = MultiTierCache()
    await asyncio_sleep_noop()
    return _CACHE_SINGLETON


@dataclass
class _CacheEntry:
    value: Any
    ttl: int | None
    set_time: float
    tags: set[str]


class MultiTierCache:
    """Simple in-memory cache with tag invalidation and perf stats."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, _CacheEntry]] = {}
        self._tags: dict[str, set[tuple[str, str]]] = {}  # tag -> {(namespace, key)}
        self._get_latencies_ms: list[float] = []
        self._gets_total = 0
        self._gets_hits = 0
        self._operations_total = 0

    def _now(self) -> float:
        return time.time()

    def _is_expired(self, entry: _CacheEntry) -> bool:
        if entry.ttl is None:
            return False
        return (self._now() - entry.set_time) > entry.ttl

    async def get(self, key: str, *, namespace: str) -> tuple[Any | None, str | None]:
        start = time.perf_counter()
        self._gets_total += 1
        ns = self._store.get(namespace, {})
        entry = ns.get(key)
        value = None
        level: str | None = None
        if entry is not None and not self._is_expired(entry):
            self._gets_hits += 1
            value = entry.value
            level = "memory"
        else:
            # Clean up expired
            if entry is not None:
                ns.pop(key, None)
        latency_ms = (time.perf_counter() - start) * 1000
        self._get_latencies_ms.append(latency_ms)
        # Ensure function remains async
        await asyncio_sleep_noop()
        return value, level

    async def set(
        self,
        key: str,
        value: Any,
        *,
        namespace: str,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        ns = self._store.setdefault(namespace, {})
        entry = _CacheEntry(value=value, ttl=ttl, set_time=self._now(), tags=set(tags or []))
        ns[key] = entry
        # Index tags
        for tag in entry.tags:
            self._tags.setdefault(tag, set()).add((namespace, key))
        self._operations_total += 1
        await asyncio_sleep_noop()

    async def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidate all entries associated with any of the provided tags."""
        invalidated = 0
        seen: set[tuple[str, str]] = set()
        for tag in tags:
            for ns_key in tuple(self._tags.get(tag, set())):
                if ns_key in seen:
                    continue
                seen.add(ns_key)
                namespace, key = ns_key
                ns = self._store.get(namespace)
                if ns and key in ns:
                    ns.pop(key, None)
                    invalidated += 1
            # Clear tag index after invalidation
            self._tags.pop(tag, None)
        await asyncio_sleep_noop()
        return invalidated

    def get_performance_stats(self) -> dict[str, Any]:
        """Return cache performance metrics for reporting."""
        hit_rate = (self._gets_hits / self._gets_total) if self._gets_total else 0.0
        latencies = sorted(self._get_latencies_ms)
        def _pct(p: float) -> float:
            if not latencies:
                return 0.0
            idx = int(max(0, min(len(latencies) - 1, round(p * (len(latencies) - 1)))))
            return latencies[idx]
        avg = sum(latencies) / len(latencies) if latencies else 0.0
        return {
            "total_operations": self._operations_total,
            "redis_enabled": False,
            "memory_cache": {
                "hits": self._gets_hits,
                "requests": self._gets_total,
                "hit_rate": hit_rate,
            },
            "performance": {
                "total_get": {
                    "avg": avg,
                    "p95": _pct(0.95),
                    "p99": _pct(0.99),
                }
            },
        }


async def asyncio_sleep_noop() -> None:
    """Tiny awaitable used to ensure async signatures perform an await."""
    import asyncio
    await asyncio.sleep(0)
