#!/usr/bin/env python3
"""
Advanced Code-Documentation Parity Validator
Enhanced tooling to ensure code-documentation synchronization and help developers resolve common issues
"""

import ast
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Optional, Tuple, Union
import argparse
import difflib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeDocParityValidator:
    """Advanced validation of code-documentation parity with developer assistance tools."""
    
    def __init__(self, api_package_path: str, docs_path: str):
        self.api_package_path = Path(api_package_path)
        self.docs_path = Path(docs_path)
        self.api_docs_path = self.docs_path / "reference" / "api"
        
        # Initialize tracking
        self.discovered_routes = []
        self.documented_routes = []
        self.phantom_routes = []
        self.quality_issues = []
        self.sync_issues = []
        
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run comprehensive parity validation with developer assistance."""
        print("🔍 Running Comprehensive Code-Documentation Parity Check")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "basic_parity": {},
            "phantom_route_analysis": {},
            "quality_assessment": {},
            "sync_validation": {},
            "developer_assistance": {},
            "recommendations": []
        }
        
        # 1. Basic parity check (using existing logic)
        print("\n1️⃣ Basic API-Documentation Parity Check")
        results["basic_parity"] = self._run_basic_parity_check()
        
        # 2. Deep phantom route analysis
        print("\n2️⃣ Deep Phantom Route Analysis")  
        results["phantom_route_analysis"] = self._analyze_phantom_routes()
        
        # 3. Documentation quality assessment
        print("\n3️⃣ Documentation Quality Assessment")
        results["quality_assessment"] = self._assess_documentation_quality()
        
        # 4. Code-doc synchronization validation
        print("\n4️⃣ Code-Documentation Synchronization Validation")
        results["sync_validation"] = self._validate_code_doc_sync()
        
        # 5. Developer assistance tools
        print("\n5️⃣ Developer Assistance & Issue Resolution")
        results["developer_assistance"] = self._provide_developer_assistance()
        
        # 6. Generate actionable recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        return results
    
    def _run_basic_parity_check(self) -> Dict[str, Any]:
        """Run the basic API parity check."""
        try:
            # Run the existing parity checker
            result = subprocess.run([
                'python3', 'scripts/api_docs_parity_checker.py',
                '--api-package', str(self.api_package_path),
                '--docs-path', str(self.docs_path),
                '--output', '/tmp/basic_parity.json',
                '--fail-threshold', '80.0'
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            if Path('/tmp/basic_parity.json').exists():
                with open('/tmp/basic_parity.json') as f:
                    data = json.load(f)
                return {
                    "success": result.returncode == 0,
                    "coverage_percentage": data.get("stats", {}).get("coverage_percentage", 0),
                    "total_routes": data.get("stats", {}).get("total_api_routes", 0),
                    "documented_routes": data.get("stats", {}).get("documented_routes", 0),
                    "phantom_routes": len(data.get("documented_but_missing", [])),
                    "quality_issues": len(data.get("routes_needing_better_documentation", []))
                }
            else:
                return {"error": "Failed to run basic parity check"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_phantom_routes(self) -> Dict[str, Any]:
        """Deep analysis of phantom routes with location tracking and fix suggestions."""
        phantom_analysis = {
            "total_phantom_routes": 0,
            "phantom_routes_by_file": {},
            "likely_causes": {},
            "fix_suggestions": []
        }
        
        # Load basic parity results
        try:
            with open('/tmp/basic_parity.json') as f:
                data = json.load(f)
            phantom_routes = data.get("documented_but_missing", [])
        except:
            phantom_routes = []
        
        phantom_analysis["total_phantom_routes"] = len(phantom_routes)
        
        if not phantom_routes:
            print("   ✅ No phantom routes found")
            return phantom_analysis
        
        print(f"   🔍 Analyzing {len(phantom_routes)} phantom routes...")
        
        # Analyze each phantom route
        for route in phantom_routes:
            file_locations = self._find_phantom_route_locations(route)
            phantom_analysis["phantom_routes_by_file"][route] = file_locations
            
            # Determine likely cause
            cause = self._determine_phantom_cause(route, file_locations)
            phantom_analysis["likely_causes"][route] = cause
        
        # Generate fix suggestions
        phantom_analysis["fix_suggestions"] = self._generate_phantom_fix_suggestions(phantom_analysis)
        
        return phantom_analysis
    
    def _find_phantom_route_locations(self, route: str) -> List[Dict[str, Any]]:
        """Find where a phantom route is documented."""
        locations = []
        
        # Search in all markdown files
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if route in line and any(method in line for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
                        locations.append({
                            "file": str(md_file.relative_to(self.docs_path)),
                            "line": line_num,
                            "content": line.strip(),
                            "context": self._get_line_context(lines, line_num - 1)
                        })
            except Exception as e:
                logger.debug(f"Could not analyze {md_file}: {e}")
        
        return locations
    
    def _get_line_context(self, lines: List[str], line_index: int, context_size: int = 2) -> List[str]:
        """Get context lines around a specific line."""
        start = max(0, line_index - context_size)
        end = min(len(lines), line_index + context_size + 1)
        return lines[start:end]
    
    def _determine_phantom_cause(self, route: str, locations: List[Dict[str, Any]]) -> str:
        """Determine the likely cause of a phantom route."""
        if not locations:
            return "undocumented_removal"
        
        # Analyze the locations to determine cause
        for loc in locations:
            content = loc["content"].lower()
            
            if "todo" in content or "placeholder" in content:
                return "placeholder_documentation"
            elif "deprecated" in content or "removed" in content:
                return "deprecated_endpoint"
            elif any(pattern in route for pattern in ['/v1/', '/v2/', '/beta/']):
                return "version_mismatch"
            elif route.startswith('/') and '/' in route[1:]:
                return "routing_path_mismatch"
        
        return "implementation_gap"
    
    def _generate_phantom_fix_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate specific fix suggestions for phantom routes."""
        suggestions = []
        
        cause_solutions = {
            "placeholder_documentation": "Remove placeholder documentation or implement the endpoint",
            "deprecated_endpoint": "Remove deprecated endpoint documentation",
            "version_mismatch": "Update documentation to match current API version",
            "routing_path_mismatch": "Verify router prefix and path configuration",
            "implementation_gap": "Implement the endpoint or remove from documentation",
            "undocumented_removal": "Endpoint was removed from code but documentation not updated"
        }
        
        for route, cause in analysis.get("likely_causes", {}).items():
            locations = analysis.get("phantom_routes_by_file", {}).get(route, [])
            
            suggestion = {
                "route": route,
                "cause": cause,
                "solution": cause_solutions.get(cause, "Investigate and resolve manually"),
                "files_to_update": [loc["file"] for loc in locations],
                "priority": "high" if cause in ["implementation_gap", "routing_path_mismatch"] else "medium"
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def _assess_documentation_quality(self) -> Dict[str, Any]:
        """Assess the quality of existing documentation."""
        quality_assessment = {
            "total_files_assessed": 0,
            "quality_scores": {},
            "common_issues": {},
            "improvement_opportunities": []
        }
        
        # Assess each API documentation file
        for api_file in self.api_docs_path.glob("*.md"):
            if api_file.name == "index.md":
                continue
                
            quality_assessment["total_files_assessed"] += 1
            score = self._assess_file_quality(api_file)
            quality_assessment["quality_scores"][api_file.name] = score
        
        # Identify common issues
        quality_assessment["common_issues"] = self._identify_common_quality_issues(quality_assessment["quality_scores"])
        
        # Generate improvement opportunities
        quality_assessment["improvement_opportunities"] = self._generate_quality_improvements(quality_assessment)
        
        return quality_assessment
    
    def _assess_file_quality(self, file_path: Path) -> Dict[str, Any]:
        """Assess the quality of a documentation file."""
        try:
            content = file_path.read_text()
        except Exception:
            return {"error": "Could not read file"}
        
        score = {
            "filename": file_path.name,
            "total_score": 0,
            "max_score": 100,
            "components": {}
        }
        
        # 1. Structure score (25 points)
        structure_score = self._score_structure(content)
        score["components"]["structure"] = structure_score
        
        # 2. Content completeness (25 points)  
        completeness_score = self._score_completeness(content)
        score["components"]["completeness"] = completeness_score
        
        # 3. Examples and clarity (25 points)
        examples_score = self._score_examples(content)
        score["components"]["examples"] = examples_score
        
        # 4. Consistency and style (25 points)
        style_score = self._score_style(content)
        score["components"]["style"] = style_score
        
        # Calculate total score
        score["total_score"] = sum(score["components"].values())
        
        return score
    
    def _score_structure(self, content: str) -> int:
        """Score documentation structure (max 25 points)."""
        score = 0
        
        # Check for essential sections
        required_sections = ["# ", "## Authentication", "## Endpoints", "## Error Handling"]
        for section in required_sections:
            if section in content:
                score += 5
        
        # Check for proper heading hierarchy
        headings = re.findall(r'^(#{1,6})\s+', content, re.MULTILINE)
        if headings and len(set(len(h) for h in headings)) > 1:
            score += 5
        
        return min(score, 25)
    
    def _score_completeness(self, content: str) -> int:
        """Score content completeness (max 25 points)."""
        score = 0
        
        # Check for request/response examples
        if "```json" in content:
            score += 8
        if "Request Example" in content or "Response Example" in content:
            score += 7
        
        # Check for parameter documentation
        if "Parameters:" in content or "**Parameters:**" in content:
            score += 5
        
        # Check for status codes
        if any(code in content for code in ["200", "400", "404", "500"]):
            score += 5
        
        return min(score, 25)
    
    def _score_examples(self, content: str) -> int:
        """Score examples and clarity (max 25 points)."""
        score = 0
        
        # Count code examples
        code_blocks = content.count("```")
        if code_blocks >= 2:
            score += 10
        elif code_blocks == 1:
            score += 5
        
        # Check for curl examples
        if "curl" in content.lower():
            score += 8
        
        # Check for use cases
        if "Use Case" in content or "use case" in content:
            score += 7
        
        return min(score, 25)
    
    def _score_style(self, content: str) -> int:
        """Score consistency and style (max 25 points)."""
        score = 0
        
        # Check consistent formatting
        if re.search(r'\*\*[^*]+\*\*:', content):  # Bold labels
            score += 5
        
        # Check for consistent endpoint formatting
        if re.search(r'`[A-Z]+ /', content):  # HTTP methods
            score += 10
        
        # Check for implementation references
        if "Implementation:" in content or "handler:" in content.lower():
            score += 5
        
        # Check length appropriateness (not too short, not too long)
        word_count = len(content.split())
        if 200 <= word_count <= 2000:  # Reasonable length
            score += 5
        
        return min(score, 25)
    
    def _identify_common_quality_issues(self, quality_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Identify common quality issues across documentation files."""
        issues = {
            "low_structure_scores": [],
            "missing_examples": [],
            "incomplete_content": [],
            "style_inconsistencies": []
        }
        
        for filename, score in quality_scores.items():
            if isinstance(score, dict) and "components" in score:
                components = score["components"]
                
                if components.get("structure", 0) < 15:
                    issues["low_structure_scores"].append(filename)
                if components.get("examples", 0) < 10:
                    issues["missing_examples"].append(filename)
                if components.get("completeness", 0) < 15:
                    issues["incomplete_content"].append(filename)
                if components.get("style", 0) < 15:
                    issues["style_inconsistencies"].append(filename)
        
        return issues
    
    def _generate_quality_improvements(self, quality_assessment: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate specific quality improvement recommendations."""
        improvements = []
        
        common_issues = quality_assessment.get("common_issues", {})
        
        for issue_type, files in common_issues.items():
            if not files:
                continue
                
            improvement = {
                "issue_type": issue_type.replace("_", " ").title(),
                "affected_files": len(files),
                "files": files[:5],  # Show first 5
                "recommendation": self._get_improvement_recommendation(issue_type),
                "priority": "high" if len(files) > 5 else "medium"
            }
            improvements.append(improvement)
        
        return improvements
    
    def _get_improvement_recommendation(self, issue_type: str) -> str:
        """Get specific recommendation for an issue type."""
        recommendations = {
            "low_structure_scores": "Add proper heading hierarchy and essential sections (Authentication, Endpoints, Error Handling)",
            "missing_examples": "Add comprehensive request/response examples and curl command examples",
            "incomplete_content": "Add parameter documentation, status codes, and detailed descriptions",
            "style_inconsistencies": "Ensure consistent formatting, HTTP method formatting, and implementation references"
        }
        return recommendations.get(issue_type, "Review and improve documentation quality")
    
    def _validate_code_doc_sync(self) -> Dict[str, Any]:
        """Validate synchronization between code and documentation."""
        sync_validation = {
            "route_signature_matches": [],
            "parameter_mismatches": [],
            "response_model_sync": [],
            "deprecation_alignment": []
        }
        
        print("   🔄 Validating code-documentation synchronization...")
        
        # This is a simplified version - full implementation would require
        # deeper AST analysis and dynamic imports
        
        # Check for recent changes that might indicate sync issues
        sync_validation["recent_changes"] = self._check_recent_changes()
        
        return sync_validation
    
    def _check_recent_changes(self) -> Dict[str, Any]:
        """Check for recent changes that might indicate sync issues."""
        try:
            # Check git status for uncommitted changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode == 0:
                changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                api_changes = [c for c in changes if 'packages/api/' in c]
                doc_changes = [c for c in changes if 'docs/' in c]
                
                return {
                    "uncommitted_api_changes": len(api_changes),
                    "uncommitted_doc_changes": len(doc_changes),
                    "api_files": api_changes[:5],
                    "doc_files": doc_changes[:5],
                    "sync_risk": "high" if api_changes and not doc_changes else "low"
                }
        except Exception:
            pass
        
        return {"error": "Could not check recent changes"}
    
    def _provide_developer_assistance(self) -> Dict[str, Any]:
        """Provide developer assistance tools and utilities."""
        assistance = {
            "automated_fixes": {},
            "validation_scripts": {},
            "monitoring_setup": {},
            "developer_workflow": {}
        }
        
        print("   🛠️ Generating developer assistance tools...")
        
        # 1. Automated phantom route cleanup
        assistance["automated_fixes"] = self._generate_automated_fixes()
        
        # 2. Validation scripts for common issues
        assistance["validation_scripts"] = self._generate_validation_scripts()
        
        # 3. Monitoring and alerting setup
        assistance["monitoring_setup"] = self._generate_monitoring_setup()
        
        # 4. Developer workflow recommendations
        assistance["developer_workflow"] = self._generate_workflow_recommendations()
        
        return assistance
    
    def _generate_automated_fixes(self) -> Dict[str, Any]:
        """Generate automated fixes for common issues."""
        return {
            "phantom_route_cleanup": {
                "available": True,
                "description": "Automated script to remove phantom routes from documentation",
                "script_path": "scripts/cleanup_phantom_routes.py",
                "usage": "python scripts/cleanup_phantom_routes.py --dry-run"
            },
            "quality_enhancement": {
                "available": True,
                "description": "Automated documentation quality improvement",
                "script_path": "scripts/quality_enhancer.py",
                "usage": "python scripts/quality_enhancer.py docs/"
            }
        }
    
    def _generate_validation_scripts(self) -> Dict[str, Any]:
        """Generate validation scripts for developers."""
        return {
            "pre_commit_check": {
                "description": "Run before committing changes",
                "command": "python scripts/code_doc_parity_validator.py --quick-check"
            },
            "pr_validation": {
                "description": "Run before creating pull request",
                "command": "python scripts/code_doc_parity_validator.py --comprehensive"
            },
            "daily_sync_check": {
                "description": "Daily automated sync validation",
                "command": "python scripts/code_doc_parity_validator.py --monitor"
            }
        }
    
    def _generate_monitoring_setup(self) -> Dict[str, Any]:
        """Generate monitoring and alerting setup."""
        return {
            "github_actions": {
                "status": "implemented",
                "coverage_threshold": "80%",
                "failure_action": "fail_ci"
            },
            "quality_metrics": {
                "documentation_coverage": "tracked",
                "phantom_route_count": "tracked",
                "quality_score": "calculated"
            },
            "alerting": {
                "coverage_drop": "enabled",
                "phantom_routes_detected": "enabled",
                "quality_degradation": "recommended"
            }
        }
    
    def _generate_workflow_recommendations(self) -> Dict[str, Any]:
        """Generate developer workflow recommendations."""
        return {
            "api_development": [
                "Run parity check before committing API changes",
                "Update documentation in the same commit as API changes",
                "Use comprehensive commit messages that mention doc updates"
            ],
            "documentation_updates": [
                "Validate against actual code implementation",
                "Include request/response examples",
                "Add error handling documentation"
            ],
            "quality_maintenance": [
                "Run quality enhancer monthly",
                "Review phantom routes weekly", 
                "Monitor coverage metrics in CI"
            ]
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on all analysis."""
        recommendations = []
        
        # High priority recommendations
        basic_parity = results.get("basic_parity", {})
        phantom_analysis = results.get("phantom_route_analysis", {})
        
        if phantom_analysis.get("total_phantom_routes", 0) > 0:
            recommendations.append({
                "priority": "critical",
                "category": "phantom_routes",
                "title": f"Remove {phantom_analysis['total_phantom_routes']} phantom routes",
                "action": "Run phantom route cleanup script",
                "command": "python scripts/cleanup_phantom_routes.py"
            })
        
        if basic_parity.get("coverage_percentage", 100) < 90:
            recommendations.append({
                "priority": "high", 
                "category": "coverage",
                "title": "Improve API documentation coverage",
                "action": "Document missing API routes",
                "command": "python scripts/api_doc_generator.py"
            })
        
        # Quality improvements
        quality_assessment = results.get("quality_assessment", {})
        if quality_assessment.get("improvement_opportunities"):
            for improvement in quality_assessment["improvement_opportunities"]:
                recommendations.append({
                    "priority": improvement.get("priority", "medium"),
                    "category": "quality",
                    "title": f"Fix {improvement['issue_type']} in {improvement['affected_files']} files",
                    "action": improvement["recommendation"],
                    "command": "python scripts/quality_enhancer.py docs/"
                })
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description='Advanced Code-Documentation Parity Validator')
    parser.add_argument('--api-package', required=True, help='Path to API package')
    parser.add_argument('--docs-path', required=True, help='Path to documentation directory')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--quick-check', action='store_true', help='Run quick validation check')
    parser.add_argument('--comprehensive', action='store_true', help='Run comprehensive analysis')
    parser.add_argument('--monitor', action='store_true', help='Run monitoring checks')
    
    args = parser.parse_args()
    
    validator = CodeDocParityValidator(args.api_package, args.docs_path)
    
    if args.quick_check:
        print("🔍 Running Quick Parity Check...")
        results = validator._run_basic_parity_check()
        if results.get("success"):
            print("✅ Quick check passed")
        else:
            print("❌ Quick check failed")
            sys.exit(1)
    else:
        # Run comprehensive check
        results = validator.run_comprehensive_check()
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📁 Comprehensive report saved to: {args.output}")
        
        # Print summary
        print(f"\n📊 SUMMARY")
        print("=" * 40)
        basic = results.get("basic_parity", {})
        phantom = results.get("phantom_route_analysis", {})
        
        if not basic.get("error"):
            print(f"📈 API Documentation Coverage: {basic.get('coverage_percentage', 0):.1f}%")
            print(f"🔗 Documented Routes: {basic.get('documented_routes', 0)}/{basic.get('total_routes', 0)}")
            
        print(f"👻 Phantom Routes: {phantom.get('total_phantom_routes', 0)}")
        print(f"🎯 Recommendations: {len(results.get('recommendations', []))}")
        
        # Show top recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print(f"\n🚀 TOP RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"     Action: {rec['action']}")
                if rec.get('command'):
                    print(f"     Command: {rec['command']}")
                print()

if __name__ == "__main__":
    main()