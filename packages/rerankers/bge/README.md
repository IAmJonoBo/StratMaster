# BGE Reranker Package

Implements cross-encoder reranking using BAAI/BGE models with a graceful
lexical fallback when transformer weights are unavailable.

## Python API

```python
from rerankers.bge import BGEReranker

reranker = BGEReranker(model_name="BAAI/bge-reranker-large", device="cuda:0", batch_size=16)
scores = reranker.score("query text", ["candidate 1", "candidate 2"])
ranked = reranker.rerank("query text", ["candidate 1", "candidate 2"], top_k=1)
```

- `device` can be `cpu`, `cuda:0`, or `auto` (prefers GPU if available).
- Batch size automatically falls back to 1 if VRAM is insufficient; this is logged.
- Set `RERANKERS_BGE_FORCE_FALLBACK=1` to force the lexical fallback, useful in CI.

## CLI

- `python -m rerankers.bge.cli --query "..." --candidates candidates.json`
  - Accepts a JSON list of candidate strings; prints ranked output.
- Use `--model`, `--device`, `--batch-size`, `--top-k`, and `--force-fallback` to customise.

Example:

```bash
python -m rerankers.bge.cli \
  --query "premium tier strategy" \
  --candidates tests/fixtures/rerank_candidates.json \
  --top-k 5
```

## Service hook

- FastAPI app available via `python -m rerankers.bge.service --port 8090`.
- Endpoint `POST /rerank` expects `{ "query": str, "candidates": [str], "top_k": int }`.
- Response returns ranked candidates with scores and preserved ordering metadata.
- Includes health endpoint `/healthz`.

## Testing

- Unit tests under `packages/rerankers/bge/tests` validate the fallback scoring,
  CLI, and service endpoint.

## Integration

- Router MCP calls the reranker when the configured provider is `local`.
- Scores surface alongside hybrid retrieval output for downstream decisioning.
- Configure routing weights in `configs/router/models-policy.yaml` under `rerank`
  tasks.

## Future work

- Add quantised INT8 models for CPU-bound deployments.
- Support streaming responses for large candidate lists.
- Provide Triton inference deployment option for higher throughput.
