"""
Minnesota Weather Service
Integrates with National Weather Service API for Twin Cities metro area weather data
Optimized for Minnesota rental equipment business weather patterns
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, and_
from app import db
from app.services.logger import get_logger
from app.models.weather_models import (
    WeatherData, MinnesotaSeasonalPattern, 
    WeatherRentalCorrelation, WeatherForecastDemand
)
import json
import time
from decimal import Decimal

logger = get_logger(__name__)

class MinnesotaWeatherService:
    """Service for fetching and analyzing Minnesota weather data"""
    
    # Minnesota locations for weather monitoring
    MINNESOTA_LOCATIONS = {
        'MSP': {
            'name': 'Minneapolis-St. Paul International Airport',
            'nws_code': 'KMSP',
            'lat': 44.8848,
            'lon': -93.2223,
            'serves_stores': ['3607', '6800', '728', '8101']  # All stores
        },
        'WAYZATA': {
            'name': 'Wayzata Area',
            'lat': 44.9733,
            'lon': -93.5066,
            'serves_stores': ['3607']
        },
        'BROOKLYN_PARK': {
            'name': 'Brooklyn Park Area', 
            'lat': 45.0941,
            'lon': -93.3563,
            'serves_stores': ['6800']
        },
        'FRIDLEY': {
            'name': 'Fridley Area',
            'lat': 45.0863,
            'lon': -93.2636,
            'serves_stores': ['8101']  # CORRECTED - 8101 is Fridley not Elk River
        },
        'ELK_RIVER': {
            'name': 'Elk River Area',
            'lat': 45.3038,
            'lon': -93.5677,
            'serves_stores': ['728']   # CORRECTED - 728 is Elk River not Fridley
        }
    }
    
    # National Weather Service API endpoints
    NWS_BASE_URL = "https://api.weather.gov"
    
    # Equipment weather sensitivity mappings
    WEATHER_SENSITIVITY = {
        'party_event': {
            'temperature_critical': True,
            'precipitation_critical': True,
            'wind_sensitive': True,
            'ideal_temp_range': (65, 85),
            'rain_cancellation_threshold': 0.1  # inches
        },
        'construction_diy': {
            'temperature_critical': True,
            'precipitation_critical': True,
            'wind_sensitive': False,
            'ideal_temp_range': (40, 90),
            'rain_cancellation_threshold': 0.25
        },
        'landscaping': {
            'temperature_critical': True,
            'precipitation_critical': False,  # Actually benefits from recent rain
            'wind_sensitive': False,
            'ideal_temp_range': (45, 85),
            'rain_cancellation_threshold': 0.5
        }
    }
    
    def __init__(self):
        self.logger = logger
        self.session = requests.Session()
        # Add user agent for NWS API compliance
        self.session.headers.update({
            'User-Agent': 'RFID-Inventory-System/1.0 (contact@yourcompany.com)'
        })
    
    def get_nws_forecast_office(self, lat: float, lon: float) -> str:
        """Get the NWS forecast office for given coordinates"""
        try:
            url = f"{self.NWS_BASE_URL}/points/{lat},{lon}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data['properties']['cwa']  # County Warning Area
            
        except Exception as e:
            self.logger.warning(f"Failed to get forecast office for {lat},{lon}: {e}")
            return "MPX"  # Default to Twin Cities office
    
    def fetch_current_weather(self, location_code: str) -> Optional[Dict]:
        """Fetch current weather conditions from NWS"""
        if location_code not in self.MINNESOTA_LOCATIONS:
            self.logger.error(f"Unknown location code: {location_code}")
            return None
        
        location = self.MINNESOTA_LOCATIONS[location_code]
        
        try:
            # Get the station information
            lat, lon = location['lat'], location['lon']
            points_url = f"{self.NWS_BASE_URL}/points/{lat},{lon}"
            
            self.logger.info(f"Fetching weather for {location['name']} ({lat}, {lon})")
            
            # First get the station/grid info
            response = self.session.get(points_url, timeout=15)
            response.raise_for_status()
            points_data = response.json()
            
            # Get current conditions from the observation station
            stations_url = points_data['properties']['observationStations']
            stations_response = self.session.get(stations_url, timeout=10)
            stations_response.raise_for_status()
            
            stations_data = stations_response.json()
            if not stations_data['features']:
                raise Exception("No weather stations found")
            
            # Use the first available station
            station_url = stations_data['features'][0]['id']
            observations_url = f"{station_url}/observations/latest"
            
            obs_response = self.session.get(observations_url, timeout=10)
            obs_response.raise_for_status()
            obs_data = obs_response.json()
            
            # Parse the observation data
            properties = obs_data['properties']
            
            weather_data = {
                'location_code': location_code,
                'location_name': location['name'],
                'observation_time': properties.get('timestamp'),
                'temperature': self._celsius_to_fahrenheit(properties.get('temperature', {}).get('value')),
                'humidity': properties.get('relativeHumidity', {}).get('value'),
                'wind_speed': self._ms_to_mph(properties.get('windSpeed', {}).get('value')),
                'wind_direction': properties.get('windDirection', {}).get('value'),
                'barometric_pressure': properties.get('barometricPressure', {}).get('value'),
                'visibility': properties.get('visibility', {}).get('value'),
                'weather_description': properties.get('textDescription', ''),
                'cloud_cover': properties.get('cloudLayers', [{}])[0].get('amount') if properties.get('cloudLayers') else None
            }
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch current weather for {location_code}: {e}")
            return None
    
    def fetch_forecast_data(self, location_code: str, days_ahead: int = 7) -> List[Dict]:
        """Fetch weather forecast data from NWS"""
        if location_code not in self.MINNESOTA_LOCATIONS:
            return []
        
        location = self.MINNESOTA_LOCATIONS[location_code]
        
        try:
            lat, lon = location['lat'], location['lon']
            points_url = f"{self.NWS_BASE_URL}/points/{lat},{lon}"
            
            response = self.session.get(points_url, timeout=15)
            response.raise_for_status()
            points_data = response.json()
            
            # Get forecast data
            forecast_url = points_data['properties']['forecast']
            forecast_response = self.session.get(forecast_url, timeout=15)
            forecast_response.raise_for_status()
            
            forecast_data = forecast_response.json()
            forecast_periods = forecast_data['properties']['periods']
            
            forecasts = []
            for i, period in enumerate(forecast_periods[:days_ahead * 2]):  # 2 periods per day (day/night)
                if period['isDaytime']:
                    forecast_date = datetime.fromisoformat(period['startTime'].replace('Z', '+00:00')).date()
                    
                    # Find corresponding night period for low temperature
                    night_temp = None
                    if i + 1 < len(forecast_periods):
                        night_period = forecast_periods[i + 1]
                        if not night_period['isDaytime']:
                            night_temp = night_period['temperature']
                    
                    forecast_item = {
                        'location_code': location_code,
                        'location_name': location['name'],
                        'forecast_date': forecast_date,
                        'temperature_high': period['temperature'],
                        'temperature_low': night_temp,
                        'weather_condition': period['shortForecast'],
                        'detailed_forecast': period['detailedForecast'],
                        'precipitation_probability': period.get('probabilityOfPrecipitation', {}).get('value'),
                        'wind_speed': period['windSpeed'],
                        'wind_direction': period['windDirection'],
                        'days_ahead': (forecast_date - date.today()).days
                    }
                    
                    forecasts.append(forecast_item)
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Failed to fetch forecast for {location_code}: {e}")
            return []
    
    def store_weather_data(self, weather_data: Dict, is_forecast: bool = False) -> bool:
        """Store weather data in database"""
        try:
            # Create or update weather record
            existing = db.session.query(WeatherData).filter(
                and_(
                    WeatherData.observation_date == weather_data.get('observation_date', date.today()),
                    WeatherData.location_code == weather_data['location_code'],
                    WeatherData.data_source == 'NWS',
                    WeatherData.is_forecast == is_forecast
                )
            ).first()
            
            if existing:
                # Update existing record
                for key, value in weather_data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # Create new record
                weather_record = WeatherData(
                    observation_date=weather_data.get('observation_date', date.today()),
                    location_code=weather_data['location_code'],
                    location_name=weather_data.get('location_name'),
                    data_source='NWS',
                    is_forecast=is_forecast,
                    **{k: v for k, v in weather_data.items() 
                       if k not in ['location_code', 'location_name', 'observation_date'] and v is not None}
                )
                db.session.add(weather_record)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to store weather data: {e}")
            return False
    
    def update_all_locations(self) -> Dict[str, bool]:
        """Update weather data for all Minnesota locations"""
        results = {}
        
        for location_code in self.MINNESOTA_LOCATIONS.keys():
            self.logger.info(f"Updating weather data for {location_code}")
            
            # Fetch current weather
            current_weather = self.fetch_current_weather(location_code)
            if current_weather:
                current_success = self.store_weather_data(current_weather, is_forecast=False)
                results[f"{location_code}_current"] = current_success
            
            # Fetch forecast data
            forecast_data = self.fetch_forecast_data(location_code, days_ahead=7)
            forecast_success = True
            
            for forecast in forecast_data:
                forecast['observation_date'] = forecast['forecast_date']
                forecast['forecast_days_ahead'] = forecast['days_ahead']
                if not self.store_weather_data(forecast, is_forecast=True):
                    forecast_success = False
            
            results[f"{location_code}_forecast"] = forecast_success
            
            # Rate limiting - be nice to NWS API
            time.sleep(1)
        
        return results
    
    def calculate_weather_impact_score(self, weather_data: Dict, industry_segment: str) -> float:
        """Calculate weather impact score for rental demand (0.0 to 1.0)"""
        if industry_segment not in self.WEATHER_SENSITIVITY:
            return 0.5  # Neutral impact for unknown segments
        
        sensitivity = self.WEATHER_SENSITIVITY[industry_segment]
        score = 1.0  # Start with perfect conditions
        
        # Temperature impact
        temp = weather_data.get('temperature_high') or weather_data.get('temperature')
        if temp is not None and sensitivity['temperature_critical']:
            ideal_min, ideal_max = sensitivity['ideal_temp_range']
            if temp < ideal_min:
                # Too cold - reduce score based on how far below ideal
                temp_penalty = min(0.5, (ideal_min - temp) / 40.0)  # Max 50% penalty
                score -= temp_penalty
            elif temp > ideal_max:
                # Too hot - reduce score based on how far above ideal  
                temp_penalty = min(0.3, (temp - ideal_max) / 20.0)  # Max 30% penalty
                score -= temp_penalty
        
        # Precipitation impact
        precipitation = weather_data.get('precipitation', 0) or 0
        if precipitation > sensitivity['rain_cancellation_threshold']:
            if industry_segment == 'landscaping':
                # Landscaping benefits from recent rain
                score += min(0.2, precipitation * 0.1)
            else:
                # Other segments penalized by rain
                rain_penalty = min(0.6, precipitation * 2.0)  # Heavy rain = major penalty
                score -= rain_penalty
        
        # Wind impact (primarily affects party/event equipment)
        wind_speed = weather_data.get('wind_speed_max') or weather_data.get('wind_speed_avg', 0)
        if wind_speed and sensitivity['wind_sensitive'] and wind_speed > 15:  # 15+ mph winds
            wind_penalty = min(0.4, (wind_speed - 15) / 25.0)  # Max 40% penalty
            score -= wind_penalty
        
        return max(0.0, min(1.0, score))  # Clamp between 0.0 and 1.0
    
    def analyze_historical_correlations(self, store_code: str = None, 
                                      industry_segment: str = 'mixed',
                                      days_back: int = 365) -> Dict:
        """Analyze historical correlations between weather and rental demand"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Get weather data
            weather_query = text("""
                SELECT 
                    observation_date,
                    location_code,
                    temperature_high,
                    temperature_low,
                    temperature_avg,
                    precipitation,
                    wind_speed_avg,
                    weather_condition
                FROM weather_data 
                WHERE observation_date BETWEEN :start_date AND :end_date
                    AND is_forecast = FALSE
                ORDER BY observation_date
            """)
            
            weather_df = pd.read_sql(weather_query, db.engine, params={
                'start_date': start_date,
                'end_date': end_date
            })
            
            if weather_df.empty:
                return {'error': 'No weather data available for analysis'}
            
            # Get rental/business data 
            business_query = text("""
                SELECT 
                    DATE(contract_date) as rental_date,
                    store_no as store_code,
                    SUM(rent_amt + sale_amt) as daily_revenue,
                    COUNT(*) as daily_contracts
                FROM pos_transactions 
                WHERE contract_date BETWEEN :start_date AND :end_date
            """)
            
            if store_code:
                business_query = text(str(business_query) + " AND store_no = :store_code")
            
            business_query = text(str(business_query) + " GROUP BY DATE(contract_date), store_no ORDER BY rental_date")
            
            params = {'start_date': start_date, 'end_date': end_date}
            if store_code:
                params['store_code'] = store_code
            
            business_df = pd.read_sql(business_query, db.engine, params=params)
            
            if business_df.empty:
                return {'error': 'No business data available for analysis'}
            
            # Merge weather and business data
            weather_df['observation_date'] = pd.to_datetime(weather_df['observation_date'])
            business_df['rental_date'] = pd.to_datetime(business_df['rental_date'])
            
            # For simplicity, use MSP weather for all stores initially
            main_weather = weather_df[weather_df['location_code'] == 'MSP'].copy()
            
            merged_df = pd.merge(
                business_df,
                main_weather,
                left_on='rental_date',
                right_on='observation_date',
                how='inner'
            )
            
            if len(merged_df) < 30:  # Need minimum data points
                return {'error': 'Insufficient data points for reliable correlation analysis'}
            
            # Calculate correlations
            correlations = {}
            weather_factors = ['temperature_high', 'temperature_low', 'precipitation', 'wind_speed_avg']
            business_metrics = ['daily_revenue', 'daily_contracts']
            
            for weather_factor in weather_factors:
                if weather_factor in merged_df.columns:
                    weather_values = merged_df[weather_factor].dropna()
                    if len(weather_values) > 10:  # Minimum threshold
                        correlations[weather_factor] = {}
                        
                        for business_metric in business_metrics:
                            if business_metric in merged_df.columns:
                                business_values = merged_df[business_metric]
                                
                                # Align data
                                combined = pd.DataFrame({
                                    'weather': weather_values,
                                    'business': business_values
                                }).dropna()
                                
                                if len(combined) >= 10:
                                    correlation = combined['weather'].corr(combined['business'])
                                    correlations[weather_factor][business_metric] = {
                                        'correlation': float(correlation) if not pd.isna(correlation) else 0.0,
                                        'data_points': len(combined),
                                        'strength': self._classify_correlation_strength(correlation)
                                    }
            
            return {
                'status': 'success',
                'store_code': store_code,
                'industry_segment': industry_segment,
                'analysis_period': f"{start_date} to {end_date}",
                'data_points': len(merged_df),
                'correlations': correlations,
                'insights': self._generate_correlation_insights(correlations)
            }
            
        except Exception as e:
            self.logger.error(f"Historical correlation analysis failed: {e}")
            return {'error': str(e)}
    
    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength"""
        if pd.isna(correlation):
            return 'none'
        
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            return 'very_strong'
        elif abs_corr >= 0.6:
            return 'strong'
        elif abs_corr >= 0.4:
            return 'moderate'
        elif abs_corr >= 0.2:
            return 'weak'
        else:
            return 'very_weak'
    
    def _generate_correlation_insights(self, correlations: Dict) -> List[str]:
        """Generate business insights from correlation analysis"""
        insights = []
        
        for weather_factor, metrics in correlations.items():
            for metric, stats in metrics.items():
                corr = stats['correlation']
                strength = stats['strength']
                
                if strength in ['strong', 'very_strong']:
                    direction = 'increases' if corr > 0 else 'decreases'
                    factor_name = weather_factor.replace('_', ' ').title()
                    metric_name = metric.replace('_', ' ').title()
                    
                    insight = f"{factor_name} strongly {direction} {metric_name} (r={corr:.2f})"
                    insights.append(insight)
        
        if not insights:
            insights.append("No strong weather correlations found in the analyzed period")
        
        return insights
    
    def _celsius_to_fahrenheit(self, celsius: float) -> Optional[float]:
        """Convert Celsius to Fahrenheit"""
        if celsius is None:
            return None
        return round((celsius * 9/5) + 32, 1)
    
    def _ms_to_mph(self, ms: float) -> Optional[float]:
        """Convert meters per second to miles per hour"""
        if ms is None:
            return None
        return round(ms * 2.237, 1)

    def get_weather_summary_for_date_range(self, start_date: date, end_date: date, 
                                         location_code: str = 'MSP') -> Dict:
        """Get weather summary for a date range"""
        try:
            query = text("""
                SELECT 
                    observation_date,
                    temperature_high,
                    temperature_low,
                    precipitation,
                    weather_condition
                FROM weather_data 
                WHERE observation_date BETWEEN :start_date AND :end_date
                    AND location_code = :location_code
                    AND is_forecast = FALSE
                ORDER BY observation_date
            """)
            
            df = pd.read_sql(query, db.engine, params={
                'start_date': start_date,
                'end_date': end_date,
                'location_code': location_code
            })
            
            if df.empty:
                return {'error': 'No weather data found for specified date range'}
            
            summary = {
                'date_range': f"{start_date} to {end_date}",
                'location': location_code,
                'total_days': len(df),
                'avg_high_temp': float(df['temperature_high'].mean()) if df['temperature_high'].notna().any() else None,
                'avg_low_temp': float(df['temperature_low'].mean()) if df['temperature_low'].notna().any() else None,
                'total_precipitation': float(df['precipitation'].sum()) if df['precipitation'].notna().any() else 0,
                'rainy_days': len(df[df['precipitation'] > 0.1]),
                'most_common_condition': df['weather_condition'].mode().iloc[0] if not df['weather_condition'].empty else None
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get weather summary: {e}")
            return {'error': str(e)}