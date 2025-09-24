# StratMaster Infrastructure Guide

This guide covers all backing services, their configuration, operational procedures, and integration patterns. StratMaster uses a comprehensive stack of 12+ services to provide storage, search, orchestration, and observability capabilities.

## Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Gateway │ Research MCP │ Knowledge MCP │ Router MCP    │
├─────────────────────────────────────────────────────────────────┤
│                    Storage Layer                                │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL │ Qdrant │ OpenSearch │ NebulaGraph │ MinIO │ DuckDB │
├─────────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                          │
├─────────────────────────────────────────────────────────────────┤
│ Temporal │ Keycloak │ SearxNG │ vLLM/Ollama │ LiteLLM │ Langfuse │
├─────────────────────────────────────────────────────────────────┤
│                  Observability Layer                           │
├─────────────────────────────────────────────────────────────────┤
│          OTEL Collector │ Prometheus │ Grafana                  │
└─────────────────────────────────────────────────────────────────┘
```

## Storage Services

### PostgreSQL (`infra/postgres/`)

**Primary relational database for structured data, user management, and audit logs.**

#### Configuration

```yaml
# docker-compose.yml
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: stratmaster
    POSTGRES_USER: stratmaster
    POSTGRES_PASSWORD: stratmaster
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./infra/postgres/init:/docker-entrypoint-initdb.d
  ports: ["5432:5432"]
```

#### Schema Design

```sql
-- Core domain tables
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE research_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    query TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES research_sessions(id),
    text TEXT NOT NULL,
    confidence DECIMAL(3,2),
    supporting_evidence JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Operations

```bash
# Connect to database
psql -h localhost -U stratmaster -d stratmaster

# Check connections and activity
SELECT * FROM pg_stat_activity;

# Database size and table statistics
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables;

# Performance tuning
EXPLAIN ANALYZE SELECT * FROM claims WHERE session_id = $1;
```

#### Backup and Recovery

```bash
# Database backup
docker exec postgres pg_dump -U stratmaster stratmaster > backup.sql

# Restore database
docker exec -i postgres psql -U stratmaster stratmaster < backup.sql

# Point-in-time recovery (production)
docker exec postgres pg_basebackup -D /backup -Ft -z -P -U stratmaster
```

### Qdrant (`infra/qdrant/`)

**Vector database for dense embeddings and semantic search.**

#### Configuration

```yaml
# docker-compose.yml
qdrant:
  image: qdrant/qdrant:latest
  ports: ["6333:6333", "6334:6334"]
  volumes:
    - qdrant_data:/qdrant/storage
    - ./infra/qdrant/config.yaml:/qdrant/config/production.yaml
```

#### Collection Management

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient("localhost", port=6333)

# Create tenant collection
client.create_collection(
    collection_name="tenant_demo_research",
    vectors_config=models.VectorParams(
        size=1024,  # ColBERT embeddings
        distance=models.Distance.COSINE
    ),
    hnsw_config=models.HnswConfigDiff(
        m=32,
        ef_construct=128
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99
        )
    )
)
```

#### Performance Tuning

| Parameter | Development | Production | Notes |
|-----------|-------------|------------|-------|
| `hnsw.m` | 16 | 32 | Balance recall/latency |
| `hnsw.ef_construct` | 64 | 128 | Higher = better recall |
| `quantization` | none | scalar | Save 4x storage |
| `replication_factor` | 1 | 2 | High availability |
| `shard_number` | 1 | 3 | Distribute load |

#### Monitoring

```bash
# Collection statistics
curl http://localhost:6333/collections/tenant_demo_research

# Cluster health
curl http://localhost:6333/cluster

# Performance metrics
curl http://localhost:6333/metrics
```

### OpenSearch (`infra/opensearch/`)

**Full-text search and sparse vector retrieval with SPLADE.**

#### Configuration

```yaml
# docker-compose.yml
opensearch:
  image: opensearchproject/opensearch:2.11.0
  environment:
    - discovery.type=single-node
    - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
    - DISABLE_SECURITY_PLUGIN=true
  ports: ["9200:9200"]
  volumes:
    - opensearch_data:/usr/share/opensearch/data
