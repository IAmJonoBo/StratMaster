# Router MCP API Reference

The Router MCP (Model Control Protocol) server handles intelligent request routing, load balancing, and model selection across the StratMaster ecosystem. It provides policy-driven routing decisions and performance optimization.

## Service Information

- **Port**: 8083 (when running full stack)
- **URL**: http://localhost:8083  
- **Protocol**: HTTP/REST API
- **Purpose**: Request routing and load balancing

## Overview

The Router MCP serves as the intelligent traffic director for StratMaster operations:

1. **Request Routing** - Intelligent routing based on request type, payload, and system load
2. **Load Balancing** - Distribution of requests across available service instances
3. **Model Selection** - Dynamic model selection based on task requirements and performance
4. **Circuit Breaking** - Fault tolerance and graceful degradation when services are unavailable
5. **Policy Enforcement** - Tenant quotas, rate limiting, and access control

## Core Capabilities

### Intelligent Routing
- **Content-Based Routing**: Route based on request content, complexity, and requirements
- **Performance Routing**: Direct requests to best-performing instances
- **Geographic Routing**: Route to geographically optimal service instances
- **Tenant-Aware Routing**: Isolated routing paths for different tenants

### Load Balancing Strategies
- **Round Robin**: Sequential distribution across healthy instances
- **Weighted Round Robin**: Distribution based on instance capacity
- **Least Connections**: Route to instance with fewest active connections
- **Response Time Based**: Route to fastest-responding instances

### Model Management
- **Dynamic Model Selection**: Choose optimal models based on task characteristics
- **Model Performance Tracking**: Monitor and compare model performance metrics
- **Fallback Strategies**: Graceful degradation when preferred models unavailable
- **Cost Optimization**: Balance performance and resource costs

## API Endpoints

### Health and Status

#### Health Check
```http
GET /health
```
Returns router service health and connected service status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "2h 34m 12s",
  "connected_services": {
    "research-mcp": "healthy",
    "knowledge-mcp": "healthy", 
    "gateway": "healthy"
  },
  "routing_rules": 15,
  "active_connections": 23
}
```

#### Service Discovery
```http
GET /services
```
Lists all available services and their current status.

**Response:**
```json
{
  "services": [
    {
      "name": "research-mcp",
      "instances": [
        {
          "id": "research-001",
          "endpoint": "http://research-mcp-1:8081",
          "status": "healthy",
          "load": 0.34,
          "response_time_ms": 245,
          "last_health_check": "2024-01-20T15:30:00Z"
        }
      ]
    }
  ]
}
```

### Routing Configuration

#### Get Routing Policies
```http
GET /routing/policies
```
Returns current routing policies and configurations.

#### Update Routing Policy
```http
POST /routing/policies
```
Updates routing policies for specific service types or tenants.

**Request:**
```json
{
  "policy_id": "research-routing-v2",
  "service_type": "research",
  "rules": [
    {
      "condition": {
        "query_complexity": "high",
        "tenant_tier": "premium"
      },
      "action": {
        "route_to": "research-mcp-premium",
        "timeout": 60,
        "retry_count": 3
      }
    }
  ],
  "load_balancing": "weighted_round_robin",
  "circuit_breaker": {
    "failure_threshold": 5,
    "recovery_timeout": 30
  }
}
```

### Request Routing

#### Route Request
```http
POST /route
```
Routes a request to the appropriate service based on routing policies.

**Request:**
```json
{
  "service_type": "research",
  "tenant_id": "demo",
  "request_payload": {
    "query": "market analysis sustainable packaging",
    "complexity": "medium",
    "priority": "normal"
  },
  "routing_hints": {
    "prefer_fast": true,
    "max_cost": 0.05,
    "required_capabilities": ["web_crawling", "pdf_extraction"]
  }
}
```

**Response:**
```json
{
  "routing_decision": {
    "selected_service": "research-mcp-001",
    "endpoint": "http://research-mcp-1:8081", 
    "routing_reason": "best_performance_match",
    "expected_response_time": 12.3,
    "estimated_cost": 0.023
  },
  "fallback_services": [
    "research-mcp-002",
    "research-mcp-003"
  ],
  "routing_metadata": {
    "policy_version": "research-routing-v2",
    "decision_time_ms": 5,
    "load_balancing_method": "performance_based"
  }
}
```

### Model Selection

#### Get Model Recommendations
```http
POST /models/recommend
```
Recommends optimal models for specific tasks.

**Request:**
```json
{
  "task_type": "text_embedding",
  "content_type": "research_query",
  "performance_requirements": {
    "max_latency_ms": 500,
    "min_accuracy": 0.85,
    "max_cost_per_request": 0.001
  },
  "content_sample": "sustainable packaging market trends analysis"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "model_id": "colbert-base-v2",
      "confidence": 0.92,
      "expected_performance": {
        "latency_ms": 234,
        "accuracy": 0.89,
        "cost_per_request": 0.0008
      },
      "reasons": [
        "Optimal for medium-length queries",
        "High accuracy for market research content",
        "Within cost constraints"
      ]
    }
  ]
}
```

#### Model Performance Metrics
```http
GET /models/{model_id}/metrics
```
Returns performance metrics for specific models.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ROUTER_MCP_PORT` | 8083 | Service port |
| `HEALTH_CHECK_INTERVAL` | 30s | Service health check frequency |
| `ROUTING_POLICY_REFRESH` | 60s | Policy refresh interval |
| `CIRCUIT_BREAKER_THRESHOLD` | 5 | Failure threshold for circuit breaker |
| `LOAD_BALANCE_METHOD` | "weighted_round_robin" | Default load balancing strategy |
| `DEFAULT_TIMEOUT` | 30s | Default request timeout |
| `RETRY_BACKOFF_FACTOR` | 2.0 | Exponential backoff multiplier |

