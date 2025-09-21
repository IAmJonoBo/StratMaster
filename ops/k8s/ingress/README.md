# Ingress Management

This guide explains how ingress resources are provisioned for StratMaster,
covering hostnames, TLS policies, and cert-manager integration.

## Hostname conventions

| Environment | Base domain                | Examples |
| ----------- | -------------------------- | -------- |
| dev         | `dev.stratmaster.local`    | `api.dev.stratmaster.local`, `minio.dev.stratmaster.local` |
| staging     | `staging.stratmaster.ai`   | `api.staging.stratmaster.ai`, `agents.staging.stratmaster.ai` |
| prod        | `stratmaster.ai`           | `api.stratmaster.ai`, `agents.stratmaster.ai`, `console.stratmaster.ai` |

- MCP servers get dedicated subdomains (e.g. `research`, `knowledge`, `compression`).
- Internal dashboards (Temporal, Langfuse) sit behind identity-aware proxies and use
  `ops.<env>.stratmaster.ai` hostnames.

## Example ingress manifest

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: stratmaster-api
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-dns
    nginx.ingress.kubernetes.io/proxy-body-size: "16m"
spec:
  rules:
    - host: api.staging.stratmaster.ai
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: stratmaster-api
                port:
                  number: 8080
  tls:
    - hosts:
        - api.staging.stratmaster.ai
      secretName: stratmaster-api-tls
```

Key points:

- TLS secrets are managed by cert-manager using DNS-01 challenges via Cloudflare.
- `proxy-body-size` bumped to 16 MB to support document uploads.
- Use separate ingress resources per tenant-critical service to avoid noisy
  neighbour issues.

## cert-manager integration

1. Install cert-manager with the Helm chart pinned in `helm/cert-manager`.
2. Provision a `ClusterIssuer` per environment. Example DNS-01 issuer:
   ```yaml
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-dns
   spec:
     acme:
       email: sre@stratmaster.ai
       server: https://acme-v02.api.letsencrypt.org/directory
       privateKeySecretRef:
         name: letsencrypt-dns-account
       solvers:
         - dns01:
             cloudflare:
               email: sre@stratmaster.ai
               apiTokenSecretRef:
                 name: cloudflare-api-token
                 key: token
   ```
3. Secrets for DNS providers are stored via Sealed Secrets (`ops/k8s/sealed-secrets`).
4. Certificate resources live next to their ingress manifests; keep names stable to
   support automated renewals.

## Traffic policies

- Enforce HTTPS by disabling HTTP listeners in the ingress controller.
- Enable `nginx.ingress.kubernetes.io/server-snippet` to set security headers:
  ```yaml
  nginx.ingress.kubernetes.io/server-snippet: |
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy strict-origin-when-cross-origin;
  ```
- For MCP services performing streaming responses, set
  `nginx.ingress.kubernetes.io/proxy-read-timeout: "600"`.
- Apply `networking.k8s.io/v1beta1` `Gateway` resources (via Gateway API) as we scale
  to multi-cluster topologies; capture experiments under `ops/k8s/gateway/`.

## Observability

- Forward ingress controller logs to Loki (`infra/observability/loki`).
- Export Prometheus metrics and alert on 5xx rates per host.
- Synthetic probes hit every public hostname and assert TLS expiry > 14 days.

## Change control

- Changes are deployed via Argo CD; PRs must include manifest diffs and updated
  diagrams where necessary.
- Use the `ops/tests/ingress-smoke.sh` script to validate route health before
  merging.
- When introducing new hostnames, update DNS Terraform and the router MCP
  configuration to keep links consistent.
