# ColBERT Retrieval Package

Utilities for building and querying ColBERT dense retrieval indices used by the
hybrid orchestrator.

## CLI

- `python -m colbert.index --config configs/retrieval/colbert.yaml`
  - Builds a ColBERT index from seed documents or datasets.
  - Supports multi-GPU sharding via `--nranks` flag.
- `python -m colbert.search --config configs/retrieval/colbert.yaml --query "..."`
  - Runs batched queries returning top-k document IDs and scores.
- `python -m colbert.eval` to compute Recall@k and MRR on validation sets.

## Indexing workflow

1. Preprocess seeds: `python -m colbert.preprocess --input seeds/demo-ceps-jtbd-dbas.json`.
2. Build index pointing to Qdrant/OpenSearch outputs for metadata enrichment.
3. Store index shards under `artifacts/colbert/<tenant>/` with manifest JSON.
4. Register the index with the orchestrator by updating `configs/retrieval/colbert.yaml`.

## Integration with Qdrant/OpenSearch

- ColBERT index stores dense embeddings. Use Qdrant for ANN search via `packages/retrieval/bridge.py`.
- Metadata (titles, fingerprints) fetched from OpenSearch after retrieving IDs.
- Config file maps ColBERT checkpoint path, Qdrant collection, and OpenSearch index per tenant.

Example config snippet:

```yaml
tenants:
  default:
    checkpoint: artifacts/colbert/default/checkpoint.dnn
    qdrant_collection: tenant_default_research
    opensearch_index: research-default-v1
    top_k: 20
```

## Testing & validation

- CLI has unit tests under `packages/retrieval/colbert/tests` covering argument
  parsing and integration with the orchestrator stub.
- Use `make test.retrieval` to run the suite.
- Smoke test script `scripts/smoke_colbert.py` queries the demo index.

## Operational guidance

- Store checkpoints in object storage with versioned folders.
- Regenerate indices after significant schema changes or new training runs.
- Monitor retrieval latency; aim for <200ms P95 when backed by GPU ANN search.
