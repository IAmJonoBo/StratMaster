# StratMaster Troubleshooting Guide

This guide covers common issues, diagnostic procedures, and solutions for StratMaster deployment and operation. Use this guide to quickly identify and resolve problems across different environments.

## Quick Diagnostics

### Health Check Commands

Run these commands first to get an overview of system health:

```bash
# Local Development
make health-check
curl http://localhost:8080/healthz
curl http://localhost:8081/info

# Kubernetes
kubectl get pods,svc,ingress -n stratmaster-prod
kubectl top pods -n stratmaster-prod
helm status stratmaster

# Docker Compose
docker-compose ps
docker stats --no-stream
```

### System Status Overview

```bash
#!/bin/bash
# Quick system health check script

echo "=== StratMaster Health Check ==="

# Check API Gateway
if curl -s -f http://localhost:8080/healthz > /dev/null; then
    echo "✅ API Gateway: Healthy"
else
    echo "❌ API Gateway: Unhealthy"
fi

# Check MCP Servers
for port in 8081 8082 8083 8084 8085; do
    service_name=$(curl -s http://localhost:$port/info 2>/dev/null | jq -r '.name // "unknown"')
    if [ "$service_name" != "unknown" ]; then
        echo "✅ MCP Server ($service_name): Healthy"
    else
        echo "❌ MCP Server (port $port): Unhealthy"
    fi
done

# Check Storage Services
services=("postgres:5432" "qdrant:6333" "opensearch:9200" "minio:9000")
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $name: Connected"
    else
        echo "❌ $name: Connection failed"
    fi
done
```

## Development Environment Issues

### Bootstrap and Setup Problems

#### Issue: `make bootstrap` fails with pip timeouts

```bash
# Error message
ERROR: Could not find a version that satisfies the requirement...
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None))
```

**Cause**: Network restrictions or corporate firewall blocking PyPI

**Solution**:

```bash
# Option 1: Use Docker-based testing instead
make test-docker

# Option 2: Configure pip with proxy (if available)
pip config set global.proxy http://your-proxy:8080
make bootstrap

# Option 3: Use alternative index
pip install --index-url https://pypi.python.org/simple/ --trusted-host pypi.python.org -e packages/api
```

#### Issue: "ModuleNotFoundError: No module named 'stratmaster_api'"

**Cause**: Package not installed in editable mode

**Solution**:

```bash
# Reinstall package
make clean
make bootstrap

# Verify installation
.venv/bin/python -c "import stratmaster_api; print('Import successful')"
```

#### Issue: "UnicodeDecodeError in importlib.metadata"

**Cause**: Conda/system Python conflicts

**Solution**:

```bash
# Use pyenv for clean Python
pyenv install 3.13.1
pyenv local 3.13.1

# Clean restart
rm -rf .venv
make bootstrap

# Alternative: Use PYTHONNOUSERSITE
PYTHONNOUSERSITE=1 make bootstrap
```

### Testing Issues

#### Issue: API tests failing with "connection refused"

```bash
# Error
requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=8080): Max retries exceeded
```

**Cause**: API server not running or wrong port

**Solution**:

```bash
# Check if server is running
netstat -tlnp | grep :8080

# Start API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --host 127.0.0.1 --port 8080 &

# Run tests against running server
pytest packages/api/tests/
```

#### Issue: Tests pass locally but fail in CI

**Cause**: Environment differences or resource constraints

**Solution**:

```bash
# Check CI environment
cat .github/workflows/ci.yml

# Run tests with same conditions as CI
PYTHONNOUSERSITE=1 python -m pytest packages/api/tests/ --tb=short

# Check for race conditions
pytest packages/api/tests/ --count=10
```

### Docker Compose Issues

#### Issue: "docker-compose up" fails with port conflicts

```bash
# Error
ERROR for stratmaster-api: Cannot start service api: Ports are not available: exposing port 8080: listen tcp 0.0.0.0:8080: bind: address already in use
```

**Solution**:

```bash
# Find process using port
lsof -ti:8080
kill $(lsof -ti:8080)

# Or use different ports
docker-compose -f docker-compose.override.yml up
```

