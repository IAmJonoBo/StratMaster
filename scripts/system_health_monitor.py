#!/usr/bin/env python3
"""
StratMaster System Health Monitor

Comprehensive health monitoring and sanity checking system with:
- Continuous service health monitoring
- Dependency freshness and vulnerability scanning
- Performance metrics collection and alerting
- Self-healing automation triggers
- GitHub Actions integration

Usage:
    python scripts/system_health_monitor.py check --all
    python scripts/system_health_monitor.py monitor --daemon
    python scripts/system_health_monitor.py report --format json
    python scripts/system_health_monitor.py heal --auto
"""

import argparse
import json
import logging
import os
import psutil
import requests
import subprocess
import sys
import time
import threading
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    name: str
    status: str  # "healthy", "warning", "critical", "unknown"
    message: str
    details: Dict[str, Any]
    timestamp: str
    execution_time_ms: int
    remediation_suggested: Optional[str] = None


@dataclass 
class SystemHealthReport:
    """Complete system health report."""
    timestamp: str
    overall_status: str
    checks: List[HealthCheckResult]
    summary: Dict[str, int]
    recommendations: List[str]
    environment_info: Dict[str, Any]


class ServiceHealthChecker:
    """Health checker for individual services."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
    
    def check_http_service(self, name: str, url: str, expected_status: int = 200) -> HealthCheckResult:
        """Check HTTP service health."""
        start_time = time.time()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            execution_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == expected_status:
                return HealthCheckResult(
                    name=f"{name}_http",
                    status="healthy",
                    message=f"Service responding (HTTP {response.status_code})",
                    details={
                        "url": url,
                        "status_code": response.status_code,
                        "response_time_ms": execution_time,
                        "content_length": len(response.content)
                    },
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=execution_time
                )
            else:
                return HealthCheckResult(
                    name=f"{name}_http",
                    status="critical",
                    message=f"Unexpected HTTP status: {response.status_code}",
                    details={"url": url, "status_code": response.status_code},
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=execution_time,
                    remediation_suggested="Check service configuration and restart if needed"
                )
                
        except requests.ConnectionError:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name=f"{name}_http",
                status="critical",
                message="Service not accessible (connection refused)",
                details={"url": url, "error": "connection_refused"},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time,
                remediation_suggested="Start the service or check network connectivity"
            )
        except requests.Timeout:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name=f"{name}_http",
                status="warning",
                message=f"Service timeout ({self.timeout}s)",
                details={"url": url, "timeout": self.timeout},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time,
                remediation_suggested="Investigate service performance or increase timeout"
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name=f"{name}_http",
                status="critical",
                message=f"Health check failed: {str(e)}",
                details={"url": url, "error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time,
                remediation_suggested="Check service logs and configuration"
            )


class DependencyChecker:
    """Check dependency health and security."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.requirements_files = [
            project_root / "requirements.txt",
            project_root / "requirements-dev.txt"
        ]
    
    def check_dependency_freshness(self) -> HealthCheckResult:
        """Check if dependencies are up to date."""
        start_time = time.time()
        
        try:
            # Use existing dependency upgrade script to check for updates
            cmd = [
                sys.executable,
                str(self.project_root / "scripts" / "dependency_upgrade.py"),
                "check", "--dry-run"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            execution_time = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                # Parse output to determine if updates are available
                output = result.stdout
                if "Total updates available: 0" in output:
                    status = "healthy"
                    message = "All dependencies are up to date"
                elif "updates available" in output:
                    status = "warning"
                    message = "Dependency updates available"
                else:
                    status = "healthy"
                    message = "Dependencies checked successfully"
                
                return HealthCheckResult(
                    name="dependency_freshness",
                    status=status,
                    message=message,
                    details={"check_output": output.strip()},
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=execution_time,
                    remediation_suggested="Run 'make deps.upgrade.safe' to update" if status == "warning" else None
                )
            else:
                return HealthCheckResult(
                    name="dependency_freshness",
                    status="warning",
                    message="Could not check dependency freshness",
                    details={"error": result.stderr, "exit_code": result.returncode},
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=execution_time
                )
                
        except subprocess.TimeoutExpired:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name="dependency_freshness",
                status="warning",
                message="Dependency check timed out",
                details={"timeout": 60},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name="dependency_freshness",
                status="critical",
                message=f"Dependency check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
    
    def check_security_vulnerabilities(self) -> HealthCheckResult:
        """Check for known security vulnerabilities in dependencies."""
        start_time = time.time()
        
        try:
            # Try to use safety if available
            result = subprocess.run(
                [sys.executable, "-m", "safety", "check", "--json"],
                capture_output=True, text=True, timeout=60
            )
            execution_time = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                # No vulnerabilities found
                return HealthCheckResult(
                    name="security_vulnerabilities",
                    status="healthy",
                    message="No known security vulnerabilities found",
                    details={"scanner": "safety"},
                    timestamp=datetime.now(UTC).isoformat(),
                    execution_time_ms=execution_time
                )
            else:
                # Vulnerabilities found or safety not available
                try:
                    vuln_data = json.loads(result.stdout) if result.stdout else []
                    vuln_count = len(vuln_data) if isinstance(vuln_data, list) else 0
                    
                    if vuln_count > 0:
                        status = "critical" if vuln_count > 5 else "warning"
                        message = f"{vuln_count} security vulnerabilities found"
                        remediation = "Review and update vulnerable packages"
                    else:
                        status = "warning"
                        message = "Security scanner unavailable or failed"
                        remediation = "Install safety package for security scanning"
                        
                    return HealthCheckResult(
                        name="security_vulnerabilities",
                        status=status,
                        message=message,
                        details={
                            "vulnerability_count": vuln_count,
                            "scanner_output": result.stdout[:1000]  # Limit output size
                        },
                        timestamp=datetime.now(UTC).isoformat(),
                        execution_time_ms=execution_time,
                        remediation_suggested=remediation
                    )
                except json.JSONDecodeError:
                    return HealthCheckResult(
                        name="security_vulnerabilities",
                        status="warning",
                        message="Could not parse security scan results",
                        details={"raw_output": result.stdout[:500]},
                        timestamp=datetime.now(UTC).isoformat(),
                        execution_time_ms=execution_time
                    )
                    
        except subprocess.TimeoutExpired:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name="security_vulnerabilities",
                status="warning",
                message="Security scan timed out",
                details={"timeout": 60},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )
        except FileNotFoundError:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name="security_vulnerabilities",
                status="warning",
                message="Security scanner (safety) not installed",
                details={"suggestion": "pip install safety"},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time,
                remediation_suggested="Install safety package: pip install safety"
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                name="security_vulnerabilities",
                status="warning",
                message=f"Security scan failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
                execution_time_ms=execution_time
            )


