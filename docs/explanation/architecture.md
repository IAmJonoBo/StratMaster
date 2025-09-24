# Architecture Overview

StratMaster employs a distributed microservices architecture designed for scalability, reliability, and maintainability. This document explains the system design, component interactions, and architectural decisions.

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web UI]
        API_CLIENT[API Clients]
        CLI[CLI Tools]
    end
    
    subgraph "API Gateway"
        GATEWAY[StratMaster Gateway API<br/>:8080]
    end
    
    subgraph "MCP Services Layer"
        RESEARCH[Research MCP<br/>:8081]
        KNOWLEDGE[Knowledge MCP<br/>:8082] 
        ROUTER[Router MCP<br/>:8083]
        EVALS[Evals MCP<br/>:8084]
        COMPRESSION[Compression MCP<br/>:8085]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL<br/>Relational Data)]
        QDRANT[(Qdrant<br/>Vector Database)]
        OPENSEARCH[(OpenSearch<br/>Full-text Search)]
        NEBULA[(NebulaGraph<br/>Knowledge Graph)]
        REDIS[(Redis<br/>Caching & Sessions)]
        MINIO[(MinIO<br/>Object Storage)]
    end
    
    subgraph "Infrastructure Services"
        TEMPORAL[Temporal<br/>Workflows]
        LANGFUSE[Langfuse<br/>LLM Observability]
        KEYCLOAK[Keycloak<br/>Authentication]
    end
    
    UI --> GATEWAY
    API_CLIENT --> GATEWAY
    CLI --> GATEWAY
    
    GATEWAY --> RESEARCH
    GATEWAY --> KNOWLEDGE  
    GATEWAY --> ROUTER
    GATEWAY --> EVALS
    GATEWAY --> COMPRESSION
    
    RESEARCH --> POSTGRES
    RESEARCH --> QDRANT
    RESEARCH --> OPENSEARCH
    
    KNOWLEDGE --> QDRANT
    KNOWLEDGE --> NEBULA
    KNOWLEDGE --> OPENSEARCH
    
    ROUTER --> REDIS
    
    GATEWAY --> TEMPORAL
    GATEWAY --> LANGFUSE
    GATEWAY --> KEYCLOAK
    
    RESEARCH --> MINIO
    KNOWLEDGE --> MINIO
```

### Component Responsibilities

#### API Gateway Layer
- **StratMaster Gateway API**: Main application entry point, request orchestration, authentication
- **Responsibilities**: Request routing, authentication, rate limiting, API composition

#### MCP (Model Control Protocol) Services
- **Research MCP**: Web research, content crawling, source validation
- **Knowledge MCP**: Vector search, graph operations, knowledge synthesis  
- **Router MCP**: Intelligent request routing, load balancing, model selection
- **Evals MCP**: Quality assessment, evaluation metrics, validation
- **Compression MCP**: Content compression, summarization, optimization

#### Data Persistence Layer
- **PostgreSQL**: Transactional data, user accounts, metadata
- **Qdrant**: Vector embeddings, semantic search indices
- **OpenSearch**: Full-text search, document indexing, analytics
- **NebulaGraph**: Knowledge graph, entity relationships, graph queries
- **Redis**: Caching, session storage, temporary data
- **MinIO**: Object storage, documents, media files

#### Infrastructure Services
- **Temporal**: Workflow orchestration, long-running processes
- **Langfuse**: LLM observability, cost tracking, performance monitoring
- **Keycloak**: Authentication, authorization, user management

## Request Flow Architecture

### Research Workflow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Research
    participant Knowledge
    participant Router
    participant DB as Databases
    
    Client->>Gateway: POST /research/plan
    Gateway->>Router: Route request
    Router->>Router: Select optimal Research MCP
    Router-->>Gateway: Return routing decision
    Gateway->>Research: Plan research request
    
    Research->>DB: Query existing sources
    Research->>Research: Generate research plan
    Research-->>Gateway: Return plan with sources
    Gateway-->>Client: Research plan response
    
    Client->>Gateway: POST /research/run
    Gateway->>Research: Execute research plan
    
    par Parallel Research Execution
        Research->>Research: Crawl Source 1
        Research->>Research: Crawl Source 2  
        Research->>Research: Crawl Source N
    end
    
    Research->>Knowledge: Store extracted content
    Knowledge->>DB: Persist vectors & graph data
    Research->>DB: Store claims & provenance
    Research-->>Gateway: Research results
    Gateway-->>Client: Claims with evidence
```

