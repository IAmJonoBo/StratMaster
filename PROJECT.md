# Open Brand Strategy AI — Engineering Blueprint (Frontier‑grade, prompt‑free)

This is the default, living blueprint I will use to design, scaffold, and govern the monorepo. It encodes engineering conventions, contracts, reliability targets, security posture, and Copilot‑oriented build steps. Oxford English; Africa/Johannesburg (SAST). Zero paid SaaS by default; optional adapters allowed.

---

## 1) Purpose and scope

Build a self‑hosted, evidence‑grounded Business & Brand Strategy platform that:

- Privately researches the web (SearxNG + headless crawling) with provenance and PII hygiene.
- Constructs a Knowledge Fabric (GraphRAG + hybrid retrieval using Qdrant + OpenSearch + NebulaGraph).
- Reasons via a multi‑agent debate with a Constitutional Critic and eval gates.
- Models CEPs, JTBD, DBAs, Experiments, Forecasts as first‑class objects.
- Ships a desktop tri‑pane UI and a mobile read‑only approvals slice.
- Uses MCP for all tool/resource access (no direct HTTP from LLM messages).

Success is defined by Acceptance Criteria in section 12.

---

## 2) Monorepo structure (authoritative)

```text
open-brand-strategy-ai/
  LICENSE
  README.md
  .editorconfig
  .gitignore
  Makefile
  docker-compose.yml
  helm/
    Chart.yaml
    values.yaml
    templates/
      deployments.yaml
      services.yaml
      ingress.yaml
      networkpolicies.yaml
      secrets.yaml
  ops/
    k8s/
      README.md
      network-policies/
      sealed-secrets/
      ingress/
    sops/
      README.md
      age-keys-template.md
    policies/
      data-egress.rego
      crawl-allowlist.rego
      tenant-quotas.rego
    threat-model/
      stride.md
      llm-prompt-injection.md
  infra/
    duckdb/
    keycloak/
    langfuse/
    litellm/
    minio/
    nebulagraph/
    opensearch/
    postgres/
    qdrant/
    searxng/
    temporal/
    vllm-or-ollama/
  packages/
    agents/
    api/
    compression/
      llmlingua/
    dataprocessing/
      arrow_duckdb/
      polars/
    dsp/
      dspy_programs/
    evals/
    ingestion/
    knowledge/
    mcp-servers/
      compression-mcp/
      evals-mcp/
      knowledge-mcp/
      research-mcp/
      router-mcp/
    orchestrator/
    providers/
      openai/
        README.md
        tool-schemas/
          decision.json
          evals.json
          graphrag.json
          research.json
          retrieval.json
        client/
          node/
          python/
    rerankers/
      bge/
    research/
    retrieval/
      colbert/
      splade/
    ui/
    verification/
      cove/
  prompts/
    agent-system-prompts/
    constitutions/
  configs/
    compression/llmlingua.yaml
    evals/thresholds.yaml
    privacy/redaction.yaml
    retrieval/colbert.yaml
    retrieval/hybrid.yaml
    retrieval/reranker.yaml
    retrieval/splade.yaml
    router/models-policy.yaml
    router/structured_decoding.yaml
  tests/
    e2e/
    integration/
    unit/
  seeds/
    demo-ceps-jtbd-dbas.json
    demo-corpus/
```

---

## 3) Reference architecture

