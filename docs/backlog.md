# Backlog

This backlog turns the blueprint roadmap into actionable slices. IDs are referenced from backlog markers across the repo.

## Sprint 2 – Knowledge Fabric

### SP2-201 — Knowledge MCP connectors

- Status: ✅ **Complete** — Knowledge MCP bootstraps optional connectors, surfaces
  runtime availability in `/info`, and degrades gracefully when backends are
  absent or unhealthy.【285a30†L1-L105】【29aa2e†L417-L468】【8585dc†L19-L70】
- Issue stub: `issue/sp2-201-knowledge-mcp-connectors`
- PR slices:
  1. `pr/sp2-201a-config-health` — tighten environment config, add readiness/telemetry hooks.
  2. `pr/sp2-201b-qdrant-adapter` — implement Qdrant dense connector with integration tests (mocked client).
  3. `pr/sp2-201c-opensearch-nebula` — wire OpenSearch/NebulaGraph connectors with graceful fallbacks.
- Acceptance: Service auto-detects connectors, exposes capability flags in `/info`, and surfaces actionable errors without crashing.

### SP2-202 — Knowledge fabric storage & GraphRAG materialisation

- Status: ⏳ **Pending** — the `packages/knowledge` package only carries design
  notes and lacks the storage contract and GraphRAG implementation modules referenced
  in the plan.【05eb90†L1-L54】【10eb41†L1-L2】
- Issue stub: `issue/sp2-202-knowledge-fabric`
- PR slices:
  1. `pr/sp2-202a-tenant-layout` — define per-tenant storage contracts and schema registry.
  2. `pr/sp2-202b-graphrag-pipeline` — ingest demo corpus into graph store with provenance.
  3. `pr/sp2-202c-summary-endpoints` — expose graph/community summaries backed by stored artefacts.
- Acceptance: Graph resources serve persisted communities per tenant; provenance and storage layout documented.

### SP2-203 — Retrieval index toolchain (ColBERT/SPLADE + hybrid orchestrator)

- Status: ⏳ **Pending** — both retrieval subpackages are documentation-only;
  the ColBERT/SPLADE CLIs and tests described in the plan have not been implemented yet.【6c173d†L1-L2】【0bbba4†L1-L39】
- Issue stub: `issue/sp2-203-retrieval-indexing`
- PR slices:
  1. `pr/sp2-203a-colbert-cli` — CLI + docs for building/querying ColBERT indexes from seeds.
  2. `pr/sp2-203b-splade-cli` — SPLADE expansion + OpenSearch indexing workflows.
  3. `pr/sp2-203c-hybrid-tests` — regression tests for weighted hybrid retrieval/reranking.
- Acceptance: `make index.colbert` / `make index.splade` succeed locally; hybrid query reflects new indices with tests covering weight tuning.

### SP2-204 — BGE reranker package

- Status: ⏳ **Pending** — the reranker package still consists of README
  guidance without the Python module, CLI, or tests that the sprint calls for.【326cef†L1-L2】【061aad†L1-L41】
- Issue stub: `issue/sp2-204-bge-reranker`
- PR slices:
  1. `pr/sp2-204a-wrapper` — package cross-encoder inference utilities with device selection.
  2. `pr/sp2-204b-api` — expose CLI/service hooks and unit tests.
- Acceptance: Knowledge MCP rerank endpoint calls into package; configurable topK and device parameters documented.

### SP2-205 — Router per-task policies

- Status: ⏳ **Pending** — router MCP still routes everything through a single
  default provider and does not enforce per-task model policies or validation
  gates from `configs/router/models-policy.yaml`.【439a49†L15-L44】【3365df†L1-L70】
- Issue stub: `issue/sp2-205-router-policies`
- PR slices:
  1. `pr/sp2-205a-schema` — extend models-policy schema for reasoning/embedding/rerank routing.
  2. `pr/sp2-205b-evals` — add validation/tests ensuring tenants cannot bypass policy.
- Acceptance: Router selects providers per task type; policy violations are rejected with clear errors.

### SP2-210 — Research MCP CLI/bootstrap

- Status: ✅ **Complete** — `python -m research_mcp` now boots the FastAPI app via
  uvicorn and wires CLI flags/environment toggles for local usage as described in the sprint scope.【1cb3ee†L1-L6】【94db32†L1-L55】
- Issue stub: `issue/sp2-210-research-mcp-cli`
- PR slices:
  1. `pr/sp2-210a-uvicorn-cli` — make entrypoint start FastAPI app via uvicorn.
  2. `pr/sp2-210b-tool-registry` — expose CLI flags for allow-lists and network toggles.
- Acceptance: `python -m research_mcp` spins up the service matching README instructions.

## Sprint 3 – Agents & Assurance

### SP3-301 — LangGraph agent graph & shared state

- Issue stub: `issue/sp3-301-agent-graph`
- PR slices:
  1. `pr/sp3-301a-state-contracts` — define typed state + tool mediation layer.
  2. `pr/sp3-301b-node-impl` — implement Researcher/Synthesiser/Strategist nodes with MCP calls.
  3. `pr/sp3-301c-checkpointing` — add persistence/checkpoint hooks.
- Acceptance: Agent graph runs end-to-end with deterministic stubs; orchestrator fallback removed.

### SP3-302 — Debate, constitution, and eval gating

- Issue stub: `issue/sp3-302-debate-evals`
- PR slices:
  1. `pr/sp3-302a-adversary` — adversary + constitutional critic prompts wired into loop.
  2. `pr/sp3-302b-cove` — verification questions + response reconciliation.
  3. `pr/sp3-302c-eval-blocks` — enforce eval gates before emitting recommendations.
- Acceptance: Tests cover pass/fail paths; API returns structured failure modes when gates fail.

### SP3-303 — DSPy program compilation & telemetry

- Issue stub: `issue/sp3-303-dspy`
- PR slices:
  1. `pr/sp3-303a-baseline-program` — baseline ResearchPlanner module with save/load.
  2. `pr/sp3-303b-langfuse-hooks` — log compilation metadata to Langfuse.
  3. `pr/sp3-303c-ci-check` — add regression ensuring checkpoints stay in sync.
- Acceptance: DSPy artefacts stored under `packages/dsp/dspy_programs`; CI verifies reproducibility.

### SP3-304 — API Pydantic model suite

- Issue stub: `issue/sp3-304-api-models`
- PR slices:
  1. `pr/sp3-304a-models` — implement Source/Provenance/Claim/... Pydantic models.
  2. `pr/sp3-304b-json-schema` — generate `$id` versioned JSON Schemas.
  3. `pr/sp3-304c-contract-tests` — add unit tests verifying schemas against seeds and API responses.
- Acceptance: Models exported under `packages/api/src/stratmaster_api/models`; schemas served via API.

## Data & Seeds

### DATA-101 — Seed corpus & provenance

- Issue stub: `issue/data-101-demo-seeds`
- PR slices:
  1. `pr/data-101a-seed-script` — idempotent loader populating Qdrant/OpenSearch/MinIO for demo.
  2. `pr/data-101b-schema-docs` — document seed schema and provenance handling (SAST timestamps).
- Acceptance: `make seed` hydrates demo environment and records provenance fingerprints.

## Infrastructure & Ops

### INF-401 — SearxNG configuration

- Issue stub: `issue/inf-401-searxng`
- PR slices: engine allow-lists, rate limits, Playwright integration docs.
- Acceptance: Helm/Compose configs documented; policies enforced.

### INF-402 — Qdrant operations

- Issue stub: `issue/inf-402-qdrant`
- PR slices: collection templates, backup/restore notes, health dashboards.
- Acceptance: Tenancy-aware collection plan documented with sizing guidance.

### INF-403 — OpenSearch operations

- Issue stub: `issue/inf-403-opensearch`
- PR slices: analyzers/SPLADE mappings, ILM policies, monitoring hooks.
- Acceptance: Index templates + tuning guidance committed to infra README.

### INF-404 — NebulaGraph operations

