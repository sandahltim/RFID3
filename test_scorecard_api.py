#!/usr/bin/env python3
"""Test scorecard correlation API endpoints"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000/api/scorecard'

def test_endpoint(endpoint, description):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Endpoint: {endpoint}")
    print("-"*60)
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            # Pretty print relevant data
            if 'data' in data:
                print("\nData Summary:")
                main_data = data['data']
                if 'store_metrics' in main_data:
                    print(f"  - Stores analyzed: {len(main_data['store_metrics'])}")
                if 'financial_health' in main_data:
                    health = main_data['financial_health']
                    if health:
                        print(f"  - Financial Health Score: {health.get('overall_score', 'N/A')}")
                        print(f"  - Status: {health.get('status', 'N/A')}")
                if 'alerts' in main_data:
                    print(f"  - Active alerts: {len(main_data['alerts'])}")
                    
            elif 'metrics' in data:
                print(f"\nStore Metrics Found: {len(data['metrics'])}")
                for store, metrics in list(data['metrics'].items())[:2]:
                    print(f"  Store {store}:")
                    print(f"    - Avg Revenue: ${metrics['avg_weekly_revenue']:,.0f}")
                    print(f"    - Revenue/Contract: ${metrics['revenue_per_contract']:,.0f}")
                    
            elif 'health' in data:
                health = data['health']
                print(f"\nFinancial Health:")
                print(f"  - Overall Score: {health['overall_score']}")
                print(f"  - AR Score: {health['ar_score']}")
                print(f"  - Status: {health['status']}")
                
            elif 'alerts' in data:
                alerts = data['alerts']
                print(f"\nAlerts Summary:")
                print(f"  - Critical: {len(alerts['critical'])}")
                print(f"  - Warnings: {len(alerts['warning'])}")
                for alert in alerts['critical'][:2]:
                    print(f"    • {alert['metric']}: {alert['message']}")
                    
            elif 'insights' in data:
                insights = data['insights']
                print(f"\nCorrelation Insights: {len(insights)}")
                for insight in insights[:2]:
                    print(f"  - {insight['relationship']}: r={insight['correlation']}")
                    print(f"    Action: {insight['action']}")
                    
            elif 'comparison' in data:
                print(f"\nStore Comparison:")
                for store, comp in list(data['comparison'].items())[:2]:
                    print(f"  Store {store}:")
                    print(f"    - Performance Grade: {comp['performance_grade']}")
                    print(f"    - Revenue vs Avg: {comp['revenue_vs_avg']:+.1f}%")
                    
            elif 'prediction' in data:
                pred = data['prediction']
                print(f"\nRevenue Prediction for Store {data.get('store_id', 'N/A')}:")
                print(f"  - Predicted Revenue: ${pred['predicted_revenue']:,.0f}")
                print(f"  - Confidence: {pred['confidence']}")
                print(f"  - Pipeline: ${pred['reservation_pipeline']:,.0f}")
            
        else:
            print(f"Error Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Is Flask running?")
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    """Test all scorecard correlation endpoints"""
    
    print("="*60)
    print("SCORECARD CORRELATION API TEST SUITE")
    print("="*60)
    print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    # Test endpoints
    endpoints = [
        ('/dashboard', 'Comprehensive Dashboard Data'),
        ('/store-metrics', 'Store Performance Metrics'),
        ('/financial-health', 'Financial Health Score'),
        ('/alerts', 'Executive Alerts'),
        ('/correlations', 'Correlation Insights'),
        ('/store-comparison', 'Store Comparison Analysis'),
        ('/revenue-prediction/3607', 'Revenue Prediction - Store 3607'),
        ('/revenue-prediction/6800', 'Revenue Prediction - Store 6800'),
        ('/revenue-prediction/8101', 'Revenue Prediction - Store 8101'),
    ]
    
    for endpoint, description in endpoints:
        test_endpoint(endpoint, description)
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()