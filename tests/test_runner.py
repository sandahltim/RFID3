"""
Comprehensive Test Runner for RFID3 System Validation
=====================================================

Main test runner to execute all test suites and generate comprehensive
validation reports for the RFID3 system improvements.

Date: 2025-08-28
Author: Testing Specialist
"""

import pytest
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import argparse

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class RFID3TestRunner:
    """Comprehensive test runner for RFID3 system validation."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_directory = Path(__file__).parent
        self.results = {
            'execution_start': datetime.now().isoformat(),
            'test_suites': {},
            'summary': {},
            'recommendations': []
        }
        
        # Define test suites in execution order
        self.test_suites = [
            {
                'name': 'Database Integrity',
                'file': 'test_database_integrity.py',
                'description': 'Validates database correlation fixes and data consistency',
                'priority': 'critical'
            },
            {
                'name': 'API Endpoints',
                'file': 'test_api_endpoints.py',
                'description': 'Tests inventory analytics and enhanced API endpoints',
                'priority': 'critical'
            },
            {
                'name': 'Dashboard Functionality',
                'file': 'test_dashboard_functionality.py',
                'description': 'Validates executive dashboard and cross-tab functionality',
                'priority': 'high'
            },
            {
                'name': 'Data Integration',
                'file': 'test_data_integration.py',
                'description': 'Tests POS data integration and financial calculations',
                'priority': 'high'
            },
            {
                'name': 'Performance Regression',
                'file': 'test_performance_regression.py',
                'description': 'Performance testing and regression prevention',
                'priority': 'medium'
            }
        ]
    
    def run_test_suite(self, suite_info, verbose=False):
        """
        Run a specific test suite and capture results.
        
        Args:
            suite_info (dict): Test suite information
            verbose (bool): Enable verbose output
            
        Returns:
            dict: Test results
        """
        suite_name = suite_info['name']
        test_file = self.test_directory / suite_info['file']
        
        print(f"\n{'='*60}")
        print(f"Running {suite_name} Test Suite")
        print(f"{'='*60}")
        print(f"Description: {suite_info['description']}")
        print(f"Priority: {suite_info['priority']}")
        print(f"File: {suite_info['file']}")
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return {
                'status': 'error',
                'message': f"Test file not found: {test_file}",
                'execution_time': 0
            }
        
        # Prepare pytest command
        pytest_args = [
            str(test_file),
            '--tb=short',  # Short traceback format
            '--disable-warnings',  # Reduce noise
            '-v' if verbose else '-q'  # Verbose or quiet
        ]
        
        # Add JSON report generation
        json_report_file = self.test_directory / f"results_{suite_info['file'].replace('.py', '.json')}"
        pytest_args.extend(['--json-report', f'--json-report-file={json_report_file}'])
        
        start_time = time.time()
        
        try:
            # Run pytest
            result = subprocess.run(
                [sys.executable, '-m', 'pytest'] + pytest_args,
                capture_output=True,
                text=True,
                cwd=self.test_directory.parent
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            suite_results = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'execution_time': round(execution_time, 2),
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            # Try to load JSON report if available
            if json_report_file.exists():
                try:
                    with open(json_report_file, 'r') as f:
                        json_data = json.load(f)
                        suite_results['detailed_results'] = {
                            'tests': json_data.get('tests', []),
                            'summary': json_data.get('summary', {}),
                            'duration': json_data.get('duration', 0)
                        }
                except Exception as e:
                    print(f"⚠️  Warning: Could not parse JSON report: {e}")
            
            # Display results
            if suite_results['status'] == 'passed':
                print(f"✅ {suite_name} - PASSED ({execution_time:.2f}s)")
            else:
                print(f"❌ {suite_name} - FAILED ({execution_time:.2f}s)")
                if verbose:
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
            
            return suite_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {suite_name} - ERROR: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'execution_time': round(execution_time, 2)
            }
    
    def run_all_tests(self, verbose=False, priority_filter=None):
        """
        Run all test suites or filtered by priority.
        
        Args:
            verbose (bool): Enable verbose output
            priority_filter (str): Filter by priority (critical, high, medium)
        """
        print("🚀 Starting RFID3 System Validation Test Suite")
        print(f"Timestamp: {self.results['execution_start']}")
        print(f"Test Directory: {self.test_directory}")
        
        # Filter test suites if priority specified
        suites_to_run = self.test_suites
        if priority_filter:
            suites_to_run = [s for s in self.test_suites if s['priority'] == priority_filter]
            print(f"🎯 Running only {priority_filter} priority tests")
        
        total_start_time = time.time()
        
        # Run each test suite
        for suite_info in suites_to_run:
            suite_results = self.run_test_suite(suite_info, verbose)
            self.results['test_suites'][suite_info['name']] = suite_results
        
        total_execution_time = time.time() - total_start_time
        
        # Generate summary
        self.generate_summary(total_execution_time)
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Display final results
        self.display_final_results()
        
        return self.results
    
    def generate_summary(self, total_execution_time):
        """Generate test execution summary."""
        suite_results = self.results['test_suites']
        
        total_suites = len(suite_results)
        passed_suites = sum(1 for r in suite_results.values() if r['status'] == 'passed')
        failed_suites = sum(1 for r in suite_results.values() if r['status'] == 'failed')
        error_suites = sum(1 for r in suite_results.values() if r['status'] == 'error')
        
        # Calculate detailed test counts if available
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for suite_result in suite_results.values():
            if 'detailed_results' in suite_result:
                summary = suite_result['detailed_results'].get('summary', {})
                total_tests += summary.get('total', 0)
                passed_tests += summary.get('passed', 0)
                failed_tests += summary.get('failed', 0)
                skipped_tests += summary.get('skipped', 0)
        
        self.results['summary'] = {
            'total_execution_time': round(total_execution_time, 2),
            'suites': {
                'total': total_suites,
                'passed': passed_suites,
                'failed': failed_suites,
                'error': error_suites,
                'success_rate': round((passed_suites / total_suites) * 100, 2) if total_suites > 0 else 0
            },
            'tests': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'success_rate': round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
            }
        }
    
    def generate_recommendations(self):
        """Generate recommendations based on test results."""
        suite_results = self.results['test_suites']
        recommendations = []
        
        # Check for critical failures
        critical_failures = []
        high_priority_failures = []
        
        for suite_name, result in suite_results.items():
            suite_info = next((s for s in self.test_suites if s['name'] == suite_name), None)
            if suite_info and result['status'] in ['failed', 'error']:
                if suite_info['priority'] == 'critical':
                    critical_failures.append(suite_name)
                elif suite_info['priority'] == 'high':
                    high_priority_failures.append(suite_name)
        
        # Generate specific recommendations
        if critical_failures:
            recommendations.append({
                'priority': 'CRITICAL',
                'title': 'Critical Test Failures Detected',
                'description': f"The following critical test suites failed: {', '.join(critical_failures)}. "
                              "These issues must be resolved before deployment.",
                'action': 'Fix critical issues immediately and re-run tests'
            })
        
        if high_priority_failures:
            recommendations.append({
                'priority': 'HIGH',
                'title': 'High Priority Test Failures',
                'description': f"The following high priority test suites failed: {', '.join(high_priority_failures)}. "
                              "These should be addressed before production deployment.",
                'action': 'Review and fix high priority issues'
            })
        
        # Performance recommendations
        slow_suites = [
            name for name, result in suite_results.items()
            if result.get('execution_time', 0) > 30  # Suites taking more than 30 seconds
        ]
        
        if slow_suites:
            recommendations.append({
                'priority': 'MEDIUM',
                'title': 'Performance Optimization Opportunity',
                'description': f"The following test suites took longer than expected: {', '.join(slow_suites)}. "
                              "Consider optimizing test execution or the underlying code.",
                'action': 'Investigate and optimize slow test suites'
            })
        
        # Success recommendations
        if not critical_failures and not high_priority_failures:
            recommendations.append({
                'priority': 'INFO',
                'title': 'System Validation Successful',
                'description': "All critical and high priority tests passed. The RFID3 system improvements "
                              "appear to be functioning correctly.",
                'action': 'Proceed with deployment confidence'
            })
        
        self.results['recommendations'] = recommendations
    
    def display_final_results(self):
        """Display final test results and summary."""
        print("\n" + "="*80)
        print("🎯 RFID3 SYSTEM VALIDATION RESULTS")
        print("="*80)
        
        summary = self.results['summary']
        
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"   Total Execution Time: {summary['total_execution_time']}s")
        print(f"   Test Suites: {summary['suites']['passed']}/{summary['suites']['total']} passed "
              f"({summary['suites']['success_rate']}%)")
        
        if summary['tests']['total'] > 0:
            print(f"   Individual Tests: {summary['tests']['passed']}/{summary['tests']['total']} passed "
                  f"({summary['tests']['success_rate']}%)")
        
        # Display suite-by-suite results
        print(f"\n📋 SUITE RESULTS:")
        for suite_name, result in self.results['test_suites'].items():
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"   {status_icon} {suite_name}: {result['status'].upper()} "
                  f"({result['execution_time']}s)")
        
        # Display recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in self.results['recommendations']:
            priority_icons = {
                'CRITICAL': '🚨',
                'HIGH': '⚠️',
                'MEDIUM': '📝',
                'INFO': 'ℹ️'
            }
            icon = priority_icons.get(rec['priority'], '📝')
            print(f"   {icon} [{rec['priority']}] {rec['title']}")
            print(f"      {rec['description']}")
            print(f"      Action: {rec['action']}\n")
        
        # Overall status
        if summary['suites']['failed'] == 0 and summary['suites']['error'] == 0:
            print("🎉 OVERALL STATUS: ALL SYSTEMS GO! ✅")
        elif any(rec['priority'] == 'CRITICAL' for rec in self.results['recommendations']):
            print("🚨 OVERALL STATUS: CRITICAL ISSUES - DO NOT DEPLOY ❌")
        else:
            print("⚠️  OVERALL STATUS: SOME ISSUES FOUND - REVIEW BEFORE DEPLOYMENT 🔄")
        
        print("="*80)
    
    def save_results_to_file(self, filename=None):
        """Save test results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"rfid3_test_results_{timestamp}.json"
        
        results_file = self.test_directory / filename
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\n💾 Test results saved to: {results_file}")
            return str(results_file)
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
            return None


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='RFID3 System Validation Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--priority', choices=['critical', 'high', 'medium'],
                        help='Run only tests of specified priority')
    parser.add_argument('--save-results', action='store_true',
                        help='Save test results to JSON file')
    parser.add_argument('--output-file', 
                        help='Specify output file for results')
    
    args = parser.parse_args()
    
    # Initialize and run tests
    runner = RFID3TestRunner()
    results = runner.run_all_tests(
        verbose=args.verbose,
        priority_filter=args.priority
    )
    
    # Save results if requested
    if args.save_results:
        runner.save_results_to_file(args.output_file)
    
    # Exit with appropriate code
    if results['summary']['suites']['failed'] > 0 or results['summary']['suites']['error'] > 0:
        # Check if any critical failures
        critical_failures = any(
            rec['priority'] == 'CRITICAL' for rec in results['recommendations']
        )
        exit_code = 2 if critical_failures else 1
    else:
        exit_code = 0
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()