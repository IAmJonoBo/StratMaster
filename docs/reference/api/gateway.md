---
title: FastAPI Gateway
description: Complete reference for all StratMaster FastAPI Gateway endpoints
version: 0.1.0
platform: FastAPI, Pydantic v2
nav_order: 1
parent: API Reference
grand_parent: Reference
---

# FastAPI Gateway Reference

Complete endpoint reference for the StratMaster FastAPI Gateway. All examples are derived from the actual test suite to ensure accuracy.

## Health & Status

### GET /healthz

Basic health check endpoint for monitoring and load balancers.

**Request:**
```http
GET /healthz HTTP/1.1
Host: localhost:8080
```

**Response:**
```json
{
  "status": "ok"
}
```

**cURL Example:**
```bash
curl -s http://localhost:8080/healthz
```

**Python Example:**
```python
import httpx

async def check_health():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8080/healthz")
        return response.json()  # {"status": "ok"}
```

---

## Research Operations

### POST /research/plan

Create a strategic research plan with task breakdown and source identification.

**Request Schema:**
```json
{
  "query": "string (min 3 chars)",
  "tenant_id": "string", 
  "include_sources": "boolean (default: true)",
  "max_sources": "integer (1-50, default: 10)"
}
```

**Response Schema:**
```json
{
  "plan_id": "string (format: plan-{uuid})",
  "tasks": ["string"],
  "sources": [
    {
      "id": "string",
      "url": "string",
      "type": "string", 
      "priority": "number"
    }
  ]
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: research-plan-001" \
  -d '{
    "query": "brand strategy trends 2024",
    "tenant_id": "tenant-a",
    "max_sources": 3
  }'
```

**Example Response:**
```json
{
  "plan_id": "plan-abc123def456",
  "tasks": [
    "Analyze current brand strategy trends",
    "Research digital transformation impact",
    "Evaluate competitive positioning"
  ],
  "sources": [
    {
      "id": "src-1",
      "url": "https://example.com/brand-trends",
      "type": "web_page",
      "priority": 0.9
    },
    {
      "id": "src-2", 
      "url": "https://example.com/digital-transformation",
      "type": "research_paper",
      "priority": 0.8
    },
    {
      "id": "src-3",
      "url": "https://example.com/competitive-analysis", 
      "type": "industry_report",
      "priority": 0.7
    }
  ]
}
```

**Test Example (from test suite):**
```python
def test_research_plan_endpoint_returns_tasks():
    c = client()
    resp = c.post(
        "/research/plan",
        headers={"Idempotency-Key": "test-key-1234"},
        json={"query": "brand strategy", "tenant_id": "tenant-a", "max_sources": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_id"].startswith("plan-")
    assert len(body["tasks"]) == 3
    assert len(body["sources"]) == 3
```

### POST /research/run

Execute a research plan and return structured claims with evidence.

**Request Schema:**
```json
{
  "plan_id": "string",
  "tenant_id": "string",
  "force_refresh": "boolean (default: false)"
}
```

**Response Schema:**
```json
{
  "run_id": "string",
  "claims": [
    {
      "id": "string",
      "text": "string",
      "confidence": "number (0-1)",
      "evidence_count": "integer",
      "source_ids": ["string"]
    }
  ],
  "evidence": [
    {
      "text": "string",
      "source_id": "string", 
      "url": "string",
      "relevance_score": "number (0-1)",
      "credibility_score": "number (0-1)"
    }
  ],
  "provenance": [
    {
      "source_id": "string",
      "fingerprint": "string",
      "collected_at": "datetime",
      "method": "string"
    }
  ],
  "graph_artifacts": {
    "nodes": [
      {
        "id": "string", 
        "type": "string",
        "name": "string",
        "properties": "object"
      }
    ],
    "edges": [
      {
        "id": "string",
        "source": "string",
        "target": "string",
        "relationship": "string"
      }
    ]
  }
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8080/research/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: research-run-001" \
  -d '{
    "plan_id": "plan-abc123def456",
    "tenant_id": "tenant-a"
  }'
```

---

## Knowledge Operations

### POST /graph/summarise

