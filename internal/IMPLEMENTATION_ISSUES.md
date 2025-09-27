# StratMaster Implementation Tracking Issues

This document outlines the GitHub issues that need to be created to track the remaining implementation work as specified in `IMPLEMENTATION_PLAN.md`.

## 🔴 Priority P0 - Critical (Weeks 1-2)

### Issue #1: Real-Time Collaboration Engine
**Status**: Ready for Implementation  
**Roadmap**: Week 4 Collaboration & Compliance  
**Description**: Implement Yjs WebSocket provider for CRDT-based editing with <150ms latency target

**Current State**: Only README and config stub exist in `packages/collaboration/`  
**Gap**: Missing WebSocket service, persistence, CRDT implementation  
**Affects**: `apps/web`, `packages/ui`, API auth, Redis/Postgres, observability

**Key Deliverables**:
- [ ] FastAPI WebSocket service at `/ws/collaboration`
- [ ] Yjs with `y-py` for CRDT structures  
- [ ] `y-redis` for pub/sub fanout
- [ ] Redis ephemeral updates + Postgres session manifests
- [ ] Keycloak token validation for WebSocket auth
- [ ] Feature flag: `ENABLE_COLLAB_LIVE` (default: false)

**Quality Gates**: <150ms echo latency on LAN, multi-tab torture test
**ADR**: `docs/architecture/adr/adr-012-real-time-collaboration.md`

---

### Issue #2: Evidence-Guided Model Recommender Enhancements  
**Status**: Foundation Ready (LMSYS/MTEB integration pending)  
**Roadmap**: Week 2 Evaluation & Routing  
**Description**: Complete LMSYS Arena and MTEB data integration for intelligent cascade routing

**Current State**: `ModelRecommender` returns hard-coded samples, no persistence/scheduler  
**Gap**: Real data ingestion, MTEB leaderboard, Langfuse integration, nightly jobs  
**Affects**: `packages/mcp-servers/router-mcp`, LiteLLM config, metrics pipeline

**Key Deliverables**:
- [ ] Async clients for LMSYS (GitHub JSON) and HuggingFace MTEB data
- [ ] SQLite persistence via `sqlmodel` 
- [ ] LiteLLM call metrics → recommender via message queue
- [ ] APScheduler-based nightly refresh job + Kubernetes CronJob
- [ ] Cascade scoring with z-score normalized utility (quality-cost-latency)
- [ ] `/router/models/recommendation` debugging endpoint
- [ ] Feature flag: `ENABLE_MODEL_RECOMMENDER_V2`

**Quality Gates**: p50 < 20ms routing decision time
**ADR**: `docs/architecture/adr/adr-013-model-recommender-data.md`

---

### Issue #3: Retrieval Benchmarking & Latency Validation
**Status**: SPLADE implemented, metrics skeleton exists  
**Roadmap**: Week 3 Retrieval Uplift validation  
**Description**: Complete NDCG@10/MRR@10 benchmarking with BEIR datasets

**Current State**: `SPLADEEvaluator` has synthetic data, API performance routes mock values  
**Gap**: Integration between retrieval package and evaluation, dataset provisioning, CI gating  
**Affects**: `packages/retrieval`, `packages/api` performance router, `tests`, infra

**Key Deliverables**:
- [ ] BEIR-compatible dataset loader (LoTTE/NQ) in MinIO
- [ ] Async evaluation task (Celery/Prefect) against live retrievers
- [ ] `/performance/retrieval` endpoint integration with Prometheus
- [ ] p95 latency instrumentation via OpenTelemetry
- [ ] CI gating with recorded responses
- [ ] Feature flag: `ENABLE_RETRIEVAL_BENCHMARKS`

**Quality Gates**: NDCG@10 ≥10% improvement, p95 latency <15% hit
**ADR**: `docs/architecture/adr/adr-014-retrieval-benchmarks.md`

---

## 🟡 Priority P1 - Important (Weeks 2-4)

### Issue #4: Advanced Caching & Performance Optimisation
**Status**: Simple Redis caching exists  
**Roadmap**: Phase 1 Performance Optimization  
**Description**: Multi-tier caching with CDN integration and invalidation policies

