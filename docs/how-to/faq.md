# Frequently Asked Questions (FAQ)

Common questions about StratMaster setup, configuration, usage, and troubleshooting. This FAQ is organized by category to help you quickly find answers.

## Getting Started

### Q: What are the minimum system requirements for running StratMaster?

**A:** For local development:
- **OS**: Linux, macOS, or Windows with WSL2
- **RAM**: 16GB minimum, 32GB recommended
- **CPU**: 4 cores minimum, 8 cores recommended  
- **Storage**: 50GB available disk space
- **Docker**: Version 20.10 or higher
- **Python**: Version 3.13 or higher

For production deployment:
- **Kubernetes cluster** with at least 3 nodes (4 vCPU, 16GB RAM each)
- **PostgreSQL** (managed service recommended)
- **Redis** for caching
- **Load balancer** with SSL termination

### Q: How long does initial setup take?

**A:** Setup time varies by environment:
- **Local development**: 15-30 minutes (depending on internet speed for Docker images)
- **Staging environment**: 2-4 hours (including infrastructure provisioning)
- **Production environment**: 4-8 hours (including security hardening and testing)

### Q: Can I run StratMaster without Kubernetes?

**A:** Yes, you have several options:
- **Docker Compose**: Suitable for development and small deployments
- **Single server**: All services on one machine (not recommended for production)
- **Cloud managed services**: Use managed databases and container services

```bash
# Docker Compose deployment
make dev.up  # Starts all services locally
```

### Q: What AI providers are supported?

**A:** StratMaster supports multiple AI providers:
- **OpenAI**: GPT-4, GPT-3.5, text-embedding-ada-002
- **Anthropic**: Claude-3 Opus, Sonnet, Haiku
- **Local models**: Via Ollama or vLLM
- **Azure OpenAI**: Enterprise-grade OpenAI models
- **Custom models**: Through the MCP interface

Configuration example:
```yaml
ai_providers:
  openai:
    api_key: "sk-..."
    models: ["gpt-4", "gpt-3.5-turbo"]
  anthropic:
    api_key: "sk-ant-..."
    models: ["claude-3-opus", "claude-3-sonnet"]
```

## Configuration

### Q: How do I configure multi-tenancy?

**A:** Multi-tenancy is built into StratMaster's architecture:

1. **Database isolation**: Each tenant has a separate schema
2. **Authentication**: Configure tenant-aware authentication
3. **API routing**: Tenant ID in headers or path

```yaml
# configs/multi-tenant/config.yaml
multi_tenant:
  enabled: true
  isolation_strategy: "schema_per_tenant"
  tenant_header: "X-Tenant-ID"
  default_tenant: "default"
```

### Q: How do I set up custom domains for each tenant?

**A:** Configure custom domains using ingress routing:

```yaml
# k8s/ingress/tenant-domains.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tenant-domains
spec:
  rules:
  - host: tenant1.stratmaster.ai
    http:
      paths:
      - path: /
        backend:
          service:
            name: stratmaster-api
            port:
              number: 8080
  - host: tenant2.stratmaster.ai  
    http:
      paths:
      - path: /
        backend:
          service:
            name: stratmaster-api
            port:
              number: 8080
```

### Q: What environment variables are required?

**A:** Essential environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=32-character-key

# Services
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
TEMPORAL_HOST=localhost:7233

