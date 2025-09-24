#!/usr/bin/env python3
"""
StratMaster DevOps Dashboard

Real-time system monitoring and management dashboard with:
- Live health status monitoring
- Dependency management interface
- Self-healing system controls
- Performance metrics visualization
- Automated recovery triggers

Usage:
    python scripts/devops_dashboard.py --port 8090
    python scripts/devops_dashboard.py --monitor-only
    python scripts/devops_dashboard.py --export-metrics
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DevOpsDashboard:
    """DevOps dashboard for StratMaster system monitoring."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.health_data = {}
        self.metrics_history = []
        self.max_history = 100
        
        # System state
        self.services_status = {}
        self.last_health_check = None
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Scripts paths
        self.health_monitor = self.project_root / "scripts" / "system_health_monitor.py"
        self.self_healing = self.project_root / "scripts" / "self_healing.py"
        self.robust_installer = self.project_root / "scripts" / "robust_installer.py"
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            # Run health check
            result = subprocess.run(
                [sys.executable, str(self.health_monitor), "check", "--all"],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                health_report = json.loads(result.stdout)
                self.health_data = health_report
                self.last_health_check = datetime.now(UTC).isoformat()
                
                # Update services status
                for check in health_report.get("checks", []):
                    if check["name"].endswith("_http"):
                        service_name = check["name"].replace("_http", "")
                        self.services_status[service_name] = {
                            "status": check["status"],
                            "message": check["message"],
                            "last_updated": check["timestamp"]
                        }
                
                return {
                    "status": "success",
                    "data": health_report,
                    "last_updated": self.last_health_check
                }
            else:
                return {
                    "status": "error",
                    "message": "Health check failed",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Health check timed out"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Health check error: {str(e)}"
            }
    
    def get_dependency_status(self) -> Dict[str, Any]:
        """Get dependency status information."""
        try:
            # Check dependency freshness
            dep_script = self.project_root / "scripts" / "dependency_upgrade.py"
            result = subprocess.run(
                [sys.executable, str(dep_script), "check", "--dry-run"],
                capture_output=True, text=True, timeout=60
            )
            
            dependency_info = {
                "last_check": datetime.now(UTC).isoformat(),
                "status": "healthy" if result.returncode == 0 else "warning",
                "output": result.stdout,
                "updates_available": "updates available" in result.stdout.lower()
            }
            
            # Get environment validation
            if self.robust_installer.exists():
                env_result = subprocess.run(
                    [sys.executable, str(self.robust_installer), "validate-environment"],
                    capture_output=True, text=True, timeout=30
                )
                
                if env_result.returncode == 0:
                    try:
                        env_data = json.loads(env_result.stdout)
                        dependency_info["environment"] = env_data
                    except json.JSONDecodeError:
                        dependency_info["environment"] = {"error": "Could not parse environment data"}
            
            return {
                "status": "success",
                "data": dependency_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Dependency check error: {str(e)}"
            }
    
    def trigger_healing(self, action: str = "auto") -> Dict[str, Any]:
        """Trigger self-healing action."""
        try:
            if action == "auto":
                cmd = [sys.executable, str(self.self_healing), "analyze", "--auto-heal"]
            elif action == "validate":
                cmd = [sys.executable, str(self.self_healing), "validate-and-heal"]
            elif action == "cleanup":
                cmd = [sys.executable, str(self.self_healing), "recover", "--cleanup"]
            elif action == "deps":
                cmd = [sys.executable, str(self.self_healing), "recover", "--dependencies"]
            elif action == "env":
                cmd = [sys.executable, str(self.self_healing), "recover", "--environment"]
            else:
                return {"status": "error", "message": f"Unknown healing action: {action}"}
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                try:
                    healing_results = json.loads(result.stdout)
                    return {
                        "status": "success",
                        "data": healing_results,
                        "message": "Healing completed successfully"
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "message": "Healing completed",
                        "output": result.stdout
                    }
            else:
                return {
                    "status": "error",
                    "message": "Healing failed",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Healing timed out"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Healing error: {str(e)}"
            }
    
    def create_snapshot(self) -> Dict[str, Any]:
        """Create system snapshot."""
        try:
            result = subprocess.run(
                [sys.executable, str(self.self_healing), "snapshot"],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                snapshot_id = result.stdout.strip().split(": ")[-1]
                return {
                    "status": "success",
                    "snapshot_id": snapshot_id,
                    "message": f"Snapshot created: {snapshot_id}"
                }
            else:
                return {
                    "status": "error",
                    "message": "Snapshot creation failed",
                    "error": result.stderr
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Snapshot error: {str(e)}"
            }
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    status = self.get_system_status()
                    
                    # Store in history
                    self.metrics_history.append({
                        "timestamp": datetime.now(UTC).isoformat(),
                        "status": status
                    })
                    
                    # Keep history size manageable
                    if len(self.metrics_history) > self.max_history:
                        self.metrics_history.pop(0)
                    
                    # Auto-healing on critical issues
                    if (status.get("status") == "success" and 
                        status.get("data", {}).get("overall_status") == "critical"):
                        logger.warning("Critical status detected, triggering auto-healing")
                        healing_result = self.trigger_healing("auto")
                        logger.info(f"Auto-healing result: {healing_result.get('status', 'unknown')}")
                    
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                
                time.sleep(interval)
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info(f"Started system monitoring with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped system monitoring")
    
    def generate_dashboard_html(self) -> str:
        """Generate HTML dashboard."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StratMaster DevOps Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
        }}
        .card h3 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-healthy {{ background-color: #28a745; }}
        .status-warning {{ background-color: #ffc107; }}
        .status-critical {{ background-color: #dc3545; }}
        .status-unknown {{ background-color: #6c757d; }}
        .button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }}
        .button:hover {{
            background: #0056b3;
        }}
        .button.danger {{
            background: #dc3545;
        }}
        .button.danger:hover {{
            background: #c82333;
        }}
        .button.success {{
            background: #28a745;
        }}
        .button.success:hover {{
            background: #218838;
        }}
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .metrics-table th, .metrics-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .metrics-table th {{
            background-color: #f8f9fa;
        }}
        .log-container {{
            max-height: 200px;
            overflow-y: auto;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            font-family: monospace;
            font-size: 12px;
        }}
        .alert {{
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid transparent;
            border-radius: 4px;
        }}
        .alert-danger {{
            color: #721c24;
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }}
        .alert-warning {{
            color: #856404;
            background-color: #fff3cd;
            border-color: #ffeaa7;
        }}
        .alert-success {{
            color: #155724;
            background-color: #d4edda;
            border-color: #c3e6cb;
        }}
    </style>
    <script>
        let autoRefresh = true;
        let refreshInterval = 30000; // 30 seconds
        
        function refreshDashboard() {{
            if (autoRefresh) {{
                location.reload();
            }}
        }}
        
        function toggleAutoRefresh() {{
            autoRefresh = !autoRefresh;
            document.getElementById('autoRefreshBtn').textContent = 
                autoRefresh ? 'Disable Auto-Refresh' : 'Enable Auto-Refresh';
        }}
        
        function triggerAction(action) {{
            const button = document.querySelector(`[onclick="triggerAction('${{action}}')"]`);
            button.disabled = true;
            button.textContent = 'Processing...';
            
            fetch(`/action?type=${{action}}`, {{
                method: 'POST'
            }})
            .then(response => response.json())
            .then(data => {{
                alert(`Action completed: ${{data.message || data.status}}`);
                setTimeout(refreshDashboard, 2000);
            }})
            .catch(error => {{
                alert(`Action failed: ${{error}}`);
            }})
            .finally(() => {{
                button.disabled = false;
                button.textContent = button.getAttribute('data-original-text');
            }});
        }}
        
        window.onload = function() {{
            // Store original button text
            document.querySelectorAll('.button').forEach(btn => {{
                btn.setAttribute('data-original-text', btn.textContent);
            }});
            
            // Set up auto-refresh
            setInterval(refreshDashboard, refreshInterval);
        }};
    </script>
</head>
<body>
    <div class="header">
        <h1>🚀 StratMaster DevOps Dashboard</h1>
        <p>System Health Monitoring & Self-Healing Platform</p>
        <p>Last updated: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
    </div>
    
    <div style="margin-bottom: 20px;">
        <button id="autoRefreshBtn" class="button" onclick="toggleAutoRefresh()">Disable Auto-Refresh</button>
        <button class="button" onclick="location.reload()">🔄 Refresh Now</button>
        <button class="button success" onclick="triggerAction('health')">🩺 Health Check</button>
        <button class="button" onclick="triggerAction('snapshot')">📸 Create Snapshot</button>
    </div>

    {self._generate_status_cards()}

    <div class="dashboard-grid">
        {self._generate_actions_card()}
        {self._generate_metrics_card()}
        {self._generate_services_card()}
        {self._generate_logs_card()}
    </div>
</body>
</html>'''
    
    def _generate_status_cards(self) -> str:
        """Generate status overview cards."""
        system_status = self.get_system_status()
        
        if system_status.get("status") == "success":
            data = system_status.get("data", {})
            overall_status = data.get("overall_status", "unknown")
            summary = data.get("summary", {})
            
            status_class = f"status-{overall_status}"
            
            alert_class = {
                "healthy": "alert-success",
                "warning": "alert-warning",
                "critical": "alert-danger"
            }.get(overall_status, "alert-warning")
            
            return f'''
            <div class="{alert_class} alert">
                <h4><span class="status-indicator {status_class}"></span>System Status: {overall_status.upper()}</h4>
                <p>Health Checks: {summary.get("healthy", 0)} healthy, {summary.get("warning", 0)} warnings, {summary.get("critical", 0)} critical</p>
                <p>Last Check: {system_status.get("last_updated", "Never")}</p>
            </div>
            '''
        else:
            return '''
            <div class="alert alert-danger">
                <h4><span class="status-indicator status-critical"></span>System Status: ERROR</h4>
                <p>Unable to retrieve system status</p>
            </div>
            '''
    
    def _generate_actions_card(self) -> str:
        """Generate actions control card."""
        return '''
        <div class="card">
            <h3>🛠️ Self-Healing Actions</h3>
            <button class="button success" onclick="triggerAction('heal-auto')">🚑 Auto Heal</button>
            <button class="button" onclick="triggerAction('heal-validate')">✅ Validate & Heal</button>
            <button class="button" onclick="triggerAction('heal-cleanup')">🧹 Cleanup</button>
            <button class="button" onclick="triggerAction('heal-deps')">📦 Fix Dependencies</button>
            <button class="button danger" onclick="triggerAction('heal-env')">🔄 Rebuild Environment</button>
            <button class="button danger" onclick="triggerAction('heal-rollback')">⏪ Rollback</button>
        </div>
        '''
    
    def _generate_metrics_card(self) -> str:
        """Generate system metrics card."""
        system_status = self.get_system_status()
        
        if system_status.get("status") == "success":
            data = system_status.get("data", {})
            checks = data.get("checks", [])
            
            metrics_html = '<table class="metrics-table"><tr><th>Component</th><th>Status</th><th>Details</th></tr>'
            
            for check in checks[:10]:  # Show first 10 checks
                status_class = f"status-{check.get('status', 'unknown')}"
                metrics_html += f'''
                <tr>
                    <td>{check.get("name", "Unknown")}</td>
                    <td><span class="status-indicator {status_class}"></span>{check.get("status", "unknown").upper()}</td>
                    <td>{check.get("message", "No details")[:50]}...</td>
                </tr>
                '''
            
            metrics_html += '</table>'
        else:
            metrics_html = '<p>No metrics available</p>'
        
        return f'''
        <div class="card">
            <h3>📊 System Metrics</h3>
            {metrics_html}
        </div>
        '''
    
    def _generate_services_card(self) -> str:
        """Generate services status card."""
        services_html = '<table class="metrics-table"><tr><th>Service</th><th>Status</th><th>Last Updated</th></tr>'
        
        if self.services_status:
            for service, info in self.services_status.items():
                status_class = f"status-{info.get('status', 'unknown')}"
                services_html += f'''
                <tr>
                    <td>{service}</td>
                    <td><span class="status-indicator {status_class}"></span>{info.get("status", "unknown").upper()}</td>
                    <td>{info.get("last_updated", "Never")[:19]}</td>
                </tr>
                '''
        else:
            services_html += '<tr><td colspan="3">No service data available</td></tr>'
        
        services_html += '</table>'
        
        return f'''
        <div class="card">
            <h3>🏗️ Services Status</h3>
            {services_html}
        </div>
        '''
    
    def _generate_logs_card(self) -> str:
        """Generate recent logs card."""
        # Get recent healing history
        logs_html = '<div class="log-container">'
        
        if hasattr(self, 'recent_logs') and self.recent_logs:
            for log in self.recent_logs[-10:]:  # Last 10 logs
                logs_html += f'<div>{log}</div>'
        else:
            logs_html += '<div>No recent logs available</div>'
        
        logs_html += '</div>'
        
        return f'''
        <div class="card">
            <h3>📝 Recent Activity</h3>
            {logs_html}
        </div>
        '''


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard."""
    
    def __init__(self, dashboard: DevOpsDashboard):
        self.dashboard = dashboard
        super().__init__()
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/' or parsed_url.path == '/dashboard':
                # Serve dashboard HTML
                html = self.dashboard.generate_dashboard_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
                
            elif parsed_url.path == '/api/status':
                # API endpoint for status
                status = self.dashboard.get_system_status()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode('utf-8'))
                
            elif parsed_url.path == '/api/dependencies':
                # API endpoint for dependencies
                deps = self.dashboard.get_dependency_status()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(deps).encode('utf-8'))
                
            else:
                self.send_error(404)
                
        except Exception as e:
            logger.error(f"GET request error: {e}")
            self.send_error(500)
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/action':
                # Handle action requests
                query_params = parse_qs(parsed_url.query)
                action_type = query_params.get('type', [''])[0]
                
                result = None
                if action_type == 'health':
                    result = self.dashboard.get_system_status()
                elif action_type == 'snapshot':
                    result = self.dashboard.create_snapshot()
                elif action_type.startswith('heal-'):
                    heal_action = action_type.replace('heal-', '')
                    result = self.dashboard.trigger_healing(heal_action)
                else:
                    result = {"status": "error", "message": f"Unknown action: {action_type}"}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            else:
                self.send_error(404)
                
        except Exception as e:
            logger.error(f"POST request error: {e}")
            self.send_error(500)
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


