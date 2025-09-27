#!/usr/bin/env python3
"""
GitHub Issues Generator for StratMaster Implementation Plan

This script generates GitHub issue bodies based on IMPLEMENTATION_PLAN.md
for tracking the remaining 1% of implementation work.
"""

import json
from typing import Dict, Any

ISSUES_DATA = [
    {
        "title": "[IMPL] Real-Time Collaboration Engine - Week 4 Priority",
        "labels": ["enhancement", "implementation-plan", "P0-critical", "collaboration", "websocket"],
        "priority": "P0",
        "milestone": "M1: Real-Time Foundation",
        "body": """## Enhancement Overview
Implement Yjs WebSocket provider for CRDT-based editing with <150ms latency target as specified in IMPLEMENTATION_PLAN.md section 1.

## Current State  
- Only README and config stub exist in `packages/collaboration/`
- Web workspace (`packages/ui`) renders static panes with no CRDT bindings
- No WebSocket service, persistence, or CRDT implementation

## Gap Analysis
**Missing Components:**
- WebSocket service, persistence, and CRDT implementation
- **Affected modules:** `apps/web` Shoelace UI, `packages/ui` state management, API auth (session tokens), Redis/Postgres infra, observability dashboards
- **Dependencies:** Yjs/y-websocket, redis streams, WebSocket gateway (FastAPI or Starlette), collaborative session persistence layer

## Implementation Design
1. **Service:** Build `packages/collaboration/src` FastAPI app exposing REST for session lifecycle plus `/ws/collaboration` endpoint
2. **CRDT:** Use Yjs with `y-py` for CRDT structures and `y-redis` for pub/sub fanout  
3. **Storage:** Redis for ephemeral updates, Postgres (existing `database/`) for session manifests via SQLAlchemy
4. **Integration:** Extend `apps/web/src/state` to hydrate collaborative documents via Yjs provider, gated behind flag
5. **Security:** Re-use Keycloak tokens validated via `packages/api.security` to authorize WebSocket upgrades

## Requirements Checklist
- [ ] FastAPI WebSocket service at `/ws/collaboration` endpoint
- [ ] Yjs with `y-py` for CRDT structures  
- [ ] `y-redis` for pub/sub fanout across sessions
- [ ] Redis ephemeral updates + Postgres session manifests
- [ ] Keycloak token validation for WebSocket auth
- [ ] Web client integration with presence UI (gated)
- [ ] Session ACL from `configs/collaboration/real_time.yaml`

## ADR/RFC Requirements  
- [x] **ADR**: `docs/architecture/adr/adr-012-real-time-collaboration.md`
- [x] **RFC**: `docs/rfc/2024-rt-collaboration.md` (API, schema, SLA, rollout)

## Feature Flag & Rollout
- [x] **Flag**: `ENABLE_COLLAB_LIVE` (default: false)
- [x] **Migration strategy**: Ship with feature flag off, provide data backfill script when enabling
- [x] **Rollback plan**: Feature flag off disables WebSocket entry points, Redis key purge script

## Test Plan
- [ ] **Unit tests**: CRDT document merges, session repository, auth guard
- [ ] **Contract tests**: WebSocket handshake, session REST endpoints  
- [ ] **E2E tests**: Browser automation verifying co-edit latency under 150ms (LAN), multi-tab editing

## Quality Gates
- [ ] **Latency**: <150ms echo latency on LAN
- [ ] **Multi-tab test**: Conflict-free merges across browser tabs
- [ ] **Presence system**: Cursors, editing awareness working

## PR Sequencing  
1. [ ] **PR 1**: Scaffold service behind flag (routers, config parsing, empty handlers + tests)
2. [ ] **PR 2**: Implement persistence & CRDT adapters  
3. [ ] **PR 3**: Wire web client + presence UI (gated)
4. [ ] **PR 4**: Enable observability & performance dashboards, final flag enablement

## Documentation Updates
- [ ] **Reference docs**: New API/WebSocket endpoints
- [ ] **How-to guides**: Deployment & scaling notes, link to ADR/RFC  
- [ ] **Tutorials**: Collaborative review workflow

## Dependencies
- Depends on: API auth system (existing)
- Blocks: Advanced caching (issue #4)

## Roadmap Timeline
- [x] Week 1-2""",
    },
    
    {
        "title": "[IMPL] Evidence-Guided Model Recommender Enhancements - Week 2 Priority", 
        "labels": ["enhancement", "implementation-plan", "P0-critical", "model-routing", "ml"],
        "priority": "P0", 
        "milestone": "M1: Real-Time Foundation",
        "body": """## Enhancement Overview
Complete LMSYS Arena and MTEB data integration for intelligent cascade routing as specified in IMPLEMENTATION_PLAN.md section 2.

## Current State
- `ModelRecommender` fetchers return hard-coded samples and no persistence or scheduler
- Providers consume it for cascade fallback but without real data
- Foundation ready but missing real data ingestion and telemetry

## Gap Analysis  
**Missing Components:**
- Real data ingestion (Arena API or cached CSV), MTEB leaderboard fetch, Langfuse integration
- **Affected modules:** `packages/mcp-servers/router-mcp`, LiteLLM gateway config (`configs/router/models-policy.yaml`), metrics pipeline, ops cron/Argo Workflows
- **Dependencies:** Storage (SQLite/Redis), nightly job runner, telemetry hooks

## Implementation Design
1. **Data ingestion:** Add async clients for LMSYS (GitHub JSON) and HuggingFace MTEB data with caching to S3/MinIO
2. **Persistence:** SQLite via `sqlmodel` under `packages/mcp-servers/router-mcp`  
3. **Telemetry:** Hook LiteLLM call metrics via `packages/api/performance` exporters to update recommender
4. **Scheduler:** APScheduler-based nightly refresh job + Kubernetes CronJob
5. **Scoring:** Extend cascade scoring to compute z-score normalized utility (quality-cost-latency weights)

## Requirements Checklist
- [ ] Async clients for LMSYS (GitHub JSON) and HuggingFace MTEB data
- [ ] SQLite persistence via `sqlmodel` with aggregated stats
- [ ] LiteLLM call metrics → recommender via message queue
- [ ] APScheduler-based nightly refresh job + Kubernetes CronJob  
- [ ] Cascade scoring with z-score normalized utility (quality-cost-latency)
- [ ] `/router/models/recommendation` debugging endpoint
- [ ] Langfuse integration for experiment tracking

## ADR/RFC Requirements
- [x] **ADR**: `docs/architecture/adr/adr-013-model-recommender-data.md` 
- [ ] **RFC**: Internal design doc if leadership requests

## Feature Flag & Rollout
- [x] **Flag**: `ENABLE_MODEL_RECOMMENDER_V2` (default: on)
- [x] **Migration strategy**: Schema migration for SQLite store behind flag, fallback to in-memory stub
- [x] **Rollback plan**: Toggle flag off, drop SQLite data (stateless), revert CronJob manifest

## Test Plan  
- [ ] **Unit tests**: Data parsers, score calculation, scheduler triggers
- [ ] **Contract tests**: Provider cascade ensuring fallback order deterministic with seed data
- [ ] **Integration tests**: Dry-run hitting real APIs (mocked fixtures in CI), verify nightly job updates DB

## Quality Gates
- [ ] **Routing performance**: p50 < 20ms for routing decisions
- [ ] **Data freshness**: Nightly updates successfully refresh model scores
- [ ] **Cascade accuracy**: Deterministic fallback order with confidence scoring

## PR Sequencing
1. [ ] **PR 1**: Data client + persistence scaffolding
2. [ ] **PR 2**: Telemetry ingestion & scoring logic update  
3. [ ] **PR 3**: Scheduler + ops manifests
4. [ ] **PR 4**: Expose admin endpoints & documentation, flip flag

## Documentation Updates
- [ ] **Reference docs**: API endpoint docs for recommendation debug
- [ ] **How-to guides**: Configuring data refresh secrets
- [ ] **Tutorials**: Optimizing tenant routing

## Dependencies  
- Depends on: LiteLLM gateway (existing)
- Blocks: Retrieval benchmarking (issue #3)

## Roadmap Timeline
- [x] Week 1-2""",
    },

    {
        "title": "[IMPL] Retrieval Benchmarking & Latency Validation - Week 3 Priority",
        "labels": ["enhancement", "implementation-plan", "P0-critical", "retrieval", "benchmarking"],
        "priority": "P0",
        "milestone": "M2: Performance & Validation", 
        "body": """## Enhancement Overview
Complete NDCG@10/MRR@10 benchmarking with BEIR datasets as specified in IMPLEMENTATION_PLAN.md section 3.

## Current State
- `SPLADEEvaluator` provides metrics skeleton with synthetic data and is unused elsewhere
- API performance routes mock NDCG values  
- SPLADE retrieval implemented but needs validation against quality targets

## Gap Analysis
**Missing Components:**
- Integration between retrieval package and evaluation harness, dataset provisioning, latency tracking, CI gating
- **Affected modules:** `packages/retrieval`, `packages/api` performance router, `tests` (contract/e2e), infra for benchmark datasets (S3 storage)
- **Dependencies:** BEIR-compatible datasets, evaluation task runner, Prometheus integration

## Implementation Design  
1. **Dataset ingestion:** BEIR-compatible dataset loader (LoTTE/NQ) stored in MinIO; CLI to sync seeds to `seeds/eval`
2. **Evaluation service:** Async task (Celery or Prefect) to run evaluator against live retrievers (BM25+dense, SPLADE)
3. **API integration:** Update `/performance/retrieval` endpoint to trigger evaluation job and surface latest metrics
4. **Latency validation:** Instrument retrieval pipeline to emit p95 metrics to OpenTelemetry & Prometheus
5. **CI gating:** Include gating in CI using recorded responses

## Requirements Checklist
- [ ] BEIR-compatible dataset loader (LoTTE/NQ) in MinIO
- [ ] CLI to sync benchmark datasets to `seeds/eval`
- [ ] Async evaluation task (Celery/Prefect) against live retrievers (BM25+dense, SPLADE)  
- [ ] `/performance/retrieval` endpoint integration with evaluation job triggers
- [ ] p95 latency instrumentation via OpenTelemetry & Prometheus
- [ ] CI gating with recorded responses for regression detection
- [ ] Results stored in Postgres table with threshold validation

## ADR/RFC Requirements
- [x] **ADR**: `docs/architecture/adr/adr-014-retrieval-benchmarks.md` (dataset choice, gating thresholds)
- [ ] **RFC**: Optional if dataset licensing requires review

## Feature Flag & Rollout
- [x] **Flag**: `ENABLE_RETRIEVAL_BENCHMARKS` (default: off)
- [x] **Migration strategy**: Fallback to synthetic metrics when disabled, dataset sync can run ahead of feature
- [x] **Rollback plan**: Disable flag, clear benchmark tables, revert CI job

## Test Plan
- [ ] **Unit tests**: Metric computations (NDCG, MRR), dataset loader
- [ ] **Contract tests**: API response schema, job scheduling  
- [ ] **E2E tests**: Run evaluation against staging search cluster, assert thresholds

## Quality Gates  
- [ ] **NDCG@10 improvement**: ≥10% vs current baseline after SPLADE-v3
- [ ] **Latency impact**: p95 <15% latency hit from benchmarking
- [ ] **MRR@10 targets**: Meet documented MRR@10 targets

## PR Sequencing
1. [ ] **PR 1**: Dataset loader + storage CLI  
2. [ ] **PR 2**: Evaluator integration & persistence
3. [ ] **PR 3**: API surface & telemetry instrumentation
4. [ ] **PR 4**: CI/Nightly job + documentation, enable flag

## Documentation Updates
- [ ] **Reference docs**: `/performance` endpoints  
- [ ] **How-to guides**: Running retrieval QA locally
- [ ] **Tutorials**: Interpreting benchmark dashboards

## Dependencies
- Depends on: Model recommender (issue #2)
- Blocks: None

## Roadmap Timeline  
- [x] Week 3-4""",
    },

    {
        "title": "[IMPL] Advanced Caching & Performance Optimisation - Phase 1 Priority",
        "labels": ["enhancement", "implementation-plan", "P1-important", "performance", "caching"],
        "priority": "P1",
        "milestone": "M2: Performance & Validation",
        "body": """## Enhancement Overview  
Implement multi-tier caching with CDN integration and invalidation policies as specified in IMPLEMENTATION_PLAN.md section 4.

## Current State
- API uses simple Redis client for memoisation and response caching in `cache_client.py`
- Lacks multi-tier caches, cache invalidation policies, or CDN integration
- No profiling or performance instrumentation

## Gap Analysis
**Missing Components:**  
- Layered caching (Redis, CDN/Edge, client hints), hot path profiling, config-driven TTLs
- **Affected modules:** API middleware, infra (Fastly/CloudFront), invalidation hooks in services, Makefile operations
- **Dependencies:** CDN configuration, profiling tools, pub/sub invalidation system

## Implementation Design
1. **Profiling:** Instrument FastAPI middlewares to capture per-endpoint timings, store in Prometheus histogram
2. **Layered cache:** Extend cache client to support tiered strategy (Redis + `fastapi-cache2` + CDN surrogate keys)  
3. **Domain-specific caches:** Strategy briefs, search results with appropriate TTLs
4. **Invalidation:** Pub/sub channel for cache bust events via Redis streams
5. **Edge integration:** Varnish/Fastly config templates with signed URL support for multi-tenant isolation

## Requirements Checklist
- [ ] FastAPI middleware for per-endpoint timing → Prometheus histogram
- [ ] Tiered cache strategy (Redis + `fastapi-cache2` + CDN surrogate keys)
- [ ] Domain-specific caches (strategy briefs, search results) with config-driven TTLs
- [ ] Pub/sub invalidation channel via Redis streams  
- [ ] Varnish/Fastly config templates with signed URL support
- [ ] Multi-tenant cache isolation with surrogate keys

## ADR/RFC Requirements
- [x] **ADR**: `docs/architecture/adr/adr-015-multi-tier-cache.md` (tiers, TTLs, invalidation)
- [ ] **RFC**: Not needed if internal change, coordinate with ops

## Feature Flag & Rollout  
- [x] **Flag**: `ENABLE_RESPONSE_CACHE_V2`, `ENABLE_EDGE_CACHE_HINTS` (default: off)
- [x] **Migration strategy**: Cache defaults maintain current behavior, CDN integration optional per environment  
- [x] **Rollback plan**: Toggle flags off, flush Redis & CDN caches via script, remove surrogate headers

## Test Plan
- [ ] **Unit tests**: Cache client tier selection, invalidation handlers
- [ ] **Contract tests**: API headers include `Cache-Control` & surrogate keys
- [ ] **Load tests**: Use existing `make test.load` to observe 3-5× improvement target

## Quality Gates
- [ ] **Performance improvement**: 3-5× improvement on load tests
- [ ] **Cache hit rates**: >80% hit rate for frequently accessed endpoints  
- [ ] **Invalidation latency**: <100ms cache invalidation propagation

## PR Sequencing
1. [ ] **PR 1**: Profiling + metrics instrumentation
2. [ ] **PR 2**: Redis + local tier refactor, flag integration
3. [ ] **PR 3**: Invalidation bus + service hooks  
4. [ ] **PR 4**: Edge/CDN documentation & rollout scripts

## Documentation Updates
- [ ] **Reference docs**: New config keys
- [ ] **How-to guides**: Enabling CDN caching
- [ ] **Tutorials**: Performance tuning workflow

## Dependencies
- Depends on: Real-time collaboration (issue #1) for cache coordination
- Blocks: None

## Roadmap Timeline
- [x] Week 2-4""",
    },

    {
        "title": "[IMPL] Phase 3 UX Quality Gates - WCAG, Mobile, Lighthouse",
        "labels": ["enhancement", "implementation-plan", "P1-important", "ux", "accessibility"],
        "priority": "P1", 
        "milestone": "M2: Performance & Validation",
        "body": """## Enhancement Overview
Implement automated accessibility audit, responsive testing, and Lighthouse CI as specified in IMPLEMENTATION_PLAN.md section 5.

## Current State  
- UI components exist but no automated accessibility audit script coverage
- No Lighthouse CI or documented mobile test plan (Phase 3 items unchecked)
- Mobile app exists but roadmap deliverable missing

## Gap Analysis
**Missing Components:**
- Accessibility tooling (axe-core, keyboard nav tests), responsiveness validation (BrowserStack matrix), performance budgets
- **Affected modules:** `apps/web`, `apps/mobile`, `scripts/accessibility_audit.py`, documentation
- **Dependencies:** axe-puppeteer, Playwright device emulation, Lighthouse CI configuration

## Implementation Design
1. **Accessibility:** Expand `scripts/accessibility_audit.py` to run axe-puppeteer and output WCAG 2.1 AA report
2. **Storybook integration:** Add accessibility checks to component library
3. **Responsive testing:** Configure Playwright suite covering breakpoints & device emulation  
4. **Performance budgets:** Add Lighthouse CI config to run against built web app, gating at score >90
5. **Mobile roadmap:** Produce document & backlog items for native features

## Requirements Checklist  
- [ ] Expand `scripts/accessibility_audit.py` with axe-puppeteer → WCAG 2.1 AA report
- [ ] Storybook accessibility checks for component library
- [ ] Playwright suite covering breakpoints & device emulation
- [ ] Document manual testing matrix for responsive design
- [ ] Lighthouse CI config running against built web app, score >90 gating
- [ ] Mobile roadmap document & backlog items aligned with roadmap deliverable

## ADR/RFC Requirements
- [ ] **ADR**: Update `docs/architecture/adr/adr-005-ux-system.md` if exists, else create accessibility addendum  
- [ ] **RFC**: Not needed

## Feature Flag & Rollout
- [x] **Flag**: `ENABLE_LIGHTHOUSE_CI` (default: off) 
- [x] **Migration strategy**: Tooling only, no runtime behavior changes, optional env var for constrained envs
- [x] **Rollback plan**: Disable `ENABLE_LIGHTHOUSE_CI` and skip Playwright job if necessary

## Test Plan
- [ ] **Unit tests**: Component-level accessibility tests (ARIA roles)
- [ ] **Contract tests**: Playwright responsiveness checks across breakpoints  
- [ ] **E2E tests**: Lighthouse CI job verifying performance budgets >90 score

## Quality Gates
- [ ] **WCAG compliance**: WCAG 2.1 AA standards met  
- [ ] **Lighthouse score**: >90 performance score maintained
- [ ] **Responsive design**: All breakpoints tested and functional
- [ ] **Mobile roadmap**: Documented plan for native features

## PR Sequencing
1. [ ] **PR 1**: Audit tooling & CI scaffolding
2. [ ] **PR 2**: Accessibility fixes & documentation updates  
3. [ ] **PR 3**: Responsive test matrix & mobile roadmap doc
4. [ ] **PR 4**: Performance tuning + enforce budgets

## Documentation Updates  
- [ ] **Reference docs**: Update UX standards doc
- [ ] **How-to guides**: Running accessibility suite locally
- [ ] **Tutorials**: Mobile testing checklist

## Dependencies
- Depends on: None
- Blocks: None

## Roadmap Timeline
- [x] Week 2-4""",
    },
]

def generate_issue_body(issue_data: Dict[str, Any]) -> str:
    """Generate the complete issue body with metadata."""
    body = issue_data["body"]
    
    # Add metadata section
    metadata = f"""
---

## Issue Metadata
**Priority:** {issue_data['priority']}  
**Milestone:** {issue_data['milestone']}  
**Labels:** {', '.join([f'`{label}`' for label in issue_data['labels']])}

**Generated from:** IMPLEMENTATION_PLAN.md via implementation tracking automation
**Related Documentation:** 
- IMPLEMENTATION_PLAN.md
- IMPLEMENTATION_ISSUES.md  
- Upgrade.md (roadmap status)
- Scratch.md (technical specification)
"""
    
    return body + metadata

def main():
    """Generate all GitHub issues as JSON for import/reference."""
    print("# GitHub Issues for StratMaster Implementation Plan")
    print()
    print("This document contains the issue bodies for creating GitHub issues to track")  
    print("implementation work from IMPLEMENTATION_PLAN.md")
    print()
    
    for i, issue_data in enumerate(ISSUES_DATA, 1):
        print(f"## Issue #{i}: {issue_data['title']}")
        print()
        print("**Create this issue with:**")
        print(f"- **Title:** {issue_data['title']}")
        print(f"- **Labels:** {', '.join(issue_data['labels'])}")
        print()
        print("**Issue Body:**")
        print("```")
        print(generate_issue_body(issue_data))
        print("```")
        print()
        print("---")
        print()

if __name__ == "__main__":
    main()
