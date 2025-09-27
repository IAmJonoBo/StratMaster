# StratMaster Intelligent DevOps & Self-Healing System

## Overview

StratMaster includes a comprehensive intelligent DevOps and self-healing system designed to ensure robust dependency management, proactive health monitoring, and automated recovery capabilities. This system is optimized for GitHub Actions and other CI/CD environments, providing network resilience and graceful degradation under constrained conditions.

## 🎯 Key Features

### 1. Network-Resilient Dependency Management
- **Intelligent Retry Logic**: Exponential backoff with jitter for network failures
- **Multiple Package Index Support**: Automatic fallback to alternative PyPI mirrors
- **Offline Mode**: Local package caching for network-constrained environments
- **GitHub Actions Optimization**: Extended timeouts and CI-specific optimizations

### 2. Comprehensive Health Monitoring
- **Real-time Service Health Checks**: HTTP endpoint monitoring with timeout detection
- **Dependency Freshness Scanning**: Automated checking for updates and security vulnerabilities
- **System Resource Monitoring**: CPU, memory, and disk usage tracking
- **Parallel Execution**: High-performance concurrent health checks

### 3. Self-Healing Automation
- **Proactive Issue Detection**: Automatic identification of system problems
- **Service Recovery**: Intelligent service restart and failover
- **Dependency Conflict Resolution**: Automated dependency fixing and rollback
- **Environment Recovery**: Virtual environment rebuilding and restoration

### 4. DevOps Dashboard
- **Web-based Monitoring**: Real-time health status visualization
- **Action Triggers**: Manual and automated healing controls
- **Historical Metrics**: System performance tracking over time
- **Alert Management**: Critical status notifications and responses

## 🚀 Quick Start

### Basic Health Check
```bash
# Run comprehensive health check
make health.check

# Check specific components
make health.check.services  # Services only
make health.check.deps      # Dependencies only
make health.check.resources # System resources only
```

### Robust Dependency Installation
```bash
# Install with network resilience
make deps.install.robust

# Install development dependencies
make deps.install.robust.dev

# Warm up package cache for offline use
make deps.cache.warmup
```

### Self-Healing Operations
```bash
# Automated healing analysis
make heal.auto

# Specific recovery actions
make heal.recover.deps      # Fix dependencies
make heal.recover.env       # Rebuild environment
make heal.cleanup          # Clean temporary files

# System snapshots and rollback
make system.snapshot       # Create snapshot
make heal.rollback         # Rollback to last known good state
```

### DevOps Dashboard
```bash
# Start web dashboard on port 8090
python scripts/devops_dashboard.py --port 8090

# Monitor without web interface
python scripts/devops_dashboard.py --monitor-only

# Export current metrics
python scripts/devops_dashboard.py --export-metrics
```

## 🛠️ Advanced Usage

### Robust Installer CLI

The robust installer provides comprehensive dependency management with network resilience:

```bash
# Install from requirements file with retry logic
python scripts/robust_installer.py install --requirements requirements.txt

# Install single package with fallback
python scripts/robust_installer.py install --package "fastapi>=0.100.0"

# Cache packages for offline installation
python scripts/robust_installer.py cache-warmup

# Validate installation environment
python scripts/robust_installer.py validate-environment
```

**Key Features:**
- **Network Strategy Detection**: Automatically adapts to network conditions
- **Exponential Backoff**: Intelligent retry delays with jitter
- **Package Index Fallback**: Multiple PyPI mirror support
- **GitHub Actions Integration**: Optimized for CI environments

### System Health Monitor CLI

Comprehensive health monitoring with detailed reporting:

```bash
# Run all health checks
python scripts/system_health_monitor.py check --all

# Continuous monitoring with alerting
python scripts/system_health_monitor.py monitor --interval 60

# Generate health reports
python scripts/system_health_monitor.py report --format json --output health_report.json
python scripts/system_health_monitor.py report --format text
```

### k6 Load Testing Baseline

Phase 5 of SCRATCH.md calls for continuous API load testing. The repository now
includes a reusable smoke profile at `bench/k6/api_smoke.js` that exercises the
model router, hybrid retrieval, and debate endpoints while tracking RED metrics.

```bash
# Basic 1 minute smoke against local stack
API_BASE=http://localhost:8000 k6 run bench/k6/api_smoke.js

# Heavier profile with custom thresholds and authentication
VUS=25 DURATION=5m API_BASE=https://staging.stratmaster.ai \
  API_TOKEN=$(cat ~/.config/stratmaster/token) \
  k6 run bench/k6/api_smoke.js
```

The script emits a `k6-smoke-summary.json` artifact suitable for trend analysis
or Grafana ingestion.

**Health Check Categories:**
- **Service Health**: HTTP endpoint monitoring with timeout detection
- **Dependency Freshness**: Update availability and security vulnerability scanning
- **System Resources**: CPU, memory, disk usage monitoring
- **Environment Validation**: Python environment and package consistency

### Self-Healing System CLI

Automated recovery and remediation capabilities:

```bash
# Analyze system and perform healing
python scripts/self_healing.py analyze --auto-heal

# Specific recovery actions
python scripts/self_healing.py recover --service api
python scripts/self_healing.py recover --dependencies
python scripts/self_healing.py recover --environment
python scripts/self_healing.py recover --cleanup

# Snapshot and rollback management
python scripts/self_healing.py snapshot
python scripts/self_healing.py rollback --to-last-known-good
python scripts/self_healing.py rollback --snapshot-id 20241201_143022

# Comprehensive validation and healing
python scripts/self_healing.py validate-and-heal
```

**Recovery Strategies:**
- **Service Recovery**: Automatic restart of failed services
- **Dependency Resolution**: Conflict resolution and reinstallation
- **Environment Rebuilding**: Virtual environment recreation from scratch
- **Cleanup Operations**: Temporary file and cache management

## 🔧 GitHub Actions Integration

### Enhanced CI/CD Workflow

The enhanced CI/CD workflow (`enhanced-ci-cd.yml`) provides:

#### 1. System Health Checks
```yaml
# Automated health validation
- name: Run comprehensive health check
  run: python scripts/system_health_monitor.py check --all
  
# Auto-healing on critical issues
- name: Auto-heal on critical issues
  if: steps.health_check.outputs.health_status == 'critical'
  run: python scripts/self_healing.py analyze --auto-heal
```

#### 2. Robust Build Process
```yaml
# Network-resilient dependency installation
- name: Bootstrap with network resilience
  run: |
    python scripts/robust_installer.py cache-warmup
    make bootstrap.robust

# Test with fallback recovery
- name: Run tests with self-healing fallback
  run: |
    timeout 600 make test || python scripts/self_healing.py recover --dependencies
```

#### 3. Security Scanning with Auto-Remediation
```yaml
# Vulnerability scanning with automatic fixes
- name: Auto-remediate security issues
  if: steps.security_scan.outputs.critical_vulns == 'true'
  run: |
    python scripts/self_healing.py recover --dependencies
    python scripts/system_health_monitor.py check --dependencies-only
```

#### 4. Intelligent Dependency Management
```yaml
# Automated dependency updates
- name: Apply safe dependency updates
  run: |
    python scripts/dependency_upgrade.py upgrade --type patch
    make test  # Validate after updates
```

Supplement the upgrade workflow with the environment diff helper to ensure the
runtime matches production snapshots before deploys:

```bash
python scripts/dependency_sync.py status --json
python scripts/dependency_sync.py sync   # exits non-zero when drift remains
```

### RAG Quality Evaluation (RAGAS + TruLens)

Phase 2.3 requires dual evaluation of retrieval responses using both RAGAS and
TruLens metrics. The repository ships a golden regression dataset at
`data/evals/golden_rag_samples.json` alongside the combined evaluator exposed via
`stratmaster_evals`.

```bash
# Run the TruLens-backed heuristic on the golden dataset
python - <<'PY'
from stratmaster_evals.models import EvaluationRequest
from stratmaster_evals.trulens import TruLensRAGEvaluator
import json

payload = json.loads(open("data/evals/golden_rag_samples.json").read())
request = EvaluationRequest(**payload, experiment_name="golden", model_name="router/test")
summary = TruLensRAGEvaluator().evaluate(request)
print(summary.metrics.as_dict())
print("passes_quality_gates=", summary.passes_quality_gates)
PY
```

The `/eval/ragas` endpoint now emits both RAGAS and TruLens metrics to Langfuse,
keeping SCRATCH quality gates visible inside Grafana dashboards and deployment
reviews.

### Environment Variables

Configure the system behavior using environment variables:

```bash
# GitHub Actions optimization
export GITHUB_ACTIONS=true

# Network timeout settings
export PIP_TIMEOUT=600
export PYTHONNOUSERSITE=1

# Health monitoring intervals
export HEALTH_CHECK_INTERVAL=300
export AUTO_HEAL_ENABLED=true
```

## 📊 Monitoring and Alerting

### Health Status Levels

The system uses a four-tier health status system:

- **🟢 Healthy**: All systems operational
- **🟡 Warning**: Issues detected but not critical
- **🔴 Critical**: Immediate attention required
- **⚪ Unknown**: Unable to determine status

### Automatic Triggers

Self-healing actions are triggered based on health status:

1. **Critical Service Failures**: Automatic service restart
2. **Dependency Conflicts**: Conflict resolution and reinstallation
3. **High Resource Usage**: Cleanup and resource optimization
4. **Environment Corruption**: Environment rebuilding

### Dashboard Features

The web dashboard provides:

- **Real-time Status**: Live health monitoring with auto-refresh
- **Action Controls**: Manual trigger buttons for healing actions
- **Historical Data**: Metrics history and trend analysis
- **Alert Management**: Critical status notifications

## 🛡️ Network Resilience Strategies

### Timeout Handling

The system implements intelligent timeout strategies:

```python
# Standard timeouts
STANDARD_TIMEOUT = 120  # seconds

# CI environment timeouts (GitHub Actions)
CI_TIMEOUT = 600  # seconds

# Network connectivity check
CONNECTIVITY_TIMEOUT = 10  # seconds
```

### Fallback Mechanisms

