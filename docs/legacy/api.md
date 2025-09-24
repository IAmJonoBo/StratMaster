# StratMaster API Documentation

This guide provides comprehensive documentation for the StratMaster API, including all endpoints, request/response schemas, authentication, and integration examples.

## API Overview

The StratMaster API is built with FastAPI and provides a RESTful interface for AI-powered brand strategy operations. All endpoints return JSON responses and follow OpenAPI 3.0 specifications.

**Base URL**: `http://localhost:8080` (development) or `https://your-domain.com` (production)
**OpenAPI Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
**API Schema**: Available at `/openapi.json`

## Authentication

### API Key Authentication

All API endpoints require authentication via API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     https://api.stratmaster.com/healthz
```

### JWT Token Authentication

For user-specific operations, use JWT tokens from Keycloak:

```bash
# Get token from Keycloak
TOKEN=$(curl -X POST http://localhost:8089/auth/realms/stratmaster/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=stratmaster-api" \
  -d "client_secret=your-secret" | jq -r '.access_token')

# Use token in API calls
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     https://api.stratmaster.com/research/plan
```

## Request Requirements

### Idempotency

All POST endpoints require an `Idempotency-Key` header (8-128 characters, alphanumeric plus `-_`):

```bash
curl -X POST https://api.stratmaster.com/research/plan \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: req-12345-abcde" \
  -d '{"query": "AI strategy trends 2024"}'
