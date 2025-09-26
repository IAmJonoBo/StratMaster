StratMaster Frontier Upgrade Plan

Copilot/“Condex” implementation brief with quality gates, deliverables, and OSS-first tech

⸻

Executive summary (what we’re doing and why)

We’ll harden StratMaster’s research→reasoning→decision pipeline with (1) an OSS-first model gateway and adaptive model routing, (2) hybrid retrieval with first-class reranking, (3) debate/strategy frameworks that are explicit and auditable, (4) built-in evaluation + observability, and (5) enterprise-grade security and supply-chain controls. All changes are incremental, testable, and reversible; every deliverable ships with quality gates and dashboards.

Key enablers: LiteLLM proxy + vLLM/TGI/Together AI for models, Langfuse + OpenTelemetry for tracing/evals, Qdrant/OpenSearch hybrid search with RRF and cross-encoder rerankers, RAGAS/TruLens for retrieval QA, Keycloak OIDC, Yjs for realtime collab, DoWhy/EconML for causal checks, and SLSA+cosign+SBOM for supply chain.  ￼

⸻

Auto-Expert setup (how we’ll work)
	•	Personas: Platform Architect (gateway, infra, SRE), IR/RAG Researcher (retrieval, rerank, evals), Causality Scientist (DoWhy/EconML), Security Engineer (OIDC/OWASP/SLSA), UX/Realtime Engineer (Yjs/HITL).
	•	Pre-registered analysis plan: baseline metrics → introduce one subsystem at a time → A/B with holdouts → ship behind flags → promote only on green gates.
	•	Evidence-gated: each strong change must show ≥2 independent sources (≥1 primary doc/spec) + harms review + counterfactual (“what if we didn’t add it?”) + uncertainty notes.

⸻

Phase 0 — Foundations (week 0–1)

0.1 Observability & eval plumbing (must-have before changes)
	•	Langfuse tracing+experiments (latency, cost, outcome labels). Add request/response anonymisation hooks.  ￼
	•	OpenTelemetry for FastAPI (auto-instrument) → OTLP → Grafana/Tempo/Prometheus. Gate on traces>95% sampled, RED metrics dashboards.  ￼
Deliverables: Langfuse project with ingestion keys; opentelemetry-instrument startup; Grafana dashboards; runbooks.
Quality gates: traces span % ≥95; p50/p95 per endpoint visible; error budget SLOs defined.

0.2 Security baselines
	•	Keycloak OIDC integration (Auth Code w/ PKCE), map roles→RBAC.  ￼
	•	PII guard via Microsoft Presidio (text) in ingress/egress filters for logging/eval payloads.  ￼
Deliverables: OIDC config, token verification middleware, Presidio service + redaction policy.
Quality gates: all public endpoints 401/403 on invalid scopes; redaction coverage tests.

⸻

Phase 1 — Model gateway & adaptive routing (week 1–2)

1.1 Open model gateway
	•	Stand up LiteLLM Proxy for one-line, provider-agnostic routing; enable model-per-task config. Wire Together AI (broad hosted models) and HF TGI/vLLM (self-hosted, OpenAI-compatible). Use cost/latency/quality tags.  ￼
Deliverables: litellm config (providers, rate limits, fallbacks), vLLM/TGI helm releases.
Quality gates: gateway p95 < 120 ms overhead; fail-open fallbacks verified; per-model cost telemetry in Langfuse.

1.2 Model recommendation engine
	•	Online bandit (UCB/TS) over candidate models per task-type (drafting, reasoning, tool-use). Arm features: prompt length, context size, tool calls, GPU availability; reward = labelled outcome (HITL accept), speed, cost (multi-objective scalar).
	•	Offline benchmarking refresh nightly with held-out tasks; anchor to public leaderboards (LMSYS arena for relative strength) & domain evals.  ￼
Quality gates: ≥10% cost-adjusted utility uplift vs static baseline across two weeks; no regression on p95 latency.

