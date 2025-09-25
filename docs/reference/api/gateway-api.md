# Gateway API

This document describes the Gateway endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Gateway API supports the following primary use cases:

1. Core gateway-api functionality and operations
2. Support gateway-api workflows and processes
3. Provide gateway-api data and management capabilities

## Endpoints

### POST Endpoints

#### `POST /colbert/query`

Endpoint handler: `colbert_query`

**Implementation:** `app.py:303`

---

#### `POST /plan`

Endpoint handler: `plan_research`

**Implementation:** `app.py:211`

---

#### `POST /run`

Endpoint handler: `run_debate`

**Implementation:** `app.py:263`

---

#### `POST /splade/query`

Endpoint handler: `splade_query`

**Implementation:** `app.py:315`

---

#### `POST /summarise`

Endpoint handler: `summarise_graph`

**Implementation:** `app.py:247`

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


