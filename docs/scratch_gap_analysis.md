# SCRATCH.md Gap Analysis

| Area | SCRATCH.md deliverable | Implementation status | Evidence | Gap |
| --- | --- | --- | --- | --- |
| Phase 0 – Observability | Langfuse + OTEL wiring with privacy sanitisation | **Implemented** – Langfuse/OTEL configured with exported dashboards + runbooks for RAG and routing telemetry | `packages/api/src/stratmaster_api/tracing.py`, `observability/langfuse/dashboards/*.json`, `observability/langfuse/runbooks/*.md`, `docs/runbooks/langfuse.md` | None |
| Phase 0 – Security | Keycloak OIDC + Presidio guardrails | **Implemented** – Keycloak middleware + Presidio redactor in `PrivacyRedactionMiddleware` | `packages/api/src/stratmaster_api/security/keycloak_auth.py`, `.../middleware/security_middleware.py` | None | 
| Phase 1 – Model Gateway | LiteLLM config + adaptive bandit routing | **Implemented** – V2 enabled by default and routing outcomes stream into Langfuse telemetry | `infra/gateway/litellm.yaml`, `packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py`, `packages/mcp-servers/router-mcp/src/router_mcp/service.py:100` | — |
| Phase 2 – Hybrid Retrieval | Qdrant/OpenSearch hybrid search with RRF fusion | **Implemented** – Qdrant/OpenSearch clients with reciprocal-rank fusion & latency tracking | `packages/api/src/stratmaster_api/services/hybrid_retrieval.py:180-360` | — |
| Phase 2 – Reranking | Cross-encoder reranker via Infinity/TGI | **Implemented** – Router MCP rerank endpoint with configurable candidate cap & SLA metrics | `packages/api/src/stratmaster_api/services/hybrid_retrieval.py:271-317` | — |
| Phase 2 – RAG evaluation | RAGAS + TruLens metrics fed to Langfuse | **Implemented** – RAGAS evaluator invoked with TruLens summary + heuristic fallback and golden dataset | `packages/evals/src/stratmaster_evals/evaluator.py`, `packages/evals/src/stratmaster_evals/trulens.py`, `data/evals/golden_rag_samples.json` | — |
| Phase 3 – Collaboration | Yjs real-time co-editing with cursor presence | **Implemented** – YDoc-backed CRDT updates + base64 sync for subscribers | `packages/api/src/stratmaster_api/collaboration.py:337-520` | — |
| Phase 6 – Supply Chain | SBOM (Syft), Trivy scans, cosign signing | **Implemented** – Supply-chain workflow with Syft SBOM, Trivy fs scan, cosign sign/verify | `.github/workflows/syft-trivy-cosign.yml:1-69` | — |

**Key gaps to address now**: continue onboarding real LMSYS/MTEB credentials for automated refreshes and extend the accessibility regression gates noted in `GAP_ANALYSIS.md`.
