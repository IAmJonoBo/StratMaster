# StratMaster V2 Development Guide

## Overview

StratMaster V2 represents a comprehensive modernization of the platform following the **SM_REFACTOR_STRAT.md** 5-sprint program. This guide provides everything needed to understand, contribute to, and track progress on V2 development.

## 🎯 V2 Objectives

### Strategic Goals
- **30% reduction** in build pipeline duration
- **90% automated test coverage** on core modules
- **Zero critical security vulnerabilities**
- **40% reduction** in developer onboarding time

### Key Features
- **Real-time collaboration engine** with WebSocket support
- **Evidence-guided model recommender V2** with LMSYS/MTEB integration
- **Advanced retrieval benchmarking** with automated validation
- **Predictive analytics** and **event-driven architecture**
- **Industry-specific templates** and **custom model fine-tuning**

## 🏗️ Architecture Overview

### V2 Branch Structure
```
v2/                           # Main V2 development branch
├── packages/                 # 26 modular packages
│   ├── api/                 # FastAPI core service
│   ├── mcp-servers/         # 8 MCP microservices
│   ├── orchestrator/        # Workflow engine
│   ├── collaboration/       # Real-time collaboration (NEW)
│   ├── analytics/           # Predictive analytics (ENHANCED)
│   └── ui/                  # Frontend components (ENHANCED)
├── scripts/                 # V2 automation tools
│   ├── v2_branch_consolidator.py
│   ├── github_issue_sync.py
│   └── v2_progress_tracker.py
├── V2_CONSOLIDATION_STRATEGY.md
├── GITHUB_ISSUES_MANUAL.md
└── v2_progress_tracking.json
```

### Feature Flags
All V2 features are controlled by feature flags to ensure safe rollout:

```json
{
  "ENABLE_COLLAB_LIVE": false,
  "ENABLE_MODEL_RECOMMENDER_V2": false,
  "ENABLE_PREDICTIVE_ANALYTICS": false,
  "ENABLE_EVENT_STREAMING": false,
  "ENABLE_INDUSTRY_TEMPLATES": false
}
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and switch to V2 branch
git clone https://github.com/IAmJonoBo/StratMaster.git
cd StratMaster
git checkout v2

# Bootstrap development environment
make bootstrap

# Validate V2 setup
python3 scripts/v2_branch_consolidator.py validate
```

### 2. Verify Installation
```bash
# Run API tests
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q

# Check V2 progress dashboard
python3 scripts/v2_progress_tracker.py dashboard
```

### 3. Start Development
```bash
# Start V2 API server
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 127.0.0.1 --port 8080

# Verify health check
curl http://127.0.0.1:8080/healthz
# Expected: {"status":"ok"}
```

## 📋 Sprint Roadmap

### Sprint 0: Mobilize & Baseline (Weeks 1-3) ⏸️
**Status**: Not Started
**Completion**: 0%

**Objectives**:
- [ ] Architecture Assessment & Domain Mapping
- [ ] Dependency Inventory & Risk Classification
- [ ] Test Coverage Benchmarking & Test Data Audit
- [ ] CI/CD & Virtual Environment Baseline Analysis

### Sprint 1: Modular Architecture Foundations (Weeks 4-6) ⏸️
**Status**: Not Started
**Completion**: 0%

**Objectives**:
- [ ] Module Boundary Implementation & Code Move Strategy
- [ ] Shared Infrastructure Layer (logging, config, auth)
- [ ] Developer Tooling Update & Lint Baseline Alignment
- [ ] Developer Guide Refresh & Migration Playbook

### Sprint 2: Dependency Modernization (Weeks 7-9) ⏸️
**Status**: Not Started
**Completion**: 0%

**Objectives**:
- [ ] Tier-1 Dependency Upgrades (Python, FastAPI, etc.)
- [ ] Security & Compliance Tooling (Snyk/Trivy/Dependabot)
- [ ] Compatibility Testing Matrix & Rollback Automation
- [ ] Container Base Image Refresh & Slimming

