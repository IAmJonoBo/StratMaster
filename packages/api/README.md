# StratMaster API

A minimal FastAPI service.

## Run locally

- Create a virtual environment
- Install deps
- Run in dev

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn stratmaster_api.app:create_app --factory --reload --port 8080
```

Health check: <http://localhost:8080/healthz>

## Debug config endpoint

For local inspection of YAML configs under the repo's `configs/` folder, you can enable a debug-only endpoint with an environment flag. This is disabled by default and should never be enabled in production.

- Flag: `STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1`
- Route: `GET /debug/config/{section}/{name}`
	- Allowed sections: `router`, `retrieval`, `evals`, `privacy`, `compression`
	- Example: `/debug/config/retrieval/hybrid` loads `configs/retrieval/hybrid.yaml`

Example run + call (local):

```bash
export STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1
uvicorn stratmaster_api.app:create_app --factory --reload --port 8080
# In another shell
curl -s http://localhost:8080/debug/config/retrieval/hybrid | jq .
```

Security notes:

- The endpoint rejects names with characters outside `[A-Za-z0-9_-]` and returns 400.
- When the flag is not set, the route returns 404.
