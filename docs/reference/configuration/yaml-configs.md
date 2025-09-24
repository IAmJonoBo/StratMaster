# YAML Configuration Reference

This document provides comprehensive reference for all YAML configuration files used in StratMaster. Each configuration file controls different aspects of system behavior, from AI model parameters to infrastructure settings.

## Configuration File Structure

StratMaster uses a hierarchical configuration system:

```
configs/
├── agents/                    # AI agent configurations
│   ├── debate-config.yaml     # Multi-agent debate settings
│   ├── personalities.yaml     # Agent personality configs
│   └── tools-config.yaml      # Agent tool configurations
├── ai/                        # AI model configurations  
│   ├── models.yaml           # Model parameters and routing
│   ├── embeddings.yaml       # Embedding model settings
│   └── providers.yaml        # AI provider configurations
├── auth/                     # Authentication configurations
│   ├── providers.yaml        # Auth provider settings
│   ├── policies.yaml         # Authorization policies
│   └── sessions.yaml         # Session management
├── database/                 # Database configurations
│   ├── connections.yaml      # Connection settings
│   ├── migrations.yaml       # Migration parameters
│   └── performance.yaml      # Performance tuning
├── monitoring/               # Observability configurations
│   ├── metrics.yaml          # Metrics collection
│   ├── logging.yaml          # Logging configuration
│   └── tracing.yaml          # Distributed tracing
└── security/                 # Security configurations
    ├── encryption.yaml       # Encryption settings
    ├── compliance.yaml       # Compliance configurations
    └── audit.yaml           # Audit logging
```

## Core Configuration Files

### 1. Application Configuration (`configs/app.yaml`)

Main application settings and feature flags:

```yaml
# Application metadata
app:
  name: "StratMaster"
  version: "0.1.0"
  description: "AI-powered brand strategy platform"
  
# Environment settings
environment:
  name: "production"  # development, staging, production
  debug: false
  testing: false

# Feature flags
features:
  multi_agent_debate: true
  experimental_models: false
  advanced_analytics: true
  enterprise_sso: true
  
# Server configuration
server:
  host: "0.0.0.0"
  port: 8080
  workers: 4
  timeout: 30
  max_request_size: "10MB"
  
# API configuration
api:
  prefix: "/api/v1"
  title: "StratMaster API"
  description: "AI-powered strategic analysis"
  version: "1.0.0"
  cors:
    allowed_origins: 
      - "https://app.stratmaster.ai"
      - "https://admin.stratmaster.ai"
    allowed_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: ["*"]
    allow_credentials: true
    max_age: 3600

# Rate limiting
rate_limits:
  default: "1000/hour"
  authenticated: "10000/hour"
  premium: "50000/hour"
  burst: 100
  
# Request/response settings
request:
  max_size: "10MB"
  timeout: 30
  retries: 3
  
response:
  compression: true
  compression_level: 6
  timeout: 60
```

### 2. AI Models Configuration (`configs/ai/models.yaml`)

Configuration for AI models and providers:

```yaml
# Default model settings
defaults:
  temperature: 0.7
  max_tokens: 4096
  top_p: 0.9
  frequency_penalty: 0.0
  presence_penalty: 0.0
  timeout: 30

# Model routing and load balancing
routing:
  strategy: "round_robin"  # round_robin, least_connections, weighted
  health_check_interval: 30
  failure_threshold: 3
  recovery_timeout: 60

# Provider configurations
providers:
  openai:
    enabled: true
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"
    organization: "${OPENAI_ORGANIZATION_ID}"
    models:
      gpt4:
        name: "gpt-4"
        max_tokens: 8192
        temperature: 0.7
        cost_per_1k_tokens: 0.03
        rate_limit: "3500/minute"
        
      gpt35_turbo:
        name: "gpt-3.5-turbo"
        max_tokens: 4096
        temperature: 0.7
        cost_per_1k_tokens: 0.002
        rate_limit: "3500/minute"
        
  anthropic:
    enabled: true
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "https://api.anthropic.com"
    models:
      claude3_opus:
        name: "claude-3-opus-20240229"
        max_tokens: 4096
        temperature: 0.7
        cost_per_1k_tokens: 0.015
        rate_limit: "4000/minute"
        
      claude3_sonnet:
        name: "claude-3-sonnet-20240229"
        max_tokens: 4096
        temperature: 0.7
        cost_per_1k_tokens: 0.003
        rate_limit: "4000/minute"

  local:
    enabled: false
    base_url: "http://localhost:11434"
    models:
      llama2:
        name: "llama2:13b"
        max_tokens: 2048
        temperature: 0.7
        cost_per_1k_tokens: 0.0

# Model assignments by task
task_models:
  research: ["gpt-4", "claude-3-opus"]
  analysis: ["gpt-4", "claude-3-sonnet"]
  synthesis: ["gpt-4", "claude-3-opus"]
  critique: ["claude-3-opus", "gpt-4"]
  quality_check: ["gpt-3.5-turbo", "claude-3-sonnet"]

# Fallback configuration
fallbacks:
  enabled: true
  max_retries: 3
  backoff_factor: 2.0
  fallback_models:
    - "gpt-3.5-turbo"
    - "claude-3-sonnet"
```

