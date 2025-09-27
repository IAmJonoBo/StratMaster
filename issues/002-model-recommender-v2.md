# Issue 002: Evidence-Guided Model Recommender V2

## Summary
Deliver the Week 2 roadmap follow-ups by implementing real LMSYS/MTEB ingestion, telemetry, and cascade routing as captured in [Implementation Plan §Evidence-Guided Model Recommender Enhancements](../IMPLEMENTATION_PLAN.md#evidence-guided-model-recommender-enhancements).

## Current State
- Recommender fetchers return hard-coded samples; no persistent cache or scheduler exists.【F:packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py†L125-L168】
- Provider adapters rely on the recommender but cannot record telemetry beyond in-memory smoothing.【F:packages/mcp-servers/router-mcp/src/router_mcp/providers.py†L30-L88】

## Proposed Solution
1. Add external data clients and persistence for leaderboard metrics.
2. Capture LiteLLM telemetry and nightly refresh jobs feeding the recommender database.
3. Expose admin/debug APIs and ensure cascade routing adheres to utility scoring.

## Feature Flag
- `ENABLE_MODEL_RECOMMENDER_V2` (default `true`, set to `false` only for emergency rollback).

## Acceptance Criteria
- Nightly job populates recommender store with LMSYS and MTEB scores (verified via metrics dashboard).
- Provider adapter selects models based on dynamic scores with deterministic fallback ordering.
- API exposes diagnostic endpoint returning current performance snapshot.
- All unit/integration tests pass with flag enabled; default CI pipeline passes with flag disabled.

## Dependencies
- Access to LMSYS/MTEB data sources or cached mirrors.
- Storage backend (SQLite/Postgres) reachable from router MCP service.

## Testing Plan
- Unit tests for data parsers, scoring, scheduler triggers.
- Integration tests using mocked HTTP fixtures to simulate external APIs.
- Contract tests for new debug endpoint.

## Rollout & Monitoring
- Deploy scheduler as Kubernetes CronJob with alerting on failures.
- Add Prometheus metrics for recommendation latency, cache freshness, and per-model selection counts.
