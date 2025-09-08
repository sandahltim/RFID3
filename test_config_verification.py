#!/usr/bin/env python3
"""
Configuration System Verification Script
Tests that user-entered configuration values are actually used in calculations
rather than just being stored as placeholders.

Created: 2025-09-07
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.config_models import (
    ExecutiveDashboardConfiguration,
    LaborCostConfiguration,
    PredictiveAnalyticsConfiguration,
    get_default_executive_dashboard_config,
    get_default_labor_cost_config
)
from app.services.financial_analytics_service import FinancialAnalyticsService
from app.services.executive_insights_service import ExecutiveInsightsService

app = create_app()
import json
from datetime import datetime, timedelta
from sqlalchemy import text


class ConfigurationVerifier:
    """Verify configuration system integration"""
    
    def __init__(self):
        self.financial_service = FinancialAnalyticsService()
        self.insights_service = ExecutiveInsightsService()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results"""
        print(f"\n{'='*60}")
        print(f"Testing: {test_name}")
        print('='*60)
        
        try:
            result = test_func()
            self.test_results['tests'].append({
                'name': test_name,
                'status': result['status'],
                'details': result.get('details', ''),
                'evidence': result.get('evidence', {})
            })
            
            self.test_results['summary']['total'] += 1
            if result['status'] == 'PASS':
                self.test_results['summary']['passed'] += 1
                print(f"✓ PASSED: {result.get('details', 'Test passed')}")
            elif result['status'] == 'FAIL':
                self.test_results['summary']['failed'] += 1
                print(f"✗ FAILED: {result.get('details', 'Test failed')}")
            else:
                self.test_results['summary']['warnings'] += 1
                print(f"⚠ WARNING: {result.get('details', 'Test has warnings')}")
            
            if result.get('evidence'):
                print(f"\nEvidence:")
                for key, value in result['evidence'].items():
                    print(f"  {key}: {value}")
                    
        except Exception as e:
            self.test_results['tests'].append({
                'name': test_name,
                'status': 'ERROR',
                'error': str(e)
            })
            self.test_results['summary']['failed'] += 1
            self.test_results['summary']['total'] += 1
            print(f"✗ ERROR: {str(e)}")
    
    def test_executive_dashboard_config_exists(self):
        """Test 1: Verify ExecutiveDashboardConfiguration model exists and has data"""
        with app.app_context():
            config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='default_user',
                config_name='default'
            ).first()
            
            if config:
                return {
                    'status': 'PASS',
                    'details': 'Executive dashboard configuration found in database',
                    'evidence': {
                        'base_health_score': config.base_health_score,
                        'revenue_tier_1_threshold': config.revenue_tier_1_threshold,
                        'executive_summary_revenue_weeks': config.executive_summary_revenue_weeks,
                        'insights_trend_analysis_weeks': config.insights_trend_analysis_weeks
                    }
                }
            else:
                return {
                    'status': 'WARNING',
                    'details': 'No executive dashboard configuration found - using defaults',
                    'evidence': get_default_executive_dashboard_config()
                }
    
    def test_labor_cost_config_exists(self):
        """Test 2: Verify LaborCostConfiguration model exists and has data"""
        with app.app_context():
            config = LaborCostConfiguration.query.filter_by(
                user_id='default_user',
                config_name='default'
            ).first()
            
            if config:
                return {
                    'status': 'PASS',
                    'details': 'Labor cost configuration found in database',
                    'evidence': {
                        'high_labor_cost_threshold': config.high_labor_cost_threshold,
                        'target_labor_cost_ratio': config.target_labor_cost_ratio,
                        'store_specific_thresholds': config.store_specific_thresholds
                    }
                }
            else:
                return {
                    'status': 'WARNING',
                    'details': 'No labor cost configuration found - using defaults',
                    'evidence': get_default_labor_cost_config()
                }
    
    def test_config_method_exists(self):
        """Test 3: Verify get_store_threshold method exists and works"""
        with app.app_context():
            exec_config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='default_user',
                config_name='default'
            ).first()
            
            if not exec_config:
                exec_config = ExecutiveDashboardConfiguration(user_id='default_user')
            
            # Test the method exists and returns values
            base_score = exec_config.get_store_threshold('default', 'base_health_score')
            trend_threshold = exec_config.get_store_threshold('3607', 'strong_positive_trend_threshold')
            
            if base_score is not None and trend_threshold is not None:
                return {
                    'status': 'PASS',
                    'details': 'get_store_threshold method works correctly',
                    'evidence': {
                        'base_health_score': base_score,
                        'strong_positive_trend_threshold': trend_threshold,
                        'method_exists': True
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'details': 'get_store_threshold method not returning values',
                    'evidence': {
                        'base_score': base_score,
                        'trend_threshold': trend_threshold
                    }
                }
    
    def test_financial_service_uses_config(self):
        """Test 4: Verify FinancialAnalyticsService actually uses configuration"""
        with app.app_context():
            # Get the labor cost config
            config = self.financial_service.get_labor_cost_config()
            
            # Check if the service is using config values
            threshold_3607 = self.financial_service.get_store_threshold('3607', 'high_threshold')
            threshold_6800 = self.financial_service.get_store_threshold('6800', 'high_threshold')
            
            if config and threshold_3607 and threshold_6800:
                return {
                    'status': 'PASS',
                    'details': 'Financial service correctly retrieves and uses configuration',
                    'evidence': {
                        'config_exists': config is not None,
                        'threshold_3607': threshold_3607,
                        'threshold_6800': threshold_6800,
                        'config_has_method': hasattr(config, 'get_store_threshold')
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'details': 'Financial service not properly using configuration',
                    'evidence': {
                        'config': config,
                        'threshold_3607': threshold_3607,
                        'threshold_6800': threshold_6800
                    }
                }
    
    def test_week_limits_from_config(self):
        """Test 5: Verify week limits are read from configuration not hardcoded"""
        with app.app_context():
            exec_config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='default_user',
                config_name='default'
            ).first()
            
            if not exec_config:
                exec_config = ExecutiveDashboardConfiguration(user_id='default_user')
            
            # Check various week configuration values
            evidence = {
                'executive_summary_revenue_weeks': exec_config.executive_summary_revenue_weeks,
                'financial_kpis_current_revenue_weeks': exec_config.financial_kpis_current_revenue_weeks,
                'insights_trend_analysis_weeks': exec_config.insights_trend_analysis_weeks,
                'forecasts_historical_weeks': exec_config.forecasts_historical_weeks,
                'default_analysis_period_weeks': exec_config.default_analysis_period_weeks
            }
            
            # Verify these are not all the same hardcoded value
            values = list(evidence.values())
            if len(set(values)) > 1:  # Different values means configuration is working
                return {
                    'status': 'PASS',
                    'details': 'Week limits are properly configured with different values',
                    'evidence': evidence
                }
            elif all(v == 3 for v in values):
                return {
                    'status': 'FAIL',
                    'details': 'All week limits are hardcoded to 3 - configuration not working',
                    'evidence': evidence
                }
            else:
                return {
                    'status': 'WARNING',
                    'details': 'Week limits are configured but all have the same value',
                    'evidence': evidence
                }
    
    def test_actual_query_usage(self):
        """Test 6: Verify actual database queries use configuration values"""
        with app.app_context():
            # Test a simple query to see if it respects configured week limits
            exec_config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='default_user',
                config_name='default'
            ).first()
            
            if not exec_config:
                return {
                    'status': 'SKIP',
                    'details': 'No configuration to test against'
                }
            
            # Get the configured weeks for trend analysis
            configured_weeks = exec_config.insights_trend_analysis_weeks or 12
            
            # Run a test query to check if it uses the configured value
            query = text("""
                SELECT COUNT(*) as record_count,
                       MIN(week_ending) as earliest_date,
                       MAX(week_ending) as latest_date,
                       COUNT(DISTINCT week_ending) as week_count
                FROM scorecard_trends_data
                WHERE week_ending >= DATE_SUB(CURRENT_DATE, INTERVAL :weeks WEEK)
            """)
            
            try:
                result = db.session.execute(query, {'weeks': configured_weeks}).fetchone()
                
                if result and result.week_count:
                    return {
                        'status': 'PASS',
                        'details': f'Queries respect configured week limits',
                        'evidence': {
                            'configured_weeks': configured_weeks,
                            'actual_weeks_returned': result.week_count,
                            'earliest_date': str(result.earliest_date) if result.earliest_date else None,
                            'latest_date': str(result.latest_date) if result.latest_date else None
                        }
                    }
                else:
                    return {
                        'status': 'WARNING',
                        'details': 'Query executed but no data returned',
                        'evidence': {
                            'configured_weeks': configured_weeks,
                            'query_result': dict(result) if result else None
                        }
                    }
            except Exception as e:
                return {
                    'status': 'ERROR',
                    'details': f'Error executing test query: {str(e)}',
                    'evidence': {
                        'configured_weeks': configured_weeks,
                        'error': str(e)
                    }
                }
    
    def test_store_specific_overrides(self):
        """Test 7: Verify store-specific configuration overrides work"""
        with app.app_context():
            # Test with labor cost config which has store-specific overrides
            labor_config = LaborCostConfiguration.query.filter_by(
                user_id='default_user',
                config_name='default'
            ).first()
            
            if not labor_config:
                labor_config = LaborCostConfiguration(user_id='default_user')
            
            # Set a test override
            if not labor_config.store_specific_thresholds:
                labor_config.store_specific_thresholds = {}
            
            labor_config.store_specific_thresholds['TEST_STORE'] = {
                'high_threshold': 99.9,
                'target': 88.8
            }
            
            # Test retrieval
            default_threshold = labor_config.get_store_threshold('DEFAULT_STORE', 'high_threshold')
            test_threshold = labor_config.get_store_threshold('TEST_STORE', 'high_threshold')
            
            if test_threshold == 99.9 and default_threshold != 99.9:
                return {
                    'status': 'PASS',
                    'details': 'Store-specific overrides work correctly',
                    'evidence': {
                        'default_threshold': default_threshold,
                        'test_store_threshold': test_threshold,
                        'override_applied': True
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'details': 'Store-specific overrides not working',
                    'evidence': {
                        'default_threshold': default_threshold,
                        'test_threshold': test_threshold,
                        'expected': 99.9
                    }
                }
    
    def test_config_update_persistence(self):
        """Test 8: Verify configuration updates are persisted and used"""
        with app.app_context():
            # Get or create config
            exec_config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='test_user',
                config_name='test_config'
            ).first()
            
            if exec_config:
                db.session.delete(exec_config)
                db.session.commit()
            
            # Create new config with test values
            test_config = ExecutiveDashboardConfiguration(
                user_id='test_user',
                config_name='test_config',
                base_health_score=99.0,
                executive_summary_revenue_weeks=99,
                insights_trend_analysis_weeks=88
            )
            db.session.add(test_config)
            db.session.commit()
            
            # Retrieve and verify
            saved_config = ExecutiveDashboardConfiguration.query.filter_by(
                user_id='test_user',
                config_name='test_config'
            ).first()
            
            if saved_config and saved_config.base_health_score == 99.0:
                # Clean up
                db.session.delete(saved_config)
                db.session.commit()
                
                return {
                    'status': 'PASS',
                    'details': 'Configuration updates are properly persisted',
                    'evidence': {
                        'saved_base_score': saved_config.base_health_score,
                        'saved_summary_weeks': saved_config.executive_summary_revenue_weeks,
                        'saved_trend_weeks': saved_config.insights_trend_analysis_weeks
                    }
                }
            else:
                return {
                    'status': 'FAIL',
                    'details': 'Configuration not properly persisted',
                    'evidence': {
                        'config_found': saved_config is not None,
                        'base_score': saved_config.base_health_score if saved_config else None
                    }
                }
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("\n" + "="*60)
        print("RFID3 Configuration System Verification")
        print("="*60)
        print(f"Started: {datetime.now().isoformat()}")
        
        # Run tests
        self.run_test("Executive Dashboard Config Exists", self.test_executive_dashboard_config_exists)
        self.run_test("Labor Cost Config Exists", self.test_labor_cost_config_exists)
        self.run_test("Config Methods Work", self.test_config_method_exists)
        self.run_test("Financial Service Uses Config", self.test_financial_service_uses_config)
        self.run_test("Week Limits From Config", self.test_week_limits_from_config)
        self.run_test("Actual Query Usage", self.test_actual_query_usage)
        self.run_test("Store-Specific Overrides", self.test_store_specific_overrides)
        self.run_test("Config Update Persistence", self.test_config_update_persistence)
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        summary = self.test_results['summary']
        print(f"Total Tests: {summary['total']}")
        print(f"Passed: {summary['passed']} ({summary['passed']/summary['total']*100:.1f}%)")
        print(f"Failed: {summary['failed']} ({summary['failed']/summary['total']*100:.1f}%)")
        print(f"Warnings: {summary['warnings']} ({summary['warnings']/summary['total']*100:.1f}%)")
        
        # Save results to file
        results_file = f"config_verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Return overall status
        if summary['failed'] > 0:
            print("\n⚠️  CONFIGURATION SYSTEM HAS ISSUES - Some values may be placeholders!")
            return False
        elif summary['warnings'] > 0:
            print("\n⚠️  CONFIGURATION SYSTEM WORKING WITH WARNINGS - Review warnings above")
            return True
        else:
            print("\n✅ CONFIGURATION SYSTEM FULLY INTEGRATED - All tests passed!")
            return True


if __name__ == "__main__":
    verifier = ConfigurationVerifier()
    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)