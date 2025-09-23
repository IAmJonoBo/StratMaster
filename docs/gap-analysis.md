# StratMaster Frontier Gap Analysis

This document inventories the current StratMaster monorepo and highlights the frontier capabilities required to meet the privacy-first, OSS-first Strategy AI mandate. Each pillar below captures the observed state (based on repository inspection and root documentation), the critical gaps, an OSS-first remediation plan, acceptance criteria, and key risks with mitigations.

## Ingestion & Research

**Current State**
- `packages/ingestion` focuses on structured document loaders and routing but lacks an explicit OCR confidence feedback loop.
- Research flows rely on the existing MCP research server with scripted web scraping and enrichment described in `PROJECT.md`.
- Seeds ship mainly as JSON assets (`demo-ceps-jtbd-dbas.json`) without the newly required multi-format/binary corpus for offline validation.

**Gaps**
- No unified ingestion pipeline that handles OCR-heavy formats (scanned PDFs, images) with quality scoring.
- Provenance pack (hash, parser, licence, crawl metadata) is not persisted uniformly.
- Clarification workflow for low-confidence parses is absent.
- Offline seed bundle mandated by stakeholders (24 artefacts across PDF/DOCX/XLSX/CSV/PPTX/HTML/TIFF) is not yet curated or wired into tests.

**OSS-First Remediation**
- Introduce a modular ingestion orchestrator that calls Unstructured, Apache Tika, pdfplumber, docTR/Tesseract, Camelot/tabula-py, and Polars.
- Attach provenance + hygiene policies (hashing, licence, redaction) before storage using DuckDB/Polars transformations.
- Add a “Confidence & Clarify” service that generates follow-up questions when confidence < 0.7, exposed via `POST /ingestion/clarify`.
- Publish the stakeholder-approved offline bundle (24 artefacts, ≤ 500 MB) alongside SHA-256 manifest in `seeds/offline-bundle/` and ensure ingestion regression tests span every format.

**Acceptance Criteria**
- `parse_success` ≥ 0.98 on demo corpus and ≥ 0.95 across each seed format; confidence scoring persisted per chunk.
- Provenance metadata available for every stored artefact, including binary bundle manifest with licence references.
- Clarification API blocks promotion to "grounded" until acknowledged.

**Risks & Mitigations**
- *Risk*: OCR latency on CPU-only hardware. *Mitigation*: Offer quantised docTR models and allow asynchronous batching.
- *Risk*: Parser drift vs. file formats. *Mitigation*: Regression tests on seeds and nightly smoke runs.
- *Risk*: Seed bundle distribution bloat. *Mitigation*: Host artefacts via object storage with checksum validation and scripted download.

## Knowledge Fabric

**Current State**
- Knowledge MCP surfaces GraphRAG style traversal, but NebulaGraph community detection and narrative summarisation are not automated.

**Gaps**
- Missing structured entity/relationship extraction pipeline with explainable metrics.
- No automated community detection (Leiden/Louvain) or knowledge narratives.

**OSS-First Remediation**
- Build extraction microservice using spaCy + transformers + OpenAI-compatible OSS models (e.g., Mixtral via vLLM) via MCP adapters.
- Schedule NebulaGraph jobs for community detection and produce narrative summaries stored in DuckDB.

**Acceptance Criteria**
- Entity/relationship recall ≥ defined thresholds on demo corpus.
- Narratives available via `/knowledge/fabric` endpoint with provenance references.

**Risks & Mitigations**
- *Risk*: Graph explosion. *Mitigation*: Hash-based deduplication + TTL policies.
- *Risk*: Model regressions. *Mitigation*: Add evaluation harness for entity/rel extraction.

## Retrieval

**Current State**
- Hybrid retrieval uses BM25 + dense embeddings (Qdrant/OpenSearch) per documentation but lacks advanced sparse/dense combination (SPLADE/ColBERT/BGE).

**Gaps**
- No SPLADE expansion or ColBERT late interaction pipeline.
- Lacks reranker with explicit grounding spans.

**OSS-First Remediation**
- Add SPLADE (distil) models served via PyTorch CPU inference and ColBERT for late interaction.
- Integrate BGE reranker; create `configs/retrieval/hybrid.yaml` to tune weights.

**Acceptance Criteria**
- Hybrid recall@50 ≥ 0.90; grounding spans returned with offsets.
- Config toggles for CPU vs GPU inference validated.

**Risks & Mitigations**
- *Risk*: Index build time. *Mitigation*: Incremental indexing + nightly compaction.
- *Risk*: Model packaging. *Mitigation*: Publish gguf/onnx snapshots into artefact store.

## Reasoning

