---
title: Environment Variables Reference
description: Complete reference for all StratMaster environment variables
version: 0.1.0
nav_order: 1
---

# Environment Variables Reference

This document provides a comprehensive reference for all environment variables used across the StratMaster platform. Variables are organized by service and include descriptions, default values, and configuration examples.

## Core Application Variables

### StratMaster API

```bash
# Application Configuration
STRATMASTER_ENV=development                    # Environment: development|staging|production
STRATMASTER_VERSION=0.1.0                     # Application version
STRATMASTER_LOG_LEVEL=INFO                    # Log level: DEBUG|INFO|WARNING|ERROR|CRITICAL
STRATMASTER_DEBUG=false                       # Enable debug mode
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=false      # Enable debug endpoints

# Server Configuration
STRATMASTER_API_HOST=127.0.0.1               # API server host
STRATMASTER_API_PORT=8080                     # API server port
STRATMASTER_API_WORKERS=4                     # Number of worker processes
STRATMASTER_API_TIMEOUT=30                    # Request timeout in seconds
STRATMASTER_API_MAX_REQUEST_SIZE=10485760     # Max request size in bytes (10MB)

# Security Configuration
STRATMASTER_JWT_SECRET=your-jwt-secret-key    # JWT signing secret
STRATMASTER_JWT_ALGORITHM=HS256               # JWT algorithm
STRATMASTER_JWT_EXPIRATION=3600               # JWT expiration in seconds
STRATMASTER_CORS_ORIGINS=http://localhost:3000,https://app.example.com
STRATMASTER_ALLOWED_HOSTS=localhost,api.example.com
STRATMASTER_SECURE_COOKIES=false              # Use secure cookies (HTTPS only)

# Rate Limiting
STRATMASTER_RATE_LIMIT_ENABLED=true           # Enable rate limiting
STRATMASTER_RATE_LIMIT_PER_MINUTE=100         # Requests per minute per client
STRATMASTER_RATE_LIMIT_BURST=50               # Burst capacity
```

### Database Configuration

```bash
# PostgreSQL Primary Database
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/stratmaster
STRATMASTER_DB_HOST=localhost                 # Database host
STRATMASTER_DB_PORT=5432                      # Database port
STRATMASTER_DB_NAME=stratmaster               # Database name
STRATMASTER_DB_USER=postgres                  # Database user
STRATMASTER_DB_PASSWORD=password              # Database password
STRATMASTER_DB_SSL_MODE=prefer                # SSL mode: disable|allow|prefer|require
STRATMASTER_DB_POOL_SIZE=20                   # Connection pool size
STRATMASTER_DB_MAX_OVERFLOW=30                # Maximum overflow connections
STRATMASTER_DB_POOL_TIMEOUT=30                # Pool timeout in seconds
STRATMASTER_DB_POOL_RECYCLE=3600              # Pool recycle time in seconds

# Read Replica (Optional)
STRATMASTER_DB_READ_URL=postgresql+psycopg://readonly:password@localhost:5433/stratmaster
STRATMASTER_DB_READ_POOL_SIZE=10              # Read replica pool size

# Database Migration
STRATMASTER_DB_AUTO_MIGRATE=false             # Auto-run migrations on startup
STRATMASTER_DB_MIGRATION_TIMEOUT=300          # Migration timeout in seconds
```

### Cache Configuration (Redis)

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0           # Redis connection URL
STRATMASTER_REDIS_HOST=localhost              # Redis host
STRATMASTER_REDIS_PORT=6379                   # Redis port
STRATMASTER_REDIS_DB=0                        # Redis database number
STRATMASTER_REDIS_PASSWORD=                   # Redis password (if required)
STRATMASTER_REDIS_SSL=false                   # Use SSL for Redis connection
STRATMASTER_REDIS_POOL_SIZE=20                # Connection pool size
STRATMASTER_REDIS_SOCKET_TIMEOUT=5            # Socket timeout in seconds
STRATMASTER_REDIS_SOCKET_CONNECT_TIMEOUT=5    # Connection timeout in seconds