### Knowledge Query Workflow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Knowledge
    participant Router
    participant Qdrant
    participant Nebula
    participant OpenSearch
    
    Client->>Gateway: POST /retrieval/hybrid/query
    Gateway->>Router: Route to Knowledge MCP
    Gateway->>Knowledge: Hybrid search request
    
    par Parallel Search
        Knowledge->>Qdrant: Dense vector search
        Knowledge->>OpenSearch: Sparse keyword search
        Knowledge->>Nebula: Graph traversal query
    end
    
    Qdrant-->>Knowledge: Vector results
    OpenSearch-->>Knowledge: Keyword results
    Nebula-->>Knowledge: Graph results
    
    Knowledge->>Knowledge: Fusion & ranking
    Knowledge-->>Gateway: Unified results
    Gateway-->>Client: Search response
```

## Service Communication Patterns

### Synchronous Communication

Primary pattern for real-time API requests:

```mermaid
graph LR
    CLIENT[Client] -->|HTTP/REST| GATEWAY[Gateway]
    GATEWAY -->|HTTP/REST| MCP[MCP Services]
    MCP -->|SQL/HTTP| DATA[Data Layer]
```

**Characteristics:**
- **Protocol**: HTTP/REST with JSON payloads
- **Timeout**: 30 seconds default, configurable per endpoint
- **Retry Logic**: Exponential backoff with circuit breakers
- **Load Balancing**: Round-robin with health checks

### Asynchronous Communication

For long-running operations and workflows:

```mermaid
graph TB
    GATEWAY[Gateway API] -->|Workflow Start| TEMPORAL[Temporal]
    TEMPORAL -->|Activity Execution| RESEARCH[Research MCP]
    TEMPORAL -->|Activity Execution| KNOWLEDGE[Knowledge MCP]
    TEMPORAL -->|Activity Execution| EVALS[Evals MCP]
    
    RESEARCH -->|Event| QUEUE[Event Queue]
    KNOWLEDGE -->|Event| QUEUE
    EVALS -->|Event| QUEUE
    
    QUEUE -->|Notification| GATEWAY
```

**Use Cases:**
- Multi-step research workflows
- Large-scale content processing
- Batch evaluation jobs
- Background model training

### Event-Driven Architecture

For reactive system behaviors:

```mermaid
graph TB
    subgraph "Event Sources"
        USER[User Actions]
        RESEARCH[Research Completion]
        KNOWLEDGE[Knowledge Updates]
        SYSTEM[System Events]
    end
    
    subgraph "Event Processing"
        QUEUE[Message Queue]
        PROCESSOR[Event Processors]
    end
    
    subgraph "Reactions"
        NOTIFICATION[Notifications]
        INDEXING[Index Updates]
        METRICS[Metrics Updates]
        WORKFLOW[Workflow Triggers]
    end
    
    USER --> QUEUE
    RESEARCH --> QUEUE  
    KNOWLEDGE --> QUEUE
    SYSTEM --> QUEUE
    
    QUEUE --> PROCESSOR
    
    PROCESSOR --> NOTIFICATION
    PROCESSOR --> INDEXING
    PROCESSOR --> METRICS
    PROCESSOR --> WORKFLOW
```

## Data Architecture

### Data Flow Patterns

```mermaid
graph TB
    subgraph "Ingestion Layer"
        WEB[Web Sources]
        API[External APIs]
        FILES[File Uploads]
        STREAMING[Real-time Streams]
    end
    
    subgraph "Processing Layer"
        ETL[ETL Pipeline]
        EMBEDDING[Embedding Generation]
        EXTRACTION[Entity Extraction]
        VALIDATION[Quality Validation]
    end
    
    subgraph "Storage Layer"
        POSTGRES[(PostgreSQL<br/>Structured Data)]
        QDRANT[(Qdrant<br/>Vectors)]
        NEBULA[(NebulaGraph<br/>Relationships)]
        OPENSEARCH[(OpenSearch<br/>Documents)]
        MINIO[(MinIO<br/>Files)]
    end
    
    subgraph "Access Layer"
        SQL[SQL Queries]
        VECTOR[Vector Search]
        GRAPH[Graph Queries]
        FULLTEXT[Full-text Search]
        OBJECT[Object Access]
    end
    
    WEB --> ETL
    API --> ETL
    FILES --> ETL
    STREAMING --> ETL
    
    ETL --> EMBEDDING
    ETL --> EXTRACTION
    ETL --> VALIDATION
    
    EMBEDDING --> QDRANT
    EXTRACTION --> NEBULA
    VALIDATION --> POSTGRES
    ETL --> OPENSEARCH
    ETL --> MINIO
    
    POSTGRES --> SQL
    QDRANT --> VECTOR
    NEBULA --> GRAPH
    OPENSEARCH --> FULLTEXT
    MINIO --> OBJECT
