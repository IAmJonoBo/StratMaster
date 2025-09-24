# Scripts Reference

StratMaster includes numerous utility scripts for development, testing, deployment, and maintenance operations. Scripts are organized by functional area and provide automation for common tasks.

## Development Scripts {#development}

### Setup and Validation

#### `smoke_api.py`
Quick smoke test for API functionality without network dependencies.

```bash
python scripts/smoke_api.py
```

**Tests:**
- API factory creation
- Health endpoint response
- OpenAPI documentation generation
- In-process validation

**Expected output:** HTTP 200 responses and Swagger UI confirmation

---

#### `advanced_testing.py`
Comprehensive testing framework with multiple test strategies.

```bash
python scripts/advanced_testing.py [--type TYPE] [--verbose]
```

**Options:**
- `--type`: Test type (unit, integration, load, property, contract)
- `--verbose`: Detailed output

**Features:**
- Property-based testing with Hypothesis
- Contract testing for API compatibility
- Load testing with configurable parameters
- Integration testing across services

---

#### `cleanup_appledouble.sh`
Removes macOS `.DS_Store` and `._` files from the repository.

```bash
bash scripts/cleanup_appledouble.sh
```

**Use case:** Clean up after macOS development work

---

### AI and Strategy Tools

#### `ai_strategy_wizard.py`
Interactive strategy planning wizard with AI assistance.

```bash
python scripts/ai_strategy_wizard.py
```

**Features:**
- Interactive strategy formulation
- AI-powered recommendations  
- Export to structured formats
- Integration with StratMaster workflows

---

#### `bench_vllm.sh`
Performance benchmarking for VLLM model serving.

```bash
bash scripts/bench_vllm.sh [MODEL_NAME] [CONCURRENCY]
```

**Parameters:**
- `MODEL_NAME`: Model to benchmark
- `CONCURRENCY`: Number of concurrent requests

**Metrics:**
- Throughput (requests/second)
- Latency percentiles  
- Memory usage
- GPU utilization

---

## Deployment Scripts {#deployment}

### Production Deployment

#### `deploy.py`
Comprehensive deployment orchestration script.

```bash
python scripts/deploy.py [--environment ENV] [--dry-run] [--rolling]
```

**Options:**
- `--environment`: Target environment (staging, production)
- `--dry-run`: Preview deployment without changes
- `--rolling`: Rolling deployment strategy

**Capabilities:**
- Multi-environment deployment
- Database migration handling
- Service health verification
- Rollback support

---

#### `deploy.sh`
Shell-based deployment script for simple scenarios.

```bash
bash scripts/deploy.sh [ENVIRONMENT]
```

**Environments:** development, staging, production

**Steps:**
- Pre-deployment validation
- Service deployment
- Health checks
- Post-deployment verification

---

### Infrastructure Management

#### `k8s_deploy.py`
Kubernetes-specific deployment automation.

```bash
python scripts/k8s_deploy.py [--cluster CLUSTER] [--namespace NS]
```

**Features:**
- Helm chart deployment
- Resource validation
- Pod health monitoring
- Service mesh configuration

---

## Maintenance Scripts {#maintenance}

### Asset Management

#### `assets_pull.py`
Downloads and manages project assets (models, datasets, configurations).

```bash
python scripts/assets_pull.py [--manifest FILE] [--verify] [--force]
```

**Options:**
- `--manifest`: Asset manifest file (default: `assets_manifest.yaml`)
- `--verify`: Verify checksums after download
- `--force`: Re-download existing assets

**Assets managed:**
- ML models (ColBERT, SPLADE, rerankers)
- Datasets and corpora
- Configuration templates
- Documentation assets

---

#### `dependency_upgrade.py`
Intelligent dependency upgrade management.

```bash
python scripts/dependency_upgrade.py [--strategy STRATEGY] [--dry-run]
```

**Strategies:**
- `conservative`: Patch updates only
- `moderate`: Minor version updates
- `aggressive`: All available updates

**Features:**
- Security vulnerability prioritization
- Compatibility testing
- Automated testing after upgrades
- Rollback capability

---

### Quality Assurance

#### `accessibility_audit.py`
Comprehensive accessibility testing and reporting.

```bash
python scripts/accessibility_audit.py [--format FORMAT] [--fix]
```

**Options:**
- `--format`: Output format (json, html, text)
- `--fix`: Auto-fix common issues

**Standards:** WCAG 2.1 AA compliance

**Checks:**
- Color contrast ratios
- Keyboard navigation
- Screen reader compatibility
- Focus management
- Semantic HTML structure

---

#### `security_scan.py`
Multi-layer security scanning and vulnerability assessment.

```bash
python scripts/security_scan.py [--scope SCOPE] [--format FORMAT]
```

**Scopes:**
- `dependencies`: Package vulnerability scanning
- `code`: Static code analysis
- `secrets`: Secret detection
- `config`: Configuration security
- `all`: Comprehensive scan

**Tools integrated:**
- Bandit for Python security issues
- Safety for dependency vulnerabilities
- TruffleHog for secret detection
- Custom configuration validators

---

### Performance and Monitoring

#### `performance_baseline.py`
Establishes performance baselines and monitors regressions.

```bash
python scripts/performance_baseline.py [--create] [--compare] [--report]
```

**Modes:**
- `--create`: Establish new baseline
- `--compare`: Compare against baseline
- `--report`: Generate performance report

**Metrics:**
- API response times
- Database query performance
- Memory usage patterns
- Resource utilization

---

#### `health_monitor.py`
Continuous health monitoring and alerting.

```bash
python scripts/health_monitor.py [--interval SECONDS] [--alert-threshold N]
```

**Monitors:**
- Service availability
- Database connectivity
- External API status
- Resource usage
- Error rates

---

## Validation Scripts

### Phase and Feature Validation

#### `validate_phase2.sh`
Validates Phase 2 enterprise feature implementation.

```bash
bash scripts/validate_phase2.sh
```

**Validates:**
- Advanced authentication features
- Multi-tenant isolation
- Enterprise integrations
- Compliance requirements
- Performance benchmarks

---

#### `validate_phase3.sh`
Validates Phase 3 advanced features.

```bash
bash scripts/validate_phase3.sh
```

**Checks:**
- ML pipeline integrity
- Advanced analytics
- Automation workflows
- Integration completeness

---

### Environment Validation

#### `validate_environment.py`
Comprehensive environment validation and configuration checking.

```bash
python scripts/validate_environment.py [--environment ENV] [--fix]
```

**Validates:**
- Environment variable configuration
- Service dependencies
- Network connectivity
- Resource availability
- Security settings

---

## Specialized Tools

### Index Management

#### `rebuild_indices.py`
Rebuilds search indices with optimization.

```bash
python scripts/rebuild_indices.py [--type TYPE] [--parallel] [--optimize]
```

**Index types:**
- `colbert`: Dense vector indices
- `splade`: Sparse attention indices
- `graph`: Knowledge graph indices
- `all`: All index types

**Features:**
- Parallel index building
- Index optimization
- Validation and testing
- Backup and rollback

---

### Data Processing

#### `data_pipeline.py`
ETL pipeline for data processing and preparation.

```bash
python scripts/data_pipeline.py [--source SOURCE] [--target TARGET] [--transform CONFIG]
```

**Sources:**
- Raw research data
- External APIs
- File uploads
- Database exports

**Transformations:**
- Data cleaning and validation
- Format standardization
- Entity extraction
- Quality assessment

---

### Configuration Management

#### `config_validator.py`
Validates configuration files and environment setup.

```bash
python scripts/config_validator.py [--config-dir DIR] [--strict]
```

**Validates:**
- YAML syntax and structure
- Required field presence
- Value range checking
- Cross-reference consistency
- Security configurations

---

## Script Usage Patterns

### Common Development Workflow

```bash
# Setup and validation
python scripts/validate_environment.py --fix
python scripts/smoke_api.py

# Development testing
python scripts/advanced_testing.py --type integration
python scripts/performance_baseline.py --compare

# Pre-deployment
python scripts/security_scan.py --scope all
python scripts/accessibility_audit.py --fix
bash scripts/validate_phase2.sh
```

### Maintenance Workflow

```bash
# Asset management
python scripts/assets_pull.py --verify
python scripts/dependency_upgrade.py --strategy moderate

# Health monitoring
python scripts/health_monitor.py --interval 300
python scripts/performance_baseline.py --create

# Index management
python scripts/rebuild_indices.py --type all --optimize
```

### Deployment Workflow

```bash
# Pre-deployment validation
bash scripts/validate_environment.sh production
python scripts/config_validator.py --strict

# Deployment
python scripts/deploy.py --environment production --rolling

# Post-deployment
python scripts/health_monitor.py --interval 60
python scripts/performance_baseline.py --compare
```

## Script Configuration

### Environment Variables

Scripts respect common environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `STRATMASTER_ENV` | Environment context | `development` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `SCRIPT_CONFIG_DIR` | Script configuration directory | `configs/scripts/` |
| `BACKUP_DIR` | Backup storage location | `backups/` |
| `ASSETS_DIR` | Asset storage location | `assets/` |

### Configuration Files

Many scripts use YAML configuration files in `configs/scripts/`:

- `deployment.yaml` - Deployment configurations
- `testing.yaml` - Testing parameters
- `monitoring.yaml` - Monitoring thresholds
- `security.yaml` - Security scan settings
- `performance.yaml` - Performance benchmarks

## Error Handling and Logging

### Standard Error Codes

All scripts follow consistent error code conventions:

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Network/connectivity error
- `4`: Validation failure
- `5`: Resource unavailable

### Logging

Scripts provide structured logging with configurable levels:

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python scripts/script_name.py

# JSON-formatted logs
LOG_FORMAT=json python scripts/script_name.py
```

## Getting Help

Most scripts provide help information:

```bash
python scripts/script_name.py --help
```

For shell scripts:
```bash
bash scripts/script_name.sh --help
```

## See Also

- [Make Commands](make-commands.md) - Make target reference
- [Operations Guide](../../how-to/operations-guide.md) - Production operations
- [Development Setup](../../how-to/development-setup.md) - Development environment setup
- [Troubleshooting](../../how-to/troubleshooting.md) - Common issues and solutions