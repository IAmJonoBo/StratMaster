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