#### Issue: Services unable to connect to each other

**Cause**: Docker network issues or service startup order

**Solution**:

```bash
# Check Docker networks
docker network ls
docker network inspect stratmaster_default

# Check service dependencies
docker-compose logs postgres
docker-compose up -d postgres
docker-compose up -d --scale api=0  # Start dependencies first
docker-compose up -d api
```

#### Issue: "No space left on device" during container builds

**Solution**:

```bash
# Clean Docker system
docker system prune -a
docker volume prune

# Check disk usage
df -h
du -sh ~/.docker/

# Remove unused images
docker image prune -a
```

## Production Environment Issues

### Kubernetes Deployment Problems

#### Issue: Pods stuck in "Pending" state

```bash
# Check pod status
kubectl describe pod <pod-name> -n stratmaster-prod
```

**Common Causes and Solutions**:

1. **Resource constraints**:

```bash
# Check node resources
kubectl top nodes
kubectl describe nodes

# Reduce resource requests temporarily
kubectl patch deployment stratmaster-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"requests":{"memory":"512Mi","cpu":"250m"}}}]}}}}'
```

1. **Image pull failures**:

```bash
# Check image pull secrets
kubectl get secrets -n stratmaster-prod
kubectl describe secret regcred

# Test image pull manually
docker pull your-registry.com/stratmaster-api:latest
```

1. **Persistent volume issues**:

```bash
# Check PV/PVC status
kubectl get pv,pvc -n stratmaster-prod
kubectl describe pvc postgres-pvc

# Check storage class
kubectl get storageclass
```

#### Issue: Services returning 503 errors

**Diagnostic Steps**:

```bash
# Check service endpoints
kubectl get endpoints -n stratmaster-prod

# Check pod readiness
kubectl get pods -n stratmaster-prod -o wide

# Test service connectivity
kubectl exec -it test-pod -- curl http://stratmaster-api:8080/healthz
```

**Solutions**:

```bash
# Check readiness probe configuration
kubectl describe deployment stratmaster-api

# Temporary fix: Remove readiness probe
kubectl patch deployment stratmaster-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","readinessProbe":null}]}}}}'

# Check logs for startup issues
kubectl logs deployment/stratmaster-api --tail=100
```

### Database Issues

#### Issue: PostgreSQL connection failures

```bash
# Error in logs
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Diagnostic Steps**:

```bash
# Check PostgreSQL pod status
kubectl get pods -l app=postgres -n stratmaster-prod

# Check PostgreSQL logs
kubectl logs -l app=postgres -n stratmaster-prod --tail=100

# Test connection from application pod
kubectl exec -it deployment/stratmaster-api -- psql $DATABASE_URL -c "SELECT version();"
```

**Solutions**:

1. **PostgreSQL not ready**:

```bash
# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Check if database is initialized
kubectl exec -it postgres-0 -- psql -U stratmaster -l
```

1. **Connection string issues**:

```bash
# Verify connection string
kubectl get secret postgres-credentials -o yaml | base64 --decode

# Test with correct connection string
DATABASE_URL="postgresql://user:pass@postgres:5432/stratmaster"
```

1. **Network policy blocking connections**:

```bash
# Check network policies
kubectl get networkpolicies -n stratmaster-prod

# Temporarily disable network policies
kubectl delete networkpolicy --all -n stratmaster-prod
```

#### Issue: Database queries are slow

**Diagnostic Steps**:

```bash
# Check active connections
kubectl exec -it postgres-0 -- psql -U stratmaster -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Check slow queries
kubectl exec -it postgres-0 -- psql -U stratmaster -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check database size
kubectl exec -it postgres-0 -- psql -U stratmaster -c "SELECT pg_size_pretty(pg_database_size('stratmaster'));"
```

**Solutions**:

```bash
# Increase connection pool size
kubectl set env deployment/stratmaster-api DATABASE_POOL_SIZE=20

# Add database indexes
kubectl exec -it postgres-0 -- psql -U stratmaster -c "CREATE INDEX idx_research_sessions_tenant_id ON research_sessions(tenant_id);"

