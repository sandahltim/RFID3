#!/usr/bin/env python3
"""Display detailed correlation analysis results"""

import json

# Load the analysis results
with open('scorecard_correlation_analysis_20250901_165521.json', 'r') as f:
    results = json.load(f)

print('=' * 80)
print('COMPREHENSIVE SCORECARD DATA CORRELATION ANALYSIS')
print('=' * 80)

print('\n1. TOP STRONG CORRELATIONS (|r| > 0.7):')
print('-' * 50)
for i, corr in enumerate(results['strong_correlations'][:15], 1):
    print(f"{i:2}. {corr['var1']:30} ↔ {corr['var2']:30} r={corr['correlation']:6.3f}")

print('\n2. STORE PERFORMANCE ANALYSIS:')
print('-' * 50)
for store, metrics in results['store_analysis'].items():
    print(f'\nStore {store}:')
    print(f"  - Average Weekly Revenue: ${metrics['avg_revenue']:,.0f}")
    print(f"  - Revenue Volatility (CV): {metrics['cv_revenue']:.2f}")
    print(f"  - Avg Contracts/Week: {metrics['avg_contracts']:.0f}")
    print(f"  - Revenue per Contract: ${metrics['revenue_per_contract']:,.0f}")

print('\n3. PREDICTIVE ANALYSIS (Reservation → Revenue):')
print('-' * 50)
for store, pred in results['predictive_analysis'].items():
    print(f'\nStore {store}:')
    print(f"  - Current Week Correlation: {pred['current_week_correlation']:.3f}")
    print(f"  - 1-Week Lag Correlation: {pred['1_week_lag_correlation']:.3f}")
    print(f"  - 2-Week Lag Correlation: {pred['2_week_lag_correlation']:.3f}")
    print(f"  - R² Score: {pred['r2_score']:.3f} ({pred['predictive_power']})")
    print(f"  - Sample Size: {pred['sample_size']} weeks")

print('\n4. FINANCIAL HEALTH METRICS:')
print('-' * 50)
fh = results['financial_health']
print(f"  - AR >45 Days Average: {fh['avg_ar_over_45_days']:.1f}%")
print(f"  - AR >45 Days Median: {fh['median_ar_over_45_days']:.1f}%")
print(f"  - AR Volatility: ±{fh['ar_volatility']:.1f}%")
print(f"  - Critical AR Threshold (75th %ile): {fh['critical_ar_threshold']:.1f}%")
print(f"  - Discount as % of Revenue: {fh['discount_as_pct_revenue']:.2f}%")
print(f"  - AR→Revenue Correlation: {fh['ar_revenue_correlation']:.3f}")
print(f"  - Discount→Revenue Correlation: {fh['discount_revenue_correlation']:.3f}")

print('\n  Alert Thresholds:')
for key, value in fh['alert_thresholds'].items():
    if 'ar' in key:
        print(f"    - {key}: {value*100:.1f}%")
    else:
        print(f"    - {key}: ${value:,.0f}")

print('\n5. OPERATIONAL EFFICIENCY (Store 8101):')
print('-' * 50)
oe = results['operational_efficiency']
print(f"  - Contract→Revenue Correlation: {oe['contract_revenue_correlation']:.3f}")
print(f"  - Delivery→Revenue Correlation: {oe['delivery_revenue_correlation']:.3f}")
print(f"  - Quote→Contract Correlation: {oe['quote_contract_correlation']:.3f}")
print(f"  - Avg Contracts/Week: {oe['avg_contracts_per_week']:.0f}")
print(f"  - Avg Deliveries/Week: {oe['avg_deliveries_per_week']:.0f}")
print(f"  - Avg Open Quotes: {oe['avg_open_quotes']:.0f}")
print(f"  - Revenue per Contract: ${oe['revenue_per_contract']:,.0f}")
print(f"  - Delivery Fulfillment Ratio: {oe['delivery_fulfillment_ratio']:.2f}")

print('\n6. STORE RANKINGS:')
print('-' * 50)
print('\n  Revenue Ranking:')
for i, (store, metrics) in enumerate(results['store_rankings']['revenue_ranking'], 1):
    print(f"    {i}. Store {store}: ${metrics['avg_revenue']:,.0f}/week")

print('\n  Stability Ranking (lower CV is better):')
for i, (store, metrics) in enumerate(results['store_rankings']['stability_ranking'], 1):
    print(f"    {i}. Store {store}: CV={metrics['cv_revenue']:.2f}")

print('\n  Efficiency Ranking (Revenue per Contract):')
for i, (store, metrics) in enumerate(results['store_rankings']['efficiency_ranking'], 1):
    print(f"    {i}. Store {store}: ${metrics['revenue_per_contract']:,.0f}/contract")

print('\n7. EXECUTIVE ALERTS:')
print('-' * 50)
print('\n  Critical Metrics:')
for alert in results['executive_alerts']['critical_metrics']:
    print(f"    - {alert['metric']}")
    print(f"      Current: {alert['current_avg']}")
    print(f"      Warning: {alert['warning_threshold']}")
    print(f"      Critical: {alert['critical_threshold']}")

print('\n  Performance Triggers:')
for trigger in results['executive_alerts']['performance_triggers']:
    print(f"    - {trigger['metric']}")
    if 'current_value' in trigger:
        print(f"      Current: {trigger['current_value']}")
    if 'normal_range' in trigger:
        print(f"      Normal Range: {trigger['normal_range']}")
    if 'critical_threshold' in trigger:
        print(f"      Critical: {trigger['critical_threshold']}")

print('\n8. EXECUTIVE DASHBOARD RECOMMENDATIONS:')
print('-' * 50)
for rec in results['executive_summary']['dashboard_recommendations']:
    print(f"\n  Widget: {rec['widget']}")
    print(f"  Metrics: {', '.join(rec['metrics'])}")
    print(f"  Update: {rec['update_frequency']}")
    print(f"  Visual: {rec['visualization']}")

print('\n9. KEY ACTIONABLE INSIGHTS:')
print('-' * 50)
for i, insight in enumerate(results['executive_summary']['actionable_insights'], 1):
    print(f"  {i}. {insight}")

print('\n' + '=' * 80)