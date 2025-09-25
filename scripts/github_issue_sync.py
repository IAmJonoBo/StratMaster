#!/usr/bin/env python3
"""
StratMaster GitHub Issue Synchronization Tool

Creates and synchronizes GitHub issues for the V2 development roadmap
based on SM_REFACTOR_STRAT.md and implementation plans.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class GitHubIssueTemplate:
    def __init__(self, title: str, body: str, labels: List[str], 
                 milestone: Optional[str] = None, priority: str = 'P2'):
        self.title = title
        self.body = body
        self.labels = labels
        self.milestone = milestone
        self.priority = priority
        self.created = False
        self.issue_number = None

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'body': self.body,
            'labels': self.labels,
            'milestone': self.milestone,
            'priority': self.priority,
            'created': self.created,
            'issue_number': self.issue_number
        }

class GitHubIssueSyncer:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.issues_dir = self.project_root / 'issues'
        self.github_ready_dir = self.project_root / 'github_issues_ready'
        self.sync_status_file = self.project_root / 'github_issue_sync_status.json'
        
        # Load existing sync status
        self.sync_status = self._load_sync_status()
    
    def _load_sync_status(self) -> Dict:
        """Load existing sync status or create new one."""
        if self.sync_status_file.exists():
            with open(self.sync_status_file) as f:
                return json.load(f)
        
        return {
            'last_sync': None,
            'synced_issues': {},
            'failed_issues': [],
            'total_issues': 0,
            'created_issues': 0
        }
    
    def _save_sync_status(self):
        """Save sync status to file."""
        self.sync_status['last_sync'] = datetime.now().isoformat()
        with open(self.sync_status_file, 'w') as f:
            json.dump(self.sync_status, f, indent=2)
    
    def discover_issue_templates(self) -> List[GitHubIssueTemplate]:
        """Discover all issue templates from issues/ and github_issues_ready/ directories."""
        print("🔍 Discovering issue templates...")
        
        templates = []
        
        # Process issues from issues/ directory
        if self.issues_dir.exists():
            for issue_file in self.issues_dir.glob('*.md'):
                template = self._parse_issue_file(issue_file, 'implementation')
                if template:
                    templates.append(template)
        
        # Process issues from github_issues_ready/ directory
        if self.github_ready_dir.exists():
            for issue_file in self.github_ready_dir.glob('issue_*.md'):
                template = self._parse_github_ready_file(issue_file)
                if template:
                    templates.append(template)
        
        print(f"✅ Discovered {len(templates)} issue templates")
        return templates
    
    def _parse_issue_file(self, file_path: Path, category: str) -> Optional[GitHubIssueTemplate]:
        """Parse issue file from issues/ directory."""
        try:
            content = file_path.read_text()
            lines = content.split('\n')
            
            # Extract title (first heading)
            title = None
            for line in lines:
                if line.startswith('#') and not line.startswith('##'):
                    title = line.strip('#').strip()
                    break
            
            if not title:
                title = file_path.stem.replace('-', ' ').title()
            
            # Determine labels and priority based on filename
            labels = ['enhancement', 'SM_REFACTOR_STRAT', 'implementation', 'v2']
            priority = 'P2'
            milestone = None
            
            filename = file_path.stem.lower()
            if any(p0_term in filename for p0_term in ['001-', '002-', '003-', 'collaboration', 'model-recommender', 'retrieval']):
                labels.append('P0-critical')
                priority = 'P0'
                milestone = 'M1: Real-Time Foundation'
            elif any(p1_term in filename for p1_term in ['004-', '005-', 'caching', 'ux-quality']):
                labels.append('P1-important')
                priority = 'P1'
                milestone = 'M2: Performance & Validation'
            else:
                labels.append('P2-enhancement')
                milestone = 'M3: Advanced Analytics'
            
            return GitHubIssueTemplate(title, content, labels, milestone, priority)
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def _parse_github_ready_file(self, file_path: Path) -> Optional[GitHubIssueTemplate]:
        """Parse issue file from github_issues_ready/ directory."""
        try:
            content = file_path.read_text()
            lines = content.split('\n')
            
            # Extract title and body from the structured format
            title = None
            body_lines = []
            in_body = False
            
            for line in lines:
                if line.startswith('# Title:'):
                    title = line.replace('# Title:', '').strip()
                elif line.startswith('## Body:') or line.startswith('## Issue Body:'):
                    in_body = True
                    continue
                elif in_body and line.startswith('## '):
                    in_body = False
                elif in_body:
                    body_lines.append(line)
            
            if not title:
                # Fallback to filename
                title = file_path.stem.replace('issue_', '').replace('_', ' ').title()
            
            body = '\n'.join(body_lines).strip()
            if not body:
                body = content  # Use full content as fallback
            
            # Determine labels and priority
            labels = ['enhancement', 'SM_REFACTOR_STRAT', 'implementation', 'v2']
            priority = 'P1'
            milestone = None
            
            filename = file_path.stem.lower()
            if 'sprint0' in filename or 'mobilize' in filename:
                labels.extend(['P0-critical', 'sprint-0'])
                priority = 'P0'
                milestone = 'Sprint 0: Mobilize & Baseline'
            elif any(p0_term in filename for p0_term in ['realtime', 'collaboration', 'model_recommender', 'retrieval']):
                labels.extend(['P0-critical', 'sprint-1'])
                priority = 'P0'
                milestone = 'M1: Real-Time Foundation'
            elif any(p1_term in filename for p1_term in ['caching', 'performance', 'ux_quality']):
                labels.extend(['P1-important', 'sprint-2'])
                priority = 'P1'
                milestone = 'M2: Performance & Validation'
            else:
                labels.extend(['P2-enhancement', 'sprint-3'])
                milestone = 'M3: Advanced Analytics'
            
            return GitHubIssueTemplate(title, body, labels, milestone, priority)
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def generate_cli_commands(self, templates: List[GitHubIssueTemplate]) -> List[str]:
        """Generate GitHub CLI commands for issue creation."""
        commands = []
        
        print("📝 Generating GitHub CLI commands...")
        
        for template in templates:
            # Prepare labels string
            labels_str = ','.join(template.labels)
            
            # Prepare body content (escape for CLI)
            body_content = template.body.replace('"', '\\"').replace('\n', '\\n')
            
            # Create CLI command
            cmd_parts = [
                'gh issue create',
                f'--title "{template.title}"',
                f'--body "{body_content}"',
                f'--label "{labels_str}"'
            ]
            
            if template.milestone:
                cmd_parts.append(f'--milestone "{template.milestone}"')
            
            commands.append(' '.join(cmd_parts))
        
        return commands
    
    def generate_batch_script(self, templates: List[GitHubIssueTemplate]) -> str:
        """Generate a batch script for creating all issues."""
        script_lines = [
            '#!/bin/bash',
            '# StratMaster V2 GitHub Issues Creation Script',
            '# Generated by github_issue_sync.py',
            '',
            'set -e  # Exit on error',
            '',
            '# Check if GitHub CLI is installed',
            'if ! command -v gh &> /dev/null; then',
            '    echo "Error: GitHub CLI (gh) is not installed"',
            '    echo "Install it from: https://cli.github.com/"',
            '    exit 1',
            'fi',
            '',
            '# Check if authenticated',
            'if ! gh auth status &> /dev/null; then',
            '    echo "Error: Not authenticated with GitHub CLI"',
            '    echo "Run: gh auth login"',
            '    exit 1',
            'fi',
            '',
            'echo "🚀 Creating StratMaster V2 GitHub Issues..."',
            'echo ""',
            '',
            'CREATED_COUNT=0',
            'FAILED_COUNT=0',
            'TOTAL_ISSUES=' + str(len(templates)),
            ''
        ]
        
        for i, template in enumerate(templates, 1):
            # Create safe filename for body content
            body_file = f"issue_{i}_body.txt"
            
            script_lines.extend([
                f'# Issue {i}: {template.title}',
                f'echo "Creating issue {i}/{len(templates)}: {template.title}"',
                f'cat > "{body_file}" << \'EOF\'',
                template.body,
                'EOF',
                ''
            ])
            
            # Build gh command
            labels_str = ','.join(template.labels)
            cmd_parts = [
                'if gh issue create',
                f'  --title "{template.title}"',
                f'  --body-file "{body_file}"',
                f'  --label "{labels_str}"'
            ]
            
            if template.milestone:
                cmd_parts.append(f'  --milestone "{template.milestone}"')
            
            script_lines.extend([
                ' '.join(cmd_parts) + '; then',
                '    echo "✅ Created successfully"',
                '    CREATED_COUNT=$((CREATED_COUNT + 1))',
                'else',
                '    echo "❌ Failed to create"',
                '    FAILED_COUNT=$((FAILED_COUNT + 1))',
                'fi',
                f'rm -f "{body_file}"',
                'echo ""',
                ''
            ])
        
        script_lines.extend([
            'echo "📊 Summary:"',
            'echo "  Total issues: $TOTAL_ISSUES"',
            'echo "  Created: $CREATED_COUNT"',
            'echo "  Failed: $FAILED_COUNT"',
            '',
            'if [ $FAILED_COUNT -eq 0 ]; then',
            '    echo "🎉 All issues created successfully!"',
            '    exit 0',
            'else',
            '    echo "⚠️  Some issues failed to create"',
            '    exit 1',
            'fi'
        ])
        
        return '\n'.join(script_lines)
    
    def generate_manual_instructions(self, templates: List[GitHubIssueTemplate]) -> str:
        """Generate manual instructions for creating issues."""
        instructions = """# Manual GitHub Issues Creation Instructions

