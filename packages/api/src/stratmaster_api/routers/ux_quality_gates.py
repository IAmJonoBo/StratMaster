"""UX Quality Gates API endpoints for accessibility monitoring and reporting.

Provides administrative endpoints for:
- WCAG 2.1 AA compliance monitoring
- Lighthouse audit results and trends
- Responsive design validation
- Automated accessibility testing
- Quality gate status and enforcement
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try to import accessibility audit components
try:
    import sys
    sys.path.append('scripts')
    from accessibility_audit import AccessibilityQualityGates, LighthouseResult, ResponsiveTestResult
    ACCESSIBILITY_AUDIT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Accessibility audit not available: {e}")
    ACCESSIBILITY_AUDIT_AVAILABLE = False


class AccessibilityAuditRequest(BaseModel):
    """Request for accessibility audit."""
    url: str = "http://localhost:8080"
    include_lighthouse: bool = True
    include_responsive: bool = True
    devices: list[str] = ["mobile", "tablet", "desktop"]
    ci_mode: bool = False


class AccessibilityAuditResponse(BaseModel):
    """Response for accessibility audit."""
    audit_id: str
    status: str
    message: str
    started_at: str


class QualityGateStatus(BaseModel):
    """Quality gate status response."""
    overall_status: str
    accessibility_score: int | None
    performance_score: int | None
    critical_issues: int
    serious_issues: int
    responsive_issues: int
    last_audit: str | None
    quality_gates_passed: bool


class AccessibilityTrend(BaseModel):
    """Accessibility trend data."""
    date: str
    accessibility_score: int
    performance_score: int
    issue_count: dict[str, int]


# Create UX Quality Gates router
router = APIRouter(prefix="/admin/ux", tags=["UX Quality Gates"])


# In-memory audit results storage (would use database in production)
_audit_results: dict[str, dict[str, Any]] = {}
_audit_trends: list[AccessibilityTrend] = []


@router.get("/status")
async def get_ux_quality_status() -> QualityGateStatus:
    """Get current UX quality gate status."""
    if not ACCESSIBILITY_AUDIT_AVAILABLE:
        return QualityGateStatus(
            overall_status="UNAVAILABLE",
            accessibility_score=None,
            performance_score=None,
            critical_issues=0,
            serious_issues=0,
            responsive_issues=0,
            last_audit=None,
            quality_gates_passed=False
        )
    
    # Get latest audit results
    latest_audit = None
    if _audit_results:
        latest_audit = max(_audit_results.items(), key=lambda x: x[1].get("timestamp", ""))
    
    if latest_audit:
        audit_data = latest_audit[1]
        lighthouse_results = audit_data.get("lighthouse_results", [])
        lighthouse_score = lighthouse_results[0].get("accessibility_score") if lighthouse_results else None
        performance_score = lighthouse_results[0].get("performance_score") if lighthouse_results else None
        
        issue_counts = audit_data.get("quality_gates", {}).get("issue_counts", {})
        responsive_results = audit_data.get("responsive_results", [])
        responsive_issues = sum(1 for r in responsive_results if not r.get("passed", True))
        
        return QualityGateStatus(
            overall_status=audit_data.get("overall_status", "UNKNOWN"),
            accessibility_score=lighthouse_score,
            performance_score=performance_score,
            critical_issues=issue_counts.get("critical", 0),
            serious_issues=issue_counts.get("serious", 0),
            responsive_issues=responsive_issues,
            last_audit=audit_data.get("timestamp"),
            quality_gates_passed=audit_data.get("overall_status") == "PASS"
        )
    
    return QualityGateStatus(
        overall_status="NEVER_RUN",
        accessibility_score=None,
        performance_score=None,
        critical_issues=0,
        serious_issues=0,
        responsive_issues=0,
        last_audit=None,
        quality_gates_passed=False
    )


@router.post("/audit", response_model=AccessibilityAuditResponse)
async def run_accessibility_audit(
    request: AccessibilityAuditRequest,
    background_tasks: BackgroundTasks
) -> AccessibilityAuditResponse:
    """Run comprehensive accessibility audit."""
    if not ACCESSIBILITY_AUDIT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Accessibility audit system not available"
        )
    
    audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Start audit in background
    background_tasks.add_task(
        _run_comprehensive_audit,
        audit_id,
        request
    )
    
    return AccessibilityAuditResponse(
        audit_id=audit_id,
        status="STARTED",
        message="Accessibility audit started in background",
        started_at=datetime.now().isoformat()
    )


@router.get("/audit/{audit_id}")
async def get_audit_results(audit_id: str) -> dict[str, Any]:
    """Get results from a specific audit."""
    if audit_id not in _audit_results:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return _audit_results[audit_id]


@router.get("/audits")
async def list_audits(limit: int = Query(10, ge=1, le=100)) -> dict[str, Any]:
    """List recent accessibility audits."""
    sorted_audits = sorted(
        _audit_results.items(),
        key=lambda x: x[1].get("timestamp", ""),
        reverse=True
    )[:limit]
    
    return {
        "audits": [
            {
                "audit_id": audit_id,
                "timestamp": audit_data.get("timestamp"),
                "overall_status": audit_data.get("overall_status"),
                "lighthouse_score": (
                    audit_data.get("lighthouse_results", [{}])[0].get("accessibility_score")
                    if audit_data.get("lighthouse_results") else None
                )
            }
            for audit_id, audit_data in sorted_audits
        ],
        "total": len(_audit_results)
    }


@router.get("/lighthouse")
async def get_lighthouse_results(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """Get Lighthouse audit results and trends."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    recent_audits = [
        audit_data for audit_data in _audit_results.values()
        if (audit_data.get("timestamp") and 
            datetime.fromisoformat(audit_data["timestamp"].replace("Z", "")) >= cutoff_date)
    ]
    
    # Extract Lighthouse trends
    trends = []
    for audit_data in recent_audits:
        lighthouse_results = audit_data.get("lighthouse_results", [])
        if lighthouse_results:
            lighthouse_result = lighthouse_results[0]
            trends.append({
                "timestamp": audit_data["timestamp"],
                "accessibility_score": lighthouse_result.get("accessibility_score", 0),
                "performance_score": lighthouse_result.get("performance_score", 0),
                "best_practices_score": lighthouse_result.get("best_practices_score", 0),
                "seo_score": lighthouse_result.get("seo_score", 0)
            })
    
    # Calculate averages
    if trends:
        avg_accessibility = sum(t["accessibility_score"] for t in trends) / len(trends)
        avg_performance = sum(t["performance_score"] for t in trends) / len(trends)
    else:
        avg_accessibility = avg_performance = 0
    
    return {
        "trends": trends,
        "summary": {
            "avg_accessibility_score": round(avg_accessibility, 1),
            "avg_performance_score": round(avg_performance, 1),
            "total_audits": len(trends),
            "period_days": days
        }
    }


