# compression-mcp

Compression MCP server exposing an LLMLingua-compatible `compress.prompt` tool. When LLMLingua is
not installed, the service falls back to a deterministic truncation strategy so local development
remains dependency-light.

## Capabilities

- `POST /tools/compress` — compresses text to a target token budget (mode defaults to `summary`)
- Health: `GET /healthz`

### Environment configuration

- `COMPRESSION_MCP_ENABLE_LLMLINGUA` (default `0`)
- `COMPRESSION_MCP_PROVIDER` (default `llmlingua`)

## Local development

```bash
python -m compression_mcp --port 8085
```

Run tests from the repo root:

```bash
PYTHONPATH=packages/mcp-servers/compression-mcp/src pytest packages/mcp-servers/compression-mcp/tests -q
```
