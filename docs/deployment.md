# StratMaster Deployment Guide

This guide covers deploying StratMaster in different environments: local development, staging, and production. Each environment has specific configurations, security considerations, and operational procedures.

## Deployment Overview

StratMaster supports multiple deployment strategies:

- **Local Development**: Docker Compose for rapid iteration
- **Staging**: Kubernetes with reduced resources for testing
- **Production**: Kubernetes with HA, monitoring, and security hardening

## Local Development Deployment

### Quick Start

```bash
# Clone and setup
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster
make bootstrap

# Start full stack
make dev.up

# Verify deployment
make health-check
```

### Service Access

| Service | URL | Credentials |
|---------|-----|-------------|
| API Gateway | http://localhost:8080 | - |
| Research MCP | http://localhost:8081 | - |
| Knowledge MCP | http://localhost:8082 | - |
| Router MCP | http://localhost:8083 | - |
| Temporal UI | http://localhost:8088 | - |
| Langfuse | http://localhost:3000 | - |
| MinIO Console | http://localhost:9001 | stratmaster/stratmaster123 |
| Keycloak | http://localhost:8089 | admin/admin |

### Docker Compose Configuration

The `docker-compose.yml` provides a complete development environment:

```yaml
version: '3.8'

services:
  # Application Services
  api:
    build: packages/api
    ports: ["8080:8080"]
    environment:
      - DATABASE_URL=postgresql://stratmaster:stratmaster@postgres:5432/stratmaster
      - QDRANT_URL=http://qdrant:6333
      - OPENSEARCH_URL=http://opensearch:9200
      - STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_started
    volumes:
      - ./configs:/app/configs
    restart: unless-stopped

  # Storage Services  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: stratmaster
      POSTGRES_USER: stratmaster
      POSTGRES_PASSWORD: stratmaster
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=en_US.UTF-8 --lc-ctype=en_US.UTF-8"
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U stratmaster"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  qdrant_data:
  opensearch_data:
  # ... additional volumes
```

### Environment Variables

Create `.env.local` for development overrides:

```bash
# Development Configuration
STRATMASTER_ENVIRONMENT=development
STRATMASTER_LOG_LEVEL=DEBUG
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1

# Database
DATABASE_URL=postgresql://stratmaster:stratmaster@localhost:5432/stratmaster

# External APIs (optional for development)
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=your-key-here

# Observability
LANGFUSE_PUBLIC_KEY=pk_dev_key
LANGFUSE_SECRET_KEY=sk_dev_key
```

### Development Workflows

```bash
# Start specific services only
docker-compose up -d postgres qdrant opensearch

# Rebuild and restart service
docker-compose up -d --build api

# View logs
docker-compose logs -f api research-mcp

# Execute commands in containers
docker-compose exec postgres psql -U stratmaster

# Clean restart
docker-compose down -v && docker-compose up -d
```

## Staging Deployment

### Kubernetes Setup

Staging uses a minimal Kubernetes setup for integration testing:

```bash
# Create namespace
kubectl create namespace stratmaster-staging

# Deploy with staging values
helm install stratmaster-staging helm/stratmaster-api \
  --namespace stratmaster-staging \
  --values helm/values-staging.yaml
```

### Staging Values (`helm/values-staging.yaml`)

```yaml
# Reduced resource requirements for staging
resources:
  api:
    requests:
      cpu: "0.5"
      memory: "1Gi"
    limits:
      cpu: "1"
      memory: "2Gi"

  postgres:
    requests:
      cpu: "0.5"
      memory: "1Gi"
    limits:
      cpu: "1"
      memory: "2Gi"

# Single replica for most services
replicaCount: 1

# Staging-specific configuration
config:
  environment: staging
  logLevel: INFO
  enableDebugEndpoints: false

# External services
external:
  database:
    host: postgres-staging.internal
    port: 5432
    database: stratmaster_staging
    
  storage:
    provider: minio
    endpoint: minio-staging.internal
    bucket: stratmaster-staging

# Security
security:
  tls:
    enabled: true
    secretName: stratmaster-staging-tls
  networkPolicies:
    enabled: true
    
# Monitoring
monitoring:
  enabled: true
  namespace: monitoring
  
# Ingress
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: stratmaster-staging.company.com
      paths:
        - path: /
          pathType: Prefix
```

