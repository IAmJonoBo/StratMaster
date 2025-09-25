# Knowledge MCP API Reference

The Knowledge MCP (Model Control Protocol) server manages vector and graph-based knowledge operations, providing semantic search, knowledge graph construction, and intelligent information retrieval capabilities.

## Service Information

- **Port**: 8082 (when running full stack)
- **URL**: http://localhost:8082
- **Protocol**: HTTP/REST API
- **Purpose**: Vector and graph search operations

## Overview

The Knowledge MCP provides comprehensive knowledge management through multiple retrieval paradigms:

1. **Vector Search** - Dense and sparse embedding-based retrieval using ColBERT and SPLADE
2. **Graph Operations** - Knowledge graph construction, traversal, and analysis using NebulaGraph
3. **Hybrid Retrieval** - Combined vector and graph search with intelligent result fusion
4. **Knowledge Extraction** - Entity recognition, relationship extraction, and concept mapping
5. **Semantic Analysis** - Content understanding, similarity assessment, and conceptual clustering

## Core Capabilities

### Vector Operations
- **Dense Retrieval**: ColBERT-based semantic similarity search
- **Sparse Retrieval**: SPLADE keyword expansion and sparse attention
- **Hybrid Search**: Intelligent combination of dense and sparse results
- **Embedding Management**: Efficient vector storage and retrieval using Qdrant

### Graph Operations  
- **Entity Extraction**: Automatic identification of entities and concepts
- **Relationship Mapping**: Discovery and modeling of entity relationships
- **Graph Traversal**: Pathfinding and neighborhood exploration
- **Subgraph Analysis**: Community detection and cluster analysis

### Knowledge Synthesis
- **Concept Consolidation**: Merging and deduplicating knowledge from multiple sources
- **Contradiction Detection**: Identifying conflicting information across sources
- **Knowledge Gap Analysis**: Detecting missing information and research opportunities
- **Temporal Reasoning**: Understanding time-based relationships and changes

## API Endpoints

!!! note "Integration Pattern"
    Knowledge MCP endpoints are typically accessed through the Gateway API's `/graph/*` and `/retrieval/*` routes for standardized authentication and request handling.

### Vector Search Endpoints

#### Dense Vector Query (ColBERT)
```http
POST /retrieval/colbert/query
```
Performs semantic search using ColBERT dense embeddings.

**Request:**
```json
{
  "query": "sustainable packaging innovations",
  "top_k": 20,
  "tenant_id": "demo",
  "filters": {
    "document_type": ["research_report", "news_article"],
    "date_range": {
      "start": "2023-01-01",
      "end": "2024-12-31"
    },
    "relevance_threshold": 0.7
  },
  "rerank": true
}
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc_001",
      "content": "Recent innovations in sustainable packaging...",
      "score": 0.94,
      "metadata": {
        "source": "https://example.com/report",
        "document_type": "research_report",
        "publication_date": "2024-01-15",
        "author": "Sustainability Research Institute"
      },
      "highlights": [
        "Recent <mark>innovations</mark> in <mark>sustainable packaging</mark> include..."
      ]
    }
  ],
  "total_results": 156,
  "query_time_ms": 234,
  "embedding_time_ms": 45,
  "search_time_ms": 189
}
```

#### Sparse Vector Query (SPLADE)
```http
Performs keyword-expansion based sparse retrieval.

#### Hybrid Retrieval
```http
POST /retrieval/hybrid/query
```
Combines dense and sparse search with intelligent result fusion.

**Request:**
```json
{
  "query": "market trends sustainable packaging",
  "dense_weight": 0.7,
  "sparse_weight": 0.3,
  "fusion_method": "reciprocal_rank",
  "top_k": 15,
  "tenant_id": "demo"
}
```

### Graph Operations

#### Knowledge Graph Summary
```http
POST /graph/summarise
```
Provides comprehensive graph analytics and summaries.

**Request:**
```json
{
  "tenant_id": "demo",
  "focus": "sustainability",
  "analysis_type": "comprehensive",
  "limit": 100,
  "include_metrics": true
}
```

**Response:**
```json
{
  "summary": {
    "total_entities": 1247,
    "total_relationships": 3891,
    "entity_types": {
      "Company": 234,
      "Product": 189,
      "Technology": 156,
      "Market": 98,
      "Regulation": 67
    },
    "relationship_types": {
      "PRODUCES": 445,
      "COMPETES_WITH": 234, 
      "REGULATED_BY": 189,
      "IMPACTS": 156
    }
  },
  "focus_analysis": {
    "central_entities": [
      {
        "entity": "Sustainable Packaging Alliance",
        "type": "Organization",
        "centrality_score": 0.89,
        "connection_count": 67
      }
    ],
    "key_relationships": [
      "Sustainability -> DRIVES -> Innovation",
      "Regulation -> INFLUENCES -> Packaging_Standards"
    ]
  },
  "insights": [
    "Strong clustering around sustainable materials innovation",
    "Emerging regulation-driven market changes",
    "Growing B2B partnership networks in sustainable packaging"
  ]
}
```

#### Entity Extraction
```http
POST /graph/extract/entities
```
Extracts entities and relationships from content.

#### Graph Traversal
```http
Performs pathfinding and neighborhood analysis.

**Request:**
```json
{
  "start_entity": "Sustainable_Packaging",
  "traversal_type": "neighborhood",
  "max_depth": 3,
  "relationship_filters": ["RELATED_TO", "PRODUCES", "INFLUENCES"],
  "limit": 50
}
```

