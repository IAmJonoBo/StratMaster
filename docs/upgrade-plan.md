# StratMaster 90-Day Upgrade Plan

This roadmap sequences the frontier upgrades across six sprints (Sprint 0–5) with explicit objectives, deliverables, quality gates, risks, and rollback plans. Each sprint is assumed to last two weeks except Sprint 0 (one week discovery) and Sprint 5 (three weeks hardening). Total duration ≈ 90 days.

## Sprint 0 — Discovery & Enablement (Week 1)
- **Objectives**: Confirm repo inventory, stand up baseline observability, capture stakeholder requirements for ingestion/retrieval upgrades, model governance, analytics privacy, and CI budgets.
- **Key Deliverables**:
  - docs/gap-analysis.md & docs/open-questions.md socialised with stakeholders (including resolved answers incorporated).
  - Low-spec hardware profile benchmarked against current stack.
  - CI baselines captured (runtime, pass/fail metrics) vs. 20-minute ceiling.
- **Definition of Done / Quality Gates**:
  - Inventory accepted by architecture & product leads.
  - Smoke tests (make test, make lint) passing on reference laptop.
- **Risks & Mitigations**: Risk of hidden drift vs. docs → run validation scripts; missing stakeholder alignment → schedule design reviews.
- **Rollback Plan**: None (information gathering only).

## Sprint 1 — Ingestion & Research Foundations (Weeks 2–3)
- **Objectives**: Ship PR-A ingestion upgrades, publish offline seed bundle, and research clarifications.
- **Key Deliverables**:
  - Modular ingestion orchestrator with OCR, provenance, and clarify workflows.
  - Offline bundle (24 artefacts ≤ 500 MB) + manifest + download script integrated into seeds/tests.
  - Research MCP updated with document ingestion tools.
  - Initial eval fixtures for ingestion accuracy.
- **Definition of Done / Quality Gates**:
  - parse_success ≥ 0.98 overall and ≥ 0.95 per format; clarify workflow triggered for <0.7 confidence cases.
  - API tests covering `/ingestion/ingest` and `/ingestion/clarify` endpoints.
- **Risks & Mitigations**: CPU latency → deliver async queue; OSS model compatibility issues → maintain fallback stub.
- **Rollback Plan**: Toggle new orchestrator behind feature flag; keep legacy parser available.

## Sprint 2 — Retrieval & Knowledge Fabric (Weeks 4–5)
- **Objectives**: Implement PR-B retrieval and knowledge fabric enhancements while prepping model policy hooks.
- **Key Deliverables**:
  - SPLADE + ColBERT indexes, BGE reranker integrated.
  - configs/retrieval/hybrid.yaml with weighting strategies.
  - Knowledge fabric entity/relationship extraction microservice.
  - Router/schema groundwork for allow-listed model enforcement surfaced in configs.
- **Definition of Done / Quality Gates**:
  - Hybrid recall@50 ≥ 0.90; grounding spans validated.
  - Entity/relationship extraction evals meeting thresholds.
- **Risks & Mitigations**: Index build time → incremental builds; Graph explosion → TTL dedupe.
- **Rollback Plan**: Maintain toggles to disable SPLADE/ColBERT and revert to existing BM25 + dense pipeline.

## Sprint 3 — Reasoning & Orchestration (Weeks 6–7)
- **Objectives**: Deliver PR-C (CoVe + reflexive critique) and PR-D (Temporal workflows) with model allow-list governance.
- **Key Deliverables**:
  - Chain-of-Verification node integrated; Outlines/xgrammar decoding enforced.
  - Router policies encode Mixtral 8×7B, Llama 3 8B, Nous-Hermes 2 7B, Phi-3 Medium defaults with licence metadata + override audit logging.
  - Temporal workflows with retries, DLQ, idempotency keys.
  - API responses exposing run IDs.
- **Definition of Done / Quality Gates**:
  - Self-consistency ≥ 0.70; contradiction ≤ 2% on eval corpus.
  - Temporal dashboards show per-run status; DLQ tested via fault injection; router audit logs visible in Langfuse.
- **Risks & Mitigations**: Increased latency → stage parallel critic runs; workflow complexity → provide diagrams & unit tests.
- **Rollback Plan**: Keep fallback direct orchestrator path available; degrade gracefully to advisory mode if CoVe fails.

## Sprint 4 — Evaluations, Observability & Security (Weeks 8–9)
- **Objectives**: Execute PR-E (evals/observability) and PR-I (security/compliance) prerequisites, plus privacy-preserving usage analytics.
- **Key Deliverables**:
  - RAGAS, FActScore, TruthfulQA harness integrated into CI.
  - Langfuse spans, OTEL traces, OpenLineage events wired to dashboards.
  - Usage analytics pipeline delivering workspace/day aggregates with k-anonymity ≥ 5, differential privacy noise, 30-day retention, and automated deletion.
  - OPA/Rego policies, secrets via SOPS/age, audit logging coverage expanded.
  - GitHub Actions pipeline for lint/type/test/evals/security/Helm lint/SBOM.
- **Definition of Done / Quality Gates**:
  - CI fails on threshold regressions; kill-switch works in staging.
  - Security scans produce zero high severity issues; policies validated with allow-list tests and analytics privacy checks (k-anonymity validation).
- **Risks & Mitigations**: CI runtime inflation → caching & matrix builds; policy misfires → staged rollout with dry-run mode.
- **Rollback Plan**: Provide bypass toggles for OPA & kill-switch with audit logging when disabled.

## Sprint 5 — UX/UI/Expert Council & Offline Hardening (Weeks 10–12)
- **Objectives**: Finalise PR-F (Expert Council), PR-G (UX/UI/UID), PR-H (Offline/Edge) while stabilising operations and analytics.
- **Key Deliverables**:
  - Expert Council MCP adapters, doctrines, and UI panel reflecting stakeholder weights/quorum rules, including dissent surfacing.
  - Tri-pane desktop enhancements, onboarding wizard, Evidence Badges, Argument Map, Graph Explorer, Strategy Kanban, Experiment Console.
  - Offline low-spec mode with gguf models (Mixtral 8×7B, Llama 3 8B, Nous-Hermes 2 7B, Phi-3 Medium), local cache, demo seed bundle, and documented workflow.
  - docs/dev-quickstart.md & updated operations guides.
- **Definition of Done / Quality Gates**:
  - Usability ≥ 0.75; accessibility audit passes; offline flow completes end-to-end on CPU profile with checksum-verified bundle.
  - Council scoring + vote recorded and surfaced in UI with quorum + objection messaging per stakeholder guidance.
- **Risks & Mitigations**: UI scope creep → incremental feature flags; offline packaging issues → pre-flight hardware matrix.
- **Rollback Plan**: Keep old UI routes accessible; offline mode opt-in until validated.

## Continuous Threads
- **Research & Compliance Reviews**: Weekly check-ins to review docs/open-questions.md and update mitigation strategies.
- **Documentation**: Update architecture, operations, and troubleshooting guides each sprint.
- **Change Management**: Use feature flags and config toggles for progressive delivery; maintain rollback scripts; track per-workflow runtime to ensure CI budget adherence.

## Risk Burn-Down Strategy
- Maintain heat map of high/medium/low risks per sprint; retire risks once mitigations validated in staging.
- Track performance metrics (latency, success rate) to ensure improvements trend positive before enabling for tenants.

## Rollback & Contingency Philosophy
- Every major feature shipped behind config flag or MCP policy gate.
- Provide automated rollback scripts for Temporal workflows, indexes, and configs.
- Preserve offline-friendly snapshots to restore baseline functionality if new models regress.