@router.get("/responsive")
async def get_responsive_design_results() -> dict[str, Any]:
    """Get responsive design test results and analysis."""
    responsive_results = []
    
    for audit_data in _audit_results.values():
        responsive_data = audit_data.get("responsive_results", [])
        for result in responsive_data:
            responsive_results.append({
                "timestamp": audit_data.get("timestamp"),
                "device_type": result.get("device_type"),
                "viewport_width": result.get("viewport_width"),
                "viewport_height": result.get("viewport_height"),
                "passed": result.get("passed", False),
                "issues": result.get("issues", [])
            })
    
    # Analyze by device type
    device_analysis = {}
    for result in responsive_results:
        device = result["device_type"]
        if device not in device_analysis:
            device_analysis[device] = {"total": 0, "passed": 0, "common_issues": {}}
        
        device_analysis[device]["total"] += 1
        if result["passed"]:
            device_analysis[device]["passed"] += 1
        
        # Count common issues
        for issue in result["issues"]:
            if issue not in device_analysis[device]["common_issues"]:
                device_analysis[device]["common_issues"][issue] = 0
            device_analysis[device]["common_issues"][issue] += 1
    
    # Calculate pass rates
    for device, analysis in device_analysis.items():
        analysis["pass_rate"] = (analysis["passed"] / analysis["total"]) if analysis["total"] > 0 else 0
    
    return {
        "device_analysis": device_analysis,
        "total_tests": len(responsive_results)
    }


@router.get("/wcag-compliance")
async def get_wcag_compliance_status() -> dict[str, Any]:
    """Get WCAG 2.1 AA compliance status and breakdown."""
    if not _audit_results:
        return {
            "compliance_status": "NO_DATA",
            "wcag_version": "2.1",
            "level": "AA",
            "total_criteria": 0,
            "criteria_passed": 0,
            "compliance_percentage": 0
        }
    
    # Get latest audit for WCAG analysis
    latest_audit = max(_audit_results.items(), key=lambda x: x[1].get("timestamp", ""))[1]
    wcag_compliance = latest_audit.get("wcag_compliance", {})
    
    total_criteria = wcag_compliance.get("total_rules_checked", 0)
    rules_passed = wcag_compliance.get("rules_passed", 0)
    compliance_percentage = (rules_passed / total_criteria * 100) if total_criteria > 0 else 0
    
    return {
        "compliance_status": "COMPLIANT" if compliance_percentage >= 100 else "NON_COMPLIANT",
        "wcag_version": wcag_compliance.get("version", "2.1"),
        "level": wcag_compliance.get("level", "AA"),
        "total_criteria": total_criteria,
        "criteria_passed": rules_passed,
        "compliance_percentage": round(compliance_percentage, 1),
        "last_audit": latest_audit.get("timestamp")
    }


