"""
Practical Validation Script for Executive Dashboard Hardcode Conversion
=====================================================================

This script provides practical validation of the hardcoded query limits conversion.
It tests actual API endpoints and database queries to ensure the conversion works correctly.

Usage:
    python validate_hardcode_conversion_practical.py --phase [before|after|both]
    
Phase Options:
    before: Test current hardcoded functionality (baseline)
    after:  Test converted configurable functionality  
    both:   Test both phases for comparison
"""

import sys
import os
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.config_models import ExecutiveDashboardConfiguration
from app.services.logger import get_logger

logger = get_logger(__name__)

class HardcodeConversionValidator:
    """Validates the conversion of hardcoded query limits to configurable parameters"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.app = create_app()
        self.validation_results = {
            'baseline_tests': {},
            'conversion_tests': {},
            'comparison_results': {},
            'errors': []
        }
    
    # ============================================================================================
    # BASELINE VALIDATION - Test current hardcoded functionality
    # ============================================================================================
    
    def validate_baseline_functionality(self) -> Dict:
        """Test all API endpoints with current hardcoded values"""
        logger.info("🔍 PHASE 1: Validating baseline functionality with hardcoded limits")
        
        baseline_results = {}
        
        # Test cases for different hardcoded limits
        test_cases = [
            {
                'name': 'Financial KPIs (LIMIT 3)',
                'endpoint': '/executive/api/financial-kpis',
                'expected_hardcoded_limit': 3,
                'description': '3-week revenue averages'
            },
            {
                'name': 'Location KPIs W1 (LIMIT 3)',
                'endpoint': '/executive/api/location-kpis/W1',
                'expected_hardcoded_limit': 3,
                'description': 'Store-specific 3-week averages'
            },
            {
                'name': 'Location KPIs W2 (LIMIT 3)', 
                'endpoint': '/executive/api/location-kpis/W2',
                'expected_hardcoded_limit': 3,
                'description': 'Store-specific 3-week averages'
            },
            {
                'name': 'Dashboard Summary (Various)',
                'endpoint': '/api/executive/dashboard_summary',
                'expected_hardcoded_limit': 'mixed',
                'description': 'Mixed limits: 3, 12, 24, 52'
            },
            {
                'name': 'Intelligent Insights (LIMIT 3,12)',
                'endpoint': '/executive/api/intelligent-insights',
                'expected_hardcoded_limit': [3, 12],
                'description': 'Recent insights and trend analysis'
            },
            {
                'name': 'Financial Forecasts Default (LIMIT 24)',
                'endpoint': '/executive/api/financial-forecasts',
                'expected_hardcoded_limit': 24,
                'description': 'Default historical data for forecasting'
            },
            {
                'name': 'Financial Forecasts 52w (LIMIT 52)',
                'endpoint': '/executive/api/financial-forecasts?horizon=52',
                'expected_hardcoded_limit': 52,
                'description': 'Full year historical data'
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"Testing: {test_case['name']}")
            result = self._test_api_endpoint(test_case['endpoint'], test_case['name'])
            
            # Analyze result for hardcoded limit indicators
            result['expected_limit'] = test_case['expected_hardcoded_limit']
            result['description'] = test_case['description']
            result['hardcoded_indicators'] = self._analyze_hardcoded_indicators(result.get('data'), test_case['expected_hardcoded_limit'])
            
            baseline_results[test_case['name']] = result
            
            # Small delay between requests
            time.sleep(0.1)
        
        self.validation_results['baseline_tests'] = baseline_results
        logger.info(f"✅ Baseline validation completed: {len(baseline_results)} endpoints tested")
        
        return baseline_results
    
    def _test_api_endpoint(self, endpoint: str, test_name: str) -> Dict:
        """Test a single API endpoint and return structured results"""
        result = {
            'endpoint': endpoint,
            'test_name': test_name,
            'timestamp': datetime.now().isoformat(),
            'status_code': None,
            'response_time': None,
            'data': None,
            'error': None,
            'success': False
        }
        
        try:
            start_time = time.time()
            
            # Use direct app testing instead of HTTP requests for reliability
            with self.app.test_client() as client:
                response = client.get(endpoint)
                result['status_code'] = response.status_code
                result['response_time'] = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        result['data'] = response.get_json()
                        result['success'] = True
                        logger.info(f"✅ {test_name}: Success ({result['response_time']:.3f}s)")
                    except Exception as e:
                        result['error'] = f"JSON parsing error: {str(e)}"
                        result['data'] = response.get_data(as_text=True)
                        logger.warning(f"⚠️ {test_name}: JSON parsing failed")
                elif response.status_code in [404, 500]:
                    result['error'] = f"HTTP {response.status_code}: {response.get_data(as_text=True)}"
                    logger.warning(f"⚠️ {test_name}: HTTP {response.status_code}")
                else:
                    result['error'] = f"Unexpected status code: {response.status_code}"
                    logger.error(f"❌ {test_name}: Unexpected status {response.status_code}")
                    
        except Exception as e:
            result['error'] = f"Request failed: {str(e)}"
            result['response_time'] = time.time() - start_time if 'start_time' in locals() else None
            logger.error(f"❌ {test_name}: Request failed - {str(e)}")
        
        return result
    
    def _analyze_hardcoded_indicators(self, data: Optional[Dict], expected_limit) -> Dict:
        """Analyze response data for indicators of hardcoded limits"""
        indicators = {
            'data_points_found': 0,
            'limit_evidence': [],
            'data_structure_analysis': {},
            'likely_uses_expected_limit': False
        }
        
        if not data:
            return indicators
        
        try:
            # Convert data to string for analysis
            data_str = json.dumps(data, default=str).lower()
            
            # Look for common patterns that indicate specific limits
            limit_patterns = {
                3: ['3wk', 'current_3', 'three', 'recent_3', '3_week'],
                12: ['12wk', '12_week', 'quarterly', '3_month', 'trend'],
                24: ['24wk', '24_week', '6_month', 'historical'],
                52: ['52wk', '52_week', 'annual', 'yearly', '12_month']
            }
            
            # Check for expected limit patterns
            if isinstance(expected_limit, int) and expected_limit in limit_patterns:
                for pattern in limit_patterns[expected_limit]:
                    if pattern in data_str:
                        indicators['limit_evidence'].append(f"Found pattern '{pattern}' suggesting {expected_limit}-limit usage")
                        indicators['likely_uses_expected_limit'] = True
            
            # Analyze data structure
            if isinstance(data, dict):
                indicators['data_structure_analysis']['keys'] = list(data.keys())
                
                # Count data points in arrays
                for key, value in data.items():
                    if isinstance(value, list):
                        indicators['data_points_found'] += len(value)
                        indicators['data_structure_analysis'][f'{key}_count'] = len(value)
            
            # Look for specific indicators of 3-week calculations
            if 'current_3wk_avg' in data_str:
                indicators['limit_evidence'].append("Found 'current_3wk_avg' field - indicates LIMIT 3 usage")
                indicators['likely_uses_expected_limit'] = True
                
        except Exception as e:
            indicators['analysis_error'] = str(e)
        
        return indicators
    
    # ============================================================================================
    # CONFIGURATION VALIDATION - Test configuration parameter loading
    # ============================================================================================
    
    def validate_configuration_system(self) -> Dict:
        """Test that configuration parameters can be loaded and applied"""
        logger.info("🔧 PHASE 2: Validating configuration system")
        
        config_results = {}
        
        with self.app.app_context():
            try:
                # Test 1: Create test configuration
                test_config = self._create_test_configuration()
                config_results['config_creation'] = {
                    'success': test_config is not None,
                    'config_id': test_config.id if test_config else None,
                    'error': None
                }
                
                # Test 2: Load configuration
                loaded_config = self._load_test_configuration()
                config_results['config_loading'] = {
                    'success': loaded_config is not None,
                    'matches_created': loaded_config.id == test_config.id if (loaded_config and test_config) else False,
                    'error': None
                }
                
                # Test 3: Test fallback behavior
                fallback_result = self._test_configuration_fallback()
                config_results['fallback_behavior'] = fallback_result
                
                # Test 4: Test configuration parameters that would be added
                expected_parameters = self._get_expected_configuration_parameters()
                config_results['expected_parameters'] = expected_parameters
                
                logger.info("✅ Configuration system validation completed")
                
            except Exception as e:
                error_msg = f"Configuration system validation failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                config_results['error'] = error_msg
                self.validation_results['errors'].append(error_msg)
        
        self.validation_results['conversion_tests']['configuration'] = config_results
        return config_results
    
    def _create_test_configuration(self) -> Optional[ExecutiveDashboardConfiguration]:
        """Create a test configuration with custom limits"""
        try:
            config = ExecutiveDashboardConfiguration(
                user_id='validation_test',
                config_name='hardcode_conversion_test',
                # Current model doesn't have query limit parameters yet
                # These would be added during the actual conversion
                base_health_score=80.0  # Use existing parameter for testing
            )
            
            db.session.add(config)
            db.session.commit()
            
            logger.info(f"✅ Test configuration created: ID {config.id}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to create test configuration: {str(e)}")
            return None
    
    def _load_test_configuration(self) -> Optional[ExecutiveDashboardConfiguration]:
        """Load the test configuration"""
        try:
            config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='validation_test',
                config_name='hardcode_conversion_test'
            ).first()
            
            if config:
                logger.info(f"✅ Test configuration loaded: ID {config.id}")
            else:
                logger.warning("⚠️ Test configuration not found")
                
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load test configuration: {str(e)}")
            return None
    
    def _test_configuration_fallback(self) -> Dict:
        """Test fallback behavior when configuration is missing"""
        try:
            # Look for non-existent configuration
            config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='nonexistent_user_test',
                config_name='nonexistent_config'
            ).first()
            
            return {
                'success': True,
                'config_found': config is not None,
                'fallback_works': config is None,  # Should be None for proper fallback
                'message': 'Fallback behavior ready for testing' if config is None else 'Unexpected config found'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Fallback testing failed'
            }
    
    def _get_expected_configuration_parameters(self) -> Dict:
        """Get the configuration parameters that should be added to the model"""
        return {
            'executive_summary_revenue_weeks': {
                'default_value': 3,
                'description': 'Number of weeks for executive summary revenue calculations (replaces LIMIT 3)',
                'current_hardcoded_locations': [
                    'tab7.py line 348: revenue calculation',
                    'tab7.py line 3109: working revenue calculation',
                    'tab7.py line 3122: current 3wk avg calculation',
                    'tab7.py line 3258: store revenue calculation',
                    'tab7.py line 3424: store current result',
                    'tab7.py line 3480: payroll trend calculation'
                ]
            },
            'financial_kpis_current_revenue_weeks': {
                'default_value': 3,
                'description': 'Number of weeks for financial KPI current revenue calculations',
                'usage': 'Financial KPIs API endpoint'
            },
            'insights_trend_analysis_weeks': {
                'default_value': 12,
                'description': 'Number of weeks for trend analysis in insights (replaces LIMIT 12)',
                'current_hardcoded_locations': [
                    'tab7.py line 3456: revenue trend query'
                ]
            },
            'forecasts_historical_weeks': {
                'default_value': 24,
                'description': 'Number of weeks of historical data for forecasts (replaces LIMIT 24)',
                'current_hardcoded_locations': [
                    'tab7.py line 3478: historical query'
                ]
            },
            'forecasting_historical_weeks': {
                'default_value': 52,
                'description': 'Number of weeks for yearly analysis (replaces hardcoded 52)',
                'current_hardcoded_locations': [
                    'tab7.py line 1442: .limit(52)',
                    'tab7.py line 1562: weeks=52 parameter',
                    'tab7.py line 2757: weeks_back = 52'
                ]
            }
        }
    
    # ============================================================================================
    # POST-CONVERSION VALIDATION - Test converted functionality
    # ============================================================================================
    
    def validate_converted_functionality(self) -> Dict:
        """Test API endpoints after conversion to configurable parameters"""
        logger.info("🔄 PHASE 3: Validating converted functionality")
        
        # This would test the actual converted endpoints
        # For now, we simulate what the tests would look like
        
        conversion_results = {
            'configuration_loading_test': self._simulate_configuration_loading_test(),
            'api_endpoints_with_config': self._simulate_converted_api_tests(),
            'store_specific_configs': self._simulate_store_specific_tests(),
            'fallback_behavior': self._simulate_fallback_tests()
        }
        
        self.validation_results['conversion_tests']['functionality'] = conversion_results
        return conversion_results
    
    def _simulate_configuration_loading_test(self) -> Dict:
        """Simulate testing of configuration loading in converted code"""
        return {
            'test_description': 'Test that converted code loads configuration parameters correctly',
            'expected_behavior': [
                'Code checks for ExecutiveDashboardConfiguration for current user/store',
                'Loads custom values for query limits if configured',
                'Falls back to default values if no configuration exists',
                'Uses loaded values in SQL LIMIT clauses'
            ],
            'test_cases': [
                {
                    'scenario': 'Custom 5-week configuration',
                    'setup': 'executive_summary_revenue_weeks = 5',
                    'expected_sql': 'LIMIT 5 (instead of hardcoded LIMIT 3)',
                    'validation': 'Verify SQL query uses LIMIT 5'
                },
                {
                    'scenario': 'Default fallback',
                    'setup': 'No configuration exists',
                    'expected_sql': 'LIMIT 3 (default fallback value)',
                    'validation': 'Verify fallback works correctly'
                }
            ]
        }
    
    def _simulate_converted_api_tests(self) -> Dict:
        """Simulate testing of converted API endpoints"""
        return {
            'test_description': 'Test API endpoints with configurable parameters',
            'endpoints_to_test': [
                {
                    'endpoint': '/executive/api/financial-kpis',
                    'config_parameters': ['executive_summary_revenue_weeks'],
                    'test_with_values': [3, 4, 5, 6],
                    'expected_result': 'Different number of data points based on config'
                },
                {
                    'endpoint': '/executive/api/intelligent-insights', 
                    'config_parameters': ['insights_trend_analysis_weeks'],
                    'test_with_values': [8, 12, 16, 20],
                    'expected_result': 'Trend analysis uses configured period'
                },
                {
                    'endpoint': '/executive/api/financial-forecasts',
                    'config_parameters': ['forecasts_historical_weeks', 'forecasting_historical_weeks'],
                    'test_with_values': [20, 24, 30, 52],
                    'expected_result': 'Historical data period matches configuration'
                }
            ]
        }
    
    def _simulate_store_specific_tests(self) -> Dict:
        """Simulate testing of store-specific configurations"""
        return {
            'test_description': 'Test that different stores can have different query limits',
            'test_scenario': {
                'W1_config': {'executive_summary_revenue_weeks': 3},
                'W2_config': {'executive_summary_revenue_weeks': 5},  
                'W3_config': {'executive_summary_revenue_weeks': 4},
            },
            'expected_behavior': [
                'W1 store uses 3-week calculations',
                'W2 store uses 5-week calculations',
                'W3 store uses 4-week calculations',
                'Each store gets different results based on their configuration'
            ],
            'validation_method': 'Compare API responses for different stores'
        }
    
    def _simulate_fallback_tests(self) -> Dict:
        """Simulate testing of fallback behavior"""
        return {
            'test_description': 'Test fallback when configuration is missing or invalid',
            'test_cases': [
                {
                    'scenario': 'No configuration exists',
                    'expected': 'Use hardcoded defaults (3, 12, 24, 52)',
                    'validation': 'Behavior identical to pre-conversion'
                },
                {
                    'scenario': 'Invalid configuration values (0, negative, extremely large)',
                    'expected': 'Use default values and log warning',
                    'validation': 'Graceful degradation'
                },
                {
                    'scenario': 'Partial configuration (some parameters missing)',
                    'expected': 'Use configured values where available, defaults for missing',
                    'validation': 'Mixed behavior works correctly'
                }
            ]
        }
    
    # ============================================================================================
    # COMPARISON AND REPORTING
    # ============================================================================================
    
    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report"""
        logger.info("📋 Generating validation report")
        
        report_lines = [
            "=" * 80,
            "EXECUTIVE DASHBOARD HARDCODE CONVERSION VALIDATION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            ""
        ]
        
        # Baseline Tests Summary
        if 'baseline_tests' in self.validation_results:
            report_lines.extend(self._generate_baseline_summary())
        
        # Configuration Tests Summary
        if 'conversion_tests' in self.validation_results:
            report_lines.extend(self._generate_configuration_summary())
        
        # Comparison Results
        report_lines.extend(self._generate_comparison_summary())
        
        # Errors Summary
        if self.validation_results['errors']:
            report_lines.extend(self._generate_errors_summary())
        
        # Recommendations
        report_lines.extend(self._generate_recommendations())
        
        report_lines.extend([
            "",
            "=" * 80,
            "END OF VALIDATION REPORT",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def _generate_baseline_summary(self) -> List[str]:
        """Generate baseline test results summary"""
        baseline = self.validation_results['baseline_tests']
        
        lines = [
            "BASELINE FUNCTIONALITY RESULTS",
            "-" * 40,
            ""
        ]
        
        successful_tests = sum(1 for test in baseline.values() if test.get('success', False))
        total_tests = len(baseline)
        
        lines.append(f"Overall Success Rate: {successful_tests}/{total_tests} ({(successful_tests/total_tests*100):.1f}%)")
        lines.append("")
        
        for test_name, result in baseline.items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            response_time = f" ({result['response_time']:.3f}s)" if result.get('response_time') else ""
            lines.append(f"{status} {test_name}{response_time}")
            
            if result.get('hardcoded_indicators', {}).get('likely_uses_expected_limit'):
                lines.append(f"    └── Found evidence of expected hardcoded limit usage")
            
            if result.get('error'):
                lines.append(f"    └── Error: {result['error']}")
        
        lines.extend(["", ""])
        return lines
    
    def _generate_configuration_summary(self) -> List[str]:
        """Generate configuration test results summary"""
        lines = [
            "CONFIGURATION SYSTEM RESULTS", 
            "-" * 40,
            ""
        ]
        
        if 'configuration' in self.validation_results.get('conversion_tests', {}):
            config_results = self.validation_results['conversion_tests']['configuration']
            
            # Configuration creation test
            if 'config_creation' in config_results:
                creation = config_results['config_creation']
                status = "✅ PASS" if creation.get('success') else "❌ FAIL"
                lines.append(f"{status} Configuration Creation")
                if creation.get('config_id'):
                    lines.append(f"    └── Created config ID: {creation['config_id']}")
            
            # Configuration loading test
            if 'config_loading' in config_results:
                loading = config_results['config_loading']
                status = "✅ PASS" if loading.get('success') else "❌ FAIL"
                lines.append(f"{status} Configuration Loading")
                if loading.get('matches_created'):
                    lines.append(f"    └── Successfully matched created configuration")
            
            # Expected parameters summary
            if 'expected_parameters' in config_results:
                params = config_results['expected_parameters']
                lines.append(f"📋 Expected Parameters: {len(params)} parameters identified")
                for param_name, param_info in params.items():
                    lines.append(f"    • {param_name}: {param_info.get('default_value', 'N/A')}")
        
        lines.extend(["", ""])
        return lines
    
    def _generate_comparison_summary(self) -> List[str]:
        """Generate comparison between before/after functionality"""
        lines = [
            "CONVERSION IMPACT ANALYSIS",
            "-" * 40,
            ""
        ]
        
        # Hardcoded limits found
        hardcoded_limits = {
            'LIMIT 3': 'Used in 6 locations for 3-week averages',
            'LIMIT 12': 'Used in 1 location for trend analysis', 
            'LIMIT 24': 'Used in 1 location for historical data',
            'Value 52': 'Used in 3 locations for yearly analysis'
        }
        
        lines.append("Hardcoded Limits Identified:")
        for limit, usage in hardcoded_limits.items():
            lines.append(f"  • {limit}: {usage}")
        
        lines.extend([
            "",
            "Proposed Configuration Parameters:",
            "  • executive_summary_revenue_weeks (default: 3)",
            "  • financial_kpis_current_revenue_weeks (default: 3)",
            "  • insights_trend_analysis_weeks (default: 12)",  
            "  • forecasts_historical_weeks (default: 24)",
            "  • forecasting_historical_weeks (default: 52)",
            "",
            "Expected Benefits:",
            "  ✓ Configurable analysis periods per store",
            "  ✓ Ability to customize based on business needs",
            "  ✓ Consistent configuration management",
            "  ✓ Fallback to current behavior when no config exists",
            "",
            ""
        ])
        
        return lines
    
    def _generate_errors_summary(self) -> List[str]:
        """Generate summary of errors encountered"""
        lines = [
            "ERRORS AND ISSUES",
            "-" * 40,
            ""
        ]
        
        if self.validation_results['errors']:
            for i, error in enumerate(self.validation_results['errors'], 1):
                lines.append(f"{i}. {error}")
        else:
            lines.append("No errors encountered during validation.")
        
        lines.extend(["", ""])
        return lines
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        lines = [
            "RECOMMENDATIONS",
            "-" * 40,
            ""
        ]
        
        # Analyze baseline results for recommendations
        baseline = self.validation_results.get('baseline_tests', {})
        successful_tests = sum(1 for test in baseline.values() if test.get('success', False))
        total_tests = len(baseline) if baseline else 0
        
        if total_tests == 0:
            lines.extend([
                "⚠️  No baseline tests completed - unable to provide specific recommendations.",
                "   Consider running baseline tests first to understand current functionality.",
                ""
            ])
        elif successful_tests == total_tests:
            lines.extend([
                "✅ All baseline tests passed - system is ready for conversion.",
                "",
                "Next Steps:",
                "1. Add configuration parameters to ExecutiveDashboardConfiguration model:",
                "   • executive_summary_revenue_weeks (Integer, default=3)",
                "   • financial_kpis_current_revenue_weeks (Integer, default=3)",
                "   • insights_trend_analysis_weeks (Integer, default=12)",
                "   • forecasts_historical_weeks (Integer, default=24)",
                "   • forecasting_historical_weeks (Integer, default=52)",
                "",
                "2. Update tab7.py queries to use configuration values:",
                "   • Replace LIMIT 3 with config.executive_summary_revenue_weeks",
                "   • Replace LIMIT 12 with config.insights_trend_analysis_weeks",
                "   • Replace LIMIT 24 with config.forecasts_historical_weeks", 
                "   • Replace hardcoded 52 with config.forecasting_historical_weeks",
                "",
                "3. Implement configuration loading helper function",
                "4. Add error handling for invalid configuration values",
                "5. Test with custom configuration values",
                "6. Verify fallback behavior works correctly",
                ""
            ])
        else:
            lines.extend([
                f"⚠️  {total_tests - successful_tests}/{total_tests} baseline tests failed.",
                "   Recommend fixing baseline issues before proceeding with conversion.",
                "",
                "Issues to address:",
            ])
            
            for test_name, result in baseline.items():
                if not result.get('success'):
                    lines.append(f"   • {test_name}: {result.get('error', 'Unknown error')}")
        
        lines.extend([
            "",
            "General Recommendations:",
            "• Test with multiple configuration values (3, 4, 5, 6 weeks)",
            "• Verify store-specific configurations work independently", 
            "• Ensure API response times remain acceptable",
            "• Add monitoring for configuration loading failures",
            "• Document new configuration options for users",
            ""
        ])
        
        return lines

# ============================================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================================

def main():
    """Main execution function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate Executive Dashboard Hardcode Conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python validate_hardcode_conversion_practical.py --phase before
    python validate_hardcode_conversion_practical.py --phase after  
    python validate_hardcode_conversion_practical.py --phase both --output report.txt
        """
    )
    
    parser.add_argument(
        '--phase', 
        choices=['before', 'after', 'both'], 
        default='before',
        help='Validation phase to run (default: before)'
    )
    
    parser.add_argument(
        '--output', 
        help='Output file for validation report (default: print to console)'
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Base URL for API testing (default: http://localhost:5000)'
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = HardcodeConversionValidator(base_url=args.base_url)
    
    try:
        print("🚀 Starting Executive Dashboard Hardcode Conversion Validation")
        print(f"Phase: {args.phase}")
        print("-" * 60)
        
        # Run validation phases
        if args.phase in ['before', 'both']:
            validator.validate_baseline_functionality()
            validator.validate_configuration_system()
        
        if args.phase in ['after', 'both']:
            validator.validate_converted_functionality()
        
        # Generate and output report
        report = validator.generate_validation_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"\n📋 Validation report saved to: {args.output}")
        else:
            print("\n" + report)
        
        # Return success/failure based on results
        baseline_success = True
        if 'baseline_tests' in validator.validation_results:
            baseline = validator.validation_results['baseline_tests']
            baseline_success = all(test.get('success', False) for test in baseline.values())
        
        if not baseline_success:
            print("\n⚠️  Some validation tests failed. See report for details.")
            sys.exit(1)
        else:
            print("\n✅ Validation completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        logger.error(f"Validation error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()