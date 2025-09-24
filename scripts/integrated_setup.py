#!/usr/bin/env python3
"""
StratMaster Integrated Setup and Upgrade System

Chains asset management with dependency upgrades for complete environment setup:
1. Register all package dependencies
2. Download required assets from manifest 
3. Run intelligent dependency upgrades
4. Validate the complete environment

This ensures all components are up-to-date before development work begins.

Usage:
    python scripts/integrated_setup.py setup --dry-run
    python scripts/integrated_setup.py setup --required-only
    python scripts/integrated_setup.py setup --full
    python scripts/integrated_setup.py validate
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path


class IntegratedSetup:
    """Manages the complete setup and upgrade workflow."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path.cwd()
        self.scripts_dir = self.project_root / "scripts"
        
    def run_setup(self, setup_type: str = "required") -> bool:
        """Run the complete setup workflow."""
        print("🚀 StratMaster Integrated Setup")
        print("=" * 50)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"Setup type: {setup_type}")
        print(f"Started: {datetime.now(UTC).isoformat()}")
        print()
        
        steps = [
            ("📦 Register Dependencies", self._register_dependencies),
            ("📥 Download Assets", lambda: self._download_assets(setup_type)),
            ("🔄 Upgrade Dependencies", self._upgrade_dependencies), 
            ("✅ Validate Environment", self._validate_environment)
        ]
        
        for step_name, step_func in steps:
            print(f"{step_name}")
            print("-" * len(step_name))
            
            try:
                success = step_func()
                if not success:
                    print(f"❌ {step_name} failed")
                    return False
                print(f"✅ {step_name} completed")
                print()
                
            except Exception as e:
                print(f"❌ {step_name} failed with error: {e}")
                return False
                
        print("🎉 Integrated setup completed successfully!")
        return True
        
    def _register_dependencies(self) -> bool:
        """Register all package dependencies."""
        cmd = [sys.executable, str(self.scripts_dir / "register_dependencies.py"), "register"]
        
        if self.dry_run:
            print("DRY RUN: Would register dependencies")
            return True
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(result.stderr)
            return False
            
    def _download_assets(self, setup_type: str) -> bool:
        """Download assets based on setup type."""
        cmd = [sys.executable, str(self.scripts_dir / "assets_pull.py"), "pull"]
        
        if setup_type in ["required", "required-only"]:
            cmd.append("--required-only")
        else:
            cmd.append("--all")
            
        if self.dry_run:
            cmd.append("--dry-run")
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(result.stderr)
            return False
            
    def _upgrade_dependencies(self) -> bool:
        """Run intelligent dependency upgrades."""
        # First check what needs upgrading
        check_cmd = [
            sys.executable, 
            str(self.scripts_dir / "dependency_upgrade.py"), 
            "check"
        ]
        
        if self.dry_run:
            check_cmd.append("--dry-run")
            
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if "Total updates available: 0" in result.stdout:
            print("✅ All dependencies are up to date")
            return True
            
        # Run safe patch updates
        upgrade_cmd = [
            sys.executable,
            str(self.scripts_dir / "dependency_upgrade.py"),
            "upgrade",
            "--type", "patch"
        ]
        
        if self.dry_run:
            upgrade_cmd.append("--dry-run")
            
        result = subprocess.run(upgrade_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(result.stderr)
            return False
            
    def _validate_environment(self) -> bool:
        """Validate the complete environment setup."""
        validations = [
            ("Dependency registry", self._validate_dependency_registry),
            ("Asset downloads", self._validate_assets),
            ("Python environment", self._validate_python_env),
        ]
        
        all_valid = True
        
        for validation_name, validation_func in validations:
            try:
                if validation_func():
                    print(f"  ✅ {validation_name}")
                else:
                    print(f"  ❌ {validation_name}")
                    all_valid = False
            except Exception as e:
                print(f"  ❌ {validation_name}: {e}")
                all_valid = False
                
        return all_valid
        
    def _validate_dependency_registry(self) -> bool:
        """Validate the dependency registry."""
        cmd = [sys.executable, str(self.scripts_dir / "register_dependencies.py"), "validate"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    def _validate_assets(self) -> bool:
        """Validate downloaded assets."""
        cmd = [sys.executable, str(self.scripts_dir / "assets_pull.py"), "verify"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    def _validate_python_env(self) -> bool:
        """Validate Python environment can load main packages."""
        if self.dry_run:
            return True
            
        try:
            # Try importing core packages
            import fastapi
            import pydantic
            import uvicorn
            return True
        except ImportError:
            return False
            
    def run_validate_only(self) -> bool:
        """Run only validation steps."""
        print("🔍 StratMaster Environment Validation")
        print("=" * 40)
        
        return self._validate_environment()


def main():
    parser = argparse.ArgumentParser(
        description="StratMaster Integrated Setup and Upgrade System",
        epilog="""
Examples:
  python scripts/integrated_setup.py setup --required-only  # Minimal setup
  python scripts/integrated_setup.py setup --full           # Complete setup  
  python scripts/integrated_setup.py setup --dry-run        # Preview changes
  python scripts/integrated_setup.py validate               # Validate only
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['setup', 'validate'],
                       help='Action to perform')
    parser.add_argument('--required-only', action='store_true',
                       help='Download only required assets')
    parser.add_argument('--full', action='store_true', 
                       help='Download all assets including optional')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    # Determine setup type
    setup_type = "required"
    if args.full:
        setup_type = "full"
    elif args.required_only:
        setup_type = "required-only"
        
    try:
        integrated_setup = IntegratedSetup(dry_run=args.dry_run)
        
        if args.command == 'setup':
            success = integrated_setup.run_setup(setup_type)
            if not success:
                sys.exit(1)
        elif args.command == 'validate':
            success = integrated_setup.run_validate_only()
            if not success:
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()