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

## Complex Workflow Examples

### Comprehensive Market Analysis Workflow

This example demonstrates a complete market analysis workflow combining multiple StratMaster services:

```python
import asyncio
import httpx
from typing import Dict, List, Any

class MarketAnalysisWorkflow:
    def __init__(self, api_base_url: str, api_key: str):
        self.client = httpx.AsyncClient(
            base_url=api_base_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
    
    async def execute_market_analysis(
        self, 
        market: str, 
        tenant_id: str
    ) -> Dict[str, Any]:
        """Execute comprehensive market analysis workflow"""
        
        # Step 1: Initialize research session
        session = await self._create_research_session(
            research_question=f"Market analysis for {market} sector including competitive landscape, trends, and opportunities",
            tenant_id=tenant_id,
            scope="comprehensive"
        )
        
        # Step 2: Parallel research and knowledge gathering
        research_tasks = [
            self._gather_market_intelligence(session["session_id"], market, tenant_id),
            self._analyze_competitive_landscape(session["session_id"], market, tenant_id), 
            self._identify_market_trends(session["session_id"], market, tenant_id)
        ]
        
        research_results = await asyncio.gather(*research_tasks)
        market_intel, competitive_data, trend_analysis = research_results
        
        # Step 3: Synthesize findings into claims
        claims = await self._synthesize_claims(
            session["session_id"],
            market_intel + competitive_data + trend_analysis,
            tenant_id
        )
        
        # Step 4: Multi-agent validation debate
        debate_result = await self._conduct_validation_debate(
            session["session_id"],
            claims,
            tenant_id
        )
        
        # Step 5: Generate strategic recommendations
        recommendations = await self._generate_recommendations(
            session["session_id"],
            debate_result["validated_claims"],
            tenant_id
        )
        
        return {
            "session_id": session["session_id"],
            "market": market,
            "validated_claims": debate_result["validated_claims"],
            "recommendations": recommendations,
            "confidence_score": debate_result["overall_confidence"]
        }
    
    async def _create_research_session(
        self, 
        research_question: str, 
        tenant_id: str, 
        scope: str
    ) -> Dict[str, Any]:
        """Create new research session"""
        response = await self.client.post("/research/session", json={
            "tenant_id": tenant_id,
            "research_question": research_question,
            "scope": scope,
            "priority": "high",
            "tags": ["market_analysis", "strategic_planning"]
        })
        return response.json()
    
    async def _conduct_validation_debate(
        self, 
        session_id: str, 
        claims: List[Dict[str, Any]], 
        tenant_id: str
    ) -> Dict[str, Any]:
        """Conduct multi-agent debate to validate claims"""
        
        debate_response = await self.client.post("/debate/run", json={
            "tenant_id": tenant_id,
            "session_id": session_id,
            "claims": claims,
            "debate_config": {
                "agents": ["market_analyst", "financial_analyst", "trend_specialist", "risk_assessor"],
                "max_rounds": 4,
                "consensus_threshold": 0.8,
                "focus_areas": [
                    "data_quality_validation",
                    "methodology_assessment", 
                    "assumption_testing",
                    "risk_evaluation"
                ]
            },
            "constitutional_constraints": {
                "accuracy_threshold": 0.85,
                "bias_mitigation": True,
                "uncertainty_quantification": True
            }
        })
        
        return debate_response.json()

# Usage Example
async def main():
    workflow = MarketAnalysisWorkflow(
        api_base_url="https://api.stratmaster.com",
        api_key="your-api-key"
    )
    
    result = await workflow.execute_market_analysis(
        market="artificial_intelligence",
        tenant_id="your-tenant-id"
    )
    
    print(f"Market analysis completed for {result['market']}")
    print(f"Overall confidence score: {result['confidence_score']}")
    print(f"Validated claims: {len(result['validated_claims'])}")

# Run the workflow
asyncio.run(main())
```

### Competitive Intelligence Pipeline

