"""
External Data Fetcher Service
Fetches external factors for correlation analysis with business data
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import json
import time
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class DataFetchService:
    """Service for fetching external data factors"""
    
    def __init__(self):
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RFID3-Analytics/1.0 (Business Analytics)'
        })
        
        # Minneapolis coordinates for weather data
        self.minneapolis_lat = 44.98
        self.minneapolis_lon = -93.26
    
    def fetch_weather_data(self, start_date: str = "2020-01-01", end_date: str = "2025-08-28") -> List[Dict]:
        """Fetch historical weather data from Open-Meteo (free API)"""
        try:
            self.logger.info(f"Fetching weather data from {start_date} to {end_date}")
            
            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                'latitude': self.minneapolis_lat,
                'longitude': self.minneapolis_lon,
                'start_date': start_date,
                'end_date': end_date,
                'daily': 'temperature_2m_mean,precipitation_sum,windspeed_10m_max',
                'timezone': 'America/Chicago'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            records = []
            daily_data = data.get('daily', {})
            dates = daily_data.get('time', [])
            
            for i, date_str in enumerate(dates):
                # Temperature
                if daily_data.get('temperature_2m_mean'):
                    records.append({
                        'date': date_str,
                        'factor_type': 'weather',
                        'factor_name': 'temperature_avg_f',
                        'value': round((daily_data['temperature_2m_mean'][i] * 9/5 + 32), 2),
                        'source': 'open-meteo.com'
                    })
                
                # Precipitation
                if daily_data.get('precipitation_sum'):
                    records.append({
                        'date': date_str,
                        'factor_type': 'weather',
                        'factor_name': 'precipitation_mm',
                        'value': daily_data['precipitation_sum'][i],
                        'source': 'open-meteo.com'
                    })
                
                # Wind speed
                if daily_data.get('windspeed_10m_max'):
                    records.append({
                        'date': date_str,
                        'factor_type': 'weather',
                        'factor_name': 'windspeed_max_mph',
                        'value': round(daily_data['windspeed_10m_max'][i] * 0.621371, 2),
                        'source': 'open-meteo.com'
                    })
            
            self.logger.info(f"Fetched {len(records)} weather records")
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to fetch weather data: {e}")
            return []
    
    def fetch_economic_indicators(self) -> List[Dict]:
        """Fetch key economic indicators (using free data sources)"""
        records = []
        
        try:
            # Use public economic data from Federal Reserve Economic Data (FRED)
            # Note: For production, you'd need a free FRED API key
            # For now, we'll use hardcoded sample data representing key indicators
            
            indicators = {
                'unemployment_rate': [3.6, 3.8, 4.0, 14.7, 8.1, 6.2, 3.9, 3.5, 3.6, 3.7],
                'interest_rate_fed': [1.75, 1.75, 0.25, 0.25, 0.25, 0.25, 2.5, 4.25, 5.25, 5.25],
                'consumer_confidence': [98.1, 99.3, 85.7, 71.8, 88.9, 95.2, 102.3, 103.4, 101.8, 100.5],
                'gas_price_avg': [2.58, 2.68, 2.18, 3.12, 4.32, 3.45, 3.68, 3.52, 3.41, 3.38]
            }
            
            # Generate sample data for last 10 quarters (2.5 years)
            base_date = datetime(2022, 1, 1)
            
            for quarter in range(10):
                quarter_date = base_date + timedelta(days=quarter * 90)
                date_str = quarter_date.strftime('%Y-%m-%d')
                
                for indicator, values in indicators.items():
                    if quarter < len(values):
                        records.append({
                            'date': date_str,
                            'factor_type': 'economic',
                            'factor_name': indicator,
                            'value': values[quarter],
                            'source': 'economic_indicators_sample'
                        })
            
            self.logger.info(f"Generated {len(records)} economic indicator records")
            
        except Exception as e:
            self.logger.error(f"Failed to generate economic indicators: {e}")
        
        return records
    
    def fetch_seasonal_events(self) -> List[Dict]:
        """Fetch seasonal and event data that might correlate with equipment rentals"""
        records = []
        
        try:
            # Key events that likely impact party/event rental business
            events = [
                # Wedding season peaks
                ('2023-05-15', 'seasonal', 'wedding_season_start', 1.0),
                ('2023-09-30', 'seasonal', 'wedding_season_end', 1.0),
                ('2024-05-15', 'seasonal', 'wedding_season_start', 1.0),
                ('2024-09-30', 'seasonal', 'wedding_season_end', 1.0),
                
                # Graduation seasons
                ('2023-05-01', 'seasonal', 'graduation_season', 1.0),
                ('2023-06-30', 'seasonal', 'graduation_season', 1.0),
                ('2024-05-01', 'seasonal', 'graduation_season', 1.0),
                ('2024-06-30', 'seasonal', 'graduation_season', 1.0),
                
                # Holiday periods (high party rental demand)
                ('2023-11-23', 'holiday', 'thanksgiving_week', 1.0),
                ('2023-12-25', 'holiday', 'christmas_week', 1.0),
                ('2023-12-31', 'holiday', 'new_years_week', 1.0),
                ('2024-11-28', 'holiday', 'thanksgiving_week', 1.0),
                ('2024-12-25', 'holiday', 'christmas_week', 1.0),
                ('2024-12-31', 'holiday', 'new_years_week', 1.0),
                
                # Summer event season
                ('2023-06-01', 'seasonal', 'summer_events_start', 1.0),
                ('2023-08-31', 'seasonal', 'summer_events_end', 1.0),
                ('2024-06-01', 'seasonal', 'summer_events_start', 1.0),
                ('2024-08-31', 'seasonal', 'summer_events_end', 1.0),
            ]
            
            for event_date, event_type, event_name, value in events:
                records.append({
                    'date': event_date,
                    'factor_type': event_type,
                    'factor_name': event_name,
                    'value': value,
                    'source': 'seasonal_calendar'
                })
            
            self.logger.info(f"Generated {len(records)} seasonal event records")
            
        except Exception as e:
            self.logger.error(f"Failed to generate seasonal events: {e}")
        
        return records
    
    def fetch_local_market_data(self) -> List[Dict]:
        """Fetch local Minneapolis market data relevant to party rentals"""
        records = []
        
        try:
            # Population and economic growth indicators for Minneapolis metro
            market_data = [
                ('2023-01-01', 'market', 'metro_population_growth_pct', 0.8),
                ('2023-01-01', 'market', 'new_housing_permits', 2340),
                ('2023-01-01', 'market', 'business_formations', 1250),
                ('2024-01-01', 'market', 'metro_population_growth_pct', 0.9),
                ('2024-01-01', 'market', 'new_housing_permits', 2180),
                ('2024-01-01', 'market', 'business_formations', 1340),
            ]
            
            for data_date, data_type, data_name, value in market_data:
                records.append({
                    'date': data_date,
                    'factor_type': data_type,
                    'factor_name': data_name,
                    'value': value,
                    'source': 'minneapolis_market_sample'
                })
            
            self.logger.info(f"Generated {len(records)} market data records")
            
        except Exception as e:
            self.logger.error(f"Failed to generate market data: {e}")
        
        return records
    
    def store_factors(self, factors: List[Dict]) -> int:
        """Store external factors in database"""
        if not factors:
            return 0
        
        stored_count = 0
        batch_size = 1000
        
        try:
            for i in range(0, len(factors), batch_size):
                batch = factors[i:i+batch_size]
                
                # Use INSERT IGNORE to handle duplicates gracefully
                query = text("""
                    INSERT IGNORE INTO external_factors 
                    (date, factor_type, factor_name, value, source, metadata)
                    VALUES (:date, :factor_type, :factor_name, :value, :source, :metadata)
                """)
                
                for factor in batch:
                    # Add metadata if not present
                    if 'metadata' not in factor:
                        factor['metadata'] = json.dumps({'imported_at': datetime.now().isoformat()})
                    
                    db.session.execute(query, factor)
                
                db.session.commit()
                stored_count += len(batch)
                
                if i % 5000 == 0:
                    self.logger.info(f"Stored {stored_count} factors so far...")
            
            self.logger.info(f"Successfully stored {stored_count} external factors")
            return stored_count
            
        except Exception as e:
            self.logger.error(f"Failed to store factors: {e}")
            db.session.rollback()
            return 0
    
    def fetch_all_external_data(self) -> Dict:
        """Fetch all external data sources and store in database"""
        self.logger.info("Starting comprehensive external data fetch...")
        
        results = {
            'weather': [],
            'economic': [],
            'seasonal': [],
            'market': []
        }
        
        # Fetch all data sources
        results['weather'] = self.fetch_weather_data()
        results['economic'] = self.fetch_economic_indicators()
        results['seasonal'] = self.fetch_seasonal_events()
        results['market'] = self.fetch_local_market_data()
        
        # Combine all factors
        all_factors = []
        for source, factors in results.items():
            all_factors.extend(factors)
        
        # Store in database
        stored_count = self.store_factors(all_factors)
        
        summary = {
            'total_fetched': len(all_factors),
            'total_stored': stored_count,
            'by_source': {k: len(v) for k, v in results.items()},
            'fetch_timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"External data fetch complete: {summary}")
        return summary
    
    def get_factors_summary(self) -> Dict:
        """Get summary of stored external factors"""
        try:
            query = text("""
                SELECT 
                    factor_type,
                    factor_name,
                    COUNT(*) as record_count,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    AVG(value) as avg_value
                FROM external_factors
                GROUP BY factor_type, factor_name
                ORDER BY factor_type, factor_name
            """)
            
            result = db.session.execute(query).fetchall()
            
            summary = {}
            for row in result:
                factor_type = row[0]
                if factor_type not in summary:
                    summary[factor_type] = {}
                
                summary[factor_type][row[1]] = {
                    'record_count': row[2],
                    'date_range': f"{row[3]} to {row[4]}",
                    'avg_value': float(row[5]) if row[5] else 0
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get factors summary: {e}")
            return {}