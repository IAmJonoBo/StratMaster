---
title: Configuration Reference
description: Complete reference for all StratMaster configuration options
version: 0.1.0
platform: YAML, Environment Variables, Docker
nav_order: 1
parent: Configuration Reference
grand_parent: Reference
---

# Configuration Reference

StratMaster uses a flexible configuration system supporting environment variables, YAML files, and runtime configuration. This reference documents all configuration options with examples and best practices.

## Configuration Hierarchy

Configuration is loaded in the following order (later sources override earlier ones):

1. **Default values** (built into the application)
2. **YAML configuration files** (`configs/`)
3. **Environment variables** (`.env` files or system environment)
4. **Command line arguments** (for specific tools)
5. **Runtime configuration** (via debug endpoints in development)

## Environment Variables

### Core Application Settings

#### `STRATMASTER_ENV`
**Purpose**: Application environment mode  
**Default**: `development`  
**Options**: `development`, `staging`, `production`  
**Example**: `STRATMASTER_ENV=production`

```bash
# Development - enables debug features, relaxed security
STRATMASTER_ENV=development

# Staging - production-like but with additional logging
STRATMASTER_ENV=staging

# Production - strict security, optimized performance
STRATMASTER_ENV=production
```

#### `STRATMASTER_LOG_LEVEL`
**Purpose**: Logging verbosity  
**Default**: `INFO`  
**Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  
**Example**: `STRATMASTER_LOG_LEVEL=DEBUG`

#### `STRATMASTER_ENABLE_DEBUG_ENDPOINTS`
**Purpose**: Enable debug and configuration endpoints  
**Default**: `0` (disabled)  
**Options**: `0` (disabled), `1` (enabled)  
**Example**: `STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1`

**Security Note**: Only enable in development environments.

#### `STRATMASTER_RELOAD`
**Purpose**: Enable automatic code reloading  
**Default**: `false`  
**Options**: `true`, `false`  
**Example**: `STRATMASTER_RELOAD=true`

### Database Configuration

#### `STRATMASTER_API_DB_URL`
**Purpose**: PostgreSQL connection string  
**Format**: `postgresql+psycopg://user:password@host:port/database`  
**Example**: `postgresql+psycopg://stratmaster:secure_password@db.example.com:5432/stratmaster`

```bash
# Development (Docker Compose)
STRATMASTER_API_DB_URL=postgresql+psycopg://postgres:postgres@postgres:5432/stratmaster

# Production with connection pooling
STRATMASTER_API_DB_URL=postgresql+psycopg://user:pass@host:5432/db?pool_size=20&max_overflow=0

# Production with SSL
STRATMASTER_API_DB_URL=postgresql+psycopg://user:pass@host:5432/db?sslmode=require
```

#### `DATABASE_POOL_SIZE`
**Purpose**: Connection pool size  
**Default**: `20`  
**Range**: `1-100`  
**Example**: `DATABASE_POOL_SIZE=50`

#### `DATABASE_MAX_OVERFLOW`
**Purpose**: Maximum connections beyond pool size  
**Default**: `10`  
**Range**: `0-50`  
**Example**: `DATABASE_MAX_OVERFLOW=20`

### Cache & Session Storage

#### `REDIS_URL`
**Purpose**: Redis connection for caching and sessions  
**Format**: `redis://[user:password@]host:port/database`  
**Example**: `redis://user:password@redis.example.com:6379/0`

```bash
# Development (Docker Compose)
REDIS_URL=redis://redis:6379/0

# Production with authentication
REDIS_URL=redis://user:secure_password@redis.example.com:6379/0

# Production with TLS
REDIS_URL=rediss://user:password@redis.example.com:6380/0
```

#### `REDIS_POOL_SIZE`
**Purpose**: Redis connection pool size  
**Default**: `10`  
**Range**: `1-100`  
**Example**: `REDIS_POOL_SIZE=25`

### Vector Database (Qdrant)

#### `QDRANT_URL`
**Purpose**: Qdrant vector database endpoint  
**Format**: `http://host:port` or `https://host:port`  
**Example**: `https://qdrant.example.com:6333`

#### `QDRANT_API_KEY`
**Purpose**: Authentication for Qdrant Cloud  
**Format**: API key string  
**Example**: `QDRANT_API_KEY=qdr_1234567890abcdef`

