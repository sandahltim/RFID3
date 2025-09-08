"""
Scorecard Analytics Service
Enhanced analytics and correlations for scorecard data integration
"""

from app import db
from app.models.financial_models import (
    ScorecardTrendsData,
    ScorecardMetricsDefinition,
    PayrollTrendsData,
    FinancialMetrics,
    StorePerformanceBenchmarks
)
from app.models.config_models import BusinessAnalyticsConfiguration
from sqlalchemy import func, and_, or_, case, text
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ScorecardAnalyticsService:
    """Service for advanced scorecard data analytics and correlations"""
    
    STORE_MAPPING = {
        '3607': 'Wayzata',
        '6800': 'Brooklyn Park',
        '728': 'Elk River',
        '8101': 'Fridley'
    }
    
    @classmethod
    def get_revenue_correlations(cls) -> Dict:
        """Calculate revenue correlations across stores and metrics"""
        try:
            # Get last 52 weeks of data
            cutoff_date = datetime.now().date() - timedelta(days=365)
            data = db.session.query(ScorecardTrendsData).filter(
                ScorecardTrendsData.week_ending >= cutoff_date
            ).order_by(ScorecardTrendsData.week_ending).all()
            
            if not data:
                return {'error': 'No data available'}
            
            correlations = {
                'store_correlations': {},
                'contract_correlations': {},
                'pipeline_correlations': {},
                'ar_impact': {}
            }
            
            # Calculate store-specific correlations
            for store_code, store_name in cls.STORE_MAPPING.items():
                revenue_field = f'revenue_{store_code}'
                contract_field = f'new_contracts_{store_code}'
                
                revenues = []
                contracts = []
                
                for row in data:
                    rev = getattr(row, revenue_field, 0) or 0
                    cont = getattr(row, contract_field, 0) or 0
                    if rev > 0 and cont > 0:
                        revenues.append(float(rev))
                        contracts.append(float(cont))
                
                if len(revenues) > 10:  # Need sufficient data
                    correlation = np.corrcoef(revenues, contracts)[0, 1]
                    avg_contract_value = sum(revenues) / sum(contracts) if sum(contracts) > 0 else 0
                    
                    correlations['store_correlations'][store_name] = {
                        'correlation': round(correlation, 3),
                        'avg_contract_value': round(avg_contract_value, 2),
                        'data_points': len(revenues)
                    }
            
            # Calculate AR aging impact
            ar_categories = {'low': [], 'medium': [], 'high': []}
            for row in data:
                ar_pct = float(row.ar_over_45_days_percent or 0)
                revenue = float(row.total_weekly_revenue or 0)
                
                # OLD - HARDCODED (WRONG): if ar_pct < 5: / elif ar_pct < 15:
                # NEW - CONFIGURABLE (CORRECT):
                config = self._get_config()
                ar_low_threshold = config.get_threshold('ar_aging_low_threshold')
                ar_medium_threshold = config.get_threshold('ar_aging_medium_threshold')
                
                if ar_pct < ar_low_threshold:
                    ar_categories['low'].append(revenue)
                elif ar_pct < ar_medium_threshold:
                    ar_categories['medium'].append(revenue)
                else:
                    ar_categories['high'].append(revenue)
            
            for category, revenues in ar_categories.items():
                if revenues:
                    correlations['ar_impact'][category] = {
                        'avg_revenue': round(np.mean(revenues), 2),
                        'revenue_volatility': round(np.std(revenues), 2),
                        'weeks': len(revenues)
                    }
            
            # Calculate pipeline conversion
            pipeline_data = []
            revenue_data = []
            
            for i in range(len(data) - 2):
                pipeline = sum([
                    float(data[i].reservation_next14_3607 or 0),
                    float(data[i].reservation_next14_6800 or 0),
                    float(data[i].reservation_next14_728 or 0),
                    float(data[i].reservation_next14_8101 or 0)
                ])
                future_revenue = float(data[i + 2].total_weekly_revenue or 0)
                
                if pipeline > 0:
                    pipeline_data.append(pipeline)
                    revenue_data.append(future_revenue)
            
            if pipeline_data:
                conversion_rate = sum(revenue_data) / sum(pipeline_data)
                correlation = np.corrcoef(pipeline_data, revenue_data)[0, 1]
                
                correlations['pipeline_correlations'] = {
                    'conversion_rate': round(conversion_rate, 3),
                    'correlation': round(correlation, 3),
                    'avg_pipeline': round(np.mean(pipeline_data), 2)
                }
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error calculating correlations: {str(e)}")
            return {'error': str(e)}
    
    @classmethod
    def get_performance_trends(cls, weeks: int = 12) -> Dict:
        """Get performance trends for specified number of weeks"""
        try:
            cutoff_date = datetime.now().date() - timedelta(weeks=weeks)
            
            data = db.session.query(ScorecardTrendsData).filter(
                ScorecardTrendsData.week_ending >= cutoff_date
            ).order_by(ScorecardTrendsData.week_ending).all()
            
            trends = {
                'weekly_data': [],
                'store_performance': {store: [] for store in cls.STORE_MAPPING.values()},
                'summary_stats': {}
            }
            
            total_revenues = []
            for row in data:
                week_data = {
                    'week': row.week_ending.strftime('%Y-%m-%d'),
                    'total_revenue': float(row.total_weekly_revenue or 0),
                    'total_contracts': sum([
                        row.new_contracts_3607 or 0,
                        row.new_contracts_6800 or 0,
                        row.new_contracts_728 or 0,
                        row.new_contracts_8101 or 0
                    ]),
                    'ar_over_45': float(row.ar_over_45_days_percent or 0)
                }
                trends['weekly_data'].append(week_data)
                total_revenues.append(week_data['total_revenue'])
                
                # Store-specific data
                for store_code, store_name in cls.STORE_MAPPING.items():
                    revenue = float(getattr(row, f'revenue_{store_code}', 0) or 0)
                    contracts = getattr(row, f'new_contracts_{store_code}', 0) or 0
                    trends['store_performance'][store_name].append({
                        'week': row.week_ending.strftime('%Y-%m-%d'),
                        'revenue': revenue,
                        'contracts': contracts
                    })
            
            # Calculate summary statistics
            if total_revenues:
                trends['summary_stats'] = {
                    'avg_weekly_revenue': round(np.mean(total_revenues), 2),
                    'revenue_std_dev': round(np.std(total_revenues), 2),
                    'revenue_trend': cls._calculate_trend(total_revenues),
                    'max_revenue': round(max(total_revenues), 2),
                    'min_revenue': round(min(total_revenues), 2)
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {str(e)}")
            return {'error': str(e)}
    
    @classmethod
    def get_store_rankings(cls, date_from: Optional[datetime] = None) -> List[Dict]:
        """Get store performance rankings"""
        try:
            if not date_from:
                date_from = datetime.now().date() - timedelta(days=90)
            
            # Query aggregated data by store
            store_data = []
            
            for store_code, store_name in cls.STORE_MAPPING.items():
                revenue_field = f'revenue_{store_code}'
                contract_field = f'new_contracts_{store_code}'
                
                result = db.session.query(
                    func.sum(getattr(ScorecardTrendsData, revenue_field)).label('total_revenue'),
                    func.sum(getattr(ScorecardTrendsData, contract_field)).label('total_contracts'),
                    func.avg(getattr(ScorecardTrendsData, revenue_field)).label('avg_revenue'),
                    func.count(ScorecardTrendsData.id).label('weeks')
                ).filter(
                    ScorecardTrendsData.week_ending >= date_from
                ).first()
                
                if result and result.total_revenue:
                    store_data.append({
                        'store_code': store_code,
                        'store_name': store_name,
                        'total_revenue': float(result.total_revenue or 0),
                        'total_contracts': int(result.total_contracts or 0),
                        'avg_weekly_revenue': float(result.avg_revenue or 0),
                        'avg_contract_value': float(result.total_revenue / result.total_contracts) if result.total_contracts else 0,
                        'weeks': result.weeks
                    })
            
            # Sort by total revenue and add rankings
            store_data.sort(key=lambda x: x['total_revenue'], reverse=True)
            for i, store in enumerate(store_data, 1):
                store['revenue_rank'] = i
                store['performance_tier'] = cls._get_performance_tier(i, len(store_data))
            
            return store_data
            
        except Exception as e:
            logger.error(f"Error getting store rankings: {str(e)}")
            return []
    
    @classmethod
    def get_predictive_insights(cls) -> Dict:
        """Generate predictive insights based on historical patterns"""
        try:
            # Get last 26 weeks for seasonal pattern analysis
            cutoff_date = datetime.now().date() - timedelta(weeks=26)
            
            data = db.session.query(ScorecardTrendsData).filter(
                ScorecardTrendsData.week_ending >= cutoff_date
            ).order_by(ScorecardTrendsData.week_ending).all()
            
            if len(data) < 12:
                return {'error': 'Insufficient data for predictions'}
            
            insights = {
                'seasonal_patterns': {},
                'revenue_forecast': {},
                'risk_indicators': [],
                'opportunities': []
            }
            
            # Analyze seasonal patterns
            monthly_revenues = {}
            for row in data:
                month = row.week_ending.month
                if month not in monthly_revenues:
                    monthly_revenues[month] = []
                monthly_revenues[month].append(float(row.total_weekly_revenue or 0))
            
            for month, revenues in monthly_revenues.items():
                insights['seasonal_patterns'][month] = {
                    'avg_revenue': round(np.mean(revenues), 2),
                    'volatility': round(np.std(revenues), 2)
                }
            
            # Simple moving average forecast
            recent_revenues = [float(row.total_weekly_revenue or 0) for row in data[-4:]]
            if recent_revenues:
                ma_forecast = np.mean(recent_revenues)
                trend = cls._calculate_trend(recent_revenues)
                
                insights['revenue_forecast'] = {
                    'next_week_estimate': round(ma_forecast * (1 + trend), 2),
                    'confidence': 'medium',
                    'based_on_weeks': 4
                }
            
            # Risk indicators
            latest = data[-1] if data else None
            if latest:
                # High AR risk
                if float(latest.ar_over_45_days_percent or 0) > 15:
                    insights['risk_indicators'].append({
                        'type': 'ar_aging',
                        'severity': 'high',
                        'message': f'AR over 45 days at {latest.ar_over_45_days_percent}%'
                    })
                
                # Revenue concentration risk
                store_revenues = [
                    float(latest.revenue_3607 or 0),
                    float(latest.revenue_6800 or 0),
                    float(latest.revenue_728 or 0),
                    float(latest.revenue_8101 or 0)
                ]
                total = sum(store_revenues)
                if total > 0:
                    max_concentration = max(store_revenues) / total
                    # OLD - HARDCODED (WRONG): if max_concentration > 0.4:
                    # NEW - CONFIGURABLE (CORRECT):
                    concentration_threshold = config.get_threshold('revenue_concentration_risk_threshold')
                    if max_concentration > concentration_threshold:
                        insights['risk_indicators'].append({
                            'type': 'concentration',
                            'severity': 'medium',
                            'message': f'Revenue concentration at {max_concentration:.1%} in single store'
                        })
            
            # Opportunities
            # Check for underperforming stores
            for store_code, store_name in cls.STORE_MAPPING.items():
                revenue_field = f'revenue_{store_code}'
                recent_store_revenues = [
                    float(getattr(row, revenue_field, 0) or 0) 
                    for row in data[-4:]
                ]
                
                if recent_store_revenues:
                    trend = cls._calculate_trend(recent_store_revenues)
                    # OLD - HARDCODED (WRONG): if trend < -0.1:  # Declining more than 10%
                    # NEW - CONFIGURABLE (CORRECT):
                    declining_threshold = config.get_threshold('declining_trend_threshold')
                    if trend < declining_threshold:
                        insights['opportunities'].append({
                            'type': 'store_improvement',
                            'store': store_name,
                            'message': f'{store_name} showing declining trend ({trend:.1%})'
                        })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating predictive insights: {str(e)}")
            return {'error': str(e)}
    
    @classmethod
    def get_dashboard_metrics(cls) -> Dict:
        """Get key metrics for dashboard display"""
        try:
            # Get current week and previous week
            latest = db.session.query(ScorecardTrendsData).order_by(
                ScorecardTrendsData.week_ending.desc()
            ).first()
            
            if not latest:
                return {'error': 'No data available'}
            
            previous = db.session.query(ScorecardTrendsData).filter(
                ScorecardTrendsData.week_ending < latest.week_ending
            ).order_by(ScorecardTrendsData.week_ending.desc()).first()
            
            # Year-over-year comparison
            last_year = db.session.query(ScorecardTrendsData).filter(
                ScorecardTrendsData.week_ending <= latest.week_ending - timedelta(days=364),
                ScorecardTrendsData.week_ending >= latest.week_ending - timedelta(days=371)
            ).first()
            
            metrics = {
                'current_week': {
                    'date': latest.week_ending.strftime('%Y-%m-%d'),
                    'revenue': float(latest.total_weekly_revenue or 0),
                    'contracts': sum([
                        latest.new_contracts_3607 or 0,
                        latest.new_contracts_6800 or 0,
                        latest.new_contracts_728 or 0,
                        latest.new_contracts_8101 or 0
                    ]),
                    'ar_aging': float(latest.ar_over_45_days_percent or 0),
                    'pipeline': sum([
                        float(latest.reservation_next14_3607 or 0),
                        float(latest.reservation_next14_6800 or 0),
                        float(latest.reservation_next14_728 or 0),
                        float(latest.reservation_next14_8101 or 0)
                    ])
                },
                'changes': {},
                'yoy': {}
            }
            
            # Week-over-week changes
            if previous:
                prev_revenue = float(previous.total_weekly_revenue or 0)
                if prev_revenue > 0:
                    metrics['changes']['revenue'] = round(
                        ((metrics['current_week']['revenue'] - prev_revenue) / prev_revenue) * 100, 1
                    )
                
                prev_contracts = sum([
                    previous.new_contracts_3607 or 0,
                    previous.new_contracts_6800 or 0,
                    previous.new_contracts_728 or 0,
                    previous.new_contracts_8101 or 0
                ])
                if prev_contracts > 0:
                    metrics['changes']['contracts'] = round(
                        ((metrics['current_week']['contracts'] - prev_contracts) / prev_contracts) * 100, 1
                    )
            
            # Year-over-year comparison
            if last_year:
                ly_revenue = float(last_year.total_weekly_revenue or 0)
                if ly_revenue > 0:
                    metrics['yoy']['revenue'] = round(
                        ((metrics['current_week']['revenue'] - ly_revenue) / ly_revenue) * 100, 1
                    )
                    metrics['yoy']['revenue_amount'] = round(
                        metrics['current_week']['revenue'] - ly_revenue, 2
                    )
            
            # Store breakdown
            metrics['store_breakdown'] = []
            for store_code, store_name in cls.STORE_MAPPING.items():
                revenue = float(getattr(latest, f'revenue_{store_code}', 0) or 0)
                contracts = getattr(latest, f'new_contracts_{store_code}', 0) or 0
                
                metrics['store_breakdown'].append({
                    'store': store_name,
                    'revenue': revenue,
                    'contracts': contracts,
                    'revenue_share': round((revenue / metrics['current_week']['revenue'] * 100) 
                                         if metrics['current_week']['revenue'] > 0 else 0, 1)
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """Calculate simple linear trend"""
        if len(values) < 2:
            return 0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Simple linear regression
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]
        
        # Return as percentage change
        if values[0] != 0:
            return slope / values[0]
        return 0
    
    @staticmethod
    def _get_performance_tier(rank: int, total: int) -> str:
        """Determine performance tier based on ranking"""
        percentile = rank / total
        
        if percentile <= 0.25:
            return 'top'
        elif percentile <= 0.5:
            return 'high'
        elif percentile <= 0.75:
            return 'moderate'
        else:
            return 'low'
    
    def _get_config(self):
        """Get business analytics configuration with safe defaults"""
        try:
            config = BusinessAnalyticsConfiguration.query.filter_by(
                user_id='default_user', 
                config_name='default'
            ).first()
            
            if config:
                return config
                
            # Create a mock config object with default values if none exists
            class MockConfig:
                def __init__(self):
                    self.ar_aging_low_threshold = 5.0
                    self.ar_aging_medium_threshold = 15.0
                    self.revenue_concentration_risk_threshold = 0.4
                    self.declining_trend_threshold = -0.1
                
                def get_threshold(self, threshold_type: str):
                    return getattr(self, threshold_type, 5.0)
            
            return MockConfig()
                
        except Exception as e:
            logging.warning(f"Failed to load business analytics config: {e}. Using defaults.")
            # Create a mock config object with default values
            class MockConfig:
                def __init__(self):
                    self.ar_aging_low_threshold = 5.0
                    self.ar_aging_medium_threshold = 15.0
                    self.revenue_concentration_risk_threshold = 0.4
                    self.declining_trend_threshold = -0.1
                
                def get_threshold(self, threshold_type: str):
                    return getattr(self, threshold_type, 5.0)
            
            return MockConfig()