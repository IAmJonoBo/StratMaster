# Troubleshooting Guide

This guide helps you diagnose and resolve common issues in StratMaster. Issues are organized by component and include step-by-step resolution procedures.

## Quick Diagnostics

### Health Check Commands

```bash
# Overall system health
make health-check

# API smoke test (no network dependencies)
python scripts/smoke_api.py

# Service connectivity
curl -s http://localhost:8080/healthz
curl -s http://localhost:8081/health
curl -s http://localhost:8082/health

# Docker services status
make dev.logs | grep -E "(ERROR|WARN|FATAL)"
docker-compose ps
```

### Common First Steps

1. **Check service status**: `make dev.logs` or `docker-compose ps`
2. **Verify configuration**: `python scripts/config_validator.py`
3. **Test API connectivity**: `curl http://localhost:8080/healthz`
4. **Check resource usage**: `docker stats`
5. **Review error logs**: `make dev.logs | grep ERROR`

## Installation and Setup Issues

### Bootstrap Failures

#### `make bootstrap` fails with pip errors

**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError
pip._vendor.urllib3.exceptions.ReadTimeoutError: Read timed out.
```

**Solutions:**
```bash
# 1. Clear existing environment
make clean

# 2. Try with increased timeout
PIP_TIMEOUT=300 make bootstrap

# 3. Use Docker-based testing instead
make test-docker

# 4. Install dependencies manually
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e packages/api --timeout 300
```

#### Virtual environment issues

**Symptoms:**
```
bash: .venv/bin/python: No such file or directory
```

**Solutions:**
```bash
# Ensure Python 3.13+ is available
python3 --version

# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv

# Use system Python if conda interferes
PYTHONNOUSERSITE=1 python3 -m venv .venv
```

#### Pre-commit hook failures

**Symptoms:**
```
pre-commit command not found
```

**Solutions:**
```bash
# Install pre-commit in virtual environment
.venv/bin/pip install pre-commit

# Reinstall hooks
.venv/bin/pre-commit install

# Skip pre-commit for urgent commits
git commit --no-verify -m "urgent fix"
```

### macOS-Specific Issues

#### AppleDouble files

**Symptoms:**
```
warning: adding embedded git repository
._file found in repository
```

**Solutions:**
```bash
# Clean up AppleDouble files
bash scripts/cleanup_appledouble.sh

# Prevent future occurrences
echo "._*" >> .gitignore
echo ".DS_Store" >> .gitignore
```

#### Homebrew Python conflicts

**Symptoms:**
```
ImportError: cannot import name '_ssl' from '_ssl'
```

**Solutions:**
```bash
# Use system Python
which python3
/usr/bin/python3 -m venv .venv

# Or reinstall Python via Homebrew
brew reinstall python@3.13
brew link --overwrite python@3.13
```

## API Service Issues

### Service Won't Start

#### Port conflicts

**Symptoms:**
```
OSError: [Errno 48] Address already in use: ('127.0.0.1', 8080)
```

**Solutions:**
```bash
# Find process using port 8080
lsof -i :8080
netstat -an | grep 8080

# Kill conflicting process
kill -9 <PID>

# Use different port
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --port 8081
```

#### Import errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'stratmaster_api'
```

**Solutions:**
```bash
# Verify package installation
.venv/bin/pip list | grep stratmaster

# Reinstall package
.venv/bin/pip install -e packages/api --force-reinstall

# Check Python path
export PYTHONPATH=$PWD/packages/api/src:$PYTHONPATH
```

#### Database connection errors

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Start database service
make dev.up  # Starts PostgreSQL in Docker

# Check database connection
docker-compose ps postgres
docker-compose logs postgres

# Test connection manually
psql -h localhost -p 5432 -U stratmaster -d stratmaster
```

### API Endpoint Issues

#### 500 Internal Server Error

**Investigation:**
```bash
# Check API logs
make dev.logs | grep api

# Test with debug enabled
STRATMASTER_ENABLE_DEBUG_ENDPOINTS=1 make api.run

# Check OpenAPI documentation
curl http://localhost:8080/openapi.json
```

**Common causes:**
1. Missing environment variables
2. Database connectivity issues
3. MCP service unavailability
4. Configuration file errors

#### 422 Validation Errors

**Symptoms:**
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solutions:**
```bash
# Check API documentation
open http://localhost:8080/docs

