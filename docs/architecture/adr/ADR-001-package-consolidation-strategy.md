# ADR-001: Package Consolidation Strategy for StratMaster Modernization

## Status
**PROPOSED** - Draft for Sprint 1 implementation

## Context

StratMaster currently has 33 separate packages with individual dependency management, creating complexity in maintenance, testing, and deployment. The SM_REFACTOR_STRAT.md modernization program targets 30% build pipeline reduction and 40% onboarding time reduction, requiring architectural simplification.

### Current State Problems
- **33 separate pyproject.toml files** causing dependency fragmentation
- **Complex interdependencies** between packages without clear contracts
- **Inconsistent testing patterns** across package boundaries
- **Slow CI/CD pipelines** due to repeated environment setup
- **Developer onboarding complexity** from architectural confusion

### Sprint 0 Findings (ARCH-001, DEP-001)
- 33 packages identified (more than estimated 29)
- Clear domain boundaries exist but are not enforced
- Consolidation potential of 45% (33 → 15 packages)
- Strong foundation in core API and MCP services

## Decision

**Consolidate 33 packages into 15 domain-aligned packages** over Sprint 1-2, following the domain boundaries identified in ARCH-001.

### Target Architecture

#### Core Application Layer (3 packages)
```
1. stratmaster-api/          # Main FastAPI application (consolidate mobile-api)
2. stratmaster-strategy/     # Strategy generation core (merge strategy, knowledge, analytics)  
3. stratmaster-collaboration/# Real-time collaboration services
```

#### MCP Services Layer (5 packages - unchanged)
```
4. router-mcp/         # Model routing and recommendation
5. research-mcp/       # Research data collection
6. knowledge-mcp/      # Knowledge graph operations  
7. compression-mcp/    # Data compression services
8. evals-mcp/          # Model evaluation
```

#### Infrastructure Layer (4 packages)
```
9. stratmaster-security/   # Security, auth, SSO integration (merge packages/security + sso-integration)
10. stratmaster-retrieval/ # Unified retrieval (merge SPLADE, ColBERT, BGE sub-packages)
11. stratmaster-data/      # Data pipeline (merge ingestion, processing, verification)
12. stratmaster-infra/     # Shared utilities (merge agents, providers, orchestration)
```

#### ML/Analytics Layer (3 packages)
```  
13. stratmaster-ml/      # ML training, evaluation frameworks
14. stratmaster-analytics/# Analytics, monitoring, observability  
15. stratmaster-integrations/# External integrations, providers
```

### Consolidation Phases

#### Phase 1 (Sprint 1): Core Consolidation
1. **API Consolidation**: Merge `mobile-api` into `api`
2. **Strategy Core**: Merge `strategy`, `knowledge`, `analytics` into unified strategy package
3. **Data Pipeline**: Merge `ingestion`, `dataprocessing`, `verification` into data package

#### Phase 2 (Sprint 2): Infrastructure Consolidation  
1. **Security Core**: Merge `security` and `sso-integration`
2. **Retrieval Engine**: Consolidate all retrieval sub-packages
3. **Shared Infrastructure**: Merge utility packages

#### Phase 3 (Sprint 3): Final Optimization
1. **ML Consolidation**: Merge ML-related packages
2. **Interface Standardization**: Establish package contracts
3. **Testing Alignment**: Unified testing patterns

## Consequences

### Positive Consequences
- **Simplified Dependencies**: Single pyproject.toml per consolidated domain
- **Clearer Ownership**: Domain-aligned package boundaries
- **Faster CI/CD**: Reduced environment setup and build complexity
- **Better Testing**: Unified testing patterns and shared fixtures
- **Improved Onboarding**: Clearer architecture for new developers

### Negative Consequences  
- **Migration Complexity**: Import path changes across all packages
- **Temporary Disruption**: Development velocity impact during migration
- **Risk of Conflicts**: Potential merge conflicts during consolidation
- **Documentation Debt**: All documentation needs updating

### Risks and Mitigations