### Sprint 3: Testing & Quality Expansion (Weeks 10-12) ⏸️
**Status**: Not Started
**Completion**: 0%

**Objectives**:
- [ ] Core Domain Unit & Integration Test Expansion
- [ ] Contract & Consumer-Driven Tests for Services/APIs
- [ ] Performance & Load Testing Harness with Observability
- [ ] Quality Gate Automation (coverage, lint, security)

### Sprint 4: CI/CD Evolution (Weeks 13-15) ⏸️
**Status**: Not Started
**Completion**: 0%

**Objectives**:
- [ ] Pipeline Re-architecture (modular builds, caching, matrix)
- [ ] Secrets, Compliance, and Supply Chain Hardening
- [ ] Virtual Environment Optimization & Developer Onboarding Scripts
- [ ] Operational Runbooks, Playbooks, and Knowledge Transfer

## 🎯 Milestones

### M1: Real-Time Foundation (Week 2) 🔄
**Progress**: 33% (1/3 criteria met)
- [ ] Real-time collaboration engine operational
- [ ] Evidence-guided model recommender V2 implemented
- [x] V2 branch established and validated

### M2: Performance & Validation (Week 4) 🔄
**Progress**: 0% (0/3 criteria met)
- [ ] Retrieval benchmarking automated
- [ ] Advanced caching implemented
- [ ] Phase 3 UX quality gates established

### M3: Advanced Analytics (Week 8) 🔄
**Progress**: 0% (0/3 criteria met)
- [ ] Predictive analytics operational
- [ ] Event-driven architecture implemented
- [ ] 90% test coverage achieved

### M4: Enterprise Features (Week 12) 🔄
**Progress**: 0% (0/3 criteria met)
- [ ] Industry templates available
- [ ] Custom model fine-tuning platform
- [ ] Knowledge graph reasoning enhanced

## 📊 Success Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Build Performance Improvement | 0% | 30% | 🔄 |
| Test Coverage | 0% | 90% | 🔄 |
| Security Vulnerabilities | 0 | 0 | ✅ |
| Onboarding Time Reduction | 0% | 40% | 🔄 |

## 🛠️ Development Tools

### Branch Consolidation
```bash
# Discover and analyze branches
python3 scripts/v2_branch_consolidator.py analyze

# Create V2 branch
python3 scripts/v2_branch_consolidator.py create

# Preview consolidation plan
python3 scripts/v2_branch_consolidator.py consolidate

# Execute consolidation
python3 scripts/v2_branch_consolidator.py consolidate --execute
```

### Issue Management
```bash
# Generate GitHub issue sync files
python3 scripts/github_issue_sync.py sync

# Validate issue templates
python3 scripts/github_issue_sync.py validate

# View sync report
python3 scripts/github_issue_sync.py report
```

### Automated Issue Creation Enhancements (V2)

The bulk creation script now supports safe re-runs and feature flag introspection tooling.

```bash
# Standard first run (creates labels + milestones if missing, then 21 issues)
./create_github_issues.sh

# Retry mode: only attempt issues that failed in a previous partial run
./create_github_issues.sh --retry-only-failed

# (Planned) Dry run: show which issues would be created (not yet implemented)
./create_github_issues.sh --dry-run   # Coming soon
```

Behavior details:
- Preflight step ensures all required labels and milestones exist (non‑interactive) to prevent hangs.
- A cache of existing issue titles (open + closed) makes the script idempotent.
- `--retry-only-failed` skips any title already present, so you can safely re-run after fixing network/API errors.

### Feature Flag → Issue Index

Generate a JSON map (`v2_issue_feature_flags.json`) linking feature flags to the issues that introduce or reference them:

```bash
python3 scripts/generate_issue_feature_index.py
# Output sample:
# {
#   "flags": {
#     "ENABLE_COLLAB_LIVE": {"issues": [123], "titles": ["Issue 001: Real-Time Collaboration Engine"]},
#     ...
#   },
#   "unmapped_issues": [...]
# }
```

