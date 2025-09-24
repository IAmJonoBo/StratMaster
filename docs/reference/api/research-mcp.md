# Research MCP API Reference

The Research MCP (Model Control Protocol) server handles web research, data crawling, and evidence collection operations. It provides structured research planning and execution capabilities with comprehensive source validation.

## Service Information

- **Port**: 8081 (when running full stack)
- **URL**: http://localhost:8081
- **Protocol**: HTTP/REST API
- **Purpose**: Web research and crawling operations

## Overview

The Research MCP orchestrates the complete research workflow:

1. **Research Planning** - Generates structured research tasks and identifies candidate sources
2. **Source Validation** - Evaluates source credibility and relevance
3. **Content Extraction** - Crawls and extracts structured content from validated sources
4. **Claim Generation** - Produces evidence-backed claims with provenance tracking
5. **Quality Assessment** - Evaluates research completeness and source diversity

## Core Capabilities

### Research Planning
- Query decomposition into structured research tasks
- Source discovery and relevance ranking  
- Research scope definition and constraint handling
- Task prioritization based on evidence requirements

### Web Crawling
- Respectful crawling with rate limiting and robots.txt compliance
- Content extraction from diverse web formats (HTML, PDF, structured data)
- Media handling for images, videos, and documents
- JavaScript-rendered content support

### Evidence Extraction
- Fact extraction with confidence scoring
- Claim-evidence relationship mapping
- Source attribution and citation generation
- Bias detection and source credibility assessment

### Data Validation
- Source authenticity verification
- Content freshness and accuracy checks
- Cross-source validation and conflict resolution
- Misinformation and hallucination detection

## API Endpoints

!!! note "Integration Pattern"
    Research MCP endpoints are typically accessed through the Gateway API's `/research/*` routes, which provide standardized request/response handling and authentication.

### Direct MCP Endpoints

#### Health Check
```http
GET /health
```
Returns service health status and version information.

#### Research Task Planning
```http
POST /research/plan
```
Generates comprehensive research plan with task decomposition.

**Request:**
```json
{
  "query": "sustainable packaging market trends",
  "scope": "global",
  "depth": "comprehensive",
  "max_sources": 25,
  "time_horizon": "2024",
  "quality_threshold": 0.8
}
```

**Response:**
```json
{
  "plan_id": "rp_20240101_001",
  "tasks": [
    {
      "task_id": "t1",
      "description": "Market size and growth analysis", 
      "priority": 1,
      "estimated_sources": 8,
      "keywords": ["sustainable packaging", "market size", "growth rate"]
    }
  ],
  "candidate_sources": [
    {
      "url": "https://example.com/report",
      "title": "Global Sustainable Packaging Report 2024",
      "relevance_score": 0.95,
      "credibility_score": 0.88,
      "last_updated": "2024-01-15T10:00:00Z"
    }
  ],
  "estimated_duration": "15-20 minutes",
  "confidence": 0.92
}
```

#### Research Execution
```http
POST /research/execute
```
Executes research plan and returns collected evidence.

**Request:**
```json
{
  "plan_id": "rp_20240101_001",
  "execution_mode": "comprehensive",
  "parallel_crawling": true,
  "quality_gates": true
}
```

**Response:**
```json
{
  "execution_id": "re_20240101_001",
  "status": "completed",
  "claims": [
    {
      "claim_id": "c1",
      "statement": "Sustainable packaging market expected to reach $440B by 2030",
      "confidence": 0.91,
      "evidence": [
        {
          "source_url": "https://example.com/report",
          "excerpt": "Market analysis shows...",
          "extraction_method": "structured_data",
          "reliability": 0.89
        }
      ],
      "provenance": {
        "extraction_time": "2024-01-20T14:30:00Z",
        "methodology": "cross_source_validation",
        "validation_score": 0.87
      }
    }
  ],
  "sources_processed": 23,
  "success_rate": 0.91,
  "quality_score": 0.86
}
```

#### Source Validation
```http
POST /sources/validate
```
Validates source credibility and content quality.

