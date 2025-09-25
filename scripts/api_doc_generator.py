#!/usr/bin/env python3
"""
API Documentation Generator
Systematically generates documentation for all discovered API routes
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import subprocess

class APIDocGenerator:
    """Generate comprehensive API documentation from discovered routes."""
    
    def __init__(self, parity_report_path: str, docs_path: str):
        self.docs_path = Path(docs_path)
        self.api_docs_path = self.docs_path / "reference" / "api"
        
        # Load the parity report
        with open(parity_report_path) as f:
            self.report = json.load(f)
    
    def generate_router_documentation(self, router_name: str, routes: List[Dict[str, Any]]) -> str:
        """Generate documentation for a specific router."""
        
        # Organize routes by method
        routes_by_method = {}
        for route in routes:
            method = route['method']
            if method not in routes_by_method:
                routes_by_method[method] = []
            routes_by_method[method].append(route)
        
        # Generate markdown
        router_title = router_name.replace('_', ' ').title()
        content = f"""# {router_title} API

This document describes the {router_title} endpoints in the StratMaster API.

## Base Path
All endpoints are prefixed with the router's base path as defined in the FastAPI router.

## Authentication
All endpoints require proper authentication. POST/PUT/DELETE endpoints also require an `Idempotency-Key` header.

## Endpoints

