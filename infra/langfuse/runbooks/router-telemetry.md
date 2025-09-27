# Router Telemetry Runbook

This runbook explains how to operationalise the router telemetry dashboards and
model recommender metrics that stream into Langfuse.

## Prerequisites
- Langfuse deployed and reachable (see `infra/langfuse/README.md`).
- `ROUTER_MCP_LANGFUSE_PUBLIC_KEY`, `ROUTER_MCP_LANGFUSE_SECRET_KEY`, and
  `ROUTER_MCP_LANGFUSE_HOST` configured in the router MCP environment.
- Model Recommender V2 flag enabled (now the default); ensure the router pods
  have been restarted after updating configuration.

## Import dashboards
1. Log into Langfuse and navigate to **Settings → Dashboards → Import**.
2. Upload the JSON files from `infra/langfuse/dashboards/`:
   - `router-telemetry.json`
   - `rag-quality.json`
3. Refresh the dashboard view and ensure widgets begin populating once router
   requests flow through the system.

## Expected signals
- `Routing Latency (p95)` widget should stabilise under the 120 ms budget defined
  in SCRATCH Phase 1.
- `Cost Per Call` visualises per-provider expenses; investigate spikes by
  checking the provider-level filters.
- `Bandit Reward & Selection Count` confirms that the bandit is learning—low
  rewards or zero selection counts indicate exploration issues.
- RAG quality widgets consume `ragas_quality_score` events; faithfulness should
  remain at ≥ 0.75 and context precision ≥ 0.6.

## Alerting hooks
- Configure Langfuse alerts (or export to Grafana via OTLP) for:
  - `latency_ms` p95 > 500 for 5 m.
  - `success_rate` < 0.9 for any tenant.
  - `reward` rolling average < 0.2 for a given model.
  - `passes_quality_gates = false` events exceeding 5 per hour.

## Troubleshooting
- **No data** – verify router MCP has the Langfuse environment variables set and
  that outbound networking is permitted.
- **High cost** – check the `cost_usd` histogram and reconcile with LiteLLM
  billing. Use the runbook’s “Bandit Reward” widget to see which model drove the
  increase.
- **Bandit not learning** – ensure the persistent store (if configured) is
  reachable and confirm the Model Recommender cronjob is running.

## References
- `packages/mcp-servers/router-mcp/src/router_mcp/telemetry.py`
- `packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py`
- `packages/api/src/stratmaster_api/tracing.py` (privacy scrubbing)