- Issue stub: `issue/inf-404-nebulagraph`
- PR slices: space layout, schema DDL, sample queries.
- Acceptance: README explains tenant isolation and GraphRAG integration.

### INF-405 — MinIO buckets & policies

- Issue stub: `issue/inf-405-minio`
- PR slices: bucket layout, IAM policies, sample `mc` commands.
- Acceptance: Storage conventions documented and referenced by services.

### INF-406 — Langfuse deployment

- Issue stub: `issue/inf-406-langfuse`
- PR slices: Docker/Helm values, API key rotation, dashboard templates.
- Acceptance: Observability quickstart runnable locally.

### INF-407 — Temporal orchestration

- Issue stub: `issue/inf-407-temporal`
- PR slices: namespace/queue strategy, worker config, sample workflows.
- Acceptance: README includes commands to run demo workflow.

### INF-408 — vLLM/Ollama serving

- Issue stub: `issue/inf-408-vllm-ollama`
- PR slices: model list, guided JSON config, resource sizing matrix.
- Acceptance: Infra doc informs router defaults and scaling guidance.

### INF-409 — LiteLLM router shim

- Issue stub: `issue/inf-409-litellm`
- PR slices: endpoint exposure, per-tenant policy mapping, tracing hooks.
- Acceptance: README details how to enable OpenAI-compatible endpoint securely.

### INF-410 — Keycloak tenancy

- Issue stub: `issue/inf-410-keycloak`
- PR slices: realm/client bootstrap, dev credentials, Helm values integration.
- Acceptance: Identity story documented end-to-end.

### INF-411 — DuckDB storage integration

- Issue stub: `issue/inf-411-duckdb`
- PR slices: storage path layout, sample analytical queries, Compose notes.
- Acceptance: README doubles as quickstart for local analytics.

### INF-412 — Postgres operations

- Issue stub: `issue/inf-412-postgres`
- PR slices: schema management, migration strategy, credential handling.
- Acceptance: Database docs tie into API models and seeds.

### INF-414 — Ingress management

- Issue stub: `issue/inf-414-ingress`
- PR slices: example manifests, hostnames/TLS, cert-manager guidance.
- Acceptance: Ops doc ready for staging rollout.

### INF-415 — Sealed secrets / SOPS

- Issue stub: `issue/inf-415-sealed-secrets`
- PR slices: bootstrap flow, key rotation policy, SOPS+age workflow.
- Acceptance: Secret management runbook committed.

### INF-416 — Network policies

- Issue stub: `issue/inf-416-network-policies`
- PR slices: example policies per component, mapping to OPA, multi-tenant notes.
- Acceptance: README links policies with enforcement reality.

## Safety & Governance

### SEC-201 — Constitutional prompts

- Issue stub: `issue/sec-201-constitutions`
- PR slices: house rules authoring, alignment review, integration tests.
- Acceptance: Constitution set stored under `prompts/constitutions`, referenced by agents.

## Compression & Tooling

### COMP-501 — LLMLingua parameter tuning

- Issue stub: `issue/comp-501-llmlingua-config`
- PR slices: task-specific configs, eval harness integration, documentation.
- Acceptance: Compression config validated against eval metrics with guardrails documented.

### COMP-502 — Compression MCP server implementation

- Issue stub: `issue/comp-502-compression-mcp`
- PR slices: FastAPI server, LLMLingua integration, tests, CLI entrypoint.
- Acceptance: `/tools/compress` endpoint live with configurable policies.

## API & Contracts

### API-701 — API model coverage

- Issue stub: `issue/api-701-model-suite`
- PR slices: implement core Pydantic models, generate JSON Schemas, align docs/tests.
- Acceptance: API emits versioned schemas and tests guard data contracts.

## Ops & Compliance

### OPS-001 — License selection

- Issue stub: `issue/ops-001-license-selection`
- PR slices: collect legal/market requirements, decide licence, update repository metadata and headers.
- Acceptance: Chosen licence committed to `LICENSE`, README badges updated, contributor guidance clarified.
