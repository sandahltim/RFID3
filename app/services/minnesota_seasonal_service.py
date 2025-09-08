"""
Minnesota Seasonal Analytics Service
Analyzes Minnesota-specific seasonal patterns for rental equipment
Includes wedding season, graduation, construction cycles, and holiday patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, and_, or_, func
from app import db
from app.services.logger import get_logger
from app.models.weather_models import MinnesotaSeasonalPattern, WeatherData
from app.models.pos_models import POSTransaction, POSTransactionItem
import json
from decimal import Decimal
import calendar
from app.config.stores import (
    STORES, STORE_MAPPING, STORE_MANAGERS,
    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,
    get_store_name, get_store_manager, get_store_business_type,
    get_store_opening_date, get_active_store_codes
)


logger = get_logger(__name__)

class MinnesotaSeasonalService:
    """Service for analyzing Minnesota-specific seasonal patterns"""
    
    # Minnesota-specific seasonal events and patterns
    MINNESOTA_SEASONAL_EVENTS = {
        'wedding_season': {
            'peak_months': [5, 6, 7, 8, 9, 10],
            'super_peak': [6, 7, 8, 9],
            'description': 'Minnesota wedding season peaks in summer months',
            'equipment_focus': 'party_event',
            'weather_dependency': 'high',
            'booking_lead_time': 180  # days
        },
        'graduation_season': {
            'peak_months': [5, 6],
            'super_peak': [5, 6],
            'description': 'High school and college graduations',
            'equipment_focus': 'party_event',
            'weather_dependency': 'high',
            'booking_lead_time': 60
        },
        'construction_spring_rush': {
            'peak_months': [4, 5, 6],
            'super_peak': [5, 6],
            'description': 'Spring construction rush after winter thaw',
            'equipment_focus': 'construction_diy',
            'weather_dependency': 'very_high',
            'booking_lead_time': 14
        },
        'summer_construction_peak': {
            'peak_months': [6, 7, 8],
            'super_peak': [7, 8],
            'description': 'Peak construction season with optimal weather',
            'equipment_focus': 'construction_diy',
            'weather_dependency': 'medium',
            'booking_lead_time': 7
        },
        'fall_home_projects': {
            'peak_months': [9, 10],
            'super_peak': [9, 10],
            'description': 'Fall home improvement before winter',
            'equipment_focus': 'construction_diy',
            'weather_dependency': 'high',
            'booking_lead_time': 21
        },
        'landscaping_spring': {
            'peak_months': [4, 5, 6],
            'super_peak': [5, 6],
            'description': 'Spring landscaping and yard preparation',
            'equipment_focus': 'landscaping',
            'weather_dependency': 'very_high',
            'booking_lead_time': 10
        },
        'landscaping_summer': {
            'peak_months': [6, 7, 8],
            'super_peak': [7, 8],
            'description': 'Summer lawn and garden maintenance',
            'equipment_focus': 'landscaping',
            'weather_dependency': 'medium',
            'booking_lead_time': 3
        },
        'fall_cleanup': {
            'peak_months': [9, 10, 11],
            'super_peak': [10, 11],
            'description': 'Fall leaf cleanup and winter preparation',
            'equipment_focus': 'landscaping',
            'weather_dependency': 'medium',
            'booking_lead_time': 7
        },
        'holiday_events': {
            'peak_months': [11, 12],
            'super_peak': [11, 12],
            'description': 'Thanksgiving, Christmas, and New Year events',
            'equipment_focus': 'party_event',
            'weather_dependency': 'low',  # Mostly indoor
            'booking_lead_time': 90
        },
        'winter_indoor_projects': {
            'peak_months': [1, 2, 3, 12],
            'super_peak': [1, 2],
            'description': 'Indoor DIY projects during winter months',
            'equipment_focus': 'construction_diy',
            'weather_dependency': 'low',
            'booking_lead_time': 14
        },
        'state_fair': {
            'peak_months': [8],
            'super_peak': [8],
            'description': 'Minnesota State Fair - major regional event',
            'equipment_focus': 'party_event',
            'weather_dependency': 'medium',
            'booking_lead_time': 365  # Booked far in advance
        },
        'fishing_opener': {
            'peak_months': [5],
            'super_peak': [5],
            'description': 'Minnesota fishing opener weekend',
            'equipment_focus': 'party_event',
            'weather_dependency': 'high',
            'booking_lead_time': 45
        }
    }
    
    # Weather thresholds for different activities
    WEATHER_THRESHOLDS = {
        'outdoor_events': {
            'min_temperature': 60,  # F
            'max_wind_speed': 15,   # mph
            'max_precipitation': 0.1  # inches
        },
        'construction': {
            'min_temperature': 35,
            'max_wind_speed': 25,
            'max_precipitation': 0.3
        },
        'landscaping': {
            'min_temperature': 45,
            'max_wind_speed': 20,
            'max_precipitation': 0.5  # Light rain OK
        }
    }
    
    def __init__(self):
        self.logger = logger
    
    def analyze_seasonal_patterns(self, years_back: int = 3, 
                                store_code: str = None) -> Dict:
        """Comprehensive seasonal pattern analysis for Minnesota market"""
        try:
            end_date = date.today()
            start_date = date(end_date.year - years_back, 1, 1)
            
            self.logger.info(f"Analyzing seasonal patterns from {start_date} to {end_date}")
            
            # Get historical rental data with seasonal analysis
            seasonal_data = self._get_seasonal_rental_data(start_date, end_date, store_code)
            
            # Analyze each seasonal event pattern
            event_analysis = self._analyze_seasonal_events(seasonal_data)
            
            # Weather impact on seasonal patterns
            weather_seasonal_analysis = self._analyze_weather_seasonal_impact(start_date, end_date)
            
            # Industry-specific seasonal patterns
            industry_seasonal_patterns = self._analyze_industry_seasonal_patterns(seasonal_data)
            
            # Predict upcoming seasonal demand
            seasonal_forecast = self._generate_seasonal_forecast(seasonal_data, event_analysis)
            
            # Generate seasonal recommendations
            recommendations = self._generate_seasonal_recommendations(
                event_analysis, weather_seasonal_analysis, seasonal_forecast
            )
            
            results = {
                'analysis_period': f"{start_date} to {end_date}",
                'store_code': store_code,
                'seasonal_events': event_analysis,
                'weather_seasonal_impact': weather_seasonal_analysis,
                'industry_patterns': industry_seasonal_patterns,
                'seasonal_forecast': seasonal_forecast,
                'recommendations': recommendations,
                'minnesota_specific_insights': self._generate_minnesota_insights(event_analysis),
                'timestamp': datetime.now().isoformat()
            }
            
            # Store seasonal patterns in database
            self._store_seasonal_patterns(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Seasonal pattern analysis failed: {e}")
            return {'error': str(e)}
    
    def _get_seasonal_rental_data(self, start_date: date, end_date: date, 
                                store_code: str = None) -> pd.DataFrame:
        """Get rental data organized for seasonal analysis"""
        
        base_query = """
            SELECT 
                DATE(pt.contract_date) as rental_date,
                YEAR(pt.contract_date) as year,
                MONTH(pt.contract_date) as month,
                DAYOFYEAR(pt.contract_date) as day_of_year,
                WEEK(pt.contract_date) as week,
                pt.store_no,
                pt.contract_no,
                COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0) as contract_value,
                pti.item_num,
                pti.desc as item_description,
                pti.qty,
                COALESCE(pti.price, 0) as item_price,
                ec.industry_segment,
                ec.weather_dependent,
                ec.party_event_type,
                ec.construction_type,
                ec.landscaping_type
            FROM pos_transactions pt
            JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
            LEFT JOIN equipment_categorization ec ON pti.item_num = ec.item_num
            WHERE pt.contract_date BETWEEN :start_date AND :end_date
        """
        
        if store_code:
            base_query += " AND pt.store_no = :store_code"
        
        base_query += " ORDER BY pt.contract_date"
        
        params = {'start_date': start_date, 'end_date': end_date}
        if store_code:
            params['store_code'] = store_code
        
        query = text(base_query)
        df = pd.read_sql(query, db.engine, params=params)
        
        if df.empty:
            return pd.DataFrame()
        
        # Add derived seasonal features
        df['rental_date'] = pd.to_datetime(df['rental_date'])
        df['is_weekend'] = df['rental_date'].dt.dayofweek.isin([5, 6])
        df['season'] = df['month'].apply(self._get_season)
        df['month_name'] = df['month'].apply(lambda x: calendar.month_name[x])
        
        # Add Minnesota-specific seasonal markers
        df['is_wedding_season'] = df['month'].isin(self.MINNESOTA_SEASONAL_EVENTS['wedding_season']['peak_months'])
        df['is_construction_season'] = df['month'].isin([4, 5, 6, 7, 8, 9, 10])
        df['is_graduation_season'] = df['month'].isin([5, 6])
        df['is_winter_months'] = df['month'].isin([12, 1, 2, 3])
        
        return df
    
    def _analyze_seasonal_events(self, seasonal_data: pd.DataFrame) -> Dict:
        """Analyze each Minnesota seasonal event pattern"""
        if seasonal_data.empty:
            return {}
        
        event_analysis = {}
        
        for event_name, event_config in self.MINNESOTA_SEASONAL_EVENTS.items():
            try:
                # Filter data for this event's peak months
                event_months = event_config['peak_months']
                event_data = seasonal_data[seasonal_data['month'].isin(event_months)]
                
                if event_data.empty:
                    continue
                
                # Filter by equipment focus if specified
                equipment_focus = event_config['equipment_focus']
                if equipment_focus != 'mixed':
                    event_data = event_data[event_data['industry_segment'] == equipment_focus]
                
                if event_data.empty:
                    continue
                
                # Calculate event statistics
                total_revenue = event_data['contract_value'].sum()
                contract_count = event_data['contract_no'].nunique()
                avg_contract_value = event_data.groupby('contract_no')['contract_value'].first().mean()
                
                # Monthly breakdown
                monthly_stats = event_data.groupby(['month', 'year']).agg({
                    'contract_value': 'sum',
                    'contract_no': 'nunique',
                    'item_num': 'count'
                }).reset_index()
                
                # Calculate year-over-year growth
                yearly_stats = event_data.groupby('year').agg({
                    'contract_value': 'sum',
                    'contract_no': 'nunique'
                }).reset_index()
                
                yoy_growth = None
                if len(yearly_stats) >= 2:
                    latest_year = yearly_stats['contract_value'].iloc[-1]
                    previous_year = yearly_stats['contract_value'].iloc[-2]
                    yoy_growth = ((latest_year - previous_year) / previous_year * 100) if previous_year > 0 else 0
                
                # Peak timing analysis
                daily_stats = event_data.groupby(['month', 'rental_date']).agg({
                    'contract_value': 'sum'
                }).reset_index()
                
                peak_day = daily_stats.loc[daily_stats['contract_value'].idxmax()] if not daily_stats.empty else None
                
                # Weather dependency analysis
                weather_dependent_revenue = event_data[event_data['weather_dependent'] == True]['contract_value'].sum()
                weather_dependency_ratio = weather_dependent_revenue / total_revenue if total_revenue > 0 else 0
                
                event_analysis[event_name] = {
                    'event_config': event_config,
                    'performance_metrics': {
                        'total_revenue': float(total_revenue),
                        'contract_count': int(contract_count),
                        'avg_contract_value': float(avg_contract_value) if not pd.isna(avg_contract_value) else 0,
                        'revenue_per_month': float(total_revenue / len(event_months)) if event_months else 0
                    },
                    'trend_analysis': {
                        'year_over_year_growth': float(yoy_growth) if yoy_growth is not None else None,
                        'seasonal_consistency': self._calculate_seasonal_consistency(monthly_stats)
                    },
                    'timing_analysis': {
                        'peak_month': int(monthly_stats.loc[monthly_stats['contract_value'].idxmax(), 'month']) if not monthly_stats.empty else None,
                        'peak_day_info': {
                            'date': peak_day['rental_date'].strftime('%Y-%m-%d') if peak_day is not None else None,
                            'month': int(peak_day['month']) if peak_day is not None else None,
                            'revenue': float(peak_day['contract_value']) if peak_day is not None else 0
                        }
                    },
                    'weather_impact': {
                        'weather_dependency_ratio': round(weather_dependency_ratio, 3),
                        'weather_dependent_revenue': float(weather_dependent_revenue)
                    },
                    'equipment_analysis': self._analyze_event_equipment(event_data, equipment_focus)
                }
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze event {event_name}: {e}")
                continue
        
        return event_analysis
    
    def _analyze_weather_seasonal_impact(self, start_date: date, end_date: date) -> Dict:
        """Analyze how weather affects seasonal patterns"""
        try:
            # Get weather data for the analysis period
            weather_query = text("""
                SELECT 
                    observation_date,
                    MONTH(observation_date) as month,
                    temperature_high,
                    temperature_low,
                    precipitation,
                    wind_speed_avg,
                    weather_condition
                FROM weather_data 
                WHERE observation_date BETWEEN :start_date AND :end_date
                    AND is_forecast = FALSE
                    AND location_code = 'MSP'
                ORDER BY observation_date
            """)
            
            weather_df = pd.read_sql(weather_query, db.engine, params={
                'start_date': start_date,
                'end_date': end_date
            })
            
            if weather_df.empty:
                return {'error': 'No weather data available for seasonal analysis'}
            
            # Analyze weather patterns by month
            monthly_weather = weather_df.groupby('month').agg({
                'temperature_high': 'mean',
                'temperature_low': 'mean',
                'precipitation': ['sum', 'mean'],
                'wind_speed_avg': 'mean'
            }).round(2)
            
            # Flatten column names
            monthly_weather.columns = ['_'.join(col).strip() for col in monthly_weather.columns]
            monthly_weather = monthly_weather.reset_index()
            
            # Calculate weather favorability for each activity type
            weather_favorability = {}
            
            for month in range(1, 13):
                month_weather = monthly_weather[monthly_weather['month'] == month]
                if month_weather.empty:
                    continue
                
                month_data = month_weather.iloc[0]
                avg_temp = month_data['temperature_high_mean']
                avg_precip = month_data['precipitation_mean']
                avg_wind = month_data['wind_speed_avg_mean']
                
                # Calculate favorability scores for different activities
                outdoor_events_score = self._calculate_weather_favorability(
                    avg_temp, avg_precip, avg_wind, 'outdoor_events'
                )
                construction_score = self._calculate_weather_favorability(
                    avg_temp, avg_precip, avg_wind, 'construction'
                )
                landscaping_score = self._calculate_weather_favorability(
                    avg_temp, avg_precip, avg_wind, 'landscaping'
                )
                
                weather_favorability[month] = {
                    'month_name': calendar.month_name[month],
                    'avg_temperature': float(avg_temp),
                    'avg_precipitation': float(avg_precip),
                    'avg_wind_speed': float(avg_wind),
                    'activity_favorability': {
                        'outdoor_events': round(outdoor_events_score, 2),
                        'construction': round(construction_score, 2),
                        'landscaping': round(landscaping_score, 2)
                    }
                }
            
            # Identify optimal weather months for each activity
            optimal_months = {
                'outdoor_events': sorted(weather_favorability.keys(), 
                                       key=lambda m: weather_favorability[m]['activity_favorability']['outdoor_events'], 
                                       reverse=True)[:6],
                'construction': sorted(weather_favorability.keys(),
                                     key=lambda m: weather_favorability[m]['activity_favorability']['construction'],
                                     reverse=True)[:6],
                'landscaping': sorted(weather_favorability.keys(),
                                    key=lambda m: weather_favorability[m]['activity_favorability']['landscaping'],
                                    reverse=True)[:6]
            }
            
            return {
                'monthly_weather_patterns': weather_favorability,
                'optimal_weather_months': optimal_months,
                'weather_insights': self._generate_weather_seasonal_insights(weather_favorability, optimal_months)
            }
            
        except Exception as e:
            self.logger.error(f"Weather seasonal impact analysis failed: {e}")
            return {'error': str(e)}
    
    def _analyze_industry_seasonal_patterns(self, seasonal_data: pd.DataFrame) -> Dict:
        """Analyze seasonal patterns by industry segment"""
        if seasonal_data.empty:
            return {}
        
        industry_patterns = {}
        
        for industry in ['party_event', 'construction_diy', 'landscaping']:
            industry_data = seasonal_data[seasonal_data['industry_segment'] == industry]
            
            if industry_data.empty:
                continue
            
            # Monthly analysis
            monthly_stats = industry_data.groupby('month').agg({
                'contract_value': ['sum', 'mean', 'count'],
                'contract_no': 'nunique'
            }).reset_index()
            
            # Flatten columns
            monthly_stats.columns = ['month', 'total_revenue', 'avg_contract_value', 'item_count', 'contract_count']
            
            # Calculate seasonal indices (average month = 1.0)
            avg_monthly_revenue = monthly_stats['total_revenue'].mean()
            monthly_stats['seasonal_index'] = monthly_stats['total_revenue'] / avg_monthly_revenue
            
            # Identify peak and low seasons
            peak_months = monthly_stats.nlargest(3, 'seasonal_index')['month'].tolist()
            low_months = monthly_stats.nsmallest(3, 'seasonal_index')['month'].tolist()
            
            # Calculate seasonality strength (coefficient of variation)
            seasonality_strength = monthly_stats['seasonal_index'].std() / monthly_stats['seasonal_index'].mean()
            
            # Year-over-year analysis
            yearly_analysis = industry_data.groupby(['year', 'month']).agg({
                'contract_value': 'sum'
            }).reset_index()
            
            # Calculate growth trends
            growth_trends = {}
            for month in range(1, 13):
                month_data = yearly_analysis[yearly_analysis['month'] == month].sort_values('year')
                if len(month_data) >= 2:
                    revenues = month_data['contract_value'].tolist()
                    # Simple linear trend
                    years = list(range(len(revenues)))
                    trend = np.polyfit(years, revenues, 1)[0] if len(revenues) > 1 else 0
                    growth_trends[month] = float(trend)
            
            industry_patterns[industry] = {
                'monthly_stats': monthly_stats.to_dict('records'),
                'peak_season': {
                    'months': peak_months,
                    'month_names': [calendar.month_name[m] for m in peak_months],
                    'avg_seasonal_index': float(monthly_stats[monthly_stats['month'].isin(peak_months)]['seasonal_index'].mean())
                },
                'low_season': {
                    'months': low_months,
                    'month_names': [calendar.month_name[m] for m in low_months],
                    'avg_seasonal_index': float(monthly_stats[monthly_stats['month'].isin(low_months)]['seasonal_index'].mean())
                },
                'seasonality_metrics': {
                    'seasonality_strength': round(float(seasonality_strength), 3),
                    'peak_to_trough_ratio': float(monthly_stats['seasonal_index'].max() / monthly_stats['seasonal_index'].min()),
                    'coefficient_of_variation': round(float(monthly_stats['total_revenue'].std() / monthly_stats['total_revenue'].mean()), 3)
                },
                'growth_trends': growth_trends,
                'industry_insights': self._generate_industry_seasonal_insights(industry, monthly_stats, peak_months, low_months)
            }
        
        return industry_patterns
    
    def _generate_seasonal_forecast(self, seasonal_data: pd.DataFrame, 
                                  event_analysis: Dict) -> Dict:
        """Generate seasonal demand forecast for upcoming months"""
        if seasonal_data.empty:
            return {}
        
        current_date = date.today()
        forecast_months = []
        
        # Generate forecast for next 12 months
        for i in range(12):
            forecast_date = date(current_date.year, current_date.month, 1) + timedelta(days=32*i)
            forecast_date = forecast_date.replace(day=1)  # First of month
            forecast_months.append(forecast_date)
        
        forecasts = []
        
        for forecast_date in forecast_months:
            month = forecast_date.month
            year = forecast_date.year
            
            # Get historical data for this month
            historical_month_data = seasonal_data[seasonal_data['month'] == month]
            
            if historical_month_data.empty:
                # Use overall averages if no historical data for this month
                base_revenue = seasonal_data['contract_value'].mean()
                base_contracts = seasonal_data.groupby('rental_date')['contract_no'].nunique().mean()
            else:
                # Calculate base metrics from historical data
                monthly_totals = historical_month_data.groupby('year').agg({
                    'contract_value': 'sum',
                    'contract_no': 'nunique'
                })
                
                base_revenue = monthly_totals['contract_value'].mean()
                base_contracts = monthly_totals['contract_no'].mean()
            
            # Apply seasonal adjustments based on event analysis
            seasonal_multiplier = 1.0
            active_events = []
            
            for event_name, event_data in event_analysis.items():
                event_config = event_data['event_config']
                if month in event_config['peak_months']:
                    # Apply event boost
                    if month in event_config.get('super_peak', []):
                        event_multiplier = 1.4  # 40% boost for super peak
                    else:
                        event_multiplier = 1.2  # 20% boost for regular peak
                    
                    seasonal_multiplier *= event_multiplier
                    active_events.append(event_name)
            
            # Weather adjustment (simplified)
            weather_adjustment = self._get_weather_adjustment_for_month(month)
            
            # Apply year-over-year growth trend
            growth_factor = 1.05  # Assume 5% annual growth
            
            # Calculate final forecast
            predicted_revenue = base_revenue * seasonal_multiplier * weather_adjustment * growth_factor
            predicted_contracts = base_contracts * seasonal_multiplier * weather_adjustment * growth_factor
            
            # Confidence level based on historical data availability
            confidence = 0.8 if len(historical_month_data) > 50 else 0.6
            
            forecast_item = {
                'forecast_date': forecast_date.isoformat(),
                'month': month,
                'month_name': calendar.month_name[month],
                'year': year,
                'predicted_revenue': round(float(predicted_revenue), 2),
                'predicted_contracts': max(1, int(predicted_contracts)),
                'base_revenue': round(float(base_revenue), 2),
                'seasonal_multiplier': round(seasonal_multiplier, 2),
                'weather_adjustment': round(weather_adjustment, 2),
                'active_seasonal_events': active_events,
                'confidence_level': confidence,
                'factors_considered': {
                    'historical_data_points': len(historical_month_data),
                    'seasonal_events': len(active_events),
                    'weather_impact': weather_adjustment != 1.0
                }
            }
            
            forecasts.append(forecast_item)
        
        # Calculate forecast summary
        total_predicted_revenue = sum(f['predicted_revenue'] for f in forecasts)
        peak_forecast_month = max(forecasts, key=lambda x: x['predicted_revenue'])
        low_forecast_month = min(forecasts, key=lambda x: x['predicted_revenue'])
        
        return {
            'forecast_period': f"{forecasts[0]['forecast_date']} to {forecasts[-1]['forecast_date']}",
            'monthly_forecasts': forecasts,
            'forecast_summary': {
                'total_predicted_revenue': round(total_predicted_revenue, 2),
                'avg_monthly_revenue': round(total_predicted_revenue / 12, 2),
                'peak_month': peak_forecast_month['month_name'],
                'peak_revenue': peak_forecast_month['predicted_revenue'],
                'low_month': low_forecast_month['month_name'],
                'low_revenue': low_forecast_month['predicted_revenue'],
                'seasonal_variation': round((peak_forecast_month['predicted_revenue'] / low_forecast_month['predicted_revenue']), 2)
            }
        }
    
    def _generate_seasonal_recommendations(self, event_analysis: Dict, 
                                         weather_analysis: Dict, 
                                         seasonal_forecast: Dict) -> List[Dict]:
        """Generate actionable seasonal recommendations"""
        recommendations = []
        current_month = datetime.now().month
        
        # Event-specific recommendations
        for event_name, event_data in event_analysis.items():
            event_config = event_data['event_config']
            
            # Check if event is approaching
            upcoming_months = [(current_month + i - 1) % 12 + 1 for i in range(1, 4)]  # Next 3 months
            
            if any(month in event_config['peak_months'] for month in upcoming_months):
                lead_time = event_config['booking_lead_time']
                
                recommendation = {
                    'type': 'seasonal_preparation',
                    'event': event_name,
                    'priority': 'high' if event_config['equipment_focus'] == 'party_event' else 'medium',
                    'action': f"Prepare for {event_name} - ensure adequate {event_config['equipment_focus']} inventory",
                    'timing': f"Start preparation {lead_time} days in advance",
                    'expected_impact': 'high',
                    'details': {
                        'peak_months': event_config['peak_months'],
                        'equipment_focus': event_config['equipment_focus'],
                        'weather_dependency': event_config['weather_dependency']
                    }
                }
                recommendations.append(recommendation)
        
        # Weather-based recommendations
        if 'optimal_weather_months' in weather_analysis:
            optimal_months = weather_analysis['optimal_weather_months']
            
            # Outdoor event recommendations
            if current_month in optimal_months.get('outdoor_events', []):
                recommendations.append({
                    'type': 'weather_opportunity',
                    'priority': 'high',
                    'action': 'Capitalize on optimal outdoor event weather',
                    'timing': 'Current month',
                    'expected_impact': 'high',
                    'details': {'focus': 'party_event', 'reason': 'optimal_weather_conditions'}
                })
        
        # Inventory recommendations based on forecast
        if 'monthly_forecasts' in seasonal_forecast:
            upcoming_forecasts = seasonal_forecast['monthly_forecasts'][:3]  # Next 3 months
            
            for forecast in upcoming_forecasts:
                if forecast['seasonal_multiplier'] > 1.3:  # High demand expected
                    recommendations.append({
                        'type': 'inventory_scaling',
                        'priority': 'medium',
                        'action': f"Scale up inventory for {forecast['month_name']}",
                        'timing': f"Prepare by end of {calendar.month_name[max(1, forecast['month'] - 1)]}",
                        'expected_impact': 'medium',
                        'details': {
                            'predicted_revenue': forecast['predicted_revenue'],
                            'active_events': forecast['active_seasonal_events']
                        }
                    })
        
        # Year-round recommendations
        recommendations.extend([
            {
                'type': 'seasonal_planning',
                'priority': 'medium',
                'action': 'Develop seasonal inventory rotation plan',
                'timing': 'Quarterly review',
                'expected_impact': 'medium',
                'details': {'focus': 'all_segments'}
            },
            {
                'type': 'weather_monitoring',
                'priority': 'low',
                'action': 'Implement weather-based demand alerts',
                'timing': 'Ongoing',
                'expected_impact': 'low',
                'details': {'focus': 'weather_dependent_equipment'}
            }
        ])
        
        # Sort by priority and expected impact
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: (
            priority_order.get(x['priority'], 0),
            priority_order.get(x['expected_impact'], 0)
        ), reverse=True)
        
        return recommendations[:8]  # Return top 8 recommendations
    
    # Helper methods
    
    def _get_season(self, month: int) -> str:
        """Get season name from month"""
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
    
    def _calculate_seasonal_consistency(self, monthly_stats: pd.DataFrame) -> float:
        """Calculate how consistent seasonal patterns are year-over-year"""
        if len(monthly_stats) < 12:
            return 0.5  # Medium consistency for limited data
        
        # Calculate coefficient of variation for each month across years
        month_variations = []
        for month in range(1, 13):
            month_data = monthly_stats[monthly_stats['month'] == month]['contract_value']
            if len(month_data) > 1:
                cv = month_data.std() / month_data.mean() if month_data.mean() > 0 else 1.0
                month_variations.append(cv)
        
        if not month_variations:
            return 0.5
        
        # Lower variation = higher consistency
        avg_variation = np.mean(month_variations)
        consistency = max(0.0, 1.0 - avg_variation)  # Convert to 0-1 scale
        
        return round(consistency, 3)
    
    def _analyze_event_equipment(self, event_data: pd.DataFrame, equipment_focus: str) -> Dict:
        """Analyze equipment patterns for a specific event"""
        if event_data.empty:
            return {}
        
        # Top equipment items for this event
        equipment_stats = event_data.groupby(['item_num', 'item_description']).agg({
            'contract_value': 'sum',
            'qty': 'sum',
            'contract_no': 'nunique'
        }).sort_values('contract_value', ascending=False)
        
        top_equipment = equipment_stats.head(10).to_dict('index')
        
        # Equipment type breakdown if categorized
        if equipment_focus == 'party_event' and 'party_event_type' in event_data.columns:
            type_breakdown = event_data.groupby('party_event_type')['contract_value'].sum().to_dict()
        elif equipment_focus == 'construction_diy' and 'construction_type' in event_data.columns:
            type_breakdown = event_data.groupby('construction_type')['contract_value'].sum().to_dict()
        elif equipment_focus == 'landscaping' and 'landscaping_type' in event_data.columns:
            type_breakdown = event_data.groupby('landscaping_type')['contract_value'].sum().to_dict()
        else:
            type_breakdown = {}
        
        return {
            'top_equipment_items': {
                item_num: {
                    'item_description': list(top_equipment.keys())[i][1],
                    'total_revenue': float(stats['contract_value']),
                    'total_quantity': int(stats['qty']),
                    'contracts_used': int(stats['contract_no'])
                }
                for i, (item_num, stats) in enumerate(list(top_equipment.items())[:5])
            },
            'equipment_type_breakdown': {str(k): float(v) for k, v in type_breakdown.items() if k is not None}
        }
    
    def _calculate_weather_favorability(self, temperature: float, precipitation: float, 
                                      wind_speed: float, activity_type: str) -> float:
        """Calculate weather favorability score for an activity type"""
        thresholds = self.WEATHER_THRESHOLDS.get(activity_type, {})
        
        score = 1.0  # Start with perfect score
        
        # Temperature penalty
        min_temp = thresholds.get('min_temperature', 0)
        if temperature < min_temp:
            temp_penalty = (min_temp - temperature) / 50.0  # Scale penalty
            score -= min(0.6, temp_penalty)
        
        # Precipitation penalty
        max_precip = thresholds.get('max_precipitation', 1.0)
        if precipitation > max_precip:
            precip_penalty = (precipitation - max_precip) / 0.5  # Scale penalty
            score -= min(0.5, precip_penalty)
        
        # Wind penalty
        max_wind = thresholds.get('max_wind_speed', 30)
        if wind_speed > max_wind:
            wind_penalty = (wind_speed - max_wind) / 20.0  # Scale penalty
            score -= min(0.3, wind_penalty)
        
        return max(0.0, min(1.0, score))
    
    def _generate_weather_seasonal_insights(self, weather_favorability: Dict, 
                                          optimal_months: Dict) -> List[str]:
        """Generate insights from weather seasonal analysis"""
        insights = []
        
        # Find best overall month
        best_month = max(weather_favorability.keys(), 
                        key=lambda m: sum(weather_favorability[m]['activity_favorability'].values()))
        best_month_name = calendar.month_name[best_month]
        
        insights.append(f"{best_month_name} offers the best overall weather conditions for rental activities")
        
        # Outdoor event insights
        outdoor_optimal = optimal_months.get('outdoor_events', [])
        if outdoor_optimal:
            outdoor_months = [calendar.month_name[m] for m in outdoor_optimal[:3]]
            insights.append(f"Optimal outdoor event months: {', '.join(outdoor_months)}")
        
        # Construction insights
        construction_optimal = optimal_months.get('construction', [])
        if construction_optimal:
            construction_months = [calendar.month_name[m] for m in construction_optimal[:3]]
            insights.append(f"Best construction weather: {', '.join(construction_months)}")
        
        return insights[:3]
    
    def _generate_industry_seasonal_insights(self, industry: str, monthly_stats: pd.DataFrame,
                                           peak_months: List[int], low_months: List[int]) -> List[str]:
        """Generate industry-specific seasonal insights"""
        insights = []
        
        peak_month_names = [calendar.month_name[m] for m in peak_months]
        low_month_names = [calendar.month_name[m] for m in low_months]
        
        seasonality_strength = monthly_stats['seasonal_index'].std()
        
        if seasonality_strength > 0.5:
            insights.append(f"Strong seasonal pattern: peak in {', '.join(peak_month_names)}")
        
        if industry == 'party_event':
            insights.append("Wedding season drives peak demand from May through October")
        elif industry == 'construction_diy':
            insights.append("Construction activity peaks after winter thaw through fall")
        elif industry == 'landscaping':
            insights.append("Landscaping follows natural growing season patterns")
        
        # Low season insight
        insights.append(f"Plan for reduced demand in {', '.join(low_month_names)}")
        
        return insights[:3]
    
    def _get_weather_adjustment_for_month(self, month: int) -> float:
        """Get weather adjustment factor for a given month"""
        # Simplified weather adjustment based on Minnesota climate patterns
        weather_adjustments = {
            1: 0.7,   # January - harsh winter
            2: 0.7,   # February - harsh winter  
            3: 0.8,   # March - late winter
            4: 1.1,   # April - spring awakening
            5: 1.2,   # May - great weather begins
            6: 1.3,   # June - peak weather
            7: 1.3,   # July - peak weather
            8: 1.2,   # August - still great
            9: 1.1,   # September - nice fall
            10: 1.0,  # October - variable fall
            11: 0.8,  # November - cooling down
            12: 0.7   # December - winter sets in
        }
        
        return weather_adjustments.get(month, 1.0)
    
    def _generate_minnesota_insights(self, event_analysis: Dict) -> List[str]:
        """Generate Minnesota-specific insights"""
        insights = []
        
        # Wedding season insight
        if 'wedding_season' in event_analysis:
            wedding_data = event_analysis['wedding_season']
            wedding_revenue = wedding_data['performance_metrics']['total_revenue']
            insights.append(f"Minnesota wedding season generates ${wedding_revenue:,.0f} in rental revenue")
        
        # Winter impact insight
        winter_events = [name for name, data in event_analysis.items() 
                        if any(month in [12, 1, 2] for month in data['event_config']['peak_months'])]
        if winter_events:
            insights.append(f"Winter indoor activities include: {', '.join(winter_events)}")
        
        # State fair insight
        if 'state_fair' in event_analysis:
            insights.append("Minnesota State Fair creates significant August rental demand")
        
        # Construction seasonality
        construction_events = [name for name, data in event_analysis.items() 
                             if data['event_config']['equipment_focus'] == 'construction_diy']
        if len(construction_events) >= 3:
            insights.append("Construction rentals show strong seasonal patterns tied to Minnesota weather")
        
        return insights[:4]
    
    def _store_seasonal_patterns(self, results: Dict) -> bool:
        """Store seasonal pattern analysis in database"""
        try:
            analysis_date = date.today()
            
            # Store each seasonal event pattern
            for event_name, event_data in results.get('seasonal_events', {}).items():
                event_config = event_data['event_config']
                performance = event_data['performance_metrics']
                
                existing = db.session.query(MinnesotaSeasonalPattern).filter(
                    and_(
                        MinnesotaSeasonalPattern.pattern_type == event_name,
                        MinnesotaSeasonalPattern.industry_segment == event_config['equipment_focus']
                    )
                ).first()
                
                if existing:
                    # Update existing pattern
                    existing.demand_multiplier = Decimal(str(performance['revenue_per_month'] / 1000))  # Normalize
                    existing.weather_sensitivity = Decimal(str(event_data['weather_impact']['weather_dependency_ratio']))
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    # Create new pattern
                    new_pattern = MinnesotaSeasonalPattern(
                        pattern_type=event_name,
                        industry_segment=event_config['equipment_focus'],
                        season=self._get_season(event_config['peak_months'][0]) if event_config['peak_months'] else 'Unknown',
                        demand_multiplier=Decimal(str(min(9.99, performance['revenue_per_month'] / 1000))),  # Cap at 9.99
                        weather_sensitivity=Decimal(str(event_data['weather_impact']['weather_dependency_ratio'])),
                        lead_time_days=event_config['booking_lead_time'],
                        event_type=event_name,
                        description=event_config['description']
                    )
                    db.session.add(new_pattern)
            
            db.session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store seasonal patterns: {e}")
            db.session.rollback()
            return False