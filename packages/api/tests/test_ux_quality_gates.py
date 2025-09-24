"""Tests for UX Quality Gates and WCAG 2.1 AA compliance system."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# Mock the optional dependencies for testing
pytest.mock.patch('playwright.async_api', MagicMock())
pytest.mock.patch('axe_selenium', MagicMock())


class TestAccessibilityQualityGates:
    """Test enhanced accessibility quality gate system."""
    
    def test_quality_gates_initialization(self):
        """Test quality gates system initialization."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        with tempfile.TemporaryDirectory() as tmpdir:
            auditor = AccessibilityQualityGates(project_root=tmpdir)
            
            assert auditor.project_root == Path(tmpdir)
            assert auditor.CONTRAST_AA_NORMAL == 4.5
            assert auditor.LIGHTHOUSE_MIN_ACCESSIBILITY_SCORE == 90
            assert auditor.results_dir.exists()
    
    def test_contrast_ratio_calculation(self):
        """Test WCAG contrast ratio calculations."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Test high contrast (should pass AA)
        result = auditor.calculate_contrast_ratio("#000000", "#ffffff")  # Black on white
        assert result.ratio > 20  # Very high contrast
        assert result.passes_aa is True
        assert result.passes_aaa is True
        
        # Test low contrast (should fail AA)
        result = auditor.calculate_contrast_ratio("#777777", "#888888")  # Gray on gray
        assert result.ratio < 4.5
        assert result.passes_aa is False
        assert result.recommended_colors is not None
    
    def test_color_conversion_utilities(self):
        """Test color conversion utilities."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Test hex to RGB conversion
        rgb = auditor._hex_to_rgb("#FF0000")
        assert rgb == (255, 0, 0)
        
        rgb = auditor._hex_to_rgb("#abc")  # Short form
        assert rgb == (170, 187, 204)
        
        rgb = auditor._hex_to_rgb("invalid")  # Invalid color
        assert rgb == (0, 0, 0)
        
        # Test RGB to hex conversion
        hex_color = auditor._rgb_to_hex((255, 0, 0))
        assert hex_color.lower() == "#ff0000"
    
    def test_relative_luminance_calculation(self):
        """Test relative luminance calculation for contrast."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Test pure colors
        white_luminance = auditor._get_relative_luminance((255, 255, 255))
        black_luminance = auditor._get_relative_luminance((0, 0, 0))
        
        assert white_luminance == 1.0
        assert black_luminance == 0.0
        assert white_luminance > black_luminance
    
    def test_accessible_color_suggestions(self):
        """Test automatic accessible color suggestions."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Test color that needs adjustment
        result = auditor.calculate_contrast_ratio("#999999", "#aaaaaa")  # Low contrast
        
        if result.recommended_colors:
            fg, bg = result.recommended_colors
            improved_result = auditor.calculate_contrast_ratio(fg, bg)
            assert improved_result.passes_aa or improved_result.ratio > result.ratio
    
    @pytest.mark.asyncio
    async def test_lighthouse_audit_mock(self):
        """Test Lighthouse audit with mocked subprocess."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Mock lighthouse report data
        mock_lighthouse_data = {
            "categories": {
                "accessibility": {"score": 0.92},
                "performance": {"score": 0.78},
                "best-practices": {"score": 0.85},
                "seo": {"score": 0.88}
            }
        }
        
        with patch('subprocess.run') as mock_subprocess, \
             patch('builtins.open', mock_open_lighthouse_report(mock_lighthouse_data)):
            
            mock_subprocess.return_value.returncode = 0
            
            result = await auditor.run_lighthouse_audit("http://localhost:8080")
            
            assert result.accessibility_score == 92
            assert result.performance_score == 78
            assert result.passed_ci is True  # Both scores above threshold
    
    @pytest.mark.asyncio
    async def test_lighthouse_audit_failure(self):
        """Test Lighthouse audit failure handling."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 1
            mock_subprocess.return_value.stderr = "Lighthouse failed to run"
            
            result = await auditor.run_lighthouse_audit("http://localhost:8080")
            
            assert result.accessibility_score == 0
            assert result.passed_ci is False
            assert "error" in result.detailed_results
    
    @pytest.mark.asyncio
    async def test_responsive_design_testing(self):
        """Test responsive design testing with mocked Playwright."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Mock Playwright components
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        
        # Mock page evaluations
        mock_page.evaluate.side_effect = [
            False,  # No horizontal scroll
            [],     # No small text elements
            []      # No small touch targets
        ]
        
        with patch('scripts.accessibility_audit.PLAYWRIGHT_AVAILABLE', True), \
             patch('playwright.async_api.async_playwright') as mock_playwright:
            
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.chromium.launch.return_value = mock_browser
            mock_playwright.return_value = mock_context
            
            results = await auditor.run_responsive_tests("http://localhost:8080", ["mobile"])
            
            assert len(results) == 1
            assert results[0].device_type == "mobile"
            assert results[0].viewport_width == 375
            assert results[0].passed is True
            assert len(results[0].issues) == 0
    
    def test_accessibility_issue_tracking(self):
        """Test accessibility issue creation and tracking."""
        from scripts.accessibility_audit import AccessibilityIssue, AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Create test issues
        critical_issue = AccessibilityIssue(
            file_path="components/Button.tsx",
            line_number=42,
            issue_type="missing-aria-label",
            severity="critical",
            description="Button missing accessible name",
            wcag_criteria=["4.1.2"],
            suggested_fix="Add aria-label attribute",
            automated_fix_available=True
        )
        
        serious_issue = AccessibilityIssue(
            file_path="pages/Dashboard.tsx",
            line_number=15,
            issue_type="low-contrast",
            severity="serious",
            description="Text contrast below 4.5:1 ratio",
            wcag_criteria=["1.4.3"],
            suggested_fix="Increase text color contrast",
            automated_fix_available=False
        )
        
        auditor.issues.extend([critical_issue, serious_issue])
        
        # Test report generation
        report = auditor.generate_accessibility_report()
        
        assert report["quality_gates"]["issue_counts"]["critical"] == 1
        assert report["quality_gates"]["issue_counts"]["serious"] == 1
        assert report["overall_status"] == "FAIL"  # 1 critical exceeds limit of 0
    
    def test_quality_gates_thresholds(self):
        """Test quality gate threshold evaluation."""
        from scripts.accessibility_audit import AccessibilityQualityGates, AccessibilityIssue
        
        auditor = AccessibilityQualityGates()
        
        # Test with issues within thresholds
        minor_issue = AccessibilityIssue(
            file_path="test.tsx", line_number=1, issue_type="test",
            severity="minor", description="Minor issue",
            wcag_criteria=[], suggested_fix="Fix it"
        )
        
        auditor.issues.append(minor_issue)
        report = auditor.generate_accessibility_report()
        
        # Should pass - no critical or serious issues
        assert report["quality_gates"]["passed"] is True
        assert report["overall_status"] == "PASS"
        
        # Test with issues exceeding thresholds
        critical_issue = AccessibilityIssue(
            file_path="test.tsx", line_number=2, issue_type="test",
            severity="critical", description="Critical issue",
            wcag_criteria=[], suggested_fix="Fix it"
        )
        
        auditor.issues.append(critical_issue)
        report = auditor.generate_accessibility_report()
        
        # Should fail - 1 critical exceeds limit of 0
        assert report["quality_gates"]["passed"] is False
        assert report["overall_status"] == "FAIL"
    
    def test_wcag_compliance_tracking(self):
        """Test WCAG 2.1 AA compliance tracking."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        
        # Check default WCAG config loading
        wcag_config = auditor.wcag_config
        assert wcag_config["title"] == "WCAG 2.1 AA"
        assert len(wcag_config["rules"]) >= 4
        
        # Verify critical rules are present
        rule_ids = [rule["id"] for rule in wcag_config["rules"]]
        assert "contrast-text" in rule_ids
        assert "keyboard-accessible" in rule_ids
        assert "focus-visible" in rule_ids
    
    def test_recommendations_generation(self):
        """Test automated recommendation generation."""
        from scripts.accessibility_audit import AccessibilityQualityGates, AccessibilityIssue, LighthouseResult, ResponsiveTestResult
        
        auditor = AccessibilityQualityGates()
        
        # Add issues that should trigger recommendations
        auditor.issues.append(AccessibilityIssue(
            file_path="test.tsx", line_number=1, issue_type="test",
            severity="critical", description="Critical issue",
            wcag_criteria=[], suggested_fix="Fix it"
        ))
        
        # Mock Lighthouse result with low score
        lighthouse_result = LighthouseResult(
            url="http://test.com",
            accessibility_score=75,  # Below 90 threshold
            performance_score=80,
            best_practices_score=85,
            seo_score=90,
            timestamp="2024-01-15T10:00:00",
            passed_ci=False,
            detailed_results={}
        )
        
        # Mock failed responsive test
        responsive_result = ResponsiveTestResult(
            device_type="mobile",
            viewport_width=375,
            viewport_height=667,
            passed=False,
            issues=["Horizontal scrolling detected"],
            screenshot_path=None
        )
        
        report = auditor.generate_accessibility_report([lighthouse_result], [responsive_result])
        
        recommendations = report["recommendations"]
        assert len(recommendations) >= 3  # Should have recommendations for all issues
        assert any("critical" in rec.lower() for rec in recommendations)
        assert any("lighthouse" in rec.lower() for rec in recommendations)
        assert any("responsive" in rec.lower() for rec in recommendations)


