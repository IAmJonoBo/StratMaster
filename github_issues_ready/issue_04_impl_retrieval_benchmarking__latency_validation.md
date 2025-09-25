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