```

#### Index Templates

```json
{
  "index_patterns": ["tenant_*_documents"],
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "analysis": {
        "analyzer": {
          "splade_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "stop"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "text": {"type": "text", "analyzer": "splade_analyzer"},
        "splade_vector": {"type": "sparse_vector"},
        "metadata": {"type": "object"},
        "tenant_id": {"type": "keyword"},
        "created_at": {"type": "date"}
      }
    }
  }
}
```

#### SPLADE Integration

```python
import requests
from transformers import AutoTokenizer, AutoModelForMaskedLM

# Index document with SPLADE expansion
def index_with_splade(text: str, doc_id: str, tenant_id: str):
    # Generate SPLADE vector (sparse)
    splade_vector = generate_splade_vector(text)
    
    doc = {
        "text": text,
        "splade_vector": splade_vector,
        "tenant_id": tenant_id,
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    response = requests.post(
        f"http://localhost:9200/tenant_{tenant_id}_documents/_doc/{doc_id}",
        json=doc
    )
    return response.json()
```

#### Operations

```bash
# Cluster health
curl http://localhost:9200/_cluster/health

# Index statistics
curl http://localhost:9200/_cat/indices?v

# Search performance
curl -X POST "http://localhost:9200/tenant_demo_documents/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"text": "AI strategy"}}}'
```

### NebulaGraph (`infra/nebulagraph/`)

**Distributed graph database for knowledge graphs and entity relationships.**

#### Configuration

```yaml
# docker-compose.yml
nebulagraph:
  image: vesoft/nebula-standalone:v3.6.0
  ports: 
    - "9669:9669"  # Graph service
    - "19669:19669" # Meta service  
    - "19779:19779" # Storage service
  volumes:
    - nebula_data:/data
    - ./infra/nebulagraph/init:/init-scripts
```

#### Schema Definition

```ngql
-- Entity types
CREATE TAG PERSON(name string, type string);
CREATE TAG ORGANIZATION(name string, industry string);
CREATE TAG CONCEPT(name string, category string);
CREATE TAG DOCUMENT(title string, url string, created_at datetime);

-- Relationship types
CREATE EDGE MENTIONS(confidence double, context string);
CREATE EDGE RELATES_TO(strength double, relationship_type string);
CREATE EDGE SOURCES_FROM(citation_count int, relevance double);

-- Create space for tenant
CREATE SPACE tenant_demo(vid_type=FIXED_STRING(32));
USE tenant_demo;
```

#### Graph Operations

```python
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

# Connect to NebulaGraph
config = Config()
config.max_connection_pool_size = 10
connection_pool = ConnectionPool()
connection_pool.init([('localhost', 9669)], config)

# Execute graph query
def find_related_concepts(concept_name: str, tenant_id: str):
    session = connection_pool.get_session('stratmaster', 'stratmaster')
    
    query = f"""
    USE tenant_{tenant_id};
    MATCH (c:CONCEPT {{name: "{concept_name}"}})-[r:RELATES_TO]-(related:CONCEPT)
    RETURN related.name, r.relationship_type, r.strength
    ORDER BY r.strength DESC
    LIMIT 10;
    """
    
    result = session.execute(query)
    return result.column_values('related.name')
```

#### Performance Optimization

```ngql
-- Create indexes for faster queries
CREATE TAG INDEX person_name_index ON PERSON(name(20));
CREATE TAG INDEX org_name_index ON ORGANIZATION(name(30));
CREATE EDGE INDEX mentions_confidence ON MENTIONS(confidence);

-- Rebuild indexes after creation
REBUILD TAG INDEX person_name_index;
REBUILD EDGE INDEX mentions_confidence;
```

### MinIO (`infra/minio/`)

**S3-compatible object storage for documents, media, and artifacts.**

#### Configuration

```yaml
# docker-compose.yml
minio:
  image: minio/minio:latest
  command: server /data --console-address ":9001"
  environment:
    MINIO_ROOT_USER: stratmaster
    MINIO_ROOT_PASSWORD: stratmaster123
  ports: ["9000:9000", "9001:9001"]
  volumes:
    - minio_data:/data
```

#### Bucket Organization

```
stratmaster/
├── tenants/
│   ├── demo/
│   │   ├── documents/          # Raw documents and PDFs
│   │   ├── artifacts/          # Generated reports and analysis
│   │   └── embeddings/         # Serialized vectors and indexes
│   └── {tenant-id}/
│       ├── documents/
│       ├── artifacts/
│       └── embeddings/
├── system/
│   ├── models/                 # ML model weights and configs
│   ├── templates/              # Report templates
│   └── backups/                # Database backups
└── public/
    ├── assets/                 # Static web assets
    └── docs/                   # Public documentation
```

#### Access Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["arn:aws:iam::tenant:user/demo-user"]},
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": ["arn:aws:s3:::stratmaster/tenants/demo/*"]
    },
    {
      "Effect": "Allow", 
      "Principal": {"AWS": ["arn:aws:iam::system:user/api-service"]},
      "Action": ["s3:*"],
      "Resource": ["arn:aws:s3:::stratmaster/system/*"]
    }
  ]
}
```

#### Operations

```bash
# Install MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc

# Configure client
mc alias set local http://localhost:9000 stratmaster stratmaster123

# Bucket operations
mc mb local/stratmaster
mc policy set public local/stratmaster/public

# File operations
mc cp document.pdf local/stratmaster/tenants/demo/documents/
mc ls local/stratmaster/tenants/demo/documents/
```

### DuckDB (`infra/duckdb/`)

**Analytics database for data processing and OLAP queries.**

#### Configuration

```yaml
# docker-compose.yml  
duckdb:
  image: marcboeker/duckdb:latest
  volumes:
    - duckdb_data:/data
    - ./infra/duckdb/queries:/queries
  command: ["duckdb", "/data/stratmaster.db"]
```

#### Analytics Queries

```sql
-- Connect to PostgreSQL for federated queries
INSTALL postgres;
LOAD postgres;
ATTACH 'postgresql://stratmaster:stratmaster@postgres:5432/stratmaster' AS pg;

-- Aggregate research metrics by tenant
CREATE VIEW tenant_research_metrics AS
SELECT 
    t.name as tenant_name,
    COUNT(rs.id) as total_sessions,
    AVG(EXTRACT(EPOCH FROM (rs.completed_at - rs.created_at))/60) as avg_duration_minutes,
    COUNT(c.id) as total_claims,
    AVG(c.confidence) as avg_confidence
FROM pg.tenants t
JOIN pg.research_sessions rs ON t.id = rs.tenant_id
LEFT JOIN pg.claims c ON rs.id = c.session_id
WHERE rs.completed_at IS NOT NULL
GROUP BY t.id, t.name;

-- Export analytics to Parquet
COPY (SELECT * FROM tenant_research_metrics) 
TO '/data/exports/tenant_metrics.parquet' (FORMAT PARQUET);
```

#### Data Processing Pipeline

```python
import duckdb
import pandas as pd

# Connect to DuckDB
conn = duckdb.connect('/data/stratmaster.db')

# Process large datasets efficiently
def analyze_research_trends(tenant_id: str):
    query = """
    SELECT 
        DATE_TRUNC('day', created_at) as date,
        query,
        COUNT(*) as frequency,
        AVG(confidence) as avg_confidence
    FROM pg.research_sessions rs
    JOIN pg.claims c ON rs.id = c.session_id
    WHERE rs.tenant_id = ?
    GROUP BY date, query
    ORDER BY date DESC, frequency DESC
    """
    
    return conn.execute(query, [tenant_id]).fetchdf()
```

## Infrastructure Services

### Temporal (`infra/temporal/`)

**Durable workflow orchestration for long-running processes.**

#### Configuration

```yaml
# docker-compose.yml
temporal-server:
  image: temporalio/auto-setup:1.22.0
  environment:
    - DB=postgresql
    - DB_PORT=5432
    - POSTGRES_USER=stratmaster
    - POSTGRES_PWD=stratmaster
    - POSTGRES_SEEDS=postgres
  ports: ["7233:7233"]
  depends_on: [postgres]

temporal-ui:
  image: temporalio/ui:2.20.0
  environment:
    - TEMPORAL_ADDRESS=temporal-server:7233
  ports: ["8088:8080"]
```

#### Workflow Definition

```python
from temporalio import workflow, activity
from datetime import timedelta
import asyncio

@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, request: ResearchRequest) -> ResearchResponse:
        # Step 1: Plan research
        plan = await workflow.execute_activity(
            plan_research,
            request,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 2: Execute searches in parallel
        search_tasks = []
        for source in plan.sources:
            task = workflow.execute_activity(
                search_source,
                source,
                start_to_close_timeout=timedelta(minutes=10)
            )
            search_tasks.append(task)
        
        results = await asyncio.gather(*search_tasks)
        
        # Step 3: Synthesize results
        synthesis = await workflow.execute_activity(
            synthesize_results,
            results,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return synthesis

@activity.defn
async def plan_research(request: ResearchRequest) -> ResearchPlan:
    # Implementation here
    pass
```

#### Operations

```bash
# Start workflow
temporal workflow start \
  --type ResearchWorkflow \
  --task-queue research-tasks \
  --input '{"query": "AI trends 2024"}'

# List running workflows  
temporal workflow list

# Query workflow history
temporal workflow show -w <workflow-id>
```

### Keycloak (`infra/keycloak/`)

**Identity and access management with multi-tenant support.**

#### Configuration

```yaml
# docker-compose.yml
keycloak:
  image: quay.io/keycloak/keycloak:22.0
  command: start-dev
  environment:
    KC_DB: postgres
    KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
    KC_DB_USERNAME: stratmaster
    KC_DB_PASSWORD: stratmaster
    KEYCLOAK_ADMIN: admin
    KEYCLOAK_ADMIN_PASSWORD: admin
  ports: ["8089:8080"]
  depends_on: [postgres]
```

#### Realm Configuration

```json
{
  "realm": "stratmaster",
  "enabled": true,
  "clients": [
    {
      "clientId": "stratmaster-api",
      "enabled": true,
      "publicClient": false,
      "serviceAccountsEnabled": true,
      "authorizationServicesEnabled": true
    },
    {
      "clientId": "stratmaster-web",
      "enabled": true,
      "publicClient": true,
      "redirectUris": ["http://localhost:3000/*"]
    }
  ],
  "users": [
    {
      "username": "demo-user",
      "enabled": true,
      "credentials": [
        {"type": "password", "value": "demo123", "temporary": false}
      ],
      "realmRoles": ["tenant-demo-user"]
    }
  ]
}
```

#### Integration

```python
from keycloak import KeycloakOpenID

# Configure OpenID Connect client
keycloak_openid = KeycloakOpenID(
    server_url="http://localhost:8089/",
    client_id="stratmaster-api",
    realm_name="stratmaster",
    client_secret_key="your-secret"
)

# Authenticate user
def authenticate(username: str, password: str):
    try:
        token = keycloak_openid.token(username, password)
        return token
    except Exception as e:
        raise AuthenticationError(f"Login failed: {e}")

# Verify JWT token
def verify_token(token: str):
    try:
        userinfo = keycloak_openid.userinfo(token)
        return userinfo
    except Exception as e:
        raise AuthorizationError(f"Token invalid: {e}")
```

### SearxNG (`infra/searxng/`)

**Privacy-focused web search aggregator.**

#### Configuration

```yaml
# docker-compose.yml
searxng:
  image: searxng/searxng:latest
  ports: ["8087:8080"]
  volumes:
    - ./infra/searxng/settings.yml:/etc/searxng/settings.yml
  environment:
    - SEARXNG_BASE_URL=http://localhost:8087/
```

#### Search Configuration

```yaml
# settings.yml
search:
  safe_search: 0
  autocomplete: "google"
  default_lang: "en"
  
engines:
  - name: google
    engine: google
    disabled: false
    use_mobile_ui: false
    
  - name: bing  
    engine: bing
    disabled: false
    
  - name: duckduckgo
    engine: duckduckgo
    disabled: false

outgoing:
  request_timeout: 10.0
  max_request_timeout: 20.0
  pool_connections: 100
  enable_http2: true
```

#### Integration

```python
import httpx
from typing import List, Dict

async def search_web(query: str, num_results: int = 10) -> List[Dict]:
    """Search web using SearxNG with privacy protection."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8087/search",
            params={
                "q": query,
                "format": "json",
                "engines": "google,bing,duckduckgo",
                "pageno": 1
            },
            headers={"User-Agent": "StratMaster Research Agent"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])[:num_results]
        else:
            raise SearchError(f"Search failed: {response.status_code}")
```

### vLLM/Ollama (`infra/vllm-or-ollama/`)

**Local LLM inference serving for cost-effective processing.**

#### vLLM Configuration

```yaml
# docker-compose.yml
vllm:
  image: vllm/vllm-openai:latest
  command: |
    --model microsoft/DialoGPT-medium
    --served-model-name gpt-3.5-turbo
    --host 0.0.0.0
    --port 8000
  ports: ["8000:8000"]
  volumes:
    - ~/.cache/huggingface:/root/.cache/huggingface
  environment:
    - CUDA_VISIBLE_DEVICES=0
```

#### Ollama Alternative

```yaml
# docker-compose.yml  
ollama:
  image: ollama/ollama:latest
  ports: ["11434:11434"]
  volumes:
    - ollama_data:/root/.ollama
  environment:
    - OLLAMA_HOST=0.0.0.0
```

#### Model Management

```bash
# Pull models with Ollama
docker exec ollama ollama pull llama2:7b
docker exec ollama ollama pull codellama:7b
docker exec ollama ollama list

# Test inference
curl http://localhost:11434/api/generate -d '{
  "model": "llama2:7b",
  "prompt": "Explain the benefits of AI in business strategy",
  "stream": false
}'
```

### LiteLLM (`infra/litellm/`)

**LLM router and proxy for unified API access.**

#### Configuration

```yaml
# docker-compose.yml
litellm:
  image: ghcr.io/berriai/litellm:main-latest
  ports: ["4000:4000"]
  volumes:
    - ./infra/litellm/config.yaml:/app/config.yaml
  environment:
    - LITELLM_CONFIG_PATH=/app/config.yaml
  command: ["--config", "/app/config.yaml", "--port", "4000"]
```

#### Router Configuration

```yaml
# config.yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}
      
  - model_name: gpt-3.5-turbo
    litellm_params: 
      model: vllm/microsoft/DialoGPT-medium
      api_base: http://vllm:8000/v1
      
  - model_name: llama2
    litellm_params:
      model: ollama/llama2:7b
      api_base: http://ollama:11434

router_settings:
  routing_strategy: least-busy
  allowed_fails: 3
  cooldown_time: 30
  retry_after: 10
```

### Langfuse (`infra/langfuse/)

**LLM observability and tracing for debugging and optimization.**

#### Configuration

```yaml
# docker-compose.yml
langfuse:
  image: langfuse/langfuse:latest
  ports: ["3000:3000"]
  environment:
    DATABASE_URL: postgresql://stratmaster:stratmaster@postgres:5432/langfuse
    NEXTAUTH_SECRET: your-secret-key
    SALT: your-salt
    NEXTAUTH_URL: http://localhost:3000
  depends_on: [postgres]
```

#### Integration

```python
from langfuse import Langfuse
from langfuse.decorators import observe

# Initialize Langfuse client
langfuse = Langfuse(
    public_key="pk_your_key",
    secret_key="sk_your_key", 
    host="http://localhost:3000"
)

@observe()
async def research_with_tracing(query: str) -> ResearchResponse:
    """Research function with automatic tracing."""
    
    # Create span for search phase
    with langfuse.span(name="web_search") as span:
        span.update(input={"query": query})
        search_results = await search_web(query)
        span.update(output={"num_results": len(search_results)})
    
    # Create span for synthesis
    with langfuse.span(name="synthesis") as span:
        claims = await synthesize_claims(search_results)
        span.update(
            output={"num_claims": len(claims)},
            metadata={"model": "gpt-3.5-turbo"}
        )
    
    return ResearchResponse(claims=claims)
```

## Observability Services

### OpenTelemetry Collector

```yaml
# docker-compose.yml
otel-collector:
  image: otel/opentelemetry-collector-contrib:latest
  command: ["--config=/etc/otel-collector-config.yaml"]
  volumes:
    - ./infra/otel/collector-config.yaml:/etc/otel-collector-config.yaml
  ports: ["4317:4317", "4318:4318"]
```

### Prometheus & Grafana

```yaml
prometheus:
  image: prom/prometheus:latest
  ports: ["9090:9090"]
  volumes:
    - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana:latest
  ports: ["3001:3000"]
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana_data:/var/lib/grafana
```

## Deployment Considerations

### Resource Requirements

| Service | CPU | Memory | Storage | Notes |
|---------|-----|--------|---------|-------|
| PostgreSQL | 1 core | 2GB | 20GB | Scales with data |
| Qdrant | 2 cores | 4GB | 50GB | Vector storage |
| OpenSearch | 2 cores | 4GB | 30GB | Text indexes |
| NebulaGraph | 1 core | 2GB | 10GB | Graph data |
| MinIO | 1 core | 1GB | 100GB | Object storage |
| Temporal | 1 core | 2GB | 5GB | Workflow state |
| Keycloak | 1 core | 1GB | 2GB | Identity data |

### Network Architecture

```bash
# Service communication matrix
API Gateway     → All MCP servers (HTTP)
Research MCP    → SearxNG (HTTP), MinIO (S3)
Knowledge MCP   → Qdrant (gRPC), OpenSearch (HTTP), NebulaGraph (TCP)
Router MCP      → vLLM/Ollama (HTTP), LiteLLM (HTTP)
All Services    → PostgreSQL (TCP), Langfuse (HTTP)
```

### Security Considerations

- **Network Segmentation**: Use Kubernetes NetworkPolicies or Docker networks
- **Secret Management**: Sealed Secrets for Kubernetes, Docker Secrets for local
- **TLS Termination**: Ingress controller or reverse proxy
- **Authentication**: Keycloak integration across all services
- **Authorization**: RBAC policies per service and tenant

## Monitoring & Alerting

### Health Checks

```bash
# Service health endpoints
curl http://localhost:8080/healthz      # API Gateway
curl http://localhost:8081/info         # Research MCP
curl http://localhost:6333/cluster      # Qdrant
curl http://localhost:9200/_cluster/health  # OpenSearch
curl http://localhost:9000/minio/health # MinIO
```

### Key Metrics

- **API Gateway**: Request rate, response time, error rate
- **Storage**: Disk usage, connection counts, query performance  
- **Search**: Index size, search latency, relevance scores
- **Inference**: Model latency, token throughput, GPU utilization
- **Workflows**: Execution time, failure rate, queue depth

### Alerting Rules

```yaml
# prometheus alerts
groups:
  - name: stratmaster
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 10m
        
      - alert: StorageLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
```

## Operational Procedures 

### Daily Operations

```bash
# Check service health
make health-check

# Monitor resource usage
docker stats
kubectl top pods

# Check logs for errors
docker-compose logs --tail=100 | grep ERROR
kubectl logs -l app=stratmaster-api --tail=100
```

### Backup Procedures

```bash
# Database backup
docker exec postgres pg_dump -U stratmaster stratmaster | gzip > backup-$(date +%Y%m%d).sql.gz

# Vector database backup
curl -X POST http://localhost:6333/collections/tenant_demo_research/snapshots

# Object storage backup
mc mirror local/stratmaster s3/backup-bucket/$(date +%Y%m%d)/
```

### Scaling Procedures

```bash
# Scale horizontally
docker-compose up -d --scale api=3 --scale research-mcp=2

# Kubernetes scaling
kubectl scale deployment stratmaster-api --replicas=5
kubectl autoscale deployment stratmaster-api --min=2 --max=10 --cpu-percent=70
```

For deployment-specific procedures, see the [Deployment Guide](deployment.md).