**Current State**
- Existing orchestrator supports constitutional debate but lacks explicit Chain-of-Verification and reflexive critique loop.
- Model routing configs do not yet encode the newly approved OSS-only foundation model allow-list or licence metadata.

**Gaps**
- Missing CoVe node with structured output validation.
- No enforced schema-guided decoding for strategic artefacts.
- Model governance lacks enforcement of stakeholder-approved defaults (Mixtral 8×7B, Llama 3 8B, Nous-Hermes 2 7B, Phi-3 Medium) and audit trail for overrides.

**OSS-First Remediation**
- Implement CoVe workflow stage in LangGraph/Temporal orchestrator; integrate reflexive critic agent using OSS models (Mixtral 8×7B, Llama 3 8B, Nous-Hermes 2 7B, Phi-3 Medium) served via vLLM/Ollama with quantised variants for offline.
- Adopt Outlines/xgrammar for JSON schema constrained decoding (Pydantic v2 models).
- Embed licence metadata + provenance for each model selection in router policies and expose override audit logs in Langfuse.

**Acceptance Criteria**
- Self-consistency ≥ 0.70; contradiction rate ≤ 2% on eval set.
- Chain-of-Verification trace stored per recommendation.
- Router enforces allow-listed models by default, records overrides with rationale, and surfaces licence notices in API responses.

**Risks & Mitigations**
- *Risk*: Structured decoding failure on long generations. *Mitigation*: Streaming validator with automatic retry on schema violations.
- *Risk*: Increased latency. *Mitigation*: Parallel critic execution + caching of verified facts.
- *Risk*: Licence drift if tenants toggle models. *Mitigation*: Add config validation + compliance CI checks for router manifests.

## Orchestration

**Current State**
- Temporal is provisioned but durable workflows/idempotency coverage is inconsistent in codebase.

**Gaps**
- Workflows not codified for ingest→retrieve→reason path; no DLQ or idempotency guard rails.
- Run identifiers are not surfaced via API responses.

**OSS-First Remediation**
- Define Temporal workflows with retry + backoff policies, DLQ queue, and idempotency keys.
- Extend API responses to expose run IDs and checkpoint metadata.

**Acceptance Criteria**
- P95 end-to-end latency ≤ 180s on demo corpus; P99 workflow success ≥ 99%.
- Failed runs appear in DLQ with actionable metadata.

**Risks & Mitigations**
- *Risk*: Temporal schema drift. *Mitigation*: Migration tests + versioned workflows.
- *Risk*: Lost idempotency state. *Mitigation*: Persist keys in Postgres with TTL cleanup.

## Evals & Observability

**Current State**
- Eval harness exists but lacks RAGAS/FActScore/TruthfulQA coverage; observability mostly Prometheus/Grafana.
- Usage analytics currently limited to raw metrics; no privacy-preserving engagement dashboards meeting k-anonymity ≥ 5.

**Gaps**
- No automated eval gating; Langfuse/OTEL instrumentation incomplete.
- No OpenLineage integration for data flows.
- Usage analytics requirements (daily active workspaces, completion/fallback, eval pass rates with differential privacy) are unmet.

**OSS-First Remediation**
- Expand `packages/evals` with RAGAS, FActScore, TruthfulQA suites; integrate into CI via GitHub Actions.
- Emit Langfuse spans, OTEL traces, and OpenLineage events to Marquez.
- Configure kill-switch when eval thresholds fail.
- Build privacy-preserving analytics pipeline (ClickHouse/Parquet or Postgres rollups) applying k-anonymity ≥ 5 and Laplace noise, surface dashboards in Grafana, and document retention (30 days) + hashing approach.

**Acceptance Criteria**
- CI fails when eval thresholds breached; dashboards show spans/traces per run.
- Kill-switch toggles strategy output to "Not evidence-qualified" with remediation steps.
- Analytics dashboards expose required metrics with privacy guards (k-anonymity ≥ 5, DP noise) and automatic 30-day data expiry.

**Risks & Mitigations**
- *Risk*: Eval flakiness. *Mitigation*: Use deterministic seeds and cached corpora.
- *Risk*: Observability overhead. *Mitigation*: Sampling strategies + compression.
- *Risk*: Analytics data re-identification. *Mitigation*: Enforce hashing, k-anonymity validation in CI, and manual privacy reviews.

## Security & Compliance

**Current State**
- Security guide references SSO, audit logging, and multi-tenant isolation; enforcement for egress allow-lists and prompt injection is partial.

**Gaps**
- No OPA/Rego enforced egress policies in repo.
- Secrets management not yet converted to SOPS/age; audit logging coverage incomplete.

**OSS-First Remediation**
- Add OPA policies and sidecar enforcement; define allow-listed domains per MCP server.
- Store secrets via SOPS + age with documented rotation; implement prompt injection guards in orchestrator policies.

