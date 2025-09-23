# StratMaster

![CI](https://github.com/IAmJonoBo/StratMaster/actions/workflows/ci.yml/badge.svg)
[![Trunk](https://img.shields.io/badge/Lint-Trunk-blue?logo=trunk)](https://github.com/IAmJonoBo/StratMaster/actions/workflows/trunk.yml)

**StratMaster** is an AI-powered Brand Strategy platform that combines evidence-grounded research, multi-agent debate, and constitutional AI to deliver reliable strategic recommendations. Built as a Python monorepo with FastAPI, multiple MCP servers, and comprehensive backing services.

## 📖 Documentation

**Quick Start**: Jump to [Quick Start](#quick-start) for immediate setup

**Comprehensive Guides**:

- **[🏗️ Architecture Overview](docs/architecture.md)** - System design, components, and data flow
- **[💻 Development Guide](docs/development.md)** - Setup, coding, testing, and contribution workflows
- **[🚀 Deployment Guide](docs/deployment.md)** - Local, staging, and production deployment
- **[🔧 Infrastructure Guide](docs/infrastructure.md)** - All 12+ backing services configuration
- **[🔒 Security Guide](docs/security.md)** - Security architecture and best practices
- **[🩺 Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions

**Additional Documentation**:

- **[📋 Engineering Blueprint](PROJECT.md)** - Complete technical specification
- **[📊 Project Backlog](docs/backlog.md)** - Development roadmap and status
- **[🤝 Contributing](CONTRIBUTING.md)** - How to contribute to the project
- **[🛡️ Security Policy](SECURITY.md)** - Vulnerability reporting

## Key Features

- **🔍 Evidence-Grounded Research**: Web crawling with provenance tracking and PII hygiene
- **🧠 Knowledge Fabric**: GraphRAG + hybrid retrieval (Qdrant + OpenSearch + NebulaGraph)
- **🤖 Multi-Agent Debate**: Constitutional AI with critic and adversary validation
- **📊 Strategic Modeling**: CEPs, JTBD, DBAs, Experiments, and Forecasts as first-class objects
- **🖥️ Modern Interface**: Desktop tri-pane UI and mobile read-only approvals
- **🔌 MCP Architecture**: Model Context Protocol for all tool/resource access
- **🔒 Security First**: Multi-tenant isolation, encryption, and audit logging
- **☁️ Cloud Native**: Kubernetes-ready with Helm charts and auto-scaling

## Quick Start

**Prerequisites**:

- Python 3.11+
- Docker Desktop (for full stack)
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

**Service URLs** (when running full stack):

- **API Gateway**: [http://localhost:8080](http://localhost:8080) (OpenAPI docs at `/docs`)
- **Research MCP**: [http://localhost:8081](http://localhost:8081) (Web research and crawling)
- **Knowledge MCP**: [http://localhost:8082](http://localhost:8082) (Vector and graph search)
- **Router MCP**: [http://localhost:8083](http://localhost:8083) (Model routing and policies)
- **Temporal UI**: [http://localhost:8088](http://localhost:8088) (Workflow management)
- **Langfuse**: [http://localhost:3000](http://localhost:3000) (LLM observability)
- **MinIO Console**: [http://localhost:9001](http://localhost:9001) (Object storage - stratmaster/stratmaster123)
- **Keycloak**: [http://localhost:8089](http://localhost:8089) (Identity management - admin/admin)

For Python-only development, see the [Development Guide](docs/development.md).

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

- **Lint**: [Trunk workflow](https://github.com/IAmJonoBo/StratMaster/actions/workflows/trunk.yml)
- **Tests/Helm**: [CI workflow](https://github.com/IAmJonoBo/StratMaster/actions/workflows/ci.yml)

## System Architecture

StratMaster follows a microservices architecture with multiple specialized components:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Web UI (Next.js)                            │
├─────────────────────────────────────────────────────────────────┤
│                  FastAPI Gateway                               │
├─────────────────────────────────────────────────────────────────┤
│  Research MCP │ Knowledge MCP │ Router MCP │ Evals MCP         │
│  Web Crawling │ Vector Search │ Model Route│ Quality Gates     │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL │ Qdrant │ OpenSearch │ NebulaGraph │ MinIO       │
│  Relational │ Vectors│ Full-text  │ Graph DB     │ Objects     │
└─────────────────────────────────────────────────────────────────┘
```

**Key Components**:

- **MCP Servers**: Specialized microservices following Model Context Protocol
- **Storage Layer**: Multi-modal data storage (relational, vector, graph, object)
- **Infrastructure**: Temporal workflows, Keycloak auth, observability stack
- **AI Pipeline**: Constitutional AI with multi-agent debate and eval gates

For detailed architecture information, see the [Architecture Overview](docs/architecture.md).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- **Development Setup**: Local environment and workflows
- **Code Standards**: Python, TypeScript, and documentation requirements
- **Testing**: Unit, integration, and end-to-end testing approaches
- **Security**: Security review process and vulnerability reporting
- **Release Process**: How changes are reviewed and deployed

## License

This project is licensed under the [MIT License](LICENSE).

## Support

- **Documentation**: Start with the [comprehensive guides](#-documentation) above
- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/IAmJonoBo/StratMaster/issues)
- **Security**: Report vulnerabilities via our [Security Policy](SECURITY.md)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)
