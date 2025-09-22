# Temporal Orchestration

Temporal coordinates StratMaster workflows (ingestion, evaluations, rendering).
This runbook covers namespace/queue strategy, retention defaults, worker config,
and demo commands.

## Namespace strategy

| Namespace             | Purpose                    | Retention |
| --------------------- | -------------------------- | --------- |
| `stratmaster-dev`     | Local development          | 3 days    |
| `stratmaster-staging` | Shared staging             | 7 days    |
| `stratmaster-prod`    | Production                 | 30 days   |
| `tenant-<id>`         | Dedicated tenant workflows | 30 days   |

- Namespaces created via `temporal operator namespace create ...` or Terraform.
- For dedicated tenants, enable archival to MinIO (`sm-<tenant>-temporal-archive`).

## Queue conventions

| Task queue           | Owner           | Notes                          |
| -------------------- | --------------- | ------------------------------ |
| `knowledge_ingest`   | Knowledge MCP   | GraphRAG materialisation.      |
| `research_workflows` | Research MCP    | Research agent pipelines.      |
| `render_playwright`  | Observability   | Page rendering via Playwright. |
| `evals`              | Evaluation MCP  | Automated regression suites.   |
| `compression`        | Compression MCP | Prompt compression tasks.      |

- Workers register with namespace-qualified queue names (`<namespace>.<queue>`)
  when running in shared clusters.

## Worker configuration

- Python workers use `temporalio` SDK. Config snippet:

  ```python
  Worker(
      client,
      task_queue="stratmaster-prod.knowledge_ingest",
      workflows=[KnowledgeIngestWorkflow],
      activities=[chunk_document, upsert_vector, upsert_keyword]
  )
  ```

- Set `activity_schedule_to_close_timeout` to 5 minutes for network-bound tasks.
- Use `max_concurrent_activity_task_pollers=5` for ingestion heavy workloads.

## Demo workflow

Start services with Docker Compose, then run:

```bash
python packages/mcp-servers/knowledge-mcp/scripts/seed_demo.py
python scripts/run_demo_workflow.py --namespace stratmaster-dev --queue knowledge_ingest
```

Inspect results via Temporal Web (`http://localhost:8088`).

## Operational practices

- Enable dynamic config for rate limiting to protect shared clusters.
- Schedule `temporal operator workflow delete --older-than 14d` in dev namespaces.
- Configure `temporal-ui` with Keycloak SSO; restrict admin access to platform team.

## Monitoring

- Export metrics to Prometheus via Temporal's metrics server (see `observability` chart).
- Alert when:
  - Workflow backlog > 100 for more than 5 minutes.
  - Activity failure rate > 5%.
  - Namespace retention near limit.

## Disaster recovery

- Take database snapshots (Temporal uses Postgres/MySQL + Elasticsearch). For dev
  use Postgres only; production uses the full stack.
- Restore process: recover DB snapshot, redeploy Temporal, reapply namespace config,
  and verify workflows resume.

## CLI snippets

```bash
tctl --ns stratmaster-prod workflow list --query "ExecutionStatus='Running'"
tctl --ns stratmaster-prod workflow terminate --wid <workflow-id> --reason "manual intervention"
tctl --ns stratmaster-prod activity complete --aid <activity-id> --result '{}'
```

## References

- `docs/orchestration/temporal.md`
- Temporal operator Helm chart values (`helm/temporal`)
- Smoke scripts: `scripts/smoke_temporal.py`