# Analyze and vacuum tables
kubectl exec -it postgres-0 -- psql -U stratmaster -c "ANALYZE; VACUUM;"
```

### Vector Database Issues

#### Issue: Qdrant search returns no results

**Diagnostic Steps**:

```bash
# Check Qdrant cluster status
curl http://localhost:6333/cluster

# Check collection info
curl http://localhost:6333/collections/tenant_demo_research

# Test search directly
curl -X POST http://localhost:6333/collections/tenant_demo_research/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, 0.3], "limit": 5}'
```

**Solutions**:

1. **Collection not created**:

```bash
# Create collection
curl -X PUT http://localhost:6333/collections/tenant_demo_research \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 1024, "distance": "Cosine"}}'
```

1. **No data indexed**:

```bash
# Check point count
curl http://localhost:6333/collections/tenant_demo_research | jq '.result.points_count'

# Index sample data
python scripts/seed_demo_data.py
```

1. **Wrong vector dimensions**:

```bash
# Check vector config
curl http://localhost:6333/collections/tenant_demo_research | jq '.result.config.params.vectors'

# Recreate collection with correct dimensions
curl -X DELETE http://localhost:6333/collections/tenant_demo_research
curl -X PUT http://localhost:6333/collections/tenant_demo_research \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 768, "distance": "Cosine"}}'  # Correct size
```

### Authentication Issues

#### Issue: "401 Unauthorized" errors from API

**Diagnostic Steps**:

```bash
# Check Keycloak status
curl http://localhost:8089/auth/realms/stratmaster/.well-known/openid_configuration

# Test token generation
curl -X POST http://localhost:8089/auth/realms/stratmaster/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=stratmaster-api" \
  -d "client_secret=your-secret"

# Verify token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/healthz
```

**Solutions**:

1. **Keycloak not accessible**:

```bash
# Check Keycloak logs
kubectl logs deployment/keycloak -n stratmaster-prod

# Port forward to debug
kubectl port-forward svc/keycloak 8089:8080 -n stratmaster-prod
```

1. **Client configuration issues**:

```bash
# Check client configuration in Keycloak admin console
# http://localhost:8089/auth/admin/

# Update client secret
kubectl create secret generic keycloak-client-secret \
  --from-literal=client-secret=new-secret \
  --dry-run=client -o yaml | kubectl apply -f -
```

1. **Token expiration**:

```bash
# Check token expiration settings
# Increase token lifespan in Keycloak realm settings

# Implement token refresh in application
# See authentication code examples
```

## Performance Issues

### High Memory Usage

#### Issue: Pods getting OOMKilled

```bash
# Check pod events
kubectl describe pod <pod-name> -n stratmaster-prod

# Check memory usage
kubectl top pods -n stratmaster-prod --sort-by=memory
```

**Solutions**:

```bash
# Increase memory limits
kubectl patch deployment stratmaster-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"4Gi"}}}]}}}}'

# Enable memory profiling
kubectl set env deployment/stratmaster-api PYTHONMALLOC=debug

# Check for memory leaks
kubectl exec -it <pod-name> -- python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f}MB')
"
```

### High CPU Usage

#### Issue: API responses are slow

**Diagnostic Steps**:

```bash
# Check CPU usage
kubectl top pods -n stratmaster-prod --sort-by=cpu

# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/healthz

# Profile API endpoints
pip install py-spy
py-spy record -o profile.svg -d 30 -p $(pgrep -f uvicorn)
```

**Solutions**:

```bash
# Scale up replicas
kubectl scale deployment stratmaster-api --replicas=5

# Increase CPU limits
kubectl patch deployment stratmaster-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"cpu":"2"}}}]}}}}'

# Enable autoscaling
kubectl autoscale deployment stratmaster-api --min=3 --max=10 --cpu-percent=70
```

### Storage Issues

#### Issue: Disk space running low

```bash
# Check disk usage in pods
kubectl exec -it <pod-name> -- df -h