Since automated GitHub issue creation requires repository write permissions, follow these steps to manually create all issues:

## Prerequisites
1. Navigate to: https://github.com/IAmJonoBo/StratMaster/issues
2. Ensure you have write access to the repository
3. Have this instruction file open for reference

## Issue Creation Steps

For each issue below:
1. Click "New issue" button
2. Copy the **Title** exactly as shown
3. Copy the **Body** content into the issue description
4. Add **Labels** as specified
5. Set **Milestone** if provided
6. Click "Submit new issue"

---

"""
        
        for i, template in enumerate(templates, 1):
            instructions += f"""
## Issue {i}: {template.title}

**Priority:** {template.priority}
**Milestone:** {template.milestone or 'None'}

### Title (copy this exactly):
```
{template.title}
```

### Labels to add:
```
{', '.join(template.labels)}
```

### Body content (copy everything below):
```
{template.body}
```

---
"""
        
        instructions += f"""

## Summary
- **Total Issues**: {len(templates)}
- **P0-Critical**: {len([t for t in templates if t.priority == 'P0'])}
- **P1-Important**: {len([t for t in templates if t.priority == 'P1'])}
- **P2-Enhancement**: {len([t for t in templates if t.priority == 'P2'])}

## Milestones to Create (if not exists):
- Sprint 0: Mobilize & Baseline
- M1: Real-Time Foundation  
- M2: Performance & Validation
- M3: Advanced Analytics

