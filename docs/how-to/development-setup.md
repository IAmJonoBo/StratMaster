# Development Setup

Complete guide to setting up StratMaster for local development. This guide covers environment configuration, dependency management, and common development workflows.

## Prerequisites

Before setting up StratMaster for development:

- **Python 3.13+** with pip and venv
- **Docker Desktop** (for full-stack development)
- **Git** with proper SSH key configuration
- **4GB+ RAM** for all services
- **20GB+ disk space** for dependencies and data

## Quick Setup

For immediate development setup:

```bash
# Clone and enter the repository
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster

# One-command bootstrap
make bootstrap

# Verify installation  
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
```

Expected result: All tests pass in ~1 second.

## Detailed Setup

### 1. Python Environment

Create an isolated Python environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

### 2. Install StratMaster API Package

Install the main API package in development mode:

```bash
# Install with development dependencies
pip install -e packages/api

# Install testing and quality tools
pip install pytest pre-commit ruff mypy
```

### 3. Configure Git Hooks

Set up automated code quality checks:

```bash
# Install pre-commit hooks
pre-commit install

# Test the hooks
pre-commit run --all-files
```

### 4. Environment Configuration

Create local environment configuration:

```bash
# Copy environment template
cp .env.example .env

# Edit configuration for local development
editor .env
```

Essential environment variables:

```env
# Basic configuration
STRATMASTER_ENV=development
STRATMASTER_LOG_LEVEL=DEBUG

# Database configuration (optional for API-only development)
DATABASE_URL=postgresql://postgres:password@localhost:5432/stratmaster

# API configuration
STRATMASTER_API_HOST=127.0.0.1
STRATMASTER_API_PORT=8080

# Enable debug endpoints (development only)
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1
```

### 5. Verify Development Setup

Test all components:

```bash
# Run API tests
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -v

# Start API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080

# Test health endpoint (in another terminal)
curl -s http://127.0.0.1:8080/healthz
```

## Full-Stack Development

For complete local development including all backing services:

### Docker Compose Setup

```bash
# Start all services
make dev.up

# View logs
make dev.logs

# Stop services
make dev.down
```

Services included:
- **StratMaster API** - Main FastAPI application
- **PostgreSQL** - Primary database
- **Redis** - Caching and queues
- **Qdrant** - Vector database
- **OpenSearch** - Search and analytics
- **NebulaGraph** - Graph database
- **MinIO** - Object storage
- **Temporal** - Workflow orchestration
- **Langfuse** - LLM observability
- **Keycloak** - Authentication and authorization

### Service Health Checks

Verify all services are running:

```bash
# Check all service health
make dev.health

# Check specific services
docker-compose ps
docker-compose logs api
```

## Development Workflows

### Code Quality

Run quality checks before committing:

```bash
# Format code
ruff format .

# Lint code
ruff check . --fix

# Type checking
mypy packages/api/src

# Run all pre-commit hooks
pre-commit run --all-files
```

### Testing

Different levels of testing:

```bash
# Fast unit tests (recommended for TDD)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/unit/ -v

# Integration tests (require running services)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/integration/ -v

# Full test suite
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -v

# Test with coverage
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ --cov=stratmaster_api
```

### API Development

Work with the FastAPI application:

```bash
# Start development server with auto-reload
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload

# Start with debugging enabled
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --log-level debug

# Generate OpenAPI schema
python scripts/generate_openapi.py
```

Access development tools:
- **API Documentation**: http://127.0.0.1:8080/docs
- **Alternative Docs**: http://127.0.0.1:8080/redoc  
- **Health Check**: http://127.0.0.1:8080/healthz
- **Debug Config**: http://127.0.0.1:8080/debug/config/router/default (when debug enabled)

### Database Development

Work with database migrations and data:

```bash
# Run database migrations (when available)
make db.migrate

# Reset database to clean state  
make db.reset

# Load test data
make db.seed
```

## IDE Configuration

### VS Code Setup

Recommended extensions and settings:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "files.associations": {
    "*.yaml": "yaml"
  }
}
```

### PyCharm Setup

Configure project interpreter:
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment → `.venv/bin/python`
3. Enable pytest as test runner
4. Configure ruff as code formatter

## Troubleshooting

### Common Issues

**Virtual environment not activated:**
```bash
# Make sure you see (.venv) in your prompt
source .venv/bin/activate
```

**Port conflicts:**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill processes if needed
lsof -ti:8080 | xargs kill -9
```

**Import errors:**
```bash
# Ensure package is installed in development mode
pip install -e packages/api

# Check Python path
python -c "import stratmaster_api; print(stratmaster_api.__file__)"
```

**Permission errors:**
```bash
# Fix file permissions
chmod +x scripts/*.py
chmod +x .githooks/*
```

### Docker Issues

**Services not starting:**
```bash
# Clean up containers and volumes
docker-compose down -v
docker system prune -f

# Rebuild and restart
make dev.up --build
```

**Port conflicts in Docker:**
```bash
# Check Docker port mappings
docker-compose ps

# Use different ports if needed
export STRATMASTER_API_PORT=8081
make dev.up
```

## Next Steps

After successful setup:

1. **Run the tutorials**: Start with [Quick Start Tutorial](../tutorials/quickstart.md)
2. **Explore the API**: Check out [API Reference](../reference/api/)
3. **Understand architecture**: Read [Architecture Overview](../explanation/architecture.md)
4. **Deploy to staging**: Follow [Deployment Guide](deployment.md)

## Getting Help

- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md) for common issues
- **FAQ**: Check [FAQ](faq.md) for frequently asked questions
- **Community**: Join [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/IAmJonoBo/StratMaster/issues)