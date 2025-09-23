# StratMaster Architecture Overview

StratMaster is an AI-powered Brand Strategy platform built as a Python monorepo with FastAPI, multiple MCP (Model Context Protocol) servers, and comprehensive backing services. This document provides a high-level overview of the system architecture, component relationships, and key design principles.

## System Design Principles

- **Evidence-Grounded**: All strategic recommendations are backed by researched sources with provenance tracking
- **Multi-Agent Debate**: Uses constitutional AI with critic/adversary agents to validate outputs
- **MCP-First**: All tool and resource access follows the Model Context Protocol pattern
- **Self-Hosted**: Zero dependency on paid SaaS by default, with optional adapters
- **Multi-Tenant**: Designed for tenant isolation from data to compute resources

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI (Next) │    │  Mobile UI      │    │  API Clients    │
│   - Tri-pane    │    │  - Read-only    │    │  - OpenAI Tools │
│   - Desktop     │    │  - Approvals    │    │  - CLI Access   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   Gateway       │
                    │   - Orchestration│
                    │   - Auth/Authz  │
                    │   - Rate Limiting│
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Research MCP   │    │ Knowledge MCP   │    │  Router MCP     │
│  - Web Crawling │    │ - Vector Search │    │ - Model Routing │
│  - Provenance   │    │ - GraphRAG      │    │ - Policy Enforce│
│  - Source Valid │    │ - Reranking     │    │ - Struct Decode │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Evals MCP     │              │
         │              │  - Gate Enforce │              │
         │              │  - Metrics      │              │
         │              │  - Quality      │              │
         │              └─────────────────┘              │
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │ Expertise MCP   │              │
         │              │ - Discipline    │              │
         │              │   Evaluation    │              │
         │              │ - Expert Memos  │              │
         │              │ - Council Votes │              │
         │              └─────────────────┘              │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Compression MCP │
                    │ - LLMLingua     │
                    │ - Token Optim   │
                    └─────────────────┘