# Check persistent volume usage
kubectl exec -it postgres-0 -- du -sh /var/lib/postgresql/data
```

**Solutions**:

```bash
# Clean up old data
kubectl exec -it postgres-0 -- psql -U stratmaster -c "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '30 days';"

# Expand persistent volume
kubectl patch pvc postgres-pvc -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# Enable log rotation
kubectl set env deployment/stratmaster-api LOG_ROTATION=true LOG_MAX_SIZE=100MB
```

## Network and Connectivity Issues

### Service Discovery Problems

#### Issue: Services can't find each other

**Diagnostic Steps**:

```bash
# Check DNS resolution
kubectl exec -it <pod-name> -- nslookup stratmaster-api
kubectl exec -it <pod-name> -- dig stratmaster-api.stratmaster-prod.svc.cluster.local

# Check service endpoints
kubectl get endpoints -n stratmaster-prod
```

**Solutions**:

```bash
# Verify service selector matches pod labels
kubectl get svc stratmaster-api -o yaml
kubectl get pods --selector=app=stratmaster-api

# Check CoreDNS
kubectl logs -n kube-system deployment/coredns

# Test connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
/ # wget -qO- http://stratmaster-api:8080/healthz
```

### Ingress Issues

#### Issue: External access not working

```bash
# Check ingress status
kubectl get ingress -n stratmaster-prod
kubectl describe ingress stratmaster-ingress
```

**Solutions**:

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Verify TLS certificates
kubectl get certificates -n stratmaster-prod
kubectl describe certificate stratmaster-tls

# Test without TLS
curl -H "Host: stratmaster.company.com" http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
```

## Monitoring and Observability Issues

### Missing Metrics

#### Issue: Prometheus not scraping metrics

**Diagnostic Steps**:

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check service monitor
kubectl get servicemonitor -n monitoring

# Test metrics endpoint
curl http://stratmaster-api:8080/metrics
```

**Solutions**:

```bash
# Add metrics annotations to service
kubectl annotate service stratmaster-api prometheus.io/scrape=true
kubectl annotate service stratmaster-api prometheus.io/port=8080
kubectl annotate service stratmaster-api prometheus.io/path=/metrics

# Check Prometheus configuration
kubectl get prometheus -o yaml -n monitoring
```

### Log Collection Issues

#### Issue: Logs not appearing in central logging

**Diagnostic Steps**:

```bash
# Check log collector pods
kubectl get pods -n logging

# Check log format
kubectl logs deployment/stratmaster-api --tail=10

# Test log shipping
kubectl logs -n logging daemonset/fluent-bit
```

**Solutions**:

```bash
# Ensure JSON logging format
kubectl set env deployment/stratmaster-api LOG_FORMAT=json

# Check log collector configuration
kubectl get configmap fluent-bit-config -o yaml

# Restart log collector
kubectl rollout restart daemonset/fluent-bit -n logging
```

## Emergency Procedures

### System Recovery

#### Complete System Failure

```bash
# 1. Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces

# 2. Restore from backup
helm rollback stratmaster 1  # Previous working version

# 3. Restore database
kubectl create job postgres-restore --from=cronjob/postgres-backup
kubectl wait --for=condition=complete job/postgres-restore --timeout=600s

# 4. Verify system health
make health-check
```

#### Data Corruption

```bash
# 1. Stop all applications
kubectl scale deployment --all --replicas=0 -n stratmaster-prod

# 2. Create database snapshot
kubectl exec postgres-0 -- pg_dump -U stratmaster stratmaster > emergency-backup.sql

# 3. Restore from clean backup
kubectl exec -i postgres-0 -- psql -U stratmaster stratmaster < last-good-backup.sql

# 4. Restart applications
kubectl scale deployment --all --replicas=1 -n stratmaster-prod
```

### Performance Emergency

#### High Load Situation

```bash
# 1. Immediate scaling
kubectl scale deployment stratmaster-api --replicas=10
kubectl scale deployment research-mcp --replicas=5

# 2. Enable rate limiting
kubectl set env deployment/stratmaster-api RATE_LIMIT_ENABLED=true

