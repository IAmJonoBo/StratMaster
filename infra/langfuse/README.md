# Langfuse Deployment

Langfuse captures LLM traces and metrics for StratMaster. This guide documents
Compose/Helm deployments, persistence, ingress, auth, API key rotation, and starter
dashboards.

## Deployment modes

- **Docker Compose** (`docker-compose.yml`): runs Langfuse with Postgres + Redis.
  Accessible at `http://localhost:3000`.
- **Helm chart** (`helm/langfuse`): production-ready setup with external Postgres,
  Redis, and ingress.

### Helm values highlights

```yaml
postgresql:
  host: postgres.stratmaster.svc.cluster.local
  database: langfuse
  user: langfuse
  existingSecret: langfuse-postgres
redis:
  host: redis.langfuse.svc.cluster.local
  existingSecret: langfuse-redis
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: langfuse.staging.stratmaster.ai
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: langfuse-tls
      hosts: [langfuse.staging.stratmaster.ai]
```

## Persistence & backups

- Use managed Postgres for durability; enable WAL archiving.
- Store snapshots nightly via `pg_dump` to `sm-backups/langfuse/` (MinIO).
- Langfuse file uploads (if enabled) stored in MinIO `sm-<tenant>-processed/langfuse/`.

## Authentication

- Behind Keycloak; configure OIDC client with callback `https://langfuse.<env>.stratmaster.ai/api/auth/callback/keycloak`.
- Service accounts (agents, pipelines) use API keys minted in the Langfuse UI.
- Assign roles: `viewer`, `editor`, `admin`. Tenant-specific dashboards use filters
  based on `tenant_id` tags.

## API key rotation

1. Create new key via Langfuse UI or API.
2. Store key in Vault and sync to Kubernetes via ExternalSecret (`langfuse-api-key`).
3. Update dependent services (agents, evaluation harness) to pick up the new secret.
4. Revoke old key once rollout completes; document rotation in `ops/change-log.md`.

## Dashboards & metrics

- Starter dashboards live under `infra/langfuse/dashboards/`:
  - `llm-latency.json` — request latency, tokens, retries.
  - `agent-success-rate.json` — run success vs. failure by tenant.
  - `compression-metrics.json` — compression ratio and guardrail violations.
- Import dashboards via Langfuse UI (`Settings → Import dashboard`).

## Observability

- Enable OTLP exporter in Langfuse to forward traces to the central collector.
- Configure alerting via Grafana when:
  - failure rate > 5% per tenant
  - trace ingest backlog > 100 events
  - ingestion latency > 60s

## Operations checklist

- Scale Langfuse workers based on ingestion throughput; monitor queue metrics.
- Upgrade strategy: follow Langfuse release notes, deploy to staging, run smoke
  tests (`scripts/smoke_langfuse.py`), then roll to production.
- Maintain `LANGFUSE_PUBLIC_URL` and `LANGFUSE_SECRET_KEY` via Sealed Secrets.
