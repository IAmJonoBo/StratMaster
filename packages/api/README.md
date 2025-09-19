# StratMaster API

The FastAPI service exposes the orchestration surface defined in `PROJECT.md`. It ships with
Pydantic v2 data contracts for research artefacts, decision briefs, and retrieval records.

## Modules

- App factory: `stratmaster_api.app:create_app`
- Data models: `stratmaster_api.models` (Source, Provenance, Claim, Assumption, Hypothesis,
  GraphArtifacts, RetrievalRecord, DecisionBrief, etc.)
- Stub orchestration service: `stratmaster_api.services.orchestrator_stub`

## Endpoints (all POST routes require `Idempotency-Key` header)

- `POST /research/plan` — build a research task list and candidate sources
- `POST /research/run` — execute a research plan and return claims, assumptions, and graph artefacts
- `POST /graph/summarise` — return graph summaries and diagnostics
- `POST /debate/run` — trigger the multi-agent debate stub and verdict
- `POST /recommendations` — emit a structured `DecisionBrief` bundle
- `POST /retrieval/colbert/query` / `POST /retrieval/splade/query` — structured retrieval stubs
- `POST /experiments` — create an experiment placeholder
- `POST /forecasts` — generate a synthetic forecast object
- `POST /evals/run` — run eval gate stub returning metrics
- Provider tooling: `GET /providers/openai/tools`, `GET /providers/openai/tools/{name}`
- Debug configs (guarded by `STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1`):
  `GET /debug/config/{section}/{name}`

## Running locally

```bash
uvicorn stratmaster_api.app:create_app --factory --reload --port 8080
```

Use `make api.run` for a convenience wrapper that installs editable deps.

## Tests

`pytest` covers health, OpenAI tool schemas, config validation, idempotency enforcement,
and the new orchestration endpoints. Run `make test` or `pytest -q` inside the repo.
