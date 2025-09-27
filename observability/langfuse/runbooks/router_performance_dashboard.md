# Router MCP Telemetry Dashboard Runbook

This dashboard tracks the SCRATCH Phase 1 routing objectives across latency,
success, and cost dimensions.

## Import instructions

1. In Langfuse select **Dashboards → Import dashboard**.
2. Upload `observability/langfuse/dashboards/router_performance_dashboard.json`.
3. Map the dataset to the `router.telemetry` collection. When using the local
   stack, telemetry arrives once the Router MCP processes traffic via
   `packages/mcp-servers/router-mcp`.
4. Save the dashboard and pin it to the "Gateway" collection.

## On-call checks

- ✅ **Latency histogram** – keep the 95th percentile below 1.2s
- ✅ **Success rate** – stay above 98% for each provider
- ✅ **Cost trend** – review spikes >15% week-over-week
- ✅ **Cascade escalation** – maintain escalation rate below 20%

## Response playbook

1. Confirm the issue by drilling into Langfuse events for the affected model.
2. Export the telemetry slice to `issues_summary.json` using
   `scripts/issuesuite_bridge.py --telemetry-export` for audit linkage.
3. Update model weights in `configs/router/models-policy.yaml` if a provider is
   degraded, then redeploy.
4. Backfill the Model Performance store by calling
   `POST /router/models/refresh` to ensure persistent metrics stay current.
