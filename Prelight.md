StratMaster — Frontier-Grade Audit & Upgrade Tasking (for Codex/Copilot)

You are Codex working inside the StratMaster monorepo.
Your job is to: (1) inventory the current state, (2) perform a repository-aware gap analysis against frontier standards, (3) generate precise PRs to close gaps, and (4) scaffold tests, evals, and UX so the system produces insightful, usable, decision-grade strategies on/offline with zero-cost OSS defaults.

1) Grounding (read these first, then explore code)
	•	Root docs: README.md, PROJECT.md (engineering blueprint), ALPHA_READINESS_SUMMARY.md, IMPLEMENTATION_SUMMARY.md, PHASE3_GAP_ANALYSIS.md, ENHANCED_IMPLEMENTATION.md, EXPERTISE_MCP_IMPLEMENTATION.md.  ￼
	•	Source layout hints: apps/web, packages/* (api, orchestrator, agents, research, knowledge, evals, mcp-servers, providers), helm/, docker/, ops/, infra/, configs/*, tests/*, seeds/*.  ￼
	•	Quick-start & service map are defined in root docs (compose + URLs). Use them when running local checks.  ￼

⸻

1) Mission & guardrails
	•	Goal: Deliver a privacy-first, OSS-first Strategy AI that can ingest documents (OCR & structured), research the web with provenance, reason reflexively (multi-agent, adversarial + constitutional + chain-of-verification), and output actionable strategic recommendations with evidence gates and forecast/causal support—all with great UX/DX and low entry requirements.
	•	Hard constraints:
	•	Zero licence cost by default (OSS): vLLM/Ollama, SearxNG + Playwright, Unstructured/Tika/docTR/Tesseract, Qdrant, OpenSearch, NebulaGraph, DuckDB/Polars/Arrow, Temporal, OpenTelemetry, Prometheus/Grafana, Langfuse (self-hosted).
	•	No raw HTTP from LLMs; all external access via MCP servers and allow-listed policies (deny-by-default egress).
	•	Per-tenant isolation & privacy (self-hosted default); optional OpenAI provider/client mode is off by default.
	•	Structured output only for machine-readable artefacts (JSON Schema / Pydantic v2 models).
	•	Performance posture: Must run well on CPU-only dev laptops (quantised 7–14B class) and scale up (vLLM on GPU). Provide knobs for batch/kv-cache/speculative decoding.

⸻

2) Deliverables (produce all as part of this run)
	1.	Repo-aware Gap Analysis → docs/gap-analysis.md
	•	Sections: Ingestion/Research, Knowledge Fabric, Retrieval, Reasoning, Orchestration, Evals/Obs, Security/Compliance, UX/UI/UID, DX/Ops, Offline/Edge.
	•	For each: current state → gap → OSS-first fix → acceptance criteria → risks/mitigations.
	2.	Upgrade Plan & Sprints → docs/upgrade-plan.md
	•	90-day roadmap split into Sprints 0–5 with DoD/quality gates, risk burn-down, and rollback.
	•	Include a low-spec mode (CPU-only, quantised models) and self-contained offline seed.
	3.	PR-ready diffs (as fenced diff blocks + file paths):
	•	PR-A Ingestion+Parsing: OCR & multi-format pipeline (Unstructured, Tika, pdfplumber, docTR/Tesseract, Camelot, tablib) + “Confidence & Clarify” pass (ask questions when confidence < 0.7).
	•	PR-B Retrieval++: SPLADE + ColBERT + BGE reranker with hybrid orchestrator config and guided grounding spans.
	•	PR-C Reasoning++: add Chain-of-Verification (CoVe) node, reflexive self-critique, and structured decoding (Outlines/xgrammar) for all agents.
	•	PR-D Orchestration: wire Temporal durable workflows, idempotency keys, retries, DLQs; expose run IDs in API.
	•	PR-E Evals & Observability: RAGAS/FActScore/TruthfulQA suites; Langfuse spans; OpenTelemetry traces; OpenLineage to Marquez; kill-switches on threshold regressions.
	•	PR-F Expert Council: discipline MCP (psychology, design/UX, communication, brand science, economics), doctrines/weights, council vote, UI panel.
	•	PR-G UX/UI/UID: tri-pane desktop + wizard onboarding (cross-platform), Projects workspace, Argument Map, Evidence Badges (GRADE), Assumption Heat-map, Graph Explorer, Strategy Kanban, Experiment Console; add **error-anticipation” UX (hints, recoveries).
	•	PR-H Offline/Edge: low-spec profiles (Ollama/gguf), local object cache, bundle minimal seeds.
	•	PR-I Security/Compliance: OPA/Rego egress allow-list, secrets SOPS/age, audit logging, prompt-injection guards.
	4.	Configs & Thresholds
	•	configs/retrieval/*.yaml, configs/evals/thresholds.yaml, configs/privacy/redaction.yaml, configs/experts/* (weights, doctrines), configs/router/models-policy.yaml (with OpenAI provider disabled by default).
	5.	CI Enhancements (.github/workflows/*)
	•	Lint/type/test; eval suites with threshold gates; security scans (Trivy/Grype, Semgrep, Bandit); Helm/chart lint; SBOM (Syft) + provenance attestations.
	6.	Dev On-Ramp → docs/dev-quickstart.md
	•	One-liners to boot stack, seed, smoke-test, and open dashboards; troubleshooting; perf profiles (CPU vs GPU).

⸻

3) Execution plan (passes)

Pass 1 — Inventory & sanity
	•	Parse and summarise current packages, MCP servers, APIs, UI app, Helm/compose services, and docs. Cross-check the files present in main.  ￼
	•	Verify local bring-up commands from docs (compose/Helm) and note any drift.  ￼

Pass 2 — Frontier benchmarks & targets
	•	Ingestion/Parsing: Add robust, format-aware pipeline:
	•	HTML/Markdown/PDF/Office (Unstructured/Tika), OCR (docTR/Tesseract), tables (Camelot/tabula-py), spreadsheets/CSVs (Polars/pyarrow), images (pytesseract + layout).
	•	Provenance pack (URL, time, hash, parser, licence) and PII redaction (Presidio) before storage.
	•	Confidence & Clarify: compute per-chunk confidence; when <0.7, create clarifying questions for the user and block promotion to “grounded”.
	•	Research: SearxNG → Playwright crawl; robots & rate-limits; licence notes kept.
	•	Knowledge Fabric: extraction → entities/relations → NebulaGraph communities (Leiden/Louvain) + narrative summaries.
	•	Retrieval: BM25 + dense (Qdrant) + SPLADE + ColBERT + BGE reranker → hybrid scores, grounding spans, de-dup by chunk hash.
	•	Reasoning: ReAct tool use, CoVe, adversarial debate, Constitutional Critic, reflexive self-critique loop, guided decoding to Pydantic schemas.
	•	Orchestration: Temporal workflows, idempotency keys, retries/backoff, DLQs, saga compensation; LangGraph agent graph checkpoints.
	•	Evals/Obs: RAGAS/groundedness/recall; contradiction rate; GRADE badge presence; Langfuse spans; OTEL traces; OpenLineage emit; kill-switch to “Not evidence-qualified” when gates fail.
	•	UX/UI/UID: Desktop tri-pane; Projects and Onboarding Wizard (cross-platform); Zen-inspired minimal visual language (Tailwind + Radix/shadcn); accessibility WCAG 2.1 AA; mobile review/approve/annotate slice only; hints & error recovery UX.
	•	Offline/Edge: local embeddings (gguf), smaller rerankers, local cache; minimal seed corpora for demos.
	•	Security/Compliance: OPA/Rego egress allow-lists; prompt-injection mitigations; secrets & audit; POPIA/GDPR defaults.
	•	OpenAI/Copilot (optional): Provider/client adapters off by default; Copilot prompt file for dev ergonomics (no tenant data egress).

Pass 3 — Propose changes
	•	For each gap, produce file-scoped diffs, config snippets, and tests. Keep blast radius small; prefer additive changes.

Pass 4 — Tests & quality gates
	•	Unit + integration + e2e (Playwright) + eval jobs. CI must fail on threshold regression.

Pass 5 — Final sweep
	•	Validate offline profile; ensure all LLM network access goes through MCP; schemas are enforced at decode; docs updated.

⸻

4) Quality gates (blockers unless stated otherwise)
	•	Ingestion: parse_success ≥ 0.98; provenance 100%; redaction pass for public outputs.
	•	Retrieval: grounding ≥ 0.80; hybrid recall@50 ≥ 0.90 on seeded queries.
	•	Reasoning: self-consistency ≥ 0.70; contradiction_rate ≤ 2%.
	•	Recommendations: GRADE badge; adversary+constitution pass; explicit assumptions & counterfactuals.
	•	Experts (if enabled): usability ≥ 0.75; WCAG AA subset pass; reactance risk ≤ 0.30 (warn 0.40, block 0.50); message-map completeness ≥ 0.85; council_score ≥ 0.75.
	•	Ops/SLOs: P95 E2E ≤ 180s (demo corpus); P99 workflow success ≥ 99%.
	•	Security: 0 leaked PII in sampled payloads; egress domains == allow-list; signed tool outputs.
	•	Offline: demo corpus completes end-to-end on CPU-only profile within target wall-time.

⸻

5) Concrete PR skeletons (generate diffs + files)

Important: Use existing repo structure and doc anchors (they exist in main). Keep optional OpenAI provider/client disabled in configs by default.  ￼

PR-A — Ingestion & Parsing (OCR + formats + clarify)
	•	New: packages/ingestion/ modules for parsers (Unstructured/Tika/docTR/Tesseract/Camelot/pdfplumber), provenance pack, confidence scoring.
	•	API: POST /ingestion/ingest, POST /ingestion/clarify (returns questions when confidence < 0.7).
	•	MCP: mcp-servers/research-mcp gets parse_document and ingest_blob tools (no egress).
	•	Tests: fixtures with PDFs, DOCX, images, tables; OCR accuracy smoke tests; provenance hashing tests.

PR-B — Retrieval++
	•	Add SPLADE/ColBERT indexes; BGE reranker; configs/retrieval/hybrid.yaml weights; expose /retrieval/* endpoints.
	•	Hybrid orchestrator returns dense/sparse/hybrid/reranker scores + grounding spans.
	•	Tests: recall@K improvements on seed corpus; latency profile.

PR-C — Reasoning++
	•	Insert Chain-of-Verification node + reflexive critique; require structured decoding for Claim, Assumption, Hypothesis, Experiment, Forecast (Pydantic v2).
	•	Failure policy: below thresholds → return research tasks and/or clarification questions (no recommendation).

PR-D — Orchestration
	•	Temporal workflows for research→ingest→index→retrieve→reason→recommend, with idempotency keys and retries; expose run IDs over API.

PR-E — Evals & Observability
	•	Wire Langfuse for LLM spans; OTEL traces; OpenLineage to Marquez; add RAGAS/groundedness CI job; dashboards JSON.

PR-F — Expert Council (discipline MCP)
	•	Expertise MCP (psychology/design/communication/brand/economics), doctrines & weights, council vote; API /experts/*; UI Expert Panel.

PR-G — UX/UI/UID & Onboarding
	•	Desktop tri-pane (Sources | Debate | Graph/Boards); Projects workspace; Onboarding Wizard (guided steps, hints, error recoveries); mobile approvals slice.
	•	Components: Argument Map, Evidence Badge (GRADE), Assumption Heat-map, Graph Explorer, Strategy Kanban, Experiment Console.
	•	Accessibility: WCAG 2.1 AA checks; readability bands surfaced.

PR-H — Offline/Edge profile
	•	Ollama/gguf models, local reranker; local object cache; demo seeds; “CPU-only mode” toggle in .env.

PR-I — Security/Compliance
	•	OPA/Rego egress allow-lists; SOPS/age secrets; audit logging; prompt-injection hardening; CI supply-chain scans (SBOM, Trivy/Grype).

⸻

6) Expected files & edits (non-exhaustive; tailor to what’s in repo)
	•	packages/api/routers/*.py (new endpoints), packages/orchestrator/graph/* (new nodes), packages/mcp-servers/* (tools), packages/evals/* (suites), packages/ui/* (new views).
	•	configs/*: retrieval, evals, experts, privacy, router policies.
	•	helm/templates/* & docker-compose.yml: add services and NetworkPolicies (deny egress).
	•	.github/workflows/*: add eval/security/sbom/helm lint jobs.
	•	docs/*: gap analysis, upgrade plan, dev quick-start, ops/runbook.
	•	tests/*: unit, integration, e2e (Playwright).

⸻

7) Developer workflow (DX)
	•	Support both make dev.up/down/logs and helm install flows; ensure scripts/setup.sh and seeds work end-to-end; keep low-spec path documented.
	•	Provide prompt files for Copilot Chat (optional) to orient to repo contracts; if tenants forbid Copilot, recommend Tabby (OSS).

⸻

8) Output format (strict)
	•	Produce two markdown files:
	•	docs/gap-analysis.md (full repo-aware gaps & fixes)
	•	docs/upgrade-plan.md (90-day sprints, DoD, risks)
	•	Then emit PR diffs (A→I) as fenced diff blocks per file with minimal viable code/config/tests to compile/run locally.
	•	Keep changes OSS-first and ensure OpenAI provider/client disabled by default in configs.
	•	When confidence < 0.7 for any inferred assumption, first write clarifying questions in docs/open-questions.md and add safe, reversible default.

⸻

9) Acceptance criteria (what “done” looks like)
	•	docker compose up (or make dev.up) boots full stack; seed runs; narrative query flows through ingest→index→retrieve→reason→debate→gates→recommend.
	•	Eval suite passes thresholds; failing gates trigger safe fallback (Not evidence-qualified + next steps).
	•	Offline profile completes demo on CPU-only.
	•	Dashboards (Grafana/Langfuse/Temporal/Marquez) show end-to-end traces; CI runs and gates are green.
	•	UI shows Projects, Onboarding Wizard, Expert Panel, and evidence-grade visuals.

⸻

Notes to Codex
	•	Prefer small, atomic PRs; minimise blast radius; keep configs explicit.
	•	Preserve tenant privacy in any optional provider wiring; redact/minimise egress.

⸻

Kickoff Checklist (execute now)
	1.	Enumerate current components, services, and configs from root docs and tree; note deltas (write to docs/gap-analysis.md).  ￼
	2.	Validate bring-up commands and service URLs; record any drift.  ￼
	3.	Draft PR-A through PR-I stubs (diffs + tests); wire CI gates; update docs and Makefile targets.
	4.	Run local smoke + eval jobs; tune thresholds to pass with sample corpus; document low-spec profile.

⸻

If you need additional repo clarifications, add them under docs/open-questions.md and proceed with reversible defaults until resolved.
