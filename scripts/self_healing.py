#!/usr/bin/env python3
"""
StratMaster Self-Healing System

Automated recovery and remediation system with:
- Proactive issue detection and resolution
- Service restart and recovery automation
- Dependency conflict resolution and rollback
- Infrastructure drift detection and correction
- Integration with health monitoring for trigger-based healing

Usage:
    python scripts/self_healing.py analyze --auto-heal
    python scripts/self_healing.py recover --service api
    python scripts/self_healing.py rollback --to-last-known-good
    python scripts/self_healing.py validate-and-heal
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import threading
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class HealingAction:
    """Represents a healing action to be taken."""
    name: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    action_type: str  # "restart", "install", "rollback", "cleanup", "config"
    command: Optional[List[str]] = None
    script: Optional[str] = None
    timeout: int = 300  # seconds
    retry_count: int = 3
    prerequisites: Optional[List[str]] = None
    rollback_action: Optional[str] = None


@dataclass
class HealingResult:
    """Result of a healing action."""
    action_name: str
    success: bool
    message: str
    details: Dict[str, Any]
    timestamp: str
    execution_time_ms: int
    output: Optional[str] = None
    error: Optional[str] = None


class ServiceRecovery:
    """Handles service-specific recovery actions."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services = {
            "api": {
                "health_url": "http://127.0.0.1:8080/healthz",
                "start_command": ["make", "api.run"],
                "process_name": "uvicorn",
                "port": 8080
            },
            "research_mcp": {
                "health_url": "http://127.0.0.1:8081/health",
                "start_command": ["make", "research-mcp.run"],
                "process_name": "uvicorn",
                "port": 8081
            }
        }
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy."""
        if service_name not in self.services:
            logger.warning(f"Unknown service: {service_name}")
            return False
        
        service = self.services[service_name]
        health_url = service["health_url"]
        
        try:
            import urllib.request
            with urllib.request.urlopen(health_url, timeout=10) as response:
                return response.status == 200
        except Exception:
            return False
    
    def restart_service(self, service_name: str) -> HealingResult:
        """Restart a specific service."""
        start_time = time.time()
        
        if service_name not in self.services:
            return HealingResult(
                action_name=f"restart_{service_name}",
                success=False,
                message=f"Unknown service: {service_name}",
                details={"service": service_name},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=0
            )
        
        service = self.services[service_name]
        
        try:
            # First, try to stop the service gracefully
            self._stop_service(service_name)
            time.sleep(2)  # Wait for graceful shutdown
            
            # Start the service
            logger.info(f"Starting service: {service_name}")
            process = subprocess.Popen(
                service["start_command"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for startup and health check
            startup_timeout = 30
            startup_start = time.time()
            
            while time.time() - startup_start < startup_timeout:
                if self.check_service_health(service_name):
                    execution_time = int((time.time() - start_time) * 1000)
                    return HealingResult(
                        action_name=f"restart_{service_name}",
                        success=True,
                        message=f"Service {service_name} restarted successfully",
                        details={
                            "service": service_name,
                            "startup_time_ms": int((time.time() - startup_start) * 1000)
                        },
                        timestamp=datetime.now(UTC).isoformat(),
                        execution_time_ms=execution_time
                    )
                time.sleep(1)
            
            # Service didn't become healthy in time
            execution_time = int((time.time() - start_time) * 1000)
            return HealingResult(
                action_name=f"restart_{service_name}",
                success=False,
                message=f"Service {service_name} failed to become healthy after restart",
                details={"service": service_name, "timeout": startup_timeout},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealingResult(
                action_name=f"restart_{service_name}",
                success=False,
                message=f"Failed to restart service {service_name}: {str(e)}",
                details={"service": service_name, "error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
    
    def _stop_service(self, service_name: str):
        """Stop a service by killing its processes."""
        try:
            service = self.services[service_name]
            process_name = service["process_name"]
            port = service["port"]
            
            # Kill by process name
            subprocess.run(
                ["pkill", "-f", process_name],
                capture_output=True, timeout=10
            )
            
            # Kill by port if still running
            try:
                lsof_result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True, text=True, timeout=10
                )
                if lsof_result.stdout:
                    pids = lsof_result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            subprocess.run(["kill", pid], timeout=5)
            except Exception:
                pass
                
        except Exception as e:
            logger.warning(f"Error stopping service {service_name}: {e}")


class DependencyRecovery:
    """Handles dependency-related recovery actions."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / ".healing_backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_dependency_backup(self) -> str:
        """Create a backup of current dependency state."""
        backup_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"deps_{backup_id}"
        backup_path.mkdir(exist_ok=True)
        
        # Backup key files
        files_to_backup = [
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
            ".dependency_registry.json"
        ]
        
        for file_name in files_to_backup:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, backup_path / file_name)
        
        # Backup virtual environment state
        if (self.project_root / ".venv").exists():
            freeze_result = subprocess.run(
                [str(self.project_root / ".venv" / "bin" / "pip"), "freeze"],
                capture_output=True, text=True
            )
            if freeze_result.returncode == 0:
                with open(backup_path / "pip_freeze.txt", "w") as f:
                    f.write(freeze_result.stdout)
        
        logger.info(f"Created dependency backup: {backup_id}")
        return backup_id
    
    def restore_dependency_backup(self, backup_id: str) -> HealingResult:
        """Restore dependencies from a backup."""
        start_time = time.time()
        backup_path = self.backup_dir / f"deps_{backup_id}"
        
        if not backup_path.exists():
            return HealingResult(
                action_name="restore_dependencies",
                success=False,
                message=f"Backup not found: {backup_id}",
                details={"backup_id": backup_id},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=0
            )
        
        try:
            # Restore requirement files
            for file_name in ["requirements.txt", "requirements-dev.txt", "pyproject.toml"]:
                backup_file = backup_path / file_name
                target_file = self.project_root / file_name
                if backup_file.exists():
                    shutil.copy2(backup_file, target_file)
                    logger.info(f"Restored {file_name}")
            
            # Reinstall dependencies
            result = subprocess.run(
                [str(self.project_root / ".venv" / "bin" / "pip"), 
                 "install", "-r", str(self.project_root / "requirements.txt")],
                capture_output=True, text=True, timeout=300
            )
            
            success = result.returncode == 0
            execution_time = int((time.time() - start_time) * 1000)
            
            return HealingResult(
                action_name="restore_dependencies",
                success=success,
                message=f"Dependency restoration {'succeeded' if success else 'failed'}",
                details={"backup_id": backup_id, "exit_code": result.returncode},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time,
                output=result.stdout if success else None,
                error=result.stderr if not success else None
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealingResult(
                action_name="restore_dependencies",
                success=False,
                message=f"Failed to restore dependencies: {str(e)}",
                details={"backup_id": backup_id, "error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
    
    def fix_dependency_conflicts(self) -> HealingResult:
        """Attempt to resolve dependency conflicts."""
        start_time = time.time()
        
        try:
            # Use the robust installer to reinstall dependencies
            robust_installer = self.project_root / "scripts" / "robust_installer.py"
            requirements_file = self.project_root / "requirements.txt"
            
            if not robust_installer.exists() or not requirements_file.exists():
                return HealingResult(
                    action_name="fix_dependency_conflicts",
                    success=False,
                    message="Required files not found for dependency conflict resolution",
                    details={
                        "robust_installer_exists": robust_installer.exists(),
                        "requirements_exists": requirements_file.exists()
                    },
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=0
                )
            
            # Run robust installer
            result = subprocess.run(
                [sys.executable, str(robust_installer), "install", 
                 "--requirements", str(requirements_file)],
                capture_output=True, text=True, timeout=600
            )
            
            success = result.returncode == 0
            execution_time = int((time.time() - start_time) * 1000)
            
            return HealingResult(
                action_name="fix_dependency_conflicts",
                success=success,
                message=f"Dependency conflict resolution {'succeeded' if success else 'failed'}",
                details={"exit_code": result.returncode},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time,
                output=result.stdout if success else None,
                error=result.stderr if not success else None
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealingResult(
                action_name="fix_dependency_conflicts",
                success=False,
                message=f"Failed to fix dependency conflicts: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )


class EnvironmentRecovery:
    """Handles environment-level recovery actions."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def cleanup_temp_files(self) -> HealingResult:
        """Clean up temporary files and caches."""
        start_time = time.time()
        
        try:
            cleaned_size = 0
            cleaned_files = 0
            
            # Clean common temporary directories
            temp_dirs = [
                self.project_root / "__pycache__",
                self.project_root / ".pytest_cache",
                self.project_root / ".mypy_cache",
                self.project_root / ".ruff_cache",
                self.project_root / "node_modules",
                Path("/tmp") / "stratmaster*"
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists() and temp_dir.is_dir():
                    # Calculate size before deletion
                    try:
                        size = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                        cleaned_size += size
                        file_count = len(list(temp_dir.rglob('*')))
                        cleaned_files += file_count
                        
                        shutil.rmtree(temp_dir)
                        logger.info(f"Cleaned {temp_dir}")
                    except Exception as e:
                        logger.warning(f"Could not clean {temp_dir}: {e}")
            
            # Clean Python cache files
            for cache_file in self.project_root.rglob("*.pyc"):
                try:
                    cleaned_size += cache_file.stat().st_size
                    cleaned_files += 1
                    cache_file.unlink()
                except Exception:
                    pass
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return HealingResult(
                action_name="cleanup_temp_files",
                success=True,
                message=f"Cleaned up temporary files: {cleaned_files} files, {cleaned_size / 1024 / 1024:.1f} MB",
                details={
                    "files_cleaned": cleaned_files,
                    "size_cleaned_mb": round(cleaned_size / 1024 / 1024, 1)
                },
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealingResult(
                action_name="cleanup_temp_files",
                success=False,
                message=f"Failed to clean temporary files: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
    
    def rebuild_virtual_environment(self) -> HealingResult:
        """Rebuild the virtual environment from scratch."""
        start_time = time.time()
        
        try:
            venv_path = self.project_root / ".venv"
            
            # Remove existing virtual environment
            if venv_path.exists():
                shutil.rmtree(venv_path)
                logger.info("Removed existing virtual environment")
            
            # Create new virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to create virtual environment: {result.stderr}")
            
            # Install basic packages
            pip_path = venv_path / "bin" / "pip"
            result = subprocess.run(
                [str(pip_path), "install", "--upgrade", "pip", "setuptools", "wheel"],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode != 0:
                logger.warning("Failed to upgrade pip, continuing anyway")
            
            # Install project dependencies
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                result = subprocess.run(
                    [str(pip_path), "install", "-r", str(requirements_file)],
                    capture_output=True, text=True, timeout=600
                )
                
                if result.returncode != 0:
                    raise Exception(f"Failed to install requirements: {result.stderr}")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return HealingResult(
                action_name="rebuild_virtual_environment",
                success=True,
                message="Virtual environment rebuilt successfully",
                details={"venv_path": str(venv_path)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealingResult(
                action_name="rebuild_virtual_environment",
                success=False,
                message=f"Failed to rebuild virtual environment: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )


class SelfHealingSystem:
    """Main self-healing system coordinator."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.service_recovery = ServiceRecovery(self.project_root)
        self.dependency_recovery = DependencyRecovery(self.project_root)
        self.environment_recovery = EnvironmentRecovery(self.project_root)
        
        # Healing history
        self.healing_history = []
        self.max_history = 100
        
        # Define healing strategies
        self.healing_strategies = {
            "service_unavailable": [
                HealingAction(
                    name="restart_service",
                    description="Restart the unhealthy service",
                    severity="medium",
                    action_type="restart",
                    timeout=60,
                    retry_count=2
                ),
                HealingAction(
                    name="rebuild_environment",
                    description="Rebuild virtual environment if service restart fails",
                    severity="high",
                    action_type="rebuild",
                    timeout=600,
                    retry_count=1
                )
            ],
            "dependency_conflicts": [
                HealingAction(
                    name="fix_conflicts",
                    description="Attempt to resolve dependency conflicts",
                    severity="medium",
                    action_type="install",
                    timeout=600,
                    retry_count=2
                ),
                HealingAction(
                    name="restore_backup",
                    description="Restore from last known good dependency state",
                    severity="high",
                    action_type="rollback",
                    timeout=300,
                    retry_count=1
                )
            ],
            "high_resource_usage": [
                HealingAction(
                    name="cleanup_temp_files",
                    description="Clean up temporary files to free space/memory",
                    severity="low",
                    action_type="cleanup",
                    timeout=60,
                    retry_count=1
                ),
                HealingAction(
                    name="restart_services",
                    description="Restart services to free memory",
                    severity="medium",
                    action_type="restart",
                    timeout=120,
                    retry_count=1
                )
            ]
        }
    
    def analyze_and_heal(self, health_report: Dict[str, Any] = None) -> List[HealingResult]:
        """Analyze system health and perform automated healing."""
        if not health_report:
            # Get health report from health monitor
            health_monitor_script = self.project_root / "scripts" / "system_health_monitor.py"
            if health_monitor_script.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, str(health_monitor_script), "check", "--all"],
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode == 0:
                        health_report = json.loads(result.stdout)
                    else:
                        logger.warning("Could not get health report, performing basic healing")
                        health_report = {"overall_status": "unknown", "checks": []}
                except Exception as e:
                    logger.error(f"Failed to get health report: {e}")
                    return []
        
        # Analyze issues and determine healing actions
        healing_actions = self._analyze_issues(health_report)
        
        # Execute healing actions
        healing_results = []
        for action in healing_actions:
            result = self._execute_healing_action(action)
            healing_results.append(result)
            
            # Store in history
            self.healing_history.append(result)
            if len(self.healing_history) > self.max_history:
                self.healing_history.pop(0)
        
        return healing_results
    
    def _analyze_issues(self, health_report: Dict[str, Any]) -> List[HealingAction]:
        """Analyze health report and determine needed healing actions."""
        actions = []
        
        if not health_report.get("checks"):
            return actions
        
        # Check for service issues
        service_issues = [
            check for check in health_report["checks"] 
            if check.get("name", "").endswith("_http") and check.get("status") == "critical"
        ]
        
        if service_issues:
            actions.extend(self.healing_strategies.get("service_unavailable", []))
        
        # Check for dependency issues
        dependency_issues = [
            check for check in health_report["checks"]
            if "dependency" in check.get("name", "") and check.get("status") in ["critical", "warning"]
        ]
        
        if dependency_issues:
            actions.extend(self.healing_strategies.get("dependency_conflicts", []))
        
        # Check for resource issues
        resource_issues = [
            check for check in health_report["checks"]
            if check.get("name") in ["cpu_usage", "memory_usage", "disk_usage"] 
            and check.get("status") in ["critical", "warning"]
        ]
        
        if resource_issues:
            actions.extend(self.healing_strategies.get("high_resource_usage", []))
        
        # Remove duplicates while preserving order
        unique_actions = []
        seen_names = set()
        for action in actions:
            if action.name not in seen_names:
                unique_actions.append(action)
                seen_names.add(action.name)
        
        return unique_actions
    
    def _execute_healing_action(self, action: HealingAction) -> HealingResult:
        """Execute a single healing action."""
        logger.info(f"Executing healing action: {action.name} - {action.description}")
        
        start_time = time.time()
        
        try:
            if action.name == "restart_service":
                # Restart all unhealthy services
                results = []
                for service_name in self.service_recovery.services.keys():
                    if not self.service_recovery.check_service_health(service_name):
                        result = self.service_recovery.restart_service(service_name)
                        results.append(result)
                
                # Return combined result
                success = all(r.success for r in results)
                messages = [r.message for r in results]
                
                return HealingResult(
                    action_name=action.name,
                    success=success,
                    message="; ".join(messages) if messages else "No services to restart",
                    details={"service_results": [asdict(r) for r in results]},
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
                
            elif action.name == "fix_conflicts":
                return self.dependency_recovery.fix_dependency_conflicts()
                
            elif action.name == "restore_backup":
                # Find most recent backup
                backups = list(self.dependency_recovery.backup_dir.glob("deps_*"))
                if backups:
                    latest_backup = max(backups).name.replace("deps_", "")
                    return self.dependency_recovery.restore_dependency_backup(latest_backup)
                else:
                    return HealingResult(
                        action_name=action.name,
                        success=False,
                        message="No dependency backups found",
                        details={},
                        timestamp=datetime.now(UTC).isoformat(),
                        execution_time_ms=0
                    )
                    
            elif action.name == "cleanup_temp_files":
                return self.environment_recovery.cleanup_temp_files()
                
            elif action.name == "rebuild_environment":
                return self.environment_recovery.rebuild_virtual_environment()
                
            else:
                return HealingResult(
                    action_name=action.name,
                    success=False,
                    message=f"Unknown healing action: {action.name}",
                    details={"action": asdict(action)},
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=0
                )
                
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealingResult(
                action_name=action.name,
                success=False,
                message=f"Healing action failed: {str(e)}",
                details={"error": str(e), "action": asdict(action)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
    
    def create_system_snapshot(self) -> str:
        """Create a snapshot of the current system state for rollback."""
        snapshot_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        logger.info(f"Creating system snapshot: {snapshot_id}")
        
        # Create dependency backup
        dep_backup_id = self.dependency_recovery.create_dependency_backup()
        
        # Store snapshot metadata
        snapshot_data = {
            "snapshot_id": snapshot_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "dependency_backup": dep_backup_id,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform
            }
        }
        
        snapshot_file = self.project_root / ".healing_backups" / f"snapshot_{snapshot_id}.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        return snapshot_id
    
    def save_healing_report(self, results: List[HealingResult], output_path: Path):
        """Save healing results to file."""
        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "healing_results": [asdict(r) for r in results],
            "summary": {
                "total_actions": len(results),
                "successful_actions": sum(1 for r in results if r.success),
                "failed_actions": sum(1 for r in results if not r.success)
            }
        }
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Healing report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="StratMaster Self-Healing System")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze system and perform healing')
    analyze_parser.add_argument('--auto-heal', action='store_true', help='Automatically perform healing actions')
    analyze_parser.add_argument('--dry-run', action='store_true', help='Show what would be healed without executing')
    
    # Recover command
    recover_parser = subparsers.add_parser('recover', help='Perform specific recovery action')
    recover_parser.add_argument('--service', help='Restart specific service')
    recover_parser.add_argument('--dependencies', action='store_true', help='Fix dependency issues')
    recover_parser.add_argument('--environment', action='store_true', help='Rebuild environment')
    recover_parser.add_argument('--cleanup', action='store_true', help='Clean temporary files')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to previous state')
    rollback_parser.add_argument('--to-last-known-good', action='store_true', 
                                help='Rollback to last known good state')
    rollback_parser.add_argument('--snapshot-id', help='Rollback to specific snapshot')
    
    # Validate and heal command
    subparsers.add_parser('validate-and-heal', help='Validate system health and heal if needed')
    
    # Snapshot command
    subparsers.add_parser('snapshot', help='Create system snapshot for rollback')
    
    # Common arguments
    parser.add_argument('--project-root', type=Path, help='Project root directory')
    parser.add_argument('--output', type=Path, help='Output file for healing report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create healing system
    healer = SelfHealingSystem(project_root=args.project_root)
    
    try:
        if args.command == 'analyze':
            if args.dry_run:
                logger.info("Dry run mode - would analyze and show healing actions")
                # TODO: Implement dry run analysis
                return 0
            else:
                results = healer.analyze_and_heal()
                
                if args.output:
                    healer.save_healing_report(results, args.output)
                else:
                    print(json.dumps([asdict(r) for r in results], indent=2))
                
                success_count = sum(1 for r in results if r.success)
                logger.info(f"Healing completed: {success_count}/{len(results)} actions successful")
                return 0 if success_count == len(results) else 1
                
        elif args.command == 'recover':
            results = []
            
            if args.service:
                result = healer.service_recovery.restart_service(args.service)
                results.append(result)
                
            if args.dependencies:
                result = healer.dependency_recovery.fix_dependency_conflicts()
                results.append(result)
                
            if args.environment:
                result = healer.environment_recovery.rebuild_virtual_environment()
                results.append(result)
                
            if args.cleanup:
                result = healer.environment_recovery.cleanup_temp_files()
                results.append(result)
                
            if not results:
                logger.error("No recovery action specified")
                return 1
                
            for result in results:
                print(json.dumps(asdict(result), indent=2))
                
            return 0 if all(r.success for r in results) else 1
            
        elif args.command == 'rollback':
            if args.to_last_known_good:
                # Find most recent backup
                backups = list(healer.dependency_recovery.backup_dir.glob("deps_*"))
                if backups:
                    latest_backup = max(backups).name.replace("deps_", "")
                    result = healer.dependency_recovery.restore_dependency_backup(latest_backup)
                    print(json.dumps(asdict(result), indent=2))
                    return 0 if result.success else 1
                else:
                    logger.error("No backups found for rollback")
                    return 1
                    
            elif args.snapshot_id:
                result = healer.dependency_recovery.restore_dependency_backup(args.snapshot_id)
                print(json.dumps(asdict(result), indent=2))
                return 0 if result.success else 1
            else:
                logger.error("Must specify rollback target")
                return 1
                
        elif args.command == 'validate-and-heal':
            # First create a snapshot
            snapshot_id = healer.create_system_snapshot()
            logger.info(f"Created snapshot {snapshot_id} before healing")
            
            # Then analyze and heal
            results = healer.analyze_and_heal()
            
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Healing completed: {success_count}/{len(results)} actions successful")
            
            return 0 if success_count == len(results) or len(results) == 0 else 1
            
        elif args.command == 'snapshot':
            snapshot_id = healer.create_system_snapshot()
            print(f"Created snapshot: {snapshot_id}")
            return 0
            
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())