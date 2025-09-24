# Issue 004: Advanced Caching & Performance Optimisation

## Summary
Execute the multi-tier caching initiative detailed in [Implementation Plan §Advanced Caching & Performance Optimisation](../IMPLEMENTATION_PLAN.md#advanced-caching--performance-optimisation) to meet roadmap performance goals.

## Current State
- API relies on a basic Redis helper without tiered strategies, invalidation hooks, or CDN integration.【F:packages/api/src/stratmaster_api/clients/cache_client.py†L1-L156】
- Roadmap Phase 1 action item “Performance Optimization” and immediate enhancement #3 remain unchecked.【F:Upgrade.md†L397-L404】【F:Upgrade.md†L510-L514】

## Proposed Solution
1. Instrument per-endpoint latency metrics and identify cacheable responses.
2. Implement tiered caching (Redis + edge/CDN) with invalidation via pub/sub.
3. Provide ops tooling and documentation for CDN rollout.

## Feature Flags
- `ENABLE_RESPONSE_CACHE_V2`
- `ENABLE_EDGE_CACHE_HINTS`

## Acceptance Criteria
- Latency dashboards demonstrate 3–5× improvement on targeted endpoints with caches enabled.
- Cache headers and surrogate keys present on API responses when flags enabled, absent otherwise.
- Automated tests cover cache hit/miss paths and invalidation triggers.
- Documentation outlines deployment steps and rollback procedures.

## Dependencies
- Redis availability; CDN vendor credentials if edge caching enabled.
- Observability stack (Prometheus, Grafana) for metrics.

## Testing Plan
- Unit tests for cache tier selection and invalidation bus.
- Contract tests verifying HTTP headers and cache behavior.
- Load testing via `make test.load` comparing before/after performance.

## Rollout & Monitoring
- Deploy instrumentation first, followed by Redis tier, then CDN hints.
- Configure alerts on cache error rate and latency regressions.