# Cache Configuration
STRATMASTER_CACHE_TTL=3600                    # Default cache TTL in seconds
STRATMASTER_CACHE_PREFIX=stratmaster          # Cache key prefix
STRATMASTER_CACHE_ENABLED=true                # Enable caching
```

## MCP Server Variables

### Research MCP

```bash
# Server Configuration
RESEARCH_MCP_HOST=127.0.0.1                  # Research MCP host
RESEARCH_MCP_PORT=8081                        # Research MCP port
RESEARCH_MCP_LOG_LEVEL=INFO                   # Log level
RESEARCH_MCP_WORKERS=2                        # Number of workers
RESEARCH_MCP_TIMEOUT=30                       # Request timeout

# Search Configuration
RESEARCH_MCP_ALLOWLIST=*.example.com,trusted-site.org  # Allowed domains
RESEARCH_MCP_USE_NETWORK=true                 # Enable network access
RESEARCH_MCP_USER_AGENT=StratMaster Research Bot 1.0   # User agent string
RESEARCH_MCP_REQUEST_TIMEOUT=30               # HTTP request timeout
RESEARCH_MCP_MAX_CONCURRENT=5                 # Max concurrent requests
RESEARCH_MCP_RETRY_ATTEMPTS=3                 # Retry attempts for failed requests
RESEARCH_MCP_RETRY_DELAY=1                   # Delay between retries

# Cache Configuration
RESEARCH_MCP_CACHE_TTL=3600                   # Cache TTL in seconds
RESEARCH_MCP_CACHE_SIZE=1000                  # Max cache entries
RESEARCH_MCP_MAX_PAGES=10                     # Max pages to crawl per request

# Search Provider Configuration
BING_API_KEY=your-bing-api-key               # Bing Search API key
GOOGLE_API_KEY=your-google-api-key           # Google Search API key
GOOGLE_CX=your-google-cx                     # Google Custom Search CX
DUCKDUCKGO_ENABLED=true                      # Enable DuckDuckGo search
```

### Knowledge MCP

```bash
# Server Configuration
KNOWLEDGE_MCP_HOST=127.0.0.1                 # Knowledge MCP host
KNOWLEDGE_MCP_PORT=8082                       # Knowledge MCP port
KNOWLEDGE_MCP_LOG_LEVEL=INFO                  # Log level
KNOWLEDGE_MCP_WORKERS=2                       # Number of workers

# Vector Database (Qdrant)
QDRANT_URL=http://localhost:6333              # Qdrant server URL
QDRANT_API_KEY=                               # Qdrant API key (if required)
QDRANT_COLLECTION=stratmaster_knowledge       # Default collection name
QDRANT_TIMEOUT=30                             # Request timeout
QDRANT_RETRY_ATTEMPTS=3                       # Retry attempts
QDRANT_BATCH_SIZE=100                         # Batch size for operations

# Graph Database (NebulaGraph)
NEBULA_HOSTS=localhost:9669                   # NebulaGraph hosts
NEBULA_USERNAME=root                          # NebulaGraph username
NEBULA_PASSWORD=nebula                        # NebulaGraph password
NEBULA_SPACE=stratmaster_graph                # Graph space name
NEBULA_TIMEOUT=30                             # Connection timeout
NEBULA_POOL_SIZE=10                           # Connection pool size

# Search Configuration
OPENSEARCH_URL=http://localhost:9200          # OpenSearch URL
OPENSEARCH_USERNAME=admin                     # OpenSearch username
OPENSEARCH_PASSWORD=admin                     # OpenSearch password
OPENSEARCH_INDEX=stratmaster_search           # Default index name
OPENSEARCH_TIMEOUT=30                         # Request timeout
OPENSEARCH_USE_SSL=false                      # Use SSL connection
OPENSEARCH_VERIFY_CERTS=true                  # Verify SSL certificates

# ColBERT Configuration
COLBERT_MODEL_PATH=./models/colbert           # ColBERT model path
COLBERT_INDEX_PATH=./indexes/colbert          # ColBERT index path
COLBERT_DEVICE=cpu                            # Device: cpu|cuda
COLBERT_BATCH_SIZE=32                         # Batch size for inference

# SPLADE Configuration
SPLADE_MODEL_PATH=./models/splade             # SPLADE model path
SPLADE_DEVICE=cpu                             # Device: cpu|cuda
SPLADE_BATCH_SIZE=16                          # Batch size for inference