```

### Content Type

All requests must include `Content-Type: application/json` header for POST/PUT operations.

## Core Endpoints

### Health and Status

#### GET /healthz

Returns API health status.

**Response**:
```json
{
  "status": "ok"
}
```

**Example**:
```bash
curl https://api.stratmaster.com/healthz
```

#### GET /ready

Returns readiness status including dependencies.

**Response**:
```json
{
  "status": "ready",
  "dependencies": {
    "database": "healthy",
    "vector_store": "healthy",
    "search_engine": "healthy"
  }
}
```

### Research Operations

#### POST /research/plan

Generate a research plan with sources and task breakdown.

**Request Body**:
```json
{
  "query": "AI strategy trends 2024",
  "max_sources": 10,
  "research_depth": "comprehensive",
  "domains": ["technology", "business"],
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  }
}
```

**Response**:
```json
{
  "plan_id": "plan_abc123",
  "query": "AI strategy trends 2024",
  "sources": [
    {
      "id": "src_1",
      "name": "TechCrunch",
      "url": "https://techcrunch.com",
      "type": "news",
      "priority": 1
    }
  ],
  "tasks": [
    {
      "id": "task_1",
      "description": "Search technology publications",
      "source_ids": ["src_1"],
      "estimated_duration": 300
    }
  ],
  "estimated_total_duration": 900,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Example**:
```bash
curl -X POST https://api.stratmaster.com/research/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: plan-$(date +%s)" \
  -d '{
    "query": "AI strategy trends 2024",
    "max_sources": 5,
    "research_depth": "focused"
  }'
```

#### POST /research/run

Execute a research plan and return structured claims and evidence.

**Request Body**:
```json
{
  "plan_id": "plan_abc123",
  "execution_options": {
    "parallel_tasks": 3,
    "timeout_per_task": 600,
    "quality_threshold": 0.8
  }
}
```

**Response**:
```json
{
  "session_id": "session_xyz789",
  "plan_id": "plan_abc123",
  "status": "completed",
  "claims": [
    {
      "id": "claim_1",
      "text": "AI adoption in enterprise increased 45% in 2024",
      "confidence": 0.92,
      "supporting_evidence": ["evidence_1", "evidence_2"],
      "sources": ["src_1", "src_2"],
      "category": "market_trend"
    }
  ],
  "evidence": [
    {
      "id": "evidence_1",
      "text": "Survey of 1000 enterprises shows 45% increase",
      "source_id": "src_1",
      "url": "https://example.com/survey",
      "relevance_score": 0.95,
      "credibility_score": 0.88
    }
  ],
  "provenance": [
    {
      "source_id": "src_1",
      "fingerprint": "sha256:abc123...",
      "collected_at": "2024-01-01T10:00:00Z",
      "method": "web_crawl"
    }
  ],
  "graph_artifacts": {
    "nodes": [
      {
        "id": "node_1",
        "type": "concept",
        "name": "AI Adoption",
        "properties": {"category": "technology"}
      }
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "node_1",
        "target": "node_2",
        "type": "relates_to",
        "weight": 0.85
      }
    ]
  },
  "completed_at": "2024-01-01T10:15:00Z"
}
```

### Knowledge Operations

#### POST /graph/summarise

Generate graph summaries and community analysis.

**Request Body**:
```json
{
  "tenant_id": "tenant_demo",
  "graph_filters": {
    "node_types": ["concept", "organization"],
    "edge_types": ["relates_to", "mentions"],
    "time_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  },
  "summary_options": {
    "include_communities": true,
    "max_communities": 10,
    "community_size_threshold": 5
  }
}
```

**Response**:
```json
{
  "graph_id": "graph_abc123",
  "tenant_id": "tenant_demo",
  "summary": {
    "total_nodes": 1250,
    "total_edges": 3780,
    "node_types": {
      "concept": 856,
      "organization": 234,
      "person": 160
    },
    "edge_types": {
      "relates_to": 2100,
      "mentions": 980,
      "sources_from": 700
    }
  },
  "communities": [
    {
      "id": "community_1",
      "name": "AI Technology Trends",
      "size": 45,
      "density": 0.78,
      "key_concepts": ["artificial intelligence", "machine learning", "automation"],
      "summary": "Community focused on AI technology developments and trends"
    }
  ],
  "insights": [
    {
      "type": "emerging_trend",
      "description": "Increased connectivity between AI and sustainability concepts",
      "confidence": 0.82,
      "supporting_nodes": ["node_1", "node_2", "node_3"]
    }
  ],
  "generated_at": "2024-01-01T10:30:00Z"
}
```

#### POST /retrieval/colbert/query

Perform dense vector retrieval using ColBERT.

**Request Body**:
```json
{
  "query": "sustainable AI practices",
  "collection": "tenant_demo_research",
  "limit": 10,
  "filters": {
    "tenant_id": "demo",
    "document_type": "research_paper",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  },
  "retrieval_options": {
    "use_query_expansion": true,
    "rerank": true,
    "include_scores": true
  }
}
```

**Response**:
```json
{
  "query": "sustainable AI practices",
  "results": [
    {
      "document_id": "doc_1",
      "score": 0.92,
      "text": "Sustainable AI practices focus on reducing computational costs...",
      "metadata": {
        "title": "Green AI: Sustainable Machine Learning Practices",
        "author": "Dr. Jane Smith",
        "source": "AI Research Journal",
        "date": "2024-03-15"
      },
      "grounding_spans": [
        {
          "start": 0,
          "end": 85,
          "text": "Sustainable AI practices focus on reducing computational costs while maintaining performance",
          "relevance": 0.95
        }
      ]
    }
  ],
  "retrieval_metadata": {
    "total_candidates": 10000,
    "query_time_ms": 45,
    "rerank_time_ms": 12,
    "index_version": "v1.2.3"
  }
}
```

#### POST /retrieval/splade/query

Perform sparse vector retrieval using SPLADE.

**Request Body**:
```json
{
  "query": "enterprise AI implementation challenges",
  "index": "tenant_demo_documents",
  "limit": 15,
  "filters": {
    "document_category": ["whitepaper", "case_study"],
    "organization_size": ["enterprise", "large_business"]
  },
  "splade_options": {
    "query_expansion": true,
    "max_expansion_terms": 50,
    "expansion_threshold": 0.1
  }
}
```

### Agent Operations

#### POST /debate/run

Trigger multi-agent debate and validation process.

**Request Body**:
```json
{
  "session_id": "session_xyz789",
  "debate_config": {
    "agents": ["strategist", "critic", "adversary"],
    "max_rounds": 3,
    "consensus_threshold": 0.8,
    "constitutional_constraints": ["safety", "accuracy", "bias_mitigation"]
  },
  "focus_areas": [
    "factual_accuracy",
    "logical_consistency", 
    "bias_detection",
    "completeness"
  ]
}
```

**Response**:
```json
{
  "debate_id": "debate_abc123",
  "session_id": "session_xyz789",
  "status": "completed",
  "rounds": [
    {
      "round": 1,
      "agent": "strategist",
      "position": "Initial recommendations based on research findings...",
      "timestamp": "2024-01-01T11:00:00Z"
    },
    {
      "round": 1,
      "agent": "critic",
      "position": "Concerns about data quality in source 3...",
      "issues_raised": ["data_quality", "sample_size"],
      "timestamp": "2024-01-01T11:05:00Z"
    }
  ],
  "verdict": {
    "consensus_reached": true,
    "confidence": 0.85,
    "approved_claims": ["claim_1", "claim_2"],
    "rejected_claims": ["claim_3"],
    "modifications_required": [
      {
        "claim_id": "claim_4",
        "modification": "Add disclaimer about market volatility",
        "reason": "Insufficient uncertainty quantification"
      }
    ]
  },
  "constitutional_compliance": {
    "safety": "passed",
    "accuracy": "passed", 
    "bias_mitigation": "warning",
    "warnings": ["Potential selection bias in data sources"]
  },
  "completed_at": "2024-01-01T11:30:00Z"
}
```

#### POST /recommendations

Generate final strategic recommendations with decision brief.

**Request Body**:
```json
{
  "session_id": "session_xyz789",
  "debate_id": "debate_abc123",
  "recommendation_options": {
    "format": "executive_summary",
    "include_implementation_plan": true,
    "risk_assessment": true,
    "confidence_intervals": true
  },
  "target_audience": "c_suite",
  "time_horizon": "12_months"
}
```

**Response**:
```json
{
  "decision_brief": {
    "id": "brief_def456",
    "title": "AI Strategy Recommendations for 2024",
    "executive_summary": "Based on comprehensive research and multi-agent validation...",
    "key_recommendations": [
      {
        "id": "rec_1",
        "title": "Invest in AI Infrastructure",
        "description": "Establish foundational AI capabilities...",
        "priority": "high",
        "confidence": 0.88,
        "expected_impact": "Reduce operational costs by 25%",
        "implementation_timeline": "Q2 2024",
        "required_investment": "$2.5M",
        "supporting_evidence": ["claim_1", "claim_2"]
      }
    ],
    "risk_assessment": {
      "high_risks": [
        {
          "risk": "Technology adoption challenges",
          "probability": 0.3,
          "impact": "medium",
          "mitigation": "Gradual rollout with training programs"
        }
      ],
      "medium_risks": [],
      "low_risks": []
    },
    "implementation_plan": {
      "milestones": [
        {
          "milestone": 1,
          "name": "Foundation",
          "duration": "3 months",
          "deliverables": ["Infrastructure setup", "Team training"],
          "success_metrics": ["System uptime > 99%", "Team certification"]
        }
      ]
    }
  },
  "confidence_analysis": {
    "overall_confidence": 0.82,
    "data_quality_score": 0.89,
    "source_diversity": 0.75,
    "expert_consensus": 0.85
  },
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### Experiment and Forecast Operations

#### POST /experiments

Create experiment definitions for A/B testing recommendations.

**Request Body**:
```json
{
  "name": "AI Implementation Strategy Test",
  "hypothesis": "Gradual AI rollout will have higher success rate than big-bang approach",
  "variants": [
    {
      "name": "gradual_rollout",
      "description": "Phased implementation over 6 months",
      "allocation": 0.5
    },
    {
      "name": "big_bang",
      "description": "Full implementation in 1 month", 
      "allocation": 0.5
    }
  ],
  "primary_metric": {
    "name": "success_rate",
    "definition": "Percentage of successful implementations",
    "unit": "percentage",
    "target": 85.0
  },
  "secondary_metrics": [
    {
      "name": "time_to_value",
      "definition": "Days until measurable business value",
      "unit": "days"
    }
  ],
  "minimum_detectable_effect": 0.1,
  "statistical_power": 0.8,
  "significance_level": 0.05
}
```

#### POST /forecasts

Generate scenario-based forecasts with confidence intervals.

**Request Body**:
```json
{
  "metric": {
    "name": "ai_adoption_rate",
    "definition": "Percentage of processes automated with AI",
    "current_value": 15.0,
    "unit": "percentage"
  },
  "scenarios": [
    {
      "name": "conservative",
      "description": "Slow, steady adoption",
      "assumptions": ["Limited budget", "Risk-averse culture"]
    },
    {
      "name": "aggressive", 
      "description": "Rapid AI implementation",
      "assumptions": ["High investment", "Change-ready organization"]
    }
  ],
  "forecast_horizon_days": 365,
  "confidence_levels": [50, 90]
}
```

### Evaluation Operations

#### POST /evals/run

Execute evaluation gates for quality assurance.

**Request Body**:
```json
{
  "session_id": "session_xyz789",
  "eval_suite": "comprehensive",
  "evaluations": [
    {
      "name": "factual_accuracy",
      "config": {
        "fact_checking_model": "gpt-4",
        "minimum_score": 0.8,
        "sources_required": 2
      }
    },
    {
      "name": "bias_detection",
      "config": {
        "bias_categories": ["gender", "racial", "geographical"],
        "threshold": 0.1
      }
    },
    {
      "name": "completeness",
      "config": {
        "required_sections": ["methodology", "limitations", "recommendations"],
        "minimum_word_count": 500
      }
    }
  ]
}
```

**Response**:
```json
{
  "eval_id": "eval_ghi789",
  "session_id": "session_xyz789", 
  "status": "completed",
  "overall_score": 0.84,
  "passed": true,
  "results": [
    {
      "evaluation": "factual_accuracy",
      "score": 0.89,
      "passed": true,
      "details": {
        "facts_checked": 15,
        "facts_verified": 13,
        "verification_rate": 0.87,
        "failed_facts": [
          {
            "claim": "AI market will grow 300% by 2025",
            "issue": "No credible source found",
            "severity": "medium"
          }
        ]
      }
    },
    {
      "evaluation": "bias_detection",
      "score": 0.78,
      "passed": true,
      "details": {
        "bias_indicators_found": 2,
        "severity_breakdown": {
          "low": 2,
          "medium": 0,
          "high": 0
        },
        "recommendations": [
          "Consider more diverse geographical data sources"
        ]
      }
    }
  ],
  "recommendations": [
    "Verify market growth statistics with additional sources",
    "Include more diverse geographical perspectives"
  ],
  "evaluated_at": "2024-01-01T13:00:00Z"
}
```

## Provider Integration

### OpenAI Tools Integration

#### GET /providers/openai/tools

Returns OpenAI-compatible tool definitions.

**Response**:
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "research_plan",
        "description": "Generate a comprehensive research plan",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Research query or topic"
            },
            "max_sources": {
              "type": "integer",
              "description": "Maximum number of sources to include",
              "default": 10
            }
          },
          "required": ["query"]
        }
      }
    }
  ]
}
```

#### GET /providers/openai/tools/{tool_name}

Get specific tool definition.

**Example**: `GET /providers/openai/tools/research_plan`

## Error Handling

### Error Response Format

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://api.stratmaster.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "The request body contains invalid data",
  "instance": "/research/plan",
  "errors": [
    {
      "field": "query",
      "message": "Query cannot be empty",
      "code": "required"
    }
  ],
  "request_id": "req_abc123"
}
```

### Common Error Codes

| Status | Type | Description |
|--------|------|-------------|
| 400 | `validation-error` | Invalid request data |
| 401 | `authentication-error` | Missing or invalid authentication |
| 403 | `authorization-error` | Insufficient permissions |
| 404 | `not-found` | Resource not found |
| 409 | `conflict` | Resource already exists |
| 422 | `processing-error` | Request valid but cannot be processed |
| 429 | `rate-limit-exceeded` | Too many requests |
| 500 | `internal-error` | Server error |
| 503 | `service-unavailable` | Service temporarily unavailable |

### Rate Limiting

API endpoints are rate limited per user/tenant:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 3600
```

