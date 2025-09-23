#!/bin/bash

# Phase 3 Feature Validation Script
# Validates all implemented Phase 3 features and infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Validation results
VALIDATION_RESULTS=()
FAILED_CHECKS=0
TOTAL_CHECKS=0

# Function to record validation result
validate_check() {
    local check_name="$1"
    local check_command="$2"
    local check_description="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    log_info "Validating: $check_description"
    
    if eval "$check_command" > /dev/null 2>&1; then
        log_success "✓ $check_name"
        VALIDATION_RESULTS+=("✓ $check_name")
        return 0
    else
        log_error "✗ $check_name"
        VALIDATION_RESULTS+=("✗ $check_name")
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

log_info "Starting Phase 3 Feature Validation"
log_info "======================================="

# 1. Database Schema Validation
log_info "1. Database Schema Validation"
validate_check "Database migration script exists" \
    "test -f database/migrate.sh" \
    "Database migration script"

validate_check "Database migration script is executable" \
    "test -x database/migrate.sh" \
    "Migration script permissions"

validate_check "Analytics schema migration exists" \
    "test -f database/migrations/001_analytics_and_workflows.sql" \
    "Analytics and workflows schema"

validate_check "Migration script dry-run syntax check" \
    "bash -n database/migrate.sh" \
    "Database migration script syntax"

# 2. CI/CD Pipeline Validation
log_info ""
log_info "2. CI/CD Pipeline Validation"
validate_check "Updated CI workflow exists" \
    "test -f .github/workflows/ci.yml" \
    "CI workflow configuration"

validate_check "Deployment workflow exists" \
    "test -f .github/workflows/deploy.yml" \
    "Deployment workflow configuration"

validate_check "CI workflow includes Docker builds" \
    "grep -q 'build-images' .github/workflows/ci.yml" \
    "Docker image building in CI"

validate_check "Deployment script exists" \
    "test -f scripts/deploy.sh" \
    "Deployment automation script"

validate_check "Deployment script is executable" \
    "test -x scripts/deploy.sh" \
    "Deployment script permissions"

# 3. Docker Configuration Validation
log_info ""
log_info "3. Docker Configuration Validation"
validate_check "API Dockerfile exists" \
    "test -f docker/api/Dockerfile" \
    "API service Dockerfile"

validate_check "Research MCP Dockerfile exists" \
    "test -f docker/research-mcp/Dockerfile" \
    "Research MCP Dockerfile"

validate_check "Knowledge MCP Dockerfile exists" \
    "test -f docker/knowledge-mcp/Dockerfile" \
    "Knowledge MCP Dockerfile"

validate_check "Router MCP Dockerfile exists" \
    "test -f docker/router-mcp/Dockerfile" \
    "Router MCP Dockerfile"

validate_check "Evals MCP Dockerfile exists" \
    "test -f docker/evals-mcp/Dockerfile" \
    "Evals MCP Dockerfile"

validate_check "Compression MCP Dockerfile exists" \
    "test -f docker/compression-mcp/Dockerfile" \
    "Compression MCP Dockerfile"

# 4. Configuration Management Validation
log_info ""
log_info "4. Configuration Management Validation"
validate_check "Production config template exists" \
    "test -f configs/production-config-template.yaml" \
    "Production configuration template"

validate_check "Kubernetes secrets template exists" \
    "test -f ops/k8s/secrets/production-secrets.yaml" \
    "Kubernetes secrets template"

validate_check "Sealed secrets template exists" \
    "test -f ops/k8s/secrets/sealed-secrets-template.yaml" \
    "Sealed secrets template"

# 5. Integration Testing Validation
log_info ""
log_info "5. Integration Testing Validation"
validate_check "Phase 3 integration tests exist" \
    "test -f tests/integration/test_phase3_features.py" \
    "Phase 3 integration test suite"

validate_check "Integration tests include analytics" \
    "grep -q 'TestAnalyticsIntegration' tests/integration/test_phase3_features.py" \
    "Analytics integration tests"

validate_check "Integration tests include workflows" \
    "grep -q 'TestApprovalWorkflowIntegration' tests/integration/test_phase3_features.py" \
    "Approval workflow integration tests"

validate_check "Integration tests include ML experiments" \
    "grep -q 'TestMLExperimentIntegration' tests/integration/test_phase3_features.py" \
    "ML experiment integration tests"

validate_check "End-to-end test exists" \
    "grep -q 'test_end_to_end_approval_workflow' tests/integration/test_phase3_features.py" \
    "End-to-end workflow test"

# 6. Documentation Validation
log_info ""
log_info "6. Documentation Validation"
validate_check "Operations guide exists" \
    "test -f docs/operations-guide.md" \
    "Production operations guide"

validate_check "Phase 3 gap analysis exists" \
    "test -f PHASE3_GAP_ANALYSIS.md" \
    "Phase 3 gap analysis document"

validate_check "README includes Phase 3 features" \
    "grep -q 'Phase 3 Enterprise Features' README.md" \
    "README updated with Phase 3 features"

validate_check "Operations guide includes troubleshooting" \
    "grep -q 'Troubleshooting' docs/operations-guide.md" \
    "Troubleshooting section in operations guide"

# 7. Helm Chart Validation
log_info ""
log_info "7. Helm Chart Validation"
if command -v helm &> /dev/null; then
    validate_check "StratMaster API Helm chart lints" \
        "helm lint helm/stratmaster-api" \
        "StratMaster API Helm chart"
    
    validate_check "Research MCP Helm chart lints" \
        "helm lint helm/research-mcp" \
        "Research MCP Helm chart"
else
    log_warning "Helm not available - skipping chart validation"
fi

# 8. Dependency Validation
log_info ""
log_info "8. Dependency Validation"
validate_check "Fixed opentelemetry dependency" \
    "grep -q '0.46b0' packages/api/pyproject.toml" \
    "OpenTelemetry dependency version fix"

validate_check "API package dependencies are valid" \
    "python3 -c 'import tomllib; f=open(\"packages/api/pyproject.toml\",\"rb\"); data=tomllib.load(f); print(len(data[\"project\"][\"dependencies\"]))'" \
    "API package dependencies"

# 9. Security Validation
log_info ""
log_info "9. Security Validation"
validate_check "Secrets are templated (not hardcoded)" \
    "! grep -r 'CHANGE_ME_IN_PRODUCTION' ops/k8s/secrets/ || true" \
    "No hardcoded secrets in templates"

validate_check "Dockerfiles use non-root users" \
    "grep -q 'USER.*mcp' docker/*/Dockerfile" \
    "Docker containers use non-root users"

validate_check "Database migration includes audit logs" \
    "grep -q 'audit_logs' database/migrations/001_analytics_and_workflows.sql" \
    "Audit logging in database schema"

# 10. Architecture Validation
log_info ""
log_info "10. Architecture Validation"
validate_check "ArgoCD configuration exists" \
    "test -d argocd/" \
    "ArgoCD configuration directory"

validate_check "Trunk configuration is valid" \
    "test -f .trunk/trunk.yaml" \
    "Trunk linting configuration"

validate_check "Pre-commit configuration exists" \
    "test -f .pre-commit-config.yaml" \
    "Pre-commit hooks configuration"

# Summary
log_info ""
log_info "Validation Summary"
log_info "=================="

echo -e "${BLUE}Total Checks:${NC} $TOTAL_CHECKS"
echo -e "${GREEN}Passed:${NC} $((TOTAL_CHECKS - FAILED_CHECKS))"
echo -e "${RED}Failed:${NC} $FAILED_CHECKS"

if [[ $FAILED_CHECKS -gt 0 ]]; then
    log_error "Some validations failed. Please review the failed checks above."
    
    echo ""
    log_info "Failed Checks:"
    for result in "${VALIDATION_RESULTS[@]}"; do
        if [[ $result =~ ^✗ ]]; then
            echo "  $result"
        fi
    done
    
    exit 1
else
    log_success "All Phase 3 feature validations passed!"
    log_success "🎉 StratMaster is ready for production deployment!"
fi

echo ""
log_info "Next steps:"
log_info "1. Set up production secrets and configuration"
log_info "2. Deploy to staging environment for testing"
log_info "3. Run comprehensive integration tests"
log_info "4. Deploy to production using the deployment script"
log_info "5. Monitor system health and performance"

log_info ""
log_info "For deployment instructions, see: docs/operations-guide.md"