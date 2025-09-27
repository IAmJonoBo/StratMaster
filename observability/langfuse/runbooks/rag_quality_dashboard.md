# Langfuse RAG Quality Dashboard Runbook

This runbook explains how to import and operate the Langfuse dashboard that
tracks the SCRATCH Phase 2.3 quality gates.

## Import instructions

1. Sign in to your Langfuse workspace with an account that has `editor` access.
2. Navigate to **Dashboards → Import dashboard**.
3. Upload `observability/langfuse/dashboards/rag_quality_dashboard.json`.
4. Confirm the data source is set to the `evaluation` collection. When running
   locally with the docker compose stack the Langfuse API is available at
   `http://localhost:3000/api/public`.
5. Save the dashboard and add it to the "Hybrid Retrieval" collection for easy
   access during release reviews.

## Operational checklist

- ❇️ **Faithfulness threshold** – keep the timeseries above `0.75` (SCRATCH gate)
- ❇️ **Context precision/recall** – stay above `0.60`
- ❇️ **TruLens groundedness** – each model should remain above `0.75`
- ❌ **Quality gate summary** – investigate any row where `passes_quality_gates`
  is `false`. Link the failure to a Langfuse trace and attach the analysis to the
  deployment review template.

## Incident response

1. Trigger the regression suite: `make eval.rag-regression`
2. Capture failing trace URLs from Langfuse and open an incident ticket (IssueSuite
   `type=incident` template).
3. Roll back the offending retriever/reranker configuration via
   `configs/retrieval/hybrid_config.yaml` and redeploy.
4. Annotate the Langfuse dashboard with a note that references the incident ID.
