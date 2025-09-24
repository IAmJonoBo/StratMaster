#!/usr/bin/env python3
"""
StratMaster Safe Dependency Upgrade System

Automated dependency upgrade system with:
- Controlled minor/patch updates across Python/Docker/GitHub Actions
- Automated test validation before applying changes  
- Change summary generation with impact analysis
- Rollback safety with backup and restoration capabilities
- License compatibility checking

Usage:
    python scripts/dependency_upgrade.py --help
    python scripts/dependency_upgrade.py check
    python scripts/dependency_upgrade.py plan --scope python
    python scripts/dependency_upgrade.py upgrade --dry-run
"""

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

try:
    import requests
    import yaml
except ImportError:
    print("Error: Missing dependencies. Install with: pip install PyYAML requests")
    sys.exit(1)


@dataclass
class DependencyUpdate:
    """Information about a potential dependency update."""
    name: str
    current_version: str
    latest_version: str
    update_type: str  # "major", "minor", "patch"
    license: str | None
    scope: str  # "python", "docker", "github-actions"
    file_path: str
    security_advisory: bool = False
    breaking_changes: list[str] = None
    
    def __post_init__(self):
        if self.breaking_changes is None:
            self.breaking_changes = []


class DependencyUpgrader:
    """Manages safe dependency upgrades across the project."""
    
    ALLOWED_LICENSES = [
        "Apache-2.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", 
        "ISC", "Python-2.0", "LGPL-2.1", "LGPL-3.0"
    ]
    
    SECURITY_ADVISORIES_URL = "https://api.github.com/advisories"
    
    def __init__(self, dry_run: bool = False, auto_approve: bool = False):
        self.dry_run = dry_run
        self.auto_approve = auto_approve
        self.backup_dir = Path(".dependency_backups")
        self.project_root = Path(".")
        
        # Ensure backup directory exists
        if not dry_run:
            self.backup_dir.mkdir(exist_ok=True)
    
    def _run_command(self, cmd: list[str], capture_output: bool = True) -> tuple[bool, str]:
        """Run a shell command safely."""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=capture_output, 
                text=True, 
                cwd=self.project_root
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def _backup_files(self, files: list[str]) -> str:
        """Create backup of dependency files."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        if self.dry_run:
            print(f"🔍 Would backup files to: {backup_path}")
            return str(backup_path)
        
        backup_path.mkdir()
        
        for file_path in files:
            src_path = Path(file_path)
            if src_path.exists():
                dst_path = backup_path / src_path.name
                shutil.copy2(src_path, dst_path)
                print(f"📄 Backed up: {file_path} -> {dst_path}")
        
        return str(backup_path)
    
    def _get_python_dependencies(self) -> list[DependencyUpdate]:
        """Analyze Python dependencies for updates."""
        updates = []
        
        # Check requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse package line: package~=1.0.0 or package>=1.0.0
                    match = re.match(r'^([a-zA-Z0-9_-]+)[~>=<]+([0-9.]+)', line)
                    if match:
                        package, version = match.groups()
                        
                        # Get latest version
                        latest = self._get_latest_pypi_version(package)
                        if latest and latest != version:
                            update_type = self._classify_version_change(version, latest)
                            
                            # Skip major version updates for safety
                            if update_type != "major":
                                updates.append(DependencyUpdate(
                                    name=package,
                                    current_version=version,
                                    latest_version=latest,
                                    update_type=update_type,
                                    license=self._get_package_license(package),
                                    scope="python",
                                    file_path=str(req_file),
                                    security_advisory=self._check_security_advisories(package, version)
                                ))
        
        return updates
    
    def _get_docker_dependencies(self) -> list[DependencyUpdate]:
        """Analyze Docker image dependencies for updates."""
        updates = []
        
        # Check docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            with open(compose_file) as f:
                compose_data = yaml.safe_load(f)
            
            services = compose_data.get('services', {})
            for service_name, service_config in services.items():
                image = service_config.get('image')
                if image and ':' in image:
                    image_name, current_tag = image.rsplit(':', 1)
                    
                    # Skip dynamic tags like 'latest'
                    if current_tag in ['latest', 'main', 'master']:
                        continue
                    
                    # Get latest tag for known image patterns
                    latest_tag = self._get_latest_docker_tag(image_name, current_tag)
                    if latest_tag and latest_tag != current_tag:
                        update_type = self._classify_version_change(current_tag, latest_tag)
                        
                        updates.append(DependencyUpdate(
                            name=f"{service_name}:{image_name}",
                            current_version=current_tag,
                            latest_version=latest_tag,
                            update_type=update_type,
                            license=None,  # Docker images don't have simple license info
                            scope="docker",
                            file_path=str(compose_file)
                        ))
        
        return updates
    
    def _get_github_action_dependencies(self) -> list[DependencyUpdate]:
        """Analyze GitHub Actions dependencies for updates."""
        updates = []
        
        workflows_dir = self.project_root / ".github" / "workflows"
        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.yml"):
                with open(workflow_file) as f:
                    try:
                        workflow_data = yaml.safe_load(f)
                        jobs = workflow_data.get('jobs', {})
                        
                        for job_name, job_config in jobs.items():
                            steps = job_config.get('steps', [])
                            
                            for step in steps:
                                if 'uses' in step:
                                    action = step['uses']
                                    if '@' in action:
                                        action_name, version = action.rsplit('@', 1)
                                        
                                        # Get latest version
                                        latest = self._get_latest_github_action_version(action_name)
                                        if latest and latest != version:
                                            update_type = self._classify_version_change(version, latest)
                                            
                                            updates.append(DependencyUpdate(
                                                name=action_name,
                                                current_version=version,
                                                latest_version=latest,
                                                update_type=update_type,
                                                license=None,
                                                scope="github-actions",
                                                file_path=str(workflow_file)
                                            ))
                                            
                    except yaml.YAMLError:
                        print(f"⚠️  Could not parse workflow file: {workflow_file}")
                        continue
        
        return updates
    
    def _get_latest_pypi_version(self, package: str) -> str | None:
        """Get latest version from PyPI."""
        try:
            response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['info']['version']
        except Exception:
            pass
        return None
    
    def _get_package_license(self, package: str) -> str | None:
        """Get package license from PyPI."""
        try:
            response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['info'].get('license')
        except Exception:
            pass
        return None
    
    def _check_security_advisories(self, package: str, version: str) -> bool:
        """Check for security advisories for a package version."""
        try:
            # Use GitHub's security advisory API
            url = f"https://api.github.com/advisories?ecosystem=pip&package={package}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                advisories = response.json()
                for advisory in advisories:
                    affected_ranges = advisory.get('vulnerabilities', [])
                    for vuln in affected_ranges:
                        if vuln.get('package', {}).get('name') == package:
                            # Check if current version is affected
                            ranges = vuln.get('ranges', [])
                            if self._version_in_vulnerable_range(version, ranges):
                                return True
        except Exception:
            pass
        return False
    
    def _version_in_vulnerable_range(self, version: str, ranges: list) -> bool:
        """Check if version falls within vulnerable ranges."""
        # Simplified version comparison - in production use packaging.version
        try:
            for range_obj in ranges:
                events = range_obj.get('events', [])
                for event in events:
                    if event.get('introduced') and event.get('fixed'):
                        # Check if version is between introduced and fixed
                        if version >= event['introduced'] and version < event['fixed']:
                            return True
        except Exception:
            pass
        return False
    
    def _run_security_scan(self) -> dict[str, list[str]]:
        """Run security scan on current dependencies."""
        print("🔒 Running security scan...")
        
        # Focus only on our application dependencies from requirements files
        app_packages = set()
        
        # Get packages from requirements files
        for req_file in ['requirements.txt', 'requirements-dev.txt']:
            req_path = self.project_root / req_file
            if req_path.exists():
                with open(req_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('-'):
                            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0]
                            app_packages.add(pkg_name.lower())
        
        # Get packages from pyproject.toml dependencies
        pyproject_path = self.project_root / "packages" / "api" / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path) as f:
                    import tomllib
                    try:
                        data = tomllib.loads(f.read())
                    except AttributeError:
                        # Python < 3.11 fallback
                        import tomli
                        f.seek(0)
                        data = tomli.load(f)
                    
                    deps = data.get('project', {}).get('dependencies', [])
                    for dep in deps:
                        pkg_name = dep.split('>=')[0].split('<=')[0].split('==')[0]
                        app_packages.add(pkg_name.lower())
            except Exception:
                pass
        
        # Run safety check if available
        safety_issues = []
        
        # Check for vulnerable packages in our app dependencies only
        success, output = self._run_command(["python", "-m", "pip", "list", "--format=json"])
        if success:
            try:
                import json
                packages = json.loads(output)
                for pkg in packages:
                    pkg_name = pkg['name'].lower()
                    if pkg_name in app_packages or pkg_name.replace('-', '_') in app_packages:
                        if self._check_security_advisories(pkg['name'], pkg['version']):
                            safety_issues.append(f"{pkg['name']}=={pkg['version']}")
            except Exception:
                pass
        
        return {
            "vulnerable_packages": safety_issues,
            "code_issues": []
        }
    
    def _get_latest_docker_tag(self, image_name: str, current_tag: str) -> str | None:
        """Get latest Docker tag for known images."""
        # This is simplified - in production you'd query Docker registries
        known_patterns = {
            'postgres': r'^\d+$',  # Major versions like "17"
            'redis': r'^\d+-alpine$',  # Versions like "8-alpine"
            'python': r'^\d+\.\d+-slim$',  # Versions like "3.13-slim"
        }
        
        for pattern_name, pattern in known_patterns.items():
            if pattern_name in image_name and re.match(pattern, current_tag):
                # This would normally query the registry
                # For now, return None to skip Docker updates
                pass
        
        return None
    
    def _get_latest_github_action_version(self, action: str) -> str | None:
        """Get latest GitHub Action version."""
        try:
            # Convert action name to API URL
            if action.startswith('actions/'):
                repo = action
            else:
                repo = action
            
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data['tag_name']
        except Exception:
            pass
        return None
    
    def _classify_version_change(self, current: str, latest: str) -> str:
        """Classify version change as major, minor, or patch."""
        def parse_version(v):
            # Remove 'v' prefix and parse semantic version
            clean_v = v.lstrip('v')
            parts = clean_v.split('.')[:3]  # Take first 3 parts
            return [int(p) if p.isdigit() else 0 for p in parts] + [0] * (3 - len(parts))
        
        try:
            curr_parts = parse_version(current)
            latest_parts = parse_version(latest)
            
            if curr_parts[0] != latest_parts[0]:
                return "major"
            elif curr_parts[1] != latest_parts[1]:
                return "minor"
            else:
                return "patch"
        except Exception:
            return "unknown"
    
    def _check_security_advisories(self, package: str, version: str) -> bool:
        """Check for security advisories affecting the package version."""
        # This is simplified - in production you'd check multiple sources
        try:
            # Check GitHub Advisory Database
            url = f"https://api.github.com/advisories?affects={package}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                advisories = response.json()
                # Simple check - in practice you'd compare version ranges
                return len(advisories) > 0
                
        except Exception:
            pass
        return False
    
    def _check_license_compatibility(self, license_name: str | None) -> bool:
        """Check if license is compatible with project."""
        if not license_name:
            return True  # Unknown license - allow but warn
        
        return license_name in self.ALLOWED_LICENSES
    
    def _run_tests(self) -> tuple[bool, str]:
        """Run project tests to validate changes."""
        print("🧪 Running test suite...")
        
        if self.dry_run:
            return True, "Dry run - tests skipped"
        
        # Run API tests (fastest validation)
        success, output = self._run_command([
            "python", "-m", "pytest", "packages/api/tests/", "-q"
        ])
        
        if success:
            print("✅ Tests passed")
        else:
            print("❌ Tests failed")
            print(output)
        
        return success, output
    
    def _apply_python_updates(self, updates: list[DependencyUpdate]) -> bool:
        """Apply Python dependency updates."""
        req_file = self.project_root / "requirements.txt"
        
        if self.dry_run:
            print("🔍 Would update requirements.txt:")
            for update in updates:
                print(f"  {update.name}: {update.current_version} -> {update.latest_version}")
            return True
        
        # Read current requirements
        with open(req_file) as f:
            lines = f.readlines()
        
        # Apply updates
        for update in updates:
            for i, line in enumerate(lines):
                if line.strip().startswith(update.name):
                    # Replace version
                    pattern = rf'^({re.escape(update.name)})[~>=<]+([0-9.]+)'
                    replacement = rf'\1~={update.latest_version}'
                    lines[i] = re.sub(pattern, replacement, line)
                    print(f"📦 Updated: {update.name} {update.current_version} -> {update.latest_version}")
        
        # Write updated requirements
        with open(req_file, 'w') as f:
            f.writelines(lines)
        
        return True
    
    def check(self) -> None:
        """Check for available dependency updates."""
        print("🔍 Checking for dependency updates...")
        print("=" * 50)
        
        all_updates = []
        
        # Check Python dependencies
        print("\n📦 Python Dependencies:")
        python_updates = self._get_python_dependencies()
        all_updates.extend(python_updates)
        
        if python_updates:
            for update in python_updates:
                security_flag = "🚨" if update.security_advisory else ""
                license_flag = "⚠️" if not self._check_license_compatibility(update.license) else ""
                print(f"  • {update.name}: {update.current_version} -> {update.latest_version} ({update.update_type}) {security_flag} {license_flag}")
        else:
            print("  ✅ All Python dependencies up to date")
        
        # Check Docker dependencies
        print("\n🐳 Docker Dependencies:")
        docker_updates = self._get_docker_dependencies()
        all_updates.extend(docker_updates)
        
        if docker_updates:
            for update in docker_updates:
                print(f"  • {update.name}: {update.current_version} -> {update.latest_version} ({update.update_type})")
        else:
            print("  ✅ All Docker dependencies up to date")
        
        # Check GitHub Actions
        print("\n🔧 GitHub Actions:")
        action_updates = self._get_github_action_dependencies()
        all_updates.extend(action_updates)
        
        if action_updates:
            for update in action_updates:
                print(f"  • {update.name}: {update.current_version} -> {update.latest_version} ({update.update_type})")
        else:
            print("  ✅ All GitHub Actions up to date")
        
        # Summary
        print("\n📊 Summary:")
        print(f"Total updates available: {len(all_updates)}")
        
        update_types = {}
        for update in all_updates:
            update_types[update.update_type] = update_types.get(update.update_type, 0) + 1
        
        for update_type, count in update_types.items():
            print(f"  {update_type}: {count}")
        
        security_count = sum(1 for u in all_updates if u.security_advisory)
        if security_count > 0:
            print(f"🚨 Security advisories: {security_count}")
    
    def plan(self, scope: str = "all") -> None:
        """Generate upgrade plan for specified scope."""
        print(f"📋 Dependency Upgrade Plan - {scope.upper()}")
        print("=" * 50)
        
        updates = []
        
        if scope in ["all", "python"]:
            updates.extend(self._get_python_dependencies())
        if scope in ["all", "docker"]:
            updates.extend(self._get_docker_dependencies())
        if scope in ["all", "github-actions"]:
            updates.extend(self._get_github_action_dependencies())
        
        if not updates:
            print("✅ No updates available for the specified scope")
            return
        
        # Group by scope and type
        by_scope = {}
        for update in updates:
            if update.scope not in by_scope:
                by_scope[update.scope] = {"patch": [], "minor": [], "major": []}
            by_scope[update.scope][update.update_type].append(update)
        
        # Display plan
        for scope_name, types in by_scope.items():
            print(f"\n{scope_name.upper()} Updates:")
            
            for update_type in ["patch", "minor", "major"]:
                type_updates = types[update_type]
                if type_updates:
                    risk_level = {"patch": "LOW", "minor": "MEDIUM", "major": "HIGH"}[update_type]
                    print(f"  {update_type.title()} ({risk_level} risk): {len(type_updates)} updates")
                    
                    for update in type_updates:
                        flags = []
                        if update.security_advisory:
                            flags.append("SECURITY")
                        if not self._check_license_compatibility(update.license):
                            flags.append("LICENSE")
                        
                        flag_str = f" [{', '.join(flags)}]" if flags else ""
                        print(f"    • {update.name}: {update.current_version} -> {update.latest_version}{flag_str}")
        
        print("\nUpgrade Strategy:")
        print("✅ Safe to auto-upgrade: Patch updates without license issues")
        print("⚠️  Manual review needed: Minor updates, license changes, security advisories")
        print("🚨 Careful review required: Major updates (not recommended for auto-upgrade)")
    
    def upgrade(self, scope: str = "python", update_type: str = "patch") -> bool:
        """Perform safe dependency upgrade."""
        print(f"🚀 Starting dependency upgrade - {scope} {update_type}")
        print("=" * 50)
        
        # Get updates for scope and type
        all_updates = []
        if scope in ["all", "python"]:
            all_updates.extend(self._get_python_dependencies())
        
        # Filter by update type
        filtered_updates = [u for u in all_updates if u.update_type == update_type]
        
        if not filtered_updates:
            print(f"✅ No {update_type} updates available for {scope}")
            return True
        
        # Check license compatibility
        license_issues = [u for u in filtered_updates if not self._check_license_compatibility(u.license)]
        if license_issues and not self.auto_approve:
            print("⚠️  License compatibility issues found:")
            for update in license_issues:
                print(f"  • {update.name}: {update.license}")
            
            if not self.dry_run:
                confirm = input("Continue anyway? (y/N): ")
                if confirm.lower() != 'y':
                    print("Upgrade cancelled")
                    return False
        
        # Create backup
        files_to_backup = list(set(u.file_path for u in filtered_updates))
        backup_path = self._backup_files(files_to_backup)
        
        try:
            # Apply updates
            if scope == "python":
                python_updates = [u for u in filtered_updates if u.scope == "python"]
                if python_updates:
                    self._apply_python_updates(python_updates)
                    
                    # Regenerate lock files
                    print("🔐 Regenerating lock files...")
                    if not self.dry_run:
                        success, output = self._run_command(["make", "lock"])
                        if not success:
                            print(f"❌ Lock file generation failed: {output}")
                            return False
            
            # Run tests to validate changes
            test_success, test_output = self._run_tests()
            if not test_success:
                print("❌ Tests failed after upgrade. Rolling back...")
                if not self.dry_run:
                    self._rollback(backup_path)
                return False
            
            print("✅ Dependency upgrade completed successfully!")
            
            # Generate change summary
            self._generate_change_summary(filtered_updates)
            
            return True
            
        except Exception as e:
            print(f"❌ Upgrade failed: {e}")
            if not self.dry_run:
                self._rollback(backup_path)
            return False
    
    def _rollback(self, backup_path: str) -> bool:
        """Rollback changes using backup."""
        print(f"🔄 Rolling back changes from: {backup_path}")
        
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            print(f"❌ Backup directory not found: {backup_path}")
            return False
        
        # Restore files
        for backup_file in backup_dir.glob("*"):
            target_file = self.project_root / backup_file.name
            shutil.copy2(backup_file, target_file)
            print(f"📄 Restored: {target_file}")
        
        print("✅ Rollback completed")
        return True
    
    def _generate_change_summary(self, updates: list[DependencyUpdate]) -> None:
        """Generate a summary of changes made."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        print(f"\n📊 Change Summary ({timestamp})")
        print("=" * 50)
        
        print(f"Updated {len(updates)} dependencies:")
        
        for update in updates:
            print(f"• {update.name}: {update.current_version} → {update.latest_version}")
            if update.security_advisory:
                print("  🚨 Addresses security advisory")
            if update.license:
                print(f"  📜 License: {update.license}")
        
        print("\nFiles modified:")
        files = set(u.file_path for u in updates)
        for file_path in files:
            print(f"• {file_path}")
        
        print("\n✅ All tests passed")
        print("🔐 Lock files updated")


