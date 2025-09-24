#!/usr/bin/env python3
"""
StratMaster Dependency Registration System

Scans all packages and services to register their dependencies for:
- Consistent version management across the monorepo
- Automated dependency tracking and upgrades
- Pre-flight dependency validation before development
- Integration with asset pull and upgrade systems

Usage:
    python scripts/register_dependencies.py scan
    python scripts/register_dependencies.py register
    python scripts/register_dependencies.py validate
"""

import argparse
import json
import sys
import toml
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Set, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)


@dataclass
class DependencyInfo:
    """Information about a package dependency."""
    name: str
    version_spec: str
    source_package: str
    source_file: str
    dependency_type: str  # "runtime", "dev", "optional"
    python_version: Optional[str] = None


@dataclass 
class PackageInfo:
    """Information about a package in the monorepo."""
    name: str
    path: str
    python_version: str
    dependencies: List[DependencyInfo]
    has_pyproject: bool = False
    has_requirements: bool = False


class DependencyRegistry:
    """Manages dependency registration across the monorepo."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.registry_file = self.project_root / ".dependency_registry.json"
        self.packages: List[PackageInfo] = []
        
    def scan_packages(self) -> List[PackageInfo]:
        """Scan all packages in the monorepo for dependencies."""
        print("📦 Scanning packages for dependencies...")
        
        packages = []
        packages_dir = self.project_root / "packages"
        
        if not packages_dir.exists():
            print(f"Warning: {packages_dir} not found")
            return packages
            
        # Scan packages directory
        for package_path in packages_dir.iterdir():
            if package_path.is_dir():
                package_info = self._scan_package(package_path)
                if package_info:
                    packages.append(package_info)
                    
        # Scan mcp-servers subdirectory
        mcp_servers_dir = packages_dir / "mcp-servers"
        if mcp_servers_dir.exists():
            for mcp_package in mcp_servers_dir.iterdir():
                if mcp_package.is_dir():
                    package_info = self._scan_package(mcp_package)
                    if package_info:
                        packages.append(package_info)
                        
        # Scan root-level dependencies
        root_package = self._scan_package(self.project_root, is_root=True)
        if root_package:
            packages.append(root_package)
            
        self.packages = packages
        print(f"✅ Found {len(packages)} packages with dependencies")
        return packages
        
    def _scan_package(self, package_path: Path, is_root: bool = False) -> Optional[PackageInfo]:
        """Scan a single package for its dependencies."""
        pyproject_path = package_path / "pyproject.toml"
        requirements_path = package_path / "requirements.txt"
        requirements_dev_path = package_path / "requirements-dev.txt"
        
        dependencies = []
        python_version = ">=3.11"  # default
        package_name = package_path.name if not is_root else "stratmaster-root"
        
        has_pyproject = pyproject_path.exists()
        has_requirements = requirements_path.exists() or requirements_dev_path.exists()
        
        # Parse pyproject.toml
        if pyproject_path.exists():
            try:
                pyproject_data = toml.load(pyproject_path)
                project = pyproject_data.get("project", {})
                
                # Get package name and Python version
                if "name" in project:
                    package_name = project["name"]
                if "requires-python" in project:
                    python_version = project["requires-python"]
                    
                # Parse runtime dependencies
                if "dependencies" in project:
                    for dep in project["dependencies"]:
                        dep_info = self._parse_dependency(dep, package_name, str(pyproject_path), "runtime")
                        if dep_info:
                            dependencies.append(dep_info)
                            
                # Parse optional dependencies
                optional_deps = project.get("optional-dependencies", {})
                for group, deps in optional_deps.items():
                    for dep in deps:
                        dep_info = self._parse_dependency(dep, package_name, str(pyproject_path), "optional")
                        if dep_info:
                            dependencies.append(dep_info)
                            
            except Exception as e:
                print(f"Warning: Failed to parse {pyproject_path}: {e}")
                
        # Parse requirements.txt
        if requirements_path.exists():
            dependencies.extend(self._parse_requirements_file(
                requirements_path, package_name, "runtime"
            ))
            
        # Parse requirements-dev.txt  
        if requirements_dev_path.exists():
            dependencies.extend(self._parse_requirements_file(
                requirements_dev_path, package_name, "dev"
            ))
            
        if dependencies or has_pyproject or has_requirements:
            return PackageInfo(
                name=package_name,
                path=str(package_path.relative_to(self.project_root)),
                python_version=python_version,
                dependencies=dependencies,
                has_pyproject=has_pyproject,
                has_requirements=has_requirements
            )
            
        return None
        
    def _parse_dependency(self, dep_line: str, package_name: str, source_file: str, dep_type: str) -> Optional[DependencyInfo]:
        """Parse a single dependency specification."""
        dep_line = dep_line.strip()
        if not dep_line or dep_line.startswith("#"):
            return None
            
        # Handle requirements.txt style vs pyproject.toml style
        if "==" in dep_line:
            name, version = dep_line.split("==", 1)
            version_spec = f"=={version}"
        elif ">=" in dep_line:
            name, version = dep_line.split(">=", 1)
            version_spec = f">={version}"
        elif "~=" in dep_line:
            name, version = dep_line.split("~=", 1)  
            version_spec = f"~={version}"
        elif ">" in dep_line and "<" in dep_line:
            # Handle range specifications
            version_spec = dep_line.split(" ", 1)[1] if " " in dep_line else ""
            name = dep_line.split(">")[0].split("<")[0]
        else:
            # Simple package name
            name = dep_line.split()[0] if " " in dep_line else dep_line
            version_spec = ""
            
        # Clean up name (remove extras)
        if "[" in name:
            name = name.split("[")[0]
            
        return DependencyInfo(
            name=name.strip(),
            version_spec=version_spec.strip(),
            source_package=package_name,
            source_file=source_file,
            dependency_type=dep_type
        )
        
    def _parse_requirements_file(self, req_file: Path, package_name: str, dep_type: str) -> List[DependencyInfo]:
        """Parse a requirements.txt file."""
        dependencies = []
        
        try:
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("-r "):
                        # Handle -r includes
                        included_file = self.project_root / line[3:]
                        if included_file.exists():
                            dependencies.extend(
                                self._parse_requirements_file(included_file, package_name, dep_type)
                            )
                    else:
                        dep_info = self._parse_dependency(line, package_name, str(req_file), dep_type)
                        if dep_info:
                            dependencies.append(dep_info)
                            
        except Exception as e:
            print(f"Warning: Failed to parse {req_file}: {e}")
            
        return dependencies
        
    def register_dependencies(self) -> None:
        """Register all discovered dependencies to the registry file."""
        print("📝 Registering dependencies...")
        
        if not self.packages:
            self.scan_packages()
            
        # Create dependency registry data
        registry_data = {
            "generated_at": datetime.now(UTC).isoformat(),
            "project_root": str(self.project_root),
            "total_packages": len(self.packages),
            "packages": []
        }
        
        # Add package info
        for package in self.packages:
            package_data = asdict(package)
            registry_data["packages"].append(package_data)
            
        # Analyze dependency conflicts
        conflicts = self._analyze_conflicts()
        registry_data["conflicts"] = conflicts
        
        # Save to file
        with open(self.registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)
            
        print(f"✅ Registered {sum(len(pkg.dependencies) for pkg in self.packages)} dependencies")
        print(f"📄 Registry saved to: {self.registry_file}")
        
        if conflicts:
            print(f"⚠️  Found {len(conflicts)} dependency conflicts - run validate for details")
            
    def _analyze_conflicts(self) -> List[Dict]:
        """Analyze dependency conflicts across packages."""
        conflicts = []
        dep_versions = defaultdict(set)
        
        # Collect all version specs per dependency
        for package in self.packages:
            for dep in package.dependencies:
                if dep.version_spec:
                    dep_versions[dep.name].add((dep.version_spec, dep.source_package))
                    
        # Find conflicts
        for dep_name, versions in dep_versions.items():
            if len(versions) > 1:
                version_specs = [v[0] for v in versions]
                source_packages = [v[1] for v in versions]
                
                # Check if specs are actually conflicting
                if self._has_version_conflict(version_specs):
                    conflicts.append({
                        "dependency": dep_name,
                        "conflicting_specs": version_specs,
                        "source_packages": source_packages
                    })
                    
        return conflicts
        
    def _has_version_conflict(self, specs: List[str]) -> bool:
        """Check if version specifications conflict."""
        # Simple conflict detection - can be enhanced
        exact_versions = [s for s in specs if s.startswith("==")]
        if len(exact_versions) > 1:
            return len(set(exact_versions)) > 1
            
        # Check for obvious range conflicts
        min_versions = [s for s in specs if s.startswith(">=")]
        max_versions = [s for s in specs if s.startswith("<")]
        
        if min_versions and max_versions:
            # More sophisticated conflict detection could be added here
            pass
            
        return False
        
    def validate_dependencies(self) -> bool:
        """Validate the dependency registry and check for issues."""
        print("🔍 Validating dependencies...")
        
        if not self.registry_file.exists():
            print("❌ Dependency registry not found. Run 'register' first.")
            return False
            
        try:
            with open(self.registry_file, 'r') as f:
                registry_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load registry: {e}")
            return False
            
        # Check for conflicts
        conflicts = registry_data.get("conflicts", [])
        if conflicts:
            print(f"⚠️  Found {len(conflicts)} dependency conflicts:")
            for conflict in conflicts:
                print(f"  • {conflict['dependency']}: {', '.join(conflict['conflicting_specs'])}")
                print(f"    Sources: {', '.join(conflict['source_packages'])}")
                
        # Check for missing dependencies
        missing_deps = self._check_missing_dependencies(registry_data)
        if missing_deps:
            print(f"⚠️  Found {len(missing_deps)} potentially missing dependencies:")
            for dep in missing_deps:
                print(f"  • {dep}")
                
        # Summary
        total_deps = sum(len(pkg["dependencies"]) for pkg in registry_data["packages"])
        print(f"\n📊 Summary:")
        print(f"  Packages: {registry_data['total_packages']}")
        print(f"  Dependencies: {total_deps}")
        print(f"  Conflicts: {len(conflicts)}")
        print(f"  Missing: {len(missing_deps)}")
        
        return len(conflicts) == 0 and len(missing_deps) == 0
        
    def _check_missing_dependencies(self, registry_data: Dict) -> List[str]:
        """Check for dependencies that might be missing from root requirements."""
        # This is a simplified check - can be enhanced
        root_deps = set()
        package_deps = set()
        
        for pkg_data in registry_data["packages"]:
            if pkg_data["name"] == "stratmaster-root":
                root_deps.update(dep["name"] for dep in pkg_data["dependencies"])
            else:
                package_deps.update(dep["name"] for dep in pkg_data["dependencies"])
                
        # Find package dependencies not in root
        missing = package_deps - root_deps
        
        # Filter out dev/build dependencies
        dev_deps = {"pytest", "mypy", "black", "flake8", "pre-commit", "pip-tools"}
        missing = missing - dev_deps
        
        return sorted(missing)


def main():
    parser = argparse.ArgumentParser(
        description="StratMaster Dependency Registration System",
        epilog="""