**Current State**: Basic Redis client for memoization in `cache_client.py`  
**Gap**: Layered caching, CDN integration, invalidation hooks  
**Affects**: API middleware, infra (Fastly/CloudFront), Makefile operations

**Key Deliverables**:
- [ ] FastAPI middleware for per-endpoint timing → Prometheus histogram
- [ ] Tiered strategy (Redis + `fastapi-cache2` + CDN surrogate keys)
- [ ] Domain-specific caches (strategy briefs, search results)
- [ ] Pub/sub invalidation via Redis streams
- [ ] Varnish/Fastly config templates with signed URL support
- [ ] Feature flags: `ENABLE_RESPONSE_CACHE_V2`, `ENABLE_EDGE_CACHE_HINTS`

**Quality Gates**: 3-5× improvement on `make test.load`
**ADR**: `docs/architecture/adr/adr-015-multi-tier-cache.md`

---

### Issue #5: Phase 3 UX Quality Gates
**Status**: UI components exist, no automated auditing  
**Roadmap**: Phase 3 WCAG, mobile, Lighthouse  
**Description**: Accessibility, responsive testing, and performance budget enforcement

**Current State**: No accessibility audit script, no Lighthouse CI, missing mobile test plan  
**Gap**: Accessibility tooling, responsiveness validation, performance budgets  
**Affects**: `apps/web`, `apps/mobile`, `scripts/accessibility_audit.py`

**Key Deliverables**:
- [ ] Expand `scripts/accessibility_audit.py` with axe-puppeteer
- [ ] Playwright breakpoint & device emulation suite
- [ ] Lighthouse CI config with >90 score gating
- [ ] Mobile roadmap document & backlog items
- [ ] Storybook accessibility checks
- [ ] Feature flag: `ENABLE_LIGHTHOUSE_CI`

**Quality Gates**: WCAG 2.1 AA compliance, Lighthouse score >90

---

## 🟢 Priority P2 - Enhancement (Month 2+)

### Issue #6: Predictive Strategy Analytics
**Status**: Forecast API generates random values  
**Roadmap**: Medium-term enhancement  
**Description**: Real time-series modeling with Prophet/PyMC and MLflow tracking

**Current State**: Random forecast values in `services.py`, no analytics service  
**Gap**: Data ingestion, model training, experiment tracking, API/UX updates  
**Affects**: `packages/analytics`, `packages/ml-training`, data warehouse schemas

**Key Deliverables**:
- [ ] ETL pipeline aggregating metrics → feature store (DuckDB/PostgreSQL)
- [ ] Prophet/NeuralProphet pipeline with MLflow logging
- [ ] Inference microservice (FastAPI) with gRPC/REST endpoints
- [ ] Web/mobile forecast graphs with confidence intervals
- [ ] Feature flag: `ENABLE_PREDICTIVE_ANALYTICS`

**ADR**: `docs/architecture/adr/adr-016-predictive-analytics.md`

---

### Issue #7: Event-Driven Microservices Architecture  
**Status**: Synchronous FastAPI calls only  
**Roadmap**: Medium-term enhancement  
**Description**: Event bus with Redis Streams/Kafka for async processing

**Current State**: No event producers/consumers exist  
**Gap**: Event bus, message schemas, observability  
**Affects**: `packages/api`, orchestrator, analytics, infra

**Key Deliverables**:
- [ ] Redis Streams event bus (prototype), Kafka option
- [ ] Protobuf/JSON schemas in `packages/contracts`
- [ ] Outbox pattern producers via Postgres + transactional worker
- [ ] Dedicated consumer workers (analytics, notifications, audit)
- [ ] OpenTelemetry tracing + Prometheus metrics
- [ ] Feature flag: `ENABLE_EVENT_STREAMING`

**ADR**: `docs/architecture/adr/adr-017-event-architecture.md`
**RFC**: Required due to architectural shift

---

### Issue #8: Industry-Specific Strategy Templates
**Status**: Generic templates only  
**Roadmap**: Medium-term enhancement  
**Description**: Vertical-specific strategy templates with industry datasets

