# Security API

This document describes the Security endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Security API supports the following primary use cases:

1. Implement authentication and authorization workflows
2. Monitor security events and generate compliance reports
3. Scan for vulnerabilities and security issues
4. Manage user permissions and access control

## Endpoints

### GET Endpoints

#### `GET /security/audit-logs/{tenant_id}`

Endpoint handler: `get_audit_logs`

**Implementation:** `routers/security.py:408`

---

#### `GET /security/compliance-report/{tenant_id}`

Endpoint handler: `get_compliance_report`

**Implementation:** `routers/security.py:463`

---

#### `GET /security/oidc/userinfo`

Endpoint handler: `get_oidc_userinfo`

**Implementation:** `routers/security.py:675`

---

#### `GET /security/permissions`

Endpoint handler: `get_user_permissions`

**Implementation:** `routers/security.py:485`

---

### POST Endpoints

#### `POST /security-alert`

Create a new resource with the provided parameters.

**Handler Function:** `create_security_alert`

**Implementation:** `routers/security.py:499`

---

#### `POST /security/oidc/callback`

Endpoint handler: `handle_oidc_callback`

**Implementation:** `routers/security.py:666`

---

#### `POST /security/oidc/login`

Endpoint handler: `initiate_oidc_login`

**Implementation:** `routers/security.py:657`

---

#### `POST /security/pii-scan`

Scan resources for issues, vulnerabilities, or patterns.

**Handler Function:** `scan_for_pii`

**Implementation:** `routers/security.py:436`

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


