---
title: Development Setup
description: Complete guide to setting up your StratMaster development environment
version: 0.1.0
platform: Python 3.11+, Docker, Git
nav_order: 1
parent: How-to Guides
---

# Development Setup

This guide walks you through setting up a complete StratMaster development environment on your local machine.

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.11+ | 3.12+ |
| **Memory** | 4GB RAM | 8GB+ RAM |
| **Storage** | 10GB free | 20GB+ free |
| **Docker** | Desktop 4.0+ | Latest version |
| **Git** | 2.30+ | Latest version |

### Platform Support

- ✅ **Linux** (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- ✅ **macOS** (10.15+, both Intel and Apple Silicon)  
- ✅ **Windows** (Windows 10+ with WSL2)

## Step 1: Repository Setup

### Clone the Repository

```bash
# Clone with full history
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster

# Or clone shallow for faster setup
git clone --depth 1 https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster
```

### Set Up Git Configuration

```bash
# Configure Git hooks to prevent AppleDouble corruption (macOS)
git config core.hooksPath .githooks

# Verify hooks are set up
ls -la .githooks/
```

## Step 2: Python Environment

### Option A: Using pyenv (Recommended)

```bash
# Install pyenv if not already installed
# macOS with Homebrew
brew install pyenv

# Ubuntu/Debian
curl https://pyenv.run | bash

# Install Python 3.12
pyenv install 3.12.7
pyenv local 3.12.7

# Verify Python version
python --version  # Should show Python 3.12.7
```

### Option B: System Python

If using system Python, ensure it's 3.11+:

```bash
# Check Python version
python3 --version

# If version is too old, install newer version
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# macOS with Homebrew  
brew install python@3.12
```

## Step 3: Bootstrap Development Environment

Run the automated bootstrap process:

```bash
# Create virtual environment and install dependencies
make bootstrap
```

This command will:
- Create `.venv/` virtual environment
- Install StratMaster API package in development mode  
- Install development tools (pytest, pre-commit, etc.)
- Set up pre-commit hooks

**Expected output:**
```
[ -d .venv ] || python3 -m venv .venv
PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e packages/api pytest pre-commit
...
Successfully installed stratmaster-api-0.1.0 pytest-8.4.2 pre-commit-4.3.0 ...
```

### Troubleshooting Bootstrap

**Network timeouts (common in corporate environments):**
```bash
# Use Docker-based testing instead
make test-docker
```

**Permission errors:**
```bash
# Ensure proper permissions
sudo chown -R $USER:$USER .venv/
```

**Conda interference:**
```bash
# Disable conda/user site packages
export PYTHONNOUSERSITE=1
make clean && make bootstrap
```

## Step 4: Verify Installation

### Run Test Suite

```bash
# Fast API tests only (~1 second)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q

# Expected output:
# .......................
# 23 passed in 1.28s
```

### Test API Server

```bash
# In-process smoke test
.venv/bin/python scripts/smoke_api.py

# Expected output:
# /healthz: ok
# /docs: ok (swagger detected)
# Smoke: PASS
```

### Manual Server Test

```bash
# Start server (background)
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --host 127.0.0.1 --port 8080 &

# Test health endpoint
curl -s http://127.0.0.1:8080/healthz
# Expected: {"status":"ok"}

# Stop server
pkill -f uvicorn
```

## Step 5: Docker Environment Setup

### Install Docker Desktop

Download and install Docker Desktop for your platform:
- **macOS**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)  
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/)

### Verify Docker Installation

```bash
# Check Docker version
docker --version
docker compose --version

# Test Docker functionality
docker run hello-world
```

### Build Development Images

```bash
# Build all service images
make docker.build

# Or build individual services
docker build -f packages/api/Dockerfile -t stratmaster-api:dev .
```

## Step 6: Full Stack Development

### Start All Services

```bash
# Start complete development stack
make dev.up

# This starts:
# - PostgreSQL (port 5432)
# - Qdrant (port 6333)
# - OpenSearch (port 9200) 
# - NebulaGraph (port 9669)
# - MinIO (port 9000)
# - Temporal (port 7233)
# - Langfuse (port 3000)
# - API Gateway (port 8080)
# - MCP servers (ports 8081-8085)
```

### Verify Services

```bash
# Check service health
make dev.health

# View logs
make dev.logs

# Stop all services
make dev.down
```

## Step 7: Development Tools Setup

### Code Editor Configuration

#### VS Code Setup

Install recommended extensions:

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter", 
    "ms-python.mypy-type-checker",
    "ms-python.ruff",
    "redhat.vscode-yaml",
    "ms-vscode.docker"
  ]
}
```

Configure settings:

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["packages/api/tests/"]
}
```

#### PyCharm Setup

