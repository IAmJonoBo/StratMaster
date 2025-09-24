# Frontier Implementation Plan

This plan turns the gaps documented in [GAP_ANALYSIS.md](GAP_ANALYSIS.md) into a sequenced backlog. Items reference existing issues under `/issues` when available and introduce additional tasks needed to reach the frontier targets from the audit brief.

## Now (0–2 weeks)

| Item | Owner | Effort | Dependencies | Exit Criteria |
| --- | --- | --- | --- | --- |
| Instrument delivery telemetry (new) | Platform Eng | M | Access to GitHub API / metrics store | DORA exporter captures deploy frequency, lead time, change failure rate, and MTTR per deployment, surfaced in CI summary; failing deploys auto-tagged for incident review.【F:.github/workflows/ci.yml†L1-L180】 |
| Define service SLOs & alerts (new) | SRE | M | Product SLA inputs; Prometheus running via `make monitoring.up` | SLO docs published with latency/availability targets, error budgets, and Prometheus alert rules deployed for API + MCP services.【F:docs/operations-guide.md†L135-L171】【F:Makefile†L120-L177】 |
| Close accessibility regression TODOs (extends workflow) | UX Eng | S | Lighthouse token; Playwright fixtures | `performance-regression` job compares latest Lighthouse runs to baselines and fails on regression >2%; HEART backlog triage report generated per PR.【F:.github/workflows/accessibility-quality-gates.yml†L168-L210】 |
| Harden docs/code parity automation (extends existing job) | Docs Eng | S | FastAPI endpoint discovery script | `parity-check` job extracts API routes, verifies docs coverage, and fails CI when mismatched.【F:.github/workflows/docs.yml†L134-L167】 |
| Kick off Model Recommender V2 (#002) | Routing Team | M | Access to LMSYS/MTEB mirrors | External data clients land, scheduler seeds persistent cache, and router exposes diagnostic API with dynamic scores behind `ENABLE_MODEL_RECOMMENDER_V2`.【F:packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py†L117-L195】【F:issues/002-model-recommender-v2.md†L1-L32】 |

### Supporting Activities
- Run baseline Lighthouse audit to establish INP/CLS targets before tightening budgets.【F:lighthouse-budget.json†L27-L49】
- Draft STRIDE threat catalogue outline so later work can populate details.【F:ops/threat-model/stride.md†L1-L3】

## Next (2–6 weeks)

| Item | Owner | Effort | Dependencies | Exit Criteria |
| --- | --- | --- | --- | --- |
| Golden signal dashboards & incident loop (new) | SRE + Data | M | Prometheus metrics exported; Grafana provisioner | Grafana dashboards for latency, saturation, errors, and traffic checked in; alert routing to Slack/PagerDuty; incident runbook links to dashboards.【F:Makefile†L120-L177】 |
| Retrieval benchmarking in CI (extends API perf) | ML Platform | M | APScheduler + BEIR datasets | CI job runs SPLADE/ColBERT benchmarks nightly with stored baselines; failures block deploy when NDCG@10 drops >5%.【F:packages/api/src/stratmaster_api/performance.py†L320-L398】 |
| Real-time collaboration service (#001) | Collaboration Team | L | Redis/Postgres infra; Keycloak tokens | WebSocket service, CRDT persistence, and UI bindings ship behind `ENABLE_COLLAB_LIVE`; <150 ms LAN latency proven via Playwright tests.【F:issues/001-real-time-collaboration.md†L1-L33】 |
| Security posture uplift (new) | Security | M | Updated STRIDE doc draft | STRIDE, ASVS L2, and OWASP LLM Top-10 mapped per component with residual risk register; SBOM job emits CycloneDX for every image push in CI.【F:.github/workflows/ci.yml†L55-L71】【F:ops/threat-model/stride.md†L1-L3】 |
| Accessibility backlog triage (#005) | UX Eng | S | Updated Lighthouse baselines | WCAG 2.2 AA issues collected, prioritized, and linked to HEART metrics with remediation dates; budgets updated to INP ≤200 ms, LCP ≤2.5 s.【F:lighthouse-budget.json†L27-L49】 |

### Supporting Activities
- Integrate docs parity results with release notes to surface breaking API/doc gaps automatically.【F:.github/workflows/docs.yml†L134-L167】【F:RELEASE_NOTES.md†L1-L120】
- Begin SBOM storage and signing pipeline design to align with SLSA goals.【F:.github/workflows/ci.yml†L55-L145】

## Later (6+ weeks)

| Item | Owner | Effort | Dependencies | Exit Criteria |
| --- | --- | --- | --- | --- |
| Predictive analytics & dashboards (#006) | Data Science | L | Reliable telemetry feeds | HEART and product metrics dashboards correlate usage with strategy outcomes; predictive models validated via backtesting before rollout.【F:issues/006-predictive-analytics.md†L1-L40】 |
| Event-driven architecture & streaming (#007) | Platform | L | Kafka/stream infra budget approval | Event bus delivers audit logs and model telemetry; retry queue + dead-letter support integrated with incident loop diagrammed in `/docs/diagrams/error-handling.md`.【F:issues/007-event-architecture.md†L1-L36】【F:docs/diagrams/error-handling.md†L1-L24】 |
| Industry templates & fine-tuning (#008/#009) | Solutions | M | Model recommender & collaboration features | Vertical playbooks and fine-tuning workflows launch after telemetry + collaboration stable; guardrails validated with mutation tests and AI evaluations.【F:issues/008-industry-templates.md†L1-L34】【F:issues/009-fine-tuning-platform.md†L1-L36】 |
| Knowledge reasoning enhancements (#010) | Research | M | Retrieval benchmarks stable | Causal reasoning modules and graph analytics validated against new benchmark suite; observability expanded to include reasoning latency/error metrics.【F:issues/010-knowledge-reasoning.md†L1-L34】 |

### Governance & Reporting
- Monthly audit review ensures DORA/SLO dashboards stay green and backlog items adjust to new findings.
- Release engineering updates CHANGELOG/RELEASE_NOTES with telemetry highlights and regression summaries each sprint.【F:RELEASE_NOTES.md†L1-L120】
