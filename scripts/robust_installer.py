#!/usr/bin/env python3
"""
StratMaster Robust Dependency Installer

Network-resilient dependency installation system with:
- Intelligent retry mechanisms with exponential backoff
- Offline mode support with local package caching
- Network failure detection and graceful degradation
- Multiple package index fallback support
- GitHub Actions environment optimization

Usage:
    python scripts/robust_installer.py install --requirements requirements.txt
    python scripts/robust_installer.py install --package fastapi==0.100.0
    python scripts/robust_installer.py cache-warmup
    python scripts/robust_installer.py validate-environment
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Monitor network connectivity and adapt installation strategy."""
    
    def __init__(self):
        self.connectivity_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def check_connectivity(self, url: str = "https://pypi.org/simple/", timeout: int = 10) -> bool:
        """Check network connectivity to a given URL."""
        cache_key = f"{url}_{timeout}"
        now = time.time()
        
        # Check cache first
        if cache_key in self.connectivity_cache:
            cached_time, result = self.connectivity_cache[cache_key]
            if now - cached_time < self.cache_ttl:
                return result
        
        try:
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                connected = response.status == 200
                self.connectivity_cache[cache_key] = (now, connected)
                return connected
        except (urllib.error.URLError, OSError, Exception) as e:
            logger.warning(f"Connectivity check failed for {url}: {e}")
            self.connectivity_cache[cache_key] = (now, False)
            return False
    
    def get_network_strategy(self) -> str:
        """Determine optimal network strategy based on connectivity."""
        strategies = [
            ("https://pypi.org/simple/", "online"),
            ("https://files.pythonhosted.org/", "limited"),
        ]
        
        for url, strategy in strategies:
            if self.check_connectivity(url, timeout=5):
                logger.info(f"Network strategy: {strategy} (via {url})")
                return strategy
        
        logger.warning("No network connectivity detected, switching to offline mode")
        return "offline"