#### High Risk: Import Path Breakage
- **Mitigation**: Automated refactoring tools, comprehensive testing
- **Rollback**: Feature flags and incremental migration

#### Medium Risk: Merge Conflicts
- **Mitigation**: Careful sequencing, small batch consolidations  
- **Testing**: Comprehensive integration tests before each merge

#### Low Risk: Developer Confusion
- **Mitigation**: Clear migration guides, ADR documentation
- **Training**: Team workshops on new architecture

## Implementation Plan

### Sprint 1 Actions

#### Week 1: Foundation Setup
1. **Create Target Package Structure**
   ```bash
   mkdir -p packages/stratmaster-{api,strategy,data,security,retrieval}
   ```

2. **Design Import Migration Strategy**
   - Create import compatibility layer
   - Design deprecation warnings
   - Plan staged migration approach

#### Week 2: Core Consolidation
1. **API Package Consolidation**
   ```bash
   # Move mobile-api into main API
   mv packages/mobile-api/src/* packages/api/src/mobile/
   ```

2. **Strategy Core Creation**
   ```bash
   # Merge strategy-related packages
   packages/strategy/ + packages/knowledge/ + packages/analytics/ 
   → packages/stratmaster-strategy/
   ```

#### Week 3: Testing and Validation
1. **Update All Import Paths**
2. **Run Comprehensive Test Suite** 
3. **Update Documentation and Examples**

### Success Criteria

#### Week 1 Success Criteria
- [ ] Target package directories created
- [ ] Import migration strategy documented  
- [ ] Migration tooling implemented

#### Week 2 Success Criteria
- [ ] First 3 package consolidations complete
- [ ] All tests passing with new structure
- [ ] Import compatibility maintained

#### Week 3 Success Criteria
- [ ] Full consolidation tested and validated
- [ ] Documentation updated
- [ ] CI/CD pipelines adapted

### Quality Gates

#### Performance Gates
- [ ] **Build time improvement**: ≥10% reduction after Sprint 1 consolidation
- [ ] **Test execution**: No regression in test suite performance
- [ ] **Environment setup**: ≥20% reduction in dependency install time

#### Quality Gates
- [ ] **Zero test failures**: All existing tests pass
- [ ] **Import compatibility**: Backward compatibility maintained
- [ ] **Documentation**: All package changes documented

## Monitoring and Success Metrics

### Quantitative Metrics
- **Package count**: 33 → 15 packages (-45%)
- **pyproject.toml files**: 33 → 15 files (-55%)
- **Build time**: Measure before/after consolidation
- **Test coverage**: Maintain >90% coverage during migration

### Qualitative Metrics  
- **Developer feedback**: Survey team on architecture clarity
- **Onboarding time**: Measure new developer setup time
- **Maintenance overhead**: Track package management effort

## Decision Rationale

### Why This Approach?
1. **Domain-Driven**: Aligns packages with business domains
2. **Incremental**: Reduces risk through phased approach
3. **Evidence-Based**: Based on Sprint 0 analysis (ARCH-001, DEP-001)
4. **Practical**: Achievable within Sprint 1-2 timeframe

### Alternatives Considered

#### Alternative 1: Big Bang Consolidation
- **Rejected**: Too risky, high probability of breaking changes

#### Alternative 2: No Consolidation
- **Rejected**: Doesn't address performance/complexity targets

#### Alternative 3: Microservice Split
- **Rejected**: Increases complexity rather than reducing it

## Related Documents
- [ARCH-001: Architecture Assessment](./ARCH-001-architecture-assessment.md)
- [DEP-001: Dependency Audit](./DEP-001-dependency-audit.md)  
- [SM_REFACTOR_STRAT.md](../../SM_REFACTOR_STRAT.md)
- [Sprint 0 Summary](./SPRINT-0-SUMMARY.md)

---

**Authors**: StratMaster Modernization Team  
**Date**: Sprint 1, Week 1
**Status**: PROPOSED → ACCEPTED (upon team review)  
**Impact**: High - Foundation for entire modernization program