### 3. Multi-Agent Debate Configuration (`configs/agents/debate-config.yaml`)

Settings for the multi-agent debate system:

```yaml
# Debate process configuration
debate:
  max_rounds: 3
  consensus_threshold: 0.8
  timeout_per_round: 300  # seconds
  min_participants: 2
  max_participants: 5
  
# Quality gates
quality_gates:
  evidence_requirements:
    minimum_sources: 3
    credibility_threshold: 0.7
    diversity_score_min: 0.6
    
  logical_consistency:
    contradiction_tolerance: 0.1
    coherence_score_min: 0.8
    
  factual_accuracy:
    fact_check_threshold: 0.85
    verification_required: true

# Agent roles and capabilities
agents:
  research:
    enabled: true
    server: "research-mcp"
    personality:
      curiosity: 0.9
      thoroughness: 0.8
      skepticism: 0.6
    capabilities:
      - "web_search"
      - "document_retrieval"
      - "source_validation"
    constraints:
      - "evidence_required"
      - "source_diversity_min=3"
      - "max_search_results=50"
      
  analysis:
    enabled: true
    server: "knowledge-mcp"
    personality:
      creativity: 0.7
      analytical_thinking: 0.9
      risk_tolerance: 0.5
    capabilities:
      - "pattern_recognition"
      - "trend_analysis"
      - "strategic_synthesis"
    constraints:
      - "logic_validation"
      - "bias_detection"
      - "max_insights=10"
      
  critic:
    enabled: true
    server: "evals-mcp"
    personality:
      skepticism: 0.9
      thoroughness: 0.8
      constructiveness: 0.7
    capabilities:
      - "assumption_challenging"
      - "alternative_scenarios"
      - "weakness_identification"
    constraints:
      - "constructive_criticism"
      - "evidence_based_challenges"
      - "max_challenges=5"
      
  synthesis:
    enabled: true
    server: "router-mcp"
    personality:
      integration_ability: 0.9
      balance: 0.8
      clarity: 0.9
    capabilities:
      - "perspective_integration"
      - "conflict_resolution"
      - "narrative_construction"
    constraints:
      - "consensus_required"
      - "completeness_check"

# Evidence grading system
evidence_grading:
  framework: "GRADE"  # GRADE, SORT, Oxford
  criteria:
    source_credibility:
      weight: 0.3
      factors: ["domain_authority", "expertise", "reputation"]
    recency:
      weight: 0.2
      max_age_days: 730
    relevance:
      weight: 0.3
      matching_threshold: 0.7
    consistency:
      weight: 0.2
      cross_reference_min: 2

# Workflow orchestration
workflow:
  engine: "temporal"
  timeouts:
    research_activity: 600   # 10 minutes
    analysis_activity: 900   # 15 minutes  
    debate_activity: 1800    # 30 minutes
    synthesis_activity: 600  # 10 minutes
  retry_policy:
    max_attempts: 3
    initial_interval: 1
    backoff_coefficient: 2.0
    max_interval: 100
```

### 4. Database Configuration (`configs/database/connections.yaml`)

Database connection and performance settings:

