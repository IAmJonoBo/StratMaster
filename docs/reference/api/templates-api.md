# Templates API

This document describes the Templates endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Templates API supports the following primary use cases:

1. Generate industry-specific templates and frameworks
2. Render custom templates with dynamic content
3. Provide structured templates for strategic planning
4. Support template-driven content generation

## Endpoints

### GET Endpoints

#### `GET /templates/catalog`

Endpoint handler: `get_template_catalog`

**Implementation:** `routers/templates.py:127`

---

#### `GET /templates/industries`

Endpoint handler: `get_industries`

**Implementation:** `routers/templates.py:62`

---

#### `GET /templates/industry/{industry}`

Endpoint handler: `get_template_for_industry`

**Implementation:** `routers/templates.py:76`

---

#### `GET /templates/industry/{industry}/kpis`

Endpoint handler: `get_kpis_for_industry`

**Implementation:** `routers/templates.py:87`

---

### POST Endpoints

#### `POST /templates/render`

Render templates or generate formatted output.

**Handler Function:** `render_strategy_template`

**Implementation:** `routers/templates.py:102`

---



## Error Handling

All endpoints follow consistent error response patterns:

### Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional context",
      "suggestion": "How to fix the issue"
    },
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes
- `400 Bad Request`: Invalid request parameters or format
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Insufficient permissions for the operation
- `404 Not Found`: Requested resource does not exist
- `409 Conflict`: Resource conflict (e.g., already exists)
- `422 Unprocessable Entity`: Valid format but invalid content
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side processing error
- `503 Service Unavailable`: Service temporarily unavailable

### Rate Limiting
- Most endpoints are rate-limited to prevent abuse
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets


