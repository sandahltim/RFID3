"""
Weather Data Tool for Minnesota Equipment Rental AI Agent
Integrates with NOAA and OpenWeatherMap APIs for weather-based business insights
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta, timezone
import json
import asyncio
import aiohttp
from dataclasses import dataclass
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather data structure"""
    timestamp: datetime
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    conditions: str
    visibility: float
    pressure: float
    source: str


@dataclass
class WeatherForecast:
    """Weather forecast structure"""
    date: datetime
    high_temp: float
    low_temp: float
    precipitation_chance: float
    conditions: str
    wind_speed: float


class WeatherQueryInput(BaseModel):
    """Input schema for weather queries"""
    query_type: str = Field(
        description="Type of query: 'current', 'forecast', 'historical', 'analysis'"
    )
    location: str = Field(
        default="Minnesota", description="Location for weather data"
    )
    days: int = Field(
        default=7, description="Number of days for forecast or historical data"
    )
    analysis_type: Optional[str] = Field(
        description="Type of weather analysis: 'equipment_demand', 'seasonal_trends'"
    )


class WeatherTool(BaseTool):
    """
    LangChain tool for weather data analysis and business correlation
    
    Provides weather insights for equipment rental demand prediction:
    - Current conditions affecting equipment needs
    - Weather forecasts for demand planning  
    - Historical weather correlation with rental patterns
    - Seasonal analysis for inventory positioning
    """
    
    name = "weather_data"
    description = """
    Get weather data and analysis for Minnesota equipment rental business planning.
    
    Use this tool for:
    - Current weather conditions affecting equipment demand
    - Weather forecasts for rental planning (construction delays, event cancellations)
    - Historical weather patterns and rental correlations
    - Seasonal equipment demand predictions
    - Weather impact analysis on specific equipment categories
    
    Minnesota locations covered:
    - Twin Cities Metro (Minneapolis/St. Paul)
    - Wayzata, Brooklyn Park, Fridley, Elk River store locations
    - State-wide construction and event planning
    """
    
    def __init__(
        self, 
        openweather_api_key: Optional[str] = None,
        noaa_api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.openweather_api_key = openweather_api_key
        self.noaa_api_key = noaa_api_key
        self.base_openweather_url = "https://api.openweathermap.org/data/2.5"
        self.base_noaa_url = "https://api.weather.gov"
        
        # Minnesota coordinates for store locations
        self.locations = {
            'wayzata': {'lat': 44.9733, 'lon': -93.5066},
            'brooklyn_park': {'lat': 45.0941, 'lon': -93.3563},
            'fridley': {'lat': 45.0861, 'lon': -93.2633},
            'elk_river': {'lat': 45.3033, 'lon': -93.5678},
            'minneapolis': {'lat': 44.9778, 'lon': -93.2650},
            'saint_paul': {'lat': 44.9537, 'lon': -93.0900},
            'minnesota': {'lat': 46.7296, 'lon': -94.6859}  # State center
        }
        
        # Weather impact patterns for equipment categories
        self.weather_impacts = {
            'construction': {
                'rain_threshold': 0.1,  # inches
                'temperature_min': 35,  # Fahrenheit
                'wind_max': 25,  # mph
                'conditions_avoid': ['thunderstorm', 'snow', 'ice']
            },
            'outdoor_events': {
                'rain_threshold': 0.05,
                'temperature_range': (50, 85),
                'wind_max': 15,
                'conditions_avoid': ['rain', 'snow', 'thunderstorm']
            },
            'landscaping': {
                'rain_threshold': 0.2,
                'temperature_min': 40,
                'wind_max': 30,
                'conditions_prefer': ['clear', 'partly_cloudy']
            }
        }
    
    def _run(self, query_input: str) -> str:
        """Execute weather query"""
        try:
            # Parse input
            if isinstance(query_input, str):
                try:
                    input_data = json.loads(query_input)
                except json.JSONDecodeError:
                    # Treat as simple location query
                    input_data = {
                        'query_type': 'current',
                        'location': query_input
                    }
            else:
                input_data = query_input
            
            query_params = WeatherQueryInput(**input_data)
            
            # Route to appropriate method
            if query_params.query_type == 'current':
                result = asyncio.run(self._get_current_weather(query_params.location))
            elif query_params.query_type == 'forecast':
                result = asyncio.run(self._get_weather_forecast(
                    query_params.location, query_params.days
                ))
            elif query_params.query_type == 'historical':
                result = asyncio.run(self._get_historical_weather(
                    query_params.location, query_params.days
                ))
            elif query_params.query_type == 'analysis':
                result = self._analyze_weather_impact(
                    query_params.location,
                    query_params.analysis_type or 'equipment_demand'
                )
            else:
                result = {
                    'success': False,
                    'error': f"Unknown query type: {query_params.query_type}"
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Weather tool error: {e}", exc_info=True)
            return json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def _get_current_weather(self, location: str) -> Dict[str, Any]:
        """Get current weather conditions"""
        coords = self._get_coordinates(location)
        if not coords:
            return {'success': False, 'error': f'Unknown location: {location}'}
        
        try:
            # Try OpenWeatherMap first
            if self.openweather_api_key:
                weather_data = await self._fetch_openweather_current(
                    coords['lat'], coords['lon']
                )
                if weather_data:
                    analysis = self._analyze_current_conditions(weather_data)
                    return {
                        'success': True,
                        'location': location,
                        'current_weather': weather_data.__dict__,
                        'business_impact': analysis,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'openweather'
                    }
            
            # Fallback to NOAA
            weather_data = await self._fetch_noaa_current(
                coords['lat'], coords['lon']
            )
            if weather_data:
                analysis = self._analyze_current_conditions(weather_data)
                return {
                    'success': True,
                    'location': location,
                    'current_weather': weather_data.__dict__,
                    'business_impact': analysis,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'noaa'
                }
            
            return {'success': False, 'error': 'No weather data available'}
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_weather_forecast(self, location: str, days: int) -> Dict[str, Any]:
        """Get weather forecast"""
        coords = self._get_coordinates(location)
        if not coords:
            return {'success': False, 'error': f'Unknown location: {location}'}
        
        try:
            if self.openweather_api_key:
                forecasts = await self._fetch_openweather_forecast(
                    coords['lat'], coords['lon'], days
                )
            else:
                forecasts = await self._fetch_noaa_forecast(
                    coords['lat'], coords['lon'], days
                )
            
            if forecasts:
                # Analyze business impact for each day
                daily_analysis = []
                for forecast in forecasts:
                    impact = self._analyze_forecast_day(forecast)
                    daily_analysis.append({
                        'date': forecast.date.isoformat(),
                        'forecast': forecast.__dict__,
                        'business_impact': impact
                    })
                
                # Generate weekly summary
                weekly_summary = self._generate_weekly_summary(forecasts)
                
                return {
                    'success': True,
                    'location': location,
                    'forecast_days': days,
                    'daily_forecasts': daily_analysis,
                    'weekly_summary': weekly_summary,
                    'timestamp': datetime.now().isoformat()
                }
            
            return {'success': False, 'error': 'No forecast data available'}
            
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_historical_weather(self, location: str, days: int) -> Dict[str, Any]:
        """Get historical weather data (simulated - would integrate with historical API)"""
        # This would integrate with historical weather APIs
        # For now, returning simulated response structure
        return {
            'success': True,
            'location': location,
            'historical_period': f'Past {days} days',
            'note': 'Historical weather integration would be implemented with NOAA Climate Data API',
            'suggested_correlation_analysis': [
                'Temperature vs equipment rental volume',
                'Precipitation impact on construction equipment',
                'Seasonal patterns in tent/event equipment'
            ]
        }
    
    def _analyze_weather_impact(self, location: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze weather impact on equipment rental business"""
        
        analyses = {
            'equipment_demand': self._analyze_equipment_demand_patterns(),
            'seasonal_trends': self._analyze_seasonal_trends(),
            'construction_impact': self._analyze_construction_weather_impact(),
            'event_planning': self._analyze_event_weather_impact()
        }
        
        if analysis_type in analyses:
            return {
                'success': True,
                'location': location,
                'analysis_type': analysis_type,
                'insights': analyses[analysis_type],
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'success': False,
            'error': f'Unknown analysis type: {analysis_type}',
            'available_analyses': list(analyses.keys())
        }
    
    async def _fetch_openweather_current(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Fetch current weather from OpenWeatherMap"""
        if not self.openweather_api_key:
            return None
        
        url = f"{self.base_openweather_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.openweather_api_key,
            'units': 'imperial'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return WeatherData(
                            timestamp=datetime.now(),
                            temperature=data['main']['temp'],
                            humidity=data['main']['humidity'],
                            precipitation=data.get('rain', {}).get('1h', 0),
                            wind_speed=data['wind']['speed'],
                            conditions=data['weather'][0]['main'].lower(),
                            visibility=data.get('visibility', 10000) / 1609.34,  # Convert to miles
                            pressure=data['main']['pressure'],
                            source='openweather'
                        )
            except Exception as e:
                logger.error(f"OpenWeather API error: {e}")
                return None
    
    async def _fetch_noaa_current(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Fetch current weather from NOAA"""
        # NOAA API implementation would go here
        # For now, returning None to fallback
        logger.info("NOAA current weather integration would be implemented here")
        return None
    
    async def _fetch_openweather_forecast(
        self, lat: float, lon: float, days: int
    ) -> List[WeatherForecast]:
        """Fetch forecast from OpenWeatherMap"""
        if not self.openweather_api_key:
            return []
        
        url = f"{self.base_openweather_url}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.openweather_api_key,
            'units': 'imperial'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        forecasts = []
                        
                        # Group by date and process
                        daily_data = {}
                        for item in data['list'][:days*8]:  # 8 forecasts per day (3-hour intervals)
                            date = datetime.fromtimestamp(item['dt']).date()
                            if date not in daily_data:
                                daily_data[date] = []
                            daily_data[date].append(item)
                        
                        for date, day_forecasts in daily_data.items():
                            # Calculate daily highs/lows from 3-hour forecasts
                            temps = [f['main']['temp'] for f in day_forecasts]
                            precip_chances = [f.get('pop', 0) * 100 for f in day_forecasts]
                            wind_speeds = [f['wind']['speed'] for f in day_forecasts]
                            conditions = day_forecasts[len(day_forecasts)//2]['weather'][0]['main'].lower()
                            
                            forecasts.append(WeatherForecast(
                                date=datetime.combine(date, datetime.min.time()),
                                high_temp=max(temps),
                                low_temp=min(temps),
                                precipitation_chance=max(precip_chances),
                                conditions=conditions,
                                wind_speed=max(wind_speeds)
                            ))
                        
                        return forecasts[:days]
            except Exception as e:
                logger.error(f"OpenWeather forecast API error: {e}")
                return []
    
    async def _fetch_noaa_forecast(
        self, lat: float, lon: float, days: int
    ) -> List[WeatherForecast]:
        """Fetch forecast from NOAA"""
        # NOAA forecast API implementation would go here
        logger.info("NOAA forecast integration would be implemented here")
        return []
    
    def _get_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """Get coordinates for location"""
        location_clean = location.lower().replace(' ', '_')
        return self.locations.get(location_clean)
    
    def _analyze_current_conditions(self, weather: WeatherData) -> Dict[str, Any]:
        """Analyze current weather impact on equipment rental business"""
        impact_analysis = {
            'overall_conditions': 'favorable',
            'equipment_recommendations': [],
            'business_alerts': []
        }
        
        # Construction equipment analysis
        if (weather.precipitation > self.weather_impacts['construction']['rain_threshold'] or
            weather.temperature < self.weather_impacts['construction']['temperature_min'] or
            weather.wind_speed > self.weather_impacts['construction']['wind_max']):
            
            impact_analysis['overall_conditions'] = 'challenging'
            impact_analysis['business_alerts'].append(
                'Construction equipment demand may be reduced due to weather conditions'
            )
        else:
            impact_analysis['equipment_recommendations'].append(
                'Good conditions for construction equipment rentals'
            )
        
        # Event equipment analysis
        if (weather.conditions in self.weather_impacts['outdoor_events']['conditions_avoid'] or
            weather.precipitation > self.weather_impacts['outdoor_events']['rain_threshold']):
            
            impact_analysis['business_alerts'].append(
                'Outdoor event equipment may need weather protection or cancellations expected'
            )
        
        return impact_analysis
    
    def _analyze_forecast_day(self, forecast: WeatherForecast) -> Dict[str, Any]:
        """Analyze single day forecast for business impact"""
        return {
            'construction_favorable': (
                forecast.precipitation_chance < 30 and
                forecast.high_temp > 35 and
                forecast.wind_speed < 25
            ),
            'events_favorable': (
                forecast.precipitation_chance < 20 and
                50 <= forecast.high_temp <= 85 and
                forecast.wind_speed < 15
            ),
            'recommendations': self._generate_daily_recommendations(forecast)
        }
    
    def _generate_daily_recommendations(self, forecast: WeatherForecast) -> List[str]:
        """Generate business recommendations for a forecast day"""
        recommendations = []
        
        if forecast.precipitation_chance > 70:
            recommendations.append("High rain probability - promote indoor equipment")
            recommendations.append("Check tent and canopy inventory for weather protection")
        
        if forecast.high_temp > 85:
            recommendations.append("Hot weather - promote cooling equipment and shade structures")
        
        if forecast.high_temp < 40:
            recommendations.append("Cold weather - heating equipment demand expected")
        
        if forecast.wind_speed > 20:
            recommendations.append("High winds - secure outdoor equipment, delay lifting operations")
        
        return recommendations
    
    def _generate_weekly_summary(self, forecasts: List[WeatherForecast]) -> Dict[str, Any]:
        """Generate weekly weather summary for business planning"""
        avg_high = sum(f.high_temp for f in forecasts) / len(forecasts)
        avg_low = sum(f.low_temp for f in forecasts) / len(forecasts)
        rain_days = sum(1 for f in forecasts if f.precipitation_chance > 40)
        
        return {
            'average_high_temp': round(avg_high, 1),
            'average_low_temp': round(avg_low, 1),
            'rainy_days_expected': rain_days,
            'construction_friendly_days': sum(1 for f in forecasts if f.precipitation_chance < 30),
            'event_friendly_days': sum(1 for f in forecasts if f.precipitation_chance < 20),
            'weekly_outlook': 'favorable' if rain_days < 3 else 'challenging'
        }
    
    def _analyze_equipment_demand_patterns(self) -> Dict[str, Any]:
        """Analyze weather-based equipment demand patterns"""
        return {
            'rain_impact': {
                'construction_reduction': '30-50% for outdoor work',
                'tent_increase': '200-300% for events',
                'pump_increase': '400-500% for flooding'
            },
            'temperature_impact': {
                'heating_equipment': 'Demand increases below 50°F',
                'cooling_equipment': 'Demand increases above 80°F',
                'construction_slowdown': 'Below 32°F or above 95°F'
            },
            'seasonal_patterns': {
                'spring': 'Construction ramp-up, landscaping peak',
                'summer': 'Event season peak, construction steady',
                'fall': 'Final construction push, event decline',
                'winter': 'Heating equipment peak, construction minimal'
            }
        }
    
    def _analyze_seasonal_trends(self) -> Dict[str, Any]:
        """Analyze seasonal equipment rental trends"""
        return {
            'minnesota_seasons': {
                'winter_challenges': [
                    'Sub-zero temperatures reduce construction',
                    'Snow removal equipment high demand',
                    'Indoor event equipment preferred'
                ],
                'spring_opportunities': [
                    'Construction season restart',
                    'Landscaping and cleanup equipment peak',
                    'Graduation and wedding season begins'
                ],
                'summer_peak': [
                    'State Fair and festival season',
                    'Construction equipment at full capacity',
                    'Outdoor event equipment maximum demand'
                ],
                'fall_preparation': [
                    'Final construction projects before winter',
                    'Leaf cleanup and winterization equipment',
                    'Holiday event preparation'
                ]
            }
        }
    
    def _analyze_construction_weather_impact(self) -> Dict[str, Any]:
        """Analyze weather impact specifically on construction equipment"""
        return {
            'weather_thresholds': self.weather_impacts['construction'],
            'impact_levels': {
                'minimal_impact': 'Clear skies, 40-80°F, winds <15mph',
                'moderate_impact': 'Light rain or 32-40°F or 80-90°F',
                'significant_impact': 'Heavy rain, <32°F, >90°F, winds >25mph',
                'work_stoppage': 'Thunderstorms, ice, >35mph winds'
            },
            'equipment_specific': {
                'excavators': 'Sensitive to wet ground conditions',
                'cranes': 'Wind speed critical safety factor',
                'concrete_equipment': 'Temperature affects curing time',
                'roofing_equipment': 'Rain and wind most limiting factors'
            }
        }
    
    def _analyze_event_weather_impact(self) -> Dict[str, Any]:
        """Analyze weather impact on event equipment rentals"""
        return {
            'weather_thresholds': self.weather_impacts['outdoor_events'],
            'event_types': {
                'weddings': 'Highly weather-sensitive, backup plans common',
                'corporate_events': 'Indoor alternatives preferred in poor weather',
                'festivals': 'May proceed with weather protection equipment',
                'sports_events': 'Often weather-resistant but may need shelters'
            },
            'equipment_adaptations': {
                'tents': 'Sidewalls and flooring for rain protection',
                'stages': 'Covering and wind resistance critical',
                'seating': 'Waterproof options in demand',
                'power': 'Weather-protected generators and distribution'
            }
        }