- Agent graph (LangGraph): Researcher → Synthesiser → Strategist → Adversary → Constitutional Critic → Recommender.
- Retrieval stack upgrades: add late‑interaction ColBERT and learned sparse SPLADE alongside Qdrant/OpenSearch; cross‑encoder reranking with BGE v2.\*.
- Structured outputs end‑to‑end: vLLM guided decoding (JSON Schema/regex/grammar) so all agents emit Pydantic‑valid objects.
- Self‑improving programs: DSPy modules compile prompts/weights for the Researcher→Synthesiser→Strategist loop; artefacts tracked in Langfuse.
- Decision assurance: Chain‑of‑Verification (CoVe) stage before the Constitutional Critic; returns verified deltas or triggers more research.
- Tool mediation: All external calls via MCP servers (section 8). Agents never perform raw HTTP.
- Dataflow (E2E):
  1. Intake → OPA policy gate → research plan.
  2. SearxNG metasearch → Playwright crawl → Unstructured/Tika parse → provenance pack.
  3. IE → dense embeddings (Qdrant) + learned sparse terms (OpenSearch/SPLADE) + late‑interaction encodings (ColBERT) + relations (NebulaGraph).
  4. GraphRAG pipeline → communities (Leiden/Louvain) → summaries → narrative answers.
  5. CoVe self‑verification → adversarial debate + constitution → Evals (Ragas, FActScore, TruthfulQA, RAGTruth/LettuceDetect) → Langfuse traces/metrics.
  6. Decision layer: CEP/JTBD/DBA scoring; causal (DoWhy/EconML); forecasting (PyMC/Prophet) → recommendations.
  7. UX surfaces: Argument map, GRADE evidence, Assumption heat‑map, Graph explorer, Strategy Kanban, Experiment console.

---

## 4) Data contracts (Pydantic v2; `packages/api/models/`)

- Core: Source, Provenance, Claim, Assumption, Hypothesis, Experiment, Metric, Forecast, CEP, JTBD, DBA
- GraphArtifacts: { nodes, edges, communities, community_summaries, narrative_chunks }
- RetrievalRecord: { dense_score, sparse_score, hybrid_score, reranker_score, grounding_spans[], chunk_hash }

Conventions:

- RFC3339 timestamps with SAST offset (UTC+2) preserved; store in UTC with offset metadata.
- Official JSON Schema per model; versioned `$id` and semantic versioning.
- Include OpenLineage context fields where applicable (job, run, dataset facets).

---

## 5) Storage and retrieval

- Vector: Qdrant (multi‑vector, HNSW; optional PQ/IVF). Collections per tenant and corpus.
- Lexical/ANN: OpenSearch (BM25, SPLADE optional; k‑NN HNSW/Faiss).
- Graph: NebulaGraph for entities/relations/communities; separate space per tenant.
- Object store: MinIO for raw/cached artefacts and snapshots.

### Enhanced retrieval methods

- Late‑interaction (ColBERT/ColBERTer): passage encodings stored in Qdrant (per‑token vectors) with compact residuals; scoring via MaxSim; index build CLI in `packages/retrieval/colbert`.
- Learned sparse (SPLADE/LSR): document expansion indexed in OpenSearch; supports BM25+SPLADE hybrid and domain adaptation; training scripts in `packages/retrieval/splade`.
- Reranking: BGE v2.\* cross‑encoders for top‑K rerank; optional layerwise/lightweight variants for CPU.

Hybrid retrieval orchestrator contract:

Inputs: query_text, filters, tenant_id, k_dense, k_sparse, k_colbert, alpha_dense_sparse, beta_colbert, reranker_limit, method_flags{bm25, splade, dense, colbert}
Outputs: ranked docs with per‑method scores {dense, sparse, colbert, hybrid, reranker}, grounding_spans[], chunk_hash, provenance_id
Structured outputs: All responses conform to Pydantic models; vLLM guided_json enforces schema.
Failure policy: if recall@K or grounding < thresholds (see section 10), return research tasks rather than recommendations.

---

## 6) Research & ingestion

- Metasearch: SearxNG self‑hosted; per‑tenant engine configuration.
- Headless crawling: Playwright workers; robots.txt honouring; domain allow‑lists; per‑host concurrency and rate‑limits; content hashing; fetch provenance.
- Parsing: Unstructured/Tika; PDFs; docTR/Tesseract OCR; Camelot tables; HTML → Markdown/Text normalisation. Trafilatura for robust main‑content extraction; Arrow normalisation for columnar tables.
- Provenance pack: { source_url, fetch_time_sast, sha256, parser_version, crawl_policy_snapshot } + OpenLineage emit.
- High‑performance data processing: Arrow for in‑memory columnar format; DuckDB for in‑process analytics (CSV/Parquet/JSON); Polars for fast DataFrames; all ETL steps emit Arrow and persist Parquet snapshots.

