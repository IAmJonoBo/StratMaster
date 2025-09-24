# Environment Variables Reference

Complete reference for all environment variables used in StratMaster. Variables are organized by functional area and include descriptions, defaults, and usage examples.

## Core Configuration {#core}

### Database Configuration

#### `DATABASE_URL`
Primary database connection string for PostgreSQL.

- **Required**: Yes
- **Format**: `postgresql://user:password@host:port/database`
- **Example**: `postgresql://stratmaster:secret@localhost:5432/stratmaster`
- **Used by**: Gateway API, MCP services

```bash
# Development
DATABASE_URL=postgresql://stratmaster:dev_password@localhost:5432/stratmaster_dev

# Production (use secrets management)
DATABASE_URL=postgresql://stratmaster:${DB_PASSWORD}@db-cluster:5432/stratmaster_prod
```

#### `DATABASE_POOL_SIZE`
Connection pool size for database connections.

- **Required**: No
- **Default**: `10`
- **Range**: `1-100`
- **Example**: `DATABASE_POOL_SIZE=20`

#### `DATABASE_MAX_OVERFLOW`
Maximum overflow connections beyond pool size.

- **Required**: No  
- **Default**: `20`
- **Range**: `0-50`
- **Example**: `DATABASE_MAX_OVERFLOW=30`

### Vector Database Configuration

#### `QDRANT_URL`
Qdrant vector database connection URL.

- **Required**: Yes
- **Format**: `http://host:port` or `https://host:port`
- **Example**: `QDRANT_URL=http://localhost:6333`
- **Used by**: Knowledge MCP, Research MCP

```bash
# Local development
QDRANT_URL=http://localhost:6333

# Production cluster
QDRANT_URL=http://qdrant-cluster.internal:6333
```

#### `QDRANT_API_KEY`
API key for Qdrant authentication (if required).

- **Required**: No (depends on Qdrant setup)
- **Example**: `QDRANT_API_KEY=your-api-key-here`
- **Security**: Store in secrets management system

### Cache Configuration

#### `REDIS_URL`
Redis connection string for caching and sessions.

- **Required**: Yes
- **Format**: `redis://[user:password@]host:port[/database]`
- **Example**: `REDIS_URL=redis://localhost:6379/0`
- **Used by**: Gateway API, Router MCP

```bash
# Local development
REDIS_URL=redis://localhost:6379/0

# Production with authentication
REDIS_URL=redis://user:password@redis-cluster:6379/0

# Redis Sentinel
REDIS_URL=redis-sentinel://sentinel1:26379,sentinel2:26379/mymaster
```

#### `REDIS_TTL_DEFAULT`
Default TTL for cached items in seconds.

- **Required**: No
- **Default**: `3600` (1 hour)
- **Example**: `REDIS_TTL_DEFAULT=7200`

## Authentication Configuration {#authentication}

### Keycloak Configuration

#### `KEYCLOAK_URL`
Keycloak server URL for authentication.

- **Required**: Yes (production)
- **Format**: `http://host:port` or `https://host:port`
- **Example**: `KEYCLOAK_URL=http://localhost:8080`
- **Used by**: Gateway API

```bash
# Development
KEYCLOAK_URL=http://localhost:8080

# Production
KEYCLOAK_URL=https://auth.stratmaster.com
```

#### `KEYCLOAK_REALM`
Keycloak realm name for StratMaster.

- **Required**: Yes (when using Keycloak)
- **Default**: `stratmaster`
- **Example**: `KEYCLOAK_REALM=stratmaster-prod`

#### `KEYCLOAK_CLIENT_ID`
Keycloak client ID for the API service.

- **Required**: Yes (when using Keycloak)
- **Example**: `KEYCLOAK_CLIENT_ID=stratmaster-api`

#### `KEYCLOAK_CLIENT_SECRET`
Keycloak client secret for the API service.

- **Required**: Yes (when using Keycloak)
- **Example**: `KEYCLOAK_CLIENT_SECRET=your-client-secret`
- **Security**: Store in secrets management system

### JWT Configuration

#### `JWT_SECRET`
Secret key for JWT token signing and verification.

- **Required**: Yes
- **Format**: Long, random string (minimum 32 characters)
- **Example**: `JWT_SECRET=your-super-secret-jwt-key-here-make-it-long`
- **Security**: Generate cryptographically secure random string