### CI/CD Pipeline

GitHub Actions for automated staging deployment:

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
          
      - name: Install dependencies
        run: make bootstrap
        
      - name: Run tests
        run: |
          PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
          helm lint helm/stratmaster-api
          
  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v1
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
          
      - name: Deploy to staging
        run: |
          helm upgrade --install stratmaster-staging helm/stratmaster-api \
            --namespace stratmaster-staging \
            --values helm/values-staging.yaml \
            --set image.tag=${{ github.sha }} \
            --wait --timeout=600s
            
      - name: Run smoke tests
        run: |
          kubectl -n stratmaster-staging wait --for=condition=ready pod -l app=stratmaster-api --timeout=300s
          curl -f https://stratmaster-staging.company.com/healthz
```

### Staging Operations

```bash
# Check deployment status
kubectl -n stratmaster-staging get pods,svc,ingress

# View application logs
kubectl -n stratmaster-staging logs -l app=stratmaster-api --tail=100

# Port forward for debugging
kubectl -n stratmaster-staging port-forward svc/stratmaster-api 8080:80

# Run database migrations
kubectl -n stratmaster-staging exec deployment/stratmaster-api -- \
  python -m alembic upgrade head

# Scale deployment
kubectl -n stratmaster-staging scale deployment stratmaster-api --replicas=2
```

## Production Deployment

### Architecture Overview

Production deployment uses a highly available Kubernetes setup:

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
├─────────────────────────────────────────────────────────────┤
│               Ingress Controller                            │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway │ Research MCP │ Knowledge MCP │ Router MCP    │
│  (3 replicas) │ (2 replicas) │ (2 replicas)  │ (2 replicas)  │
├─────────────────────────────────────────────────────────────────┤
│             Storage Layer (Multi-AZ)                           │
│  PostgreSQL │ Qdrant Cluster │ OpenSearch │ NebulaGraph     │
│  (Primary + Standby)  (3 nodes)     (3 nodes)  (3 nodes)       │
├─────────────────────────────────────────────────────────────────┤
│           Infrastructure Services                              │
│  Temporal │ Keycloak │ MinIO │ Monitoring │ Logging          │
└─────────────────────────────────────────────────────────────────┘
```

### Production Values (`helm/values-production.yaml`)

```yaml
# High availability configuration
replicaCount:
  api: 3
  researchMcp: 2
  knowledgeMcp: 2
  routerMcp: 2

# Production resource allocation
resources:
  api:
    requests:
      cpu: "2"
      memory: "4Gi"
    limits:
      cpu: "4"
      memory: "8Gi"

  postgres:
    requests:
      cpu: "4"
      memory: "8Gi"
    limits:
      cpu: "8"
      memory: "16Gi"

# Database configuration
postgresql:
  enabled: true
  architecture: replication
  auth:
    existingSecret: postgres-credentials
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: fast-ssd
  readReplicas:
    replicaCount: 2
    persistence:
      enabled: true
      size: 100Gi

# Vector database clustering
qdrant:
  cluster:
    enabled: true
    replicas: 3
  persistence:
    enabled: true
    size: 200Gi
    storageClass: fast-ssd
  resources:
    requests:
      cpu: "2"
      memory: "8Gi"

# Production security
security:
  tls:
    enabled: true
    certificateManager: true
  networkPolicies:
    enabled: true
    denyAll: true
  podSecurityPolicy:
    enabled: true
  serviceAccount:
    create: true
    automountServiceAccountToken: false

# Auto-scaling
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Monitoring and observability
monitoring:
  enabled: true
  prometheus:
    enabled: true
    retention: 30d
  grafana:
    enabled: true
    persistence:
      enabled: true
  alerting:
    enabled: true
    webhookUrl: https://slack.com/hooks/your-webhook

# Backup configuration
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention: 30
  storage:
    provider: s3
    bucket: stratmaster-backups
    region: us-east-1
```

### Production Secrets

Use Sealed Secrets or external secret management:

```yaml
# sealed-secrets/postgres-credentials.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: postgres-credentials
  namespace: stratmaster-prod
spec:
  encryptedData:
    postgres-password: AgBy3i4OJSWK+PiTySYZZA9rO43cGHuSmhkmQqkuyWQxr...
    replication-password: AgBy3i4OJSWK+PiTySYZZA9rO43cGHuSmhkmQqkuyWQxr...
```

### Deployment Process

```bash
# 1. Create production namespace
kubectl create namespace stratmaster-prod

# 2. Apply network policies
kubectl apply -f ops/k8s/network-policies/

# 3. Deploy sealed secrets
kubectl apply -f ops/k8s/sealed-secrets/

# 4. Deploy with production values
helm upgrade --install stratmaster helm/stratmaster-api \
  --namespace stratmaster-prod \
  --values helm/values-production.yaml \
  --set image.tag=${IMAGE_TAG} \
  --wait --timeout=1200s

# 5. Verify deployment
kubectl -n stratmaster-prod get pods,svc,ingress
kubectl -n stratmaster-prod rollout status deployment/stratmaster-api
```

### Blue-Green Deployment

For zero-downtime deployments:

```bash
# 1. Deploy to green environment
helm upgrade --install stratmaster-green helm/stratmaster-api \
  --namespace stratmaster-green \
  --values helm/values-production.yaml \
  --set image.tag=${NEW_IMAGE_TAG}

# 2. Run smoke tests against green
curl -f https://stratmaster-green.company.com/healthz

# 3. Switch traffic to green
kubectl patch ingress stratmaster-ingress \
  --patch '{"spec":{"rules":[{"host":"stratmaster.company.com","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"stratmaster-green","port":{"number":80}}}}]}}]}}'

# 4. Monitor for issues, rollback if needed
kubectl patch ingress stratmaster-ingress \
  --patch '{"spec":{"rules":[{"host":"stratmaster.company.com","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"stratmaster-blue","port":{"number":80}}}}]}}]}}'
```

### Disaster Recovery

#### Database Backup and Restore

```bash
# Automated backup (runs via CronJob)
kubectl create job --from=cronjob/postgres-backup postgres-backup-manual

# Restore from backup
kubectl create job postgres-restore --image=postgres:15 -- \
  /bin/bash -c "psql ${DATABASE_URL} < /backups/backup-20240101.sql"

# Point-in-time recovery
kubectl exec -it postgres-primary-0 -- \
  pg_basebackup -D /var/lib/postgresql/recovery -Ft -z -P
```

#### Vector Database Recovery

```bash
# Create Qdrant snapshot
curl -X POST http://qdrant-cluster:6333/collections/tenant_demo_research/snapshots

# List available snapshots
curl http://qdrant-cluster:6333/collections/tenant_demo_research/snapshots

# Restore from snapshot
curl -X PUT http://qdrant-cluster:6333/collections/tenant_demo_research/snapshots/recover \
  -H "Content-Type: application/json" \
  -d '{"location": "s3://backups/qdrant/snapshot-20240101.tar"}'
```

### Production Monitoring

#### Health Checks

```bash
# Service health endpoints
curl https://stratmaster.company.com/healthz
curl https://stratmaster.company.com/ready

# Deep health check
curl https://stratmaster.company.com/health/deep
```

#### Key Metrics Dashboard

Monitor these critical metrics:

- **Application**: Request rate, error rate, response time
- **Infrastructure**: CPU, memory, disk usage
- **Database**: Connection count, query performance, replication lag
- **Storage**: Vector search latency, index size, disk usage
- **Network**: Ingress traffic, service mesh metrics

#### Alerting Rules

```yaml
# prometheus-alerts.yaml
groups:
  - name: stratmaster-production
    rules:
      - alert: APIHighErrorRate
        expr: rate(http_requests_total{job="stratmaster-api",code=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in API"
          
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          
      - alert: VectorSearchLatencyHigh
        expr: histogram_quantile(0.95, rate(qdrant_request_duration_seconds_bucket[5m])) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High vector search latency"
```

### Security Hardening

#### Network Security

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: stratmaster-network-policy
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
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

#### Pod Security

