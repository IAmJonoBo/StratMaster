# DEP-001: StratMaster Dependency Inventory & Risk Classification

## Executive Summary

This document provides a comprehensive audit of StratMaster's dependency landscape as part of Sprint 0 of the SM_REFACTOR_STRAT.md modernization program. The audit reveals **33 packages** with complex dependency relationships requiring consolidation and risk mitigation.

## Key Findings

### Critical Issues Identified
- **33 Separate Packages**: More than previously estimated (29), indicating higher complexity
- **Dependency Fragmentation**: Each package manages its own dependencies independently
- **Version Drift Risk**: High potential for version conflicts across packages
- **Build Complexity**: No unified dependency resolution strategy

### Immediate Risk Assessment
- **HIGH RISK**: Potential for dependency conflicts during integration
- **MEDIUM RISK**: Security vulnerabilities in unmanaged dependencies  
- **LOW RISK**: Performance impact from duplicate dependencies

## Package Inventory Analysis

### Package Categories

#### 1. Core Application Packages (6)
- `packages/api/` - Main FastAPI application
- `packages/mobile-api/` - Mobile-specific API endpoints
- `packages/dsp/` - Digital Signal Processing utilities
- `packages/orchestration_os/` - OS-level orchestration
- `packages/orchestrator/` - Main orchestration engine
- `packages/collaboration/` - Real-time collaboration (stub)

#### 2. MCP Microservices (5)
- `packages/mcp-servers/research-mcp/` - Research data collection
- `packages/mcp-servers/expertise-mcp/` - Expertise management
- `packages/mcp-servers/compression-mcp/` - Data compression
- `packages/mcp-servers/evals-mcp/` - Model evaluation
- `packages/mcp-servers/router-mcp/` - Model routing
- `packages/mcp-servers/knowledge-mcp/` - Knowledge management

#### 3. Business Logic Packages (8)
- `packages/strategy/` - Core strategy generation
- `packages/knowledge/` - Knowledge management
- `packages/security/` - Authentication & security
- `packages/analytics/` - Analytics and metrics
- `packages/agents/` - Agent management
- `packages/integrations/` - External integrations
- `packages/ingestion/` - Data ingestion
- `packages/verification/` - Data verification

#### 4. ML/Data Packages (8)
- `packages/retrieval/` - Information retrieval
- `packages/rerankers/` - Result reranking
- `packages/ml-training/` - ML model training
- `packages/evals/` - Evaluation frameworks
- `packages/providers/` - Model providers
- `packages/dataprocessing/` - Data processing
- `packages/research/` - Research utilities
- `packages/compression/` - Data compression

#### 5. Infrastructure Packages (6)
- `packages/sso-integration/` - SSO integration
- `packages/retrieval/src/splade/` - SPLADE retrieval
- `packages/retrieval/src/colbert/` - ColBERT retrieval
- `packages/rerankers/src/bge/` - BGE reranking
- `packages/verification/src/cove/` - COVE verification
- Plus nested sub-packages

## Dependency Risk Assessment

### High-Risk Dependencies

#### 1. Security-Critical Dependencies
```
Packages with auth/security concerns:
- packages/security/ - Core auth package
- packages/sso-integration/ - SSO handling  
- packages/api/ - Main API surface
- packages/mobile-api/ - Mobile API endpoints
```
**Risk**: Security vulnerabilities, auth bypass, data exposure
**Mitigation**: Centralized security dependency management, regular audits

#### 2. External API Dependencies
```
Packages with external connections:
- packages/providers/ - Model provider APIs
- packages/integrations/ - Third-party integrations
- packages/research/ - External data sources
- packages/mcp-servers/research-mcp/ - Research APIs
```
**Risk**: API changes, rate limiting, service outages
**Mitigation**: Abstraction layers, fallback strategies, monitoring

#### 3. ML/AI Model Dependencies
```
Packages with ML dependencies:
- packages/ml-training/ - Training frameworks
- packages/evals/ - Evaluation libraries
- packages/retrieval/ - ML retrieval models
- packages/rerankers/ - Ranking models
```
**Risk**: Model version compatibility, CUDA dependencies, size constraints
**Mitigation**: Version pinning, containerization, model versioning

### Medium-Risk Dependencies

#### 1. Data Processing Pipeline
```
Critical data flow packages:
- packages/ingestion/ - Data input
- packages/dataprocessing/ - Processing logic
- packages/compression/ - Data compression
- packages/verification/ - Quality assurance
```
**Risk**: Data corruption, performance bottlenecks, memory issues
**Mitigation**: Data validation, performance monitoring, backup strategies

#### 2. Infrastructure Dependencies
```
Infrastructure-related packages:
- packages/orchestrator/ - Main orchestration
- packages/orchestration_os/ - OS integration
- packages/analytics/ - Metrics collection
```
**Risk**: System resource exhaustion, monitoring gaps
**Mitigation**: Resource limits, comprehensive monitoring