@router.post("/quality-gates/enforce")
async def enforce_quality_gates() -> dict[str, Any]:
    """Enforce quality gates and return enforcement status."""
    if not _audit_results:
        return {
            "enforcement_status": "NO_DATA",
            "message": "No audit data available for enforcement"
        }
    
    # Get latest audit results
    latest_audit = max(_audit_results.items(), key=lambda x: x[1].get("timestamp", ""))[1]
    
    overall_status = latest_audit.get("overall_status")
    quality_gates_passed = latest_audit.get("quality_gates", {}).get("passed", False)
    
    # Determine enforcement action
    if overall_status == "PASS" and quality_gates_passed:
        enforcement_status = "PASSED"
        message = "All quality gates passed - deployment approved"
        should_block = False
    else:
        enforcement_status = "BLOCKED"
        message = "Quality gates failed - deployment blocked"
        should_block = True
        
        # Add specific failure reasons
        failures = []
        issue_counts = latest_audit.get("quality_gates", {}).get("issue_counts", {})
        
        if issue_counts.get("critical", 0) > 0:
            failures.append(f"{issue_counts['critical']} critical accessibility issues")
        
        lighthouse_results = latest_audit.get("lighthouse_results", [])
        if lighthouse_results:
            lighthouse_score = lighthouse_results[0].get("accessibility_score", 0)
            if lighthouse_score < 90:
                failures.append(f"Lighthouse accessibility score {lighthouse_score}/100 (minimum: 90)")
        
        responsive_results = latest_audit.get("responsive_results", [])
        responsive_failures = [r for r in responsive_results if not r.get("passed", True)]
        if responsive_failures:
            failures.append(f"Responsive design issues on {len(responsive_failures)} device(s)")
        
        if failures:
            message += ": " + ", ".join(failures)
    
    return {
        "enforcement_status": enforcement_status,
        "should_block_deployment": should_block,
        "message": message,
        "audit_timestamp": latest_audit.get("timestamp"),
        "recommendations": latest_audit.get("recommendations", [])
    }


@router.get("/dashboard")
async def get_ux_dashboard() -> dict[str, Any]:
    """Get comprehensive UX quality dashboard data."""
    status = await get_ux_quality_status()
    lighthouse_data = await get_lighthouse_results(30)  # 30 days of data
    responsive_data = await get_responsive_design_results()
    wcag_data = await get_wcag_compliance_status()
    
    return {
        "overview": {
            "overall_status": status.overall_status,
            "quality_gates_passed": status.quality_gates_passed,
            "last_audit": status.last_audit
        },
        "scores": {
            "accessibility": status.accessibility_score,
            "performance": status.performance_score,
            "wcag_compliance": wcag_data["compliance_percentage"]
        },
        "issues": {
            "critical": status.critical_issues,
            "serious": status.serious_issues,
            "responsive": status.responsive_issues
        },
        "trends": lighthouse_data["trends"][-7:],  # Last 7 audits
        "responsive_analysis": responsive_data["device_analysis"],
        "recommendations": _get_dashboard_recommendations(status, wcag_data)
    }


def _get_dashboard_recommendations(status: QualityGateStatus, wcag_data: dict[str, Any]) -> list[str]:
    """Generate dashboard recommendations based on current status."""
    recommendations = []
    
    if status.critical_issues > 0:
        recommendations.append(f"🚨 Fix {status.critical_issues} critical accessibility issues")
    
    if status.accessibility_score and status.accessibility_score < 90:
        recommendations.append(f"📈 Improve Lighthouse accessibility score to 90+ (current: {status.accessibility_score})")
    
    if status.performance_score and status.performance_score < 75:
        recommendations.append(f"⚡ Improve performance score to 75+ (current: {status.performance_score})")
    
    if wcag_data["compliance_percentage"] < 100:
        recommendations.append(f"♿ Achieve 100% WCAG 2.1 AA compliance (current: {wcag_data['compliance_percentage']}%)")
    
    if status.responsive_issues > 0:
        recommendations.append(f"📱 Fix responsive design issues on {status.responsive_issues} device(s)")
    
    if not recommendations:
        recommendations.append("✨ All quality gates passed - maintain excellent UX standards!")
    
    return recommendations


async def _run_comprehensive_audit(audit_id: str, request: AccessibilityAuditRequest) -> None:
    """Run comprehensive accessibility audit in background."""
    try:
        logger.info(f"Starting comprehensive audit {audit_id}")
        
        auditor = AccessibilityQualityGates()
        
        lighthouse_results = []
        responsive_results = []
        
        if request.include_lighthouse:
            logger.info("Running Lighthouse audit...")
            lighthouse_result = await auditor.run_lighthouse_audit(request.url, request.ci_mode)
            lighthouse_results.append(lighthouse_result)
        
        if request.include_responsive:
            logger.info("Running responsive design tests...")
            responsive_results = await auditor.run_responsive_tests(request.url, request.devices)
        
        # Generate comprehensive report
        report = auditor.generate_accessibility_report(lighthouse_results, responsive_results)
        
        # Store results
        _audit_results[audit_id] = report
        
        logger.info(f"Audit {audit_id} completed with status: {report['overall_status']}")
        
    except Exception as e:
        logger.error(f"Audit {audit_id} failed: {e}")
        _audit_results[audit_id] = {
            "audit_id": audit_id,
            "timestamp": datetime.now().isoformat(),
            "overall_status": "ERROR",
            "error": str(e)
        }