**Current State**: Generic strategy synthesizer, no industry variants  
**Gap**: Template library, taxonomy, dataset ingestion, UI selectors  
**Affects**: `packages/strategy`, `apps/web` UI, API endpoints, seeds

**Key Deliverables**:
- [ ] `packages/strategy/src/strategy_pipeline/templates/` with Jinja per vertical
- [ ] Synthesizer accepts `industry` parameter with vertical heuristics
- [ ] Curated industry knowledge base in `seeds/industry/`
- [ ] UI dropdown for industry selection with recommended KPIs
- [ ] API schema updates for optional `industry` field
- [ ] Feature flag: `ENABLE_INDUSTRY_TEMPLATES`

**ADR**: `docs/architecture/adr/adr-018-industry-templates.md`

---

### Issue #9: Custom Model Fine-Tuning Platform
**Status**: Constitutional compliance focus only  
**Roadmap**: Advanced feature  
**Description**: Secure fine-tuning with Ray/Kubeflow orchestration and model registry

**Current State**: ML training focuses on constitutional compliance, no fine-tuning infra  
**Gap**: Dataset management, compute orchestration, model registry, compliance  
**Affects**: `packages/ml-training`, `ops` K8s jobs, `packages/providers`, billing

**Key Deliverables**:
- [ ] Secure dataset store with lineage tracking (MinIO + metadata DB)
- [ ] Ray Serve/Kubeflow fine-tuning jobs (LoRA adapters)
- [ ] MLflow model registry with evaluation metrics  
- [ ] LiteLLM gateway adapter loading per tenant with access controls
- [ ] Review workflow requiring compliance sign-off before deployment
- [ ] Feature flag: `ENABLE_CUSTOM_FINE_TUNING`

**ADR**: `docs/architecture/adr/adr-019-fine-tuning-platform.md`
**RFC**: Required (enterprise impact, significant investment)

---

### Issue #10: Advanced Knowledge Graph Reasoning
**Status**: Basic ingestion and queries only  
**Roadmap**: Advanced feature  
**Description**: Causal inference and multi-hop reasoning over NebulaGraph

**Current State**: Knowledge pipeline supports hybrid query, no advanced reasoning  
**Gap**: Graph analytics, query planner, reasoning service  
**Affects**: `packages/knowledge`, orchestrator, strategy scoring, ML components

**Key Deliverables**:
- [ ] Graph analytics (PageRank, motif detection) with networkx/igraph
- [ ] NebulaGraph multi-hop reasoning queries
- [ ] DoWhy/EconML causal inference between strategic variables
- [ ] `/knowledge/reasoning` endpoints returning causal narratives
- [ ] UI causal graph overlays in workspace
- [ ] Feature flag: `ENABLE_KNOWLEDGE_REASONING`

**ADR**: `docs/architecture/adr/adr-020-knowledge-reasoning.md`

---

## Implementation Coordination

### Milestones
- **M1: Real-Time Foundation** (Week 2) - Issues #1, #2
- **M2: Performance & Validation** (Week 4) - Issues #3, #4, #5  
- **M3: Advanced Analytics** (Month 2) - Issues #6, #7
- **M4: Enterprise Features** (Month 3+) - Issues #8, #9, #10

### Dependencies
- Issue #2 → Issue #3 (model recommender feeds into retrieval benchmarks)
- Issue #1 → Issue #4 (collaboration needs caching for performance)
- Issue #7 → Issue #6 (event architecture enables predictive analytics)

### Feature Flag Strategy
All features default to **OFF** to maintain current behavior until ready for production deployment.

### Quality Gates Summary
- **Collaboration**: <150ms echo latency, multi-tab tests
- **Model Selection**: p50 <20ms routing decisions  
- **Retrieval**: NDCG@10 ≥10% improvement, p95 <15% latency hit
- **Caching**: 3-5× performance improvement on load tests
- **UX**: WCAG 2.1 AA compliance, Lighthouse >90

*Generated from IMPLEMENTATION_PLAN.md analysis - January 2024*