---

## 7) Reasoning orchestration

- LangGraph agents with shared blackboard state and checkpointing per tool call.
- Adversary attacks assumptions; Constitutional Critic enforces house rules (Constitution files in `prompts/constitutions/`).
- Recommender outputs a decision brief: point estimate + 50% & 90% intervals; assumptions; counterfactuals; a Safer alternative; provenance and GRADE badge.
- Verification: Chain‑of‑Verification (CoVe) between Synthesiser and Strategist; plans verification questions, answers independently, and amends the draft before debate.
- Self‑improving programs (DSPy): compile modules for research planning, synthesis, and critique; maintain program checkpoints in packages/dsp/dspy_programs with evaluation records.

All agent tool calls return structured outputs enforced by vLLM guided decoding (JSON Schema via Outlines/xgrammar).

---

## 8) MCP servers (packages/mcp-servers)

- research-mcp: tools { metasearch(query,…), crawl(url/spec, …) }; resources { cached_page, provenance } (SearxNG/Playwright).
- knowledge-mcp: resources { vector.search, keyword.search, graph.query, graph.community_summaries }; tools { graphrag.run(spec), colbert.search(spec), splade.search(spec), rerank.bge(pairs, model) } (Qdrant/OpenSearch/NebulaGraph).
- evals-mcp: tools { evals.run(suite, thresholds) }; resources { eval_reports/latest }; emits OpenLineage.
- router-mcp: tools { complete, embed, rerank } with policy enforcement; logs to Langfuse; routes to vLLM/Ollama via a LiteLLM‑style shim.
- compression-mcp: tools { compress.prompt(text, target_tokens, mode) }
  Uses LLMLingua‑2; applied before egress or expensive chains.

Transport:

- Local: stdio. Services: SSE/WebSocket. Provide TS and Python client examples.

Safety:

- Agents can only access network/resources via MCP tools; schemas allow‑listed; results signed; isolation between tool outputs and prompts.

---

## 8A) OpenAI / GPT integration (optional, policy‑gated)

**Purpose.** Allow tenants to optionally use OpenAI models **as a routed provider** and allow **GPT-based clients** to use this system’s tools safely—without changing our zero‑cost defaults or privacy posture.

**Modes.**

1. **Provider mode (router):** The model router can call OpenAI endpoints for completion/embedding/rerank when `openai.enabled=true` for a tenant. Defaults remain local (vLLM/Ollama).
2. **Client mode (tools):** Expose our system as **OpenAI tool-calling functions** (Responses API style) so GPT can invoke research, retrieval, GraphRAG, evals, and decision modules through JSON‑schema tools.

**Security & privacy guardrails.**

- Off by default; per‑tenant toggle (`configs/router/models-policy.yaml` → `providers.openai.enabled: false`).
- **Data minimisation:** send only query text and minimal spans; never raw tenant documents unless explicitly allowed by policy and redaction rules.
- **PII & secrets:** apply redaction policy before egress; block tool calls that would transmit restricted fields.
- **Retention & training:** document that OpenAI **does not use API data to train by default**; tenants may additionally request **zero‑data‑retention** if eligible. Keys live in KMS; no keys in images.
- Structured outputs: when routing to OpenAI, require JSON schema (Responses API) mirroring our Pydantic models; reject free‑form text for critical paths.

**OpenAI tool definitions (Client mode).**

- `research.search_and_crawl` → runs metasearch + Playwright with provenance.
- `retrieval.hybrid_query` → hybrid (dense+sparse+graph) with reranker.
- `graphrag.community_summaries` → returns narrative/community summaries.
- `evals.run_suite` → runs RAG/grounding/evidence gates and returns scores.
- `decision.plan_experiment` → designs A/B or bandit with priors and MDE.

**Router (Provider mode).**

- Implement `infra/litellm/` to offer an OpenAI‑compatible endpoint and provider shims; enforce per‑tenant rate/cost limits and block lists.
- `packages/mcp-servers/router-mcp` gets a new provider `openai` with tool names `complete|embed|rerank` that call the router with the tenant’s policy.
- Enable guided_json/grammar on local vLLM; if provider lacks equivalent guarantees, wrap with schema validation and reject on parse failure.