```bash
# Generate secure JWT secret
JWT_SECRET=$(openssl rand -hex 32)
```

#### `JWT_ALGORITHM`
Algorithm used for JWT token signing.

- **Required**: No
- **Default**: `HS256`
- **Options**: `HS256`, `HS384`, `HS512`, `RS256`, `RS384`, `RS512`
- **Example**: `JWT_ALGORITHM=HS256`

#### `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
Access token expiration time in minutes.

- **Required**: No
- **Default**: `30`
- **Range**: `5-1440` (5 minutes to 24 hours)
- **Example**: `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60`

#### `JWT_REFRESH_TOKEN_EXPIRE_DAYS`
Refresh token expiration time in days.

- **Required**: No
- **Default**: `7`
- **Range**: `1-30`
- **Example**: `JWT_REFRESH_TOKEN_EXPIRE_DAYS=14`

### Session Configuration

#### `SESSION_SECRET_KEY`
Secret key for session encryption.

- **Required**: Yes
- **Format**: Long, random string (minimum 32 characters)
- **Example**: `SESSION_SECRET_KEY=your-session-secret-key`
- **Security**: Different from JWT_SECRET

#### `SESSION_TIMEOUT`
Session timeout in seconds.

- **Required**: No
- **Default**: `3600` (1 hour)
- **Example**: `SESSION_TIMEOUT=7200`

## Service Configuration

### API Gateway Settings

#### `STRATMASTER_ENV`
Environment context for the application.

- **Required**: No
- **Default**: `development`
- **Options**: `development`, `staging`, `production`
- **Example**: `STRATMASTER_ENV=production`

#### `API_HOST`
Host binding for the API server.

- **Required**: No
- **Default**: `127.0.0.1`
- **Example**: `API_HOST=0.0.0.0`
- **Security**: Use `127.0.0.1` for single-host, `0.0.0.0` for containers

#### `API_PORT`
Port number for the API server.

- **Required**: No
- **Default**: `8080`
- **Example**: `API_PORT=8080`

#### `API_WORKERS`
Number of worker processes for the API server.

- **Required**: No
- **Default**: `1`
- **Recommendation**: CPU cores × 2
- **Example**: `API_WORKERS=4`

### MCP Service Ports

#### `RESEARCH_MCP_PORT`
Port for Research MCP service.

- **Required**: No
- **Default**: `8081`
- **Example**: `RESEARCH_MCP_PORT=8081`

#### `KNOWLEDGE_MCP_PORT`  
Port for Knowledge MCP service.

- **Required**: No
- **Default**: `8082`
- **Example**: `KNOWLEDGE_MCP_PORT=8082`

#### `ROUTER_MCP_PORT`
Port for Router MCP service.

- **Required**: No
- **Default**: `8083`
- **Example**: `ROUTER_MCP_PORT=8083`

#### `EVALS_MCP_PORT`
Port for Evals MCP service.

- **Required**: No
- **Default**: `8084`
- **Example**: `EVALS_MCP_PORT=8084`

#### `COMPRESSION_MCP_PORT`
Port for Compression MCP service.

- **Required**: No
- **Default**: `8085`
- **Example**: `COMPRESSION_MCP_PORT=8085`

## Observability Configuration {#observability}

### Logging Configuration

#### `LOG_LEVEL`
Logging verbosity level.

- **Required**: No
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`
- **Example**: `LOG_LEVEL=INFO`

#### `LOG_FORMAT`
Log message format.

- **Required**: No
- **Default**: `text`
- **Options**: `text`, `json`, `structured`
- **Example**: `LOG_FORMAT=json`

#### `LOG_FILE`
Log file path (if file logging enabled).

- **Required**: No
- **Default**: None (stdout only)
- **Example**: `LOG_FILE=/app/logs/stratmaster.log`

### Tracing Configuration

#### `OPENTELEMETRY_ENDPOINT`
OpenTelemetry collector endpoint for tracing.

- **Required**: No
- **Format**: `http://host:port/v1/traces`
- **Example**: `OPENTELEMETRY_ENDPOINT=http://jaeger:14268/api/traces`

#### `OTEL_SERVICE_NAME`
Service name for OpenTelemetry traces.

- **Required**: No
- **Default**: `stratmaster-api`
- **Example**: `OTEL_SERVICE_NAME=stratmaster-gateway`

