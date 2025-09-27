# Langfuse Dashboards and Runbooks

The SCRATCH plan calls for Langfuse-backed observability across RAG quality and
model routing. The repository now ships import-ready dashboards and operating
runbooks under `observability/langfuse/`.

## Available dashboards

| Dashboard | JSON export | Runbook |
| --- | --- | --- |
| RAG Quality Gates | `observability/langfuse/dashboards/rag_quality_dashboard.json` | `observability/langfuse/runbooks/rag_quality_dashboard.md` |
| Router MCP Telemetry | `observability/langfuse/dashboards/router_performance_dashboard.json` | `observability/langfuse/runbooks/router_performance_dashboard.md` |

## Import quickstart

```bash
# From repository root, port-forward the local Langfuse stack (if needed)
docker compose up langfuse

# Import the dashboards using the Langfuse CLI (>=2.0)
langfuse dashboards import observability/langfuse/dashboards/rag_quality_dashboard.json
langfuse dashboards import observability/langfuse/dashboards/router_performance_dashboard.json
```

Each runbook documents the SLO thresholds, on-call response steps, and how to tie
Langfuse evidence back to deployment reviews. Reference the runbooks during
release readiness checks and paste links to the dashboards in the Ops notebook.
