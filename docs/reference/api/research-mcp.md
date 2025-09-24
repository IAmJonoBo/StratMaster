---
title: Research MCP API Reference
description: Complete API reference for the Research MCP server
version: 0.3.0
nav_order: 2
---

# Research MCP API Reference

The Research MCP server provides comprehensive research capabilities including web search, content crawling, and resource caching. This service enables strategic analysis by gathering external information from trusted sources.

## Base Information

**Base URL**: `http://localhost:8081`  
**Version**: 0.3.0  
**OpenAPI Spec**: `/docs`

## Authentication

All requests to the Research MCP server require tenant isolation. Include the `tenant_id` in request payloads to ensure data isolation.

```bash
# All requests should include tenant context
curl -X POST http://localhost:8081/tools/metasearch \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "your-tenant-id", "query": "market analysis"}'
```

## Service Information

### GET /info

Get service information and capabilities.

**Response:**
```json
{
  "name": "research-mcp",
  "version": "0.3.0",
  "capabilities": [
    "health", 
    "info", 
    "metasearch", 
    "crawl", 
    "resources"
  ],
  "allowlist": ["*.example.com", "trusted-site.org"],
  "network_enabled": true
}
```

### GET /healthz

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Search Tools

### POST /tools/metasearch

Perform multi-engine web search across configured search providers.

**Request Body:**
```json
{
  "tenant_id": "string",
  "query": "string (min: 3 chars)",
  "limit": "integer (1-20, default: 5)"
}
```

**Response:**
```json
{
  "query": "market analysis AI adoption",
  "results": [
    {
      "title": "AI Adoption Trends in Enterprise Markets",
      "url": "https://example.com/ai-trends-2024",
      "snippet": "Recent studies show 67% of enterprises are actively exploring AI solutions...",
      "fetched_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8081/tools/metasearch \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-abc",
    "query": "AI market trends 2024",
    "limit": 10
  }'
```

**Error Responses:**
- `400 Bad Request`: Invalid query parameters
- `403 Forbidden`: Search blocked by allowlist
- `429 Too Many Requests`: Rate limit exceeded

## Web Crawling

### POST /tools/crawl

Crawl web pages and extract structured content.

**Request Body:**
```json
{
  "tenant_id": "string",
  "spec": {
    "url": "https://example.com",
    "obey_robots": true,
    "max_depth": "integer (1-3, default: 1)",
    "render_js": false
  }
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "pages": [
    {
      "url": "https://example.com/page1",
      "title": "Market Analysis Report",
      "content": "Extracted page content...",
      "metadata": {
        "word_count": 1500,
        "last_modified": "2024-01-15T09:00:00Z",
        "language": "en"
      },
      "cache_key": "cache_abc123",
      "crawled_at": "2024-01-15T10:45:00Z"
    }
  ],
  "crawl_stats": {
    "total_pages": 1,
    "successful_pages": 1,
    "failed_pages": 0,
    "total_time_seconds": 2.5
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8081/tools/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-abc",
    "spec": {
      "url": "https://trusted-source.com/report",
      "obey_robots": true,
      "max_depth": 2,
      "render_js": false
    }
  }'
```

**Error Responses:**
- `400 Bad Request`: Invalid crawl specification
- `403 Forbidden`: URL not in allowlist
- `404 Not Found`: URL unreachable
- `429 Too Many Requests`: Crawl rate limit exceeded

## Resource Management

### GET /resources/cached_page/{cache_key}

Retrieve cached page content by cache key.

**Parameters:**
- `cache_key`: String identifier from crawl response

**Response:**
```json
{
  "cache_key": "cache_abc123",
  "url": "https://example.com/page1",
  "title": "Market Analysis Report",
  "content": "Full page content...",
  "metadata": {
    "word_count": 1500,
    "last_modified": "2024-01-15T09:00:00Z",
    "language": "en",
    "content_type": "text/html"
  },
  "cached_at": "2024-01-15T10:45:00Z"
}
```

**Example:**
```bash
curl http://localhost:8081/resources/cached_page/cache_abc123
```

**Error Responses:**
- `404 Not Found`: Cache key not found or expired

### GET /resources/provenance/{cache_key}

Get provenance information for cached content.

**Parameters:**
- `cache_key`: String identifier from crawl response

**Response:**
```json
{
  "cache_key": "cache_abc123",
  "original_url": "https://example.com/page1",
  "crawl_timestamp": "2024-01-15T10:45:00Z",
  "crawl_config": {
    "obey_robots": true,
    "max_depth": 1,
    "render_js": false
  },
  "tenant_id": "tenant-abc",
  "content_hash": "sha256:abc123...",
  "expiry": "2024-01-22T10:45:00Z"
}
```

