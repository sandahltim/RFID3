"""
Direct Query Limits Validation Script
====================================

This script directly tests the SQL queries with hardcoded LIMIT statements
to ensure they can be successfully converted to configurable parameters.

It identifies and validates:
1. Current hardcoded LIMIT statements in tab7.py
2. Data returned by each query
3. Impact of changing LIMIT values
4. Database performance with different limits

Usage: python validate_query_limits_direct.py
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.services.logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)

class QueryLimitsValidator:
    """Validates hardcoded LIMIT statements and their conversion readiness"""
    
    def __init__(self):
        self.app = create_app()
        self.hardcoded_queries = self._define_hardcoded_queries()
        self.validation_results = {}
    
    def _define_hardcoded_queries(self) -> Dict:
        """Define the hardcoded queries found in tab7.py for testing"""
        
        return {
            'revenue_3wk_avg_1': {
                'description': '3-week revenue average calculation (line ~348)',
                'current_limit': 3,
                'sql_template': """
                    SELECT AVG(total_weekly_revenue) as avg_3wk
                    FROM scorecard_trends_data 
                    WHERE total_weekly_revenue IS NOT NULL
                    ORDER BY week_ending DESC 
                    LIMIT {limit}
                """,
                'config_parameter': 'executive_summary_revenue_weeks'
            },
            
            'current_revenue_3wk': {
                'description': 'Current 3-week average revenue (line ~3109)',
                'current_limit': 3,
                'sql_template': """
                    SELECT AVG(total_weekly_revenue) as current_3wk_avg
                    FROM (
                        SELECT total_weekly_revenue
                        FROM scorecard_trends_data
                        WHERE total_weekly_revenue IS NOT NULL
                            AND total_weekly_revenue > 0
                            AND week_ending <= CURDATE()
                        ORDER BY week_ending DESC 
                        LIMIT {limit}
                    ) recent_weeks
                """,
                'config_parameter': 'financial_kpis_current_revenue_weeks'
            },
            
            'store_revenue_3wk': {
                'description': 'Store-specific 3-week revenue (line ~3258)',  
                'current_limit': 3,
                'sql_template': """
                    SELECT AVG(revenue_W1) as avg_revenue
                    FROM (
                        SELECT revenue_W1
                        FROM scorecard_trends_data 
                        WHERE revenue_W1 IS NOT NULL
                        ORDER BY week_ending DESC 
                        LIMIT {limit}
                    ) recent_weeks
                """,
                'config_parameter': 'executive_summary_revenue_weeks'
            },
            
            'payroll_trends_3wk': {
                'description': 'Payroll trends 3-week data (line ~3480)',
                'current_limit': 3,
                'sql_template': """
                    SELECT AVG(labor_cost) as avg_labor_cost
                    FROM executive_payroll_trends 
                    WHERE store_id = 'W1'
                    ORDER BY week_ending DESC 
                    LIMIT {limit}
                """,
                'config_parameter': 'executive_summary_revenue_weeks'
            },
            
            'revenue_trend_12wk': {
                'description': '12-week revenue trend analysis (line ~3456)',
                'current_limit': 12,
                'sql_template': """
                    SELECT week_ending, total_weekly_revenue
                    FROM scorecard_trends_data 
                    WHERE total_weekly_revenue IS NOT NULL
                    ORDER BY week_ending DESC 
                    LIMIT {limit}
                """,
                'config_parameter': 'insights_trend_analysis_weeks'
            },
            
            'historical_data_24wk': {
                'description': '24-week historical data for forecasting (line ~3478)',
                'current_limit': 24,
                'sql_template': """
                    SELECT week_ending, total_weekly_revenue
                    FROM scorecard_trends_data
                    WHERE total_weekly_revenue IS NOT NULL
                        AND total_weekly_revenue > 0
                    ORDER BY week_ending DESC 
                    LIMIT {limit}
                """,
                'config_parameter': 'forecasts_historical_weeks'
            },
            
            'yearly_trend_52wk': {
                'description': 'Full year trend analysis (52 weeks)',
                'current_limit': 52,
                'sql_template': """
                    SELECT week_ending, total_weekly_revenue
                    FROM scorecard_trends_data
                    WHERE total_weekly_revenue IS NOT NULL
                    ORDER BY week_ending DESC 
                    LIMIT {limit}
                """,
                'config_parameter': 'forecasting_historical_weeks'
            }
        }
    
    def validate_all_queries(self) -> Dict:
        """Validate all hardcoded queries with different LIMIT values"""
        logger.info("🔍 Starting validation of hardcoded query limits")
        
        with self.app.app_context():
            for query_name, query_info in self.hardcoded_queries.items():
                logger.info(f"Testing query: {query_info['description']}")
                
                result = self._validate_single_query(query_name, query_info)
                self.validation_results[query_name] = result
                
                # Brief pause between queries
                import time
                time.sleep(0.1)
        
        logger.info(f"✅ Completed validation of {len(self.hardcoded_queries)} query patterns")
        return self.validation_results
    
    def _validate_single_query(self, query_name: str, query_info: Dict) -> Dict:
        """Validate a single query with different LIMIT values"""
        
        result = {
            'query_name': query_name,
            'description': query_info['description'],
            'current_limit': query_info['current_limit'],
            'config_parameter': query_info['config_parameter'],
            'test_results': {},
            'performance_data': {},
            'errors': []
        }
        
        # Test with current limit and alternative values
        test_limits = [
            query_info['current_limit'],  # Current hardcoded value
            query_info['current_limit'] + 1,  # One more
            query_info['current_limit'] + 2,  # Two more
            max(1, query_info['current_limit'] - 1),  # One less (minimum 1)
        ]
        
        # Add some specific test values based on the limit type
        if query_info['current_limit'] == 3:
            test_limits.extend([4, 5, 6])
        elif query_info['current_limit'] == 12:
            test_limits.extend([8, 16, 20])
        elif query_info['current_limit'] == 24:
            test_limits.extend([20, 30, 36])
        elif query_info['current_limit'] == 52:
            test_limits.extend([26, 39, 78])
        
        # Remove duplicates and sort
        test_limits = sorted(set(test_limits))
        
        for limit_value in test_limits:
            test_result = self._test_query_with_limit(query_info['sql_template'], limit_value)
            result['test_results'][f'limit_{limit_value}'] = test_result
            
            # Mark if this is the current hardcoded value
            if limit_value == query_info['current_limit']:
                result['test_results'][f'limit_{limit_value}']['is_current_hardcoded'] = True
        
        # Analyze results
        result['analysis'] = self._analyze_query_results(result['test_results'])
        
        return result
    
    def _test_query_with_limit(self, sql_template: str, limit_value: int) -> Dict:
        """Test a single query with a specific LIMIT value"""
        
        test_result = {
            'limit_value': limit_value,
            'success': False,
            'row_count': 0,
            'execution_time': 0,
            'sample_data': None,
            'error': None
        }
        
        try:
            # Format SQL with the specific limit
            sql_query = sql_template.format(limit=limit_value)
            
            # Time the query execution
            import time
            start_time = time.time()
            
            # Execute query
            result = db.session.execute(text(sql_query))
            rows = result.fetchall()
            
            end_time = time.time()
            
            # Record results
            test_result['success'] = True
            test_result['row_count'] = len(rows)
            test_result['execution_time'] = end_time - start_time
            
            # Store sample data (first few rows)
            if rows:
                # Convert rows to dictionaries for JSON serialization
                sample_rows = []
                for row in rows[:3]:  # First 3 rows as sample
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[f'col_{i}'] = str(value) if value is not None else None
                    sample_rows.append(row_dict)
                test_result['sample_data'] = sample_rows
            
            logger.debug(f"Query with LIMIT {limit_value}: {len(rows)} rows, {test_result['execution_time']:.3f}s")
            
        except Exception as e:
            test_result['error'] = str(e)
            logger.warning(f"Query with LIMIT {limit_value} failed: {str(e)}")
        
        return test_result
    
    def _analyze_query_results(self, test_results: Dict) -> Dict:
        """Analyze the results of testing a query with different limits"""
        
        analysis = {
            'total_tests': len(test_results),
            'successful_tests': 0,
            'failed_tests': 0,
            'row_count_analysis': {},
            'performance_analysis': {},
            'data_consistency': {},
            'recommendations': []
        }
        
        successful_results = []
        
        for test_name, test_result in test_results.items():
            if test_result['success']:
                analysis['successful_tests'] += 1
                successful_results.append(test_result)
            else:
                analysis['failed_tests'] += 1
        
        if successful_results:
            # Row count analysis
            row_counts = [r['row_count'] for r in successful_results]
            analysis['row_count_analysis'] = {
                'min_rows': min(row_counts),
                'max_rows': max(row_counts),
                'row_counts_by_limit': {r['limit_value']: r['row_count'] for r in successful_results}
            }
            
            # Performance analysis  
            exec_times = [r['execution_time'] for r in successful_results]
            analysis['performance_analysis'] = {
                'min_time': min(exec_times),
                'max_time': max(exec_times),
                'avg_time': sum(exec_times) / len(exec_times),
                'performance_impact': max(exec_times) - min(exec_times)
            }
            
            # Data consistency check
            analysis['data_consistency'] = self._check_data_consistency(successful_results)
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_query_recommendations(successful_results, analysis)
        
        return analysis
    
    def _check_data_consistency(self, successful_results: List[Dict]) -> Dict:
        """Check if different LIMIT values return consistent data"""
        
        consistency = {
            'has_data': False,
            'data_overlaps': True,
            'expected_behavior': True,
            'issues': []
        }
        
        # Check if any queries returned data
        has_data = any(r['row_count'] > 0 for r in successful_results)
        consistency['has_data'] = has_data
        
        if not has_data:
            consistency['issues'].append("No queries returned data - may indicate empty tables")
            return consistency
        
        # Check that higher limits return more or equal rows
        results_by_limit = sorted(successful_results, key=lambda x: x['limit_value'])
        
        for i in range(1, len(results_by_limit)):
            prev_result = results_by_limit[i-1]
            curr_result = results_by_limit[i]
            
            # Higher limit should return >= rows (unless table has fewer rows)
            if curr_result['row_count'] < prev_result['row_count']:
                consistency['expected_behavior'] = False
                consistency['issues'].append(
                    f"LIMIT {curr_result['limit_value']} returned fewer rows ({curr_result['row_count']}) "
                    f"than LIMIT {prev_result['limit_value']} ({prev_result['row_count']})"
                )
        
        return consistency
    
    def _generate_query_recommendations(self, successful_results: List[Dict], analysis: Dict) -> List[str]:
        """Generate recommendations based on query analysis"""
        
        recommendations = []
        
        # Performance recommendations
        perf = analysis['performance_analysis']
        if perf['performance_impact'] > 0.1:  # More than 100ms difference
            recommendations.append(
                f"Performance varies by {perf['performance_impact']:.3f}s between different limits. "
                f"Consider query optimization if using large limits."
            )
        
        # Row count recommendations
        row_analysis = analysis['row_count_analysis']
        max_rows = row_analysis['max_rows']
        
        if max_rows == 0:
            recommendations.append("Query returns no data. Verify table has data and query logic is correct.")
        elif max_rows < 10:
            recommendations.append(f"Query returns limited data ({max_rows} max rows). Consider if higher limits are needed.")
        elif max_rows > 100:
            recommendations.append(f"Query can return substantial data ({max_rows} max rows). Consider performance impact of large limits.")
        
        # Configuration recommendations
        current_limit_results = [r for r in successful_results if r.get('is_current_hardcoded')]
        if current_limit_results:
            current_rows = current_limit_results[0]['row_count']
            recommendations.append(f"Current hardcoded limit returns {current_rows} rows. This should be the default configuration value.")
        
        # Safety recommendations
        consistency = analysis.get('data_consistency', {})
        if not consistency.get('expected_behavior', True):
            recommendations.append("Data consistency issues detected. Review query logic before making configurable.")
        
        return recommendations
    
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive validation report"""
        
        report_lines = [
            "=" * 80,
            "QUERY LIMITS VALIDATION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            ""
        ]
        
        # Executive Summary
        total_queries = len(self.validation_results)
        successful_queries = sum(1 for r in self.validation_results.values() 
                               if r.get('analysis', {}).get('successful_tests', 0) > 0)
        
        report_lines.extend([
            "EXECUTIVE SUMMARY",
            "-" * 40,
            f"Total Query Patterns Tested: {total_queries}",
            f"Successfully Validated: {successful_queries}",
            f"Validation Success Rate: {(successful_queries/total_queries*100):.1f}%",
            ""
        ])
        
        # Detailed Results for Each Query
        for query_name, result in self.validation_results.items():
            report_lines.extend(self._generate_query_report_section(query_name, result))
        
        # Configuration Recommendations
        report_lines.extend(self._generate_configuration_recommendations())
        
        # Implementation Guidance
        report_lines.extend(self._generate_implementation_guidance())
        
        report_lines.extend([
            "",
            "=" * 80,
            "END OF VALIDATION REPORT",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def _generate_query_report_section(self, query_name: str, result: Dict) -> List[str]:
        """Generate report section for a single query"""
        
        lines = [
            f"QUERY: {result['description']}",
            "-" * 60,
            f"Query Name: {query_name}",
            f"Current Hardcoded Limit: {result['current_limit']}",
            f"Target Configuration Parameter: {result['config_parameter']}",
            ""
        ]
        
        # Test Results Summary
        analysis = result.get('analysis', {})
        if analysis:
            lines.extend([
                "Test Results:",
                f"  • Total Tests Run: {analysis['total_tests']}",
                f"  • Successful Tests: {analysis['successful_tests']}",
                f"  • Failed Tests: {analysis['failed_tests']}",
                ""
            ])
            
            # Row Count Analysis
            if 'row_count_analysis' in analysis:
                row_analysis = analysis['row_count_analysis']
                lines.extend([
                    "Data Analysis:",
                    f"  • Row Count Range: {row_analysis['min_rows']} - {row_analysis['max_rows']}",
                ])
                
                # Show row counts for different limits
                for limit_val, row_count in sorted(row_analysis['row_counts_by_limit'].items()):
                    status = " (CURRENT)" if limit_val == result['current_limit'] else ""
                    lines.append(f"    - LIMIT {limit_val}: {row_count} rows{status}")
                
                lines.append("")
            
            # Performance Analysis
            if 'performance_analysis' in analysis:
                perf = analysis['performance_analysis']
                lines.extend([
                    "Performance Analysis:",
                    f"  • Execution Time Range: {perf['min_time']:.3f}s - {perf['max_time']:.3f}s",
                    f"  • Average Execution Time: {perf['avg_time']:.3f}s",
                    f"  • Performance Impact: {perf['performance_impact']:.3f}s",
                    ""
                ])
            
            # Recommendations
            if analysis.get('recommendations'):
                lines.append("Recommendations:")
                for rec in analysis['recommendations']:
                    lines.append(f"  • {rec}")
                lines.append("")
        
        # Error Summary
        if result.get('errors'):
            lines.append("Errors Encountered:")
            for error in result['errors']:
                lines.append(f"  • {error}")
            lines.append("")
        
        lines.append("")
        return lines
    
    def _generate_configuration_recommendations(self) -> List[str]:
        """Generate overall configuration recommendations"""
        
        lines = [
            "CONFIGURATION PARAMETER RECOMMENDATIONS",
            "-" * 60,
            ""
        ]
        
        # Group results by configuration parameter
        param_groups = {}
        for result in self.validation_results.values():
            param = result['config_parameter']
            if param not in param_groups:
                param_groups[param] = []
            param_groups[param].append(result)
        
        for param_name, param_results in param_groups.items():
            lines.append(f"Parameter: {param_name}")
            
            # Get current hardcoded values for this parameter
            current_values = list(set(r['current_limit'] for r in param_results))
            lines.append(f"  Current Hardcoded Values: {current_values}")
            
            # Recommend default value (most common current value)
            if len(current_values) == 1:
                recommended_default = current_values[0]
                lines.append(f"  Recommended Default: {recommended_default}")
            else:
                lines.append(f"  Recommended Default: {min(current_values)} (conservative choice)")
            
            # List affected queries
            affected_queries = [r['description'] for r in param_results]
            lines.append(f"  Affects {len(affected_queries)} query pattern(s):")
            for query_desc in affected_queries:
                lines.append(f"    • {query_desc}")
            
            lines.append("")
        
        return lines
    
    def _generate_implementation_guidance(self) -> List[str]:
        """Generate implementation guidance based on validation results"""
        
        lines = [
            "IMPLEMENTATION GUIDANCE",
            "-" * 60,
            ""
        ]
        
        # Analyze overall validation success
        total_queries = len(self.validation_results)
        successful_queries = sum(1 for r in self.validation_results.values() 
                               if r.get('analysis', {}).get('successful_tests', 0) > 0)
        
        if successful_queries == total_queries:
            lines.extend([
                "✅ All queries validated successfully - ready for conversion!",
                "",
                "Implementation Steps:",
                "",
                "1. Database Schema Updates:",
                "   ALTER TABLE executive_dashboard_configuration ADD COLUMN:",
                "   • executive_summary_revenue_weeks INTEGER DEFAULT 3",
                "   • financial_kpis_current_revenue_weeks INTEGER DEFAULT 3", 
                "   • insights_trend_analysis_weeks INTEGER DEFAULT 12",
                "   • forecasts_historical_weeks INTEGER DEFAULT 24",
                "   • forecasting_historical_weeks INTEGER DEFAULT 52",
                "",
                "2. Code Changes in tab7.py:",
                "   Replace hardcoded LIMIT values with configuration lookups:",
                "   • LIMIT 3 → LIMIT {config.executive_summary_revenue_weeks}",
                "   • LIMIT 12 → LIMIT {config.insights_trend_analysis_weeks}",
                "   • LIMIT 24 → LIMIT {config.forecasts_historical_weeks}",
                "   • Hardcoded 52 → {config.forecasting_historical_weeks}",
                "",
                "3. Configuration Loading Function:",
                "   Create helper function to load configuration with fallback:",
                "   ```python",
                "   def get_dashboard_config(user_id='default', store_id='default'):",
                "       config = ExecutiveDashboardConfiguration.query.filter_by(",
                "           user_id=user_id, config_name=store_id).first()",
                "       return config or get_default_executive_dashboard_config()",
                "   ```",
                "",
                "4. Error Handling:",
                "   • Validate configuration values are positive integers",
                "   • Log warnings for invalid values and use defaults",
                "   • Implement reasonable limits (e.g., max 104 weeks)",
                "",
                "5. Testing Strategy:",
                "   • Test with default values (should match current behavior)",
                "   • Test with custom values (2, 4, 5 weeks for LIMIT 3 replacements)",
                "   • Test fallback behavior with missing configuration",
                "   • Verify API responses remain consistent",
                "",
            ])
        else:
            lines.extend([
                f"⚠️  {total_queries - successful_queries}/{total_queries} queries failed validation.",
                "",
                "Before proceeding with conversion:",
                "1. Review failed queries and fix underlying issues",
                "2. Ensure database tables have sufficient test data", 
                "3. Verify query syntax is correct",
                "4. Re-run validation after fixes",
                ""
            ])
        
        lines.extend([
            "6. Rollback Plan:",
            "   • Keep original hardcoded values as fallback defaults",
            "   • Implement feature flag to disable configuration loading",
            "   • Monitor query performance after deployment",
            "",
            "7. User Documentation:",
            "   • Document new configuration options",
            "   • Provide examples of typical configuration values",
            "   • Explain impact of different limit values on reports",
            ""
        ])
        
        return lines

def main():
    """Main execution function"""
    print("🔍 Starting Query Limits Validation")
    print("=" * 50)
    
    try:
        # Initialize validator
        validator = QueryLimitsValidator()
        
        # Run validation
        results = validator.validate_all_queries()
        
        # Generate report
        report = validator.generate_comprehensive_report()
        
        # Output results
        output_file = f"query_limits_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"\n📋 Validation report saved to: {output_file}")
        print("\n" + "=" * 50)
        print("QUICK SUMMARY:")
        print("=" * 50)
        
        # Print quick summary to console
        total_queries = len(results)
        successful_queries = sum(1 for r in results.values() 
                               if r.get('analysis', {}).get('successful_tests', 0) > 0)
        
        print(f"Queries Tested: {total_queries}")
        print(f"Successful: {successful_queries}")
        print(f"Success Rate: {(successful_queries/total_queries*100):.1f}%")
        
        if successful_queries == total_queries:
            print("\n✅ All queries validated successfully!")
            print("System is ready for hardcode conversion.")
        else:
            print(f"\n⚠️  {total_queries - successful_queries} queries failed validation.")
            print("Review the full report for details.")
        
        print(f"\nFull report: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {str(e)}")
        logger.error(f"Validation error: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())