# Feature flags
ENABLE_DEBUG_MODE=false
ENABLE_EXPERIMENTAL_FEATURES=false
```

See [Configuration Reference](../reference/configuration/) for complete list.

## Usage and Features

### Q: How does the multi-agent debate system work?

**A:** The multi-agent debate system uses specialized AI agents that collaborate:

1. **Research Agent**: Gathers information from multiple sources
2. **Analysis Agent**: Processes information into insights  
3. **Critic Agent**: Challenges assumptions and identifies weaknesses
4. **Evidence Agent**: Validates claims with supporting evidence
5. **Synthesis Agent**: Integrates insights into coherent strategy

The agents debate iteratively until consensus is reached or maximum rounds completed.

See [Multi-Agent Debate](../explanation/multi-agent-debate.md) for detailed explanation.

### Q: What quality assurance mechanisms are in place?

**A:** StratMaster implements multiple quality gates:

- **Evidence Grading**: Using GRADE framework (High/Moderate/Low/Very Low)
- **Factual Accuracy**: Percentage of claims supported by evidence
- **Source Diversity**: Multiple independent sources required
- **Logical Consistency**: Automated detection of contradictions
- **Peer Review**: Multi-agent validation process

Quality metrics are tracked and reported for each analysis.

### Q: How do I customize the analysis framework?

**A:** You can customize analysis through configuration:

```yaml
# configs/analysis/framework.yaml
analysis_framework:
  debate_rounds: 3
  consensus_threshold: 0.8
  evidence_requirements:
    minimum_sources: 3
    credibility_threshold: 0.7
  quality_gates:
    factual_accuracy_min: 0.85
    logical_consistency_min: 0.9
```

### Q: Can I integrate with existing business intelligence tools?

**A:** Yes, StratMaster provides multiple integration options:

- **REST API**: Full programmatic access to all features
- **Webhooks**: Real-time notifications of analysis completion
- **Export formats**: JSON, CSV, PDF reports
- **Database access**: Direct query access to analysis results

```python
# Example API integration
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://api.stratmaster.ai/strategies",
        json={
            "topic": "Market expansion analysis",
            "constraints": ["Budget < $1M", "Timeline: 6 months"]
        },
        headers={"Authorization": "Bearer <token>"}
    )
    analysis = response.json()
```

## Performance and Scaling

### Q: How does StratMaster scale with usage?

**A:** StratMaster is designed for horizontal scaling:

- **API layer**: Stateless services with auto-scaling
- **MCP services**: Independent scaling based on demand
- **Databases**: Read replicas and sharding support
- **Caching**: Multi-level caching (Redis, CDN, application)

Auto-scaling triggers:
- CPU utilization > 70%
- Memory utilization > 80%  
- Response time > 500ms
- Queue depth > 100 items

### Q: What are typical response times for analysis?

**A:** Response times depend on analysis complexity:

- **Simple queries**: 2-5 seconds
- **Standard analysis**: 30-60 seconds  
- **Complex multi-source analysis**: 2-5 minutes
- **Comprehensive reports**: 5-15 minutes

Performance can be improved through:
- Caching frequently requested analyses
- Parallel processing of research tasks
- Optimized vector search indices
- Dedicated resources for premium users

### Q: How much does it cost to run StratMaster?

**A:** Costs vary by deployment size and usage:

**Development environment** (local):
- No cloud costs, just local resources

**Staging environment** (AWS):
- EKS cluster: ~$150/month
- RDS PostgreSQL: ~$100/month  
- Other services: ~$50/month
- **Total**: ~$300/month

**Production environment** (AWS):
- EKS cluster (3 nodes): ~$450/month
- RDS Multi-AZ: ~$300/month
- Vector databases: ~$200/month
- Load balancer, storage, bandwidth: ~$150/month
- AI provider costs: $100-1000/month (usage-based)
- **Total**: ~$1200-2100/month

## Troubleshooting

### Q: The API is returning 500 errors. How do I debug?

**A:** Follow this debugging sequence:

1. **Check API logs**:
```bash
kubectl logs -n stratmaster-production deployment/stratmaster-api --tail=100
```

2. **Verify database connectivity**:
```bash
kubectl exec -n stratmaster-production deployment/stratmaster-api -- \
  python -c "import psycopg2; psycopg2.connect('postgresql://...')"