Use cases:
- Trace deployment readiness for gated features.
- Power dashboards / documentation linking flags to roadmap scope.
- Detect orphaned flags (those with empty `issues`).

### Milestone Validation (CI)

The workflow `.github/workflows/validate-milestones.yml` runs on pushes/PRs to `v2` and `main` and invokes:

```bash
python scripts/validate_milestones.py --verbose
```

Purpose:
- Prevent accidental milestone renames/deletions that would break automation.
- Fast feedback if a required milestone (M1–M4, Sprint 0) is missing.

Manual usage examples:
```bash
python scripts/validate_milestones.py                # Validate default required list
python scripts/validate_milestones.py --list         # List fetched milestones
python scripts/validate_milestones.py --expected "M1: Real-Time Foundation" "Sprint 0: Mobilize & Baseline"
```

Exit code is non‑zero if any required milestone is missing (enforces CI quality gate).

### Live Progress Dashboard Mode

`v2_progress_tracker.py` now supports a `--live` augmentation which augments the static progress data with real GitHub counts (issues + milestones) via the GitHub CLI.

```bash
python3 scripts/v2_progress_tracker.py dashboard --live
```

Requirements:
- `gh` authenticated (`gh auth status` must succeed).

When `--live` is supplied the dashboard shows an additional section summarizing:
- Total issues (open/closed counts)
- Milestones (open vs closed, upcoming targets)
- Optional derived percentages for roadmap completion.

### Troubleshooting Bulk Issue Creation

| Symptom | Likely Cause | Resolution |
|---------|--------------|-----------|
| Script appears to hang after first issue | Missing label/milestone causing interactive prompt | Preflight now auto-creates; pull latest script and re-run |
| Issues duplicated | Script was run before retry logic patch | Use GitHub UI search on `"Issue 00"` and close duplicates, or future duplicate detector script (planned) |
| `gh: Not authenticated` | GitHub CLI not logged in | Run `gh auth login` |
| `API rate limit exceeded` | Unauthenticated or excessive runs | Authenticate or wait/reset, then use `--retry-only-failed` |

### Planned Improvements

| Enhancement | Description | Status |
|-------------|-------------|--------|
| `--dry-run` mode | Output planned creations without executing `gh issue create` | Planned |
| Duplicate detector | Script to list multiple issues sharing the same canonical base title | Planned |
| Title normalization in flag index | Strip `Issue NNN:` prefix for cleaner dashboards | Planned |


### Progress Tracking
```bash
# View progress dashboard
python3 scripts/v2_progress_tracker.py dashboard

# Update sprint progress
python3 scripts/v2_progress_tracker.py sprint --update sprint_1 --status in_progress

# Update milestones
python3 scripts/v2_progress_tracker.py milestone --update M1 --status completed

# Update metrics
python3 scripts/v2_progress_tracker.py metrics --test_coverage 85 --build_performance_improvement 25

# Add blockers/achievements
python3 scripts/v2_progress_tracker.py blocker --add "CI pipeline failing" --severity high
python3 scripts/v2_progress_tracker.py achievement --add "V2 branch created successfully"
```

## 📝 GitHub Issue Tracking

### Total Issues: 21
- **P0-Critical**: Real-time collaboration, model recommender V2, retrieval benchmarking
- **P1-Important**: Performance optimization, UX quality gates
- **P2-Enhancement**: Predictive analytics, event architecture, industry templates

### Issue Creation Options

#### Option 1: Automated (GitHub CLI)
```bash
# Install GitHub CLI if needed
gh auth login

# Execute automated creation
./create_github_issues.sh
```

#### Option 2: Manual Creation
Follow the detailed instructions in `GITHUB_ISSUES_MANUAL.md`:
1. Navigate to https://github.com/IAmJonoBo/StratMaster/issues
2. For each issue, copy title and body from the manual
3. Apply suggested labels and milestones
4. Create issue and track in GitHub Projects

#### Option 3: Batch Commands
Copy commands from `github_cli_commands.txt` and execute individually.

## 🔄 Development Workflow

