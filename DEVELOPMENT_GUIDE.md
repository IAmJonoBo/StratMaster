# StratMaster Development Guide

This guide covers everything you need to develop, test, and contribute to StratMaster. Whether you're setting up for the first time or looking for specific workflows, this guide provides comprehensive instructions.

## Quick Start

### Prerequisites

- **Python 3.13+**: Required for all Python components
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
# Expected: 23 passed in ~1s
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
└── lib/python3.13/    # Installed packages
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

```json
{
  "python.pythonPath": ".venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/*.pyc": true
  }
}
```

#### PyCharm Configuration

1. **Python Interpreter**: Set to `.venv/bin/python`
2. **Code Style**: Use Black formatter with 88-character line length
3. **Run Configurations**: Create for pytest and uvicorn
4. **Type Checking**: Enable mypy integration

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
├── orchestrator/       # Temporal workflow engine
├── analytics/          # Metrics and monitoring
├── providers/          # External API integrations
└── [13 more packages]  # SSO, mobile, training, etc.
```

### Package Dependencies

```mermaid
graph TD
    API[api] --> MCP[mcp-servers/*]
    API --> Agents[agents]
    API --> Analytics[analytics]
    
    Agents --> Research[research]
    Agents --> Knowledge[knowledge]
    Agents --> Retrieval[retrieval]
    
    Knowledge --> Rerankers[rerankers]
    Research --> Providers[providers]
    
    Orchestrator --> API
    Analytics --> Orchestrator
```

## Development Workflow

### Daily Development

```bash
# Start development session
make dev.up

# Run tests during development
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -v

# Lint and format code
trunk check --all
trunk format

# Run specific test file
.venv/bin/python -m pytest packages/api/tests/test_research.py -v

# Restart API server
make dev.restart api
```

### Testing Strategy

#### Unit Tests (Primary)

```bash
# Run all API tests (recommended - fast and reliable)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q

# Run specific test with coverage
.venv/bin/python -m pytest packages/api/tests/test_experts.py --cov=stratmaster_api

# Run with detailed output
.venv/bin/python -m pytest packages/api/tests/ -v --tb=short
```

#### Integration Tests

```bash
# Run integration tests (requires services running)
.venv/bin/python -m pytest tests/integration/ -v

# Test specific MCP server integration
.venv/bin/python -m pytest tests/integration/test_research_mcp.py -v
```

#### End-to-End Tests

```bash
# Run E2E tests with Playwright
.venv/bin/python -m pytest tests/e2e/ --headed

# Run specific E2E workflow
.venv/bin/python -m pytest tests/e2e/test_expert_council_flow.py -v
```

#### Docker-Based Testing

```bash
# When local environment has issues
make test-docker

# Clean Docker test environment
make test-docker-clean
```

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

All packages must pass mypy strict mode:

```bash
# Check specific package
mypy packages/api/src/

# Check all packages
mypy packages/

# Generate type coverage report
mypy --html-report mypy-report packages/api/src/
```

## Testing Best Practices

### Test Organization

```
packages/api/tests/
├── conftest.py           # Shared fixtures
├── test_health.py        # Health endpoint tests
├── test_research.py      # Research endpoint tests
├── test_experts.py       # Expert system tests
├── test_debate.py        # Debate system tests
└── integration/          # Integration test suite
    ├── test_mcp_integration.py
    └── test_workflow_integration.py
```

### Writing Tests

```python
# Good test structure
import pytest
from fastapi.testclient import TestClient
from stratmaster_api.app import create_app

@pytest.fixture
def client():
    """Test client fixture with proper setup."""
    app = create_app()
    return TestClient(app)

def test_research_plan_endpoint(client):
    """Test research plan generation with valid input."""
    # Arrange
    request_data = {
        "query": "AI strategy trends 2024",
        "depth": "comprehensive"
    }
    headers = {"Idempotency-Key": "test-key-123"}
    
    # Act
    response = client.post("/research/plan", json=request_data, headers=headers)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert "tasks" in data
    assert len(data["tasks"]) > 0
```

### Mock Services

```python
# Mock external dependencies
@pytest.fixture
def mock_research_mcp(monkeypatch):
    """Mock research MCP service responses."""
    async def mock_call(method, params):
        if method == "generate_plan":
            return {"plan_id": "test-plan", "tasks": []}
        return {}
    
    monkeypatch.setattr("stratmaster_api.mcpclients.research.call", mock_call)
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

## Debugging

### API Server Debugging

```bash
# Start API server with debugging
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --log-level debug

# Debug specific endpoint
curl -v http://localhost:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: debug-key" \
  -d '{"query": "test"}'

# Check OpenAPI schema
curl http://localhost:8080/openapi.json | jq .
```

### Database Debugging

```bash
# Connect to development database
psql postgresql://stratmaster:stratmaster@localhost:5432/stratmaster

# Check vector store
curl http://localhost:6333/collections

# Check search engine
curl http://localhost:9200/_cluster/health
```

### Log Analysis

```bash
# API server logs
docker logs stratmaster-api -f

# MCP server logs
docker logs stratmaster-research-mcp -f

# All service logs
make dev.logs
```

### Performance Profiling

```python
# Profile API endpoint
import cProfile
import pstats

def profile_research_endpoint():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your API call here
    response = client.post("/research/plan", json=data)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(20)

# Memory profiling with memory_profiler
@profile
def test_memory_usage():
    # Your code here
    pass
```

## Advanced Development

### Custom MCP Server Development

```python
# Creating a new MCP server
from mcp.server import MCPServer
from mcp.server.models import InitializationOptions

class CustomMCPServer(MCPServer):
    def __init__(self):
        super().__init__("custom-mcp")
        
    @self.tool("custom_tool")
    async def custom_tool(self, params: dict) -> dict:
        """Custom tool implementation."""
        return {"result": "processed"}

# Register the server
server = CustomMCPServer()
```

### Adding New Endpoints

```python
# In packages/api/src/stratmaster_api/routers/custom.py
from fastapi import APIRouter, Depends
from stratmaster_api.models import CustomRequest, CustomResponse
from stratmaster_api.dependencies import verify_idempotency

router = APIRouter(prefix="/custom", tags=["custom"])

@router.post("/process", response_model=CustomResponse)
async def process_custom(
    request: CustomRequest,
    idempotency_key: str = Depends(verify_idempotency)
):
    """Process custom request."""
    # Implementation here
    return CustomResponse(result="processed")

# Register in main app
from stratmaster_api.routers import custom
app.include_router(custom.router)
```

### Schema Development

```python
# Define new Pydantic models
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class CustomRequest(BaseModel):
    """Request model for custom operations."""
    query: str = Field(..., description="Query string")
    options: Optional[dict] = Field(None, description="Additional options")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "example query",
                    "options": {"depth": "shallow"}
                }
            ]
        }
    }
```

## Troubleshooting

### Common Issues

#### Bootstrap Fails

```bash
# Check Python version
python3 --version  # Must be 3.13+

# Clean and retry
rm -rf .venv
make bootstrap
```

#### Tests Fail

```bash
# Check environment isolation
echo $PYTHONNOUSERSITE  # Should be 1

# Clean pytest cache
rm -rf .pytest_cache packages/api/.pytest_cache

# Run tests in verbose mode
.venv/bin/python -m pytest packages/api/tests/ -v --tb=long
```

#### Docker Issues

```bash
# Check Docker status
docker info

# Clean Docker environment
make dev.down
docker system prune -f
make dev.up
```

#### Network Issues

```bash
# Check service connectivity
curl -I http://localhost:8080/healthz

# Check port conflicts
lsof -i :8080

# Reset network
docker network prune -f
```

### Getting Help

- **Documentation**: Check `docs/` directory for comprehensive guides
- **Issues**: Open GitHub issue with reproduction steps
- **Discussions**: Use GitHub Discussions for questions
- **Slack**: Internal team channel for real-time help

---

This guide provides comprehensive coverage for StratMaster development. For specific technical details, see the reference documentation in `docs/reference/`.