Multiple fallback strategies ensure reliability:

1. **Package Index Fallback**: PyPI → PyPI mirrors → Local cache
2. **Installation Methods**: Batch install → Individual packages → Offline mode
3. **Recovery Actions**: Service restart → Environment rebuild → Rollback
4. **Network Strategies**: Online → Limited connectivity → Offline mode

### Error Handling

Comprehensive error handling with recovery:

```python
# Network errors: Retry with exponential backoff
# Timeout errors: Increase timeout and retry
# Dependency conflicts: Rollback and reinstall
# Service failures: Restart with health checks
```

## 📝 Troubleshooting

### Common Issues and Solutions

#### 1. Network Timeout Errors
```bash
# Problem: pip install timeouts in CI
# Solution: Use robust installer
python scripts/robust_installer.py install --requirements requirements.txt
```

#### 2. Service Health Check Failures
```bash
# Problem: Services not responding
# Solution: Restart services with health validation
python scripts/self_healing.py recover --service api
```

#### 3. Dependency Conflicts
```bash
# Problem: Version conflicts between packages
# Solution: Use conflict resolution
python scripts/self_healing.py recover --dependencies
```

#### 4. Environment Corruption
```bash
# Problem: Virtual environment broken
# Solution: Rebuild environment
python scripts/self_healing.py recover --environment
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Enable debug logging
python scripts/system_health_monitor.py check --all --verbose
python scripts/self_healing.py analyze --auto-heal --verbose
python scripts/robust_installer.py install --package fastapi --verbose
```

### Log Analysis

Check system logs for detailed information:

```bash
# Health check logs
tail -f /tmp/health_monitor.log

# Self-healing logs  
tail -f /tmp/self_healing.log

# Dashboard logs
tail -f /tmp/devops_dashboard.log
```

## 🔄 Best Practices

### 1. Regular Health Checks

Set up regular health monitoring:

```bash
# Daily health checks
crontab -e
0 6 * * * cd /path/to/stratmaster && make health.check

# Continuous monitoring
make health.monitor &  # Run in background
```

### 2. Proactive Snapshots

Create snapshots before major changes:

```bash
# Before dependency updates
make system.snapshot

# Before deployments
python scripts/self_healing.py snapshot
```

### 3. CI/CD Integration

Use the enhanced workflow for robust CI/CD:

```yaml
# Include health checks in all workflows
- name: Health Check
  run: make health.check

# Use robust bootstrap
- name: Setup Environment  
  run: make bootstrap.robust
```

### 4. Monitoring Dashboard

Keep the dashboard running for continuous visibility:

```bash
# Start dashboard
python scripts/devops_dashboard.py --port 8090 &

# Access dashboard
open http://localhost:8090
```

## 🔒 Security Considerations

### 1. Vulnerability Scanning

Automated security vulnerability checking:

```bash
# Check for known vulnerabilities
python scripts/system_health_monitor.py check --dependencies-only

# Install security scanner
pip install safety bandit
```

### 2. Dependency Validation

Verify dependency integrity:

```bash
# Validate dependency registry
python scripts/register_dependencies.py validate

# Check for conflicts
python scripts/dependency_upgrade.py check
```

### 3. Environment Isolation

Use virtual environments for isolation:

```bash
# Robust virtual environment setup
make bootstrap.robust

# Environment validation
python scripts/robust_installer.py validate-environment
```

## 🚀 Performance Optimization

### 1. Parallel Execution

The system uses parallel execution for performance:

```python
# Health checks run concurrently
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit all health check tasks
    futures = [executor.submit(check_func) for check_func in checks]
```

### 2. Caching Strategy

Intelligent caching reduces network usage:

```bash
# Warm up package cache
make deps.cache.warmup

# Use cached packages in offline mode
python scripts/robust_installer.py install --package fastapi --no-offline
```

### 3. Resource Monitoring

Continuous resource monitoring prevents issues:

```bash
# Monitor system resources
make health.check.resources

# Cleanup when needed
make heal.cleanup
```

## 📈 Metrics and Analytics

### Health Metrics

Track system health over time:

- **Uptime**: Service availability percentage
- **Response Time**: Health check execution time
- **Recovery Time**: Time to resolution for issues
- **Success Rate**: Percentage of successful operations

### Performance Metrics

Monitor system performance:

- **CPU Usage**: Average and peak CPU utilization
- **Memory Usage**: Memory consumption patterns
- **Disk Usage**: Storage utilization trends
- **Network**: Connectivity success rates

### Export Metrics

Export metrics for external monitoring:

```bash
# Export current metrics
python scripts/devops_dashboard.py --export-metrics > metrics.json

# Generate reports
python scripts/system_health_monitor.py report --format json > health_report.json
```

## 🤝 Contributing

When contributing to the DevOps system:

1. **Test Network Resilience**: Ensure features work with network constraints
2. **Add Health Checks**: Include health validation for new components
3. **Document Recovery**: Provide self-healing procedures for new features
4. **Update Dashboard**: Add monitoring for new capabilities

## 📄 License

This DevOps and self-healing system is part of StratMaster and follows the same licensing terms.