⸻

Phase 2 — Retrieval that wins (week 2–4)

2.1 Hybrid retrieval
	•	Keep Qdrant, add sparse vectors + dense in same collection; do hybrid scoring and/or upstream OpenSearch BM25 + RRF fusion.  ￼
	•	Add SPLADE or BGE-M3 sparse generation (fast CPU path) for sparse side when OpenSearch isn’t available. Evaluate on BEIR sets; report nDCG@10/MRR@10 deltas.  ￼
Deliverables: Qdrant hybrid schema; OpenSearch hybrid pipeline with normalization/RRF; batch indexer.
Quality gates: +≥20% nDCG@10 vs dense-only on 3 BEIR datasets; recall@50 ≥ baseline.

2.2 First-class reranking
	•	Serve cross-encoder rerankers (e.g., mxbai-rerank-large-v2 or bge-reranker-v2) via Infinity/TGI; wire to top-k from hybrid retriever.  ￼
Quality gates: +≥10 points nDCG@10 on BEIR passages after rerank; p95 rerank latency < 450 ms@k=100 on A100 or <800 ms@CPU.

2.3 RAG evaluation loop
	•	Add RAGAS and TruLens for answer faithfulness, context precision/recall; feed metrics into Langfuse. Ship regression suite with golden Q/A+contexts.  ￼
Quality gates: Faithfulness ≥0.75; context precision ≥0.6 on internal set; CI gate blocks on −5% drift.

⸻

Phase 3 — Debating & strategising, upgraded (week 3–5)

3.1 Methodology refresh
	•	Make debates explicit with Toulmin schema (claim/grounds/warrant/backing/qualifier/rebuttal) + argument maps; serialise to JSON for audit/UI overlays.  ￼
	•	Keep “self-play” but prioritise retrieval-checked, warrant-first reasoning; reroute to domain agents when confidence < threshold.

3.2 Causality & forecasting guardrails
	•	For strategy recommendations affecting KPIs, require a causal check using DoWhy/EconML (graph→identify→estimate→refute). Add synthetic control for pre/post policy changes when RCTs absent.  ￼
	•	Report Brier scores for probabilistic forecasts and use conservative extremising only when justified.  ￼
Quality gates: any “High-impact” recommendation must include causal DAG screenshot + identification result + refutation test passing.

3.3 HITL rubric & collaboration
	•	Standardise human review rubric (evidence adequacy, warrant strength, risk flags).
	•	Add real-time co-editing in briefs using Yjs + y-websocket; cursor presence and conflict-free merges.  ￼
Deliverables: JSON schemas for arguments; causal notebook templates; Yjs provider and UI affordances.
Quality gates: ≥90% of accepted outputs include structured argument frames; collab latency <150 ms LAN, <400 ms WAN.

⸻

Phase 4 — Exports & enterprise (week 4–5)
	•	Finish backend exports: Notion (create page/append blocks), Trello (cards), Jira (issues). Include dry-run previews and audit trails.  ￼
Quality gates: idempotency, retries, rate-limit backoff; integration tests with sandboxes.

⸻

Phase 5 — Performance & reliability (parallel from week 2)
	•	k6 API load tests in CI (smoke, stress, soak); Locust optional for Pythonic scenarios. SLOs: p50/p95, error rate, saturation.  ￼
	•	GPU serving: measure vLLM throughput tokens/s and queueing; ensure OpenAI-compatibility across stacks.  ￼
Quality gates: gateway + retriever p95 under agreed budgets; no head-of-line blocking at >P75 load.

⸻

Phase 6 — Supply chain & platform hardening
	•	SBOM with Syft; scan with Trivy; sign images with cosign; aim SLSA L3 provenance in CI.  ￼
	•	Apply OWASP LLM Top-10 controls (prompt injection, data leakage, insecure plugins): red-team tests in CI.  ￼