### Feature Development Process
1. **Branch Creation**: `git checkout -b feature/v2-feature-name`
2. **Feature Flag**: Add feature flag for new functionality
3. **Implementation**: Develop with V2 architecture patterns
4. **Testing**: Comprehensive test coverage (unit, integration, e2e)
5. **Quality Gates**: Pass all automated quality checks
6. **PR Review**: Peer review with V2 architecture compliance
7. **Integration**: Merge to V2 with feature flag controls

### Quality Assurance
- **Pre-commit Hooks**: Automated code quality checks
- **CI/CD Pipeline**: Multi-stage validation (lint, test, security, performance)
- **Feature Flag Testing**: A/B test new features before full rollout
- **Rollback Strategy**: Immediate rollback capability for any V2 component

## 🚨 Risk Management

### Technical Risks & Mitigation
- **Merge Conflicts**: Automated conflict resolution with manual review fallback
- **Breaking Changes**: Feature flags ensure backward compatibility
- **Performance Regression**: Comprehensive benchmarking and monitoring
- **Test Coverage Gaps**: Mandatory 90% coverage with automated enforcement

### Process Risks & Mitigation
- **Developer Adoption**: Comprehensive migration guides and training
- **Timeline Delays**: Phased rollout with MVP approach
- **Quality Degradation**: Automated quality gates and rollback procedures
- **Communication Gaps**: Automated progress reporting and dashboards

## 📈 Progress Monitoring

### Weekly Reports
- Sprint progress and objective completion
- Metric updates and trend analysis
- Blocker identification and resolution
- Achievement celebration and documentation

### Dashboard Updates
- Real-time progress visualization
- Milestone tracking and forecasting
- Success metric monitoring
- Risk assessment and mitigation tracking

## 🎯 Success Criteria

### Technical Validation
- [x] V2 branch successfully consolidated with all valuable commits
- [ ] All existing tests pass on V2 branch
- [ ] 90%+ test coverage achieved across core modules
- [ ] 30% CI/CD performance improvement demonstrated
- [x] Zero critical security vulnerabilities maintained
- [x] Feature flag system operational and tested (scaffold present; enable via configs/v2-flags.json)

### Process Validation
- [ ] 40% reduction in developer onboarding time measured
- [x] All 21 implementation issues tracked in GitHub (auto-created via `create_github_issues.sh` with milestone + label preflight)
- [ ] Sprint milestones aligned with delivery schedule
- [ ] Automated quality gates preventing regressions
- [ ] Developer satisfaction > 8/10 (V2 workflow survey)

## 🚀 Next Steps

### Week 1 Priorities
1. **Execute Branch Consolidation**: Complete automated branch discovery and consolidation
2. **Create GitHub Issues**: Sync all 21 implementation issues to GitHub
3. **Sprint 0 Launch**: Begin architecture assessment and dependency audit
4. **Team Onboarding**: Train developers on V2 workflow and tools
5. **Progress Baseline**: Establish initial metrics and tracking

### Getting Started Today
1. Review this guide and the [V2 Consolidation Strategy](V2_CONSOLIDATION_STRATEGY.md)
2. Set up your V2 development environment using the Quick Start guide
3. Create GitHub issues using the instructions in [GITHUB_ISSUES_MANUAL.md](GITHUB_ISSUES_MANUAL.md)
4. Start Sprint 0 objectives and update progress using the tracking tools
5. Join the V2 development effort and help build the future of StratMaster!

---

## 📚 Additional Resources

- **[SM_REFACTOR_STRAT.md](SM_REFACTOR_STRAT.md)**: Complete 5-sprint modernization program
- **[V2_CONSOLIDATION_STRATEGY.md](V2_CONSOLIDATION_STRATEGY.md)**: Detailed consolidation strategy
- **[GITHUB_ISSUES_MANUAL.md](GITHUB_ISSUES_MANUAL.md)**: Issue creation instructions
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: General contribution guidelines
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)**: Original implementation roadmap

**Questions?** Check existing GitHub Discussions or create a new discussion with the "v2-development" label.

*Last updated: 2025-09-25 (issues auto-created)*
