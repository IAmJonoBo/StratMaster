#!/usr/bin/env python3
"""
Documentation Quality Enhancer
Improves documentation quality and validates CI quality gates
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any
import subprocess

class DocumentationQualityEnhancer:
    """Enhance API documentation quality and validate quality gates."""
    
    def __init__(self, docs_path: str):
        self.docs_path = Path(docs_path)
        self.api_docs_path = self.docs_path / "reference" / "api"
    
    def enhance_route_documentation(self, route_file: Path) -> int:
        """Enhance a specific API documentation file."""
        content = route_file.read_text()
        original_content = content
        enhancements = 0
        
        # Enhancement 1: Add proper descriptions from docstrings
        content = self._add_proper_descriptions(content)
        if content != original_content:
            enhancements += 1
            original_content = content
        
        # Enhancement 2: Add request/response examples
        content = self._add_request_response_examples(content)
        if content != original_content:
            enhancements += 1
            original_content = content
        
        # Enhancement 3: Add error handling documentation
        content = self._add_error_handling(content)
        if content != original_content:
            enhancements += 1
            original_content = content
        
        # Enhancement 4: Add use cases and context
        content = self._add_use_cases(content, route_file.stem)
        if content != original_content:
            enhancements += 1
        
        # Write back enhanced content
        route_file.write_text(content)
        return enhancements
    
    def _add_proper_descriptions(self, content: str) -> str:
        """Replace 'Endpoint handler: function_name' with proper descriptions."""
        
        # Dictionary of common endpoint patterns and their descriptions
        descriptions = {
            'get_.*_status': 'Get the current operational status and health metrics.',
            'get_.*_data': 'Retrieve data for the specified resource with optional filtering.',
            'get_.*_metrics': 'Fetch performance and operational metrics for monitoring.',
            'create_.*': 'Create a new resource with the provided parameters.',
            'update_.*': 'Update an existing resource with new information.',
            'delete_.*': 'Remove the specified resource from the system.',
            'generate_.*': 'Generate new content or analysis based on input parameters.',
            'process_.*': 'Process the provided data through the system pipeline.',
            'validate_.*': 'Validate the provided data against system rules.',
            'analyze_.*': 'Perform analysis on the provided data or resources.',
            'export_.*': 'Export data in the requested format.',
            'import_.*': 'Import and process external data into the system.',
            'render_.*': 'Render templates or generate formatted output.',
            'scan_.*': 'Scan resources for issues, vulnerabilities, or patterns.',
            'audit_.*': 'Perform audit operations and generate compliance reports.',
            'monitor_.*': 'Monitor system resources and provide real-time feedback.',
            'optimize_.*': 'Optimize system performance or resource allocation.',
            'configure_.*': 'Configure system settings or resource parameters.',
            'backup_.*': 'Create backup copies of data or system state.',
            'restore_.*': 'Restore data or system state from backup.',
        }
        
        for pattern, description in descriptions.items():
            # Replace basic endpoint handler references
            handler_pattern = rf"Endpoint handler: `({pattern})`"
            replacement = f"{description}\n\n**Handler Function:** `\\1`"
            content = re.sub(handler_pattern, replacement, content, flags=re.IGNORECASE)
        
        return content
    
    def _add_request_response_examples(self, content: str) -> str:
        """Add request and response examples to endpoints."""
        
        # Add examples for common endpoint patterns
        patterns = [
            (r'(### POST Endpoints.*?)(\n#### `POST /.*?/create.*?`\n)', self._create_endpoint_example),
            (r'(#### `GET /.*?/status.*?`\n)', self._status_endpoint_example),
            (r'(#### `POST /.*?/analyze.*?`\n)', self._analyze_endpoint_example),
            (r'(#### `GET /.*?/metrics.*?`\n)', self._metrics_endpoint_example),
        ]
        
        for pattern, example_func in patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in reversed(list(matches)):  # Reverse to maintain indices
                start, end = match.span()
                enhanced_section = example_func(match.group(0))
                content = content[:start] + enhanced_section + content[end:]
        
        return content
    
    def _create_endpoint_example(self, match_text: str) -> str:
        """Add example for create endpoints."""
        if "**Request Example:**" in match_text:
            return match_text
        
        example = """

