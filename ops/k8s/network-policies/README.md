# Network Policies

Network policies enforce zero-trust communication between StratMaster services.
This document describes per-component policies and how they relate to OPA
controls under `ops/policies/`.

## Baseline

- Default namespace policy denies all ingress/egress except DNS.
- Policies are authored per workload and stored in this directory alongside Helm
  values.
- Use labels `app`, `component`, and `tenant` to scope rules precisely.

## Component matrix

| Source → Destination                         | Allowed?               | Policy file                   |
| -------------------------------------------- | ---------------------- | ----------------------------- |
| API → Postgres                               | ✅                     | `api-to-postgres.yaml`        |
| API → Temporal                               | ✅                     | `api-to-temporal.yaml`        |
| API → Qdrant/OpenSearch                      | ✅                     | `api-to-retrieval.yaml`       |
| API → MinIO                                  | ✅ (egress only)       | `api-to-minio.yaml`           |
| MCP (Research, Knowledge, Compression) → API | ✅                     | `mcp-to-api.yaml`             |
| MCP → External internet                      | 🚫 (except allow-list) | `mcp-egress.yaml`             |
| Temporal workers → External internet         | ⚠️ limited             | `temporal-egress.yaml`        |
| Observability stack → Everything             | 🚫                     | n/a (pull-based via scraping) |

- External egress is only granted via named CIDR ranges or DNS names defined in
  `NetworkPolicy` objects.
- For MCP servers we rely on application-level proxies for allow-listed domains.

## Example policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-to-postgres
spec:
  podSelector:
    matchLabels:
      app: stratmaster-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: database
          podSelector:
            matchLabels:
              app: postgres
      ports:
        - port: 5432
          protocol: TCP
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: database
          podSelector:
            matchLabels:
              app: postgres
      ports:
        - port: 5432
          protocol: TCP
```

## Validation

1. Apply policies using Argo CD/Helm.
2. Run `ops/tests/network/check_connectivity.sh` which executes `kubectl exec`
   probes verifying allowed traffic and asserting blocked flows return timeouts.
3. OPA policies in `ops/policies/network.rego` ensure every workload has an
   explicit deny-by-default policy. CI runs `conftest test` to enforce.

## Multi-tenant strategy

- Tenants are separated by namespace (`tenant-<name>`). Namespace selectors in
  policies ensure cross-tenant traffic is rejected.
- Shared services (MinIO, Postgres) expose per-tenant service accounts and rely
  on network policies plus TLS mutual auth for segmentation.
- For air-gapped tenants, set `tenant.<name>.allow_internet=false` in values to
  omit egress policies entirely.

## Monitoring & auditing

- Calico/CIlium flow logs stream into OpenSearch; dashboards surface unusual
  cross-namespace attempts.
- Nightly job runs `kubectl get netpol -A` and compares against desired state to
  detect drift.
- Keep `ops/k8s/network-policies/CHANGELOG.md` updated with policy revisions and
  attach diffs to change records.
