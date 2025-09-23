---
title: Make Commands
description: Complete reference for all Makefile commands in StratMaster
version: 0.1.0
platform: GNU Make, Bash, Docker
nav_order: 1
parent: CLI Reference
grand_parent: Reference
---

# Make Commands Reference

StratMaster uses a comprehensive Makefile with over 40 commands for development, testing, deployment, and maintenance. This reference documents all available commands with usage examples.

## Core Development Commands

### Environment Setup

#### `make bootstrap`
Create development environment with essential dependencies.

```bash
make bootstrap
```

**What it does:**
- Creates Python virtual environment (`.venv/`)
- Installs StratMaster API package in development mode
- Installs testing tools (pytest, pre-commit)
- Sets up pre-commit hooks

**Duration:** ~2-3 minutes  
**Requirements:** Python 3.11+

#### `make clean`
Clean up development environment.

```bash
make clean
```

**What it does:**
- Removes `.venv/` directory
- Cleans up build artifacts

#### `make setup`
User-friendly setup for non-developers.

```bash
make setup
```

**What it does:**
- Runs `./setup.sh` script
- Provides guided setup process
- Handles common configuration issues

### Testing Commands

#### `make test`
Run complete test suite.

```bash
make test
```

**What it does:**
- Creates virtual environment if needed
- Installs all test dependencies
- Runs pytest with quiet output
- Tests API and MCP servers

**Expected output:**
```
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest -q
.......................
23 passed in 1.28s
```

#### `make test-fast`
Quick test run without setup (development only).

```bash
make test-fast
```

**What it does:**
- Uses existing Python installation
- Runs tests with local source paths
- No dependency installation

**Requirements:** pytest available in current environment

#### `make test-docker`
Run tests in isolated Docker environment.

```bash
make test-docker
```

**What it does:**
- Runs tests in clean Python 3.13 container
- Avoids local environment contamination
- Useful for CI/CD validation

**Duration:** ~3-5 minutes (includes Docker image pull)

### Advanced Testing Suite

#### `make test.advanced`
Run comprehensive testing suite including property-based and integration tests.

```bash
make test.advanced
```

**What it does:**
- Executes `scripts/advanced_testing.py all`
- Runs property-based tests with Hypothesis
- Performs API contract validation
- Includes integration test scenarios

#### `make test.property`
Run property-based tests with Hypothesis.

```bash
make test.property
```

**What it does:**
- Tests API endpoints with generated inputs
- Validates data model invariants
- Finds edge cases automatically

#### `make test.contract`
Validate API contracts against OpenAPI specifications.

```bash
make test.contract
```

**What it does:**
- Tests request/response schema compliance
- Validates endpoint behavior consistency
- Checks for breaking changes

#### `make test.load`
Performance and load testing.

```bash
make test.load
```

**What it does:**
- Runs load tests for 30 seconds (default)
- Measures response times and throughput
- Identifies performance bottlenecks

#### `make test.integration`
End-to-end integration testing.

```bash
make test.integration
```

**What it does:**
- Tests complete workflows
- Validates service interactions
- Checks data flow integrity

## API Server Commands

#### `make api.run`
Start FastAPI development server.

```bash
make api.run
```

**What it does:**
- Creates virtual environment if needed
- Installs API package in development mode
- Starts Uvicorn server with hot reload
- Binds to `127.0.0.1:8080`

**Access points:**
- **API**: http://127.0.0.1:8080
- **Docs**: http://127.0.0.1:8080/docs
- **Health**: http://127.0.0.1:8080/healthz

#### `make api.docker`
Run API in Docker container.

```bash
make api.docker
```

**What it does:**
- Builds Docker image `stratmaster-api:dev`
- Runs container with port mapping
- Provides isolated API environment

## MCP Server Commands

#### `make research-mcp.run`
Start Research MCP server.

```bash
make research-mcp.run
```

**What it does:**
- Installs Research MCP package
- Starts server on `127.0.0.1:8081`
- Provides web crawling and research capabilities

