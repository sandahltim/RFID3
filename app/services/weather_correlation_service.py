"""
Weather Correlation Service
Extends ML Correlation Service to analyze weather-rental correlations
Specialized for Minnesota rental equipment business
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, and_, or_, func
from app import db
from app.services.logger import get_logger
from app.services.ml_correlation_service import MLCorrelationService
from app.services.minnesota_weather_service import MinnesotaWeatherService
from app.services.minnesota_industry_analytics import MinnesotaIndustryAnalytics
from app.models.weather_models import (
    WeatherData, WeatherRentalCorrelation, WeatherForecastDemand,
    StoreRegionalAnalytics, EquipmentCategorization
)
from app.models.pos_models import POSTransaction, POSTransactionItem, POSEquipment
import json
from decimal import Decimal
import warnings
from app.config.stores import (
    STORES, STORE_MAPPING, STORE_MANAGERS,
    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,
    get_store_name, get_store_manager, get_store_business_type,
    get_store_opening_date, get_active_store_codes
)

warnings.filterwarnings('ignore')

# Import ML libraries with fallbacks
try:
    from scipy.stats import pearsonr, spearmanr
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.stats.diagnostic import het_breuschpagan
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

logger = get_logger(__name__)

class WeatherCorrelationService:
    """Service for analyzing correlations between weather patterns and rental demand"""
    
    def __init__(self):
        self.logger = logger
        self.ml_service = MLCorrelationService()
        self.weather_service = MinnesotaWeatherService()
        self.industry_service = MinnesotaIndustryAnalytics()
    
    def analyze_weather_rental_correlations(self, store_code: str = None, 
                                          industry_segment: str = 'all',
                                          days_back: int = 365,
                                          include_forecasts: bool = False) -> Dict:
        """Comprehensive weather-rental correlation analysis"""
        try:
            # Validate store code using centralized configuration
            if store_code and store_code != 'all':
                if store_code not in STORES:
                    self.logger.warning(f"Invalid store code {store_code}, using all stores")
                    store_code = None
            self.logger.info(f"Starting weather-rental correlation analysis for store {store_code}, segment {industry_segment}")
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Get aligned weather and business data
            aligned_data = self._get_aligned_weather_business_data(
                start_date, end_date, store_code, industry_segment
            )
            
            if aligned_data.empty:
                return {'error': 'No aligned weather-business data available'}
            
            # Calculate correlations
            correlations = self._calculate_weather_correlations(aligned_data)
            
            # Analyze lag effects
            lag_analysis = self._analyze_lag_effects(aligned_data)
            
            # Generate demand forecasts if requested
            forecasts = {}
            if include_forecasts:
                forecasts = self._generate_weather_based_forecasts(
                    aligned_data, store_code, industry_segment
                )
            
            # Store correlation results
            self._store_correlation_results(correlations, store_code, industry_segment)
            
            # Generate business insights
            insights = self._generate_weather_insights(correlations, lag_analysis)
            
            results = {
                'status': 'success',
                'analysis_parameters': {
                    'store_code': store_code,
                    'industry_segment': industry_segment,
                    'date_range': f"{start_date} to {end_date}",
                    'days_analyzed': len(aligned_data),
                    'include_forecasts': include_forecasts
                },
                'correlations': correlations,
                'lag_analysis': lag_analysis,
                'forecasts': forecasts,
                'insights': insights,
                'data_summary': self._get_data_summary(aligned_data),
                'timestamp': datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Weather correlation analysis failed: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def _get_aligned_weather_business_data(self, start_date: date, end_date: date,
                                         store_code: str = None,
                                         industry_segment: str = 'all') -> pd.DataFrame:
        """Get weather and business data aligned by date"""
        
        # Weather data query
        weather_query = text("""
            SELECT 
                observation_date,
                location_code,
                temperature_high,
                temperature_low,
                temperature_avg,
                precipitation,
                wind_speed_avg,
                wind_speed_max,
                weather_condition,
                humidity_avg,
                cloud_cover
            FROM weather_data 
            WHERE observation_date BETWEEN :start_date AND :end_date
                AND is_forecast = FALSE
                AND location_code = 'MSP'  -- Use MSP as primary location
            ORDER BY observation_date
        """)
        
        weather_df = pd.read_sql(weather_query, db.engine, params={
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Business data query with industry segment filtering
        business_base_query = """
            SELECT 
                DATE(pt.contract_date) as business_date,
                pt.store_no,
                SUM(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as daily_revenue,
                COUNT(DISTINCT pt.contract_no) as daily_contracts,
                COUNT(pti.id) as daily_items,
                AVG(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as avg_contract_value
            FROM pos_transactions pt
            JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
        """
        
        # Add industry segment filtering if specified
        if industry_segment != 'all':
            business_base_query += """
                JOIN equipment_categorization ec ON pti.item_num = ec.item_num
                WHERE ec.industry_segment = :industry_segment
            """
        else:
            business_base_query += " WHERE 1=1"
        
        business_base_query += """
            AND pt.contract_date BETWEEN :start_date AND :end_date
        """
        
        # Add store filtering if specified
        if store_code:
            business_base_query += " AND pt.store_no = :store_code"
        
        business_base_query += """
            GROUP BY DATE(pt.contract_date), pt.store_no
            ORDER BY business_date
        """
        
        business_query = text(business_base_query)
        
        params = {'start_date': start_date, 'end_date': end_date}
        if industry_segment != 'all':
            params['industry_segment'] = industry_segment
        if store_code:
            params['store_code'] = store_code
        
        business_df = pd.read_sql(business_query, db.engine, params=params)
        
        if weather_df.empty or business_df.empty:
            return pd.DataFrame()
        
        # Aggregate business data by date if multiple stores
        if not store_code:
            business_df = business_df.groupby('business_date').agg({
                'daily_revenue': 'sum',
                'daily_contracts': 'sum', 
                'daily_items': 'sum',
                'avg_contract_value': 'mean'
            }).reset_index()
        
        # Align dates
        weather_df['observation_date'] = pd.to_datetime(weather_df['observation_date'])
        business_df['business_date'] = pd.to_datetime(business_df['business_date'])
        
        # Merge data
        aligned_df = pd.merge(
            business_df,
            weather_df,
            left_on='business_date',
            right_on='observation_date',
            how='inner'
        )
        
        # Fill missing weather values with interpolation
        numeric_weather_cols = ['temperature_high', 'temperature_low', 'temperature_avg', 
                               'precipitation', 'wind_speed_avg', 'humidity_avg', 'cloud_cover']
        
        for col in numeric_weather_cols:
            if col in aligned_df.columns:
                aligned_df[col] = aligned_df[col].interpolate(method='linear')
        
        # Add derived weather features
        aligned_df['temperature_range'] = aligned_df['temperature_high'] - aligned_df['temperature_low']
        aligned_df['is_rainy'] = (aligned_df['precipitation'] > 0.1).astype(int)
        aligned_df['is_windy'] = (aligned_df['wind_speed_avg'] > 15).astype(int)
        aligned_df['weather_score'] = self._calculate_weather_score(aligned_df, industry_segment)
        
        # Add time-based features
        aligned_df['day_of_week'] = aligned_df['business_date'].dt.dayofweek
        aligned_df['month'] = aligned_df['business_date'].dt.month
        aligned_df['is_weekend'] = (aligned_df['day_of_week'].isin([5, 6])).astype(int)
        
        self.logger.info(f"Aligned data: {len(aligned_df)} days with both weather and business data")
        
        return aligned_df
    
    def _calculate_weather_score(self, df: pd.DataFrame, industry_segment: str) -> pd.Series:
        """Calculate composite weather score for rental favorability"""
        if industry_segment == 'party_event':
            # Party events prefer mild temps, no rain, light winds
            temp_score = 1.0 - (np.abs(df['temperature_high'] - 75) / 50).clip(0, 1)
            precip_score = 1.0 - (df['precipitation'] / 0.5).clip(0, 1)
            wind_score = 1.0 - ((df['wind_speed_avg'] - 5) / 20).clip(0, 1)
            return (temp_score + precip_score + wind_score) / 3
            
        elif industry_segment == 'construction_diy':
            # Construction tolerates wider temp range, less affected by light rain
            temp_score = 1.0 - (np.abs(df['temperature_high'] - 65) / 60).clip(0, 1)
            precip_score = 1.0 - (df['precipitation'] / 0.8).clip(0, 1)
            return (temp_score + precip_score) / 2
            
        elif industry_segment == 'landscaping':
            # Landscaping benefits from recent rain, prefers moderate temps
            temp_score = 1.0 - (np.abs(df['temperature_high'] - 70) / 45).clip(0, 1)
            precip_score = np.minimum(df['precipitation'] / 0.3, 1.0)  # Benefits from rain up to point
            return (temp_score + precip_score) / 2
            
        else:
            # General score for mixed/all segments
            return 1.0 - (np.abs(df['temperature_high'] - 70) / 50).clip(0, 1)
    
    def _calculate_weather_correlations(self, df: pd.DataFrame) -> Dict:
        """Calculate correlations between weather factors and business metrics"""
        if not SCIPY_AVAILABLE or len(df) < 10:
            return {}
        
        correlations = {}
        
        # Weather factors to analyze
        weather_factors = [
            'temperature_high', 'temperature_low', 'temperature_avg', 'temperature_range',
            'precipitation', 'wind_speed_avg', 'humidity_avg', 'cloud_cover',
            'weather_score', 'is_rainy', 'is_windy'
        ]
        
        # Business metrics to correlate
        business_metrics = ['daily_revenue', 'daily_contracts', 'daily_items', 'avg_contract_value']
        
        for weather_factor in weather_factors:
            if weather_factor not in df.columns:
                continue
            
            correlations[weather_factor] = {}
            weather_values = df[weather_factor].dropna()
            
            if len(weather_values) < 5:
                continue
            
            for business_metric in business_metrics:
                if business_metric not in df.columns:
                    continue
                
                # Align data (remove NaN pairs)
                combined = df[[weather_factor, business_metric]].dropna()
                
                if len(combined) < 5:
                    continue
                
                try:
                    # Pearson correlation
                    pearson_corr, pearson_p = pearsonr(
                        combined[weather_factor], combined[business_metric]
                    )
                    
                    # Spearman correlation (rank-based)
                    spearman_corr, spearman_p = spearmanr(
                        combined[weather_factor], combined[business_metric]
                    )
                    
                    # Classification of correlation strength
                    strength = self._classify_correlation_strength(pearson_corr)
                    
                    # Statistical significance
                    is_significant = pearson_p < 0.05
                    
                    correlations[weather_factor][business_metric] = {
                        'pearson_correlation': float(pearson_corr) if not np.isnan(pearson_corr) else 0.0,
                        'pearson_p_value': float(pearson_p) if not np.isnan(pearson_p) else 1.0,
                        'spearman_correlation': float(spearman_corr) if not np.isnan(spearman_corr) else 0.0,
                        'spearman_p_value': float(spearman_p) if not np.isnan(spearman_p) else 1.0,
                        'correlation_strength': strength,
                        'is_significant': is_significant,
                        'data_points': len(combined),
                        'effect_size': abs(pearson_corr) if not np.isnan(pearson_corr) else 0.0
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Correlation calculation failed for {weather_factor} vs {business_metric}: {e}")
                    continue
        
        return correlations
    
    def _analyze_lag_effects(self, df: pd.DataFrame, max_lag: int = 7) -> Dict:
        """Analyze how weather affects business with different time lags"""
        if not SCIPY_AVAILABLE or len(df) < max_lag + 10:
            return {}
        
        lag_analysis = {}
        weather_factors = ['temperature_high', 'precipitation', 'weather_score']
        business_metrics = ['daily_revenue', 'daily_contracts']
        
        for weather_factor in weather_factors:
            if weather_factor not in df.columns:
                continue
                
            lag_analysis[weather_factor] = {}
            
            for business_metric in business_metrics:
                if business_metric not in df.columns:
                    continue
                
                lag_results = []
                
                for lag in range(0, max_lag + 1):
                    try:
                        # Create lagged weather data
                        weather_lagged = df[weather_factor].shift(lag)
                        business_data = df[business_metric]
                        
                        # Remove NaN values
                        combined = pd.DataFrame({
                            'weather': weather_lagged,
                            'business': business_data
                        }).dropna()
                        
                        if len(combined) < 5:
                            continue
                        
                        corr, p_val = pearsonr(combined['weather'], combined['business'])
                        
                        lag_results.append({
                            'lag_days': lag,
                            'correlation': float(corr) if not np.isnan(corr) else 0.0,
                            'p_value': float(p_val) if not np.isnan(p_val) else 1.0,
                            'data_points': len(combined)
                        })
                        
                    except Exception as e:
                        continue
                
                if lag_results:
                    # Find optimal lag
                    best_lag_info = max(lag_results, key=lambda x: abs(x['correlation']))
                    
                    lag_analysis[weather_factor][business_metric] = {
                        'all_lags': lag_results,
                        'optimal_lag_days': best_lag_info['lag_days'],
                        'optimal_correlation': best_lag_info['correlation'],
                        'interpretation': self._interpret_lag(best_lag_info['lag_days'], weather_factor)
                    }
        
        return lag_analysis
    
    def _interpret_lag(self, lag_days: int, weather_factor: str) -> str:
        """Interpret the meaning of weather lag effects"""
        if lag_days == 0:
            return f"Same-day {weather_factor} impact"
        elif lag_days == 1:
            return f"Next-day {weather_factor} impact"
        elif lag_days <= 3:
            return f"{weather_factor} affects demand {lag_days} days later"
        else:
            return f"Long-term {weather_factor} impact ({lag_days} days)"
    
    def _generate_weather_based_forecasts(self, historical_data: pd.DataFrame,
                                        store_code: str = None,
                                        industry_segment: str = 'all') -> Dict:
        """Generate demand forecasts based on weather forecasts"""
        try:
            # Get weather forecasts for next 7 days
            forecast_weather = self.weather_service.fetch_forecast_data('MSP', days_ahead=7)
            
            if not forecast_weather:
                return {'error': 'No weather forecast data available'}
            
            # Calculate baseline demand from historical data
            baseline_revenue = historical_data['daily_revenue'].mean()
            baseline_contracts = historical_data['daily_contracts'].mean()
            
            # Get weather correlation coefficients
            correlations = self._calculate_weather_correlations(historical_data)
            
            forecasts = []
            for forecast in forecast_weather:
                forecast_date = forecast['forecast_date']
                
                # Start with baseline
                predicted_revenue = baseline_revenue
                predicted_contracts = baseline_contracts
                
                # Apply weather adjustments based on correlations
                temp_high = forecast.get('temperature_high')
                precipitation_prob = forecast.get('precipitation_probability', 0) / 100.0
                
                # Temperature adjustment
                if temp_high and 'temperature_high' in correlations:
                    temp_corr = correlations['temperature_high'].get('daily_revenue', {})
                    if temp_corr.get('is_significant'):
                        # Simple linear adjustment (can be improved)
                        temp_deviation = (temp_high - historical_data['temperature_high'].mean()) / 20.0
                        temp_adjustment = temp_deviation * temp_corr['pearson_correlation'] * 0.3
                        predicted_revenue *= (1 + temp_adjustment)
                
                # Precipitation adjustment  
                if precipitation_prob > 0.3:  # Significant chance of rain
                    if 'precipitation' in correlations:
                        precip_corr = correlations['precipitation'].get('daily_revenue', {})
                        if precip_corr.get('is_significant'):
                            precip_adjustment = precipitation_prob * precip_corr['pearson_correlation'] * 0.4
                            predicted_revenue *= (1 + precip_adjustment)
                
                # Calculate weather score for this forecast
                weather_score = self.weather_service.calculate_weather_impact_score(
                    {'temperature_high': temp_high, 'precipitation': precipitation_prob * 0.5},
                    industry_segment
                )
                
                # Adjust contracts proportionally
                predicted_contracts = max(1, int(predicted_contracts * (predicted_revenue / baseline_revenue)))
                
                forecast_item = {
                    'forecast_date': forecast_date.isoformat(),
                    'days_ahead': forecast['days_ahead'],
                    'predicted_revenue': round(predicted_revenue, 2),
                    'predicted_contracts': predicted_contracts,
                    'weather_score': round(weather_score, 2),
                    'weather_conditions': forecast['weather_condition'],
                    'temperature_high': temp_high,
                    'precipitation_probability': forecast.get('precipitation_probability'),
                    'confidence_level': 0.6  # Medium confidence for weather-based forecasts
                }
                
                forecasts.append(forecast_item)
            
            return {
                'store_code': store_code,
                'industry_segment': industry_segment,
                'baseline_revenue': round(baseline_revenue, 2),
                'baseline_contracts': int(baseline_contracts),
                'forecasts': forecasts,
                'total_predicted_revenue': sum(f['predicted_revenue'] for f in forecasts)
            }
            
        except Exception as e:
            self.logger.error(f"Weather forecast generation failed: {e}")
            return {'error': str(e)}
    
    def _store_correlation_results(self, correlations: Dict, store_code: str = None,
                                 industry_segment: str = 'all') -> bool:
        """Store correlation results in database"""
        try:
            analysis_date = date.today()
            
            for weather_factor, business_metrics in correlations.items():
                for business_metric, correlation_data in business_metrics.items():
                    
                    # Skip if correlation is not significant and weak
                    if (not correlation_data['is_significant'] and 
                        correlation_data['correlation_strength'] in ['weak', 'very_weak']):
                        continue
                    
                    # Check if record exists
                    existing = db.session.query(WeatherRentalCorrelation).filter(
                        and_(
                            WeatherRentalCorrelation.analysis_date == analysis_date,
                            WeatherRentalCorrelation.store_code == store_code,
                            WeatherRentalCorrelation.weather_factor == weather_factor,
                            WeatherRentalCorrelation.industry_segment == industry_segment
                        )
                    ).first()
                    
                    correlation_strength_enum = correlation_data['correlation_strength']
                    if correlation_strength_enum == 'none':
                        correlation_strength_enum = 'very_weak'
                    
                    if existing:
                        # Update existing record
                        existing.correlation_coefficient = Decimal(str(correlation_data['pearson_correlation']))
                        existing.p_value = Decimal(str(correlation_data['pearson_p_value']))
                        existing.correlation_strength = correlation_strength_enum
                        existing.data_points_analyzed = correlation_data['data_points']
                        existing.r_squared = Decimal(str(correlation_data['pearson_correlation'] ** 2))
                    else:
                        # Create new record
                        new_correlation = WeatherRentalCorrelation(
                            analysis_date=analysis_date,
                            store_code=store_code,
                            weather_factor=weather_factor,
                            industry_segment=industry_segment,
                            correlation_coefficient=Decimal(str(correlation_data['pearson_correlation'])),
                            p_value=Decimal(str(correlation_data['pearson_p_value'])),
                            correlation_strength=correlation_strength_enum,
                            data_points_analyzed=correlation_data['data_points'],
                            r_squared=Decimal(str(correlation_data['pearson_correlation'] ** 2)),
                            business_insight=self._generate_correlation_insight(
                                weather_factor, business_metric, correlation_data
                            ),
                            forecasting_value='high' if correlation_data['is_significant'] else 'low'
                        )
                        db.session.add(new_correlation)
            
            db.session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store correlation results: {e}")
            db.session.rollback()
            return False
    
    def _generate_correlation_insight(self, weather_factor: str, business_metric: str,
                                    correlation_data: Dict) -> str:
        """Generate business insight from correlation data"""
        corr = correlation_data['pearson_correlation']
        strength = correlation_data['correlation_strength']
        
        factor_name = weather_factor.replace('_', ' ').title()
        metric_name = business_metric.replace('_', ' ').title()
        
        if abs(corr) < 0.1:
            return f"No meaningful relationship between {factor_name} and {metric_name}"
        
        direction = "increases" if corr > 0 else "decreases"
        
        if strength in ['strong', 'very_strong']:
            return f"Strong relationship: {factor_name} significantly {direction} {metric_name}"
        elif strength == 'moderate':
            return f"Moderate relationship: {factor_name} {direction} {metric_name}"
        else:
            return f"Weak relationship: {factor_name} slightly {direction} {metric_name}"
    
    def _generate_weather_insights(self, correlations: Dict, lag_analysis: Dict) -> List[str]:
        """Generate actionable business insights from weather correlation analysis"""
        insights = []
        
        # Find strongest correlations
        strong_correlations = []
        for weather_factor, business_metrics in correlations.items():
            for business_metric, correlation_data in business_metrics.items():
                if (correlation_data['is_significant'] and 
                    correlation_data['correlation_strength'] in ['strong', 'very_strong']):
                    strong_correlations.append({
                        'weather_factor': weather_factor,
                        'business_metric': business_metric,
                        'correlation': correlation_data['pearson_correlation'],
                        'strength': correlation_data['correlation_strength']
                    })
        
        if strong_correlations:
            insights.append(f"Found {len(strong_correlations)} strong weather-business correlations")
            
            # Highlight top correlation
            top_correlation = max(strong_correlations, key=lambda x: abs(x['correlation']))
            factor_name = top_correlation['weather_factor'].replace('_', ' ').title()
            metric_name = top_correlation['business_metric'].replace('_', ' ').title()
            direction = "positively" if top_correlation['correlation'] > 0 else "negatively"
            
            insights.append(f"Strongest correlation: {factor_name} {direction} affects {metric_name}")
        
        # Analyze temperature effects
        temp_effects = []
        for temp_factor in ['temperature_high', 'temperature_low', 'temperature_avg']:
            if temp_factor in correlations:
                for metric, data in correlations[temp_factor].items():
                    if data['is_significant']:
                        temp_effects.append(data['pearson_correlation'])
        
        if temp_effects:
            avg_temp_effect = np.mean(temp_effects)
            if avg_temp_effect > 0.3:
                insights.append("Higher temperatures generally increase rental demand")
            elif avg_temp_effect < -0.3:
                insights.append("Higher temperatures generally decrease rental demand")
        
        # Analyze precipitation effects
        if 'precipitation' in correlations:
            precip_correlations = correlations['precipitation']
            revenue_corr = precip_correlations.get('daily_revenue', {})
            if revenue_corr.get('is_significant'):
                if revenue_corr['pearson_correlation'] < -0.3:
                    insights.append("Rain significantly reduces rental revenue - consider weather contingency planning")
                elif revenue_corr['pearson_correlation'] > 0.2:
                    insights.append("Light rain may actually increase certain rental demand")
        
        # Analyze lag effects
        if lag_analysis:
            leading_indicators = []
            for weather_factor, business_metrics in lag_analysis.items():
                for business_metric, lag_data in business_metrics.items():
                    if lag_data['optimal_lag_days'] > 0 and abs(lag_data['optimal_correlation']) > 0.3:
                        leading_indicators.append({
                            'factor': weather_factor,
                            'lag_days': lag_data['optimal_lag_days'],
                            'correlation': lag_data['optimal_correlation']
                        })
            
            if leading_indicators:
                insights.append(f"Found {len(leading_indicators)} leading weather indicators for demand forecasting")
        
        # Weather score insights
        if 'weather_score' in correlations:
            weather_score_corr = correlations['weather_score'].get('daily_revenue', {})
            if weather_score_corr.get('is_significant') and weather_score_corr['pearson_correlation'] > 0.4:
                insights.append("Composite weather conditions strongly predict rental demand")
        
        if not insights:
            insights.append("No strong weather correlations found - consider expanding analysis period")
        
        return insights
    
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
    
    def _get_data_summary(self, df: pd.DataFrame) -> Dict:
        """Get summary statistics of the analyzed data"""
        if df.empty:
            return {}
        
        return {
            'total_days': len(df),
            'date_range': {
                'start': df['business_date'].min().isoformat() if 'business_date' in df.columns else None,
                'end': df['business_date'].max().isoformat() if 'business_date' in df.columns else None
            },
            'business_metrics': {
                'avg_daily_revenue': float(df['daily_revenue'].mean()) if 'daily_revenue' in df.columns else None,
                'avg_daily_contracts': float(df['daily_contracts'].mean()) if 'daily_contracts' in df.columns else None,
                'total_revenue': float(df['daily_revenue'].sum()) if 'daily_revenue' in df.columns else None
            },
            'weather_summary': {
                'avg_temperature': float(df['temperature_high'].mean()) if 'temperature_high' in df.columns else None,
                'total_precipitation': float(df['precipitation'].sum()) if 'precipitation' in df.columns else None,
                'rainy_days': int((df['precipitation'] > 0.1).sum()) if 'precipitation' in df.columns else None
            }
        }
    
    def get_weather_impact_dashboard_data(self, store_code: str = None,
                                        days_back: int = 90) -> Dict:
        """Get dashboard data for weather impact visualization"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Get recent correlation analysis
            recent_correlations = self.analyze_weather_rental_correlations(
                store_code=store_code, 
                industry_segment='all',
                days_back=days_back
            )
            
            # Get weather summary
            weather_summary = self.weather_service.get_weather_summary_for_date_range(
                start_date, end_date
            )
            
            # Get equipment categorization summary
            if store_code:
                industry_mix = self.industry_service.analyze_store_industry_mix(store_code)
            else:
                industry_mix = {'error': 'Multi-store industry mix not implemented'}
            
            dashboard_data = {
                'summary': {
                    'analysis_period': f"{start_date} to {end_date}",
                    'store_code': store_code,
                    'last_updated': datetime.now().isoformat()
                },
                'weather_correlations': recent_correlations,
                'weather_summary': weather_summary,
                'industry_mix': industry_mix,
                'key_metrics': self._extract_key_metrics(recent_correlations),
                'recommendations': self._generate_recommendations(recent_correlations, industry_mix)
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Dashboard data generation failed: {e}")
            return {'error': str(e)}
    
    def _extract_key_metrics(self, correlation_analysis: Dict) -> Dict:
        """Extract key metrics from correlation analysis for dashboard"""
        if correlation_analysis.get('status') != 'success':
            return {}
        
        correlations = correlation_analysis.get('correlations', {})
        
        # Find strongest correlations
        strongest_positive = None
        strongest_negative = None
        max_positive = -1
        max_negative = 1
        
        for weather_factor, business_metrics in correlations.items():
            for business_metric, correlation_data in business_metrics.items():
                corr = correlation_data.get('pearson_correlation', 0)
                if correlation_data.get('is_significant'):
                    if corr > max_positive:
                        max_positive = corr
                        strongest_positive = f"{weather_factor} → {business_metric}"
                    if corr < max_negative:
                        max_negative = corr
                        strongest_negative = f"{weather_factor} → {business_metric}"
        
        return {
            'strongest_positive_correlation': {
                'relationship': strongest_positive,
                'correlation': round(max_positive, 3) if max_positive > -1 else None
            },
            'strongest_negative_correlation': {
                'relationship': strongest_negative,
                'correlation': round(max_negative, 3) if max_negative < 1 else None
            },
            'total_significant_correlations': sum(
                1 for weather_factor, business_metrics in correlations.items()
                for business_metric, correlation_data in business_metrics.items()
                if correlation_data.get('is_significant')
            ),
            'weather_sensitivity_score': self._calculate_weather_sensitivity_score(correlations)
        }
    
    def _calculate_weather_sensitivity_score(self, correlations: Dict) -> float:
        """Calculate overall weather sensitivity score (0-1)"""
        if not correlations:
            return 0.0
        
        significant_correlations = []
        for weather_factor, business_metrics in correlations.items():
            for business_metric, correlation_data in business_metrics.items():
                if correlation_data.get('is_significant'):
                    significant_correlations.append(abs(correlation_data['pearson_correlation']))
        
        if not significant_correlations:
            return 0.0
        
        return min(1.0, np.mean(significant_correlations) * 2)  # Scale to 0-1
    
    def _generate_recommendations(self, correlation_analysis: Dict, industry_mix: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if correlation_analysis.get('status') != 'success':
            return ["Unable to generate recommendations - insufficient data"]
        
        insights = correlation_analysis.get('insights', [])
        
        # Weather-based recommendations
        if any('rain' in insight.lower() for insight in insights):
            recommendations.append("Implement weather contingency plans for outdoor equipment rentals")
        
        if any('temperature' in insight.lower() for insight in insights):
            recommendations.append("Adjust inventory levels based on temperature forecasts")
        
        # Industry mix recommendations
        if not isinstance(industry_mix, dict) or 'error' in industry_mix:
            pass  # Skip industry recommendations
        else:
            industry_breakdown = industry_mix.get('industry_breakdown', [])
            if industry_breakdown:
                party_segment = next((seg for seg in industry_breakdown 
                                    if seg['industry_segment'] == 'party_event'), None)
                if party_segment and party_segment['revenue_percentage'] > 50:
                    recommendations.append("High party/event focus - monitor weather forecasts closely for outdoor events")
        
        # General recommendations
        recommendations.extend([
            "Use 3-7 day weather forecasts for demand planning",
            "Consider dynamic pricing based on weather conditions",
            "Develop weather-aware inventory transfer strategies"
        ])
        
        return recommendations[:5]  # Limit to top 5 recommendations