```yaml
# Primary database (PostgreSQL)
primary:
  driver: "postgresql"
  host: "${DATABASE_HOST}"
  port: 5432
  database: "${DATABASE_NAME}"
  username: "${DATABASE_USER}"
  password: "${DATABASE_PASSWORD}"
  
  # Connection pool settings
  pool:
    size: 20
    max_overflow: 30
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true
    
  # SSL configuration
  ssl:
    mode: "require"  # disable, allow, prefer, require, verify-ca, verify-full
    cert_file: "/etc/ssl/certs/client-cert.pem"
    key_file: "/etc/ssl/private/client-key.pem"
    ca_file: "/etc/ssl/certs/ca-cert.pem"
    
  # Query optimization
  query_timeout: 30
  statement_timeout: 60
  lock_timeout: 30

# Read replicas
read_replicas:
  enabled: true
  load_balance_strategy: "round_robin"
  replica_1:
    host: "${DATABASE_READ_HOST_1}"
    port: 5432
    weight: 1
  replica_2:
    host: "${DATABASE_READ_HOST_2}"
    port: 5432
    weight: 1

# Vector database (Qdrant)
vector:
  host: "${QDRANT_HOST}"
  port: 6333
  grpc_port: 6334
  api_key: "${QDRANT_API_KEY}"
  
  # Collection settings
  collections:
    strategies:
      vector_size: 384
      distance: "Cosine"
      shard_number: 1
      replication_factor: 2
      
    documents:
      vector_size: 1536
      distance: "Cosine"
      shard_number: 2
      replication_factor: 2
      
  # Performance tuning
  performance:
    max_connections: 100
    timeout: 30
    search_timeout: 10
    
# Search database (OpenSearch)
search:
  hosts:
    - "${OPENSEARCH_HOST}:9200"
  username: "${OPENSEARCH_USER}"
  password: "${OPENSEARCH_PASSWORD}"
  
  # SSL settings
  ssl:
    enabled: true
    verify_certs: true
    ca_certs: "/etc/ssl/certs/opensearch-ca.pem"
    
  # Index settings
  indices:
    strategies:
      shards: 2
      replicas: 1
      max_result_window: 10000
      
    documents:
      shards: 3
      replicas: 1
      max_result_window: 50000
      
# Graph database (NebulaGraph)
graph:
  hosts:
    - "${NEBULA_HOST}:9669"
  username: "${NEBULA_USER}"
  password: "${NEBULA_PASSWORD}"
  
  # Connection settings
  connection_pool_size: 20
  timeout: 30
  idle_time: 28800  # 8 hours
  
  # Space settings
  space: "stratmaster"
  replica_factor: 1
  partition_num: 10

# Cache (Redis)
cache:
  host: "${REDIS_HOST}"
  port: 6379
  password: "${REDIS_PASSWORD}"
  database: 0
  
  # Connection settings
  connection_pool:
    max_connections: 50
    retry_on_timeout: true
    socket_timeout: 30
    socket_connect_timeout: 30
    
  # Cache policies
  policies:
    default_ttl: 3600  # 1 hour
    max_ttl: 86400     # 24 hours
    compression: true
    serialization: "pickle"
```

### 5. Security Configuration (`configs/security/encryption.yaml`)

Encryption and security settings:

