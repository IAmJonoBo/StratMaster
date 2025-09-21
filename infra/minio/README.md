# MinIO Buckets & Policies

This guide captures the tenancy strategy for MinIO, lifecycle expectations, and
sample workflows so teams can store and retrieve artefacts reliably.

## Bucket layout

| Bucket name                      | Purpose                              | Lifecycle |
| -------------------------------- | ------------------------------------ | --------- |
| `sm-{tenant}-raw`                | Landing zone for raw uploads (PDFs, transcripts). | 30 days hot, transition to glacier tier after 60 days. |
| `sm-{tenant}-processed`          | Normalised artefacts, embeddings, agent outputs. | 90 days hot, delete after 365 days. |
| `sm-shared-model-assets`         | Shared prompts, constitutions, evaluation artefacts. | Retain indefinitely with versioning. |
| `sm-demo`                        | Demo dataset synced by `seeds/seed_demo.py`. | Resettable; empty bucket nightly. |

- Tenants map 1:1 with customer environments (e.g. `acme`, `default`).
- Bucket names are DNS-safe and kept under 63 chars; use hyphen-separated IDs.
- Enable versioning on all buckets except `sm-demo` so accidental deletes can be
  rolled back.

## Access policies

- **Service accounts:** each MCP/API component receives an IAM user with scoped
  access to its tenant buckets. Example policy snippet:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
        "Resource": [
          "arn:aws:s3:::sm-acme-processed/*",
          "arn:aws:s3:::sm-acme-raw/*"
        ]
      }
    ]
  }
  ```
- **Tenant isolation:** policies never span tenants. Shared buckets (`sm-shared-model-assets`)
  are read-only for product teams, writable only by platform automation.
- **Console access:** disable console login for app users; use MinIO console only for
  platform engineers.

## Lifecycle configuration

Apply lifecycle policies using the MinIO `mc` tool:

```bash
mc ilm add local/sm-acme-raw \
  --expiry-days 30 \
  --transition-days 60 --transition-tier GLACIER

mc ilm add local/sm-acme-processed \
  --expiry-days 365
```

For shared assets, enable object locking and MFA delete when deploying to
production-grade MinIO or S3.

## Example workflows

### Upload artefacts

```bash
mc alias set local http://localhost:9000 stratmaster stratmaster123
mc cp research-output.pdf local/sm-default-raw/research/2024-03-18.pdf
```

### Download agent output

```bash
mc cp local/sm-default-processed/agents/session-123.json ./downloads/
```

### Sync prompts into the shared bucket

```bash
mc mirror prompts/constitutions local/sm-shared-model-assets/prompts
```

## Pipeline integration

- CI pipelines use temporary credentials minted by the platform IAM service.
- Airflow/Temporal workers reference `SM_MINIO_BUCKET_PROCESSED` and
  `SM_MINIO_BUCKET_RAW` env vars to locate tenant buckets.
- When running locally, `.env.dev` sets default buckets so `make dev.up` seeds
  MinIO with demo content.

## Security checklist

- Enforce TLS (`MINIO_SERVER_URL=https://...`) in staging/prod clusters.
- Rotate access keys quarterly; use service-account impersonation instead of static keys where possible.
- Enable audit logs by forwarding MinIO events to the observability stack (Loki or
  OpenSearch) and monitor for cross-tenant access attempts.