# 3. Monitor resources
kubectl top nodes
kubectl top pods -n stratmaster-prod

# 4. Check for DDoS
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller | grep -E "rate limit|429"
```

## Common Error Messages

### API Errors

| Error                       | Cause                   | Solution                                                              |
| --------------------------- | ----------------------- | --------------------------------------------------------------------- |
| `500 Internal Server Error` | Application error       | Check logs: `kubectl logs deployment/stratmaster-api`                 |
| `502 Bad Gateway`           | Service unavailable     | Check service health: `kubectl get pods`                              |
| `503 Service Unavailable`   | Readiness probe failing | Check probe config: `kubectl describe deployment`                     |
| `Connection refused`        | Service not running     | Restart service: `kubectl rollout restart deployment/stratmaster-api` |

### Database Errors

| Error                            | Cause                    | Solution                                                                |
| -------------------------------- | ------------------------ | ----------------------------------------------------------------------- |
| `psycopg2.OperationalError`      | Connection failed        | Check database pod: `kubectl get pods -l app=postgres`                  |
| `FATAL: database does not exist` | Database not initialized | Run init scripts: `kubectl exec postgres-0 -- psql -f /init/schema.sql` |
| `connection limit exceeded`      | Too many connections     | Increase `max_connections` in PostgreSQL config                         |
| `disk full`                      | Storage exhausted        | Expand PVC or clean old data                                            |

### Authentication Errors

| Error              | Cause                         | Solution                                       |
| ------------------ | ----------------------------- | ---------------------------------------------- |
| `401 Unauthorized` | Invalid/expired token         | Check Keycloak connectivity and token validity |
| `403 Forbidden`    | Insufficient permissions      | Check user roles and permissions               |
| `JWT decode error` | Token validation failed       | Verify JWT signing key configuration           |
| `Client not found` | Keycloak client misconfigured | Check client configuration in Keycloak admin   |

## Getting Help

When troubleshooting issues:

1. **Gather Information**:
   - Error messages and stack traces
   - System resource usage
   - Recent changes or deployments
   - Log files and metrics

2. **Check Documentation**:
   - [Architecture Overview](architecture.md)
   - [Deployment Guide](deployment.md)
   - [Infrastructure Guide](infrastructure.md)
   - [Security Guide](security.md)

3. **Use Diagnostic Tools**:
   - `kubectl describe` for resource details
   - `kubectl logs` for application logs
   - `kubectl top` for resource usage
   - `curl` for connectivity testing

4. **Create Support Request**:
   - Include diagnostic output
   - Provide reproduction steps
   - Specify environment (dev/staging/prod)
   - Include timeline of when issue started

Remember: When in doubt, check the logs first - they usually contain the key information needed to diagnose and resolve issues.

## Git Corruption: AppleDouble Files (macOS)

### Issue: `error: non-monotonic index .git/objects/pack/._pack-*.idx` or fatal pack/index errors

**Cause**: macOS Finder, Spotlight, or iCloud/Dropbox creates AppleDouble (`._*`) files inside `.git`, corrupting pack indices and breaking git gc/fsck.

**Solution**:

1. Run the cleanup script to purge AppleDouble artifacts:

   ```bash
   bash scripts/cleanup_appledouble.sh
   ```

2. Optionally, run dot_clean on the pack directory:

   ```bash
   dot_clean -m .git/objects/pack
   ```

3. Re-run:

   ```bash
   git fsck --strict
   git gc --prune=now
   ```

4. If errors persist, repeat steps 1–3 and avoid browsing `.git` in Finder.

**Prevention**:

- A `.metadata_never_index` file is now present at repo root to discourage Spotlight/Finder from indexing and creating AppleDouble files.
- Keep the repo out of iCloud/Dropbox/OneDrive synced folders.
- Optionally add the repo path to System Settings > Spotlight > Privacy.

**References**:

- See `scripts/cleanup_appledouble.sh` for safe cleanup.
- For more info, see: <https://github.com/git/git/blob/master/Documentation/RelNotes/2.42.0.txt#L70>
