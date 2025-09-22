# Knowledge Package

The knowledge package defines storage contracts and pipelines powering the
Knowledge MCP. It covers GraphRAG materialisation, tenant storage, and exposed
APIs.

## Architecture

```text
seeds → ingestion workers → Qdrant (vectors)
                   ↘︎            → OpenSearch (keywords)
                    ↘︎           → NebulaGraph (graph context)
```

- Ingestion orchestrated via Temporal workflows (`knowledge_ingest`).
- Storage adapters expose consistent CRUD interfaces irrespective of backend.

## Storage contracts

| Asset type | Backend     | Schema                                                                       |
| ---------- | ----------- | ---------------------------------------------------------------------------- |
| `artefact` | Qdrant      | `{'id', 'title', 'summary', 'fingerprint', 'tenant_id', 'source', 'vector'}` |
| `artefact` | OpenSearch  | Mirrors Qdrant payload + SPLADE expansion field.                             |
| `graph`    | NebulaGraph | Nodes (`hypothesis`, `artefact`) edges (`supports`, `derived_from`).         |
| `manifest` | MinIO       | JSON manifest keyed by asset IDs + provenance.                               |

Contracts are defined in `packages/knowledge/src/knowledge/storage/contracts.py`
with Pydantic models ensuring validation on ingest.

## GraphRAG pipeline

1. **Ingest** raw documents via connectors (SearxNG, MCP seeds, MinIO uploads).
2. **Chunk & embed** content using the embeddings MCP (Qdrant vectors) and SPLADE
   expansion for OpenSearch.
3. **Link** artefacts to hypotheses/claims in NebulaGraph using heuristics +
   manual curation hooks.
4. **Materialise** graph communities and store summaries under `graph_summary`
   nodes.
5. **Expose** retrieval APIs returning combined results with provenance.

Temporal workflow `knowledge.materialise_graph` coordinates each step and emits
OTEL traces for observability.

## APIs

- `GET /knowledge/{tenant}/artefacts/{id}` — fetch canonical artefact with cross-store
  payload.
- `POST /knowledge/{tenant}/search` — hybrid search returning fused Qdrant +
  OpenSearch results.
- `POST /knowledge/{tenant}/graph/community` — returns graph neighbourhoods for a
  hypothesis.

All responses include `fingerprint`, `sast`, and a provenance array referencing
source URLs or internal docs.

## Tenancy

- Tenants are isolated via namespaced collections/indices and bucket prefixes.
- Access tokens carry `tenant_id` claims validated before hitting storage backends.
- Shared demo tenant `default` uses `seeds/seed_demo.py` output.

## Testing

- Unit tests under `packages/knowledge/tests` mock external clients.
- Integration tests run in CI hitting dockerised services; triggered via
  `make test.knowledge`.
- Contract tests ensure storage schemas match Pydantic definitions and that
  serialization is stable.

## Extending the pipeline

1. Add connectors under `packages/knowledge/connectors` implementing the
   `Connector` protocol.
2. Update ingestion workflow to include the connector, with feature flag toggles.
3. Document configuration in `docs/knowledge/connectors.md` and update examples.
4. Add regression tests covering success/failure modes.

## Observability

- Metrics exposed via Prometheus: ingestion throughput, error rates, queue depths.
- Langfuse spans capture chunking and summarisation operations; filter by
  `component=knowledge`.
- Alerts trigger when ingestion backlog > 100 items or when fingerprint drift is
  detected between Qdrant and OpenSearch.
