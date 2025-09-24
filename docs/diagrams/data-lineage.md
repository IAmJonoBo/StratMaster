# Data Lineage & Storage Flow

```mermaid
flowchart TD
    subgraph Ingestion
        Crawl[Research MCP Crawlers]
        Uploads[User Uploads]
        External[Third-party Integrations]
    end

    subgraph Processing
        ETL[Ingestion & PII Scrub]
        Claims[Evidence Extraction]
        Embeddings[Vector Encoding]
        Graph[Graph Construction]
    end

    subgraph Storage
        PG[(PostgreSQL)]
        Qdrant[(Qdrant)]
        OpenSearch[(OpenSearch)]
        Nebula[(NebulaGraph)]
        MinIO[(MinIO Object Store)]
    end

    subgraph Downstream
        API[Gateway API]
        Analytics[Analytics & Dashboards]
        Exports[Export Connectors]
    end

    Crawl --> ETL
    Uploads --> ETL
    External --> ETL

    ETL --> Claims
    Claims --> PG
    Claims --> MinIO

    ETL --> Embeddings
    Embeddings --> Qdrant

    ETL --> Graph
    Graph --> Nebula

    ETL --> OpenSearch

    PG --> API
    Qdrant --> API
    OpenSearch --> API
    Nebula --> API
    MinIO --> API

    API --> Analytics
    API --> Exports
```

**Notes**
- Ingestion applies PII scrubbing before persistence to meet compliance expectations.
- Gateway federates reads across PostgreSQL, Qdrant, OpenSearch, and NebulaGraph to assemble strategy responses.
- Export connectors consume curated artefacts from MinIO and relational sources.
