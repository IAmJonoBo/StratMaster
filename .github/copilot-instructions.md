# StratMaster - GitHub Copilot Instructions

**ALWAYS** reference these instructions first before searching or using bash commands. Only use additional search and context gathering if the information here is incomplete or found to be in error.

## Repository Overview

StratMaster is a Python 3.11+ monorepo implementing an AI-powered Brand Strategy platform with FastAPI, multiple MCP (Model Context Protocol) servers, and comprehensive backing services. The system uses Docker Compose for local development and Helm for Kubernetes deployment.

## Key Architecture Components

- **API Server**: FastAPI application (`packages/api`) with Pydantic v2 models
- **MCP Servers**: Research, Knowledge, Router, Evals, and Compression microservices
- **Infrastructure**: Postgres, Qdrant, OpenSearch, NebulaGraph, MinIO, Temporal, Langfuse, Keycloak
- **Build System**: Make-based with Python virtual environments
- **Quality**: Pre-commit hooks, Trunk linting, pytest testing

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

- **Time**: ~1 second, 17 tests pass
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
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --port 8080
```

- **Time**: Starts in ~2-3 seconds
- **Endpoints**: Health at `/healthz`, OpenAPI docs at `/docs`
- **Test**: `curl http://localhost:8080/healthz` should return `{"status":"ok"}`

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

**Expected result**: `17 passed in ~1.02s`

3. **API functionality validation**:

```bash
# Start API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --port 8080 &

# Test health endpoint
curl http://localhost:8080/healthz
# Should return: {"status":"ok"}

# Test OpenAPI docs
curl http://localhost:8080/docs | grep "StratMaster API"
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

## Network and Environment Issues

**Common problems and solutions**:

1. **pip timeouts**: **VERY COMMON** in restricted environments
   - **Solution**: Document as "fails due to firewall/network limitations"
   - **Alternative**: Note that CI environment works, local restrictions prevent testing
   - **Timeout settings**: Always set 10+ minute timeouts for pip operations

2. **Docker image access denied**:
   - **Solution**: Some Docker images may not be accessible, document which ones work
   - **Alternative**: Use individual service containers that are available

3. **Pre-commit network failures**:
   - **Solution**: Document as "fails due to network limitations" but explain the expected behavior

## **CRITICAL**: Timing Expectations

- **make bootstrap**: 2-3 minutes (NEVER CANCEL - set 10+ min timeout)
- **API tests**: 1-2 seconds
- **API server startup**: 2-3 seconds
- **make dev.up**: 2-5 minutes (when images are available)
- **Helm linting**: 5-10 seconds per chart
- **Pre-commit hooks**: 1-2 minutes (often times out)

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

## Known Working Commands Summary

```bash
# Commands that work when network allows:
make bootstrap                                           # 2-3 min (often fails due to network)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q  # 1-2 sec (after bootstrap)
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --port 8080  # 2-3 sec (after bootstrap)
helm lint helm/stratmaster-api                          # 5-10 sec
bash scripts/cleanup_appledouble.sh                     # instant

# Often fail due to network restrictions (document as limitations):
make test                                               # Often fails - network timeouts
.venv/bin/pre-commit run --all-files                   # Often fails - network timeouts
make dev.up                                             # May fail - Docker image access issues

# Docker alternatives (also network-dependent):
make test-docker                                        # 3-10 min (may fail on image access)
```

## Important Files and Locations

- **Main API**: `packages/api/src/stratmaster_api/`
- **API Tests**: `packages/api/tests/` (17 tests, all pass)
- **MCP Server**: `packages/mcp-servers/research-mcp/`
- **Docker Compose**: `docker-compose.yml` (12+ services)
- **Makefile**: All build targets and commands
- **Helm Charts**: `helm/stratmaster-api/`, `helm/research-mcp/`
- **CI/CD**: `.github/workflows/ci.yml`, `.github/workflows/trunk.yml`
- **Quality Config**: `.pre-commit-config.yaml`, `.trunk/trunk.yaml`

## CI/CD Pipeline

The GitHub Actions CI pipeline:

- Runs on Python 3.11 and 3.12
- Installs packages and runs pytest
- Lints and validates Helm charts
- Trunk linting for code quality
- **All commands in CI should work locally** after proper setup

Always test your changes against the same commands used in CI before committing.
