# knowledge-mcp

Knowledge MCP server exposing retrieval and graph capabilities for agents.

## Capabilities

- `POST /tools/hybrid_query` — dense+sparse hybrid results with configurable weights
- `POST /tools/colbert_search` — ColBERT-style late interaction stub
- `POST /tools/splade_search` — SPLADE sparse retrieval stub
- `POST /tools/rerank_bge` — BGE reranker simulation
- `GET /resources/graph/community_summaries` — community summaries with representative nodes
- Health & metadata: `GET /healthz`, `GET /info`

Configuration is driven by environment variables:

- `KNOWLEDGE_MCP_VECTOR_ENABLE` (default `0`) – when `1` uses Qdrant available at
  `KNOWLEDGE_MCP_VECTOR_HOST`/`KNOWLEDGE_MCP_VECTOR_COLLECTION`
- `KNOWLEDGE_MCP_VECTOR_PROBE_ENABLE` (default `0`) – when `1` issues a sample search using
  `KNOWLEDGE_MCP_VECTOR_PROBE_QUERY`/`KNOWLEDGE_MCP_VECTOR_PROBE_TOP_K` to gate availability
- `KNOWLEDGE_MCP_KEYWORD_ENABLE` (default `0`) – when `1` uses OpenSearch
  (`KNOWLEDGE_MCP_KEYWORD_HOST`/`KNOWLEDGE_MCP_KEYWORD_INDEX`)
- `KNOWLEDGE_MCP_KEYWORD_PROBE_ENABLE` and related `*_PROBE_QUERY`/`*_PROBE_TOP_K` mirror the vector
  behaviour for OpenSearch
- `KNOWLEDGE_MCP_GRAPH_ENABLE` (default `0`) – when `1` fetches summaries from NebulaGraph
  (`KNOWLEDGE_MCP_GRAPH_HOST`/`KNOWLEDGE_MCP_GRAPH_SPACE`)
- `KNOWLEDGE_MCP_GRAPH_PROBE_ENABLE` (default `0`) – when `1` runs a bounded match query (limit
  `KNOWLEDGE_MCP_GRAPH_PROBE_LIMIT`) to ensure graph connectivity

When connectors are disabled or the dependency/liveness check fails, the service falls back to
deterministic synthetic responses so local development remains simple.

`GET /info` now emits per-connector status blocks (`enabled`, `available`, `last_error`). These fields
reflect the outcome of lightweight readiness checks executed at startup and after each tool call. Use
them in orchestration layers to short-circuit expensive queries or surface actionable operator alerts.
If probes are enabled, successful round-trips are also recorded as OTEL counters
(`knowledge_mcp.connector.success`, `knowledge_mcp.connector.degraded`) so dashboards can track live
degradations.

## Local development

```bash
python -m knowledge_mcp --port 8082
```

Optional demo seeding (requires qdrant-client/opensearch-py):

```bash
python packages/mcp-servers/knowledge-mcp/scripts/seed_demo.py
```

Run tests from the repo root:

```bash
PYTHONPATH=packages/mcp-servers/knowledge-mcp/src pytest packages/mcp-servers/knowledge-mcp/tests -q
```

The current implementation relies on synthetic responses but keeps interfaces aligned with
Qdrant/OpenSearch/NebulaGraph integrations so the transport can be swapped without touching
the FastAPI surface.
