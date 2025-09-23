# StratMaster Developer Quick Start

This guide provides fast paths for developers to bootstrap StratMaster, validate the stack, and toggle between full-fat and low-spec/offline modes. It consolidates information scattered through README.md, PROJECT.md, and the Makefile into action-oriented steps.

## 1. Bootstrap the Environment

```bash
# Create virtualenv, install toolchain, pre-commit hooks
make bootstrap

# (Optional) install MCP + UI dependencies via Poetry
make deps.mcp
make deps.ui
```

**Expected outcome**: `.venv` populated with pinned dependencies from `requirements*.txt`; pre-commit installed.

## 2. Run Fast Smoke Tests

```bash
# API-focused tests (~1s)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests -q

# Full repository tests (~5s)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest -q

# Static analysis (Ruff + MyPy)
make lint
make typecheck
```

**Tip**: Use `make check.all` (to be introduced) to chain lint + type + test once the DX upgrades land.

## 3. Launch the Full Stack (Docker Compose)

```bash
# Start everything (API, MCP servers, Qdrant, OpenSearch, NebulaGraph, MinIO, Temporal, Langfuse, SearxNG, vLLM, OTEL, etc.)
make dev.up

# Tail all service logs
make dev.logs

# Tear down stack
make dev.down
```

Service URLs once the stack is healthy:

| Service | URL | Notes |
|---------|-----|-------|
| API Gateway | http://localhost:8080 | Swagger UI at `/docs` |
| Research MCP | http://localhost:8081 | Document/web research tools |
| Knowledge MCP | http://localhost:8082 | Graph + retrieval operations |
| Router MCP | http://localhost:8083 | Model routing policies |
| Evals MCP | http://localhost:8084 | Evaluation harness |
| Compression MCP | http://localhost:8085 | Summaries + embeddings |
| Temporal UI | http://localhost:8088 | Workflow dashboard |
| Langfuse | http://localhost:3000 | LLM observability (admin/admin) |
| Grafana | http://localhost:3001 | Metrics dashboards |
| Prometheus | http://localhost:9090 | Metrics store |
| MinIO Console | http://localhost:9001 | Object storage (stratmaster/stratmaster123) |
| Keycloak | http://localhost:8089 | IAM (admin/admin) |

## 4. Seed & Evaluate

```bash
# Load demo datasets and evaluation fixtures
make seeds.load

# Run ingestion smoke (to be upgraded in PR-A)
python scripts/smoke_ingestion.py

# Run evaluation harness once PR-E lands
make eval.ragas
make eval.truthfulqa
```

Results appear in Langfuse dashboards (spans) and Grafana (metrics). Ensure kill-switch thresholds remain green.

## 5. Offline / Low-Spec Mode

Planned enhancements (Sprint 5) introduce a toggleable offline profile.

```bash
# Start CPU-only stack using Ollama + gguf models
make dev.low-spec

# Warm local caches and embeddings
python scripts/offline/warm_cache.py

# Run end-to-end smoke in offline mode
make smoke.offline
```

Hardware reference: 8-core CPU, 32 GB RAM, no discrete GPU. Expect < 180s end-to-end latency on demo corpus.

## 6. Troubleshooting Cheatsheet

| Symptom | Quick Fix |
|---------|-----------|
| Docker compose fails with missing network | Run `docker network create stratmaster` then `make dev.up` |
| Temporal UI shows stuck workflows | Check DLQ (`make temporal.dlq`) and replay after fix |
| Langfuse refuses connections | Ensure `.env` uses `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY` from docker-compose |
| MCP server 404 on tool | Re-run `make dev.up` after `make bootstrap`; ensures auto-generated tool registry |
| Offline mode missing models | Run `scripts/offline/download_models.sh` before `make dev.low-spec` |

## 7. Performance Profiles

| Profile | Models | Intended Use |
|---------|--------|--------------|
| **Standard (GPU-ready)** | vLLM (Mixtral or Llama-3 70B), ColBERT GPU, SPLADE GPU | Full-fidelity research & reasoning |
| **Balanced CPU** | vLLM (quantised 14B), SPLADE CPU, ColBERT INT8, BGE-small reranker | Dev laptops with high RAM |
| **Offline Low-Spec** | Ollama gguf (Nous-Hermes 2 7B), MiniLM reranker, DuckDB caches | Demo flows without internet |

Document performance observations in `docs/operations-guide.md` as upgrades land.

## 8. Contribute & Iterate

- Follow `CONTRIBUTING.md` for branching, commit hygiene, and pre-commit usage.
- Update docs/open-questions.md when making assumptions.
- Run `make pr.review` (to be added) for automated diff summaries before opening PRs.
