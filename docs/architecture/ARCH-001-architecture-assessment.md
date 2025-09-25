# ARCH-001: StratMaster Architecture Assessment & Domain Mapping

## Executive Summary

This document provides a comprehensive assessment of the current StratMaster architecture as part of Sprint 0 of the SM_REFACTOR_STRAT.md modernization program. The assessment identifies current module boundaries, domain relationships, and opportunities for modular architecture improvements.

## Current Architecture Overview

### High-Level System Architecture

```
StratMaster Monorepo Structure:
├── apps/                    # Client Applications
│   ├── web/                # Next.js web application
│   ├── mobile/             # React Native mobile app
│   └── desktop/            # Tauri desktop application
├── packages/               # Core Business Logic (29 packages)
│   ├── api/                # Main FastAPI application
│   ├── mcp-servers/        # MCP microservices (5 servers)
│   ├── collaboration/      # Real-time collaboration (stub)
│   ├── strategy/           # Strategy generation logic
│   ├── security/           # Authentication & authorization
│   └── [24 other packages] # Various domain modules
├── infra/                  # Infrastructure definitions
├── helm/                   # Kubernetes deployment charts
└── docs/                   # Documentation (rebuilt)
```

### Domain Boundaries Analysis

#### 1. Core Domains (Well-Defined)
- **API Gateway** (`packages/api/`) - Central FastAPI application
- **Strategy Generation** (`packages/strategy/`) - Core business logic
- **Security** (`packages/security/`) - Auth, RBAC, encryption
- **Knowledge Management** (`packages/knowledge/`) - Data ingestion and processing

#### 2. MCP Microservices (Partially Modular)
- **Router MCP** - Model routing and recommendation
- **Research MCP** - Research data collection
- **Knowledge MCP** - Knowledge graph operations
- **Compression MCP** - Data compression services
- **Evals MCP** - Model evaluation

#### 3. Supporting Infrastructure (Mixed Maturity)
- **Retrieval Systems** - SPLADE, ColBERT, BGE implementations
- **Analytics** - Performance tracking and metrics
- **Integrations** - External API connections

## Current State Assessment

### Strengths
1. **Monorepo Structure**: Well-organized with clear package separation
2. **MCP Architecture**: Good foundation for microservices
3. **Documentation**: Recently rebuilt with Diátaxis framework
4. **CI/CD Infrastructure**: Comprehensive GitHub Actions workflows
5. **Containerization**: Docker support across services

### Identified Issues

#### 1. Module Boundaries (HIGH PRIORITY)
- **Cross-cutting Dependencies**: Many packages have circular or unclear dependencies
- **Domain Mixing**: Some packages combine multiple business concerns
- **Interface Contracts**: Lack of formal API contracts between modules

#### 2. Dependency Management (CRITICAL)
- **29 Packages**: Each with separate pyproject.toml files
- **Dependency Drift**: Version inconsistencies across packages
- **Build Complexity**: No unified dependency resolution

#### 3. Testing Architecture (HIGH PRIORITY)
- **Coverage Gaps**: Inconsistent test coverage across packages
- **Test Data**: No centralized test data management
- **Integration Testing**: Limited cross-package testing

## Modularization Strategy

### Proposed Domain Architecture

#### Core Application Layer
```
┌─────────────────────────────────────────────────────────┐
│                 Client Applications                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   Web UI    │ │  Mobile App │ │   Desktop Client    │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Business Logic Layer
```
┌─────────────────────────────────────────────────────────┐
│                   API Gateway                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Strategy Engine Core                      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────────────┐  │ │
│  │  │Strategy  │ │Knowledge │ │    Collaboration    │  │ │
│  │  │Services  │ │Management│ │     Services        │  │ │
│  │  └──────────┘ └──────────┘ └─────────────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### MCP Services Layer
```
┌─────────────────────────────────────────────────────────┐
│                 MCP Microservices                       │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │
│ │ Router   │ │Research  │ │Knowledge │ │   Evals     │  │
│ │   MCP    │ │   MCP    │ │   MCP    │ │    MCP      │  │
│ └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Infrastructure Layer
```
┌─────────────────────────────────────────────────────────┐
│                Infrastructure Services                  │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │
│ │Security/ │ │Analytics/│ │Retrieval │ │Infrastructure│  │
│ │  Auth    │ │Observ.   │ │ Systems  │ │  Services    │  │
│ └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Module Consolidation Plan

#### Phase 1: Core Consolidation
1. **API Gateway** - Keep as central entry point
2. **Strategy Core** - Merge strategy, knowledge, analytics packages
3. **Security Core** - Consolidate auth, security, integrations
4. **MCP Services** - Standardize interface contracts

#### Phase 2: Infrastructure Consolidation  
1. **Retrieval Engine** - Unified SPLADE/ColBERT/BGE package
2. **Data Pipeline** - Merge ingestion, verification, processing
3. **Shared Libraries** - Common utilities and models

## Key Findings & Recommendations

### 1. Immediate Actions (Sprint 1)
- **Dependency Consolidation**: Unify version management
- **Interface Contracts**: Define API boundaries between modules
- **Testing Strategy**: Establish consistent testing patterns

### 2. Medium-Term Goals (Sprint 2-3)
- **Module Refactoring**: Reduce package count from 29 to ~15
- **Shared Libraries**: Extract common patterns
- **Documentation**: Update architecture diagrams

### 3. Long-Term Vision (Sprint 4+)
- **Microservice Architecture**: True service boundaries
- **Event-Driven Communication**: Async messaging patterns
- **Infrastructure as Code**: Full automation

## Success Metrics

### Quantitative Targets
- **Module Count**: Reduce from 29 to 15 packages (-48%)
- **Dependency Conflicts**: Eliminate all version conflicts (0 conflicts)
- **Build Time**: Target 30% reduction in CI/CD pipeline duration
- **Test Coverage**: Achieve 90% coverage across core modules

### Qualitative Improvements
- **Developer Experience**: Simplified onboarding and development
- **Maintainability**: Clear ownership and responsibility boundaries
- **Scalability**: Architecture supports horizontal scaling
- **Security**: Consistent security patterns across all modules

## Next Steps

### Sprint 0 Completion
- [ ] Complete dependency audit (DEP-001)
- [ ] Establish test coverage baseline (QA-001)
- [ ] Document CI/CD performance baseline (OPS-001)

### Sprint 1 Preparation
- [ ] Draft ADRs for major architectural decisions
- [ ] Create module migration plan with timelines
- [ ] Establish quality gates for refactoring work

## Appendices

### A. Current Package Inventory
[Complete list of 29 packages with descriptions - see DEP-001 report]

### B. Dependency Graph Analysis
[Visual dependency graphs - to be completed with DEP-001]

### C. Performance Baseline
[Current build and test performance metrics - see OPS-001 report]

---

**Document Status**: Draft v1.0
**Last Updated**: Sprint 0 - Week 1
**Next Review**: End of Sprint 0
**Related Documents**: DEP-001, QA-001, OPS-001