#### `make expertise-mcp.run`
Start Expertise MCP server.

```bash
make expertise-mcp.run
```

**What it does:**
- Installs Expertise MCP package
- Starts expert evaluation server
- Provides domain expertise analysis

#### `make expertise-mcp.schemas`
Generate JSON schemas for Expert Council models.

```bash
make expertise-mcp.schemas
```

**What it does:**
- Generates OpenAPI-compatible schemas
- Exports Pydantic model definitions
- Updates schema documentation

#### `make experts.mcp.up`
Start Expertise MCP in Docker.

```bash
make experts.mcp.up
```

**What it does:**
- Starts expertise-mcp container
- Provides containerized expert services

## Docker & Infrastructure

### Basic Docker Commands

#### `make dev.up`
Start complete development stack.

```bash
make dev.up
```

**What it does:**
- Starts all services via Docker Compose
- Includes databases, APIs, and supporting services
- Runs in background mode (`-d`)

**Services started:**
- PostgreSQL (port 5432)
- Qdrant (port 6333) 
- OpenSearch (port 9200)
- NebulaGraph (port 9669)
- MinIO (port 9000/9001)
- Temporal (port 7233/8088)
- Langfuse (port 3000)
- Keycloak (port 8089)
- API Gateway (port 8080)
- MCP servers (ports 8081-8085)

#### `make dev.down`
Stop all development services.

```bash
make dev.down
```

**What it does:**
- Stops all Docker containers
- Preserves data volumes
- Cleans up networks

#### `make dev.logs`
View logs from all services.

```bash
make dev.logs
```

**What it does:**
- Follows logs from all containers
- Real-time log streaming
- Use Ctrl+C to exit

### Phase 2 Production Features

#### `make phase2.up`
Start Phase 2 monitoring services.

```bash
make phase2.up
```

**What it does:**
- Starts Prometheus and Grafana
- Provides production monitoring stack
- Sets up telemetry collection

**Access points:**
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

#### `make phase2.full`
Start complete Phase 2 stack.

```bash
make phase2.full
```

**What it does:**
- Starts all monitoring services
- Includes collaboration features
- Enables ML training pipeline

**Additional services:**
- **Real-time collaboration**: ws://localhost:8084/ws
- **Constitutional ML API**: http://localhost:8085

#### `make phase2.down`
Stop Phase 2 services.

```bash
make phase2.down
```

#### `make phase2.status`
Check Phase 2 service status.

```bash
make phase2.status
```

**Example output:**
```
📊 Phase 2 Service Status
========================
NAME                  COMMAND              STATUS
prometheus            /bin/prometheus      Up 2 minutes
grafana               /run.sh              Up 2 minutes
```

### Specialized Services

#### `make telemetry.up`
Start monitoring and telemetry services only.

```bash
make telemetry.up
```

#### `make collaboration.up`
Start real-time collaboration services.

```bash
make collaboration.up
```

#### `make ml.up`
Start ML training and constitutional AI services.

```bash
make ml.up
```

#### `make dev.phase2`
Complete development environment with Phase 2 features.

```bash
make dev.phase2
```

**What it does:**
- Combines `dev.up` and `phase2.up`
- Provides comprehensive development environment
- Shows service URLs and credentials

**Example output:**
```
🎉 Full development environment with Phase 2 features ready!

Available services:
  - API: http://localhost:8080
  - API Docs: http://localhost:8080/docs  
  - Grafana: http://localhost:3001 (admin/admin)
  - Prometheus: http://localhost:9090
  - Langfuse: http://localhost:3000
```

## Code Quality & Linting

#### `make lint`
Run code linting.

```bash
make lint
```

**What it does:**
- Runs Ruff linter on all Python code
- Checks code style and quality
- Reports issues without fixing

#### `make format`
Auto-format code.

```bash
make format
```

**What it does:**
- Runs Ruff auto-fix for safe changes
- Applies Black code formatting
- Modifies files in place

#### `make precommit-install`
Set up pre-commit hooks.

