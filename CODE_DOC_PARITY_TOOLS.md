# Code-Documentation Parity Tools

This directory contains advanced tools to ensure code-documentation synchronization and help developers resolve common issues.

## Tools Overview

### 1. 🔍 `code_doc_parity_validator.py`
**Comprehensive code-documentation parity validation with developer assistance**

```bash
# Quick validation check
python scripts/code_doc_parity_validator.py --api-package packages/api/src/stratmaster_api --docs-path docs/ --quick-check

# Comprehensive analysis with detailed report
python scripts/code_doc_parity_validator.py --api-package packages/api/src/stratmaster_api --docs-path docs/ --comprehensive --output parity-report.json

# Monitoring mode for CI/CD
python scripts/code_doc_parity_validator.py --api-package packages/api/src/stratmaster_api --docs-path docs/ --monitor
```

**Features:**
- Deep phantom route analysis with location tracking and fix suggestions
- Documentation quality assessment with scoring
- Code-documentation synchronization validation
- Automated fix generation
- Developer assistance tools and workflows

### 2. 🧹 `cleanup_phantom_routes.py`
**Automated phantom route cleanup with safety checks**

```bash
# Dry run to see what would be cleaned (safe)
python scripts/cleanup_phantom_routes.py --dry-run --docs-path docs/

# Actually perform the cleanup
python scripts/cleanup_phantom_routes.py --execute --docs-path docs/

# Generate cleanup report
python scripts/cleanup_phantom_routes.py --dry-run --output cleanup-report.md
```

**Features:**
- Identifies phantom routes automatically
- Analyzes cleanup strategies (remove placeholder, deprecated, etc.)
- Safe dry-run mode by default
- Generates comprehensive cleanup reports
- Manual review flagging for complex cases

### 3. 🛠️ `dev_sync_helper.py`
**One-stop developer tool for code-documentation sync**

```bash
# Quick check before committing
python scripts/dev_sync_helper.py --mode quick

# Comprehensive analysis
python scripts/dev_sync_helper.py --mode comprehensive

# Save results to file
python scripts/dev_sync_helper.py --output dev-check-results.json
```

**Features:**
- Developer-friendly summary with actionable recommendations
- Quick fixes with automated commands
- Git status integration for sync risk assessment
- CI/CD quality gate validation
- Workflow recommendations

### 4. 🎣 `pre_commit_parity_check.py`
**Pre-commit hook for code-documentation parity**

```bash
# Install as pre-commit hook
ln -s ../../scripts/pre_commit_parity_check.py .git/hooks/pre-commit

# Run manually
python scripts/pre_commit_parity_check.py
```

**Features:**
- Lightweight checks before commits
- Blocks commits only for critical issues
- Warns for non-critical issues
- Integrates with git workflow

## Usage Workflows

### For Day-to-Day Development

1. **Before making API changes:**
   ```bash
   python scripts/dev_sync_helper.py --mode quick
   ```

2. **After making API changes:**
   ```bash
   # Update documentation, then verify sync
   python scripts/dev_sync_helper.py --mode comprehensive
   ```

3. **Before committing:**
   ```bash
   python scripts/pre_commit_parity_check.py
   ```

### For Documentation Maintenance

1. **Monthly quality review:**
   ```bash
   python scripts/code_doc_parity_validator.py --api-package packages/api/src/stratmaster_api --docs-path docs/ --comprehensive --output monthly-review.json
   ```

2. **Clean up phantom routes:**
   ```bash
   python scripts/cleanup_phantom_routes.py --dry-run
   # Review the output, then:
   python scripts/cleanup_phantom_routes.py --execute
   ```

3. **Improve documentation quality:**
   ```bash
   python scripts/quality_enhancer.py docs/
   ```

### For CI/CD Integration

The tools are automatically integrated into the CI pipeline with:

- **API Documentation Coverage**: Enforces 80% minimum coverage
- **Comprehensive Parity Check**: Runs full validation on Python 3.13
- **Quality Gates**: Validates all quality standards

## Common Issues and Solutions

### Issue: "API documentation coverage is below 80%"
**Solution:**
```bash
# Generate missing documentation automatically
python scripts/api_doc_generator.py /tmp/current_parity_report.json docs/

# Then enhance quality
python scripts/quality_enhancer.py docs/
```

### Issue: "Found X phantom routes in documentation"
**Solution:**
```bash
# Clean them up automatically
python scripts/cleanup_phantom_routes.py --dry-run  # Review first
python scripts/cleanup_phantom_routes.py --execute  # Apply changes
```

### Issue: "High sync risk: API changes without documentation updates"
**Solution:**
1. Update documentation for your API changes
2. Commit documentation changes with API changes
3. Run `python scripts/dev_sync_helper.py` to verify

### Issue: "Documentation quality score below 80%"
**Solution:**
```bash
# Apply automated quality improvements
python scripts/quality_enhancer.py docs/
```

## Quality Metrics

The tools track these key metrics:

- **API Documentation Coverage**: Percentage of API routes with documentation
- **Phantom Route Count**: Number of documented but non-existent routes
- **Documentation Quality Score**: Composite score based on structure, completeness, examples, and style
- **Sync Risk Assessment**: Risk level based on uncommitted changes
- **CI Quality Gates**: Number of active vs total quality gates

## Developer Workflow Integration

### Recommended Git Workflow

1. **Feature Development:**
   ```bash
   git checkout -b feature/new-endpoint
   # Implement new API endpoint
   # Update documentation
   python scripts/dev_sync_helper.py --mode quick  # Verify sync
   git commit -m "Add new endpoint with documentation"
   ```

2. **Pull Request Creation:**
   ```bash
   python scripts/dev_sync_helper.py --mode comprehensive --output pr-check.json
   # Address any issues found
   git push origin feature/new-endpoint
   # Create PR with clean parity report
   ```

3. **Documentation Updates:**
   ```bash
   git checkout -b docs/improve-quality
   python scripts/quality_enhancer.py docs/
   python scripts/cleanup_phantom_routes.py --execute
   git commit -m "Improve documentation quality and clean phantom routes"
   ```

## Integration with Existing Tools

These new tools complement existing StratMaster quality tools:

- **API Parity Checker**: Enhanced with deep analysis and fix suggestions
- **Quality Enhancer**: Provides comprehensive quality improvements
- **Mutation Testing**: Code robustness validation
- **DORA Metrics**: Delivery performance tracking
- **SBOM Generation**: Supply chain security

## Troubleshooting

### Tool Not Working?
1. Ensure you're in the project root directory
2. Check that required scripts exist in the `scripts/` directory
3. Verify Python 3.13+ is available
4. Check that the API package path is correct

### Getting "No routes found" errors?
1. Verify the API package path: `packages/api/src/stratmaster_api`
2. Check that Python files are not corrupted
3. Ensure FastAPI routes use standard `@router.method()` decorators

### Performance Issues?
1. Use `--mode quick` for faster checks
2. The comprehensive mode is designed for thorough analysis
3. CI runs are optimized with selective checks

## Contributing

When adding new API endpoints:

1. **Document in the same commit** as the implementation
2. **Run quality checks** before committing
3. **Update relevant router documentation** files
4. **Include request/response examples** in documentation

When improving these tools:

1. **Test with the existing codebase** first
2. **Maintain backward compatibility** with existing scripts
3. **Update this README** with new features
4. **Add comprehensive error handling**

---

For more information, see the individual script help:
```bash
python scripts/code_doc_parity_validator.py --help
python scripts/cleanup_phantom_routes.py --help
python scripts/dev_sync_helper.py --help
```