#### `OTEL_RESOURCE_ATTRIBUTES`
Additional resource attributes for traces.

- **Required**: No
- **Format**: Comma-separated key=value pairs
- **Example**: `OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=production`

### Metrics Configuration

#### `PROMETHEUS_METRICS_ENABLED`
Enable Prometheus metrics endpoint.

- **Required**: No
- **Default**: `true`
- **Options**: `true`, `false`
- **Example**: `PROMETHEUS_METRICS_ENABLED=true`

#### `METRICS_PORT`
Port for metrics endpoint.

- **Required**: No
- **Default**: `9090`
- **Example**: `METRICS_PORT=9090`

### Langfuse Configuration

#### `LANGFUSE_URL`
Langfuse server URL for LLM observability.

- **Required**: No
- **Format**: `http://host:port` or `https://host:port`
- **Example**: `LANGFUSE_URL=http://localhost:3000`

#### `LANGFUSE_PUBLIC_KEY`
Langfuse public key for authentication.

- **Required**: No (when using Langfuse)
- **Example**: `LANGFUSE_PUBLIC_KEY=pk_your_public_key`

#### `LANGFUSE_SECRET_KEY`
Langfuse secret key for authentication.

- **Required**: No (when using Langfuse)
- **Example**: `LANGFUSE_SECRET_KEY=sk_your_secret_key`
- **Security**: Store in secrets management system

## Feature Flags {#feature-flags}

### Development Features

#### `STRATMASTER_ENABLE_DEBUG_ENDPOINTS`
Enable debug configuration endpoints.

- **Required**: No
- **Default**: `0` (disabled)
- **Options**: `0` (disabled), `1` (enabled)
- **Example**: `STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1`
- **Security**: Never enable in production

#### `ENABLE_API_DOCS`
Enable OpenAPI documentation endpoints.

- **Required**: No
- **Default**: `1` (enabled)
- **Options**: `0` (disabled), `1` (enabled)
- **Example**: `ENABLE_API_DOCS=1`

#### `ENABLE_CORS`
Enable CORS (Cross-Origin Resource Sharing).

- **Required**: No
- **Default**: `0` (disabled)
- **Options**: `0` (disabled), `1` (enabled)
- **Example**: `ENABLE_CORS=1`

#### `CORS_ORIGINS`
Allowed CORS origins (when CORS enabled).

- **Required**: No (when CORS enabled)
- **Format**: Comma-separated URLs
- **Example**: `CORS_ORIGINS=http://localhost:3000,https://app.stratmaster.com`

### Experimental Features

#### `ENABLE_EXPERIMENTAL_FEATURES`
Enable experimental and beta features.

- **Required**: No
- **Default**: `0` (disabled)
- **Options**: `0` (disabled), `1` (enabled)
- **Example**: `ENABLE_EXPERIMENTAL_FEATURES=1`

#### `ENABLE_ML_TRAINING`
Enable machine learning model training features.

- **Required**: No
- **Default**: `0` (disabled)
- **Options**: `0` (disabled), `1` (enabled)
- **Example**: `ENABLE_ML_TRAINING=1`

#### `ENABLE_ADVANCED_ANALYTICS`
Enable advanced analytics and reporting.

- **Required**: No
- **Default**: `0` (disabled)
- **Options**: `0` (disabled), `1` (enabled)
- **Example**: `ENABLE_ADVANCED_ANALYTICS=1`

## Performance Configuration {#performance}

### Request Handling

#### `REQUEST_TIMEOUT`
Default request timeout in seconds.

- **Required**: No
- **Default**: `30`
- **Range**: `5-300`
- **Example**: `REQUEST_TIMEOUT=60`

#### `MAX_REQUEST_SIZE`
Maximum request body size.

- **Required**: No
- **Default**: `10MB`
- **Format**: Size with unit (KB, MB, GB)
- **Example**: `MAX_REQUEST_SIZE=50MB`

#### `MAX_CONCURRENT_REQUESTS`
Maximum concurrent requests per service.

- **Required**: No
- **Default**: `100`
- **Range**: `10-1000`
- **Example**: `MAX_CONCURRENT_REQUESTS=200`

### Database Performance

#### `DB_CONNECTION_TIMEOUT`
Database connection timeout in seconds.

- **Required**: No
- **Default**: `10`
- **Range**: `1-60`
- **Example**: `DB_CONNECTION_TIMEOUT=15`