**Request Example:**
```json
{
  "name": "string",
  "parameters": {},
  "metadata": {
    "created_by": "user_id",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**Response Example:**
```json
{
  "id": "resource_123",
  "status": "created",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Status Codes:**
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input parameters
- `409 Conflict`: Resource already exists

"""
        return match_text + example
    
    def _status_endpoint_example(self, match_text: str) -> str:
        """Add example for status endpoints."""
        if "**Response Example:**" in match_text:
            return match_text
            
        example = """

**Response Example:**
```json
{
  "status": "operational",
  "uptime_seconds": 3600,
  "last_updated": "2024-01-01T12:00:00Z",
  "metrics": {
    "requests_per_minute": 45,
    "average_response_time_ms": 125
  }
}
```

**Status Values:**
- `operational`: Service is running normally
- `degraded`: Service is running with reduced performance
- `maintenance`: Service is under maintenance
- `error`: Service is experiencing issues

"""
        return match_text + example
    
    def _analyze_endpoint_example(self, match_text: str) -> str:
        """Add example for analyze endpoints."""
        if "**Request Example:**" in match_text:
            return match_text
            
        example = """

**Request Example:**
```json
{
  "data": "input data to analyze",
  "analysis_type": "comprehensive",
  "options": {
    "include_confidence": true,
    "max_results": 10
  }
}
```

**Response Example:**
```json
{
  "analysis_id": "analysis_123",
  "results": [
    {
      "finding": "Key insight discovered",
      "confidence": 0.85,
      "evidence": ["source1", "source2"]
    }
  ],
  "metadata": {
    "processing_time_ms": 1500,
    "model_used": "gpt-4o"
  }
}
```

"""
        return match_text + example
    
    def _metrics_endpoint_example(self, match_text: str) -> str:
        """Add example for metrics endpoints."""
        if "**Response Example:**" in match_text:
            return match_text
            
        example = """

**Query Parameters:**
- `time_range`: Time period (1h, 24h, 7d, 30d)
- `granularity`: Data granularity (minute, hour, day)
- `format`: Response format (json, csv)

**Response Example:**
```json
{
  "metric_name": "api_requests",
  "time_range": "24h",
  "data_points": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "value": 142.5,
      "labels": {
        "service": "api",
        "endpoint": "/analytics"
      }
    }
  ],
  "summary": {
    "min": 98.2,
    "max": 256.7,
    "avg": 142.5,
    "total_points": 144
  }
}
```

"""
        return match_text + example
    
    def _add_error_handling(self, content: str) -> str:
        """Add comprehensive error handling documentation."""
        
        if "## Error Handling" in content:
            return content
        
        error_section = """

## Error Handling

All endpoints follow consistent error response patterns:

### Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional context",
      "suggestion": "How to fix the issue"
    },
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes
- `400 Bad Request`: Invalid request parameters or format
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Insufficient permissions for the operation
- `404 Not Found`: Requested resource does not exist
- `409 Conflict`: Resource conflict (e.g., already exists)
- `422 Unprocessable Entity`: Valid format but invalid content
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side processing error
- `503 Service Unavailable`: Service temporarily unavailable

### Rate Limiting
- Most endpoints are rate-limited to prevent abuse
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

"""
        
        # Add error section before the last line
        lines = content.split('\n')
        lines.insert(-1, error_section)
        return '\n'.join(lines)
    
    def _add_use_cases(self, content: str, router_name: str) -> str:
        """Add use cases and context for the router."""
        
        if "## Use Cases" in content:
            return content
        
        # Router-specific use cases
        use_cases_map = {
            'analytics': [
                "Monitor system performance and user engagement metrics",
                "Generate business intelligence dashboards and reports",
                "Track HEART metrics (Happiness, Engagement, Adoption, Retention, Task success)",
                "Forecast trends and predict future performance patterns"
            ],
            'security': [
                "Implement authentication and authorization workflows",
                "Monitor security events and generate compliance reports",
                "Scan for vulnerabilities and security issues",
                "Manage user permissions and access control"
            ],
            'strategy': [
                "Generate strategic analysis and recommendations",
                "Create business model canvases and strategic frameworks",
                "Parse and analyze strategic documents",
                "Support strategic planning and decision-making processes"
            ],
            'templates': [
                "Generate industry-specific templates and frameworks",
                "Render custom templates with dynamic content",
                "Provide structured templates for strategic planning",
                "Support template-driven content generation"
            ],
            'ux_quality_gates': [
                "Monitor user experience quality and accessibility",
                "Run automated accessibility audits",
                "Track Core Web Vitals and performance metrics",
                "Enforce UX quality standards in CI/CD pipelines"
            ],
            'enhanced_performance': [
                "Optimize system performance and resource utilization",
                "Monitor and manage background task processing",
                "Implement performance quality gates and thresholds",
                "Track and analyze system performance metrics"
            ]
        }
        
        router_key = router_name.replace('-api', '').replace('_', '')
        use_cases = use_cases_map.get(router_key, [
            f"Core {router_name} functionality and operations",
            f"Support {router_name} workflows and processes",
            f"Provide {router_name} data and management capabilities"
        ])
        
        use_cases_section = f"""

## Use Cases

This {router_name.replace('-api', '').replace('_', ' ').title()} API supports the following primary use cases:

"""
        for i, use_case in enumerate(use_cases, 1):
            use_cases_section += f"{i}. {use_case}\n"
        
        use_cases_section += "\n"
        
        # Add use cases after the authentication section
        auth_end = content.find("## Endpoints")
        if auth_end != -1:
            content = content[:auth_end] + use_cases_section + content[auth_end:]
        else:
            # Add before the last section
            content = content + use_cases_section
        
        return content
    
    def validate_quality_gates(self) -> Dict[str, Any]:
        """Validate that CI quality gates are properly enforced."""
        
        ci_file = Path("/home/runner/work/StratMaster/StratMaster/.github/workflows/ci.yml")
        if not ci_file.exists():
            return {"error": "CI workflow file not found"}
        
        ci_content = ci_file.read_text()
        
        quality_checks = {
            "api_parity_check": "api_docs_parity_checker.py" in ci_content,
            "mutation_testing": "mutation_testing.py" in ci_content,
            "dora_metrics": "dora_metrics.py" in ci_content,
            "sbom_generation": "generate_sbom.py" in ci_content,
            "lighthouse_budget": "lighthouse-budget.json" in ci_content or "lighthouse" in ci_content.lower(),
            "security_scanning": "bandit" in ci_content or "pip-audit" in ci_content,
        }
        
        # Check if quality gates have proper thresholds
        threshold_checks = {}
        
        # Check API parity threshold
        if "--fail-threshold" in ci_content:
            threshold_match = re.search(r"--fail-threshold\s+(\d+(?:\.\d+)?)", ci_content)
            if threshold_match:
                threshold_checks["api_parity_threshold"] = float(threshold_match.group(1))
            else:
                threshold_checks["api_parity_threshold"] = "not_found"
        
        # Check mutation testing threshold
        if "--quality-gates" in ci_content:
            threshold_checks["mutation_quality_gates"] = "enabled"
        else:
            threshold_checks["mutation_quality_gates"] = "disabled"
        
        return {
            "quality_checks": quality_checks,
            "threshold_checks": threshold_checks,
            "total_checks": len([c for c in quality_checks.values() if c]),
            "missing_checks": [k for k, v in quality_checks.items() if not v]
        }
    
    def enhance_all_documentation(self) -> Dict[str, Any]:
        """Enhance all API documentation files."""
        
        results = {
            "files_enhanced": [],
            "total_enhancements": 0,
            "files_processed": 0
        }
        
        # Process all API documentation files
        for api_file in self.api_docs_path.glob("*-api.md"):
            enhancements = self.enhance_route_documentation(api_file)
            results["files_processed"] += 1
            results["total_enhancements"] += enhancements
            
            if enhancements > 0:
                results["files_enhanced"].append({
                    "file": str(api_file),
                    "enhancements": enhancements
                })
        
        return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 quality_enhancer.py <docs_path>")
        sys.exit(1)
    
    docs_path = sys.argv[1]
    enhancer = DocumentationQualityEnhancer(docs_path)
    
    print("✨ Starting documentation quality enhancement...")
    
    # 1. Enhance all documentation
    print("📝 Enhancing API documentation quality...")
    results = enhancer.enhance_all_documentation()
    print(f"   Processed {results['files_processed']} files")
    print(f"   Applied {results['total_enhancements']} total enhancements")
    
    if results["files_enhanced"]:
        print("   Enhanced files:")
        for file_info in results["files_enhanced"]:
            filename = Path(file_info["file"]).name
            print(f"     - {filename}: {file_info['enhancements']} improvements")
    
    # 2. Validate quality gates
    print("🔍 Validating CI quality gates...")
    gate_results = enhancer.validate_quality_gates()
    
    if "error" in gate_results:
        print(f"   ❌ Error: {gate_results['error']}")
    else:
        print(f"   ✅ {gate_results['total_checks']}/6 quality checks active")
        
        if gate_results["missing_checks"]:
            print("   ⚠️  Missing quality checks:")
            for check in gate_results["missing_checks"]:
                print(f"     - {check}")
        
        print("   Quality gate thresholds:")
        for check, value in gate_results["threshold_checks"].items():
            print(f"     - {check}: {value}")
    
    print("\n✅ Documentation quality enhancement completed!")

if __name__ == "__main__":
    main()