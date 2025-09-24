# StratMaster System Architecture

This document provides comprehensive architectural diagrams for the StratMaster platform using Mermaid notation.

## System Overview

```mermaid
graph TB
    User[User Interface] --> API[StratMaster API]
    API --> Auth[Authentication Service]
    API --> Collab[Collaboration Service]
    API --> Analytics[Analytics Engine]
    API --> Events[Event Bus]
    
    API --> MCP[MCP Services Layer]
    MCP --> Research[Research MCP]
    MCP --> Knowledge[Knowledge MCP] 
    MCP --> Router[Router MCP]
    MCP --> Evals[Evals MCP]
    MCP --> Compression[Compression MCP]
    
    API --> Data[Data Layer]
    Data --> PG[(PostgreSQL)]
    Data --> Qdrant[(Qdrant)]
    Data --> Neo4j[(NebulaGraph)]
    Data --> OpenSearch[(OpenSearch)]
    Data --> Redis[(Redis)]
    Data --> MinIO[(MinIO)]
    
    Events --> RedisStreams[Redis Streams]
    Events --> Kafka[Kafka]
    
    Analytics --> ML[ML Pipeline]
    ML --> Prophet[Prophet Forecasting]
    ML --> MLflow[MLflow Registry]
    
    Auth --> Keycloak[Keycloak]
    
    API --> External[External Integrations]
    External --> Notion[Notion API]
    External --> Trello[Trello API]
    External --> Jira[Jira API]
    
    classDef primary fill:#e1f5fe
    classDef secondary fill:#f3e5f5
    classDef database fill:#e8f5e8
    classDef external fill:#fff3e0
    
    class User,API primary
    class MCP,Auth,Collab,Analytics,Events secondary
    class PG,Qdrant,Neo4j,OpenSearch,Redis,MinIO database
    class External,Notion,Trello,Jira,Keycloak external
```

## Request Lifecycle Flow

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant Auth
    participant Events
    participant MCP
    participant DB
    participant Analytics
    
    User->>UI: Create Strategy Request
    UI->>API: POST /strategy
    API->>Auth: Verify Token
    Auth-->>API: Token Valid
    
    API->>Events: Emit StrategyCreated Event
    Events->>Analytics: Process Event
    
    API->>MCP: Research Request
    MCP->>DB: Query Knowledge
    DB-->>MCP: Knowledge Data
    MCP-->>API: Research Results
    
    API->>MCP: Generate Strategy
    MCP->>DB: Store Strategy
    MCP-->>API: Strategy Response
    
    API->>Events: Emit StrategyCompleted Event
    API-->>UI: Strategy Result
    UI-->>User: Display Strategy
    
    Analytics->>DB: Store Metrics
```

## Event-Driven Architecture

```mermaid
graph LR
    subgraph "Event Producers"
        API[API Services]
        Collab[Collaboration Service]
        MCP[MCP Services]
    end
    
    subgraph "Event Streaming"
        Redis[Redis Streams]
        Kafka[Kafka Topics]
    end
    
    subgraph "Event Consumers"
        Analytics[Analytics Consumer]
        Audit[Audit Consumer] 
        Notification[Notification Consumer]
        ML[ML Pipeline Consumer]
    end
    
    API --> Redis
    Collab --> Redis
    MCP --> Redis
    
    Redis --> Kafka
    
    Kafka --> Analytics
    Kafka --> Audit
    Kafka --> Notification  
    Kafka --> ML
    
    Analytics --> MetricsDB[(Metrics DB)]
    Audit --> AuditDB[(Audit DB)]
    Notification --> Users[User Notifications]
    ML --> ModelRegistry[Model Registry]
    
    classDef producer fill:#e3f2fd
    classDef streaming fill:#f1f8e9
    classDef consumer fill:#fce4ec
    classDef storage fill:#fff8e1
    
    class API,Collab,MCP producer
    class Redis,Kafka streaming
    class Analytics,Audit,Notification,ML consumer
    class MetricsDB,AuditDB,Users,ModelRegistry storage
