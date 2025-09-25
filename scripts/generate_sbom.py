#!/usr/bin/env python3
"""
SBOM (Software Bill of Materials) Generator
Implements SLSA provenance and SBOM generation as identified in GAP_ANALYSIS.md
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib
import urllib.request
import argparse


class SBOMGenerator:
    """Generate CycloneDX SBOM with SLSA provenance for StratMaster."""
    
    def __init__(self, output_format: str = "json"):
        self.output_format = output_format
        self.repo_root = Path.cwd()
        self.sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:stratmaster-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tools": [
                    {
                        "vendor": "StratMaster",
                        "name": "SBOM Generator",
                        "version": "1.0.0"
                    }
                ],
                "component": {
                    "type": "application",
                    "bom-ref": "stratmaster-app",
                    "name": "StratMaster",
                    "version": self._get_app_version(),
                    "description": "AI-powered strategic planning and analysis platform",
                    "licenses": [{"license": {"id": "MIT"}}]
                }
            },
            "components": [],
            "services": [],
            "vulnerabilities": [],
            "compositions": []
        }
        
    def _get_app_version(self) -> str:
        """Get application version from git or package metadata."""
        try:
            # Try git describe first
            result = subprocess.run(
                ["git", "describe", "--tags", "--always", "--dirty"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        
        # Fallback to package version
        try:
            pyproject_path = self.repo_root / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path) as f:
                    content = f.read()
                    # Simple version extraction (would use proper TOML parser in production)
                    for line in content.split('\n'):
                        if line.strip().startswith('version ='):
                            return line.split('=')[1].strip().strip('"\'')
        except Exception:
            pass
        
        return "dev-snapshot"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
    
    def scan_python_dependencies(self) -> List[Dict[str, Any]]:
        """Scan Python dependencies from requirements files and installed packages."""
        components = []
        
        # Scan requirements files
        req_files = [
            "requirements.txt",
            "requirements-dev.txt", 
            "pyproject.toml"
        ]
        
        for req_file in req_files:
            req_path = self.repo_root / req_file
            if req_path.exists():
                components.extend(self._parse_requirements_file(req_path))
        
        # Try to get installed packages via pip list
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                installed_packages = json.loads(result.stdout)
                for package in installed_packages:
                    components.append({
                        "type": "library",
                        "bom-ref": f"python-{package['name']}-{package['version']}",
                        "name": package["name"],
                        "version": package["version"],
                        "scope": "required",
                        "purl": f"pkg:pypi/{package['name']}@{package['version']}",
                        "properties": [
                            {"name": "source", "value": "pip-installed"}
                        ]
                    })
        except Exception as e:
            print(f"Warning: Could not scan installed packages: {e}")
        
        return components
    
    def _parse_requirements_file(self, req_path: Path) -> List[Dict[str, Any]]:
        """Parse a requirements file for dependencies."""
        components = []
        
        try:
            with open(req_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse requirement line (simplified - real parser would handle more formats)
                        if '==' in line:
                            name, version = line.split('==')
                            name = name.strip()
                            version = version.split('#')[0].strip()  # Remove comments
                            
                            components.append({
                                "type": "library",
                                "bom-ref": f"python-{name}-{version}",
                                "name": name,
                                "version": version,
                                "scope": "required",
                                "purl": f"pkg:pypi/{name}@{version}",
                                "properties": [
                                    {"name": "source", "value": str(req_path.name)}
                                ]
                            })
                        elif '>=' in line:
                            name = line.split('>=')[0].strip()
                            min_version = line.split('>=')[1].split('#')[0].strip()
                            
                            components.append({
                                "type": "library",
                                "bom-ref": f"python-{name}-{min_version}+",
                                "name": name,
                                "version": f">={min_version}",
                                "scope": "required", 
                                "purl": f"pkg:pypi/{name}",
                                "properties": [
                                    {"name": "source", "value": str(req_path.name)},
                                    {"name": "constraint", "value": f">={min_version}"}
                                ]
                            })
                        
        except Exception as e:
            print(f"Warning: Could not parse {req_path}: {e}")
        
        return components
    
    def scan_javascript_dependencies(self) -> List[Dict[str, Any]]:
        """Scan JavaScript dependencies from package.json files."""
        components = []
        
        # Find all package.json files
        for package_json in self.repo_root.rglob("package.json"):
            if "node_modules" in str(package_json):
                continue
                
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                
                # Add dependencies
                for dep_type in ["dependencies", "devDependencies"]:
                    deps = package_data.get(dep_type, {})
                    for name, version in deps.items():
                        components.append({
                            "type": "library",
                            "bom-ref": f"npm-{name}-{version}",
                            "name": name,
                            "version": version,
                            "scope": "required" if dep_type == "dependencies" else "optional",
                            "purl": f"pkg:npm/{name}@{version}",
                            "properties": [
                                {"name": "source", "value": str(package_json.relative_to(self.repo_root))},
                                {"name": "dependency_type", "value": dep_type}
                            ]
                        })
                        
            except Exception as e:
                print(f"Warning: Could not parse {package_json}: {e}")
        
        return components
    
    def scan_container_dependencies(self) -> List[Dict[str, Any]]:
        """Scan container base images and layers."""
        components = []
        
        # Find Dockerfiles
        for dockerfile in self.repo_root.rglob("Dockerfile*"):
            try:
                with open(dockerfile) as f:
                    content = f.read()
                
                # Extract FROM statements
                for line in content.split('\n'):
                    line = line.strip()
                    if line.upper().startswith('FROM '):
                        image_ref = line.split()[1]
                        
                        # Parse image reference
                        if ':' in image_ref:
                            image_name, tag = image_ref.rsplit(':', 1)
                        else:
                            image_name, tag = image_ref, "latest"
                        
                        components.append({
                            "type": "container",
                            "bom-ref": f"container-{image_name.replace('/', '-')}-{tag}",
                            "name": image_name,
                            "version": tag,
                            "scope": "required",
                            "purl": f"pkg:docker/{image_name}@{tag}",
                            "properties": [
                                {"name": "source", "value": str(dockerfile.relative_to(self.repo_root))},
                                {"name": "type", "value": "base-image"}
                            ]
                        })
                        
            except Exception as e:
                print(f"Warning: Could not parse {dockerfile}: {e}")
        
        return components
    
    def scan_system_services(self) -> List[Dict[str, Any]]:
        """Identify system services and external dependencies."""
        services = []
        
        # Common service configurations to scan
        service_configs = [
            ("docker-compose.yml", self._parse_docker_compose),
            ("helm/*/values.yaml", self._parse_helm_values),
            ("configs/**/*.yaml", self._parse_config_files)
        ]
        
        for pattern, parser in service_configs:
            for config_file in self.repo_root.rglob(pattern):
                try:
                    services.extend(parser(config_file))
                except Exception as e:
                    print(f"Warning: Could not parse {config_file}: {e}")
        
        return services
    
    def _parse_docker_compose(self, compose_file: Path) -> List[Dict[str, Any]]:
        """Parse docker-compose.yml for service dependencies."""
        services = []
        
        try:
            import yaml
            with open(compose_file) as f:
                compose_data = yaml.safe_load(f)
            
            for service_name, service_config in compose_data.get("services", {}).items():
                image = service_config.get("image", "")
                if image:
                    services.append({
                        "bom-ref": f"service-{service_name}",
                        "name": service_name,
                        "description": f"Docker service: {image}",
                        "endpoints": [f"http://{service_name}:8080"],  # Default assumption
                        "authenticated": True,
                        "x-trust-boundary": False,
                        "properties": [
                            {"name": "source", "value": str(compose_file.relative_to(self.repo_root))},
                            {"name": "image", "value": image}
                        ]
                    })
                    
        except ImportError:
            print("Warning: PyYAML not available, skipping docker-compose parsing")
        except Exception as e:
            print(f"Warning: Could not parse docker-compose: {e}")
        
        return services
    
    def _parse_helm_values(self, values_file: Path) -> List[Dict[str, Any]]:
        """Parse Helm values for service configurations."""
        # Simplified - would need full Helm template parsing in production
        return []
    
    def _parse_config_files(self, config_file: Path) -> List[Dict[str, Any]]:
        """Parse configuration files for external service references."""
        # Simplified - would scan for database URLs, API endpoints, etc.
        return []
    
    def add_vulnerability_data(self) -> None:
        """Add known vulnerability data for components."""
        # This would integrate with vulnerability databases like:
        # - GitHub Security Advisory Database
        # - NVD (National Vulnerability Database)
        # - Snyk, etc.
        
        # For now, add placeholder structure
        self.sbom_data["vulnerabilities"] = [
            {
                "id": "EXAMPLE-CVE-2024-0001",
                "description": "Example vulnerability - would be populated from real sources",
                "published": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z",
                "ratings": [
                    {
                        "source": {"name": "NVD"},
                        "score": 7.5,
                        "severity": "HIGH",
                        "method": "CVSSv3"
                    }
                ],
                "affects": [
                    {"ref": "python-example-1.0.0"}
                ]
            }
        ]
    
    def generate_slsa_provenance(self) -> Dict[str, Any]:
        """Generate SLSA provenance metadata."""
        # Get build environment information
        build_env = {
            "os": os.uname().sysname if hasattr(os, 'uname') else "unknown",
            "arch": os.uname().machine if hasattr(os, 'uname') else "unknown",
            "python_version": sys.version,
            "build_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Get git information if available
        git_info = {}
        try:
            git_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=self.repo_root
            )
            if git_commit.returncode == 0:
                git_info["commit"] = git_commit.stdout.strip()
                
            git_remote = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True, text=True, cwd=self.repo_root
            )
            if git_remote.returncode == 0:
                git_info["repository"] = git_remote.stdout.strip()
                
        except Exception:
            pass
        
        provenance = {
            "_type": "https://in-toto.io/Statement/v0.1",
            "subject": [
                {
                    "name": "stratmaster",
                    "digest": {
                        "sha256": "placeholder-would-be-actual-artifact-hash"
                    }
                }
            ],
            "predicateType": "https://slsa.dev/provenance/v0.2",
            "predicate": {
                "builder": {
                    "id": "StratMaster CI/CD Pipeline"
                },
                "buildType": "StratMaster Build",
                "invocation": {
                    "configSource": git_info,
                    "parameters": build_env
                },
                "materials": [
                    {
                        "uri": git_info.get("repository", "unknown"),
                        "digest": {
                            "sha1": git_info.get("commit", "unknown")
                        }
                    }
                ]
            }
        }
        
        return provenance
    
    def generate_sbom(self, include_vulnerabilities: bool = False) -> Dict[str, Any]:
        """Generate complete SBOM."""
        print("🔍 Scanning dependencies...")
        
        # Scan different types of dependencies
        all_components = []
        
        python_deps = self.scan_python_dependencies()
        all_components.extend(python_deps)
        print(f"  Found {len(python_deps)} Python dependencies")
        
        js_deps = self.scan_javascript_dependencies()
        all_components.extend(js_deps)
        print(f"  Found {len(js_deps)} JavaScript dependencies")
        
        container_deps = self.scan_container_dependencies()
        all_components.extend(container_deps)
        print(f"  Found {len(container_deps)} container dependencies")
        
        # Remove duplicates (simple deduplication by bom-ref)
        seen_refs = set()
        unique_components = []
        for component in all_components:
            if component["bom-ref"] not in seen_refs:
                unique_components.append(component)
                seen_refs.add(component["bom-ref"])
        
        self.sbom_data["components"] = unique_components
        
        # Scan services
        services = self.scan_system_services()
        self.sbom_data["services"] = services
        print(f"  Found {len(services)} services")
        
        # Add vulnerability data if requested
        if include_vulnerabilities:
            self.add_vulnerability_data()
        
        print(f"✅ Generated SBOM with {len(unique_components)} components")
        
        return self.sbom_data
    
    def save_sbom(self, output_path: str) -> None:
        """Save SBOM to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.sbom_data, f, indent=2)
        
        print(f"📁 SBOM saved to: {output_file}")
    
    def save_provenance(self, output_path: str) -> None:
        """Save SLSA provenance to file."""
        provenance = self.generate_slsa_provenance()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(provenance, f, indent=2)
        
        print(f"📁 SLSA provenance saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate SBOM and SLSA provenance')
    parser.add_argument('--output', '-o', default='sbom.json', help='Output SBOM file path')
    parser.add_argument('--provenance', '-p', help='Output provenance file path')
    parser.add_argument('--include-vulnerabilities', action='store_true', help='Include vulnerability data')
    parser.add_argument('--format', choices=['json', 'xml'], default='json', help='Output format')
    
    args = parser.parse_args()
    
    print("🚀 Starting SBOM Generation")
    print("=" * 50)
    
    generator = SBOMGenerator(output_format=args.format)
    
    # Generate SBOM
    sbom_data = generator.generate_sbom(include_vulnerabilities=args.include_vulnerabilities)
    generator.save_sbom(args.output)
    
    # Generate SLSA provenance if requested
    if args.provenance:
        generator.save_provenance(args.provenance)
    
    # Print summary
    print(f"\n📊 SBOM Summary:")
    print(f"  Components: {len(sbom_data.get('components', []))}")
    print(f"  Services: {len(sbom_data.get('services', []))}")
    print(f"  Vulnerabilities: {len(sbom_data.get('vulnerabilities', []))}")
    
    print(f"\n✅ SBOM generation completed successfully!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())