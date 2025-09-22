# StratMaster Development Guide

This guide covers everything you need to develop, test, and contribute to StratMaster. Whether you're setting up for the first time or looking for specific workflows, this guide provides comprehensive instructions.

## Quick Start

### Prerequisites

- **Python 3.11+**: Required for all Python components
- **Docker Desktop**: For full-stack development and testing
- **Git**: With signed commits recommended
- **Node.js 18+**: For web UI development (optional)
- **Helm 3.x**: For Kubernetes deployment testing (optional)

### 1-Minute Setup

```bash
# Clone the repository
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster

# Bootstrap development environment (2-3 minutes)
make bootstrap

# Verify installation
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
# Expected: 19 passed in ~1s
```

### Full Development Stack

```bash
# Start all services (2-5 minutes first run)
make dev.up

# View service logs
make dev.logs

# Stop all services
make dev.down
```

**Available Services:**
- **API Server**: http://localhost:8080 (FastAPI with OpenAPI docs)
- **Research MCP**: http://localhost:8081  
- **Knowledge MCP**: http://localhost:8082
- **Router MCP**: http://localhost:8083
- **Evals MCP**: http://localhost:8084
- **Compression MCP**: http://localhost:8085
- **Temporal UI**: http://localhost:8088
- **Langfuse**: http://localhost:3000
- **MinIO Console**: http://localhost:9001
- **Keycloak**: http://localhost:8089 (admin/admin)

## Development Environment

### Python Virtual Environment

The project uses a Python virtual environment for dependency isolation:

```bash
# Created automatically by make bootstrap
.venv/
├── bin/python          # Python interpreter  
├── bin/pip            # Package installer
├── bin/pytest         # Test runner
├── bin/uvicorn        # ASGI server
└── lib/python3.11/    # Installed packages
```

### Environment Variables

Key environment variables for development:

```bash
# API Configuration
STRATMASTER_API_HOST=127.0.0.1
STRATMASTER_API_PORT=8080
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1

# MCP Server Endpoints
RESEARCH_MCP_URL=http://localhost:8081
KNOWLEDGE_MCP_URL=http://localhost:8082
ROUTER_MCP_URL=http://localhost:8083

# Database Connections
DATABASE_URL=postgresql://stratmaster:stratmaster@localhost:5432/stratmaster
QDRANT_URL=http://localhost:6333
OPENSEARCH_URL=http://localhost:9200
NEBULA_HOSTS=localhost:9669

# Observability
LANGFUSE_URL=http://localhost:3000
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### IDE Configuration

#### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.linting.ruffEnabled": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".venv": true
  }
}
```

#### PyCharm Settings

- **Interpreter**: Point to `.venv/bin/python`
- **Code Style**: Import `ruff.toml` and `mypy.ini`
- **Run Configurations**: Use `uvicorn stratmaster_api.app:create_app --factory`

## Package Structure

StratMaster is organized as a monorepo with independent packages:

```
packages/
├── api/                 # FastAPI gateway application
├── mcp-servers/        # Model Context Protocol services
│   ├── research-mcp/   # Web research and crawling
│   ├── knowledge-mcp/  # Vector and graph search  
│   ├── router-mcp/     # Model routing and policies
│   ├── evals-mcp/      # Quality evaluation gates
│   └── compression-mcp/ # Token compression service
├── agents/             # LangGraph multi-agent workflows
├── retrieval/          # ColBERT/SPLADE indexing
│   ├── colbert/        # Dense vector retrieval
│   └── splade/         # Sparse vector expansion
├── rerankers/          # BGE cross-encoder reranking
├── knowledge/          # GraphRAG and storage
├── research/           # Web crawling and provenance
├── orchestrator/       # Temporal workflow orchestration
├── verification/       # CoVe verification agents
├── dsp/               # DSPy program synthesis
├── evals/             # Evaluation frameworks
├── providers/         # External API integrations
└── ui/                # Next.js web interface
```

### Package Development