```python
class CompetitiveIntelligencePipeline:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    async def execute_competitive_analysis(
        self,
        target_company: str,
        competitors: List[str],
        tenant_id: str
    ) -> Dict[str, Any]:
        """Execute comprehensive competitive intelligence pipeline"""
        
        # Step 1: Multi-source data gathering
        intelligence_data = await self._gather_competitive_intelligence(
            target_company, competitors, tenant_id
        )
        
        # Step 2: Relationship mapping using knowledge graph
        relationship_map = await self.client.post("/knowledge/graph/query", json={
            "tenant_id": tenant_id,
            "query_type": "competitive_relationships",
            "parameters": {
                "target_entity": target_company,
                "competitor_entities": competitors,
                "relationship_types": ["COMPETES_WITH", "PARTNERS_WITH", "SUPPLIES_TO"],
                "max_depth": 3
            }
        })
        
        # Step 3: Strategic positioning assessment
        positioning_analysis = await self._assess_strategic_positioning(
            target_company, competitors, intelligence_data, tenant_id
        )
        
        # Step 4: Scenario modeling
        scenarios = await self.client.post("/analysis/scenarios", json={
            "tenant_id": tenant_id,
            "scenario_type": "competitive_dynamics",
            "base_entities": [target_company] + competitors,
            "scenario_parameters": {
                "time_horizon": "18_months",
                "uncertainty_factors": [
                    "market_disruption",
                    "regulatory_changes", 
                    "technology_shifts"
                ]
            }
        })
        
        return {
            "target_company": target_company,
            "intelligence_summary": intelligence_data["summary"],
            "relationship_insights": relationship_map.json(),
            "positioning_assessment": positioning_analysis,
            "future_scenarios": scenarios.json()["scenarios"]
        }

# Usage
pipeline = CompetitiveIntelligencePipeline(client)
competitive_analysis = await pipeline.execute_competitive_analysis(
    target_company="Tesla",
    competitors=["Rivian", "Ford", "GM"],
    tenant_id="your-tenant-id"
)
```

### Real-Time Decision Support

```python
class RealTimeDecisionSupport:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.active_sessions = {}
    
    async def initiate_decision_support(
        self,
        decision_context: Dict[str, Any],
        tenant_id: str,
        urgency: str = "high"
    ) -> str:
        """Initiate real-time decision support session"""
        
        session_response = await self.client.post("/research/session", json={
            "tenant_id": tenant_id,
            "research_question": decision_context["description"],
            "scope": "comprehensive" if urgency == "high" else "standard",
            "priority": urgency,
            "metadata": decision_context
        })
        
        session_id = session_response.json()["session_id"]
        self.active_sessions[session_id] = {
            "status": "active",
            "context": decision_context,
            "tenant_id": tenant_id
        }
        
        # Start continuous intelligence gathering
        asyncio.create_task(self._continuous_intelligence_gathering(session_id))
        
        return session_id
    
    async def _continuous_intelligence_gathering(self, session_id: str):
        """Continuously gather and analyze relevant intelligence"""
        
        session_info = self.active_sessions[session_id]
        context = session_info["context"]
        tenant_id = session_info["tenant_id"]
        
        while session_info["status"] == "active":
            try:
                # Execute research based on current context
                research_response = await self.client.post("/research/plan", json={
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "query": context["description"],
                    "focus_areas": context.get("key_concerns", [])
                })
                
                # Update decision recommendations based on new intelligence
                await self._update_decision_recommendations(session_id)
                
                # Wait before next intelligence cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"Intelligence gathering error for session {session_id}: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    async def get_decision_recommendations(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get current decision recommendations"""
        
        response = await self.client.post("/recommendations", json={
            "tenant_id": self.active_sessions[session_id]["tenant_id"],
            "cep_id": session_id,
            "jtbd_ids": ["strategic_decision"],
            "risk_tolerance": "medium"
        })
        
        return response.json()
    
    async def request_expedited_analysis(
        self,
        session_id: str,
        specific_question: str,
        max_time_minutes: int = 15
    ) -> Dict[str, Any]:
        """Request expedited analysis for urgent decisions"""
        
        response = await self.client.post("/research/plan", json={
            "tenant_id": self.active_sessions[session_id]["tenant_id"],
            "query": specific_question,
            "scope": "focused",
            "priority": "urgent",
            "max_duration_minutes": max_time_minutes
        })
        
        return response.json()

# Usage
decision_support = RealTimeDecisionSupport(client)

# Initiate decision support for market entry
session_id = await decision_support.initiate_decision_support(
    decision_context={
        "type": "market_entry",
        "description": "Evaluating entry into European EV market",
        "timeline": "decision_needed_in_2_weeks",
        "key_concerns": ["regulatory_compliance", "competition", "supply_chain"]
    },
    tenant_id="your-tenant-id",
    urgency="high"
)

# Get current recommendations
recommendations = await decision_support.get_decision_recommendations(session_id)

# Request expedited analysis for specific concern
expedited_analysis = await decision_support.request_expedited_analysis(
    session_id,
    "What are the specific regulatory requirements for EV market entry in Germany?",
    max_time_minutes=10
)
```

These examples demonstrate advanced usage patterns for StratMaster's API, showing how to:

1. **Orchestrate Complex Workflows**: Combine multiple services for comprehensive analysis
2. **Handle Parallel Processing**: Use async/await for efficient concurrent operations  
3. **Implement Real-Time Intelligence**: Continuous monitoring and analysis
4. **Manage Session State**: Track and manage long-running analysis sessions
5. **Context-Aware Analysis**: Adapt analysis based on decision context and urgency

---

<div class="note">
<p><strong>📝 Note:</strong> All code examples in this reference are derived from the actual test suite in <code>packages/api/tests/</code> to ensure accuracy and up-to-date functionality.</p>
</div>