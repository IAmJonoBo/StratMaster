#!/usr/bin/env python3
"""
GitHub Issues Creation Script for SM_REFACTOR_STRAT.md Implementation

This script generates formatted GitHub issue bodies from the existing issue templates
in the /issues directory and the SM_REFACTOR_STRAT.md Sprint 0 requirements.

Usage:
    python scripts/create_github_issues.py

Output:
    Creates markdown files ready for manual GitHub issue creation
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any

def read_issue_template(issue_path: Path) -> Dict[str, str]:
    """Read an issue template and extract title and body."""
    with open(issue_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title from first heading
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"Issue from {issue_path.stem}"
    
    # Convert to implementation title format
    if "Issue" in title and ":" in title:
        title = title.split(":", 1)[1].strip()
    
    title = f"[IMPL] {title}"
    
    return {
        'title': title,
        'body': content,
        'path': str(issue_path)
    }

def generate_sprint_0_issue() -> Dict[str, str]:
    """Generate the Sprint 0 mobilization issue from SM_REFACTOR_STRAT.md."""
    return {
        'title': '[SPRINT-0] Mobilize & Baseline - Architecture Assessment & Dependency Audit',
        'body': '''## Epic Overview
Implement Sprint 0 of the SM_REFACTOR_STRAT.md program: Mobilize & Baseline activities (Weeks 1-3) to capture current architecture, define modularization strategy, and establish tooling baselines.

## Sprint 0 Objectives  
- Capture current architecture, runtime, and dependency graph
- Define modularization strategy and target operating model
- Establish tooling baselines for testing and virtual environment setup

## Issues / Epics from SM_REFACTOR_STRAT.md
1. `ARCH-001` Architecture Assessment & Domain Mapping
2. `DEP-001` Dependency Inventory & Risk Classification  
3. `QA-001` Test Coverage Benchmarking & Test Data Audit
4. `OPS-001` CI/CD & Virtual Environment Baseline Analysis

## Key Activities Checklist
- [ ] **Architecture Discovery**: Run automated architecture discovery scripts; document data flow diagrams
- [ ] **Dependency Analysis**: Classify dependencies by criticality, EOL status, and upgrade path
- [ ] **Test Analysis**: Analyze test suites for coverage, flakiness, and runtime
- [ ] **Environment Baseline**: Measure setup time for current virtual environments and Docker images

## Quality Gates
- [ ] **ADR Creation**: Architecture decision records (ADR) for module boundaries drafted
- [ ] **Security Review**: Dependency risk matrix approved by security
- [ ] **Coverage Baseline**: Baseline coverage report validated (unit, integration, end-to-end)
- [ ] **DevOps Audit**: CI/CD audit report reviewed by DevOps guild

## Deliverables
- [ ] **Baseline Architecture Workbook**: Complete current state documentation + ADR backlog
- [ ] **Dependency Audit Report**: Upgrade priority backlog with risk assessment
- [ ] **Test Coverage Heatmap**: Coverage metrics + data quality findings
- [ ] **CI/CD Benchmark Report**: Environment setup performance baseline

## Implementation Tasks

### ARCH-001: Architecture Assessment & Domain Mapping
- [ ] Document current module boundaries and dependencies
- [ ] Create data flow diagrams for key user journeys
- [ ] Identify modularization opportunities and anti-patterns
- [ ] Draft ADRs for proposed module boundaries

### DEP-001: Dependency Inventory & Risk Classification
- [ ] Catalog all 29 packages and their dependency trees
- [ ] Classify dependencies by criticality (core, optional, dev)
- [ ] Identify EOL packages and security vulnerabilities
- [ ] Create upgrade priority matrix

### QA-001: Test Coverage Benchmarking & Test Data Audit  
- [ ] Generate comprehensive test coverage report
- [ ] Analyze test execution times and identify flaky tests
- [ ] Audit test data quality and maintainability
- [ ] Document testing gaps and improvement opportunities

### OPS-001: CI/CD & Virtual Environment Baseline Analysis
- [ ] Measure current CI/CD pipeline performance
- [ ] Benchmark virtual environment setup times
- [ ] Document Docker image sizes and build times
- [ ] Identify optimization opportunities

## Success Criteria
- Complete understanding of current architecture documented
- Clear modularization strategy defined with stakeholder buy-in
- Baseline metrics established for all quality improvements
- Foundation ready for Sprint 1 implementation work

## Timeline
**Duration:** 3 weeks (Sprint 0)
**Dependencies:** None - this is the foundation sprint
**Blocks:** All subsequent sprints depend on baseline completion

## Documentation Updates
- [ ] **Architecture docs**: Current state diagrams and proposed future state
- [ ] **Development guides**: Updated setup and testing procedures
- [ ] **Decision records**: ADRs for major architectural decisions

## Quality Metrics Targets (from SM_REFACTOR_STRAT.md)
- 30% reduction in build pipeline duration
- 90% automated test coverage on core modules
- Zero critical security vulnerabilities
- 40% reduction in onboarding time

## Related Work
- Follows SM_REFACTOR_STRAT.md Sprint 0 definition
- Enables subsequent Sprint 1-4 implementation work
- Establishes quality gates for modernization targets''',
        'path': 'SM_REFACTOR_STRAT.md Sprint 0'
    }

def create_issue_creation_script():
    """Create a comprehensive script for GitHub issue creation."""
    
    # Get all issue templates
    issues_dir = Path('issues')
    issue_files = []
    
    if issues_dir.exists():
        issue_files = list(issues_dir.glob('*.md'))
        issue_files.sort()
    
    issues = []
    
    # Add Sprint 0 issue first
    issues.append(generate_sprint_0_issue())
    
    # Add implementation issues
    for issue_file in issue_files:
        try:
            issue = read_issue_template(issue_file)
            issues.append(issue)
        except Exception as e:
            print(f"Warning: Could not process {issue_file}: {e}")
    
    # Write individual issue files
    output_dir = Path('github_issues_ready')
    output_dir.mkdir(exist_ok=True)
    
    # Write summary file
    summary_content = f"""# GitHub Issues for SM_REFACTOR_STRAT.md Implementation