#### `DB_QUERY_TIMEOUT`
Database query timeout in seconds.

- **Required**: No
- **Default**: `30`
- **Range**: `5-300`
- **Example**: `DB_QUERY_TIMEOUT=60`

#### `DB_STATEMENT_CACHE_SIZE`
Prepared statement cache size.

- **Required**: No
- **Default**: `100`
- **Range**: `10-1000`
- **Example**: `DB_STATEMENT_CACHE_SIZE=200`

### Caching Performance

#### `CACHE_TTL_SHORT`
TTL for short-lived cache items (seconds).

- **Required**: No
- **Default**: `300` (5 minutes)
- **Example**: `CACHE_TTL_SHORT=600`

#### `CACHE_TTL_MEDIUM`
TTL for medium-lived cache items (seconds).

- **Required**: No
- **Default**: `3600` (1 hour)
- **Example**: `CACHE_TTL_MEDIUM=7200`

#### `CACHE_TTL_LONG`
TTL for long-lived cache items (seconds).

- **Required**: No
- **Default**: `86400` (24 hours)
- **Example**: `CACHE_TTL_LONG=172800`

## External Service Configuration

### Search and Indexing

#### `OPENSEARCH_URL`
OpenSearch cluster URL for full-text search.

- **Required**: No
- **Format**: `http://host:port` or `https://host:port`
- **Example**: `OPENSEARCH_URL=http://localhost:9200`

#### `OPENSEARCH_USERNAME`
OpenSearch authentication username.

- **Required**: No (depends on OpenSearch setup)
- **Example**: `OPENSEARCH_USERNAME=stratmaster`

#### `OPENSEARCH_PASSWORD`
OpenSearch authentication password.

- **Required**: No (depends on OpenSearch setup)
- **Example**: `OPENSEARCH_PASSWORD=secure_password`
- **Security**: Store in secrets management system

### Graph Database

#### `NEBULA_GRAPH_HOST`
NebulaGraph database host.

- **Required**: No
- **Default**: `localhost`
- **Example**: `NEBULA_GRAPH_HOST=nebula-cluster`

#### `NEBULA_GRAPH_PORT`
NebulaGraph database port.

- **Required**: No
- **Default**: `9669`
- **Example**: `NEBULA_GRAPH_PORT=9669`

#### `NEBULA_GRAPH_USERNAME`
NebulaGraph authentication username.

- **Required**: No
- **Default**: `root`
- **Example**: `NEBULA_GRAPH_USERNAME=stratmaster`

#### `NEBULA_GRAPH_PASSWORD`
NebulaGraph authentication password.

- **Required**: No
- **Default**: `nebula`
- **Example**: `NEBULA_GRAPH_PASSWORD=secure_password`
- **Security**: Store in secrets management system

### Object Storage

#### `MINIO_URL`
MinIO object storage URL.

- **Required**: No
- **Format**: `http://host:port` or `https://host:port`
- **Example**: `MINIO_URL=http://localhost:9000`

#### `MINIO_ACCESS_KEY`
MinIO access key for authentication.

- **Required**: No (when using MinIO)
- **Example**: `MINIO_ACCESS_KEY=stratmaster`

#### `MINIO_SECRET_KEY`
MinIO secret key for authentication.

- **Required**: No (when using MinIO)
- **Example**: `MINIO_SECRET_KEY=stratmaster123`
- **Security**: Store in secrets management system

#### `MINIO_BUCKET_NAME`
Default bucket name for object storage.

- **Required**: No
- **Default**: `stratmaster`
- **Example**: `MINIO_BUCKET_NAME=stratmaster-prod`

### Workflow Engine

#### `TEMPORAL_HOST`
Temporal workflow engine host.

- **Required**: No
- **Default**: `localhost`
- **Example**: `TEMPORAL_HOST=temporal-frontend`

#### `TEMPORAL_PORT`
Temporal workflow engine port.

- **Required**: No
- **Default**: `7233`
- **Example**: `TEMPORAL_PORT=7233`

#### `TEMPORAL_NAMESPACE`
Temporal namespace for workflows.

- **Required**: No
- **Default**: `default`
- **Example**: `TEMPORAL_NAMESPACE=stratmaster`

## Development and Testing

### Test Configuration

#### `TEST_DATABASE_URL`
Database URL for running tests.