```

## Predictive Analytics Pipeline

```mermaid
flowchart TB
    subgraph "Data Sources"
        UserActions[User Actions]
        StrategyData[Strategy Data]
        PerformanceMetrics[Performance Metrics]
        ExternalData[External Data]
    end
    
    subgraph "Data Pipeline"
        Ingestion[Data Ingestion]
        Processing[Data Processing]
        FeatureStore[Feature Store]
    end
    
    subgraph "ML Pipeline"
        Prophet[Prophet Models]
        HEART[HEART Metrics ML]
        BusinessML[Business Metrics ML]
        ModelRegistry[MLflow Registry]
    end
    
    subgraph "Serving Layer"
        PredictionAPI[Prediction API]
        Cache[Prediction Cache]
        Fallback[Heuristic Fallback]
    end
    
    subgraph "Applications"
        Dashboard[Analytics Dashboard]
        Alerts[Predictive Alerts]
        Recommendations[AI Recommendations]
    end
    
    UserActions --> Ingestion
    StrategyData --> Ingestion
    PerformanceMetrics --> Ingestion
    ExternalData --> Ingestion
    
    Ingestion --> Processing
    Processing --> FeatureStore
    
    FeatureStore --> Prophet
    FeatureStore --> HEART
    FeatureStore --> BusinessML
    
    Prophet --> ModelRegistry
    HEART --> ModelRegistry
    BusinessML --> ModelRegistry
    
    ModelRegistry --> PredictionAPI
    PredictionAPI --> Cache
    Cache --> Fallback
    
    PredictionAPI --> Dashboard
    PredictionAPI --> Alerts
    PredictionAPI --> Recommendations
    
    classDef data fill:#e8eaf6
    classDef pipeline fill:#e0f2f1
    classDef ml fill:#fce4ec
    classDef serving fill:#fff3e0
    classDef app fill:#f3e5f5
    
    class UserActions,StrategyData,PerformanceMetrics,ExternalData data
    class Ingestion,Processing,FeatureStore pipeline
    class Prophet,HEART,BusinessML,ModelRegistry ml
    class PredictionAPI,Cache,Fallback serving
    class Dashboard,Alerts,Recommendations app
```

## Industry Templates Architecture

```mermaid
graph TB
    subgraph "Template Management"
        TemplateEngine[Template Engine]
        TemplateRegistry[Template Registry]
        Validator[Template Validator]
    end
    
    subgraph "Industry Templates"
        Tech[Technology Template]
        Healthcare[Healthcare Template]
        Fintech[Fintech Template]
        Retail[Retail Template]
        Generic[Generic Template]
    end
    
    subgraph "Template Components"
        Metadata[Template Metadata]
        KPIs[Industry KPIs]
        Jinja[Jinja Templates]
        Variables[Template Variables]
    end
    
    subgraph "Strategy Generation"
        API[Strategy API]
        Synthesizer[Strategy Synthesizer]
        Renderer[Template Renderer]
    end
    
    API --> TemplateEngine
    TemplateEngine --> TemplateRegistry
    TemplateRegistry --> Tech
    TemplateRegistry --> Healthcare
    TemplateRegistry --> Fintech
    TemplateRegistry --> Retail
    TemplateRegistry --> Generic
    
    Tech --> Metadata
    Tech --> KPIs
    Tech --> Jinja
    Tech --> Variables
    
    TemplateEngine --> Validator
    TemplateEngine --> Synthesizer
    Synthesizer --> Renderer
    
    Renderer --> Output[Industry-Specific Strategy]
    
    classDef engine fill:#e1f5fe
    classDef template fill:#f3e5f5
    classDef component fill:#e8f5e8
    classDef generation fill:#fff3e0
    
    class TemplateEngine,TemplateRegistry,Validator engine
    class Tech,Healthcare,Fintech,Retail,Generic template
    class Metadata,KPIs,Jinja,Variables component
    class API,Synthesizer,Renderer generation