This directory contains {len(issues)} GitHub issues ready for creation to implement the SM_REFACTOR_STRAT.md modernization program.

## Issues Overview

### Sprint 0 (Foundation)
1. **Sprint 0 Mobilization** - Architecture assessment, dependency audit, test coverage baseline

### Implementation Issues (P0-Critical)
"""
    
    for i, issue in enumerate(issues):
        # Write individual issue file
        issue_filename = f"issue_{i+1:02d}_{issue['title'].replace('[', '').replace(']', '').replace(' ', '_').replace('/', '_').lower()}.md"
        issue_filename = re.sub(r'[^a-z0-9_.]', '', issue_filename)
        
        issue_file_path = output_dir / issue_filename
        
        # Create full issue content
        full_content = f"""# {issue['title']}

**Labels:** enhancement, SM_REFACTOR_STRAT, implementation
**Priority:** P0 (for Sprint 0 and first 3 issues), P1 (for others)
**Milestone:** SM_REFACTOR_STRAT Modernization Program

---

{issue['body']}

---

## How to Create This Issue

1. Go to https://github.com/IAmJonoBo/StratMaster/issues/new
2. Copy the title: `{issue['title']}`
3. Copy the body content above (between the --- lines)
4. Add labels: `enhancement`, `SM_REFACTOR_STRAT`, `implementation`
5. Set appropriate priority and milestone
6. Create the issue

**Source:** Generated from {issue['path']}
"""
        
        with open(issue_file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        # Add to summary
        summary_content += f"{i+1}. **{issue['title']}**\\n"
    
    # Write summary and instructions
    summary_content += f"""

## Manual Creation Instructions

1. **Individual Issues**: Each issue file in this directory contains:
   - Ready-to-copy title and body
   - Suggested labels and priority
   - Step-by-step creation instructions

2. **Batch Creation**: 
   - Start with Sprint 0 issue (foundation for all other work)
   - Create P0-critical issues next (001-003) 
   - Create remaining issues based on sprint schedule

3. **Labels to Apply**:
   - `enhancement` - for all implementation issues
   - `SM_REFACTOR_STRAT` - to track the modernization program
   - `implementation` - to distinguish from bugs/features
   - `P0-critical` - for Sprint 0 and issues 001-003
   - `sprint-0`, `sprint-1`, etc. - for sprint tracking

## Sprint Schedule (from SM_REFACTOR_STRAT.md)

- **Sprint 0 (Weeks 1-3)**: Mobilize & Baseline
- **Sprint 1 (Weeks 4-6)**: Modular Architecture Foundations  
- **Sprint 2 (Weeks 7-9)**: Dependency Modernization & Compatibility
- **Sprint 3 (Weeks 10-12)**: Testing & Quality Expansion
- **Sprint 4 (Weeks 13-15)**: CI/CD Evolution & Environment Optimization

## Success Metrics

The SM_REFACTOR_STRAT.md program targets:
- 30% reduction in build pipeline duration
- 90% automated test coverage on core modules
- Zero critical security vulnerabilities  
- 40% reduction in onboarding time

Created: {len(issues)} issues ready for GitHub creation
"""
    
    with open(output_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"✅ Created {len(issues)} GitHub issue files in {output_dir}/")
    print(f"📋 See {output_dir}/README.md for creation instructions")
    
    return len(issues)

if __name__ == "__main__":
    issues_created = create_issue_creation_script()
    print(f"\\n🚀 Ready to create {issues_created} GitHub issues for SM_REFACTOR_STRAT.md implementation!")