After creating all issues, they will be automatically linked and trackable through GitHub's project management features.
"""
        
        return instructions
    
    def export_sync_files(self, templates: List[GitHubIssueTemplate]) -> Dict[str, Path]:
        """Export synchronization files for different methods."""
        output_files = {}
        
        # Generate CLI commands file
        cli_commands = self.generate_cli_commands(templates)
        cli_file = self.project_root / 'github_cli_commands.txt'
        cli_file.write_text('\n'.join(cli_commands))
        output_files['cli_commands'] = cli_file
        
        # Generate batch script
        batch_script = self.generate_batch_script(templates)
        batch_file = self.project_root / 'create_github_issues.sh'
        batch_file.write_text(batch_script)
        batch_file.chmod(0o755)  # Make executable
        output_files['batch_script'] = batch_file
        
        # Generate manual instructions
        manual_instructions = self.generate_manual_instructions(templates)
        manual_file = self.project_root / 'GITHUB_ISSUES_MANUAL.md'
        manual_file.write_text(manual_instructions)
        output_files['manual_instructions'] = manual_file
        
        # Generate JSON export for programmatic use
        json_export = {
            'generated_date': datetime.now().isoformat(),
            'total_issues': len(templates),
            'issues': [template.to_dict() for template in templates]
        }
        json_file = self.project_root / 'github_issues_export.json'
        json_file.write_text(json.dumps(json_export, indent=2))
        output_files['json_export'] = json_file
        
        return output_files
    
    def validate_templates(self, templates: List[GitHubIssueTemplate]) -> Tuple[bool, List[str]]:
        """Validate issue templates for completeness."""
        print("🔍 Validating issue templates...")
        
        errors = []
        
        for i, template in enumerate(templates, 1):
            if not template.title or len(template.title.strip()) < 5:
                errors.append(f"Issue {i}: Title too short or empty")
            
            if not template.body or len(template.body.strip()) < 20:
                errors.append(f"Issue {i}: Body too short or empty")
            
            if not template.labels:
                errors.append(f"Issue {i}: No labels specified")
            
            required_labels = {'enhancement', 'SM_REFACTOR_STRAT', 'implementation', 'v2'}
            if not required_labels.issubset(set(template.labels)):
                missing = required_labels - set(template.labels)
                errors.append(f"Issue {i}: Missing required labels: {missing}")
        
        if errors:
            print(f"❌ Validation failed with {len(errors)} errors")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"✅ All {len(templates)} templates validated successfully")
        
        return len(errors) == 0, errors
    
    def generate_summary_report(self, templates: List[GitHubIssueTemplate]) -> str:
        """Generate a summary report of the sync operation."""
        total = len(templates)
        by_priority = {}
        by_milestone = {}
        
        for template in templates:
            # Count by priority
            priority = template.priority
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            # Count by milestone
            milestone = template.milestone or 'No Milestone'
            by_milestone[milestone] = by_milestone.get(milestone, 0) + 1
        
        report = f"""# StratMaster V2 GitHub Issues Sync Report