Quality gates: 0 critical CVEs at release; signed artifacts enforced at admission; red-team suite green.

⸻

Work packages (assignable to Copilot/“Condex”)
	1.	Gateway & routing

	•	Files: infra/gateway/litellm.yaml, apps/api/services/model_router.py (UCB/TS), infra/helm/vllm/values.yaml, infra/helm/tgi/values.yaml.
	•	Tests: unit (routing maths), integration (provider fallback), smoke (OpenAI-compat).
	•	Dashboards: model mix, reward, cost.

	2.	Retrieval & rerank

	•	Files: retrieval/hybrid.py, retrieval/indexer.py, retrieval/rerank.py.
	•	Infra: OpenSearch hybrid pipeline with RRF; Qdrant dual-vector schema.  ￼
	•	Tests: BEIR harness (nDCG/MRR); latency budgets.

	3.	Debate & argumentation

	•	Files: debate/toulmin.py, debate/schemas.py, ui/argument_map.tsx.
	•	Tests: schema validation; warrant-presence rules.

	4.	Causal & forecast checks

	•	Files: analysis/causal/dag.py, analysis/causal/estimate.py; notebooks for DoWhy/EconML pipelines.  ￼
	•	Tests: refutation must pass on seeded examples; CI fails on violations.

	5.	RAG evaluation

	•	Files: eval/ragas_suite.py, eval/trulens_suite.py, datasets in eval/data/.  ￼
	•	CI: regression budget ±5%.

	6.	Observability & HITL

	•	Files: observability/otel.py, observability/dashboards/, ui/collab/yjs-provider.ts.  ￼

	7.	Exports

	•	Files: integrations/notion.py, trello.py, jira.py; end-to-end mocks.  ￼

	8.	Security & supply chain

	•	Files: security/oidc.py, sec/owasp_llm_checks.py, .github/workflows/syft-trivy-cosign.yml.  ￼

⸻

Quality gates (go/no-go)
	•	Routing: ≥10% cost-adjusted utility gain vs fixed model; fallbacks verified.
	•	Retrieval: +≥20% nDCG@10 hybrid vs dense-only (BEIR), +≥10 with rerank.  ￼
	•	RAG: RAGAS faithfulness ≥0.75, precision ≥0.6; no hallucination regressions.  ￼
	•	Performance: p95 API under budgets from k6 soak; no tail amplification in router.  ￼
	•	Security: 0 critical CVE; signed artifacts; OWASP LLM checks pass; OIDC tokens enforced.  ￼

⸻

Copy-ready snippets (drop into the repo)

LiteLLM proxy (excerpt)

