# Strategy API

This document describes the Strategy endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Strategy API supports the following primary use cases:

1. Generate strategic analysis and recommendations
2. Create business model canvases and strategic frameworks
3. Parse and analyze strategic documents
4. Support strategic planning and decision-making processes

## Endpoints

### GET Endpoints

#### `GET /strategy/canvas/{tenant_id}`

Endpoint handler: `get_business_model_canvas`

**Implementation:** `routers/strategy.py:696`

---

### POST Endpoints

#### `POST /strategy/brief`

Generate new content or analysis based on input parameters.

**Handler Function:** `generate_strategy_brief`

**Implementation:** `routers/strategy.py:685`

---

#### `POST /strategy/parse`

Endpoint handler: `parse_document`

**Implementation:** `routers/strategy.py:661`

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