# BGE Reranker Configuration
BGE_RERANKER_MODEL=BAAI/bge-reranker-large    # BGE reranker model
BGE_RERANKER_DEVICE=cpu                       # Device: cpu|cuda
BGE_RERANKER_BATCH_SIZE=32                    # Batch size for reranking
```

### Router MCP

```bash
# Server Configuration
ROUTER_MCP_HOST=127.0.0.1                    # Router MCP host
ROUTER_MCP_PORT=8083                          # Router MCP port
ROUTER_MCP_LOG_LEVEL=INFO                     # Log level
ROUTER_MCP_WORKERS=2                          # Number of workers

# Service Discovery
SERVICE_DISCOVERY_ENABLED=true                # Enable service discovery
SERVICE_DISCOVERY_INTERVAL=30                 # Discovery interval in seconds
HEALTH_CHECK_INTERVAL=15                      # Health check interval in seconds
HEALTH_CHECK_TIMEOUT=5                        # Health check timeout in seconds

# Circuit Breaker Configuration
CIRCUIT_BREAKER_ENABLED=true                  # Enable circuit breakers
CIRCUIT_BREAKER_THRESHOLD=10                  # Failure threshold
CIRCUIT_BREAKER_TIMEOUT=60                    # Circuit breaker timeout in seconds
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=5         # Max calls in half-open state

# Load Balancing
DEFAULT_LOAD_BALANCING=round_robin            # Default algorithm: round_robin|least_connections|weighted|random
MAX_RETRIES_DEFAULT=2                         # Default max retries
REQUEST_TIMEOUT_DEFAULT=10000                 # Default request timeout in ms

# Service URLs
RESEARCH_MCP_URL=http://localhost:8081        # Research MCP URL
KNOWLEDGE_MCP_URL=http://localhost:8082       # Knowledge MCP URL
EVALS_MCP_URL=http://localhost:8084           # Evals MCP URL
EXPERTISE_MCP_URL=http://localhost:8085       # Expertise MCP URL
COMPRESSION_MCP_URL=http://localhost:8086     # Compression MCP URL
```

### Evals MCP

```bash
# Server Configuration
EVALS_MCP_HOST=127.0.0.1                     # Evals MCP host
EVALS_MCP_PORT=8084                           # Evals MCP port
EVALS_MCP_LOG_LEVEL=INFO                      # Log level
EVALS_MCP_WORKERS=2                           # Number of workers

# Evaluation Configuration
EVALS_TIMEOUT=60                              # Evaluation timeout in seconds
EVALS_MAX_CONCURRENT=3                        # Max concurrent evaluations
EVALS_CACHE_RESULTS=true                      # Cache evaluation results
EVALS_CACHE_TTL=7200                          # Cache TTL in seconds

# Quality Scoring
QUALITY_SCORE_WEIGHTS=credibility:0.35,relevance:0.25,recency:0.20,completeness:0.15,consistency:0.05
CREDIBILITY_MINIMUM_THRESHOLD=0.6             # Minimum credibility threshold
RELEVANCE_MINIMUM_THRESHOLD=0.7              # Minimum relevance threshold
QUALITY_GRADE_THRESHOLDS=A:0.85,B:0.75,C:0.65,D:0.50  # Quality grade thresholds
```

### Expertise MCP

```bash
# Server Configuration
EXPERTISE_MCP_HOST=127.0.0.1                 # Expertise MCP host
EXPERTISE_MCP_PORT=8085                       # Expertise MCP port
EXPERTISE_MCP_LOG_LEVEL=INFO                  # Log level
EXPERTISE_MCP_WORKERS=2                       # Number of workers

# Domain Expertise Configuration
EXPERTISE_DOMAINS=technology,finance,healthcare,manufacturing,retail  # Supported domains
EXPERTISE_CONFIDENCE_THRESHOLD=0.7            # Minimum confidence threshold
EXPERTISE_MAX_RECOMMENDATIONS=10              # Max recommendations per request
```

### Compression MCP

```bash
# Server Configuration
COMPRESSION_MCP_HOST=127.0.0.1               # Compression MCP host
COMPRESSION_MCP_PORT=8086                     # Compression MCP port
COMPRESSION_MCP_LOG_LEVEL=INFO                # Log level
COMPRESSION_MCP_WORKERS=2                     # Number of workers

# Compression Configuration
COMPRESSION_ALGORITHM=gzip                    # Compression algorithm: gzip|brotli|lz4
COMPRESSION_LEVEL=6                           # Compression level (1-9)
COMPRESSION_MIN_SIZE=1024                     # Minimum size to compress (bytes)
COMPRESSION_CACHE_TTL=3600                    # Compressed content cache TTL
```

## External Service Configuration

### Authentication (Keycloak)

```bash
# Keycloak Configuration
KEYCLOAK_SERVER_URL=http://localhost:8080     # Keycloak server URL
KEYCLOAK_REALM=stratmaster                    # Keycloak realm
KEYCLOAK_CLIENT_ID=stratmaster-api            # Client ID
KEYCLOAK_CLIENT_SECRET=your-client-secret     # Client secret
KEYCLOAK_ADMIN_USERNAME=admin                 # Admin username
KEYCLOAK_ADMIN_PASSWORD=admin                 # Admin password

# JWT Configuration
KEYCLOAK_JWT_AUDIENCE=stratmaster-api         # JWT audience
KEYCLOAK_JWT_ISSUER=http://localhost:8080/realms/stratmaster  # JWT issuer
KEYCLOAK_JWT_ALGORITHM=RS256                  # JWT algorithm
KEYCLOAK_JWKS_CACHE_TTL=3600                  # JWKS cache TTL in seconds
```

### Object Storage (MinIO)

```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000                 # MinIO endpoint
MINIO_ACCESS_KEY=stratmaster                  # Access key
MINIO_SECRET_KEY=stratmaster123               # Secret key
MINIO_SECURE=false                            # Use HTTPS
MINIO_REGION=us-east-1                        # Region
MINIO_BUCKET=stratmaster-data                 # Default bucket

# Storage Configuration
STORAGE_PROVIDER=minio                        # Storage provider: minio|s3|azure|gcs
STORAGE_UPLOAD_MAX_SIZE=104857600             # Max upload size (100MB)
STORAGE_ALLOWED_EXTENSIONS=pdf,doc,docx,txt,csv,json  # Allowed file extensions
```

### Observability

```bash
# OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317  # OTLP endpoint
OTEL_EXPORTER_OTLP_HEADERS=                   # OTLP headers
OTEL_SERVICE_NAME=stratmaster-api             # Service name
OTEL_SERVICE_VERSION=0.1.0                    # Service version
OTEL_RESOURCE_ATTRIBUTES=environment=development,team=platform  # Resource attributes

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-xxx                 # Langfuse public key
LANGFUSE_SECRET_KEY=sk-lf-xxx                 # Langfuse secret key
LANGFUSE_HOST=http://localhost:3000           # Langfuse host
LANGFUSE_ENABLED=true                         # Enable Langfuse tracing

# Prometheus Configuration
PROMETHEUS_ENABLED=true                       # Enable Prometheus metrics
PROMETHEUS_PORT=9090                          # Prometheus metrics port
PROMETHEUS_PATH=/metrics                      # Metrics endpoint path
METRICS_NAMESPACE=stratmaster                 # Metrics namespace
```

### Workflow Orchestration (Temporal)

```bash
# Temporal Configuration
TEMPORAL_HOST=localhost                       # Temporal server host
TEMPORAL_PORT=7233                            # Temporal server port
TEMPORAL_NAMESPACE=stratmaster                # Temporal namespace
TEMPORAL_TASK_QUEUE=stratmaster-tasks         # Default task queue
TEMPORAL_WORKER_CONCURRENCY=10                # Worker concurrency
TEMPORAL_WORKFLOW_TIMEOUT=3600                # Workflow timeout in seconds
TEMPORAL_ACTIVITY_TIMEOUT=300                 # Activity timeout in seconds
```

## AI/ML Configuration

### Language Models

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-xxx                         # OpenAI API key
OPENAI_ORG_ID=org-xxx                         # OpenAI organization ID
OPENAI_DEFAULT_MODEL=gpt-4                    # Default model
OPENAI_MAX_TOKENS=4096                        # Max tokens per request
OPENAI_TEMPERATURE=0.1                        # Temperature for generation
OPENAI_TIMEOUT=60                             # Request timeout in seconds

# Azure OpenAI Configuration (Alternative)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/  # Azure OpenAI endpoint
AZURE_OPENAI_API_KEY=your-api-key            # Azure OpenAI API key
AZURE_OPENAI_API_VERSION=2023-12-01-preview  # API version
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4           # Deployment name

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-xxx                  # Anthropic API key
ANTHROPIC_DEFAULT_MODEL=claude-3-opus-20240229  # Default model
ANTHROPIC_MAX_TOKENS=4096                     # Max tokens per request
ANTHROPIC_TIMEOUT=60                          # Request timeout

# Local Model Configuration
LOCAL_MODELS_PATH=./models                    # Local models directory
EMBEDDING_MODEL_PATH=./models/text-embedding-ada-002  # Embedding model path
EMBEDDING_DEVICE=cpu                          # Device for embeddings: cpu|cuda
EMBEDDING_BATCH_SIZE=32                       # Batch size for embeddings
```

