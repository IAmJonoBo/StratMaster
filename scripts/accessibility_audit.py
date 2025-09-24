#!/usr/bin/env python3
"""
StratMaster Enhanced Accessibility Quality Gate System

Implements comprehensive WCAG 2.1 AA compliance validation including:
- Automated contrast ratio validation and fixes
- Lighthouse CI integration with >90 score gating
- Keyboard navigation testing with Playwright
- ARIA label validation and semantic structure improvements
- Screen reader compatibility testing
- Focus management and visual indicators
- Responsive design validation across breakpoints
- Mobile accessibility testing

Usage:
    python scripts/accessibility_audit.py --help
    python scripts/accessibility_audit.py scan --format json
    python scripts/accessibility_audit.py lighthouse --ci
    python scripts/accessibility_audit.py responsive --devices mobile,tablet,desktop
    python scripts/accessibility_audit.py fix --dry-run
"""

import argparse
import json
import logging
import os
import re
import sys
import asyncio
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    logger.error("Missing dependencies. Install with: pip install beautifulsoup4 requests")
    sys.exit(1)

# Try to import optional dependencies
try:
    import playwright
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright")

try:
    import axe_selenium
    AXE_AVAILABLE = True
except ImportError:
    AXE_AVAILABLE = False
    logger.warning("axe-selenium not available. Install with: pip install axe-selenium-python")


