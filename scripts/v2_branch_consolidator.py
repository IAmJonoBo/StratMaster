#!/usr/bin/env python3
"""
StratMaster V2 Branch Consolidation Tool

Intelligently discovers, analyzes, and consolidates development branches
into a unified V2 branch following the SM_REFACTOR_STRAT.md modernization program.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

class BranchInfo:
    def __init__(self, name: str, commit_hash: str, commit_date: str, 
                 author: str, commit_message: str):
        self.name = name
        self.commit_hash = commit_hash
        self.commit_date = commit_date
        self.author = author
        self.commit_message = commit_message
        self.feature_category = self._categorize_feature()
        self.merge_priority = self._calculate_priority()

    def _categorize_feature(self) -> str:
        """Categorize branch by feature area based on SM_REFACTOR_STRAT.md."""
        name_lower = self.name.lower()
        message_lower = self.commit_message.lower()
        
        # P0-Critical features (Sprint 0-1)
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'collaboration', 'realtime', 'collab'
        ]):
            return 'P0-collaboration'
        
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'model', 'recommender', 'routing', 'lmsys', 'mteb'
        ]):
            return 'P0-model-recommender'
        
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'retrieval', 'benchmark', 'search', 'vector'
        ]):
            return 'P0-retrieval'
        
        # P1-Important features (Sprint 2-3)
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'cache', 'performance', 'optimization'
        ]):
            return 'P1-performance'
        
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'ux', 'ui', 'accessibility', 'quality'
        ]):
            return 'P1-ux-quality'
        
        # P2-Enhancement features (Sprint 4+)
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'analytics', 'predictive', 'metrics'
        ]):
            return 'P2-analytics'
        
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'event', 'streaming', 'kafka', 'redis'
        ]):
            return 'P2-events'
        
        # Infrastructure and tooling
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'ci', 'cd', 'pipeline', 'deploy', 'ops'
        ]):
            return 'infrastructure'
        
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'test', 'quality', 'lint', 'coverage'
        ]):
            return 'quality'
        
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'docs', 'documentation', 'readme'
        ]):
            return 'documentation'
        
        # Security and compliance
        if any(keyword in name_lower or keyword in message_lower for keyword in [
            'security', 'auth', 'rbac', 'compliance'
        ]):
            return 'security'
        
        # Default category
        return 'feature-general'

    def _calculate_priority(self) -> int:
        """Calculate merge priority based on feature category and recency."""
        category_priorities = {
            'P0-collaboration': 100,
            'P0-model-recommender': 95,
            'P0-retrieval': 90,
            'P1-performance': 80,
            'P1-ux-quality': 75,
            'security': 85,
            'infrastructure': 70,
            'quality': 65,
            'P2-analytics': 60,
            'P2-events': 55,
            'documentation': 50,
            'feature-general': 40
        }
        
        base_priority = category_priorities.get(self.feature_category, 30)
        
        # Boost priority for recent commits (within last 30 days)
        try:
            commit_date = datetime.strptime(self.commit_date, '%Y-%m-%d %H:%M:%S %z')
            days_old = (datetime.now(commit_date.tzinfo) - commit_date).days
            recency_bonus = max(0, 20 - days_old)
        except:
            recency_bonus = 0
        
        return base_priority + recency_bonus

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'commit_hash': self.commit_hash,
            'commit_date': self.commit_date,
            'author': self.author,
            'commit_message': self.commit_message,
            'feature_category': self.feature_category,
            'merge_priority': self.merge_priority
        }

class V2BranchConsolidator:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.git_dir = self.project_root / '.git'
        if not self.git_dir.exists():
            raise ValueError(f"Not a git repository: {self.project_root}")
        
        self.v2_branch_name = 'v2'
        self.analysis_file = self.project_root / 'v2_consolidation_analysis.json'
        
    def run_git_command(self, cmd: List[str]) -> Tuple[str, bool]:
        """Execute git command and return output and success status."""
        try:
            result = subprocess.run(
                ['git'] + cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip(), True
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            print(f"Error output: {e.stderr}")
            return e.stderr.strip(), False

    def discover_branches(self) -> List[BranchInfo]:
        """Discover all remote and local branches with metadata."""
        print("🔍 Discovering branches...")
        
        # Fetch latest from all remotes
        fetch_cmd = ['fetch', '--all', '--prune']
        _, success = self.run_git_command(fetch_cmd)
        if not success:
            print("Warning: Could not fetch from remotes")
        
        # Get all branches (local and remote)
        branch_cmd = ['branch', '-a', '--format=%(refname:short)|%(objectname)|%(committerdate:iso)|%(authorname)|%(subject)']
        output, success = self.run_git_command(branch_cmd)
        
        if not success:
            print("Error: Could not list branches")
            return []
        
        branches = []
        seen_commits = set()
        
        for line in output.split('\n'):
            if not line.strip():
                continue
                
            parts = line.split('|', 4)
            if len(parts) != 5:
                continue
                
            name, commit_hash, commit_date, author, commit_message = parts
            
            # Skip HEAD references and already processed commits
            if 'HEAD' in name or commit_hash in seen_commits:
                continue
            
            # Skip the current V2 branch if it exists
            if name == self.v2_branch_name or name == f'origin/{self.v2_branch_name}':
                continue
            
            seen_commits.add(commit_hash)
            branches.append(BranchInfo(name, commit_hash, commit_date, author, commit_message))
        
        # Sort by priority (highest first)
        branches.sort(key=lambda b: b.merge_priority, reverse=True)
        
        print(f"✅ Discovered {len(branches)} unique branches")
        return branches

    def analyze_branches(self, branches: List[BranchInfo]) -> Dict:
        """Analyze branches and create consolidation plan."""
        print("📊 Analyzing branches for consolidation...")
        
        analysis = {
            'discovery_date': datetime.now().isoformat(),
            'total_branches': len(branches),
            'categories': {},
            'consolidation_plan': [],
            'conflicts_expected': [],
            'merge_order': []
        }
        
        # Categorize branches
        for branch in branches:
            category = branch.feature_category
            if category not in analysis['categories']:
                analysis['categories'][category] = []
            analysis['categories'][category].append(branch.to_dict())
        
        # Create consolidation plan
        high_priority = [b for b in branches if b.merge_priority >= 80]
        medium_priority = [b for b in branches if 60 <= b.merge_priority < 80]
        low_priority = [b for b in branches if b.merge_priority < 60]
        
        analysis['consolidation_plan'] = [
            {
                'phase': 'Phase 1: Critical Features (P0)',
                'branches': [b.to_dict() for b in high_priority],
                'estimated_conflicts': 'Low - these are core features'
            },
            {
                'phase': 'Phase 2: Important Features (P1)',
                'branches': [b.to_dict() for b in medium_priority],
                'estimated_conflicts': 'Medium - may have integration points'
            },
            {
                'phase': 'Phase 3: Enhancement Features (P2+)',
                'branches': [b.to_dict() for b in low_priority],
                'estimated_conflicts': 'High - experimental features'
            }
        ]
        
        # Define merge order
        analysis['merge_order'] = [b.name for b in branches]
        
        return analysis

    def save_analysis(self, analysis: Dict):
        """Save analysis to JSON file."""
        with open(self.analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"📄 Analysis saved to: {self.analysis_file}")

    def create_v2_branch(self, base_branch: str = None) -> bool:
        """Create V2 branch from specified base or current branch."""
        base_branch = base_branch or 'main'
        
        print(f"🏗️  Creating V2 branch from {base_branch}...")
        
        # Ensure we're on the base branch
        checkout_cmd = ['checkout', base_branch]
        _, success = self.run_git_command(checkout_cmd)
        if not success:
            print(f"Error: Could not checkout {base_branch}")
            return False
        
        # Pull latest changes
        pull_cmd = ['pull', 'origin', base_branch]
        _, success = self.run_git_command(pull_cmd)
        if not success:
            print(f"Warning: Could not pull latest {base_branch}")
        
        # Create V2 branch
        create_cmd = ['checkout', '-b', self.v2_branch_name]
        _, success = self.run_git_command(create_cmd)
        if not success:
            print(f"Error: Could not create {self.v2_branch_name} branch")
            return False
        
        print(f"✅ V2 branch created successfully")
        return True

    def consolidate_branches(self, dry_run: bool = True) -> bool:
        """Execute branch consolidation following the analysis."""
        if not self.analysis_file.exists():
            print("Error: No analysis file found. Run 'analyze' command first.")
            return False
        
        with open(self.analysis_file) as f:
            analysis = json.load(f)
        
        if dry_run:
            print("🔍 DRY RUN: Branch consolidation preview")
            self._preview_consolidation(analysis)
            return True
        
        print("🚀 Starting branch consolidation...")
        
        # Ensure we're on V2 branch
        checkout_cmd = ['checkout', self.v2_branch_name]
        _, success = self.run_git_command(checkout_cmd)
        if not success:
            print(f"Error: V2 branch does not exist. Create it first.")
            return False
        
        successful_merges = 0
        failed_merges = []
        
        for phase in analysis['consolidation_plan']:
            print(f"\n📋 {phase['phase']}")
            
            for branch_data in phase['branches']:
                branch_name = branch_data['name']
                print(f"  🔄 Merging {branch_name}...")
                
                success = self._merge_branch(branch_name)
                if success:
                    successful_merges += 1
                    print(f"    ✅ Success")
                else:
                    failed_merges.append(branch_name)
                    print(f"    ❌ Failed")
        
        print(f"\n📊 Consolidation Summary:")
        print(f"  ✅ Successful merges: {successful_merges}")
        print(f"  ❌ Failed merges: {len(failed_merges)}")
        
        if failed_merges:
            print(f"  Failed branches: {', '.join(failed_merges)}")
        
        return len(failed_merges) == 0

    def _preview_consolidation(self, analysis: Dict):
        """Preview what consolidation would do."""
        print(f"\n📈 Consolidation Plan Preview:")
        print(f"Total branches to consolidate: {analysis['total_branches']}")
        
        for phase in analysis['consolidation_plan']:
            print(f"\n{phase['phase']}:")
            print(f"  Branches: {len(phase['branches'])}")
            print(f"  Expected conflicts: {phase['estimated_conflicts']}")
            
            for branch in phase['branches'][:3]:  # Show first 3 branches
                print(f"    - {branch['name']} ({branch['feature_category']})")
            
            if len(phase['branches']) > 3:
                print(f"    ... and {len(phase['branches']) - 3} more")

    def _merge_branch(self, branch_name: str) -> bool:
        """Attempt to merge a single branch."""
        # Try to merge the branch
        merge_cmd = ['merge', '--no-ff', '-m', f'Merge {branch_name} into V2', branch_name]
        _, success = self.run_git_command(merge_cmd)
        
        if success:
            return True
        
        # If merge failed, try to resolve automatically
        print(f"    ⚠️  Merge conflict detected for {branch_name}")
        
        # Abort the merge for now
        abort_cmd = ['merge', '--abort']
        self.run_git_command(abort_cmd)
        
        return False

    def validate_v2_branch(self) -> bool:
        """Validate that V2 branch is in good state."""
        print("🔍 Validating V2 branch...")
        
        # Check if V2 branch exists
        show_cmd = ['show-ref', '--verify', '--quiet', f'refs/heads/{self.v2_branch_name}']
        _, exists = self.run_git_command(show_cmd)
        
        if not exists:
            print(f"❌ V2 branch does not exist")
            return False
        
        # Switch to V2 branch
        checkout_cmd = ['checkout', self.v2_branch_name]
        _, success = self.run_git_command(checkout_cmd)
        if not success:
            print(f"❌ Could not checkout V2 branch")
            return False
        
        # Check for any uncommitted changes
        status_cmd = ['status', '--porcelain']
        output, _ = self.run_git_command(status_cmd)
        if output:
            print(f"⚠️  V2 branch has uncommitted changes:")
            print(output)
            return False
        
        print("✅ V2 branch validation passed")
        return True

    def generate_report(self) -> str:
        """Generate consolidation report."""
        if not self.analysis_file.exists():
            return "No analysis available. Run 'analyze' command first."
        
        with open(self.analysis_file) as f:
            analysis = json.load(f)
        
        report = f"""
