#!/usr/bin/env python3
"""
Script to generate OpenAPI specification from the StratMaster FastAPI app.
This script can be run standalone to extract the OpenAPI schema.
"""
import json
import sys
from pathlib import Path

# Add the API package to Python path
api_src = Path(__file__).resolve().parent.parent / "packages" / "api" / "src"
sys.path.insert(0, str(api_src))

try:
    from stratmaster_api.app import create_app
    
    # Create the FastAPI app instance
    app = create_app()
    
    # Extract the OpenAPI schema
    openapi_schema = app.openapi()
    
    # Write to the docs.new/reference/api directory
    output_path = Path(__file__).parent / "docs.new" / "reference" / "api" / "openapi.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write as JSON first (YAML conversion would require PyYAML)
    json_output_path = output_path.with_suffix('.json')
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"OpenAPI schema generated successfully: {json_output_path}")
    print(f"Endpoints found: {len(openapi_schema.get('paths', {}))}")
    print(f"Components found: {len(openapi_schema.get('components', {}).get('schemas', {}))}")
    
except ImportError as e:
    print(f"Error importing StratMaster API: {e}")
    print("Make sure the development environment is set up with 'make bootstrap'")
    sys.exit(1)
except Exception as e:
    print(f"Error generating OpenAPI schema: {e}")
    sys.exit(1)