### Routing Policies Configuration

```yaml
# configs/router/routing-policies.yaml
policies:
  research_routing:
    rules:
      - name: "high_complexity_premium"
        condition:
          query_complexity: "high"
          tenant_tier: "premium"
        action:
          route_to: "research-mcp-premium"
          timeout: 60
          retry_count: 3
      - name: "standard_routing"
        condition:
          default: true
        action:
          route_to: "research-mcp-standard"
          timeout: 30
          retry_count: 2

  knowledge_routing:
    load_balancing: "least_connections"
    circuit_breaker:
      failure_threshold: 3
      recovery_timeout: 30
```

### Model Selection Policies

```yaml  
# configs/router/model-selection.yaml
models:
  text_embedding:
    colbert_base:
      performance_tier: "standard"
      cost_per_request: 0.0008
      avg_latency_ms: 245
      accuracy_score: 0.87
      max_input_tokens: 512
    
    colbert_large:
      performance_tier: "premium"
      cost_per_request: 0.002
      avg_latency_ms: 450
      accuracy_score: 0.91
      max_input_tokens: 1024

selection_criteria:
  prefer_accuracy: 0.4
  prefer_speed: 0.4  
  prefer_cost: 0.2
```

## Routing Strategies

### Content-Based Routing
Routes requests based on payload analysis:

```python
# Example routing logic
def route_research_request(request):
    complexity = analyze_query_complexity(request.query)
    tenant_tier = get_tenant_tier(request.tenant_id)
    
    if complexity == "high" and tenant_tier == "premium":
        return "research-mcp-premium"
    elif complexity == "low":
        return "research-mcp-fast"
    else:
        return "research-mcp-standard"
```

### Performance-Based Routing
Routes based on real-time service performance:

```python
def route_by_performance(service_type, request):
    services = get_healthy_services(service_type)
    performance_scores = [
        calculate_score(s.response_time, s.success_rate, s.load)
        for s in services
    ]
    return services[max_performance_index]
```

### Geographic Routing
Routes to geographically optimal instances:

```python
def geographic_routing(client_location, service_type):
    services = get_services_by_type(service_type)
    distances = [
        calculate_distance(client_location, s.location)
        for s in services
    ]
    return services[min_distance_index]
```

## Circuit Breaker Implementation

### Circuit Breaker States
- **Closed**: Normal operation, requests flow through
- **Open**: Service failure detected, requests blocked
- **Half-Open**: Testing if service has recovered

### Configuration Example
```json
{
  "circuit_breaker": {
    "failure_threshold": 5,
    "success_threshold": 3,
    "timeout_duration": "30s",
    "failure_rate_threshold": 0.5,
    "slow_call_duration_threshold": "2s"
  }
}
```

## Monitoring and Observability

### Routing Metrics
- **Request Volume**: Total requests routed per service
- **Routing Latency**: Time to make routing decisions  
- **Success Rate**: Percentage of successful routing decisions
- **Load Distribution**: Balance of requests across instances

### Performance Tracking
- **Service Response Times**: Real-time latency monitoring
- **Error Rates**: Failure rate tracking per service
- **Throughput**: Requests per second handling capacity
- **Circuit Breaker Activity**: Open/close events and recovery times

### Tracing Integration
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("route_request")
def route_request(request):
    span = trace.get_current_span()
    span.set_attribute("service_type", request.service_type)
    span.set_attribute("tenant_id", request.tenant_id)
    
    # Routing logic
    routing_decision = make_routing_decision(request)
    
    span.set_attribute("selected_service", routing_decision.service)
    return routing_decision
```

## Error Handling and Resilience

### Retry Strategies
- **Exponential Backoff**: Increasing delays between retries
- **Jittered Backoff**: Random variance to prevent thundering herd
- **Circuit Breaker Integration**: Stop retries when circuit is open

### Fallback Mechanisms
- **Service Fallbacks**: Secondary service selection when primary fails
- **Degraded Mode**: Simplified routing when advanced features unavailable
- **Cache Fallbacks**: Use cached routing decisions when service discovery fails

### Error Response Format
```json
{
  "error": {
    "type": "ROUTING_ERROR",
    "code": "NO_HEALTHY_SERVICES",
    "message": "No healthy instances available for service type 'research'",
    "details": {
      "service_type": "research",
      "attempted_instances": ["research-001", "research-002"],
      "circuit_breaker_status": "open",
      "retry_after": 30
    }
  }
}
```

## Integration Examples

### Python Client Integration
```python
from router_mcp_client import RouterMCPClient

async def route_research_request():
    router = RouterMCPClient("http://localhost:8083")
    
    routing_result = await router.route_request(
        service_type="research",
        tenant_id="demo",
        payload={
            "query": "sustainable packaging trends",
            "complexity": "medium"
        }
    )
    
    # Use routing result to make actual request
    selected_endpoint = routing_result.endpoint
    return await make_request(selected_endpoint, payload)
```

### Direct HTTP Integration
```python
import httpx

async def get_model_recommendation():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8083/models/recommend",
            json={
                "task_type": "text_embedding",
                "performance_requirements": {
                    "max_latency_ms": 300,
                    "min_accuracy": 0.85
                }
            }
        )
        return response.json()
```

## See Also

- [Gateway API Reference](gateway.md) - Main API orchestration
- [Research MCP API](research-mcp.md) - Research service routing
- [Knowledge MCP API](knowledge-mcp.md) - Knowledge service routing  
- [Configuration Reference](../configuration/yaml-configs.md#router-policies) - Router configuration
- [Operations Guide](../../how-to/operations-guide.md#router-management) - Router operations and maintenance