**Config (example; add to `configs/router/models-policy.yaml`):**

```yaml
tenants:
  tenant-a:
    providers:
      local:
        default: true
        models:
          - mixtral-8x22b-instruct
          - qwen2.5-14b-instruct
      openai:
        enabled: true
        models:
          - gpt-large-reasoning
          - text-embedding-3-large
        egress:
          allow_domains:
            - api.openai.com
        privacy:
          send_raw_docs: false
          max_snippet_chars: 2000
        limits:
          max_tokens_per_min: 120000
          budget_usd_month: 500
```

**API additions (FastAPI).**

- `/providers/openai/tools` → returns tool JSON Schemas for OpenAI Responses API.
- `/providers/openai/proxy/*` → optional signed proxy path with policy enforcement (sanitise, redact, sign, log).

**UX toggle.**

- Tenant settings page: “Enable OpenAI provider” (with retention notice), budget caps, and scope checkboxes (“Allow embeddings”, “Allow completions”, “Allow rerank”).

**Acceptance tests.**

- Provider: route a small query to OpenAI and verify provenance, cost logging, and kill‑switch on budget breach.
- Client: run a sample OpenAI tool‑calling session using our `/tools` schema; verify only allowed fields egress; confirm recommendation blocked if evidence gates fail.

---

## 9) API (FastAPI; `packages/api`)

Endpoints (JWT via Keycloak; OpenAPI enabled):

- POST /research/plan
- POST /research/run
- POST /graph/summarise
- POST /debate/run
- POST /recommendations
- POST /retrieval/colbert/query
- POST /retrieval/splade/query
- /experiments/\*
- /forecasts/\*
- POST /evals/run

Cross‑cutting:

- Idempotency keys (header `Idempotency-Key`) with dedupe storage.
- Retry semantics documented (Temporal task queue names in response metadata).
- Tracing headers: W3C TraceContext propagated; Langfuse span IDs returned.

---

## 10) Evals & quality gates (configs/evals/thresholds.yaml)

- Ingestion: parse_success ≥ 0.98; checksum/provenance 100%; public outputs pass PII redaction.
- Retrieval: grounding ≥ 0.8; hybrid recall@50 ≥ 0.9 (seeded sets); ColBERT MRR@10 ≥ BM25+dense baseline; SPLADE nDCG@10 ≥ BM25 baseline.
- Reasoning: self_consistency ≥ 0.7; contradiction_rate ≤ 2%; CoVe_verified_fraction ≥ 0.8.
- Recommendations: GRADE badge present; provenance complete; Adversary and Constitutional Critic pass; FActScore ≥ 0.75; TruthfulQA ≥ 0.65 on internal suite.
- Online: human spot‑check ≥ 10% sessions; intervention rate downward MoM; hallucination flag rate (LettuceDetect over RAGTruth) ≤ 3%.
- Egress (OpenAI‑enabled tenants): zero PII leakage in sampled payloads; cost guard: monthly budget not exceeded; egress domains match allow‑list; tool outputs cryptographically signed before model consumption.

CI blocks merges on regression below thresholds.

---

## 11) Observability & lineage

- Tracing/metrics: OpenTelemetry SDK in every service; exported to Prometheus/Grafana; Langfuse for LLM spans/prompts/metrics.
- Provider metrics: per‑tenant OpenAI usage (tokens, cost, error codes), routed vs local share, and budget burn‑down; surfaced in Grafana + Langfuse dashboards.
- Lineage: OpenLineage emitters; Marquez UI quickstart.
- Minimal SLOs: P95 end‑to‑end research→recommendation ≤ 180s (demo corpus); P99 workflow success ≥ 99% under nominal load.
- Log taxonomy: structured JSON (level, ts, trace_id, span_id, tenant_id, user_id, workflow_id, component, event).
- Retrieval method diagnostics: per‑query breakdown (BM25, SPLADE, dense, ColBERT) with score deltas and win/loss vs control; surfaced in Grafana.
- Structured output conformance: schema‑validation pass rate; top schema errors.
- Compression efficiency: LLMLingua token‑reduction %, quality deltas (Ragas/FActScore) pre/post.

