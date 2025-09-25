# Gateway API Reference

The StratMaster Gateway API is the main FastAPI application that orchestrates all system operations. It provides a unified interface for research, knowledge operations, multi-agent debate, and strategic recommendations.

## Base URL

When running locally: `http://127.0.0.1:8080`

## Authentication

All POST endpoints require the `Idempotency-Key` header:
- **Header**: `Idempotency-Key`
- **Format**: 8-128 characters, alphanumeric with underscores and hyphens (`[A-Za-z0-9_-]`)
- **Purpose**: Prevents duplicate operations and ensures request idempotency

Example:
```bash
curl -X POST "http://127.0.0.1:8080/research/plan" \
  -H "Idempotency-Key: req-123456789" \
  -H "Content-Type: application/json" \
  -d '{"query": "market analysis", "tenant_id": "demo", "max_sources": 5}'
```

## Health and Status Endpoints

### Health Check
```http
GET /healthz
```

**Response:**
```json
{
  "status": "ok"
}
```

## Research Endpoints

### Plan Research
```http
POST /research/plan
```

Builds a research task list and identifies candidate sources for investigation.

**Request Body:**
```json
{
  "query": "string",
  "tenant_id": "string", 
  "max_sources": 10
}
```

**Response:**
```json
{
  "plan_id": "string",
  "tasks": ["string"],
  "sources": [
    {
      "url": "string",
      "title": "string", 
      "relevance": 0.95
    }
  ]
}
```

### Execute Research
```http
POST /research/run
```

Executes a research plan and returns claims, assumptions, and graph artifacts.

**Request Body:**
```json
{
  "plan_id": "string",
  "tenant_id": "string"
}
```

**Response:**
```json
{
  "research_id": "string",
  "claims": ["string"],
  "assumptions": ["string"],
  "graph_artifacts": {}
}
```

## Knowledge Graph Endpoints

### Summarise Graph
```http
POST /graph/summarise
```

Returns graph summaries and diagnostics for the knowledge graph.

**Request Body:**
```json
{
  "tenant_id": "string",
  "focus": "string",
  "limit": 50
}
```

## Multi-Agent Debate Endpoints

### Run Debate
```http
POST /debate/run
```

Triggers multi-agent debate process and returns verdict.

**Request Body:**
```json
{
  "tenant_id": "string",
  "hypothesis_id": "string",
  "claim_ids": ["string"],
  "max_turns": 5
}
```

## Strategic Recommendations

### Generate Recommendations
```http
POST /recommendations
```

Generates structured strategic recommendations based on research and debate outcomes.

**Request Body:**
```json
{
  "tenant_id": "string",
  "cep_id": "string",
  "jtbd_ids": ["string"],
  "risk_tolerance": "medium"
}
```

## Retrieval Endpoints

### ColBERT Query
```http
POST /retrieval/colbert/query
```

Performs dense retrieval using ColBERT embeddings.

### SPLADE Query  
```http

Performs sparse retrieval using SPLADE representations.

**Request Body (both endpoints):**
```json
{
  "tenant_id": "string",
  "query": "string",
  "top_k": 10
}
```

## Experiment and Forecast Endpoints

### Create Experiment
```http
POST /experiments
```

Creates an experiment placeholder for tracking research iterations.

### Create Forecast
```http

Generates synthetic forecast objects for scenario planning.

## Evaluation Endpoints

### Run Evaluations
```http
POST /evals/run
```

Executes evaluation suite and returns quality metrics.

**Request Body:**
```json
{
  "tenant_id": "string",
  "suite": "string"
}
```

## Schema Endpoints

### List Model Schemas
```http
GET /schemas/models
```

Returns all available Pydantic model schemas with version information.

### Get Model Schema
```http
GET /schemas/models/{name}
```

Returns specific model schema definition.

## Debug Endpoints

!!! warning "Debug Only"
    Debug endpoints are only available when `STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1` environment variable is set.

### Get Configuration
```http
GET /debug/config/{section}/{name}
```

Returns configuration for specific section and name.

**Supported Sections:**
- `router` - Model routing configurations
- `retrieval` - Retrieval system settings
- `evals` - Evaluation thresholds
- `privacy` - Privacy and redaction rules
- `compression` - Compression configurations

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Successful operation
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

Error responses include detailed error messages:
```json
{
  "detail": "Error description"
}
```

## Rate Limiting

The API implements standard FastAPI rate limiting. Clients should implement exponential backoff for retries.

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Spec**: `/openapi.json`

## Examples

### Complete Research Workflow

1. Plan research:
```bash
curl -X POST "http://127.0.0.1:8080/research/plan" \
  -H "Idempotency-Key: plan-001" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sustainable packaging trends 2024",
    "tenant_id": "demo",
    "max_sources": 10
  }'
```

2. Execute research:
```bash
curl -X POST "http://127.0.0.1:8080/research/run" \
  -H "Idempotency-Key: run-001" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "plan-123",
    "tenant_id": "demo"
  }'
```

3. Generate recommendations:
```bash
curl -X POST "http://127.0.0.1:8080/recommendations" \
  -H "Idempotency-Key: rec-001" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "demo",
    "cep_id": "sustainability-initiative",
    "jtbd_ids": ["reduce-environmental-impact"],
    "risk_tolerance": "medium"
  }'
```

## See Also

- [Research MCP API](research-mcp.md) - Research orchestration service
- [Knowledge MCP API](knowledge-mcp.md) - Knowledge graph operations  
- [Router MCP API](router-mcp.md) - Request routing and load balancing
- [OpenAPI Specification](openapi.md) - Interactive documentation