Generate summaries and diagnostics for knowledge graph artifacts.

**Request Schema:**
```json
{
  "tenant_id": "string",
  "graph_id": "string (optional)",
  "summary_type": "string (default: 'overview')"
}
```

**Response Schema:**
```json
{
  "summary_id": "string",
  "node_count": "integer",
  "edge_count": "integer", 
  "density": "number",
  "key_concepts": ["string"],
  "relationships": ["string"],
  "recommendations": ["string"]
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8080/graph/summarise \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: graph-summary-001" \
  -d '{
    "tenant_id": "tenant-a",
    "summary_type": "detailed"
  }'
```

### POST /retrieval/colbert/query

Query ColBERT dense retrieval system for semantic search.

**Request Schema:**
```json
{
  "query": "string",
  "tenant_id": "string",
  "top_k": "integer (default: 10)",
  "filters": "object (optional)"
}
```

**Response Schema:**
```json
{
  "query_id": "string",
  "results": [
    {
      "document_id": "string",
      "score": "number",
      "text": "string",
      "metadata": "object"
    }
  ],
  "total_results": "integer",
  "query_time_ms": "number"
}
```

### POST /retrieval/splade/query

Query SPLADE sparse retrieval system for keyword-based search.

**Request Schema:**
```json
{
  "query": "string", 
  "tenant_id": "string",
  "top_k": "integer (default: 10)",
  "expand_query": "boolean (default: true)"
}
```

**Response Schema:**
```json
{
  "query_id": "string",
  "expanded_terms": ["string"],
  "results": [
    {
      "document_id": "string",
      "score": "number", 
      "text": "string",
      "highlighted": "string"
    }
  ]
}
```

---

## Debate System

### POST /debate/run

Execute multi-agent debate validation for research claims.

**Request Schema:**
```json
{
  "session_id": "string",
  "tenant_id": "string", 
  "claims": [
    {
      "id": "string",
      "text": "string",
      "confidence": "number",
      "evidence_ids": ["string"]
    }
  ],
  "debate_config": {
    "max_rounds": "integer (default: 3)",
    "agents": ["string"],
    "consensus_threshold": "number (default: 0.8)"
  }
}
```

**Response Schema:**
```json
{
  "debate_id": "string",
  "tenant_id": "string",
  "rounds": [
    {
      "round": "integer",
      "agent": "string",
      "position": "string", 
      "issues_raised": ["string"],
      "timestamp": "datetime"
    }
  ],
  "verdict": {
    "consensus_reached": "boolean",
    "confidence": "number",
    "approved_claims": ["string"],
    "rejected_claims": ["string"],
    "modifications_required": [
      {
        "claim_id": "string",
        "modification": "string", 
        "reason": "string"
      }
    ]
  },
  "constitutional_compliance": {
    "safety": "string",
    "accuracy": "string",
    "bias_mitigation": "string",
    "warnings": ["string"]
  }
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8080/debate/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: debate-001" \
  -d '{
    "session_id": "session-abc123",
    "tenant_id": "tenant-a",
    "claims": [
      {
        "id": "claim-1",
        "text": "AI reduces customer support costs by 30%",
        "confidence": 0.85,
        "evidence_ids": ["ev-1", "ev-2"]
      }
    ],
    "debate_config": {
      "max_rounds": 3,
      "agents": ["strategist", "critic", "adversary"]
    }
  }'
```

---

## Expert Council

### POST /experts/evaluate

Get expert evaluation across multiple disciplines.

**Request Schema:**
```json
{
  "tenant_id": "string",
  "decision_context": {
    "type": "string",
    "domain": "string", 
    "timeline": "string",
    "budget_range": "string"
  },
  "claims": [
    {
      "id": "string",
      "text": "string", 
      "confidence": "number"
    }
  ],
  "expert_disciplines": ["string"]
}
```

**Response Schema:**
```json
{
  "evaluation_id": "string",
  "expert_memos": [
    {
      "discipline": "string",
      "expert_id": "string",
      "assessment": {
        "recommendation": "string",
        "confidence": "number",
        "key_risks": ["string"],
        "success_factors": ["string"]
      }
    }
  ]
}
```

