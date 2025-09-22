# Seeds

This directory ships the demo corpus used across StratMaster services. It includes
curated Customer Engagement Plays (CEPs), Jobs-To-Be-Done (JTBD), and Data-Backed
Assets (DBAs) together with provenance metadata. The bundle powers local
demonstrations, QA scenarios, and regression tests.

## Dataset bundle

- `demo-ceps-jtbd-dbas.json` — canonical bundle consumed by loaders.
- `seed_demo.py` — idempotent loader wiring the dataset into Postgres, Qdrant,
  OpenSearch, and MinIO.

The JSON bundle groups artefacts by domain. Every record follows a consistent
shape so provenance and SAST (source-as-of timestamp) data is preserved.

| Key        | Type       | Description                                                    |
| ---------- | ---------- | -------------------------------------------------------------- |
| `id`       | string     | Stable identifier, namespaced per asset type.                  |
| `title`    | string     | Short handle surfaced in dashboards and search results.        |
| `summary`  | string     | Compressed description or hypothesis statement.                |
| extra keys | string/obj | Domain-specific attributes (e.g. `sponsor`, `persona`).        |
| `sast`     | RFC 3339   | Source-as-of timestamp; mirrored to provenance `collected_at`. |
| `source`   | object     | Provenance block (`type`, `reference`, `collected_at`).        |

The loader enforces that `sast` and `source.collected_at` are aligned and normalises
timestamps to UTC. Before persistence, a SHA-256 fingerprint is calculated over the
canonicalised record (asset type + JSON payload). The fingerprint is stored in
Postgres, indexed in OpenSearch, embedded into Qdrant payloads, and included in the
MinIO manifest so downstream systems can detect drift.

## Running the loader

```bash
python seeds/seed_demo.py \
  --dataset seeds/demo-ceps-jtbd-dbas.json
```

Environment variables let you point at remote infrastructure. The defaults match
`docker-compose.yml` and the `make dev.*` targets.

| Environment variable     | Default value                                               | Notes                                                                        |
| ------------------------ | ----------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `SEED_POSTGRES_DSN`      | `postgresql://postgres:postgres@localhost:5432/stratmaster` | Uses `stratmaster_demo.assets` schema/table; upsert semantics.               |
| `SEED_QDRANT_URL`        | `http://localhost:6333`                                     | Loader recreates the collection to guarantee deterministic state.            |
| `SEED_QDRANT_COLLECTION` | `stratmaster-demo`                                          | Collection payload stores fingerprints, SAST, and summary text.              |
| `SEED_OPENSEARCH_URL`    | `http://localhost:9200`                                     | Index named via `SEED_OPENSEARCH_INDEX`; mappings provisioned automatically. |
| `SEED_OPENSEARCH_INDEX`  | `stratmaster-demo`                                          | Fielded search across `title`, `summary`, and keywords.                      |
| `SEED_MINIO_ENDPOINT`    | `localhost:9000`                                            | Uses S3-compatible API; set `SEED_MINIO_SECURE=true` for TLS endpoints.      |
| `SEED_MINIO_ACCESS_KEY`  | `stratmaster`                                               | Demo credentials align with docker compose.                                  |
| `SEED_MINIO_SECRET_KEY`  | `stratmaster123`                                            | —                                                                            |
| `SEED_MINIO_BUCKET`      | `stratmaster-demo`                                          | Objects land under `assets/<type>/<id>.json`.                                |
| `SEED_MINIO_REGION`      | `us-east-1`                                                 | Required when creating buckets against AWS/S3.                               |
| `SEED_MINIO_SECURE`      | `false`                                                     | Toggle to `true` when MinIO is served behind TLS.                            |

Use `--skip` to omit backends when a dependency is unavailable (e.g. `--skip qdrant
minio`). All operations are idempotent: repeated runs converge to the same state by
using `ON CONFLICT` upserts, Qdrant upserts, OpenSearch document IDs, and `PUT`
object semantics.

## Service-specific notes

### Postgres

- Data lives in `stratmaster_demo.assets` to isolate demo content from app tables.
- Columns: `(asset_type, asset_id, title, summary, attributes JSONB, provenance JSONB,
sast TIMESTAMPTZ, fingerprint TEXT)`.
- The loader keeps provenance attributes synchronised and updates the fingerprint on
  every run to highlight upstream edits.

### Qdrant

- Collections are recreated with deterministic 16-dimension pseudo-embeddings so a
  clean slate is ensured.
- Payload includes `asset_type`, `title`, `summary`, `fingerprint`, `sast`, and
  domain-specific `attributes`.
- Useful for validating vector search + hybrid retrieval flows in development.

### OpenSearch

- Index template sets a lightweight schema (text fields + keyword metadata) and zero
  replicas for single-node dev stacks.
- Fingerprints enable cheap deduplication checks while SAST stays queryable for
  recency filtering.

### MinIO

- Bucket holds a manifest (`manifests/demo-assets.json`) summarising seeded IDs plus
  per-asset JSON artefacts.
- Artefacts are structured identically to the database payload so pipelines can fetch
  them directly and hydrate caches or downstream services.

## Provenance & SAST guidance

- `sast` timestamps are expected to be monotonic snapshots published by research or
  ops teams; keep them in UTC ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`).
- Fingerprints are deterministic; if a file changes without bumping SAST the hash
  still changes, ensuring change detection.
- When extending the dataset, include the provenance block and update SAST to the
  capture time so the loader can validate alignment automatically.

## Validation & observability

The script logs progress for every backend. Run with `python -m logging` env vars or
`LOG_LEVEL=DEBUG` to inspect HTTP calls. All optional dependencies are guarded so the
same script works in CI (where services might be unavailable) and during full-stack
runs. Future work can add pytest fixtures that invoke `seed_demo.py --skip minio`
under Docker to keep regression coverage lightweight.
