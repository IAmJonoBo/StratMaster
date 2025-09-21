# Keycloak Tenancy

Keycloak provides identity and access management for StratMaster. This guide
covers realm/client bootstrap, dev credential strategy, and deployment options.

## Realms

| Realm             | Purpose                   | Notes |
| ----------------- | ------------------------- | ----- |
| `stratmaster-dev` | Local development stack   | Uses Docker Compose; admin/admin credentials. |
| `stratmaster`     | Shared staging/prod realm | Backed by Postgres with high availability. |
| `tenant-<id>`     | Dedicated customer realm  | Optional; used when customers bring their own IdP. |

- Realms follow a consistent client naming scheme (`api`, `agents`, `console`).
- Admin users exist only in platform-managed realms; tenants manage their own
  users via realm admin roles.

## Bootstrap procedure

1. Create the realm via Keycloak admin API or using the CLI (`kcadm.sh`).
   ```bash
   docker exec -it keycloak /opt/keycloak/bin/kcadm.sh create realms -s realm=stratmaster -s enabled=true
   ```
2. Create service clients:
   ```bash
   kcadm.sh create clients -r stratmaster -s clientId=stratmaster-api -s publicClient=false -s protocol=openid-connect -s 'redirectUris=["https://api.stratmaster.ai/*"]'
   kcadm.sh create clients -r stratmaster -s clientId=stratmaster-agents -s publicClient=false -s protocol=openid-connect -s 'redirectUris=["https://agents.stratmaster.ai/*"]'
   ```
3. Configure client scopes (`profile`, `email`, `roles`).
4. Create groups (`strategists`, `admins`, `read-only`) and assign default roles.
5. Enable fine-grained admin permissions so tenants cannot alter platform-wide config.

## Dev credentials

- Docker Compose seeds the admin user via `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD`.
- Demo users stored in `seeds/keycloak/users.json`; script `scripts/seed_keycloak.py`
  imports them on `make dev.up`.
- Rotate dev passwords monthly; they are intentionally simple but stored in
  `.env.dev` (git-ignored).

## Tenant isolation

- By default tenants authenticate against the shared `stratmaster` realm with
  realm roles scoped to their tenant.
- For customers requiring isolation, spin up a dedicated realm (`tenant-acme`).
  - Use realm attributes `tenant_id` to match router policies.
  - Provision identity brokering to allow SAML/OIDC federation.
- Each realm stores credentials in the central Postgres instance but schema is
  logically separated via `keycloak` namespace.

## Helm deployment

- Chart: `helm/keycloak` (wraps Bitnami chart with custom themes).
- Values highlights:
  ```yaml
  replicas: 2
  persistence:
    enabled: true
    size: 10Gi
  extraEnvVars:
    - name: KEYCLOAK_PROXY
      value: edge
  ingress:
    hostname: sso.staging.stratmaster.ai
    tls: true
  ```
- External secrets (admin credentials) provided via `ExternalSecret` referencing
  Sealed Secrets.

## Integration points

- API uses OAuth2 client credentials for MCP-to-API authentication.
- SPA/console uses PKCE + refresh tokens; tokens limited to 15 minutes.
- Temporal UI integrates via OIDC using the same realm.

## Operations

- Back up realm exports weekly (`/opt/keycloak/bin/kc.sh export`). Store exports in
  MinIO under `sm-backups/keycloak/`.
- Monitor with Prometheus (JMX exporter) and set alerts for session spikes or login
  failures.
- Upgrade strategy: roll out new Keycloak images in staging, run smoke tests via
  `scripts/smoke_keycloak.sh`, then promote to production.
