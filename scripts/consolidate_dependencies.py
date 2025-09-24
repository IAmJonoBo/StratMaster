#!/usr/bin/env python3
"""
StratMaster Dependency Consolidation System

Automatically consolidates package dependencies into root requirements files
based on the dependency registry. This ensures all dependencies are available
for development and deployment.

Usage:
    python scripts/consolidate_dependencies.py consolidate
    python scripts/consolidate_dependencies.py consolidate --dev-only
    python scripts/consolidate_dependencies.py preview
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


class DependencyConsolidator:
    """Consolidates package dependencies into root requirements."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.registry_file = self.project_root / ".dependency_registry.json"
        self.requirements_file = self.project_root / "requirements.txt"
        self.requirements_dev_file = self.project_root / "requirements-dev.txt"
        
    def consolidate_dependencies(self, dev_only: bool = False, dry_run: bool = False) -> bool:
        """Consolidate dependencies from registry into requirements files."""
        if not self.registry_file.exists():
            print("❌ Dependency registry not found. Run 'make deps.register' first.")
            return False
            
        try:
            with open(self.registry_file, 'r') as f:
                registry_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load registry: {e}")
            return False
            
        # Analyze dependencies
        runtime_deps, dev_deps = self._analyze_dependencies(registry_data)
        
        # Show preview
        self._show_consolidation_preview(runtime_deps, dev_deps)
        
        if dry_run:
            return True
            
        # Update requirements files
        if not dev_only:
            success = self._update_requirements_file(runtime_deps, self.requirements_file)
            if not success:
                return False
                
        success = self._update_requirements_file(dev_deps, self.requirements_dev_file, is_dev=True)
        return success
        
    def _analyze_dependencies(self, registry_data: Dict) -> tuple[Dict[str, str], Dict[str, str]]:
        """Analyze dependencies from registry and categorize them."""
        runtime_deps = {}
        dev_deps = {}
        
        # Current root dependencies
        current_runtime = self._load_current_requirements(self.requirements_file)
        current_dev = self._load_current_requirements(self.requirements_dev_file)
        
        # Collect all dependencies with version resolution
        for package_data in registry_data["packages"]:
            if package_data["name"] == "stratmaster-root":
                continue  # Skip root package to avoid circular deps
                
            for dep in package_data["dependencies"]:
                dep_name = dep["name"]
                version_spec = dep["version_spec"] 
                dep_type = dep["dependency_type"]
                
                # Categorize dependency
                if dep_type == "dev" or self._is_dev_dependency(dep_name):
                    target_deps = dev_deps
                else:
                    target_deps = runtime_deps
                    
                # Version resolution - choose most restrictive that's compatible
                if dep_name in target_deps:
                    target_deps[dep_name] = self._resolve_version_conflict(
                        target_deps[dep_name], version_spec
                    )
                else:
                    target_deps[dep_name] = version_spec
                    
        # Merge with current requirements to preserve manual additions
        runtime_deps.update(current_runtime)
        dev_deps.update(current_dev)
        
        return runtime_deps, dev_deps
        
    def _load_current_requirements(self, req_file: Path) -> Dict[str, str]:
        """Load current requirements from file."""
        current_deps = {}
        
        if not req_file.exists():
            return current_deps
            
        try:
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-r"):
                        if "==" in line:
                            name, version = line.split("==", 1)
                            current_deps[name] = f"=={version}"
                        elif "~=" in line:
                            name, version = line.split("~=", 1)
                            current_deps[name] = f"~={version}"
                        elif ">=" in line:
                            name, version = line.split(">=", 1)
                            current_deps[name] = f">={version}"
                        else:
                            current_deps[line] = ""
        except Exception as e:
            print(f"Warning: Failed to parse {req_file}: {e}")
            
        return current_deps
        
    def _is_dev_dependency(self, dep_name: str) -> bool:
        """Check if a dependency should be categorized as dev."""
        dev_patterns = {
            "pytest", "mypy", "black", "flake8", "ruff", "pre-commit", 
            "pytest-", "types-", "isort", "bandit", "coverage",
            "pip-tools", "build", "twine", "wheel"
        }
        
        return any(pattern in dep_name.lower() for pattern in dev_patterns)
        
    def _resolve_version_conflict(self, existing: str, new: str) -> str:
        """Resolve version conflicts by choosing most restrictive compatible spec."""
        if not existing or not new:
            return existing or new
            
        # Simple resolution - prefer exact versions, then ~=, then >=
        if existing.startswith("=="):
            return existing
        elif new.startswith("=="):
            return new
        elif existing.startswith("~="):
            return existing
        elif new.startswith("~="):
            return new
        else:
            # For >= specs, choose the higher minimum version
            if existing.startswith(">=") and new.startswith(">="):
                try:
                    existing_ver = existing[2:]
                    new_ver = new[2:] 
                    # Simple version comparison - can be enhanced
                    if self._compare_versions(new_ver, existing_ver) > 0:
                        return new
                except:
                    pass
            return existing
            
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Simple version comparison. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal."""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            # Pad to same length
            max_len = max(len(parts1), len(parts2))
            parts1.extend([0] * (max_len - len(parts1)))
            parts2.extend([0] * (max_len - len(parts2)))
            
            for p1, p2 in zip(parts1, parts2):
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            return 0
        except:
            return 0  # If parsing fails, assume equal
            
    def _show_consolidation_preview(self, runtime_deps: Dict[str, str], dev_deps: Dict[str, str]):
        """Show preview of what will be consolidated."""
        print("📋 Dependency Consolidation Preview")
        print("=" * 40)
        
        print(f"\n📦 Runtime Dependencies ({len(runtime_deps)}):")
        for name, version in sorted(runtime_deps.items()):
            print(f"  • {name}{version}")
            
        print(f"\n🛠️  Development Dependencies ({len(dev_deps)}):")
        for name, version in sorted(dev_deps.items()):
            print(f"  • {name}{version}")
            
    def _update_requirements_file(self, dependencies: Dict[str, str], req_file: Path, is_dev: bool = False) -> bool:
        """Update a requirements file with consolidated dependencies."""
        try:
            lines = []
            
            # Add header comment
            if is_dev:
                lines.append("# StratMaster Development Dependencies")
                lines.append("# Generated by dependency consolidation system")
                lines.append("# Include runtime dependencies")
                lines.append("-r requirements.txt")
                lines.append("")
            else:
                lines.append("# StratMaster Runtime Dependencies")  
                lines.append("# Generated by dependency consolidation system")
                lines.append("")
                
            # Add dependencies sorted alphabetically
            for name, version in sorted(dependencies.items()):
                if version:
                    lines.append(f"{name}{version}")
                else:
                    lines.append(name)
                    
            # Write file
            with open(req_file, 'w') as f:
                f.write('\n'.join(lines) + '\n')
                
            print(f"✅ Updated {req_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update {req_file}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="StratMaster Dependency Consolidation System",
        epilog="""
Examples:
  python scripts/consolidate_dependencies.py consolidate        # Update both files
  python scripts/consolidate_dependencies.py consolidate --dev-only  # Dev only  
  python scripts/consolidate_dependencies.py preview           # Preview changes
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['consolidate', 'preview'],
                       help='Action to perform')
    parser.add_argument('--dev-only', action='store_true',
                       help='Update only development dependencies')
    
    args = parser.parse_args()
    
    try:
        consolidator = DependencyConsolidator()
        
        if args.command == 'consolidate':
            success = consolidator.consolidate_dependencies(
                dev_only=args.dev_only,
                dry_run=False
            )
            if not success:
                sys.exit(1)
        elif args.command == 'preview':
            consolidator.consolidate_dependencies(dry_run=True)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()