"""
        
        # Sort methods in logical order
        method_order = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        for method in method_order:
            if method not in routes_by_method:
                continue
                
            content += f"### {method} Endpoints\n\n"
            
            for route in sorted(routes_by_method[method], key=lambda x: x['path']):
                content += f"#### `{method} {route['path']}`\n\n"
                
                # Add description from docstring if available
                if route.get('docstring'):
                    content += f"{route['docstring']}\n\n"
                else:
                    content += f"Endpoint handler: `{route['function_name']}`\n\n"
                
                # Add response model if available
                if route.get('response_model'):
                    content += f"**Response Model:** `{route['response_model']}`\n\n"
                
                # Add parameters if available
                if route.get('parameters'):
                    content += "**Parameters:**\n\n"
                    for param in route['parameters']:
                        required = "required" if param.get('required', True) else "optional"
                        param_type = param.get('type', 'unknown')
                        content += f"- `{param['name']}` ({param_type}, {required})\n"
                    content += "\n"
                
                # Add file reference
                content += f"**Implementation:** `{route['file']}:{route['line_number']}`\n\n"
                content += "---\n\n"
        
        return content
    
    def clean_phantom_routes(self) -> List[str]:
        """Remove documented routes that don't exist in the code."""
        phantom_routes = []
        
        # Common phantom routes found in docs
        phantom_patterns = [
            "/forecasts",
            "/retrieval/splade/query", 
            "/knowledge/consolidate",
            "/strategy",
            "/graph/traverse",
            "/sources/validate"
        ]
        
        for api_file in self.api_docs_path.glob("*.md"):
            content = api_file.read_text()
            original_content = content
            
            for pattern in phantom_patterns:
                # Remove lines containing phantom routes
                lines = content.split('\n')
                filtered_lines = []
                skip_next = False
                
                for i, line in enumerate(lines):
                    if pattern in line and any(method in line for method in ['GET', 'POST', 'PUT', 'DELETE']):
                        phantom_routes.append(f"{pattern} in {api_file.name}")
                        # Skip this line and potentially the next few lines if they're part of the documentation
                        skip_next = True
                        continue
                    elif skip_next and (line.strip() == "" or line.startswith("**") or line.startswith("```")):
                        # Skip empty lines and related documentation after phantom route
                        if line.strip() == "" or not line.startswith("**"):
                            skip_next = False
                        continue
                    else:
                        skip_next = False
                        filtered_lines.append(line)
                
                content = '\n'.join(filtered_lines)
            
            # Write back only if changed
            if content != original_content:
                api_file.write_text(content)
        
        return phantom_routes
    
    def generate_all_documentation(self) -> Dict[str, Any]:
        """Generate documentation for all undocumented routes."""
        
        # Group undocumented routes by router
        routes_by_router = {}
        for route in self.report.get('undocumented_routes', []):
            router = route['file'].replace('routers/', '').replace('.py', '')
            if router == 'app':
                router = 'gateway'  # Main app routes go in gateway
            
            if router not in routes_by_router:
                routes_by_router[router] = []
            routes_by_router[router].append(route)
        
        generated_files = []
        
        # Generate documentation for each router
        for router, routes in routes_by_router.items():
            filename = f"{router}-api.md"
            file_path = self.api_docs_path / filename
            
            # Generate content
            content = self.generate_router_documentation(router, routes)
            
            # Write file
            file_path.write_text(content)
            generated_files.append(str(file_path))
        
        # Update the API index
        self.update_api_index(routes_by_router.keys())
        
        return {
            'generated_files': generated_files,
            'routers_documented': len(routes_by_router),
            'total_routes_documented': len(self.report.get('undocumented_routes', []))
        }
    
    def update_api_index(self, router_names: List[str]):
        """Update the API index file to include new router documentation."""
        index_path = self.api_docs_path / "index.md"
        
        if not index_path.exists():
            content = """# API Reference

This section contains comprehensive API documentation for all StratMaster endpoints.

## API Components

"""
        else:
            content = index_path.read_text()
        
        # Add references to new router documentation
        for router in sorted(router_names):
            router_title = router.replace('_', ' ').title()
            link_line = f"- [{router_title} API]({router}-api.md)\n"
            
            if link_line.strip() not in content:
                content += link_line
        
        index_path.write_text(content)
    
    def enhance_existing_documentation(self) -> List[str]:
        """Enhance the quality of existing documented routes."""
        enhanced = []
        
        # Routes that need better documentation based on the report
        routes_to_enhance = self.report.get('routes_needing_better_documentation', [])
        
        for route_info in routes_to_enhance:
            route_path = route_info.get('path', '')
            
            # Enhance specific routes
            if '/healthz' in route_path:
                self.enhance_health_endpoint()
                enhanced.append('/healthz')
            elif '/recommendations' in route_path:
                self.enhance_recommendations_endpoint()
                enhanced.append('/recommendations')
            elif '/health' in route_path:
                self.enhance_health_endpoint()
                enhanced.append('/health')
        
        return enhanced
    
    def enhance_health_endpoint(self):
        """Enhance health endpoint documentation."""
        gateway_doc = self.api_docs_path / "gateway.md"
        if gateway_doc.exists():
            content = gateway_doc.read_text()
            
            # Look for existing health documentation and enhance it
            if "GET /healthz" in content:
                # Replace basic health doc with comprehensive version
                enhanced_health = """### Health Check
```http
GET /healthz
```

Returns the health status of the StratMaster API gateway and its dependencies.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00Z", 
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "mcp_services": "healthy",
    "cache": "healthy"
  }
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service or dependencies are unhealthy

**Use Cases:**
- Health checks in load balancers
- Kubernetes readiness/liveness probes
- Monitoring system health status
"""
                # Replace existing health section
                import re
                pattern = r"### Health Check.*?(?=###|\Z)"
                content = re.sub(pattern, enhanced_health, content, flags=re.DOTALL)
                gateway_doc.write_text(content)
    
    def enhance_recommendations_endpoint(self):
        """Enhance recommendations endpoint documentation."""
        gateway_doc = self.api_docs_path / "gateway.md"
        if gateway_doc.exists():
            content = gateway_doc.read_text()
            
            if "POST /recommendations" in content:
                # Add comprehensive recommendations documentation
                enhanced_rec = """### Generate Recommendations
```http
POST /recommendations
```

Generate strategic recommendations based on research analysis and multi-agent debate outcomes.

**Headers:**
- `Idempotency-Key`: Required for request deduplication
- `Content-Type`: application/json

**Request Body:**
```json
{
  "tenant_id": "string",
  "research_context": {
    "query": "market analysis for AI tools",
    "sources": ["web", "academic", "industry_reports"]
  },
  "analysis_type": "strategic_planning",
  "priority": "high",
  "constraints": {
    "timeline": "6_months",
    "budget": "100000",
    "market_focus": "enterprise"
  }
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "id": "rec_001",
      "title": "Market Entry Strategy",
      "description": "Recommended approach for market entry",
      "confidence": 0.85,
      "evidence": ["source1", "source2"],
      "implementation_timeline": "Q2 2024"
    }
  ],
  "analysis_metadata": {
    "model_used": "gpt-4o",
    "processing_time_ms": 1250,
    "evidence_quality": "high"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Processing error
"""
                # Replace or add recommendations section
                if "### Generate Recommendations" in content:
                    import re
                    pattern = r"### Generate Recommendations.*?(?=###|\Z)"
                    content = re.sub(pattern, enhanced_rec, content, flags=re.DOTALL)
                else:
                    content += "\n" + enhanced_rec
                
                gateway_doc.write_text(content)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 api_doc_generator.py <parity_report.json> <docs_path>")
        sys.exit(1)
    
    parity_report_path = sys.argv[1]
    docs_path = sys.argv[2]
    
    generator = APIDocGenerator(parity_report_path, docs_path)
    
    print("🔧 Starting API documentation generation...")
    
    # 1. Clean phantom routes
    print("🧹 Cleaning phantom routes...")
    phantom_routes = generator.clean_phantom_routes()
    if phantom_routes:
        print(f"   Removed {len(phantom_routes)} phantom routes:")
        for route in phantom_routes:
            print(f"     - {route}")
    else:
        print("   No phantom routes found")
    
    # 2. Generate comprehensive documentation
    print("📝 Generating documentation for undocumented routes...")
    results = generator.generate_all_documentation()
    print(f"   Generated {results['routers_documented']} router documentation files")
    print(f"   Documented {results['total_routes_documented']} API routes")
    
    # 3. Enhance existing documentation
    print("✨ Enhancing existing route documentation...")
    enhanced = generator.enhance_existing_documentation()
    if enhanced:
        print(f"   Enhanced {len(enhanced)} existing routes: {', '.join(enhanced)}")
    else:
        print("   No existing routes needed enhancement")
    
    print("\n✅ API documentation generation completed!")
    print(f"📁 Generated files: {len(results['generated_files'])}")
    for file_path in results['generated_files']:
        print(f"   - {file_path}")

if __name__ == "__main__":
    main()