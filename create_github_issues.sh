- Track accessibility and performance metrics via dashboards.

EOF

if gh issue create   --title "Issue 005: Phase 3 UX Quality Gates"   --body-file "issue_5_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P1-important"   --milestone "M2: Performance & Validation"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_5_body.txt"
fi
echo ""

#!/usr/bin/env bash
set -euo pipefail

# DEPRECATED WRAPPER (2025-09): internal IssueSuite implementation removed.
# This script now forwards to the external 'issuesuite' CLI.
# Prefer calling the CLI directly:
#   issuesuite sync --update --respect-status --preflight --config issue_suite.config.yaml --summary-json issues_summary.json

usage() {
    cat <<'EOF'
Deprecated: create_github_issues.sh
Usage:
    ./create_github_issues.sh [--validate|--validate-strict] [issuesuite sync flags]

Examples:
    Validate only:
        ./create_github_issues.sh --validate
    Dry-run sync:
        ./create_github_issues.sh --validate --dry-run --update --config issue_suite.config.yaml --summary-json issues_summary.json

All non-validation flags are forwarded to:
    issuesuite sync (unless only validation requested)

Environment:
    Requires authenticated GitHub CLI only if you perform a real (non-mock, non-dry-run) sync.
EOF
}

RUN_VALIDATE=0
STRICT=0
PASSTHRU=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --validate) RUN_VALIDATE=1 ;;
        --validate-strict) RUN_VALIDATE=1; STRICT=1 ;;
        -h|--help) usage; exit 0 ;;
        *) PASSTHRU+=("$1") ;;
    esac
    shift
done

if ! command -v issuesuite >/dev/null 2>&1; then
    echo "[error] issuesuite CLI not found in PATH. Install with: pip install 'issuesuite>=0.1.4'" >&2
    exit 1
fi