# Validate request format
curl -X POST http://localhost:8080/research/plan \
  -H "Idempotency-Key: test-123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "tenant_id": "demo", 
    "max_sources": 5
  }'
```

#### Missing Idempotency-Key header

**Symptoms:**
```json
{
  "detail": "Missing required header: Idempotency-Key"
}
```

**Solution:**
```bash
# All POST requests need this header
curl -X POST http://localhost:8080/research/plan \
  -H "Idempotency-Key: unique-key-123" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

## Docker and Container Issues

### Container Startup Problems

#### Docker daemon not running

**Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker

# Verify Docker is running
docker version
docker-compose version
```

#### Port binding errors

**Symptoms:**
```
Error starting userland proxy: bind for 0.0.0.0:8080 failed: port is already allocated
```

**Solutions:**
```bash
# Find and stop conflicting containers
docker ps -a
docker stop <container_name>

# Use different ports in docker-compose.override.yml
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  api:
    ports:
      - "8081:8080"
EOF
```

#### Memory/resource constraints

**Symptoms:**
```
docker: Error response from daemon: Mounts denied
```

**Solutions:**
```bash
# Increase Docker memory limits (Docker Desktop)
# Or clean up system resources
docker system prune -a
docker volume prune

# Check available resources
docker system df
```

### Service Communication Issues

#### Services can't reach each other

**Symptoms:**
```
requests.exceptions.ConnectionError: HTTPConnectionPool(host='research-mcp', port=8081)
```

**Investigation:**
```bash
# Check network connectivity
docker-compose exec api ping research-mcp
docker-compose exec api nslookup research-mcp

# Verify service discovery
docker network ls
docker network inspect stratmaster_default
```

**Solutions:**
```bash
# Restart services with network recreation
make dev.down
docker network prune
make dev.up

# Check service definitions in docker-compose.yml
# Ensure services are on same network
```

#### DNS resolution failures

**Symptoms:**
```
Name or service not known: research-mcp
```

**Solutions:**
```bash
# Use IP addresses temporarily
docker-compose exec api getent hosts research-mcp

# Or specify external names
echo "127.0.0.1 research-mcp" >> /etc/hosts  # Not recommended

# Fix docker-compose networks
docker-compose down
docker-compose up --force-recreate
```

## Database Issues

### PostgreSQL Connection Problems

#### Connection refused

**Symptoms:**
```
psycopg2.OperationalError: connection to server at "localhost", port 5432 failed
```

**Investigation:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres
docker-compose logs postgres

# Test direct connection
docker-compose exec postgres psql -U stratmaster -d stratmaster
```

**Solutions:**
```bash
# Restart PostgreSQL service
docker-compose restart postgres

# Check configuration
docker-compose exec postgres cat /var/lib/postgresql/data/postgresql.conf

# Clear data and restart fresh (WARNING: loses data)
docker-compose down -v
make dev.up
```

#### Authentication failed

**Symptoms:**
```
FATAL: password authentication failed for user "stratmaster"
```

**Solutions:**
```bash
# Check environment variables
echo $DATABASE_URL
docker-compose exec api env | grep DATABASE

# Reset PostgreSQL password
docker-compose exec postgres psql -U postgres
# Then: ALTER USER stratmaster PASSWORD 'newpassword';

# Update connection string
export DATABASE_URL="postgresql://stratmaster:newpassword@localhost:5432/stratmaster"
```

### Vector Database (Qdrant) Issues

#### Qdrant service unavailable

**Symptoms:**
```
requests.exceptions.ConnectionError: Failed to establish a new connection to qdrant:6333
```

**Investigation:**
```bash
# Check Qdrant status
docker-compose ps qdrant
docker-compose logs qdrant

# Test direct connection
curl http://localhost:6333/collections
```

**Solutions:**
```bash
# Restart Qdrant
docker-compose restart qdrant

# Clear Qdrant data if corrupted
docker-compose down
docker volume rm stratmaster_qdrant_data
make dev.up
```

#### Collection errors

**Symptoms:**
```
QdrantException: Collection 'documents' not found
```

**Solutions:**
```bash
# List existing collections
curl http://localhost:6333/collections

# Create missing collections
python -c "
from qdrant_client import QdrantClient
client = QdrantClient('localhost', port=6333)
# Create your collections here
"

# Or reinitialize database
python scripts/init_vector_db.py
```

## MCP Service Issues

### Research MCP Problems

#### Service won't start

