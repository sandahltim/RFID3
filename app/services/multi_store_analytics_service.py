"""
Multi-Store Analytics Service
Analyzes regional demand patterns across Minnesota stores
Provides store comparison and transfer recommendations
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
from app.models.weather_models import StoreRegionalAnalytics, WeatherRentalCorrelation
from app.models.pos_models import POSTransaction, POSTransactionItem, POSEquipment
import json
from decimal import Decimal

logger = get_logger(__name__)

class MultiStoreAnalyticsService:
    """Service for multi-store comparison and regional demand analysis"""
    
    # Minnesota store geographic and market data
    STORE_GEOGRAPHIC_DATA = {
        '3607': {
            'name': 'Wayzata',
            'coordinates': (44.9733, -93.5066),
            'county': 'Hennepin',
            'market_characteristics': {
                'affluent_suburban': True,
                'lake_access': True,
                'high_event_demand': True,
                'premium_pricing_tolerance': 'high'
            },
            'competition_analysis': {
                'direct_competitors': 3,
                'market_saturation': 0.7,
                'competitive_advantage': 'premium_service'
            },
            'customer_demographics': {
                'median_household_income': 85000,
                'age_profile': 'mixed_affluent',
                'event_frequency': 'high'
            }
        },
        '6800': {
            'name': 'Brooklyn Park',
            'coordinates': (45.0941, -93.3563),
            'county': 'Hennepin',
            'market_characteristics': {
                'suburban_mixed': True,
                'family_oriented': True,
                'construction_demand': True,
                'premium_pricing_tolerance': 'medium'
            },
            'competition_analysis': {
                'direct_competitors': 2,
                'market_saturation': 0.5,
                'competitive_advantage': 'convenience'
            },
            'customer_demographics': {
                'median_household_income': 68000,
                'age_profile': 'family_focused',
                'event_frequency': 'medium'
            }
        },
        '728': {
            'name': 'Elk River',  # CORRECTED - 728 is Elk River not Fridley
            'coordinates': (45.3033, -93.5677),  # CORRECTED coordinates
            'county': 'Sherburne',  # CORRECTED county
            'market_characteristics': {
                'rural_suburban': True,  # CORRECTED characteristics
                'agricultural_support': True,
                'diy_homeowner_base': True,
                'premium_pricing_tolerance': 'medium'
            },
            'competition_analysis': {
                'direct_competitors': 2,  # CORRECTED for rural market
                'market_saturation': 0.4,  # CORRECTED - less saturated rural market
                'competitive_advantage': 'rural_accessibility'  # CORRECTED
            },
            'customer_demographics': {
                'median_household_income': 75000,  # CORRECTED - rural areas higher due to property values
                'age_profile': 'rural_mixed',  # CORRECTED
                'event_frequency': 'low'
            }
        },
        '8101': {
            'name': 'Fridley',  # CORRECTED - 8101 is Fridley not Elk River
            'coordinates': (45.0863, -93.2636),  # CORRECTED coordinates  
            'county': 'Anoka',  # CORRECTED county
            'address': '8101 Ashton Ave NE, Fridley, MN',  # VERIFIED from web research
            'brand': 'Broadway Tent & Event',  # CORRECTED brand
            'market_characteristics': {
                'events_focused': True,  # CORRECTED - pure events location
                'wedding_venues_nearby': True,
                'corporate_event_demand': True,
                'premium_pricing_tolerance': 'high'  # Events allow higher pricing
            },
            'competition_analysis': {
                'direct_competitors': 3,  # CORRECTED for events market
                'market_saturation': 0.6,  # CORRECTED - competitive events market
                'competitive_advantage': '50_year_expertise'  # CORRECTED
            },
            'customer_demographics': {
                'median_household_income': 68000,  # CORRECTED for Fridley
                'age_profile': 'event_planners_families',  # CORRECTED
                'event_frequency': 'high'  # CORRECTED - pure events location
            }
        }
    }
    
    def __init__(self):
        self.logger = logger
        self.weather_service = MinnesotaWeatherService()
        self.industry_service = MinnesotaIndustryAnalytics()
    
    def analyze_regional_demand_patterns(self, analysis_period_days: int = 365) -> Dict:
        """Analyze demand patterns across all Minnesota stores"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=analysis_period_days)
            
            self.logger.info(f"Analyzing regional demand patterns from {start_date} to {end_date}")
            
            # Get comprehensive store performance data
            store_performance = self._get_store_performance_data(start_date, end_date)
            
            # Analyze industry segment distribution by store
            industry_distribution = self._analyze_industry_distribution_by_store()
            
            # Calculate regional benchmarks
            regional_benchmarks = self._calculate_regional_benchmarks(store_performance)
            
            # Analyze seasonal patterns by store
            seasonal_patterns = self._analyze_seasonal_patterns_by_store(start_date, end_date)
            
            # Weather impact analysis by store
            weather_impacts = self._analyze_weather_impact_by_store(start_date, end_date)
            
            # Generate transfer recommendations
            transfer_recommendations = self._generate_transfer_recommendations(
                store_performance, industry_distribution
            )
            
            # Market opportunity analysis
            market_opportunities = self._analyze_market_opportunities()
            
            results = {
                'analysis_period': f"{start_date} to {end_date}",
                'store_performance': store_performance,
                'industry_distribution': industry_distribution,
                'regional_benchmarks': regional_benchmarks,
                'seasonal_patterns': seasonal_patterns,
                'weather_impacts': weather_impacts,
                'transfer_recommendations': transfer_recommendations,
                'market_opportunities': market_opportunities,
                'insights': self._generate_regional_insights(
                    store_performance, industry_distribution, seasonal_patterns
                ),
                'timestamp': datetime.now().isoformat()
            }
            
            # Store results in database
            self._store_regional_analytics(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Regional demand pattern analysis failed: {e}")
            return {'error': str(e)}
    
    def _get_store_performance_data(self, start_date: date, end_date: date) -> Dict:
        """Get comprehensive performance data for all stores"""
        
        query = text("""
            SELECT 
                pt.store_no,
                COUNT(DISTINCT pt.contract_no) as total_contracts,
                SUM(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as total_revenue,
                AVG(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as avg_contract_value,
                COUNT(DISTINCT pt.customer_no) as unique_customers,
                COUNT(pti.id) as total_items_rented,
                
                -- Monthly metrics
                SUM(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) / 
                    DATEDIFF(:end_date, :start_date) * 30 as avg_monthly_revenue,
                
                -- Customer metrics
                SUM(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) / 
                    NULLIF(COUNT(DISTINCT pt.customer_no), 0) as revenue_per_customer,
                
                -- Item metrics
                AVG(pti.qty) as avg_items_per_contract,
                
                -- Timing metrics
                AVG(DATEDIFF(pt.actual_pickup_date, pt.actual_delivery_date)) as avg_rental_duration,
                
                -- Recent performance (last 30 days)
                SUM(CASE WHEN pt.contract_date >= DATE_SUB(:end_date, INTERVAL 30 DAY) 
                    THEN COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0) ELSE 0 END) as last_30_days_revenue
                
            FROM pos_transactions pt
            JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
            WHERE pt.contract_date BETWEEN :start_date AND :end_date
                AND pt.store_no IN ('3607', '6800', '728', '8101')
            GROUP BY pt.store_no
            ORDER BY total_revenue DESC
        """)
        
        performance_df = pd.read_sql(query, db.engine, params={
            'start_date': start_date,
            'end_date': end_date
        })
        
        if performance_df.empty:
            return {}
        
        store_performance = {}
        total_system_revenue = performance_df['total_revenue'].sum()
        
        for _, row in performance_df.iterrows():
            store_code = row['store_no']
            
            # Calculate performance metrics
            revenue_share = (row['total_revenue'] / total_system_revenue * 100) if total_system_revenue > 0 else 0
            
            # Get store geographic data
            geo_data = self.STORE_GEOGRAPHIC_DATA.get(store_code, {})
            
            store_performance[store_code] = {
                'store_name': geo_data.get('name', f'Store {store_code}'),
                'basic_metrics': {
                    'total_contracts': int(row['total_contracts']),
                    'total_revenue': float(row['total_revenue']),
                    'avg_contract_value': float(row['avg_contract_value']),
                    'unique_customers': int(row['unique_customers']),
                    'total_items_rented': int(row['total_items_rented'])
                },
                'performance_ratios': {
                    'revenue_share_percentage': round(revenue_share, 2),
                    'revenue_per_customer': float(row['revenue_per_customer']),
                    'avg_items_per_contract': float(row['avg_items_per_contract']),
                    'avg_rental_duration_days': float(row['avg_rental_duration']) if row['avg_rental_duration'] else 0
                },
                'trend_indicators': {
                    'avg_monthly_revenue': float(row['avg_monthly_revenue']),
                    'last_30_days_revenue': float(row['last_30_days_revenue']),
                    'momentum_score': self._calculate_momentum_score(row)
                },
                'geographic_data': geo_data,
                'market_position': self._assess_market_position(store_code, row, performance_df)
            }
        
        return store_performance
    
    def _analyze_industry_distribution_by_store(self) -> Dict:
        """Analyze how industry segments are distributed across stores"""
        
        query = text("""
            SELECT 
                pe.current_store as store_code,
                ec.industry_segment,
                COUNT(*) as item_count,
                SUM(pe.turnover_ytd) as ytd_revenue,
                AVG(pe.turnover_ytd) as avg_revenue_per_item,
                COUNT(CASE WHEN ec.weather_dependent = 1 THEN 1 END) as weather_dependent_count
            FROM pos_equipment pe
            JOIN equipment_categorization ec ON pe.item_num = ec.item_num
            WHERE pe.inactive = 0 
                AND pe.current_store IN ('3607', '6800', '728', '8101')
                AND ec.industry_segment IS NOT NULL
            GROUP BY pe.current_store, ec.industry_segment
            ORDER BY pe.current_store, ytd_revenue DESC
        """)
        
        distribution_df = pd.read_sql(query, db.engine)
        
        if distribution_df.empty:
            return {}
        
        industry_distribution = {}
        
        for store_code in ['3607', '6800', '728', '8101']:
            store_data = distribution_df[distribution_df['store_code'] == store_code]
            
            if store_data.empty:
                continue
            
            total_items = store_data['item_count'].sum()
            total_revenue = store_data['ytd_revenue'].sum()
            
            segments = {}
            for _, row in store_data.iterrows():
                segment = row['industry_segment']
                segments[segment] = {
                    'item_count': int(row['item_count']),
                    'item_percentage': round((row['item_count'] / total_items * 100), 2) if total_items > 0 else 0,
                    'ytd_revenue': float(row['ytd_revenue']),
                    'revenue_percentage': round((row['ytd_revenue'] / total_revenue * 100), 2) if total_revenue > 0 else 0,
                    'avg_revenue_per_item': float(row['avg_revenue_per_item']),
                    'weather_dependent_count': int(row['weather_dependent_count'])
                }
            
            # Calculate specialization scores
            specialization_score = self._calculate_specialization_score(segments)
            diversity_score = 1.0 - specialization_score
            
            industry_distribution[store_code] = {
                'store_name': self.STORE_GEOGRAPHIC_DATA.get(store_code, {}).get('name', f'Store {store_code}'),
                'segments': segments,
                'summary': {
                    'total_items': int(total_items),
                    'total_revenue': float(total_revenue),
                    'primary_segment': max(segments.keys(), key=lambda k: segments[k]['revenue_percentage']),
                    'specialization_score': round(specialization_score, 3),
                    'diversity_score': round(diversity_score, 3),
                    'weather_dependency_ratio': round(sum(seg['weather_dependent_count'] for seg in segments.values()) / total_items, 3) if total_items > 0 else 0
                }
            }
        
        return industry_distribution
    
    def _calculate_specialization_score(self, segments: Dict) -> float:
        """Calculate how specialized a store is (0 = diverse, 1 = highly specialized)"""
        if not segments:
            return 0.0
        
        revenue_percentages = [seg['revenue_percentage'] for seg in segments.values()]
        
        # Calculate Herfindahl-Hirschman Index (normalized)
        hhi = sum((pct / 100) ** 2 for pct in revenue_percentages)
        
        # Normalize to 0-1 scale (perfect specialization would be 1.0)
        return hhi
    
    def _calculate_regional_benchmarks(self, store_performance: Dict) -> Dict:
        """Calculate regional benchmarks and performance rankings"""
        
        if not store_performance:
            return {}
        
        # Extract metrics for benchmarking
        metrics = {
            'total_revenue': [],
            'avg_contract_value': [],
            'revenue_per_customer': [],
            'avg_items_per_contract': [],
            'avg_monthly_revenue': []
        }
        
        store_metrics = {}
        for store_code, perf in store_performance.items():
            store_metrics[store_code] = {}
            
            # Basic metrics
            store_metrics[store_code]['total_revenue'] = perf['basic_metrics']['total_revenue']
            store_metrics[store_code]['avg_contract_value'] = perf['basic_metrics']['avg_contract_value']
            
            # Performance ratios
            store_metrics[store_code]['revenue_per_customer'] = perf['performance_ratios']['revenue_per_customer']
            store_metrics[store_code]['avg_items_per_contract'] = perf['performance_ratios']['avg_items_per_contract']
            
            # Trend indicators
            store_metrics[store_code]['avg_monthly_revenue'] = perf['trend_indicators']['avg_monthly_revenue']
            
            # Add to benchmark lists
            for metric in metrics:
                metrics[metric].append(store_metrics[store_code][metric])
        
        # Calculate benchmarks
        benchmarks = {}
        for metric, values in metrics.items():
            if values:
                benchmarks[metric] = {
                    'mean': round(float(np.mean(values)), 2),
                    'median': round(float(np.median(values)), 2),
                    'std': round(float(np.std(values)), 2),
                    'min': round(float(np.min(values)), 2),
                    'max': round(float(np.max(values)), 2)
                }
        
        # Rank stores by each metric
        rankings = {}
        for metric in metrics:
            if metrics[metric]:
                store_rankings = sorted(store_metrics.keys(), 
                                      key=lambda store: store_metrics[store][metric], 
                                      reverse=True)
                rankings[metric] = {f"rank_{i+1}": store for i, store in enumerate(store_rankings)}
        
        # Calculate composite performance scores
        performance_scores = {}
        for store_code in store_metrics:
            # Normalize metrics and calculate weighted score
            score = 0
            weights = {
                'total_revenue': 0.3,
                'avg_contract_value': 0.2,
                'revenue_per_customer': 0.2,
                'avg_items_per_contract': 0.15,
                'avg_monthly_revenue': 0.15
            }
            
            for metric, weight in weights.items():
                if benchmarks[metric]['max'] > benchmarks[metric]['min']:
                    normalized_score = (store_metrics[store_code][metric] - benchmarks[metric]['min']) / (benchmarks[metric]['max'] - benchmarks[metric]['min'])
                    score += normalized_score * weight
            
            performance_scores[store_code] = round(score, 3)
        
        return {
            'benchmarks': benchmarks,
            'rankings': rankings,
            'performance_scores': performance_scores,
            'top_performer': max(performance_scores, key=performance_scores.get),
            'benchmark_insights': self._generate_benchmark_insights(benchmarks, rankings, performance_scores)
        }
    
    def _analyze_seasonal_patterns_by_store(self, start_date: date, end_date: date) -> Dict:
        """Analyze seasonal demand patterns for each store"""
        
        query = text("""
            SELECT 
                pt.store_no,
                MONTH(pt.contract_date) as month,
                ec.industry_segment,
                COUNT(pt.contract_no) as contract_count,
                SUM(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as monthly_revenue
            FROM pos_transactions pt
            JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
            LEFT JOIN equipment_categorization ec ON pti.item_num = ec.item_num
            WHERE pt.contract_date BETWEEN :start_date AND :end_date
                AND pt.store_no IN ('3607', '6800', '728', '8101')
            GROUP BY pt.store_no, MONTH(pt.contract_date), ec.industry_segment
            ORDER BY pt.store_no, month
        """)
        
        seasonal_df = pd.read_sql(query, db.engine, params={
            'start_date': start_date,
            'end_date': end_date
        })
        
        if seasonal_df.empty:
            return {}
        
        seasonal_patterns = {}
        
        for store_code in ['3607', '6800', '728', '8101']:
            store_data = seasonal_df[seasonal_df['store_no'] == store_code]
            
            if store_data.empty:
                continue
            
            # Aggregate by month across all segments
            monthly_totals = store_data.groupby('month').agg({
                'contract_count': 'sum',
                'monthly_revenue': 'sum'
            })
            
            # Calculate seasonal indices (average = 1.0)
            avg_monthly_contracts = monthly_totals['contract_count'].mean()
            avg_monthly_revenue = monthly_totals['monthly_revenue'].mean()
            
            monthly_patterns = {}
            for month in range(1, 13):
                if month in monthly_totals.index:
                    contracts = monthly_totals.loc[month, 'contract_count']
                    revenue = monthly_totals.loc[month, 'monthly_revenue']
                    
                    contract_index = contracts / avg_monthly_contracts if avg_monthly_contracts > 0 else 1.0
                    revenue_index = revenue / avg_monthly_revenue if avg_monthly_revenue > 0 else 1.0
                else:
                    contract_index = 0.5  # Below average for missing months
                    revenue_index = 0.5
                
                monthly_patterns[month] = {
                    'month_name': self._get_month_name(month),
                    'contract_index': round(contract_index, 2),
                    'revenue_index': round(revenue_index, 2),
                    'seasonality_strength': abs(contract_index - 1.0)
                }
            
            # Identify peak and low seasons
            peak_months = sorted(monthly_patterns.keys(), 
                               key=lambda m: monthly_patterns[m]['revenue_index'], 
                               reverse=True)[:3]
            low_months = sorted(monthly_patterns.keys(), 
                              key=lambda m: monthly_patterns[m]['revenue_index'])[:3]
            
            seasonal_patterns[store_code] = {
                'store_name': self.STORE_GEOGRAPHIC_DATA.get(store_code, {}).get('name', f'Store {store_code}'),
                'monthly_patterns': monthly_patterns,
                'peak_season': {
                    'months': peak_months,
                    'month_names': [self._get_month_name(m) for m in peak_months],
                    'avg_revenue_index': round(np.mean([monthly_patterns[m]['revenue_index'] for m in peak_months]), 2)
                },
                'low_season': {
                    'months': low_months,
                    'month_names': [self._get_month_name(m) for m in low_months],
                    'avg_revenue_index': round(np.mean([monthly_patterns[m]['revenue_index'] for m in low_months]), 2)
                },
                'seasonality_strength': round(np.std([monthly_patterns[m]['revenue_index'] for m in monthly_patterns]), 2)
            }
        
        return seasonal_patterns
    
    def _analyze_weather_impact_by_store(self, start_date: date, end_date: date) -> Dict:
        """Analyze how weather differently impacts each store"""
        
        weather_impacts = {}
        
        for store_code in ['3607', '6800', '728', '8101']:
            try:
                # Get weather correlation data for this store
                from app.services.weather_correlation_service import WeatherCorrelationService
                weather_correlation_service = WeatherCorrelationService()
                
                store_weather_analysis = weather_correlation_service.analyze_weather_rental_correlations(
                    store_code=store_code,
                    industry_segment='all',
                    days_back=(end_date - start_date).days
                )
                
                if store_weather_analysis.get('status') == 'success':
                    correlations = store_weather_analysis.get('correlations', {})
                    
                    # Extract key weather sensitivities
                    weather_sensitivity = {
                        'temperature_sensitivity': self._extract_weather_sensitivity(correlations, 'temperature_high'),
                        'precipitation_sensitivity': self._extract_weather_sensitivity(correlations, 'precipitation'),
                        'weather_score_correlation': self._extract_weather_sensitivity(correlations, 'weather_score'),
                        'overall_weather_dependency': self._calculate_overall_weather_dependency(correlations)
                    }
                    
                    weather_impacts[store_code] = {
                        'store_name': self.STORE_GEOGRAPHIC_DATA.get(store_code, {}).get('name', f'Store {store_code}'),
                        'weather_sensitivity': weather_sensitivity,
                        'primary_weather_driver': self._identify_primary_weather_driver(correlations),
                        'weather_insights': store_weather_analysis.get('insights', [])[:3]  # Top 3 insights
                    }
                else:
                    weather_impacts[store_code] = {
                        'store_name': self.STORE_GEOGRAPHIC_DATA.get(store_code, {}).get('name', f'Store {store_code}'),
                        'error': 'Weather analysis not available'
                    }
                    
            except Exception as e:
                self.logger.warning(f"Weather impact analysis failed for store {store_code}: {e}")
                weather_impacts[store_code] = {
                    'store_name': self.STORE_GEOGRAPHIC_DATA.get(store_code, {}).get('name', f'Store {store_code}'),
                    'error': str(e)
                }
        
        return weather_impacts
    
    def _generate_transfer_recommendations(self, store_performance: Dict, 
                                         industry_distribution: Dict) -> List[Dict]:
        """Generate equipment transfer recommendations between stores"""
        
        recommendations = []
        
        # Analyze inventory efficiency by segment
        for segment in ['party_event', 'construction_diy', 'landscaping']:
            segment_analysis = {}
            
            for store_code in store_performance.keys():
                if store_code in industry_distribution:
                    segments = industry_distribution[store_code]['segments']
                    if segment in segments:
                        seg_data = segments[segment]
                        
                        # Calculate revenue efficiency (revenue per item)
                        efficiency = seg_data['avg_revenue_per_item']
                        
                        segment_analysis[store_code] = {
                            'efficiency': efficiency,
                            'item_count': seg_data['item_count'],
                            'revenue': seg_data['ytd_revenue']
                        }
            
            if len(segment_analysis) >= 2:
                # Find underperforming and overperforming stores
                sorted_stores = sorted(segment_analysis.keys(), 
                                     key=lambda store: segment_analysis[store]['efficiency'])
                
                underperformer = sorted_stores[0]
                overperformer = sorted_stores[-1]
                
                # Check if there's a significant efficiency gap
                efficiency_ratio = (segment_analysis[overperformer]['efficiency'] / 
                                  segment_analysis[underperformer]['efficiency'])
                
                if (efficiency_ratio > 1.5 and 
                    segment_analysis[overperformer]['item_count'] > 5 and
                    segment_analysis[underperformer]['item_count'] < segment_analysis[overperformer]['item_count']):
                    
                    recommendation = {
                        'type': 'equipment_transfer',
                        'from_store': overperformer,
                        'from_store_name': self.STORE_GEOGRAPHIC_DATA.get(overperformer, {}).get('name', overperformer),
                        'to_store': underperformer,
                        'to_store_name': self.STORE_GEOGRAPHIC_DATA.get(underperformer, {}).get('name', underperformer),
                        'equipment_segment': segment,
                        'rationale': f"Transfer {segment} equipment from high-efficiency to low-efficiency store",
                        'efficiency_gap': round(efficiency_ratio, 2),
                        'estimated_impact': 'medium',
                        'priority': 'medium' if efficiency_ratio < 2.0 else 'high'
                    }
                    
                    recommendations.append(recommendation)
        
        # Geographic proximity recommendations
        geographic_recommendations = self._generate_geographic_recommendations(
            store_performance, industry_distribution
        )
        recommendations.extend(geographic_recommendations)
        
        # Seasonal transfer recommendations
        seasonal_recommendations = self._generate_seasonal_recommendations(industry_distribution)
        recommendations.extend(seasonal_recommendations)
        
        # Rank recommendations by priority and impact
        recommendations.sort(key=lambda r: (
            {'high': 3, 'medium': 2, 'low': 1}[r.get('priority', 'low')],
            {'high': 3, 'medium': 2, 'low': 1}[r.get('estimated_impact', 'low')]
        ), reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _generate_geographic_recommendations(self, store_performance: Dict, 
                                           industry_distribution: Dict) -> List[Dict]:
        """Generate recommendations based on geographic proximity and market coverage"""
        
        recommendations = []
        
        # Example: Twin Cities metro stores can share inventory more easily
        metro_stores = ['3607', '6800', '728']  # Wayzata, Brooklyn Park, Fridley
        rural_store = '8101'  # Elk River
        
        # Check if Elk River needs support from metro area
        if rural_store in store_performance and rural_store in industry_distribution:
            elk_river_performance = store_performance[rural_store]
            elk_river_revenue_share = elk_river_performance['performance_ratios']['revenue_share_percentage']
            
            if elk_river_revenue_share < 15:  # If Elk River has low market share
                # Find best metro store to support it
                best_metro_store = None
                best_performance = 0
                
                for metro_store in metro_stores:
                    if metro_store in store_performance:
                        metro_perf = store_performance[metro_store]['basic_metrics']['total_revenue']
                        if metro_perf > best_performance:
                            best_performance = metro_perf
                            best_metro_store = metro_store
                
                if best_metro_store:
                    recommendations.append({
                        'type': 'geographic_support',
                        'from_store': best_metro_store,
                        'from_store_name': self.STORE_GEOGRAPHIC_DATA.get(best_metro_store, {}).get('name', best_metro_store),
                        'to_store': rural_store,
                        'to_store_name': self.STORE_GEOGRAPHIC_DATA.get(rural_store, {}).get('name', rural_store),
                        'rationale': 'Support rural store with metro area inventory during peak demand',
                        'estimated_impact': 'medium',
                        'priority': 'medium'
                    })
        
        return recommendations
    
    def _generate_seasonal_recommendations(self, industry_distribution: Dict) -> List[Dict]:
        """Generate seasonal transfer recommendations"""
        
        recommendations = []
        current_month = datetime.now().month
        
        # Spring/summer party equipment transfers
        if current_month in [3, 4, 5]:  # Spring preparation
            party_stores = []
            
            for store_code, data in industry_distribution.items():
                segments = data['segments']
                if 'party_event' in segments:
                    party_efficiency = segments['party_event']['avg_revenue_per_item']
                    party_stores.append((store_code, party_efficiency))
            
            if len(party_stores) >= 2:
                party_stores.sort(key=lambda x: x[1], reverse=True)
                top_performer = party_stores[0]
                bottom_performer = party_stores[-1]
                
                if top_performer[1] > bottom_performer[1] * 1.3:
                    recommendations.append({
                        'type': 'seasonal_transfer',
                        'from_store': top_performer[0],
                        'from_store_name': self.STORE_GEOGRAPHIC_DATA.get(top_performer[0], {}).get('name', top_performer[0]),
                        'to_store': bottom_performer[0],
                        'to_store_name': self.STORE_GEOGRAPHIC_DATA.get(bottom_performer[0], {}).get('name', bottom_performer[0]),
                        'equipment_segment': 'party_event',
                        'rationale': 'Prepare for wedding/event season by redistributing party equipment',
                        'seasonal_timing': 'spring_preparation',
                        'estimated_impact': 'high',
                        'priority': 'high'
                    })
        
        return recommendations
    
    def _analyze_market_opportunities(self) -> Dict:
        """Analyze market opportunities across all stores"""
        
        opportunities = {}
        
        for store_code, geo_data in self.STORE_GEOGRAPHIC_DATA.items():
            store_opportunities = []
            
            market_char = geo_data.get('market_characteristics', {})
            competition = geo_data.get('competition_analysis', {})
            demographics = geo_data.get('customer_demographics', {})
            
            # Market saturation opportunity
            if competition.get('market_saturation', 0) < 0.6:
                store_opportunities.append({
                    'type': 'market_expansion',
                    'description': 'Low market saturation - opportunity for growth',
                    'potential': 'high'
                })
            
            # Premium pricing opportunity
            if (demographics.get('median_household_income', 0) > 70000 and 
                market_char.get('premium_pricing_tolerance') == 'high'):
                store_opportunities.append({
                    'type': 'premium_pricing',
                    'description': 'Affluent market - opportunity for premium service offerings',
                    'potential': 'medium'
                })
            
            # Geographic advantage
            if competition.get('competitive_advantage') == 'geographic_coverage':
                store_opportunities.append({
                    'type': 'geographic_expansion',
                    'description': 'Geographic advantage - expand coverage area',
                    'potential': 'medium'
                })
            
            # Specialized service opportunity
            if market_char.get('high_event_demand'):
                store_opportunities.append({
                    'type': 'service_specialization',
                    'description': 'High event demand - specialize in event services',
                    'potential': 'high'
                })
            
            opportunities[store_code] = {
                'store_name': geo_data.get('name', f'Store {store_code}'),
                'opportunities': store_opportunities,
                'market_potential_score': len([opp for opp in store_opportunities if opp['potential'] == 'high']) * 0.5 + 
                                          len([opp for opp in store_opportunities if opp['potential'] == 'medium']) * 0.3
            }
        
        return opportunities
    
    # Helper methods
    
    def _calculate_momentum_score(self, row) -> float:
        """Calculate momentum score based on recent vs historical performance"""
        monthly_avg = row['avg_monthly_revenue']
        last_30_days = row['last_30_days_revenue']
        
        if monthly_avg <= 0:
            return 0.0
        
        momentum = (last_30_days / monthly_avg)
        return round(min(2.0, max(0.0, momentum)), 2)
    
    def _assess_market_position(self, store_code: str, row, all_stores_df) -> Dict:
        """Assess market position relative to other stores"""
        
        total_revenue = row['total_revenue']
        all_revenues = all_stores_df['total_revenue'].tolist()
        
        rank = sorted(all_revenues, reverse=True).index(total_revenue) + 1
        percentile = (len(all_revenues) - rank + 1) / len(all_revenues) * 100
        
        if percentile >= 75:
            position = 'market_leader'
        elif percentile >= 50:
            position = 'strong_performer'
        elif percentile >= 25:
            position = 'average_performer'
        else:
            position = 'underperformer'
        
        return {
            'rank': rank,
            'percentile': round(percentile, 1),
            'position': position
        }
    
    def _extract_weather_sensitivity(self, correlations: Dict, weather_factor: str) -> Dict:
        """Extract weather sensitivity metrics for a specific factor"""
        if weather_factor not in correlations:
            return {'sensitivity': 'unknown', 'correlation': 0.0}
        
        revenue_corr = correlations[weather_factor].get('daily_revenue', {})
        correlation = revenue_corr.get('pearson_correlation', 0.0)
        is_significant = revenue_corr.get('is_significant', False)
        
        if not is_significant:
            sensitivity = 'low'
        elif abs(correlation) > 0.6:
            sensitivity = 'high'
        elif abs(correlation) > 0.3:
            sensitivity = 'medium'
        else:
            sensitivity = 'low'
        
        return {
            'sensitivity': sensitivity,
            'correlation': round(correlation, 3),
            'is_significant': is_significant
        }
    
    def _calculate_overall_weather_dependency(self, correlations: Dict) -> float:
        """Calculate overall weather dependency score"""
        significant_correlations = []
        
        for weather_factor, business_metrics in correlations.items():
            for business_metric, correlation_data in business_metrics.items():
                if correlation_data.get('is_significant'):
                    significant_correlations.append(abs(correlation_data['pearson_correlation']))
        
        if not significant_correlations:
            return 0.0
        
        return round(np.mean(significant_correlations), 3)
    
    def _identify_primary_weather_driver(self, correlations: Dict) -> str:
        """Identify the primary weather factor affecting this store"""
        max_correlation = 0
        primary_driver = 'none'
        
        for weather_factor, business_metrics in correlations.items():
            revenue_data = business_metrics.get('daily_revenue', {})
            if revenue_data.get('is_significant'):
                correlation = abs(revenue_data['pearson_correlation'])
                if correlation > max_correlation:
                    max_correlation = correlation
                    primary_driver = weather_factor
        
        return primary_driver.replace('_', ' ').title() if primary_driver != 'none' else 'None'
    
    def _generate_benchmark_insights(self, benchmarks: Dict, rankings: Dict, 
                                   performance_scores: Dict) -> List[str]:
        """Generate insights from benchmark analysis"""
        insights = []
        
        # Top performer insight
        top_performer = max(performance_scores, key=performance_scores.get)
        top_store_name = self.STORE_GEOGRAPHIC_DATA.get(top_performer, {}).get('name', top_performer)
        insights.append(f"{top_store_name} is the top overall performer with score {performance_scores[top_performer]}")
        
        # Revenue distribution insight
        revenue_std = benchmarks['total_revenue']['std']
        revenue_mean = benchmarks['total_revenue']['mean']
        if revenue_std / revenue_mean > 0.5:  # High variability
            insights.append("Significant revenue variation between stores - opportunities for improvement")
        
        # Contract value insight
        contract_values = [performance_scores[store] for store in performance_scores]
        if max(contract_values) / min(contract_values) > 1.5:
            insights.append("Large differences in performance efficiency across stores")
        
        return insights[:3]  # Top 3 insights
    
    def _generate_regional_insights(self, store_performance: Dict, 
                                  industry_distribution: Dict, 
                                  seasonal_patterns: Dict) -> List[str]:
        """Generate overall regional insights"""
        insights = []
        
        # Performance insights
        if store_performance:
            revenue_shares = [perf['performance_ratios']['revenue_share_percentage'] 
                            for perf in store_performance.values()]
            max_share = max(revenue_shares)
            
            if max_share > 40:
                dominant_store = next(store for store, perf in store_performance.items() 
                                    if perf['performance_ratios']['revenue_share_percentage'] == max_share)
                store_name = self.STORE_GEOGRAPHIC_DATA.get(dominant_store, {}).get('name', dominant_store)
                insights.append(f"{store_name} dominates regional revenue with {max_share:.1f}% market share")
        
        # Specialization insights
        if industry_distribution:
            specialization_scores = [dist['summary']['specialization_score'] 
                                   for dist in industry_distribution.values()]
            avg_specialization = np.mean(specialization_scores)
            
            if avg_specialization > 0.6:
                insights.append("Stores are highly specialized - consider cross-training opportunities")
            elif avg_specialization < 0.4:
                insights.append("Stores have diverse offerings - good risk distribution")
        
        # Seasonal insights
        if seasonal_patterns:
            seasonality_strengths = [pattern['seasonality_strength'] 
                                   for pattern in seasonal_patterns.values()]
            avg_seasonality = np.mean(seasonality_strengths)
            
            if avg_seasonality > 0.5:
                insights.append("Strong seasonal patterns - important for inventory planning")
        
        return insights[:5]  # Top 5 insights
    
    def _store_regional_analytics(self, results: Dict) -> bool:
        """Store regional analytics results in database"""
        try:
            analysis_date = date.today()
            
            for store_code, performance in results.get('store_performance', {}).items():
                # Store overall store performance
                existing = db.session.query(StoreRegionalAnalytics).filter(
                    and_(
                        StoreRegionalAnalytics.store_code == store_code,
                        StoreRegionalAnalytics.analysis_date == analysis_date,
                        StoreRegionalAnalytics.metric_name == 'overall_performance'
                    )
                ).first()
                
                if existing:
                    existing.metric_value = Decimal(str(performance['basic_metrics']['total_revenue']))
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    new_analytics = StoreRegionalAnalytics(
                        store_code=store_code,
                        store_name=performance.get('store_name'),
                        analysis_date=analysis_date,
                        industry_segment='all',
                        metric_name='overall_performance',
                        metric_value=Decimal(str(performance['basic_metrics']['total_revenue'])),
                        metric_unit='dollars',
                        regional_average=Decimal(str(results.get('regional_benchmarks', {}).get('benchmarks', {}).get('total_revenue', {}).get('mean', 0))),
                        variance_from_regional=Decimal(str(performance['performance_ratios'].get('revenue_share_percentage', 0))),
                        confidence_level=Decimal('0.85')
                    )
                    db.session.add(new_analytics)
            
            db.session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store regional analytics: {e}")
            db.session.rollback()
            return False
    
    def _get_month_name(self, month_num: int) -> str:
        """Get month name from month number"""
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        return months[month_num] if 1 <= month_num <= 12 else 'Unknown'