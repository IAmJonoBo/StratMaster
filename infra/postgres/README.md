# Postgres Operations

This document captures the operational contract for StratMaster's Postgres
clusters: schema design, migration tooling, tenant isolation, and
backup/restore procedures.

## Schema layout

- Primary application schema: `stratmaster_api` (API models, task queues).
- Demo content schema: `stratmaster_demo` (created by `seeds/seed_demo.py`).
- Observability schema: `stratmaster_telemetry` (Langfuse, tracing). Separate
  database when using managed services.

Conventions:

- Always prefix tables with a domain (`research_`, `agents_`, `knowledge_`).
- Reference data (enums, lookups) lives under `stratmaster_api.ref_*`.
- Use `TIMESTAMPTZ` for all temporal columns and default to `NOW()`.

## Migration tooling

- `alembic` is the source of truth. Configuration lives under
  `packages/api/alembic.ini`.
- Use autogenerate to create migrations, then hand-edit for idempotency and
  reversible operations.
- Apply migrations via `make migrate` (wraps Alembic with env-aware DSN).
- CI runs `alembic upgrade head` against a disposable database to detect drift.

## Tenant isolation

- Production clusters run in PostgreSQL 14+ with logical replication enabled for
  reporting workloads.
- Each tenant receives a dedicated schema (`tenant_<id>`). A SECURITY DEFINER
  function ensures tenants cannot cross schema boundaries.
- API services authenticate using role `app_tenant_<id>` with `SET ROLE` on
  connection checkout.

Example policy:

```sql
CREATE POLICY tenant_row_level_policy ON stratmaster_api.reports
USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

Tenants are onboarded via Terraform which creates the schema, grants, and sets
secrets via Sealed Secrets.

## Credential management

- Secrets stored in SOPS files under `ops/k8s/secrets/postgres-*.yaml`.
- Applications receive credentials via Kubernetes Secrets managed by the
  platform operator.
- Rotate credentials quarterly; run `scripts/rotate_postgres_password.py` to
  update the user, then refresh the sealed secret.

## Backup and restore

- Nightly logical backups with `pg_dump` stored in MinIO (`sm-backups/postgres/`).
- Point-in-time recovery via WAL archiving to object storage (use `wal-g`).
- Monthly full restores exercised in staging; document outcome in
  `ops/runbooks/postgres-dr.md`.
- Monitor backup jobs with Prometheus alerts on freshness and duration.

## Maintenance

- Enable `pg_stat_statements` and collect metrics via the observability stack.
- Vacuum/ANALYZE runs weekly; autovacuum tuned for tenant schemas with high churn.
- Apply minor version patches within 14 days of release; capture upgrade plan in
  the change log.

## Local development

- Docker Compose exposes Postgres on `localhost:5432` (user/password `postgres`).
- Use `make db.psql` to open a psql shell inside the container.
- Run `make db.reset` to drop and recreate schemas when testing migrations.

## References

- `docs/data/database-architecture.md`
- Terraform module `infra/terraform/modules/postgres`
- Observability dashboards in Grafana (`Postgres - Primary`)
