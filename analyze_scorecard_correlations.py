#!/usr/bin/env python3
"""
Comprehensive Scorecard Trends Correlation Analysis
Identifies high-value insights for executive dashboard
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

def load_and_clean_data():
    """Load and clean the scorecard trends data"""
    # Load data
    df = pd.read_csv('shared/POR/ScorecardTrends9.1.25.csv')
    
    # Select relevant columns (ignore empty Column1-29)
    relevant_cols = [
        'Week ending Sunday',
        'Total Weekly Revenue',
        '3607 Revenue', '6800 Revenue', '728 Revenue', '8101 Revenue',
        '# New Open Contracts 3607', '# New Open Contracts 6800', 
        '# New Open Contracts 728', '# New Open Contracts 8101',
        '# Deliveries Scheduled next 7 days Weds-Tues 8101',
        '$ on Reservation - Next 14 days - 3607', '$ on Reservation - Next 14 days - 6800',
        '$ on Reservation - Next 14 days - 728', '$ on Reservation - Next 14 days - 8101',
        'Total $ on Reservation 3607', 'Total $ on Reservation 6800',
        'Total $ on Reservation 728', 'Total $ on Reservation 8101',
        '% -Total AR ($) > 45 days',
        'Total Discount $ Company Wide',
        'WEEK NUMBER',
        '# Open Quotes 8101',
        '$ Total AR (Cash Customers)'
    ]
    
    df = df[relevant_cols].copy()
    
    # Rename columns for easier access
    column_mapping = {
        'Week ending Sunday': 'week_ending',
        'Total Weekly Revenue': 'total_weekly_revenue',
        '3607 Revenue': 'revenue_3607',
        '6800 Revenue': 'revenue_6800',
        '728 Revenue': 'revenue_728',
        '8101 Revenue': 'revenue_8101',
        '# New Open Contracts 3607': 'new_contracts_3607',
        '# New Open Contracts 6800': 'new_contracts_6800',
        '# New Open Contracts 728': 'new_contracts_728',
        '# New Open Contracts 8101': 'new_contracts_8101',
        '# Deliveries Scheduled next 7 days Weds-Tues 8101': 'deliveries_scheduled_8101',
        '$ on Reservation - Next 14 days - 3607': 'reservation_next14_3607',
        '$ on Reservation - Next 14 days - 6800': 'reservation_next14_6800',
        '$ on Reservation - Next 14 days - 728': 'reservation_next14_728',
        '$ on Reservation - Next 14 days - 8101': 'reservation_next14_8101',
        'Total $ on Reservation 3607': 'total_reservation_3607',
        'Total $ on Reservation 6800': 'total_reservation_6800',
        'Total $ on Reservation 728': 'total_reservation_728',
        'Total $ on Reservation 8101': 'total_reservation_8101',
        '% -Total AR ($) > 45 days': 'ar_over_45_days_percent',
        'Total Discount $ Company Wide': 'total_discount',
        'WEEK NUMBER': 'week_number',
        '# Open Quotes 8101': 'open_quotes_8101',
        '$ Total AR (Cash Customers)': 'total_ar_cash'
    }
    
    df.rename(columns=column_mapping, inplace=True)
    
    # Convert week_ending to datetime (Excel serial date)
    df['week_ending'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(df['week_ending'], 'D')
    
    # Remove rows with all NaN values in revenue columns
    revenue_cols = ['revenue_3607', 'revenue_6800', 'revenue_728', 'revenue_8101']
    df = df.dropna(subset=revenue_cols, how='all')
    
    # Sort by date
    df.sort_values('week_ending', inplace=True)
    
    return df

def calculate_correlations(df):
    """Calculate correlation matrix and identify significant relationships"""
    
    # Select numeric columns for correlation
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    numeric_cols = [col for col in numeric_cols if col != 'week_number']  # Exclude week number
    
    # Calculate correlation matrix
    corr_matrix = df[numeric_cols].corr()
    
    # Find strong correlations (abs > 0.7)
    strong_correlations = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_value = corr_matrix.iloc[i, j]
            if abs(corr_value) > 0.7 and not pd.isna(corr_value):
                strong_correlations.append({
                    'var1': corr_matrix.columns[i],
                    'var2': corr_matrix.columns[j],
                    'correlation': round(corr_value, 3)
                })
    
    # Sort by absolute correlation
    strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
    
    return corr_matrix, strong_correlations

def analyze_store_performance(df):
    """Analyze cross-store performance patterns"""
    
    store_analysis = {}
    stores = ['3607', '6800', '728', '8101']
    
    for store in stores:
        revenue_col = f'revenue_{store}'
        contracts_col = f'new_contracts_{store}'
        
        if revenue_col in df.columns:
            store_data = df[[revenue_col, contracts_col]].dropna()
            
            if len(store_data) > 0:
                store_analysis[store] = {
                    'avg_revenue': round(store_data[revenue_col].mean(), 2),
                    'std_revenue': round(store_data[revenue_col].std(), 2),
                    'cv_revenue': round(store_data[revenue_col].std() / store_data[revenue_col].mean(), 3) if store_data[revenue_col].mean() > 0 else 0,
                    'avg_contracts': round(store_data[contracts_col].mean(), 1) if contracts_col in store_data.columns else 0,
                    'revenue_per_contract': round(store_data[revenue_col].mean() / store_data[contracts_col].mean(), 2) if contracts_col in store_data.columns and store_data[contracts_col].mean() > 0 else 0,
                    'data_points': len(store_data)
                }
    
    # Calculate store rankings
    if store_analysis:
        # Rank by average revenue
        revenue_ranking = sorted(store_analysis.items(), key=lambda x: x[1]['avg_revenue'], reverse=True)
        
        # Rank by revenue stability (lower CV is better)
        stability_ranking = sorted(store_analysis.items(), key=lambda x: x[1]['cv_revenue'])
        
        # Rank by revenue per contract efficiency
        efficiency_ranking = sorted(store_analysis.items(), key=lambda x: x[1]['revenue_per_contract'], reverse=True)
    
    return store_analysis, {
        'revenue_ranking': revenue_ranking if store_analysis else [],
        'stability_ranking': stability_ranking if store_analysis else [],
        'efficiency_ranking': efficiency_ranking if store_analysis else []
    }

def analyze_predictive_relationships(df):
    """Analyze predictive relationships between reservations and future revenue"""
    
    predictive_analysis = {}
    stores = ['3607', '6800', '8101']  # Store 728 has no reservation data
    
    for store in stores:
        revenue_col = f'revenue_{store}'
        reservation_14d_col = f'reservation_next14_{store}'
        total_reservation_col = f'total_reservation_{store}'
        
        if all(col in df.columns for col in [revenue_col, reservation_14d_col]):
            # Create lagged features (reservations from 1-2 weeks ago)
            store_df = df[[revenue_col, reservation_14d_col, total_reservation_col, 'week_ending']].copy()
            store_df[f'reservation_14d_lag1'] = store_df[reservation_14d_col].shift(1)
            store_df[f'reservation_14d_lag2'] = store_df[reservation_14d_col].shift(2)
            store_df[f'total_reservation_lag1'] = store_df[total_reservation_col].shift(1)
            
            # Calculate correlations with lagged features
            clean_df = store_df.dropna()
            
            if len(clean_df) > 10:
                predictive_analysis[store] = {
                    'current_week_correlation': round(clean_df[revenue_col].corr(clean_df[reservation_14d_col]), 3),
                    '1_week_lag_correlation': round(clean_df[revenue_col].corr(clean_df['reservation_14d_lag1']), 3),
                    '2_week_lag_correlation': round(clean_df[revenue_col].corr(clean_df['reservation_14d_lag2']), 3),
                    'total_reservation_correlation': round(clean_df[revenue_col].corr(clean_df['total_reservation_lag1']), 3),
                    'sample_size': len(clean_df)
                }
                
                # Simple linear regression for predictive power (using numpy instead of sklearn)
                X = clean_df[['reservation_14d_lag1', 'total_reservation_lag1']].values
                y = clean_df[revenue_col].values
                
                if len(X) > 5:
                    # Add intercept term
                    X_with_intercept = np.column_stack([np.ones(len(X)), X])
                    
                    # Calculate coefficients using normal equation
                    try:
                        coefficients = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
                        y_pred = X_with_intercept @ coefficients
                        
                        # Calculate R-squared
                        ss_res = np.sum((y - y_pred) ** 2)
                        ss_tot = np.sum((y - np.mean(y)) ** 2)
                        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                        
                        predictive_analysis[store]['r2_score'] = round(r2, 3)
                        predictive_analysis[store]['predictive_power'] = 'Strong' if r2 > 0.5 else 'Moderate' if r2 > 0.3 else 'Weak'
                    except:
                        predictive_analysis[store]['r2_score'] = 0
                        predictive_analysis[store]['predictive_power'] = 'Unable to calculate'
    
    return predictive_analysis

def analyze_financial_health(df):
    """Analyze financial health correlations"""
    
    financial_cols = ['ar_over_45_days_percent', 'total_discount', 'total_weekly_revenue', 'total_ar_cash']
    financial_df = df[financial_cols].dropna()
    
    financial_insights = {}
    
    if len(financial_df) > 10:
        # AR aging impact on revenue
        ar_revenue_corr = financial_df['ar_over_45_days_percent'].corr(financial_df['total_weekly_revenue'])
        
        # Discount impact on revenue
        discount_revenue_corr = financial_df['total_discount'].corr(financial_df['total_weekly_revenue'])
        
        # Calculate financial health score components
        financial_df['ar_health_score'] = 100 * (1 - financial_df['ar_over_45_days_percent'])
        financial_df['discount_health_score'] = 100 * (1 - financial_df['total_discount'] / financial_df['total_weekly_revenue'].clip(lower=1))
        
        financial_insights = {
            'ar_revenue_correlation': round(ar_revenue_corr, 3),
            'discount_revenue_correlation': round(discount_revenue_corr, 3),
            'avg_ar_over_45_days': round(financial_df['ar_over_45_days_percent'].mean() * 100, 1),
            'median_ar_over_45_days': round(financial_df['ar_over_45_days_percent'].median() * 100, 1),
            'ar_volatility': round(financial_df['ar_over_45_days_percent'].std() * 100, 1),
            'critical_ar_threshold': round(financial_df['ar_over_45_days_percent'].quantile(0.75) * 100, 1),
            'discount_as_pct_revenue': round((financial_df['total_discount'] / financial_df['total_weekly_revenue'].clip(lower=1)).mean() * 100, 2)
        }
        
        # Identify alert thresholds
        financial_insights['alert_thresholds'] = {
            'ar_critical': financial_df['ar_over_45_days_percent'].quantile(0.9),
            'ar_warning': financial_df['ar_over_45_days_percent'].quantile(0.75),
            'discount_critical': financial_df['total_discount'].quantile(0.9),
            'revenue_critical_low': financial_df['total_weekly_revenue'].quantile(0.1)
        }
    
    return financial_insights

def analyze_operational_efficiency(df):
    """Analyze operational efficiency metrics"""
    
    efficiency_metrics = {}
    
    # Focus on store 8101 which has delivery data
    store_df = df[['revenue_8101', 'new_contracts_8101', 'deliveries_scheduled_8101', 'open_quotes_8101']].dropna()
    
    if len(store_df) > 10:
        # Contract to revenue conversion
        contract_revenue_corr = store_df['new_contracts_8101'].corr(store_df['revenue_8101'])
        
        # Delivery scheduling efficiency
        delivery_revenue_corr = store_df['deliveries_scheduled_8101'].corr(store_df['revenue_8101'])
        
        # Quote conversion analysis
        quote_contract_corr = store_df['open_quotes_8101'].corr(store_df['new_contracts_8101'])
        
        efficiency_metrics = {
            'contract_revenue_correlation': round(contract_revenue_corr, 3),
            'delivery_revenue_correlation': round(delivery_revenue_corr, 3),
            'quote_contract_correlation': round(quote_contract_corr, 3),
            'avg_contracts_per_week': round(store_df['new_contracts_8101'].mean(), 1),
            'avg_deliveries_per_week': round(store_df['deliveries_scheduled_8101'].mean(), 1),
            'avg_open_quotes': round(store_df['open_quotes_8101'].mean(), 1),
            'revenue_per_contract': round(store_df['revenue_8101'].sum() / store_df['new_contracts_8101'].sum(), 2) if store_df['new_contracts_8101'].sum() > 0 else 0,
            'delivery_fulfillment_ratio': round(store_df['deliveries_scheduled_8101'].sum() / store_df['new_contracts_8101'].sum(), 2) if store_df['new_contracts_8101'].sum() > 0 else 0
        }
    
    return efficiency_metrics

def identify_executive_alerts(df, financial_insights, efficiency_metrics):
    """Identify key metrics for executive alerts"""
    
    alerts = {
        'critical_metrics': [],
        'leading_indicators': [],
        'performance_triggers': []
    }
    
    # Critical financial health metrics
    if financial_insights:
        if 'alert_thresholds' in financial_insights:
            alerts['critical_metrics'].append({
                'metric': 'AR Over 45 Days',
                'critical_threshold': f"{financial_insights['alert_thresholds']['ar_critical']*100:.1f}%",
                'warning_threshold': f"{financial_insights['alert_thresholds']['ar_warning']*100:.1f}%",
                'current_avg': f"{financial_insights['avg_ar_over_45_days']:.1f}%",
                'alert_type': 'financial_health'
            })
    
    # Leading indicators from reservations
    alerts['leading_indicators'].append({
        'metric': '14-Day Reservation Pipeline',
        'description': 'Strong predictor of revenue 1-2 weeks ahead',
        'monitoring_frequency': 'Weekly',
        'alert_type': 'predictive'
    })
    
    # Performance triggers
    if efficiency_metrics:
        alerts['performance_triggers'].append({
            'metric': 'Contract to Revenue Conversion',
            'optimal_range': 'Correlation > 0.7',
            'current_value': efficiency_metrics.get('contract_revenue_correlation', 'N/A'),
            'alert_type': 'operational'
        })
    
    # Week-over-week revenue volatility
    revenue_data = df['total_weekly_revenue'].dropna()
    if len(revenue_data) > 4:
        weekly_changes = revenue_data.pct_change().dropna()
        volatility = weekly_changes.std()
        
        alerts['performance_triggers'].append({
            'metric': 'Weekly Revenue Volatility',
            'critical_threshold': f"{volatility*2*100:.1f}% change",
            'normal_range': f"±{volatility*100:.1f}%",
            'alert_type': 'revenue'
        })
    
    return alerts

def generate_executive_summary(all_results):
    """Generate executive summary with key findings"""
    
    summary = {
        'key_findings': [],
        'actionable_insights': [],
        'dashboard_recommendations': []
    }
    
    # Key findings
    if all_results['store_rankings']['revenue_ranking']:
        top_store = all_results['store_rankings']['revenue_ranking'][0]
        summary['key_findings'].append(
            f"Store {top_store[0]} is the revenue leader with ${top_store[1]['avg_revenue']:,.0f} weekly average"
        )
    
    if all_results['predictive_analysis']:
        best_predictor = max(all_results['predictive_analysis'].items(), 
                           key=lambda x: x[1].get('r2_score', 0))
        if best_predictor[1].get('r2_score', 0) > 0.3:
            summary['key_findings'].append(
                f"Store {best_predictor[0]} reservations show {best_predictor[1]['predictive_power']} predictive power (R²={best_predictor[1]['r2_score']})"
            )
    
    if all_results['financial_health']:
        summary['key_findings'].append(
            f"AR over 45 days averages {all_results['financial_health']['avg_ar_over_45_days']:.1f}% with high volatility (±{all_results['financial_health']['ar_volatility']:.1f}%)"
        )
    
    # Actionable insights
    summary['actionable_insights'] = [
        "Implement weekly monitoring of 14-day reservation pipeline as revenue predictor",
        "Set AR aging alerts at 75th percentile for early intervention",
        "Focus on improving contract-to-revenue conversion in underperforming stores",
        "Monitor quote-to-contract conversion as leading indicator"
    ]
    
    # Dashboard recommendations
    summary['dashboard_recommendations'] = [
        {
            'widget': 'Store Performance Scorecard',
            'metrics': ['Weekly Revenue', 'Contract Volume', 'Revenue/Contract'],
            'update_frequency': 'Weekly',
            'visualization': 'Comparative bar charts with trend lines'
        },
        {
            'widget': 'Revenue Predictor',
            'metrics': ['14-Day Reservations', 'Predicted Revenue', 'Confidence Interval'],
            'update_frequency': 'Daily',
            'visualization': 'Time series with forecast bands'
        },
        {
            'widget': 'Financial Health Monitor',
            'metrics': ['AR Aging %', 'Discount Rate', 'Cash Position'],
            'update_frequency': 'Daily',
            'visualization': 'Gauge charts with alert zones'
        },
        {
            'widget': 'Executive Alert Panel',
            'metrics': ['Critical Thresholds', 'Anomaly Detection', 'Action Items'],
            'update_frequency': 'Real-time',
            'visualization': 'Alert cards with severity indicators'
        }
    ]
    
    return summary

def main():
    """Main analysis execution"""
    
    print("=" * 80)
    print("SCORECARD TRENDS CORRELATION ANALYSIS")
    print("=" * 80)
    
    # Load and clean data
    print("\n1. LOADING AND CLEANING DATA...")
    df = load_and_clean_data()
    print(f"   - Loaded {len(df)} valid records")
    print(f"   - Date range: {df['week_ending'].min().date()} to {df['week_ending'].max().date()}")
    
    # Calculate correlations
    print("\n2. CALCULATING CORRELATIONS...")
    corr_matrix, strong_correlations = calculate_correlations(df)
    print(f"   - Found {len(strong_correlations)} strong correlations (|r| > 0.7)")
    
    # Store performance analysis
    print("\n3. ANALYZING STORE PERFORMANCE...")
    store_analysis, store_rankings = analyze_store_performance(df)
    print(f"   - Analyzed {len(store_analysis)} stores")
    
    # Predictive analysis
    print("\n4. ANALYZING PREDICTIVE RELATIONSHIPS...")
    predictive_analysis = analyze_predictive_relationships(df)
    print(f"   - Evaluated predictive models for {len(predictive_analysis)} stores")
    
    # Financial health analysis
    print("\n5. ANALYZING FINANCIAL HEALTH...")
    financial_health = analyze_financial_health(df)
    
    # Operational efficiency
    print("\n6. ANALYZING OPERATIONAL EFFICIENCY...")
    operational_efficiency = analyze_operational_efficiency(df)
    
    # Executive alerts
    print("\n7. IDENTIFYING EXECUTIVE ALERTS...")
    executive_alerts = identify_executive_alerts(df, financial_health, operational_efficiency)
    
    # Compile all results
    all_results = {
        'analysis_date': datetime.now().isoformat(),
        'data_summary': {
            'total_records': len(df),
            'date_range': f"{df['week_ending'].min().date()} to {df['week_ending'].max().date()}",
            'weeks_analyzed': df['week_ending'].nunique()
        },
        'strong_correlations': strong_correlations[:10],  # Top 10
        'store_analysis': store_analysis,
        'store_rankings': store_rankings,
        'predictive_analysis': predictive_analysis,
        'financial_health': financial_health,
        'operational_efficiency': operational_efficiency,
        'executive_alerts': executive_alerts
    }
    
    # Generate executive summary
    print("\n8. GENERATING EXECUTIVE SUMMARY...")
    executive_summary = generate_executive_summary(all_results)
    all_results['executive_summary'] = executive_summary
    
    # Save results
    output_file = f"scorecard_correlation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✓ Analysis complete! Results saved to: {output_file}")
    
    # Print key insights
    print("\n" + "=" * 80)
    print("KEY INSIGHTS FOR EXECUTIVE DASHBOARD")
    print("=" * 80)
    
    print("\n📊 CROSS-STORE PERFORMANCE PATTERNS:")
    if store_rankings['revenue_ranking']:
        print("\n   Revenue Leaders:")
        for i, (store, metrics) in enumerate(store_rankings['revenue_ranking'][:3], 1):
            print(f"   {i}. Store {store}: ${metrics['avg_revenue']:,.0f}/week (σ=${metrics['std_revenue']:,.0f})")
    
    print("\n🔮 REVENUE PREDICTABILITY:")
    for store, pred in predictive_analysis.items():
        if 'r2_score' in pred:
            print(f"   Store {store}: {pred['predictive_power']} prediction (R²={pred['r2_score']:.2f})")
            print(f"      - 1-week lag correlation: {pred['1_week_lag_correlation']:.2f}")
    
    print("\n💰 FINANCIAL HEALTH CORRELATIONS:")
    if financial_health:
        print(f"   - AR >45 days impact on revenue: r={financial_health['ar_revenue_correlation']:.2f}")
        print(f"   - Average AR >45 days: {financial_health['avg_ar_over_45_days']:.1f}%")
        print(f"   - Critical threshold (75th %ile): {financial_health['critical_ar_threshold']:.1f}%")
    
    print("\n⚙️ OPERATIONAL EFFICIENCY:")
    if operational_efficiency:
        print(f"   - Contract→Revenue correlation: {operational_efficiency['contract_revenue_correlation']:.2f}")
        print(f"   - Revenue per contract: ${operational_efficiency['revenue_per_contract']:,.0f}")
        print(f"   - Delivery fulfillment ratio: {operational_efficiency['delivery_fulfillment_ratio']:.2f}")
    
    print("\n🚨 EXECUTIVE ALERT INDICATORS:")
    for alert in executive_alerts['critical_metrics']:
        print(f"   - {alert['metric']}: Current {alert['current_avg']}, Alert at {alert['critical_threshold']}")
    
    print("\n" + "=" * 80)
    
    return all_results

if __name__ == "__main__":
    results = main()