class SystemResourceChecker:
    """Check system resource health."""
    
    def check_system_resources(self) -> List[HealthCheckResult]:
        """Check CPU, memory, disk usage."""
        results = []
        timestamp = datetime.now(UTC).isoformat()
        
        # Check CPU usage
        start_time = time.time()
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            execution_time = int((time.time() - start_time) * 1000)
            
            if cpu_percent < 80:
                status = "healthy"
                message = f"CPU usage normal ({cpu_percent:.1f}%)"
                remediation = None
            elif cpu_percent < 95:
                status = "warning"
                message = f"High CPU usage ({cpu_percent:.1f}%)"
                remediation = "Investigate high CPU processes"
            else:
                status = "critical"
                message = f"Critical CPU usage ({cpu_percent:.1f}%)"
                remediation = "Immediate attention required - check for runaway processes"
            
            results.append(HealthCheckResult(
                name="cpu_usage",
                status=status,
                message=message,
                details={"cpu_percent": cpu_percent, "cpu_count": psutil.cpu_count()},
                timestamp=timestamp,
                execution_time_ms=execution_time,
                remediation_suggested=remediation
            ))
        except Exception as e:
            results.append(HealthCheckResult(
                name="cpu_usage",
                status="unknown",
                message=f"Could not check CPU usage: {str(e)}",
                details={"error": str(e)},
                timestamp=timestamp,
                execution_time_ms=0
            ))
        
        # Check memory usage
        start_time = time.time()
        try:
            memory = psutil.virtual_memory()
            execution_time = int((time.time() - start_time) * 1000)
            
            if memory.percent < 80:
                status = "healthy"
                message = f"Memory usage normal ({memory.percent:.1f}%)"
                remediation = None
            elif memory.percent < 95:
                status = "warning"
                message = f"High memory usage ({memory.percent:.1f}%)"
                remediation = "Consider scaling or optimizing memory usage"
            else:
                status = "critical"
                message = f"Critical memory usage ({memory.percent:.1f}%)"
                remediation = "Immediate action required - risk of OOM"
            
            results.append(HealthCheckResult(
                name="memory_usage",
                status=status,
                message=message,
                details={
                    "memory_percent": memory.percent,
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "memory_available_gb": round(memory.available / (1024**3), 2)
                },
                timestamp=timestamp,
                execution_time_ms=execution_time,
                remediation_suggested=remediation
            ))
        except Exception as e:
            results.append(HealthCheckResult(
                name="memory_usage",
                status="unknown",
                message=f"Could not check memory usage: {str(e)}",
                details={"error": str(e)},
                timestamp=timestamp,
                execution_time_ms=0
            ))
        
        # Check disk usage
        start_time = time.time()
        try:
            disk = psutil.disk_usage('/')
            execution_time = int((time.time() - start_time) * 1000)
            
            disk_percent = (disk.used / disk.total) * 100
            
            if disk_percent < 80:
                status = "healthy"
                message = f"Disk usage normal ({disk_percent:.1f}%)"
                remediation = None
            elif disk_percent < 95:
                status = "warning"
                message = f"High disk usage ({disk_percent:.1f}%)"
                remediation = "Consider cleaning up disk space"
            else:
                status = "critical"
                message = f"Critical disk usage ({disk_percent:.1f}%)"
                remediation = "Immediate cleanup required - disk nearly full"
            
            results.append(HealthCheckResult(
                name="disk_usage",
                status=status,
                message=message,
                details={
                    "disk_percent": round(disk_percent, 1),
                    "disk_total_gb": round(disk.total / (1024**3), 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                timestamp=timestamp,
                execution_time_ms=execution_time,
                remediation_suggested=remediation
            ))
        except Exception as e:
            results.append(HealthCheckResult(
                name="disk_usage",
                status="unknown",
                message=f"Could not check disk usage: {str(e)}",
                details={"error": str(e)},
                timestamp=timestamp,
                execution_time_ms=0
            ))
        
        return results


class SystemHealthMonitor:
    """Main system health monitoring class."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.service_checker = ServiceHealthChecker()
        self.dependency_checker = DependencyChecker(self.project_root)
        self.resource_checker = SystemResourceChecker()
        
        # Default services to monitor
        self.services = {
            "stratmaster_api": "http://127.0.0.1:8080/healthz",
            "research_mcp": "http://127.0.0.1:8081/health"
        }
        
        # Health history for trend analysis
        self.health_history = []
        self.max_history = 100
    
    def run_all_checks(self) -> SystemHealthReport:
        """Run all health checks and return comprehensive report."""
        logger.info("Starting comprehensive health check...")
        start_time = time.time()
        
        all_checks = []
        
        # Run checks in parallel for better performance
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all check tasks
            future_to_check = {}
            
            # Service checks
            for service_name, url in self.services.items():
                future = executor.submit(self.service_checker.check_http_service, service_name, url)
                future_to_check[future] = f"service_{service_name}"
            
            # Dependency checks
            future = executor.submit(self.dependency_checker.check_dependency_freshness)
            future_to_check[future] = "dependency_freshness"
            
            future = executor.submit(self.dependency_checker.check_security_vulnerabilities)
            future_to_check[future] = "security_vulnerabilities"
            
            # System resource checks
            future = executor.submit(self.resource_checker.check_system_resources)
            future_to_check[future] = "system_resources"
            
            # Collect results
            for future in as_completed(future_to_check, timeout=120):
                check_name = future_to_check[future]
                try:
                    result = future.result()
                    if isinstance(result, list):
                        all_checks.extend(result)
                    else:
                        all_checks.append(result)
                except Exception as e:
                    logger.error(f"Check {check_name} failed: {e}")
                    all_checks.append(HealthCheckResult(
                        name=check_name,
                        status="critical",
                        message=f"Check execution failed: {str(e)}",
                        details={"error": str(e)},
                        timestamp=datetime.now(UTC).isoformat(),
                        execution_time_ms=0
                    ))
        
        # Generate summary
        summary = {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}
        recommendations = []
        
        for check in all_checks:
            summary[check.status] = summary.get(check.status, 0) + 1
            if check.remediation_suggested:
                recommendations.append(f"{check.name}: {check.remediation_suggested}")
        
        # Determine overall status
        if summary.get("critical", 0) > 0:
            overall_status = "critical"
        elif summary.get("warning", 0) > 0:
            overall_status = "warning"
        elif summary.get("unknown", 0) > 0:
            overall_status = "unknown"
        else:
            overall_status = "healthy"
        
        # Environment info
        environment_info = {
            "hostname": os.uname().nodename if hasattr(os, 'uname') else "unknown",
            "python_version": sys.version,
            "platform": sys.platform,
            "github_actions": os.getenv('GITHUB_ACTIONS', 'false'),
            "ci_environment": os.getenv('CI', 'false'),
            "check_duration_ms": int((time.time() - start_time) * 1000)
        }
        
        report = SystemHealthReport(
            timestamp=datetime.now(UTC).isoformat(),
            overall_status=overall_status,
            checks=all_checks,
            summary=summary,
            recommendations=recommendations,
            environment_info=environment_info
        )
        
        # Store in history
        self.health_history.append(report)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        logger.info(f"Health check completed in {environment_info['check_duration_ms']}ms")
        logger.info(f"Overall status: {overall_status}")
        logger.info(f"Summary: {summary}")
        
        return report
    
    def save_report(self, report: SystemHealthReport, output_path: Path):
        """Save health report to file."""
        with open(output_path, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        logger.info(f"Health report saved to {output_path}")
    
    def monitor_continuously(self, interval_seconds: int = 60, max_iterations: int = None):
        """Run continuous monitoring with specified interval."""
        logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")
        
        iteration = 0
        try:
            while max_iterations is None or iteration < max_iterations:
                report = self.run_all_checks()
                
                # Alert on critical issues
                if report.overall_status == "critical":
                    self._handle_critical_alert(report)
                
                # Save periodic reports
                if iteration % 10 == 0:  # Save every 10 iterations
                    report_path = Path(f"/tmp/health_report_{int(time.time())}.json")
                    self.save_report(report, report_path)
                
                iteration += 1
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
    
    def _handle_critical_alert(self, report: SystemHealthReport):
        """Handle critical health alerts."""
        logger.critical(f"CRITICAL HEALTH ALERT: {report.overall_status}")
        critical_checks = [c for c in report.checks if c.status == "critical"]
        
        for check in critical_checks:
            logger.critical(f"  - {check.name}: {check.message}")
            if check.remediation_suggested:
                logger.critical(f"    Remediation: {check.remediation_suggested}")


def main():
    parser = argparse.ArgumentParser(description="StratMaster System Health Monitor")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Run health checks')
    check_parser.add_argument('--all', action='store_true', help='Run all checks')
    check_parser.add_argument('--services-only', action='store_true', help='Check services only')
    check_parser.add_argument('--dependencies-only', action='store_true', help='Check dependencies only')
    check_parser.add_argument('--resources-only', action='store_true', help='Check system resources only')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Continuous monitoring')
    monitor_parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    monitor_parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    monitor_parser.add_argument('--max-iterations', type=int, help='Maximum number of iterations')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate health report')
    report_parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format')
    report_parser.add_argument('--output', type=Path, help='Output file (default: stdout)')
    
    # Heal command (placeholder for future self-healing features)
    heal_parser = subparsers.add_parser('heal', help='Self-healing actions')
    heal_parser.add_argument('--auto', action='store_true', help='Automatic healing')
    heal_parser.add_argument('--dry-run', action='store_true', help='Show what would be healed')
    
    # Common arguments
    parser.add_argument('--project-root', type=Path, help='Project root directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create monitor
    monitor = SystemHealthMonitor(project_root=args.project_root)
    
    try:
        if args.command == 'check':
            report = monitor.run_all_checks()
            
            if hasattr(args, 'output') and args.output:
                monitor.save_report(report, args.output)
            else:
                print(json.dumps(asdict(report), indent=2, default=str))
            
            # Exit with appropriate code
            return 0 if report.overall_status in ["healthy", "warning"] else 1
            
        elif args.command == 'monitor':
            if args.daemon:
                logger.info("Daemon mode not yet implemented")
                return 1
            else:
                monitor.monitor_continuously(args.interval, args.max_iterations)
                return 0
                
        elif args.command == 'report':
            report = monitor.run_all_checks()
            
            if args.format == 'json':
                output = json.dumps(asdict(report), indent=2, default=str)
            else:
                # Simple text format
                output = f"Health Report - {report.timestamp}\n"
                output += f"Overall Status: {report.overall_status.upper()}\n\n"
                output += f"Summary: {report.summary}\n\n"
                output += "Checks:\n"
                for check in report.checks:
                    output += f"  - {check.name}: {check.status} - {check.message}\n"
                if report.recommendations:
                    output += "\nRecommendations:\n"
                    for rec in report.recommendations:
                        output += f"  - {rec}\n"
            
            if hasattr(args, 'output') and args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                logger.info(f"Report saved to {args.output}")
            else:
                print(output)
            
            return 0
            
        elif args.command == 'heal':
            logger.info("Self-healing functionality not yet implemented")
            if args.auto:
                logger.info("Would perform automatic healing")
            if args.dry_run:
                logger.info("Dry run mode - would show healing actions")
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