**Request:**
```json
{
  "sources": [
    {
      "url": "https://example.com/article",
      "content_type": "article",
      "claimed_date": "2024-01-15"
    }
  ],
  "validation_criteria": {
    "check_authority": true,
    "verify_freshness": true,
    "assess_bias": true,
    "validate_claims": true
  }
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RESEARCH_MCP_PORT` | 8081 | Service port |
| `RESEARCH_MAX_PARALLEL_CRAWLS` | 5 | Concurrent crawling limit |
| `RESEARCH_REQUEST_TIMEOUT` | 30s | HTTP request timeout |
| `RESEARCH_RESPECT_ROBOTS` | true | Honor robots.txt files |
| `RESEARCH_USER_AGENT` | "StratMaster-Research/1.0" | Crawling user agent |
| `RESEARCH_RATE_LIMIT` | "1/second" | Rate limiting configuration |

### Quality Thresholds

```yaml
# configs/research/quality-thresholds.yaml
source_credibility_min: 0.7
content_relevance_min: 0.8
fact_confidence_min: 0.75
cross_validation_sources: 3
bias_detection_enabled: true
hallucination_check_enabled: true
```

## Integration Patterns

### Through Gateway API
```python
import httpx

async def research_workflow(query: str):
    async with httpx.AsyncClient() as client:
        # Plan research
        plan_response = await client.post(
            "http://localhost:8080/research/plan",
            headers={"Idempotency-Key": "plan-001"},
            json={
                "query": query,
                "tenant_id": "demo",
                "max_sources": 10
            }
        )
        plan = plan_response.json()
        
        # Execute research
        run_response = await client.post(
            "http://localhost:8080/research/run",
            headers={"Idempotency-Key": "run-001"}, 
            json={
                "plan_id": plan["plan_id"],
                "tenant_id": "demo"
            }
        )
        return run_response.json()
```

### Direct MCP Integration
```python
import httpx

async def direct_research():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/research/plan",
            json={
                "query": "market analysis",
                "scope": "global",
                "max_sources": 15
            }
        )
        return response.json()
```

## Error Handling

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `400` | Invalid research parameters | Check query format and constraints |
| `429` | Rate limit exceeded | Implement exponential backoff |
| `503` | Crawling service unavailable | Retry after delay or check source accessibility |
| `422` | Source validation failed | Review source URLs and accessibility |

### Error Response Format
```json
{
  "error": {
    "code": "CRAWL_FAILED",
    "message": "Unable to access source content",
    "details": {
      "url": "https://example.com/blocked",
      "status_code": 403,
      "robots_txt_blocked": true
    },
    "retry_after": 300
  }
}
```

## Performance Characteristics

### Throughput
- **Concurrent Sources**: Up to 5 parallel crawls
- **Average Response Time**: 2-15 seconds per source
- **Batch Processing**: 25+ sources in 15-20 minutes
- **Quality Validation**: <1 second per source

### Resource Usage
- **Memory**: ~100MB baseline + ~10MB per concurrent crawl
- **Network**: Respectful crawling with 1 request/second default
- **Storage**: Temporary content caching for validation

## Monitoring and Observability

### Health Metrics
- Service uptime and response times
- Crawling success rates and failure patterns
- Source validation accuracy scores
- Quality gate effectiveness metrics

### Tracing Integration
Research operations are fully integrated with OpenTelemetry tracing:
```python
# Automatic span creation for research operations
with tracer.start_as_current_span("research.plan") as span:
    span.set_attribute("query.length", len(query))
    span.set_attribute("max_sources", max_sources)
    # Research planning logic
```

## Security Considerations

### Content Safety
- Malware and phishing URL detection
- Content sanitization and XSS prevention
- PII redaction in extracted content
- Source authenticity verification

### Privacy Protection
- No storage of personally identifiable information
- Anonymized request logging
- Secure content transmission
- Compliance with data protection regulations

## See Also

- [Gateway API Reference](gateway.md) - Main API orchestration
- [Knowledge MCP API](knowledge-mcp.md) - Knowledge graph operations
- [Quality Configuration](../configuration/yaml-configs.md#research-quality) - Research quality settings
- [Troubleshooting Research Issues](../../how-to/troubleshooting.md#research-problems) - Common problems and solutions