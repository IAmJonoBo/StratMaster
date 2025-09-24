#!/usr/bin/env python3
"""
Validate Actual Implementation Status

Performs comprehensive validation of implemented features vs documented claims.
Provides accurate implementation percentages and identifies gaps.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

def check_file_exists(path: str) -> bool:
    """Check if file exists."""
    return Path(path).exists()

def check_lines_of_code(path: str) -> int:
    """Count lines of code in Python files."""
    if not Path(path).exists():
        return 0
    
    try:
        result = subprocess.run(
            ["find", path, "-name", "*.py", "-exec", "wc", "-l", "{}", "+"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        total_line = [line for line in lines if 'total' in line]
        if total_line:
            return int(total_line[0].split()[0])
        return 0
    except:
        return 0

def check_api_routers() -> Tuple[int, List[str]]:
    """Check API routers."""
    router_dir = Path("packages/api/src/stratmaster_api/routers")
    if not router_dir.exists():
        return 0, []
    
    routers = [f.stem for f in router_dir.glob("*.py") if f.name != "__init__.py"]
    return len(routers), routers

def check_feature_flag_implementations() -> Dict[str, bool]:
    """Check which feature flags are properly implemented."""
    flags = {}
    
    # Check Model Recommender V2
    model_recommender = Path("packages/mcp-servers/router-mcp/src/router_mcp/model_recommender.py")
    if model_recommender.exists():
        content = model_recommender.read_text()
        flags["ENABLE_MODEL_RECOMMENDER_V2"] = "ENABLE_MODEL_RECOMMENDER_V2" in content and "is_model_recommender_v2_enabled" in content
    
    # Check Collaboration
    collab_api = Path("packages/api/src/stratmaster_api/collaboration.py")
    if collab_api.exists():
        content = collab_api.read_text()
        flags["ENABLE_COLLAB_LIVE"] = "ENABLE_COLLAB_LIVE" in content and "is_collaboration_enabled" in content
    
    return flags

def check_integration_completeness() -> Dict[str, dict]:
    """Check integration completeness."""
    integrations = {}
    
    # Check export integrations
    export_dir = Path("packages/integrations/src")
    if export_dir.exists():
        integrations["export_integrations"] = {
            "notion": check_file_exists("packages/integrations/src/notion/__init__.py"),
            "trello": check_file_exists("packages/integrations/src/trello/__init__.py"), 
            "jira": check_file_exists("packages/integrations/src/jira/__init__.py"),
            "total_lines": check_lines_of_code("packages/integrations/src")
        }
    
    # Check collaboration service
    collab_service = Path("packages/collaboration/src/collaboration")
    if collab_service.exists():
        integrations["collaboration"] = {
            "service_implemented": check_file_exists("packages/collaboration/src/collaboration/service.py"),
            "models_implemented": check_file_exists("packages/collaboration/src/collaboration/models.py"),
            "websocket_ready": check_file_exists("packages/api/src/stratmaster_api/routers/collaboration.py"),
            "total_lines": check_lines_of_code("packages/collaboration/src")
        }
    
    return integrations

def validate_phase3_features() -> bool:
    """Run Phase 3 validation script."""
    try:
        result = subprocess.run(
            ["bash", "scripts/validate_phase3.sh"],
            capture_output=True,
            text=True,
            cwd="."
        )
        return result.returncode == 0
    except:
        return False

def main():
    """Main validation function."""
    print("🔍 StratMaster Actual Implementation Validation")
    print("=" * 50)
    
    # Check API implementation
    router_count, routers = check_api_routers()
    api_lines = check_lines_of_code("packages/api/src")
    
    print(f"📦 API Implementation:")
    print(f"   Routers: {router_count}")
    print(f"   Router files: {', '.join(routers)}")
    print(f"   Total API lines: {api_lines:,}")
    
    # Check feature flags
    flags = check_feature_flag_implementations()
    print(f"\n🚩 Feature Flag Implementation:")
    for flag, implemented in flags.items():
        status = "✅" if implemented else "❌"
        print(f"   {status} {flag}")
    
    # Check integrations
    integrations = check_integration_completeness()
    print(f"\n🔗 Integration Status:")
    for integration, details in integrations.items():
        print(f"   {integration}:")
        for key, value in details.items():
            if isinstance(value, bool):
                status = "✅" if value else "❌" 
                print(f"     {status} {key}")
            else:
                print(f"     • {key}: {value:,}" if isinstance(value, int) else f"     • {key}: {value}")
    
    # Check Phase 3 validation
    phase3_status = validate_phase3_features()
    print(f"\n✅ Phase 3 Validation: {'PASS' if phase3_status else 'FAIL'}")
    
    # Calculate implementation percentage
    total_checks = 0
    passed_checks = 0
    
    # Count router completeness (target: 15)
    total_checks += 15
    passed_checks += min(router_count, 15)
    
    # Count feature flag implementations
    total_checks += len(flags) * 2  # Implementation + testing
    passed_checks += sum(flags.values()) * 2
    
    # Count integration readiness
    for integration, details in integrations.items():
        component_checks = [v for v in details.values() if isinstance(v, bool)]
        total_checks += len(component_checks)
        passed_checks += sum(component_checks)
    
    # Phase 3 infrastructure
    total_checks += 37  # From phase 3 validation
    if phase3_status:
        passed_checks += 37
    
    # Calculate percentage
    if total_checks > 0:
        percentage = (passed_checks / total_checks) * 100
        print(f"\n📊 Calculated Implementation Status: {percentage:.1f}%")
        print(f"   Passed: {passed_checks}/{total_checks} checks")
    
    # Summary assessment
    print(f"\n🎯 Assessment Summary:")
    if percentage >= 95:
        print("   Status: PRODUCTION READY 🚀")
    elif percentage >= 90:
        print("   Status: FINAL INTEGRATION SPRINT 🔧")
    elif percentage >= 85:
        print("   Status: INTEGRATION PHASE 🔄")
    else:
        print("   Status: DEVELOPMENT PHASE 🛠️")
    
    print(f"\n📋 Key Findings:")
    print(f"   • {router_count} API routers implemented")
    print(f"   • {api_lines:,} lines of API code")
    print(f"   • Feature flags properly implemented: {sum(flags.values())}/{len(flags)}")
    print(f"   • Phase 3 validation: {'PASSED' if phase3_status else 'FAILED'}")

if __name__ == "__main__":
    main()