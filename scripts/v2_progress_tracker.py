#!/usr/bin/env python3
"""
StratMaster V2 Progress Tracking Tool

Tracks progress on the V2 development roadmap, sprint milestones,
and implementation issues following SM_REFACTOR_STRAT.md.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ProgressTracker:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.progress_file = self.project_root / 'v2_progress_tracking.json'
        self.config_file = self.project_root / 'v2_tracking_config.json'
        
        # Load configuration and progress
        self.config = self._load_config()
        self.progress = self._load_progress()
    
    def _load_config(self) -> Dict:
        """Load tracking configuration or create default."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        
        # Default configuration based on SM_REFACTOR_STRAT.md
        config = {
            'sprints': {
                'sprint_0': {
                    'name': 'Sprint 0: Mobilize & Baseline',
                    'start_week': 1,
                    'duration_weeks': 3,
                    'objectives': [
                        'Architecture Assessment & Domain Mapping',
                        'Dependency Inventory & Risk Classification',
                        'Test Coverage Benchmarking & Test Data Audit',
                        'CI/CD & Virtual Environment Baseline Analysis'
                    ]
                },
                'sprint_1': {
                    'name': 'Sprint 1: Modular Architecture Foundations',
                    'start_week': 4,
                    'duration_weeks': 3,
                    'objectives': [
                        'Module Boundary Implementation & Code Move Strategy',
                        'Shared Infrastructure Layer',
                        'Developer Tooling Update & Lint Baseline Alignment',
                        'Developer Guide Refresh & Migration Playbook'
                    ]
                },
                'sprint_2': {
                    'name': 'Sprint 2: Dependency Modernization & Compatibility',
                    'start_week': 7,
                    'duration_weeks': 3,
                    'objectives': [
                        'Tier-1 Dependency Upgrades',
                        'Security & Compliance Tooling',
                        'Compatibility Testing Matrix & Rollback Automation',
                        'Container Base Image Refresh & Slimming'
                    ]
                },
                'sprint_3': {
                    'name': 'Sprint 3: Testing & Quality Expansion',
                    'start_week': 10,
                    'duration_weeks': 3,
                    'objectives': [
                        'Core Domain Unit & Integration Test Expansion',
                        'Contract & Consumer-Driven Tests for Services/APIs',
                        'Performance & Load Testing Harness',
                        'Quality Gate Automation'
                    ]
                },
                'sprint_4': {
                    'name': 'Sprint 4: CI/CD Evolution & Environment Optimization',
                    'start_week': 13,
                    'duration_weeks': 3,
                    'objectives': [
                        'Pipeline Re-architecture',
                        'Secrets, Compliance, and Supply Chain Hardening',
                        'Virtual Environment Optimization & Developer Onboarding Scripts',
                        'Operational Runbooks, Playbooks, and Knowledge Transfer'
                    ]
                }
            },
            'milestones': {
                'M1': {
                    'name': 'M1: Real-Time Foundation',
                    'target_week': 2,
                    'success_criteria': [
                        'Real-time collaboration engine operational',
                        'Evidence-guided model recommender V2 implemented',
                        'V2 branch established and validated'
                    ]
                },
                'M2': {
                    'name': 'M2: Performance & Validation',
                    'target_week': 4,
                    'success_criteria': [
                        'Retrieval benchmarking automated',
                        'Advanced caching implemented',
                        'Phase 3 UX quality gates established'
                    ]
                },
                'M3': {
                    'name': 'M3: Advanced Analytics',
                    'target_week': 8,
                    'success_criteria': [
                        'Predictive analytics operational',
                        'Event-driven architecture implemented',
                        '90% test coverage achieved'
                    ]
                },
                'M4': {
                    'name': 'M4: Enterprise Features',
                    'target_week': 12,
                    'success_criteria': [
                        'Industry templates available',
                        'Custom model fine-tuning platform',
                        'Knowledge graph reasoning enhanced'
                    ]
                }
            },
            'success_metrics': {
                'build_performance_improvement': {
                    'target': 30,
                    'unit': 'percent_reduction',
                    'baseline': 0
                },
                'test_coverage': {
                    'target': 90,
                    'unit': 'percent',
                    'baseline': 0
                },
                'security_vulnerabilities': {
                    'target': 0,
                    'unit': 'critical_count',
                    'baseline': 0
                },
                'onboarding_time_reduction': {
                    'target': 40,
                    'unit': 'percent_reduction',
                    'baseline': 0
                }
            }
        }
        
        # Save default config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def _load_progress(self) -> Dict:
        """Load progress data or create new tracking."""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return json.load(f)
        
        # Initialize progress tracking
        progress = {
            'project_start_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'current_sprint': 'sprint_0',
            'completed_sprints': [],
            'sprint_progress': {},
            'milestone_progress': {},
            'issue_tracking': {},
            'metrics': {
                'build_performance_improvement': 0,
                'test_coverage': 0,
                'security_vulnerabilities': 0,
                'onboarding_time_reduction': 0
            },
            'blockers': [],
            'achievements': []
        }
        
        # Initialize sprint progress
        for sprint_id in self.config['sprints'].keys():
            progress['sprint_progress'][sprint_id] = {
                'status': 'not_started',
                'start_date': None,
                'completion_date': None,
                'objectives_completed': [],
                'completion_percentage': 0
            }
        
        # Initialize milestone progress
        for milestone_id in self.config['milestones'].keys():
            progress['milestone_progress'][milestone_id] = {
                'status': 'not_started',
                'completion_date': None,
                'criteria_met': [],
                'completion_percentage': 0
            }
        
        return progress
    
    def _save_progress(self):
        """Save progress data."""
        self.progress['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def update_sprint_progress(self, sprint_id: str, objectives_completed: List[str] = None,
                             status: str = None) -> bool:
        """Update sprint progress."""
        if sprint_id not in self.config['sprints']:
            print(f"Error: Unknown sprint ID '{sprint_id}'")
            return False
        
        sprint_progress = self.progress['sprint_progress'][sprint_id]
        
        if status:
            sprint_progress['status'] = status
            if status == 'in_progress' and not sprint_progress['start_date']:
                sprint_progress['start_date'] = datetime.now().isoformat()
            elif status == 'completed' and not sprint_progress['completion_date']:
                sprint_progress['completion_date'] = datetime.now().isoformat()
                if sprint_id not in self.progress['completed_sprints']:
                    self.progress['completed_sprints'].append(sprint_id)
        
        if objectives_completed:
            sprint_progress['objectives_completed'] = objectives_completed
        
        # Calculate completion percentage
        total_objectives = len(self.config['sprints'][sprint_id]['objectives'])
        completed_objectives = len(sprint_progress['objectives_completed'])
        sprint_progress['completion_percentage'] = (completed_objectives / total_objectives) * 100 if total_objectives > 0 else 0
        
        self._save_progress()
        print(f"✅ Updated {sprint_id} progress: {sprint_progress['completion_percentage']:.1f}% complete")
        return True
    
    def update_milestone_progress(self, milestone_id: str, criteria_met: List[str] = None,
                                status: str = None) -> bool:
        """Update milestone progress."""
        if milestone_id not in self.config['milestones']:
            print(f"Error: Unknown milestone ID '{milestone_id}'")
            return False
        
        milestone_progress = self.progress['milestone_progress'][milestone_id]
        
        if status:
            milestone_progress['status'] = status
            if status == 'completed' and not milestone_progress['completion_date']:
                milestone_progress['completion_date'] = datetime.now().isoformat()
        
        if criteria_met:
            milestone_progress['criteria_met'] = criteria_met
        
        # Calculate completion percentage
        total_criteria = len(self.config['milestones'][milestone_id]['success_criteria'])
        met_criteria = len(milestone_progress['criteria_met'])
        milestone_progress['completion_percentage'] = (met_criteria / total_criteria) * 100 if total_criteria > 0 else 0
        
        self._save_progress()
        print(f"✅ Updated {milestone_id} progress: {milestone_progress['completion_percentage']:.1f}% complete")
        return True
    
    def update_metrics(self, **metrics) -> bool:
        """Update success metrics."""
        for metric_name, value in metrics.items():
            if metric_name in self.config['success_metrics']:
                self.progress['metrics'][metric_name] = value
                print(f"✅ Updated {metric_name}: {value}")
            else:
                print(f"Warning: Unknown metric '{metric_name}'")
        
        self._save_progress()
        return True
    
    def add_blocker(self, description: str, severity: str = 'medium', 
                   affected_sprint: str = None) -> bool:
        """Add a blocker."""
        blocker = {
            'id': len(self.progress['blockers']) + 1,
            'description': description,
            'severity': severity,
            'affected_sprint': affected_sprint,
            'created_date': datetime.now().isoformat(),
            'resolved_date': None,
            'status': 'open'
        }
        
        self.progress['blockers'].append(blocker)
        self._save_progress()
        print(f"🚨 Added blocker #{blocker['id']}: {description}")
        return True
    
    def resolve_blocker(self, blocker_id: int) -> bool:
        """Resolve a blocker."""
        for blocker in self.progress['blockers']:
            if blocker['id'] == blocker_id:
                blocker['status'] = 'resolved'
                blocker['resolved_date'] = datetime.now().isoformat()
                self._save_progress()
                print(f"✅ Resolved blocker #{blocker_id}")
                return True
        
        print(f"Error: Blocker #{blocker_id} not found")
        return False
    
    def add_achievement(self, description: str, sprint: str = None) -> bool:
        """Add an achievement."""
        achievement = {
            'id': len(self.progress['achievements']) + 1,
            'description': description,
            'sprint': sprint,
            'date': datetime.now().isoformat()
        }
        
        self.progress['achievements'].append(achievement)
        self._save_progress()
        print(f"🎉 Added achievement: {description}")
        return True
    
    def generate_dashboard(self) -> str:
        """Generate a progress dashboard."""
        current_date = datetime.now()
        project_start = datetime.fromisoformat(self.progress['project_start_date'])
        weeks_elapsed = (current_date - project_start).days / 7
        
        dashboard = f"""# StratMaster V2 Progress Dashboard

## Project Overview
- **Start Date**: {project_start.strftime('%Y-%m-%d')}
- **Weeks Elapsed**: {weeks_elapsed:.1f}
- **Current Sprint**: {self.config['sprints'][self.progress['current_sprint']]['name']}
- **Last Updated**: {current_date.strftime('%Y-%m-%d %H:%M')}

## Success Metrics Progress
"""
        
        for metric_name, config in self.config['success_metrics'].items():
            current_value = self.progress['metrics'][metric_name]
            target = config['target']
            unit = config['unit']
            
            if unit == 'percent_reduction':
                status = "✅" if current_value >= target else "🔄"
                dashboard += f"- **{metric_name.replace('_', ' ').title()}**: {current_value}% / {target}% {status}\n"
            elif unit == 'percent':
                status = "✅" if current_value >= target else "🔄"
                dashboard += f"- **{metric_name.replace('_', ' ').title()}**: {current_value}% / {target}% {status}\n"
            elif unit == 'critical_count':
                status = "✅" if current_value <= target else "🚨"
                dashboard += f"- **{metric_name.replace('_', ' ').title()}**: {current_value} / {target} {status}\n"
        
        dashboard += "\n## Sprint Progress\n"
        
        for sprint_id, sprint_config in self.config['sprints'].items():
            sprint_progress = self.progress['sprint_progress'][sprint_id]
            status_icon = {
                'not_started': '⏸️',
                'in_progress': '🔄',
                'completed': '✅',
                'blocked': '🚨'
            }.get(sprint_progress['status'], '❓')
            
            dashboard += f"### {sprint_config['name']} {status_icon}\n"
            dashboard += f"- **Status**: {sprint_progress['status']}\n"
            dashboard += f"- **Progress**: {sprint_progress['completion_percentage']:.1f}%\n"
            dashboard += f"- **Objectives**: {len(sprint_progress['objectives_completed'])}/{len(sprint_config['objectives'])}\n"
            
            if sprint_progress['start_date']:
                start_date = datetime.fromisoformat(sprint_progress['start_date'])
                dashboard += f"- **Started**: {start_date.strftime('%Y-%m-%d')}\n"
            
            if sprint_progress['completion_date']:
                end_date = datetime.fromisoformat(sprint_progress['completion_date'])
                dashboard += f"- **Completed**: {end_date.strftime('%Y-%m-%d')}\n"
            
            dashboard += "\n"
        
        dashboard += "## Milestone Progress\n"
        
        for milestone_id, milestone_config in self.config['milestones'].items():
            milestone_progress = self.progress['milestone_progress'][milestone_id]
            status_icon = "✅" if milestone_progress['completion_percentage'] >= 100 else "🔄"
            
            dashboard += f"### {milestone_config['name']} {status_icon}\n"
            dashboard += f"- **Progress**: {milestone_progress['completion_percentage']:.1f}%\n"
            dashboard += f"- **Criteria Met**: {len(milestone_progress['criteria_met'])}/{len(milestone_config['success_criteria'])}\n"
            
            if milestone_progress['completion_date']:
                end_date = datetime.fromisoformat(milestone_progress['completion_date'])
                dashboard += f"- **Completed**: {end_date.strftime('%Y-%m-%d')}\n"
            
            dashboard += "\n"
        
        # Show active blockers
        active_blockers = [b for b in self.progress['blockers'] if b['status'] == 'open']
        if active_blockers:
            dashboard += f"## Active Blockers ({len(active_blockers)})\n"
            for blocker in active_blockers:
                severity_icon = {'high': '🚨', 'medium': '⚠️', 'low': '📝'}.get(blocker['severity'], '❓')
                dashboard += f"- **#{blocker['id']}** {severity_icon} {blocker['description']}\n"
                if blocker['affected_sprint']:
                    dashboard += f"  - *Affects*: {blocker['affected_sprint']}\n"
            dashboard += "\n"
        
        # Show recent achievements
        recent_achievements = sorted(self.progress['achievements'], 
                                   key=lambda x: x['date'], reverse=True)[:5]
        if recent_achievements:
            dashboard += f"## Recent Achievements ({len(recent_achievements)})\n"
            for achievement in recent_achievements:
                date = datetime.fromisoformat(achievement['date'])
                dashboard += f"- 🎉 {achievement['description']} ({date.strftime('%Y-%m-%d')})\n"
            dashboard += "\n"
        
        dashboard += """## Next Steps
1. Review current sprint objectives and update completion status
2. Address any active blockers
3. Update metrics based on latest measurements
4. Plan upcoming milestone deliverables

*Dashboard auto-generated by v2_progress_tracker.py*
"""
        
        return dashboard
    
    def generate_weekly_report(self) -> str:
        """Generate weekly progress report."""
        current_sprint = self.progress['current_sprint']
        sprint_config = self.config['sprints'][current_sprint]
        sprint_progress = self.progress['sprint_progress'][current_sprint]
        
        report = f"""# Weekly Progress Report - Week {datetime.now().strftime('%Y-W%U')}

## Current Sprint: {sprint_config['name']}
- **Progress**: {sprint_progress['completion_percentage']:.1f}%
- **Status**: {sprint_progress['status']}
- **Objectives Completed**: {len(sprint_progress['objectives_completed'])}/{len(sprint_config['objectives'])}

### Sprint Objectives
"""
        
        for i, objective in enumerate(sprint_config['objectives'], 1):
            status = "✅" if objective in sprint_progress['objectives_completed'] else "⏸️"
            report += f"{i}. {objective} {status}\n"
        
        # Show metrics progress
        report += "\n### Success Metrics\n"
        for metric_name, value in self.progress['metrics'].items():
            target = self.config['success_metrics'][metric_name]['target']
            progress_pct = (value / target) * 100 if target > 0 else 0
            report += f"- {metric_name.replace('_', ' ').title()}: {value} ({progress_pct:.1f}% of target)\n"
        
        # Show blockers and achievements
        active_blockers = len([b for b in self.progress['blockers'] if b['status'] == 'open'])
        recent_achievements = len([a for a in self.progress['achievements'] 
                                 if datetime.fromisoformat(a['date']) > datetime.now() - timedelta(days=7)])
        
        report += f"\n### This Week\n"
        report += f"- **New Blockers**: {active_blockers}\n"
        report += f"- **Achievements**: {recent_achievements}\n"
        
        return report