```

3. **Check resource usage**:
```bash
kubectl top pods -n stratmaster-production
kubectl describe pod <failing-pod> -n stratmaster-production
```

4. **Review recent changes**:
```bash
kubectl rollout history deployment/stratmaster-api -n stratmaster-production
```

### Q: Vector search is returning poor results. How do I improve accuracy?

**A:** To improve vector search accuracy:

1. **Check embedding quality**:
```python
# Test embedding generation
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["test query"])
print(f"Embedding shape: {embeddings.shape}")
```

2. **Optimize search parameters**:
```python
# Adjust search configuration
search_params = {
    "metric": "cosine",  # or "euclidean", "dot"
    "ef_construct": 200,  # Higher = better quality, slower indexing
    "ef": 128,           # Higher = better recall, slower search
    "m": 16              # Higher = better recall, more memory
}
```

3. **Re-index with better parameters**:
```bash
make vector.reindex  # Rebuilds vector indices
```

### Q: The system is running slowly. What should I check?

**A:** Performance troubleshooting checklist:

1. **Database performance**:
```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Check connections
SELECT count(*) FROM pg_stat_activity;
```

2. **Resource utilization**:
```bash
# Check node resources
kubectl top nodes

# Check pod resources  
kubectl top pods --all-namespaces --sort-by=memory
```

3. **Cache hit rates**:
```bash
# Redis cache statistics
redis-cli info stats | grep keyspace
```

4. **Network latency**:
```bash
# Test internal service communication
kubectl exec deployment/stratmaster-api -- \
  curl -w "@curl-format.txt" -s http://postgres:5432
```

### Q: How do I recover from a complete system failure?

**A:** Disaster recovery procedure:

1. **Assess the situation**:
```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes

# Check critical services
kubectl get pods -n stratmaster-production
```

2. **Restore from backups**:
```bash
# Database restore
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier stratmaster-prod-restored \
  --db-snapshot-identifier latest-snapshot

# Application restore
helm install stratmaster-prod ./helm/stratmaster-api \
  --namespace stratmaster-production \
  --values helm/values/production.yaml
```

3. **Verify recovery**:
```bash
# Run smoke tests
make test.smoke.production

# Check critical endpoints
curl -f http://api.stratmaster.ai/healthz
```

See [Disaster Recovery](operations.md#disaster-recovery) for complete procedures.

## Security

### Q: How do I set up SSL certificates?

**A:** StratMaster supports multiple certificate options:

**Let's Encrypt (Recommended)**:
```yaml
# k8s/certificates/letsencrypt.yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: stratmaster-tls
spec:
  secretName: stratmaster-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.stratmaster.ai
  - www.stratmaster.ai
```

**Custom certificates**:
```bash
# Import existing certificates
kubectl create secret tls stratmaster-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n stratmaster-production
```

### Q: How do I enable audit logging?

**A:** Audit logging is enabled by default. Configure detail level:

```yaml
# configs/audit/logging.yaml
audit_logging:
  enabled: true
  level: "detailed"  # minimal, standard, detailed, complete
  destinations:
    - type: "file"
      path: "/var/log/audit/stratmaster.log"
    - type: "database"
      table: "audit_logs"
    - type: "siem"
      endpoint: "https://siem.company.com/events"
```

### Q: What data is encrypted and how?

**A:** StratMaster encrypts data at multiple levels:

- **At Rest**: AES-256-GCM encryption for all stored data
- **In Transit**: TLS 1.3 for all network communications
- **In Processing**: Homomorphic encryption for sensitive computations
- **Backups**: Customer-managed keys for backup encryption

Key management through HashiCorp Vault or cloud KMS.

## Integration and API

### Q: How do I authenticate API requests?

**A:** StratMaster supports multiple authentication methods:

**JWT Bearer Tokens**:
```python
import httpx

headers = {"Authorization": "Bearer <your-jwt-token>"}
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://api.stratmaster.ai/strategies",
        headers=headers
    )
```

**API Keys**:
```python
headers = {"X-API-Key": "<your-api-key>"}
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://api.stratmaster.ai/strategies", 
        headers=headers
    )
```

**OAuth 2.0**:
```python
from authlib.integrations.httpx_client import OAuth2Session

