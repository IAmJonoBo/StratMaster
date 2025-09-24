#!/bin/bash
# Quality Gate Validation Script
# Tests all documentation quality gates and standards

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run a check and report results
run_check() {
    local check_name="$1"
    local check_command="$2"
    local description="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo ""
    log_info "Running: $check_name"
    echo "Description: $description"
    echo "Command: $check_command"
    
    if eval "$check_command" > /tmp/check_output 2>&1; then
        log_success "✅ PASSED: $check_name"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "❌ FAILED: $check_name"
        echo "Error output:"
        cat /tmp/check_output || echo "No output available"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
    
    rm -f /tmp/check_output
}

echo "🚀 StratMaster Documentation Quality Gate Validation"
echo "=================================================="
echo ""
echo "This script validates all documentation quality standards including:"
echo "- Markdown linting (markdownlint)"
echo "- Spelling checks (cspell)"
echo "- Prose linting (Vale)"
echo "- Link validation (lychee)"
echo "- Documentation structure validation"
echo ""

# Check if required tools are available
log_info "Checking required tools..."

check_tool() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 is available"
    else
        log_error "$1 is not installed. Please install it first."
        echo "Installation instructions:"
        case $1 in
            "markdownlint")
                echo "npm install -g markdownlint-cli"
                ;;
            "cspell")
                echo "npm install -g cspell"
                ;;
            "vale")
                echo "See: https://vale.sh/docs/vale-cli/installation/"
                ;;
            "lychee")
                echo "cargo install lychee"
                ;;
        esac
        exit 1
    fi
}

# Check for required tools
check_tool "markdownlint"
check_tool "cspell" 
check_tool "vale"
check_tool "lychee"

echo ""
log_info "All required tools are available. Starting quality gate validation..."

# 1. Markdown Linting
run_check \
    "Markdown Linting" \
    "markdownlint --config .markdownlint.json docs/ *.md" \
    "Validates markdown files against style rules"

# 2. Spell Checking
run_check \
    "Spell Checking" \
    "cspell --config cspell.json 'docs/**/*.md' '*.md'" \
    "Checks spelling in all markdown files"

# 3. Prose Linting
run_check \
    "Prose Linting (Vale)" \
    "vale --config .vale.ini docs/" \
    "Validates prose style using Vale with Microsoft/Google guidelines"

# 4. Link Validation
run_check \
    "Link Validation" \
    "lychee --config lychee.toml docs/ *.md" \
    "Validates all internal and external links"

# 5. Documentation Structure Validation
run_check \
    "Documentation Structure" \
    "test -f docs/index.md && test -d docs/tutorials && test -d docs/how-to && test -d docs/reference && test -d docs/explanation" \
    "Validates Diátaxis documentation structure exists"

# 6. Required Files Check
run_check \
    "Required Root Files" \
    "test -f README.md && test -f CHANGELOG.md && test -f CONTRIBUTING.md && test -f SECURITY.md && test -f LICENSE" \
    "Validates all required root documentation files exist"

# 7. MkDocs Configuration
run_check \
    "MkDocs Configuration" \
    "test -f mkdocs.yml && python -c 'import yaml; yaml.safe_load(open(\"mkdocs.yml\"))'" \
    "Validates MkDocs configuration file is valid YAML"

# 8. API Documentation
run_check \
    "API Documentation" \
    "test -f docs/reference/api/openapi.md && test -f docs/reference/api/index.md" \
    "Validates API documentation files exist"

# 9. Configuration Documentation
run_check \
    "Configuration Documentation" \
    "test -f docs/reference/configuration/yaml-configs.md && test -f docs/reference/configuration/environment.md" \
    "Validates configuration documentation is complete"

# 10. Tutorial Completeness
run_check \
    "Tutorial Completeness" \
    "test -f docs/tutorials/quickstart.md && test -f docs/tutorials/first-analysis.md" \
    "Validates essential tutorials exist"

