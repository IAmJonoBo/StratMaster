# API Reference

StratMaster provides a comprehensive REST API built with FastAPI, offering endpoints for research, knowledge management, strategy generation, and system administration. All APIs follow OpenAPI 3.1 specifications and include comprehensive documentation.

## API Overview

The StratMaster API ecosystem consists of:

### Gateway API
The main FastAPI application that orchestrates all operations:

- **Base URL**: `http://localhost:8080` (development) 
- **Production URL**: Configured via environment
- **OpenAPI Docs**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- **Schema**: Available at `/openapi.json`

### MCP Server APIs
Microservice APIs that handle specialized functions:

- **Research MCP** - Research plan generation and execution
- **Knowledge MCP** - Knowledge graph and vector search operations
- **Router MCP** - Request routing and load balancing
- **Evals MCP** - Strategy evaluation and quality assessment

## Interactive Documentation

Explore the API interactively:

!!! tip "Live API Documentation"
    
    - **Swagger UI**: [http://localhost:8080/docs](http://localhost:8080/docs) - Interactive testing interface
    - **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc) - Clean reference documentation
    - **OpenAPI Spec**: [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json) - Machine-readable specification

## Authentication

All API endpoints require authentication:

```http
Authorization: Bearer your-api-key-here
```

Authentication is handled through:
- JWT tokens for user sessions
- API keys for service-to-service communication
- OAuth 2.0 flows for third-party integrations

## Common Patterns

### Idempotency
All mutation operations require an idempotency key:

```http
Idempotency-Key: unique-operation-id
```

### Response Format
All responses follow a consistent structure:

```json
{
  "data": {},
  "meta": {
    "timestamp": "2024-01-18T10:30:00Z",
    "request_id": "req_123456",
    "version": "0.2.0"
  }
}
```

### Error Handling
Errors follow RFC 7807 Problem Details:

```json
{
  "type": "https://stratmaster.com/problems/validation-error",
  "title": "Validation Error", 
  "status": 400,
  "detail": "The request body contains invalid data",
  "instance": "/api/research/plan"
}
```

## Rate Limits

Default rate limits apply to all endpoints:

- **Authenticated requests**: 1000 requests per hour
- **Anonymous requests**: 100 requests per hour  
- **Burst limit**: 10 requests per second

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## API Reference Pages

- **[Gateway API](gateway.md)** - Main application endpoints with examples
- **[Research MCP](research-mcp.md)** - Research planning and execution
- **[Knowledge MCP](knowledge-mcp.md)** - Knowledge graph and retrieval
- **[Router MCP](router-mcp.md)** - Request routing and load balancing
- **[OpenAPI Specification](openapi.md)** - Complete interactive specification- [Analytics API](analytics-api.md)
- [Cache Admin API](cache_admin-api.md)
- [Collaboration API](collaboration-api.md)
- [Debate API](debate-api.md)
- [Enhanced Performance API](enhanced_performance-api.md)
- [Experts API](experts-api.md)
- [Export API](export-api.md)
- [Gateway API](gateway-api.md)
- [Ingestion API](ingestion-api.md)
- [Performance API](performance-api.md)
- [Security API](security-api.md)
- [Strategy API](strategy-api.md)
- [Templates API](templates-api.md)
- [Ui API](ui-api.md)
- [Ux Quality Gates API](ux_quality_gates-api.md)
- [Verification API](verification-api.md)