```bash
# Development (Docker Compose)
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# Production (Qdrant Cloud)
QDRANT_URL=https://xyz-123.eu-west.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=qdr_your_api_key_here
```

### Search Engine (OpenSearch)

#### `OPENSEARCH_URL`
**Purpose**: OpenSearch cluster endpoint  
**Format**: `http://host:port` or `https://host:port`  
**Example**: `https://search.example.com:9200`

#### `OPENSEARCH_USERNAME`
**Purpose**: OpenSearch authentication username  
**Default**: `admin`  
**Example**: `OPENSEARCH_USERNAME=stratmaster_user`

#### `OPENSEARCH_PASSWORD`
**Purpose**: OpenSearch authentication password  
**Example**: `OPENSEARCH_PASSWORD=secure_password_123`

```bash
# Development (Docker Compose)
OPENSEARCH_URL=http://opensearch:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin

# Production (AWS OpenSearch)
OPENSEARCH_URL=https://search-stratmaster-abc123.us-east-1.es.amazonaws.com
OPENSEARCH_USERNAME=stratmaster_service
OPENSEARCH_PASSWORD=very_secure_password
```

### Graph Database (NebulaGraph)

#### `NEBULA_HOSTS`
**Purpose**: NebulaGraph cluster hosts  
**Format**: `host1:port1,host2:port2,host3:port3`  
**Example**: `nebula1.example.com:9669,nebula2.example.com:9669`

#### `NEBULA_USERNAME`
**Purpose**: NebulaGraph authentication username  
**Default**: `root`  
**Example**: `NEBULA_USERNAME=stratmaster_user`

#### `NEBULA_PASSWORD`
**Purpose**: NebulaGraph authentication password  
**Default**: `nebula`  
**Example**: `NEBULA_PASSWORD=secure_graph_password`

#### `NEBULA_SPACE`
**Purpose**: Default graph space name  
**Default**: `stratmaster`  
**Example**: `NEBULA_SPACE=production_knowledge`

### Object Storage (MinIO/S3)

#### `MINIO_ENDPOINT`
**Purpose**: MinIO/S3 endpoint  
**Format**: `host:port` (without protocol)  
**Example**: `s3.amazonaws.com` or `minio.example.com:9000`

#### `MINIO_ACCESS_KEY`
**Purpose**: S3 access key / MinIO username  
**Example**: `MINIO_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE`

#### `MINIO_SECRET_KEY`
**Purpose**: S3 secret key / MinIO password  
**Example**: `MINIO_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY`

#### `MINIO_SECURE`
**Purpose**: Use HTTPS for object storage  
**Default**: `false`  
**Options**: `true`, `false`  
**Example**: `MINIO_SECURE=true`

```bash
# Development (Docker Compose MinIO)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=stratmaster
MINIO_SECRET_KEY=stratmaster123
MINIO_SECURE=false

# Production (AWS S3)
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=AKIA...
MINIO_SECRET_KEY=...
MINIO_SECURE=true

# Production (MinIO cluster)
MINIO_ENDPOINT=storage.example.com:9000
MINIO_ACCESS_KEY=service_account
MINIO_SECRET_KEY=very_secure_key
MINIO_SECURE=true
```

### Observability & Monitoring

#### `LANGFUSE_PUBLIC_KEY`
**Purpose**: Langfuse LLM observability public key  
**Format**: `pk-lf-*`  
**Example**: `LANGFUSE_PUBLIC_KEY=pk-lf-1234567890abcdef`

#### `LANGFUSE_SECRET_KEY`
**Purpose**: Langfuse LLM observability secret key  
**Format**: `sk-lf-*`  
**Example**: `LANGFUSE_SECRET_KEY=sk-lf-fedcba0987654321`

#### `LANGFUSE_HOST`
**Purpose**: Langfuse server endpoint  
**Default**: `https://cloud.langfuse.com`  
**Example**: `LANGFUSE_HOST=https://langfuse.example.com`

```bash
# Development (Docker Compose)
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=pk-lf-dev-key
LANGFUSE_SECRET_KEY=sk-lf-dev-secret

# Production (Langfuse Cloud)
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-prod-key
LANGFUSE_SECRET_KEY=sk-lf-prod-secret
```