```

## Security & Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant Gateway
    participant Keycloak
    participant Services
    participant Audit
    
    User->>UI: Login Request
    UI->>Keycloak: Authenticate
    Keycloak-->>UI: JWT Token
    
    UI->>API: Request with JWT
    API->>Gateway: Validate Token
    Gateway->>Keycloak: Token Verification
    Keycloak-->>Gateway: Token Valid
    
    Gateway->>API: Forward Request
    API->>Services: Process Request
    Services-->>API: Response
    
    API->>Audit: Log Access
    API-->>UI: Response
    UI-->>User: Display Result
    
    Note over Audit: All actions logged for compliance
    Note over Gateway: Rate limiting & security policies applied
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Load Balancer]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "API Tier"
            API1[API Pod 1]
            API2[API Pod 2]
            API3[API Pod 3]
        end
        
        subgraph "MCP Services"
            Research[Research MCP]
            Knowledge[Knowledge MCP]
            Router[Router MCP]
        end
        
        subgraph "Supporting Services"
            Collab[Collaboration]
            Analytics[Analytics]
            Events[Event Streaming]
        end
    end
    
    subgraph "Data Persistence"
        PG[(PostgreSQL Cluster)]
        Redis[(Redis Cluster)]
        Vector[(Vector DBs)]
        Files[(Object Storage)]
    end
    
    subgraph "External Services"
        Keycloak[Keycloak]
        Monitoring[Monitoring Stack]
        Logging[Logging Stack]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Research
    API2 --> Knowledge
    API3 --> Router
    
    Research --> PG
    Knowledge --> Vector
    Router --> Redis
    
    Analytics --> Events
    Events --> Redis
    
    API1 --> Keycloak
    API2 --> Monitoring
    API3 --> Logging
    
    classDef api fill:#e3f2fd
    classDef service fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef external fill:#fce4ec
    
    class API1,API2,API3 api
    class Research,Knowledge,Router,Collab,Analytics,Events service
    class PG,Redis,Vector,Files data
    class Keycloak,Monitoring,Logging external
```

## Data Flow Architecture

```mermaid
flowchart LR
    subgraph "Input Sources"
        UserInput[User Input]
        Documents[Documents]
        APIs[External APIs]
        Sensors[Performance Sensors]
    end
    
    subgraph "Ingestion Layer"
        APIGateway[API Gateway]
        MessageQueue[Message Queue]
        StreamProcessor[Stream Processor]
    end
    
    subgraph "Processing Layer"
        Orchestrator[Orchestrator]
        MCP[MCP Services]
        MLPipeline[ML Pipeline]
        Analytics[Analytics Engine]
    end
    
    subgraph "Storage Layer"
        OLTP[(OLTP - PostgreSQL)]
        Vector[(Vector - Qdrant)]
        Graph[(Graph - NebulaGraph)]
        Search[(Search - OpenSearch)]
        Cache[(Cache - Redis)]
        Files[(Files - MinIO)]
    end
    
    subgraph "Output Layer"
        WebUI[Web UI]
        API[REST API]
        Webhooks[Webhooks]
        Exports[Export Integrations]
    end
    
    UserInput --> APIGateway
    Documents --> MessageQueue
    APIs --> StreamProcessor
    Sensors --> StreamProcessor
    
    APIGateway --> Orchestrator
    MessageQueue --> MCP
    StreamProcessor --> Analytics
    
    Orchestrator --> OLTP
    MCP --> Vector
    MCP --> Graph
    MLPipeline --> Search
    Analytics --> Cache
    
    OLTP --> WebUI
    Vector --> API
    Cache --> Webhooks
    Files --> Exports
    
    classDef input fill:#e8eaf6
    classDef ingest fill:#e0f2f1
    classDef process fill:#fce4ec
    classDef storage fill:#fff8e1
    classDef output fill:#f3e5f5
    
    class UserInput,Documents,APIs,Sensors input
    class APIGateway,MessageQueue,StreamProcessor ingest
    class Orchestrator,MCP,MLPipeline,Analytics process
    class OLTP,Vector,Graph,Search,Cache,Files storage
    class WebUI,API,Webhooks,Exports output
```