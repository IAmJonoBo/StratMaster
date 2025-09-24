#!/usr/bin/env python3
"""
Performance Regression Detection Script
Implements regression comparison as identified in GAP_ANALYSIS.md accessibility section
"""

import json
import os
import sys
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import argparse


class PerformanceRegressionDetector:
    """Detect performance and accessibility regressions between runs."""
    
    def __init__(self, threshold_performance: float = 2.0, threshold_accessibility: float = 5.0):
        self.threshold_performance = threshold_performance  # % degradation threshold
        self.threshold_accessibility = threshold_accessibility  # Score degradation threshold
        
        # Core Web Vitals targets from GAP_ANALYSIS.md
        self.cwv_targets = {
            'lcp': 2500,    # LCP ≤ 2.5s target
            'inp': 200,     # INP ≤ 200ms target
            'cls': 0.1,     # CLS ≤ 0.1 target
            'fcp': 1800,    # First Contentful Paint
            'tbt': 200      # Total Blocking Time
        }
        
        # Accessibility score targets
        self.accessibility_targets = {
            'accessibility': 95,  # WCAG 2.2 AA target
            'best_practices': 90,
            'seo': 85
        }
    
    def load_lighthouse_report(self, report_path: str) -> Optional[Dict[str, Any]]:
        """Load and parse a Lighthouse JSON report."""
        try:
            report_file = Path(report_path)
            if not report_file.exists():
                print(f"Warning: Report file not found: {report_path}")
                return None
                
            with open(report_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading report {report_path}: {e}")
            return None
    
    def extract_metrics(self, lighthouse_report: Dict[str, Any]) -> Dict[str, float]:
        """Extract key metrics from Lighthouse report."""
        metrics = {}
        
        if not lighthouse_report:
            return metrics
        
        # Extract Core Web Vitals and performance metrics
        audits = lighthouse_report.get('audits', {})
        
        # Core Web Vitals
        lcp_audit = audits.get('largest-contentful-paint', {})
        if 'numericValue' in lcp_audit:
            metrics['lcp'] = lcp_audit['numericValue']
            
        inp_audit = audits.get('interactive', {})  # Approximation for INP
        if 'numericValue' in inp_audit:
            metrics['inp'] = inp_audit['numericValue']
            
        cls_audit = audits.get('cumulative-layout-shift', {})
        if 'numericValue' in cls_audit:
            metrics['cls'] = cls_audit['numericValue']
            
        fcp_audit = audits.get('first-contentful-paint', {})
        if 'numericValue' in fcp_audit:
            metrics['fcp'] = fcp_audit['numericValue']
            
        tbt_audit = audits.get('total-blocking-time', {})
        if 'numericValue' in tbt_audit:
            metrics['tbt'] = tbt_audit['numericValue']
        
        # Extract category scores
        categories = lighthouse_report.get('categories', {})
        
        for category_name in ['performance', 'accessibility', 'best-practices', 'seo']:
            category_data = categories.get(category_name, {})
            if 'score' in category_data and category_data['score'] is not None:
                metrics[category_name.replace('-', '_')] = category_data['score'] * 100
        
        return metrics
    
    def compare_metrics(self, current: Dict[str, float], baseline: Dict[str, float]) -> Dict[str, Any]:
        """Compare current metrics against baseline and detect regressions."""
        comparison = {
            'regressions': [],
            'improvements': [], 
            'stable': [],
            'overall_regression': False,
            'regression_severity': 'none'
        }
        
        # Check each metric
        all_metrics = set(current.keys()) | set(baseline.keys())
        
        for metric_name in all_metrics:
            current_value = current.get(metric_name)
            baseline_value = baseline.get(metric_name)
            
            if current_value is None or baseline_value is None:
                continue
            
            # Calculate percentage change
            if baseline_value == 0:
                percent_change = 0 if current_value == 0 else float('inf')
            else:
                percent_change = ((current_value - baseline_value) / baseline_value) * 100
            
            metric_result = {
                'metric': metric_name,
                'current': current_value,
                'baseline': baseline_value,
                'change_percent': percent_change,
                'change_absolute': current_value - baseline_value
            }
            
            # Determine if this is a regression based on metric type
            is_regression = self._is_regression(metric_name, percent_change, current_value, baseline_value)
            
            if is_regression:
                severity = self._get_regression_severity(metric_name, percent_change, current_value)
                metric_result['severity'] = severity
                comparison['regressions'].append(metric_result)
                
                if severity in ['critical', 'major']:
                    comparison['overall_regression'] = True
                    if comparison['regression_severity'] == 'none':
                        comparison['regression_severity'] = severity
                    elif severity == 'critical':
                        comparison['regression_severity'] = 'critical'
                        
            elif percent_change < -self.threshold_performance:  # Improvement
                comparison['improvements'].append(metric_result)
            else:
                comparison['stable'].append(metric_result)
        
        return comparison
    
    def _is_regression(self, metric_name: str, percent_change: float, current_value: float, baseline_value: float) -> bool:
        """Determine if a metric change constitutes a regression."""
        
        # For performance metrics (lower is better)
        if metric_name in ['lcp', 'inp', 'cls', 'fcp', 'tbt']:
            # Check against absolute targets first
            target = self.cwv_targets.get(metric_name, float('inf'))
            if current_value > target and baseline_value <= target:
                return True  # Crossed threshold - definite regression
            
            # Check percentage degradation
            return percent_change > self.threshold_performance
        
        # For score metrics (higher is better)
        elif metric_name in ['performance', 'accessibility', 'best_practices', 'seo']:
            # Check against absolute targets
            target = self.accessibility_targets.get(metric_name, 0)
            if current_value < target and baseline_value >= target:
                return True  # Fell below threshold
            
            # Check percentage degradation (negative change is bad for scores)
            return percent_change < -self.threshold_accessibility
        
        # Default: use performance threshold
        return percent_change > self.threshold_performance
    
    def _get_regression_severity(self, metric_name: str, percent_change: float, current_value: float) -> str:
        """Determine severity of regression."""
        
        # Critical regressions
        if metric_name == 'lcp' and current_value > 4000:  # > 4s is critical
            return 'critical'
        elif metric_name == 'inp' and current_value > 500:  # > 500ms is critical
            return 'critical'
        elif metric_name == 'accessibility' and current_value < 80:  # < 80 is critical
            return 'critical'
        elif abs(percent_change) > 25:  # > 25% change is critical
            return 'critical'
        
        # Major regressions
        elif abs(percent_change) > 10:  # > 10% change is major
            return 'major'
        
        # Minor regressions
        else:
            return 'minor'
    
    def generate_baseline(self, reports_dir: str, output_file: str) -> bool:
        """Generate baseline from multiple reports (typically from main branch)."""
        reports_path = Path(reports_dir)
        if not reports_path.exists():
            print(f"Reports directory not found: {reports_dir}")
            return False
        
        # Collect all metrics from reports
        all_metrics = []
        report_files = list(reports_path.glob('*.json'))
        
        if not report_files:
            print(f"No JSON reports found in {reports_dir}")
            return False
        
        for report_file in report_files:
            report = self.load_lighthouse_report(report_file)
            if report:
                metrics = self.extract_metrics(report)
                if metrics:
                    all_metrics.append(metrics)
        
        if not all_metrics:
            print("No valid metrics found in reports")
            return False
        
        # Calculate baseline (median of all runs)
        baseline = {}
        all_metric_names = set()
        for metrics in all_metrics:
            all_metric_names.update(metrics.keys())
        
        for metric_name in all_metric_names:
            values = [m[metric_name] for m in all_metrics if metric_name in m]
            if values:
                baseline[metric_name] = statistics.median(values)
        
        # Save baseline
        baseline_data = {
            'timestamp': '2024-01-01T00:00:00Z',  # Would use actual timestamp
            'source': 'main-branch',
            'sample_size': len(all_metrics),
            'metrics': baseline,
            'cwv_targets': self.cwv_targets,
            'accessibility_targets': self.accessibility_targets
        }
        
        with open(output_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        print(f"Baseline generated with {len(all_metrics)} samples: {output_file}")
        return True
    
    def detect_regressions(self, current_reports_dir: str, baseline_file: str, output_file: str) -> Dict[str, Any]:
        """Main regression detection function."""
        
        # Load baseline
        try:
            with open(baseline_file) as f:
                baseline_data = json.load(f)
                baseline_metrics = baseline_data.get('metrics', {})
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading baseline: {e}")
            return {'error': 'Failed to load baseline'}
        
        # Load current reports
        current_reports = []
        reports_path = Path(current_reports_dir)
        
        for report_file in reports_path.glob('*.json'):
            report = self.load_lighthouse_report(report_file)
            if report:
                metrics = self.extract_metrics(report)
                if metrics:
                    current_reports.append({
                        'file': report_file.name,
                        'metrics': metrics
                    })
        
        if not current_reports:
            print("No current reports found")
            return {'error': 'No current reports to analyze'}
        
        # Calculate current metrics (median if multiple reports)
        if len(current_reports) == 1:
            current_metrics = current_reports[0]['metrics']
        else:
            # Calculate median across all current reports
            current_metrics = {}
            all_metric_names = set()
            for report in current_reports:
                all_metric_names.update(report['metrics'].keys())
            
            for metric_name in all_metric_names:
                values = [r['metrics'][metric_name] for r in current_reports if metric_name in r['metrics']]
                if values:
                    current_metrics[metric_name] = statistics.median(values)
        
        # Perform comparison
        comparison = self.compare_metrics(current_metrics, baseline_metrics)
        
        # Build result
        result = {
            'timestamp': '2024-01-01T00:00:00Z',  # Would use actual timestamp
            'baseline_source': baseline_data.get('source', 'unknown'),
            'current_reports_count': len(current_reports),
            'comparison': comparison,
            'current_metrics': current_metrics,
            'baseline_metrics': baseline_metrics,
            'targets_met': self._check_targets(current_metrics),
            'recommendations': self._generate_recommendations(comparison, current_metrics)
        }
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _check_targets(self, metrics: Dict[str, float]) -> Dict[str, bool]:
        """Check if current metrics meet targets."""
        targets_met = {}
        
        # Check Core Web Vitals targets
        for metric, target in self.cwv_targets.items():
            if metric in metrics:
                targets_met[metric] = metrics[metric] <= target
        
        # Check accessibility targets  
        for metric, target in self.accessibility_targets.items():
            if metric in metrics:
                targets_met[metric] = metrics[metric] >= target
        
        return targets_met
    
    def _generate_recommendations(self, comparison: Dict[str, Any], current_metrics: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations based on regression analysis."""
        recommendations = []
        
        regressions = comparison.get('regressions', [])
        critical_regressions = [r for r in regressions if r.get('severity') == 'critical']
        
        if critical_regressions:
            recommendations.append("🚨 CRITICAL: Performance regressions detected that require immediate attention")
            
            for reg in critical_regressions:
                metric = reg['metric']
                if metric == 'lcp':
                    recommendations.append(f"• LCP regression: {reg['current']:.0f}ms (target: ≤2500ms). Optimize images, reduce server response time, eliminate render-blocking resources")
                elif metric == 'inp':
                    recommendations.append(f"• INP regression: {reg['current']:.0f}ms (target: ≤200ms). Optimize JavaScript execution, reduce input delay")
                elif metric == 'accessibility':
                    recommendations.append(f"• Accessibility score dropped to {reg['current']:.1f}% (target: ≥95%). Run accessibility audit to identify specific issues")
        
        elif regressions:
            recommendations.append("⚠️ Performance regressions detected that should be reviewed")
            
        improvements = comparison.get('improvements', [])
        if improvements:
            recommendations.append(f"✅ Performance improvements detected in {len(improvements)} metrics")
        
        # Check specific targets
        if 'lcp' in current_metrics and current_metrics['lcp'] > self.cwv_targets['lcp']:
            recommendations.append("• LCP exceeds target: Consider optimizing largest content element, improving server performance")
        
        if 'inp' in current_metrics and current_metrics['inp'] > self.cwv_targets['inp']:
            recommendations.append("• INP exceeds target: Optimize event handlers, reduce JavaScript execution time")
        
        if not recommendations:
            recommendations.append("✅ No significant performance regressions detected")
        
        return recommendations
    
    def _print_summary(self, result: Dict[str, Any]) -> None:
        """Print regression detection summary."""
        comparison = result['comparison']
        
        print("\n📊 Performance Regression Detection Summary")
        print("=" * 50)
        
        if comparison['overall_regression']:
            print(f"🚨 REGRESSION DETECTED - Severity: {comparison['regression_severity'].upper()}")
        else:
            print("✅ No significant regressions detected")
        
        print(f"\nBaseline: {result['baseline_source']}")
        print(f"Current reports analyzed: {result['current_reports_count']}")
        
        regressions = comparison['regressions']
        improvements = comparison['improvements']
        
        if regressions:
            print(f"\n❌ Regressions ({len(regressions)}):")
            for reg in regressions:
                severity_emoji = {'critical': '🚨', 'major': '⚠️', 'minor': '📉'}.get(reg.get('severity', 'minor'), '📉')
                print(f"  {severity_emoji} {reg['metric']}: {reg['current']:.1f} ({reg['change_percent']:+.1f}%)")
        
        if improvements:
            print(f"\n✅ Improvements ({len(improvements)}):")
            for imp in improvements[:3]:  # Show top 3
                print(f"  📈 {imp['metric']}: {imp['current']:.1f} ({imp['change_percent']:+.1f}%)")
        
        print(f"\n📋 Recommendations:")
        for rec in result['recommendations']:
            print(f"  {rec}")


def main():
    parser = argparse.ArgumentParser(description='Performance Regression Detection')
    parser.add_argument('--mode', choices=['generate-baseline', 'detect'], required=True,
                       help='Mode: generate-baseline or detect')
    parser.add_argument('--current-reports', help='Directory containing current Lighthouse reports')  
    parser.add_argument('--baseline-file', help='Baseline file path')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--performance-threshold', type=float, default=2.0,
                       help='Performance regression threshold percentage (default: 2.0)')
    parser.add_argument('--accessibility-threshold', type=float, default=5.0,
                       help='Accessibility regression threshold percentage (default: 5.0)')
    
    args = parser.parse_args()
    
    detector = PerformanceRegressionDetector(
        threshold_performance=args.performance_threshold,
        threshold_accessibility=args.accessibility_threshold
    )
    
    if args.mode == 'generate-baseline':
        if not args.current_reports or not args.output:
            print("Error: --current-reports and --output required for generate-baseline mode")
            return 1
        
        success = detector.generate_baseline(args.current_reports, args.output)
        return 0 if success else 1
    
    elif args.mode == 'detect':
        if not all([args.current_reports, args.baseline_file, args.output]):
            print("Error: --current-reports, --baseline-file, and --output required for detect mode")
            return 1
        
        result = detector.detect_regressions(args.current_reports, args.baseline_file, args.output)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            return 1
        
        # Return non-zero exit code if critical regressions detected
        if result['comparison']['overall_regression']:
            severity = result['comparison']['regression_severity']
            if severity == 'critical':
                return 2  # Critical regression
            else:
                return 1  # Non-critical regression
        
        return 0  # No regressions


if __name__ == '__main__':
    sys.exit(main())