# StratMaster Production Operations Guide

This guide covers operational procedures for StratMaster production environments, including deployment, monitoring, troubleshooting, and maintenance.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Deployment Procedures](#deployment-procedures)
- [Database Management](#database-management)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Troubleshooting](#troubleshooting)
- [Security Procedures](#security-procedures)
- [Backup and Recovery](#backup-and-recovery)
- [Performance Optimization](#performance-optimization)

## Prerequisites

### Required Tools

```bash
# Kubernetes management
kubectl >= 1.25
helm >= 3.10

# Database management
psql >= 14
pgdump >= 14

# Container management
docker >= 20.10
docker-compose >= 2.0

# Security tools
kubeseal >= 0.18 (for sealed secrets)
sops >= 3.7 (for secret management)
```

### Access Requirements

- Kubernetes cluster admin access
- Database admin credentials
- Container registry push access
- Monitoring system access (Grafana, Prometheus)

## Environment Setup

### 1. Kubernetes Cluster Preparation

```bash
# Create namespace
kubectl create namespace stratmaster-production

# Setup RBAC
kubectl apply -f ops/k8s/rbac/

# Install sealed-secrets controller (if using)
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml
```

### 2. Secret Management

#### Using Kubernetes Secrets (for development)
```bash
# Apply secrets directly (NOT for production)
kubectl apply -f ops/k8s/secrets/production-secrets.yaml
```

#### Using Sealed Secrets (recommended for production)
```bash
# Encrypt secrets
kubeseal < ops/k8s/secrets/production-secrets.yaml > ops/k8s/secrets/sealed-secrets.yaml

# Apply encrypted secrets
kubectl apply -f ops/k8s/secrets/sealed-secrets.yaml
```

#### Using External Secret Management
```bash
# AWS Secrets Manager
kubectl apply -f ops/k8s/external-secrets/aws-secrets.yaml

# HashiCorp Vault
kubectl apply -f ops/k8s/external-secrets/vault-secrets.yaml
```

### 3. Database Setup

```bash
# Run database migrations
export POSTGRES_URL="postgresql://user:pass@host:5432/stratmaster"
./database/migrate.sh

# Verify schema
psql $POSTGRES_URL -c "\dt"
```

## Deployment Procedures

### 1. Standard Deployment

```bash
# Deploy using script
./scripts/deploy.sh deploy-prod \
  --image-tag v1.2.3 \
  --values-file helm/values-production.yaml \
  --wait \
  --timeout 900s

# Verify deployment
kubectl get pods -n stratmaster-production
kubectl get services -n stratmaster-production
```

### 2. Blue-Green Deployment

```bash
# Deploy to green environment
./scripts/deploy.sh deploy-prod \
  --namespace stratmaster-green \
  --image-tag v1.2.3 \
  --wait

# Switch traffic after verification
kubectl patch ingress stratmaster-ingress \
  --patch '{"spec":{"rules":[{"host":"api.stratmaster.com","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"stratmaster-green","port":{"number":80}}}}]}}]}}'

# Clean up blue environment after successful deployment
kubectl delete namespace stratmaster-blue
```

### 3. Rolling Update

```bash
# Update image tags in Helm values
helm upgrade stratmaster-api helm/stratmaster-api \
  --namespace stratmaster-production \
  --values helm/values-production.yaml \
  --set image.tag=v1.2.3 \
  --wait \
  --timeout 600s
```

### 4. Rollback Procedures

```bash
# Rollback using deployment script
./scripts/deploy.sh rollback \
  --namespace stratmaster-production \
  --revision previous

# Or using Helm
helm rollback stratmaster-api -n stratmaster-production

# Emergency rollback (immediate)
kubectl rollout undo deployment/stratmaster-api -n stratmaster-production
```

## Database Management

### 1. Schema Migrations

```bash
# Check current migration status
./database/migrate.sh --dry-run

# Apply new migrations
./database/migrate.sh --verbose

# Rollback migration (manual process)
psql $POSTGRES_URL < database/rollback/rollback_001.sql
```

### 2. Database Backup

```bash
# Full backup
pg_dump $POSTGRES_URL > backups/stratmaster-$(date +%Y%m%d-%H%M%S).sql

# Schema-only backup
pg_dump --schema-only $POSTGRES_URL > backups/schema-$(date +%Y%m%d).sql

# Automated backup using CronJob
kubectl apply -f ops/k8s/cronjobs/database-backup.yaml
```

### 3. Database Monitoring

```bash
# Check connection counts
psql $POSTGRES_URL -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Check database size
psql $POSTGRES_URL -c "SELECT pg_size_pretty(pg_database_size('stratmaster'));"

# Monitor slow queries
psql $POSTGRES_URL -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Monitoring and Alerting

### 1. Health Checks

```bash
# API health check
curl https://api.stratmaster.com/healthz

# Database health check
python scripts/health_check.py --component database

# Comprehensive health check
python scripts/health_check.py --comprehensive
```

### 2. Key Metrics to Monitor

#### Application Metrics
- API response time (p95 < 500ms)
- API error rate (< 1%)
- Active user sessions
- Workflow completion rate
- ML model inference time

#### Infrastructure Metrics
- CPU usage (< 80%)
- Memory usage (< 85%)
- Database connections (< 80% of max)
- Storage usage (< 90%)

#### Business Metrics
- Approval workflow completion time
- Constitutional compliance rate
- User satisfaction scores
- System availability (SLA: 99.5%)

### 3. Alert Configuration

```yaml
# Example Prometheus alert rules
groups:
- name: stratmaster-api
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} requests/second"
  
  - alert: DatabaseConnectionHigh
    expr: pg_stat_database_numbackends > 80
    for: 10m
    annotations:
      summary: "Database connection count high"
      description: "Connection count is {{ $value }}"
```

## Troubleshooting

### 1. Common Issues

#### Pod Startup Issues
```bash
# Check pod status
kubectl get pods -n stratmaster-production

# View pod logs
kubectl logs deployment/stratmaster-api -n stratmaster-production --tail=100

# Describe pod for events
kubectl describe pod <pod-name> -n stratmaster-production

# Check resource usage
kubectl top pods -n stratmaster-production
```

#### Database Connection Issues
```bash
# Test database connection
psql $POSTGRES_URL -c "SELECT 1;"

# Check connection pool status
kubectl logs deployment/stratmaster-api -n stratmaster-production | grep -i "connection"

# Monitor active connections
psql $POSTGRES_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

#### Memory Issues
```bash
# Check memory usage
kubectl top pods -n stratmaster-production

# Check for memory leaks in logs
kubectl logs deployment/stratmaster-api -n stratmaster-production | grep -i "memory\|oom"

# Restart deployment if needed
kubectl rollout restart deployment/stratmaster-api -n stratmaster-production
```

### 2. Performance Issues

#### Slow API Responses
```bash
# Check response times in logs
kubectl logs deployment/stratmaster-api -n stratmaster-production | grep -E "duration|took"

# Query slow database queries
psql $POSTGRES_URL -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Check Redis performance
redis-cli --latency-history -h redis.stratmaster-production.svc.cluster.local
```

#### High CPU Usage
```bash
# Check CPU usage
kubectl top pods -n stratmaster-production

# Profile application (if profiling enabled)
curl https://api.stratmaster.com/debug/pprof/profile > cpu.prof

# Check for expensive queries
psql $POSTGRES_URL -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### 3. Log Analysis

```bash
# Stream logs from all API pods
kubectl logs -f deployment/stratmaster-api -n stratmaster-production --all-containers=true

# Search for specific errors
kubectl logs deployment/stratmaster-api -n stratmaster-production | grep -i error

# Export logs for analysis
kubectl logs deployment/stratmaster-api -n stratmaster-production --since=1h > api-logs.txt
```

## Security Procedures

### 1. Security Scanning

```bash
# Scan container images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image stratmaster-api:latest

# Scan Kubernetes manifests
kubectl apply --dry-run=client -f helm/stratmaster-api/templates/ | trivy k8s -
```

### 2. Certificate Management

```bash
# Check certificate expiration
kubectl get certificates -n stratmaster-production

# Renew certificates (cert-manager)
kubectl annotate certificate stratmaster-tls cert-manager.io/force-renew="true" -n stratmaster-production
```

### 3. Access Control

```bash
# Review RBAC permissions
kubectl auth can-i --list --as=system:serviceaccount:stratmaster-production:stratmaster-api

# Audit recent API access
kubectl logs deployment/stratmaster-api -n stratmaster-production | grep -E "POST|PUT|DELETE" | tail -20
```

## Backup and Recovery

### 1. Database Backup

```bash
# Full backup with compression
pg_dump $POSTGRES_URL | gzip > backups/stratmaster-full-$(date +%Y%m%d).sql.gz

# Incremental backup (using WAL-E or similar)
wal-e backup-push /var/lib/postgresql/data
```

### 2. Configuration Backup

```bash
# Backup Kubernetes resources
kubectl get all,secrets,configmaps -n stratmaster-production -o yaml > backups/k8s-resources-$(date +%Y%m%d).yaml

# Backup Helm values
cp helm/values-production.yaml backups/helm-values-$(date +%Y%m%d).yaml
```

### 3. Recovery Procedures

```bash
# Restore database from backup
gunzip -c backups/stratmaster-full-20241220.sql.gz | psql $POSTGRES_URL

# Restore Kubernetes resources
kubectl apply -f backups/k8s-resources-20241220.yaml

# Verify restoration
python scripts/health_check.py --comprehensive
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM approval_workflows WHERE status = 'pending';

-- Update statistics
ANALYZE;

-- Reindex if needed
REINDEX INDEX idx_approval_workflows_status_tenant;

-- Vacuum to reclaim space
VACUUM ANALYZE approval_workflows;
```

### 2. Application Optimization

```bash
# Enable Redis caching
kubectl patch configmap stratmaster-config -n stratmaster-production -p '{"data":{"CACHE_ENABLED":"true"}}'

# Adjust connection pool sizes
kubectl patch deployment stratmaster-api -n stratmaster-production -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"DB_POOL_SIZE","value":"50"}]}]}}}}'