Each package has its own:
- **README.md**: Usage instructions and examples
- **pyproject.toml**: Dependencies and build configuration
- **tests/**: Unit and integration tests
- **src/**: Source code with proper namespace

To work on a specific package:

```bash
# Install package in editable mode
pip install -e packages/api

# Run package-specific tests
pytest packages/api/tests/

# Run package in development mode
cd packages/api && uvicorn stratmaster_api.app:create_app --factory --reload
```

## Testing

StratMaster uses a multi-layer testing strategy:

### Unit Tests (Fast)

```bash
# Run all API tests (1-2 seconds)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q

# Run specific package tests
pytest packages/retrieval/colbert/tests/ -v

# Run with coverage
pytest --cov=packages/api --cov-report=html
```

### Integration Tests (Medium)

```bash
# Full repository tests (2-5 seconds)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest -q

# Test with real services (requires docker-compose up)
pytest tests/integration/ --live-services
```

### End-to-End Tests (Slow)

```bash
# Docker-based testing (3-10 minutes)
make test-docker

# Playwright UI tests
cd packages/ui && npm run test:e2e
```

### Test Organization

```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Component interaction tests  
├── e2e/              # Full workflow tests
├── fixtures/         # Test data and mocks
├── conftest.py       # Pytest configuration
└── utils/            # Test helper functions
```

### Test Best Practices

- **Fast by Default**: Unit tests should run in milliseconds
- **Isolated**: Each test should be independent
- **Deterministic**: No flaky tests due to timing or randomness
- **Meaningful**: Test behavior, not implementation details
- **Fixtures**: Use pytest fixtures for setup/teardown

## Code Quality

### Linting and Formatting

StratMaster uses [Trunk](https://trunk.io) for unified linting:

```bash
# Install trunk (one-time setup)
curl https://get.trunk.io -fsSL | bash

# Run all linters
trunk check --all

# Auto-fix issues
trunk format

# Specific linters
ruff check packages/api/
black packages/api/
mypy packages/api/
```

### Pre-commit Hooks

Automatic quality checks on every commit:

```bash
# Install hooks (included in make bootstrap)
.venv/bin/pre-commit install

# Run manually
.venv/bin/pre-commit run --all-files

# Skip hooks (emergency only)
git commit --no-verify -m "emergency fix"
```

### Type Checking

All Python code must include type hints:

```python
from typing import List, Dict, Optional
from pydantic import BaseModel

class ResearchClaim(BaseModel):
    id: str
    text: str
    confidence: float
    supporting_evidence: List[str]
    
def validate_claims(claims: List[ResearchClaim]) -> Dict[str, bool]:
    """Validate research claims for quality and completeness."""
    return {claim.id: claim.confidence > 0.8 for claim in claims}
```

**Type Checking Commands:**
```bash
# Check all packages
mypy packages/

# Check specific package  
mypy packages/api/src/

# Generate type coverage report
mypy --html-report mypy-report packages/api/
```

## API Development

### FastAPI Application

The main API is built with FastAPI and follows these patterns:

```python
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Annotated

class ResearchRequest(BaseModel):
    query: str
    max_sources: int = 10

class ResearchResponse(BaseModel):
    claims: List[ResearchClaim]
    provenance: List[Source]

@app.post("/research/plan", response_model=ResearchResponse)
async def create_research_plan(
    request: ResearchRequest,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=128)]
) -> ResearchResponse:
    """Generate a research plan with sources and task breakdown."""
    # Implementation here
    pass
```

### API Testing

```bash
# Start API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --port 8080

# Test health endpoint
curl http://localhost:8080/healthz
# Expected: {"status":"ok"}

# Test with idempotency key
curl -X POST http://localhost:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-123" \
  -d '{"query": "AI strategy trends 2024"}'
```

### OpenAPI Documentation

Access interactive API docs at http://localhost:8080/docs

**Key Features:**
- **Auto-generated**: From Pydantic models and type hints
- **Interactive**: Test endpoints directly in browser
- **OpenAI Compatible**: Tool schemas available at `/providers/openai/tools`

## MCP Server Development

Model Context Protocol servers follow a consistent pattern:

### Server Structure

```python
from fastapi import FastAPI
from mcp import MCPServer
from .config import Config
from .service import ResearchService

def create_app() -> FastAPI:
    app = FastAPI(title="Research MCP")
    config = Config()
    service = ResearchService(config)
    
    @app.get("/info")
    async def info():
        return {
            "name": "research-mcp",
            "version": "0.1.0", 
            "capabilities": service.get_capabilities()
        }
    
    @app.post("/research/search")
    async def search(request: SearchRequest):
        return await service.search(request)
    
    return app
```

### MCP Development Workflow

```bash
# Start individual MCP server
cd packages/mcp-servers/research-mcp
uvicorn research_mcp.app:create_app --factory --reload --port 8081

# Test MCP endpoints
curl http://localhost:8081/info
curl -X POST http://localhost:8081/research/search -d '{"query": "test"}'

# Run MCP-specific tests
pytest tests/ -v
```

### MCP Integration Testing

```python
import pytest
from httpx import AsyncClient
from research_mcp.app import create_app

@pytest.mark.asyncio
async def test_research_search():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/research/search",
            json={"query": "AI trends", "max_results": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) <= 5
```

## Infrastructure Development

### Local Development with Docker Compose

The `docker-compose.yml` provides a complete development environment:

```yaml
services:
  api:
    build: packages/api
    ports: ["8080:8080"]
    environment:
      - DATABASE_URL=postgresql://stratmaster:stratmaster@postgres:5432/stratmaster
    depends_on: [postgres, qdrant, opensearch]
  
  research-mcp:
    build: packages/mcp-servers/research-mcp
    ports: ["8081:8081"]
    
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: stratmaster
      POSTGRES_USER: stratmaster
      POSTGRES_PASSWORD: stratmaster
```

### Service Dependencies

Understanding service startup order:

```bash
# Core storage (start first)
docker-compose up -d postgres qdrant opensearch nebulagraph

# Infrastructure services  
docker-compose up -d temporal keycloak langfuse minio

# Application services
docker-compose up -d api research-mcp knowledge-mcp router-mcp

# Development utilities
docker-compose up -d searxng vllm
```

### Database Migrations

```bash
# Run database migrations (when implemented)
.venv/bin/python -m alembic upgrade head

# Create new migration
.venv/bin/python -m alembic revision --autogenerate -m "Add new table"
```

## Debugging

### API Debugging

```bash
# Enable debug endpoints
export STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1

# Start with debugger
.venv/bin/python -m debugpy --listen 5678 -m uvicorn stratmaster_api.app:create_app --factory

# Debug configuration
curl http://localhost:8080/debug/config/api/database
```

### Logging Configuration

```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
logger.info("Research request received", query="AI trends", user_id="123")
```

### Performance Profiling

```bash
# Profile API endpoint
pip install py-spy
py-spy record -o profile.svg -- .venv/bin/uvicorn stratmaster_api.app:create_app --factory

# Memory profiling  
pip install memory-profiler
mprof run .venv/bin/python -m pytest packages/api/tests/
mprof plot
```

## Deployment Testing

### Kubernetes Local Testing

```bash
# Install minikube or kind
kind create cluster --name stratmaster

# Test Helm charts
helm lint helm/stratmaster-api
helm lint helm/research-mcp

# Deploy locally
helm install stratmaster-api helm/stratmaster-api --dry-run
```

### Container Testing

```bash
# Build and test containers
docker build -t stratmaster-api packages/api/
docker run -p 8080:8080 stratmaster-api

# Test multi-arch builds
docker buildx build --platform linux/amd64,linux/arm64 packages/api/
```

## Troubleshooting

### Common Issues

#### "pip timeouts / network restrictions"
- **Cause**: Corporate firewalls blocking PyPI
- **Solution**: Use `make test-docker` or configure pip proxy

#### "UnicodeDecodeError in importlib.metadata"
- **Cause**: Conda/system Python conflicts  
- **Solution**: Use pyenv for clean Python installation

#### "ModuleNotFoundError: No module named 'stratmaster_api'"
- **Cause**: Package not installed in editable mode
- **Solution**: Run `make bootstrap` or `pip install -e packages/api`

#### "Docker containers failing to start"
- **Cause**: Insufficient resources or port conflicts
- **Solution**: Check `docker-compose logs` and free up ports/memory

### Debug Commands

```bash
# Check Python environment
.venv/bin/python -c "import sys; print(sys.path)"
.venv/bin/pip list

# Check service health
curl http://localhost:8080/healthz
curl http://localhost:8081/info

# Check Docker resources
docker system df
docker stats

# Check network connectivity
nmap -p 8080-8090 localhost
```

### Performance Issues

```bash
# Monitor resource usage
htop
docker stats

# Profile database queries
psql -h localhost -U stratmaster -c "SELECT * FROM pg_stat_activity;"

# Check vector database performance
curl http://localhost:6333/metrics
```

## Contributing Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/new-documentation

# Make changes and commit
git add .
git commit -m "docs: add comprehensive development guide"

# Push and create PR
git push origin feature/new-documentation
gh pr create --title "Add development documentation"
```

### PR Checklist

Before submitting a pull request:

- [ ] **Tests Pass**: `PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q`
- [ ] **Linting**: `trunk check --all` passes
- [ ] **Type Checking**: `mypy packages/` passes  
- [ ] **Documentation**: READMEs updated for changed components
- [ ] **Security**: No secrets or PII in commits
- [ ] **Breaking Changes**: Migration guide provided

### Code Review

- **Small PRs**: Keep changes focused and reviewable
- **Clear Descriptions**: Explain what and why, not just how
- **Tests Included**: Cover new functionality and edge cases
- **Documentation**: Update relevant docs and examples

## Next Steps

- **Advanced Development**: See [Infrastructure Guide](infrastructure.md) for service-specific development
- **Deployment**: See [Deployment Guide](deployment.md) for staging and production
- **Architecture**: See [Architecture Overview](architecture.md) for system design
- **Security**: See [Security Guide](security.md) for security practices