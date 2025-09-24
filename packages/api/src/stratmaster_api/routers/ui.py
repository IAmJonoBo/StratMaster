"""
Sprint 6: UX System
Modern web components framework with tri-pane workspace.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui", tags=["ui"])


class HardwareProfile(BaseModel):
    """Hardware detection profile for optimal UX configuration."""
    device_type: str  # mobile, tablet, desktop
    screen_width: int
    screen_height: int
    memory_gb: float | None = None
    connection_speed: str | None = None  # slow, fast, unknown


class UIConfig(BaseModel):
    """UI configuration based on hardware profile."""
    components: str  # cdn, local, minimal
    theme: str  # light, dark, auto
    performance_mode: str  # high, medium, low
    enable_animations: bool
    enable_offline: bool
    max_items_per_page: int


class WorkspaceLayout(BaseModel):
    """Tri-pane workspace layout configuration."""
    brief_width: str = "30%"
    evidence_width: str = "40%"
    plan_width: str = "30%"
    show_brief: bool = True
    show_evidence: bool = True
    show_plan: bool = True
    responsive_breakpoint: int = 768


def detect_hardware_profile(user_agent: str, screen_info: dict | None = None) -> HardwareProfile:
    """Detect hardware profile from user agent and screen info."""
    # Simple user agent parsing for demo
    user_agent_lower = user_agent.lower()
    
    # Default values
    device_type = "desktop"
    screen_width = 1920
    screen_height = 1080
    
    # Mobile detection
    if any(mobile in user_agent_lower for mobile in ["mobile", "android", "iphone", "ipod"]):
        device_type = "mobile"
        screen_width = 375
        screen_height = 667
    
    # Tablet detection
    elif any(tablet in user_agent_lower for tablet in ["tablet", "ipad"]):
        device_type = "tablet"
        screen_width = 768
        screen_height = 1024
    
    # Override with actual screen info if provided
    if screen_info:
        screen_width = screen_info.get("width", screen_width)
        screen_height = screen_info.get("height", screen_height)
    
    return HardwareProfile(
        device_type=device_type,
        screen_width=screen_width,
        screen_height=screen_height
    )


def generate_ui_config(profile: HardwareProfile) -> UIConfig:
    """Generate optimal UI configuration for hardware profile."""
    if profile.device_type == "mobile":
        return UIConfig(
            components="cdn",  # Use CDN for mobile to reduce bundle size
            theme="auto",
            performance_mode="high",  # Optimize for mobile
            enable_animations=False,  # Reduce animations for performance
            enable_offline=True,  # Mobile users need offline support
            max_items_per_page=10
        )
    elif profile.device_type == "tablet":
        return UIConfig(
            components="cdn",
            theme="auto", 
            performance_mode="medium",
            enable_animations=True,
            enable_offline=True,
            max_items_per_page=20
        )
    else:  # desktop
        return UIConfig(
            components="local",  # Desktop can handle local components
            theme="light",
            performance_mode="low",  # Desktop has more resources
            enable_animations=True,
            enable_offline=False,  # Desktop likely has stable connection
            max_items_per_page=50
        )


def generate_workspace_layout(profile: HardwareProfile) -> WorkspaceLayout:
    """Generate workspace layout based on hardware profile."""
    if profile.device_type == "mobile":
        # Mobile: Stack vertically, hide some panes by default
        return WorkspaceLayout(
            brief_width="100%",
            evidence_width="100%",
            plan_width="100%",
            show_brief=True,
            show_evidence=False,  # Hidden by default on mobile
            show_plan=True,
            responsive_breakpoint=480
        )
    elif profile.device_type == "tablet":
        # Tablet: Two-pane layout
        return WorkspaceLayout(
            brief_width="50%",
            evidence_width="50%",
            plan_width="100%",
            show_brief=True,
            show_evidence=True,
            show_plan=True,
            responsive_breakpoint=768
        )
    else:
        # Desktop: Full tri-pane
        return WorkspaceLayout(
            brief_width="25%",
            evidence_width="45%",
            plan_width="30%",
            show_brief=True,
            show_evidence=True,
            show_plan=True,
            responsive_breakpoint=1200
        )


def generate_shoelace_html(config: UIConfig, layout: WorkspaceLayout) -> str:
    """Generate Shoelace-based HTML for the workspace."""
    
    # CDN or local Shoelace resources
    if config.components == "cdn":
        shoelace_css = 'https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.15.1/cdn/themes/light.css'
        shoelace_js = 'https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.15.1/cdn/shoelace-autoloader.js'
    else:
        shoelace_css = '/static/shoelace/themes/light.css'
        shoelace_js = '/static/shoelace/shoelace-autoloader.js'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StratMaster - Strategy Workspace</title>
    <link rel="stylesheet" href="{shoelace_css}">
    <script type="module" src="{shoelace_js}"></script>
    <script src="https://cdn.jsdelivr.net/npm/@open-props/open-props"></script>
    
    <style>
        :root {{
            --workspace-brief-width: {layout.brief_width};
            --workspace-evidence-width: {layout.evidence_width};
            --workspace-plan-width: {layout.plan_width};
        }}
        
        body {{
            font-family: var(--sl-font-sans);
            margin: 0;
            padding: 0;
            background: var(--sl-color-neutral-50);
        }}
        
        .workspace-container {{
            display: flex;
            height: 100vh;
            gap: var(--sl-spacing-small);
            padding: var(--sl-spacing-small);
        }}
        
        .workspace-pane {{
            background: white;
            border: 1px solid var(--sl-color-neutral-200);
            border-radius: var(--sl-border-radius-medium);
            padding: var(--sl-spacing-medium);
            overflow-y: auto;
        }}
        
        .brief-pane {{
            width: var(--workspace-brief-width);
            min-width: 250px;
        }}
        
        .evidence-pane {{
            width: var(--workspace-evidence-width);
            min-width: 300px;
        }}
        
        .plan-pane {{
            width: var(--workspace-plan-width);
            min-width: 250px;
        }}
        
        .pane-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--sl-spacing-medium);
            padding-bottom: var(--sl-spacing-small);
            border-bottom: 1px solid var(--sl-color-neutral-200);
        }}
        
        .pane-title {{
            font-size: var(--sl-font-size-large);
            font-weight: var(--sl-font-weight-semibold);
            color: var(--sl-color-neutral-900);
        }}
        
        @media (max-width: {layout.responsive_breakpoint}px) {{
            .workspace-container {{
                flex-direction: column;
                height: auto;
            }}
            
            .workspace-pane {{
                width: 100% !important;
                min-height: 300px;
            }}
            
            .brief-pane {{ {"order: 1;" if layout.show_brief else "display: none;"} }}
            .evidence-pane {{ {"order: 2;" if layout.show_evidence else "display: none;"} }}
            .plan-pane {{ {"order: 3;" if layout.show_plan else "display: none;"} }}
        }}
        
        {"/* Disable animations for performance */" if not config.enable_animations else ""}
        {"* { animation-duration: 0s !important; transition-duration: 0s !important; }" if not config.enable_animations else ""}
    </style>
</head>
<body>
    <div class="workspace-container">
        <!-- Brief Pane -->
        {"" if not layout.show_brief else '''
        <div class="workspace-pane brief-pane">
            <div class="pane-header">
                <div class="pane-title">
                    <sl-icon name="file-text"></sl-icon>
                    Brief
                </div>
                <sl-button-group>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="plus"></sl-icon>
                        New
                    </sl-button>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="upload"></sl-icon>
                        Import
                    </sl-button>
                </sl-button-group>
            </div>
            
            <sl-card class="brief-card">
                <div slot="header">
                    <sl-badge variant="primary">Draft</sl-badge>
                    Strategy Brief
                </div>
                
                <sl-textarea 
                    placeholder="Describe your strategic challenge..."
                    rows="4"
                    resize="vertical">
                </sl-textarea>
                
                <sl-divider></sl-divider>
                
                <sl-details summary="Success Metrics">
                    <sl-input placeholder="Add a success metric..."></sl-input>
                    <sl-button size="small" variant="text" class="add-metric-btn">
                        <sl-icon slot="prefix" name="plus"></sl-icon>
                        Add Metric
                    </sl-button>
                </sl-details>
                
                <sl-details summary="Assumptions">
                    <sl-alert variant="neutral" open>
                        <sl-icon slot="icon" name="info-circle"></sl-icon>
                        Add your key assumptions to validate through research.
                    </sl-alert>
                </sl-details>
                
                <div slot="footer">
                    <sl-button variant="primary" size="small">
                        <sl-icon slot="prefix" name="play"></sl-icon>
                        Start Research
                    </sl-button>
                </div>
            </sl-card>
        </div>
        '''}
        
        <!-- Evidence Pane -->
        {"" if not layout.show_evidence else '''
        <div class="workspace-pane evidence-pane">
            <div class="pane-header">
                <div class="pane-title">
                    <sl-icon name="search"></sl-icon>
                    Evidence
                </div>
                <sl-button-group>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="funnel"></sl-icon>
                        Filter
                    </sl-button>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="arrow-down-up"></sl-icon>
                        Sort
                    </sl-button>
                </sl-button-group>
            </div>
            
            <sl-tab-group>
                <sl-tab slot="nav" panel="claims">Claims</sl-tab>
                <sl-tab slot="nav" panel="sources">Sources</sl-tab>
                <sl-tab slot="nav" panel="debates">Debates</sl-tab>
                
                <sl-tab-panel name="claims">
                    <div class="evidence-list">
                        <sl-card class="evidence-item">
                            <div class="evidence-header">
                                <sl-badge variant="success">High Confidence</sl-badge>
                                <sl-rating value="4" readonly></sl-rating>
                            </div>
                            <p>Market demand for premium features has increased 40% year-over-year.</p>
                            <div class="evidence-footer">
                                <sl-tag size="small">Market Research</sl-tag>
                                <sl-tag size="small">Q4 2024</sl-tag>
                            </div>
                        </sl-card>
                        
                        <sl-card class="evidence-item">
                            <div class="evidence-header">
                                <sl-badge variant="warning">Medium Confidence</sl-badge>
                                <sl-rating value="3" readonly></sl-rating>
                            </div>
                            <p>Customer acquisition costs are stabilizing in target segments.</p>
                            <div class="evidence-footer">
                                <sl-tag size="small">Analytics</sl-tag>
                                <sl-tag size="small">Current</sl-tag>
                            </div>
                        </sl-card>
                    </div>
                </sl-tab-panel>
                
                <sl-tab-panel name="sources">
                    <sl-alert variant="neutral" open>
                        <sl-icon slot="icon" name="database"></sl-icon>
                        Sources will appear here as research progresses.
                    </sl-alert>
                </sl-tab-panel>
                
                <sl-tab-panel name="debates">
                    <sl-alert variant="neutral" open>
                        <sl-icon slot="icon" name="chat-bubble"></sl-icon>
                        AI debates and expert evaluations will appear here.
                    </sl-alert>
                </sl-tab-panel>
            </sl-tab-group>
        </div>
        '''}
        
        <!-- Plan Pane -->
        {"" if not layout.show_plan else '''
        <div class="workspace-pane plan-pane">
            <div class="pane-header">
                <div class="pane-title">
                    <sl-icon name="list-check"></sl-icon>
                    Plan
                </div>
                <sl-button-group>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="download"></sl-icon>
                        Export
                    </sl-button>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="share"></sl-icon>
                        Share
                    </sl-button>
                </sl-button-group>
            </div>
            
            <sl-card>
                <div slot="header">Recommended Actions</div>
                
                <sl-details summary="🎯 High Priority" open>
                    <sl-checkbox>Validate premium pricing hypothesis with A/B test</sl-checkbox>
                    <sl-checkbox>Conduct customer interviews (n=20)</sl-checkbox>
                    <sl-checkbox>Analyze competitor premium offerings</sl-checkbox>
                </sl-details>
                
                <sl-details summary="📊 Medium Priority">
                    <sl-checkbox>Review internal metrics and dashboards</sl-checkbox>
                    <sl-checkbox>Survey existing customer base</sl-checkbox>
                </sl-details>
                
                <sl-details summary="🔍 Research Phase">
                    <sl-progress-bar value="65" label="Research Progress"></sl-progress-bar>
                    <sl-badge variant="primary">3 of 5 tasks complete</sl-badge>
                </sl-details>
                
                <div slot="footer">
                    <sl-button-group>
                        <sl-button variant="neutral" size="small">Save Draft</sl-button>
                        <sl-button variant="primary" size="small">
                            <sl-icon slot="prefix" name="check-circle"></sl-icon>
                            Approve Plan
                        </sl-button>
                    </sl-button-group>
                </div>
            </sl-card>
            
            <sl-card style="margin-top: var(--sl-spacing-medium);">
                <div slot="header">Export Options</div>
                
                <sl-button-group>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="file-pdf"></sl-icon>
                        PDF Report
                    </sl-button>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="trello"></sl-icon>
                        Trello
                    </sl-button>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="notion"></sl-icon>
                        Notion
                    </sl-button>
                    <sl-button size="small" variant="text">
                        <sl-icon slot="prefix" name="jira"></sl-icon>
                        Jira
                    </sl-button>
                </sl-button-group>
            </sl-card>
        </div>
        '''}
    </div>
    
    <script>
        // Basic interactivity
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('StratMaster Workspace initialized');
            console.log('Device type: {config.performance_mode}');
            console.log('Performance mode: {config.performance_mode}');
            
            // PWA registration for offline support
            {"" if not config.enable_offline else """
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js')
                    .then(reg => console.log('Service Worker registered'))
                    .catch(err => console.log('Service Worker registration failed'));
            }
            """}
        }});
    </script>
</body>
</html>"""
    
    return html


