# StratMaster

![CI](https://github.com/IAmJonoBo/StratMaster/actions/workflows/ci.yml/badge.svg)
[![Trunk](https://img.shields.io/badge/Lint-Trunk-blue?logo=trunk)](https://github.com/IAmJonoBo/StratMaster/actions/workflows/trunk.yml)

Initial scaffolding for the StratMaster monorepo. See `PROJECT.md` for the full engineering blueprint.

## Quick start

- Python 3.11+
- Optional: uv or pipx

### Run the full stack (dev)

The compose file now brings up the API, MCP servers, and backing services (Postgres, Qdrant,
OpenSearch, NebulaGraph, MinIO, Temporal, Langfuse, Keycloak, SearxNG, vLLM, OTEL, etc.).

```bash
make dev.up      # start containers in the background
make dev.logs    # tail logs across services
make dev.down    # tear everything down
```

The API is available on <http://localhost:8080>, Research MCP on <http://localhost:8081>,
Knowledge MCP on <http://localhost:8082>, Router MCP on <http://localhost:8083>, Evals MCP on
<http://localhost:8084>, Compression MCP on <http://localhost:8085>, Temporal UI on
<http://localhost:8088>, Langfuse on <http://localhost:3000>, MinIO console on
<http://localhost:9001>, and Keycloak on <http://localhost:8089> (admin/admin).

See `packages/api/README.md` for Python-only development instructions.

## Regression guard checklist

Run these quick checks before merging or after pulling changes to avoid regressions:

1. Bootstrap the env (creates .venv, installs tooling)

```bash
make bootstrap
```

1. Run API tests only (fast, ~1s)

```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
# Expected: 19 passed
```

1. Full repo tests (optional, ~2–5s locally)

```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest -q
# Expected: all tests pass (count may grow over time)
```

1. API smoke (in‑process ASGI)

```bash
.venv/bin/python scripts/smoke_api.py
# Expected: /healthz 200 {"status":"ok"} and /docs contains Swagger UI
```

1. Manual health (uvicorn)

```bash
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --host 127.0.0.1 --port 8080 &
curl -s http://127.0.0.1:8080/healthz
# Expected: {"status":"ok"}
```

1. Helm chart lint

```bash
helm lint helm/stratmaster-api
helm lint helm/research-mcp
# Expected: 0 failures (warnings OK)
```

1. AppleDouble hygiene (macOS)

```bash
git config core.hooksPath .githooks   # one‑time
bash scripts/cleanup_appledouble.sh   # manual cleanup anytime
```

Notes:

- If local pip installs time out (corporate network), document as “fails due to firewall/network limitations” and use `make test-docker` instead.
- Prefer installing from lock files (`requirements.lock`, `requirements-dev.lock`) for reproducible environments.
- Helm charts are currently at version 0.1.1 and values files set `image.tag: "0.1.1"`. If you haven't published container images for that tag yet, temporarily set `image.tag` back to `dev` in your local values to run.

## Running tests

If your local Python environment is clean (not Conda-managed), you can run:

1. Create a virtual environment and install tooling

```bash
make bootstrap
```

1. Run tests

```bash
make test
```

### Git hooks (AppleDouble cleanup)

To avoid macOS AppleDouble junk corrupting the repository (e.g. `._*` files under `.git`), this repo includes a pre-push hook that runs a cleanup script. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

You can also run the cleanup manually at any time:

```bash
bash scripts/cleanup_appledouble.sh
```

If you encounter pip/Conda interference on macOS (UnicodeDecodeError in importlib.metadata), use one of these alternatives. Note that CI runs all tests automatically on every push/PR, so local runs are optional.

- Use pyenv to install a clean CPython and recreate the venv

```bash
# Install a clean CPython (example)
pyenv install 3.12.5
pyenv local 3.12.5
make clean && make bootstrap && make test
```

- Run tests in Docker (no local Python needed)

```bash
make test-docker
```

- Quick local run without installs (only if pytest is available globally)

```bash
make test-fast
```

### Troubleshooting

- Ensure Docker Desktop is running before `make test-docker`.
- If using Conda, set `PYTHONNOUSERSITE=1` to reduce user-site contamination.

### CI dashboards

- Lint: [Trunk workflow](https://github.com/IAmJonoBo/StratMaster/actions/workflows/trunk.yml)
- Tests/Helm: [CI workflow](https://github.com/IAmJonoBo/StratMaster/actions/workflows/ci.yml)