def create_dashboard_handler(dashboard):
    """Create handler with dashboard reference."""
    def handler(*args, **kwargs):
        DashboardHandler.__init__ = lambda self, *a, **kw: BaseHTTPRequestHandler.__init__(self, *a, **kw)
        h = DashboardHandler(dashboard)
        h.__init__ = lambda *a, **kw: None
        return h
    return handler


def main():
    parser = argparse.ArgumentParser(description="StratMaster DevOps Dashboard")
    
    parser.add_argument('--port', type=int, default=8090, help='Dashboard port')
    parser.add_argument('--host', default='127.0.0.1', help='Dashboard host')
    parser.add_argument('--monitor-only', action='store_true', help='Start monitoring without web interface')
    parser.add_argument('--export-metrics', action='store_true', help='Export metrics and exit')
    parser.add_argument('--project-root', type=Path, help='Project root directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create dashboard
    dashboard = DevOpsDashboard(project_root=args.project_root)
    
    try:
        if args.export_metrics:
            # Export current metrics
            status = dashboard.get_system_status()
            deps = dashboard.get_dependency_status()
            
            metrics = {
                "timestamp": datetime.now(UTC).isoformat(),
                "system_status": status,
                "dependency_status": deps
            }
            
            print(json.dumps(metrics, indent=2))
            return 0
            
        elif args.monitor_only:
            # Start monitoring without web interface
            dashboard.start_monitoring()
            logger.info("Monitoring started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                dashboard.stop_monitoring()
            return 0
            
        else:
            # Start web dashboard
            dashboard.start_monitoring()
            
            # Create custom handler
            def handler(*args, **kwargs):
                h = DashboardHandler(dashboard)
                BaseHTTPRequestHandler.__init__(h, *args, **kwargs)
                return h
            
            httpd = HTTPServer((args.host, args.port), lambda *a, **kw: DashboardHandler(dashboard))
            
            logger.info(f"Dashboard starting on http://{args.host}:{args.port}")
            logger.info("Press Ctrl+C to stop")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                httpd.shutdown()
                dashboard.stop_monitoring()
                
            return 0
            
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())