```

### Data Consistency Model

#### Strong Consistency
- **User accounts and authentication**: PostgreSQL with ACID transactions
- **Financial/billing data**: PostgreSQL with strict consistency
- **Configuration and system state**: PostgreSQL with immediate consistency

#### Eventual Consistency
- **Vector embeddings**: Qdrant with eventual consistency across nodes
- **Full-text indices**: OpenSearch with near real-time updates
- **Knowledge graph**: NebulaGraph with eventual consistency
- **Cache data**: Redis with TTL-based invalidation

#### Consistency Patterns

```mermaid
sequenceDiagram
    participant App
    participant Postgres
    participant Qdrant
    participant Nebula
    participant Cache
    
    Note over App,Cache: Strong Consistency Write
    App->>Postgres: Write user data
    Postgres-->>App: Transaction confirmed
    
    Note over App,Cache: Eventual Consistency Write  
    App->>Qdrant: Write vector embedding
    App->>Nebula: Write graph relationship
    Qdrant-->>App: Async confirmation
    Nebula-->>App: Async confirmation
    
    Note over App,Cache: Cache Invalidation
    App->>Cache: Invalidate related keys
    Cache-->>App: Invalidation confirmed
```

## Scalability Architecture

### Horizontal Scaling Patterns

```mermaid
graph TB
    subgraph "Load Balancers"
        LB1[Load Balancer]
        LB2[Geographic LB]
    end
    
    subgraph "API Gateway Cluster"
        GW1[Gateway 1]
        GW2[Gateway 2]
        GW3[Gateway N]
    end
    
    subgraph "MCP Service Clusters"
        subgraph "Research Cluster"
            R1[Research 1]
            R2[Research 2]
            R3[Research N]
        end
        subgraph "Knowledge Cluster"
            K1[Knowledge 1]
            K2[Knowledge 2]
            K3[Knowledge N]
        end
    end
    
    subgraph "Data Layer Clusters"
        subgraph "Database Cluster"
            PG_PRIMARY[(Primary)]
            PG_REPLICA1[(Replica 1)]
            PG_REPLICA2[(Replica N)]
        end
        subgraph "Vector Cluster"
            Q1[(Qdrant 1)]
            Q2[(Qdrant 2)]
            Q3[(Qdrant N)]
        end
    end
    
    LB1 --> GW1
    LB1 --> GW2
    LB1 --> GW3
    
    GW1 --> R1
    GW1 --> K1
    GW2 --> R2
    GW2 --> K2
    GW3 --> R3
    GW3 --> K3
    
    R1 --> PG_PRIMARY
    R2 --> PG_REPLICA1
    R3 --> PG_REPLICA2
    
    K1 --> Q1
    K2 --> Q2
    K3 --> Q3
```

### Auto-scaling Configuration

```yaml
# Kubernetes HPA Example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: stratmaster-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: stratmaster-gateway
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
```

## Security Architecture

### Authentication and Authorization Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Keycloak
    participant MCP
    participant Database
    
    Client->>Gateway: Request with credentials
    Gateway->>Keycloak: Validate credentials
    Keycloak-->>Gateway: JWT token + user info
    Gateway->>Gateway: Authorize request
    
    alt Authorized Request
        Gateway->>MCP: Forward request + user context
        MCP->>Database: Execute with user permissions
        Database-->>MCP: Query results
        MCP-->>Gateway: Response
        Gateway-->>Client: Authorized response
    else Unauthorized Request
        Gateway-->>Client: 401/403 Error
    end
```

### Network Security Architecture

```mermaid
graph TB
    subgraph "Public Zone"
        LB[Load Balancer]
        CDN[CDN]
        WAF[Web Application Firewall]
    end
    
    subgraph "DMZ"
        GW[Gateway API]
        AUTH[Authentication Service]
    end
    
    subgraph "Private Zone"
        MCP[MCP Services]
        CACHE[Redis Cluster]
    end
    
    subgraph "Data Zone"
        DB[(Databases)]
        STORAGE[(Object Storage)]
    end
    
    INTERNET -->|HTTPS| CDN
    CDN --> WAF
    WAF --> LB
    LB --> GW
    
    GW --> AUTH
    GW --> MCP
    MCP --> CACHE
    MCP --> DB
    MCP --> STORAGE
    
    classDef publicZone fill:#ffcccc
    classDef dmzZone fill:#ffffcc
    classDef privateZone fill:#ccffcc
    classDef dataZone fill:#ccccff
    
    class LB,CDN,WAF publicZone
    class GW,AUTH dmzZone
    class MCP,CACHE privateZone
    class DB,STORAGE dataZone
```