### POST /experts/vote

Aggregate expert memos into weighted council vote.

**Request Schema:**
```json
{
  "evaluation_id": "string",
  "tenant_id": "string",
  "voting_method": "string (default: 'weighted')",
  "confidence_threshold": "number (default: 0.7)"
}
```

**Response Schema:**
```json
{
  "vote_id": "string",
  "council_recommendation": "string",
  "aggregate_confidence": "number",
  "consensus_level": "string",
  "dissenting_opinions": ["string"]
}
```

---

## Recommendations

### POST /recommendations

Generate strategic recommendations based on research and analysis.

**Request Schema:**
```json
{
  "tenant_id": "string",
  "cep_id": "string",
  "jtbd_ids": ["string"],
  "risk_tolerance": "string"
}
```

**Response Schema:**
```json
{
  "decision_brief": {
    "id": "string",
    "title": "string",
    "key_recommendations": ["string"],
    "confidence_score": "number",
    "risk_assessment": "string"
  },
  "workflow": {
    "tenant_id": "string",
    "status": "string"
  }
}
```

**Test Example:**
```python
def test_recommendations_endpoint_returns_decision_brief():
    c = client()
    resp = c.post(
        "/recommendations",
        headers={"Idempotency-Key": "test-key-1234"},
        json={
            "tenant_id": "tenant-a",
            "cep_id": "cep-1", 
            "jtbd_ids": ["jtbd-1"],
            "risk_tolerance": "medium",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision_brief"]["id"].startswith("brief-")
    assert body["workflow"]["tenant_id"] == "tenant-a"
```

---

## Ingestion

### POST /ingestion/ingest

Process and ingest documents with content analysis.

**Request Schema:**
```json
{
  "tenant_id": "string",
  "filename": "string",
  "content": "string (base64 encoded)",
  "mimetype": "string"
}
```

**Response Schema:**
```json
{
  "document_id": "string",
  "needs_clarification": "boolean",
  "metrics": {
    "overall_confidence": "number",
    "processing_time_ms": "number"
  },
  "chunks": [
    {
      "id": "string",
      "index": "integer",
      "text": "string", 
      "confidence": "number",
      "kind": "string"
    }
  ]
}
```

**Test Example:**
```python
def test_ingestion_endpoint_returns_chunks():
    c = client()
    resp = c.post(
        "/ingestion/ingest",
        headers={"Idempotency-Key": "test-key-1234"},
        json={
            "tenant_id": "tenant-a",
            "filename": "notes.txt",
            "content": base64.b64encode(b"Evidence backed insight").decode(),
            "mimetype": "text/plain",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["needs_clarification"] is True
    assert body["metrics"]["overall_confidence"] < 0.7
    assert len(body["chunks"]) == 1
```

### POST /ingestion/clarify

Generate clarification prompts for low-confidence content.

**Request Schema:**
```json
{
  "document_id": "string",
  "chunks": [
    {
      "id": "string",
      "index": "integer",
      "text": "string",
      "confidence": "number",
      "kind": "string"
    }
  ],
  "threshold": "number (default: 0.7)"
}
```

**Response Schema:**
```json
{
  "clarification_id": "string",
  "prompts": [
    {
      "chunk_id": "string",
      "question": "string",
      "context": "string",
      "priority": "string"
    }
  ]
}
```

---

## Experiments & Forecasts

### POST /experiments

Create strategic experiment definitions.

**Request Schema:**
```json
{
  "tenant_id": "string",
  "title": "string",
  "hypothesis": "string",
  "success_metrics": ["string"],
  "duration_weeks": "integer",
  "confidence_threshold": "number"
}
```

**Response Schema:**
```json
{
  "experiment_id": "string",
  "tenant_id": "string", 
  "status": "string",
  "created_at": "datetime",
  "hypothesis_confidence": "number",
  "risk_factors": ["string"]
}
```

### POST /forecasts  

Generate predictive forecasts based on historical data.