**Symptoms:**
```
ModuleNotFoundError: No module named 'research_mcp'
```

**Solutions:**
```bash
# Install research MCP package
.venv/bin/pip install -e packages/mcp-servers/research-mcp

# Check PYTHONPATH
export PYTHONPATH=$PWD/packages/mcp-servers/research-mcp/src:$PYTHONPATH

# Run with explicit path
cd packages/mcp-servers/research-mcp
python -m research_mcp.app
```

#### Web crawling failures

**Symptoms:**
```
HTTP 403 Forbidden
requests.exceptions.Timeout
```

**Investigation:**
```bash
# Check robots.txt compliance
curl http://target-site.com/robots.txt

# Test with different user agent
curl -H "User-Agent: StratMaster-Research/1.0" http://target-site.com

# Check rate limiting
grep -i "rate" logs/research-mcp.log
```

**Solutions:**
```bash
# Adjust crawling configuration
# configs/research/quality-thresholds.yaml
respect_robots_txt: true
request_delay: 2.0
max_concurrent_requests: 3

# Use proxy if needed
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

### Knowledge MCP Problems

#### Vector search failures

**Symptoms:**
```
RuntimeError: CUDA out of memory
ModuleNotFoundError: No module named 'torch'
```

**Solutions:**
```bash
# Check GPU availability
nvidia-smi

# Use CPU-only mode
export CUDA_VISIBLE_DEVICES=""

# Install missing dependencies
.venv/bin/pip install torch torchvision

# Reduce batch size in config
# configs/knowledge/retrieval-models.yaml
batch_size: 8  # Reduce from 32
```

#### Index building failures

**Symptoms:**
```
FileNotFoundError: Index file not found
PermissionError: Cannot write to index directory
```

**Solutions:**
```bash
# Create index directories
mkdir -p data/indices/colbert data/indices/splade

# Fix permissions
chmod -R 755 data/

# Rebuild indices
make index.colbert
make index.splade

# Verify index files
ls -la data/indices/
```

## Performance Issues

### Slow API Responses

#### High response times

**Investigation:**
```bash
# Profile API performance
python scripts/performance_benchmark.py --target http://localhost:8080

# Check database slow queries
docker-compose exec postgres psql -U stratmaster -d stratmaster -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;"

# Monitor resource usage
docker stats
```

**Solutions:**
```bash
# Increase worker processes
# Modify docker-compose.yml or use environment variable
export API_WORKERS=4

# Add database indices
python scripts/optimize_database.py

# Enable caching
export REDIS_URL=redis://localhost:6379
```

#### Memory leaks

**Symptoms:**
```
MemoryError: Unable to allocate memory
```

**Investigation:**
```bash
# Monitor memory usage over time
while true; do
  docker stats --no-stream | grep api
  sleep 30
done

# Profile memory usage
python -m memory_profiler scripts/test_memory.py
```

**Solutions:**
```bash
# Restart services periodically
# Add health checks with memory limits in docker-compose.yml

# Optimize model loading
export MODEL_CACHE_SIZE=100MB
export BATCH_SIZE=16

# Use memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

### Database Performance Issues

#### Slow queries

**Investigation:**
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- Analyze slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC;
```

**Solutions:**
```sql
-- Add missing indices
CREATE INDEX CONCURRENTLY idx_table_column ON table_name(column);

-- Update statistics
ANALYZE;

-- Optimize configuration
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

## Network and Connectivity Issues

### External API Access Problems

#### SSL/TLS certificate errors

**Symptoms:**
```
requests.exceptions.SSLError: certificate verify failed
```

**Solutions:**
```bash
# Update CA certificates
apt-get update && apt-get install -y ca-certificates

# Disable SSL verification (not recommended for production)
export PYTHONHTTPSVERIFY=0

# Use specific CA bundle
export REQUESTS_CA_BUNDLE=/path/to/cacert.pem
```

#### Proxy configuration

**Symptoms:**
```
ProxyError: Cannot connect to proxy
```

**Solutions:**
```bash
# Configure proxy settings
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1,.local

# Configure in Docker
# docker-compose.yml
services:
  api:
    environment:
      - HTTP_PROXY=http://proxy.company.com:8080
      - HTTPS_PROXY=http://proxy.company.com:8080
```

#### DNS resolution issues

**Symptoms:**
```
gaierror: Name or service not known
```

