---
title: Quick Start Tutorial
description: Get up and running with StratMaster in 10 minutes
version: 0.1.0
platform: Python 3.11+, Docker
nav_order: 1
parent: Tutorials
---

# Quick Start Tutorial

Get StratMaster running on your machine in under 10 minutes. This tutorial will walk you through setting up the environment, starting the API server, and making your first strategic research request.

## Prerequisites

Before you begin, ensure you have:
- **Python 3.11+** installed
- **Docker Desktop** (optional, for full stack)
- **Git** for cloning the repository
- **4GB+ RAM** available

## Step 1: Environment Setup

First, clone the repository and set up your development environment:

```bash
# Clone the repository
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster

# Bootstrap the development environment
make bootstrap
```

This command will:
- Create a Python virtual environment (`.venv`)
- Install the StratMaster API package  
- Install development tools (pytest, pre-commit)
- Set up pre-commit hooks

<div class="note">
<p><strong>💡 Note:</strong> The bootstrap process typically takes 2-3 minutes. If you encounter network timeouts, this is normal in restricted environments - the core functionality will still work.</p>
</div>

## Step 2: Verify Installation

Run the test suite to ensure everything is working:

```bash
# Run API tests (fast - about 1 second)
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
```

**Expected output:**
```
.....................
23 passed in 1.28s
```

## Step 3: Start the API Server

Launch the FastAPI server:

```bash
# Start the API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
INFO:     Started reloader process [1234] using WatchFiles
INFO:     Application startup complete.
```

## Step 4: Test the Health Endpoint

Open a new terminal and verify the server is running:

```bash
curl -s http://127.0.0.1:8080/healthz
```

**Expected response:**
```json
{"status":"ok"}
```

## Step 5: Explore the API Documentation

Visit the interactive API documentation in your browser:
- **Swagger UI**: http://127.0.0.1:8080/docs
- **ReDoc**: http://127.0.0.1:8080/redoc
- **OpenAPI Schema**: http://127.0.0.1:8080/openapi.json

## Step 6: Your First Research Request

Now let's create your first strategic research plan. **All POST endpoints require an `Idempotency-Key` header** for safe retries.

### Create a Research Plan

```bash
curl -X POST http://127.0.0.1:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: quickstart-demo-001" \
  -d '{
    "query": "brand strategy trends 2024",
    "tenant_id": "demo-tenant",
    "max_sources": 3
  }'
```

**Expected response:**
```json
{
  "plan_id": "plan-abc123def456",
  "tenant_id": "demo-tenant", 
  "query": "brand strategy trends 2024",
  "tasks": [
    {
      "id": "task-1",
      "type": "web_search",
      "query": "brand strategy trends 2024",
      "priority": "high"
    },
    {
      "id": "task-2", 
      "type": "academic_search",
      "query": "brand positioning digital transformation",
      "priority": "medium"
    },
    {
      "id": "task-3",
      "type": "industry_analysis", 
      "query": "marketing technology adoption rates",
      "priority": "medium"
    }
  ],
  "sources": [
    {
      "id": "src-1",
      "url": "https://example.com/marketing-trends",
      "type": "web_page",
      "priority": 0.9
    },
    {
      "id": "src-2",
      "url": "https://example.com/brand-study", 
      "type": "research_paper",
      "priority": 0.8
    },
    {
      "id": "src-3",
      "url": "https://example.com/industry-report",
      "type": "industry_report", 
      "priority": 0.7
    }
  ],
  "estimated_duration_minutes": 45,
  "created_at": "2024-01-18T10:30:00Z"
}
```

### Execute the Research Plan

Use the `plan_id` from above to execute the research:

```bash
curl -X POST http://127.0.0.1:8080/research/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: quickstart-demo-002" \
  -d '{
    "plan_id": "plan-abc123def456",
    "tenant_id": "demo-tenant"
  }'
```

**Expected response includes:**
```json
{
  "session_id": "session-xyz789abc123",
  "tenant_id": "demo-tenant",
  "claims": [
    {
      "id": "claim-1",
      "text": "Digital transformation is driving 67% of brand strategy changes in 2024",
      "confidence": 0.85,
      "evidence_count": 3,
      "source_ids": ["src-1", "src-2"]
    }
  ],
  "evidence": [
    {
      "text": "Survey of 1000 enterprises shows 67% reported major brand strategy shifts",
      "source_id": "src-1", 
      "url": "https://example.com/marketing-trends",
      "relevance_score": 0.95,
      "credibility_score": 0.88
    }
  ],
  "status": "completed",
  "completed_at": "2024-01-18T10:35:00Z"
}
```

### Generate Strategic Recommendations

Finally, generate actionable recommendations based on the research:

```bash
curl -X POST http://127.0.0.1:8080/recommendations \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: quickstart-demo-003" \
  -d '{
    "tenant_id": "demo-tenant",
    "cep_id": "cep-digital-transformation",
    "jtbd_ids": ["jtbd-brand-modernization"],
    "risk_tolerance": "medium"
  }'
```

**Expected response includes:**
```json
{
  "decision_brief": {
    "id": "brief-def789ghi012",
    "title": "Digital Brand Transformation Strategy", 
    "key_recommendations": [
      "Implement customer-centric digital touchpoints",
      "Develop data-driven brand messaging framework",
      "Establish cross-channel brand consistency protocols"
    ],
    "confidence_score": 0.82,
    "risk_assessment": "medium"
  },
  "workflow": {
    "tenant_id": "demo-tenant",
    "status": "completed"
  }
}
```

## Step 7: What's Next?

Congratulations! You've successfully:
- ✅ Set up StratMaster locally
- ✅ Created a research plan
- ✅ Executed research with evidence collection
- ✅ Generated strategic recommendations

### Next Steps

| Goal | Next Tutorial |
|------|---------------|
| **Build a complete analysis** | [Your First Strategy Analysis](first-analysis.md) |
| **Set up multi-agent validation** | [Multi-Agent Debate Setup](multi-agent-setup.md) |
| **Deploy to production** | [Production Deployment](production-deployment.md) |
| **Understand the architecture** | [Architecture Overview](../explanation/architecture.md) |

### Explore More Features

The system includes many more capabilities:
- **Multi-Agent Debate**: Validate findings through AI critic review
- **Expert Council**: Leverage domain expertise evaluation
- **Graph Knowledge**: Build knowledge graphs from research
- **Evaluation Gates**: Ensure quality with automated testing
- **Full Stack**: Complete UI and infrastructure services

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find and kill the process using port 8080
lsof -ti:8080 | xargs kill -9
```

**Import errors:**
```bash
# Ensure you're using the virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

**Bootstrap fails:**
```bash
# If network timeouts occur, try Docker instead
make test-docker
```

### Getting Help

- **Documentation**: Browse the [How-to Guides](../how-to/) for specific problems
- **Reference**: Check the [API Reference](../reference/api/) for endpoint details  
- **Issues**: Report bugs on [GitHub Issues](https://github.com/IAmJonoBo/StratMaster/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)

---

<div class="success">
<p><strong>🎉 Success!</strong> You now have StratMaster running locally and have made your first strategic research requests. The system is ready for more advanced workflows!</p>
</div>