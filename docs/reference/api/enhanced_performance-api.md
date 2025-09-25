# Enhanced Performance API

This document describes the Enhanced Performance endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Enhanced Performance API supports the following primary use cases:

1. Core enhanced_performance-api functionality and operations
2. Support enhanced_performance-api workflows and processes
3. Provide enhanced_performance-api data and management capabilities

## Endpoints

### GET Endpoints

#### `GET /performance/retrieval/datasets`

Endpoint handler: `list_beir_datasets`

**Implementation:** `routers/enhanced_performance.py:86`

---

#### `GET /performance/retrieval/datasets/{dataset_name}`

Endpoint handler: `get_dataset_info`

**Implementation:** `routers/enhanced_performance.py:105`

---

#### `GET /performance/retrieval/status`


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

**Handler Function:** `get_retrieval_benchmarking_status`

**Implementation:** `routers/enhanced_performance.py:59`

---

#### `GET /performance/retrieval/tasks`

Endpoint handler: `list_evaluation_tasks`

**Implementation:** `routers/enhanced_performance.py:244`

---

#### `GET /performance/retrieval/tasks/{task_id}/result`

Endpoint handler: `get_task_result`

**Implementation:** `routers/enhanced_performance.py:283`

---

### POST Endpoints

#### `POST /performance/retrieval/benchmark`

Endpoint handler: `run_beir_benchmark`

**Implementation:** `routers/enhanced_performance.py:123`

---

#### `POST /performance/retrieval/quality-gates`

Validate the provided data against system rules.

**Handler Function:** `validate_quality_gates`

**Implementation:** `routers/enhanced_performance.py:191`

---

#### `POST /performance/retrieval/tasks/cleanup`

Endpoint handler: `cleanup_old_tasks`

**Implementation:** `routers/enhanced_performance.py:331`

---

### DELETE Endpoints

#### `DELETE /performance/retrieval/tasks/{task_id}`

Endpoint handler: `cancel_task`

**Implementation:** `routers/enhanced_performance.py:310`

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


