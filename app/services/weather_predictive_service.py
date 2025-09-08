"""
Weather-Based Predictive Service
Advanced predictive models incorporating weather forecasts for demand planning
Specialized for Minnesota rental equipment business
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, and_, or_, func
from app import db
from app.services.logger import get_logger
from app.services.minnesota_weather_service import MinnesotaWeatherService
from app.services.minnesota_industry_analytics import MinnesotaIndustryAnalytics
from app.services.minnesota_seasonal_service import MinnesotaSeasonalService
from app.services.weather_correlation_service import WeatherCorrelationService
from app.models.weather_models import WeatherForecastDemand, WeatherData, WeatherRentalCorrelation
from app.models.pos_models import POSTransaction, POSTransactionItem
import json
from decimal import Decimal
from app.config.stores import (
    STORES, STORE_MAPPING, STORE_MANAGERS,
    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,
    get_store_name, get_store_manager, get_store_business_type,
    get_store_opening_date, get_active_store_codes
)


# Import ML libraries with fallbacks
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from scipy import stats
    from scipy.stats import pearsonr
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = get_logger(__name__)

class WeatherPredictiveService:
    """Service for weather-based demand forecasting and predictive analytics"""
    
    def __init__(self):
        self.logger = logger
        self.weather_service = MinnesotaWeatherService()
        self.industry_service = MinnesotaIndustryAnalytics()
        self.seasonal_service = MinnesotaSeasonalService()
        self.correlation_service = WeatherCorrelationService()
        
        # Model configurations
        self.models = {}
        self.scalers = {}
        
    def generate_comprehensive_demand_forecast(self, store_code: str = None, 
                                             forecast_days: int = 14,
                                             include_confidence_intervals: bool = True) -> Dict:
        """Generate comprehensive demand forecast incorporating weather, seasonal, and trend data"""
        try:
            self.logger.info(f"Generating comprehensive demand forecast for {forecast_days} days")
            
            # Get historical data for model training
            historical_data = self._get_comprehensive_historical_data(store_code)
            
            if historical_data.empty:
                return {'error': 'Insufficient historical data for forecasting'}
            
            # Get weather forecasts
            weather_forecasts = self.weather_service.fetch_forecast_data('MSP', days_ahead=forecast_days)
            
            if not weather_forecasts:
                return {'error': 'Weather forecast data unavailable'}
            
            # Train or update predictive models
            model_results = self._train_predictive_models(historical_data, store_code)
            
            # Generate forecasts for each day
            daily_forecasts = []
            
            for i, weather_forecast in enumerate(weather_forecasts[:forecast_days]):
                forecast_date = weather_forecast['forecast_date']
                
                # Create feature vector for this day
                features = self._create_forecast_features(weather_forecast, forecast_date, historical_data)
                
                # Generate predictions using multiple models
                predictions = self._generate_multi_model_predictions(features, store_code)
                
                # Apply business rules and constraints
                adjusted_predictions = self._apply_business_rules(predictions, forecast_date, store_code)
                
                # Calculate confidence intervals if requested
                confidence_intervals = {}
                if include_confidence_intervals:
                    confidence_intervals = self._calculate_confidence_intervals(
                        adjusted_predictions, features, model_results, store_code
                    )
                
                daily_forecast = {
                    'forecast_date': forecast_date.isoformat(),
                    'days_ahead': i + 1,
                    'weather_conditions': {
                        'temperature_high': weather_forecast.get('temperature_high'),
                        'temperature_low': weather_forecast.get('temperature_low'),
                        'weather_condition': weather_forecast.get('weather_condition'),
                        'precipitation_probability': weather_forecast.get('precipitation_probability'),
                        'wind_speed': weather_forecast.get('wind_speed')
                    },
                    'predictions': adjusted_predictions,
                    'confidence_intervals': confidence_intervals,
                    'model_metrics': self._get_prediction_metrics(adjusted_predictions, model_results),
                    'risk_factors': self._identify_risk_factors(weather_forecast, forecast_date),
                    'recommendations': self._generate_daily_recommendations(adjusted_predictions, weather_forecast)
                }
                
                daily_forecasts.append(daily_forecast)
            
            # Generate summary and insights
            forecast_summary = self._generate_forecast_summary(daily_forecasts, store_code)
            
            # Store forecasts in database
            self._store_demand_forecasts(daily_forecasts, store_code)
            
            results = {
                'status': 'success',
                'forecast_parameters': {
                    'store_code': store_code,
                    'forecast_days': forecast_days,
                    'forecast_generated_at': datetime.now().isoformat(),
                    'models_used': list(model_results.keys()) if model_results else []
                },
                'daily_forecasts': daily_forecasts,
                'forecast_summary': forecast_summary,
                'model_performance': model_results,
                'business_insights': self._generate_forecast_insights(daily_forecasts, forecast_summary),
                'timestamp': datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Comprehensive demand forecast failed: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def _get_comprehensive_historical_data(self, store_code: str = None, days_back: int = 730) -> pd.DataFrame:
        """Get comprehensive historical data for model training"""
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        # Main business data query with weather data joined
        base_query = """
            SELECT 
                DATE(pt.contract_date) as business_date,
                pt.store_no,
                SUM(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as daily_revenue,
                COUNT(DISTINCT pt.contract_no) as daily_contracts,
                COUNT(pti.id) as daily_items,
                AVG(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as avg_contract_value,
                
                -- Industry segment breakdown
                SUM(CASE WHEN ec.industry_segment = 'party_event' 
                    THEN COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0) ELSE 0 END) as party_revenue,
                SUM(CASE WHEN ec.industry_segment = 'construction_diy' 
                    THEN COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0) ELSE 0 END) as construction_revenue,
                SUM(CASE WHEN ec.industry_segment = 'landscaping' 
                    THEN COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0) ELSE 0 END) as landscaping_revenue,
                
                -- Weather dependent revenue
                SUM(CASE WHEN ec.weather_dependent = 1 
                    THEN COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0) ELSE 0 END) as weather_dependent_revenue
                
            FROM pos_transactions pt
            JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
            LEFT JOIN equipment_categorization ec ON pti.item_num = ec.item_num
            WHERE pt.contract_date BETWEEN :start_date AND :end_date
        """
        
        if store_code:
            base_query += " AND pt.store_no = :store_code"
        
        base_query += """
            GROUP BY DATE(pt.contract_date), pt.store_no
            ORDER BY business_date
        """
        
        params = {'start_date': start_date, 'end_date': end_date}
        if store_code:
            params['store_code'] = store_code
        
        business_query = text(base_query)
        business_df = pd.read_sql(business_query, db.engine, params=params)
        
        if business_df.empty:
            return pd.DataFrame()
        
        # Aggregate by date if multiple stores
        if not store_code:
            business_df = business_df.groupby('business_date').agg({
                'daily_revenue': 'sum',
                'daily_contracts': 'sum',
                'daily_items': 'sum',
                'avg_contract_value': 'mean',
                'party_revenue': 'sum',
                'construction_revenue': 'sum',
                'landscaping_revenue': 'sum',
                'weather_dependent_revenue': 'sum'
            }).reset_index()
        
        # Get weather data
        weather_query = text("""
            SELECT 
                observation_date,
                temperature_high,
                temperature_low,
                temperature_avg,
                precipitation,
                wind_speed_avg,
                wind_speed_max,
                weather_condition,
                humidity_avg,
                cloud_cover,
                barometric_pressure
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
            self.logger.warning("No weather data available - using business data only")
            return self._add_time_features(business_df)
        
        # Merge business and weather data
        business_df['business_date'] = pd.to_datetime(business_df['business_date'])
        weather_df['observation_date'] = pd.to_datetime(weather_df['observation_date'])
        
        merged_df = pd.merge(
            business_df,
            weather_df,
            left_on='business_date',
            right_on='observation_date',
            how='inner'
        )
        
        # Add derived features
        merged_df = self._add_comprehensive_features(merged_df)
        
        return merged_df
    
    def _add_comprehensive_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive features for model training"""
        
        # Time-based features
        df['year'] = df['business_date'].dt.year
        df['month'] = df['business_date'].dt.month
        df['day_of_year'] = df['business_date'].dt.dayofyear
        df['day_of_week'] = df['business_date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_holiday'] = self._identify_holidays(df['business_date']).astype(int)
        
        # Seasonal features
        df['season'] = df['month'].apply(self._get_season_number)
        df['is_wedding_season'] = df['month'].isin([5, 6, 7, 8, 9, 10]).astype(int)
        df['is_construction_season'] = df['month'].isin([4, 5, 6, 7, 8, 9, 10]).astype(int)
        df['is_landscaping_season'] = df['month'].isin([4, 5, 6, 7, 8, 9, 10, 11]).astype(int)
        
        # Weather features
        if 'temperature_high' in df.columns:
            df['temperature_range'] = df['temperature_high'] - df['temperature_low']
            df['is_hot_day'] = (df['temperature_high'] > 85).astype(int)
            df['is_cold_day'] = (df['temperature_high'] < 50).astype(int)
            df['is_comfortable_temp'] = ((df['temperature_high'] >= 65) & 
                                        (df['temperature_high'] <= 80)).astype(int)
        
        if 'precipitation' in df.columns:
            df['is_rainy'] = (df['precipitation'] > 0.1).astype(int)
            df['is_heavy_rain'] = (df['precipitation'] > 0.5).astype(int)
            df['precipitation_category'] = pd.cut(df['precipitation'], 
                                                bins=[-0.1, 0.1, 0.5, 1.0, float('inf')],
                                                labels=['none', 'light', 'moderate', 'heavy'])
        
        if 'wind_speed_avg' in df.columns:
            df['is_windy'] = (df['wind_speed_avg'] > 15).astype(int)
            df['is_very_windy'] = (df['wind_speed_avg'] > 25).astype(int)
        
        # Weather condition categories
        if 'weather_condition' in df.columns:
            df['weather_category'] = df['weather_condition'].apply(self._categorize_weather_condition)
        
        # Composite weather score
        df['weather_score'] = self._calculate_composite_weather_score(df)
        
        # Lag features (previous day effects)
        for lag in [1, 2, 3, 7]:
            df[f'revenue_lag_{lag}'] = df['daily_revenue'].shift(lag)
            df[f'weather_score_lag_{lag}'] = df['weather_score'].shift(lag)
            if 'temperature_high' in df.columns:
                df[f'temp_lag_{lag}'] = df['temperature_high'].shift(lag)
        
        # Moving averages
        for window in [3, 7, 14]:
            df[f'revenue_ma_{window}'] = df['daily_revenue'].rolling(window=window).mean()
            df[f'weather_score_ma_{window}'] = df['weather_score'].rolling(window=window).mean()
        
        # Trend features
        df['revenue_trend_7d'] = df['daily_revenue'].rolling(window=7).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 7 else 0
        )
        
        return df
    
    def _train_predictive_models(self, historical_data: pd.DataFrame, store_code: str = None) -> Dict:
        """Train multiple predictive models"""
        if not SKLEARN_AVAILABLE:
            self.logger.warning("scikit-learn not available - using simple models")
            return self._train_simple_models(historical_data, store_code)
        
        model_results = {}
        
        # Prepare feature matrix and target variables
        feature_columns = self._get_feature_columns(historical_data)
        X = historical_data[feature_columns].fillna(0)
        
        # Multiple target variables
        targets = {
            'daily_revenue': 'daily_revenue',
            'daily_contracts': 'daily_contracts',
            'party_revenue': 'party_revenue',
            'construction_revenue': 'construction_revenue'
        }
        
        for target_name, target_column in targets.items():
            if target_column not in historical_data.columns:
                continue
            
            y = historical_data[target_column].fillna(0)
            
            # Skip if insufficient data
            if len(X) < 30 or y.sum() == 0:
                continue
            
            try:
                # Scale features
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                # Train multiple models
                models = {
                    'linear_regression': LinearRegression(),
                    'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                    'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
                }
                
                target_results = {}
                
                for model_name, model in models.items():
                    try:
                        # Train model
                        model.fit(X_scaled, y)
                        
                        # Cross-validation
                        cv_scores = cross_val_score(model, X_scaled, y, cv=5, 
                                                  scoring='neg_mean_absolute_error')
                        
                        # Feature importance (if available)
                        feature_importance = {}
                        if hasattr(model, 'feature_importances_'):
                            importance_scores = model.feature_importances_
                            feature_importance = dict(zip(feature_columns, importance_scores))
                        elif hasattr(model, 'coef_'):
                            importance_scores = np.abs(model.coef_)
                            feature_importance = dict(zip(feature_columns, importance_scores))
                        
                        target_results[model_name] = {
                            'model': model,
                            'scaler': scaler,
                            'cv_mae': float(-cv_scores.mean()),
                            'cv_std': float(cv_scores.std()),
                            'feature_importance': {k: float(v) for k, v in 
                                                 sorted(feature_importance.items(), 
                                                       key=lambda x: x[1], reverse=True)[:10]}
                        }
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to train {model_name} for {target_name}: {e}")
                        continue
                
                model_results[target_name] = target_results
                
                # Store best models
                if target_results:
                    best_model_name = min(target_results.keys(), 
                                        key=lambda k: target_results[k]['cv_mae'])
                    self.models[f"{store_code or 'all'}_{target_name}"] = target_results[best_model_name]['model']
                    self.scalers[f"{store_code or 'all'}_{target_name}"] = target_results[best_model_name]['scaler']
                
            except Exception as e:
                self.logger.warning(f"Failed to train models for {target_name}: {e}")
                continue
        
        return model_results
    
    def _train_simple_models(self, historical_data: pd.DataFrame, store_code: str = None) -> Dict:
        """Train simple statistical models when sklearn is not available"""
        model_results = {}
        
        # Simple correlation-based models
        if 'daily_revenue' in historical_data.columns and 'weather_score' in historical_data.columns:
            # Linear relationship with weather score
            if SCIPY_AVAILABLE:
                correlation, p_value = pearsonr(historical_data['weather_score'], 
                                              historical_data['daily_revenue'])
                
                model_results['simple_weather_model'] = {
                    'type': 'correlation_based',
                    'correlation': float(correlation),
                    'p_value': float(p_value),
                    'baseline_revenue': float(historical_data['daily_revenue'].mean()),
                    'weather_sensitivity': float(correlation * historical_data['daily_revenue'].std())
                }
        
        # Seasonal averages
        if 'month' in historical_data.columns:
            monthly_averages = historical_data.groupby('month')['daily_revenue'].mean().to_dict()
            model_results['seasonal_model'] = {
                'type': 'seasonal_averages',
                'monthly_averages': {int(k): float(v) for k, v in monthly_averages.items()}
            }
        
        return model_results
    
    def _create_forecast_features(self, weather_forecast: Dict, forecast_date: date, 
                                historical_data: pd.DataFrame) -> Dict:
        """Create feature vector for a specific forecast day"""
        
        features = {}
        
        # Time-based features
        features['year'] = forecast_date.year
        features['month'] = forecast_date.month
        features['day_of_year'] = forecast_date.timetuple().tm_yday
        features['day_of_week'] = forecast_date.weekday()
        features['is_weekend'] = 1 if forecast_date.weekday() >= 5 else 0
        features['is_holiday'] = 1 if self._is_holiday(forecast_date) else 0
        
        # Seasonal features
        features['season'] = self._get_season_number(forecast_date.month)
        features['is_wedding_season'] = 1 if forecast_date.month in [5, 6, 7, 8, 9, 10] else 0
        features['is_construction_season'] = 1 if forecast_date.month in [4, 5, 6, 7, 8, 9, 10] else 0
        features['is_landscaping_season'] = 1 if forecast_date.month in [4, 5, 6, 7, 8, 9, 10, 11] else 0
        
        # Weather features
        temp_high = weather_forecast.get('temperature_high', 70)
        temp_low = weather_forecast.get('temperature_low', temp_high - 15)
        precip_prob = weather_forecast.get('precipitation_probability', 0) / 100.0
        wind_speed = self._extract_wind_speed(weather_forecast.get('wind_speed', '5 mph'))
        
        features['temperature_high'] = temp_high
        features['temperature_low'] = temp_low
        features['temperature_range'] = temp_high - temp_low
        features['is_hot_day'] = 1 if temp_high > 85 else 0
        features['is_cold_day'] = 1 if temp_high < 50 else 0
        features['is_comfortable_temp'] = 1 if 65 <= temp_high <= 80 else 0
        
        features['precipitation'] = precip_prob * 0.5  # Convert probability to estimated inches
        features['is_rainy'] = 1 if precip_prob > 0.3 else 0
        features['is_heavy_rain'] = 1 if precip_prob > 0.7 else 0
        
        features['wind_speed_avg'] = wind_speed
        features['is_windy'] = 1 if wind_speed > 15 else 0
        features['is_very_windy'] = 1 if wind_speed > 25 else 0
        
        # Weather condition
        weather_condition = weather_forecast.get('weather_condition', '').lower()
        features['weather_category'] = self._categorize_weather_condition(weather_condition)
        
        # Composite weather score
        features['weather_score'] = self._calculate_weather_score_from_forecast(weather_forecast)
        
        # Historical context features (if available)
        if not historical_data.empty:
            # Recent trend
            recent_data = historical_data.tail(7)  # Last 7 days
            if len(recent_data) > 0:
                features['recent_avg_revenue'] = recent_data['daily_revenue'].mean()
                features['recent_revenue_trend'] = self._calculate_trend(recent_data['daily_revenue'].values)
            
            # Same month historical average
            same_month_data = historical_data[historical_data['month'] == forecast_date.month]
            if len(same_month_data) > 0:
                features['historical_month_avg'] = same_month_data['daily_revenue'].mean()
            
        return features
    
    def _generate_multi_model_predictions(self, features: Dict, store_code: str = None) -> Dict:
        """Generate predictions using multiple models"""
        predictions = {}
        
        # Prepare feature vector
        feature_columns = self._get_feature_columns_from_dict(features)
        feature_vector = np.array([features.get(col, 0) for col in feature_columns]).reshape(1, -1)
        
        # Use trained models if available
        for target in ['daily_revenue', 'daily_contracts', 'party_revenue', 'construction_revenue']:
            model_key = f"{store_code or 'all'}_{target}"
            
            if model_key in self.models and model_key in self.scalers:
                try:
                    # Scale features
                    scaled_features = self.scalers[model_key].transform(feature_vector)
                    
                    # Make prediction
                    prediction = self.models[model_key].predict(scaled_features)[0]
                    predictions[target] = max(0, float(prediction))  # Ensure non-negative
                    
                except Exception as e:
                    self.logger.warning(f"Model prediction failed for {target}: {e}")
                    predictions[target] = self._fallback_prediction(target, features)
            else:
                predictions[target] = self._fallback_prediction(target, features)
        
        return predictions
    
    def _apply_business_rules(self, predictions: Dict, forecast_date: date, 
                            store_code: str = None) -> Dict:
        """Apply business rules and constraints to predictions"""
        adjusted_predictions = predictions.copy()
        
        # Minimum thresholds
        adjusted_predictions['daily_revenue'] = max(100, adjusted_predictions.get('daily_revenue', 0))
        adjusted_predictions['daily_contracts'] = max(1, int(adjusted_predictions.get('daily_contracts', 0)))
        
        # Consistency checks
        daily_revenue = adjusted_predictions['daily_revenue']
        daily_contracts = adjusted_predictions['daily_contracts']
        
        # Average contract value should be reasonable
        avg_contract_value = daily_revenue / daily_contracts if daily_contracts > 0 else 0
        if avg_contract_value > 2000:  # Unusually high
            adjusted_predictions['daily_contracts'] = max(1, int(daily_revenue / 500))  # Assume $500 avg
        elif avg_contract_value < 50:  # Unusually low
            adjusted_predictions['daily_revenue'] = daily_contracts * 150  # Assume $150 avg
        
        # Industry segment consistency
        party_revenue = adjusted_predictions.get('party_revenue', 0)
        construction_revenue = adjusted_predictions.get('construction_revenue', 0)
        
        segment_total = party_revenue + construction_revenue
        if segment_total > daily_revenue * 1.1:  # Allow 10% tolerance
            # Scale down segment revenues proportionally
            scale_factor = daily_revenue * 0.9 / segment_total
            adjusted_predictions['party_revenue'] = party_revenue * scale_factor
            adjusted_predictions['construction_revenue'] = construction_revenue * scale_factor
        
        # Weekend effects
        if forecast_date.weekday() >= 5:  # Weekend
            adjusted_predictions['party_revenue'] *= 1.3  # Higher party demand
            adjusted_predictions['construction_revenue'] *= 0.7  # Lower construction demand
        
        # Seasonal constraints
        month = forecast_date.month
        if month in [12, 1, 2, 3]:  # Winter months
            adjusted_predictions['party_revenue'] *= 0.6  # Reduced outdoor events
            adjusted_predictions['construction_revenue'] *= 0.4  # Reduced construction
        
        return adjusted_predictions
    
    def _calculate_confidence_intervals(self, predictions: Dict, features: Dict, 
                                      model_results: Dict, store_code: str = None) -> Dict:
        """Calculate confidence intervals for predictions"""
        confidence_intervals = {}
        
        for target, prediction in predictions.items():
            if target in model_results:
                target_results = model_results[target]
                
                # Use cross-validation MAE as uncertainty measure
                best_model = min(target_results.keys(), key=lambda k: target_results[k]['cv_mae'])
                mae = target_results[best_model]['cv_mae']
                
                # 80% confidence interval (±1.28 * MAE)
                lower_80 = max(0, prediction - 1.28 * mae)
                upper_80 = prediction + 1.28 * mae
                
                # 95% confidence interval (±1.96 * MAE)
                lower_95 = max(0, prediction - 1.96 * mae)
                upper_95 = prediction + 1.96 * mae
                
                confidence_intervals[target] = {
                    '80_percent': {'lower': round(lower_80, 2), 'upper': round(upper_80, 2)},
                    '95_percent': {'lower': round(lower_95, 2), 'upper': round(upper_95, 2)},
                    'prediction_uncertainty': round(mae, 2)
                }
            else:
                # Default uncertainty for simple models
                uncertainty = prediction * 0.3  # 30% uncertainty
                confidence_intervals[target] = {
                    '80_percent': {'lower': max(0, round(prediction - uncertainty, 2)), 
                                 'upper': round(prediction + uncertainty, 2)},
                    '95_percent': {'lower': max(0, round(prediction - 1.5 * uncertainty, 2)), 
                                 'upper': round(prediction + 1.5 * uncertainty, 2)},
                    'prediction_uncertainty': round(uncertainty, 2)
                }
        
        return confidence_intervals
    
    def _identify_risk_factors(self, weather_forecast: Dict, forecast_date: date) -> List[Dict]:
        """Identify risk factors that could affect the forecast"""
        risk_factors = []
        
        # Weather risks
        temp_high = weather_forecast.get('temperature_high', 70)
        precip_prob = weather_forecast.get('precipitation_probability', 0)
        wind_speed = self._extract_wind_speed(weather_forecast.get('wind_speed', '5 mph'))
        
        if temp_high > 90:
            risk_factors.append({
                'type': 'weather_risk',
                'factor': 'extreme_heat',
                'description': f'Very high temperature ({temp_high}°F) may reduce outdoor activity',
                'impact': 'medium',
                'affected_segments': ['party_event', 'construction_diy']
            })
        
        if temp_high < 40:
            risk_factors.append({
                'type': 'weather_risk',
                'factor': 'extreme_cold',
                'description': f'Very low temperature ({temp_high}°F) may reduce all outdoor activity',
                'impact': 'high',
                'affected_segments': ['party_event', 'construction_diy', 'landscaping']
            })
        
        if precip_prob > 60:
            risk_factors.append({
                'type': 'weather_risk',
                'factor': 'high_precipitation',
                'description': f'High precipitation probability ({precip_prob}%) may cancel outdoor events',
                'impact': 'high',
                'affected_segments': ['party_event']
            })
        
        if wind_speed > 20:
            risk_factors.append({
                'type': 'weather_risk',
                'factor': 'high_wind',
                'description': f'High wind speed ({wind_speed} mph) may affect tent/outdoor equipment',
                'impact': 'medium',
                'affected_segments': ['party_event']
            })
        
        # Seasonal risks
        month = forecast_date.month
        if month in [11, 12, 1, 2, 3] and temp_high > 60:
            risk_factors.append({
                'type': 'seasonal_anomaly',
                'factor': 'unusually_warm_winter',
                'description': 'Unusually warm weather for winter may increase demand',
                'impact': 'positive',
                'affected_segments': ['construction_diy']
            })
        
        # Day-of-week risks
        if forecast_date.weekday() == 0:  # Monday
            risk_factors.append({
                'type': 'temporal_risk',
                'factor': 'monday_effect',
                'description': 'Monday typically has lower rental demand',
                'impact': 'low',
                'affected_segments': ['all']
            })
        
        return risk_factors
    
    def _generate_daily_recommendations(self, predictions: Dict, weather_forecast: Dict) -> List[str]:
        """Generate daily recommendations based on predictions and weather"""
        recommendations = []
        
        daily_revenue = predictions.get('daily_revenue', 0)
        party_revenue = predictions.get('party_revenue', 0)
        construction_revenue = predictions.get('construction_revenue', 0)
        
        # Revenue-based recommendations
        if daily_revenue > 1500:
            recommendations.append("High demand expected - ensure adequate staffing")
        elif daily_revenue < 300:
            recommendations.append("Low demand expected - consider maintenance tasks")
        
        # Weather-based recommendations
        temp_high = weather_forecast.get('temperature_high', 70)
        precip_prob = weather_forecast.get('precipitation_probability', 0)
        
        if precip_prob > 50:
            recommendations.append("Rain likely - proactively contact outdoor event customers")
        
        if temp_high > 85 and party_revenue > construction_revenue:
            recommendations.append("Hot weather - ensure cooling equipment is available")
        
        # Segment-specific recommendations
        if party_revenue > daily_revenue * 0.6:
            recommendations.append("Party equipment focus day - prioritize event setup")
        
        if construction_revenue > daily_revenue * 0.6:
            recommendations.append("Construction equipment focus day - ensure power tools ready")
        
        return recommendations[:3]  # Top 3 recommendations
    
    # Helper methods
    
    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature columns for model training"""
        feature_columns = []
        
        # Always include these if available
        base_features = [
            'year', 'month', 'day_of_year', 'day_of_week', 'is_weekend', 'is_holiday',
            'season', 'is_wedding_season', 'is_construction_season', 'is_landscaping_season',
            'temperature_high', 'temperature_low', 'temperature_range',
            'is_hot_day', 'is_cold_day', 'is_comfortable_temp',
            'precipitation', 'is_rainy', 'is_heavy_rain',
            'wind_speed_avg', 'is_windy', 'is_very_windy',
            'weather_score'
        ]
        
        for col in base_features:
            if col in df.columns:
                feature_columns.append(col)
        
        # Add lag features if available
        for lag in [1, 2, 3, 7]:
            lag_cols = [f'revenue_lag_{lag}', f'weather_score_lag_{lag}', f'temp_lag_{lag}']
            for col in lag_cols:
                if col in df.columns:
                    feature_columns.append(col)
        
        # Add moving averages if available
        for window in [3, 7, 14]:
            ma_cols = [f'revenue_ma_{window}', f'weather_score_ma_{window}']
            for col in ma_cols:
                if col in df.columns:
                    feature_columns.append(col)
        
        # Add trend features
        if 'revenue_trend_7d' in df.columns:
            feature_columns.append('revenue_trend_7d')
        
        return feature_columns
    
    def _get_feature_columns_from_dict(self, features: Dict) -> List[str]:
        """Get feature column names from feature dictionary"""
        return list(features.keys())
    
    def _fallback_prediction(self, target: str, features: Dict) -> float:
        """Generate fallback prediction when models are unavailable"""
        # Simple rule-based predictions
        if target == 'daily_revenue':
            base = 400  # Base daily revenue
            weather_multiplier = features.get('weather_score', 0.8)
            seasonal_multiplier = 1.2 if features.get('is_wedding_season', 0) else 0.9
            return base * weather_multiplier * seasonal_multiplier
        
        elif target == 'daily_contracts':
            revenue = self._fallback_prediction('daily_revenue', features)
            return max(1, int(revenue / 200))  # Assume $200 avg contract
        
        elif target == 'party_revenue':
            total_revenue = self._fallback_prediction('daily_revenue', features)
            party_ratio = 0.4 if features.get('is_wedding_season', 0) else 0.2
            return total_revenue * party_ratio
        
        elif target == 'construction_revenue':
            total_revenue = self._fallback_prediction('daily_revenue', features)
            construction_ratio = 0.5 if features.get('is_construction_season', 0) else 0.3
            return total_revenue * construction_ratio
        
        return 0.0
    
    def _get_season_number(self, month: int) -> int:
        """Convert month to season number"""
        if month in [12, 1, 2]:
            return 0  # Winter
        elif month in [3, 4, 5]:
            return 1  # Spring
        elif month in [6, 7, 8]:
            return 2  # Summer
        else:
            return 3  # Fall
    
    def _categorize_weather_condition(self, condition: str) -> int:
        """Categorize weather condition into numeric value"""
        condition = condition.lower() if condition else ''
        
        if any(word in condition for word in ['sunny', 'clear', 'fair']):
            return 1  # Excellent
        elif any(word in condition for word in ['partly cloudy', 'mostly sunny']):
            return 2  # Good
        elif any(word in condition for word in ['cloudy', 'overcast']):
            return 3  # Fair
        elif any(word in condition for word in ['rain', 'drizzle', 'shower']):
            return 4  # Poor
        elif any(word in condition for word in ['storm', 'thunderstorm']):
            return 5  # Very poor
        else:
            return 3  # Default to fair
    
    def _calculate_composite_weather_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate composite weather score"""
        score = pd.Series(1.0, index=df.index)  # Start with perfect score
        
        # Temperature component
        if 'temperature_high' in df.columns:
            temp_score = 1.0 - (np.abs(df['temperature_high'] - 75) / 50).clip(0, 1)
            score *= temp_score
        
        # Precipitation component
        if 'precipitation' in df.columns:
            precip_score = 1.0 - (df['precipitation'] / 0.5).clip(0, 1)
            score *= precip_score
        
        # Wind component
        if 'wind_speed_avg' in df.columns:
            wind_score = 1.0 - ((df['wind_speed_avg'] - 5) / 20).clip(0, 1)
            score *= wind_score
        
        return score.clip(0, 1)
    
    def _calculate_weather_score_from_forecast(self, weather_forecast: Dict) -> float:
        """Calculate weather score from forecast data"""
        temp_high = weather_forecast.get('temperature_high', 75)
        precip_prob = weather_forecast.get('precipitation_probability', 0) / 100.0
        wind_speed = self._extract_wind_speed(weather_forecast.get('wind_speed', '5 mph'))
        
        # Temperature score
        temp_score = 1.0 - min(1.0, abs(temp_high - 75) / 50)
        
        # Precipitation score
        precip_score = 1.0 - min(1.0, precip_prob)
        
        # Wind score
        wind_score = 1.0 - min(1.0, max(0, wind_speed - 5) / 20)
        
        return (temp_score + precip_score + wind_score) / 3
    
    def _extract_wind_speed(self, wind_string: str) -> float:
        """Extract wind speed number from string"""
        import re
        if isinstance(wind_string, str):
            numbers = re.findall(r'\d+', wind_string)
            return float(numbers[0]) if numbers else 5.0
        return float(wind_string) if wind_string else 5.0
    
    def _identify_holidays(self, dates: pd.Series) -> pd.Series:
        """Identify holidays in date series"""
        # Simplified holiday detection for major US holidays
        holidays = pd.Series(False, index=dates.index)
        
        for i, date in enumerate(dates):
            month, day = date.month, date.day
            # Major holidays that affect rental business
            if (month == 1 and day == 1) or \
               (month == 7 and day == 4) or \
               (month == 11 and 22 <= day <= 28) or \
               (month == 12 and day == 25):
                holidays.iloc[i] = True
        
        return holidays
    
    def _is_holiday(self, date: date) -> bool:
        """Check if a single date is a holiday"""
        month, day = date.month, date.day
        return ((month == 1 and day == 1) or 
                (month == 7 and day == 4) or 
                (month == 11 and 22 <= day <= 28) or 
                (month == 12 and day == 25))
    
    def _calculate_trend(self, values: np.ndarray) -> float:
        """Calculate linear trend in values"""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        try:
            slope = np.polyfit(x, values, 1)[0]
            return float(slope)
        except:
            return 0.0
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic time features when weather data is not available"""
        if 'business_date' in df.columns:
            df['business_date'] = pd.to_datetime(df['business_date'])
            df['month'] = df['business_date'].dt.month
            df['day_of_week'] = df['business_date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        return df
    
    def _generate_forecast_summary(self, daily_forecasts: List[Dict], store_code: str = None) -> Dict:
        """Generate summary of forecast results"""
        if not daily_forecasts:
            return {}
        
        total_revenue = sum(f['predictions']['daily_revenue'] for f in daily_forecasts)
        total_contracts = sum(f['predictions']['daily_contracts'] for f in daily_forecasts)
        
        # Find peak day
        peak_day = max(daily_forecasts, key=lambda x: x['predictions']['daily_revenue'])
        low_day = min(daily_forecasts, key=lambda x: x['predictions']['daily_revenue'])
        
        # Count high-risk days
        high_risk_days = sum(1 for f in daily_forecasts 
                           if any(risk['impact'] == 'high' for risk in f.get('risk_factors', [])))
        
        return {
            'forecast_period': f"{daily_forecasts[0]['forecast_date']} to {daily_forecasts[-1]['forecast_date']}",
            'total_predicted_revenue': round(total_revenue, 2),
            'total_predicted_contracts': int(total_contracts),
            'avg_daily_revenue': round(total_revenue / len(daily_forecasts), 2),
            'avg_daily_contracts': round(total_contracts / len(daily_forecasts), 1),
            'peak_day': {
                'date': peak_day['forecast_date'],
                'revenue': peak_day['predictions']['daily_revenue'],
                'contracts': peak_day['predictions']['daily_contracts']
            },
            'low_day': {
                'date': low_day['forecast_date'],
                'revenue': low_day['predictions']['daily_revenue'],
                'contracts': low_day['predictions']['daily_contracts']
            },
            'revenue_variability': round(total_revenue / len(daily_forecasts) if daily_forecasts else 0, 2),
            'high_risk_days': high_risk_days,
            'weather_dependent_days': sum(1 for f in daily_forecasts 
                                        if f['predictions']['daily_revenue'] != f.get('base_revenue', 0))
        }
    
    def _generate_forecast_insights(self, daily_forecasts: List[Dict], forecast_summary: Dict) -> List[str]:
        """Generate business insights from forecast results"""
        insights = []
        
        if not daily_forecasts:
            return insights
        
        # Revenue insights
        avg_revenue = forecast_summary.get('avg_daily_revenue', 0)
        if avg_revenue > 1000:
            insights.append("Strong demand period expected - ensure adequate inventory")
        elif avg_revenue < 300:
            insights.append("Low demand period - good time for maintenance and preparation")
        
        # Weather insights
        rainy_days = sum(1 for f in daily_forecasts 
                        if any('precipitation' in risk['factor'] for risk in f.get('risk_factors', [])))
        if rainy_days > len(daily_forecasts) * 0.4:
            insights.append("Multiple rainy days expected - prepare indoor alternatives")
        
        # Peak day insights
        peak_revenue = forecast_summary.get('peak_day', {}).get('revenue', 0)
        low_revenue = forecast_summary.get('low_day', {}).get('revenue', 0)
        if peak_revenue > low_revenue * 2:
            insights.append("High demand variability - flexible staffing recommended")
        
        # Risk insights
        high_risk_days = forecast_summary.get('high_risk_days', 0)
        if high_risk_days > 0:
            insights.append(f"{high_risk_days} high-risk days identified - monitor weather closely")
        
        return insights[:5]  # Top 5 insights
    
    def _store_demand_forecasts(self, daily_forecasts: List[Dict], store_code: str = None) -> bool:
        """Store demand forecasts in database"""
        try:
            for forecast in daily_forecasts:
                forecast_date = datetime.fromisoformat(forecast['forecast_date']).date()
                predictions = forecast['predictions']
                
                # Check if forecast already exists
                existing = db.session.query(WeatherForecastDemand).filter(
                    and_(
                        WeatherForecastDemand.forecast_date == forecast_date,
                        WeatherForecastDemand.store_code == store_code,
                        WeatherForecastDemand.industry_segment == 'all'
                    )
                ).first()
                
                if existing:
                    # Update existing forecast
                    existing.predicted_demand_revenue = Decimal(str(predictions['daily_revenue']))
                    existing.predicted_demand_units = predictions['daily_contracts']
                    existing.expected_weather_conditions = forecast['weather_conditions']
                    existing.forecast_generated_at = datetime.now(timezone.utc)
                else:
                    # Create new forecast
                    new_forecast = WeatherForecastDemand(
                        forecast_date=forecast_date,
                        forecast_generated_at=datetime.now(timezone.utc),
                        forecast_horizon_days=forecast['days_ahead'],
                        store_code=store_code,
                        industry_segment='all',
                        predicted_demand_revenue=Decimal(str(predictions['daily_revenue'])),
                        predicted_demand_units=predictions['daily_contracts'],
                        expected_weather_conditions=forecast['weather_conditions'],
                        confidence_level=Decimal('0.8'),
                        model_version='weather_ml_v1'
                    )
                    db.session.add(new_forecast)
            
            db.session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store demand forecasts: {e}")
            db.session.rollback()
            return False
    
    def _get_prediction_metrics(self, predictions: Dict, model_results: Dict) -> Dict:
        """Get metrics for predictions"""
        metrics = {}
        
        for target, prediction in predictions.items():
            if target in model_results and model_results[target]:
                best_model = min(model_results[target].keys(), 
                               key=lambda k: model_results[target][k]['cv_mae'])
                metrics[target] = {
                    'model_used': best_model,
                    'cross_val_mae': model_results[target][best_model]['cv_mae'],
                    'confidence': 'high' if model_results[target][best_model]['cv_mae'] < prediction * 0.2 else 'medium'
                }
            else:
                metrics[target] = {
                    'model_used': 'fallback',
                    'confidence': 'low'
                }
        
        return metrics