### Multi-Agent Debate Configuration

```bash
# Debate Configuration
DEBATE_MAX_ROUNDS=5                           # Maximum debate rounds
DEBATE_CONSENSUS_THRESHOLD=0.8                # Consensus threshold
DEBATE_TIMEOUT=300                            # Debate timeout in seconds
DEBATE_AGENT_TIMEOUT=60                       # Individual agent timeout

# Agent Configuration
DEBATE_AGENTS=strategist,critic,adversary,financial_analyst  # Available agents
AGENT_STRATEGIST_MODEL=gpt-4                  # Strategist agent model
AGENT_CRITIC_MODEL=gpt-4                      # Critic agent model
AGENT_ADVERSARY_MODEL=gpt-4                   # Adversary agent model
AGENT_FINANCIAL_ANALYST_MODEL=gpt-4           # Financial analyst model

# Constitutional AI Configuration
CONSTITUTIONAL_AI_ENABLED=true                # Enable constitutional constraints
CONSTITUTIONAL_SAFETY_THRESHOLD=0.9           # Safety threshold
CONSTITUTIONAL_ACCURACY_THRESHOLD=0.8         # Accuracy threshold
CONSTITUTIONAL_BIAS_THRESHOLD=0.7             # Bias mitigation threshold
```

## Environment-Specific Configurations

### Development Environment

```bash
# Development-specific settings
STRATMASTER_ENV=development
STRATMASTER_DEBUG=true
STRATMASTER_LOG_LEVEL=DEBUG
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=true
STRATMASTER_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
STRATMASTER_DB_ECHO=true                      # Enable SQL query logging
STRATMASTER_CACHE_ENABLED=false               # Disable caching for development
```

### Staging Environment

```bash
# Staging-specific settings
STRATMASTER_ENV=staging
STRATMASTER_DEBUG=false
STRATMASTER_LOG_LEVEL=INFO
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=false
STRATMASTER_CORS_ORIGINS=https://staging.example.com
STRATMASTER_DB_SSL_MODE=require               # Require SSL in staging
STRATMASTER_SECURE_COOKIES=true               # Use secure cookies
```

### Production Environment

```bash
# Production-specific settings
STRATMASTER_ENV=production
STRATMASTER_DEBUG=false
STRATMASTER_LOG_LEVEL=WARNING
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=false
STRATMASTER_CORS_ORIGINS=https://app.example.com
STRATMASTER_ALLOWED_HOSTS=api.example.com
STRATMASTER_DB_SSL_MODE=require               # Require SSL in production
STRATMASTER_SECURE_COOKIES=true               # Use secure cookies
STRATMASTER_RATE_LIMIT_PER_MINUTE=50          # Stricter rate limiting
```

## Configuration Management

### Environment File Structure

```bash
# Recommended file structure
.env                        # Local development (gitignored)
.env.example               # Example configuration (committed)
.env.development           # Development defaults
.env.staging               # Staging configuration
.env.production            # Production configuration (secure)
```

### Loading Environment Variables

