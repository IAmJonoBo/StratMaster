---
title: Legacy Documentation Migration
description: Status of documentation migration to Diátaxis structure
version: 0.1.0
---

# Legacy Documentation Migration

This document tracks the migration of legacy documentation to the new Diátaxis-structured documentation system.

## Migration Status

### ✅ Fully Migrated (Superseded by new docs)

| Legacy File | New Location | Status |
|-------------|--------------|---------|
| `docs/api.md` | `docs/reference/api/gateway.md` | ✅ **Superseded** - New version is more comprehensive with test-derived examples |
| `docs/architecture.md` | `docs/explanation/architecture.md` | ✅ **Superseded** - New version has deeper technical details |
| `docs/dev-quickstart.md` | `docs/tutorials/quickstart.md` | ✅ **Superseded** - New tutorial is more comprehensive |
| `docs/development.md` | `docs/how-to/development-setup.md` | ✅ **Superseded** - New guide is more detailed |

### 🔄 Partially Migrated (Content to be integrated)

| Legacy File | Integration Target | Action Needed |
|-------------|-------------------|---------------|
| `docs/deployment.md` | `docs/tutorials/production-deployment.md` | Extract deployment tutorial content |
| `docs/infrastructure.md` | `docs/reference/configuration/` | Extract infrastructure config examples |
| `docs/security.md` | `docs/explanation/security-model.md` | Create security explanation doc |
| `docs/troubleshooting.md` | `docs/how-to/troubleshooting.md` | Create troubleshooting how-to guide |
| `docs/operations-guide.md` | `docs/how-to/operations.md` | Create operations how-to guide |

### 📋 To Be Preserved (Meta/Project docs)

| Legacy File | Status | Reason |
|-------------|--------|---------|
| `docs/backlog.md` | Keep | Project planning document |
| `docs/gap-analysis.md` | Keep | Analysis/planning document |
| `docs/upgrade-plan.md` | Keep | Project roadmap document |
| `docs/pr-blueprints.md` | Keep | Development process document |
| `docs/open-questions.md` | Keep | Active planning document |

### 🗑️ Can Be Removed (Redundant/Outdated)

| Legacy File | Reason | Action |
|-------------|--------|---------|
| `docs/CURRENT_STATE_SUMMARY.md` | Outdated snapshot | Remove after archiving |
| `docs/ENGINEERING_STATUS.md` | Outdated status | Remove after archiving |
| `docs/BRANCH_PROTECTION.md` | GitHub-specific config | Move to `.github/` or remove |

## Content Integration Plan

### High Priority (Complete documentation)
1. **Troubleshooting Guide** - Many users will need this
2. **Security Model** - Important for production deployments  
3. **Production Deployment Tutorial** - Critical for adoption

### Medium Priority (Nice to have)
1. **Operations How-to** - Useful for SRE/DevOps teams
2. **Performance Tuning Guide** - Advanced optimization
3. **Contributing Guide Enhancement** - Better onboarding

### Low Priority (Future iterations)
1. **Advanced Configuration Examples** - Power user features
2. **Integration Patterns** - Third-party integrations
3. **Migration Guides** - Version upgrade guides

## Cleanup Actions

### Safe to Remove Now
These files are fully superseded by better versions:

```bash
# Legacy API documentation (superseded by reference/api/)
rm docs/api.md

# Legacy architecture doc (superseded by explanation/architecture.md) 
rm docs/architecture.md

# Legacy dev quickstart (superseded by tutorials/quickstart.md)
rm docs/dev-quickstart.md

# Legacy development guide (superseded by how-to/development-setup.md)
rm docs/development.md

# Outdated status documents
rm docs/CURRENT_STATE_SUMMARY.md
rm docs/ENGINEERING_STATUS.md
```

### Content to Extract First
Before removing these files, extract useful content:

1. **From `docs/deployment.md`**:
   - Kubernetes deployment examples
   - Production configuration templates
   - Scaling guidance

2. **From `docs/infrastructure.md`**:
   - Service configuration examples
   - Infrastructure sizing guidelines
   - Monitoring setup instructions

3. **From `docs/security.md`**:
   - Security architecture principles
   - Threat model analysis
   - Compliance frameworks

4. **From `docs/troubleshooting.md`**:
   - Common error scenarios
   - Debugging procedures
   - Performance investigation steps

## Quality Improvements in New Docs

The new Diátaxis-structured documentation provides:

### Better Organization
- **Clear purpose** for each document type
- **Logical navigation** with hierarchical structure
- **Cross-references** between related topics

### Enhanced Content Quality  
- **Code examples derived from tests** - guaranteed accuracy
- **Version and platform metadata** - clear compatibility
- **Consistent formatting** with front-matter
- **Microsoft/Google style guide compliance**

### Improved User Experience
- **Progressive disclosure** - tutorials → how-to → reference → explanation
- **Task-oriented guidance** - clear goals and outcomes
- **Copy-paste ready examples** - tested code snippets
- **Visual hierarchy** - proper headings and navigation

## Migration Verification

To ensure no important content is lost:

1. ✅ **API Reference**: New version covers all 20 endpoints with test examples
2. ✅ **Architecture**: New version is more comprehensive with diagrams
3. ✅ **Development Setup**: New version includes troubleshooting
4. ✅ **Quick Start**: New version has complete workflow

## Next Steps

1. **Create missing how-to guides** from legacy content
2. **Extract useful examples** from infrastructure docs  
3. **Archive legacy files** before deletion
4. **Update all cross-references** to point to new structure
5. **Test navigation flows** end-to-end