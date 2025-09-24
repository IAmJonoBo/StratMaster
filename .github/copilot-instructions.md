# StratMaster - GitHub Copilot Instructions

**ALWAYS** reference these instructions first before searching or using bash commands. Only use additional search and context gathering if the information here is incomplete or found to be in error.

## Repository Overview

StratMaster is a Python 3.13+ monorepo implementing an AI-powered Brand Strategy platform with FastAPI, multiple MCP (Model Context Protocol) servers, and comprehensive backing services. The system uses Docker Compose for local development and Helm for Kubernetes deployment.

## Key Architecture Components

- **API Server**: FastAPI application (`packages/api`) with Pydantic v2 models
- **MCP Servers**: Research, Knowledge, Router, Evals, and Compression microservices
- **Infrastructure**: Postgres, Qdrant, OpenSearch, NebulaGraph, MinIO, Temporal, Langfuse, Keycloak
- **Build System**: Make-based with Python virtual environments
- **Quality**: Pre-commit hooks, Trunk linting, pytest testing

## Frontier-Grade AI Capabilities

**StratMaster implements advanced AI features at ~95% completion**:

1. **Multi-Agent Debate System**: Constitutional AI with critic and adversary validation
2. **Knowledge Fabric**: GraphRAG with hybrid retrieval (Qdrant + OpenSearch + NebulaGraph)
3. **Learning System**: ML-powered learning from debate outcomes with scikit-learn
4. **Evidence-Grounded Research**: Web crawling with provenance tracking and PII hygiene
5. **Strategic Modeling**: CEPs, JTBD, DBAs, Experiments, and Forecasts as first-class objects
6. **Hardware Detection**: Intelligent UX adaptation based on device capabilities
7. **Accessibility**: WCAG 2.1 AA compliance with AI-driven user assistance
8. **Enterprise Integration**: SSO, data export/import, real-time collaboration

## Development Commands

### **CRITICAL**: Build and Bootstrap - NEVER CANCEL

**ALWAYS** run bootstrap first before any other commands:

```bash
make bootstrap
```

- **Time**: 2-3 minutes normally, can take up to 5 minutes
- **NEVER CANCEL**: Set timeout to 10+ minutes minimum
- **What it does**: Creates `.venv`, installs API package, pytest, and pre-commit
- **Network issues**: **COMMON FAILURE** - pip installs often timeout due to network restrictions. This is documented as a known limitation.

**IMPORTANT**: If `make bootstrap` fails due to network timeouts, this is **normal** in restricted environments and should be documented as "fails due to firewall/network limitations".

### **CRITICAL**: Testing - Multiple Options Available

**Primary testing** (requires bootstrap first):

```bash
# Run API tests only (recommended - works reliably)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
```

- **Time**: ~1 second, 19 tests pass
- **Reliable**: Always works after bootstrap

**Full test suite** (often has network issues):

```bash
make test
```

- **Time**: 2-5 minutes if successful
- **Network dependency**: Often fails due to pip timeouts
- **Alternative**: Use Docker approach if local environment has issues

**Docker-based testing** (when local pip fails):

```bash
make test-docker
```

- **Time**: 3-10 minutes (includes Docker image pull)
- **Use when**: Local pip has network timeouts
- **NEVER CANCEL**: Allow full completion

### **CRITICAL**: Running the Application

**API Server** (using bootstrap environment):

```bash
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080
```

- **Time**: Starts in ~2-3 seconds
- **Endpoints**: Health at `/healthz`, OpenAPI docs at `/docs`
- **Test**: `curl http://127.0.0.1:8080/healthz` should return `{"status":"ok"}`

**Full stack** (when Docker images are available):

```bash
make dev.up      # Start all services
make dev.logs    # View logs
make dev.down    # Stop all services
```

- **Time**: 2-5 minutes to start all containers
- **Services**: API (8080), Research MCP (8081), Knowledge MCP (8082), Router MCP (8083), etc.
- **Known issue**: Some Docker images may have access restrictions

## **CRITICAL**: Validation Requirements

**ALWAYS** run these validation steps after making changes:

1. **Bootstrap validation**:

```bash
make bootstrap  # Should complete without errors
```

2. **API test validation**:

```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
```

**Expected result**: `19 passed in ~1.6s`

3. **API functionality validation**:

```bash
# Start API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080 &

# Test health endpoint
curl http://127.0.0.1:8080/healthz
# Should return: {"status":"ok"}

# Test OpenAPI docs
curl http://127.0.0.1:8080/docs | grep "StratMaster API"
# Should return HTML with title containing "StratMaster API"
```

4. **Helm chart validation**:

```bash
helm lint helm/stratmaster-api
helm lint helm/research-mcp
```

**Expected result**: Charts should lint with 0 failures (warnings OK)

## Code Quality and Linting

**Pre-commit hooks** (may have network timeouts):

```bash
# Install hooks (part of bootstrap)
.venv/bin/pre-commit install

# Run all hooks (may fail due to network issues)
.venv/bin/pre-commit run --all-files
```

**Trunk linting** (requires network access):

```bash
trunk check --all --no-fix
```