**Acceptance Criteria**
- Security scans (Trivy/Grype, Semgrep, Bandit) run in CI and pass.
- Audit logs include principal, action, artefact, and evidence of redaction.

**Risks & Mitigations**
- *Risk*: Policy misconfiguration blocking legitimate traffic. *Mitigation*: Provide staging/bypass toggles with telemetry.
- *Risk*: Secret rotation friction. *Mitigation*: Documented automation scripts + fallback credentials.

## UX/UI/UID

**Current State**
- UI provides tri-pane layout and mobile approvals but lacks wizard onboarding, evidence badges, and argument mapping per frontier brief.

**Gaps**
- Missing Projects workspace, Onboarding Wizard, Expert Council panel (with weighted quorum + dissent rationale), and advanced visualisations (Argument Map, Graph Explorer, Strategy Kanban, Experiment Console).
- Accessibility posture to WCAG 2.1 AA not fully documented.

**OSS-First Remediation**
- Implement new React components (tri-pane enhancements, wizard flows) using OSS component libraries (Radix UI, shadcn, D3/VisX).
- Add Evidence Badges (GRADE) and assumption heat-map overlays; integrate Expert Council view showing Strategic Leadership 0.20, Org Psychology 0.15, Service Design 0.15, Communications 0.15, Brand Science 0.15, Economics 0.20 weights plus quorum status/objections.
- Run axe-core automated accessibility tests and manual keyboard navigation checks.

**Acceptance Criteria**
- UX flows validated with usability ≥ 0.75; accessibility audit passes WCAG 2.1 AA subset.
- Evidence badges and assumption heat-map visible on strategy detail view; Expert Council panel surfaces quorum score, dissent reasons, and tie-break highlighting per stakeholder rules.

**Risks & Mitigations**
- *Risk*: UI performance on low-end hardware. *Mitigation*: Code-splitting and skeleton loading.
- *Risk*: Accessibility regressions. *Mitigation*: CI gating with axe/pa11y.

## Developer Experience & Operations

**Current State**
- Make targets exist for bootstrap/dev flows but low-spec CPU profile and automated smoke/eval gating are not fully scripted.
- CI workflows do not yet respect the 20-minute per-push budget (hard limit 22 minutes) communicated by engineering leadership.

**Gaps**
- No single command for CPU-only offline profile.
- CI lacks comprehensive SBOM + security scans + Helm lint gating while staying within 20-minute runtime budget.

**OSS-First Remediation**
- Extend Makefile/scripts for `make dev.low-spec`, `make eval.ragas`, `make security.scan`.
- Add GitHub Actions for lint/type/test, evals, security scans (Trivy/Grype, Semgrep, Bandit), Helm lint, and SBOM (Syft) with attestations.
- Introduce caching/matrix strategies so lint/type/test finish ≤ 12 minutes and the full workflow ≤ 20 minutes; move heavier eval/security sweeps to nightly schedule with shared artefacts.

**Acceptance Criteria**
- Developers can bootstrap and run smoke/eval/security pipelines with documented one-liners.
- CI pipeline enforces failure on regressions or security findings and reports per-job runtime proving compliance with 20-minute ceiling.

**Risks & Mitigations**
- *Risk*: Increased CI duration. *Mitigation*: Cache dependencies, parallelise jobs, provide nightly heavy jobs.
- *Risk*: Developer friction with new scripts. *Mitigation*: Document fallback manual steps.
- *Risk*: Cache misses causing budget overruns. *Mitigation*: Pre-build Docker layers and warm caches via scheduled workflows.

## Offline & Edge

**Current State**
- Offline story mentions Ollama/vLLM but lacks documented workflow for CPU-only completion.
- Seed corpus currently limited to JSON bundle; binary artefact pack (24 docs with checksums) not yet produced or referenced in docs.

**Gaps**
- No toggleable low-spec mode with gguf models and local caches.
- Demo seed corpus bundling (per stakeholder spec) not scripted nor validated end-to-end.

**OSS-First Remediation**
- Provide config profile using Ollama + gguf embeddings, local rerankers, DuckDB caches, and MinIO-based artefact storage.
- Bundle the approved 24-document corpus with manifest + downloader script and offline evaluation harness covering ingestion→retrieval→reasoning using only allow-listed models.

**Acceptance Criteria**
- Offline mode completes ingest→recommend within defined wall-time on CPU-only laptop.
- Local cache warms and replays without external network access.
- Seed downloader verifies SHA-256 manifest and surfaces licence metadata for each artefact.

**Risks & Mitigations**
- *Risk*: Model size vs. laptop memory. *Mitigation*: Offer tiered profiles (7B/13B) and streaming inference.
- *Risk*: Seed corpora staleness. *Mitigation*: Provide update script and checksum verification.
