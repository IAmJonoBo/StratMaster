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

---

## 🗂 Roadmap Issue Automation Suite

This repository manages roadmap issues from a single canonical Markdown file: `ISSUES.md`. Creation, updates, and closure are automated via a consistent toolchain safe for both local developers and remote automation (e.g., GitHub Copilot agents in CI).

### Components
| Artifact | Purpose |
|----------|---------|
| `ISSUES.md` | Declarative issue definitions (single source of truth) |
| `issue_suite.config.yaml` | Configuration (patterns, milestones, output paths, AI settings) |
| External `issuesuite` package | Installed dependency providing CLI (validate, sync, export, summary, schema) |
| `.github/workflows/validate-issues.yml` | CI validation + dry-run + artifact pipeline |
| `issue_suite.config.yaml` | Local configuration consumed by the external CLI |

### Unified CLI (External)
All functionality is now provided by the external IssueSuite distribution. Typical commands:
```bash
ISSUES_SUITE_MOCK=1 issuesuite validate --config issue_suite.config.yaml --skip-label-exists --skip-milestone-exists
ISSUES_SUITE_MOCK=1 issuesuite sync --dry-run --update --config issue_suite.config.yaml --summary-json issues_summary.json
ISSUES_SUITE_MOCK=1 issuesuite export --pretty --config issue_suite.config.yaml --output issues_export.json
ISSUES_SUITE_MOCK=1 issuesuite summary --config issue_suite.config.yaml
ISSUES_SUITE_MOCK=1 issuesuite schema --config issue_suite.config.yaml --stdout > issue_change_summary.schema.json
```

### Make Targets (Convenience)
Instead of manual commands you can use:
```bash
make issuesuite.install    # install (PyPI then source fallback)
make issuesuite.validate   # validate (mock by default)
make issuesuite.sync.dry   # dry-run sync + summary JSON
make issuesuite.schema     # generate schemas
make issuesuite.summary    # human-readable summary
```
Override mock mode by exporting `ISSUES_SUITE_MOCK=` (empty) before running a target.

Fallback logic: If PyPI is temporarily unavailable the Make target clones the upstream repository and installs from source.

### Machine-Readable Change Summary
`sync` writes a JSON summary (default `issues_summary.json` or custom via `--summary-json`):
```json
{
  "schemaVersion": 1,
  "generated_at": "2025-09-25T12:34:56Z",
  "dry_run": true,
  "totals": {"specs": 42, "created": 3, "updated": 5, "closed": 1, "skipped": 33},
  "changes": {
    "created": [{"external_id": "012", "title": "Issue 012: ...", "labels": ["meta:roadmap"], "milestone": "M1: Real-Time Foundation", "hash": "abcd1234"}],
    "updated": [{"external_id": "023", "number": 145, "prev_hash": "deadbeef", "new_hash": "1a2b3c4d", "diff": {"labels_added": ["new"], "labels_removed": ["old"], "body_changed": true, "body_diff": ["@@ -1 +1 @@", "-old", "+new"]}}],
    "closed": [{"external_id": "005", "number": 101}]
  }
}
```

### JSON Schemas
Generated via:
```bash
issuesuite schema --config issue_suite.config.yaml --stdout > issue_change_summary.schema.json
```
Outputs:
| File | Defines |
|------|---------|
| `issue_export.schema.json` | Schema for full export array |
| `issue_change_summary.schema.json` | Schema for sync summary JSON |

### Configuration Highlights (`issue_suite.config.yaml`)
| Key | Meaning |
|-----|---------|
| `source.id_pattern` | Regex external IDs must match |
| `source.milestone_pattern` | Enforced milestone naming regex |
| `defaults.inject_labels` | Auto-added labels to every issue (idempotent) |
| `behavior.truncate_body_diff` | Max unified diff lines stored in summary |
| `ai.emit_change_events` | Toggle summary JSON emission |
| `github.project.enable` | Enable future project board syncing |

### Diff Summarization
Updates include structured diff keys (`labels_added`, `labels_removed`, `milestone_from/to`, `body_diff`) enabling AI agents to reason about changes without scraping textual logs.