```yaml
# Encryption settings
encryption:
  # At-rest encryption
  at_rest:
    algorithm: "AES-256-GCM"
    key_provider: "vault"  # vault, aws_kms, azure_kv, gcp_kms
    key_rotation_days: 90
    backup_keys_count: 3
    
  # In-transit encryption  
  in_transit:
    tls_version: "1.3"
    cipher_suites:
      - "TLS_AES_256_GCM_SHA384"
      - "TLS_CHACHA20_POLY1305_SHA256"
      - "TLS_AES_128_GCM_SHA256"
    certificate_provider: "letsencrypt"
    
  # Field-level encryption
  fields:
    - table: "users"
      columns: ["email", "phone"]
      algorithm: "AES-256-GCM"
    - table: "strategies" 
      columns: ["content", "insights"]
      algorithm: "AES-256-GCM"

# Key management
key_management:
  provider: "hashicorp_vault"
  vault:
    address: "${VAULT_ADDR}"
    token: "${VAULT_TOKEN}"
    mount_path: "kv-v2"
    key_path: "stratmaster/encryption-keys"
    
  # Key rotation policy
  rotation:
    enabled: true
    schedule: "0 2 * * 0"  # Weekly on Sunday at 2 AM
    grace_period_days: 7
    
  # Backup and recovery
  backup:
    enabled: true
    provider: "aws_s3"
    bucket: "stratmaster-key-backups"
    encryption: "SSE-KMS"

# Authentication
authentication:
  # JWT settings
  jwt:
    algorithm: "RS256"
    public_key_path: "/etc/jwt/public.pem"
    private_key_path: "/etc/jwt/private.pem"
    issuer: "stratmaster.ai"
    audience: ["api.stratmaster.ai"]
    expiration: 3600  # 1 hour
    
  # Session management
  sessions:
    provider: "redis"
    ttl: 86400  # 24 hours
    secure: true
    http_only: true
    same_site: "strict"
    
  # OAuth providers
  oauth:
    google:
      enabled: true
      client_id: "${GOOGLE_CLIENT_ID}"
      client_secret: "${GOOGLE_CLIENT_SECRET}"
      scopes: ["openid", "profile", "email"]
      
    microsoft:
      enabled: true
      client_id: "${MICROSOFT_CLIENT_ID}"
      client_secret: "${MICROSOFT_CLIENT_SECRET}"
      tenant_id: "${MICROSOFT_TENANT_ID}"

# Authorization
authorization:
  # RBAC configuration
  rbac:
    enabled: true
    default_role: "viewer"
    role_hierarchy:
      - "admin"
      - "tenant_admin"
      - "strategist"  
      - "analyst"
      - "viewer"
      
  # ABAC configuration  
  abac:
    enabled: true
    policies_path: "/etc/abac/policies.json"
    
  # Multi-tenancy
  multi_tenant:
    isolation_level: "strict"
    tenant_header: "X-Tenant-ID"
    default_tenant: "default"

# Audit logging
audit:
  enabled: true
  level: "detailed"  # minimal, standard, detailed, complete
  
  # Log destinations
  destinations:
    - type: "file"
      path: "/var/log/audit/stratmaster.log"
      rotation: "daily"
      retention_days: 365
      
    - type: "database"
      table: "audit_logs"
      async: true
      
    - type: "siem"
      endpoint: "${SIEM_ENDPOINT}"
      api_key: "${SIEM_API_KEY}"
      
  # Events to audit
  events:
    authentication: ["login", "logout", "failed_login"]
    authorization: ["permission_granted", "permission_denied"]
    data_access: ["create", "read", "update", "delete"]
    configuration: ["settings_changed", "user_added", "role_modified"]
    security: ["encryption_key_rotated", "certificate_renewed"]
```

### 6. Monitoring Configuration (`configs/monitoring/metrics.yaml`)

Observability and monitoring settings:

```yaml
# Metrics collection
metrics:
  # Prometheus settings
  prometheus:
    enabled: true
    endpoint: "/metrics"
    port: 9090
    scrape_interval: 15
    evaluation_interval: 15
    
  # Custom metrics
  custom:
    business_metrics:
      - name: "strategies_created_total"
        type: "counter"
        description: "Total number of strategies created"
        labels: ["tenant", "user_type", "complexity"]
        
      - name: "analysis_duration_seconds"
        type: "histogram"
        description: "Time taken for analysis completion"
        buckets: [1, 5, 10, 30, 60, 300, 600]
        
      - name: "quality_score"
        type: "gauge"
        description: "Current analysis quality score"
        labels: ["analysis_type", "agent"]
        
    technical_metrics:
      - name: "database_connections_active"
        type: "gauge"
        description: "Active database connections"
        labels: ["database", "type"]
        
      - name: "ai_model_requests_total"
        type: "counter" 
        description: "Total AI model requests"
        labels: ["provider", "model", "status"]

# Distributed tracing
tracing:
  enabled: true
  provider: "jaeger"  # jaeger, zipkin, datadog, honeycomb
  
  # Jaeger configuration
  jaeger:
    agent_host: "${JAEGER_AGENT_HOST}"
    agent_port: 6831
    collector_endpoint: "${JAEGER_COLLECTOR_ENDPOINT}"
    
  # Sampling configuration
  sampling:
    type: "probabilistic"
    rate: 0.1  # Sample 10% of traces
    
  # Trace attributes
  attributes:
    service_name: "stratmaster-api"
    service_version: "0.1.0"
    environment: "${ENVIRONMENT}"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "json"  # json, text
  
  # Structured logging
  structured:
    enabled: true
    fields:
      timestamp: true
      level: true
      logger: true
      module: true
      function: true
      line: true
      trace_id: true
      span_id: true
      user_id: true
      tenant_id: true
      correlation_id: true
      
  # Log destinations
  destinations:
    console:
      enabled: true
      level: "INFO"
      
    file:
      enabled: true
      path: "/var/log/stratmaster/app.log"
      level: "DEBUG"
      rotation: "daily"
      retention_days: 30
      max_size: "100MB"
      
    remote:
      enabled: true
      type: "loki"  # loki, elasticsearch, datadog
      endpoint: "${LOKI_ENDPOINT}"
      
  # Performance logging
  performance:
    slow_query_threshold: 1.0  # seconds
    slow_request_threshold: 2.0  # seconds
    
# Alerting
alerting:
  enabled: true
  provider: "alertmanager"  # alertmanager, pagerduty, opsgenie
  
  # Alert rules
  rules:
    - name: "high_error_rate"
      condition: "rate(http_requests_total{status=~'5..'}[5m]) > 0.1"
      duration: "2m"
      severity: "critical"
      description: "High error rate detected"
      
    - name: "high_latency"
      condition: "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5"
      duration: "5m"
      severity: "warning"
      description: "High response latency detected"
      
    - name: "database_connections_exhausted"
      condition: "database_connections_active / database_connections_max > 0.9"
      duration: "1m"
      severity: "critical"
      description: "Database connection pool nearly exhausted"

# Health checks
health:
  enabled: true
  endpoint: "/healthz"
  
  # Component checks
  checks:
    database:
      enabled: true
      timeout: 5
      query: "SELECT 1"
      
    cache:
      enabled: true
      timeout: 2
      command: "PING"
      
    ai_providers:
      enabled: true
      timeout: 10
      test_prompt: "Hello"
      
    external_services:
      enabled: true
      timeout: 5
      services:
        - name: "vector_db"
          url: "http://qdrant:6333/health"
        - name: "search_db"  
          url: "http://opensearch:9200/_cluster/health"
```

## Environment-Specific Configurations

### Development Environment (`configs/environments/development.yaml`)

```yaml
environment: "development"
debug: true

# Relaxed security for development
security:
  tls_required: false
  csrf_protection: false
  rate_limiting: false
  
# Faster iteration
ai:
  temperature: 0.9  # More creative for testing
  timeout: 15       # Faster timeouts
  
# Local services
services:
  database_url: "postgresql://stratmaster:password@localhost:5432/stratmaster_dev"
  redis_url: "redis://localhost:6379/0"
  qdrant_url: "http://localhost:6333"
  
# Enhanced logging
logging:
  level: "DEBUG"
  console_enabled: true
  file_enabled: false
```

### Production Environment (`configs/environments/production.yaml`)

```yaml
environment: "production"
debug: false

# Maximum security
security:
  tls_required: true
  tls_version: "1.3"
  csrf_protection: true
  rate_limiting: true
  audit_logging: "complete"
  
# Conservative AI settings
ai:
  temperature: 0.7
  timeout: 60
  retry_attempts: 3
  
# Production services (externalized)
services:
  database_url: "${DATABASE_URL}"
  redis_url: "${REDIS_URL}"
  qdrant_url: "${QDRANT_URL}"
  
# Minimal logging
logging:
  level: "INFO"
  console_enabled: false
  structured_logging: true
  
# Resource limits
resources:
  max_memory: "4Gi"
  max_cpu: "2000m"
  max_connections: 1000
```

## Configuration Validation

### Schema Validation

All configuration files are validated against JSON schemas:

```yaml
# configs/schemas/app-schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: "object"
properties:
  app:
    type: "object"
    properties:
      name:
        type: "string"
        minLength: 1
      version:
        type: "string"
        pattern: "^\\d+\\.\\d+\\.\\d+$"
    required: ["name", "version"]
  environment:
    type: "object"
    properties:
      name:
        type: "string"
        enum: ["development", "staging", "production"]
    required: ["name"]
required: ["app", "environment"]
```

### Configuration Testing

Test configuration validity:

```bash
# Validate all configurations
make config.validate

# Test specific environment
make config.test.production

# Dry-run with configuration
make deploy.dry-run --config=production
```

## Migration and Upgrades

### Configuration Migration

When upgrading between versions:

```bash
# Backup current configuration
cp -r configs configs.backup.$(date +%Y%m%d)

# Run migration script
python scripts/migrate_config.py --from=0.0.9 --to=0.1.0

# Validate migrated configuration
make config.validate
```

### Version Compatibility

Configuration compatibility matrix:

| Config Version | App Version | Notes |
|---|---|---|
| 1.0 | 0.1.0+ | Initial release |
| 1.1 | 0.1.5+ | Added multi-tenancy |
| 1.2 | 0.2.0+ | Enhanced security |
| 2.0 | 1.0.0+ | Breaking changes |

---

This YAML configuration reference provides comprehensive control over all aspects of StratMaster's behavior. Always validate configurations before deployment and maintain backups of working configurations.