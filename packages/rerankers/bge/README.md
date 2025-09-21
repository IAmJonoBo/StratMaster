# BGE Reranker Package

Implements cross-encoder reranking using BAAI/bge models with configurable batch
and device selection.

## Inference API

```python
from rerankers.bge import BGEReranker

reranker = BGEReranker(model_name="BAAI/bge-reranker-large", device="cuda:0", batch_size=16)
scores = reranker.score("query text", ["candidate 1", "candidate 2"])
```

- `device` can be `cpu`, `cuda:0`, or `auto` (prefers GPU if available).
- Batch size automatically falls back to 1 if VRAM is insufficient; this is logged.
- Model is loaded via `transformers.AutoModelForSequenceClassification` with FP16
  when running on GPU.

## CLI

- `python -m rerankers.bge.cli --query "..." --candidates candidates.json`
  - Accepts JSON list of candidate strings; prints ranked output.
- Use `--model`, `--device`, `--batch-size`, and `--top-k` flags to customise.

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
- Response returns ranked candidates with scores and normalised weights.
- Includes health endpoint `/healthz` and Prometheus metrics `/metrics`.

## Testing

- Unit tests under `packages/rerankers/bge/tests` validate device selection and
  deterministic scoring on small fixtures.
- Service tests ensure HTTP endpoint returns expected orderings.

## Integration

- Router MCP calls the reranker after retrieving candidates from Qdrant/OpenSearch.
- Scores stored alongside results for auditability and combined with dense scores.
- Configure routing weights in `configs/router/models-policy.yaml` under `rerank`
  tasks.

## Future work

- Add quantised INT8 models for CPU-bound deployments.
- Support streaming responses for large candidate lists.
- Provide Triton inference deployment option for higher throughput.
