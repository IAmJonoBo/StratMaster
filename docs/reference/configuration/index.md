# Configuration Reference

Complete reference for all StratMaster configuration options, including environment variables, YAML configuration files, and runtime settings.

## Organization

### Environment Variables
Runtime configuration through environment variables:
- **[Core Configuration](environment.md#core)** - Database, Redis, basic service settings
- **[Authentication](environment.md#authentication)** - Keycloak, JWT, session management
- **[Observability](environment.md#observability)** - Logging, tracing, metrics
- **[Feature Flags](environment.md#feature-flags)** - Development and experimental features
- **[Performance](environment.md#performance)** - Scaling, timeouts, resource limits

### YAML Configuration Files  
Structured configuration files for complex settings:
- **[Service Configurations](yaml-configs.md#services)** - MCP service settings and policies
- **[AI and ML Models](yaml-configs.md#models)** - Model parameters, retrieval settings
- **[Security and Privacy](yaml-configs.md#security)** - Access control, encryption, data protection
- **[Quality and Evaluation](yaml-configs.md#quality)** - Thresholds, validation rules
- **[Infrastructure](yaml-configs.md#infrastructure)** - Database, networking, deployment

## Configuration Hierarchy

StratMaster uses a layered configuration approach with the following precedence (highest to lowest):

1. **Environment Variables** - Runtime overrides
2. **YAML Configuration Files** - Structured settings
3. **Default Values** - Built-in fallbacks

### Override Examples

```bash
# Environment variable overrides YAML setting
export DATABASE_URL="postgresql://override-host:5432/db"

# YAML overrides default
# configs/database/connection.yaml
url: "postgresql://yaml-host:5432/db"

# Default value used if neither above is set
default_database_url = "postgresql://localhost:5432/stratmaster"
```

## Configuration Validation

### Automatic Validation

All configuration is validated at startup:

```bash
# Validate all configuration
python scripts/config_validator.py

# Validate specific section
python scripts/config_validator.py --section retrieval

# Check configuration in different environment
python scripts/config_validator.py --environment production
```

### Configuration Schema

Configuration follows JSON Schema validation:

```python
from stratmaster_api.schemas import (
    CompressionConfig,
    RetrievalHybridConfig, 
    EvalsThresholds,
    PrivacyConfig
)

# Validate configuration programmatically
config = RetrievalHybridConfig.model_validate(yaml_data)
```

### Debug Configuration Endpoints

!!! warning "Debug Only"
    Configuration endpoints are only available when `STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1`

```bash
# Get configuration for specific section
curl http://localhost:8080/debug/config/retrieval/colbert

# List all configuration sections
curl http://localhost:8080/debug/config/router/models-policy
```

## Configuration Sections

### Core Services

| Section | Purpose | Key Files |
|---------|---------|-----------|
| `router` | Request routing and load balancing | `configs/router/models-policy.yaml` |
| `retrieval` | Vector and hybrid search | `configs/retrieval/colbert.yaml`, `configs/retrieval/splade.yaml` |
| `evals` | Quality assessment thresholds | `configs/evals/thresholds.yaml` |
| `privacy` | Data protection and redaction | `configs/privacy/redaction.yaml` |
| `compression` | Content compression | `configs/compression/llmlingua.yaml` |

### Authentication and Security

| Section | Purpose | Key Files |
|---------|---------|-----------|
| `sso` | Single sign-on configuration | `configs/sso/enterprise-sso-config.yaml` |
| `constitutional` | AI safety and governance | `configs/constitutional/multi_tenant.yaml` |
| `experts` | Expert system configuration | `configs/experts/council-config.yaml` |

### Infrastructure and Operations

| Section | Purpose | Key Files |
|---------|---------|-----------|
| `telemetry` | Monitoring and observability | `configs/telemetry/grafana.yaml` |
| `collaboration` | Real-time collaboration | `configs/collaboration/real_time.yaml` |
| `production` | Production deployment | `configs/production-config-template.yaml` |

## Environment-Specific Configuration

### Development Environment

```bash
# .env.development
STRATMASTER_ENV=development
LOG_LEVEL=DEBUG
ENABLE_DEBUG_ENDPOINTS=1
DATABASE_URL=postgresql://localhost:5432/stratmaster_dev
QDRANT_URL=http://localhost:6333
```

### Staging Environment

```bash
# .env.staging
STRATMASTER_ENV=staging
LOG_LEVEL=INFO
ENABLE_DEBUG_ENDPOINTS=0
DATABASE_URL=postgresql://staging-db:5432/stratmaster_staging
QDRANT_URL=http://qdrant-staging:6333
KEYCLOAK_URL=http://keycloak-staging:8080
```

### Production Environment

```bash
# .env.production (use secrets management in practice)
STRATMASTER_ENV=production
LOG_LEVEL=WARN
ENABLE_DEBUG_ENDPOINTS=0
DATABASE_URL=${DATABASE_URL_FROM_SECRETS}
QDRANT_URL=${QDRANT_URL_FROM_SECRETS}
KEYCLOAK_URL=${KEYCLOAK_URL_FROM_SECRETS}
```

## Configuration Best Practices

### Security

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Validate all inputs** at application startup
4. **Use least-privilege** principle for service accounts
5. **Rotate secrets regularly** using automated tools

### Performance

1. **Profile before optimizing** configuration
2. **Use connection pooling** for databases and external services  
3. **Set appropriate timeouts** to prevent resource exhaustion
4. **Monitor resource usage** and adjust limits accordingly
5. **Cache frequently accessed** configuration data

### Maintainability

1. **Document all settings** with clear descriptions
2. **Use consistent naming** conventions across services
3. **Group related settings** logically
4. **Provide sensible defaults** for all optional settings
5. **Version configuration files** alongside code changes

## Advanced Configuration

### Dynamic Configuration Updates

Some configurations support hot-reload without service restart:

```bash
# Reload routing policies
curl -X POST http://localhost:8083/routing/policies/reload

# Update evaluation thresholds
curl -X PUT http://localhost:8080/config/evals/thresholds \
  -H "Content-Type: application/json" \
  -d '{"accuracy_threshold": 0.95}'
```

### Configuration Templates

Use Jinja2 templates for dynamic configuration generation:

```yaml
# configs/templates/database.yaml.j2
database:
  url: "postgresql://{{ db_user }}:{{ db_password }}@{{ db_host }}:{{ db_port }}/{{ db_name }}"
  pool_size: {{ pool_size | default(10) }}
  max_overflow: {{ max_overflow | default(20) }}
```

```bash
# Generate configuration from template
python scripts/generate_config.py \
  --template configs/templates/database.yaml.j2 \
  --output configs/database.yaml \
  --vars db_user=stratmaster db_host=prod-db-cluster
```

### Configuration Validation in CI

```yaml
# .github/workflows/config-validation.yml
name: Configuration Validation
on: [push, pull_request]
jobs:
  validate-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Configuration
        run: |
          python scripts/config_validator.py --all-environments
          yamllint configs/
          python -m json.tool configs/schemas/*.json
```

## Migration and Upgrades

### Configuration Migration

When upgrading StratMaster versions:

```bash
# Check for configuration changes
python scripts/config_migration.py --from-version 0.1.0 --to-version 0.2.0

# Apply automatic migrations
python scripts/config_migration.py --migrate --backup

# Validate migrated configuration
python scripts/config_validator.py --strict
```

### Backward Compatibility

StratMaster maintains backward compatibility for configuration:

- **Deprecated settings** are supported with warnings
- **New required settings** have reasonable defaults
- **Breaking changes** are documented in release notes
- **Migration scripts** are provided for major version upgrades

## Troubleshooting Configuration Issues

### Common Problems

#### Configuration not loading

```bash
# Check file permissions
ls -la configs/retrieval/colbert.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('configs/retrieval/colbert.yaml'))"

# Check file path resolution
python -c "
import os
from pathlib import Path
print(Path('configs/retrieval/colbert.yaml').resolve().exists())
"
```

#### Environment variables not recognized

```bash
# Check variable is set
echo $DATABASE_URL

# Verify variable name (case-sensitive)
env | grep -i database

# Check variable precedence
python -c "
import os
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
print('All DB vars:', {k:v for k,v in os.environ.items() if 'DB' in k.upper()})
"
```

#### Configuration validation errors

```bash
# Get detailed validation errors
python scripts/config_validator.py --verbose --section retrieval

# Check against schema
python -c "
from stratmaster_api.schemas import RetrievalHybridConfig
import yaml
with open('configs/retrieval/hybrid.yaml') as f:
    data = yaml.safe_load(f)
try:
    config = RetrievalHybridConfig.model_validate(data)
    print('Valid configuration')
except Exception as e:
    print(f'Validation error: {e}')
"
```

## See Also

- **[Environment Variables](environment.md)** - Complete environment variable reference
- **[YAML Configurations](yaml-configs.md)** - Detailed YAML configuration guide
- **[Development Setup](../../how-to/development-setup.md)** - Configuration for development
- **[Deployment Guide](../../how-to/deployment.md)** - Production configuration
- **[Troubleshooting](../../how-to/troubleshooting.md)** - Configuration issue resolution