### Status Handling
If an issue has `status: closed` metadata, the `status:closed` label is injected automatically (and validation enforces presence). With `--respect-status`, issues are closed on GitHub.

### Migration Notes
- Legacy custom Python scripts have been removed in favor of the external IssueSuite CLI.
- CI should invoke `issuesuite` directly.

### AI / Automation Usage Pattern
1. `validate` (fail fast)
2. `sync --dry-run --update --summary-json summary.json`
3. Parse `summary.json` for targeted follow-up actions (e.g., comment, label governance)
4. `export` + `report` to build dashboards / progress snapshots.

Example (pseudo-code for an agent):
```python
import json, subprocess
subprocess.run(['issuesuite','sync','--dry-run','--update','--config','issue_suite.config.yaml','--summary-json','summary.json'],check=True)
data=json.loads(open('summary.json').read())
for created in data['changes']['created']:
  print('Created candidate:', created['external_id'], created['title'])
```

### Key Files Generated
| File | Purpose |
|------|---------|
| `.issues_sync_state.json` | Stores hashes (drift detection) |
| `.issues_sync.lock` | Prevents concurrent writers |
| `issues_mapping.json` | External ID -> GitHub issue number mapping |

### Legacy Wrapper
Removed; use the `issuesuite` CLI directly.

### Hash Drift Rules
Any change to title, body, labels, or milestone regenerates the hash and triggers update when `--update` is used.

### Recommended CI Flow
1. Validate (`issuesuite validate --config issue_suite.config.yaml --skip-label-exists --skip-milestone-exists`)
2. Dry-run sync (`issuesuite sync --dry-run --update --config issue_suite.config.yaml --summary-json issues_summary.json`)
3. Export (`issuesuite export --pretty --config issue_suite.config.yaml --output issues_export.json`)
4. Optional schema validation / reporting

### Extending
Enhancements should be proposed upstream in the IssueSuite repository; bump dependency version here after updates.

### Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| Lock file persists | Previous crash | Remove `.issues_sync.lock` if safe |
| Expected update missing | Forgot `--update` | Re-run with flag |
| Validation fails missing label | Not created yet | Use `--preflight` |

### Automation Guidance (Remote Copilot)
Remote agents must never mutate without first:
1. Running validation.
2. Running a dry-run sync and presenting diff summary.
3. Proceeding with real sync only after human or policy approval.

---

### 🤖 AI Schema Usage

Two JSON Schemas are emitted for machine reasoning / contract validation:

| Schema File | Description | Typical Consumer Action |
|-------------|-------------|-------------------------|
| `issue_export.schema.json` | Array schema describing each declarative issue object exported via `export` | Validate full roadmap export; feed into embedding or planning models |
| `issue_change_summary.schema.json` | Object schema describing a single sync run and its categorized change sets | Triage automation, selective follow-up (commenting, assignment) |

Recommended agent validation snippet (Python):
```python
import json, jsonschema
export = json.load(open('issues_export.json'))
schema = json.load(open('issue_export.schema.json'))
jsonschema.validate(export, schema)
summary = json.load(open('issues_summary.json'))
jsonschema.validate(summary, json.load(open('issue_change_summary.schema.json')))
for created in summary['changes']['created']:
    print('New issue candidate:', created.get('external_id'))
```

Minimal OpenAI function tool description example:
```json
{
  "name": "get_issue_change_summary",
  "description": "Returns structured change summary from last declarative roadmap sync.",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

Design principles for AI consumption:
1. Deterministic hashes enable fast drift detection without re-fetching bodies.
2. Bounded diff size (`truncate_body_diff`) protects token budgets.
3. Stable external IDs decouple local planning from GitHub issue numbers.
4. Schemas versioned (`schemaVersion`) to allow non-breaking additive fields.

When extending schemas, always:
1. Add new fields as optional.
2. Increment `schemaVersion` only for backward-incompatible changes.
3. Update this guide and re-run `python scripts/issue_suite.py schema`.

---