## Observability Architecture

### Monitoring and Tracing Stack

```mermaid
graph TB
    subgraph "Application Layer"
        GATEWAY[Gateway API]
        MCP[MCP Services]
        DB[Databases]
    end
    
    subgraph "Collection Layer"
        OTEL[OpenTelemetry Collector]
        PROMETHEUS[Prometheus]
        JAEGER[Jaeger]
        FLUENTD[Fluentd]
    end
    
    subgraph "Storage Layer"
        TSDB[(Time Series DB)]
        TRACES[(Trace Storage)]
        LOGS[(Log Storage)]
    end
    
    subgraph "Visualization Layer"
        GRAFANA[Grafana]
        LANGFUSE[Langfuse]
        KIBANA[Kibana]
    end
    
    GATEWAY -->|Metrics| OTEL
    GATEWAY -->|Traces| OTEL
    GATEWAY -->|Logs| FLUENTD
    
    MCP -->|Metrics| OTEL
    MCP -->|Traces| OTEL  
    MCP -->|Logs| FLUENTD
    
    DB -->|Metrics| PROMETHEUS
    
    OTEL --> PROMETHEUS
    OTEL --> JAEGER
    FLUENTD --> LOGS
    
    PROMETHEUS --> TSDB
    JAEGER --> TRACES
    
    GRAFANA --> TSDB
    GRAFANA --> TRACES
    LANGFUSE --> TRACES
    KIBANA --> LOGS
```

### Key Metrics Tracked

#### Application Metrics
- **Request Rate**: Requests per second across all services
- **Response Time**: P50, P95, P99 latency percentiles
- **Error Rate**: 4xx and 5xx error percentages
- **Throughput**: Business transactions per minute

#### Infrastructure Metrics
- **CPU Usage**: Per service and aggregate
- **Memory Usage**: Heap, off-heap, and system memory
- **Network I/O**: Bytes sent/received, connection counts
- **Disk I/O**: Read/write operations, queue depth

#### Business Metrics
- **Research Requests**: Successful research completions
- **Query Performance**: Search result quality and speed
- **User Engagement**: Active users, session duration
- **Cost Metrics**: API calls, compute usage, storage costs

## Deployment Architecture

### Multi-Environment Strategy

```mermaid
graph TB
    subgraph "Development"
        DEV_CODE[Source Code]
        DEV_BUILD[Build & Test]
        DEV_DEPLOY[Local Deployment]
    end
    
    subgraph "Staging"
        STAGE_DEPLOY[Staging Deployment]
        STAGE_TEST[Integration Tests]
        STAGE_PERF[Performance Tests]
    end
    
    subgraph "Production"
        PROD_CANARY[Canary Deployment]
        PROD_MONITOR[Monitoring]
        PROD_SCALE[Auto-scaling]
    end
    
    DEV_CODE --> DEV_BUILD
    DEV_BUILD --> DEV_DEPLOY
    DEV_DEPLOY -->|Merge to Main| STAGE_DEPLOY
    
    STAGE_DEPLOY --> STAGE_TEST
    STAGE_TEST --> STAGE_PERF
    STAGE_PERF -->|Gate Passed| PROD_CANARY
    
    PROD_CANARY --> PROD_MONITOR
    PROD_MONITOR --> PROD_SCALE
```

### Container and Orchestration

```mermaid
graph TB
    subgraph "Container Registry"
        REGISTRY[Docker Registry]
        IMAGES[Container Images]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "System Namespace"
            NGINX[NGINX Ingress]
            CERT[Cert Manager]
            MONITOR[Monitoring Stack]
        end
        
        subgraph "Application Namespace"
            GATEWAY[Gateway Pods]
            MCP[MCP Service Pods]
            WORKER[Worker Pods]
        end
        
        subgraph "Data Namespace"
            DB_OPERATOR[Database Operators]
            PERSISTENT[Persistent Volumes]
        end
    end
    
    subgraph "External Services"
        DNS[DNS Provider]
        SECRETS[Secret Manager]
        BACKUP[Backup Service]
    end
    
    REGISTRY --> IMAGES
    IMAGES --> GATEWAY
    IMAGES --> MCP
    IMAGES --> WORKER
    
    NGINX --> GATEWAY
    CERT --> NGINX
    
    GATEWAY --> MCP
    MCP --> WORKER
    
    DB_OPERATOR --> PERSISTENT
    
    DNS --> NGINX
    SECRETS --> GATEWAY
    BACKUP --> PERSISTENT
```

