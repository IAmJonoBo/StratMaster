# NebulaGraph Operations

NebulaGraph stores entity/relationship data powering GraphRAG workflows. This
document outlines space layout, schema DDL, retention, and integration guidance.

## Space layout

| Space name             | Purpose                                | Partition | Replica |
| ---------------------- | -------------------------------------- | --------- | ------- |
| `tenant_<id>_strategy` | Strategic entities (hypotheses, plays) | 5         | 2       |
| `tenant_<id>_research` | Research artefacts, citations          | 5         | 2       |
| `demo_stratmaster`     | Demo knowledge graph                   | 3         | 1       |

- Spaces are created per tenant to isolate workloads. Default vid type `FIXED_STRING(128)`.
- Use `meta_client_timeout_ms=60000` for reliable schema propagation.

## Schema DDL

Example for `tenant_acme_strategy`:

```ngql
CREATE TAG IF NOT EXISTS hypothesis(name string, status string, fingerprint string, sast timestamp);
CREATE TAG IF NOT EXISTS artefact(title string, url string, fingerprint string);
CREATE EDGE IF NOT EXISTS supports(weight double, rationale string);
CREATE EDGE IF NOT EXISTS derived_from(weight double);
```

- Index frequently queried properties:

  ```ngql
  CREATE TAG INDEX IF NOT EXISTS idx_hypothesis_name ON hypothesis(name(64));
  CREATE EDGE INDEX IF NOT EXISTS idx_supports_weight ON supports(weight);
  ```

## Retention & policies

- Nightly job prunes edges older than 365 days unless tagged `permanent=true`.
- Snapshots taken weekly using `nebula-dump` and stored in MinIO `sm-backups/nebulagraph/`.
- Enable WAL recycling to prevent disk exhaustion on busy clusters (`wal_ttl = 1440`).

## Sample GraphRAG queries

- Fetch supporting artefacts for a hypothesis:

  ```ngql
  GO 2 STEPS FROM "hypothesis:premium-upsell" OVER supports YIELD supports.weight AS weight, $$.artefact.title AS title;
  ```

- Identify hypotheses impacted by a given artefact:

  ```ngql
  GO 2 STEPS FROM "artefact:voc-sentiment" OVER <<supports REVERSE YIELD supports.weight AS weight, $$.hypothesis.name;
  ```

- Discover communities:

  ```ngql
  CALL algo.subgraph("tenant_acme_strategy", {"seed_vertices": ["hypothesis:premium-upsell"]});
  ```

## Integration with Knowledge MCP

- Knowledge MCP pulls graph context via the NebulaGraph Python client (`nebula3`).
- Connection parameters are read from `packages/knowledge/config.py` and align with
  tenant namespaces.
- Graph responses feed into prompt construction for the Strategist agent; ensure
  edges carry `rationale` text so the agent can surface reasoning snippets.

## Maintenance & monitoring

- Monitor via NebulaGraph Dashboard; expose metrics to Prometheus.
- Alert on:
  - storage leader imbalance > 20%
  - response latency > 500ms
  - metad service availability
- Upgrade procedure: rolling restart of storage/graph/meta services with data
  snapshot validated beforehand.

## Security

- Enable role-based auth; each tenant uses a dedicated user with access only to its
  spaces (`GRANT ROLE USER ON SPACE tenant_acme_strategy TO acme_rw`).
- Encrypt traffic using TLS; certificates issued via cert-manager and mounted into
  pods.
- Network policies restrict access to Knowledge MCP and the observability stack.