# infra/gateway/litellm.yaml
model_list:
  - model_name: together/llama-3.1-70b-instruct
    litellm_params: { model: together_ai/llama-3.1-70b-instruct, api_key: ${TOGETHER_API_KEY} }
  - model_name: vllm/gemma-2-27b
    litellm_params: { model: openai/v1, api_base: http://vllm:8000/v1, api_key: dummy }
  - model_name: tgi/llama-3.1-8b
    litellm_params: { model: hf/tgi, api_base: http://tgi:8080, api_key: dummy }
router:
  strategy: ucb1
  objectives: [accept_label, -latency_ms, -cost_usd]

(Refs: LiteLLM proxy, vLLM OpenAI-compat, TGI.  ￼)

OpenSearch hybrid with RRF (concept)

{
  "request_processors": [
    { "neural_query_enricher" : { "query_text" : "{{q}}" } },
    { "normalization-processor": { "technique": "minmax" } }
  ],
  "phase_results_processors": [
    { "rrf": { "rank_window_size": 100, "rank_constant": 60 } }
  ]
}

(OpenSearch hybrid + RRF.  ￼)

Qdrant dual-vector schema (concept)
	•	Dense: vector: { size: 1024, distance: "Cosine" }
	•	Sparse: sparse_vectors: { bm25: { index: "enabled" } }
(Hybrid in Qdrant.  ￼)

k6 CI smoke

import http from 'k6/http'; import { check, sleep } from 'k6';
export const options = { vus: 10, duration: '1m' };
export default function () {
  const r = http.post(`${__ENV.API}/debate/learning/predict`, JSON.stringify({text:"test"}), { headers: {'Content-Type':'application/json'}});
  check(r, { 'status 200': (res) => res.status === 200 });
  sleep(1);
}

(k6 API testing.  ￼)

OTel auto-instrument run

opentelemetry-instrument uvicorn app.main:app --host 0.0.0.0 --port 8000

(FastAPI instrumentation.  ￼)

⸻

Risks, counterfactuals, and safer fallbacks
	•	Risk: Hybrid search adds infra complexity. Counterfactual: keep dense-only; expect lower recall on jargon. Mitigation: feature flags + per-collection toggles; begin with rerank-only.  ￼
	•	Risk: Online bandit misroutes early. Mitigation: start with offline eval priors; cap exploration; HITL veto.
	•	Risk: Rerank latency spikes. Mitigation: serve x-small/base rerankers on CPU, large on GPU; fallback thresholds.  ￼

⸻

Deliverables checklist (what you can expect to land)
	•	Code: gateway, router, hybrid retriever, reranker service, debate schemas, causal notebooks, export backends.
	•	Tests: BEIR harness, RAGAS suite, OIDC auth tests, k6 load scripts, OWASP-LLM red-team set.  ￼
	•	Dashboards: Langfuse dashboards, Grafana RED/Saturation, evaluation trendlines.
	•	Docs: runbooks, architecture diagrams, SLOs, risk register.
	•	Compliance: SBOMs, signed images, SLSA provenance, Trivy reports.  ￼

⸻

Evidence-gated protocol (for each major change)
	•	Data: Langfuse traces/evals, BEIR/MTEB results, k6 outputs.  ￼
	•	Methods: A/B or shadow, RRF hybrid, cross-encoder rerank, causal refutation where applicable.  ￼
	•	Key results: nDCG/MRR uplift, faithfulness/precision, latency/cost deltas.
	•	Uncertainty: domain drift, dataset bias, cost volatility.
	•	Safer alternative: configuration flag to revert to previous stack.

⸻

Provenance block (top sources)
	•	Model gateway & serving: LiteLLM proxy; vLLM OpenAI-compat; HF TGI; Together AI API.  ￼
	•	Observability & evals: Langfuse docs; OpenTelemetry FastAPI; RAGAS; TruLens.  ￼
	•	Retrieval: Qdrant hybrid/sparse; OpenSearch hybrid + RRF; BEIR; MTEB.  ￼
	•	Reranking: mxbai-rerank-v2; bge-reranker-v2.  ￼
	•	Debate frameworks: Toulmin; argument mapping.  ￼
	•	Causality & forecasting: DoWhy/EconML; synthetic control; Brier & extremising.  ￼
	•	Security & supply chain: Keycloak OIDC; OWASP LLM Top-10; Syft; Trivy; cosign; SLSA.  ￼

⸻

Next actions (sequenced)
	1.	Ship Phase-0 observability + OIDC + redaction (small PRs).
	2.	Deploy LiteLLM + vLLM/TGI + Together AI; flip router behind flag.
	3.	Introduce hybrid retrieval and reranking; gate on BEIR uplift.
	4.	Land RAG eval CI + k6 soak; set SLOs.
	5.	Switch debates to Toulmin JSON; show argument map UI.
	6.	Wire causal checks for “High-impact” strategies.
	7.	Finish Notion/Trello/Jira backends; publish marketplace guides.
	8.	Enforce SBOM + Trivy + cosign + SLSA in CI.

This plan is ready for Copilot to scaffold code and for Condex to run migrations, tests, and infra rollouts with clear pass/fail gates.