```python
# Python example using python-dotenv
from dotenv import load_dotenv
import os

# Load environment-specific configuration
env = os.getenv('STRATMASTER_ENV', 'development')
load_dotenv(f'.env.{env}')
load_dotenv('.env')  # Override with local settings

# Access variables
database_url = os.getenv('DATABASE_URL')
log_level = os.getenv('STRATMASTER_LOG_LEVEL', 'INFO')
```

### Docker Configuration

```yaml
# docker-compose.yml example
version: '3.9'
services:
  api:
    build: ./packages/api
    environment:
      - STRATMASTER_ENV=${STRATMASTER_ENV:-development}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    env_file:
      - .env
      - .env.${STRATMASTER_ENV:-development}
```

### Kubernetes Configuration

```yaml
# ConfigMap for non-sensitive configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: stratmaster-config
data:
  STRATMASTER_ENV: "production"
  STRATMASTER_LOG_LEVEL: "INFO"
  STRATMASTER_API_PORT: "8080"

---
# Secret for sensitive configuration
apiVersion: v1
kind: Secret
metadata:
  name: stratmaster-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://..."
  REDIS_URL: "redis://..."
  JWT_SECRET: "your-jwt-secret"
```

## Validation and Testing

### Configuration Validation

```python
# Configuration validation example
import os
from typing import Dict, Any
import sys

def validate_required_env_vars() -> Dict[str, Any]:
    """Validate required environment variables"""
    
    required_vars = {
        'DATABASE_URL': 'Database connection URL',
        'REDIS_URL': 'Redis connection URL',
        'STRATMASTER_JWT_SECRET': 'JWT signing secret',
    }
    
    missing_vars = []
    config = {}
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var}: {description}")
        else:
            config[var] = value
    
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        sys.exit(1)
    
    return config

# Validate on startup
config = validate_required_env_vars()
```

### Configuration Testing

```bash
# Test configuration loading
python -c "
import os
from dotenv import load_dotenv

load_dotenv('.env.example')
print('Configuration loaded successfully')
print(f'Environment: {os.getenv(\"STRATMASTER_ENV\")}')
print(f'Log Level: {os.getenv(\"STRATMASTER_LOG_LEVEL\")}')
print(f'Database: {os.getenv(\"DATABASE_URL\", \"Not configured\")}')
"
```

## Security Best Practices

### Sensitive Data Handling

1. **Never commit secrets**: Use `.env` files that are gitignored
2. **Use secrets management**: Employ proper secrets management in production
3. **Rotate secrets regularly**: Implement secret rotation policies
4. **Principle of least privilege**: Only provide necessary access
5. **Environment isolation**: Separate secrets by environment

### Environment Variable Security

```bash
# Example secure practices

# Use strong, unique secrets
STRATMASTER_JWT_SECRET=$(openssl rand -base64 64)

# Use environment-specific prefixes
PROD_DATABASE_URL=postgresql://...
STAGING_DATABASE_URL=postgresql://...

# Avoid default passwords
STRATMASTER_DB_PASSWORD=$(openssl rand -base64 32)

# Use secure defaults
STRATMASTER_SECURE_COOKIES=true
STRATMASTER_DB_SSL_MODE=require
```

## Troubleshooting

### Common Configuration Issues

1. **Missing environment variables**: Check `.env` file loading
2. **Database connection failures**: Verify database URL and credentials
3. **Service discovery issues**: Check service URLs and network connectivity
4. **Authentication failures**: Verify JWT secrets and Keycloak configuration
5. **Cache connection issues**: Check Redis URL and authentication

### Debug Configuration

```bash
# Enable debug logging to troubleshoot configuration
STRATMASTER_DEBUG=true
STRATMASTER_LOG_LEVEL=DEBUG

# Test database connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('Database connection successful')
"

# Test Redis connection
python -c "
import redis
import os
from urllib.parse import urlparse
url = urlparse(os.getenv('REDIS_URL'))
r = redis.Redis(host=url.hostname, port=url.port, db=url.path[1:])
r.ping()
print('Redis connection successful')
"
```

## Related Documentation

- [Configuration Management Guide](../how-to/configuration.md) - Configuration management practices
- [Security Hardening Guide](../../how-to/security-hardening.md) - Security configuration
- [Deployment Tutorial](../../tutorials/production-deployment.md) - Production deployment
- [Development Setup Guide](../../how-to/development-setup.md) - Development environment