```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: stratmaster-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### Performance Optimization

#### Horizontal Pod Autoscaling

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: stratmaster-api-hpa
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
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### Database Optimization

```sql
-- Production PostgreSQL tuning
-- postgresql.conf settings
shared_buffers = '2GB'
effective_cache_size = '6GB'
work_mem = '64MB'
maintenance_work_mem = '512MB'
max_connections = 200
checkpoint_completion_target = 0.9
wal_buffers = '16MB'
random_page_cost = 1.1
```

### Compliance and Auditing

#### Audit Logging

```yaml
# Enable Kubernetes audit logging
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  namespaces: ["stratmaster-prod"]
  resources:
  - group: ""
    resources: ["pods", "services"]
  - group: "apps"
    resources: ["deployments", "statefulsets"]
```

#### Data Protection

```yaml
# Backup encryption
apiVersion: batch/v1
kind: CronJob
metadata:
  name: encrypted-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: stratmaster/backup:latest
            env:
            - name: GPG_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: backup-encryption
                  key: key-id
            command:
            - /bin/bash
            - -c
            - |
              pg_dump ${DATABASE_URL} | gpg --encrypt -r ${GPG_KEY_ID} | \
              aws s3 cp - s3://stratmaster-backups/db-$(date +%Y%m%d).sql.gpg
```

## Multi-Region Deployment

### Global Architecture

For global deployment with data locality:

```
Primary Region (US-East):
├── Full StratMaster Stack
├── Primary Database (Read/Write)
└── Complete Vector Indexes

Secondary Region (EU-West):
├── API Gateway + MCP Servers
├── Database Read Replica
├── Regional Vector Indexes
└── Local Object Storage

Tertiary Region (Asia-Pacific):
├── API Gateway (Cache Heavy)
├── Database Read Replica
└── CDN Distribution
```

### Cross-Region Configuration

```yaml
# Multi-region values
global:
  region: us-east-1
  primaryRegion: us-east-1
  replication:
    enabled: true
    regions:
      - eu-west-1
      - ap-southeast-1

database:
  replication:
    enabled: true
    readReplicas:
      - region: eu-west-1
        replicas: 2
      - region: ap-southeast-1
        replicas: 1

storage:
  crossRegionReplication:
    enabled: true
    regions:
      - eu-west-1
      - ap-southeast-1
```

## Troubleshooting Deployments

### Common Issues

#### Pod Startup Failures

```bash
# Check pod status
kubectl -n stratmaster-prod describe pod <pod-name>

# View logs
kubectl -n stratmaster-prod logs <pod-name> --previous

# Check resource constraints
kubectl -n stratmaster-prod top pods
```

#### Service Discovery Issues

```bash
# Test service connectivity
kubectl -n stratmaster-prod run test-pod --image=busybox --rm -it -- /bin/sh
nslookup stratmaster-api
wget -qO- http://stratmaster-api:8080/healthz
```

#### Database Connection Problems

```bash
# Check database connectivity
kubectl -n stratmaster-prod exec -it deployment/stratmaster-api -- \
  python -c "import psycopg2; conn = psycopg2.connect('${DATABASE_URL}'); print('Connected')"

# Monitor connection pool
kubectl -n stratmaster-prod exec -it postgres-primary-0 -- \
  psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### Performance Issues

#### High Memory Usage

```bash
# Check memory metrics
kubectl -n stratmaster-prod top pods --sort-by=memory

# Analyze memory leaks
kubectl -n stratmaster-prod exec -it <pod-name> -- \
  python -c "import psutil; print(psutil.virtual_memory())"
```

#### Slow Database Queries

```bash
# Enable query logging
kubectl -n stratmaster-prod exec -it postgres-primary-0 -- \
  psql -c "ALTER SYSTEM SET log_statement = 'all';"

# Analyze slow queries
kubectl -n stratmaster-prod exec -it postgres-primary-0 -- \
  psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

For detailed troubleshooting procedures, see the [Troubleshooting Guide](troubleshooting.md).

## Next Steps

- **Infrastructure Details**: See [Infrastructure Guide](infrastructure.md) for service-specific configurations
- **Development Setup**: See [Development Guide](development.md) for local development
- **Security Practices**: See [Security Guide](security.md) for hardening procedures
- **Architecture Overview**: See [Architecture Overview](architecture.md) for system design