```

## Core Components

### API Gateway (`packages/api`)
- **FastAPI Application**: Central orchestration point for all requests
- **Pydantic v2 Models**: Type-safe data contracts for all domain objects
- **OpenAI Tool Integration**: Compatible tool schemas for external integrations
- **Idempotency**: All POST endpoints require `Idempotency-Key` headers

**Key Endpoints**:
- `POST /research/plan` - Generate research task lists
- `POST /research/run` - Execute research and return structured claims
- `POST /debate/run` - Multi-agent debate validation
- `POST /recommendations` - Generate decision briefs
- `POST /experts/evaluate` - Run expert discipline evaluation and return memos
- `POST /experts/vote` - Aggregate expert memos into weighted council vote
- `GET /providers/openai/tools` - OpenAI-compatible tool schemas

### MCP Servers (`packages/mcp-servers`)

#### Research MCP (`research-mcp`)
- **Web Crawling**: SearxNG integration with headless browser support
- **Provenance Tracking**: SHA-256 fingerprints and SAST timestamps
- **Source Validation**: Quality scoring and duplicate detection
- **Privacy**: PII sanitization and data handling policies

#### Knowledge MCP (`knowledge-mcp`) 
- **Vector Storage**: Qdrant for dense embeddings
- **Sparse Retrieval**: OpenSearch with SPLADE expansion
- **Graph Storage**: NebulaGraph for entity relationships
- **Hybrid Search**: Weighted combination of retrieval methods
- **Reranking**: BGE cross-encoder for result refinement

#### Router MCP (`router-mcp`)
- **Model Management**: Support for vLLM, Ollama, and cloud providers
- **Policy Enforcement**: Per-task guardrails and rate limiting
- **Structured Decoding**: JSON schema validation for outputs
- **Load Balancing**: Intelligent routing based on capacity and cost

#### Evals MCP (`evals-mcp`)
- **Quality Gates**: Automated evaluation before output approval
- **Metrics Collection**: Performance and accuracy tracking
- **Test Suites**: FActScore, TruthfulQA integration
- **A/B Testing**: Experiment framework for model comparisons

#### Expertise MCP (`expertise-mcp`)
- **Multi-Discipline Evaluation**: Psychology, design, communication, accessibility, brand science
- **Expert Memos**: Structured findings and recommendations per discipline
- **Council Voting**: Weighted aggregation of expert assessments
- **Local-Only Processing**: No external network access, tenant-isolated evaluation
- **Constitutional Integration**: Works with existing constitutional prompts and debate workflows

#### Compression MCP (`compression-mcp`)
- **LLMLingua Integration**: Intelligent prompt compression
- **Token Optimization**: Reduce costs while preserving quality
- **Task-Specific Tuning**: Optimized compression per use case

### Backing Services

#### Storage Layer
- **PostgreSQL**: Relational data, user management, audit logs
- **Qdrant**: Vector embeddings for semantic search
- **OpenSearch**: Full-text and sparse vector search
- **NebulaGraph**: Knowledge graph and entity relationships
- **MinIO**: Object storage for documents and media
- **DuckDB**: Analytics and data processing pipelines

#### Infrastructure Services  
- **Temporal**: Workflow orchestration and state management
- **Keycloak**: Identity and access management
- **Langfuse**: LLM observability and tracing
- **SearxNG**: Privacy-focused web search
- **vLLM/Ollama**: Local LLM inference serving

#### Observability
- **OpenTelemetry**: Distributed tracing across services
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Dashboards and visualization
- **Structured Logging**: JSON logs with correlation IDs

## Data Flow Architecture

### 1. Research Pipeline
```
User Query → Research MCP → SearxNG → Web Sources → 
Provenance Tracking → Knowledge MCP → Vector Storage → 
Hybrid Retrieval → Reranking → Structured Claims
```

### 2. Knowledge Fabric
```
Raw Documents → Ingestion → Chunking → 
Dense Vectors (ColBERT) → Sparse Vectors (SPLADE) →
Graph Extraction → Community Detection → 
Materialized Views → Retrieval Endpoints
```

### 3. Agent Debate Flow
```
Initial Recommendations → Constitutional Critic →
Adversarial Challenges → Evidence Validation →
Eval Gates → Quality Scoring → Final Decision Brief
```

## Security Architecture

### Multi-Tenant Isolation
- **Namespace Separation**: All resources prefixed with tenant IDs
- **Network Policies**: Kubernetes-level traffic isolation
- **Data Encryption**: At-rest and in-transit encryption
- **Access Controls**: RBAC through Keycloak integration

### Constitutional AI
- **Prompt Governance**: Version-controlled constitutional prompts
- **Safety Gates**: Multi-layer validation before output
- **Audit Trails**: Complete provenance from source to recommendation
- **PII Protection**: Automatic detection and sanitization

## Deployment Architecture

### Local Development (`docker-compose.yml`)
- Single-node deployment with all services
- Shared volumes for rapid development
- Debug endpoints enabled
- Sample data seeded

### Kubernetes Production (`helm/`)
- Multi-node deployment with HA configurations
- Sealed secrets for credential management
- Network policies for security
- Horizontal pod autoscaling
- Persistent volume claims for data

## Technology Stack

### Backend
- **Python 3.13+**: Core runtime with strict typing
- **FastAPI**: Async web framework with OpenAPI
- **Pydantic v2**: Data validation and serialization
- **LangGraph**: Multi-agent workflow orchestration
- **DSPy**: Program synthesis and optimization

### Storage
- **PostgreSQL 15+**: Primary database with JSONB support
- **Qdrant**: Vector database with quantization
- **OpenSearch**: Search engine with ML plugins
- **NebulaGraph**: Distributed graph database
- **MinIO**: S3-compatible object storage

### Infrastructure
- **Docker**: Containerization and local development
- **Kubernetes**: Production orchestration
- **Helm**: Package management and deployment
- **Temporal**: Durable workflow execution
- **OpenTelemetry**: Observability and tracing

### Quality & Tooling
- **Trunk**: Unified linting (ruff, black, mypy, hadolint)
- **pytest**: Test framework with fixtures and mocks  
- **pre-commit**: Git hook automation
- **GitHub Actions**: CI/CD pipelines

## Scalability Considerations

### Horizontal Scaling
- **Stateless Services**: All MCP servers designed for horizontal scaling
- **Event-Driven**: Async processing with message queues
- **Caching**: Multi-level caching with Redis/Memcached
- **CDN**: Static asset distribution

### Performance Optimization  
- **Connection Pooling**: Database connection management
- **Batch Processing**: Vectorization and bulk operations
- **Lazy Loading**: On-demand resource initialization
- **Compression**: Response and storage compression

### Cost Management
- **Resource Quotas**: Per-tenant resource limits
- **Auto-scaling**: CPU/memory-based scaling policies
- **Spot Instances**: Cost-effective compute for batch jobs
- **Model Optimization**: Quantization and pruning for inference

## Development Workflow

### Repository Structure
- **Monorepo**: Single repository with multiple packages
- **Package Isolation**: Independent versioning and testing
- **Shared Utilities**: Common libraries and configurations
- **Documentation**: Co-located with code for maintainability

### Testing Strategy
- **Unit Tests**: 95%+ coverage with fast execution
- **Integration Tests**: Component interaction validation
- **End-to-End Tests**: Full workflow testing with Playwright
- **Performance Tests**: Load testing and benchmarking

### Release Management
- **Semantic Versioning**: Automated version bumping
- **Feature Flags**: Progressive rollout capabilities
- **Blue-Green Deployment**: Zero-downtime deployments
- **Rollback**: Automated rollback on failure detection

## Next Steps

This architecture is designed to evolve with the project's needs. Key areas for future enhancement include:

1. **Multi-Region Deployment**: Geographic distribution for latency
2. **Advanced Security**: Zero-trust architecture and attestation
3. **ML Pipelines**: Automated model training and evaluation
4. **Federation**: Cross-tenant knowledge sharing capabilities

For detailed implementation guidance, see:
- [Development Guide](development.md)
- [Deployment Guide](deployment.md)
- [Infrastructure Guide](infrastructure.md)
- [Security Guide](security.md)