**Limits**:
- **Per User**: 1000 requests/hour
- **Per Tenant**: 10000 requests/hour  
- **Per IP**: 100 requests/minute

## SDK and Client Libraries

### Python SDK

```python
from stratmaster_client import StratMasterClient

# Initialize client
client = StratMasterClient(
    base_url="https://api.stratmaster.com",
    api_key="your-api-key"
)

# Research workflow
plan = await client.research.create_plan(
    query="AI strategy trends 2024",
    max_sources=5
)

session = await client.research.execute_plan(plan.plan_id)
debate = await client.debate.run(session.session_id)
recommendations = await client.recommendations.generate(
    session_id=session.session_id,
    debate_id=debate.debate_id
)
```

### JavaScript/TypeScript SDK

```typescript
import { StratMasterAPI } from '@stratmaster/api-client';

const client = new StratMasterAPI({
  baseURL: 'https://api.stratmaster.com',
  apiKey: 'your-api-key'
});

// Research workflow
const plan = await client.research.createPlan({
  query: 'AI strategy trends 2024',
  maxSources: 5
});

const session = await client.research.executePlan(plan.planId);
const recommendations = await client.recommendations.generate({
  sessionId: session.sessionId
});
```

### cURL Examples

Complete workflow using cURL:

```bash
#!/bin/bash
set -e

API_BASE="https://api.stratmaster.com"
TOKEN="your-api-key"

# 1. Create research plan
PLAN=$(curl -s -X POST "$API_BASE/research/plan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: plan-$(date +%s)" \
  -d '{"query": "AI strategy trends 2024", "max_sources": 5}')

PLAN_ID=$(echo $PLAN | jq -r '.plan_id')
echo "Created plan: $PLAN_ID"

# 2. Execute research
SESSION=$(curl -s -X POST "$API_BASE/research/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: session-$(date +%s)" \
  -d "{\"plan_id\": \"$PLAN_ID\"}")

SESSION_ID=$(echo $SESSION | jq -r '.session_id')
echo "Research session: $SESSION_ID"

# 3. Run debate validation
DEBATE=$(curl -s -X POST "$API_BASE/debate/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: debate-$(date +%s)" \
  -d "{\"session_id\": \"$SESSION_ID\"}")

DEBATE_ID=$(echo $DEBATE | jq -r '.debate_id')
echo "Debate completed: $DEBATE_ID"

# 4. Generate recommendations
RECOMMENDATIONS=$(curl -s -X POST "$API_BASE/recommendations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: rec-$(date +%s)" \
  -d "{\"session_id\": \"$SESSION_ID\", \"debate_id\": \"$DEBATE_ID\"}")

echo "Final recommendations:"
echo $RECOMMENDATIONS | jq '.decision_brief.key_recommendations'
```

## Monitoring and Observability

### Metrics Endpoint

**GET /metrics** (Prometheus format)

```
# HELP stratmaster_requests_total Total number of API requests
# TYPE stratmaster_requests_total counter
stratmaster_requests_total{method="POST",endpoint="/research/plan",status="200"} 1234

# HELP stratmaster_request_duration_seconds Request duration in seconds
# TYPE stratmaster_request_duration_seconds histogram
stratmaster_request_duration_seconds_bucket{le="0.1"} 100
stratmaster_request_duration_seconds_bucket{le="0.5"} 450
stratmaster_request_duration_seconds_bucket{le="1.0"} 800
```

### Health Endpoints

**GET /health/deep** - Comprehensive health check including dependencies

```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 45,
      "connections": 23
    },
    "vector_store": {
      "status": "healthy", 
      "response_time_ms": 12,
      "collections": 5
    },
    "search_engine": {
      "status": "healthy",
      "response_time_ms": 8,
      "indices": 3
    }
  },
  "version": "0.1.0",
  "build": "abc123",
  "uptime_seconds": 86400
}
```

## Testing and Development

### API Testing

Use the OpenAPI specification for automated testing:

```python
import pytest
import httpx
from openapi_core import create_spec
from openapi_core.contrib.requests import RequestsOpenAPIRequest
from openapi_core.contrib.requests import RequestsOpenAPIResponse

# Load OpenAPI spec
spec = create_spec(httpx.get("http://localhost:8080/openapi.json").json())

def test_research_plan_endpoint():
    response = httpx.post(
        "http://localhost:8080/research/plan",
        json={"query": "test query"},
        headers={"Idempotency-Key": "test-123"}
    )
    
    # Validate against OpenAPI spec
    openapi_request = RequestsOpenAPIRequest(response.request)
    openapi_response = RequestsOpenAPIResponse(response)
    
    spec.validate_request(openapi_request)
    spec.validate_response(openapi_request, openapi_response)
```

### Mock Server

For testing and development, use the built-in mock mode:

```bash
# Start API in mock mode
STRATMASTER_MOCK_RESPONSES=true uvicorn stratmaster_api.app:create_app --factory

# All endpoints return realistic mock data
curl -X POST http://localhost:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test" \
  -d '{"query": "test"}'
```

For more development information, see the [Development Guide](development.md).