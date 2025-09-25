# Verification API

This document describes the Verification endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Verification API supports the following primary use cases:

1. Core verification-api functionality and operations
2. Support verification-api workflows and processes
3. Provide verification-api data and management capabilities

## Endpoints

### GET Endpoints

#### `GET /verification/status`


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

**Handler Function:** `get_verification_status`

**Implementation:** `routers/verification.py:69`

---

#### `GET /verification/{verification_id}`

Endpoint handler: `get_verification_result`

**Implementation:** `routers/verification.py:212`

---

#### `GET /verification/{verification_id}/export`

Export data in the requested format.

**Handler Function:** `export_verification_report`

**Implementation:** `routers/verification.py:231`

---

### POST Endpoints

#### `POST /verification/verify`

Endpoint handler: `verify_claims`

**Implementation:** `routers/verification.py:83`

---

#### `POST /verification/verify-single`

Endpoint handler: `verify_single_claim`

**Implementation:** `routers/verification.py:157`

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


