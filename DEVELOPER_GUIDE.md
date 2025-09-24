# StratMaster Developer Quick Reference

## 🚀 Quick Start Commands

```bash
# Bootstrap environment (creates .venv, installs dependencies)
make bootstrap

# Run all API tests (should show 42+ passing tests)  
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -v

# Start API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080

# Run performance benchmark
curl -X POST http://127.0.0.1:8080/performance/benchmark

# View API documentation
open http://127.0.0.1:8080/docs
```

## 📊 Key Endpoints

### Export Integrations (Real APIs - No Mocks)
```bash
# Export to Notion (dry run)
curl -X POST http://127.0.0.1:8080/export/notion \
  -H "Content-Type: application/json" \
  -d '{
    "notion_token": "YOUR_TOKEN",
    "parent_page_id": "PAGE_ID", 
    "strategy_id": "test_strategy",
    "dry_run": true
  }'

# Export to Trello  
curl -X POST http://127.0.0.1:8080/export/trello \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_KEY",
    "api_token": "YOUR_TOKEN",
    "strategy_id": "test_strategy", 
    "dry_run": true
  }'

# Export to Jira
curl -X POST http://127.0.0.1:8080/export/jira \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "https://your-domain.atlassian.net",
    "username": "your-email@domain.com",
    "api_token": "YOUR_TOKEN",
    "project_key": "PROJECT",
    "strategy_id": "test_strategy",
    "dry_run": true
  }'
```

### Performance Monitoring
```bash
# Run comprehensive benchmark
curl -X POST http://127.0.0.1:8080/performance/benchmark

# Check performance health
curl http://127.0.0.1:8080/performance/health
```

### Strategy Operations
```bash
# Generate strategy brief
curl -X POST http://127.0.0.1:8080/strategy/generate-brief \
  -H "Content-Type: application/json" \
  -d '{
    "objectives": ["Increase market share"],
    "assumptions": ["Market is growing"],
    "context": "Technology sector"
  }'
```

### Debate & Learning
```bash
# Escalate debate to expert
curl -X POST http://127.0.0.1:8080/debate/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "debate_id": "debate_123",
    "expert_type": "domain_specialist",
    "context": "Need expert opinion on market analysis"
  }'

# Get learning metrics
curl http://127.0.0.1:8080/debate/learning/metrics
```

## 🔧 Development Tools

### Testing Commands
```bash
# Run all tests
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -v

# Run specific test file
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/test_comprehensive.py -v

# Run tests with coverage
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ --cov=stratmaster_api

# Run only export integration tests
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/test_comprehensive.py::TestExportIntegrations -v
```

### Quality Checks
```bash
# Run pre-commit hooks
.venv/bin/pre-commit run --all-files

# Format code (if available)
.venv/bin/black packages/api/src/

# Type checking (if mypy available)
.venv/bin/mypy packages/api/src/stratmaster_api/
```

### Docker Development
```bash
# Start full stack (if Docker available)
make dev.up

# View logs
make dev.logs

# Stop stack
make dev.down
```

## 📈 Quality Gates & Monitoring

### Performance Benchmarks (From Upgrade.md)
- **Gateway Latency**: p50 < 5ms, p95 < 15ms
- **Routing Decision**: p50 < 20ms  
- **RAGAS Faithfulness**: ≥ 0.8
- **RAGAS Precision/Recall**: ≥ 0.7
- **Retrieval Improvement**: ≥ 10% NDCG@10
- **Export Idempotency**: Re-runs update, don't duplicate
- **End-to-End Tracing**: 100% LLM calls traced

### Test Expectations
- **Original API Tests**: 23/23 must pass
- **Comprehensive Tests**: 19+ should pass (some endpoints may be 404)
- **Total Coverage**: 42+ passing tests expected
- **Integration Tests**: Export, performance, ML, observability

## 🏗️ Architecture Components

### Core Services
- **FastAPI App**: Main API server (`stratmaster_api.app:create_app`)
- **Export Integrations**: Notion, Trello, Jira clients (real APIs)
- **Performance Monitor**: Benchmarking and quality gates
- **Collaboration**: Yjs CRDT WebSocket server (components ready)
- **Security**: OIDC/Keycloak authentication (framework ready)

### Data Systems
- **PostgreSQL**: Primary data store (when available)
- **Redis**: Caching and collaboration state
- **Qdrant**: Vector embeddings
- **OpenSearch**: Full-text and sparse retrieval
- **NebulaGraph**: Knowledge graph

### ML/AI Pipeline
- **scikit-learn 1.7.2**: Real ML predictions (no mocks)
- **Debate Learning**: Outcome prediction and model retraining
- **Evidence Processing**: Multi-format document parsing
- **Constitutional AI**: Multi-agent debate with critic validation

## 🚨 Troubleshooting

### Common Issues

**Tests Failing?**
```bash
# Ensure bootstrap completed successfully
make bootstrap

# Check Python environment
PYTHONNOUSERSITE=1 .venv/bin/python --version  # Should be 3.11+
```

**Import Errors?**
```bash
# Verify API package is installed in editable mode
.venv/bin/pip list | grep stratmaster-api
```

**Server Won't Start?**
```bash
# Check for port conflicts
lsof -i :8080

# Start with explicit factory mode
.venv/bin/uvicorn stratmaster_api.app:create_app --factory
```

**Export APIs Not Working?**
```bash
# Verify integrations are available
python -c "from stratmaster_api.routers.export import INTEGRATIONS_AVAILABLE; print(INTEGRATIONS_AVAILABLE)"
# Should print: True
```

### Network Issues
Some package installations may timeout in restricted environments. The core functionality should work with the base installation from `make bootstrap`.

## 📚 Key Files & Locations

### Implementation Files
- **Main App**: `packages/api/src/stratmaster_api/app.py`
- **Export System**: `packages/api/src/stratmaster_api/integrations/`
- **Performance**: `packages/api/src/stratmaster_api/performance.py`
- **Tests**: `packages/api/tests/`

### Configuration
- **Dependencies**: `packages/api/pyproject.toml`
- **Docker**: `docker-compose.yml`
- **Kubernetes**: `helm/stratmaster-api/`

### Documentation  
- **Implementation Status**: `Upgrade.md`
- **Technical Details**: `Scratch.md`
- **Summary**: `IMPLEMENTATION_SUMMARY.md`

## 🎯 Next Development Steps

1. **Complete OIDC Integration**: Wire Keycloak components to FastAPI middleware
2. **Deploy WebSocket Server**: Enable real-time collaboration  
3. **Add External Data**: LMSYS Arena/MTEB integration for model recommender
4. **Performance Optimization**: Advanced caching and response times
5. **Production Deployment**: Kubernetes, monitoring, scaling

---

*Quick Reference Version: 1.0*  
*Last Updated: December 2024*