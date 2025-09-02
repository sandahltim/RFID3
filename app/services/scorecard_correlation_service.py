"""
Scorecard Correlation Service for Executive Dashboard
Provides real-time correlation analysis and predictive insights
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

class ScorecardCorrelationService:
    """Service for analyzing scorecard trends and providing executive insights"""
    
    # Store mapping reference - each store has multiple identifiers
    STORE_MAPPING = {
        '001': {'scorecard_id': '3607', 'name': 'Wayzata', 'opened_date': '2008-01-01'},
        '002': {'scorecard_id': '6800', 'name': 'Brooklyn Park', 'opened_date': '2022-01-01'}, 
        '003': {'scorecard_id': '8101', 'name': 'Fridley', 'opened_date': '2022-01-01'},
        '004': {'scorecard_id': '728', 'name': 'Elk River', 'opened_date': '2024-01-01'},
        '000': {'scorecard_id': '000', 'name': 'Company Wide', 'opened_date': '2000-01-01'},
        '0': {'scorecard_id': '000', 'name': 'Company Wide', 'opened_date': '2000-01-01'}
    }
    
    def __init__(self, csv_path='shared/POR/ScorecardTrends9.1.25.csv'):
        self.csv_path = csv_path
        self.df = None
        self.pos_data = None  # Will hold POS transaction data
        self.correlations = None
        self.store_metrics = {}
        self.alert_thresholds = {}
        self._load_and_process_data()
        self._load_pos_data()
    
    def _load_and_process_data(self):
        """Load and process scorecard data"""
        try:
            # Load CSV
            self.df = pd.read_csv(self.csv_path)
            
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
            
            # Select only relevant columns
            relevant_cols = list(column_mapping.keys())
            self.df = self.df[relevant_cols].copy()
            self.df.rename(columns=column_mapping, inplace=True)
            
            # Convert week_ending to datetime
            self.df['week_ending'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(self.df['week_ending'], 'D')
            
            # Keep all rows that have either total revenue OR store-specific revenue
            # Early data (2022-2023) only has total revenue, later data has store breakdowns
            self.df = self.df.dropna(subset=['total_weekly_revenue'], how='all')
            
            # Sort by date
            self.df.sort_values('week_ending', inplace=True)
            
            # Calculate alert thresholds
            self._calculate_alert_thresholds()
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.df = pd.DataFrame()
    
    def _load_pos_data(self):
        """Load POS transaction data for deeper historical analysis"""
        try:
            pos_path = 'shared/POR/transactions8.26.25.csv'
            self.pos_data = pd.read_csv(pos_path)
            
            # Convert contract dates
            self.pos_data['Contract Date'] = pd.to_datetime(self.pos_data['Contract Date'], errors='coerce')
            
            # Add scorecard store mapping - handle both integer and string store numbers
            def map_store_id(store_no):
                # Convert to padded string format (001, 002, etc.)
                if pd.isna(store_no):
                    return 'Unknown'
                padded_store = str(int(store_no)).zfill(3)
                return self.STORE_MAPPING.get(padded_store, {}).get('scorecard_id', 'Unknown')
            
            def get_store_opened_date(store_no):
                if pd.isna(store_no):
                    return None
                padded_store = str(int(store_no)).zfill(3)
                opened_str = self.STORE_MAPPING.get(padded_store, {}).get('opened_date')
                return pd.to_datetime(opened_str) if opened_str else None
            
            self.pos_data['scorecard_store_id'] = self.pos_data['Store No'].apply(map_store_id)
            self.pos_data['store_opened_date'] = self.pos_data['Store No'].apply(get_store_opened_date)
            
            # Filter transactions to only include dates AFTER each store's actual opening
            # This removes data quality issues where transactions predate store openings
            valid_transactions = (
                (self.pos_data['Contract Date'].notna()) &
                (self.pos_data['scorecard_store_id'].isin(['3607', '6800', '8101', '728', '000'])) &
                (self.pos_data['store_opened_date'].notna()) &
                (self.pos_data['Contract Date'] >= self.pos_data['store_opened_date'])
            )
            
            self.pos_data = self.pos_data[valid_transactions].copy()
            
            print(f"Loaded {len(self.pos_data):,} POS transactions from {self.pos_data['Contract Date'].min()} to {self.pos_data['Contract Date'].max()}")
            
        except Exception as e:
            print(f"Error loading POS data: {e}")
            self.pos_data = pd.DataFrame()
    
    def _calculate_alert_thresholds(self):
        """Calculate alert thresholds based on historical data"""
        if self.df.empty:
            return
        
        # AR aging thresholds
        ar_data = self.df['ar_over_45_days_percent'].dropna()
        if len(ar_data) > 0:
            self.alert_thresholds['ar_warning'] = ar_data.quantile(0.75)
            self.alert_thresholds['ar_critical'] = ar_data.quantile(0.90)
        
        # Revenue thresholds
        revenue_data = self.df['total_weekly_revenue'].dropna()
        if len(revenue_data) > 0:
            self.alert_thresholds['revenue_low'] = revenue_data.quantile(0.10)
            self.alert_thresholds['revenue_critical_low'] = revenue_data.quantile(0.05)
        
        # Discount thresholds
        discount_data = self.df['total_discount'].dropna()
        if len(discount_data) > 0:
            self.alert_thresholds['discount_warning'] = discount_data.quantile(0.75)
            self.alert_thresholds['discount_critical'] = discount_data.quantile(0.90)
    
    def get_store_performance_metrics(self):
        """Get comprehensive store performance metrics using both scorecard and POS data"""
        stores = ['3607', '6800', '8101', '728']
        metrics = {}
        
        for store in stores:
            revenue_col = f'revenue_{store}'
            contracts_col = f'new_contracts_{store}'
            
            # Get scorecard trend data (recent, aggregated)
            scorecard_data = None
            if revenue_col in self.df.columns:
                scorecard_data = self.df[[revenue_col, contracts_col, 'week_ending']].dropna(subset=[revenue_col])
            
            # Get POS transaction data (historical, detailed)  
            pos_store_data = None
            if self.pos_data is not None and not self.pos_data.empty:
                pos_store_data = self.pos_data[self.pos_data['scorecard_store_id'] == store].copy()
                
            # Build comprehensive metrics
            store_metrics = {'scorecard_store_id': store, 'store_name': self._get_store_name(store)}
            
            # Scorecard metrics (recent aggregated data)
            if scorecard_data is not None and len(scorecard_data) > 0:
                avg_revenue = scorecard_data[revenue_col].mean()
                std_revenue = scorecard_data[revenue_col].std()
                
                store_metrics.update({
                    'avg_weekly_revenue': round(avg_revenue, 2),
                    'revenue_volatility': round(std_revenue / avg_revenue, 3) if avg_revenue > 0 else 0,
                    'avg_contracts': round(scorecard_data[contracts_col].mean(), 1) if scorecard_data[contracts_col].notna().sum() > 0 else 0,
                    'revenue_per_contract': round(avg_revenue / scorecard_data[contracts_col].mean(), 2) if scorecard_data[contracts_col].mean() > 0 else 0,
                    'latest_revenue': round(scorecard_data[revenue_col].iloc[-1], 2),
                    'trend': self._calculate_trend(scorecard_data[revenue_col]),
                    'scorecard_data_start': scorecard_data['week_ending'].min().strftime('%Y-%m-%d'),
                    'scorecard_data_points': len(scorecard_data)
                })
            
            # POS metrics (deep historical data)
            if pos_store_data is not None and len(pos_store_data) > 0:
                pos_revenue = pos_store_data['Total'].fillna(0)
                
                store_metrics.update({
                    'pos_total_transactions': len(pos_store_data),
                    'pos_data_start': pos_store_data['Contract Date'].min().strftime('%Y-%m-%d'), 
                    'pos_data_end': pos_store_data['Contract Date'].max().strftime('%Y-%m-%d'),
                    'pos_total_revenue': round(pos_revenue.sum(), 2),
                    'pos_avg_transaction': round(pos_revenue.mean(), 2),
                    'pos_years_of_history': round((pos_store_data['Contract Date'].max() - pos_store_data['Contract Date'].min()).days / 365.25, 1)
                })
            
            if store_metrics.get('avg_weekly_revenue') or store_metrics.get('pos_total_transactions'):
                metrics[store] = store_metrics
        
        return metrics
    
    def _get_store_name(self, store_id):
        """Get store name from mapping"""
        for pos_id, info in self.STORE_MAPPING.items():
            if info['scorecard_id'] == store_id:
                return info['name']
        return f'Store {store_id}'
    
    def get_store_timeline_analysis(self):
        """Analyze store timeline data quality and provide insights"""
        if self.pos_data is None or self.pos_data.empty:
            return {}
        
        timeline_analysis = {}
        for store_id in ['3607', '6800', '8101', '728']:
            store_data = self.pos_data[self.pos_data['scorecard_store_id'] == store_id]
            
            if len(store_data) > 0:
                # Find the corresponding POS store info
                store_info = None
                for pos_id, info in self.STORE_MAPPING.items():
                    if info['scorecard_id'] == store_id:
                        store_info = info
                        break
                
                if store_info:
                    opened_date = pd.to_datetime(store_info['opened_date'])
                    actual_first_transaction = store_data['Contract Date'].min()
                    actual_last_transaction = store_data['Contract Date'].max()
                    
                    timeline_analysis[store_id] = {
                        'store_name': store_info['name'],
                        'official_opening': opened_date.strftime('%Y-%m-%d'),
                        'first_transaction': actual_first_transaction.strftime('%Y-%m-%d'),
                        'last_transaction': actual_last_transaction.strftime('%Y-%m-%d'),
                        'valid_transactions': len(store_data),
                        'years_of_data': round((actual_last_transaction - actual_first_transaction).days / 365.25, 1),
                        'data_starts_after_opening': actual_first_transaction >= opened_date
                    }
        
        return timeline_analysis
    
    def _calculate_trend(self, series, window=4):
        """Calculate trend direction"""
        if len(series) < window:
            return 'neutral'
        
        recent = series.tail(window).mean()
        previous = series.iloc[-window*2:-window].mean() if len(series) >= window*2 else series.head(window).mean()
        
        if recent > previous * 1.05:
            return 'up'
        elif recent < previous * 0.95:
            return 'down'
        else:
            return 'neutral'
    
    def get_revenue_predictions(self, store_id):
        """Get revenue predictions based on reservation pipeline"""
        revenue_col = f'revenue_{store_id}'
        reservation_col = f'reservation_next14_{store_id}'
        total_res_col = f'total_reservation_{store_id}'
        
        if not all(col in self.df.columns for col in [revenue_col, reservation_col]):
            return None
        
        # Get recent data
        recent_data = self.df[[revenue_col, reservation_col, total_res_col, 'week_ending']].dropna().tail(12)
        
        if len(recent_data) < 4:
            return None
        
        # Calculate correlation-based prediction
        correlation = recent_data[revenue_col].corr(recent_data[reservation_col].shift(1))
        
        # Simple prediction based on last reservation value
        last_reservation = recent_data[reservation_col].iloc[-1]
        avg_conversion_rate = recent_data[revenue_col].mean() / recent_data[reservation_col].mean() if recent_data[reservation_col].mean() > 0 else 1
        
        prediction = {
            'predicted_revenue': round(last_reservation * avg_conversion_rate, 2),
            'confidence': 'High' if abs(correlation) > 0.7 else 'Medium' if abs(correlation) > 0.4 else 'Low',
            'correlation': round(correlation, 3),
            'reservation_pipeline': round(last_reservation, 2),
            'avg_conversion_rate': round(avg_conversion_rate, 2)
        }
        
        return prediction
    
    def get_financial_health_score(self):
        """Calculate comprehensive financial health score"""
        latest_data = self.df.dropna(subset=['ar_over_45_days_percent', 'total_discount', 'total_weekly_revenue']).tail(1)
        
        if latest_data.empty:
            return None
        
        ar_percent = latest_data['ar_over_45_days_percent'].iloc[0]
        total_revenue = latest_data['total_weekly_revenue'].iloc[0]
        total_discount = latest_data['total_discount'].iloc[0] if 'total_discount' in latest_data else 0
        
        # Calculate component scores (0-100, higher is better)
        ar_score = max(0, 100 * (1 - ar_percent))
        
        discount_rate = total_discount / total_revenue if total_revenue > 0 else 0
        discount_score = max(0, 100 * (1 - discount_rate * 10))  # Assuming 10% discount is very high
        
        # Revenue health based on percentile
        revenue_percentile = (self.df['total_weekly_revenue'] <= total_revenue).mean()
        revenue_score = revenue_percentile * 100
        
        # Overall health score (weighted average)
        health_score = (ar_score * 0.4 + discount_score * 0.3 + revenue_score * 0.3)
        
        return {
            'overall_score': round(health_score, 1),
            'ar_score': round(ar_score, 1),
            'discount_score': round(discount_score, 1),
            'revenue_score': round(revenue_score, 1),
            'ar_percent': round(ar_percent * 100, 1),
            'discount_rate': round(discount_rate * 100, 2),
            'status': 'Healthy' if health_score > 70 else 'Warning' if health_score > 50 else 'Critical'
        }
    
    def get_executive_alerts(self):
        """Get current executive alerts based on thresholds"""
        alerts = []
        
        latest_data = self.df.tail(1)
        if latest_data.empty:
            return alerts
        
        # AR aging alert
        if 'ar_over_45_days_percent' in latest_data:
            ar_percent = latest_data['ar_over_45_days_percent'].iloc[0]
            if ar_percent > self.alert_thresholds.get('ar_critical', 0.3):
                alerts.append({
                    'type': 'critical',
                    'metric': 'AR Aging',
                    'message': f'AR over 45 days at {ar_percent*100:.1f}% (Critical: >{self.alert_thresholds["ar_critical"]*100:.1f}%)',
                    'action': 'Immediate collection efforts required'
                })
            elif ar_percent > self.alert_thresholds.get('ar_warning', 0.2):
                alerts.append({
                    'type': 'warning',
                    'metric': 'AR Aging',
                    'message': f'AR over 45 days at {ar_percent*100:.1f}% (Warning: >{self.alert_thresholds["ar_warning"]*100:.1f}%)',
                    'action': 'Review collection processes'
                })
        
        # Revenue alert
        if 'total_weekly_revenue' in latest_data:
            revenue = latest_data['total_weekly_revenue'].iloc[0]
            if revenue < self.alert_thresholds.get('revenue_critical_low', 0):
                alerts.append({
                    'type': 'critical',
                    'metric': 'Weekly Revenue',
                    'message': f'Revenue at ${revenue:,.0f} (Critical low: <${self.alert_thresholds["revenue_critical_low"]:,.0f})',
                    'action': 'Review sales pipeline and conversion rates'
                })
        
        # Store-specific alerts
        for store in ['3607', '6800', '728', '8101']:
            revenue_col = f'revenue_{store}'
            if revenue_col in latest_data:
                store_revenue = latest_data[revenue_col].iloc[0]
                if pd.notna(store_revenue):
                    historical_avg = self.df[revenue_col].mean()
                    if store_revenue < historical_avg * 0.7:
                        alerts.append({
                            'type': 'warning',
                            'metric': f'Store {store} Revenue',
                            'message': f'Revenue at ${store_revenue:,.0f} (30% below average)',
                            'action': f'Investigate Store {store} performance issues'
                        })
        
        return alerts
    
    def get_correlation_insights(self):
        """Get key correlation insights for decision making"""
        insights = []
        
        # Revenue drivers
        for store in ['3607', '6800', '728', '8101']:
            revenue_col = f'revenue_{store}'
            contracts_col = f'new_contracts_{store}'
            
            if all(col in self.df.columns for col in [revenue_col, contracts_col]):
                corr = self.df[[revenue_col, contracts_col]].corr().iloc[0, 1]
                if abs(corr) > 0.7:
                    insights.append({
                        'type': 'strong_correlation',
                        'relationship': f'Store {store} Contracts → Revenue',
                        'correlation': round(corr, 3),
                        'insight': f'Strong relationship between contracts and revenue in Store {store}',
                        'action': 'Focus on contract generation to drive revenue'
                    })
        
        # Financial correlations
        if all(col in self.df.columns for col in ['ar_over_45_days_percent', 'total_weekly_revenue']):
            ar_revenue_corr = self.df[['ar_over_45_days_percent', 'total_weekly_revenue']].corr().iloc[0, 1]
            if abs(ar_revenue_corr) > 0.3:
                insights.append({
                    'type': 'financial_correlation',
                    'relationship': 'AR Aging → Revenue',
                    'correlation': round(ar_revenue_corr, 3),
                    'insight': 'AR aging significantly impacts revenue',
                    'action': 'Improve collection processes to boost revenue'
                })
        
        return insights
    
    def get_dashboard_data(self):
        """Get all data needed for executive dashboard"""
        # Get total data range
        total_data_points = len(self.df)
        
        # Get store-specific data range
        store_revenue_cols = ['revenue_3607', 'revenue_6800', 'revenue_728', 'revenue_8101']
        store_data = self.df.dropna(subset=store_revenue_cols, how='all')
        store_data_points = len(store_data)
        
        return {
            'store_metrics': self.get_store_performance_metrics(),
            'financial_health': self.get_financial_health_score(),
            'alerts': self.get_executive_alerts(),
            'correlations': self.get_correlation_insights(),
            'last_updated': datetime.now().isoformat(),
            'data_points': total_data_points,
            'store_data_points': store_data_points,
            'date_range': {
                'start': self.df['week_ending'].min().isoformat() if not self.df.empty else None,
                'end': self.df['week_ending'].max().isoformat() if not self.df.empty else None
            },
            'store_data_range': {
                'start': store_data['week_ending'].min().isoformat() if not store_data.empty else None,
                'end': store_data['week_ending'].max().isoformat() if not store_data.empty else None
            }
        }

# Singleton instance
_service_instance = None

def get_scorecard_service():
    """Get or create the scorecard correlation service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ScorecardCorrelationService()
    return _service_instance