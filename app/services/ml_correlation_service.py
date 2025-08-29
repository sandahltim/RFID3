"""
ML Correlation Service
Analyzes correlations between business data and external factors
Uses lightweight models optimized for Pi 5 performance
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from app import db
from app.services.logger import get_logger
import json
import warnings
warnings.filterwarnings('ignore')

# Import ML libraries with fallbacks for Pi compatibility
try:
    from scipy.stats import pearsonr, spearmanr
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Logger will be initialized in the class

try:
    from statsmodels.tsa.stattools import grangercausalitytests
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

logger = get_logger(__name__)

class MLCorrelationService:
    """Service for ML-powered correlation analysis"""
    
    def __init__(self):
        self.logger = logger
    
    def get_business_time_series(self) -> pd.DataFrame:
        """Get business data as time series for correlation analysis"""
        try:
            # Get weekly equipment revenue aggregated by store
            query = text("""
                SELECT 
                    DATE(DATE_SUB(CURRENT_DATE, INTERVAL WEEKDAY(CURRENT_DATE) DAY)) as week_start,
                    current_store,
                    SUM(turnover_ytd) as weekly_revenue,
                    COUNT(*) as item_count,
                    AVG(turnover_ytd) as avg_revenue_per_item
                FROM pos_equipment 
                WHERE inactive = 0 AND turnover_ytd > 0
                GROUP BY week_start, current_store
                ORDER BY week_start, current_store
            """)
            
            df = pd.read_sql(query, db.engine)
            
            if df.empty:
                # Generate sample time series data for demonstration
                self.logger.warning("No business data found, generating sample data")
                dates = pd.date_range(start='2023-01-01', end='2024-08-28', freq='W')
                
                data = []
                for i, date in enumerate(dates):
                    # Simulate seasonal patterns in rental business
                    base_revenue = 1000
                    seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * i / 52)  # Annual cycle
                    weather_noise = np.random.normal(0, 100)
                    
                    data.append({
                        'week_start': date,
                        'current_store': '3607',  # Wayzata
                        'weekly_revenue': base_revenue * seasonal_factor + weather_noise,
                        'item_count': 50 + int(10 * seasonal_factor),
                        'avg_revenue_per_item': 20 * seasonal_factor
                    })
                
                df = pd.DataFrame(data)
            
            df['week_start'] = pd.to_datetime(df['week_start'])
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get business time series: {e}")
            return pd.DataFrame()
    
    def get_external_factors_time_series(self) -> pd.DataFrame:
        """Get external factors as time series"""
        try:
            query = text("""
                SELECT 
                    date,
                    factor_type,
                    factor_name,
                    value
                FROM external_factors
                ORDER BY date, factor_type, factor_name
            """)
            
            df = pd.read_sql(query, db.engine)
            
            if df.empty:
                return pd.DataFrame()
            
            # Pivot to get factors as columns
            df_pivot = df.pivot_table(
                index='date', 
                columns=['factor_type', 'factor_name'], 
                values='value',
                aggfunc='mean'
            )
            
            # Flatten column names
            df_pivot.columns = [f"{col[0]}_{col[1]}" for col in df_pivot.columns]
            df_pivot = df_pivot.reset_index()
            df_pivot['date'] = pd.to_datetime(df_pivot['date'])
            
            return df_pivot
            
        except Exception as e:
            self.logger.error(f"Failed to get external factors: {e}")
            return pd.DataFrame()
    
    def align_time_series(self, business_df: pd.DataFrame, factors_df: pd.DataFrame) -> pd.DataFrame:
        """Align business and external factor time series"""
        if business_df.empty or factors_df.empty:
            return pd.DataFrame()
        
        try:
            # Convert business data to weekly aggregates
            business_df['week_start'] = business_df['week_start'].dt.to_period('W').dt.start_time
            
            # Aggregate business data by week (sum across stores)
            business_weekly = business_df.groupby('week_start').agg({
                'weekly_revenue': 'sum',
                'item_count': 'sum',
                'avg_revenue_per_item': 'mean'
            }).reset_index()
            
            # Convert external factors to weekly aggregates
            factors_df['week_start'] = factors_df['date'].dt.to_period('W').dt.start_time
            factors_weekly = factors_df.groupby('week_start').agg({
                col: 'mean' for col in factors_df.columns if col != 'date'
            }).reset_index()
            
            # Merge on week_start
            aligned_df = pd.merge(business_weekly, factors_weekly, on='week_start', how='inner')
            
            # Forward fill missing values
            aligned_df = aligned_df.fillna(method='ffill').fillna(method='bfill')
            
            self.logger.info(f"Aligned time series: {len(aligned_df)} weeks of data")
            return aligned_df
            
        except Exception as e:
            self.logger.error(f"Failed to align time series: {e}")
            return pd.DataFrame()
    
    def calculate_correlations(self, df: pd.DataFrame) -> Dict:
        """Calculate correlations between business metrics and external factors"""
        if df.empty or not SCIPY_AVAILABLE:
            return {}
        
        correlations = {}
        business_metrics = ['weekly_revenue', 'item_count', 'avg_revenue_per_item']
        
        # Get external factor columns
        factor_columns = [col for col in df.columns if col not in business_metrics + ['week_start']]
        
        try:
            for business_metric in business_metrics:
                if business_metric not in df.columns:
                    continue
                
                correlations[business_metric] = {}
                business_values = df[business_metric].dropna()
                
                for factor_col in factor_columns:
                    if factor_col not in df.columns:
                        continue
                    
                    # Align the data (remove NaN pairs)
                    factor_values = df[factor_col]
                    combined = pd.DataFrame({
                        'business': business_values,
                        'factor': factor_values
                    }).dropna()
                    
                    if len(combined) < 5:  # Need minimum data points
                        continue
                    
                    try:
                        # Calculate Pearson correlation
                        pearson_corr, pearson_p = pearsonr(combined['business'], combined['factor'])
                        
                        # Calculate Spearman correlation (rank-based, more robust)
                        spearman_corr, spearman_p = spearmanr(combined['business'], combined['factor'])
                        
                        correlations[business_metric][factor_col] = {
                            'pearson_correlation': float(pearson_corr),
                            'pearson_p_value': float(pearson_p),
                            'spearman_correlation': float(spearman_corr),
                            'spearman_p_value': float(spearman_p),
                            'data_points': len(combined),
                            'significance': 'significant' if pearson_p < 0.05 else 'not_significant'
                        }
                        
                    except Exception as e:
                        self.logger.warning(f"Correlation calculation failed for {business_metric} vs {factor_col}: {e}")
                        continue
            
            self.logger.info(f"Calculated correlations for {len(correlations)} business metrics")
            return correlations
            
        except Exception as e:
            self.logger.error(f"Failed to calculate correlations: {e}")
            return {}
    
    def calculate_lagged_correlations(self, df: pd.DataFrame, max_lag: int = 4) -> Dict:
        """Calculate lagged correlations to find leading/trailing indicators"""
        if df.empty or not SCIPY_AVAILABLE:
            return {}
        
        lagged_correlations = {}
        business_metrics = ['weekly_revenue', 'item_count']
        factor_columns = [col for col in df.columns if col.startswith(('weather_', 'economic_')) and col in df.columns]
        
        try:
            for business_metric in business_metrics:
                if business_metric not in df.columns:
                    continue
                
                lagged_correlations[business_metric] = {}
                business_values = df[business_metric].dropna()
                
                for factor_col in factor_columns:
                    if factor_col not in df.columns:
                        continue
                    
                    factor_values = df[factor_col].dropna()
                    
                    if len(factor_values) < max_lag + 5:
                        continue
                    
                    lag_results = {}
                    
                    # Test different lags
                    for lag in range(0, max_lag + 1):
                        try:
                            if lag == 0:
                                # No lag - current correlation
                                aligned = pd.DataFrame({
                                    'business': business_values,
                                    'factor': factor_values
                                }).dropna()
                            else:
                                # Lag the factor (factor leads business)
                                factor_lagged = factor_values.shift(lag)
                                aligned = pd.DataFrame({
                                    'business': business_values,
                                    'factor': factor_lagged
                                }).dropna()
                            
                            if len(aligned) < 5:
                                continue
                            
                            corr, p_val = pearsonr(aligned['business'], aligned['factor'])
                            
                            lag_results[f'lag_{lag}'] = {
                                'correlation': float(corr),
                                'p_value': float(p_val),
                                'data_points': len(aligned)
                            }
                            
                        except Exception:
                            continue
                    
                    if lag_results:
                        # Find best lag
                        best_lag = max(lag_results.keys(), 
                                     key=lambda x: abs(lag_results[x]['correlation']))
                        
                        lagged_correlations[business_metric][factor_col] = {
                            'best_lag': best_lag,
                            'best_correlation': lag_results[best_lag]['correlation'],
                            'all_lags': lag_results
                        }
            
            return lagged_correlations
            
        except Exception as e:
            self.logger.error(f"Failed to calculate lagged correlations: {e}")
            return {}
    
    def generate_correlation_insights(self, correlations: Dict, lagged_correlations: Dict) -> Dict:
        """Generate business insights from correlation analysis"""
        insights = {
            'strong_correlations': [],
            'leading_indicators': [],
            'recommendations': [],
            'summary_stats': {}
        }
        
        try:
            # Find strong correlations
            for business_metric, factors in correlations.items():
                for factor_name, stats in factors.items():
                    correlation = abs(stats['pearson_correlation'])
                    
                    if correlation > 0.5 and stats['significance'] == 'significant':
                        direction = 'positive' if stats['pearson_correlation'] > 0 else 'negative'
                        
                        insights['strong_correlations'].append({
                            'business_metric': business_metric,
                            'factor': factor_name,
                            'correlation': stats['pearson_correlation'],
                            'direction': direction,
                            'strength': 'strong' if correlation > 0.7 else 'moderate',
                            'p_value': stats['pearson_p_value']
                        })
            
            # Find leading indicators
            for business_metric, factors in lagged_correlations.items():
                for factor_name, lag_info in factors.items():
                    best_corr = abs(lag_info['best_correlation'])
                    
                    if best_corr > 0.4 and 'lag_' in lag_info['best_lag']:
                        lag_weeks = int(lag_info['best_lag'].split('_')[1])
                        
                        if lag_weeks > 0:  # Factor leads business
                            insights['leading_indicators'].append({
                                'business_metric': business_metric,
                                'factor': factor_name,
                                'lead_weeks': lag_weeks,
                                'correlation': lag_info['best_correlation']
                            })
            
            # Generate recommendations
            if insights['strong_correlations']:
                insights['recommendations'].append(
                    "Strong correlations found - consider these factors in demand forecasting"
                )
            
            if insights['leading_indicators']:
                insights['recommendations'].append(
                    "Leading indicators identified - use for early warning system"
                )
            
            # Summary statistics
            all_correlations = []
            for metric_data in correlations.values():
                for factor_data in metric_data.values():
                    all_correlations.append(abs(factor_data['pearson_correlation']))
            
            if all_correlations:
                insights['summary_stats'] = {
                    'total_factor_pairs': len(all_correlations),
                    'avg_correlation_strength': np.mean(all_correlations),
                    'max_correlation': max(all_correlations),
                    'significant_correlations': len(insights['strong_correlations'])
                }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate insights: {e}")
            return insights
    
    def run_full_correlation_analysis(self) -> Dict:
        """Run complete correlation analysis pipeline"""
        self.logger.info("Starting full correlation analysis...")
        
        try:
            # Get data
            business_df = self.get_business_time_series()
            factors_df = self.get_external_factors_time_series()
            
            # Align time series
            aligned_df = self.align_time_series(business_df, factors_df)
            
            if aligned_df.empty:
                return {
                    'status': 'failed',
                    'error': 'No aligned data available for analysis',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Calculate correlations
            correlations = self.calculate_correlations(aligned_df)
            lagged_correlations = self.calculate_lagged_correlations(aligned_df)
            
            # Generate insights
            insights = self.generate_correlation_insights(correlations, lagged_correlations)
            
            # Compile results
            results = {
                'status': 'success',
                'data_summary': {
                    'weeks_analyzed': len(aligned_df),
                    'factors_analyzed': len([col for col in aligned_df.columns if col.startswith(('weather_', 'economic_'))]),
                    'date_range': f"{aligned_df['week_start'].min()} to {aligned_df['week_start'].max()}"
                },
                'correlations': correlations,
                'lagged_correlations': lagged_correlations,
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info("Correlation analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Correlation analysis failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }