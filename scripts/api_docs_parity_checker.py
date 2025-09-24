#!/usr/bin/env python3
"""
API Documentation Parity Checker
Implements docs/code parity automation as identified in GAP_ANALYSIS.md
"""

import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Optional, Tuple
import argparse
import importlib.util
import inspect


class APIRouteDiscovery:
    """Discover FastAPI routes and validate documentation coverage."""
    
    def __init__(self, api_package_path: str):
        self.api_package_path = Path(api_package_path)
        self.discovered_routes = []
        self.schemas = {}
        
    def discover_routes(self) -> List[Dict[str, Any]]:
        """Discover all FastAPI routes in the package."""
        print("🔍 Discovering API routes...")
        
        # Find all Python files in the package
        python_files = list(self.api_package_path.rglob("*.py"))
        
        for py_file in python_files:
            if py_file.name.startswith("__"):
                continue
            
            try:
                self._analyze_python_file(py_file)
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}")
        
        print(f"Found {len(self.discovered_routes)} API routes")
        return self.discovered_routes
    
    def _analyze_python_file(self, py_file: Path) -> None:
        """Analyze a Python file for FastAPI route definitions."""
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Look for FastAPI route decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    route_info = self._extract_route_from_function(node, py_file, content)
                    if route_info:
                        self.discovered_routes.append(route_info)
                        
        except (SyntaxError, UnicodeDecodeError, IOError) as e:
            print(f"Warning: Could not parse {py_file}: {e}")
    
    def _extract_route_from_function(self, func_node: ast.FunctionDef, py_file: Path, content: str) -> Optional[Dict[str, Any]]:
        """Extract route information from a function with FastAPI decorators."""
        route_info = None
        
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                # Handle decorator calls like @app.get("/path")
                if (hasattr(decorator.func, 'attr') and 
                    decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']):
                    
                    method = decorator.func.attr.upper()
                    path = None
                    
                    # Extract path from decorator arguments
                    if decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                        elif isinstance(decorator.args[0], ast.Str):  # Python < 3.8 compatibility
                            path = decorator.args[0].s
                    
                    if path:
                        route_info = {
                            'method': method,
                            'path': path,
                            'function_name': func_node.name,
                            'file': str(py_file.relative_to(self.api_package_path)),
                            'line_number': func_node.lineno,
                            'docstring': ast.get_docstring(func_node),
                            'parameters': [],
                            'response_model': None,
                            'tags': [],
                            'summary': None,
                            'description': None
                        }
                        
                        # Extract additional metadata from decorator kwargs
                        for keyword in decorator.keywords:
                            if keyword.arg == 'tags' and isinstance(keyword.value, ast.List):
                                route_info['tags'] = [self._extract_string_value(item) for item in keyword.value.elts]
                            elif keyword.arg == 'summary':
                                route_info['summary'] = self._extract_string_value(keyword.value)
                            elif keyword.arg == 'description':
                                route_info['description'] = self._extract_string_value(keyword.value)
                            elif keyword.arg == 'response_model':
                                route_info['response_model'] = self._extract_type_annotation(keyword.value)
                        
                        # Extract parameters from function signature
                        route_info['parameters'] = self._extract_function_parameters(func_node)
                        
                        break
        
        return route_info
    
    def _extract_string_value(self, node: ast.AST) -> Optional[str]:
        """Extract string value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, str) else str(node.value)
        elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
            return node.s
        return None
    
    def _extract_type_annotation(self, node: ast.AST) -> Optional[str]:
        """Extract type annotation as string."""
        try:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
        except:
            return None
    
    def _extract_function_parameters(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract parameter information from function signature."""
        parameters = []
        
        for arg in func_node.args.args:
            if arg.arg == 'self':
                continue
            
            param_info = {
                'name': arg.arg,
                'type': None,
                'required': True,
                'description': None
            }
            
            # Extract type annotation
            if arg.annotation:
                param_info['type'] = self._extract_type_annotation(arg.annotation)
            
            parameters.append(param_info)
        
        return parameters


class DocumentationChecker:
    """Check documentation coverage for discovered API routes."""
    
    def __init__(self, docs_path: str):
        self.docs_path = Path(docs_path)
        self.doc_files = []
        self.documented_routes = set()
        
    def scan_documentation(self) -> Set[str]:
        """Scan documentation files for API route references."""
        print("📖 Scanning documentation files...")
        
        # Find all documentation files
        doc_extensions = {'.md', '.rst', '.txt'}
        self.doc_files = [
            f for f in self.docs_path.rglob("*") 
            if f.suffix.lower() in doc_extensions and f.is_file()
        ]
        
        route_pattern = re.compile(r'(?:GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+([/\w\-\{\}:]+)', re.IGNORECASE)
        path_pattern = re.compile(r'`([/\w\-\{\}:]+)`')
        
        for doc_file in self.doc_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find route references
                route_matches = route_pattern.findall(content)
                path_matches = path_pattern.findall(content)
                
                # Normalize and add to documented routes
                for match in route_matches + path_matches:
                    if match.startswith('/'):
                        self.documented_routes.add(self._normalize_path(match))
                        
            except (UnicodeDecodeError, IOError) as e:
                print(f"Warning: Could not read {doc_file}: {e}")
        
        print(f"Found {len(self.documented_routes)} documented routes")
        return self.documented_routes
    
    def _normalize_path(self, path: str) -> str:
        """Normalize API path for comparison."""
        # Convert path parameters to consistent format
        # e.g., /users/{user_id} or /users/{id} -> /users/{id}
        normalized = re.sub(r'\{[^}]+\}', '{id}', path)
        return normalized.rstrip('/')


class ParityChecker:
    """Main parity checker that combines route discovery and documentation scanning."""
    
    def __init__(self, api_package_path: str, docs_path: str):
        self.route_discovery = APIRouteDiscovery(api_package_path)
        self.doc_checker = DocumentationChecker(docs_path)
        
    def check_parity(self) -> Dict[str, Any]:
        """Perform comprehensive parity check between API and documentation."""
        print("🔍 Starting API documentation parity check...")
        
        # Discover routes
        discovered_routes = self.route_discovery.discover_routes()
        
        # Scan documentation
        documented_paths = self.doc_checker.scan_documentation()
        
        # Create route path set for comparison
        discovered_paths = set()
        route_details = {}
        
        for route in discovered_routes:
            normalized_path = self.doc_checker._normalize_path(route['path'])
            discovered_paths.add(normalized_path)
            route_details[normalized_path] = route
        
        # Find gaps
        undocumented_routes = discovered_paths - documented_paths
        documented_but_not_implemented = documented_paths - discovered_paths
        
        # Calculate coverage
        total_routes = len(discovered_paths)
        documented_routes = len(discovered_paths - undocumented_routes)
        coverage_percentage = (documented_routes / total_routes * 100) if total_routes > 0 else 0
        
        # Generate detailed analysis
        results = {
            'timestamp': '2024-01-01T00:00:00Z',  # Would use actual timestamp
            'summary': {
                'total_routes': total_routes,
                'documented_routes': documented_routes,
                'undocumented_routes': len(undocumented_routes),
                'coverage_percentage': coverage_percentage,
                'documentation_files_scanned': len(self.doc_checker.doc_files)
            },
            'undocumented_routes': [],
            'documented_but_not_implemented': list(documented_but_not_implemented),
            'well_documented_routes': [],
            'routes_needing_improvement': []
        }
        
        # Analyze each undocumented route
        for path in undocumented_routes:
            route = route_details.get(path)
            if route:
                results['undocumented_routes'].append({
                    'path': route['path'],
                    'method': route['method'],
                    'function_name': route['function_name'],
                    'file': route['file'],
                    'line_number': route['line_number'],
                    'has_docstring': bool(route['docstring']),
                    'has_summary': bool(route['summary']),
                    'tags': route['tags']
                })
        
        # Analyze documented routes for quality
        for path in (discovered_paths - undocumented_routes):
            route = route_details.get(path)
            if route:
                quality_score = self._calculate_documentation_quality(route)
                
                route_analysis = {
                    'path': route['path'],
                    'method': route['method'],
                    'function_name': route['function_name'],
                    'quality_score': quality_score,
                    'has_docstring': bool(route['docstring']),
                    'has_summary': bool(route['summary']),
                    'has_description': bool(route['description']),
                    'parameter_count': len(route['parameters']),
                    'tags': route['tags']
                }
                
                if quality_score >= 80:
                    results['well_documented_routes'].append(route_analysis)
                else:
                    results['routes_needing_improvement'].append(route_analysis)
        
        return results
    
    def _calculate_documentation_quality(self, route: Dict[str, Any]) -> int:
        """Calculate documentation quality score for a route."""
        score = 0
        
        # Base score for being documented
        score += 30
        
        # Docstring presence and quality
        if route['docstring']:
            score += 20
            if len(route['docstring']) > 50:  # Substantial docstring
                score += 10
        
        # Summary and description
        if route['summary']:
            score += 15
        if route['description']:
            score += 15
        
        # Parameters documented
        if route['parameters']:
            score += 10
        
        return min(score, 100)
    
    def generate_report(self, results: Dict[str, Any], output_file: str) -> None:
        """Generate comprehensive parity report."""
        
        # Save JSON report
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        summary = results['summary']
        
        print("\n📊 API Documentation Parity Report")
        print("=" * 50)
        print(f"Total API routes: {summary['total_routes']}")
        print(f"Documented routes: {summary['documented_routes']}")
        print(f"Documentation coverage: {summary['coverage_percentage']:.1f}%")
        print(f"Documentation files scanned: {summary['documentation_files_scanned']}")
        
        if results['undocumented_routes']:
            print(f"\n❌ Undocumented routes ({len(results['undocumented_routes'])}):")
            for route in results['undocumented_routes'][:5]:  # Show first 5
                print(f"  • {route['method']} {route['path']} ({route['file']}:{route['line_number']})")
            
            if len(results['undocumented_routes']) > 5:
                print(f"  ... and {len(results['undocumented_routes']) - 5} more")
        
        if results['documented_but_not_implemented']:
            print(f"\n⚠️ Documented but not implemented ({len(results['documented_but_not_implemented'])}):")
            for path in results['documented_but_not_implemented'][:3]:
                print(f"  • {path}")
        
        if results['routes_needing_improvement']:
            print(f"\n📝 Routes needing better documentation ({len(results['routes_needing_improvement'])}):")
            for route in results['routes_needing_improvement'][:3]:
                print(f"  • {route['method']} {route['path']} (quality: {route['quality_score']}%)")
        
        # Generate recommendations
        recommendations = []
        
        if summary['coverage_percentage'] < 90:
            recommendations.append(f"📋 Priority: Improve documentation coverage from {summary['coverage_percentage']:.1f}% to >90%")
        
        if len(results['undocumented_routes']) > 0:
            recommendations.append(f"📝 Document {len(results['undocumented_routes'])} missing API routes")
        
        if len(results['routes_needing_improvement']) > 0:
            recommendations.append(f"✨ Enhance documentation quality for {len(results['routes_needing_improvement'])} routes")
        
        if len(results['documented_but_not_implemented']) > 0:
            recommendations.append(f"🔧 Remove or implement {len(results['documented_but_not_implemented'])} documented but missing routes")
        
        if recommendations:
            print(f"\n📋 Recommendations:")
            for rec in recommendations:
                print(f"  {rec}")
        else:
            print(f"\n✅ Documentation parity looks good!")
        
        print(f"\n📁 Full report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='API Documentation Parity Checker')
    parser.add_argument('--api-package', required=True, help='Path to API package (e.g., packages/api/src/stratmaster_api)')
    parser.add_argument('--docs-path', required=True, help='Path to documentation directory (e.g., docs/)')
    parser.add_argument('--output', default='api-parity-report.json', help='Output report file')
    parser.add_argument('--fail-threshold', type=float, default=80.0, help='Minimum coverage percentage to pass (default: 80.0)')
    
    args = parser.parse_args()
    
    # Validate inputs
    api_path = Path(args.api_package)
    docs_path = Path(args.docs_path)
    
    if not api_path.exists():
        print(f"Error: API package path does not exist: {api_path}")
        return 1
    
    if not docs_path.exists():
        print(f"Error: Documentation path does not exist: {docs_path}")
        return 1
    
    # Run parity check
    checker = ParityChecker(str(api_path), str(docs_path))
    results = checker.check_parity()
    checker.generate_report(results, args.output)
    
    # Check if coverage meets threshold
    coverage = results['summary']['coverage_percentage']
    if coverage < args.fail_threshold:
        print(f"\n❌ FAIL: Documentation coverage {coverage:.1f}% is below threshold {args.fail_threshold}%")
        return 1
    else:
        print(f"\n✅ PASS: Documentation coverage {coverage:.1f}% meets threshold {args.fail_threshold}%")
        return 0


if __name__ == '__main__':
    sys.exit(main())