---

## 12) Acceptance criteria (verification)

- `docker-compose up` boots the stack and demo workspace:
  a) run a narrative query; b) explore graph communities; c) run debate+constitution; d) pass eval gates; e) produce a decision brief with GRADE, provenance, and 50% & 90% intervals plus a Safer alternative.
- Only MCP tools perform network access; no direct HTTP from LLM messages.
- Per‑tenant isolation: separate DBs/indices/buckets/secrets enforced by config and NetworkPolicies.
- Langfuse shows traces end‑to‑end; Grafana dashboards populated; Temporal UI shows durable runs with retries/idempotency.
- CI runs unit+integration+eval suites and fails on threshold regressions.

---

## 13) Security, privacy, compliance

- Prompt‑injection: allow‑list schemas; signed tool results; isolation of tool results; content sanitisation (strip/style/quote); strict cross‑domain allow‑lists.
- Secrets: SOPS+age; no secrets in images; least‑privilege K8s service accounts.
- Policies: OPA/Rego deny‑by‑default egress; crawl allow‑lists; per‑tenant quotas.
- Compliance defaults: POPIA/GDPR‑friendly; clear data retention policies; audit: immutable Langfuse traces.
- OpenAI‑specific notes (when enabled):
  - Training: API content is **not used for training by default**; document this for tenants and keep the toggle off unless approved.
  - Retention: tenants may request **zero data retention** for API content where available; otherwise default platform retention applies.
  - Egress policy: only `api.openai.com` allowed; deny all others. All payloads are redacted/minimised per policy before egress.

---

## 14) DX & Ops

- Local dev: `docker-compose.yml` includes Postgres, Qdrant, OpenSearch, NebulaGraph, MinIO, SearxNG, Langfuse, Temporal, Keycloak, vLLM/Ollama, DuckDB. CLI utilities to build ColBERT/SPLADE indices; sample notebooks for Arrow/DuckDB/Polars pipelines.
- K8s: single Helm chart; values for single‑tenant vs multi‑tenant; strict NetworkPolicies; per‑tenant storage classes.
- Testing: unit (pytest/vitest), integration (spun services), e2e (Playwright).
- Quality: pre‑commit (ruff/black/mypy; eslint/biome); bandit, semgrep; checkov for IaC.
- Timezone & locale: SAST examples in docs; Oxford English copy.

---

## 15) Conventions (code, repos, review)

- Python: 3.13+; ruff/black/mypy; typing required; pydantic v2 models; exceptions mapped to Problem Details JSON.
- TypeScript/React: strict TypeScript; ESLint/Biome; Tailwind; accessibility (WCAG 2.1 AA); keyboard shortcuts documented.
- Commits: Conventional Commits; signed commits recommended; small, reviewable PRs; checklist below.
- Branching: trunk‑based with short‑lived feature branches; CI on PR; required status checks.
- Docs: each package has a README with usage and tracing pointers.

PR checklist (reviewers/Gate):

- [ ] Unit tests for changed surfaces
- [ ] Integration/e2e updated if behaviour changed
- [ ] Telemetry: spans/metrics added and linked to trace IDs
- [ ] Security: inputs validated, outputs sanitised, PII policy respected
- [ ] Config defaults safe; multi‑tenant isolation preserved
- [ ] Docs/READMEs updated; examples reflect SAST

---

## 16) Config stubs

- `configs/router/models-policy.yaml`: tenants → allowed models, max context, temperature caps, routing rules by task/type/cost.
- `configs/retrieval/hybrid.yaml`: dense model+k; sparse method+k; alpha weights; reranker limits.
- `configs/evals/thresholds.yaml`: ingestion/retrieval/reasoning/recommendation/online thresholds and kill‑switches.
- `configs/privacy/redaction.yaml`: PII patterns (Presidio‑style), redact/annotate policies.
- `configs/retrieval/colbert.yaml`: encoder, dim, nprobe, maxsim_threshold, max_seq_len, index_shards.
- `configs/retrieval/splade.yaml`: model, expansion_topk, prune_threshold, index_analyzers.
- `configs/retrieval/reranker.yaml`: model_name, topk_in, topk_out, device.
- `configs/router/structured_decoding.yaml`: enabled: true; backend: outlines|xgrammar; strict_json: true.
- `configs/compression/llmlingua.yaml`: enabled, target_token_ratio, safety_keywords, domains_exempt.

