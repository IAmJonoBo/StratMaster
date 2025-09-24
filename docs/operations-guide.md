# StratMaster Operations Guide

This guide provides comprehensive operational instructions for deploying, managing, and maintaining StratMaster in production environments.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Kubernetes cluster (for production)
- Helm 3.x
- Python 3.13+
- Node.js 18+ (for UI development)

### Quick Start
```bash
# Clone and setup
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster
make setup.full

# Start development environment
make dev.up

# Verify health
curl http://localhost:8080/healthz
```

## 🏗️ Architecture Overview

StratMaster consists of multiple microservices:

### Core Services
- **API Gateway**: FastAPI application (`packages/api`)
- **Research MCP**: Research and analysis service
- **Knowledge MCP**: Knowledge graph management
- **Router MCP**: Model routing and selection
- **Evals MCP**: Evaluation and benchmarking
- **Compression MCP**: Data compression and optimization

### Infrastructure Components
- **PostgreSQL**: Primary database
- **Redis**: Caching and real-time collaboration
- **Qdrant**: Vector database for embeddings
- **OpenSearch**: Search and analytics
- **NebulaGraph**: Knowledge graph storage
- **MinIO**: Object storage
- **Temporal**: Workflow orchestration
- **Keycloak**: Authentication and authorization

## 🛠️ Deployment

### Development Environment
```bash
# Full stack with all services
make dev.up

# Monitor logs
make dev.logs

# Clean shutdown
make dev.down
```

### Production Deployment with Kubernetes

#### 1. Prepare Configuration
```bash
# Copy production template
cp configs/production-config-template.yaml configs/production-config.yaml

# Edit configuration for your environment
vim configs/production-config.yaml
```

#### 2. Deploy with Helm
```bash
# Install API service
helm install stratmaster-api helm/stratmaster-api \
  --namespace stratmaster \
  --create-namespace \
  --values configs/production-values.yaml

# Install MCP services
helm install research-mcp helm/research-mcp \
  --namespace stratmaster \
  --values configs/production-values.yaml
```

#### 3. Verify Deployment
```bash
# Check pod status
kubectl get pods -n stratmaster

# Check service health
kubectl port-forward svc/stratmaster-api 8080:8080
curl http://localhost:8080/healthz
```

### Environment Configuration

#### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/stratmaster
REDIS_URL=redis://host:6379

# Authentication
KEYCLOAK_URL=https://auth.example.com
KEYCLOAK_REALM=stratmaster
KEYCLOAK_CLIENT_ID=stratmaster-api

# Storage
MINIO_ENDPOINT=https://storage.example.com
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key

# Feature Flags
ENABLE_COLLAB_LIVE=true
ENABLE_MODEL_RECOMMENDER_V2=true
INTEGRATIONS_AVAILABLE=true
```

#### Optional Configuration
```bash
# Performance
ENABLE_RESPONSE_CACHE_V2=true
ENABLE_EDGE_CACHE_HINTS=true
ENABLE_RETRIEVAL_BENCHMARKS=true

# Analytics
ENABLE_PREDICTIVE_ANALYTICS=false
ENABLE_EVENT_STREAMING=false
```

## 📊 Monitoring and Observability

### Health Checks
```bash
# API health
curl http://localhost:8080/healthz

# Service-specific health checks
curl http://localhost:8080/health/database
curl http://localhost:8080/health/redis
curl http://localhost:8080/health/services
```

### Metrics and Monitoring

#### Prometheus Metrics
- Gateway latency (p50, p95, p99)
- Request success/failure rates
- Database connection pool usage
- Cache hit/miss rates
- Model routing decisions

#### Key Performance Indicators
- **Response Time**: API p95 < 500ms
- **Availability**: >99.9% uptime
- **Error Rate**: <0.1% 4xx/5xx responses
- **Collaboration Latency**: <150ms for real-time features

### Logging
Structured JSON logging with correlation IDs:
```bash
# View API logs
kubectl logs -f deployment/stratmaster-api -n stratmaster

# Search logs with correlation ID
kubectl logs -f deployment/stratmaster-api -n stratmaster | grep "correlation_id=abc123"
```

## 🔧 Maintenance

### Database Management

#### Migrations
```bash
# Run database migrations
python scripts/migrate.py upgrade

# Check migration status
python scripts/migrate.py status

# Rollback migration (if needed)
python scripts/migrate.py downgrade
```

#### Backups
```bash
# Create database backup
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup-20241201.sql
```

### Asset Management
```bash
# Download required assets
make assets.required

# Verify asset integrity
make assets.verify

# Pull all assets (including optional)
make assets.pull
```

### Dependency Updates
```bash
# Check for updates
make deps.check

# Safe patch updates
make deps.upgrade.safe

# Review and apply minor updates
make deps.upgrade
```

## 🔍 Troubleshooting

### Common Issues

#### Service Won't Start
1. Check logs: `kubectl logs deployment/stratmaster-api -n stratmaster`
2. Verify configuration: `kubectl describe pod -n stratmaster`
3. Check dependencies: Database, Redis, external services

#### High Response Times
1. Check database queries: Enable query logging
2. Verify cache hit rates: Monitor Redis metrics
3. Review external API latency: Check integration timeouts

#### Memory Issues
1. Monitor pod resource usage: `kubectl top pods -n stratmaster`
2. Check for memory leaks: Application metrics
3. Adjust resource limits: Update Helm values

#### Authentication Problems
1. Verify Keycloak configuration
2. Check token expiration and refresh logic
3. Validate OIDC endpoints and certificates

### Performance Tuning

#### Database Optimization
```sql
-- Check slow queries
SELECT query, mean_time, rows, 100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Optimize indexes
ANALYZE;
REINDEX DATABASE stratmaster;
```

#### Cache Optimization
```bash
# Monitor Redis performance
redis-cli --latency-history

# Check memory usage
redis-cli info memory

# Optimize cache TTLs based on usage patterns
```

### Emergency Procedures

#### Service Rollback
```bash
# Rollback Helm release
helm rollback stratmaster-api -n stratmaster

# Emergency feature flag disable
kubectl set env deployment/stratmaster-api ENABLE_FEATURE_FLAG=false -n stratmaster
```

#### Database Recovery
```bash
# Point-in-time recovery (if configured)
# Follow your database provider's recovery procedures

# Manual data recovery from backups
psql $DATABASE_URL < latest-backup.sql
```

## 🔐 Security

### Access Control
- All APIs require authentication via Keycloak
- Role-based access control (RBAC) implemented
- Audit logging for all administrative actions

### Data Protection
- PII detection and handling implemented
- Data encryption at rest and in transit
- Regular security scans with automated remediation

### Compliance
- GDPR compliance for data handling
- SOC 2 Type II controls implemented
- Regular security audits and penetration testing

## 📚 Additional Resources

### Documentation
- [API Reference](docs/reference/api/)
- [Architecture Decisions](docs/architecture/adr/)
- [Development Guide](DEVELOPER_GUIDE.md)
- [Contributing Guidelines](CONTRIBUTING.md)

### Support
- GitHub Issues: Bug reports and feature requests
- Documentation: Complete API and deployment guides
- Monitoring Dashboards: Real-time system health

---

*Operations Guide - Updated December 2024*
*Version: Production Ready - Comprehensive Operational Coverage*