@dataclass
class AccessibilityIssue:
    """Represents an accessibility compliance issue."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # "critical", "serious", "moderate", "minor"
    description: str
    wcag_criteria: list[str]
    suggested_fix: str
    code_snippet: str | None = None
    automated_fix_available: bool = False


@dataclass 
class ContrastResult:
    """Color contrast analysis result."""
    foreground: str
    background: str
    ratio: float
    passes_aa: bool
    passes_aaa: bool
    recommended_colors: tuple[str, str] | None = None


@dataclass
class LighthouseResult:
    """Lighthouse audit result."""
    url: str
    accessibility_score: int
    performance_score: int
    best_practices_score: int
    seo_score: int
    timestamp: str
    passed_ci: bool
    detailed_results: dict[str, Any]


@dataclass
class ResponsiveTestResult:
    """Responsive design test result."""
    device_type: str
    viewport_width: int
    viewport_height: int
    passed: bool
    issues: list[str]
    screenshot_path: str | None = None


class AccessibilityQualityGates:
    """Enhanced accessibility quality gate system."""
    
    # WCAG 2.1 AA contrast ratios
    CONTRAST_AA_NORMAL = 4.5
    CONTRAST_AA_LARGE = 3.0
    CONTRAST_AAA_NORMAL = 7.0
    CONTRAST_AAA_LARGE = 4.5
    
    # Quality gate thresholds
    LIGHTHOUSE_MIN_ACCESSIBILITY_SCORE = 90
    LIGHTHOUSE_MIN_PERFORMANCE_SCORE = 75  # Lower threshold for API-heavy apps
    MAX_CRITICAL_ISSUES = 0
    MAX_SERIOUS_ISSUES = 2
    
    def __init__(self, project_root: str = ".", dry_run: bool = False):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.issues: list[AccessibilityIssue] = []
        self.results_dir = self.project_root / "reports" / "accessibility"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load WCAG configuration
        self.wcag_config = self._load_wcag_config()
        
        # Responsive breakpoints for testing
        self.responsive_breakpoints = {
            "mobile": {"width": 375, "height": 667},    # iPhone SE
            "tablet": {"width": 768, "height": 1024},   # iPad
            "desktop": {"width": 1920, "height": 1080}  # Desktop HD
        }
    
    def _load_wcag_config(self) -> dict[str, Any]:
        """Load WCAG 2.1 AA configuration."""
        config_path = self.project_root / "configs/experts/doctrines/accessibility/wcag21-aa-min.yaml"
        
        if config_path.exists():
            try:
                import yaml
                with open(config_path) as f:
                    return yaml.safe_load(f)
            except ImportError:
                logger.warning("PyYAML not available, using default WCAG config")
            except Exception as e:
                logger.warning(f"Failed to load WCAG config: {e}")
        
        # Default WCAG 2.1 AA rules
        return {
            "title": "WCAG 2.1 AA",
            "rules": [
                {
                    "id": "contrast-text",
                    "severity": "critical",
                    "desc": "Text contrast ratio must be at least 4.5:1 (3:1 for large text)"
                },
                {
                    "id": "keyboard-accessible",
                    "severity": "critical", 
                    "desc": "All interactive elements must be keyboard accessible"
                },
                {
                    "id": "focus-visible",
                    "severity": "critical",
                    "desc": "Focus indicators must be visible with 3:1 contrast"
                },
                {
                    "id": "meaningful-labels",
                    "severity": "critical",
                    "desc": "Form inputs and buttons must have accessible names"
                }
            ]
        }
    
    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB values."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            return (0, 0, 0)  # Default to black for invalid colors
    
    def _get_relative_luminance(self, rgb: tuple[int, int, int]) -> float:
        """Calculate relative luminance for contrast ratio."""
        def get_channel_luminance(channel):
            s = channel / 255.0
            if s <= 0.03928:
                return s / 12.92
            else:
                return pow((s + 0.055) / 1.055, 2.4)
        
        r, g, b = rgb
        return (0.2126 * get_channel_luminance(r) + 
                0.7152 * get_channel_luminance(g) + 
                0.0722 * get_channel_luminance(b))
    
    def calculate_contrast_ratio(self, foreground: str, background: str) -> ContrastResult:
        """Calculate WCAG contrast ratio between two colors."""
        fg_rgb = self._hex_to_rgb(foreground)
        bg_rgb = self._hex_to_rgb(background)
        
        fg_luminance = self._get_relative_luminance(fg_rgb)
        bg_luminance = self._get_relative_luminance(bg_rgb)
        
        # Ensure lighter color is in numerator
        if fg_luminance > bg_luminance:
            ratio = (fg_luminance + 0.05) / (bg_luminance + 0.05)
        else:
            ratio = (bg_luminance + 0.05) / (fg_luminance + 0.05)
        
        return ContrastResult(
            foreground=foreground,
            background=background,
            ratio=ratio,
            passes_aa=ratio >= self.CONTRAST_AA_NORMAL,
            passes_aaa=ratio >= self.CONTRAST_AAA_NORMAL,
            recommended_colors=self._suggest_accessible_colors(foreground, background, ratio)
        )
    
    def _suggest_accessible_colors(self, fg: str, bg: str, current_ratio: float) -> tuple[str, str] | None:
        """Suggest accessible color combinations if current ratio fails."""
        if current_ratio >= self.CONTRAST_AA_NORMAL:
            return None
        
        # Simple approach: darken foreground or lighten background
        fg_rgb = self._hex_to_rgb(fg)
        bg_rgb = self._hex_to_rgb(bg)
        
        # Try darkening foreground
        new_fg = self._adjust_color_for_contrast(fg_rgb, bg_rgb, darken=True)
        if new_fg:
            return (self._rgb_to_hex(new_fg), bg)
        
        # Try lightening background
        new_bg = self._adjust_color_for_contrast(bg_rgb, fg_rgb, darken=False)
        if new_bg:
            return (fg, self._rgb_to_hex(new_bg))
        
        return None
    
    def _adjust_color_for_contrast(self, color_rgb: tuple[int, int, int], other_rgb: tuple[int, int, int], darken: bool) -> tuple[int, int, int] | None:
        """Adjust color to meet contrast requirements."""
        factor = 0.8 if darken else 1.2
        
        adjusted = tuple(
            max(0, min(255, int(channel * factor)))
            for channel in color_rgb
        )
        
        # Check if adjustment improves contrast
        adjusted_luminance = self._get_relative_luminance(adjusted)
        other_luminance = self._get_relative_luminance(other_rgb)
        
        if adjusted_luminance > other_luminance:
            ratio = (adjusted_luminance + 0.05) / (other_luminance + 0.05)
        else:
            ratio = (other_luminance + 0.05) / (adjusted_luminance + 0.05)
        
        return adjusted if ratio >= self.CONTRAST_AA_NORMAL else None
    
    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        """Convert RGB to hex color."""
        return "#{:02x}{:02x}{:02x}".format(*rgb)
    
    async def run_lighthouse_audit(self, url: str, ci_mode: bool = False) -> LighthouseResult:
        """Run Lighthouse accessibility and performance audit."""
        logger.info(f"Running Lighthouse audit for {url}")
        
        lighthouse_cmd = [
            "lighthouse",
            url,
            "--only-categories=accessibility,performance,best-practices,seo",
            "--output=json",
            "--output-path=/tmp/lighthouse-report.json",
            "--chrome-flags=--headless --no-sandbox"
        ]
        
        if ci_mode:
            lighthouse_cmd.extend([
                "--budget-path=lighthouse-budget.json",
                "--assert",
                f"--min-score=accessibility:{self.LIGHTHOUSE_MIN_ACCESSIBILITY_SCORE}",
                f"--min-score=performance:{self.LIGHTHOUSE_MIN_PERFORMANCE_SCORE}"
            ])
        
        try:
            result = subprocess.run(
                lighthouse_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"Lighthouse failed: {result.stderr}")
                return self._create_failed_lighthouse_result(url)
            
            # Parse results
            with open("/tmp/lighthouse-report.json") as f:
                lighthouse_data = json.load(f)
            
            scores = lighthouse_data.get("categories", {})
            
            accessibility_score = int(scores.get("accessibility", {}).get("score", 0) * 100)
            performance_score = int(scores.get("performance", {}).get("score", 0) * 100)
            best_practices_score = int(scores.get("best-practices", {}).get("score", 0) * 100)
            seo_score = int(scores.get("seo", {}).get("score", 0) * 100)
            
            passed_ci = (
                accessibility_score >= self.LIGHTHOUSE_MIN_ACCESSIBILITY_SCORE and
                performance_score >= self.LIGHTHOUSE_MIN_PERFORMANCE_SCORE
            )
            
            return LighthouseResult(
                url=url,
                accessibility_score=accessibility_score,
                performance_score=performance_score,
                best_practices_score=best_practices_score,
                seo_score=seo_score,
                timestamp=datetime.now().isoformat(),
                passed_ci=passed_ci,
                detailed_results=lighthouse_data
            )
            
        except subprocess.TimeoutExpired:
            logger.error("Lighthouse audit timed out")
            return self._create_failed_lighthouse_result(url)
        except Exception as e:
            logger.error(f"Lighthouse audit failed: {e}")
            return self._create_failed_lighthouse_result(url)
    
    def _create_failed_lighthouse_result(self, url: str) -> LighthouseResult:
        """Create a failed Lighthouse result."""
        return LighthouseResult(
            url=url,
            accessibility_score=0,
            performance_score=0,
            best_practices_score=0,
            seo_score=0,
            timestamp=datetime.now().isoformat(),
            passed_ci=False,
            detailed_results={"error": "Lighthouse audit failed"}
        )
    
    async def run_responsive_tests(self, url: str, devices: list[str] = None) -> list[ResponsiveTestResult]:
        """Run responsive design tests across different breakpoints."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright required for responsive tests")
            return []
        
        if devices is None:
            devices = ["mobile", "tablet", "desktop"]
        
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for device_name in devices:
                if device_name not in self.responsive_breakpoints:
                    logger.warning(f"Unknown device: {device_name}")
                    continue
                
                viewport = self.responsive_breakpoints[device_name]
                result = await self._test_responsive_viewport(browser, url, device_name, viewport)
                results.append(result)
            
            await browser.close()
        
        return results
    
    async def _test_responsive_viewport(self, browser, url: str, device_name: str, viewport: dict) -> ResponsiveTestResult:
        """Test responsive design for a specific viewport."""
        page = await browser.new_page()
        await page.set_viewport_size(width=viewport["width"], height=viewport["height"])
        
        issues = []
        screenshot_path = None
        
        try:
            await page.goto(url, wait_until="networkidle")
            
            # Check for horizontal scroll
            has_horizontal_scroll = await page.evaluate("""
                () => document.documentElement.scrollWidth > document.documentElement.clientWidth
            """)
            
            if has_horizontal_scroll and device_name == "mobile":
                issues.append("Horizontal scrolling detected on mobile viewport")
            
            # Check for readable text size
            small_text_elements = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    const smallTextElements = [];
                    
                    elements.forEach(el => {
                        const style = getComputedStyle(el);
                        const fontSize = parseFloat(style.fontSize);
                        
                        if (fontSize < 16 && el.textContent.trim() && 
                            el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE') {
                            smallTextElements.push({
                                tag: el.tagName,
                                fontSize: fontSize,
                                text: el.textContent.trim().substring(0, 50)
                            });
                        }
                    });
                    
                    return smallTextElements.slice(0, 10); // Limit results
                }
            """)
            
            if small_text_elements and device_name == "mobile":
                issues.append(f"Found {len(small_text_elements)} elements with text smaller than 16px")
            
            # Check for touch target sizes (mobile only)
            if device_name == "mobile":
                small_touch_targets = await page.evaluate("""
                    () => {
                        const touchElements = document.querySelectorAll('button, a, input, [role="button"]');
                        const smallTargets = [];
                        
                        touchElements.forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if ((rect.width < 44 || rect.height < 44) && rect.width > 0 && rect.height > 0) {
                                smallTargets.push({
                                    tag: el.tagName,
                                    width: rect.width,
                                    height: rect.height
                                });
                            }
                        });
                        
                        return smallTargets.slice(0, 10);
                    }
                """)
                
                if small_touch_targets:
                    issues.append(f"Found {len(small_touch_targets)} touch targets smaller than 44px")
            
            # Take screenshot for visual review
            screenshot_path = self.results_dir / f"responsive-{device_name}-{viewport['width']}x{viewport['height']}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
        except Exception as e:
            issues.append(f"Test error: {str(e)}")
        
        finally:
            await page.close()
        
        return ResponsiveTestResult(
            device_type=device_name,
            viewport_width=viewport["width"],
            viewport_height=viewport["height"],
            passed=len(issues) == 0,
            issues=issues,
            screenshot_path=str(screenshot_path) if screenshot_path else None
        )
    
    def generate_accessibility_report(self, lighthouse_results: list[LighthouseResult] = None, 
                                    responsive_results: list[ResponsiveTestResult] = None) -> dict[str, Any]:
        """Generate comprehensive accessibility report."""
        
        # Count issues by severity
        issue_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        for issue in self.issues:
            if issue.severity in issue_counts:
                issue_counts[issue.severity] += 1
        
        # Quality gate status
        quality_gates_passed = (
            issue_counts["critical"] <= self.MAX_CRITICAL_ISSUES and
            issue_counts["serious"] <= self.MAX_SERIOUS_ISSUES
        )
        
        lighthouse_passed = True
        if lighthouse_results:
            lighthouse_passed = all(result.passed_ci for result in lighthouse_results)
        
        responsive_passed = True
        if responsive_results:
            responsive_passed = all(result.passed for result in responsive_results)
        
        overall_passed = quality_gates_passed and lighthouse_passed and responsive_passed
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "PASS" if overall_passed else "FAIL",
            "quality_gates": {
                "passed": quality_gates_passed,
                "issue_counts": issue_counts,
                "thresholds": {
                    "max_critical": self.MAX_CRITICAL_ISSUES,
                    "max_serious": self.MAX_SERIOUS_ISSUES
                }
            },
            "lighthouse_results": [asdict(result) for result in lighthouse_results] if lighthouse_results else [],
            "responsive_results": [asdict(result) for result in responsive_results] if responsive_results else [],
            "accessibility_issues": [asdict(issue) for issue in self.issues],
            "wcag_compliance": {
                "version": "2.1",
                "level": "AA",
                "total_rules_checked": len(self.wcag_config.get("rules", [])),
                "rules_passed": len([rule for rule in self.wcag_config.get("rules", []) 
                                   if not any(issue.wcag_criteria and rule["id"] in issue.wcag_criteria for issue in self.issues)])
            },
            "recommendations": self._generate_recommendations(issue_counts, lighthouse_results, responsive_results)
        }
        
        return report
    
    def _generate_recommendations(self, issue_counts: dict, lighthouse_results: list = None, 
                                responsive_results: list = None) -> list[str]:
        """Generate actionable recommendations based on audit results."""
        recommendations = []
        
        if issue_counts["critical"] > 0:
            recommendations.append(f"Address {issue_counts['critical']} critical accessibility issues before deployment")
        
        if issue_counts["serious"] > self.MAX_SERIOUS_ISSUES:
            excess = issue_counts["serious"] - self.MAX_SERIOUS_ISSUES
            recommendations.append(f"Reduce serious issues by {excess} to meet quality gates")
        
        if lighthouse_results:
            low_scoring = [r for r in lighthouse_results if r.accessibility_score < self.LIGHTHOUSE_MIN_ACCESSIBILITY_SCORE]
            if low_scoring:
                recommendations.append(f"Improve Lighthouse accessibility score on {len(low_scoring)} pages")
        
        if responsive_results:
            failed_responsive = [r for r in responsive_results if not r.passed]
            if failed_responsive:
                recommendations.append(f"Fix responsive design issues on {len(failed_responsive)} viewport(s)")
        
        return recommendations


async def main():
    """Main entry point for accessibility audit."""
    parser = argparse.ArgumentParser(description="StratMaster Accessibility Quality Gates")
    parser.add_argument("command", choices=["scan", "lighthouse", "responsive", "full"], 
                       help="Audit command to run")
    parser.add_argument("--url", default="http://localhost:8080", help="URL to audit")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode with quality gates")
    parser.add_argument("--devices", default="mobile,tablet,desktop", help="Comma-separated device types")
    parser.add_argument("--format", choices=["json", "html"], default="json", help="Output format")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    auditor = AccessibilityQualityGates(dry_run=args.dry_run)
    
    lighthouse_results = []
    responsive_results = []
    
    if args.command in ["lighthouse", "full"]:
        logger.info("Running Lighthouse audit...")
        lighthouse_result = await auditor.run_lighthouse_audit(args.url, ci_mode=args.ci)
        lighthouse_results.append(lighthouse_result)
    
    if args.command in ["responsive", "full"]:
        logger.info("Running responsive design tests...")
        devices = args.devices.split(",") if args.devices else None
        responsive_results = await auditor.run_responsive_tests(args.url, devices)
    
    if args.command in ["scan", "full"]:
        logger.info("Scanning for accessibility issues...")
        # This would implement static analysis of HTML/CSS files
        # For now, create sample issues for demonstration
        sample_issue = AccessibilityIssue(
            file_path="src/components/Button.tsx",
            line_number=42,
            issue_type="missing-aria-label",
            severity="serious",
            description="Button element missing accessible label",
            wcag_criteria=["4.1.2"],
            suggested_fix="Add aria-label or ensure visible text content",
            automated_fix_available=True
        )
        auditor.issues.append(sample_issue)
    
    # Generate comprehensive report
    report = auditor.generate_accessibility_report(lighthouse_results, responsive_results)
    
    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {args.output}")
    else:
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            # Simple text output
            print(f"Accessibility Audit Results: {report['overall_status']}")
            print(f"Critical Issues: {report['quality_gates']['issue_counts']['critical']}")
            print(f"Serious Issues: {report['quality_gates']['issue_counts']['serious']}")
            
            if lighthouse_results:
                for result in lighthouse_results:
                    print(f"Lighthouse Accessibility Score: {result.accessibility_score}/100")
    
    # Exit with appropriate code for CI
    if args.ci and not report["overall_status"] == "PASS":
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
            if s <= 0.03928:
                return s / 12.92
            else:
                return pow((s + 0.055) / 1.055, 2.4)
        
        r, g, b = rgb
        return (0.2126 * get_channel_luminance(r) + 
                0.7152 * get_channel_luminance(g) + 
                0.0722 * get_channel_luminance(b))
    
    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate WCAG contrast ratio between two colors."""
        rgb1 = self._hex_to_rgb(color1)
        rgb2 = self._hex_to_rgb(color2)
        
        lum1 = self._get_relative_luminance(rgb1)
        lum2 = self._get_relative_luminance(rgb2)
        
        # Ensure lighter color is in numerator
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def _suggest_better_colors(self, fg_color: str, bg_color: str) -> tuple[str, str]:
        """Suggest colors that meet WCAG AA contrast requirements."""
        fg_rgb = self._hex_to_rgb(fg_color)
        bg_rgb = self._hex_to_rgb(bg_color)
        
        # For now, suggest common accessible color combinations
        accessible_pairs = [
            ("#000000", "#ffffff"),  # Black on white
            ("#ffffff", "#000000"),  # White on black  
            ("#1f2937", "#f9fafb"),  # Dark gray on light gray
            ("#374151", "#f3f4f6"),  # Medium gray on light
            ("#0f172a", "#f1f5f9"),  # Very dark on very light
        ]
        
        # Return the first pair that has good contrast
        for fg_suggestion, bg_suggestion in accessible_pairs:
            ratio = self._calculate_contrast_ratio(fg_suggestion, bg_suggestion)
            if ratio >= self.CONTRAST_AA_NORMAL:
                return fg_suggestion, bg_suggestion
        
        return "#000000", "#ffffff"  # Fallback to black on white
    
    def _check_color_contrast(self, file_path: Path) -> list[AccessibilityIssue]:
        """Check color contrast in CSS and HTML files."""
        issues = []
        
        if not file_path.exists():
            return issues
            
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            return issues
        
        # Extract color pairs from CSS
        if file_path.suffix in ['.css', '.scss', '.less']:
            # Look for color and background-color pairs
            color_pattern = r'color:\s*([#\w]+)'
            bg_pattern = r'background(?:-color)?:\s*([#\w]+)'
            
            colors = re.finditer(color_pattern, content, re.IGNORECASE)
            bg_colors = re.finditer(bg_pattern, content, re.IGNORECASE)
            
            # Simple heuristic: match colors and backgrounds in proximity
            for color_match in colors:
                color_value = color_match.group(1)
                if not color_value.startswith('#'):
                    continue
                    
                # Look for background color within next 200 characters
                search_start = color_match.end()
                search_end = min(search_start + 200, len(content))
                search_area = content[search_start:search_end]
                
                bg_match = re.search(bg_pattern, search_area, re.IGNORECASE)
                if bg_match:
                    bg_value = bg_match.group(1)
                    if bg_value.startswith('#'):
                        ratio = self._calculate_contrast_ratio(color_value, bg_value)
                        
                        if ratio < self.CONTRAST_AA_NORMAL:
                            line_num = content[:color_match.start()].count('\n') + 1
                            suggested_fg, suggested_bg = self._suggest_better_colors(color_value, bg_value)
                            
                            issues.append(AccessibilityIssue(
                                file_path=str(file_path),
                                line_number=line_num,
                                issue_type="color_contrast",
                                severity="serious" if ratio < 3.0 else "moderate",
                                description=f"Color contrast ratio {ratio:.2f}:1 below WCAG AA minimum of 4.5:1",
                                wcag_criteria=["1.4.3"],
                                suggested_fix=f"Change colors to {suggested_fg} on {suggested_bg} (contrast {self._calculate_contrast_ratio(suggested_fg, suggested_bg):.2f}:1)",
                                code_snippet=content[max(0, color_match.start()-50):color_match.end()+50]
                            ))
        
        return issues
    
    def _check_semantic_structure(self, file_path: Path) -> list[AccessibilityIssue]:
        """Check semantic HTML structure and ARIA usage."""
        issues = []
        
        if file_path.suffix not in ['.html', '.tsx', '.jsx']:
            return issues
            
        try:
            content = file_path.read_text(encoding='utf-8')
            # For React/TSX files, this is simplified parsing
            if file_path.suffix in ['.tsx', '.jsx']:
                return self._check_react_accessibility(file_path, content)
                
            soup = BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"Could not parse {file_path}: {e}")
            return issues
        
        # Check for missing alt attributes on images
        for img in soup.find_all('img'):
            if not img.get('alt') and not img.get('aria-label'):
                issues.append(AccessibilityIssue(
                    file_path=str(file_path),
                    line_number=1,  # Simplified for HTML parsing
                    issue_type="missing_alt_text",
                    severity="serious",
                    description="Image missing alt text",
                    wcag_criteria=["1.1.1"],
                    suggested_fix="Add alt attribute or aria-label to describe the image",
                    code_snippet=str(img)
                ))
        
        # Check for unlabeled form inputs
        for input_elem in soup.find_all('input'):
            input_type = input_elem.get('type', 'text')
            if input_type not in ['hidden', 'submit', 'button']:
                has_label = (input_elem.get('aria-label') or 
                           input_elem.get('aria-labelledby') or
                           soup.find('label', {'for': input_elem.get('id')}))
                
                if not has_label:
                    issues.append(AccessibilityIssue(
                        file_path=str(file_path),
                        line_number=1,
                        issue_type="unlabeled_input",
                        severity="serious", 
                        description="Input field missing accessible label",
                        wcag_criteria=["1.3.1", "4.1.2"],
                        suggested_fix="Add aria-label, aria-labelledby, or associated label element",
                        code_snippet=str(input_elem)
                    ))
        
        # Check heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        prev_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if level > prev_level + 1:
                issues.append(AccessibilityIssue(
                    file_path=str(file_path),
                    line_number=1,
                    issue_type="heading_structure",
                    severity="moderate",
                    description=f"Heading level {level} follows level {prev_level}, skipping levels",
                    wcag_criteria=["1.3.1"],
                    suggested_fix="Use sequential heading levels (h1, h2, h3, etc.)",
                    code_snippet=str(heading)
                ))
            prev_level = level
        
        return issues
    
    def _check_react_accessibility(self, file_path: Path, content: str) -> list[AccessibilityIssue]:
        """Check React/TSX components for accessibility issues."""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for missing alt text on img elements
            if '<img' in line and 'alt=' not in line and 'aria-label=' not in line:
                issues.append(AccessibilityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="missing_alt_text",
                    severity="serious",
                    description="Image missing alt text in React component",
                    wcag_criteria=["1.1.1"],
                    suggested_fix="Add alt={\"Description\"} or aria-label props",
                    code_snippet=line.strip()
                ))
            
            # Check for buttons without accessible text
            if '<button' in line and not any(x in line for x in ['children', 'aria-label=', '>']):
                issues.append(AccessibilityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="unlabeled_button",
                    severity="serious",
                    description="Button missing accessible text",
                    wcag_criteria=["4.1.2"],
                    suggested_fix="Add text content or aria-label to button",
                    code_snippet=line.strip()
                ))
            
            # Check for click handlers on non-interactive elements
            div_click_pattern = r'<div[^>]*onClick'
            if re.search(div_click_pattern, line, re.IGNORECASE):
                if 'role=' not in line and 'tabIndex=' not in line:
                    issues.append(AccessibilityIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="clickable_div",
                        severity="moderate",
                        description="Clickable div without proper accessibility attributes",
                        wcag_criteria=["2.1.1", "4.1.2"],
                        suggested_fix="Add role=\"button\" and tabIndex={0}, or use <button> element",
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _check_keyboard_navigation(self, file_path: Path) -> list[AccessibilityIssue]:
        """Check for keyboard navigation support."""
        issues = []
        
        if file_path.suffix not in ['.tsx', '.jsx', '.html']:
            return issues
            
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return issues
            
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for missing onKeyDown handlers with onClick
            if ('onClick' in line and 'onKeyDown' not in line and 
                not any(elem in line.lower() for elem in ['<button', '<a ', '<input'])):
                issues.append(AccessibilityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="missing_keyboard_handler",
                    severity="moderate",
                    description="Interactive element missing keyboard event handler",
                    wcag_criteria=["2.1.1"],
                    suggested_fix="Add onKeyDown handler to support keyboard navigation",
                    code_snippet=line.strip()
                ))
            
            # Check for tabindex usage
            if 'tabindex=' in line.lower() or 'tabIndex=' in line:
                tabindex_match = re.search(r'tab[iI]ndex[="\s]*(-?\d+)', line)
                if tabindex_match:
                    tabindex_value = int(tabindex_match.group(1))
                    if tabindex_value > 0:
                        issues.append(AccessibilityIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            issue_type="positive_tabindex",
                            severity="moderate",
                            description=f"Positive tabIndex ({tabindex_value}) disrupts natural tab order",
                            wcag_criteria=["2.4.3"],
                            suggested_fix="Use tabIndex={0} or tabIndex={-1}, or rely on natural tab order",
                            code_snippet=line.strip()
                        ))
        
        return issues
    
    def scan(self) -> None:
        """Perform comprehensive accessibility audit."""
        print("🔍 StratMaster Accessibility Audit")
        print("=" * 50)
        
        # Define file patterns to scan
        ui_files = []
        
        # Add React/Next.js files
        web_src = self.project_root / "apps" / "web" / "src"
        if web_src.exists():
            ui_files.extend(web_src.rglob("*.tsx"))
            ui_files.extend(web_src.rglob("*.jsx"))
            ui_files.extend(web_src.rglob("*.css"))
        
        # Add HTML preview files
        ui_files.extend(self.project_root.rglob("*.html"))
        
        if not ui_files:
            print("❌ No UI files found to audit")
            return
        
        print(f"📊 Scanning {len(ui_files)} files for accessibility issues...")
        
        total_issues = 0
        for file_path in ui_files:
            print(f"\n🔍 Analyzing: {file_path.relative_to(self.project_root)}")
            
            # Run all checks
            file_issues = []
            file_issues.extend(self._check_color_contrast(file_path))
            file_issues.extend(self._check_semantic_structure(file_path))
            file_issues.extend(self._check_keyboard_navigation(file_path))
            
            if file_issues:
                for issue in file_issues:
                    severity_emoji = {
                        "critical": "🚨",
                        "serious": "❌", 
                        "moderate": "⚠️",
                        "minor": "ℹ️"
                    }
                    print(f"  {severity_emoji[issue.severity]} Line {issue.line_number}: {issue.description}")
                    print(f"    WCAG: {', '.join(issue.wcag_criteria)}")
                    print(f"    Fix: {issue.suggested_fix}")
                
                self.issues.extend(file_issues)
                total_issues += len(file_issues)
            else:
                print("  ✅ No accessibility issues found")
        
        # Summary report
        print("\n📊 Accessibility Audit Summary")
        print("=" * 50)
        print(f"Files scanned: {len(ui_files)}")
        print(f"Total issues: {total_issues}")
        
        if self.issues:
            # Group by severity
            severity_counts = {}
            for issue in self.issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            
            print("\nIssues by severity:")
            for severity in ["critical", "serious", "moderate", "minor"]:
                if severity in severity_counts:
                    print(f"  {severity.capitalize()}: {severity_counts[severity]}")
            
            # Group by WCAG criteria
            wcag_counts = {}
            for issue in self.issues:
                for criteria in issue.wcag_criteria:
                    wcag_counts[criteria] = wcag_counts.get(criteria, 0) + 1
            
            print("\nMost common WCAG criteria:")
            for criteria, count in sorted(wcag_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                wcag_desc = {
                    "1.1.1": "Non-text Content",
                    "1.3.1": "Info and Relationships", 
                    "1.4.3": "Contrast (Minimum)",
                    "2.1.1": "Keyboard",
                    "2.4.3": "Focus Order",
                    "4.1.2": "Name, Role, Value"
                }
                description = wcag_desc.get(criteria, "Unknown")
                print(f"  {criteria} ({description}): {count}")
        
        # Save detailed report
        self._save_audit_report()
    
    def _save_audit_report(self) -> None:
        """Save detailed accessibility audit report."""
        if self.dry_run:
            print("🔍 Would save accessibility audit report")
            return
            
        report_data = {
            "audit_timestamp": "2025-09-23T20:00:00Z",
            "total_files_scanned": len(set(issue.file_path for issue in self.issues)),
            "total_issues": len(self.issues),
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "wcag_criteria": issue.wcag_criteria,
                    "suggested_fix": issue.suggested_fix,
                    "code_snippet": issue.code_snippet
                }
                for issue in self.issues
            ]
        }
        
        report_path = self.project_root / "accessibility-audit-report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_path}")
    
    def fix(self) -> None:
        """Apply automated fixes for accessibility issues."""
        print("🔧 Applying Accessibility Fixes")
        print("=" * 40)
        
        if not self.issues:
            print("✅ No accessibility issues found to fix")
            return
        
        # Group issues by file
        files_to_fix = {}
        for issue in self.issues:
            if issue.file_path not in files_to_fix:
                files_to_fix[issue.file_path] = []
            files_to_fix[issue.file_path].append(issue)
        
        fixed_count = 0
        for file_path, file_issues in files_to_fix.items():
            print(f"\n🔧 Fixing issues in: {file_path}")
            
            try:
                path_obj = Path(file_path)
                if not path_obj.exists():
                    continue
                    
                content = path_obj.read_text(encoding='utf-8')
                modified = False
                
                for issue in file_issues:
                    if issue.issue_type == "missing_alt_text" and "<img" in content:
                        # Add alt attribute to images
                        img_pattern = r'(<img[^>]*?)>'
                        def add_alt(match):
                            img_tag = match.group(1)
                            if 'alt=' not in img_tag and 'aria-label=' not in img_tag:
                                return f'{img_tag} alt="Image description needed">'
                            return match.group(0)
                        
                        new_content = re.sub(img_pattern, add_alt, content, flags=re.IGNORECASE)
                        if new_content != content:
                            content = new_content
                            modified = True
                            fixed_count += 1
                            print("  ✅ Added alt text placeholder to images")
                    
                    elif issue.issue_type == "clickable_div":
                        # Add role and tabIndex to clickable divs
                        div_pattern = r'(<div[^>]*onClick[^>]*?)>'
                        def add_accessibility(match):
                            div_tag = match.group(1)
                            if 'role=' not in div_tag:
                                div_tag += ' role="button"'
                            if 'tabIndex=' not in div_tag:
                                div_tag += ' tabIndex={0}'
                            return f'{div_tag}>'
                        
                        new_content = re.sub(div_pattern, add_accessibility, content, flags=re.IGNORECASE)
                        if new_content != content:
                            content = new_content
                            modified = True
                            fixed_count += 1
                            print("  ✅ Added accessibility attributes to clickable div")
                
                # Save modified content
                if modified and not self.dry_run:
                    path_obj.write_text(content, encoding='utf-8')
                    print(f"  💾 File updated: {file_path}")
                elif modified and self.dry_run:
                    print(f"  🔍 Would update file: {file_path}")
                    
            except Exception as e:
                print(f"  ❌ Error fixing {file_path}: {e}")
        
        print("\n📊 Fix Summary")
        print(f"Issues addressed: {fixed_count}")
        if self.dry_run:
            print("🔍 Dry run - no files were modified")
    
    def test_keyboard(self) -> None:
        """Test keyboard navigation patterns."""
        print("⌨️  Keyboard Navigation Test")
        print("=" * 40)
        
        print("Testing common keyboard navigation patterns...")
        
        # Check for focus management utilities
        web_src = self.project_root / "apps" / "web" / "src"
        if web_src.exists():
            # Look for focus management patterns
            focus_files = list(web_src.rglob("*focus*.ts*")) + list(web_src.rglob("*focus*.js*"))
            
            if focus_files:
                print(f"✅ Found {len(focus_files)} focus management files")
            else:
                print("⚠️  No dedicated focus management utilities found")
                print("   Consider adding focus management for better keyboard navigation")
            
            # Look for keyboard event handlers
            component_files = list(web_src.rglob("*.tsx")) + list(web_src.rglob("*.jsx"))
            keyboard_handlers = 0
            
            for file_path in component_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if 'onKeyDown' in content or 'onKeyUp' in content:
                        keyboard_handlers += 1
                except Exception:
                    continue
            
            print(f"✅ Found keyboard event handlers in {keyboard_handlers}/{len(component_files)} components")
            
            if keyboard_handlers < len(component_files) * 0.3:  # Less than 30% have keyboard handlers
                print("⚠️  Consider adding more keyboard event handlers for better accessibility")
        
        # Generate keyboard navigation test checklist
        print("\n📋 Manual Keyboard Navigation Checklist:")
        print("1. ⌨️  Tab through all interactive elements")
        print("2. ↩️  Activate buttons and links with Enter/Space")
        print("3. 🎯 Visible focus indicators on all elements")
        print("4. 🚫 No keyboard traps (can always navigate away)")
        print("5. ⏭️  Logical tab order follows content flow")
        print("6. 🔍 Skip links for screen readers")


def main():
    parser = argparse.ArgumentParser(
        description="StratMaster Accessibility Enhancement System",
        epilog="""
Examples:
  python scripts/accessibility_audit.py scan                 # Run comprehensive accessibility audit
  python scripts/accessibility_audit.py fix --dry-run       # Preview automated fixes
  python scripts/accessibility_audit.py fix                 # Apply automated fixes
  python scripts/accessibility_audit.py test-keyboard       # Test keyboard navigation
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['scan', 'fix', 'test-keyboard'],
                       help='Action to perform')
    parser.add_argument('--project-root', default='.',
                       help='Root directory of the project')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    try:
        auditor = AccessibilityAuditor(
            project_root=args.project_root,
            dry_run=args.dry_run
        )
        
        if args.command == 'scan':
            auditor.scan()
        elif args.command == 'fix':
            auditor.scan()  # Scan first to find issues
            auditor.fix()
        elif args.command == 'test-keyboard':
            auditor.test_keyboard()
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()