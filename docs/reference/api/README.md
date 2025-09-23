---
title: API Reference
description: Complete reference for all StratMaster API endpoints with examples
version: 0.1.0
platform: FastAPI, REST
nav_order: 1
parent: Reference
has_children: true
---

# API Reference

Complete reference documentation for the StratMaster API. All endpoints are built with FastAPI and follow OpenAPI 3.0 specifications.

## Base Information

| Property | Value |
|----------|-------|
| **Base URL** | `http://localhost:8080` (development) |
| **API Version** | `v1` |
| **Content Type** | `application/json` |
| **Authentication** | JWT via Keycloak (production) |
| **Rate Limiting** | 1000 requests/minute per tenant |

## Interactive Documentation

- **Swagger UI**: [http://localhost:8080/docs](http://localhost:8080/docs)
- **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc)  
- **OpenAPI Schema**: [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json)

## Common Headers

All POST endpoints require an idempotency key for safe retries:

```http
Content-Type: application/json
Idempotency-Key: unique-request-id-123
```

**Idempotency Key Requirements:**
- Length: 8-128 characters
- Format: `[A-Za-z0-9_-]`
- Must be unique per request
- Same key returns cached response

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "type": "validation_error",
  "code": "INVALID_INPUT"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found
- `422` - Unprocessable Entity (schema validation)
- `500` - Internal Server Error

## API Categories

### 🔍 Research & Knowledge
Core research and knowledge management endpoints:
- [Research Operations](gateway.md#research-operations) - Planning and execution
- [Knowledge Operations](gateway.md#knowledge-operations) - Graph and retrieval
- [Ingestion](gateway.md#ingestion) - Document processing

### 🤖 AI & Analysis  
Multi-agent AI and analysis endpoints:
- [Debate System](gateway.md#debate-system) - Multi-agent validation
- [Expert Council](gateway.md#expert-council) - Domain expertise
- [Recommendations](gateway.md#recommendations) - Strategic synthesis

### 📊 Experiments & Evaluation
Strategic modeling and quality assurance:
- [Experiments](gateway.md#experiments) - Hypothesis testing
- [Forecasts](gateway.md#forecasts) - Predictive modeling
- [Evaluation Gates](gateway.md#evaluation-gates) - Quality control

### 🔧 System & Configuration
System management and configuration:
- [Health & Status](gateway.md#health-status) - System monitoring
- [Debug & Configuration](gateway.md#debug-configuration) - Development tools
- [Schema Export](gateway.md#schema-export) - Model definitions

## Quick Examples

### Health Check
```bash
curl -s http://localhost:8080/healthz
# Response: {"status":"ok"}
```

### Create Research Plan
```bash
curl -X POST http://localhost:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: example-001" \
  -d '{
    "query": "AI customer support ROI analysis",
    "tenant_id": "demo-company",
    "max_sources": 5
  }'
```

### Generate Recommendations
```bash
curl -X POST http://localhost:8080/recommendations \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: example-002" \
  -d '{
    "tenant_id": "demo-company",
    "cep_id": "cep-ai-investment",
    "risk_tolerance": "medium"
  }'
```

## Model Schemas

All request and response models are defined using Pydantic v2 with strict validation:

- **Core Models**: Source, Claim, Evidence, Assumption, Hypothesis
- **Graph Models**: GraphArtifacts, Node, Edge, Relationship  
- **Workflow Models**: DecisionBrief, RecommendationOutcome
- **AI Models**: DebateTrace, ExpertMemo, ConstitutionalCompliance

See [Model Definitions](gateway.md#model-definitions) for complete schemas.

## Rate Limits

| Endpoint Category | Requests/Minute | Concurrent |
|-------------------|------------------|------------|
| **Health/Status** | 1000 | 50 |
| **Research** | 100 | 5 |
| **AI/Debate** | 50 | 3 |
| **Evaluation** | 200 | 10 |

## Versioning

The API uses semantic versioning:
- **Major Version**: Breaking changes (e.g., v1 → v2)
- **Minor Version**: New features, backward compatible  
- **Patch Version**: Bug fixes

Current version: **v0.1.0**

## Client Libraries

Official client libraries are available:

- **Python**: `packages/providers/openai/client/python/`
- **Node.js**: `packages/providers/openai/client/node/`
- **OpenAI Tools**: Compatible with OpenAI Assistant APIs

## Support

- **API Issues**: [GitHub Issues](https://github.com/IAmJonoBo/StratMaster/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)
- **Security Issues**: [Security Policy](../../../SECURITY.md)

---

## Endpoint Categories

<div class="grid grid-2col">

### [📋 FastAPI Gateway](gateway.md)
Complete endpoint reference with examples:
- All 20 HTTP endpoints
- Request/response schemas  
- Code examples from tests
- Error handling patterns

### [🔍 MCP Servers](research-mcp.md)
Model Context Protocol server APIs:
- Research MCP (web crawling)
- Knowledge MCP (vector/graph search)
- Router MCP (model routing)
- Evals MCP (quality gates)

</div>