## Summary
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Issues**: {total}
- **Source Directories**: issues/, github_issues_ready/

## Priority Breakdown
"""
        
        for priority in sorted(by_priority.keys()):
            count = by_priority[priority]
            percentage = (count / total * 100) if total > 0 else 0
            report += f"- **{priority}**: {count} issues ({percentage:.1f}%)\n"
        
        report += "\n## Milestone Breakdown\n"
        for milestone in sorted(by_milestone.keys()):
            count = by_milestone[milestone]
            percentage = (count / total * 100) if total > 0 else 0
            report += f"- **{milestone}**: {count} issues ({percentage:.1f}%)\n"
        
        report += f"""
## Files Generated
- `github_cli_commands.txt` - GitHub CLI commands
- `create_github_issues.sh` - Executable bash script
- `GITHUB_ISSUES_MANUAL.md` - Manual creation instructions
- `github_issues_export.json` - JSON export for automation

## Next Steps
1. **Automated Creation**: Run `./create_github_issues.sh` (requires GitHub CLI)
2. **Manual Creation**: Follow instructions in `GITHUB_ISSUES_MANUAL.md`
3. **Verification**: Check GitHub Issues page for created issues
4. **Project Setup**: Configure GitHub Projects/Milestones as needed

## SM_REFACTOR_STRAT.md Alignment
This sync creates issues for the complete 5-sprint modernization program:
- **Sprint 0** (Weeks 1-3): Mobilize & Baseline
- **Sprint 1** (Weeks 4-6): Modular Architecture Foundations
- **Sprint 2** (Weeks 7-9): Dependency Modernization & Compatibility  
- **Sprint 3** (Weeks 10-12): Testing & Quality Expansion
- **Sprint 4** (Weeks 13-15): CI/CD Evolution & Environment Optimization
"""
        
        return report

def main():
    parser = argparse.ArgumentParser(
        description="StratMaster GitHub Issue Synchronization Tool",
        epilog="""
Examples:
  python scripts/github_issue_sync.py sync        # Generate all sync files
  python scripts/github_issue_sync.py validate    # Validate templates only
  python scripts/github_issue_sync.py report      # Generate summary report
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', 
                       choices=['sync', 'validate', 'report'],
                       help='Action to perform')
    
    args = parser.parse_args()
    
    try:
        syncer = GitHubIssueSyncer()
        
        templates = syncer.discover_issue_templates()
        
        if args.command == 'validate':
            valid, errors = syncer.validate_templates(templates)
            sys.exit(0 if valid else 1)
            
        elif args.command == 'sync':
            # Validate first
            valid, errors = syncer.validate_templates(templates)
            if not valid:
                print("❌ Cannot sync: validation failed")
                sys.exit(1)
            
            # Generate sync files
            output_files = syncer.export_sync_files(templates)
            
            print(f"\n📦 Generated sync files:")
            for file_type, file_path in output_files.items():
                print(f"  - {file_type}: {file_path}")
            
            # Generate and display report
            report = syncer.generate_summary_report(templates)
            report_file = syncer.project_root / 'GITHUB_ISSUES_SYNC_REPORT.md'
            report_file.write_text(report)
            print(f"  - report: {report_file}")
            
            print(f"\n🎉 Sync files generated successfully!")
            print(f"📖 See {report_file} for detailed instructions")
            
        elif args.command == 'report':
            report = syncer.generate_summary_report(templates)
            print(report)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()