## Version Conflict Analysis

### Detected Potential Conflicts

#### Python Version Requirements
```
All packages specify: python >=3.11
Base system: Python 3.12
Status: ✅ COMPATIBLE
```

#### FastAPI Versions
```
Multiple packages use FastAPI:
- packages/api/: fastapi >=0.117.1
- packages/mobile-api/: [needs audit]
- packages/mcp-servers/*/: fastapi >=0.117.1
Status: ⚠️ NEEDS VERIFICATION
```

#### Pydantic Versions  
```
Critical dependency across packages:
- packages/api/: pydantic >=2.5.0
- packages/orchestrator/: pydantic >=2.11.9
- Multiple others: various pydantic versions
Status: ⚠️ VERSION DRIFT RISK
```

## Consolidation Recommendations

### Phase 1: Immediate Consolidation (Sprint 1)
1. **Root-Level Dependency Management**
   - Move all dependencies to root `pyproject.toml`
   - Use workspace/monorepo dependency resolution
   - Eliminate per-package dependency files

2. **Version Standardization**
   - Pin critical dependencies (FastAPI, Pydantic, Python)
   - Establish version update policy
   - Create dependency upgrade automation

### Phase 2: Package Consolidation (Sprint 2)
1. **Merge Related Packages**
   - Combine retrieval sub-packages into single `retrieval`
   - Merge MCP servers with similar functionality
   - Consolidate utility packages

2. **Create Shared Libraries**
   - Extract common utilities across packages
   - Create shared models and schemas
   - Establish common interfaces

### Phase 3: Architecture Optimization (Sprint 3-4)
1. **Domain-Driven Consolidation**
   - Group packages by business domain
   - Reduce from 33 to target of 12-15 packages
   - Clear ownership and responsibility boundaries

## Security Assessment

### Vulnerability Scan Results
```bash
# Requires security tooling setup
pip-audit --format=json > security-report.json
safety check --json > safety-report.json
```
**Status**: TO BE COMPLETED with security tooling setup

### Dependency Licenses
```bash
# Requires license scanning
pip-licenses --format=json > license-report.json
```
**Status**: TO BE COMPLETED with license compliance check

## Quality Gates

### Dependency Management Metrics
- [ ] **Zero Version Conflicts**: All packages use compatible versions
- [ ] **Security Clean**: No high/critical vulnerabilities
- [ ] **License Compliance**: All dependencies have compatible licenses
- [ ] **Build Performance**: <5 minute full environment setup

### Consolidation Targets
- [ ] **Package Count**: Reduce from 33 to 15 packages (-45%)
- [ ] **Dependency Deduplication**: Eliminate duplicate dependencies
- [ ] **Root Management**: Single source of dependency truth
- [ ] **Automated Updates**: Dependency update automation in place

## Implementation Plan

### Sprint 1 Actions
1. **Create Root Dependency File**
   - Consolidate all dependencies into root `pyproject.toml`
   - Set up workspace-style dependency management
   - Remove individual package dependency files

2. **Version Conflict Resolution**
   - Identify and resolve all version conflicts
   - Pin critical dependency versions
   - Test full environment builds

3. **Security Baseline**
   - Run comprehensive security scans
   - Address any high/critical vulnerabilities
   - Set up automated security monitoring

### Sprint 2+ Actions
1. **Package Consolidation**
   - Merge related packages based on ARCH-001 recommendations
   - Refactor import paths and module structure
   - Update documentation and build scripts

2. **Shared Library Creation**
   - Extract common patterns into shared libraries
   - Establish consistent API patterns
   - Create package templates for future work

## Monitoring & Maintenance

### Automated Dependency Management
1. **Renovate/Dependabot Setup**
   - Automated dependency update PRs
   - Security vulnerability notifications
   - Version compatibility testing

2. **Quality Checks**
   - Pre-commit hooks for dependency validation
   - CI/CD gates for security and compatibility
   - Regular dependency audits (monthly)

### Success Metrics
- **Build Time**: 30% reduction in CI/CD pipeline duration
- **Developer Experience**: 40% reduction in onboarding time
- **Security Posture**: Zero high/critical vulnerabilities maintained
- **Maintenance Overhead**: 50% reduction in dependency management effort

## Next Steps

### Sprint 0 Completion
- [ ] Complete security vulnerability scan
- [ ] Document license compliance status
- [ ] Create detailed consolidation roadmap

### Sprint 1 Preparation  
- [ ] Design root dependency management structure
- [ ] Plan package merge sequence and rollback strategy
- [ ] Set up automated dependency monitoring

---

**Document Status**: Draft v1.0  
**Packages Assessed**: 33 packages
**Last Updated**: Sprint 0 - Week 1
**Next Review**: End of Sprint 0
**Related Documents**: ARCH-001, QA-001, OPS-001