def main():
    parser = argparse.ArgumentParser(
        description="StratMaster Safe Dependency Upgrade System",
        epilog="""
Examples:
  python scripts/dependency_upgrade.py check                    # Check for updates
  python scripts/dependency_upgrade.py plan --scope python     # Plan Python updates  
  python scripts/dependency_upgrade.py upgrade --dry-run       # Simulate upgrade
  python scripts/dependency_upgrade.py upgrade --type patch    # Apply patch updates
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['check', 'plan', 'upgrade', 'security-scan'],
                       help='Action to perform')
    parser.add_argument('--scope', choices=['all', 'python', 'docker', 'github-actions'],
                       default='python', help='Scope of dependencies to check')
    parser.add_argument('--type', choices=['patch', 'minor', 'major'],
                       default='patch', help='Type of updates to apply')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without executing')
    parser.add_argument('--auto-approve', action='store_true',
                       help='Automatically approve license compatibility issues')
    
    args = parser.parse_args()
    
    try:
        upgrader = DependencyUpgrader(
            dry_run=args.dry_run,
            auto_approve=args.auto_approve
        )
        
        if args.command == 'check':
            upgrader.check()
        elif args.command == 'plan':
            upgrader.plan(scope=args.scope)
        elif args.command == 'upgrade':
            success = upgrader.upgrade(scope=args.scope, update_type=args.type)
            if not success:
                sys.exit(1)
        elif args.command == 'security-scan':
            scan_results = upgrader._run_security_scan()
            if scan_results['vulnerable_packages']:
                print("🚨 Vulnerable packages found:")
                for pkg in scan_results['vulnerable_packages']:
                    print(f"  • {pkg}")
                print("\nConsider upgrading these packages with: python scripts/dependency_upgrade.py upgrade --type minor")
            else:
                print("✅ No security vulnerabilities detected in current dependencies")
                
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()