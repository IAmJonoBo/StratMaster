# Contributing to StratMaster

Thanks for your interest in contributing to StratMaster! This guide covers everything you need to know to contribute effectively to the project.

## Getting Started

### Prerequisites

- **Python 3.13+**: Required for all Python components
- **Docker Desktop**: For full-stack development and testing
- **Git**: With signed commits recommended
- **Node.js 18+**: For web UI development (if working on frontend)

### First-Time Setup

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/your-username/StratMaster.git
cd StratMaster

# 3. Add upstream remote
git remote add upstream https://github.com/IAmJonoBo/StratMaster.git

# 4. Set up development environment
make bootstrap

# 5. Verify setup
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
# Expected: 19 passed in ~1s
```

## Development Workflow

### Branch Strategy

We use a trunk-based development model with short-lived feature branches:

```bash
# 1. Update your main branch
git checkout main
git pull upstream main

# 2. Create a feature branch
git checkout -b feature/your-feature-name

# 3. Make your changes
# ... develop, test, commit ...

# 4. Push and create PR
git push origin feature/your-feature-name
gh pr create --title "Brief description of changes"
```

### Commit Standards

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: type(scope): description
git commit -m "feat(api): add research plan endpoint"
git commit -m "fix(mcp): resolve vector search timeout"
git commit -m "docs: update deployment guide"
git commit -m "test: add integration tests for knowledge fabric"
```

**Types**:
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

## Code Quality Standards

### Linting and Formatting