Examples:
  python scripts/register_dependencies.py scan      # Scan and display packages
  python scripts/register_dependencies.py register  # Register to file
  python scripts/register_dependencies.py validate  # Validate registry
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['scan', 'register', 'validate'],
                       help='Action to perform')
    parser.add_argument('--output', help='Output file for scan results')
    
    args = parser.parse_args()
    
    try:
        registry = DependencyRegistry()
        
        if args.command == 'scan':
            packages = registry.scan_packages()
            
            if args.output:
                output_data = [asdict(pkg) for pkg in packages]
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"📄 Scan results saved to: {args.output}")
            else:
                # Display summary
                for pkg in packages:
                    print(f"\n📦 {pkg.name} ({pkg.path})")
                    print(f"   Python: {pkg.python_version}")
                    print(f"   Dependencies: {len(pkg.dependencies)}")
                    if pkg.dependencies:
                        for dep in pkg.dependencies[:5]:  # Show first 5
                            print(f"     • {dep.name} {dep.version_spec}")
                        if len(pkg.dependencies) > 5:
                            print(f"     ... and {len(pkg.dependencies) - 5} more")
                            
        elif args.command == 'register':
            registry.register_dependencies()
            
        elif args.command == 'validate':
            is_valid = registry.validate_dependencies()
            if not is_valid:
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()