#!/usr/bin/env python3
"""
CI Flake Detection and Quarantine System
Implements automated flake detection as identified in GAP_ANALYSIS.md
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import subprocess
import re


class FlakeDetector:
    """Detect and manage flaky tests in CI pipeline."""
    
    def __init__(self, quarantine_file: str = "flaky_tests.json"):
        self.quarantine_file = Path(quarantine_file)
        self.quarantine_data = self._load_quarantine_data()
        self.test_results = []
        self.flaky_tests = set()
        
    def _load_quarantine_data(self) -> Dict[str, Any]:
        """Load existing quarantine data."""
        if self.quarantine_file.exists():
            try:
                with open(self.quarantine_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            'quarantined_tests': {},
            'flake_history': {},
            'last_updated': None,
            'stats': {
                'total_quarantined': 0,
                'false_positives': 0,
                'recovered_tests': 0
            }
        }
    
    def _save_quarantine_data(self) -> None:
        """Save quarantine data to file."""
        self.quarantine_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        with open(self.quarantine_file, 'w') as f:
            json.dump(self.quarantine_data, f, indent=2)
    
    def run_tests_with_retry(self, test_command: str, retry_count: int = 3) -> Dict[str, Any]:
        """Run tests with retry logic and collect flake data."""
        print(f"🧪 Running tests with flake detection: {test_command}")
        
        all_results = []
        final_result = None
        
        for attempt in range(retry_count):
            print(f"\n🔄 Attempt {attempt + 1}/{retry_count}")
            
            result = self._run_single_test_session(test_command, attempt)
            all_results.append(result)
            
            if result['success']:
                final_result = result
                if attempt > 0:
                    print(f"✅ Tests passed on retry {attempt + 1} - potential flakes detected")
                break
            else:
                print(f"❌ Tests failed on attempt {attempt + 1}")
                
            # Don't retry on the last attempt
            if attempt < retry_count - 1:
                time.sleep(2)  # Brief pause between retries
        
        # If no successful runs, use the last result
        if final_result is None:
            final_result = all_results[-1]
        
        # Analyze for flakes
        flake_analysis = self._analyze_flakes(all_results)
        final_result['flake_analysis'] = flake_analysis
        
        return final_result
    
    def _run_single_test_session(self, test_command: str, attempt: int) -> Dict[str, Any]:
        """Run a single test session and capture results."""
        start_time = time.time()
        
        try:
            # Run the test command and capture output
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            
            # Parse test results
            parsed_results = self._parse_test_output(result.stdout + result.stderr)
            
            return {
                'attempt': attempt,
                'success': result.returncode == 0,
                'duration': duration,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'parsed_results': parsed_results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'attempt': attempt,
                'success': False,
                'duration': time.time() - start_time,
                'returncode': -1,
                'error': 'Test execution timed out',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'attempt': attempt,
                'success': False,
                'duration': time.time() - start_time,
                'returncode': -1,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        results = {
            'passed': [],
            'failed': [],
            'errors': [],
            'skipped': [],
            'total_tests': 0
        }
        
        # Look for pytest result lines
        # Pattern: test_file.py::test_function PASSED/FAILED/ERROR/SKIPPED
        test_pattern = re.compile(
            r'([^\s]+\.py::[^\s]+)\s+(PASSED|FAILED|ERROR|SKIPPED)',
            re.MULTILINE
        )
        
        matches = test_pattern.findall(output)
        
        for test_name, status in matches:
            status_lower = status.lower()
            if status_lower in results:
                results[status_lower].append(test_name)
        
        results['total_tests'] = len(matches)
        
        # Extract summary line if present
        summary_pattern = re.compile(
            r'=+\s*(?:(\d+)\s+failed,?\s*)?(?:(\d+)\s+passed,?\s*)?(?:(\d+)\s+skipped,?\s*)?(?:(\d+)\s+error)?',
            re.MULTILINE
        )
        
        summary_match = summary_pattern.search(output)
        if summary_match:
            failed, passed, skipped, errors = summary_match.groups()
            results['summary'] = {
                'failed': int(failed) if failed else 0,
                'passed': int(passed) if passed else 0,
                'skipped': int(skipped) if skipped else 0,
                'errors': int(errors) if errors else 0
            }
        
        return results
    
    def _analyze_flakes(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test results to identify flaky tests."""
        if len(all_results) < 2:
            return {'flaky_tests': [], 'analysis': 'Insufficient retry attempts for flake detection'}
        
        # Collect test results across attempts
        test_outcomes = {}
        
        for result in all_results:
            if 'parsed_results' in result:
                parsed = result['parsed_results']
                
                # Track each test's outcomes
                for status in ['passed', 'failed', 'errors']:
                    for test_name in parsed.get(status, []):
                        if test_name not in test_outcomes:
                            test_outcomes[test_name] = []
                        test_outcomes[test_name].append(status)
        
        # Identify flaky tests (different outcomes across runs)
        flaky_tests = []
        for test_name, outcomes in test_outcomes.items():
            unique_outcomes = set(outcomes)
            if len(unique_outcomes) > 1:
                flaky_tests.append({
                    'test_name': test_name,
                    'outcomes': outcomes,
                    'flake_pattern': f"{'/'.join(outcomes)}"
                })
        
        # Update historical flake data
        for flaky_test in flaky_tests:
            test_name = flaky_test['test_name']
            if test_name not in self.quarantine_data['flake_history']:
                self.quarantine_data['flake_history'][test_name] = {
                    'first_detected': datetime.now(timezone.utc).isoformat(),
                    'flake_count': 0,
                    'patterns': []
                }
            
            self.quarantine_data['flake_history'][test_name]['flake_count'] += 1
            self.quarantine_data['flake_history'][test_name]['patterns'].append({
                'pattern': flaky_test['flake_pattern'],
                'detected_at': datetime.now(timezone.utc).isoformat()
            })
        
        analysis = {
            'flaky_tests': flaky_tests,
            'total_flaky': len(flaky_tests),
            'retry_attempts': len(all_results),
            'final_success': all_results[-1]['success'] if all_results else False
        }
        
        if flaky_tests:
            print(f"\n⚠️ Detected {len(flaky_tests)} flaky tests:")
            for flaky_test in flaky_tests:
                print(f"  - {flaky_test['test_name']}: {flaky_test['flake_pattern']}")
        
        return analysis
    
    def quarantine_persistent_flakes(self, threshold: int = 3) -> List[str]:
        """Quarantine tests that have been flaky multiple times."""
        newly_quarantined = []
        
        for test_name, history in self.quarantine_data['flake_history'].items():
            if (history['flake_count'] >= threshold and 
                test_name not in self.quarantine_data['quarantined_tests']):
                
                self.quarantine_data['quarantined_tests'][test_name] = {
                    'quarantined_at': datetime.now(timezone.utc).isoformat(),
                    'reason': f"Persistent flaking (detected {history['flake_count']} times)",
                    'flake_count': history['flake_count']
                }
                newly_quarantined.append(test_name)
        
        if newly_quarantined:
            self.quarantine_data['stats']['total_quarantined'] += len(newly_quarantined)
            print(f"\n🚨 Quarantined {len(newly_quarantined)} persistent flaky tests:")
            for test_name in newly_quarantined:
                print(f"  - {test_name}")
        
        return newly_quarantined
    
    def generate_flake_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive flake detection report."""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_quarantined': len(self.quarantine_data['quarantined_tests']),
                'total_with_flake_history': len(self.quarantine_data['flake_history']),
                'detection_runs': len(self.test_results)
            },
            'quarantined_tests': self.quarantine_data['quarantined_tests'],
            'flake_history': self.quarantine_data['flake_history'],
            'stats': self.quarantine_data['stats']
        }
        
        # Print summary
        print("\n📊 Flake Detection Report")
        print("=" * 40)
        print(f"Tests in quarantine: {report['summary']['total_quarantined']}")
        print(f"Tests with flake history: {report['summary']['total_with_flake_history']}")
        
        if self.quarantine_data['quarantined_tests']:
            print("\n🚨 Quarantined Tests:")
            for test_name, data in self.quarantine_data['quarantined_tests'].items():
                print(f"  - {test_name}")
                print(f"    Reason: {data['reason']}")
                print(f"    Quarantined: {data['quarantined_at']}")
        
        # Export to file
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n📁 Report exported to: {output_path}")
        
        return report
    
    def save_state(self) -> None:
        """Save current flake detection state."""
        self._save_quarantine_data()


def main():
    """Main entry point for flake detection."""
    if len(sys.argv) < 2:
        print("Usage: python flake_detector.py <test_command> [quarantine_file] [--report-only]")
        print("\nExamples:")
        print("  python flake_detector.py 'python -m pytest packages/api/tests/'")
        print("  python flake_detector.py 'make test' flaky_tests.json")
        print("  python flake_detector.py --report-only  # Generate report from existing data")
        return 1
    
    test_command = sys.argv[1]
    quarantine_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "flaky_tests.json"
    report_only = '--report-only' in sys.argv
    
    detector = FlakeDetector(quarantine_file)
    
    if report_only:
        # Just generate report from existing data
        detector.generate_flake_report(f"{quarantine_file.replace('.json', '')}_report.json")
        return 0
    
    # Run tests with flake detection
    try:
        result = detector.run_tests_with_retry(test_command, retry_count=3)
        
        # Quarantine persistent flakes
        detector.quarantine_persistent_flakes(threshold=2)
        
        # Generate report
        detector.generate_flake_report(f"{quarantine_file.replace('.json', '')}_report.json")
        
        # Save state
        detector.save_state()
        
        # Set GitHub Actions outputs
        if os.getenv('GITHUB_ACTIONS'):
            flake_count = result.get('flake_analysis', {}).get('total_flaky', 0)
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
                f.write(f"flaky_tests_detected={flake_count}\n")
                f.write(f"quarantined_tests={len(detector.quarantine_data['quarantined_tests'])}\n")
        
        # Exit with original test result
        return 0 if result['success'] else 1
        
    except Exception as e:
        print(f"💥 Flake detection error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())