- **Required**: No (for tests)
- **Format**: `postgresql://user:password@host:port/test_database`
- **Example**: `TEST_DATABASE_URL=postgresql://stratmaster:test@localhost:5432/stratmaster_test`

#### `RUN_SLOW_TESTS`
Include slow tests in test execution.

- **Required**: No
- **Default**: `0` (disabled)
- **Options**: `0` (disabled), `1` (enabled)
- **Example**: `RUN_SLOW_TESTS=1`

#### `PYTEST_MARKERS`
Pytest markers for test selection.

- **Required**: No
- **Example**: `PYTEST_MARKERS=not slow`

### Python Environment

#### `PYTHONNOUSERSITE`
Disable user site-packages directory.

- **Required**: No (recommended for clean installs)
- **Default**: Not set
- **Options**: `1` (disable user site)
- **Example**: `PYTHONNOUSERSITE=1`

#### `PIP_DISABLE_PIP_VERSION_CHECK`
Disable pip version check warnings.

- **Required**: No
- **Default**: Not set
- **Options**: `1` (disable warnings)
- **Example**: `PIP_DISABLE_PIP_VERSION_CHECK=1`

## Environment File Templates

### Development Environment

```bash
# .env.development
STRATMASTER_ENV=development
LOG_LEVEL=DEBUG
ENABLE_DEBUG_ENDPOINTS=1
ENABLE_API_DOCS=1
ENABLE_CORS=1

# Database
DATABASE_URL=postgresql://stratmaster:dev_password@localhost:5432/stratmaster_dev
DATABASE_POOL_SIZE=5

# Cache
REDIS_URL=redis://localhost:6379/0

# Vector Database
QDRANT_URL=http://localhost:6333

# Authentication (optional for development)
JWT_SECRET=development-jwt-secret-key-change-in-production
SESSION_SECRET_KEY=development-session-secret-key

# Services
API_PORT=8080
RESEARCH_MCP_PORT=8081
KNOWLEDGE_MCP_PORT=8082

# Observability
PROMETHEUS_METRICS_ENABLED=true
LOG_FORMAT=text

# Python
PYTHONNOUSERSITE=1
PIP_DISABLE_PIP_VERSION_CHECK=1
```

### Production Environment

```bash
# .env.production
STRATMASTER_ENV=production
LOG_LEVEL=WARN
LOG_FORMAT=json
ENABLE_DEBUG_ENDPOINTS=0
ENABLE_API_DOCS=1

# Database (use secrets management)
DATABASE_URL=${DATABASE_URL_SECRET}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Cache
REDIS_URL=${REDIS_URL_SECRET}
REDIS_TTL_DEFAULT=3600

# Vector Database
QDRANT_URL=${QDRANT_URL_SECRET}
QDRANT_API_KEY=${QDRANT_API_KEY_SECRET}

# Authentication
KEYCLOAK_URL=https://auth.stratmaster.com
KEYCLOAK_REALM=stratmaster-prod
KEYCLOAK_CLIENT_ID=stratmaster-api
KEYCLOAK_CLIENT_SECRET=${KEYCLOAK_CLIENT_SECRET}
JWT_SECRET=${JWT_SECRET}
SESSION_SECRET_KEY=${SESSION_SECRET_KEY}

# Performance
API_WORKERS=8
REQUEST_TIMEOUT=60
MAX_CONCURRENT_REQUESTS=500

# Observability
PROMETHEUS_METRICS_ENABLED=true
OPENTELEMETRY_ENDPOINT=https://traces.stratmaster.com/v1/traces
LANGFUSE_URL=https://langfuse.stratmaster.com
LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}

# External Services
OPENSEARCH_URL=${OPENSEARCH_URL_SECRET}
OPENSEARCH_USERNAME=${OPENSEARCH_USERNAME_SECRET}
OPENSEARCH_PASSWORD=${OPENSEARCH_PASSWORD_SECRET}
MINIO_URL=${MINIO_URL_SECRET}
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY_SECRET}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY_SECRET}
```

## See Also

- [YAML Configurations](yaml-configs.md) - Structured configuration files
- [Configuration Overview](index.md) - Configuration system overview
- [Development Setup](../../how-to/development-setup.md) - Environment setup guide
- [Deployment Guide](../../how-to/deployment.md) - Production configuration
- [Security Model](../../explanation/security.md) - Security configuration guidelines