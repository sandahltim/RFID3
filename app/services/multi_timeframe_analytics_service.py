"""
Multi-Timeframe Analytics Service
Comprehensive business analytics with user-selectable timeframes and comparisons
NO HARDCODED VALUES - ALL CALCULATIONS FROM DATABASE
"""

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import text, func
from decimal import Decimal
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class TimeframeType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    THREE_WEEK_AVG_FORWARD = "3week_avg_forward"
    THREE_WEEK_AVG_PREVIOUS = "3week_avg_previous" 
    THREE_WEEK_TOTAL = "3week_total"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    YTD = "ytd"
    CUSTOM = "custom"

class ComparisonType(Enum):
    PREVIOUS_PERIOD = "previous_period"
    PREVIOUS_YEAR = "previous_year"
    MOVING_12_MONTH = "moving_12_month"
    MOVING_3_MONTH = "moving_3_month"
    CUSTOM_COMPARISON = "custom_comparison"

@dataclass
class TimeframePeriod:
    start_date: datetime
    end_date: datetime
    period_days: int
    business_hours_total: int  # Total business hours in period
    label: str

@dataclass 
class AnalyticsResult:
    current_value: float
    comparison_value: float
    change_percent: float
    period: TimeframePeriod
    comparison_period: TimeframePeriod