#### `OTEL_EXPORTER_OTLP_ENDPOINT`
**Purpose**: OpenTelemetry collector endpoint  
**Format**: `http://host:port` or `https://host:port`  
**Example**: `https://otel.example.com:4317`

#### `GRAFANA_URL`
**Purpose**: Grafana dashboard URL  
**Example**: `GRAFANA_URL=https://monitoring.example.com:3000`

#### `PROMETHEUS_URL`
**Purpose**: Prometheus metrics endpoint  
**Example**: `PROMETHEUS_URL=https://metrics.example.com:9090`

### AI Model Providers

#### `OPENAI_API_KEY`
**Purpose**: OpenAI API authentication  
**Format**: `sk-*`  
**Example**: `OPENAI_API_KEY=sk-1234567890abcdef...`

**Security Note**: This is optional and disabled by default for privacy.

#### `OPENAI_BASE_URL`
**Purpose**: OpenAI API base URL (for proxies/alternatives)  
**Default**: `https://api.openai.com/v1`  
**Example**: `OPENAI_BASE_URL=https://your-proxy.example.com/v1`

#### `ANTHROPIC_API_KEY`
**Purpose**: Anthropic Claude API authentication  
**Format**: `sk-ant-*`  
**Example**: `ANTHROPIC_API_KEY=sk-ant-api03-...`

### Authentication & Security

#### `KEYCLOAK_SERVER_URL`
**Purpose**: Keycloak authentication server  
**Example**: `KEYCLOAK_SERVER_URL=https://auth.example.com`

#### `KEYCLOAK_REALM`
**Purpose**: Keycloak realm name  
**Default**: `stratmaster`  
**Example**: `KEYCLOAK_REALM=production`

#### `KEYCLOAK_CLIENT_ID`
**Purpose**: Keycloak OAuth client ID  
**Example**: `KEYCLOAK_CLIENT_ID=stratmaster-api`

#### `KEYCLOAK_CLIENT_SECRET`
**Purpose**: Keycloak OAuth client secret  
**Example**: `KEYCLOAK_CLIENT_SECRET=your-client-secret-here`

```bash
# Production Keycloak setup
KEYCLOAK_SERVER_URL=https://auth.company.com
KEYCLOAK_REALM=company-realm
KEYCLOAK_CLIENT_ID=stratmaster-production
KEYCLOAK_CLIENT_SECRET=very-secure-client-secret
```

### MCP Server Configuration

#### Research MCP Settings
```bash
RESEARCH_MCP_ALLOWLIST=example.com,trusted-site.org
RESEARCH_MCP_CACHE_DIR=/app/cache
RESEARCH_MCP_ENABLE_NETWORK=1
SEARXNG_ENDPOINT=http://searxng:8080/search
```

#### Knowledge MCP Settings
```bash
KNOWLEDGE_MCP_EMBEDDING_MODEL=text-embedding-ada-002
KNOWLEDGE_MCP_SIMILARITY_THRESHOLD=0.7
KNOWLEDGE_MCP_MAX_RESULTS=50
```

#### Router MCP Settings  
```bash
ROUTER_MCP_DEFAULT_MODEL=gpt-4
ROUTER_MCP_FALLBACK_MODEL=gpt-3.5-turbo
ROUTER_MCP_MAX_RETRIES=3
ROUTER_MCP_TIMEOUT_SECONDS=30
```

## YAML Configuration Files

StratMaster supports YAML configuration files in the `configs/` directory for complex configurations.

### Router Configuration (`configs/router/default.yaml`)

```yaml
# Router MCP configuration
providers:
  openai:
    enabled: false  # Disabled by default for privacy
    models:
      - gpt-4
      - gpt-3.5-turbo
      - text-embedding-ada-002
    rate_limits:
      requests_per_minute: 500
      tokens_per_minute: 120000
  
  local:
    enabled: true
    default: true
    models:
      - mixtral-8x7b-instruct
      - llama-2-13b-chat
    endpoint: http://ollama:11434

routing:
  default_provider: local
  fallback_provider: openai
  selection_strategy: cost_optimized
  
policies:
  max_tokens: 4096
  temperature: 0.7
  privacy:
    send_raw_docs: false
    max_snippet_chars: 2000
```

### Retrieval Configuration (`configs/retrieval/hybrid.yaml`)