client = OAuth2Session(client_id, client_secret)
token = client.fetch_token(token_url, username=username, password=password)
```

### Q: What are the API rate limits?

**A:** Rate limits vary by authentication level:

- **Unauthenticated**: 100 requests/hour
- **Authenticated**: 1,000 requests/hour  
- **Premium**: 10,000 requests/hour
- **Enterprise**: 50,000 requests/hour

Rate limit headers in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Q: How do I set up webhooks for analysis completion?

**A:** Configure webhooks in your tenant settings:

```python
# Register webhook endpoint
webhook_config = {
    "url": "https://your-app.com/webhooks/stratmaster",
    "events": ["analysis.completed", "analysis.failed"],
    "secret": "your-webhook-secret"
}

response = await client.post("/webhooks", json=webhook_config)
```

Webhook payload example:
```json
{
    "event": "analysis.completed",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "analysis_id": "analysis-123",
        "tenant_id": "tenant-456", 
        "status": "completed",
        "confidence": 0.87,
        "insights_count": 5
    }
}
```

## Monitoring and Observability

### Q: What metrics should I monitor?

**A:** Key metrics to track:

**Application metrics**:
- Request rate and response time
- Error rates by endpoint
- Analysis completion rates
- Queue depths and processing times

**Infrastructure metrics**:
- CPU and memory utilization
- Database performance
- Cache hit rates
- Storage usage

**Business metrics**:
- Active users and sessions
- Analysis quality scores
- Feature usage patterns
- Customer satisfaction scores

### Q: How do I set up alerts?

**A:** Configure alerts in Prometheus/AlertManager:

```yaml
# alerts/stratmaster.yml
groups:
- name: stratmaster
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response latency detected"
```

### Q: How do I access logs and traces?

**A:** Logs and traces are available through multiple interfaces:

**Kubernetes logs**:
```bash
kubectl logs -n stratmaster-production deployment/stratmaster-api -f
```

**Centralized logging**:
- Grafana Loki: `http://grafana.stratmaster.ai`
- ElasticSearch/Kibana: `http://kibana.stratmaster.ai`

**Distributed tracing**:
- Jaeger: `http://jaeger.stratmaster.ai`
- Zipkin: `http://zipkin.stratmaster.ai`

## Development

### Q: How do I contribute to StratMaster?

**A:** Follow the contribution process:

1. **Fork the repository** and clone locally
2. **Set up development environment**:
```bash
make bootstrap
make dev.up
```

3. **Create feature branch**:
```bash
git checkout -b feature/my-improvement
```

4. **Make changes and test**:
```bash
make test
make lint
```

5. **Submit pull request** with clear description

See [Contributing Guide](../../CONTRIBUTING.md) for detailed guidelines.

### Q: How do I run tests locally?

**A:** StratMaster has multiple test suites:

```bash
# Unit tests
make test.unit

# Integration tests  
make test.integration

# End-to-end tests
make test.e2e

# All tests
make test
```

Test with different configurations:
```bash
# Test with PostgreSQL
DATABASE_URL=postgresql://... make test

# Test with different AI providers
OPENAI_API_KEY=sk-... make test.ai
```

### Q: How do I debug MCP server communication?

**A:** Debug MCP servers using built-in tools:

```bash
# Enable debug logging
MCP_DEBUG=true python -m research_mcp

# Test MCP communication
echo '{"method": "ping", "params": {}}' | python -m mcp_client

# Monitor MCP traffic
tcpdump -i lo0 -A 'port 8080 and host localhost'
```

---

## Still Need Help?

If your question isn't answered here:

1. **Check the documentation**: [Full Documentation](../index.md)
2. **Search GitHub Issues**: [StratMaster Issues](https://github.com/IAmJonoBo/StratMaster/issues)
3. **Join discussions**: [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)
4. **Contact support**: [Support Guidelines](../../SECURITY.md)

**Found an error in this FAQ?** Please [submit an issue](https://github.com/IAmJonoBo/StratMaster/issues/new) or contribute an improvement!