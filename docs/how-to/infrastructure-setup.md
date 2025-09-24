# Infrastructure Setup

This guide covers setting up StratMaster infrastructure across different environments, from local development to production deployment on Kubernetes. Follow these step-by-step instructions to get your infrastructure running.

## Local Development Setup

### Prerequisites

Ensure you have the following installed:

- **Docker & Docker Compose** (v20.10+)
- **Python 3.13+**
- **Node.js 18+** (for UI development)
- **Helm 3.8+** (for Kubernetes deployments)
- **kubectl** (matching your cluster version)

### Quick Local Stack

Start the complete local development environment:

```bash
# Bootstrap development environment
make bootstrap

# Start all services
make dev.up

# View logs
make dev.logs

# Stop all services
make dev.down
```

This starts:
- PostgreSQL (port 5432)
- Qdrant vector database (port 6333)
- OpenSearch (port 9200)
- NebulaGraph (port 9669)
- MinIO object storage (port 9000)
- Temporal server (port 7233)
- Langfuse observability (port 3000)
- Keycloak identity provider (port 8180)

### Service Configuration

#### Database Setup
```bash
# Initialize databases
make db.migrate

# Seed test data
make db.seed

# Reset database (development only)
make db.reset
```

#### Vector Database Setup
```bash
# Create Qdrant collections
make vector.setup

# Index sample documents
make vector.index

# Test vector search
curl -X POST "http://localhost:6333/collections/strategies/points/search" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, 0.3],
    "limit": 5,
    "with_payload": true
  }'
```

#### Search Engine Setup
```bash
# Create OpenSearch indices
make search.setup

# Index documents for full-text search
make search.index

# Test search functionality
curl -X GET "localhost:9200/strategies/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match": {
        "content": "brand strategy"
      }
    }
  }'
```

### Development Workflow

#### Running Individual Services
```bash
# Start API server only
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --port 8080

# Start specific MCP server
cd packages/mcp-servers/research
python -m research_mcp

# Start Temporal worker
.venv/bin/python -m stratmaster_api.workers.temporal_worker
```

#### Environment Variables
Create `.env.local` for development overrides:

```bash
# .env.local
DATABASE_URL=postgresql://stratmaster:password@localhost:5432/stratmaster_dev
QDRANT_URL=http://localhost:6333
OPENSEARCH_URL=http://localhost:9200
NEBULA_HOST=localhost:9669

# API keys (development only)
OPENAI_API_KEY=your_development_key_here
ANTHROPIC_API_KEY=your_development_key_here

# Feature flags
ENABLE_DEBUG_MODE=true
ENABLE_EXPERIMENTAL_FEATURES=true
LOG_LEVEL=debug
```

## Staging Environment

### AWS EKS Setup

#### 1. Create EKS Cluster
```bash
# Install eksctl if not already installed
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
  --name stratmaster-staging \
  --region us-west-2 \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed \
  --enable-ssm
```

#### 2. Install Required Addons
```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# Install Cluster Autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Install Prometheus + Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

#### 3. Deploy StratMaster
```bash
# Add secrets
kubectl create namespace stratmaster-staging
kubectl create secret generic api-secrets \
  --namespace stratmaster-staging \
  --from-literal=database-url="postgresql://..." \
  --from-literal=openai-api-key="sk-..." \
  --from-literal=jwt-secret="your-secret-key"

# Deploy using Helm
helm install stratmaster-staging ./helm/stratmaster-api \
  --namespace stratmaster-staging \
  --values helm/values/staging.yaml
```

### Staging Configuration

```yaml
# helm/values/staging.yaml
global:
  environment: staging
  domain: staging.stratmaster.ai

api:
  replicaCount: 2
  image:
    repository: stratmaster/api
    tag: "v0.1.0"
  
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 500m
      memory: 1Gi

database:
  enabled: false  # Use external RDS
  external:
    host: stratmaster-staging.cluster-xxx.us-west-2.rds.amazonaws.com
    port: 5432
    database: stratmaster_staging

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

## Production Environment

### High Availability Setup

#### Architecture Overview
```mermaid
graph TB
    subgraph "Load Balancer"
        ALB[AWS Application Load Balancer]
    end
    
    subgraph "EKS Cluster - Multi-AZ"
        subgraph "AZ-1"
            API1[API Pod 1]
            MCP1[MCP Services 1]
        end
        subgraph "AZ-2"
            API2[API Pod 2]
            MCP2[MCP Services 2]
        end
        subgraph "AZ-3"
            API3[API Pod 3]
            MCP3[MCP Services 3]
        end
    end
    
    subgraph "Data Layer"
        RDS[(RDS Multi-AZ)]
        QDRANT[(Qdrant Cluster)]
        OPENSEARCH[(OpenSearch Cluster)]
    end
    
    ALB --> API1
    ALB --> API2
    ALB --> API3
    
    API1 --> RDS
    API2 --> RDS
    API3 --> RDS
```

#### 1. Production EKS Cluster
```bash
# Production cluster with enhanced security
eksctl create cluster \
  --name stratmaster-production \
  --region us-west-2 \
  --zones us-west-2a,us-west-2b,us-west-2c \
  --node-type m5.xlarge \
  --nodes 6 \
  --nodes-min 3 \
  --nodes-max 20 \
  --managed \
  --enable-ssm \
  --private-access \
  --public-access \
  --vpc-private-subnets \
  --asg-access \
  --external-dns-access \
  --full-ecr-access
```

#### 2. Security Hardening
```bash
# Install Falco for runtime security
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --namespace falco-system --create-namespace

# Install Pod Security Standards
kubectl label --overwrite ns stratmaster-production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

# Install Network Policies
kubectl apply -f ops/k8s/network-policies/
```

