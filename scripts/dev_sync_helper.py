#!/usr/bin/env python3
"""
Developer Code-Documentation Sync Helper
One-stop tool for developers to ensure code-documentation parity and resolve common issues
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import argparse

class DevSyncHelper:
    """Developer helper for maintaining code-documentation synchronization."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.api_package = self.project_root / "packages" / "api" / "src" / "stratmaster_api"
        self.docs_path = self.project_root / "docs"
        self.scripts_path = self.project_root / "scripts"
        
    def run_developer_check(self, mode: str = "comprehensive") -> Dict[str, Any]:
        """Run developer-friendly check with actionable results."""
        print("🛠️ StratMaster Developer Code-Doc Sync Helper")
        print("=" * 50)
        print(f"Project: {self.project_root.name}")
        print(f"Mode: {mode}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "mode": mode,
            "checks": {},
            "issues_found": [],
            "quick_fixes": [],
            "next_steps": []
        }
        
        # 1. Basic parity check
        print("1️⃣ Checking API-Documentation Parity...")
        parity_result = self._check_api_parity()
        results["checks"]["api_parity"] = parity_result
        self._analyze_parity_issues(parity_result, results)
        
        # 2. Phantom route detection
        print("\n2️⃣ Scanning for Phantom Routes...")
        phantom_result = self._check_phantom_routes()
        results["checks"]["phantom_routes"] = phantom_result
        self._analyze_phantom_issues(phantom_result, results)
        
        if mode == "comprehensive":
            # 3. Documentation quality check
            print("\n3️⃣ Assessing Documentation Quality...")
            quality_result = self._check_documentation_quality()
            results["checks"]["documentation_quality"] = quality_result
            self._analyze_quality_issues(quality_result, results)
            
            # 4. CI/CD integration check
            print("\n4️⃣ Validating CI/CD Integration...")
            ci_result = self._check_ci_integration()
            results["checks"]["ci_integration"] = ci_result
            self._analyze_ci_issues(ci_result, results)
        
        # 5. Git status check
        print("\n5️⃣ Checking Git Status...")
        git_result = self._check_git_status()
        results["checks"]["git_status"] = git_result
        self._analyze_git_issues(git_result, results)
        
        # 6. Generate recommendations
        self._generate_developer_recommendations(results)
        
        return results
    
    def _check_api_parity(self) -> Dict[str, Any]:
        """Check API documentation parity."""
        try:
            result = subprocess.run([
                'python3', str(self.scripts_path / 'api_docs_parity_checker.py'),
                '--api-package', str(self.api_package),
                '--docs-path', str(self.docs_path),
                '--output', '/tmp/dev_parity_check.json',
                '--fail-threshold', '80.0'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if Path('/tmp/dev_parity_check.json').exists():
                with open('/tmp/dev_parity_check.json') as f:
                    data = json.load(f)
                
                stats = data.get("stats", {})
                coverage = stats.get("coverage_percentage", 0)
                
                print(f"   📊 Coverage: {coverage:.1f}%")
                print(f"   📋 Routes: {stats.get('documented_routes', 0)}/{stats.get('total_api_routes', 0)} documented")
                
                status = "✅ PASS" if result.returncode == 0 else "❌ FAIL"
                print(f"   {status}")
                
                return {
                    "success": result.returncode == 0,
                    "coverage": coverage,
                    "total_routes": stats.get("total_api_routes", 0),
                    "documented_routes": stats.get("documented_routes", 0),
                    "undocumented_routes": len(data.get("undocumented_routes", [])),
                    "phantom_routes": len(data.get("documented_but_missing", [])),
                    "data": data
                }
            else:
                print("   ❌ Failed to run parity check")
                return {"error": "Failed to run parity check"}
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": str(e)}
    
    def _check_phantom_routes(self) -> Dict[str, Any]:
        """Check for phantom routes specifically."""
        try:
            # Use the previous parity check results if available
            if Path('/tmp/dev_parity_check.json').exists():
                with open('/tmp/dev_parity_check.json') as f:
                    data = json.load(f)
                
                phantom_routes = data.get("documented_but_missing", [])
                phantom_count = len(phantom_routes)
                
                print(f"   👻 Found: {phantom_count} phantom routes")
                
                if phantom_count == 0:
                    print("   ✅ No phantom routes detected")
                    return {"phantom_count": 0, "phantom_routes": []}
                else:
                    print(f"   ⚠️ Phantom routes need cleanup")
                    for i, route in enumerate(phantom_routes[:3], 1):
                        print(f"     {i}. {route}")
                    if len(phantom_routes) > 3:
                        print(f"     ... and {len(phantom_routes) - 3} more")
                
                return {
                    "phantom_count": phantom_count,
                    "phantom_routes": phantom_routes,
                    "needs_cleanup": phantom_count > 0
                }
            else:
                return {"error": "No parity check data available"}
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": str(e)}
    
    def _check_documentation_quality(self) -> Dict[str, Any]:
        """Check documentation quality."""
        try:
            # Count API documentation files and assess quality
            api_docs_path = self.docs_path / "reference" / "api"
            if not api_docs_path.exists():
                print("   ❌ API documentation directory not found")
                return {"error": "API docs directory not found"}
            
            api_files = list(api_docs_path.glob("*-api.md"))
            total_files = len(api_files)
            
            print(f"   📚 API doc files: {total_files}")
            
            # Quick quality assessment
            quality_issues = 0
            for api_file in api_files:
                try:
                    content = api_file.read_text()
                    word_count = len(content.split())
                    
                    # Basic quality checks
                    if word_count < 100:  # Too short
                        quality_issues += 1
                    elif "Endpoint handler:" in content and "Request Example:" not in content:  # Missing examples
                        quality_issues += 1
                        
                except Exception:
                    quality_issues += 1
            
            quality_score = max(0, 100 - (quality_issues * 100 // max(total_files, 1)))
            
            print(f"   📊 Quality score: {quality_score}%")
            
            if quality_score >= 80:
                print("   ✅ Good quality")
            elif quality_score >= 60:
                print("   ⚠️ Needs improvement")
            else:
                print("   ❌ Poor quality")
            
            return {
                "total_files": total_files,
                "quality_issues": quality_issues,
                "quality_score": quality_score,
                "needs_improvement": quality_score < 80
            }
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": str(e)}
    
    def _check_ci_integration(self) -> Dict[str, Any]:
        """Check CI/CD integration for quality gates."""
        try:
            ci_file = self.project_root / ".github" / "workflows" / "ci.yml"
            if not ci_file.exists():
                print("   ❌ CI workflow file not found")
                return {"error": "CI workflow not found"}
            
            ci_content = ci_file.read_text()
            
            # Check for key quality gates
            gates = {
                "api_parity_check": "api_docs_parity_checker.py" in ci_content,
                "fail_threshold": "--fail-threshold" in ci_content,
                "mutation_testing": "mutation_testing.py" in ci_content,
                "dora_metrics": "dora_metrics.py" in ci_content,
                "sbom_generation": "generate_sbom.py" in ci_content,
            }
            
            active_gates = sum(gates.values())
            total_gates = len(gates)
            
            print(f"   🔧 Active gates: {active_gates}/{total_gates}")
            
            missing_gates = [name for name, active in gates.items() if not active]
            if missing_gates:
                print(f"   ⚠️ Missing: {', '.join(missing_gates)}")
                print("   ❌ CI integration incomplete")
            else:
                print("   ✅ CI integration complete")
            
            return {
                "active_gates": active_gates,
                "total_gates": total_gates,
                "gates": gates,
                "missing_gates": missing_gates,
                "integration_complete": len(missing_gates) == 0
            }
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": str(e)}
    
    def _check_git_status(self) -> Dict[str, Any]:
        """Check git status for uncommitted changes."""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                changes = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                
                api_changes = [c for c in changes if 'packages/api/' in c]
                doc_changes = [c for c in changes if 'docs/' in c]
                
                print(f"   📝 Uncommitted changes: {len(changes)}")
                if api_changes:
                    print(f"   🔧 API changes: {len(api_changes)}")
                if doc_changes:
                    print(f"   📚 Doc changes: {len(doc_changes)}")
                
                # Assess sync risk
                sync_risk = "high" if api_changes and not doc_changes else "low" if not changes else "medium"
                
                if sync_risk == "high":
                    print("   ⚠️ High sync risk: API changes without doc updates")
                elif sync_risk == "medium":
                    print("   ℹ️ Medium sync risk: Uncommitted changes present")
                else:
                    print("   ✅ Low sync risk")
                
                return {
                    "total_changes": len(changes),
                    "api_changes": len(api_changes),
                    "doc_changes": len(doc_changes),
                    "sync_risk": sync_risk,
                    "changes": changes[:10]  # First 10 changes
                }
            else:
                return {"error": "Could not check git status"}
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": str(e)}
    
    def _analyze_parity_issues(self, parity_result: Dict[str, Any], results: Dict[str, Any]):
        """Analyze parity issues and add to results."""
        if parity_result.get("error"):
            results["issues_found"].append({
                "type": "critical",
                "category": "parity_check",
                "message": "API parity check failed to run",
                "fix": "Check if scripts/api_docs_parity_checker.py exists and is executable"
            })
            return
        
        coverage = parity_result.get("coverage", 0)
        undocumented = parity_result.get("undocumented_routes", 0)
        
        if coverage < 80:
            results["issues_found"].append({
                "type": "high",
                "category": "coverage",
                "message": f"API documentation coverage is {coverage:.1f}% (below 80% threshold)",
                "fix": f"Document {undocumented} missing API routes",
                "command": "python scripts/api_doc_generator.py /tmp/current_parity_report.json docs/"
            })
            
            results["quick_fixes"].append({
                "title": "Generate missing API documentation",
                "command": "python scripts/api_doc_generator.py /tmp/dev_parity_check.json docs/",
                "description": f"Automatically generate documentation for {undocumented} undocumented routes"
            })
    
    def _analyze_phantom_issues(self, phantom_result: Dict[str, Any], results: Dict[str, Any]):
        """Analyze phantom route issues."""
        if phantom_result.get("error"):
            return
        
        phantom_count = phantom_result.get("phantom_count", 0)
        
        if phantom_count > 0:
            results["issues_found"].append({
                "type": "high",
                "category": "phantom_routes",
                "message": f"Found {phantom_count} phantom routes in documentation",
                "fix": "Clean up phantom routes from documentation",
                "command": "python scripts/cleanup_phantom_routes.py --dry-run"
            })
            
            results["quick_fixes"].append({
                "title": "Clean up phantom routes",
                "command": "python scripts/cleanup_phantom_routes.py --dry-run",
                "description": f"Remove {phantom_count} phantom routes from documentation"
            })
    
    def _analyze_quality_issues(self, quality_result: Dict[str, Any], results: Dict[str, Any]):
        """Analyze documentation quality issues."""
        if quality_result.get("error"):
            return
        
        quality_score = quality_result.get("quality_score", 100)
        
        if quality_score < 80:
            results["issues_found"].append({
                "type": "medium",
                "category": "quality",
                "message": f"Documentation quality score is {quality_score}% (below 80%)",
                "fix": "Enhance documentation quality",
                "command": "python scripts/quality_enhancer.py docs/"
            })
            
            results["quick_fixes"].append({
                "title": "Enhance documentation quality",
                "command": "python scripts/quality_enhancer.py docs/",
                "description": f"Apply quality improvements to {quality_result.get('quality_issues', 0)} files"
            })
    
    def _analyze_ci_issues(self, ci_result: Dict[str, Any], results: Dict[str, Any]):
        """Analyze CI integration issues."""
        if ci_result.get("error"):
            return
        
        missing_gates = ci_result.get("missing_gates", [])
        
        if missing_gates:
            results["issues_found"].append({
                "type": "medium",
                "category": "ci_integration",
                "message": f"Missing {len(missing_gates)} quality gates in CI: {', '.join(missing_gates)}",
                "fix": "Add missing quality gates to CI workflow"
            })
    
    def _analyze_git_issues(self, git_result: Dict[str, Any], results: Dict[str, Any]):
        """Analyze git status issues."""
        if git_result.get("error"):
            return
        
        sync_risk = git_result.get("sync_risk", "low")
        
        if sync_risk == "high":
            results["issues_found"].append({
                "type": "high",
                "category": "sync_risk",
                "message": "High sync risk: API changes without documentation updates",
                "fix": "Update documentation for API changes before committing"
            })
            
            results["next_steps"].append("Update documentation for API changes")
    
    def _generate_developer_recommendations(self, results: Dict[str, Any]):
        """Generate developer-friendly recommendations."""
        issues = results.get("issues_found", [])
        quick_fixes = results.get("quick_fixes", [])
        
        # Prioritize recommendations
        critical_issues = [i for i in issues if i.get("type") == "critical"]
        high_issues = [i for i in issues if i.get("type") == "high"]
        
        if critical_issues:
            results["next_steps"].extend([
                "❗ CRITICAL: Fix critical issues first",
                *[f"   - {issue['message']}" for issue in critical_issues]
            ])
        
        if high_issues:
            results["next_steps"].extend([
                "🔥 HIGH PRIORITY: Address high priority issues",
                *[f"   - {issue['message']}" for issue in high_issues]
            ])
        
        if quick_fixes:
            results["next_steps"].extend([
                "⚡ QUICK FIXES: Run these automated fixes",
                *[f"   - {fix['title']}: {fix['command']}" for fix in quick_fixes]
            ])
        
        # Add workflow recommendations
        results["next_steps"].extend([
            "",
            "📋 WORKFLOW RECOMMENDATIONS:",
            "   - Run this tool before committing changes",
            "   - Update docs in the same commit as API changes", 
            "   - Use comprehensive commit messages mentioning doc updates",
            "   - Run quality enhancer monthly for maintenance"
        ])

    def print_summary(self, results: Dict[str, Any]):
        """Print a developer-friendly summary."""
        print(f"\n📊 DEVELOPER SUMMARY")
        print("=" * 40)
        
        # Overall status
        issues = results.get("issues_found", [])
        critical_count = len([i for i in issues if i.get("type") == "critical"])
        high_count = len([i for i in issues if i.get("type") == "high"])
        
        if critical_count > 0:
            print(f"🚨 Status: CRITICAL - {critical_count} critical issues")
        elif high_count > 0:
            print(f"⚠️ Status: NEEDS ATTENTION - {high_count} high priority issues")
        else:
            print("✅ Status: GOOD - No critical issues found")
        
        # Key metrics
        parity = results.get("checks", {}).get("api_parity", {})
        phantom = results.get("checks", {}).get("phantom_routes", {})
        
        if not parity.get("error"):
            print(f"📊 API Coverage: {parity.get('coverage', 0):.1f}%")
            print(f"📋 Documented Routes: {parity.get('documented_routes', 0)}/{parity.get('total_routes', 0)}")
        
        if not phantom.get("error"):
            print(f"👻 Phantom Routes: {phantom.get('phantom_count', 0)}")
        
        # Quick actions
        quick_fixes = results.get("quick_fixes", [])
        if quick_fixes:
            print(f"\n⚡ QUICK ACTIONS ({len(quick_fixes)} available):")
            for fix in quick_fixes[:3]:
                print(f"   {fix['title']}")
                print(f"   → {fix['command']}")
                print()
        
        # Next steps
        next_steps = results.get("next_steps", [])
        if next_steps:
            print("🚀 NEXT STEPS:")
            for step in next_steps[:8]:  # Show first 8 steps
                print(f"   {step}")
            
            if len(next_steps) > 8:
                print(f"   ... and {len(next_steps) - 8} more recommendations")

def main():
    parser = argparse.ArgumentParser(description='Developer Code-Documentation Sync Helper')
    parser.add_argument('--mode', choices=['quick', 'comprehensive'], default='comprehensive',
                       help='Check mode: quick (basic checks) or comprehensive (full analysis)')
    parser.add_argument('--project-root', help='Project root directory (default: current directory)')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    helper = DevSyncHelper(args.project_root)
    
    # Run the check
    results = helper.run_developer_check(args.mode)
    
    # Print summary (unless quiet mode)
    if not args.quiet:
        helper.print_summary(results)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Full results saved to: {args.output}")
    
    # Exit with appropriate code
    issues = results.get("issues_found", [])
    critical_issues = [i for i in issues if i.get("type") == "critical"]
    
    if critical_issues:
        sys.exit(2)  # Critical issues
    elif issues:
        sys.exit(1)  # Non-critical issues
    else:
        sys.exit(0)  # No issues

if __name__ == "__main__":
    main()