---

## 17) UI feature slices (Next.js + Tailwind)

- Tri‑pane layout (Sources | Debate | Graph/Boards); resizable panes; keyboard navigation; URL state.
- Views: Argument Map; Evidence Badge (GRADE + provenance count); Assumption Heat‑map; Graph Explorer; Strategy Kanban; Experiment Console.
- Mobile: read‑only briefs, approvals, comments, notifications; offline‑friendly caches for briefs.
- Reliability Meter: shows FActScore/grounding/CoVe pass; links to evidence spans.
- Research Trace: compact timeline of metasearch→crawl→parse→retrieval→debate with per‑stage metrics.

---

## 18) Reliability & safety policies

- Temporal: retries with exponential backoff; idempotency keys; dead‑letter queues; saga compensation for multi‑step jobs.
- Circuit breakers: MCP tool failures trip per‑tenant breakers; recovery via jittered backoff.
- Kill‑switch: when evals below thresholds or grounding fails → return research tasks instead of recommendations.
- Structured decoding required for all machine‑readable outputs (guided_json/grammar). On violation, auto‑retry with stricter decoding; if still failing, return “Not evidence‑qualified” with research tasks.
- Prompt compression safety: never compress provenance or numeric results; compression runs only on narrative prompts and is logged.

---

## 19) Supply‑chain & build integrity

- Pin dependencies; use lockfiles; reproducible builds; minimal base images; Trivy/Grype scans in CI.
- SBOMs (Syft) published for images; provenance attestations (SLSA‑like) for releases.
- Container user non‑root; read‑only file systems where viable.

---

## 20) Commands to expose in README/Makefile

- make dev.up / make dev.down / make seed
- helm install brandai ./helm -f helm/values.yaml
- temporal server start-dev (dev only) + sample workflow run
- docker compose -f docker-compose.yml up langfuse
- OpenLineage/Marquez quickstart
- export OPENAI_API_KEY=... && make provider.openai.test # runs a minimal routed completion + embedding and logs cost
- curl -s "<http://127.0.0.1:8080/providers/openai/tools>" # returns OpenAI tool JSON Schemas for Client mode
- make index.colbert # train/build ColBERT index on demo corpus
- make index.splade # train/build SPLADE expansion + OpenSearch index
- make eval.bench # run Ragas + FActScore + TruthfulQA + LettuceDetect on seeds
- make etl.arrow # run Arrow/DuckDB/Polars demo pipeline
- python scripts/smoke_api.py # quick in‑process smoke for API /healthz and /docs

---

## 21) Roadmap checkpoints (development milestones)

- Milestone 1: Scaffold repo, compose stack, Helm skeleton, configs stubs
- Milestone 2: API contracts + research-mcp + crawler + provenance
- Milestone 3: Knowledge fabric (Qdrant/OpenSearch/NebulaGraph) + hybrid orchestrator + ColBERT/SPLADE indexing + BGE reranking
- Milestone 4: Agents (LangGraph) + debate/constitution + eval gates wiring + CoVe verification + DSPy compilation
- Milestone 5: UI tri‑pane shells + observability dashboards + seeds/evals
- Milestone 6: Structured decoding everywhere; LLMLingua compression; retrieval diagnostics dashboards; FActScore/TruthfulQA suites.

---

## 22) Glossary

- CEPs: Customer Event Paths; JTBD: Jobs To Be Done; DBAs: Decisions, Bets, Assumptions
- GraphRAG: graph‑structured retrieval‑augmented generation
- GRADE: evidence quality rating for recommendations

---