def main():
    parser = argparse.ArgumentParser(
        description="StratMaster V2 Progress Tracking Tool",
        epilog="""
Examples:
  python scripts/v2_progress_tracker.py dashboard       # Show progress dashboard
  python scripts/v2_progress_tracker.py sprint --update sprint_1 --status in_progress
  python scripts/v2_progress_tracker.py milestone --update M1 --status completed
  python scripts/v2_progress_tracker.py metrics --test_coverage 85 --build_performance_improvement 25
  python scripts/v2_progress_tracker.py blocker --add "CI pipeline failing" --severity high
  python scripts/v2_progress_tracker.py achievement --add "V2 branch created successfully"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Show progress dashboard')
    dashboard_parser.add_argument('--export', help='Export dashboard to file')
    
    # Sprint command
    sprint_parser = subparsers.add_parser('sprint', help='Update sprint progress')
    sprint_parser.add_argument('--update', required=True, help='Sprint ID to update')
    sprint_parser.add_argument('--status', help='Sprint status')
    sprint_parser.add_argument('--objectives', nargs='*', help='Completed objectives')
    
    # Milestone command
    milestone_parser = subparsers.add_parser('milestone', help='Update milestone progress')
    milestone_parser.add_argument('--update', required=True, help='Milestone ID to update')
    milestone_parser.add_argument('--status', help='Milestone status')
    milestone_parser.add_argument('--criteria', nargs='*', help='Met criteria')
    
    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Update success metrics')
    metrics_parser.add_argument('--build_performance_improvement', type=int)
    metrics_parser.add_argument('--test_coverage', type=int)
    metrics_parser.add_argument('--security_vulnerabilities', type=int)
    metrics_parser.add_argument('--onboarding_time_reduction', type=int)
    
    # Blocker command
    blocker_parser = subparsers.add_parser('blocker', help='Manage blockers')
    blocker_parser.add_argument('--add', help='Add blocker description')
    blocker_parser.add_argument('--resolve', type=int, help='Resolve blocker by ID')
    blocker_parser.add_argument('--severity', choices=['low', 'medium', 'high'], default='medium')
    blocker_parser.add_argument('--sprint', help='Affected sprint')
    
    # Achievement command
    achievement_parser = subparsers.add_parser('achievement', help='Add achievement')
    achievement_parser.add_argument('--add', required=True, help='Achievement description')
    achievement_parser.add_argument('--sprint', help='Related sprint')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate weekly report')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        tracker = ProgressTracker()
        
        if args.command == 'dashboard':
            dashboard = tracker.generate_dashboard()
            if args.export:
                Path(args.export).write_text(dashboard)
                print(f"Dashboard exported to {args.export}")
            else:
                print(dashboard)
        
        elif args.command == 'sprint':
            objectives = args.objectives if args.objectives else None
            tracker.update_sprint_progress(args.update, objectives, args.status)
        
        elif args.command == 'milestone':
            criteria = args.criteria if args.criteria else None
            tracker.update_milestone_progress(args.update, criteria, args.status)
        
        elif args.command == 'metrics':
            metrics = {}
            for metric in ['build_performance_improvement', 'test_coverage', 
                          'security_vulnerabilities', 'onboarding_time_reduction']:
                value = getattr(args, metric)
                if value is not None:
                    metrics[metric] = value
            
            if metrics:
                tracker.update_metrics(**metrics)
            else:
                print("No metrics specified")
        
        elif args.command == 'blocker':
            if args.add:
                tracker.add_blocker(args.add, args.severity, args.sprint)
            elif args.resolve:
                tracker.resolve_blocker(args.resolve)
            else:
                print("Specify --add or --resolve")
        
        elif args.command == 'achievement':
            tracker.add_achievement(args.add, args.sprint)
        
        elif args.command == 'report':
            report = tracker.generate_weekly_report()
            print(report)
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()