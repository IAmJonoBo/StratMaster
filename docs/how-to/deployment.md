# Deployment Guide

This guide covers deploying StratMaster in different environments, from development to production. Choose the deployment method that best fits your infrastructure and requirements.

## Quick Start

### Docker Compose (Recommended for Development)

The fastest way to get StratMaster running with all services:

```bash
# Clone the repository
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster

# Start the full stack
make dev.up

# Verify services are running
make dev.logs
```

**Services Available:**
- Gateway API: http://localhost:8080
- Research MCP: http://localhost:8081
- Knowledge MCP: http://localhost:8082
- Router MCP: http://localhost:8083
- Temporal UI: http://localhost:8088
- Langfuse: http://localhost:3000
- MinIO Console: http://localhost:9001

## Deployment Options

### Local Development

#### Option 1: Docker Compose (Full Stack)

Best for: Complete system testing, integration development

```bash
# Start all services
make dev.up

# Monitor logs
make dev.logs

# Stop when done
make dev.down
```

#### Option 2: Individual Services

Best for: API development, focused testing

```bash
# Bootstrap environment
make bootstrap

# Run Gateway API only
make api.run

# Run Research MCP (in separate terminal)
make research-mcp.run

# Run Expertise MCP (in separate terminal)  
make expertise-mcp.run
```

### Staging Environment

#### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM recommended
- 50GB+ storage
- Network access to required external services

#### Configuration

1. **Create environment file:**

```bash
# .env.staging
STRATMASTER_ENV=staging
DATABASE_URL=postgresql://user:pass@postgres:5432/stratmaster_staging
QDRANT_URL=http://qdrant:6333
KEYCLOAK_URL=http://keycloak:8080
LANGFUSE_URL=http://langfuse:3000
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
ENABLE_DEBUG_ENDPOINTS=0
```

2. **Deploy staging stack:**

```bash
# Use staging configuration
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Verify deployment
python scripts/health_check.py --environment staging
```

3. **Run validation tests:**

```bash
make test.integration
python scripts/validate_phase2.sh
```

### Production Environment

#### Infrastructure Requirements

**Minimum Production Setup:**
- 4 CPU cores, 16GB RAM per API instance
- PostgreSQL 14+ with replication
- Qdrant cluster with 3+ nodes
- OpenSearch cluster (3+ nodes recommended)
- Redis cluster for session management
- Load balancer (NGINX, HAProxy, or cloud LB)

**Recommended Production Setup:**
- Kubernetes cluster with auto-scaling
- Managed database services (RDS, Cloud SQL)
- Managed vector database (Qdrant Cloud)
- Service mesh (Istio/Linkerd) for observability
- External secrets management (HashiCorp Vault, cloud KMS)

#### Kubernetes Deployment

1. **Prepare cluster:**

```bash
# Ensure kubectl is configured
kubectl cluster-info

# Create namespace
kubectl create namespace stratmaster-prod

# Apply configurations
kubectl apply -f ops/k8s/namespace.yaml
kubectl apply -f ops/k8s/network-policies/
```

2. **Deploy with Helm:**

```bash
# Add StratMaster Helm repo
helm repo add stratmaster ./helm

# Install with production values
helm install stratmaster-prod stratmaster/stratmaster-api \
  --namespace stratmaster-prod \
  --values helm/values-production.yaml \
  --set image.tag=v0.2.0
```

3. **Configure ingress:**

```bash
# Apply ingress configuration
kubectl apply -f ops/k8s/ingress/production-ingress.yaml

# Verify ingress
kubectl get ingress -n stratmaster-prod
```

4. **Set up monitoring:**

```bash
# Deploy monitoring stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Apply service monitors
kubectl apply -f ops/k8s/monitoring/
```

#### Cloud Platform Deployments

##### AWS ECS

```bash
# Build and push image
docker build -t stratmaster-api:prod ./packages/api
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ECR_REGISTRY
docker tag stratmaster-api:prod $ECR_REGISTRY/stratmaster-api:prod
docker push $ECR_REGISTRY/stratmaster-api:prod

# Deploy ECS service
aws ecs update-service --cluster stratmaster-prod --service api-service --task-definition stratmaster-api:latest
```

##### Google Cloud Run

```bash
# Build for Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT_ID/stratmaster-api

# Deploy
gcloud run deploy stratmaster-api \
  --image gcr.io/$PROJECT_ID/stratmaster-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$DATABASE_URL,QDRANT_URL=$QDRANT_URL"
```

##### Azure Container Instances

```bash
# Create resource group
az group create --name stratmaster-rg --location eastus

# Deploy container group
az container create \
  --resource-group stratmaster-rg \
  --name stratmaster-api \
  --image stratmaster-api:prod \
  --cpu 2 --memory 8 \
  --ports 8080 \
  --environment-variables DATABASE_URL=$DATABASE_URL QDRANT_URL=$QDRANT_URL
```