This blueprint is the single source of truth for scaffolding and governance. Keep it updated as the system evolves; treat changes here as architectural decisions (ADC/ADR).

---

## 23) Implementation details: schemas, tool specs, tests

**A. OpenAI tool JSON Schemas (Client mode; served at `/providers/openai/tools`).**

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "research_search_and_crawl",
        "description": "Privacy-preserving metasearch + Playwright crawl with provenance and licence notes.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": { "type": "string" },
            "max_pages": { "type": "integer", "minimum": 1, "maximum": 5 },
            "respect_robots": { "type": "boolean", "default": true },
            "allow_domains": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["query"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "retrieval_hybrid_query",
        "description": "Hybrid retrieval over dense, sparse, and graph with reranker and grounding spans.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": { "type": "string" },
            "k": {
              "type": "integer",
              "minimum": 1,
              "maximum": 50,
              "default": 20
            },
            "alpha": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "default": 0.5
            },
            "filters": { "type": "object" }
          },
          "required": ["query"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "graphrag_community_summaries",
        "description": "Return community summaries and narrative synopses from the knowledge graph.",
        "parameters": {
          "type": "object",
          "properties": {
            "seed_entities": { "type": "array", "items": { "type": "string" } },
            "algo": {
              "type": "string",
              "enum": ["leiden", "louvain"],
              "default": "leiden"
            }
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "evals_run_suite",
        "description": "Run retrieval/grounding/debate evals and return scores and threshold verdicts.",
        "parameters": {
          "type": "object",
          "properties": {
            "suite": {
              "type": "string",
              "enum": ["rag", "reasoning", "debate"]
            }
          },
          "required": ["suite"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "decision_plan_experiment",
        "description": "Design an experiment (A/B or Thompson bandit) with priors and MDE calculation.",
        "parameters": {
          "type": "object",
          "properties": {
            "hypothesis": { "type": "string" },
            "metric": { "type": "string" },
            "mde": { "type": "number" },
            "unit": {
              "type": "string",
              "enum": ["user", "account", "session"]
            },
            "bandit": { "type": "boolean", "default": false }
          },
          "required": ["hypothesis", "metric"]
        }
      }
    }
  ]
}
```

**B. Provider policy (YAML) — reference snippet.**

```yaml
providers:
  openai:
    enabled: false
    routing:
      reasoning: gpt-large-reasoning
      embedding: text-embedding-3-large
      rerank: gpt-mini-reranker
    privacy:
      send_raw_docs: false
      redact_pii: true
      max_snippet_chars: 2000
    limits:
      tpm: 120000
      rpm: 300
      budget_usd_month: 500
    egress:
      allow_domains: [api.openai.com]
```

**C. Tests (abridged).**

- **Contract tests:** `/providers/openai/tools` returns valid JSON Schema; round‑trip with OpenAI Responses API mock passes.
- **Redaction tests:** ensure PII masks are applied before egress; sampled payloads contain no restricted tokens.
- **Budget tests:** simulated heavy load triggers budget kill‑switch; recommendations degrade to “Not evidence‑qualified” with instructions.
- **Provenance tests:** responses include signed provenance IDs; Langfuse spans link to egress events.

### D. Structured decoding config (router)

```yaml
structured_outputs:
  enabled: true
  backend: outlines # or xgrammar
  strict_json: true
  error_policy: retry_then_fail
  max_retries: 2
```

### E. CoVe verification flow (pseudo‑sequence)

1. Synthesiser drafts answer (with evidence spans).
2. CoVe module plans verification questions for each claim/step.
3. CoVe answers each question independently (using retrieval/tools as needed).
4. Synthesiser revises draft using verified deltas; passes to Strategist or triggers more research if failed.

### F. DSPy program stub

```python
import dspy

class ResearchPlanner(dspy.Module):
    def __init__(self, ...):
        # configure module, load weights, etc.
        ...
    def forward(self, query):
        # plan research tasks, adapt prompts, etc.
        ...

# Compile and persist artefacts
planner = ResearchPlanner(...)
planner.save("packages/dsp/dspy_programs/research_planner_v1.pt")
```
