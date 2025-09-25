#!/usr/bin/env python3
"""
Automated Phantom Route Cleanup Tool
Helps developers identify and remove phantom routes from documentation
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Set
import argparse
import subprocess

class PhantomRouteCleanup:
    """Automated cleanup of phantom routes in documentation."""
    
    def __init__(self, docs_path: str, dry_run: bool = True):
        self.docs_path = Path(docs_path)
        self.dry_run = dry_run
        self.phantom_routes = []
        self.cleanup_actions = []
        
    def identify_phantom_routes(self) -> List[str]:
        """Identify phantom routes using the parity checker."""
        try:
            # Run parity checker to get phantom routes
            result = subprocess.run([
                'python3', 'scripts/api_docs_parity_checker.py',
                '--api-package', 'packages/api/src/stratmaster_api',
                '--docs-path', str(self.docs_path),
                '--output', '/tmp/phantom_check.json',
                '--fail-threshold', '80.0'
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            if Path('/tmp/phantom_check.json').exists():
                with open('/tmp/phantom_check.json') as f:
                    data = json.load(f)
                self.phantom_routes = data.get("documented_but_missing", [])
                return self.phantom_routes
            else:
                print("❌ Could not run parity check")
                return []
                
        except Exception as e:
            print(f"❌ Error identifying phantom routes: {e}")
            return []
    
    def analyze_phantom_routes(self) -> Dict[str, Any]:
        """Analyze phantom routes and their locations."""
        analysis = {
            "total_phantom_routes": len(self.phantom_routes),
            "route_locations": {},
            "cleanup_strategy": {}
        }
        
        if not self.phantom_routes:
            return analysis
        
        print(f"🔍 Analyzing {len(self.phantom_routes)} phantom routes...")
        
        for route in self.phantom_routes:
            locations = self._find_route_in_docs(route)
            analysis["route_locations"][route] = locations
            
            # Determine cleanup strategy
            strategy = self._determine_cleanup_strategy(route, locations)
            analysis["cleanup_strategy"][route] = strategy
        
        return analysis
    
    def _find_route_in_docs(self, route: str) -> List[Dict[str, Any]]:
        """Find all locations where a phantom route is documented."""
        locations = []
        
        # Search in all markdown files
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Look for HTTP method + route pattern
                    if route in line and any(method in line for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
                        locations.append({
                            "file": str(md_file.relative_to(self.docs_path)),
                            "full_path": str(md_file),
                            "line": line_num,
                            "content": line.strip(),
                            "context_before": lines[max(0, line_num-2):line_num-1] if line_num > 1 else [],
                            "context_after": lines[line_num:min(len(lines), line_num+2)] if line_num < len(lines) else []
                        })
            except Exception as e:
                print(f"Warning: Could not analyze {md_file}: {e}")
        
        return locations
    
    def _determine_cleanup_strategy(self, route: str, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine the best cleanup strategy for a phantom route."""
        if not locations:
            return {"action": "no_action", "reason": "Route not found in documentation"}
        
        # Analyze the context to determine strategy
        strategies = []
        
        for loc in locations:
            content = loc["content"].lower()
            context = " ".join(loc.get("context_before", []) + loc.get("context_after", [])).lower()
            
            if any(word in content for word in ["todo", "placeholder", "coming soon"]):
                strategies.append("remove_placeholder")
            elif any(word in context for word in ["deprecated", "removed", "obsolete"]):
                strategies.append("remove_deprecated")
            elif route.count("/") <= 1:  # Simple route like "/docs"
                strategies.append("remove_generic")
            elif any(version in route for version in ["/v1/", "/v2/", "/beta/"]):
                strategies.append("update_version")
            else:
                strategies.append("manual_review")
        
        # Choose the most common strategy
        if strategies:
            most_common = max(set(strategies), key=strategies.count)
            return {
                "action": most_common,
                "confidence": strategies.count(most_common) / len(strategies),
                "locations_count": len(locations)
            }
        
        return {"action": "manual_review", "confidence": 0.0, "locations_count": len(locations)}
    
    def perform_cleanup(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform automated cleanup of phantom routes."""
        cleanup_results = {
            "routes_processed": 0,
            "routes_cleaned": 0,
            "manual_review_needed": 0,
            "files_modified": set(),
            "actions_taken": []
        }
        
        if not analysis.get("route_locations"):
            print("ℹ️ No phantom routes to clean up")
            return cleanup_results
        
        print(f"🧹 {'[DRY RUN] ' if self.dry_run else ''}Starting phantom route cleanup...")
        
        for route, strategy in analysis.get("cleanup_strategy", {}).items():
            cleanup_results["routes_processed"] += 1
            locations = analysis["route_locations"].get(route, [])
            
            action = strategy.get("action", "manual_review")
            confidence = strategy.get("confidence", 0.0)
            
            if action == "manual_review" or confidence < 0.5:
                cleanup_results["manual_review_needed"] += 1
                print(f"⚠️ Manual review needed for: {route}")
                self._log_manual_review_item(route, locations)
            else:
                success = self._execute_cleanup_action(route, locations, action)
                if success:
                    cleanup_results["routes_cleaned"] += 1
                    for loc in locations:
                        cleanup_results["files_modified"].add(loc["file"])
                
                cleanup_results["actions_taken"].append({
                    "route": route,
                    "action": action,
                    "success": success,
                    "files": [loc["file"] for loc in locations]
                })
        
        print(f"\n📊 Cleanup Summary:")
        print(f"   Processed: {cleanup_results['routes_processed']} routes")
        print(f"   Cleaned: {cleanup_results['routes_cleaned']} routes")
        print(f"   Manual review: {cleanup_results['manual_review_needed']} routes")
        print(f"   Files modified: {len(cleanup_results['files_modified'])} files")
        
        return cleanup_results
    
    def _execute_cleanup_action(self, route: str, locations: List[Dict[str, Any]], action: str) -> bool:
        """Execute a specific cleanup action."""
        try:
            for location in locations:
                file_path = Path(location["full_path"])
                
                if not file_path.exists():
                    continue
                
                content = file_path.read_text()
                lines = content.split('\n')
                
                # Find and remove the line(s) containing the phantom route
                modified_lines = []
                skip_next = 0
                
                for i, line in enumerate(lines):
                    if skip_next > 0:
                        skip_next -= 1
                        continue
                    
                    if route in line and any(method in line for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
                        print(f"{'[DRY RUN] ' if self.dry_run else ''}Removing phantom route {route} from {location['file']}:{i+1}")
                        
                        # Depending on action, might remove additional lines
                        if action == "remove_placeholder":
                            # Remove the route line and any following description lines
                            skip_next = self._count_description_lines(lines, i)
                        elif action == "remove_deprecated":
                            # Just remove the route line
                            pass
                        elif action == "remove_generic":
                            # Remove route and minimal context
                            pass
                        
                        # Skip this line (it gets removed)
                        continue
                    
                    modified_lines.append(line)
                
                # Write back the modified content
                if not self.dry_run:
                    modified_content = '\n'.join(modified_lines)
                    file_path.write_text(modified_content)
            
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning up {route}: {e}")
            return False
    
    def _count_description_lines(self, lines: List[str], start_index: int) -> int:
        """Count how many description lines follow a route definition."""
        count = 0
        for i in range(start_index + 1, min(len(lines), start_index + 5)):
            line = lines[i].strip()
            if not line or line.startswith('#') or any(method in line for method in ['GET', 'POST', 'PUT', 'DELETE']):
                break
            count += 1
        return count
    
    def _log_manual_review_item(self, route: str, locations: List[Dict[str, Any]]):
        """Log an item that needs manual review."""
        print(f"   Route: {route}")
        for loc in locations[:2]:  # Show first 2 locations
            print(f"     File: {loc['file']}:{loc['line']}")
            print(f"     Context: {loc['content']}")
        if len(locations) > 2:
            print(f"     ... and {len(locations) - 2} more locations")
        print()
    
    def generate_cleanup_report(self, analysis: Dict[str, Any], cleanup_results: Dict[str, Any]) -> str:
        """Generate a comprehensive cleanup report."""
        report = f"""# Phantom Route Cleanup Report

**Generated**: {Path.cwd().name} - {analysis.get('total_phantom_routes', 0)} phantom routes analyzed

## Summary
- **Total Phantom Routes**: {analysis.get('total_phantom_routes', 0)}
- **Routes Cleaned**: {cleanup_results.get('routes_cleaned', 0)}
- **Manual Review Needed**: {cleanup_results.get('manual_review_needed', 0)}
- **Files Modified**: {len(cleanup_results.get('files_modified', set()))}

## Actions Taken
"""
        
        for action in cleanup_results.get('actions_taken', []):
            status = "✅ Success" if action['success'] else "❌ Failed"
            report += f"- **{action['route']}**: {action['action']} - {status}\n"
            for file in action['files']:
                report += f"  - Modified: {file}\n"
            report += "\n"
        
        if cleanup_results.get('manual_review_needed', 0) > 0:
            report += "\n## Manual Review Required\n\n"
            for route, strategy in analysis.get('cleanup_strategy', {}).items():
                if strategy.get('action') == 'manual_review' or strategy.get('confidence', 0) < 0.5:
                    report += f"### {route}\n"
                    report += f"- **Reason**: {strategy.get('action', 'Unknown')}\n"
                    report += f"- **Confidence**: {strategy.get('confidence', 0):.1%}\n"
                    
                    locations = analysis.get('route_locations', {}).get(route, [])
                    if locations:
                        report += f"- **Locations**:\n"
                        for loc in locations:
                            report += f"  - {loc['file']}:{loc['line']}\n"
                    report += "\n"
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Automated Phantom Route Cleanup')
    parser.add_argument('--docs-path', default='docs', help='Path to documentation directory')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Run in dry-run mode (default)')
    parser.add_argument('--execute', action='store_true', help='Actually perform cleanup (not dry-run)')
    parser.add_argument('--output', help='Save cleanup report to file')
    
    args = parser.parse_args()
    
    # If --execute is specified, disable dry-run
    dry_run = not args.execute
    
    cleanup = PhantomRouteCleanup(args.docs_path, dry_run=dry_run)
    
    print("🔍 Phantom Route Cleanup Tool")
    print("=" * 40)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'EXECUTION MODE (files will be modified)'}")
    print(f"Docs path: {args.docs_path}")
    print()
    
    # Step 1: Identify phantom routes
    phantom_routes = cleanup.identify_phantom_routes()
    
    if not phantom_routes:
        print("✅ No phantom routes found! Documentation is in sync with code.")
        return
    
    print(f"Found {len(phantom_routes)} phantom routes:")
    for i, route in enumerate(phantom_routes, 1):
        print(f"  {i}. {route}")
    print()
    
    # Step 2: Analyze phantom routes
    analysis = cleanup.analyze_phantom_routes()
    
    # Step 3: Perform cleanup
    cleanup_results = cleanup.perform_cleanup(analysis)
    
    # Step 4: Generate report
    if args.output:
        report = cleanup.generate_cleanup_report(analysis, cleanup_results)
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\n📁 Cleanup report saved to: {args.output}")
    
    # Step 5: Provide next steps
    if dry_run and cleanup_results.get('routes_cleaned', 0) > 0:
        print(f"\n🚀 Next Steps:")
        print(f"   To apply these changes, run:")
        print(f"   python scripts/cleanup_phantom_routes.py --execute --docs-path {args.docs_path}")
    
    if cleanup_results.get('manual_review_needed', 0) > 0:
        print(f"\n⚠️ Manual review required for {cleanup_results['manual_review_needed']} routes")
        print(f"   Review the locations listed above and manually remove or fix these phantom routes")

if __name__ == "__main__":
    main()