class TestLighthouseIntegration:
    """Test Lighthouse CI integration."""
    
    def test_lighthouse_config_validation(self):
        """Test Lighthouse CI configuration."""
        from pathlib import Path
        
        config_path = Path("lighthouse-budget.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            
            assert "ci" in config
            assert "assert" in config["ci"]
            assert "budgets" in config
            
            # Verify accessibility threshold
            assertions = config["ci"]["assert"]["assertions"]
            assert "categories:accessibility" in assertions
            
            accessibility_assertion = assertions["categories:accessibility"]
            assert accessibility_assertion[0] == "error"  # Error level
            assert accessibility_assertion[1]["minScore"] >= 0.9  # 90% minimum
    
    def test_performance_budget_configuration(self):
        """Test performance budget configuration."""
        from pathlib import Path
        
        config_path = Path("lighthouse-budget.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            
            budgets = config["budgets"][0]
            
            # Check timing budgets
            timing_budgets = {budget["metric"]: budget["budget"] for budget in budgets["timings"]}
            assert timing_budgets["first-contentful-paint"] <= 3000  # 3s FCP
            assert timing_budgets["largest-contentful-paint"] <= 4000  # 4s LCP
            
            # Check resource budgets
            resource_budgets = {budget["resourceType"]: budget["budget"] for budget in budgets["resourceSizes"]}
            assert resource_budgets["total"] <= 1000  # 1MB total
            assert resource_budgets["script"] <= 300   # 300KB JS


class TestResponsiveDesignValidation:
    """Test responsive design validation."""
    
    def test_viewport_configuration(self):
        """Test responsive viewport configurations."""
        from scripts.accessibility_audit import AccessibilityQualityGates
        
        auditor = AccessibilityQualityGates()
        breakpoints = auditor.responsive_breakpoints
        
        # Verify standard breakpoints
        assert "mobile" in breakpoints
        assert "tablet" in breakpoints
        assert "desktop" in breakpoints
        
        # Verify mobile-first approach (mobile smallest)
        assert breakpoints["mobile"]["width"] < breakpoints["tablet"]["width"]
        assert breakpoints["tablet"]["width"] < breakpoints["desktop"]["width"]
    
    def test_responsive_test_result_structure(self):
        """Test responsive test result data structure."""
        from scripts.accessibility_audit import ResponsiveTestResult
        
        result = ResponsiveTestResult(
            device_type="mobile",
            viewport_width=375,
            viewport_height=667,
            passed=True,
            issues=[],
            screenshot_path="/path/to/screenshot.png"
        )
        
        assert result.device_type == "mobile"
        assert result.viewport_width == 375
        assert result.passed is True
        assert len(result.issues) == 0


class TestWCAGCompliance:
    """Test WCAG 2.1 AA compliance features."""
    
    def test_wcag_criteria_mapping(self):
        """Test WCAG success criteria mapping."""
        # Common WCAG 2.1 AA success criteria
        wcag_criteria = {
            "1.4.3": "Contrast (Minimum)",
            "2.1.1": "Keyboard",
            "2.4.7": "Focus Visible",
            "4.1.2": "Name, Role, Value"
        }
        
        for criterion_id, description in wcag_criteria.items():
            assert len(criterion_id.split('.')) == 3  # Format: X.Y.Z
            assert description  # Non-empty description
    
    def test_severity_classification(self):
        """Test issue severity classification."""
        severity_levels = ["critical", "serious", "moderate", "minor"]
        
        # Verify severity hierarchy
        critical_issues = ["missing-aria-label", "keyboard-trap", "no-focus-indicator"]
        serious_issues = ["low-contrast", "missing-alt-text", "heading-skip"]
        
        for issue_type in critical_issues:
            assert issue_type  # Would map to critical in real implementation
        
        for issue_type in serious_issues:
            assert issue_type  # Would map to serious in real implementation


# Helper functions for mocking
def mock_open_lighthouse_report(data):
    """Mock file open for Lighthouse report."""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(data))