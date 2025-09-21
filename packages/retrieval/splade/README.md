# SPLADE Retrieval Package

This package contains training and inference utilities for SPLADE expansions and
OpenSearch indexing.

## Training workflow

1. Prepare training corpus (JSONL with `text`, `doc_id`, `labels`).
2. Run `python -m splade.train --config configs/retrieval/splade-train.yaml`.
   - Uses Hugging Face Transformers with gradient checkpointing.
   - Outputs checkpoints under `artifacts/splade/<run-id>/`.
3. Evaluate using `python -m splade.eval --config configs/retrieval/splade-eval.yaml`.
   - Metrics include nDCG@10, MRR@10.
4. Promote the best checkpoint by updating `configs/retrieval/splade.yaml`.

Config highlights (`splade-train.yaml`):

```yaml
model_name: naver/splade-cocondenser-selfdistil
batch_size: 16
learning_rate: 1e-5
max_steps: 20000
warmup_steps: 500
```

## Inference & expansion

- Generate SPLADE expansions from seed documents:
  ```bash
  python -m splade.expand \
    --input seeds/demo-ceps-jtbd-dbas.json \
    --output artifacts/splade/demo-expansions.jsonl
  ```
- Script tokenises text, produces sparse activations, and writes JSON lines with
  `{ "doc_id": "...", "expansion": {"token": weight, ...} }`.
- Use `--max-features` to cap expansion size (default 200 tokens).

## OpenSearch indexing

- CLI `python -m splade.index --config configs/retrieval/splade.yaml` uploads
  expansions to OpenSearch.
- Steps:
  1. Ensure index template exists (see `infra/opensearch/README.md`).
  2. Provide OpenSearch endpoint credentials via env vars (`OPENSEARCH_HOST`, `OPENSEARCH_USER`, `OPENSEARCH_PASSWORD`).
  3. Command performs bulk indexing using `_bulk` API with retry logic.
- After indexing, run `python -m splade.verify` to compare fingerprints against
  Qdrant payloads and ensure parity.

## Integration with retrieval orchestrator

- Router uses SPLADE scores as the sparse component in hybrid search.
- The package exposes `SpladeHybridScorer` which combines dense (Qdrant) and sparse
  scores with configurable weights.
- Update `configs/router/models-policy.yaml` to adjust weighting per task.

## Testing

- Unit tests in `tests/test_splade_cli.py` cover argument parsing and sample outputs.
- Integration tests run in CI using a mocked OpenSearch instance.

## Future enhancements

- Add ONNX export for faster inference.
- Implement incremental indexing to avoid full reloads.
- Provide per-tenant fine-tuning recipes.