## Configuration Management

### Environment Variables

#### Required Configuration

```bash
# Core service configuration
DATABASE_URL=postgresql://user:pass@host:5432/stratmaster
QDRANT_URL=http://qdrant-host:6333
REDIS_URL=redis://redis-host:6379

# Authentication
KEYCLOAK_URL=http://keycloak-host:8080
KEYCLOAK_REALM=stratmaster
KEYCLOAK_CLIENT_ID=stratmaster-api

# Observability
LANGFUSE_URL=http://langfuse-host:3000
OPENTELEMETRY_ENDPOINT=http://jaeger-host:14268

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-32-byte-encryption-key
```

#### Optional Configuration

```bash
# Feature flags
ENABLE_DEBUG_ENDPOINTS=0
ENABLE_EXPERIMENTAL_FEATURES=0
ENABLE_TELEMETRY=1

# Performance tuning
API_WORKERS=4
MAX_REQUEST_SIZE=10MB
REQUEST_TIMEOUT=30s
CONNECTION_POOL_SIZE=20

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/stratmaster.log
```

### Secrets Management

#### Development (Environment Files)

```bash
# .env.local
SECRET_KEY=dev-secret-key
DATABASE_URL=postgresql://localhost:5432/stratmaster_dev
```

#### Production (External Secrets)

**HashiCorp Vault:**
```bash
# Store secrets in Vault
vault kv put secret/stratmaster/prod \
  secret_key="production-secret" \
  database_url="postgresql://prod-host/stratmaster"

# Use vault-agent or init container to retrieve
```

**Kubernetes Secrets:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: stratmaster-secrets
  namespace: stratmaster-prod
type: Opaque
stringData:
  DATABASE_URL: "postgresql://..."
  SECRET_KEY: "..."
```

**Cloud Secrets (AWS Secrets Manager):**
```bash
# Store secret
aws secretsmanager create-secret \
  --name stratmaster/prod/database \
  --secret-string '{"url":"postgresql://..."}'

# Reference in ECS task definition
"secrets": [{
  "name": "DATABASE_URL",
  "valueFrom": "arn:aws:secretsmanager:region:account:secret:stratmaster/prod/database"
}]
```

## Database Setup

### PostgreSQL Configuration

#### Production Database Setup

```sql
-- Create database and user
CREATE DATABASE stratmaster_prod;
CREATE USER stratmaster WITH ENCRYPTED PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE stratmaster_prod TO stratmaster;

-- Configure for performance
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '8GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
SELECT pg_reload_conf();
```

#### Database Migration

```bash
# Run migrations
python scripts/migrate_database.py --environment production

# Verify migration
python scripts/validate_database.py --environment production
```

### Vector Database (Qdrant)

#### Cluster Setup

```yaml
# qdrant-cluster.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: qdrant-config
data:
  config.yaml: |
    cluster:
      enabled: true
      p2p:
        port: 6335
      consensus:
        tick_period_ms: 100
    storage:
      performance:
        max_search_threads: 4
        max_optimization_threads: 2
```

#### Collection Initialization

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://qdrant-cluster:6333")

# Create collections with production settings
client.create_collection(
    collection_name="documents",
    vectors_config=models.VectorParams(
        size=768,
        distance=models.Distance.COSINE
    ),
    hnsw_config=models.HnswConfigDiff(
        m=32,
        ef_construct=256,
        full_scan_threshold=10000
    ),
    optimizers_config=models.OptimizersConfigDiff(
        default_segment_number=4,
        max_segment_size=200000
    )
)
```

## Load Balancing and Scaling

### NGINX Configuration

```nginx
# /etc/nginx/sites-available/stratmaster
upstream stratmaster_api {
    least_conn;
    server api-1:8080 max_fails=3 fail_timeout=30s;
    server api-2:8080 max_fails=3 fail_timeout=30s;
    server api-3:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.stratmaster.com;
    
    # Health check endpoint (bypass load balancing)
    location /healthz {
        proxy_pass http://api-1:8080/healthz;
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }
    
    # API routes
    location / {
        proxy_pass http://stratmaster_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
        
        # Request size limits
        client_max_body_size 50M;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
}
```

### Auto-scaling Configuration

#### Kubernetes HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: stratmaster-api-hpa
  namespace: stratmaster-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: stratmaster-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

## Monitoring and Observability

### Health Checks

```bash
# Automated health monitoring
python scripts/health_monitor.py --interval 30 --alert-webhook $SLACK_WEBHOOK

# Comprehensive health check
make health-check

# Service-specific health checks
curl http://api.stratmaster.com/healthz
curl http://research.stratmaster.com/health
curl http://knowledge.stratmaster.com/health
```