if [[ $RUN_VALIDATE -eq 1 ]]; then
    echo "[wrapper] Running issuesuite validate..."
    set +e
    if [[ $STRICT -eq 1 ]]; then
        issuesuite validate --config issue_suite.config.yaml --strict || VALID_RC=$?
    else
        issuesuite validate --config issue_suite.config.yaml || VALID_RC=$?
    fi
    set -e
    if [[ ${VALID_RC:-0} -ne 0 ]]; then
        echo "[wrapper] Validation failed (code $VALID_RC). Aborting." >&2
        exit $VALID_RC
    fi
    if [[ ${#PASSTHRU[@]} -eq 0 ]]; then
        echo "[wrapper] Validation successful."
        exit 0
    fi
fi

echo "[wrapper] Delegating to: issuesuite sync ${PASSTHRU[*]}"
issuesuite sync "${PASSTHRU[@]}"
echo "[wrapper] Completed."
exit 0
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_9_body.txt"
echo ""

# Issue 10: Issue 010: Advanced Knowledge Graph Reasoning
echo "Creating issue 10/21: Issue 010: Advanced Knowledge Graph Reasoning"
cat > "issue_10_body.txt" << 'EOF'
# Issue 010: Advanced Knowledge Graph Reasoning

## Summary
Implement the knowledge reasoning enhancements in [Implementation Plan §Advanced Knowledge Graph Reasoning](../IMPLEMENTATION_PLAN.md#advanced-knowledge-graph-reasoning).

## Current State
- Knowledge pipeline performs ingestion and hybrid search but lacks causal inference and advanced analytics.【F:packages/knowledge/src/knowledge/pipeline.py†L1-L100】

## Proposed Solution
1. Extend knowledge package with graph analytics (PageRank, community detection) and NebulaGraph integrations.
2. Integrate causal inference libraries (DoWhy/EconML) to compute causal scores stored alongside graph edges.
3. Expose reasoning APIs and UI overlays behind `ENABLE_KNOWLEDGE_REASONING`.

## Feature Flag
- `ENABLE_KNOWLEDGE_REASONING` (default `false`).

## Acceptance Criteria
- Graph analytics outputs persisted with metadata and surfaced via API.
- Causal reasoning endpoints return narratives with supporting evidence; strategy engine can consume causal weights.
- UI visualises causal graph overlays when flag enabled.
- Documentation covers algorithms, interpretation guidance, and privacy considerations.

## Dependencies
- NebulaGraph cluster access and analytics libraries (networkx, dowhy).
- Strategy engine integration for consuming causal insights.

## Testing Plan
- Unit tests for analytics algorithms using deterministic synthetic graphs.
- Contract tests for reasoning API schema and latency budgets.
- Integration tests ensuring strategy recommendations incorporate causal adjustments without regression.

## Rollout & Monitoring
- Start with analytics-only reports, then enable UI overlays.
- Monitor computation latency, cache hit rates, and user adoption metrics.

EOF

if gh issue create   --title "Issue 010: Advanced Knowledge Graph Reasoning"   --body-file "issue_10_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P2-enhancement"   --milestone "M3: Advanced Analytics"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_10_body.txt"
echo ""

# Issue 11: 01 Sprint0 Mobilize  Baseline  Architecture Assessment  Dependency Audit
echo "Creating issue 11/21: 01 Sprint0 Mobilize  Baseline  Architecture Assessment  Dependency Audit"
if $RETRY_ONLY_FAILED && issue_exists "01 Sprint0 Mobilize  Baseline  Architecture Assessment  Dependency Audit"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_11_body.txt" << 'EOF'
# [SPRINT-0] Mobilize & Baseline - Architecture Assessment & Dependency Audit

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

## Epic Overview
Implement Sprint 0 of the SM_REFACTOR_STRAT.md program: Mobilize & Baseline activities (Weeks 1-3) to capture current architecture, define modularization strategy, and establish tooling baselines.

## Sprint 0 Objectives
- Capture current architecture, runtime, and dependency graph
- Define modularization strategy and target operating model
- Establish tooling baselines for testing and virtual environment setup

## Issues / Epics from SM_REFACTOR_STRAT.md
1. `ARCH-001` Architecture Assessment & Domain Mapping
2. `DEP-001` Dependency Inventory & Risk Classification
3. `QA-001` Test Coverage Benchmarking & Test Data Audit
4. `OPS-001` CI/CD & Virtual Environment Baseline Analysis

## Key Activities Checklist
- [ ] **Architecture Discovery**: Run automated architecture discovery scripts; document data flow diagrams
- [ ] **Dependency Analysis**: Classify dependencies by criticality, EOL status, and upgrade path
- [ ] **Test Analysis**: Analyze test suites for coverage, flakiness, and runtime
- [ ] **Environment Baseline**: Measure setup time for current virtual environments and Docker images

## Quality Gates
- [ ] **ADR Creation**: Architecture decision records (ADR) for module boundaries drafted
- [ ] **Security Review**: Dependency risk matrix approved by security
- [ ] **Coverage Baseline**: Baseline coverage report validated (unit, integration, end-to-end)
- [ ] **DevOps Audit**: CI/CD audit report reviewed by DevOps guild

## Deliverables
- [ ] **Baseline Architecture Workbook**: Complete current state documentation + ADR backlog
- [ ] **Dependency Audit Report**: Upgrade priority backlog with risk assessment
- [ ] **Test Coverage Heatmap**: Coverage metrics + data quality findings
- [ ] **CI/CD Benchmark Report**: Environment setup performance baseline

## Implementation Tasks

### ARCH-001: Architecture Assessment & Domain Mapping
- [ ] Document current module boundaries and dependencies
- [ ] Create data flow diagrams for key user journeys
- [ ] Identify modularization opportunities and anti-patterns
- [ ] Draft ADRs for proposed module boundaries

### DEP-001: Dependency Inventory & Risk Classification
- [ ] Catalog all 29 packages and their dependency trees
- [ ] Classify dependencies by criticality (core, optional, dev)
- [ ] Identify EOL packages and security vulnerabilities
- [ ] Create upgrade priority matrix

### QA-001: Test Coverage Benchmarking & Test Data Audit
- [ ] Generate comprehensive test coverage report
- [ ] Analyze test execution times and identify flaky tests
- [ ] Audit test data quality and maintainability
- [ ] Document testing gaps and improvement opportunities

### OPS-001: CI/CD & Virtual Environment Baseline Analysis
- [ ] Measure current CI/CD pipeline performance
- [ ] Benchmark virtual environment setup times
- [ ] Document Docker image sizes and build times
- [ ] Identify optimization opportunities

## Success Criteria
- Complete understanding of current architecture documented
- Clear modularization strategy defined with stakeholder buy-in
- Baseline metrics established for all quality improvements
- Foundation ready for Sprint 1 implementation work

## Timeline
**Duration:** 3 weeks (Sprint 0)
**Dependencies:** None - this is the foundation sprint
**Blocks:** All subsequent sprints depend on baseline completion

## Documentation Updates
- [ ] **Architecture docs**: Current state diagrams and proposed future state
- [ ] **Development guides**: Updated setup and testing procedures
- [ ] **Decision records**: ADRs for major architectural decisions

## Quality Metrics Targets (from SM_REFACTOR_STRAT.md)
- 30% reduction in build pipeline duration
- 90% automated test coverage on core modules
- Zero critical security vulnerabilities
- 40% reduction in onboarding time

## Related Work
- Follows SM_REFACTOR_STRAT.md Sprint 0 definition
- Enables subsequent Sprint 1-4 implementation work
- Establishes quality gates for modernization targets

---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[SPRINT-0] Mobilize & Baseline - Architecture Assessment & Dependency Audit`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from SM_REFACTOR_STRAT.md Sprint 0

EOF

if gh issue create   --title "01 Sprint0 Mobilize  Baseline  Architecture Assessment  Dependency Audit"   --body-file "issue_11_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P0-critical,sprint-0"   --milestone "Sprint 0: Mobilize & Baseline"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_11_body.txt"
fi
echo ""

# Issue 12: 02 Impl Realtime Collaboration Engine
echo "Creating issue 12/21: 02 Impl Realtime Collaboration Engine"
if $RETRY_ONLY_FAILED && issue_exists "02 Impl Realtime Collaboration Engine"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_12_body.txt" << 'EOF'
# [IMPL] Real-Time Collaboration Engine

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 001: Real-Time Collaboration Engine

## Summary
Implement the real-time collaboration service described in [Implementation Plan §Real-Time Collaboration](../IMPLEMENTATION_PLAN.md#real-time-collaboration-engine) to deliver the Week 4 roadmap objective.

## Current State
- `packages/collaboration/` only provides documentation; there is no running service or client integration.【F:packages/collaboration/README.md†L1-L42】
- Web workspace panes render static content without CRDT bindings.

## Proposed Solution
1. Scaffold a FastAPI WebSocket service with Yjs-based CRDT support and persistence.
2. Wire the web client behind the `ENABLE_COLLAB_LIVE` feature flag.
3. Add audit logging, observability, and rollout tooling as outlined in the implementation plan.

## Feature Flag
- `ENABLE_COLLAB_LIVE` (default `false`).

## Acceptance Criteria
- Collaboration service container runs locally and in CI with health checks.
- Web clients joined to the same session see <150 ms update propagation under LAN test conditions.
- Comprehensive unit, contract, and E2E tests exist and pass with the feature flag enabled; default pipelines continue to pass with the flag disabled.
- Documentation updates published for API reference, tutorials, and operations guides.

## Dependencies
- Redis/Postgres availability for session state.
- Keycloak tokens for WebSocket authentication.

## Testing Plan
- Run unit tests for session repository and CRDT merge logic.
- Execute Playwright/Browser-driven co-editing scenarios.
- Include load test validating concurrent participants.

## Rollout & Monitoring
- Stage rollout (dev → staging shadow → pilot).
- Add Prometheus dashboards for session counts and latency.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Real-Time Collaboration Engine`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/001-real-time-collaboration.md

EOF

if gh issue create   --title "02 Impl Realtime Collaboration Engine"   --body-file "issue_12_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P0-critical,sprint-1"   --milestone "M1: Real-Time Foundation"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_12_body.txt"
fi
echo ""

# Issue 13: 03 Impl Evidenceguided Model Recommender V2
echo "Creating issue 13/21: 03 Impl Evidenceguided Model Recommender V2"
if $RETRY_ONLY_FAILED && issue_exists "03 Impl Evidenceguided Model Recommender V2"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_13_body.txt" << 'EOF'
# [IMPL] Evidence-Guided Model Recommender V2

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 002: Evidence-Guided Model Recommender V2

## Summary
Deliver the Week 2 roadmap follow-ups by implementing real LMSYS/MTEB ingestion, telemetry, and cascade routing as captured in [Implementation Plan §Evidence-Guided Model Recommender Enhancements](../IMPLEMENTATION_PLAN.md#evidence-guided-model-recommender-enhancements).

## Current State
- Recommender fetchers return hard-coded samples; no persistent cache or scheduler exists.【F:packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py†L125-L168】
- Provider adapters rely on the recommender but cannot record telemetry beyond in-memory smoothing.【F:packages/mcp-servers/router-mcp/src/router_mcp/providers.py†L30-L88】

## Proposed Solution
1. Add external data clients and persistence for leaderboard metrics.
2. Capture LiteLLM telemetry and nightly refresh jobs feeding the recommender database.
3. Expose admin/debug APIs and ensure cascade routing adheres to utility scoring.

## Feature Flag
- `ENABLE_MODEL_RECOMMENDER_V2` (default `false`).

## Acceptance Criteria
- Nightly job populates recommender store with LMSYS and MTEB scores (verified via metrics dashboard).
- Provider adapter selects models based on dynamic scores with deterministic fallback ordering.
- API exposes diagnostic endpoint returning current performance snapshot.
- All unit/integration tests pass with flag enabled; default CI pipeline passes with flag disabled.

## Dependencies
- Access to LMSYS/MTEB data sources or cached mirrors.
- Storage backend (SQLite/Postgres) reachable from router MCP service.

## Testing Plan
- Unit tests for data parsers, scoring, scheduler triggers.
- Integration tests using mocked HTTP fixtures to simulate external APIs.
- Contract tests for new debug endpoint.

## Rollout & Monitoring
- Deploy scheduler as Kubernetes CronJob with alerting on failures.
- Add Prometheus metrics for recommendation latency, cache freshness, and per-model selection counts.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Evidence-Guided Model Recommender V2`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/002-model-recommender-v2.md

EOF

if gh issue create   --title "03 Impl Evidenceguided Model Recommender V2"   --body-file "issue_13_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P0-critical,sprint-1"   --milestone "M1: Real-Time Foundation"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_13_body.txt"
fi
echo ""

# Issue 14: 04 Impl Retrieval Benchmarking  Latency Validation
echo "Creating issue 14/21: 04 Impl Retrieval Benchmarking  Latency Validation"
if $RETRY_ONLY_FAILED && issue_exists "04 Impl Retrieval Benchmarking  Latency Validation"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_14_body.txt" << 'EOF'
# [IMPL] Retrieval Benchmarking & Latency Validation

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 003: Retrieval Benchmarking & Latency Validation

## Summary
Implement the benchmark workflow and latency quality gates documented in [Implementation Plan §Retrieval Benchmarking & Latency Validation](../IMPLEMENTATION_PLAN.md#retrieval-benchmarking--latency-validation).

## Current State
- The SPLADE evaluator loads synthetic sample data and is not integrated with live retrieval systems.【F:packages/retrieval/src/splade/src/splade/evaluator.py†L62-L186】
- API performance endpoints emit mocked NDCG/MRR values, so roadmap quality gates remain unmet.【F:packages/api/src/stratmaster_api/performance.py†L369-L417】

## Proposed Solution
1. Add dataset loaders and storage for BEIR-style corpora.
2. Integrate evaluator with live retrieval pipelines and persist results.
3. Expose benchmark metrics via API/Prometheus and enforce latency thresholds.

## Feature Flag
- `ENABLE_RETRIEVAL_BENCHMARKS` (default `false`).

## Acceptance Criteria
- Benchmark job produces NDCG@10 and MRR metrics against baseline and SPLADE pipelines, stored for historical comparison.
- `/performance/retrieval` reflects real benchmark data when flag enabled, and returns legacy mock data when disabled.
- Latency instrumentation captures p95 latency ≤200 ms and alerts on regressions.
- Test suites cover metric calculations, dataset loaders, API contracts, and integration flow.

## Dependencies
- Storage for benchmark datasets (MinIO/S3) and compute resources for evaluation jobs.
- Access to retrieval backends (OpenSearch/Qdrant) in staging environments.

## Testing Plan
- Unit tests for metric computations and data ingestion.
- Integration tests running evaluator against stubbed retrieval services.
- Nightly job validation with real services in staging.

## Rollout & Monitoring
- Introduce nightly CI workflow to run benchmarks and publish Prometheus metrics.
- Configure alerting for metric drops >10% or latency regression beyond thresholds.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Retrieval Benchmarking & Latency Validation`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/003-retrieval-benchmarks.md

EOF

if gh issue create   --title "04 Impl Retrieval Benchmarking  Latency Validation"   --body-file "issue_14_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P0-critical,sprint-1"   --milestone "M1: Real-Time Foundation"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_14_body.txt"
fi
echo ""

# Issue 15: 05 Impl Advanced Caching  Performance Optimisation
echo "Creating issue 15/21: 05 Impl Advanced Caching  Performance Optimisation"
if $RETRY_ONLY_FAILED && issue_exists "05 Impl Advanced Caching  Performance Optimisation"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_15_body.txt" << 'EOF'
# [IMPL] Advanced Caching & Performance Optimisation

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 004: Advanced Caching & Performance Optimisation

## Summary
Execute the multi-tier caching initiative detailed in [Implementation Plan §Advanced Caching & Performance Optimisation](../IMPLEMENTATION_PLAN.md#advanced-caching--performance-optimisation) to meet roadmap performance goals.

## Current State
- API relies on a basic Redis helper without tiered strategies, invalidation hooks, or CDN integration.【F:packages/api/src/stratmaster_api/clients/cache_client.py†L1-L156】
- Roadmap Phase 1 action item “Performance Optimization” and immediate enhancement #3 remain unchecked.【F:Upgrade.md†L397-L404】【F:Upgrade.md†L510-L514】

## Proposed Solution
1. Instrument per-endpoint latency metrics and identify cacheable responses.
2. Implement tiered caching (Redis + edge/CDN) with invalidation via pub/sub.
3. Provide ops tooling and documentation for CDN rollout.

## Feature Flags
- `ENABLE_RESPONSE_CACHE_V2`
- `ENABLE_EDGE_CACHE_HINTS`

## Acceptance Criteria
- Latency dashboards demonstrate 3–5× improvement on targeted endpoints with caches enabled.
- Cache headers and surrogate keys present on API responses when flags enabled, absent otherwise.
- Automated tests cover cache hit/miss paths and invalidation triggers.
- Documentation outlines deployment steps and rollback procedures.

## Dependencies
- Redis availability; CDN vendor credentials if edge caching enabled.
- Observability stack (Prometheus, Grafana) for metrics.

## Testing Plan
- Unit tests for cache tier selection and invalidation bus.
- Contract tests verifying HTTP headers and cache behavior.
- Load testing via `make test.load` comparing before/after performance.

## Rollout & Monitoring
- Deploy instrumentation first, followed by Redis tier, then CDN hints.
- Configure alerts on cache error rate and latency regressions.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Advanced Caching & Performance Optimisation`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/004-advanced-caching.md

EOF

if gh issue create   --title "05 Impl Advanced Caching  Performance Optimisation"   --body-file "issue_15_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P1-important,sprint-2"   --milestone "M2: Performance & Validation"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_15_body.txt"
fi
echo ""

# Issue 16: 06 Impl Phase 3 Ux Quality Gates
echo "Creating issue 16/21: 06 Impl Phase 3 Ux Quality Gates"
if $RETRY_ONLY_FAILED && issue_exists "06 Impl Phase 3 Ux Quality Gates"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_16_body.txt" << 'EOF'
# [IMPL] Phase 3 UX Quality Gates

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 005: Phase 3 UX Quality Gates

## Summary
Close the remaining Phase 3 UX deliverables described in [Implementation Plan §Phase 3 UX Quality Gates](../IMPLEMENTATION_PLAN.md#phase-3-ux-quality-gates).

## Current State
- WCAG 2.1 AA validation, responsive testing, and Lighthouse performance budgets are outstanding in the roadmap checklist.【F:Upgrade.md†L575-L588】
- Accessibility tooling exists only as a placeholder script without CI coverage.

## Proposed Solution
1. Expand accessibility audit tooling (axe, keyboard navigation) and integrate into CI.
2. Add Playwright responsiveness tests and document mobile testing matrix.
3. Configure Lighthouse CI with score thresholds >90 and remediate issues.

## Feature Flags
- `ENABLE_LIGHTHOUSE_CI` (controls expensive checks).
- Component-level flags as needed for remediation rollouts.

## Acceptance Criteria
- Automated accessibility suite passes with zero critical violations across key pages.
- Responsive tests cover defined breakpoints and device profiles.
- Lighthouse CI job runs in PR (optional) and nightly pipelines, enforcing score budgets.
- Documentation includes accessibility guide, responsive testing checklist, and updated mobile roadmap.

## Dependencies
- Browser automation infrastructure (Playwright, headless Chrome).
- Potential BrowserStack/Sauce Labs accounts for device coverage.

## Testing Plan
- Component unit tests verifying ARIA roles and keyboard support.
- Playwright scenarios for viewport-specific regressions.
- Lighthouse CI runs capturing performance metrics.

## Rollout & Monitoring
- Introduce tooling behind flags to avoid blocking contributors, then progressively enforce.
- Track accessibility and performance metrics via dashboards.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Phase 3 UX Quality Gates`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/005-phase3-ux-quality.md

EOF

if gh issue create   --title "06 Impl Phase 3 Ux Quality Gates"   --body-file "issue_16_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P1-important,sprint-2"   --milestone "M2: Performance & Validation"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_16_body.txt"
fi
echo ""

# Issue 17: 07 Impl Predictive Strategy Analytics
echo "Creating issue 17/21: 07 Impl Predictive Strategy Analytics"
if $RETRY_ONLY_FAILED && issue_exists "07 Impl Predictive Strategy Analytics"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_17_body.txt" << 'EOF'
# [IMPL] Predictive Strategy Analytics

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 006: Predictive Strategy Analytics

## Summary
Implement the predictive analytics capability outlined in [Implementation Plan §Predictive Strategy Analytics](../IMPLEMENTATION_PLAN.md#predictive-strategy-analytics).

## Current State
- Forecast API returns random values without real time-series models or data pipelines.【F:packages/api/src/stratmaster_api/services.py†L726-L788】
- No ML training workflow or feature store exists for strategy metrics.

## Proposed Solution
1. Build data ingestion and feature engineering pipeline for historical strategy metrics.
2. Implement forecasting models (Prophet/NeuralProphet) with MLflow tracking.
3. Deploy inference service and update API/UX to consume real forecasts behind `ENABLE_PREDICTIVE_ANALYTICS`.

## Feature Flag
- `ENABLE_PREDICTIVE_ANALYTICS` (default `false`).

## Acceptance Criteria
- Historical data ingested into analytics store with reproducible transformations.
- Forecast service produces validated metrics (MAPE, RMSE) above defined thresholds and exposes model lineage.
- API/UI display real forecasts when flag enabled and fall back to legacy behavior otherwise.
- Documentation covers operations, model governance, and troubleshooting.

## Dependencies
- Data warehouse or analytics database for historical metrics.
- ML tooling (Prophet, MLflow) and compute resources for training.

## Testing Plan
- Unit tests for feature engineering and model evaluation utilities.
- Contract tests for forecast API schema and fallback logic.
- Integration tests training lightweight models on sample data during CI.

## Rollout & Monitoring
- Pilot with internal tenants, then expand. Monitor forecast accuracy and drift via dashboards.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Predictive Strategy Analytics`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/006-predictive-analytics.md

EOF

if gh issue create   --title "07 Impl Predictive Strategy Analytics"   --body-file "issue_17_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P2-enhancement,sprint-3"   --milestone "M3: Advanced Analytics"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_17_body.txt"
fi
echo ""

# Issue 18: 08 Impl Eventdriven Microservices Architecture
echo "Creating issue 18/21: 08 Impl Eventdriven Microservices Architecture"
if $RETRY_ONLY_FAILED && issue_exists "08 Impl Eventdriven Microservices Architecture"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_18_body.txt" << 'EOF'
# [IMPL] Event-Driven Microservices Architecture

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 007: Event-Driven Microservices Architecture

## Summary
Adopt the event-driven architecture described in [Implementation Plan §Event-Driven Microservices Architecture](../IMPLEMENTATION_PLAN.md#event-driven-microservices-architecture) to meet scalability roadmap goals.

## Current State
- All services communicate synchronously; no Kafka/Redis Streams producers or consumers exist.【F:Upgrade.md†L413-L418】
- There is no outbox pattern or schema registry for domain events.

## Proposed Solution
1. Introduce outbox table and dispatcher to emit events via Redis Streams (initially) or Kafka.
2. Define event schemas and implement producers in API services after transactional commits.
3. Build consumer workers for analytics, notifications, and audit logging.

## Feature Flag
- `ENABLE_EVENT_STREAMING` (default `false`).

## Acceptance Criteria
- Event schemas published and validated; producers emit events for key domain changes when flag enabled.
- Consumers process events idempotently with monitoring for lag and failures.
- Documentation outlines event catalog and deployment steps.
- With flag disabled, system behaves as today with no side effects.

## Dependencies
- Message broker (Redis Streams or Kafka) and infrastructure support.
- Observability stack for lag and error metrics.

## Testing Plan
- Unit tests for schema validation and producer logic.
- Integration tests running docker-compose with broker, verifying end-to-end event flow.
- Contract tests for event payloads using jsonschema/protobuf tooling.

## Rollout & Monitoring
- Enable per-event-type, starting with low-risk events (export audit).
- Monitor consumer lag, error rates, and throughput; configure alerts.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Event-Driven Microservices Architecture`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/007-event-architecture.md

EOF

if gh issue create   --title "08 Impl Eventdriven Microservices Architecture"   --body-file "issue_18_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P2-enhancement,sprint-3"   --milestone "M3: Advanced Analytics"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_18_body.txt"
fi
echo ""

# Issue 19: 09 Impl Industryspecific Strategy Templates
echo "Creating issue 19/21: 09 Impl Industryspecific Strategy Templates"
if $RETRY_ONLY_FAILED && issue_exists "09 Impl Industryspecific Strategy Templates"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_19_body.txt" << 'EOF'
# [IMPL] Industry-Specific Strategy Templates

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 008: Industry-Specific Strategy Templates

## Summary
Deliver the industry template expansion described in [Implementation Plan §Industry-Specific Strategy Templates](../IMPLEMENTATION_PLAN.md#industry-specific-strategy-templates).

## Current State
- Strategy synthesizer relies on a single generic Jinja template; no industry metadata or datasets exist.【F:packages/strategy/src/strategy_pipeline/strategy_synthesizer.py†L67-L577】
- Seeds lack vertical-specific content.

## Proposed Solution
1. Create template metadata/catalog with per-vertical Jinja templates and YAML descriptors.
2. Extend API and synthesizer logic to accept an `industry` parameter and apply vertical heuristics.
3. Update UI to allow industry selection and surface recommended KPIs; seed datasets accordingly.

## Feature Flag
- `ENABLE_INDUSTRY_TEMPLATES` (default `false`).

## Acceptance Criteria
- Template catalog stored in repo with automated validation tests.
- Strategy generation honors requested industry and returns relevant KPIs and assumptions.
- UI exposes industry selection and is covered by E2E tests.
- Documentation includes template catalog reference and customization guide.

## Dependencies
- Updated knowledge base and seeds for vertical content.
- Coordination with export integrations to map industry-specific fields where needed.

## Testing Plan
- Unit tests for template loader/renderer and metadata schema.
- Contract tests verifying API accepts/returns industry field.
- UI integration tests for workflow selection.

## Rollout & Monitoring
- Roll out per-vertical to gather feedback; monitor user adoption metrics and template usage analytics.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Industry-Specific Strategy Templates`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/008-industry-templates.md

EOF

if gh issue create   --title "09 Impl Industryspecific Strategy Templates"   --body-file "issue_19_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P2-enhancement,sprint-3"   --milestone "M3: Advanced Analytics"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_19_body.txt"
fi
echo ""

# Issue 20: 10 Impl Custom Model Finetuning Platform
echo "Creating issue 20/21: 10 Impl Custom Model Finetuning Platform"
if $RETRY_ONLY_FAILED && issue_exists "10 Impl Custom Model Finetuning Platform"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_20_body.txt" << 'EOF'
# [IMPL] Custom Model Fine-Tuning Platform

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 009: Custom Model Fine-Tuning Platform

## Summary
Implement the enterprise fine-tuning platform defined in [Implementation Plan §Custom Model Fine-Tuning Platform](../IMPLEMENTATION_PLAN.md#custom-model-fine-tuning-platform).

## Current State
- ML training code focuses on constitutional compliance; no dataset registry, orchestration, or adapter deployment path exists.【F:packages/ml-training/src/constitutional_trainer.py†L1-L404】

## Proposed Solution
1. Build dataset registry and secure storage workflow (ingestion, validation, lineage).
2. Orchestrate fine-tuning jobs (Ray/Kubeflow) and store artifacts in a model registry with evaluation metrics.
3. Integrate LiteLLM gateway with per-tenant adapters and add compliance approval workflow.

## Feature Flag
- `ENABLE_CUSTOM_FINE_TUNING` (default `false`).

## Acceptance Criteria
- Tenants can submit fine-tuning jobs via API; job lifecycle observable via dashboard.
- Model artifacts stored with metadata, evaluations, and access controls; adapters deployable through gateway when approved.
- Documentation details dataset handling, compliance, and rollback.
- With flag disabled, system continues to use vendor models without exposing fine-tune APIs.

## Dependencies
- Scalable compute resources (GPU nodes) and storage (MinIO/S3).
- Compliance review tooling and audit logging.

## Testing Plan
- Unit tests for dataset validation and job config serialization.
- Integration tests executing lightweight fine-tune on synthetic data in CI or nightly pipeline.
- Contract tests for job submission/status APIs and adapter deployment flow.

## Rollout & Monitoring
- Pilot with internal datasets; expand to enterprise tenants after compliance sign-off.
- Monitor job success rates, resource utilization, and adapter inference metrics.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Custom Model Fine-Tuning Platform`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/009-fine-tuning-platform.md

EOF

if gh issue create   --title "10 Impl Custom Model Finetuning Platform"   --body-file "issue_20_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P2-enhancement,sprint-3"   --milestone "M3: Advanced Analytics"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_20_body.txt"
fi
echo ""

# Issue 21: 11 Impl Advanced Knowledge Graph Reasoning
echo "Creating issue 21/21: 11 Impl Advanced Knowledge Graph Reasoning"
if $RETRY_ONLY_FAILED && issue_exists "11 Impl Advanced Knowledge Graph Reasoning"; then
    echo "  ↪ Skipped (already exists)"
else
cat > "issue_21_body.txt" << 'EOF'
# [IMPL] Advanced Knowledge Graph Reasoning

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

# Issue 010: Advanced Knowledge Graph Reasoning

## Summary
Implement the knowledge reasoning enhancements in [Implementation Plan §Advanced Knowledge Graph Reasoning](../IMPLEMENTATION_PLAN.md#advanced-knowledge-graph-reasoning).

## Current State
- Knowledge pipeline performs ingestion and hybrid search but lacks causal inference and advanced analytics.【F:packages/knowledge/src/knowledge/pipeline.py†L1-L100】

## Proposed Solution
1. Extend knowledge package with graph analytics (PageRank, community detection) and NebulaGraph integrations.
2. Integrate causal inference libraries (DoWhy/EconML) to compute causal scores stored alongside graph edges.
3. Expose reasoning APIs and UI overlays behind `ENABLE_KNOWLEDGE_REASONING`.

## Feature Flag
- `ENABLE_KNOWLEDGE_REASONING` (default `false`).

## Acceptance Criteria
- Graph analytics outputs persisted with metadata and surfaced via API.
- Causal reasoning endpoints return narratives with supporting evidence; strategy engine can consume causal weights.
- UI visualises causal graph overlays when flag enabled.
- Documentation covers algorithms, interpretation guidance, and privacy considerations.

## Dependencies
- NebulaGraph cluster access and analytics libraries (networkx, dowhy).
- Strategy engine integration for consuming causal insights.

## Testing Plan
- Unit tests for analytics algorithms using deterministic synthetic graphs.
- Contract tests for reasoning API schema and latency budgets.
- Integration tests ensuring strategy recommendations incorporate causal adjustments without regression.

## Rollout & Monitoring
- Start with analytics-only reports, then enable UI overlays.
- Monitor computation latency, cache hit rates, and user adoption metrics.


---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `[IMPL] Advanced Knowledge Graph Reasoning`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from issues/010-knowledge-reasoning.md

EOF

if gh issue create   --title "11 Impl Advanced Knowledge Graph Reasoning"   --body-file "issue_21_body.txt"   --label "enhancement,SM_REFACTOR_STRAT,implementation,v2,P2-enhancement,sprint-3"   --milestone "M3: Advanced Analytics"; then
    echo "✅ Created successfully"
    CREATED_COUNT=$((CREATED_COUNT + 1))
else
    echo "❌ Failed to create"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi
rm -f "issue_21_body.txt"
fi
echo ""

echo "📊 Summary:"
echo "  Total issues: $TOTAL_ISSUES"
echo "  Created: $CREATED_COUNT"
echo "  Failed: $FAILED_COUNT"

if [ $FAILED_COUNT -eq 0 ]; then
    echo "🎉 All issues created successfully!"
    exit 0
else
    echo "⚠️  Some issues failed to create"
    exit 1
fi
