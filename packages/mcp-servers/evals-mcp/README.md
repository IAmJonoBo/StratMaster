# evals-mcp

Evaluation MCP server that simulates running evaluation suites (RAG, TruthfulQA, FactScore).
Metrics are synthetic but respect configurable thresholds so downstream components can test
kill-switch behaviour.

## Capabilities

- `POST /tools/run` — runs a suite (`rag`, `truthfulqa`, `factscore`, `custom`) and returns
  metrics plus pass/fail status
- Health & metadata: `GET /healthz`, `GET /info`

### Environment configuration

- `EVALS_MCP_RAGAS_THRESHOLD` (default `0.75`)
- `EVALS_MCP_FACTSCORE_THRESHOLD` (default `0.7`)
- `EVALS_MCP_TRUTHFULQA_THRESHOLD` (default `0.65`)

## Local development

```bash
python -m evals_mcp --host 127.0.0.1 --port 8084
```

Run tests from the repo root:

```bash
PYTHONPATH=packages/mcp-servers/evals-mcp/src pytest packages/mcp-servers/evals-mcp/tests -q
```

Replace the synthetic metric generator with real evaluation pipelines (Ragas, FActScore,
TruthfulQA, LettuceDetect, etc.) before production deployment.
