# Analytics API

This document describes the Analytics endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.



## Use Cases

This Analytics API supports the following primary use cases:

1. Monitor system performance and user engagement metrics
2. Generate business intelligence dashboards and reports
3. Track HEART metrics (Happiness, Engagement, Adoption, Retention, Task success)
4. Forecast trends and predict future performance patterns

## Endpoints

### GET Endpoints

#### `GET /analytics/dashboard/{dashboard_id}`

Retrieve data for the specified resource with optional filtering.

**Handler Function:** `get_dashboard_data`

**Implementation:** `routers/analytics.py:82`

---

#### `GET /analytics/forecast/heart/{tenant_id}`

Endpoint handler: `get_heart_metrics_forecast`

**Implementation:** `routers/analytics.py:162`

---

#### `GET /analytics/forecast/product/{tenant_id}`

Endpoint handler: `get_product_metrics_forecast`

**Implementation:** `routers/analytics.py:174`

---

#### `GET /analytics/metrics/{metric_name}`


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


Retrieve data for the specified resource with optional filtering.

**Handler Function:** `get_metric_data`

**Implementation:** `routers/analytics.py:54`

---

#### `GET /analytics/report/{report_type}`

Generate new content or analysis based on input parameters.

**Handler Function:** `generate_analytics_report`

**Implementation:** `routers/analytics.py:135`

---

#### `GET /analytics/status`


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

**Handler Function:** `get_analytics_status`

**Implementation:** `routers/analytics.py:39`

---

### POST Endpoints

#### `POST /analytics/forecast/custom`

Create a new resource with the provided parameters.

**Handler Function:** `create_custom_forecast`

**Implementation:** `routers/analytics.py:186`

---

#### `POST /analytics/metrics/{metric_name}/record`

Endpoint handler: `record_metric`

**Implementation:** `routers/analytics.py:112`

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