StratMaster uses [Trunk](https://trunk.io) for unified code quality:

```bash
# Install trunk (one-time)
curl https://get.trunk.io -fsSL | bash

# Run all linters
trunk check --all

# Auto-fix issues  
trunk format

# Pre-commit hooks (included in make bootstrap)
.venv/bin/pre-commit install
```

**Supported Linters**:
- **Python**: ruff, black, mypy, bandit
- **JavaScript/TypeScript**: ESLint, Prettier
- **Infrastructure**: hadolint, yamllint, shellcheck
- **Documentation**: markdownlint

### Python Code Standards

```python
# Type hints are required
from typing import List, Dict, Optional
from pydantic import BaseModel

class ResearchRequest(BaseModel):
    """Research request with validation."""
    query: str
    max_sources: int = 10
    tenant_id: Optional[str] = None

def process_research(request: ResearchRequest) -> List[Dict[str, str]]:
    """Process research request and return structured results."""
    # Implementation here
    pass
```

**Requirements**:
- **Type Hints**: All functions must have type annotations
- **Docstrings**: Use Google style for public functions
- **Error Handling**: Use proper exception types with clear messages
- **Pydantic Models**: For all API contracts and data validation

### Testing Standards

We maintain high test coverage with multiple test types:

```bash
# Unit tests (fast, isolated)
pytest packages/api/tests/ -v

# Integration tests (with real services)
pytest tests/integration/ --live-services

# End-to-end tests (full workflows)
make test-docker
```

**Test Organization**:
```
tests/
├── unit/              # Fast, mocked tests
├── integration/       # Component interaction tests
├── e2e/              # Full workflow tests
├── fixtures/         # Test data and mocks
└── conftest.py       # Pytest configuration
```

**Writing Tests**:
```python
import pytest
from httpx import AsyncClient
from stratmaster_api.app import create_app

@pytest.mark.asyncio
async def test_research_endpoint():
    """Test research endpoint returns valid response."""
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/research/plan",
            json={"query": "AI trends 2024"},
            headers={"Idempotency-Key": "test-123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
```

## Pull Request Process

### Before Submitting

**Pre-submission Checklist**:
- [ ] **Tests Pass**: `PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q`
- [ ] **Linting**: `trunk check --all` passes
- [ ] **Type Checking**: `mypy packages/` passes
- [ ] **Documentation**: READMEs updated for changed components
- [ ] **Security**: No secrets or PII in commits
- [ ] **Breaking Changes**: Migration guide provided if needed

### PR Guidelines

**PR Title**: Use conventional commit format
```
feat(api): add multi-tenant research endpoint
fix(mcp): resolve timeout in vector search
docs: update deployment guide with new service
```

**PR Description Template**:
```markdown
## What Changed
Brief description of the changes made.

## Why
Explanation of the motivation and context.

## How
Technical details of the implementation approach.

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] README updated
- [ ] API docs updated
- [ ] Breaking changes documented

## Checklist
- [ ] Tests pass locally
- [ ] Linting passes
- [ ] No secrets in commits
- [ ] Proper commit messages
```

### Review Process

1. **Automated Checks**: CI must pass (tests, linting, Helm validation)
2. **Code Review**: At least one approval from a maintainer
3. **Security Review**: Required for security-sensitive changes
4. **Documentation Review**: Required for user-facing changes

**Review Criteria**:
- **Functionality**: Does it solve the intended problem?
- **Code Quality**: Is it readable, maintainable, and well-tested?
- **Performance**: Are there any performance implications?
- **Security**: Does it introduce security risks?
- **Architecture**: Does it fit the overall system design?

## Development Areas

### Core Components

**API Gateway** (`packages/api/`):
- FastAPI application with Pydantic v2 models
- OpenAPI documentation and tool schemas
- Authentication and authorization
- Request validation and response serialization

**MCP Servers** (`packages/mcp-servers/`):
- Research MCP: Web crawling and provenance
- Knowledge MCP: Vector search and GraphRAG
- Router MCP: Model routing and policies
- Evals MCP: Quality gates and metrics

**Specialized Packages**:
- **Retrieval**: ColBERT/SPLADE indexing
- **Rerankers**: BGE cross-encoder scoring
- **Agents**: LangGraph multi-agent workflows
- **UI**: Next.js web interface

### Infrastructure Components

**Storage Services** (`infra/`):
- PostgreSQL: Relational data and user management
- Qdrant: Vector embeddings and semantic search
- OpenSearch: Full-text and sparse vector search
- NebulaGraph: Knowledge graphs and entity relationships

**Platform Services**:
- Temporal: Workflow orchestration
- Keycloak: Identity and access management
- Langfuse: LLM observability and tracing
- MinIO: Object storage for documents

### Documentation

**User Documentation**:
- Architecture and system design
- Deployment and operations guides
- API reference and examples
- Troubleshooting procedures

**Developer Documentation**:
- Package-specific READMEs
- Code examples and tutorials
- Integration patterns
- Contributing guidelines

## Specialized Contribution Areas

### Machine Learning & AI

If contributing to ML/AI components:

- **Model Integration**: Follow MCP patterns for model access
- **Evaluation**: Include quality metrics and benchmarks  
- **Safety**: Implement constitutional AI constraints
- **Performance**: Consider inference latency and cost
- **Bias**: Test for and mitigate algorithmic bias

### Security

For security-related contributions:

- **Threat Modeling**: Update STRIDE analysis if needed
- **Penetration Testing**: Include security test scenarios
- **Compliance**: Ensure GDPR/SOC2 requirements met
- **Audit Logging**: All security events must be logged
- **Zero Trust**: Follow principle of least privilege

### Infrastructure

For infrastructure and deployment:

- **Kubernetes**: Follow cloud-native best practices
- **Monitoring**: Include appropriate metrics and alerts
- **Scaling**: Consider horizontal and vertical scaling
- **Disaster Recovery**: Document backup/restore procedures
- **Cost Optimization**: Consider resource efficiency

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be Respectful**: Treat all contributors with respect
- **Be Collaborative**: Work together and help others
- **Be Patient**: Support newcomers and different experience levels
- **Be Constructive**: Provide helpful feedback and suggestions

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code reviews and technical discussions
- **Security Issues**: Private disclosure via security policy

## Recognition

Contributors are recognized through:

- **Git History**: All commits include proper attribution
- **Release Notes**: Significant contributions highlighted
- **Contributors File**: Long-term contributors listed
- **Maintainer Status**: Active contributors may become maintainers

## Getting Help

**For Development Questions**:
1. Check the [Development Guide](docs/development.md)
2. Search existing GitHub Issues and Discussions
3. Create a new Discussion with the "question" label

**For Bugs**:
1. Check the [Troubleshooting Guide](docs/troubleshooting.md)
2. Search existing Issues
3. Create a new Issue with reproduction steps

**For Security Issues**:
- Follow the [Security Policy](SECURITY.md)
- Do not create public issues for security vulnerabilities

Thank you for contributing to StratMaster! Your contributions help build a better AI-powered strategy platform for everyone.
