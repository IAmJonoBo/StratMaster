# Cache Admin API

This document describes the Cache Admin endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Cache Admin API supports the following primary use cases:

1. Core cache_admin-api functionality and operations
2. Support cache_admin-api workflows and processes
3. Provide cache_admin-api data and management capabilities

## Endpoints

### GET Endpoints

#### `GET /admin/cache/config`

Endpoint handler: `get_cache_configuration`

**Implementation:** `routers/cache_admin.py:348`

---

#### `GET /admin/cache/keys/sample`

Endpoint handler: `sample_cache_keys`

**Implementation:** `routers/cache_admin.py:288`

---

#### `GET /admin/cache/memory/stats`

Endpoint handler: `get_memory_cache_stats`

**Implementation:** `routers/cache_admin.py:250`

---

#### `GET /admin/cache/performance`

Endpoint handler: `get_cache_performance_detailed`

**Implementation:** `routers/cache_admin.py:95`

---

#### `GET /admin/cache/stats`

Endpoint handler: `get_cache_statistics`

**Implementation:** `routers/cache_admin.py:78`

---

#### `GET /admin/cache/status`


**Response Example:**
```json
{
  "status": "operational",
  "uptime_seconds": 3600,
  "last_updated": "2024-01-01T12:00:00Z",
  "metrics": {
    "requests_per_minute": 45,
    "average_response_time_ms": 125
  }
}
```

**Status Values:**
- `operational`: Service is running normally
- `degraded`: Service is running with reduced performance
- `maintenance`: Service is under maintenance
- `error`: Service is experiencing issues


Get the current operational status and health metrics.

**Handler Function:** `get_cache_status`

**Implementation:** `routers/cache_admin.py:56`

---

### POST Endpoints

#### `POST /admin/cache/clear`

Endpoint handler: `clear_all_cache`

**Implementation:** `routers/cache_admin.py:209`

---

#### `POST /admin/cache/invalidate`

Endpoint handler: `invalidate_cache`

**Implementation:** `routers/cache_admin.py:157`

---

#### `POST /admin/cache/warmup`

Endpoint handler: `warmup_cache`

**Implementation:** `routers/cache_admin.py:318`

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