## Performance Characteristics

### Expected Performance Metrics

| Component | Throughput | Latency | Scalability |
|-----------|------------|---------|-------------|
| Gateway API | 10,000 req/sec | P95 < 100ms | Linear scaling |
| Research MCP | 100 concurrent crawls | 5-30s per source | CPU bound |
| Knowledge MCP | 1,000 queries/sec | P95 < 50ms | Memory bound |
| Vector Search | 500 queries/sec | P95 < 20ms | Index size dependent |
| Graph Queries | 200 queries/sec | P95 < 100ms | Complexity dependent |

### Bottleneck Analysis

#### Common Bottlenecks
1. **Database Connections**: Limited connection pool size
2. **Vector Index Size**: Memory constraints for large indices
3. **Network Bandwidth**: Large response payloads
4. **CPU Usage**: Embedding generation and inference
5. **I/O Operations**: File system and network operations

#### Mitigation Strategies
- **Connection Pooling**: Shared connections across services
- **Index Partitioning**: Distribute vectors across nodes
- **Response Compression**: Reduce payload sizes
- **Async Processing**: Non-blocking I/O operations
- **Caching**: Multi-layer caching strategy

## Disaster Recovery Architecture

### Backup and Recovery Strategy

```mermaid
graph TB
    subgraph "Primary Site"
        PRIMARY[Primary Services]
        PRIMARY_DB[(Primary Databases)]
        PRIMARY_STORAGE[(Primary Storage)]
    end
    
    subgraph "Backup Systems"
        BACKUP_DB[(Database Backups)]
        BACKUP_STORAGE[(Storage Backups)]
        BACKUP_CONFIG[Configuration Backups]
    end
    
    subgraph "Secondary Site"
        SECONDARY[Secondary Services]
        SECONDARY_DB[(Secondary Databases)]
        SECONDARY_STORAGE[(Secondary Storage)]
    end
    
    PRIMARY_DB -->|Continuous Replication| SECONDARY_DB
    PRIMARY_STORAGE -->|Async Replication| SECONDARY_STORAGE
    
    PRIMARY_DB -->|Daily Backups| BACKUP_DB
    PRIMARY_STORAGE -->|Daily Backups| BACKUP_STORAGE
    PRIMARY -->|Config Backups| BACKUP_CONFIG
    
    BACKUP_DB -->|Restore| SECONDARY_DB
    BACKUP_STORAGE -->|Restore| SECONDARY_STORAGE
    BACKUP_CONFIG -->|Deploy| SECONDARY
```

### Recovery Procedures

#### Recovery Time Objectives (RTO)
- **Database Failover**: < 5 minutes
- **Application Restart**: < 10 minutes  
- **Full System Recovery**: < 1 hour
- **Point-in-time Recovery**: < 4 hours

#### Recovery Point Objectives (RPO)
- **Critical Data**: < 1 minute (continuous replication)
- **Vector Indices**: < 15 minutes (incremental backups)
- **Configuration**: < 1 hour (scheduled backups)
- **Log Data**: < 5 minutes (near real-time streaming)

## Future Architecture Evolution

### Planned Enhancements

1. **Multi-Region Deployment**: Geographic distribution for lower latency
2. **Event Sourcing**: Complete audit trail and replay capability
3. **Serverless Components**: Function-as-a-Service for peak efficiency
4. **AI/ML Pipeline**: Integrated model training and deployment
5. **Advanced Caching**: Intelligent caching with ML-driven eviction

### Technology Roadmap

```mermaid
timeline
    title Architecture Evolution Roadmap
    
    Q1 2024 : Current State
             : Monolithic API
             : Basic MCP services
             : Single-region deployment
             
    Q2 2024 : Microservices
             : Service mesh (Istio)
             : Multi-region replication
             : Advanced monitoring
             
    Q3 2024 : Event-driven architecture
             : Serverless functions
             : ML pipeline automation
             : Edge computing
             
    Q4 2024 : AI-native architecture
             : Intelligent routing
             : Predictive scaling
             : Self-healing systems
```

## See Also

- [Multi-Agent Debate](multi-agent-debate.md) - AI collaboration architecture
- [Security Model](security.md) - Detailed security architecture  
- [Design Decisions](design-decisions.md) - Architecture decision records
- [Deployment Guide](../how-to/deployment.md) - Production deployment
- [API Reference](../reference/api/) - Detailed API specifications