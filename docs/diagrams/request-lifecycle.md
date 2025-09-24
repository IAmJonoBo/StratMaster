# Request Lifecycle (StratMaster Gateway)

```mermaid
direction LR
sequenceDiagram
    participant Client as Client App
    participant API as Gateway API
    participant Router as Router MCP
    participant Service as Downstream MCPs
    participant Obs as Observability Stack
    participant Store as Data Stores

    Client->>API: Authenticated HTTP request
    API->>Router: Policy lookup / routing context
    Router-->>API: Model & service decision
    API->>Service: Forward request with tenant context
    Service->>Store: Persist events, vectors, artefacts
    Service->>Obs: Emit OTEL traces & Prometheus metrics
    API->>Obs: Push request logs & spans
    Service-->>API: Response payload / error
    API-->>Client: Response with correlation ID
```

**Notes**
- Gateway annotates each request with correlation IDs before invoking downstream MCP services.
- Downstream services publish traces/metrics that feed Grafana and Langfuse dashboards for triage.
- Data writes span PostgreSQL, Qdrant, OpenSearch, and MinIO depending on operation type.