### Metrics Collection

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'stratmaster-api'
    static_configs:
      - targets: ['api:8080']
    metrics_path: '/metrics'
    scrape_interval: 10s
    
  - job_name: 'stratmaster-research-mcp'
    static_configs:
      - targets: ['research-mcp:8081']
    metrics_path: '/metrics'
    
  - job_name: 'stratmaster-knowledge-mcp'
    static_configs:
      - targets: ['knowledge-mcp:8082']
    metrics_path: '/metrics'
```

#### Grafana Dashboards

```bash
# Import pre-built dashboards
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @ops/grafana/stratmaster-overview.json

curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @ops/grafana/api-performance.json
```

## Security Configuration

### TLS/SSL Setup

#### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d api.stratmaster.com -d knowledge.stratmaster.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Custom Certificates

```nginx
server {
    listen 443 ssl http2;
    server_name api.stratmaster.com;
    
    ssl_certificate /etc/ssl/certs/stratmaster.crt;
    ssl_certificate_key /etc/ssl/private/stratmaster.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

### Network Security

#### Firewall Rules

```bash
# Basic firewall setup
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow from 10.0.0.0/8 to any port 8080  # Internal API access
sudo ufw allow from 10.0.0.0/8 to any port 5432  # Database access
```

#### Network Policies (Kubernetes)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: stratmaster-api-netpol
  namespace: stratmaster-prod
spec:
  podSelector:
    matchLabels:
      app: stratmaster-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
```

## Backup and Recovery

### Database Backups

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/stratmaster"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h $DB_HOST -U $DB_USER stratmaster_prod | gzip > "$BACKUP_DIR/stratmaster_$DATE.sql.gz"

# Retain last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp "$BACKUP_DIR/stratmaster_$DATE.sql.gz" s3://stratmaster-backups/database/
```

### Vector Database Backups

```python
# Qdrant backup
import requests
import json

def backup_qdrant_collection(collection_name, backup_path):
    snapshot_url = f"http://qdrant:6333/collections/{collection_name}/snapshots"
    response = requests.post(snapshot_url)
    snapshot_name = response.json()["result"]["name"]
    
    # Download snapshot
    download_url = f"{snapshot_url}/{snapshot_name}"
    with open(f"{backup_path}/{collection_name}_{snapshot_name}.snapshot", "wb") as f:
        response = requests.get(download_url)
        f.write(response.content)
```

### Recovery Procedures

```bash
# Database recovery
gunzip < stratmaster_20240101_120000.sql.gz | psql -h $DB_HOST -U $DB_USER stratmaster_prod

# Qdrant recovery
curl -X POST "http://qdrant:6333/collections/documents/snapshots/upload" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @documents_snapshot.snapshot
```

## Troubleshooting Common Issues

### Service Startup Problems

```bash
# Check service logs
docker-compose logs api
kubectl logs -l app=stratmaster-api -n stratmaster-prod

# Verify configuration
python scripts/config_validator.py --environment production

# Test database connectivity
python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Database connection successful')
conn.close()
"
```

### Performance Issues

```bash
# Check resource usage
docker stats
kubectl top pods -n stratmaster-prod

# Analyze slow queries
tail -f /var/log/postgresql/postgresql.log | grep "duration:"

# Profile API performance
python scripts/performance_benchmark.py --target http://api.stratmaster.com
```

### Scaling Issues

```bash
# Check HPA status
kubectl describe hpa stratmaster-api-hpa -n stratmaster-prod

# Manual scaling
kubectl scale deployment stratmaster-api --replicas=10 -n stratmaster-prod

# Check resource limits
kubectl describe pod -l app=stratmaster-api -n stratmaster-prod
```

## Deployment Checklist

### Pre-deployment

- [ ] Code review and testing completed
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Database migrations prepared
- [ ] Configuration validated
- [ ] Backup strategy verified
- [ ] Rollback plan prepared

### Deployment

- [ ] Maintenance window scheduled
- [ ] Database migrations executed
- [ ] Services deployed with health checks
- [ ] Load balancer updated
- [ ] DNS updated (if needed)
- [ ] SSL certificates verified
- [ ] Monitoring alerts configured

### Post-deployment

- [ ] Health checks passed
- [ ] Performance metrics normal
- [ ] Error rates within acceptable limits
- [ ] User acceptance testing passed
- [ ] Documentation updated
- [ ] Stakeholders notified

## See Also

- [Infrastructure Setup](infrastructure.md) - Detailed infrastructure configuration
- [Operations Guide](operations-guide.md) - Production operations and maintenance  
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Security Guide](../explanation/security.md) - Security architecture and best practices