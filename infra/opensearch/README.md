# OpenSearch Operations

OpenSearch serves keyword search for StratMaster. This guide captures index
templates, analyzers, mappings, ILM policies, and monitoring practices.

## Index templates

| Index         | Pattern                | Template file                               |
| ------------- | ---------------------- | ------------------------------------------- |
| `research-*`  | `research-<tenant>-*`  | `infra/opensearch/templates/research.json`  |
| `knowledge-*` | `knowledge-<tenant>-*` | `infra/opensearch/templates/knowledge.json` |
| `logs-*`      | `logs-*`               | Shared observability template               |

Example snippet:

```json
{
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "analysis": {
        "analyzer": {
          "stratmaster_splade": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "asciifolding", "porter_stem"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "title": { "type": "text", "analyzer": "english" },
        "summary": { "type": "text", "analyzer": "stratmaster_splade" },
        "fingerprint": { "type": "keyword" },
        "sast": { "type": "date" },
        "tenant_id": { "type": "keyword" }
      }
    }
  }
}
```

## SPLADE field mappings

- Hybrid retrieval uses SPLADE expansions stored in `expansion` fields.
- Configure dynamic templates to map `*.splade` to `rank_features` type for
  efficient re-ranking.
- Ingestion scripts (`packages/retrieval/splade`) ensure expansions are normalised
  and truncated.

## ILM policies

| Policy name   | Phases       | Details                                                            |
| ------------- | ------------ | ------------------------------------------------------------------ |
| `sm-hot-warm` | hot → warm   | Hot: replica 1, rollover at 50 GB. Warm: force merge to 1 segment. |
| `sm-logs`     | hot → delete | Delete after 30 days.                                              |
| `sm-demo`     | hot only     | Demo indices truncated nightly.                                    |

Apply policies using:

```bash
curl -u admin:admin -XPUT https://localhost:9200/_ilm/policy/sm-hot-warm -H 'Content-Type: application/json' -d @ilm/hot-warm.json
```

Attach policies to templates via `index.lifecycle.name`.

## Monitoring & alerts

- Use OpenSearch Dashboards for cluster health. Dashboards under `observability/opensearch`.
- Prometheus exporter `infra/opensearch/exporter` emits metrics for CPU, heap,
  and request latency.
- Alerts:
  - Cluster status yellow/red
  - JVM heap > 75%
  - Indexing failures > 0

## Backups

- Snapshot repository configured against MinIO (`s3://sm-backups/opensearch`).
- Nightly snapshots triggered via `_snapshot/sm-backups/<date>`.
- Restore procedure documented in `ops/runbooks/opensearch-dr.md`.

## Security

- Enable OpenSearch Security plugin; use fine-grained access with roles per tenant.
- HTTP traffic terminates at ingress with mTLS for internal clients.
- Audit logs shipped to OpenSearch `logs-security-*` index.

## Integration tips

- Knowledge MCP indexing pipeline uses the same templates; ensure `tenant_id` is
  set per document.
- Router MCP consults OpenSearch for fallback retrieval when Qdrant is unhealthy.
- Keep `configs/retrieval/splade.yaml` aligned with index names and analyzers.