**Solutions:**
```bash
# Check DNS configuration
cat /etc/resolv.conf

# Test DNS resolution
nslookup google.com
dig google.com

# Configure custom DNS in Docker
# docker-compose.yml
services:
  api:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

## Configuration Issues

### Environment Variables

#### Missing variables

**Symptoms:**
```
KeyError: 'DATABASE_URL'
ValueError: QDRANT_URL not set
```

**Investigation:**
```bash
# Check environment variables
env | grep STRATMASTER
docker-compose exec api env | grep -E "(DATABASE|QDRANT|REDIS)"

# Validate configuration
python scripts/config_validator.py --environment development
```

**Solutions:**
```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://stratmaster:password@postgres:5432/stratmaster
QDRANT_URL=http://qdrant:6333
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
EOF

# Source environment file
set -a && source .env && set +a
```

### YAML Configuration Issues

#### Invalid YAML syntax

**Symptoms:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solutions:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('configs/file.yaml'))"

# Use yamllint for comprehensive checking
.venv/bin/pip install yamllint
yamllint configs/

# Fix common issues
# - Ensure proper indentation (spaces, not tabs)
# - Quote strings with special characters
# - Use proper list syntax
```

#### Configuration not found

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'configs/retrieval/colbert.yaml'
```

**Solutions:**
```bash
# Check configuration files exist
find configs/ -name "*.yaml" -type f

# Copy from templates if needed
cp configs/retrieval/colbert.yaml.template configs/retrieval/colbert.yaml

# Download required configurations
python scripts/assets_pull.py --verify
```

## Testing Issues

### Test Failures

#### Import errors in tests

**Symptoms:**
```
ImportError: attempted relative import with no known parent package
```

**Solutions:**
```bash
# Run tests from project root
cd /path/to/StratMaster
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest

# Use test-fast for development
make test-fast

# Set PYTHONPATH explicitly
export PYTHONPATH=$PWD/packages/api/src:$PYTHONPATH
python -m pytest
```

#### Database test errors

**Symptoms:**
```
psycopg2.OperationalError: database "test_stratmaster" does not exist
```

**Solutions:**
```bash
# Ensure test database exists
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE test_stratmaster;"

# Use test configuration
export DATABASE_URL="postgresql://stratmaster:password@postgres:5432/test_stratmaster"

# Run tests with database setup
python scripts/setup_test_db.py
make test
```

#### Docker test problems

**Symptoms:**
```
docker: Error response from daemon: pull access denied
```

**Solutions:**
```bash
# Build local images first
docker build -t python:3.13-slim .

# Use test-docker target
make test-docker

# Or run tests locally
make test-fast
```

## Getting Additional Help

### Log Collection

```bash
# Collect all relevant logs
mkdir -p debug_logs/$(date +%Y%m%d_%H%M%S)
make dev.logs > debug_logs/$(date +%Y%m%d_%H%M%S)/services.log
docker-compose ps > debug_logs/$(date +%Y%m%d_%H%M%S)/containers.txt
env | grep -E "(STRATMASTER|DATABASE|QDRANT)" > debug_logs/$(date +%Y%m%d_%H%M%S)/env.txt
```

### System Information

```bash
# Gather system information
cat > debug_info.txt << EOF
System: $(uname -a)
Python: $(python3 --version)
Docker: $(docker --version)
Docker Compose: $(docker-compose --version)
Git: $(git --version)
Free Memory: $(free -h)
Disk Space: $(df -h)
EOF
```

### Health Report

```bash
# Generate comprehensive health report
python scripts/health_report.py --output health_report.json
```

### Community Resources

- **GitHub Issues**: [Report bugs and request features](https://github.com/IAmJonoBo/StratMaster/issues)
- **GitHub Discussions**: [Ask questions and get help](https://github.com/IAmJonoBo/StratMaster/discussions)
- **Documentation**: [Full documentation](https://iamjonobo.github.io/StratMaster/)

### Creating Bug Reports

When reporting issues, include:

1. **Environment details**: OS, Python version, Docker version
2. **Steps to reproduce**: Exact commands that trigger the issue
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens  
5. **Logs and error messages**: Full error output
6. **Configuration**: Relevant config files and environment variables

## See Also

- [Development Setup](development-setup.md) - Initial setup guide
- [Operations Guide](operations-guide.md) - Production operations
- [FAQ](faq.md) - Frequently asked questions
- [API Reference](../reference/api/) - Complete API documentation