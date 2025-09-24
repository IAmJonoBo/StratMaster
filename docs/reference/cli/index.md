# CLI Reference

This section provides comprehensive documentation for all command-line tools, scripts, and Make targets available in StratMaster.

## Organization

### Make Targets
Make targets are the primary development interface, organized by functionality:
- **[Core Development](make-commands.md#development)** - Bootstrap, test, run services
- **[Docker Operations](make-commands.md#docker)** - Container management and full-stack deployment
- **[Quality Assurance](make-commands.md#quality)** - Linting, formatting, security scanning
- **[Dependencies](make-commands.md#dependencies)** - Package management and upgrades
- **[Specialized](make-commands.md#specialized)** - Index building, schema generation

### Scripts
Utility scripts for automation and advanced operations:
- **[Development Scripts](scripts.md#development)** - Setup, testing, and validation utilities
- **[Deployment Scripts](scripts.md#deployment)** - Production deployment and management
- **[Maintenance Scripts](scripts.md#maintenance)** - System maintenance and monitoring

## Quick Reference

### Essential Commands

```bash
# Bootstrap development environment
make bootstrap

# Run API locally  
make api.run

# Run full stack
make dev.up

# Run tests
make test

# Code quality checks
make lint
make format
```

### Service Management

```bash
# Individual services
make api.run                    # Gateway API on :8080
make research-mcp.run           # Research MCP on :8081
make expertise-mcp.run          # Expertise MCP on :8082

# Docker stack  
make dev.up                     # Start all services
make dev.down                   # Stop all services
make dev.logs                   # View service logs
```

### Development Workflow

```bash
# Setup
make bootstrap                  # Create venv and install dependencies
make precommit-install          # Install git hooks

# Development cycle
make test                       # Run test suite
make lint                       # Check code quality  
make format                     # Auto-format code
make precommit                  # Run all pre-commit checks

# Advanced testing
make test.integration           # Integration test suite
make test.load                  # Load testing
make test.contract              # Contract testing
```

## Navigation

- **[Make Commands](make-commands.md)** - Complete Make target reference with examples
- **[Scripts](scripts.md)** - Utility scripts and automation tools

## Getting Help

Each Make target includes help documentation:
```bash
make help                       # Show all available targets
```

For script-specific help:
```bash  
python scripts/script_name.py --help
```

## Environment Variables

Common environment variables that affect CLI behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONNOUSERSITE` | `1` | Disable user site-packages for clean installs |
| `PIP_DISABLE_PIP_VERSION_CHECK` | `1` | Skip pip version warnings |
| `STRATMASTER_ENABLE_DEBUG_ENDPOINTS` | `""` | Enable debug API endpoints |
| `DOCKER_COMPOSE_FILE` | `docker-compose.yml` | Docker Compose configuration file |

## See Also

- [Development Setup](../../how-to/development-setup.md) - Complete development environment setup
- [Operations Guide](../../how-to/operations-guide.md) - Production operations and maintenance
- [Troubleshooting](../../how-to/troubleshooting.md) - Common CLI issues and solutions