```bash
make precommit-install
```

**What it does:**
- Installs pre-commit package
- Sets up Git hooks for commit validation
- Includes pre-push hooks

#### `make precommit`
Run pre-commit checks manually.

```bash
make precommit
```

**What it does:**
- Runs all configured pre-commit hooks
- Validates code before commit
- May modify files automatically

## Retrieval & Indexing

#### `make index.colbert`
Build ColBERT dense retrieval index.

```bash
make index.colbert
```

**What it does:**
- Trains ColBERT model on demo corpus
- Builds vector search index
- Uses configuration from `configs/retrieval/colbert.yaml`

**Requirements:** ColBERT dependencies installed

#### `make index.splade`
Build SPLADE sparse retrieval index.

```bash
make index.splade
```

**What it does:**
- Trains SPLADE expansion model
- Builds OpenSearch index with expanded terms
- Uses configuration from `configs/retrieval/splade.yaml`

## Dependency Management

#### `make lock`
Generate dependency lock files.

```bash
make lock
```

**What it does:**
- Uses pip-tools to generate `requirements.lock`
- Creates `requirements-dev.lock` for development
- Includes cryptographic hashes for security
- Uses backtracking resolver

#### `make lock-upgrade`
Upgrade dependencies and refresh lock files.

```bash
make lock-upgrade
```

**What it does:**
- Upgrades to latest allowed versions
- Regenerates lock files with new versions
- Maintains compatibility constraints

### Advanced Dependency Management

#### `make deps.check`
Check for available dependency updates.

```bash
make deps.check
```

**What it does:**
- Scans for outdated packages
- Shows available updates
- Categorizes by update type (patch/minor/major)

#### `make deps.plan`
Plan dependency upgrade strategy.

```bash
make deps.plan --scope python
```

**What it does:**
- Analyzes upgrade paths
- Identifies potential conflicts
- Suggests upgrade sequence

#### `make deps.upgrade.safe`
Apply safe patch updates only.

```bash
make deps.upgrade.safe
```

**What it does:**
- Applies patch-level updates automatically
- Maintains API compatibility
- Low risk of breaking changes

#### `make deps.upgrade`
Apply minor version updates (requires review).

```bash
make deps.upgrade
```

**What it does:**
- Applies minor version updates
- May include new features
- Requires manual testing

## Asset Management

#### `make assets.plan`
Plan cryptographically verified asset downloads.

```bash
make assets.plan
```

**What it does:**
- Shows required assets and checksums
- Plans download strategy
- Verifies asset integrity

#### `make assets.pull`
Download all external assets.

```bash
make assets.pull
```

**What it does:**
- Downloads models, datasets, etc.
- Verifies checksums
- Places assets in correct locations

#### `make assets.required`
Download only required assets.

```bash
make assets.required
```

**What it does:**
- Downloads minimal required assets
- Skips optional/development assets
- Faster setup for production

#### `make assets.verify`
Verify integrity of downloaded assets.

```bash
make assets.verify
```

**What it does:**
- Checks file hashes
- Validates asset integrity
- Reports any corruption

## Security & Compliance

#### `make security.scan`
Run comprehensive security scan.

```bash
make security.scan
```

**What it does:**
- Runs Bandit security linter
- Checks for dependency vulnerabilities with pip-audit
- Scans for common security issues

**Example output:**
```
🔒 Running comprehensive security scan...
Python Security (bandit):
[main]   INFO    profile include tests: None
[main]   INFO    cli include tests: None
Test results:
   No issues identified.

Dependency Vulnerabilities (pip-audit):
No known vulnerabilities found.
```

#### `make security.install`
Install security scanning tools.

```bash
make security.install
```

**What it does:**
- Installs bandit, pip-audit, safety
- Sets up detect-secrets for credential scanning
- Prepares security baseline

#### `make security.baseline`
Create security baseline for secret detection.

```bash
make security.baseline
```

**What it does:**
- Scans codebase for potential secrets
- Creates `.secrets.baseline` file
- Establishes known false positives

