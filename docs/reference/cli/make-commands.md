# Make Commands Reference

Complete reference for all Make targets in StratMaster. Targets are organized by functional area for easier navigation.

## Development {#development}

### Core Development Setup

#### `make bootstrap`
Sets up the development environment with Python virtual environment and essential dependencies.

```bash
make bootstrap
```

**What it does:**
- Creates `.venv` Python virtual environment if it doesn't exist
- Installs StratMaster API package in development mode
- Installs pytest for testing
- Installs pre-commit hooks for code quality

**Prerequisites:** Python 3.13+

**Output:** Ready-to-use development environment

---

#### `make clean`
Removes the Python virtual environment to start fresh.

```bash
make clean
```

**Use when:** Starting over or resolving dependency conflicts.

---

### Running Services

#### `make api.run`
Runs the StratMaster Gateway API locally with hot reload.

```bash
make api.run
```

**Details:**
- **Port:** 8080
- **URL:** http://127.0.0.1:8080
- **Features:** Auto-reload on code changes
- **Health check:** http://127.0.0.1:8080/healthz
- **API docs:** http://127.0.0.1:8080/docs

---

#### `make research-mcp.run`
Runs the Research MCP service locally.

```bash
make research-mcp.run
```

**Details:**
- **Port:** 8081  
- **Purpose:** Web research and crawling operations
- **Auto-reload:** Enabled for development

---

#### `make expertise-mcp.run`
Runs the Expertise MCP service locally.

```bash
make expertise-mcp.run
```

**Details:**
- **Port:** 8082
- **Purpose:** Expert analysis and domain knowledge
- **Dependencies:** Requires API package installation

---

### Testing

#### `make test`
Runs the complete test suite.

```bash
make test
```

**Includes:**
- Unit tests for all packages
- API endpoint validation
- Model schema verification
- Integration checks

**Expected output:** All tests passing

---

#### `make test-fast`
Runs tests without pip install (faster for development).

```bash
make test-fast
```

**Use when:** Making frequent code changes and testing

---

#### `make test-docker`
Runs tests in a clean Docker container to avoid local Python conflicts.

```bash
make test-docker
```

**Use when:** 
- Local Python environment has conflicts
- Verifying clean install behavior
- CI/CD validation

---

#### `make test.integration`
Runs integration test suite.

```bash
make test.integration
```

**Tests:** Cross-service communication and full workflow validation

---

#### `make test.load`
Performs load testing on the system.

```bash
make test.load
```

**Purpose:** Validate system performance under load

---

#### `make test.contract`
Runs contract tests to validate API compatibility.

```bash
make test.contract
```

**Validates:** API request/response contracts remain stable

---

#### `make test.property`
Runs property-based testing for robust validation.

```bash
make test.property
```

**Tests:** Edge cases and property invariants

---

#### `make test.advanced`
Runs comprehensive advanced test suite.

```bash
make test.advanced
```

**Includes:** Integration, load, contract, and property tests

---

## Docker Operations {#docker}

### Full Stack Management

#### `make dev.up`
Starts the complete StratMaster stack using Docker Compose.

```bash
make dev.up
```

**Services started:**
- Gateway API (port 8080)
- Research MCP (port 8081)  
- Knowledge MCP (port 8082)
- Router MCP (port 8083)
- PostgreSQL database
- Qdrant vector database
- OpenSearch
- NebulaGraph
- MinIO object storage
- Temporal workflow engine
- Langfuse observability
- Keycloak authentication

---

#### `make dev.down`
Stops all Docker services and removes containers.

```bash
make dev.down
```

**Effect:** Complete shutdown of development stack

---

#### `make dev.logs`
Shows live logs from all running services.

```bash
make dev.logs
```

**Usage:** Monitor service activity and debug issues

---

#### `make api.docker`
Builds and runs the API service in Docker.

```bash
make api.docker
```

**Details:**
- Builds `stratmaster-api:dev` image
- Runs container on port 8080
- Auto-removes container on exit

---

### Specialized Docker Services

#### `make experts.mcp.up`
Starts only the Expertise MCP service in Docker.

```bash
make experts.mcp.up
```

---

#### `make collaboration.up`
Starts collaboration and communication services.

```bash
make collaboration.up
```

---

#### `make telemetry.up`
Starts telemetry and observability services.

```bash
make telemetry.up
```

---

#### `make ml.up`
Starts machine learning and model serving services.

```bash
make ml.up
```

---

### Monitoring Services

#### `make monitoring.up`
Starts monitoring infrastructure.

```bash
make monitoring.up
```

**Services:** Prometheus, Grafana, AlertManager

---

#### `make monitoring.down`
Stops monitoring services.

```bash
make monitoring.down
```

---

#### `make monitoring.status`
Shows status of monitoring services.

```bash
make monitoring.status
```

---

#### `make monitoring.full`
Comprehensive monitoring setup with all components.

```bash
make monitoring.full
```

---

## Code Quality {#quality}

### Linting and Formatting

#### `make lint`
Runs code linting checks.

```bash
make lint
```

**Tools:** Ruff linter with project-specific configuration

**Exit codes:**
- 0: No issues found
- 1: Linting issues detected

---

#### `make format`
Auto-formats code according to project standards.

```bash
make format
```

**Tools:** 
- Ruff for import sorting and fixes
- Black for code formatting

---

#### `make precommit-install`
Installs pre-commit hooks for automatic quality checks.

```bash
make precommit-install
```

**Hooks installed:**
- Code formatting
- Import sorting  
- Linting
- Security scanning
- Type checking

---

#### `make precommit`
Runs all pre-commit hooks on all files.

```bash
make precommit
```

**Use when:** Validating entire codebase before commits

---

### Security Scanning

#### `make security.install`
Installs security scanning tools.

```bash
make security.install
```

---

#### `make security.scan`
Performs comprehensive security vulnerability scan.

```bash
make security.scan
```

**Scans for:**
- Dependency vulnerabilities
- Secret detection
- Code security issues
- Configuration vulnerabilities

---

#### `make security.baseline`
Establishes security baseline for future comparisons.

```bash
make security.baseline
```

---

#### `make security.check`
Quick security validation against baseline.

```bash
make security.check
```

---

### Accessibility

#### `make accessibility.scan`
Scans for accessibility issues in UI components.

```bash
make accessibility.scan
```

---

#### `make accessibility.fix`
Auto-fixes common accessibility issues.

```bash
make accessibility.fix
```

---

#### `make accessibility.test`
Runs accessibility test suite.

```bash
make accessibility.test
```

---

## Dependencies {#dependencies}

### Package Management

#### `make lock`
Generates pinned dependency lock files with security hashes.

```bash
make lock
```

**Generates:**
- `requirements.lock` - Production dependencies
- `requirements-dev.lock` - Development dependencies

**Features:** Hash verification for security

---

#### `make lock-upgrade`
Upgrades dependencies to latest allowed versions and updates lock files.

```bash
make lock-upgrade
```

---

#### `make deps.check`
Checks for dependency updates and security vulnerabilities.

```bash
make deps.check
```

**Reports:**
- Available updates
- Security advisories
- Compatibility issues

---

#### `make deps.plan`
Creates update plan for dependencies.

```bash
make deps.plan
```

---

#### `make deps.upgrade`
Upgrades dependencies with comprehensive review.

```bash
make deps.upgrade
```

**Includes:** Major and minor version updates with testing

---

#### `make deps.upgrade.safe`
Performs safe patch-level dependency upgrades only.

```bash
make deps.upgrade.safe
```

**Upgrades:** Patch versions only (lowest risk)

---

## Specialized Operations {#specialized}

### Index Building

#### `make index.colbert`
Builds ColBERT dense retrieval index.

```bash
make index.colbert
```

**Configuration:** `configs/retrieval/colbert.yaml`

**Output:** Optimized vector search index

---

#### `make index.splade`
Builds SPLADE sparse retrieval index.

```bash
make index.splade
```

**Configuration:** `configs/retrieval/splade.yaml`

**Output:** Sparse attention-based search index

---

### Schema Generation

#### `make expertise-mcp.schemas`
Generates JSON schemas for Expert Council models.

```bash
make expertise-mcp.schemas
```

**Output:** Updated JSON schema files for API validation

---

### Asset Management

#### `make assets.required`
Lists all required assets for the project.

```bash
make assets.required
```

---

#### `make assets.plan`
Creates asset download and verification plan.

```bash
make assets.plan
```

---

#### `make assets.pull`
Downloads all required project assets.

```bash
make assets.pull
```

**Downloads:** Models, datasets, configurations

---

#### `make assets.verify`
Verifies integrity of downloaded assets.

```bash
make assets.verify
```

**Checks:** File hashes, signatures, completeness

---

### Health and Setup

#### `make health-check`
Comprehensive system health validation.

```bash
make health-check
```

**Checks:**
- Service connectivity
- Database connections
- Model availability
- Configuration validity

---

#### `make setup`
Complete project setup and initialization.

```bash
make setup
```

**Performs:** Bootstrap + asset download + health check

---

## Phase 2 Enterprise Features {#phase2}

#### `make dev.phase2`
Starts Phase 2 enterprise development stack.

```bash
make dev.phase2
```

---

#### `make phase2.up`
Starts Phase 2 production services.

```bash
make phase2.up
```

---

#### `make phase2.down`
Stops Phase 2 services.

```bash
make phase2.down
```

---

#### `make phase2.status`
Shows Phase 2 service status.

```bash
make phase2.status
```

---

#### `make phase2.full`
Complete Phase 2 deployment with all features.

```bash
make phase2.full
```

---

## Dry Run Operations

Many operations support "dry run" mode for safety:

- `make deps.upgrade.dry` - Preview dependency upgrades
- `make accessibility.scan.dry` - Preview accessibility fixes
- `make test.advanced.dry` - Preview advanced test execution
- `make assets.pull.dry` - Preview asset downloads
- `make test.load.dry` - Preview load test execution

Dry run operations show what would be done without making changes.

## Common Workflows

### New Developer Setup
```bash
make bootstrap          # Setup environment
make precommit-install  # Install git hooks
make test               # Verify everything works
make dev.up             # Start full stack
```

### Development Cycle
```bash
make test-fast          # Quick tests during development
make lint               # Check code quality
make format             # Auto-format
make precommit          # Final validation
```

### Production Deployment Prep
```bash
make security.scan      # Security validation
make test.advanced      # Comprehensive testing
make assets.verify      # Asset integrity
make health-check       # System validation
```

## Troubleshooting

### Common Issues

**`make bootstrap` fails:**
- Check Python 3.13+ is available
- Verify internet connectivity for package downloads
- Clear existing `.venv` with `make clean`

**Tests fail:**
- Run `make test-docker` for clean environment testing
- Check service availability with `make health-check`
- Verify configuration files are present

**Docker issues:**
- Ensure Docker is running
- Check port conflicts (8080-8088 range)
- Review logs with `make dev.logs`

### Getting Help

For detailed error information, most Make targets support verbose output:
```bash
make target VERBOSE=1
```

## See Also

- [Scripts Reference](scripts.md) - Utility scripts and automation tools
- [Development Setup](../../how-to/development-setup.md) - Complete setup guide
- [Troubleshooting](../../how-to/troubleshooting.md) - Issue resolution guide