# Qdrant Operations

This runbook documents the Qdrant setup for StratMaster: collection design,
tenancy strategy, recommended index parameters, and monitoring.

## Collection layout

| Collection name        | Purpose                                     | Vector size | Distance |
| ---------------------- | ------------------------------------------- | ----------- | -------- |
| `tenant_<id>_research` | Research MCP summaries + citations          | 1024        | Cosine   |
| `tenant_<id>_assets`   | Knowledge MCP canonical artefacts           | 1536        | Dot      |
| `demo_stratmaster`     | Demo corpus seeded via `seeds/seed_demo.py` | 16          | Cosine   |

- Each tenant gets isolated collections prefixed with their namespace. Use
  payload filters (`tenant_id`) when performing cross-collection queries.
- For hybrid retrieval, store the dense vector plus metadata fields (`summary`,
  `source`, `fingerprint`).

## Recommended parameters

| Parameter                  | Value                                                 | Notes                                                    |
| -------------------------- | ----------------------------------------------------- | -------------------------------------------------------- |
| `hnsw.m`                   | 32                                                    | Balanced recall/latency for 1k QPS.                      |
| `hnsw.ef_construct`        | 128                                                   | Higher values improve recall; adjust for large datasets. |
| `quantization`             | `scalar` for `tenant_*` collections, `none` for demo. |
| `replication_factor`       | 2 (staging/prod)                                      | Enables HA.                                              |
| `write_consistency_factor` | 1 (dev), 2 (prod)                                     | Trade-off between availability and durability.           |
| `shard_number`             | 3 (prod)                                              | Spread load across nodes.                                |

## Seeding & updates

- Demo data loaded by `seeds/seed_demo.py` recreates the `demo_stratmaster`
  collection with deterministic vectors.
- Knowledge MCP (`packages/mcp-servers/knowledge-mcp`) exposes `/admin/seed`
  endpoint to re-run ingestion when connectors update.
- For bulk imports use the Qdrant gRPC API with batching (`batch_size=256`).

## Backups & restore

- Nightly snapshots with `qdrant-backup` container. Configure to upload to
  `sm-backups/qdrant/<cluster>/<date>.tar` in MinIO.
- Restore procedure:
  1. Scale down Qdrant to zero replicas.
  2. Download snapshot and unpack under `/qdrant/snapshots/<collection>/`.
  3. Scale deployment back up and verify `GET /collections/<name>`.
- Record restores in `ops/runbooks/qdrant-dr.md`.

## Monitoring

- Scrape `/metrics` for Prometheus. Alerts:
  - High `qdrant_cluster_failed` counts.
  - Latency > 200ms P95 on `/collections/<name>/points/search`.
  - Disk usage > 80% on attached volumes.
- Use Qdrant console (`/dashboard`) for quick inspection. Restrict access via
  OAuth proxy when exposed outside the cluster.

## Maintenance

- Upgrade one node at a time (rolling strategy). For version bumps across major
  releases, test snapshots in staging first.
- Run compaction monthly (`POST /collections/<name>/points/optimize`) to reclaim
  disk space after large deletes.
- Keep `configs/qdrant/config.yaml` in sync with runtime flags (telemetry,
  logging).

## Security

- Enforce API key authentication; keys stored in Sealed Secrets and mounted into
  MCP deployments.
- Limit ingress to router IP ranges; use NetworkPolicies to block pod-to-pod
  access from unrelated namespaces.
- Enable TLS termination via ingress controller or Qdrant native TLS when
  running across clusters.
