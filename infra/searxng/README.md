# SearxNG Configuration

SearxNG provides metasearch capabilities that feed StratMaster's research
workflows. This document captures engine allow-lists, tenancy overrides, rate
limits, and operational notes.

## Engine allow-list

We only enable privacy-friendly engines with clear licensing:

| Engine        | Enabled | Notes                               |
| ------------- | ------- | ----------------------------------- |
| DuckDuckGo    | ✅      | Primary web source.                 |
| Brave         | ✅      | Used for recency-sensitive queries. |
| Wikipedia     | ✅      | Citation-friendly.                  |
| StackOverflow | ✅      | Technical research.                 |
| Google        | 🚫      | Disabled to avoid ToS conflicts.    |
| Bing          | 🚫      | Disabled.                           |

Blocked domains (glob patterns) live under `configs/searxng/blocklist.txt` and
include ad networks, social media, and competitors.

## Tenant overrides

- Tenants may disable open web queries by setting `tenants.<id>.searxng.enabled=false`.
- When disabled, SearxNG only returns results from curated knowledge bases or
  custom plugins (e.g. company intranet, Confluence).
- Override file: `configs/searxng/overrides/<tenant>.yaml`.

## Rate limiting

- Nginx ingress enforces 30 requests/min per tenant via `limit_req`.
- SearxNG internal limiter set to 10 queries per 10 seconds per IP.
- Additional throttling applied by Router MCP to prevent runaway agent loops.

## Playwright handoff

For complex pages requiring rendering:

1. SearxNG identifies results flagged `requires_render=true` (custom plugin).
2. Requests are enqueued into the Playwright worker queue (Temporal task `render_page`).
3. Rendered HTML/PDF stored in MinIO `sm-{tenant}-processed/playwright/`.
4. Knowledge MCP polls the queue and enriches the artefact payload with the
   rendered snapshot.

## Deployment

- Docker Compose service `searxng` exposes port 8087.
- Helm chart `helm/searxng` configures environment variables and mounting of
  overrides.
- Use Redis for caching; ensure `REDIS_URL` points to the shared cache service.

## Operations & runbooks

- Health endpoint: `/health`.
- Monitor search latency and error rate via Prometheus exporter.
- Run `scripts/check_searxng.py` weekly to validate allow-lists and blocklists.
- When updating engines, review upstream commit history for API changes.
- Document incidents and blocked queries in `ops/runbooks/searxng.md`.

## Security

- Disable result logging by setting `search.result_backend = none`.
- API access limited to internal network ranges; enforce via NetworkPolicy.
- Filter tracking parameters using SearxNG's `remove_url_parameter` filters.