# StratMaster V2 Branch Consolidation Report

## Overview
- **Discovery Date**: {analysis['discovery_date']}
- **Total Branches**: {analysis['total_branches']}
- **Categories**: {len(analysis['categories'])}

## Branch Categories
"""
        
        for category, branches in analysis['categories'].items():
            report += f"### {category.replace('-', ' ').title()} ({len(branches)} branches)\n"
            for branch in branches[:3]:
                report += f"- `{branch['name']}` - {branch['commit_message'][:50]}...\n"
            if len(branches) > 3:
                report += f"- ... and {len(branches) - 3} more\n"
            report += "\n"
        
        report += "## Consolidation Plan\n"
        for phase in analysis['consolidation_plan']:
            report += f"### {phase['phase']}\n"
            report += f"- **Branches**: {len(phase['branches'])}\n"
            report += f"- **Expected Conflicts**: {phase['estimated_conflicts']}\n\n"
        
        return report

def main():
    parser = argparse.ArgumentParser(
        description="StratMaster V2 Branch Consolidation Tool",
        epilog="""
Examples:
  python scripts/v2_branch_consolidator.py analyze           # Discover and analyze branches
  python scripts/v2_branch_consolidator.py create           # Create V2 branch
  python scripts/v2_branch_consolidator.py consolidate      # Preview consolidation
  python scripts/v2_branch_consolidator.py consolidate --execute  # Execute consolidation
  python scripts/v2_branch_consolidator.py validate         # Validate V2 branch
  python scripts/v2_branch_consolidator.py report           # Generate report
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', 
                       choices=['analyze', 'create', 'consolidate', 'validate', 'report'],
                       help='Action to perform')
    parser.add_argument('--execute', action='store_true',
                       help='Execute consolidation (default is dry-run)')
    parser.add_argument('--base-branch', default='main',
                       help='Base branch for V2 creation (default: main)')
    
    args = parser.parse_args()
    
    try:
        consolidator = V2BranchConsolidator()
        
        if args.command == 'analyze':
            branches = consolidator.discover_branches()
            analysis = consolidator.analyze_branches(branches)
            consolidator.save_analysis(analysis)
            print("\n📊 Analysis complete! Run 'report' command to view details.")
            
        elif args.command == 'create':
            success = consolidator.create_v2_branch(args.base_branch)
            sys.exit(0 if success else 1)
            
        elif args.command == 'consolidate':
            success = consolidator.consolidate_branches(dry_run=not args.execute)
            sys.exit(0 if success else 1)
            
        elif args.command == 'validate':
            success = consolidator.validate_v2_branch()
            sys.exit(0 if success else 1)
            
        elif args.command == 'report':
            report = consolidator.generate_report()
            print(report)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()