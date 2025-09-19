# router-mcp

Model router MCP service that simulates completion, embedding, and rerank tools. The current
implementation uses synthetic outputs but matches the API surface planned for LiteLLM/vLLM and
OpenAI provider shims.

## Capabilities

- `POST /tools/complete` — returns a completion based on the prompt and configured provider
- `POST /tools/embed` — returns deterministic embeddings for a batch of strings
- `POST /tools/rerank` — reranks candidate documents for a query
- Health & metadata: `GET /healthz`, `GET /info`

### Environment configuration

- `ROUTER_MCP_PROVIDER` (default `local`)
- `ROUTER_MCP_COMPLETION_MODEL` (default `mixtral-8x7b`)
- `ROUTER_MCP_EMBEDDING_MODEL` (default `bge-small`)
- `ROUTER_MCP_RERANK_MODEL` (default `bge-reranker-large`)
- `ROUTER_MCP_TEMPERATURE` (default `0.2`)

## Local development

```bash
python -m router_mcp --port 8083
```

Run tests from the repo root:

```bash
PYTHONPATH=packages/mcp-servers/router-mcp/src pytest packages/mcp-servers/router-mcp/tests -q
```

Replace the synthetic helpers with actual provider calls (LiteLLM/vLLM/OpenAI) before
production use.