```yaml
# Hybrid retrieval configuration
colbert:
  index_path: /data/colbert/index
  model_name: colbert-ir/colbertv2.0
  similarity_threshold: 0.75
  max_results: 100

splade:
  index_name: splade_index
  model_name: naver/splade-cocondenser-ensembledistil
  expansion_threshold: 0.1
  max_results: 100

hybrid:
  colbert_weight: 0.7
  splade_weight: 0.3
  rerank: true
  rerank_top_k: 20
  final_top_k: 10
```

### Evaluation Configuration (`configs/evals/thresholds.yaml`)

```yaml
# Quality evaluation thresholds
thresholds:
  factscore:
    minimum: 0.75
    target: 0.85
    
  truthfulness:
    minimum: 0.80
    target: 0.90
    
  coherence:
    minimum: 0.70
    target: 0.85
    
  constitutional_compliance:
    minimum: 0.90
    target: 0.95

gates:
  evidence_quality:
    min_sources_per_claim: 2
    credibility_threshold: 0.7
    
  bias_detection:
    max_bias_score: 0.3
    perspective_diversity_min: 0.6
    
  safety:
    harmful_content_threshold: 0.1
    pii_detection_threshold: 0.9
```

### Expert Configuration (`configs/experts/disciplines.yaml`)

```yaml
# Expert Council discipline definitions
disciplines:
  customer_experience:
    name: "Customer Experience Expert"
    expertise:
      - user_research
      - journey_mapping
      - satisfaction_metrics
      - retention_analysis
    evaluation_frameworks:
      - jobs_to_be_done
      - customer_effort_score
      - net_promoter_score
    
  technology_implementation:
    name: "Technology Implementation Specialist"
    expertise:
      - system_architecture
      - integration_complexity
      - technical_risk_assessment
      - scalability_planning
    evaluation_frameworks:
      - technology_readiness_level
      - implementation_maturity_model
      - risk_assessment_matrix
    
  financial_analysis:
    name: "Financial Analysis Expert"
    expertise:
      - roi_calculation
      - cost_benefit_analysis
      - budget_planning
      - financial_modeling
    evaluation_frameworks:
      - net_present_value
      - internal_rate_return
      - payback_period
```

## Docker Compose Configuration

### Development Configuration

```yaml
# docker-compose.yml (excerpt)
version: "3.9"

services:
  api:
    build: ./packages/api
    ports:
      - "8080:8080"
    environment:
      STRATMASTER_ENV: development
      STRATMASTER_LOG_LEVEL: DEBUG
      STRATMASTER_ENABLE_DEBUG_ENDPOINTS: "1"
      STRATMASTER_API_DB_URL: postgresql+psycopg://postgres:postgres@postgres:5432/stratmaster
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      OPENSEARCH_URL: http://opensearch:9200
    depends_on:
      - postgres
      - redis
      - qdrant
      - opensearch
```

### Production Configuration

```yaml
# docker-compose.prod.yml (excerpt)
version: "3.9"

services:
  api:
    image: stratmaster/api:0.1.0
    ports:
      - "8080:8080"
    environment:
      STRATMASTER_ENV: production
      STRATMASTER_LOG_LEVEL: INFO
      STRATMASTER_API_DB_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      QDRANT_URL: ${QDRANT_URL}
      QDRANT_API_KEY: ${QDRANT_API_KEY}
    secrets:
      - db_password
      - redis_password
      - qdrant_api_key
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Kubernetes Configuration

### ConfigMap Example

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: stratmaster-config
data:
  STRATMASTER_ENV: "production"
  STRATMASTER_LOG_LEVEL: "INFO"
  QDRANT_URL: "https://qdrant.example.com:6333"
  OPENSEARCH_URL: "https://opensearch.example.com:9200"
  LANGFUSE_HOST: "https://langfuse.example.com"
```

### Secret Example

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: stratmaster-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@host:5432/db"
  REDIS_URL: "redis://user:pass@host:6379/0"
  QDRANT_API_KEY: "qdr_your_key_here"
  LANGFUSE_SECRET_KEY: "sk-lf-your-secret"