# Scale deployment based on load
kubectl scale deployment stratmaster-api --replicas=5 -n stratmaster-production
```

### 3. Resource Tuning

```yaml
# Update resource requests/limits
resources:
  requests:
    cpu: "2"
    memory: "4Gi"
  limits:
    cpu: "4"
    memory: "8Gi"
```

## Emergency Procedures

### 1. Emergency Shutdown

```bash
# Scale down all deployments
kubectl scale deployment --all --replicas=0 -n stratmaster-production

# Maintenance page
kubectl apply -f ops/k8s/maintenance-page.yaml
```

### 2. Emergency Recovery

```bash
# Restore from last good backup
./scripts/emergency-restore.sh --backup-date 20241220

# Verify system integrity
python scripts/health_check.py --comprehensive --strict
```

### 3. Incident Response

1. **Assess Impact**: Determine scope and severity
2. **Notify Stakeholders**: Use incident communication channels
3. **Implement Fix**: Apply immediate remediation
4. **Monitor Recovery**: Verify system stability
5. **Post-Mortem**: Document lessons learned

---

## 📞 Support Contacts

- **Platform Team**: platform-team@company.com
- **Database Team**: db-team@company.com
- **Security Team**: security-team@company.com
- **On-Call Engineer**: +1-555-ONCALL (1-555-662-2255)

## 📚 Additional Resources

- [StratMaster Architecture Overview](../docs/architecture.md)
- [API Documentation](../docs/api.md)
- [Security Policies](../SECURITY.md)
- [Monitoring Dashboards](https://grafana.stratmaster.com)
- [Log Analysis](https://logs.stratmaster.com)