@router.get("/hardware-detection")
async def hardware_detection_wizard() -> HTMLResponse:
    """Hardware detection wizard for optimal UX configuration."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StratMaster - Hardware Detection</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.15.1/cdn/themes/light.css">
    <script type="module" src="https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.15.1/cdn/shoelace-autoloader.js"></script>
    
    <style>
        body {
            font-family: var(--sl-font-sans);
            margin: 0;
            padding: var(--sl-spacing-large);
            background: var(--sl-color-neutral-50);
        }
        
        .wizard-container {
            max-width: 600px;
            margin: 0 auto;
        }
        
        .detection-card {
            margin-bottom: var(--sl-spacing-medium);
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <sl-card class="detection-card">
            <div slot="header">
                <h2>🔧 Hardware Detection Wizard</h2>
                <p>We're optimizing StratMaster for your device...</p>
            </div>
            
            <sl-progress-bar value="100" label="Detection Complete"></sl-progress-bar>
            
            <div style="margin: var(--sl-spacing-medium) 0;">
                <sl-details summary="Detected Configuration" open>
                    <dl>
                        <dt><strong>Device Type:</strong></dt>
                        <dd id="device-type">Detecting...</dd>
                        
                        <dt><strong>Screen Resolution:</strong></dt>
                        <dd id="screen-resolution">Detecting...</dd>
                        
                        <dt><strong>Memory:</strong></dt>
                        <dd id="memory">Detecting...</dd>
                        
                        <dt><strong>Connection:</strong></dt>
                        <dd id="connection">Detecting...</dd>
                    </dl>
                </sl-details>
                
                <sl-details summary="Recommended Settings">
                    <div id="recommendations">Loading recommendations...</div>
                </sl-details>
            </div>
            
            <div slot="footer">
                <sl-button-group>
                    <sl-button variant="neutral">Customize Settings</sl-button>
                    <sl-button variant="primary" id="launch-workspace">
                        <sl-icon slot="prefix" name="rocket"></sl-icon>
                        Launch Workspace
                    </sl-button>
                </sl-button-group>
            </div>
        </sl-card>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', async function() {
            // Detect hardware capabilities
            const screen = window.screen;
            const devicePixelRatio = window.devicePixelRatio || 1;
            
            // Device type detection
            const userAgent = navigator.userAgent;
            let deviceType = 'desktop';
            if (/Mobile|Android|iPhone|iPod/.test(userAgent)) {
                deviceType = 'mobile';
            } else if (/Tablet|iPad/.test(userAgent)) {
                deviceType = 'tablet';
            }
            
            // Memory detection (if available)
            const memory = navigator.deviceMemory || 'Unknown';
            
            // Connection detection (if available)
            const connection = navigator.connection;
            let connectionSpeed = 'Unknown';
            if (connection) {
                if (connection.effectiveType === '4g' || connection.downlink > 10) {
                    connectionSpeed = 'Fast';
                } else if (connection.effectiveType === '3g') {
                    connectionSpeed = 'Medium';
                } else {
                    connectionSpeed = 'Slow';
                }
            }
            
            // Update UI
            document.getElementById('device-type').textContent = deviceType.charAt(0).toUpperCase() + deviceType.slice(1);
            document.getElementById('screen-resolution').textContent = `${screen.width}x${screen.height} (${devicePixelRatio}x DPI)`;
            document.getElementById('memory').textContent = memory === 'Unknown' ? 'Unknown' : `${memory} GB`;
            document.getElementById('connection').textContent = connectionSpeed;
            
            // Generate recommendations
            let recommendations = [];
            if (deviceType === 'mobile') {
                recommendations = [
                    '📱 Mobile-optimized layout enabled',
                    '⚡ Performance mode: High (reduced animations)',
                    '📶 Offline support enabled',
                    '🎨 CDN components for faster loading'
                ];
            } else if (deviceType === 'tablet') {
                recommendations = [
                    '📱 Two-pane layout optimized for tablet',
                    '⚡ Performance mode: Medium',
                    '🎨 Enhanced touch interactions',
                    '📶 Smart caching enabled'
                ];
            } else {
                recommendations = [
                    '🖥️ Full tri-pane workspace layout',
                    '⚡ Performance mode: Full features enabled',
                    '🎨 Rich animations and transitions',
                    '💾 Local component loading'
                ];
            }
            
            document.getElementById('recommendations').innerHTML = 
                '<ul>' + recommendations.map(rec => `<li>${rec}</li>`).join('') + '</ul>';
            
            // Launch workspace
            document.getElementById('launch-workspace').addEventListener('click', () => {
                const profile = {
                    device_type: deviceType,
                    screen_width: screen.width,
                    screen_height: screen.height,
                    memory_gb: memory !== 'Unknown' ? memory : null,
                    connection_speed: connectionSpeed.toLowerCase()
                };
                
                // Redirect to workspace with profile
                window.location.href = '/ui/workspace?' + new URLSearchParams({
                    profile: JSON.stringify(profile)
                });
            });
        });
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html)


@router.get("/workspace")
async def workspace_ui() -> HTMLResponse:
    """Main tri-pane workspace UI - Sprint 6."""
    
    # For demo purposes, create a default profile
    # In production, this would come from the query parameters or user session
    default_profile = HardwareProfile(
        device_type="desktop",
        screen_width=1920,
        screen_height=1080
    )
    
    config = generate_ui_config(default_profile)
    layout = generate_workspace_layout(default_profile)
    
    html = generate_shoelace_html(config, layout)
    return HTMLResponse(content=html)


@router.post("/config")
async def generate_ui_configuration(profile: HardwareProfile) -> dict[str, Any]:
    """Generate UI configuration based on hardware profile - Sprint 6."""
    config = generate_ui_config(profile)
    layout = generate_workspace_layout(profile)
    
    return {
        "profile": profile.model_dump(),
        "config": config.model_dump(),
        "layout": layout.model_dump(),
        "first_contentful_paint_target": "< 2s",
        "lighthouse_score_target": "> 90"
    }