# 11. How-to Guide Completeness
run_check \
    "How-to Guide Completeness" \
    "test -f docs/how-to/development-setup.md && test -f docs/how-to/deployment.md && test -f docs/how-to/troubleshooting.md && test -f docs/how-to/infrastructure-setup.md && test -f docs/how-to/operations.md && test -f docs/how-to/faq.md" \
    "Validates all essential how-to guides exist"

# 12. Explanation Document Completeness
run_check \
    "Explanation Document Completeness" \
    "test -f docs/explanation/architecture.md && test -f docs/explanation/multi-agent-debate.md && test -f docs/explanation/security.md && test -f docs/explanation/design-decisions.md" \
    "Validates all explanation documents exist"

# 13. Cross-reference Validation
run_check \
    "Cross-reference Validation" \
    "find docs/ -name '*.md' -exec grep -o '\\[.*\\]([^h][^t][^t][^p][^)]*)' {} \\; | sed 's/.*](\\([^)]*\\)).*/\\1/' | sort | uniq | while read link; do test -f \"docs/\$link\" || { echo \"Broken link: \$link\"; exit 1; }; done" \
    "Validates all internal documentation links resolve correctly"

# 14. Image Reference Validation
run_check \
    "Image Reference Validation" \
    "grep -r '!\\[.*\\](.*)' docs/ | cut -d':' -f2 | sed 's/.*!\\[.*\\](\\([^)]*\\)).*/\\1/' | sort | uniq | while read img; do test -f \"docs/\$img\" || test -f \"\$img\" || (echo \"Missing image: \$img\" && exit 1); done || true" \
    "Validates all image references exist"

# 15. Quality Gate Metadata
run_check \
    "Quality Gate Configuration" \
    "test -f .markdownlint.json && test -f cspell.json && test -f .vale.ini && test -f lychee.toml" \
    "Validates all quality gate configuration files exist"

# 16. GitHub Workflows
run_check \
    "Documentation CI/CD" \
    "test -f .github/workflows/docs.yml && grep -q 'markdownlint\\|cspell\\|vale\\|lychee' .github/workflows/docs.yml" \
    "Validates GitHub Actions workflow includes documentation quality checks"

# 17. Documentation Build Test
if command -v mkdocs &> /dev/null; then
    run_check \
        "Documentation Build" \
        "mkdocs build --strict" \
        "Validates documentation builds successfully with strict mode"
else
    log_warning "MkDocs not available, skipping build test"
fi

# 18. README Links
run_check \
    "README Link Validation" \
    "grep -o '\\[.*\\](docs/[^)]*)' README.md | sed 's/.*](\\([^)]*\\)).*/\\1/' | while read link; do test -f \"\$link\" || (echo \"Broken README link: \$link\" && exit 1); done" \
    "Validates all documentation links in README are valid"

# Summary
echo ""
echo "======================================================"
log_info "Quality Gate Validation Summary"
echo "======================================================"
echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"

if [[ $FAILED_CHECKS -eq 0 ]]; then
    echo ""
    log_success "🎉 All quality gates passed! Documentation meets all quality standards."
    echo ""
    echo "Quality standards validated:"
    echo "✅ Markdown formatting and style"
    echo "✅ Spelling and grammar" 
    echo "✅ Prose style and readability"
    echo "✅ Link integrity and accessibility"
    echo "✅ Documentation structure completeness"
    echo "✅ Cross-reference consistency"
    echo "✅ Build and deployment readiness"
    echo ""
    exit 0
else
    echo ""
    log_error "💥 $FAILED_CHECKS quality gate(s) failed. Please fix the issues above."
    echo ""
    echo "Common fixes:"
    echo "• Run 'markdownlint --fix' to auto-fix markdown issues"
    echo "• Add missing words to cspell.json dictionary"
    echo "• Review Vale suggestions for prose improvements"
    echo "• Fix or remove broken links"
    echo "• Ensure all referenced files exist"
    echo ""
    echo "For detailed help, see docs/how-to/troubleshooting.md"
    echo ""
    exit 1
fi