#### `make security.check`
Quick security validation.

```bash
make security.check
```

**What it does:**
- Fast security scan with JSON output
- Creates `bandit-report.json`
- Suitable for CI/CD pipelines

## Accessibility Enhancement

#### `make accessibility.scan`
Run WCAG 2.1 AA accessibility audit.

```bash
make accessibility.scan
```

**What it does:**
- Scans UI components for accessibility issues
- Checks WCAG 2.1 AA compliance
- Reports violations and suggestions

#### `make accessibility.fix`
Apply automated accessibility fixes.

```bash
make accessibility.fix
```

**What it does:**
- Applies safe accessibility improvements
- Adds ARIA labels and roles
- Fixes common accessibility patterns

#### `make accessibility.test`
Test keyboard navigation and screen reader compatibility.

```bash
make accessibility.test
```

**What it does:**
- Tests keyboard-only navigation
- Validates focus management
- Checks screen reader compatibility

## Health & Monitoring

#### `make health-check`
Check health of all running services.

```bash
make health-check
```

**What it does:**
- Tests API health endpoint
- Checks Grafana availability
- Validates Prometheus metrics

**Example output:**
```
🏥 Checking service health...
API Health:
{"status":"ok"}

Grafana Health:
{"commit":"abc123","database":"ok","version":"9.0.0"}

Prometheus Health:
Prometheus is Healthy.
```

## Dry Run Commands

Many commands support `--dry-run` mode for safe testing:

#### Dry Run Examples
```bash
make assets.plan.dry      # Plan asset downloads (dry run)
make assets.pull.dry      # Simulate asset downloads
make deps.check.dry       # Check dependencies (dry run)
make deps.upgrade.dry     # Simulate dependency upgrades
make accessibility.scan.dry # Simulate accessibility scan
make accessibility.fix.dry  # Simulate accessibility fixes
make test.advanced.dry    # Simulate advanced testing
make test.load.dry        # Simulate load testing
```

## Command Categories Summary

| Category | Commands | Purpose |
|----------|----------|---------|
| **Environment** | `bootstrap`, `clean`, `setup` | Setup and cleanup |
| **Testing** | `test`, `test-fast`, `test-docker`, `test.*` | Quality assurance |
| **Development** | `api.run`, `*-mcp.run`, `lint`, `format` | Active development |
| **Infrastructure** | `dev.up/down`, `phase2.*`, `health-check` | Service management |
| **Dependencies** | `lock`, `deps.*`, `assets.*` | Dependency management |
| **Security** | `security.*`, `accessibility.*` | Security and compliance |
| **Indexing** | `index.colbert`, `index.splade` | Search index building |

## Best Practices

### Daily Development Workflow
```bash
# Start development session
make bootstrap          # First time only
make dev.phase2        # Start full environment
make test              # Validate current state

# During development
make lint              # Check code quality
make test-fast         # Quick validation
make format            # Auto-format code

# End of session
make dev.down          # Stop services
```

### CI/CD Integration
```bash
# Recommended CI pipeline commands
make bootstrap
make test-docker       # Isolated testing
make security.check    # Security validation
make lint              # Code quality
make health-check      # Service validation
```

### Production Deployment
```bash
# Production preparation
make assets.required   # Download required assets
make lock              # Pin dependencies
make security.scan     # Security audit
make test.advanced     # Comprehensive testing
```

## Troubleshooting

### Common Issues

**Virtual environment conflicts:**
```bash
make clean && make bootstrap
```

**Docker issues:**
```bash
make dev.down
docker system prune
make dev.up
```

**Port conflicts:**
```bash
# Find processes using ports
lsof -i :8080
# Kill if necessary
kill -9 <PID>
```

**Asset download failures:**
```bash
make assets.verify     # Check integrity
make assets.pull       # Re-download
```

---

<div class="note">
<p><strong>💡 Tip:</strong> Use <code>make -n &lt;command&gt;</code> to see what a command will do without executing it. This is useful for understanding complex commands before running them.</p>
</div>