**Request Schema:**
```json
{
  "tenant_id": "string",
  "forecast_type": "string",
  "time_horizon": "string", 
  "variables": ["string"],
  "confidence_intervals": ["number"]
}
```

**Response Schema:**
```json
{
  "forecast_id": "string",
  "predictions": [
    {
      "variable": "string",
      "predicted_value": "number",
      "confidence_interval": [number, number],
      "methodology": "string"
    }
  ],
  "model_performance": {
    "accuracy": "number",
    "mae": "number",
    "rmse": "number"
  }
}
```

---

## Evaluation Gates

### POST /evals/run

Execute evaluation gates for quality assurance.

**Request Schema:**
```json
{
  "tenant_id": "string",
  "suite": "string",
  "artifacts": "object (optional)",
  "thresholds": "object (optional)"
}
```

**Response Schema:**
```json
{
  "run_id": "string",
  "passed": "boolean",
  "overall_score": "number",
  "metrics": {
    "factscore": "number",
    "truthfulness": "number", 
    "coherence": "number",
    "actionability": "number"
  },
  "gates": {
    "constitutional_compliance": "string",
    "evidence_quality": "string",
    "bias_detection": "string"
  }
}
```

**Test Example:**
```python
def test_eval_run_endpoint_emits_metrics():
    c = client()
    resp = c.post(
        "/evals/run",
        headers={"Idempotency-Key": "test-key-1234"},
        json={"tenant_id": "tenant-a", "suite": "smoke"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"].startswith("eval-")
    assert body["passed"] is True
    assert "factscore" in body["metrics"]
```

---

## Debug & Configuration

### GET /debug/config/{section}/{name}

Retrieve configuration values (development only).

**Requires:** `STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1`

**Parameters:**
- `section`: Configuration section (router, retrieval, evals, privacy, compression)
- `name`: Configuration key name

**Response:**
```json
{
  "section": "string",
  "name": "string", 
  "value": "any",
  "type": "string",
  "description": "string"
}
```

**Example:**
```bash
# Requires debug endpoints enabled
curl -s http://localhost:8080/debug/config/router/default_model
```

---

## Schema Export

### GET /schemas/models

List all available Pydantic model schemas.

**Response:**
```json
{
  "models": ["string"],
  "version": "string",
  "total_count": "integer"
}
```

### GET /schemas/models/{name}

Get specific model schema definition.

**Response:**
```json
{
  "name": "string",
  "schema": "object",
  "version": "string", 
  "description": "string"
}
```

**Example:**
```bash
curl -s http://localhost:8080/schemas/models/ResearchPlanRequest
```

---

## Error Handling

### Common Error Responses

**400 Bad Request - Missing Idempotency Key:**
```json
{
  "detail": "Idempotency-Key header is required",
  "type": "validation_error"
}
```

**422 Unprocessable Entity - Validation Error:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "query"],
      "msg": "String should have at least 3 characters",
      "input": "ai"
    }
  ]
}
```

**Test Example:**
```python
def test_missing_idempotency_key_rejected():
    c = client()
    resp = c.post(
        "/research/plan",
        json={"query": "market", "tenant_id": "tenant-a"},
    )
    assert resp.status_code == 400
    assert "Idempotency-Key" in resp.json()["detail"]
```

## Model Definitions

All models use Pydantic v2 with strict validation:

### Core Models
- `Source` - Research source with metadata
- `Claim` - Structured claim with confidence  
- `Evidence` - Supporting evidence with provenance
- `Assumption` - Underlying assumptions requiring validation
- `Hypothesis` - Testable hypothesis definitions

### Workflow Models
- `DecisionBrief` - Strategic recommendation synthesis
- `RecommendationOutcome` - Implementation guidance
- `ExperimentDefinition` - Strategic experiment configuration

### AI Models
- `DebateTrace` - Multi-agent debate conversation
- `ExpertMemo` - Domain expert evaluation  
- `ConstitutionalCompliance` - Safety and accuracy validation

---

<div class="note">
<p><strong>📝 Note:</strong> All code examples in this reference are derived from the actual test suite in <code>packages/api/tests/</code> to ensure accuracy and up-to-date functionality.</p>
</div>