#### 3. Data Layer Setup

**RDS PostgreSQL**:
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier stratmaster-prod \
  --db-instance-class db.r5.2xlarge \
  --engine postgres \
  --engine-version 15.4 \
  --master-username stratmaster \
  --master-user-password "$(openssl rand -base64 32)" \
  --allocated-storage 500 \
  --storage-type gp3 \
  --storage-encrypted \
  --multi-az \
  --backup-retention-period 30 \
  --monitoring-interval 60 \
  --enable-performance-insights
```

**Qdrant Vector Database**:
```yaml
# helm/values/production-qdrant.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: qdrant
  template:
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.7.0
        ports:
        - containerPort: 6333
        - containerPort: 6334
        volumeMounts:
        - name: qdrant-data
          mountPath: /qdrant/storage
        env:
        - name: QDRANT__CLUSTER__ENABLED
          value: "true"
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
          limits:
            cpu: 2
            memory: 8Gi
  volumeClaimTemplates:
  - metadata:
      name: qdrant-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

#### 4. Production Deployment
```yaml
# helm/values/production.yaml
global:
  environment: production
  domain: api.stratmaster.ai

api:
  replicaCount: 6
  image:
    repository: stratmaster/api
    tag: "v0.1.0"
  
  resources:
    requests:
      cpu: 1
      memory: 2Gi
    limits:
      cpu: 2
      memory: 4Gi
  
  autoscaling:
    enabled: true
    minReplicas: 6
    maxReplicas: 50
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80

security:
  podSecurityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  
  networkPolicy:
    enabled: true
  
  serviceAccount:
    create: true
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/stratmaster-api-role

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
```

### Deployment Process

#### 1. Build and Push Images
```bash
# Build all service images
make docker.build.all

# Tag for production
docker tag stratmaster/api:latest stratmaster/api:v0.1.0

# Push to registry
make docker.push.all
```

#### 2. Deploy with Rolling Update
```bash
# Deploy to production
helm upgrade --install stratmaster-prod ./helm/stratmaster-api \
  --namespace stratmaster-production \
  --values helm/values/production.yaml \
  --atomic \
  --timeout 10m

# Verify deployment
kubectl rollout status deployment/stratmaster-api -n stratmaster-production

# Run smoke tests
make test.smoke.production
```

## Monitoring and Observability

### Metrics Collection
```yaml
# Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "stratmaster_rules.yml"

scrape_configs:
  - job_name: 'stratmaster-api'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - stratmaster-production
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: stratmaster-api
```

### Alerting Rules
```yaml
# stratmaster_rules.yml
groups:
- name: stratmaster.rules
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

### Log Aggregation
```yaml
# Fluent Bit configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [INPUT]
        Name tail
        Path /var/log/containers/*stratmaster*.log
        Parser docker
        Tag stratmaster.*
    
    [FILTER]
        Name kubernetes
        Match stratmaster.*
        Merge_Log On
    
    [OUTPUT]
        Name es
        Match *
        Host elasticsearch.logging.svc.cluster.local
        Port 9200
        Index stratmaster-logs
```

## Disaster Recovery

### Backup Strategy
```bash
# Database backups
aws rds create-db-snapshot \
  --db-instance-identifier stratmaster-prod \
  --db-snapshot-identifier stratmaster-prod-$(date +%Y%m%d-%H%M%S)

# Vector database backups
kubectl exec -n stratmaster-production qdrant-0 -- \
  /opt/qdrant/qdrant --snapshot /qdrant/storage/snapshots

# Configuration backups
kubectl get configmaps,secrets -n stratmaster-production -o yaml > \
  backups/k8s-config-$(date +%Y%m%d).yaml
```

### Recovery Procedures
```bash
# Restore from RDS snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier stratmaster-prod-restored \
  --db-snapshot-identifier stratmaster-prod-20231201-120000

# Restore vector database
kubectl cp backups/qdrant-snapshot.tar.gz qdrant-0:/tmp/
kubectl exec qdrant-0 -- tar -xzf /tmp/qdrant-snapshot.tar.gz -C /qdrant/storage/

# Redeploy applications
helm rollback stratmaster-prod 1
```

## Troubleshooting

### Common Issues

#### 1. Pod Startup Issues
```bash
# Check pod status
kubectl get pods -n stratmaster-production

# View pod logs
kubectl logs -f deployment/stratmaster-api -n stratmaster-production

# Debug pod configuration
kubectl describe pod <pod-name> -n stratmaster-production
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
kubectl run --rm -i --tty --image postgres:15 postgres-client -- \
  psql "postgresql://user:pass@host:5432/dbname"

# Check service DNS resolution
kubectl run --rm -i --tty --image busybox dns-test -- nslookup postgres.stratmaster-production.svc.cluster.local
```

#### 3. Performance Issues
```bash
# Check resource usage
kubectl top pods -n stratmaster-production
kubectl top nodes

# View HPA status
kubectl get hpa -n stratmaster-production

# Check metrics
kubectl port-forward svc/prometheus 9090:9090
```

### Health Checks

#### Application Health
```bash
# API health check
curl -f http://api.stratmaster.ai/healthz

# Database health
curl -f http://api.stratmaster.ai/health/database

# Dependencies health
curl -f http://api.stratmaster.ai/health/dependencies
```

#### Infrastructure Health
```bash
# Cluster health
kubectl cluster-info
kubectl get nodes

# Service health
kubectl get svc -n stratmaster-production
kubectl get endpoints -n stratmaster-production
```

---

This infrastructure setup provides a robust, scalable foundation for StratMaster across all environments. Regular monitoring, testing, and maintenance ensure reliable operation and quick recovery from any issues.