```

## Configuration Best Practices

### Security
- **Never commit secrets** to version control
- **Use environment variables** for sensitive data in production
- **Rotate credentials** regularly
- **Use least privilege** for service accounts
- **Enable TLS** for all external connections

### Performance
- **Tune connection pools** based on expected load
- **Configure caching** appropriately for your use case
- **Set appropriate timeouts** to prevent resource exhaustion
- **Monitor resource usage** and adjust limits accordingly

### Reliability
- **Configure health checks** for all services
- **Set up monitoring** and alerting
- **Use circuit breakers** for external service calls  
- **Implement graceful degradation** when services are unavailable

### Development vs. Production

| Setting | Development | Production |
|---------|-------------|------------|
| **Log Level** | `DEBUG` | `INFO` |
| **Debug Endpoints** | Enabled | Disabled |
| **Auto-reload** | Enabled | Disabled |
| **Database Pool** | Small (5-10) | Large (20-50) |
| **Cache TTL** | Short (1min) | Long (1hr) |
| **Rate Limits** | Generous | Strict |
| **SSL/TLS** | Optional | Required |

## Environment-Specific Examples

### Local Development (.env)
```bash
# Local development environment
STRATMASTER_ENV=development
STRATMASTER_LOG_LEVEL=DEBUG
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1

# Local services (Docker Compose)
STRATMASTER_API_DB_URL=postgresql+psycopg://postgres:postgres@localhost:5432/stratmaster
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
OPENSEARCH_URL=http://localhost:9200

# Disable external AI services for privacy
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

### Staging Environment
```bash
# Staging environment
STRATMASTER_ENV=staging
STRATMASTER_LOG_LEVEL=INFO
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1

# Managed services
STRATMASTER_API_DB_URL=postgresql+psycopg://user:pass@staging-db.internal:5432/stratmaster
REDIS_URL=redis://user:pass@staging-cache.internal:6379/0
QDRANT_URL=https://staging-vector.internal:6333
QDRANT_API_KEY=qdr_staging_key

# Observability
LANGFUSE_HOST=https://staging-langfuse.internal
LANGFUSE_PUBLIC_KEY=pk-lf-staging
LANGFUSE_SECRET_KEY=sk-lf-staging
```

### Production Environment
```bash
# Production environment
STRATMASTER_ENV=production
STRATMASTER_LOG_LEVEL=WARNING
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=0

# Production databases with SSL
STRATMASTER_API_DB_URL=postgresql+psycopg://user:pass@prod-db.internal:5432/stratmaster?sslmode=require
REDIS_URL=rediss://user:pass@prod-cache.internal:6380/0
QDRANT_URL=https://vector-db.internal:6333
QDRANT_API_KEY=${QDRANT_API_KEY_SECRET}

# Production observability
LANGFUSE_HOST=https://observability.internal
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-collector.internal:4317

# Authentication
KEYCLOAK_SERVER_URL=https://auth.company.com
KEYCLOAK_REALM=production
KEYCLOAK_CLIENT_ID=stratmaster-prod
KEYCLOAK_CLIENT_SECRET=${KEYCLOAK_CLIENT_SECRET}
```

## Troubleshooting Configuration

### Common Issues

**Database Connection Errors:**
```bash
# Check connection string format
STRATMASTER_API_DB_URL=postgresql+psycopg://user:pass@host:port/database

# Test connection
psql "postgresql://user:pass@host:port/database" -c "SELECT 1;"
```

**Redis Connection Issues:**
```bash
# Check Redis URL format
REDIS_URL=redis://user:pass@host:port/database

# Test connection
redis-cli -u redis://user:pass@host:port ping
```

**Service Discovery Problems:**
```bash
# Check service names in Docker Compose
docker compose ps
docker compose logs service-name

# Test connectivity
docker compose exec api curl http://redis:6379
```

**Configuration Loading:**
```bash
# Enable debug mode to see configuration loading
STRATMASTER_LOG_LEVEL=DEBUG

# Check configuration via debug endpoint (development only)
curl http://localhost:8080/debug/config/router/default_model
```

## Migration and Upgrade Notes

When upgrading StratMaster versions:

1. **Review configuration changes** in the changelog
2. **Update environment variables** as needed
3. **Migrate configuration files** to new formats
4. **Test configuration** in staging environment first
5. **Monitor for errors** after deployment

---

<div class="warning">
<p><strong>⚠️ Security Warning:</strong> Never commit sensitive configuration values like passwords, API keys, or connection strings to version control. Use environment variables, secret management systems, or encrypted configuration files in production.</p>
</div>