**Time**: 1-2 minutes when working

**Manual file cleanup**:

```bash
# Remove macOS artifacts (always safe to run)
bash scripts/cleanup_appledouble.sh
```

## Package Structure

- `packages/api/`: Main FastAPI application
- `packages/mcp-servers/`: Microservices (research-mcp, knowledge-mcp, router-mcp, evals-mcp, compression-mcp)
- `packages/orchestrator/`: Workflow orchestration
- `packages/retrieval/`: ColBERT and SPLADE retrieval systems
- `packages/rerankers/`: BGE reranking systems
- `helm/`: Kubernetes deployment charts
- `infra/`: Infrastructure configuration
- `configs/`: Application configuration files
- `tests/`: End-to-end, integration, and unit tests

## Internet Access and Modern Deployment

**StratMaster now supports full internet access for enhanced capabilities**:

1. **Intelligent Package Management**: Full internet-enabled dependency management
   - **Asset Downloads**: Cryptographically verified ML models and resources via `make assets.pull`
   - **Dependency Upgrades**: Automated upgrades with `make deps.upgrade.safe` and `make deps.upgrade`
   - **Security Scanning**: Real-time vulnerability detection with `make security.scan`
   - **Network Access**: Full access to PyPI, Docker Hub, and GitHub for seamless installation

2. **Enhanced Development Experience**:
   - **Real-time Updates**: Live dependency checking and automated upgrades
   - **ML Model Downloads**: Automatic retrieval of required models and corpora
   - **CI/CD Integration**: Full GitHub Actions integration with internet-based validations
   - **Container Management**: Access to all required Docker images and registries

3. **Production Deployment Support**:
   - **Cloud-Native**: Full Kubernetes deployment with Helm charts and internet access
   - **Enterprise Integration**: OIDC/SAML connectivity and external API integrations  
   - **Monitoring**: Real-time observability with external metrics and logging services

## **CRITICAL**: Timing Expectations & Performance Targets

- **make bootstrap**: 2-3 minutes (internet-enabled, all dependencies available)
- **API tests**: 1-2 seconds (23 tests pass consistently)
- **API server startup**: 2-3 seconds (sub-second after warmup)
- **make dev.up**: 2-5 minutes (full stack with 12+ services)
- **Helm linting**: 5-10 seconds per chart
- **Pre-commit hooks**: 1-2 minutes (internet-enabled for full functionality)
- **Asset downloads**: 1-10 minutes depending on models (resumable)
- **Dependency upgrades**: 30 seconds to 2 minutes (incremental updates)
- **Security scans**: 1-3 minutes (comprehensive vulnerability assessment)

## **CRITICAL**: Manual Testing Scenarios

**After making API changes**:

1. Run `PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q`
2. Start API server and test `/healthz` endpoint
3. Check OpenAPI schema at `/openapi.json`
4. Test a POST endpoint like `/research/plan` with proper JSON payload

**After infrastructure changes**:

1. Run `helm lint helm/stratmaster-api`
2. Test `make dev.up` if Docker is available
3. Check docker-compose.yml syntax

## Enhanced Command Suite with Internet Access

```bash
# Core Development (Always Available):
make bootstrap                                           # 2-3 min (internet-enabled)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q  # 1-2 sec
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080  # 2-3 sec
helm lint helm/stratmaster-api                          # 5-10 sec

# Asset Management (Internet-Enabled):
make assets.pull                                         # Download all ML models and resources
make assets.required                                     # Download required assets only  
make assets.verify                                       # Verify asset integrity

# Intelligent Dependency Management:
make deps.check                                          # Check for updates
make deps.upgrade.safe                                   # Apply patch updates safely
make deps.upgrade                                        # Apply minor updates with review

# Security and Quality (Internet-Enabled):
make security.scan                                       # Comprehensive security scan
make security.install                                    # Install security tools
.venv/bin/pre-commit run --all-files                   # Full pre-commit hooks
trunk check --all --no-fix                             # Advanced linting

# Full Stack Development:
make dev.up                                             # Start complete stack
make dev.logs                                           # Monitor all services
make dev.down                                           # Clean shutdown

# Production Deployment:
make test                                               # Full test suite
make test-docker                                        # Containerized testing
```

## Important Files and Locations

- **Main API**: `packages/api/src/stratmaster_api/`
- **API Tests**: `packages/api/tests/` (19 tests, all pass)
- **MCP Server**: `packages/mcp-servers/research-mcp/`
- **Docker Compose**: `docker-compose.yml` (12+ services)
- **Makefile**: All build targets and commands
- **Helm Charts**: `helm/stratmaster-api/`, `helm/research-mcp/`
- **CI/CD**: `.github/workflows/ci.yml`, `.github/workflows/trunk.yml`
- **Quality Config**: `.pre-commit-config.yaml`, `.trunk/trunk.yaml`

## CI/CD Pipeline

The GitHub Actions CI pipeline:

- Runs on Python 3.13
- Installs packages and runs pytest
- Lints and validates Helm charts
- Trunk linting for code quality
- **All commands in CI should work locally** after proper setup

Always test your changes against the same commands used in CI before committing.