### Knowledge Synthesis

#### Concept Consolidation
```http
Merges and deduplicates knowledge from multiple sources.

#### Contradiction Detection
```http
POST /knowledge/validate/consistency
```
Identifies conflicting information across knowledge sources.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KNOWLEDGE_MCP_PORT` | 8082 | Service port |
| `QDRANT_URL` | `http://localhost:6333` | Vector database URL |
| `NEBULA_GRAPH_HOST` | `localhost` | Graph database host |
| `NEBULA_GRAPH_PORT` | 9669 | Graph database port |
| `COLBERT_MODEL_PATH` | `./models/colbert` | ColBERT model location |
| `SPLADE_MODEL_PATH` | `./models/splade` | SPLADE model location |
| `MAX_QUERY_LENGTH` | 512 | Maximum query token length |
| `DEFAULT_TOP_K` | 10 | Default result count |

### Model Configuration

```yaml
# configs/knowledge/retrieval-models.yaml
dense_retrieval:
  model: "colbert-base"
  dimension: 768
  max_tokens: 512
  batch_size: 32

sparse_retrieval:
  model: "splade-max"
  vocabulary_size: 30522
  regularization: 0.01
  
hybrid_fusion:
  fusion_method: "reciprocal_rank"
  dense_weight: 0.7
  sparse_weight: 0.3
  normalization: "minmax"

graph_embeddings:
  node_embedding_dim: 256
  relationship_embedding_dim: 128
  walk_length: 10
  walks_per_node: 80
```

## Performance Optimization

### Vector Search Performance
- **Index Type**: HNSW for fast approximate search
- **Quantization**: 4-bit quantization for memory efficiency  
- **Batch Processing**: Automatic query batching for throughput
- **Caching**: LRU cache for frequent queries

### Graph Query Optimization
- **Index Strategy**: Composite indexes on entity types and properties
- **Query Planning**: Automatic query plan optimization
- **Partitioning**: Tenant-based graph partitioning
- **Connection Pooling**: Efficient database connection management

## Integration Examples

### Python SDK Integration
```python
from knowledge_mcp_client import KnowledgeMCPClient

async def semantic_search_example():
    client = KnowledgeMCPClient("http://localhost:8082")
    
    # Dense vector search
    results = await client.search_dense(
        query="sustainable packaging innovations",
        top_k=10,
        tenant_id="demo"
    )
    
    # Graph traversal  
    graph_data = await client.traverse_graph(
        start_entity="Sustainable_Packaging",
        max_depth=2,
        tenant_id="demo"
    )
    
    return results, graph_data
```

### Direct HTTP Integration
```python
import httpx

async def hybrid_search_example():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8082/retrieval/hybrid/query",
            json={
                "query": "market trends sustainable packaging",
                "dense_weight": 0.8,
                "sparse_weight": 0.2,
                "top_k": 20,
                "tenant_id": "demo"
            }
        )
        return response.json()
```

## Advanced Features

### Multi-Modal Retrieval
Support for different content types:
- **Text**: Standard semantic search and keyword matching
- **Images**: Visual similarity search using CLIP embeddings
- **Documents**: PDF and structured document processing
- **Tables**: Tabular data understanding and querying

### Temporal Knowledge Management
- **Version Control**: Track knowledge evolution over time
- **Temporal Queries**: Search with time-based constraints
- **Change Detection**: Identify knowledge updates and modifications
- **Historical Analysis**: Trend analysis across time periods

## Error Handling

### Common Error Patterns

| Error Code | Description | Common Causes |
|------------|-------------|---------------|
| `400` | Invalid query format | Malformed JSON, invalid parameters |
| `413` | Query too large | Exceeds max_query_length limit |  
| `503` | Vector database unavailable | Qdrant connection issues |
| `504` | Query timeout | Complex graph traversal or large result sets |

### Error Response Structure
```json
{
  "error": {
    "type": "VECTOR_SEARCH_ERROR",
    "message": "Query embedding failed",
    "details": {
      "model": "colbert-base",
      "query_length": 1024,
      "max_supported": 512
    },
    "suggestions": [
      "Reduce query length",
      "Use query truncation",
      "Split into multiple queries"
    ]
  }
}
```

## Monitoring and Metrics

### Performance Metrics
- **Query Latency**: P50, P95, P99 response times
- **Throughput**: Queries per second capacity
- **Cache Hit Rate**: Vector and graph cache effectiveness
- **Model Performance**: Embedding generation times

### Quality Metrics  
- **Retrieval Accuracy**: Relevance of returned results
- **Graph Connectivity**: Knowledge graph completeness
- **Consistency Scores**: Cross-source information alignment
- **Coverage Analysis**: Knowledge domain completeness

## Security and Privacy

### Data Protection
- **Tenant Isolation**: Complete data separation by tenant
- **Encryption**: Data encrypted at rest and in transit  
- **Access Control**: Role-based access to knowledge domains
- **Audit Logging**: Complete operation audit trails

### Content Safety
- **PII Detection**: Automatic identification and handling of sensitive data
- **Content Filtering**: Inappropriate content detection and removal
- **Source Validation**: Content origin verification and trustworthiness scoring

## See Also

- [Gateway API Reference](gateway.md) - Main API orchestration layer
- [Research MCP API](research-mcp.md) - Research and content collection
- [Configuration Reference](../configuration/yaml-configs.md#knowledge-retrieval) - Knowledge system configuration
- [Troubleshooting Guide](../../how-to/troubleshooting.md#knowledge-retrieval-issues) - Common issues and solutions