class DependencyInstaller:
    """Robust dependency installer with network resilience."""
    
    def __init__(self, 
                 python_executable: str = None,
                 cache_dir: Path = None,
                 max_retries: int = 5,
                 timeout_seconds: int = 300):
        self.python_executable = python_executable or sys.executable
        self.cache_dir = cache_dir or Path.home() / ".cache" / "stratmaster"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.network_monitor = NetworkMonitor()
        
        # Package index mirrors for fallback
        self.package_indexes = [
            "https://pypi.org/simple/",
            "https://pypi.python.org/simple/",
            # Add more mirrors as needed
        ]
        
        # GitHub Actions optimizations
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        if self.is_github_actions:
            logger.info("GitHub Actions environment detected, applying optimizations")
            self.timeout_seconds = 600  # Longer timeouts for CI
    
    def _run_pip_command(self, args: List[str], attempt: int = 1) -> Tuple[bool, str]:
        """Run a pip command with retry logic."""
        # Build base command
        cmd = [
            self.python_executable, "-m", "pip",
            "--disable-pip-version-check",
            "--timeout", str(self.timeout_seconds),
        ]
        cmd.extend(args)
        
        # Add caching and optimization flags
        if self.cache_dir:
            cmd.extend(["--cache-dir", str(self.cache_dir)])
        
        # GitHub Actions optimizations (only add supported flags)
        if self.is_github_actions:
            # Check pip version to determine supported flags
            try:
                pip_version_result = subprocess.run(
                    [self.python_executable, "-m", "pip", "--version"],
                    capture_output=True, text=True, timeout=10
                )
                if pip_version_result.returncode == 0:
                    pip_version_str = pip_version_result.stdout
                    # Only add modern flags for newer pip versions
                    if "pip 2" in pip_version_str or "pip 3" in pip_version_str:
                        cmd.extend(["--progress-bar", "off"])
            except Exception:
                pass
        
        logger.info(f"Attempt {attempt}: {' '.join(cmd)}")
        
        try:
            # Set environment variables for better pip behavior
            env = os.environ.copy()
            env.update({
                'PYTHONNOUSERSITE': '1',
                'PIP_DISABLE_PIP_VERSION_CHECK': '1',
                'PIP_NO_WARN_SCRIPT_LOCATION': '1',
                'PIP_TIMEOUT': str(self.timeout_seconds),
            })
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds + 60,  # Extra buffer
                env=env
            )
            
            if result.returncode == 0:
                logger.info(f"Command succeeded on attempt {attempt}")
                return True, result.stdout
            else:
                error_msg = f"Command failed (exit code {result.returncode}): {result.stderr}"
                logger.warning(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {self.timeout_seconds} seconds"
            logger.warning(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Command failed with exception: {e}"
            logger.warning(error_msg)
            return False, error_msg
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        import random
        base_delay = min(60, 2 ** attempt)  # Cap at 60 seconds
        jitter = random.uniform(0.5, 1.5)  # Add randomness
        return base_delay * jitter
    
    def install_package(self, 
                       package_spec: str, 
                       allow_offline: bool = True) -> bool:
        """Install a single package with retry logic."""
        logger.info(f"Installing package: {package_spec}")
        
        network_strategy = self.network_monitor.get_network_strategy()
        
        if network_strategy == "offline" and not allow_offline:
            logger.error("Offline mode not allowed and no network connectivity")
            return False
        
        for attempt in range(1, self.max_retries + 1):
            # Choose installation strategy based on network and attempt
            if network_strategy == "offline":
                args = ["install", "--offline", "--find-links", str(self.cache_dir), package_spec]
            elif attempt > 1:
                # Use alternate index on retries
                index_url = self.package_indexes[(attempt - 1) % len(self.package_indexes)]
                args = ["install", "-i", index_url, package_spec]
            else:
                args = ["install", package_spec]
            
            success, output = self._run_pip_command(args, attempt)
            
            if success:
                logger.info(f"Successfully installed {package_spec}")
                return True
            
            if attempt < self.max_retries:
                delay = self._calculate_backoff_delay(attempt)
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
                
                # Re-check network strategy for next attempt
                network_strategy = self.network_monitor.get_network_strategy()
        
        logger.error(f"Failed to install {package_spec} after {self.max_retries} attempts")
        return False
    
    def install_requirements(self, requirements_file: Path) -> bool:
        """Install packages from requirements file with resilience."""
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        logger.info(f"Installing requirements from: {requirements_file}")
        
        # Try batch installation first (more efficient)
        if self._try_batch_install(requirements_file):
            return True
        
        # Fall back to individual package installation
        logger.info("Batch installation failed, trying individual packages...")
        return self._install_requirements_individually(requirements_file)
    
    def _try_batch_install(self, requirements_file: Path) -> bool:
        """Try to install all requirements at once."""
        args = ["install", "-r", str(requirements_file)]
        
        # Add user flag if not in virtual environment
        if not self._in_virtual_environment():
            args.append("--user")
        
        for attempt in range(1, 3):  # Limit batch attempts
            success, output = self._run_pip_command(args, attempt)
            if success:
                logger.info("Batch installation successful")
                return True
            
            if attempt < 2:
                delay = self._calculate_backoff_delay(attempt)
                time.sleep(delay)
        
        return False
    
    def _install_requirements_individually(self, requirements_file: Path) -> bool:
        """Install each requirement individually with error tolerance."""
        with open(requirements_file, 'r') as f:
            lines = f.readlines()
        
        packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                packages.append(line)
        
        logger.info(f"Installing {len(packages)} packages individually")
        
        failed_packages = []
        for package in packages:
            if not self.install_package(package):
                failed_packages.append(package)
        
        if failed_packages:
            logger.warning(f"Failed to install {len(failed_packages)} packages: {failed_packages}")
            # Don't fail completely - some packages may be optional
            return len(failed_packages) < len(packages) * 0.5  # Allow up to 50% failure
        
        logger.info("All packages installed successfully")
        return True
    
    def _in_virtual_environment(self) -> bool:
        """Check if running in a virtual environment."""
        return hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
    
    def warm_cache(self, packages: List[str] = None) -> bool:
        """Pre-download packages for offline installation."""
        if not packages:
            # Default packages for StratMaster
            packages = [
                "fastapi>=0.100.0", "pydantic>=2.0.0", "uvicorn[standard]",
                "pytest", "requests", "click", "pyyaml"
            ]
        
        logger.info(f"Warming cache with {len(packages)} packages...")
        
        success_count = 0
        for package in packages:
            args = ["download", "--dest", str(self.cache_dir), package]
            success, output = self._run_pip_command(args)
            if success:
                success_count += 1
                logger.info(f"Cached: {package}")
            else:
                logger.warning(f"Failed to cache: {package}")
        
        logger.info(f"Cache warming completed: {success_count}/{len(packages)} packages")
        return success_count > 0
    
    def validate_environment(self) -> Dict[str, any]:
        """Validate the installation environment."""
        validation_result = {
            "timestamp": datetime.now(UTC).isoformat(),
            "python_executable": self.python_executable,
            "python_version": sys.version,
            "virtual_environment": self._in_virtual_environment(),
            "cache_dir": str(self.cache_dir),
            "cache_size_mb": self._get_cache_size(),
            "network_strategy": self.network_monitor.get_network_strategy(),
            "github_actions": self.is_github_actions,
            "pip_version": self._get_pip_version(),
        }
        
        logger.info("Environment validation:")
        for key, value in validation_result.items():
            logger.info(f"  {key}: {value}")
        
        return validation_result
    
    def _get_cache_size(self) -> float:
        """Get cache directory size in MB."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file())
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    def _get_pip_version(self) -> str:
        """Get pip version."""
        try:
            result = subprocess.run(
                [self.python_executable, "-m", "pip", "--version"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"


def main():
    parser = argparse.ArgumentParser(description="StratMaster Robust Dependency Installer")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install packages')
    install_group = install_parser.add_mutually_exclusive_group(required=True)
    install_group.add_argument('--requirements', type=Path, help='Requirements file to install')
    install_group.add_argument('--package', help='Single package to install')
    install_parser.add_argument('--no-offline', action='store_true', 
                               help='Disable offline installation fallback')
    
    # Cache warmup command
    cache_parser = subparsers.add_parser('cache-warmup', help='Pre-download packages for offline use')
    cache_parser.add_argument('--packages', nargs='*', help='Specific packages to cache')
    
    # Environment validation command
    subparsers.add_parser('validate-environment', help='Validate installation environment')
    
    # Common arguments
    parser.add_argument('--python', default=sys.executable, help='Python executable to use')
    parser.add_argument('--cache-dir', type=Path, help='Cache directory')
    parser.add_argument('--max-retries', type=int, default=5, help='Maximum retry attempts')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create installer
    installer = DependencyInstaller(
        python_executable=args.python,
        cache_dir=args.cache_dir,
        max_retries=args.max_retries,
        timeout_seconds=args.timeout
    )
    
    try:
        if args.command == 'install':
            if args.requirements:
                success = installer.install_requirements(args.requirements)
            else:
                success = installer.install_package(
                    args.package, 
                    allow_offline=not args.no_offline
                )
            return 0 if success else 1
            
        elif args.command == 'cache-warmup':
            success = installer.warm_cache(args.packages)
            return 0 if success else 1
            
        elif args.command == 'validate-environment':
            result = installer.validate_environment()
            print(json.dumps(result, indent=2))
            return 0
            
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        logger.info("Installation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())