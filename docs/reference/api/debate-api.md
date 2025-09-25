# Debate API

This document describes the Debate endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Debate API supports the following primary use cases:

1. Core debate-api functionality and operations
2. Support debate-api workflows and processes
3. Provide debate-api data and management capabilities

## Endpoints

### GET Endpoints

#### `GET /debate/learning/metrics`


**Query Parameters:**
- `time_range`: Time period (1h, 24h, 7d, 30d)
- `granularity`: Data granularity (minute, hour, day)
- `format`: Response format (json, csv)

**Response Example:**
```json
{
  "metric_name": "api_requests",
  "time_range": "24h",
  "data_points": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "value": 142.5,
      "labels": {
        "service": "api",
        "endpoint": "/analytics"
      }
    }
  ],
  "summary": {
    "min": 98.2,
    "max": 256.7,
    "avg": 142.5,
    "total_points": 144
  }
}
```


Fetch performance and operational metrics for monitoring.

**Handler Function:** `get_debate_learning_metrics`

**Implementation:** `routers/debate.py:431`

---

#### `GET /debate/{debate_id}/status`


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

**Handler Function:** `get_debate_status`

**Implementation:** `routers/debate.py:396`

---

### POST Endpoints

#### `POST /debate/accept`

Endpoint handler: `accept_debate`

**Implementation:** `routers/debate.py:378`

---

#### `POST /debate/escalate`

Endpoint handler: `escalate_debate`

**Implementation:** `routers/debate.py:362`

---

#### `POST /debate/learning/predict`

Endpoint handler: `predict_debate_outcome`

**Implementation:** `routers/debate.py:439`

---

#### `POST /debate/{debate_id}/pause`

Endpoint handler: `pause_debate`

**Implementation:** `routers/debate.py:406`

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


