# research-mcp

Structured MCP server exposing the research tools described in `PROJECT.md`.

## Capabilities

- `POST /tools/metasearch` — invokes SearxNG (when `RESEARCH_MCP_ENABLE_NETWORK=1`) or returns
  synthetic results for offline testing
- `POST /tools/crawl` — fetches pages via HTTP (optional) and persists artefacts; always enforces
  domain allow-lists
- `GET /resources/cached_page/{cache_key}` — retrieve cached content for a crawl
- `GET /resources/provenance/{cache_key}` — retrieve provenance metadata (URL, SHA-256, fetched_at)
- Health & metadata: `GET /healthz`, `GET /info`

Allow-listed domains are supplied via `RESEARCH_MCP_ALLOWLIST` (comma-separated). Defaults to
`example.com` so the service boots safely without external dependencies. Set
`RESEARCH_MCP_ENABLE_NETWORK=1` and provide a SearxNG endpoint (e.g. `SEARXNG_ENDPOINT`) to enable
real HTTP calls. Optional flags include `RESEARCH_MCP_USE_PLAYWRIGHT=1` for Playwright-based
rendering and `RESEARCH_MCP_MINIO_*` / `RESEARCH_MCP_ENABLE_OPENLINEAGE` to emit provenance to
external sinks. Cached artefacts live under `RESEARCH_MCP_CACHE_DIR` (defaults to
`.cache/research_mcp`).

## Local development

```bash
uvicorn research_mcp.app:create_app --factory --reload --port 8081
```

Run tests via `pytest` in this package (`make test` at repo root runs them automatically).

The current implementation is a placeholder: replace the stub store with real SearxNG +
Playwright integrations and connect provenance events to OpenLineage before production use.
