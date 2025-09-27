# SCRATCH.md Gap Analysis

| Area | SCRATCH.md deliverable | Implementation status | Evidence | Gap |
| --- | --- | --- | --- | --- |
| Phase 0 – Observability | Langfuse + OTEL wiring with privacy sanitisation | **Partially implemented** – `tracing_manager` supports Langfuse/OTEL and `create_app` wires FastAPI instrumentation | `packages/api/src/stratmaster_api/tracing.py`, `packages/api/src/stratmaster_api/app.py:214` | Privacy scrubber does not remove PII when Presidio unavailable; no Langfuse dashboards/config artefacts checked in | 
| Phase 0 – Security | Keycloak OIDC + Presidio guardrails | **Implemented** – Keycloak middleware + Presidio redactor in `PrivacyRedactionMiddleware` | `packages/api/src/stratmaster_api/security/keycloak_auth.py`, `.../middleware/security_middleware.py` | None | 
| Phase 1 – Model Gateway | LiteLLM config + adaptive bandit routing | **Partially implemented** – LiteLLM YAML present, bandit selector fetches arena/MTEB data when V2 flag on | `infra/gateway/litellm.yaml`, `packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py` | V2 flag defaults off so live data never used; no Langfuse cost telemetry hook | 
| Phase 2 – Hybrid Retrieval | Qdrant/OpenSearch hybrid search with RRF fusion | **Implemented** – Qdrant/OpenSearch clients with reciprocal-rank fusion & latency tracking | `packages/api/src/stratmaster_api/services/hybrid_retrieval.py:180-360` | — |
| Phase 2 – Reranking | Cross-encoder reranker via Infinity/TGI | **Implemented** – Router MCP rerank endpoint with configurable candidate cap & SLA metrics | `packages/api/src/stratmaster_api/services/hybrid_retrieval.py:271-317` | — |
| Phase 2 – RAG evaluation | RAGAS + TruLens metrics fed to Langfuse | **Implemented** – RAGAS evaluator invoked with graceful heuristics fallback when disabled | `packages/api/src/stratmaster_api/services/hybrid_retrieval.py:318-366` | — |
| Phase 3 – Collaboration | Yjs real-time co-editing with cursor presence | **Implemented** – YDoc-backed CRDT updates + base64 sync for subscribers | `packages/api/src/stratmaster_api/collaboration.py:337-520` | — |
| Phase 6 – Supply Chain | SBOM (Syft), Trivy scans, cosign signing | **Implemented** – Supply-chain workflow with Syft SBOM, Trivy fs scan, cosign sign/verify | `.github/workflows/syft-trivy-cosign.yml:1-69` | — |

**Key gaps to address now**: implement true hybrid retrieval + reranking + RAG evaluation loop, wire real Yjs CRDT collaboration server, and add supply-chain workflow as specified.
