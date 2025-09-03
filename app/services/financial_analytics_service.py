"""
Advanced Financial Analytics Service for Minnesota Equipment Rental Company
Provides sophisticated financial analysis including:
- 3-week rolling averages for trend smoothing
- Year-over-year comparisons with seasonal adjustments
- Multi-store performance benchmarking
- Predictive financial modeling
- Asset-level ROI analysis and optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, func, and_, or_
from decimal import Decimal
import json
import logging

from app import db
from app.services.logger import get_logger
from app.models.financial_models import PayrollTrendsData, ScorecardTrendsData
from app.models.db_models import PLData
from app.models.pos_models import POSTransaction, POSTransactionItem, POSEquipment, POSCustomer
from app.config.stores import (
    STORES, STORE_MAPPING, STORE_MANAGERS,
    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,
    get_store_name, get_store_manager, get_store_business_type,
    get_store_opening_date, get_active_store_codes
)
from app.models.config_models import LaborCostConfiguration, get_default_labor_cost_config


logger = get_logger(__name__)

class FinancialAnalyticsService:
    """
    Comprehensive financial analytics service for Minnesota equipment rental company
    Focuses on multi-store operations across 4 locations: Wayzata, Brooklyn Park, Fridley, Elk River
    """
    
    # Use centralized store configuration
    STORE_CODES = {code: get_store_name(code) for code in get_active_store_codes()}
    
    # Business mix profiles from centralized configuration
    STORE_BUSINESS_MIX = {}
    for store_code in get_active_store_codes():
        business_type = get_store_business_type(store_code)
        if '100% Construction' in business_type:
            STORE_BUSINESS_MIX[store_code] = {'construction': 1.00, 'events': 0.00}
        elif '100% Events' in business_type:
            STORE_BUSINESS_MIX[store_code] = {'construction': 0.00, 'events': 1.00}
        elif '90% DIY/10% Events' in business_type:
            STORE_BUSINESS_MIX[store_code] = {'construction': 0.90, 'events': 0.10}
        else:
            STORE_BUSINESS_MIX[store_code] = {'construction': 0.50, 'events': 0.50}
    
    # COMMENTED OUT: Old hardcoded revenue percentages - replaced with calculated actual performance
    # STORE_REVENUE_TARGETS = {
    #     '3607': 0.153,  # 15.3% of total revenue
    #     '6800': 0.275,  # 27.5% of total revenue - largest operation
    #     '728': 0.121,   # 12.1% of total revenue - smallest operation
    #     '8101': 0.248   # 24.8% of total revenue - major events operation
    # }
    
    # Revenue targets should be configurable business goals (moved to config system)
    # Actual performance is now calculated from real data using calculate_actual_store_performance()
    
    def __init__(self):
        self.logger = logger
        
    def get_analysis_config(self) -> Dict:
        """
        Get configurable analysis parameters. 
        TODO: Move to database configuration system when implemented.
        For now, provides centralized defaults with future configurability.
        
        Returns:
            Dict with analysis configuration parameters
        """
        # TODO: Replace with database configuration lookup
        # For now, centralized configurable defaults
        return {
            'rolling_window_weeks': 3,          # Default 3-week rolling averages
            'default_analysis_weeks': 26,       # Default 26-week lookback period  
            'trend_analysis_window': 3,         # Window for trend calculations
            'smoothing_center': True,           # Center the rolling window
            'min_data_points': 10,              # Minimum data points for valid analysis
            'confidence_threshold': 0.95,       # Statistical confidence level
            'volatility_threshold': 15.0        # Percentage threshold for high volatility
        }
    
    def get_config_value(self, key: str, default=None):
        """
        Get a specific configuration value with fallback default.
        
        Args:
            key: Configuration key to retrieve
            default: Fallback value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.get_analysis_config()
        return config.get(key, default)
    
    def get_labor_cost_config(self, user_id: str = 'default_user'):
        """
        Get labor cost configuration from database or defaults.
        
        Args:
            user_id: User ID to get configuration for
            
        Returns:
            LaborCostConfiguration instance or default values
        """
        try:
            config = db.session.query(LaborCostConfiguration).filter(
                LaborCostConfiguration.user_id == user_id,
                LaborCostConfiguration.is_active == True
            ).first()
            
            if config:
                return config
            
            # Create default configuration if none exists
            default_config = LaborCostConfiguration(user_id=user_id)
            db.session.add(default_config)
            db.session.commit()
            return default_config
            
        except Exception as e:
            logger.error(f"Error getting labor cost config: {e}")
            # Return a temporary config with defaults if database fails
            return type('DefaultConfig', (), get_default_labor_cost_config()['global_thresholds'])()
    
    def get_store_labor_threshold(self, store_code: str, threshold_type: str = 'high_threshold', user_id: str = 'default_user'):
        """
        Get store-specific labor cost threshold with fallback to global defaults.
        
        Args:
            store_code: Store code to get threshold for
            threshold_type: 'high_threshold', 'warning_level', or 'target'  
            user_id: User ID for configuration
            
        Returns:
            Threshold value for the store
        """
        try:
            config = self.get_labor_cost_config(user_id)
            if hasattr(config, 'get_store_threshold'):
                return config.get_store_threshold(store_code, threshold_type)
            else:
                # Fallback to global defaults if config object doesn't have method
                defaults = get_default_labor_cost_config()['global_thresholds']
                threshold_map = {
                    'high_threshold': 'high_cost_threshold',
                    'warning_level': 'warning_level', 
                    'target': 'target_ratio'
                }
                return defaults.get(threshold_map.get(threshold_type, 'high_cost_threshold'), 35.0)
        except Exception as e:
            logger.error(f"Error getting store labor threshold: {e}")
            return 35.0  # Safe fallback
    
    # ==========================================
    # ACTUAL STORE PERFORMANCE CALCULATIONS
    # ==========================================
    
    def calculate_actual_store_performance(self, timeframe: str = 'monthly', custom_start: date = None, custom_end: date = None) -> Dict:
        """
        Calculate actual store contribution both in dollars and percentage of total company revenue.
        
        Args:
            timeframe: 'weekly', 'monthly', 'quarterly', 'yearly', 'ytd', 'custom'
            custom_start: Start date for custom timeframe
            custom_end: End date for custom timeframe
            
        Returns:
            Dict with actual performance data per store (dollars + percentages)
        """
        try:
            # Calculate date range based on timeframe
            end_date = datetime.now().date()
            
            if timeframe == 'weekly':
                start_date = end_date - timedelta(weeks=1)
            elif timeframe == 'monthly':
                start_date = end_date - timedelta(days=30)
            elif timeframe == 'quarterly':
                start_date = end_date - timedelta(days=90)
            elif timeframe == 'yearly':
                start_date = end_date - timedelta(days=365)
            elif timeframe == 'ytd':
                start_date = date(end_date.year, 1, 1)
            elif timeframe == 'custom' and custom_start and custom_end:
                start_date = custom_start
                end_date = custom_end
            else:
                start_date = end_date - timedelta(days=30)  # Default to monthly
            
            # Query actual store performance from scorecard data
            query = text("""
                SELECT 
                    'Wayzata' as store_name, '3607' as store_code,
                    COALESCE(SUM(revenue_3607), 0) as actual_revenue_dollars
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                
                UNION ALL
                
                SELECT 
                    'Brooklyn Park' as store_name, '6800' as store_code,
                    COALESCE(SUM(revenue_6800), 0) as actual_revenue_dollars
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                
                UNION ALL
                
                SELECT 
                    'Elk River' as store_name, '728' as store_code,
                    COALESCE(SUM(revenue_728), 0) as actual_revenue_dollars
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                
                UNION ALL
                
                SELECT 
                    'Fridley' as store_name, '8101' as store_code,
                    COALESCE(SUM(revenue_8101), 0) as actual_revenue_dollars
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
            """)
            
            results = db.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            if not results:
                return {"error": "No store performance data available for the specified period"}
            
            # Calculate total company revenue for percentage calculations
            total_company_revenue = sum(float(row.actual_revenue_dollars) for row in results)
            
            # Build store performance data
            store_performance = {}
            for row in results:
                actual_dollars = float(row.actual_revenue_dollars)
                actual_percentage = (actual_dollars / total_company_revenue * 100) if total_company_revenue > 0 else 0
                
                store_performance[row.store_name] = {
                    'store_code': row.store_code,
                    'actual_revenue_dollars': round(actual_dollars, 2),
                    'actual_revenue_percentage': round(actual_percentage, 2),
                    'timeframe': timeframe,
                    'period_start': start_date.isoformat(),
                    'period_end': end_date.isoformat()
                }
            
            return {
                "success": True,
                "total_company_revenue": round(total_company_revenue, 2),
                "store_performance": store_performance,
                "timeframe_info": {
                    "timeframe": timeframe,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days_analyzed": (end_date - start_date).days
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating actual store performance: {e}")
            return {"error": str(e)}
        
    # ==========================================
    # 3-WEEK ROLLING AVERAGES ANALYSIS
    # ==========================================
    
    def calculate_rolling_averages(self, metric_type: str = 'revenue', weeks_back: int = None) -> Dict:
        """
        Calculate rolling averages for financial metrics using configurable parameters.
        
        Args:
            metric_type: 'revenue', 'contracts', 'utilization', 'profitability'
            weeks_back: Number of weeks to analyze (uses config default if None)
        """
        try:
            # Use configurable analysis period if not specified
            if weeks_back is None:
                weeks_back = self.get_config_value('default_analysis_weeks', 26)
                
            end_date = datetime.now().date()
            start_date = end_date - timedelta(weeks=weeks_back)
            
            if metric_type == 'revenue':
                return self._calculate_revenue_rolling_averages(start_date, end_date)
            elif metric_type == 'contracts':
                return self._calculate_contracts_rolling_averages(start_date, end_date)
            elif metric_type == 'utilization':
                return self._calculate_utilization_rolling_averages(start_date, end_date)
            elif metric_type == 'profitability':
                return self._calculate_profitability_rolling_averages(start_date, end_date)
            else:
                return self._calculate_comprehensive_rolling_averages(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error calculating rolling averages for {metric_type}: {e}")
            return {"error": str(e)}
    
    def _calculate_revenue_rolling_averages(self, start_date: date, end_date: date) -> Dict:
        """Calculate 3-week rolling averages for revenue metrics"""
        try:
            # Get weekly revenue data from scorecard trends  
            query = text("""
                SELECT 
                    week_ending,
                    total_weekly_revenue,
                    revenue_3607,
                    revenue_6800, 
                    revenue_728,
                    revenue_8101
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                ORDER BY week_ending
            """)
            
            result = db.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            if not result:
                return {"error": "No revenue data available for the specified period"}
            
            df = pd.DataFrame([{
                'week_ending': row.week_ending,
                'total_revenue': float(row.total_weekly_revenue or 0),
                'wayzata': float(row.revenue_3607 or 0),
                'brooklyn_park': float(row.revenue_6800 or 0),
                'elk_river': float(row.revenue_728 or 0),
                'fridley': float(row.revenue_8101 or 0)
            } for row in result])
            
            # Get configurable rolling window parameters
            rolling_window = self.get_config_value('rolling_window_weeks', 3)
            center_window = self.get_config_value('smoothing_center', True)
            
            # Calculate configurable rolling averages (was hardcoded window=3)
            df['total_avg'] = df['total_revenue'].rolling(window=rolling_window, center=center_window).mean()
            df['wayzata_avg'] = df['wayzata'].rolling(window=rolling_window, center=center_window).mean()
            df['brooklyn_park_avg'] = df['brooklyn_park'].rolling(window=rolling_window, center=center_window).mean()
            df['fridley_avg'] = df['fridley'].rolling(window=rolling_window, center=center_window).mean()
            df['elk_river_avg'] = df['elk_river'].rolling(window=rolling_window, center=center_window).mean()
            
            # Calculate forward and backward rolling averages for trend analysis
            trend_window = self.get_config_value('trend_analysis_window', 3)
            df['total_forward_avg'] = df['total_revenue'].rolling(window=trend_window).mean()
            df['total_backward_avg'] = df['total_revenue'].rolling(window=trend_window).mean().shift(-(trend_window-1))
            
            # Trend analysis using configurable windows
            df['revenue_trend'] = ((df['total_forward_avg'] - df['total_backward_avg']) / 
                                 df['total_backward_avg'] * 100).fillna(0)
            
            # Store performance analysis using configurable windows
            store_metrics = {}
            window_size = rolling_window  # Use the same configurable window
            
            for store_key, store_name in [('wayzata', 'Wayzata'), ('brooklyn_park', 'Brooklyn Park'), 
                                        ('fridley', 'Fridley'), ('elk_river', 'Elk River')]:
                store_metrics[store_name] = {
                    'current_avg': float(df[f'{store_key}_avg'].iloc[-window_size:].mean()),
                    'previous_avg': float(df[f'{store_key}_avg'].iloc[-(window_size*2):-window_size].mean()),
                    'growth_rate': 0,
                    'volatility': float(df[store_key].std()),
                    'contribution_pct': float(df[store_key].sum() / df['total_revenue'].sum() * 100)
                }
                
                # Calculate growth rate using configurable periods
                if store_metrics[store_name]['previous_avg'] > 0:
                    store_metrics[store_name]['growth_rate'] = (
                        (store_metrics[store_name]['current_avg'] - 
                         store_metrics[store_name]['previous_avg']) /
                        store_metrics[store_name]['previous_avg'] * 100
                    )
            
            # Summary metrics using configurable windows
            summary = {
                'total_periods': len(df),
                'current_avg': float(df['total_avg'].iloc[-window_size:].mean()),
                'previous_avg': float(df['total_avg'].iloc[-(window_size*2):-window_size].mean()),
                'smoothed_trend': float(df['revenue_trend'].iloc[-window_size:].mean()),
                'trend_strength': 'strong' if abs(df['revenue_trend'].iloc[-window_size:].mean()) > 5 else 'moderate',
                'peak_week': df.loc[df['total_revenue'].idxmax(), 'week_ending'].strftime('%Y-%m-%d'),
                'peak_revenue': float(df['total_revenue'].max()),
                'rolling_window_weeks': rolling_window,
                'analysis_weeks': (end_date - start_date).days // 7
            }
            
            return {
                "success": True,
                "metric_type": "revenue_rolling_averages",
                "analysis_period": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d'),
                    "weeks_analyzed": len(df)
                },
                "summary": summary,
                "store_performance": store_metrics,
                "weekly_data": df.fillna(0).to_dict('records'),
                "insights": self._generate_revenue_insights(df, store_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error calculating revenue rolling averages: {e}")
            return {"error": str(e)}
    
    def _calculate_contracts_rolling_averages(self, start_date: date, end_date: date) -> Dict:
        """Calculate 3-week rolling averages for new contracts"""
        try:
            query = text("""
                SELECT 
                    week_ending,
                    new_contracts_3607,
                    new_contracts_6800,
                    new_contracts_728,
                    new_contracts_8101,
                    (new_contracts_3607 + new_contracts_6800 + 
                     new_contracts_728 + new_contracts_8101) as total_contracts
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                ORDER BY week_ending
            """)
            
            result = db.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            if not result:
                return {"error": "No contract data available"}
            
            df = pd.DataFrame([{
                'week_ending': row.week_ending,
                'total_contracts': int(row.total_contracts or 0),
                'wayzata': int(row.new_contracts_3607 or 0),
                'brooklyn_park': int(row.new_contracts_6800 or 0),
                'fridley': int(row.new_contracts_728 or 0),
                'elk_river': int(row.new_contracts_8101 or 0)
            } for row in result])
            
            # Configurable rolling averages
            # OLD - HARDCODED (WRONG): df[f'{col}_3wk_avg'] = df[col].rolling(window=3, center=True).mean()
            # NEW - CONFIGURABLE (CORRECT):
            rolling_window = self.get_config_value('rolling_window_weeks', 3)
            for col in ['total_contracts', 'wayzata', 'brooklyn_park', 'fridley', 'elk_river']:
                df[f'{col}_3wk_avg'] = df[col].rolling(window=rolling_window, center=True).mean()
                df[f'{col}_trend'] = df[col].rolling(window=rolling_window).mean().pct_change() * 100
            
            # Performance analysis
            store_analysis = {}
            for store in ['wayzata', 'brooklyn_park', 'fridley', 'elk_river']:
                store_name = store.replace('_', ' ').title()
                recent_avg = float(df[f'{store}_3wk_avg'].iloc[-3:].mean())
                previous_avg = float(df[f'{store}_3wk_avg'].iloc[-6:-3].mean())
                
                store_analysis[store_name] = {
                    'current_3wk_avg': recent_avg,
                    'previous_3wk_avg': previous_avg,
                    'growth_rate': ((recent_avg - previous_avg) / max(previous_avg, 1)) * 100,
                    'market_share': float(df[store].sum() / df['total_contracts'].sum() * 100),
                    'consistency_score': float(100 - (df[store].std() / max(df[store].mean(), 1) * 100))
                }
            
            return {
                "success": True,
                "metric_type": "contracts_rolling_averages",
                "analysis_period": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d')
                },
                "summary": {
                    'total_contracts_analyzed': int(df['total_contracts'].sum()),
                    'avg_weekly_contracts': float(df['total_contracts'].mean()),
                    'peak_week_contracts': int(df['total_contracts'].max()),
                    'contract_velocity_trend': float(df['total_contracts_trend'].iloc[-3:].mean())
                },
                "store_analysis": store_analysis,
                "weekly_data": df.fillna(0).to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error calculating contracts rolling averages: {e}")
            return {"error": str(e)}
    
    # ==========================================
    # YEAR-OVER-YEAR COMPARISON ANALYSIS
    # ==========================================
    
    def calculate_year_over_year_analysis(self, metric_type: str = 'comprehensive') -> Dict:
        """
        Calculate comprehensive year-over-year comparisons with seasonal adjustments
        
        Args:
            metric_type: 'revenue', 'profitability', 'efficiency', 'comprehensive'
        """
        try:
            current_year = datetime.now().year
            previous_year = current_year - 1
            
            if metric_type == 'revenue':
                return self._calculate_revenue_yoy(current_year, previous_year)
            elif metric_type == 'profitability':
                return self._calculate_profitability_yoy(current_year, previous_year)
            elif metric_type == 'efficiency':
                return self._calculate_efficiency_yoy(current_year, previous_year)
            else:
                # Default to revenue calculation if no specific type provided
                return self._calculate_revenue_yoy(current_year, previous_year)
                
        except Exception as e:
            logger.error(f"Error calculating YoY analysis for {metric_type}: {e}")
            return {"error": str(e)}
    
    def _calculate_revenue_yoy(self, current_year: int, previous_year: int) -> Dict:
        """Calculate year-over-year revenue analysis with seasonal adjustments"""
        try:
            # Get current year data
            current_query = text("""
                SELECT 
                    EXTRACT(MONTH FROM week_ending) as month_num,
                    EXTRACT(WEEK FROM week_ending) as week_num,
                    week_ending,
                    total_weekly_revenue,
                    revenue_3607 + revenue_6800 + revenue_728_temp + revenue_728 as calculated_total
                FROM scorecard_trends_data 
                WHERE EXTRACT(YEAR FROM week_ending) = :year
                ORDER BY week_ending
            """)
            
            current_data = db.session.execute(current_query, {'year': current_year}).fetchall()
            previous_data = db.session.execute(current_query, {'year': previous_year}).fetchall()
            
            if not current_data or not previous_data:
                return {"error": "Insufficient data for YoY comparison"}
            
            # Convert to DataFrames
            current_df = pd.DataFrame([{
                'week_ending': row.week_ending,
                'month_num': int(row.month_num),
                'week_num': int(row.week_num),
                'revenue': float(row.total_weekly_revenue or row.calculated_total or 0)
            } for row in current_data])
            
            previous_df = pd.DataFrame([{
                'week_ending': row.week_ending,
                'month_num': int(row.month_num),
                'week_num': int(row.week_num),
                'revenue': float(row.total_weekly_revenue or row.calculated_total or 0)
            } for row in previous_data])
            
            # Monthly aggregations for seasonal analysis
            current_monthly = current_df.groupby('month_num')['revenue'].agg(['sum', 'mean', 'count']).reset_index()
            previous_monthly = previous_df.groupby('month_num')['revenue'].agg(['sum', 'mean', 'count']).reset_index()
            
            # Merge for comparison
            monthly_comparison = current_monthly.merge(
                previous_monthly, on='month_num', suffixes=['_current', '_previous']
            )
            
            # Calculate YoY growth rates
            monthly_comparison['yoy_growth_rate'] = (
                (monthly_comparison['sum_current'] - monthly_comparison['sum_previous']) /
                monthly_comparison['sum_previous'] * 100
            ).fillna(0)
            
            # Seasonal adjustment factors
            monthly_comparison['seasonal_factor'] = (
                monthly_comparison['sum_previous'] / monthly_comparison['sum_previous'].mean()
            )
            
            # Store-specific YoY analysis
            store_yoy = self._calculate_store_yoy_revenue(current_year, previous_year)
            
            # Growth trend analysis
            ytd_current = current_df['revenue'].sum()
            ytd_previous = previous_df['revenue'].sum()
            overall_growth = ((ytd_current - ytd_previous) / max(ytd_previous, 1)) * 100
            
            # Seasonal insights
            peak_month_current = monthly_comparison.loc[monthly_comparison['sum_current'].idxmax(), 'month_num']
            peak_month_previous = monthly_comparison.loc[monthly_comparison['sum_previous'].idxmax(), 'month_num']
            
            return {
                "success": True,
                "metric_type": "revenue_year_over_year",
                "comparison_period": {
                    "current_year": current_year,
                    "previous_year": previous_year,
                    "current_ytd": float(ytd_current),
                    "previous_ytd": float(ytd_previous),
                    "overall_growth_rate": float(overall_growth)
                },
                "monthly_analysis": monthly_comparison.to_dict('records'),
                "store_performance": store_yoy,
                "seasonal_insights": {
                    "peak_month_current": int(peak_month_current),
                    "peak_month_previous": int(peak_month_previous),
                    "peak_month_changed": peak_month_current != peak_month_previous,
                    "seasonal_consistency": float(monthly_comparison['seasonal_factor'].std()),
                    "strongest_growth_month": int(monthly_comparison.loc[
                        monthly_comparison['yoy_growth_rate'].idxmax(), 'month_num'
                    ])
                },
                "growth_insights": self._generate_yoy_insights(monthly_comparison, overall_growth)
            }
            
        except Exception as e:
            logger.error(f"Error calculating revenue YoY: {e}")
            return {"error": str(e)}
    
    def _calculate_store_yoy_revenue(self, current_year: int, previous_year: int) -> Dict:
        """Calculate store-specific year-over-year revenue analysis"""
        try:
            query = text("""
                SELECT 
                    EXTRACT(YEAR FROM week_ending) as year,
                    SUM(revenue_3607) as wayzata_total,
                    SUM(revenue_6800) as brooklyn_park_total,
                    SUM(revenue_728_temp) as fridley_total,
                    SUM(revenue_728) as elk_river_total
                FROM scorecard_trends_data 
                WHERE EXTRACT(YEAR FROM week_ending) IN (:current_year, :previous_year)
                GROUP BY EXTRACT(YEAR FROM week_ending)
            """)
            
            results = db.session.execute(query, {
                'current_year': current_year,
                'previous_year': previous_year
            }).fetchall()
            
            data = {row.year: row for row in results}
            
            store_analysis = {}
            for store_col, store_name in [('wayzata_total', 'Wayzata'), 
                                        ('brooklyn_park_total', 'Brooklyn Park'),
                                        ('fridley_total', 'Fridley'), 
                                        ('elk_river_total', 'Elk River')]:
                
                current_revenue = float(getattr(data.get(current_year), store_col, 0) or 0)
                previous_revenue = float(getattr(data.get(previous_year), store_col, 0) or 0)
                
                growth_rate = 0
                if previous_revenue > 0:
                    growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
                
                store_analysis[store_name] = {
                    'current_year_revenue': current_revenue,
                    'previous_year_revenue': previous_revenue,
                    'growth_rate': growth_rate,
                    'revenue_change': current_revenue - previous_revenue,
                    'performance_tier': 'high' if growth_rate > 10 else 'moderate' if growth_rate > 0 else 'declining'
                }
            
            return store_analysis
            
        except Exception as e:
            logger.error(f"Error calculating store YoY revenue: {e}")
            return {}
    
    # ==========================================
    # FINANCIAL FORECASTING MODELS
    # ==========================================
    
    def generate_financial_forecasts(self, horizon_weeks: int = 12, 
                                   confidence_level: float = 0.95) -> Dict:
        """
        Generate predictive financial forecasts with confidence intervals
        
        Args:
            horizon_weeks: Number of weeks to forecast
            confidence_level: Confidence level for prediction intervals (0.90, 0.95, 0.99)
        """
        try:
            # Get historical data for forecasting
            lookback_weeks = min(52, horizon_weeks * 4)  # Use 4x horizon or 1 year max
            end_date = datetime.now().date()
            start_date = end_date - timedelta(weeks=lookback_weeks)
            
            historical_data = self._get_forecasting_data(start_date, end_date)
            
            if not historical_data:
                return {"error": "Insufficient historical data for forecasting"}
            
            # Generate forecasts for different metrics
            revenue_forecast = self._forecast_revenue(historical_data, horizon_weeks, confidence_level)
            profitability_forecast = self._forecast_profitability(historical_data, horizon_weeks, confidence_level)
            cash_flow_forecast = self._forecast_cash_flow(historical_data, horizon_weeks, confidence_level)
            
            # Combined executive forecast summary
            forecast_summary = self._generate_forecast_summary(
                revenue_forecast, profitability_forecast, cash_flow_forecast
            )
            
            return {
                "success": True,
                "forecast_parameters": {
                    "horizon_weeks": horizon_weeks,
                    "confidence_level": confidence_level,
                    "historical_periods": len(historical_data),
                    "forecast_generated": datetime.now().isoformat()
                },
                "revenue_forecast": revenue_forecast,
                "profitability_forecast": profitability_forecast,
                "cash_flow_forecast": cash_flow_forecast,
                "executive_summary": forecast_summary,
                "recommendations": self._generate_forecast_recommendations(forecast_summary)
            }
            
        except Exception as e:
            logger.error(f"Error generating financial forecasts: {e}")
            return {"error": str(e)}
    
    def _get_forecasting_data(self, start_date: date, end_date: date) -> List[Dict]:
        """Get comprehensive historical data for forecasting"""
        try:
            query = text("""
                SELECT 
                    s.week_ending,
                    s.total_weekly_revenue,
                    s.revenue_3607 + s.revenue_6800 + s.revenue_728_temp + s.revenue_728 as calculated_revenue,
                    p.rental_revenue,
                    p.all_revenue,
                    p.payroll_amount,
                    (p.all_revenue - p.payroll_amount) as gross_profit
                FROM scorecard_trends_data s
                LEFT JOIN payroll_trends_data p ON s.week_ending = p.week_ending
                WHERE s.week_ending BETWEEN :start_date AND :end_date
                ORDER BY s.week_ending
            """)
            
            results = db.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            return [{
                'week_ending': row.week_ending,
                'revenue': float(row.total_weekly_revenue or row.calculated_revenue or 0),
                'rental_revenue': float(row.rental_revenue or 0),
                'all_revenue': float(row.all_revenue or 0),
                'payroll_cost': float(row.payroll_amount or 0),
                'gross_profit': float(row.gross_profit or 0)
            } for row in results]
            
        except Exception as e:
            logger.error(f"Error getting forecasting data: {e}")
            return []
    
    def _forecast_revenue(self, historical_data: List[Dict], horizon_weeks: int, 
                         confidence_level: float) -> Dict:
        """Generate revenue forecasts with trend analysis"""
        try:
            df = pd.DataFrame(historical_data)
            revenue_series = df['revenue'].values
            
            # Simple trend-based forecasting with seasonality
            if len(revenue_series) < 4:
                return {"error": "Insufficient data for revenue forecasting"}
            
            # Calculate trend and seasonal components
            trend = np.polyfit(range(len(revenue_series)), revenue_series, 1)
            seasonal_period = min(13, len(revenue_series) // 4)  # Quarterly seasonality
            
            forecasts = []
            for week in range(1, horizon_weeks + 1):
                # Trend component
                trend_value = trend[0] * (len(revenue_series) + week) + trend[1]
                
                # Seasonal component (simple moving average)
                if len(revenue_series) >= seasonal_period:
                    seasonal_index = (week - 1) % seasonal_period
                    seasonal_factor = revenue_series[-seasonal_period + seasonal_index] / np.mean(revenue_series[-seasonal_period:])
                    seasonal_adjustment = trend_value * (seasonal_factor - 1) * 0.3  # 30% seasonal impact
                else:
                    seasonal_adjustment = 0
                
                forecast_value = max(0, trend_value + seasonal_adjustment)
                
                # Confidence intervals (simplified)
                std_error = np.std(revenue_series) * (1 + week * 0.1)  # Increasing uncertainty
                z_score = 1.96 if confidence_level == 0.95 else 2.576 if confidence_level == 0.99 else 1.645
                
                confidence_interval = z_score * std_error
                
                forecast_date = df['week_ending'].iloc[-1] + timedelta(weeks=week)
                
                forecasts.append({
                    'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                    'weeks_ahead': week,
                    'forecast_value': round(forecast_value, 2),
                    'confidence_low': round(max(0, forecast_value - confidence_interval), 2),
                    'confidence_high': round(forecast_value + confidence_interval, 2),
                    'trend_component': round(trend_value, 2),
                    'seasonal_adjustment': round(seasonal_adjustment, 2)
                })
            
            # Forecast summary
            total_forecasted = sum(f['forecast_value'] for f in forecasts)
            total_historical = sum(revenue_series[-horizon_weeks:]) if len(revenue_series) >= horizon_weeks else sum(revenue_series)
            growth_rate = ((total_forecasted - total_historical) / max(total_historical, 1)) * 100
            
            return {
                "forecast_type": "revenue",
                "forecasts": forecasts,
                "summary": {
                    "total_forecasted": round(total_forecasted, 2),
                    "avg_weekly_forecast": round(total_forecasted / horizon_weeks, 2),
                    "projected_growth_rate": round(growth_rate, 2),
                    "forecast_confidence": confidence_level,
                    "trend_direction": "increasing" if trend[0] > 0 else "decreasing"
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting revenue: {e}")
            return {"error": str(e)}
    
    # ==========================================
    # MULTI-STORE PERFORMANCE ANALYSIS
    # ==========================================
    
    def analyze_multi_store_performance(self, analysis_period_weeks: int = 26) -> Dict:
        """
        Comprehensive multi-store performance analysis and benchmarking
        
        Args:
            analysis_period_weeks: Number of weeks to analyze
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(weeks=analysis_period_weeks)
            
            # Store revenue and operational metrics
            store_metrics = self._calculate_store_metrics(start_date, end_date)
            
            # Benchmarking analysis
            benchmarks = self._calculate_store_benchmarks(store_metrics)
            
            # Efficiency analysis
            efficiency_analysis = self._analyze_store_efficiency(start_date, end_date)
            
            # Resource allocation optimization
            resource_optimization = self._optimize_resource_allocation(store_metrics)
            
            return {
                "success": True,
                "analysis_period": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d'),
                    "weeks_analyzed": analysis_period_weeks
                },
                "store_metrics": store_metrics,
                "performance_benchmarks": benchmarks,
                "efficiency_analysis": efficiency_analysis,
                "resource_optimization": resource_optimization,
                "executive_insights": self._generate_multi_store_insights(
                    store_metrics, benchmarks, efficiency_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing multi-store performance: {e}")
            return {"error": str(e)}
    
    def _calculate_store_metrics(self, start_date: date, end_date: date) -> Dict:
        """Calculate comprehensive metrics for each store"""
        try:
            # Revenue metrics by store
            revenue_query = text("""
                SELECT 
                    '3607' as store_code,
                    'Wayzata' as store_name,
                    SUM(revenue_3607) as total_revenue,
                    AVG(revenue_3607) as avg_weekly_revenue,
                    COUNT(*) as weeks_data,
                    SUM(new_contracts_3607) as total_contracts
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                UNION ALL
                SELECT 
                    '6800' as store_code,
                    'Brooklyn Park' as store_name,
                    SUM(revenue_6800) as total_revenue,
                    AVG(revenue_6800) as avg_weekly_revenue,
                    COUNT(*) as weeks_data,
                    SUM(new_contracts_6800) as total_contracts
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                UNION ALL
                SELECT 
                    '728' as store_code,
                    'Fridley' as store_name,
                    SUM(revenue_728_temp) as total_revenue,
                    AVG(revenue_728_temp) as avg_weekly_revenue,
                    COUNT(*) as weeks_data,
                    SUM(new_contracts_728) as total_contracts
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                UNION ALL
                SELECT 
                    '8101' as store_code,
                    'Elk River' as store_name,
                    SUM(revenue_728) as total_revenue,
                    AVG(revenue_728) as avg_weekly_revenue,
                    COUNT(*) as weeks_data,
                    SUM(new_contracts_8101) as total_contracts
                FROM scorecard_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
            """)
            
            revenue_results = db.session.execute(revenue_query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            # Payroll metrics by store
            payroll_query = text("""
                SELECT 
                    location_code,
                    SUM(rental_revenue) as rental_revenue,
                    SUM(all_revenue) as all_revenue,
                    SUM(payroll_amount) as payroll_cost,
                    SUM(wage_hours) as total_hours,
                    AVG(payroll_amount / NULLIF(wage_hours, 0)) as avg_hourly_rate
                FROM payroll_trends_data 
                WHERE week_ending BETWEEN :start_date AND :end_date
                GROUP BY location_code
            """)
            
            payroll_results = db.session.execute(payroll_query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            payroll_data = {row.location_code: row for row in payroll_results}
            
            # Combine metrics
            store_metrics = {}
            for row in revenue_results:
                store_code = row.store_code
                store_name = row.store_name
                payroll_info = payroll_data.get(store_code)
                
                total_revenue = float(row.total_revenue or 0)
                total_contracts = int(row.total_contracts or 0)
                payroll_cost = float(payroll_info.payroll_cost or 0) if payroll_info else 0
                total_hours = float(payroll_info.total_hours or 0) if payroll_info else 0
                
                store_metrics[store_name] = {
                    'store_code': store_code,
                    'financial_metrics': {
                        'total_revenue': total_revenue,
                        'avg_weekly_revenue': float(row.avg_weekly_revenue or 0),
                        'revenue_per_contract': total_revenue / max(total_contracts, 1),
                        'payroll_cost': payroll_cost,
                        'gross_profit': total_revenue - payroll_cost,
                        'profit_margin': ((total_revenue - payroll_cost) / max(total_revenue, 1)) * 100
                    },
                    'operational_metrics': {
                        'total_contracts': total_contracts,
                        'avg_weekly_contracts': total_contracts / max(row.weeks_data, 1),
                        'contracts_per_hour': total_contracts / max(total_hours, 1),
                        'total_labor_hours': total_hours,
                        'revenue_per_hour': total_revenue / max(total_hours, 1)
                    },
                    'efficiency_scores': {
                        'revenue_efficiency': (total_revenue / max(total_hours, 1)) / 100,  # Revenue per hour / 100
                        'contract_efficiency': (total_contracts / max(total_hours, 1)) * 10,  # Contracts per hour * 10
                        'cost_efficiency': 100 - ((payroll_cost / max(total_revenue, 1)) * 100)  # 100 - cost ratio
                    }
                }
            
            return store_metrics
            
        except Exception as e:
            logger.error(f"Error calculating store metrics: {e}")
            return {}
    
    def _calculate_store_benchmarks(self, store_metrics: Dict) -> Dict:
        """Calculate benchmarking metrics across all stores"""
        try:
            if not store_metrics:
                return {}
            
            # Extract all financial metrics
            revenues = [metrics['financial_metrics']['total_revenue'] for metrics in store_metrics.values()]
            profit_margins = [metrics['financial_metrics']['profit_margin'] for metrics in store_metrics.values()]
            revenue_per_hours = [metrics['operational_metrics']['revenue_per_hour'] for metrics in store_metrics.values()]
            
            # Calculate benchmarks
            benchmarks = {
                'revenue_benchmarks': {
                    'top_performer': max(revenues),
                    'average_performance': np.mean(revenues),
                    'bottom_performer': min(revenues),
                    'performance_gap': max(revenues) - min(revenues),
                    'coefficient_of_variation': (np.std(revenues) / max(np.mean(revenues), 1)) * 100
                },
                'profitability_benchmarks': {
                    'highest_margin': max(profit_margins),
                    'average_margin': np.mean(profit_margins),
                    'lowest_margin': min(profit_margins),
                    'margin_consistency': 100 - ((np.std(profit_margins) / max(np.mean(profit_margins), 1)) * 100)
                },
                'efficiency_benchmarks': {
                    'most_efficient_rph': max(revenue_per_hours),
                    'average_rph': np.mean(revenue_per_hours),
                    'least_efficient_rph': min(revenue_per_hours),
                    'efficiency_spread': max(revenue_per_hours) - min(revenue_per_hours)
                }
            }
            
            # Store rankings
            store_rankings = {}
            for store_name, metrics in store_metrics.items():
                revenue_rank = len([r for r in revenues if r > metrics['financial_metrics']['total_revenue']]) + 1
                margin_rank = len([m for m in profit_margins if m > metrics['financial_metrics']['profit_margin']]) + 1
                efficiency_rank = len([e for e in revenue_per_hours if e > metrics['operational_metrics']['revenue_per_hour']]) + 1
                
                overall_score = (5 - revenue_rank) + (5 - margin_rank) + (5 - efficiency_rank)
                
                store_rankings[store_name] = {
                    'revenue_rank': revenue_rank,
                    'margin_rank': margin_rank,
                    'efficiency_rank': efficiency_rank,
                    'overall_score': overall_score,
                    'overall_rank': len([s for s in store_rankings.values() if s.get('overall_score', 0) > overall_score]) + 1
                }
            
            # Update rankings with final overall ranks
            sorted_stores = sorted(store_rankings.items(), key=lambda x: x[1]['overall_score'], reverse=True)
            for i, (store_name, rankings) in enumerate(sorted_stores):
                store_rankings[store_name]['overall_rank'] = i + 1
            
            benchmarks['store_rankings'] = store_rankings
            
            return benchmarks
            
        except Exception as e:
            logger.error(f"Error calculating benchmarks: {e}")
            return {}
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _generate_revenue_insights(self, df: pd.DataFrame, store_metrics: Dict) -> List[str]:
        """Generate actionable insights from revenue analysis"""
        insights = []
        
        try:
            # Overall trend insights
            recent_trend = df['revenue_trend'].iloc[-3:].mean()
            if recent_trend > 5:
                insights.append(f"Revenue shows strong upward trend (+{recent_trend:.1f}% over last 3 weeks)")
            elif recent_trend < -5:
                insights.append(f"Revenue declining trend (-{abs(recent_trend):.1f}% over last 3 weeks) requires attention")
            
            # Store performance insights
            best_store = max(store_metrics.items(), key=lambda x: x[1]['growth_rate'])
            worst_store = min(store_metrics.items(), key=lambda x: x[1]['growth_rate'])
            
            insights.append(f"{best_store[0]} leads growth at +{best_store[1]['growth_rate']:.1f}%")
            
            if worst_store[1]['growth_rate'] < -2:
                insights.append(f"{worst_store[0]} needs support with {worst_store[1]['growth_rate']:.1f}% decline")
            
            # Seasonality insights
            peak_revenue = df['total_revenue'].max()
            current_revenue = df['total_revenue'].iloc[-1]
            if current_revenue < peak_revenue * 0.8:
                insights.append(f"Current revenue is {((current_revenue/peak_revenue-1)*100):+.1f}% below peak performance")
            
        except Exception as e:
            logger.warning(f"Error generating revenue insights: {e}")
        
        return insights
    
    def _generate_yoy_insights(self, monthly_comparison: pd.DataFrame, overall_growth: float) -> List[str]:
        """Generate insights from year-over-year analysis"""
        insights = []
        
        try:
            # Overall performance insight
            if overall_growth > 10:
                insights.append(f"Exceptional YoY growth of {overall_growth:.1f}% indicates strong business expansion")
            elif overall_growth > 0:
                insights.append(f"Positive YoY growth of {overall_growth:.1f}% shows steady business health")
            else:
                insights.append(f"YoY decline of {abs(overall_growth):.1f}% requires strategic intervention")
            
            # Monthly performance insights
            best_month = monthly_comparison.loc[monthly_comparison['yoy_growth_rate'].idxmax()]
            worst_month = monthly_comparison.loc[monthly_comparison['yoy_growth_rate'].idxmin()]
            
            insights.append(f"Month {int(best_month['month_num'])} shows strongest growth at +{best_month['yoy_growth_rate']:.1f}%")
            
            if worst_month['yoy_growth_rate'] < -5:
                insights.append(f"Month {int(worst_month['month_num'])} declining {abs(worst_month['yoy_growth_rate']):.1f}% needs focus")
            
            # Seasonal consistency
            growth_volatility = monthly_comparison['yoy_growth_rate'].std()
            if growth_volatility > 15:
                insights.append(f"High growth volatility ({growth_volatility:.1f}%) suggests seasonal challenges")
            
        except Exception as e:
            logger.warning(f"Error generating YoY insights: {e}")
        
        return insights
    
    def get_executive_financial_dashboard(self) -> Dict:
        """
        Generate comprehensive executive financial dashboard with all key metrics
        """
        try:
            # Get rolling averages for key metrics
            revenue_rolling = self.calculate_rolling_averages('revenue', weeks_back=26)
            contracts_rolling = self.calculate_rolling_averages('contracts', weeks_back=26)
            
            # Get year-over-year analysis
            yoy_analysis = self.calculate_year_over_year_analysis('comprehensive')
            
            # Get multi-store performance
            store_performance = self.analyze_multi_store_performance(26)
            
            # Get financial forecasts
            forecasts = self.generate_financial_forecasts(12, 0.95)
            
            # Combine into executive summary
            dashboard = {
                "success": True,
                "generated_at": datetime.now().isoformat(),
                "executive_summary": {
                    "revenue_health": "strong" if revenue_rolling.get("summary", {}).get("smoothed_trend", 0) > 0 else "declining",
                    "yoy_performance": "growth" if yoy_analysis.get("comparison_period", {}).get("overall_growth_rate", 0) > 0 else "decline",
                    "store_count": len(self.STORE_CODES),
                    "forecast_confidence": "high" if forecasts.get("success", False) else "limited"
                },
                "rolling_averages": revenue_rolling,
                "yoy_analysis": yoy_analysis,
                "store_performance": store_performance,
                "forecasts": forecasts,
                "key_recommendations": self._generate_executive_recommendations(
                    revenue_rolling, yoy_analysis, store_performance, forecasts
                )
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating executive dashboard: {e}")
            return {"error": str(e), "success": False}
    
    def _generate_executive_recommendations(self, revenue_data: Dict, yoy_data: Dict, 
                                          store_data: Dict, forecast_data: Dict) -> List[str]:
        """Generate executive-level recommendations based on financial analysis"""
        recommendations = []
        
        try:
            # Revenue trend recommendations
            if revenue_data.get("success") and "summary" in revenue_data:
                trend = revenue_data["summary"].get("smoothed_trend", 0)
                if trend < -2:
                    recommendations.append("PRIORITY: Implement revenue recovery strategy - 3-week trend shows decline")
                elif trend > 5:
                    recommendations.append("OPPORTUNITY: Scale successful strategies - strong revenue momentum")
            
            # YoY performance recommendations
            if yoy_data.get("success") and "comparison_period" in yoy_data:
                growth = yoy_data["comparison_period"].get("overall_growth_rate", 0)
                if growth < 0:
                    recommendations.append("STRATEGIC: Address YoY decline - investigate market factors and operational efficiency")
                elif growth > 15:
                    recommendations.append("GROWTH: Exceptional performance - consider expansion opportunities")
            
            # Store performance recommendations
            if store_data.get("success") and "performance_benchmarks" in store_data:
                benchmarks = store_data["performance_benchmarks"]
                if "store_rankings" in benchmarks:
                    # Find lowest performing store
                    lowest_rank = max(store_rankings["overall_rank"] for store_rankings in benchmarks["store_rankings"].values())
                    lowest_store = [store for store, rankings in benchmarks["store_rankings"].items() 
                                  if rankings["overall_rank"] == lowest_rank][0]
                    recommendations.append(f"OPERATIONAL: Focus improvement efforts on {lowest_store} - lowest overall performance")
            
            # Forecast-based recommendations
            if forecast_data.get("success") and "executive_summary" in forecast_data:
                forecast_summary = forecast_data["executive_summary"]
                if "projected_decline" in forecast_summary and forecast_summary["projected_decline"]:
                    recommendations.append("PLANNING: Prepare for forecasted revenue decline - implement cost controls")
                elif "growth_opportunity" in forecast_summary and forecast_summary["growth_opportunity"]:
                    recommendations.append("INVESTMENT: Strong forecast supports strategic investments and hiring")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _forecast_profitability(self, historical_data: List[Dict], horizon_weeks: int, 
                               confidence_level: float) -> Dict:
        """Generate profitability forecasts"""
        try:
            df = pd.DataFrame(historical_data)
            profit_series = df['gross_profit'].values
            
            if len(profit_series) < 4:
                return {"error": "Insufficient data for profitability forecasting"}
            
            # Calculate profit margins
            margin_series = []
            for i, row in df.iterrows():
                if row['all_revenue'] and row['all_revenue'] > 0:
                    margin_series.append((row['gross_profit'] / row['all_revenue']) * 100)
                else:
                    margin_series.append(0)
            
            # Trend analysis
            profit_trend = np.polyfit(range(len(profit_series)), profit_series, 1)
            margin_trend = np.polyfit(range(len(margin_series)), margin_series, 1)
            
            forecasts = []
            for week in range(1, horizon_weeks + 1):
                # Profit forecast
                profit_forecast = profit_trend[0] * (len(profit_series) + week) + profit_trend[1]
                margin_forecast = margin_trend[0] * (len(margin_series) + week) + margin_trend[1]
                
                # Confidence intervals
                profit_std = np.std(profit_series)
                profit_ci = 1.96 * profit_std * (1 + week * 0.1) if confidence_level == 0.95 else 2.576 * profit_std * (1 + week * 0.1)
                
                forecast_date = df['week_ending'].iloc[-1] + timedelta(weeks=week)
                
                forecasts.append({
                    'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                    'weeks_ahead': week,
                    'profit_forecast': round(max(0, profit_forecast), 2),
                    'margin_forecast_pct': round(margin_forecast, 2),
                    'profit_confidence_low': round(max(0, profit_forecast - profit_ci), 2),
                    'profit_confidence_high': round(profit_forecast + profit_ci, 2),
                })
            
            return {
                "forecast_type": "profitability",
                "forecasts": forecasts,
                "summary": {
                    "avg_forecasted_profit": round(np.mean([f['profit_forecast'] for f in forecasts]), 2),
                    "avg_forecasted_margin": round(np.mean([f['margin_forecast_pct'] for f in forecasts]), 2),
                    "profit_trend_direction": "increasing" if profit_trend[0] > 0 else "decreasing",
                    "margin_trend_direction": "improving" if margin_trend[0] > 0 else "declining"
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting profitability: {e}")
            return {"error": str(e)}
    
    def _forecast_cash_flow(self, historical_data: List[Dict], horizon_weeks: int, 
                           confidence_level: float) -> Dict:
        """Generate cash flow forecasts"""
        try:
            df = pd.DataFrame(historical_data)
            
            # Simulate cash flow data (in real implementation, would use actual cash flow data)
            df['estimated_cash_flow'] = df['gross_profit'] * 0.85  # Assume 85% cash conversion
            cash_flow_series = df['estimated_cash_flow'].values
            
            if len(cash_flow_series) < 4:
                return {"error": "Insufficient data for cash flow forecasting"}
            
            # Trend and seasonal analysis
            trend = np.polyfit(range(len(cash_flow_series)), cash_flow_series, 1)
            
            # Calculate seasonal factors (quarterly)
            seasonal_factors = []
            if len(cash_flow_series) >= 12:  # At least 3 months of data
                for i in range(len(cash_flow_series)):
                    season_idx = i % 13  # 13-week quarters
                    seasonal_factors.append(cash_flow_series[i] / np.mean(cash_flow_series))
            
            forecasts = []
            cumulative_cash_flow = 0
            
            for week in range(1, horizon_weeks + 1):
                # Base trend forecast
                base_forecast = trend[0] * (len(cash_flow_series) + week) + trend[1]
                
                # Apply seasonal adjustment if available
                if seasonal_factors:
                    seasonal_idx = (week - 1) % len(seasonal_factors)
                    seasonal_adjustment = seasonal_factors[seasonal_idx]
                    cash_flow_forecast = base_forecast * seasonal_adjustment
                else:
                    cash_flow_forecast = base_forecast
                
                cash_flow_forecast = max(0, cash_flow_forecast)
                cumulative_cash_flow += cash_flow_forecast
                
                # Confidence intervals
                std_error = np.std(cash_flow_series) * (1 + week * 0.08)
                z_score = 1.96 if confidence_level == 0.95 else 2.576
                ci = z_score * std_error
                
                forecast_date = df['week_ending'].iloc[-1] + timedelta(weeks=week)
                
                forecasts.append({
                    'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                    'weeks_ahead': week,
                    'weekly_cash_flow': round(cash_flow_forecast, 2),
                    'cumulative_cash_flow': round(cumulative_cash_flow, 2),
                    'confidence_low': round(max(0, cash_flow_forecast - ci), 2),
                    'confidence_high': round(cash_flow_forecast + ci, 2)
                })
            
            return {
                "forecast_type": "cash_flow",
                "forecasts": forecasts,
                "summary": {
                    "total_forecasted_cash_flow": round(cumulative_cash_flow, 2),
                    "avg_weekly_cash_flow": round(cumulative_cash_flow / horizon_weeks, 2),
                    "cash_flow_trend": "positive" if trend[0] > 0 else "negative",
                    "liquidity_outlook": "strong" if cumulative_cash_flow > 0 else "concerning"
                }
            }
            
        except Exception as e:
            logger.error(f"Error forecasting cash flow: {e}")
            return {"error": str(e)}
    
    def _generate_forecast_summary(self, revenue_forecast: Dict, profitability_forecast: Dict, 
                                 cash_flow_forecast: Dict) -> Dict:
        """Generate executive forecast summary"""
        try:
            summary = {
                "overall_outlook": "positive",
                "key_insights": [],
                "risk_factors": [],
                "opportunities": []
            }
            
            # Revenue insights
            if revenue_forecast.get("success") != False and "summary" in revenue_forecast:
                rev_summary = revenue_forecast["summary"]
                if rev_summary.get("projected_growth_rate", 0) > 5:
                    summary["key_insights"].append("Strong revenue growth projected")
                    summary["opportunities"].append("Scale successful revenue strategies")
                elif rev_summary.get("projected_growth_rate", 0) < -2:
                    summary["key_insights"].append("Revenue decline forecasted")
                    summary["risk_factors"].append("Implement revenue recovery plan")
            
            # Profitability insights
            if profitability_forecast.get("success") != False and "summary" in profitability_forecast:
                profit_summary = profitability_forecast["summary"]
                if profit_summary.get("margin_trend_direction") == "improving":
                    summary["key_insights"].append("Profit margins trending upward")
                elif profit_summary.get("margin_trend_direction") == "declining":
                    summary["risk_factors"].append("Margin pressure requires cost management")
            
            # Cash flow insights
            if cash_flow_forecast.get("success") != False and "summary" in cash_flow_forecast:
                cash_summary = cash_flow_forecast["summary"]
                if cash_summary.get("liquidity_outlook") == "strong":
                    summary["key_insights"].append("Strong cash flow position forecasted")
                    summary["opportunities"].append("Consider strategic investments")
                else:
                    summary["risk_factors"].append("Cash flow concerns require attention")
            
            # Overall outlook
            risk_count = len(summary["risk_factors"])
            opportunity_count = len(summary["opportunities"])
            
            if opportunity_count > risk_count:
                summary["overall_outlook"] = "positive"
            elif risk_count > opportunity_count:
                summary["overall_outlook"] = "cautious"
            else:
                summary["overall_outlook"] = "neutral"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating forecast summary: {e}")
            return {"overall_outlook": "uncertain", "key_insights": [], "error": str(e)}
    
    def _calculate_utilization_rolling_averages(self, start_date: date, end_date: date) -> Dict:
        """Calculate equipment utilization rolling averages"""
        try:
            # This would integrate with equipment utilization data
            # For now, return structure for future implementation
            return {
                "success": True,
                "metric_type": "utilization_rolling_averages",
                "message": "Equipment utilization analysis available with RFID integration",
                "structure": {
                    "utilization_trends": [],
                    "store_utilization": {},
                    "category_utilization": {},
                    "optimization_opportunities": []
                }
            }
        except Exception as e:
            logger.error(f"Error calculating utilization rolling averages: {e}")
            return {"error": str(e)}
    
    def _calculate_profitability_rolling_averages(self, start_date: date, end_date: date) -> Dict:
        """Calculate profitability rolling averages"""
        try:
            # Get payroll and revenue data for profitability analysis
            query = text("""
                SELECT 
                    p.week_ending,
                    p.location_code,
                    p.all_revenue,
                    p.payroll_amount,
                    (p.all_revenue - p.payroll_amount) as gross_profit,
                    CASE WHEN p.all_revenue > 0 
                         THEN ((p.all_revenue - p.payroll_amount) / p.all_revenue) * 100 
                         ELSE 0 END as profit_margin_pct
                FROM payroll_trends_data p
                WHERE p.week_ending BETWEEN :start_date AND :end_date
                ORDER BY p.week_ending, p.location_code
            """)
            
            results = db.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            if not results:
                return {"error": "No profitability data available"}
            
            df = pd.DataFrame([{
                'week_ending': row.week_ending,
                'store_code': row.location_code,
                'revenue': float(row.all_revenue or 0),
                'payroll': float(row.payroll_amount or 0),
                'gross_profit': float(row.gross_profit or 0),
                'margin_pct': float(row.profit_margin_pct or 0)
            } for row in results])
            
            # Calculate rolling averages by store
            store_analysis = {}
            for store_code in df['store_code'].unique():
                store_df = df[df['store_code'] == store_code].copy()
                store_df = store_df.sort_values('week_ending')
                
                # Configurable rolling averages
                # OLD - HARDCODED (WRONG): store_df['profit_3wk_avg'] = store_df['gross_profit'].rolling(window=3, center=True).mean()
                # NEW - CONFIGURABLE (CORRECT):
                rolling_window = self.get_config_value('rolling_window_weeks', 3)
                store_df['profit_3wk_avg'] = store_df['gross_profit'].rolling(window=rolling_window, center=True).mean()
                store_df['margin_3wk_avg'] = store_df['margin_pct'].rolling(window=rolling_window, center=True).mean()
                
                # Trend analysis
                recent_avg_profit = float(store_df['profit_3wk_avg'].iloc[-3:].mean())
                previous_avg_profit = float(store_df['profit_3wk_avg'].iloc[-6:-3].mean())
                
                store_name = self.STORE_CODES.get(store_code, f"Store {store_code}")
                store_analysis[store_name] = {
                    'current_3wk_avg_profit': recent_avg_profit,
                    'previous_3wk_avg_profit': previous_avg_profit,
                    'current_3wk_avg_margin': float(store_df['margin_3wk_avg'].iloc[-3:].mean()),
                    'profit_trend': 'improving' if recent_avg_profit > previous_avg_profit else 'declining',
                    'profit_volatility': float(store_df['gross_profit'].std())
                }
            
            # Company-wide analysis
            company_df = df.groupby('week_ending').agg({
                'revenue': 'sum',
                'payroll': 'sum',
                'gross_profit': 'sum'
            }).reset_index()
            
            company_df['margin_pct'] = (company_df['gross_profit'] / company_df['revenue'] * 100).fillna(0)
            # OLD - HARDCODED (WRONG): company_df['profit_3wk_avg'] = company_df['gross_profit'].rolling(window=3, center=True).mean()
            # NEW - CONFIGURABLE (CORRECT):
            rolling_window = self.get_config_value('rolling_window_weeks', 3)
            company_df['profit_3wk_avg'] = company_df['gross_profit'].rolling(window=rolling_window, center=True).mean()
            
            return {
                "success": True,
                "metric_type": "profitability_rolling_averages",
                "analysis_period": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d')
                },
                "company_summary": {
                    'current_3wk_avg_profit': float(company_df['profit_3wk_avg'].iloc[-3:].mean()),
                    'current_avg_margin': float(company_df['margin_pct'].iloc[-3:].mean()),
                    'total_profit_ytd': float(company_df['gross_profit'].sum())
                },
                "store_analysis": store_analysis,
                "weekly_data": company_df.fillna(0).to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error calculating profitability rolling averages: {e}")
            return {"error": str(e)}
    
    def _calculate_comprehensive_rolling_averages(self, start_date: date, end_date: date) -> Dict:
        """Calculate comprehensive rolling averages across all metrics"""
        try:
            revenue_data = self._calculate_revenue_rolling_averages(start_date, end_date)
            contracts_data = self._calculate_contracts_rolling_averages(start_date, end_date)
            profitability_data = self._calculate_profitability_rolling_averages(start_date, end_date)
            
            return {
                "success": True,
                "metric_type": "comprehensive_rolling_averages",
                "analysis_period": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d')
                },
                "revenue_analysis": revenue_data,
                "contracts_analysis": contracts_data,
                "profitability_analysis": profitability_data,
                "executive_summary": self._generate_comprehensive_summary(
                    revenue_data, contracts_data, profitability_data
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive rolling averages: {e}")
            return {"error": str(e)}
    
    def _generate_comprehensive_summary(self, revenue_data: Dict, contracts_data: Dict, 
                                       profitability_data: Dict) -> Dict:
        """Generate executive summary of comprehensive analysis"""
        try:
            summary = {
                "overall_health_score": 75,  # Default neutral score
                "key_trends": [],
                "critical_actions": [],
                "growth_opportunities": []
            }
            
            # Analyze revenue trends
            if revenue_data.get("success") and "summary" in revenue_data:
                trend = revenue_data["summary"].get("smoothed_trend", 0)
                if trend > 5:
                    summary["key_trends"].append("Strong revenue momentum")
                    summary["overall_health_score"] += 10
                elif trend < -3:
                    summary["key_trends"].append("Revenue declining")
                    summary["critical_actions"].append("Address revenue decline")
                    summary["overall_health_score"] -= 15
            
            # Analyze contract trends
            if contracts_data.get("success") and "summary" in contracts_data:
                velocity = contracts_data["summary"].get("contract_velocity_trend", 0)
                if velocity > 0:
                    summary["key_trends"].append("Contract volume growing")
                elif velocity < -5:
                    summary["critical_actions"].append("Boost new contract acquisition")
            
            # Analyze profitability
            if profitability_data.get("success") and "company_summary" in profitability_data:
                margin = profitability_data["company_summary"].get("current_avg_margin", 0)
                if margin > 25:
                    summary["key_trends"].append("Healthy profit margins")
                    summary["growth_opportunities"].append("Scale high-margin services")
                elif margin < 15:
                    summary["critical_actions"].append("Improve cost management")
                    summary["overall_health_score"] -= 10
            
            # Cap health score
            summary["overall_health_score"] = max(0, min(100, summary["overall_health_score"]))
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating comprehensive summary: {e}")
            return {"overall_health_score": 50, "error": str(e)}
    
    def _analyze_store_efficiency(self, start_date: date, end_date: date) -> Dict:
        """Analyze operational efficiency across stores"""
        try:
            query = text("""
                SELECT 
                    p.location_code,
                    AVG(CASE WHEN p.wage_hours > 0 THEN p.all_revenue / p.wage_hours ELSE 0 END) as avg_revenue_per_hour,
                    AVG(CASE WHEN p.all_revenue > 0 THEN (p.payroll_amount / p.all_revenue) * 100 ELSE 0 END) as avg_labor_cost_ratio,
                    SUM(p.all_revenue) as total_revenue,
                    SUM(p.payroll_amount) as total_payroll,
                    SUM(p.wage_hours) as total_hours,
                    COUNT(*) as periods_count
                FROM payroll_trends_data p
                WHERE p.week_ending BETWEEN :start_date AND :end_date
                GROUP BY p.location_code
            """)
            
            results = db.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            efficiency_scores = {}
            for row in results:
                store_name = self.STORE_CODES.get(row.location_code, f"Store {row.location_code}")
                
                # Calculate efficiency metrics
                revenue_per_hour = float(row.avg_revenue_per_hour or 0)
                labor_cost_ratio = float(row.avg_labor_cost_ratio or 0)
                
                # Efficiency score using configurable baseline (higher revenue per hour, lower labor cost ratio = better)
                config = self.get_labor_cost_config()
                efficiency_baseline = getattr(config, 'efficiency_baseline', 100.0)
                
                revenue_efficiency = min(100, revenue_per_hour / 10)  # Cap at 100 for $1000/hour
                cost_efficiency = max(0, efficiency_baseline - labor_cost_ratio)
                overall_efficiency = (revenue_efficiency + cost_efficiency) / 2
                
                efficiency_scores[store_name] = {
                    'revenue_per_hour': revenue_per_hour,
                    'labor_cost_ratio_pct': labor_cost_ratio,
                    'revenue_efficiency_score': round(revenue_efficiency, 1),
                    'cost_efficiency_score': round(cost_efficiency, 1),
                    'overall_efficiency_score': round(overall_efficiency, 1),
                    'total_revenue': float(row.total_revenue or 0),
                    'total_hours': float(row.total_hours or 0)
                }
            
            # Rank stores by efficiency
            ranked_stores = sorted(efficiency_scores.items(), 
                                 key=lambda x: x[1]['overall_efficiency_score'], 
                                 reverse=True)
            
            return {
                "success": True,
                "efficiency_metrics": efficiency_scores,
                "efficiency_rankings": [
                    {"rank": i+1, "store": store, "score": metrics['overall_efficiency_score']}
                    for i, (store, metrics) in enumerate(ranked_stores)
                ],
                "efficiency_insights": self._generate_efficiency_insights(efficiency_scores)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing store efficiency: {e}")
            return {"error": str(e)}
    
    def _optimize_resource_allocation(self, store_metrics: Dict) -> Dict:
        """Generate resource allocation optimization recommendations"""
        try:
            if not store_metrics:
                return {"error": "No store metrics available for optimization"}
            
            optimization_recommendations = {}
            
            # Analyze each store's performance
            for store_name, metrics in store_metrics.items():
                financial = metrics.get('financial_metrics', {})
                operational = metrics.get('operational_metrics', {})
                
                recommendations = []
                priority_score = 0
                
                # Revenue per hour analysis
                revenue_per_hour = operational.get('revenue_per_hour', 0)
                if revenue_per_hour < 500:  # Below $500/hour
                    recommendations.append("Increase pricing or improve productivity")
                    priority_score += 3
                elif revenue_per_hour > 1000:  # Above $1000/hour
                    recommendations.append("Consider expanding capacity")
                    priority_score -= 1
                
                # Profit margin analysis
                profit_margin = financial.get('profit_margin', 0)
                if profit_margin < 20:  # Below 20% margin
                    recommendations.append("Focus on cost reduction initiatives")
                    priority_score += 2
                elif profit_margin > 40:  # Above 40% margin
                    recommendations.append("Opportunity for competitive pricing")
                
                # Contract efficiency
                contracts_per_hour = operational.get('contracts_per_hour', 0)
                if contracts_per_hour < 0.5:  # Less than 0.5 contracts per hour
                    recommendations.append("Streamline contract processing")
                    priority_score += 2
                
                optimization_recommendations[store_name] = {
                    'priority_score': priority_score,
                    'priority_level': 'high' if priority_score >= 5 else 'medium' if priority_score >= 3 else 'low',
                    'recommendations': recommendations,
                    'current_performance': {
                        'revenue_per_hour': revenue_per_hour,
                        'profit_margin': profit_margin,
                        'contracts_per_hour': contracts_per_hour
                    }
                }
            
            # Generate overall allocation strategy
            high_priority_stores = [store for store, data in optimization_recommendations.items() 
                                  if data['priority_level'] == 'high']
            
            allocation_strategy = {
                'focus_stores': high_priority_stores,
                'investment_priorities': [],
                'resource_shifts': []
            }
            
            if high_priority_stores:
                allocation_strategy['investment_priorities'].append("Operational efficiency improvements")
                allocation_strategy['resource_shifts'].append(f"Prioritize support for {len(high_priority_stores)} underperforming locations")
            
            return {
                "success": True,
                "store_recommendations": optimization_recommendations,
                "allocation_strategy": allocation_strategy,
                "optimization_summary": {
                    "total_stores_analyzed": len(store_metrics),
                    "high_priority_stores": len(high_priority_stores),
                    "optimization_potential": "high" if len(high_priority_stores) > 1 else "moderate"
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")
            return {"error": str(e)}
    
    def _generate_efficiency_insights(self, efficiency_scores: Dict) -> List[str]:
        """Generate insights from efficiency analysis"""
        insights = []
        
        try:
            if not efficiency_scores:
                return ["No efficiency data available"]
            
            # Find best and worst performers
            best_store = max(efficiency_scores.items(), key=lambda x: x[1]['overall_efficiency_score'])
            worst_store = min(efficiency_scores.items(), key=lambda x: x[1]['overall_efficiency_score'])
            
            insights.append(f"{best_store[0]} leads efficiency at {best_store[1]['overall_efficiency_score']:.1f} points")
            
            if worst_store[1]['overall_efficiency_score'] < 60:
                insights.append(f"{worst_store[0]} needs efficiency improvement (score: {worst_store[1]['overall_efficiency_score']:.1f})")
            
            # Labor cost insights
            # Use configurable labor cost thresholds instead of hardcoded 35%
            high_labor_cost_stores = []
            for store, metrics in efficiency_scores.items():
                # Get store-specific or global threshold
                store_codes = {'Wayzata': '3607', 'Brooklyn Park': '6800', 'Elk River': '728', 'Fridley': '8101'}
                store_code = store_codes.get(store, '3607')  # Default to first store if not found
                threshold = self.get_store_labor_threshold(store_code, 'high_threshold')
                
                if metrics['labor_cost_ratio_pct'] > threshold:
                    high_labor_cost_stores.append({'store': store, 'ratio': metrics['labor_cost_ratio_pct'], 'threshold': threshold})
            
            if high_labor_cost_stores:
                thresholds_used = set([store['threshold'] for store in high_labor_cost_stores])
                if len(thresholds_used) == 1:
                    threshold_text = f">{list(thresholds_used)[0]:.1f}%"
                else:
                    threshold_text = "above configured thresholds"
                insights.append(f"{len(high_labor_cost_stores)} stores have high labor cost ratios ({threshold_text})")
            
            # Revenue per hour insights
            low_productivity_stores = [store for store, metrics in efficiency_scores.items() 
                                     if metrics['revenue_per_hour'] < 500]
            
            if low_productivity_stores:
                insights.append(f"{len(low_productivity_stores)} stores below $500/hour productivity target")
            
        except Exception as e:
            logger.warning(f"Error generating efficiency insights: {e}")
        
        return insights
    
    def _generate_multi_store_insights(self, store_metrics: Dict, benchmarks: Dict, 
                                     efficiency_analysis: Dict) -> List[str]:
        """Generate executive insights from multi-store analysis"""
        insights = []
        
        try:
            # Performance spread insights
            if benchmarks and 'revenue_benchmarks' in benchmarks:
                performance_gap = benchmarks['revenue_benchmarks'].get('performance_gap', 0)
                if performance_gap > 50000:  # $50k+ gap
                    insights.append(f"Large performance gap (${performance_gap:,.0f}) between top and bottom stores")
            
            # Efficiency insights
            if efficiency_analysis.get('success') and 'efficiency_rankings' in efficiency_analysis:
                rankings = efficiency_analysis['efficiency_rankings']
                if len(rankings) >= 2:
                    top_store = rankings[0]
                    bottom_store = rankings[-1]
                    score_gap = top_store['score'] - bottom_store['score']
                    if score_gap > 30:
                        insights.append(f"Significant efficiency gap: {top_store['store']} outperforms {bottom_store['store']} by {score_gap:.1f} points")
            
            # Growth opportunity insights
            total_stores = len(store_metrics)
            if total_stores >= 3:
                insights.append(f"Multi-store advantage: {total_stores} locations provide diversification and growth opportunities")
            
        except Exception as e:
            logger.warning(f"Error generating multi-store insights: {e}")
        
        return insights