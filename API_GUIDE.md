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
  "depth": "comprehensive",
  "focus_areas": ["technology", "market", "competition"]
}
```

**Response**:
```json
{
  "plan_id": "plan-123",
  "tasks": [
    {
      "id": "task-1",
      "description": "Market analysis of AI trends",
      "sources": ["academic", "industry", "news"],
      "priority": "high"
    }
  ],
  "estimated_time": "15-30 minutes",
  "confidence": 0.85
}
```

#### POST /research/run

Execute research based on a plan or query.

**Request Body**:
```json
{
  "query": "AI strategy trends 2024",
  "plan_id": "plan-123",
  "include_sources": true
}
```

**Response**:
```json
{
  "research_id": "research-456",
  "claims": [
    {
      "id": "claim-1",
      "statement": "AI adoption increased 40% in 2024",
      "confidence": 0.9,
      "evidence": ["source-1", "source-2"],
      "grade": "A"
    }
  ],
  "sources": [
    {
      "id": "source-1", 
      "title": "AI Market Report 2024",
      "url": "https://example.com/report",
      "credibility": "high"
    }
  ]
}
```

### Expert Operations

#### POST /experts/evaluate

Get expert analysis from multiple disciplines.

**Request Body**:
```json
{
  "topic": "AI strategy implementation",
  "experts": ["technology", "business", "risk"],
  "context": "Fortune 500 company",
  "depth": "detailed"
}
```

**Response**:
```json
{
  "evaluation_id": "eval-789",
  "expert_memos": [
    {
      "expert": "technology",
      "confidence": 0.88,
      "recommendation": "Adopt gradual AI integration",
      "reasoning": "Technical infrastructure ready",
      "risks": ["skill gap", "integration complexity"]
    }
  ],
  "consensus": "moderate_agreement",
  "next_steps": ["pilot program", "training plan"]
}
```

#### POST /experts/vote

Get weighted expert council vote on decisions.

**Request Body**:
```json
{
  "decision": "Should we implement AI customer service?",
  "evaluation_id": "eval-789",
  "voting_method": "weighted",
  "include_reasoning": true
}
```

**Response**:
```json
{
  "vote_id": "vote-101",
  "decision": "approve",
  "confidence": 0.75,
  "vote_breakdown": {
    "approve": 3,
    "reject": 1, 
    "abstain": 0
  },
  "expert_votes": [
    {
      "expert": "technology",
      "vote": "approve",
      "weight": 0.3,
      "reasoning": "Technical feasibility high"
    }
  ]
}
```

### Debate and Validation

#### POST /debate/run

Run multi-turn debate on strategic questions.

**Request Body**:
```json
{
  "thesis": "AI will replace 30% of jobs by 2030",
  "rounds": 3,
  "participants": ["economist", "technologist", "sociologist"],
  "evidence_required": true
}
```

**Response**:
```json
{
  "debate_id": "debate-202",
  "final_position": "nuanced_agreement", 
  "confidence": 0.72,
  "rounds": [
    {
      "round": 1,
      "arguments": [
        {
          "participant": "economist",
          "position": "support",
          "argument": "Historical precedent shows...",
          "evidence": ["source-1", "source-2"]
        }
      ]
    }
  ],
  "synthesis": "Jobs will transform rather than disappear"
}
```

### Recommendations

#### POST /recommendations

Generate strategic recommendations.

**Request Body**:
```json
{
  "situation": "Company considering AI adoption",
  "constraints": ["budget: $100k", "timeline: 6 months"],
  "goals": ["efficiency", "competitive_advantage"],
  "industry": "healthcare"
}
```

**Response**:
```json
{
  "recommendation_id": "rec-303",
  "primary_recommendation": "Implement AI-assisted diagnostics pilot",
  "confidence": 0.84,
  "rationale": "Highest ROI with manageable risk",
  "alternatives": [
    {
      "option": "AI customer service",
      "confidence": 0.72,
      "pros": ["cost savings", "24/7 availability"],
      "cons": ["patient satisfaction risk"]
    }
  ],
  "implementation_plan": {
    "phase_1": "Vendor selection and pilot setup",
    "timeline": "2 months",
    "budget": "$40k"
  }
}
```

## Schema Reference

### Key Data Types

#### Claims
```json
{
  "id": "string",
  "statement": "string", 
  "confidence": "float (0-1)",
  "evidence": ["source_id", "..."],
  "grade": "A|B|C|D|F",
  "methodology": "string"
}
```

#### Sources  
```json
{
  "id": "string",
  "title": "string",
  "url": "string",
  "credibility": "high|medium|low",
  "date_published": "ISO 8601",
  "domain": "string"
}
```

#### Expert Memo
```json
{
  "expert": "string",
  "discipline": "string", 
  "confidence": "float (0-1)",
  "recommendation": "string",
  "reasoning": "string",
  "risks": ["string", "..."],
  "opportunities": ["string", "..."]
}
```

## Error Handling

### Standard Error Format

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://api.stratmaster.com/errors/validation",
  "title": "Validation Error", 
  "status": 400,
  "detail": "Missing required field: query",
  "instance": "/research/plan",
  "errors": [
    {
      "field": "query",
      "message": "This field is required",
      "code": "required"
    }
  ]
}
```

### Common Error Codes

- `400` - Validation error, malformed request
- `401` - Authentication required  
- `403` - Insufficient permissions
- `422` - Idempotency key already used
- `429` - Rate limit exceeded
- `500` - Internal server error

## Rate Limits

- **Default**: 100 requests per minute per API key
- **Research endpoints**: 10 requests per minute (resource intensive)  
- **Expert endpoints**: 20 requests per minute
- **Health endpoints**: 1000 requests per minute

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640995200
```

## Integration Examples

### Python Client

```python
import httpx
import asyncio

class StratMasterClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8080"):
        self.api_key = api_key
        self.base_url = base_url
        
    async def research(self, query: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": f"req-{hash(query)}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/research/run",
                json={"query": query},
                headers=headers
            )
            return response.json()

# Usage
client = StratMasterClient("your-api-key")
result = asyncio.run(client.research("AI trends 2024"))
```

### JavaScript/Node.js Client

```javascript
class StratMasterClient {
    constructor(apiKey, baseUrl = 'http://localhost:8080') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }
    
    async research(query) {
        const response = await fetch(`${this.baseUrl}/research/run`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
                'Idempotency-Key': `req-${Date.now()}`
            },
            body: JSON.stringify({ query })
        });
        
        return response.json();
    }
}

// Usage
const client = new StratMasterClient('your-api-key');
const result = await client.research('AI trends 2024');
```

## Webhooks (Beta)

Subscribe to events for asynchronous processing updates:

### Webhook Events

- `research.completed` - Research task finished
- `debate.concluded` - Debate reached conclusion  
- `expert.evaluated` - Expert analysis complete

### Webhook Payload Example

```json
{
  "event": "research.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "research_id": "research-456",
    "status": "completed",
    "claims_count": 15,
    "confidence": 0.87
  }
}
```

## Changelog

### v0.2.0 (Current)
- Added expert council system
- Enhanced debate capabilities
- Improved error handling
- Added webhook support

### v0.1.0 
- Initial API release
- Basic research and recommendation endpoints
- Authentication and rate limiting

---

For detailed technical reference, see the [API Reference Documentation](docs/reference/api/).

For integration examples and tutorials, see the [Integration Guide](docs/tutorials/).