**Example:**
```bash
curl http://localhost:8081/resources/provenance/cache_abc123
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RESEARCH_MCP_HOST` | Server bind host | `127.0.0.1` |
| `RESEARCH_MCP_PORT` | Server port | `8081` |
| `RESEARCH_MCP_LOG_LEVEL` | Log level | `INFO` |
| `RESEARCH_MCP_ALLOWLIST` | Comma-separated allowed domains | `""` |
| `RESEARCH_MCP_USE_NETWORK` | Enable network access | `true` |
| `RESEARCH_MCP_CACHE_TTL` | Cache TTL in seconds | `3600` |
| `RESEARCH_MCP_MAX_PAGES` | Max pages per crawl | `10` |
| `RESEARCH_MCP_REQUEST_TIMEOUT` | HTTP request timeout | `30` |

### Search Providers

Configure multiple search backends:

```yaml
# config/research-mcp.yaml
search:
  providers:
    - name: "duckduckgo"
      enabled: true
      weight: 1.0
    - name: "bing"
      enabled: true
      weight: 0.8
      api_key: "${BING_API_KEY}"
    - name: "google"
      enabled: false
      api_key: "${GOOGLE_API_KEY}"
      cx: "${GOOGLE_CX}"

crawling:
  allowlist:
    - "*.wikipedia.org"
    - "*.github.com"
    - "example.com"
  robots_cache_ttl: 3600
  max_concurrent: 5
  user_agent: "StratMaster Research Bot 1.0"
```

## Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|---------|
| `/tools/metasearch` | 100 requests | 1 minute |
| `/tools/crawl` | 20 requests | 1 minute |
| `/resources/*` | 1000 requests | 1 minute |

## Error Handling

The Research MCP server uses standard HTTP status codes and provides detailed error messages:

### Common Error Format

```json
{
  "detail": "Error description",
  "error_code": "RESEARCH_ERROR_001",
  "timestamp": "2024-01-15T10:45:00Z",
  "tenant_id": "tenant-abc"
}
```

### Error Codes

| Code | Description | Status |
|------|-------------|---------|
| `RESEARCH_ERROR_001` | Invalid query parameters | 400 |
| `RESEARCH_ERROR_002` | URL not in allowlist | 403 |
| `RESEARCH_ERROR_003` | Crawl timeout | 408 |
| `RESEARCH_ERROR_004` | Rate limit exceeded | 429 |
| `RESEARCH_ERROR_005` | Network error | 502 |

## SDK Examples

### Python Client

```python
import httpx
from typing import Dict, List, Any

class ResearchMCPClient:
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def search(
        self, 
        tenant_id: str, 
        query: str, 
        limit: int = 5
    ) -> Dict[str, Any]:
        """Perform metasearch"""
        response = await self.client.post(
            "/tools/metasearch",
            json={
                "tenant_id": tenant_id,
                "query": query,
                "limit": limit
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def crawl(
        self, 
        tenant_id: str, 
        url: str, 
        max_depth: int = 1
    ) -> Dict[str, Any]:
        """Crawl web pages"""
        response = await self.client.post(
            "/tools/crawl",
            json={
                "tenant_id": tenant_id,
                "spec": {
                    "url": url,
                    "max_depth": max_depth,
                    "obey_robots": True
                }
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_cached_page(self, cache_key: str) -> Dict[str, Any]:
        """Get cached page content"""
        response = await self.client.get(f"/resources/cached_page/{cache_key}")
        response.raise_for_status()
        return response.json()

# Usage example
async def main():
    client = ResearchMCPClient()
    
    # Search for information
    search_results = await client.search(
        tenant_id="my-tenant",
        query="AI market trends",
        limit=10
    )
    
    # Crawl a specific page
    crawl_results = await client.crawl(
        tenant_id="my-tenant",
        url="https://example.com/ai-report",
        max_depth=2
    )
    
    # Get cached content
    if crawl_results["pages"]:
        cache_key = crawl_results["pages"][0]["cache_key"]
        cached_content = await client.get_cached_page(cache_key)
```

### JavaScript Client

