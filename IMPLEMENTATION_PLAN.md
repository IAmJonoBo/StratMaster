# StratMaster Enhancement Implementation Plan

This plan synthesizes roadmap items marked as upcoming or incomplete across `Upgrade.md`, architecture docs, and phase gate checklists. Each section evaluates the current repository state, enumerates gaps, and proposes a concrete implementation and rollout strategy that preserves existing behavior until the relevant feature flag is enabled.

## Contents
1. [Real-Time Collaboration Engine](#real-time-collaboration-engine)
2. [Evidence-Guided Model Recommender Enhancements](#evidence-guided-model-recommender-enhancements)
3. [Retrieval Benchmarking & Latency Validation](#retrieval-benchmarking--latency-validation)
4. [Advanced Caching & Performance Optimisation](#advanced-caching--performance-optimisation)
5. [Phase 3 UX Quality Gates](#phase-3-ux-quality-gates)
6. [Predictive Strategy Analytics](#predictive-strategy-analytics)
7. [Event-Driven Microservices Architecture](#event-driven-microservices-architecture)
8. [Industry-Specific Strategy Templates](#industry-specific-strategy-templates)
9. [Custom Model Fine-Tuning Platform](#custom-model-fine-tuning-platform)
10. [Advanced Knowledge Graph Reasoning](#advanced-knowledge-graph-reasoning)

---

## Real-Time Collaboration Engine
- **Roadmap reference:** Upgrade.md §Week 4 collaboration plan & “Immediate High-Impact Enhancements”.
- **Current state:** The monorepo only contains a README and config stub under `packages/collaboration/`, with no executable service or UI wiring.【F:packages/collaboration/README.md†L1-L42】 The web workspace (`packages/ui`) currently renders static panes with no CRDT bindings.

### Gap analysis & affected modules
- Missing WebSocket service, persistence, and CRDT implementation. Affects `apps/web` Shoelace UI, `packages/ui` state management, API auth (session tokens), Redis/Postgres infra, and observability dashboards.
- Dependency gaps: Yjs/y-websocket, redis streams, WebSocket gateway (FastAPI or Starlette), collaborative session persistence layer.

### Design sketch
1. **Service:** Build `packages/collaboration/src` FastAPI app exposing REST for session lifecycle plus a `/ws/collaboration` endpoint. Use Yjs with `y-py` for CRDT structures and `y-redis` for pub/sub fanout.
2. **State storage:** Redis for ephemeral updates, Postgres (existing `database/`) for session manifests, leveraging SQLAlchemy models.
3. **Integration:** Extend `apps/web/src/state` to hydrate collaborative documents via Yjs provider, gating behind `ENABLE_COLLAB_LIVE` flag (default `false`). Add presence and audit events routed through `packages/api` for logging.
4. **Security:** Re-use Keycloak tokens validated via `packages/api.security` to authorize WebSocket upgrades; include per-session ACL from `configs/collaboration/real_time.yaml`.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-012-real-time-collaboration.md` (to document CRDT choice, storage, and auth strategy).
- **RFC:** Needed because this introduces a new service and protocol. Draft `docs/rfc/2024-rt-collaboration.md` summarising API, schema, SLA, and rollout.

### Migration & compatibility
- Ship with feature flag off. No migration until flag toggled. Provide data backfill script to seed collaborative sessions when enabling.

### Feature flag & rollout
- Add `ENABLE_COLLAB_LIVE` env var consumed by API and web. Stage rollout: dev → staging shadow (read-only) → pilot tenants.

### Test plan
- Unit: CRDT document merges, session repository, auth guard.
- Contract: WebSocket handshake, session REST endpoints.
- E2E: Browser automation verifying co-edit latency under 150 ms (LAN), multi-tab editing.

### CI impacts
- Add optional integration tests tagged `collaboration` (skipped when flag off). Extend Docker Compose to include collaboration service container for CI.

### Rollback
- Feature flag off disables WebSocket entry points. Maintain schema migrations reversible. Provide Redis key purge script.

### PR sequencing
1. **Scaffold service behind flag** (routers, config parsing, empty handlers + tests).
2. **Implement persistence & CRDT adapters**.
3. **Wire web client + presence UI** (gated).
4. **Enable observability & performance dashboards**, final flag enablement PR.

### Documentation updates
- Reference docs: new API/WebSocket endpoints.
- Tutorials: collaborative review workflow.
- How-to: deployment & scaling notes, link to ADR/RFC.

---

## Evidence-Guided Model Recommender Enhancements
- **Roadmap reference:** Upgrade.md Week 2 items for LMSYS/MTEB integration, cascade routing, nightly scoring.
- **Current state:** `ModelRecommender` fetchers currently return hard-coded samples and no persistence or scheduler, while providers consume it for cascade fallback.【F:packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py†L1-L200】【F:packages/mcp-servers/router-mcp/src/router_mcp/providers.py†L1-L116】

### Gap analysis & affected modules
- Needs real data ingestion (Arena API or cached CSV), MTEB leaderboard fetch, Langfuse integration, storage (SQLite/Redis), and nightly job runner.
- Touches `packages/mcp-servers/router-mcp`, LiteLLM gateway config (`configs/router/models-policy.yaml`), metrics pipeline, and ops cron/Argo Workflows.

### Design sketch
1. **Data ingestion:** Add async clients for LMSYS (GitHub JSON) and HuggingFace MTEB data with caching to S3/MinIO. Persist aggregated stats in SQLite via `sqlmodel` under `packages/mcp-servers/router-mcp`.
2. **Telemetry:** Hook LiteLLM call metrics (latency/cost/success) via `packages/api/performance` exporters to update recommender via message queue.
3. **Scheduler:** Introduce APScheduler-based nightly refresh job triggered via CLI & Kubernetes CronJob.
4. **Confidence scoring:** Extend cascade scoring to compute z-score normalized utility (quality-cost-latency weights) and expose debugging endpoint `/router/models/recommendation`.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-013-model-recommender-data.md` covering data sources & privacy.
- **RFC:** Not needed (contained change), but add internal design doc in `docs/rfc/` if leadership requests.

### Migration & compatibility
- Schema migration for SQLite store (behind flag). Provide fallback to in-memory stub if DB unavailable. No breaking API changes.

### Feature flag & rollout
- Flag `ENABLE_MODEL_RECOMMENDER_V2`. Default off; when disabled, keep static scoring. Provide admin endpoint to toggle per-tenant.

### Test plan
- Unit: data parsers, score calculation, scheduler triggers.
- Contract: provider cascade ensuring fallback order deterministic with seed data.
- Integration: dry-run hitting real APIs (behind mocked fixtures in CI) and verifying nightly job updates DB.

### CI impacts
- Add tox env that mocks external HTTP via recorded fixtures. Ensure CronJob manifests validated via `helm template --strict`.

### Rollback
- Toggle flag off; drop SQLite data (stateless). Provide script to revert CronJob manifest.

### PR sequencing
1. **Data client + persistence scaffolding.**
2. **Telemetry ingestion & scoring logic update.**
3. **Scheduler + ops manifests.**
4. **Expose admin endpoints & documentation, flip flag.**

### Documentation updates
- Reference: API endpoint docs for recommendation debug.
- How-to: configuring data refresh secrets.
- Tutorials: optimizing tenant routing.

---

## Retrieval Benchmarking & Latency Validation
- **Roadmap reference:** Upgrade.md Week 3 “Next” items and Phase 2 quality gate checklist.
- **Current state:** `SPLADEEvaluator` provides metrics skeleton with synthetic data and is unused elsewhere; API performance routes mock NDCG values.【F:packages/retrieval/src/splade/src/splade/evaluator.py†L1-L200】【F:packages/api/src/stratmaster_api/performance.py†L369-L417】

### Gap analysis & affected modules
- Need integration between retrieval package and evaluation harness, dataset provisioning, latency tracking, and CI gating.
- Affects `packages/retrieval`, `packages/api` performance router, `tests` (contract/e2e), and infra for benchmark datasets (S3 storage).

### Design sketch
1. **Dataset ingestion:** Add BEIR-compatible dataset loader (LoTTE/NQ) stored in MinIO; create CLI to sync seeds to `seeds/eval`.
2. **Evaluation service:** Build async task (Celery or Prefect) to run evaluator against live retrievers (BM25+dense, SPLADE). Store results in Postgres table with thresholds.
3. **API integration:** Update `/performance/retrieval` endpoint to trigger evaluation job and surface latest metrics. Hook into Prometheus.
4. **Latency validation:** Instrument retrieval pipeline to emit p95 metrics to OpenTelemetry & Prometheus; include gating in CI using recorded responses.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-014-retrieval-benchmarks.md` (dataset choice, gating thresholds).
- RFC optional if dataset licensing requires review.

### Migration & compatibility
- Provide fallback to synthetic metrics when flag disabled. Dataset sync script can run ahead of feature enablement.

### Feature flag & rollout
- Flag `ENABLE_RETRIEVAL_BENCHMARKS`. When off, API returns current mock. Rollout: gather baseline, compare to thresholds, then enforce failing CI if regression >10%.

### Test plan
- Unit: metric computations (NDCG, MRR), dataset loader.
- Contract: API response schema, job scheduling.
- E2E: run evaluation against staging search cluster, assert thresholds.

### CI impacts
- Adds optional (nightly) workflow running benchmark job; gating job triggered manually for releases. Need to cache dataset artifacts to keep runtime reasonable.

### Rollback
- Disable flag, clear benchmark tables, revert CI job.

### PR sequencing
1. **Dataset loader + storage CLI.**
2. **Evaluator integration & persistence.**
3. **API surface & telemetry instrumentation.**
4. **CI/Nightly job + documentation, enable flag.**

### Documentation updates
- Reference: `/performance` endpoints.
- How-to: running retrieval QA locally.
- Tutorial: interpreting benchmark dashboards.

---

## Advanced Caching & Performance Optimisation
- **Roadmap reference:** Upgrade.md immediate enhancement #3 and Phase 1 action item “Performance Optimization”.
- **Current state:** API uses a simple Redis client for memoisation and response caching, but lacks multi-tier caches, cache invalidation policies, or CDN integration.【F:packages/api/src/stratmaster_api/clients/cache_client.py†L1-L156】

### Gap analysis & affected modules
- Need layered caching (Redis, CDN/Edge, client hints), hot path profiling, and config-driven TTLs. Impacts API middleware, infra (Fastly/CloudFront), invalidation hooks in services, and Makefile operations.

### Design sketch
1. **Profiling:** Instrument FastAPI middlewares to capture per-endpoint timings, storing results in Prometheus histogram.
2. **Layered cache:** Extend cache client to support tiered strategy (Redis + `fastapi-cache2` + CDN surrogate keys). Introduce domain-specific caches (strategy briefs, search results).
3. **Invalidation:** Add pub/sub channel for cache bust events triggered by create/update APIs, using Redis streams.
4. **Edge integration:** Provide Varnish/Fastly config templates; add signed URL support for multi-tenant isolation.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-015-multi-tier-cache.md` (tiers, TTLs, invalidation).
- No RFC needed if change is internal, but coordinate with ops.

### Migration & compatibility
- Cache defaults maintain current behavior. CDN integration optional per environment. Provide fallback to simple cache if env vars unset.

### Feature flag & rollout
- Flags: `ENABLE_RESPONSE_CACHE_V2`, `ENABLE_EDGE_CACHE_HINTS`. Start with read-only GET endpoints, then expand.

### Test plan
- Unit: cache client tier selection, invalidation handlers.
- Contract: ensure API headers include `Cache-Control` & surrogate keys.
- Load tests: use existing `make test.load` to observe 3–5× improvement target.

### CI impacts
- Need smoke test ensuring caching middleware doesn’t break auth. Possibly add GitHub Actions job invoking `make test.performance --dry-run` (if added).

### Rollback
- Toggle flags off; flush Redis & CDN caches via script. Remove surrogate headers.

### PR sequencing
1. **Profiling + metrics instrumentation.**
2. **Redis + local tier refactor, flag integration.**
3. **Invalidation bus + service hooks.**
4. **Edge/CDN documentation & rollout scripts.**

### Documentation updates
- Reference: new config keys.
- How-to: enabling CDN caching.
- Tutorial: performance tuning workflow.

---

## Phase 3 UX Quality Gates
- **Roadmap reference:** Upgrade.md Phase 3 (WCAG, mobile responsiveness, Lighthouse) & deliverables checklist.
- **Current state:** UI components exist, but there is no automated accessibility audit script coverage, Lighthouse CI, or documented mobile test plan (Phase 3 items unchecked).【F:Upgrade.md†L575-L588】 Mobile app exists but roadmap deliverable missing.

### Gap analysis & affected modules
- Need accessibility tooling (axe-core, keyboard nav tests), responsiveness validation (BrowserStack matrix), and performance budgets integrated into CI. Touches `apps/web`, `apps/mobile`, `scripts/accessibility_audit.py`, documentation.

### Design sketch
1. **Accessibility:** Expand `scripts/accessibility_audit.py` to run axe-puppeteer and output WCAG 2.1 AA report. Add Storybook accessibility checks.
2. **Responsive testing:** Configure Playwright suite covering breakpoints & device emulation. Document manual testing matrix.
3. **Performance:** Add Lighthouse CI config to run against built web app, gating at score >90.
4. **Mobile roadmap:** Produce document & backlog items for native features, aligning with roadmap deliverable.

### ADR / RFC
- No ADR needed; update `docs/architecture/adr/adr-005-ux-system.md` if exists, else create addendum summarising accessibility posture.

### Migration & compatibility
- Tooling only; does not change runtime behavior. Add optional env var to skip Lighthouse in constrained envs.

### Feature flag & rollout
- Introduce `ENABLE_LIGHTHOUSE_CI` to gate expensive checks. Accessibility fixes rolled out gradually with toggles for high-impact components.

### Test plan
- Unit: component-level accessibility tests (ARIA roles).
- Contract: Playwright responsiveness checks.
- E2E: Lighthouse CI job verifying performance budgets.

### CI impacts
- Add GitHub Action (nightly + PR optional) running Lighthouse & Playwright; ensure caching for node modules.

### Rollback
- Disable `ENABLE_LIGHTHOUSE_CI` and skip Playwright job if necessary.

### PR sequencing
1. **Audit tooling & CI scaffolding.**
2. **Accessibility fixes & documentation updates.**
3. **Responsive test matrix & mobile roadmap doc.**
4. **Performance tuning + enforce budgets.**

### Documentation updates
- Reference: update UX standards doc.
- How-to: running accessibility suite locally.
- Tutorial: mobile testing checklist.

---

## Predictive Strategy Analytics
- **Roadmap reference:** Upgrade.md medium-term enhancement #4.
- **Current state:** Forecast API generates random values without real models or time-series pipelines.【F:packages/api/src/stratmaster_api/services.py†L720-L789】 No dedicated analytics service for predictive modeling.

### Gap analysis & affected modules
- Need data ingestion (strategy metrics), model training (Prophet/PyMC), experiment tracking (MLflow), and API/UX updates. Impacts `packages/api` forecast routes, `packages/analytics`, `packages/ml-training`, data warehouse schemas.

### Design sketch
1. **Data pipeline:** Build ETL to aggregate historical metrics from `database/` into feature store (DuckDB or PostgreSQL timeseries table).
2. **Modeling:** Implement modular forecasting pipeline using `prophet` and `neuralprophet` within `packages/ml-training`, logging runs to MLflow.
3. **Serving:** Deploy inference microservice (FastAPI) exposing `/forecast` endpoints, consumed by API via gRPC/REST. Provide fallbacks to naive models.
4. **UX:** Update web/mobile to display forecast graphs with confidence intervals sourced from real models.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-016-predictive-analytics.md` (model selection, data governance).
- RFC recommended due to cross-functional impact and potential PII usage.

### Migration & compatibility
- Add migrations for analytics tables. Provide data backfill job. Keep existing random output behind `ENABLE_PREDICTIVE_ANALYTICS` flag until stable.

### Feature flag & rollout
- Flag `ENABLE_PREDICTIVE_ANALYTICS`. Begin with pilot tenants; include versioned model registry.

### Test plan
- Unit: feature engineering, model evaluation metrics.
- Contract: API schema responses, fallback logic when model unavailable.
- Integration: training pipeline on sampled dataset, verifying MLflow artifacts.

### CI impacts
- Add smoke tests with lightweight models; heavy training relegated to nightly job. Ensure deterministic tests by seeding data.

### Rollback
- Toggle flag to revert to heuristic forecasts. Archive MLflow experiment version.

### PR sequencing
1. **Data model & ETL scaffolding.**
2. **Model training pipeline + evaluation.**
3. **Serving layer + API integration.**
4. **UX updates & documentation; enable flag.**

### Documentation updates
- Reference: new analytics endpoints.
- How-to: operating forecasting service.
- Tutorial: interpreting predictive dashboards.

---

## Event-Driven Microservices Architecture
- **Roadmap reference:** Upgrade.md medium-term enhancement #5.
- **Current state:** System relies on synchronous FastAPI calls; no Kafka/Redis Streams producers or consumers exist.【F:Upgrade.md†L413-L418】

### Gap analysis & affected modules
- Need event bus, message schemas, producer/consumer services, and observability. Impacts `packages/api`, orchestrator, analytics, infra (Kafka cluster or Redis Streams), ops Helm charts.

### Design sketch
1. **Event bus selection:** Start with Redis Streams (existing dependency) for initial prototype, optionally upgrade to Kafka for production scale.
2. **Schema:** Define Protobuf/JSON schemas for key events (strategy_created, debate_updated, export_completed) stored in `packages/contracts`.
3. **Producers:** Instrument API service to emit events after transactional commits (use outbox pattern via Postgres table + Debezium or transactional outbox worker).
4. **Consumers:** Build dedicated workers for analytics, notifications, and audit logging.
5. **Observability:** Use OpenTelemetry for tracing event flow, and Prometheus metrics for lag.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-017-event-architecture.md` (bus choice, delivery semantics).
- RFC required due to architectural shift; includes SLA and migration plan.

### Migration & compatibility
- Adopt outbox pattern to ensure at-least-once delivery without breaking existing APIs. Provide migration to create outbox table and background dispatcher.

### Feature flag & rollout
- Flag `ENABLE_EVENT_STREAMING`. When off, producers no-op. Gradual rollout per event type.

### Test plan
- Unit: schema validation, producer/consumer logic.
- Contract: ensure events conform to schema (using `schemathesis` or custom validators).
- Integration: end-to-end flow in docker-compose with Redis Streams/Kafka.

### CI impacts
- Additional service container (Kafka or Redis streams) for integration tests. Add health check job verifying consumer lag < threshold.

### Rollback
- Disable producers (flag). Consumers exit gracefully. Clear outbox table entries if necessary.

### PR sequencing
1. **Schema + outbox infrastructure.**
2. **Initial producers (strategy, debate).**
3. **Consumers (analytics, notifications).**
4. **Kafka migration + ops tooling (optional).**

### Documentation updates
- Reference: event catalog.
- How-to: deploying stream processors.
- Tutorial: subscribing to events.

---

## Industry-Specific Strategy Templates
- **Roadmap reference:** Upgrade.md medium-term enhancement #6.
- **Current state:** Strategy synthesizer uses generic template with no vertical-specific variants or datasets.【F:packages/strategy/src/strategy_pipeline/strategy_synthesizer.py†L67-L577】 Seeds contain no industry libraries.

### Gap analysis & affected modules
- Need template library, taxonomy, dataset ingestion, UI selectors, and export mapping. Impacts `packages/strategy`, `apps/web` UI, `packages/api` strategy endpoints, seeds repository.

### Design sketch
1. **Template store:** Create `packages/strategy/src/strategy_pipeline/templates/` containing Jinja templates per vertical with metadata YAML.
2. **Selection logic:** Extend synthesizer to accept `industry` parameter, merging vertical heuristics (KPIs, assumptions).
3. **Dataset:** Add curated industry knowledge base to `seeds/industry/` and ingestion pipeline hooking into knowledge fabric.
4. **UX:** UI dropdown for industry selection; show recommended KPIs per vertical; ensure API schema updates allow optional `industry` field.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-018-industry-templates.md` documenting template structure.
- No RFC necessary.

### Migration & compatibility
- Default to existing template if industry unspecified. Provide data migration to seed template metadata table.

### Feature flag & rollout
- Flag `ENABLE_INDUSTRY_TEMPLATES`. Rollout per vertical to gather feedback.

### Test plan
- Unit: template rendering, metadata parsing.
- Contract: API accepts/returns industry field.
- E2E: UI flow selecting industry and verifying generated content.

### CI impacts
- Additional snapshot tests for templates. Update docs build to include template catalog.

### Rollback
- Remove metadata entries, toggle flag off to revert to generic template.

### PR sequencing
1. **Template metadata schema + loader.**
2. **Synthesis logic + API schema changes.**
3. **UI integration + docs.**
4. **Seed datasets + rollout toggles.**

### Documentation updates
- Reference: API field definitions.
- How-to: creating custom templates.
- Tutorial: using industry accelerators.

---

## Custom Model Fine-Tuning Platform
- **Roadmap reference:** Upgrade.md advanced feature #7.
- **Current state:** ML training package focuses on constitutional compliance; no infrastructure for fine-tuning or distributed training.【F:packages/ml-training/src/constitutional_trainer.py†L1-L404】 No orchestration or dataset registry.

### Gap analysis & affected modules
- Requires dataset management, compute orchestration (Ray, Hugging Face), model registry, compliance review. Touches `packages/ml-training`, `ops` (K8s jobs), `packages/providers`, billing subsystem.

### Design sketch
1. **Data management:** Implement secure dataset store with lineage tracking (MinIO + metadata DB). Build CLI for customer dataset uploads with validation.
2. **Training orchestration:** Use Ray Serve or Kubeflow to run fine-tuning jobs (LoRA adapters). Provide templates for GPTQ/PEFT.
3. **Model registry:** Extend MLflow or build custom registry for storing artifacts and versioning with evaluation metrics.
4. **Serving integration:** Update LiteLLM gateway to load adapters per tenant with access controls.
5. **Compliance:** Add review workflow requiring sign-off before deployment.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-019-fine-tuning-platform.md` (orchestration, data handling).
- RFC required (enterprise-impacting, significant investment).

### Migration & compatibility
- Introduce new DB tables for datasets/models. Provide scripts to migrate existing evaluation metrics. Keep default path using vendor models until flag enabled.

### Feature flag & rollout
- Flag `ENABLE_CUSTOM_FINE_TUNING`. Pilot with internal datasets; roll out to enterprise tier after compliance checks.

### Test plan
- Unit: dataset validation, job config serialization.
- Contract: API endpoints for job submission/status.
- Integration: end-to-end fine-tune on synthetic dataset in CI (reduced scale) and load adapter for inference.

### CI impacts
- Need dedicated pipeline (possibly nightly) to run miniature fine-tune for regression. Add linting for YAML job specs.

### Rollback
- Abort running jobs, disable adapters via flag. Remove dataset records if requested.

### PR sequencing
1. **Dataset registry + APIs.**
2. **Training orchestration scaffolding.**
3. **Serving integration + access controls.**
4. **Compliance workflow & documentation; enable flag.**

### Documentation updates
- Reference: API endpoints for fine-tuning.
- How-to: submitting fine-tune jobs.
- Tutorial: evaluating custom models.

---

## Advanced Knowledge Graph Reasoning
- **Roadmap reference:** Upgrade.md advanced feature #8.
- **Current state:** Knowledge pipeline supports ingestion and hybrid query but lacks causal inference or advanced reasoning over graphs.【F:packages/knowledge/src/knowledge/pipeline.py†L1-L100】 No integration with NebulaGraph beyond storage wrappers.

### Gap analysis & affected modules
- Need graph analytics (community detection, causal inference), query planner, reasoning service. Impacts `packages/knowledge`, orchestrator, strategy scoring, ML components.

### Design sketch
1. **Graph analytics module:** Extend `knowledge` package with algorithms (PageRank, motif detection) using `networkx`/`igraph`. Add NebulaGraph queries for multi-hop reasoning.
2. **Causal inference:** Integrate DoWhy/EconML to estimate causal effects between strategic variables, storing results alongside edges.
3. **Reasoning API:** Expose `/knowledge/reasoning` endpoints returning causal narratives and evidence trails, consumed by strategy engine.
4. **UI:** Visualize causal graph overlays in workspace, behind flag.

### ADR / RFC
- **ADR stub:** `docs/architecture/adr/adr-020-knowledge-reasoning.md` (algorithms, data privacy).
- RFC optional but recommended due to algorithmic complexity.

### Migration & compatibility
- Schema changes for storing causal metrics. Provide migration script and backfill job. Keep existing query endpoints unaffected when flag off.

### Feature flag & rollout
- Flag `ENABLE_KNOWLEDGE_REASONING`. Start with analytics-only mode (reports) before exposing UI automation.

### Test plan
- Unit: graph analytics outputs, causal estimator validation with synthetic data.
- Contract: API response schema & latency budgets.
- Integration: evaluate strategy recommendations incorporating causal weights, ensuring regressions caught.

### CI impacts
- Additional dependencies (networkx, dowhy). Ensure deterministic tests by seeding random number generators.

### Rollback
- Toggle flag off; drop new tables if necessary (after backup). Provide script to remove causal metrics.

### PR sequencing
1. **Graph analytics foundation.**
2. **Causal inference integration + storage.**
3. **API/UX exposure.**
4. **Documentation & rollout.**

### Documentation updates
- Reference: reasoning API.
- How-to: interpreting causal reports.
- Tutorial: using causal insights in strategy planning.

---

*Prepared by StratMaster engineering planning bot — January 2024.*
