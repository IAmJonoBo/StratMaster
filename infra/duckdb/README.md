# DuckDB Storage Integration

DuckDB powers analytical workflows and lightweight data marts inside StratMaster.
This guide covers deployment patterns, persistence locations, resource sizing, and
sample analytical queries.

## Deployment options

- **Docker Compose**: service `duckdb` exposes a shared volume at
  `./volumes/duckdb`. Use `make analytics.shell` to open a DuckDB CLI with the
  volume mounted.
- **Helm**: chart `helm/duckdb` deploys DuckDB in server mode with the HTTP API
  enabled. Persistent volume claims map to cloud object storage (via s3fs or
  object storage gateway).

## Persistence

| Environment | Storage path                              | Notes |
| ----------- | ------------------------------------------ | ----- |
| Dev         | `volumes/duckdb/duckdb-dev.db`             | Local file; reset with `make analytics.reset`. |
| Staging     | `s3://sm-<tenant>-analytics/duckdb/`       | Use DuckDB's S3 integration with temporary credentials. |
| Production  | `s3://sm-<tenant>-analytics/duckdb/`       | Enable versioned buckets for rollback. |

Set the following environment variables for remote storage:

```bash
export DUCKDB_S3_ENDPOINT=https://s3.amazonaws.com
export DUCKDB_S3_REGION=us-east-1
export DUCKDB_ACCESS_KEY_ID=...
export DUCKDB_SECRET_ACCESS_KEY=...
```

## Resource sizing

| Workload            | CPU | Memory | Notes |
| ------------------- | --- | ------ | ----- |
| Notebook exploration| 4   | 16 GB  | Suitable for ad-hoc analysts. |
| Batch transformations | 8 | 32 GB  | For scheduled pipelines via Temporal. |
| Heavy aggregation    | 16 | 64 GB  | Consider splitting by tenant to avoid contention. |

## Sample queries

- Join knowledge artefacts with metrics stored in Parquet:
  ```sql
  INSTALL httpfs; LOAD httpfs;
  SELECT a.id, m.metric, m.value
  FROM read_parquet('s3://sm-default-processed/metrics/*.parquet') m
  JOIN read_json('s3://sm-default-processed/knowledge/*.json') a
    ON a.id = m.asset_id
  WHERE m.metric = 'engagement_score';
  ```
- Use Arrow flight endpoint to serve data to Polars:
  ```python
  import duckdb
  import polars as pl

  con = duckdb.connect("duckdb-dev.db", read_only=True)
  df = con.execute("SELECT * FROM metrics.daily LIMIT 100").fetch_arrow_table()
  pl_df = pl.from_arrow(df)
  ```

## Integration tips

- Temporal workers use DuckDB for intermediate joins before persisting to Postgres.
- Configure Arrow/Polars pipelines via `packages/analytics/config.py` to reference
  DuckDB DSNs.
- Use `duckdb.query_graphviz()` during debugging to inspect execution plans.

## Maintenance

- Run `VACUUM` monthly on long-lived databases.
- Archive old `.db` files to cold storage; keep 30 days of snapshots handy.
- Monitor disk utilisation and query latency via the analytics dashboard in Grafana.