```javascript
class ResearchMCPClient {
    constructor(baseUrl = 'http://localhost:8081') {
        this.baseUrl = baseUrl;
    }
    
    async search(tenantId, query, limit = 5) {
        const response = await fetch(`${this.baseUrl}/tools/metasearch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tenant_id: tenantId,
                query: query,
                limit: limit
            })
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async crawl(tenantId, url, maxDepth = 1) {
        const response = await fetch(`${this.baseUrl}/tools/crawl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tenant_id: tenantId,
                spec: {
                    url: url,
                    max_depth: maxDepth,
                    obey_robots: true
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`Crawl failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Usage
const client = new ResearchMCPClient();

try {
    const results = await client.search('my-tenant', 'AI trends', 10);
    console.log('Search results:', results);
    
    const crawlData = await client.crawl('my-tenant', 'https://example.com');
    console.log('Crawl data:', crawlData);
} catch (error) {
    console.error('Error:', error);
}
```

## Integration Patterns

### Research Pipeline Integration

```python
# Integrate with StratMaster research pipeline
class ResearchPipeline:
    def __init__(self):
        self.research_client = ResearchMCPClient()
    
    async def gather_evidence(
        self, 
        tenant_id: str, 
        research_question: str
    ) -> List[Dict]:
        """Gather evidence for research question"""
        
        # Step 1: Search for relevant sources
        search_results = await self.research_client.search(
            tenant_id=tenant_id,
            query=research_question,
            limit=15
        )
        
        evidence = []
        
        # Step 2: Crawl promising sources
        for result in search_results["results"][:5]:
            try:
                crawl_data = await self.research_client.crawl(
                    tenant_id=tenant_id,
                    url=str(result["url"]),
                    max_depth=1
                )
                
                for page in crawl_data["pages"]:
                    evidence.append({
                        "source_url": page["url"],
                        "title": page["title"],
                        "content": page["content"][:2000],  # Truncate
                        "cache_key": page["cache_key"],
                        "relevance_score": self._calculate_relevance(
                            research_question, 
                            page["content"]
                        )
                    })
                    
            except Exception as e:
                print(f"Failed to crawl {result['url']}: {e}")
                continue
        
        # Sort by relevance
        evidence.sort(key=lambda x: x["relevance_score"], reverse=True)
        return evidence[:10]  # Top 10 most relevant
```

### Caching Strategy

```python
# Implement intelligent caching
class ResearchCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.research_client = ResearchMCPClient()
    
    async def cached_search(
        self, 
        tenant_id: str, 
        query: str, 
        ttl: int = 3600
    ) -> Dict:
        """Search with Redis caching"""
        cache_key = f"search:{tenant_id}:{hash(query)}"
        
        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Fallback to API
        results = await self.research_client.search(tenant_id, query)
        
        # Cache results
        await self.redis.setex(
            cache_key, 
            ttl, 
            json.dumps(results)
        )
        
        return results
```

## Best Practices

### Security Considerations

1. **Allowlist Management**: Always configure domain allowlists for production
2. **Rate Limiting**: Implement client-side rate limiting to avoid 429 errors
3. **Content Validation**: Validate crawled content before processing
4. **Tenant Isolation**: Always include tenant_id in requests

### Performance Optimization

1. **Concurrent Requests**: Use async clients for parallel operations
2. **Caching**: Implement intelligent caching for repeated queries
3. **Content Limits**: Set reasonable limits for crawled content size
4. **Connection Pooling**: Reuse HTTP connections when possible

### Error Handling

1. **Retry Logic**: Implement exponential backoff for transient errors
2. **Graceful Degradation**: Handle service unavailability gracefully
3. **Logging**: Log all errors with context for debugging
4. **Circuit Breaker**: Implement circuit breaker pattern for reliability

## Monitoring and Debugging

### Health Monitoring

```bash
# Check service health
curl http://localhost:8081/healthz

# Get service information
curl http://localhost:8081/info
```

### Logs

Research MCP logs structured JSON events:

```json
{
  "timestamp": "2024-01-15T10:45:00Z",
  "level": "INFO",
  "event": "metasearch_completed",
  "tenant_id": "tenant-abc",
  "query": "AI trends",
  "results_count": 8,
  "duration_ms": 1250
}
```

### Metrics

Key metrics to monitor:

- Search request rate and latency
- Crawl success/failure rates
- Cache hit rates
- Network error rates
- Active tenant count

## Related Services

- [Knowledge MCP](knowledge-mcp.md) - Vector and graph search
- [Router MCP](router-mcp.md) - Request routing and load balancing
- [Evals MCP](evals-mcp.md) - Content evaluation and scoring

For integration examples, see the [API Gateway Reference](gateway.md).