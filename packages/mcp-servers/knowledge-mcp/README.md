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

- `KNOWLEDGE_MCP_VECTOR_HOST` (default `http://localhost:6333`)
- `KNOWLEDGE_MCP_VECTOR_COLLECTION` (default `default`)
- `KNOWLEDGE_MCP_KEYWORD_HOST` (default `http://localhost:9200`)
- `KNOWLEDGE_MCP_KEYWORD_INDEX` (default `documents`)
- `KNOWLEDGE_MCP_GRAPH_HOST` (default `nebula://localhost:9669`)
- `KNOWLEDGE_MCP_GRAPH_SPACE` (default `knowledge`)

## Local development

```bash
python -m knowledge_mcp --port 8082
```

Run tests from the repo root:

```bash
PYTHONPATH=packages/mcp-servers/knowledge-mcp/src pytest packages/mcp-servers/knowledge-mcp/tests -q
```

The current implementation relies on synthetic responses but keeps interfaces aligned with
Qdrant/OpenSearch/NebulaGraph integrations so the transport can be swapped without touching
the FastAPI surface.