class MultiTimeframeAnalyticsService:
    """
    Comprehensive analytics service supporting multiple timeframes and comparisons
    """
    
    # Business constants
    ACTIVE_STORE_CODES = ['3607', '6800', '728', '8101']
    BUSINESS_HOURS_PER_DAY = 10  # 8am-6pm
    EXCLUDED_STORE_CODES = ['0', '000']
    
    def __init__(self):
        self.logger = logger
    
    def get_timeframe_dates(self, 
                           timeframe_type: Union[TimeframeType, str],
                           custom_start: Optional[datetime] = None,
                           custom_end: Optional[datetime] = None,
                           reference_date: Optional[datetime] = None) -> TimeframePeriod:
        """
        Calculate start and end dates for any timeframe type
        """
        if isinstance(timeframe_type, str):
            timeframe_type = TimeframeType(timeframe_type)
        
        ref_date = reference_date or datetime.now()
        
        if timeframe_type == TimeframeType.CUSTOM:
            if not custom_start or not custom_end:
                raise ValueError("Custom timeframe requires start and end dates")
            period_days = (custom_end - custom_start).days + 1
            return TimeframePeriod(
                start_date=custom_start,
                end_date=custom_end,
                period_days=period_days,
                business_hours_total=period_days * self.BUSINESS_HOURS_PER_DAY,
                label=f"Custom: {custom_start.strftime('%Y-%m-%d')} to {custom_end.strftime('%Y-%m-%d')}"
            )
        
        elif timeframe_type == TimeframeType.DAILY:
            start_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=1,
                business_hours_total=self.BUSINESS_HOURS_PER_DAY,
                label=f"Daily: {start_date.strftime('%Y-%m-%d')}"
            )
            
        elif timeframe_type == TimeframeType.WEEKLY:
            # Current week (Monday to Sunday)
            days_since_monday = ref_date.weekday()
            start_date = ref_date - timedelta(days=days_since_monday)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=7,
                business_hours_total=7 * self.BUSINESS_HOURS_PER_DAY,
                label=f"Weekly: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )
            
        elif timeframe_type == TimeframeType.THREE_WEEK_AVG_FORWARD:
            start_date = ref_date - timedelta(days=20)  # 3 weeks back
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = ref_date.replace(hour=23, minute=59, second=59)
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=21,
                business_hours_total=21 * self.BUSINESS_HOURS_PER_DAY,
                label=f"3-Week Forward Average: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )
            
        elif timeframe_type == TimeframeType.THREE_WEEK_AVG_PREVIOUS:
            end_date = ref_date - timedelta(days=1)  # Previous day
            start_date = end_date - timedelta(days=20)  # 3 weeks before that
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59)
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=21,
                business_hours_total=21 * self.BUSINESS_HOURS_PER_DAY,
                label=f"3-Week Previous Average: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )
            
        elif timeframe_type == TimeframeType.MONTHLY:
            start_date = ref_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start_date + relativedelta(months=1)
            end_date = next_month - timedelta(microseconds=1)
            period_days = (end_date - start_date).days + 1
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=period_days,
                business_hours_total=period_days * self.BUSINESS_HOURS_PER_DAY,
                label=f"Monthly: {start_date.strftime('%B %Y')}"
            )
            
        elif timeframe_type == TimeframeType.QUARTERLY:
            quarter = (ref_date.month - 1) // 3 + 1
            start_date = datetime(ref_date.year, (quarter - 1) * 3 + 1, 1)
            end_date = start_date + relativedelta(months=3) - timedelta(microseconds=1)
            period_days = (end_date - start_date).days + 1
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=period_days,
                business_hours_total=period_days * self.BUSINESS_HOURS_PER_DAY,
                label=f"Q{quarter} {ref_date.year}"
            )
            
        elif timeframe_type == TimeframeType.YEARLY:
            start_date = datetime(ref_date.year, 1, 1)
            end_date = datetime(ref_date.year, 12, 31, 23, 59, 59)
            period_days = (end_date - start_date).days + 1
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=period_days,
                business_hours_total=period_days * self.BUSINESS_HOURS_PER_DAY,
                label=f"Year {ref_date.year}"
            )
            
        elif timeframe_type == TimeframeType.YTD:
            start_date = datetime(ref_date.year, 1, 1)
            end_date = ref_date.replace(hour=23, minute=59, second=59)
            period_days = (end_date - start_date).days + 1
            return TimeframePeriod(
                start_date=start_date,
                end_date=end_date,
                period_days=period_days,
                business_hours_total=period_days * self.BUSINESS_HOURS_PER_DAY,
                label=f"YTD {ref_date.year}"
            )
        
        else:
            raise ValueError(f"Unsupported timeframe type: {timeframe_type}")
    
    def get_comparison_period(self, 
                             current_period: TimeframePeriod,
                             comparison_type: Union[ComparisonType, str]) -> TimeframePeriod:
        """
        Calculate comparison period dates based on current period and comparison type
        """
        if isinstance(comparison_type, str):
            comparison_type = ComparisonType(comparison_type)
        
        period_length = current_period.end_date - current_period.start_date
        
        if comparison_type == ComparisonType.PREVIOUS_PERIOD:
            comp_end = current_period.start_date - timedelta(microseconds=1)
            comp_start = comp_end - period_length
            return TimeframePeriod(
                start_date=comp_start,
                end_date=comp_end,
                period_days=current_period.period_days,
                business_hours_total=current_period.business_hours_total,
                label=f"Previous Period"
            )
        
        elif comparison_type == ComparisonType.PREVIOUS_YEAR:
            comp_start = current_period.start_date - relativedelta(years=1)
            comp_end = current_period.end_date - relativedelta(years=1)
            return TimeframePeriod(
                start_date=comp_start,
                end_date=comp_end,
                period_days=current_period.period_days,
                business_hours_total=current_period.business_hours_total,
                label=f"Same Period Previous Year"
            )
        
        elif comparison_type == ComparisonType.MOVING_12_MONTH:
            comp_start = current_period.start_date - relativedelta(months=12)
            comp_end = current_period.start_date - timedelta(microseconds=1)
            period_days = (comp_end - comp_start).days + 1
            return TimeframePeriod(
                start_date=comp_start,
                end_date=comp_end,
                period_days=period_days,
                business_hours_total=period_days * self.BUSINESS_HOURS_PER_DAY,
                label=f"Previous 12 Months"
            )
        
        elif comparison_type == ComparisonType.MOVING_3_MONTH:
            comp_start = current_period.start_date - relativedelta(months=3)
            comp_end = current_period.start_date - timedelta(microseconds=1)
            period_days = (comp_end - comp_start).days + 1
            return TimeframePeriod(
                start_date=comp_start,
                end_date=comp_end,
                period_days=period_days,
                business_hours_total=period_days * self.BUSINESS_HOURS_PER_DAY,
                label=f"Previous 3 Months"
            )
        
        else:
            raise ValueError(f"Unsupported comparison type: {comparison_type}")
    
    def calculate_revenue_metrics(self,
                                 timeframe_type: Union[TimeframeType, str],
                                 comparison_type: Union[ComparisonType, str] = ComparisonType.PREVIOUS_PERIOD,
                                 custom_start: Optional[datetime] = None,
                                 custom_end: Optional[datetime] = None) -> AnalyticsResult:
        """
        Calculate revenue metrics for any timeframe with comparison
        """
        try:
            session = db.session()
            
            # Get current period
            current_period = self.get_timeframe_dates(timeframe_type, custom_start, custom_end)
            comparison_period = self.get_comparison_period(current_period, comparison_type)
            
            # Revenue calculation query
            revenue_query = text("""
                SELECT 
                    SUM(CASE WHEN DATE(week_ending) BETWEEN :current_start AND :current_end 
                         THEN total_weekly_revenue ELSE 0 END) as current_revenue,
                    SUM(CASE WHEN DATE(week_ending) BETWEEN :comp_start AND :comp_end 
                         THEN total_weekly_revenue ELSE 0 END) as comparison_revenue
                FROM scorecard_trends_data
                WHERE total_weekly_revenue IS NOT NULL
                  AND (DATE(week_ending) BETWEEN :current_start AND :current_end
                       OR DATE(week_ending) BETWEEN :comp_start AND :comp_end)
            """)
            
            result = session.execute(revenue_query, {
                'current_start': current_period.start_date.date(),
                'current_end': current_period.end_date.date(),
                'comp_start': comparison_period.start_date.date(),
                'comp_end': comparison_period.end_date.date()
            }).fetchone()
            
            current_value = float(result.current_revenue or 0)
            comparison_value = float(result.comparison_revenue or 0)
            
            # Calculate percentage change
            change_percent = 0
            if comparison_value > 0:
                change_percent = ((current_value - comparison_value) / comparison_value) * 100
            
            return AnalyticsResult(
                current_value=current_value,
                comparison_value=comparison_value,
                change_percent=change_percent,
                period=current_period,
                comparison_period=comparison_period
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating revenue metrics: {e}", exc_info=True)
            raise
        finally:
            if 'session' in locals():
                session.close()
    
    def calculate_utilization_metrics(self,
                                    timeframe_type: Union[TimeframeType, str],
                                    comparison_type: Union[ComparisonType, str] = ComparisonType.PREVIOUS_PERIOD,
                                    custom_start: Optional[datetime] = None,
                                    custom_end: Optional[datetime] = None) -> AnalyticsResult:
        """
        Calculate equipment utilization: rental_hours / (available_hours - maintenance_hours)
        Business hours only: 8am-6pm = 10 hours/day
        """
        try:
            session = db.session()
            
            current_period = self.get_timeframe_dates(timeframe_type, custom_start, custom_end)
            comparison_period = self.get_comparison_period(current_period, comparison_type)
            
            # Utilization calculation query
            utilization_query = text("""
                WITH rental_hours AS (
                    SELECT 
                        SUM(CASE WHEN DATE(pt.contract_date) BETWEEN :current_start AND :current_end 
                            THEN LEAST(pti.hours * pti.qty, :business_hours_per_period) 
                            ELSE 0 END) as current_rental_hours,
                        SUM(CASE WHEN DATE(pt.contract_date) BETWEEN :comp_start AND :comp_end 
                            THEN LEAST(pti.hours * pti.qty, :business_hours_per_period)
                            ELSE 0 END) as comp_rental_hours
                    FROM pos_transaction_items pti
                    JOIN pos_transactions pt ON pti.contract_no = pt.contract_no
                    WHERE pti.store_code IN ('3607', '6800', '728', '8101')
                      AND pti.store_code NOT IN ('0', '000')
                      AND pti.hours IS NOT NULL
                      AND pti.hours > 0
                      AND (DATE(pt.contract_date) BETWEEN :current_start AND :current_end
                           OR DATE(pt.contract_date) BETWEEN :comp_start AND :comp_end)
                ),
                equipment_inventory AS (
                    SELECT 
                        COUNT(CASE WHEN status NOT IN ('maintenance') THEN 1 END) as available_equipment_count
                    FROM combined_inventory
                    WHERE store_code IN ('3607', '6800', '728', '8101')
                      AND store_code NOT IN ('0', '000')  
                      AND rental_rate > 0
                      AND (is_inactive IS NULL OR is_inactive = 0)
                )
                SELECT 
                    rh.current_rental_hours,
                    rh.comp_rental_hours,
                    ei.available_equipment_count,
                    (ei.available_equipment_count * :current_business_hours) as current_available_hours,
                    (ei.available_equipment_count * :comp_business_hours) as comp_available_hours
                FROM rental_hours rh
                CROSS JOIN equipment_inventory ei
            """)
            
            result = session.execute(utilization_query, {
                'current_start': current_period.start_date.date(),
                'current_end': current_period.end_date.date(),
                'comp_start': comparison_period.start_date.date(),
                'comp_end': comparison_period.end_date.date(),
                'business_hours_per_period': current_period.business_hours_total,
                'current_business_hours': current_period.business_hours_total,
                'comp_business_hours': comparison_period.business_hours_total
            }).fetchone()
            
            # Calculate utilization percentages
            current_utilization = 0
            if result.current_available_hours > 0:
                current_utilization = (result.current_rental_hours / result.current_available_hours) * 100
            
            comparison_utilization = 0
            if result.comp_available_hours > 0:
                comparison_utilization = (result.comp_rental_hours / result.comp_available_hours) * 100
            
            # Calculate change percentage
            change_percent = 0
            if comparison_utilization > 0:
                change_percent = ((current_utilization - comparison_utilization) / comparison_utilization) * 100
            
            return AnalyticsResult(
                current_value=current_utilization,
                comparison_value=comparison_utilization, 
                change_percent=change_percent,
                period=current_period,
                comparison_period=comparison_period
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating utilization metrics: {e}", exc_info=True)
            raise
        finally:
            if 'session' in locals():
                session.close()
    
    def calculate_yoy_growth_analysis(self,
                                    timeframe_type: Union[TimeframeType, str] = TimeframeType.MONTHLY,
                                    months_back: int = 12) -> Dict:
        """
        Calculate comprehensive YoY growth analysis with moving averages
        """
        try:
            session = db.session()
            
            # Get moving average growth over specified months
            yoy_query = text("""
                WITH monthly_revenue AS (
                    SELECT 
                        YEAR(week_ending) as year,
                        MONTH(week_ending) as month,
                        AVG(total_weekly_revenue) as avg_monthly_revenue
                    FROM scorecard_trends_data
                    WHERE total_weekly_revenue IS NOT NULL
                      AND week_ending >= DATE_SUB(CURDATE(), INTERVAL :months_back MONTH)
                    GROUP BY YEAR(week_ending), MONTH(week_ending)
                ),
                yoy_comparison AS (
                    SELECT 
                        current.year,
                        current.month,
                        current.avg_monthly_revenue as current_revenue,
                        previous.avg_monthly_revenue as previous_year_revenue,
                        CASE WHEN previous.avg_monthly_revenue > 0 
                             THEN ((current.avg_monthly_revenue - previous.avg_monthly_revenue) / previous.avg_monthly_revenue) * 100
                             ELSE NULL END as yoy_growth_pct
                    FROM monthly_revenue current
                    LEFT JOIN monthly_revenue previous 
                      ON current.month = previous.month 
                      AND current.year = previous.year + 1
                    WHERE previous.avg_monthly_revenue IS NOT NULL
                )
                SELECT 
                    AVG(yoy_growth_pct) as avg_yoy_growth,
                    COUNT(*) as months_analyzed,
                    MIN(yoy_growth_pct) as min_growth,
                    MAX(yoy_growth_pct) as max_growth,
                    STDDEV(yoy_growth_pct) as growth_volatility
                FROM yoy_comparison
                WHERE yoy_growth_pct IS NOT NULL
            """)
            
            result = session.execute(yoy_query, {'months_back': months_back}).fetchone()
            
            return {
                'avg_yoy_growth': float(result.avg_yoy_growth or 0),
                'months_analyzed': result.months_analyzed or 0,
                'min_growth': float(result.min_growth or 0),
                'max_growth': float(result.max_growth or 0),
                'growth_volatility': float(result.growth_volatility or 0),
                'analysis_period_months': months_back
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating YoY growth analysis: {e}", exc_info=True)
            raise
        finally:
            if 'session' in locals():
                session.close()
    
    def get_financial_kpis(self,
                          timeframe_type: str = "3week_avg_forward",
                          comparison_type: str = "previous_year") -> Dict:
        """
        Get comprehensive financial KPIs with user-selectable timeframes
        """
        try:
            # Calculate revenue metrics
            revenue_result = self.calculate_revenue_metrics(timeframe_type, comparison_type)
            
            # Calculate utilization metrics  
            utilization_result = self.calculate_utilization_metrics(timeframe_type, comparison_type)
            
            # Calculate YoY growth analysis (12-month and 3-month)
            yoy_12month = self.calculate_yoy_growth_analysis(TimeframeType.MONTHLY, 12)
            yoy_3month = self.calculate_yoy_growth_analysis(TimeframeType.MONTHLY, 3)
            
            # Calculate business health score (formula-based on real metrics)
            health_score = self._calculate_health_score(revenue_result, utilization_result, yoy_12month)
            
            return {
                "success": True,
                "timeframe": {
                    "type": timeframe_type,
                    "period": revenue_result.period.label,
                    "comparison": revenue_result.comparison_period.label
                },
                "revenue_metrics": {
                    "current_value": round(revenue_result.current_value, 2),
                    "comparison_value": round(revenue_result.comparison_value, 2),
                    "change_pct": round(revenue_result.change_percent, 1)
                },
                "utilization_metrics": {
                    "current_value": round(utilization_result.current_value, 1),
                    "comparison_value": round(utilization_result.comparison_value, 1),
                    "change_pct": round(utilization_result.change_percent, 1)
                },
                "yoy_analysis": {
                    "moving_12_month": yoy_12month,
                    "moving_3_month": yoy_3month
                },
                "operational_health": {
                    "health_score": health_score,
                    "factors": self._get_health_score_factors(revenue_result, utilization_result, yoy_12month)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting financial KPIs: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _calculate_health_score(self, revenue_result: AnalyticsResult, 
                               utilization_result: AnalyticsResult, 
                               yoy_analysis: Dict) -> int:
        """
        Calculate business health score based on multiple factors
        """
        score = 50  # Base score
        
        # Revenue performance factor (25 points max)
        if revenue_result.current_value > 100000:
            score += 25
        elif revenue_result.current_value > 75000:
            score += 20
        elif revenue_result.current_value > 50000:
            score += 15
        elif revenue_result.current_value > 25000:
            score += 10
        
        # Utilization factor (25 points max)
        if utilization_result.current_value > 80:
            score += 25
        elif utilization_result.current_value > 70:
            score += 20
        elif utilization_result.current_value > 60:
            score += 15
        elif utilization_result.current_value > 50:
            score += 10
        
        # YoY growth factor (25 points max)
        avg_yoy = yoy_analysis.get('avg_yoy_growth', 0)
        if avg_yoy > 10:
            score += 25
        elif avg_yoy > 5:
            score += 20
        elif avg_yoy > 0:
            score += 15
        elif avg_yoy > -5:
            score += 10
        elif avg_yoy > -10:
            score += 5
        
        # Trend consistency factor (bonus/penalty)
        volatility = yoy_analysis.get('growth_volatility', 0)
        if volatility < 5:  # Low volatility is good
            score += 5
        elif volatility > 20:  # High volatility is concerning
            score -= 5
        
        return max(0, min(100, score))
    
    def _get_health_score_factors(self, revenue_result: AnalyticsResult,
                                 utilization_result: AnalyticsResult,
                                 yoy_analysis: Dict) -> Dict:
        """
        Return detailed breakdown of health score factors
        """
        return {
            "revenue_factor": {
                "value": revenue_result.current_value,
                "change_pct": revenue_result.change_percent,
                "impact": "Strong" if revenue_result.current_value > 75000 else "Moderate" if revenue_result.current_value > 50000 else "Weak"
            },
            "utilization_factor": {
                "value": utilization_result.current_value,
                "change_pct": utilization_result.change_percent,
                "impact": "Strong" if utilization_result.current_value > 70 else "Moderate" if utilization_result.current_value > 50 else "Weak"
            },
            "growth_factor": {
                "avg_yoy_growth": yoy_analysis.get('avg_yoy_growth', 0),
                "volatility": yoy_analysis.get('growth_volatility', 0),
                "impact": "Strong" if yoy_analysis.get('avg_yoy_growth', 0) > 5 else "Declining" if yoy_analysis.get('avg_yoy_growth', 0) < 0 else "Stable"
            }
        }