1. Open project in PyCharm
2. Configure Python interpreter: `Settings > Project > Python Interpreter`
3. Select existing environment: `.venv/bin/python`
4. Configure pytest: `Settings > Tools > Python Integrated Tools > Testing`

### Pre-commit Hooks

Pre-commit hooks run automatically after bootstrap, but you can configure them manually:

```bash
# Install hooks
.venv/bin/pre-commit install

# Run all hooks manually
.venv/bin/pre-commit run --all-files

# Update hooks
.venv/bin/pre-commit autoupdate
```

### Linting and Formatting

```bash
# Run ruff linter
.venv/bin/ruff check .

# Run ruff formatter
.venv/bin/ruff format .

# Run mypy type checker
.venv/bin/mypy packages/api/src/

# Run all linting (may require network access)
make lint
```

## Step 8: Development Workflow

### Standard Development Commands

```bash
# Common development tasks
make bootstrap     # Set up environment
make test          # Run all tests
make test-fast     # Run tests without setup
make lint          # Run linting/formatting
make clean         # Clean build artifacts
```

### Package Development

```bash
# Install package in development mode
pip install -e packages/api/

# Run package tests  
pytest packages/api/tests/

# Run specific test
pytest packages/api/tests/test_endpoints.py::test_research_plan_endpoint_returns_tasks
```

### API Development

```bash
# Start API with hot reload
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080

# View OpenAPI docs
open http://127.0.0.1:8080/docs

# Test endpoint
curl -X POST http://127.0.0.1:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: dev-test-001" \
  -d '{"query": "test", "tenant_id": "dev", "max_sources": 1}'
```

## Step 9: Environment Variables

### Required Environment Variables

Create `.env` file in project root:

```bash
# .env
STRATMASTER_ENV=development
STRATMASTER_LOG_LEVEL=DEBUG
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1

# Database
DATABASE_URL=postgresql://stratmaster:stratmaster123@localhost:5432/stratmaster

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Search
OPENSEARCH_URL=http://localhost:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin

# Graph Database  
NEBULA_HOSTS=localhost:9669
NEBULA_USERNAME=root
NEBULA_PASSWORD=nebula

# Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=stratmaster
MINIO_SECRET_KEY=stratmaster123

# Observability
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=http://localhost:3000

# Optional: AI Providers (disabled by default)
OPENAI_API_KEY=sk-xxx (optional)
```

### Load Environment Variables

```bash
# Load from .env file
export $(grep -v '^#' .env | xargs)

# Or use python-dotenv
python -c "from dotenv import load_dotenv; load_dotenv()"
```

## Step 10: Debugging Setup

### Python Debugging

#### VS Code Debug Configuration

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug API Server",
      "type": "python", 
      "request": "launch",
      "program": ".venv/bin/uvicorn",
      "args": [
        "stratmaster_api.app:create_app",
        "--factory",
        "--reload",
        "--host", "127.0.0.1", 
        "--port", "8080"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "STRATMASTER_ENV": "development"
      }
    }
  ]
}
```

#### Debug Tests

```bash
# Debug specific test
python -m pytest packages/api/tests/test_endpoints.py::test_research_plan_endpoint_returns_tasks --pdb

# Debug with VS Code
# Set breakpoint and run "Python: Debug Tests"
```

### Docker Debugging

```bash
# Debug container startup
docker compose -f docker-compose.yml up --build

# Inspect container logs
docker compose logs api

# Execute commands in running container
docker compose exec api bash
```

## Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall in development mode
pip install -e packages/api/
```

**Port conflicts:**
```bash
# Find process using port
lsof -ti:8080

# Kill process
lsof -ti:8080 | xargs kill -9
```

**Docker issues:**
```bash
# Clean Docker system
docker system prune -a

# Rebuild without cache
docker compose build --no-cache
```

**Git hooks not working:**
```bash
# Reconfigure hooks
git config core.hooksPath .githooks
chmod +x .githooks/*
```

### Getting Help

- **Documentation**: Check [Troubleshooting Guide](troubleshooting.md)
- **Tests**: Run `make test` to verify setup
- **Issues**: Report on [GitHub Issues](https://github.com/IAmJonoBo/StratMaster/issues)
- **Discussions**: Ask in [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)

---

<div class="success">
<p><strong>✅ Setup Complete!</strong> Your StratMaster development environment is ready. You can now start building, testing, and contributing to the project.</p>
</div>

## Next Steps

- **Start coding**: [API Reference](../reference/api/) for endpoint development
- **Run tests**: [Testing Guide](testing.md) for test-driven development  
- **Deploy locally**: [Configuration Management](configuration.md) for advanced setup
- **Understand architecture**: [Architecture Overview](../explanation/architecture.md)