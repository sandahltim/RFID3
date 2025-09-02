"""
Minnesota Industry Analytics Service
Categorizes equipment into industry segments (Party/Event vs DIY/Construction)
Analyzes seasonal patterns specific to Minnesota market
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Tuple, Set
from sqlalchemy import text, and_, or_, func
from app import db
from app.services.logger import get_logger
from app.models.weather_models import (
    EquipmentCategorization, MinnesotaSeasonalPattern,
    StoreRegionalAnalytics, WeatherRentalCorrelation
)
from app.models.pos_models import POSEquipment, POSTransaction, POSTransactionItem
import re
import json
from decimal import Decimal

logger = get_logger(__name__)

class MinnesotaIndustryAnalytics:
    """Service for Minnesota-specific industry analytics and equipment categorization"""
    
    # Equipment categorization keywords and patterns
    PARTY_EVENT_KEYWORDS = {
        'tent': ['tent', 'canopy', 'pavilion', 'marquee', 'shelter'],
        'table': ['table', 'round', 'rectangular', 'cocktail', 'bistro', 'banquet'],
        'chair': ['chair', 'folding', 'chiavari', 'stacking', 'barstool', 'bench'],
        'lighting': ['light', 'string', 'lantern', 'uplighting', 'chandelier', 'spot'],
        'linens': ['linen', 'tablecloth', 'napkin', 'runner', 'overlay', 'sash'],
        'dishes': ['plate', 'glass', 'cup', 'silverware', 'china', 'stemware'],
        'heating': ['heater', 'warming', 'propane', 'patio heater'],
        'bar': ['bar', 'portable bar', 'back bar', 'wine bar'],
        'dance': ['dance floor', 'staging', 'platform', 'riser'],
        'sound': ['speaker', 'microphone', 'pa system', 'sound system', 'audio'],
        'decor': ['arch', 'backdrop', 'column', 'fountain', 'centerpiece']
    }
    
    CONSTRUCTION_DIY_KEYWORDS = {
        'power_tools': [
            'drill', 'saw', 'grinder', 'sander', 'router', 'compressor',
            'nailer', 'stapler', 'welder', 'generator', 'mixer'
        ],
        'hand_tools': [
            'hammer', 'wrench', 'screwdriver', 'pliers', 'level', 'square',
            'chisel', 'file', 'clamp', 'vise'
        ],
        'heavy_equipment': [
            'excavator', 'skid steer', 'bobcat', 'loader', 'backhoe',
            'trencher', 'compactor', 'roller'
        ],
        'scaffolding': ['scaffold', 'staging', 'ladder', 'platform', 'tower'],
        'concrete': ['concrete', 'cement', 'mixer', 'vibrator', 'float', 'screed'],
        'cutting': ['chainsaw', 'cutoff saw', 'chop saw', 'circular saw', 'jigsaw'],
        'material_handling': [
            'dolly', 'cart', 'hoist', 'winch', 'come along', 'pulley',
            'conveyor', 'lift', 'jack'
        ],
        'safety': ['harness', 'hard hat', 'safety', 'barrier', 'cone', 'vest'],
        'plumbing': ['snake', 'auger', 'pipe', 'fitting', 'valve', 'pump'],
        'electrical': ['wire', 'conduit', 'outlet', 'switch', 'panel', 'meter']
    }
    
    LANDSCAPING_KEYWORDS = {
        'mowing': ['mower', 'edger', 'trimmer', 'blower', 'vacuum'],
        'aerating': ['aerator', 'dethatcher', 'overseeder', 'spreader'],
        'tree_care': ['chainsaw', 'pruner', 'pole saw', 'chipper', 'stump grinder'],
        'soil_prep': ['tiller', 'cultivator', 'rake', 'hoe', 'shovel', 'spade'],
        'irrigation': ['sprinkler', 'hose', 'timer', 'valve', 'nozzle'],
        'hardscaping': ['plate compactor', 'brick saw', 'paver', 'retaining wall']
    }
    
    # Minnesota seasonal patterns
    MINNESOTA_SEASONAL_PATTERNS = {
        'party_event': {
            'peak_months': [5, 6, 7, 8, 9, 10],  # May-October
            'wedding_season': [5, 6, 7, 8, 9],   # May-September
            'graduation_season': [5, 6],          # May-June
            'outdoor_event_season': [4, 5, 6, 7, 8, 9, 10],  # April-October
            'holiday_events': [11, 12],           # November-December
            'weather_dependent': True,
            'cancellation_risk': 'high'
        },
        'construction_diy': {
            'peak_months': [4, 5, 6, 7, 8, 9, 10],  # April-October
            'spring_construction': [4, 5, 6],         # April-June
            'summer_peak': [6, 7, 8],                 # June-August
            'fall_projects': [9, 10],                 # September-October
            'winter_indoor': [11, 12, 1, 2, 3],      # November-March
            'weather_dependent': True,
            'cancellation_risk': 'medium'
        },
        'landscaping': {
            'peak_months': [4, 5, 6, 7, 8, 9, 10],   # April-October
            'spring_prep': [4, 5],                    # April-May
            'summer_maintenance': [6, 7, 8],          # June-August
            'fall_cleanup': [9, 10, 11],              # September-November
            'weather_dependent': True,
            'cancellation_risk': 'low'
        }
    }
    
    # Minnesota store characteristics
    STORE_PROFILES = {
        '3607': {  # Wayzata
            'name': 'Wayzata',
            'brand': 'A1 Rent It',  # ADDED brand identification
            'address': '3607 Shoreline Drive, Wayzata, MN 55391',  # ADDED verified address
            'market_type': 'affluent_mixed',  # UPDATED to reflect mixed model
            'primary_segments': ['construction_diy', 'party_event'],  # CORRECTED order (90/10)
            'customer_drive_time': 25,
            'competition_level': 'high',
            'specialties': ['high-end_diy', 'lake_properties', 'premium_events']  # CORRECTED specialties
        },
        '6800': {  # Brooklyn Park
            'name': 'Brooklyn Park',
            'brand': 'A1 Rent It',  # ADDED brand identification
            'market_type': 'construction_specialist',  # CORRECTED market type
            'primary_segments': ['construction_diy'],  # CORRECTED - pure construction focus
            'customer_drive_time': 20,
            'competition_level': 'medium',
            'specialties': ['commercial_construction', 'industrial_equipment', 'contractor_tools']  # CORRECTED specialties
        },
        '728': {   # CORRECTED - Elk River not Fridley
            'name': 'Elk River',
            'brand': 'A1 Rent It',  # ADDED brand identification
            'market_type': 'rural_mixed',  # UPDATED to reflect mixed model
            'primary_segments': ['construction_diy', 'landscaping', 'party_event'],  # Matches 90/10 mix
            'customer_drive_time': 30,
            'competition_level': 'low',
            'specialties': ['agricultural', 'large_property_maintenance', 'rural_events']
        },
        '8101': {  # CORRECTED - Fridley not Elk River
            'name': 'Fridley',
            'brand': 'Broadway Tent & Event',  # ADDED brand identification
            'market_type': 'events_specialist',  # CORRECTED market type
            'primary_segments': ['party_event'],  # CORRECTED - pure events focus
            'customer_drive_time': 25,
            'competition_level': 'medium',
            'specialties': ['weddings', 'corporate_events', 'tent_rentals', 'event_planning']  # CORRECTED specialties
        }
    }
    
    def __init__(self):
        self.logger = logger
    
    def categorize_equipment_item(self, item_data: Dict) -> Dict:
        """Categorize a single equipment item into industry segments"""
        item_num = item_data.get('item_num', '')
        name = item_data.get('name', '').lower()
        description = item_data.get('desc', '').lower()
        category = item_data.get('category', '').lower()
        
        # Combine all text for analysis
        combined_text = f"{name} {description} {category}".lower()
        
        # Initialize scoring
        scores = {
            'party_event': 0,
            'construction_diy': 0, 
            'landscaping': 0
        }
        
        matched_keywords = []
        
        # Score based on party/event keywords
        for subcategory, keywords in self.PARTY_EVENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    scores['party_event'] += 2 if keyword in name else 1
                    matched_keywords.append(f"party_{keyword}")
        
        # Score based on construction/DIY keywords  
        for subcategory, keywords in self.CONSTRUCTION_DIY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    scores['construction_diy'] += 2 if keyword in name else 1
                    matched_keywords.append(f"construction_{keyword}")
        
        # Score based on landscaping keywords
        for subcategory, keywords in self.LANDSCAPING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    scores['landscaping'] += 2 if keyword in name else 1
                    matched_keywords.append(f"landscaping_{keyword}")
        
        # Determine primary category
        max_score = max(scores.values())
        if max_score == 0:
            primary_category = 'uncategorized'
            confidence = 0.0
        else:
            primary_category = max(scores, key=scores.get)
            # Calculate confidence based on score difference
            sorted_scores = sorted(scores.values(), reverse=True)
            if len(sorted_scores) > 1 and sorted_scores[1] > 0:
                confidence = min(1.0, (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0])
            else:
                confidence = min(1.0, sorted_scores[0] / 5.0)  # Scale confidence
        
        # Determine subcategories
        subcategories = self._determine_subcategories(combined_text, primary_category)
        
        # Weather sensitivity assessment
        weather_info = self._assess_weather_sensitivity(primary_category, subcategories)
        
        return {
            'item_num': item_num,
            'item_name': item_data.get('name'),
            'primary_category': primary_category,
            'confidence_score': round(confidence, 2),
            'category_scores': scores,
            'subcategories': subcategories,
            'matched_keywords': matched_keywords,
            'weather_dependent': weather_info['weather_dependent'],
            'weather_cancellation_risk': weather_info['cancellation_risk'],
            'seasonal_patterns': self._get_seasonal_patterns(primary_category),
            'classification_method': 'keyword_match'
        }
    
    def _determine_subcategories(self, text: str, primary_category: str) -> Dict:
        """Determine specific subcategories within the primary category"""
        subcategories = {}
        
        if primary_category == 'party_event':
            for subcat, keywords in self.PARTY_EVENT_KEYWORDS.items():
                if any(keyword in text for keyword in keywords):
                    subcategories[subcat] = True
        elif primary_category == 'construction_diy':
            for subcat, keywords in self.CONSTRUCTION_DIY_KEYWORDS.items():
                if any(keyword in text for keyword in keywords):
                    subcategories[subcat] = True
        elif primary_category == 'landscaping':
            for subcat, keywords in self.LANDSCAPING_KEYWORDS.items():
                if any(keyword in text for keyword in keywords):
                    subcategories[subcat] = True
        
        return subcategories
    
    def _assess_weather_sensitivity(self, category: str, subcategories: Dict) -> Dict:
        """Assess weather sensitivity for equipment category"""
        if category == 'party_event':
            # Most party equipment is highly weather sensitive
            outdoor_items = ['tent', 'lighting', 'heating', 'dance']
            if any(subcat in subcategories for subcat in outdoor_items):
                return {'weather_dependent': True, 'cancellation_risk': 'high'}
            else:
                return {'weather_dependent': True, 'cancellation_risk': 'medium'}
        
        elif category == 'construction_diy':
            # Construction tools vary in weather sensitivity
            outdoor_tools = ['heavy_equipment', 'concrete', 'cutting']
            if any(subcat in subcategories for subcat in outdoor_tools):
                return {'weather_dependent': True, 'cancellation_risk': 'medium'}
            else:
                return {'weather_dependent': False, 'cancellation_risk': 'low'}
        
        elif category == 'landscaping':
            # Landscaping equipment is weather dependent but less cancelled
            return {'weather_dependent': True, 'cancellation_risk': 'low'}
        
        else:
            return {'weather_dependent': False, 'cancellation_risk': 'low'}
    
    def _get_seasonal_patterns(self, category: str) -> Dict:
        """Get seasonal patterns for equipment category"""
        return self.MINNESOTA_SEASONAL_PATTERNS.get(category, {})
    
    def categorize_all_equipment(self, batch_size: int = 1000) -> Dict:
        """Categorize all equipment in the database"""
        try:
            # Get all equipment items
            query = text("""
                SELECT 
                    item_num, name, category, department, type_desc,
                    turnover_ytd, turnover_ltd, current_store
                FROM pos_equipment
                WHERE inactive = 0
                ORDER BY item_num
            """)
            
            equipment_df = pd.read_sql(query, db.engine)
            
            if equipment_df.empty:
                return {'error': 'No equipment data found'}
            
            results = {
                'total_items': len(equipment_df),
                'categorized': 0,
                'categories': {
                    'party_event': 0,
                    'construction_diy': 0,
                    'landscaping': 0,
                    'mixed': 0,
                    'uncategorized': 0
                },
                'processing_errors': 0
            }
            
            # Process in batches
            for i in range(0, len(equipment_df), batch_size):
                batch = equipment_df.iloc[i:i + batch_size]
                
                for _, item in batch.iterrows():
                    try:
                        # Categorize the item
                        categorization = self.categorize_equipment_item(item.to_dict())
                        
                        # Store or update categorization
                        self._store_equipment_categorization(categorization)
                        
                        # Update results
                        results['categorized'] += 1
                        primary_cat = categorization['primary_category']
                        if primary_cat in results['categories']:
                            results['categories'][primary_cat] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to categorize item {item['item_num']}: {e}")
                        results['processing_errors'] += 1
                
                # Commit batch
                db.session.commit()
                self.logger.info(f"Processed batch {i//batch_size + 1}, items {i}-{min(i+batch_size, len(equipment_df))}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Equipment categorization failed: {e}")
            return {'error': str(e)}
    
    def _store_equipment_categorization(self, categorization: Dict) -> bool:
        """Store equipment categorization in database"""
        try:
            # Check if categorization already exists
            existing = db.session.query(EquipmentCategorization).filter(
                EquipmentCategorization.item_num == categorization['item_num']
            ).first()
            
            if existing:
                # Update existing record
                existing.industry_segment = categorization['primary_category']
                existing.confidence_score = Decimal(str(categorization['confidence_score']))
                existing.classification_method = categorization['classification_method']
                existing.weather_dependent = categorization['weather_dependent']
                existing.weather_cancellation_risk = categorization['weather_cancellation_risk']
                existing.classification_keywords = categorization['matched_keywords']
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # Create new record
                new_categorization = EquipmentCategorization(
                    item_num=categorization['item_num'],
                    item_name=categorization['item_name'],
                    industry_segment=categorization['primary_category'],
                    confidence_score=Decimal(str(categorization['confidence_score'])),
                    classification_method=categorization['classification_method'],
                    weather_dependent=categorization['weather_dependent'],
                    weather_cancellation_risk=categorization['weather_cancellation_risk'],
                    classification_keywords=categorization['matched_keywords']
                )
                
                # Add seasonal information
                seasonal = categorization.get('seasonal_patterns', {})
                if 'peak_months' in seasonal:
                    if seasonal['peak_months']:
                        new_categorization.peak_season_start = seasonal['peak_months'][0]
                        new_categorization.peak_season_end = seasonal['peak_months'][-1]
                
                db.session.add(new_categorization)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store categorization for {categorization['item_num']}: {e}")
            db.session.rollback()
            return False
    
    def analyze_store_industry_mix(self, store_code: str) -> Dict:
        """Analyze industry segment mix for a specific store"""
        try:
            query = text("""
                SELECT 
                    ec.industry_segment,
                    COUNT(*) as item_count,
                    SUM(pe.turnover_ytd) as ytd_revenue,
                    AVG(ec.confidence_score) as avg_confidence,
                    SUM(CASE WHEN ec.weather_dependent = 1 THEN 1 ELSE 0 END) as weather_dependent_count
                FROM equipment_categorization ec
                JOIN pos_equipment pe ON ec.item_num = pe.item_num
                WHERE pe.current_store = :store_code
                    AND pe.inactive = 0
                GROUP BY ec.industry_segment
                ORDER BY ytd_revenue DESC
            """)
            
            results_df = pd.read_sql(query, db.engine, params={'store_code': store_code})
            
            if results_df.empty:
                return {'error': f'No categorized equipment found for store {store_code}'}
            
            # Calculate percentages
            total_items = results_df['item_count'].sum()
            total_revenue = results_df['ytd_revenue'].sum()
            
            analysis = {
                'store_code': store_code,
                'store_name': self.STORE_PROFILES.get(store_code, {}).get('name', 'Unknown'),
                'total_items': int(total_items),
                'total_ytd_revenue': float(total_revenue) if total_revenue else 0,
                'industry_breakdown': [],
                'weather_dependency': {
                    'weather_dependent_items': int(results_df['weather_dependent_count'].sum()),
                    'weather_dependency_ratio': float(results_df['weather_dependent_count'].sum() / total_items) if total_items > 0 else 0
                },
                'store_profile': self.STORE_PROFILES.get(store_code, {})
            }
            
            for _, row in results_df.iterrows():
                segment_data = {
                    'industry_segment': row['industry_segment'],
                    'item_count': int(row['item_count']),
                    'item_percentage': float(row['item_count'] / total_items * 100) if total_items > 0 else 0,
                    'ytd_revenue': float(row['ytd_revenue']) if row['ytd_revenue'] else 0,
                    'revenue_percentage': float(row['ytd_revenue'] / total_revenue * 100) if total_revenue > 0 else 0,
                    'avg_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0,
                    'weather_dependent_count': int(row['weather_dependent_count'])
                }
                analysis['industry_breakdown'].append(segment_data)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Store industry mix analysis failed for {store_code}: {e}")
            return {'error': str(e)}
    
    def compare_stores_by_industry(self) -> Dict:
        """Compare all stores by industry segment performance"""
        try:
            query = text("""
                SELECT 
                    pe.current_store as store_code,
                    ec.industry_segment,
                    COUNT(*) as item_count,
                    SUM(pe.turnover_ytd) as ytd_revenue,
                    AVG(pe.turnover_ytd) as avg_revenue_per_item,
                    SUM(CASE WHEN ec.weather_dependent = 1 THEN 1 ELSE 0 END) as weather_dependent_count
                FROM equipment_categorization ec
                JOIN pos_equipment pe ON ec.item_num = pe.item_num
                WHERE pe.inactive = 0 AND pe.current_store IS NOT NULL
                GROUP BY pe.current_store, ec.industry_segment
                ORDER BY pe.current_store, ytd_revenue DESC
            """)
            
            results_df = pd.read_sql(query, db.engine)
            
            if results_df.empty:
                return {'error': 'No data available for store comparison'}
            
            # Organize data by store
            store_comparison = {}
            for store_code in results_df['store_code'].unique():
                store_data = results_df[results_df['store_code'] == store_code]
                
                total_items = store_data['item_count'].sum()
                total_revenue = store_data['ytd_revenue'].sum()
                
                store_comparison[store_code] = {
                    'store_name': self.STORE_PROFILES.get(store_code, {}).get('name', 'Unknown'),
                    'total_items': int(total_items),
                    'total_revenue': float(total_revenue) if total_revenue else 0,
                    'segments': {},
                    'primary_segment': None,
                    'diversification_score': 0
                }
                
                # Calculate segment breakdown
                segment_revenues = {}
                for _, row in store_data.iterrows():
                    segment = row['industry_segment']
                    revenue = float(row['ytd_revenue']) if row['ytd_revenue'] else 0
                    segment_revenues[segment] = revenue
                    
                    store_comparison[store_code]['segments'][segment] = {
                        'item_count': int(row['item_count']),
                        'revenue': revenue,
                        'revenue_percentage': float(revenue / total_revenue * 100) if total_revenue > 0 else 0,
                        'avg_revenue_per_item': float(row['avg_revenue_per_item']) if row['avg_revenue_per_item'] else 0
                    }
                
                # Determine primary segment
                if segment_revenues:
                    primary = max(segment_revenues, key=segment_revenues.get)
                    store_comparison[store_code]['primary_segment'] = primary
                    
                    # Calculate diversification score (entropy-based)
                    if total_revenue > 0:
                        percentages = [rev/total_revenue for rev in segment_revenues.values() if rev > 0]
                        entropy = -sum(p * np.log2(p) for p in percentages if p > 0)
                        # Normalize to 0-1 scale (max entropy for 4 segments is 2)
                        store_comparison[store_code]['diversification_score'] = float(entropy / 2.0)
            
            # Add regional comparisons and insights
            analysis = {
                'store_comparison': store_comparison,
                'regional_insights': self._generate_regional_insights(store_comparison),
                'transfer_opportunities': self._identify_transfer_opportunities(store_comparison)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Store comparison analysis failed: {e}")
            return {'error': str(e)}
    
    def _generate_regional_insights(self, store_comparison: Dict) -> List[str]:
        """Generate insights from store comparison"""
        insights = []
        
        # Find most diversified store
        diversification_scores = {store: data['diversification_score'] 
                                for store, data in store_comparison.items()}
        most_diversified = max(diversification_scores, key=diversification_scores.get)
        insights.append(f"Store {most_diversified} has the most diversified inventory mix")
        
        # Find revenue leaders by segment
        segment_leaders = {}
        for store, data in store_comparison.items():
            for segment, seg_data in data['segments'].items():
                if segment not in segment_leaders or seg_data['revenue'] > segment_leaders[segment]['revenue']:
                    segment_leaders[segment] = {'store': store, 'revenue': seg_data['revenue']}
        
        for segment, leader in segment_leaders.items():
            if leader['revenue'] > 0:
                insights.append(f"Store {leader['store']} leads in {segment} segment with ${leader['revenue']:,.0f} YTD")
        
        return insights
    
    def _identify_transfer_opportunities(self, store_comparison: Dict) -> List[Dict]:
        """Identify equipment transfer opportunities between stores"""
        opportunities = []
        
        # Simple heuristic: stores with low revenue per item in a segment
        # could receive transfers from stores with excess inventory
        
        for segment in ['party_event', 'construction_diy', 'landscaping']:
            segment_performance = []
            
            for store, data in store_comparison.items():
                if segment in data['segments']:
                    seg_data = data['segments'][segment]
                    if seg_data['item_count'] > 0:
                        segment_performance.append({
                            'store': store,
                            'avg_revenue': seg_data['avg_revenue_per_item'],
                            'item_count': seg_data['item_count']
                        })
            
            if len(segment_performance) >= 2:
                # Sort by average revenue per item
                segment_performance.sort(key=lambda x: x['avg_revenue'])
                
                lowest_performer = segment_performance[0]
                highest_performer = segment_performance[-1]
                
                # If there's a significant gap, suggest transfer
                if (highest_performer['avg_revenue'] > lowest_performer['avg_revenue'] * 1.5 and
                    highest_performer['item_count'] > 10):
                    
                    opportunities.append({
                        'segment': segment,
                        'from_store': highest_performer['store'],
                        'to_store': lowest_performer['store'],
                        'rationale': f"Transfer {segment} equipment from high-performing to low-performing store",
                        'potential_impact': 'medium'
                    })
        
        return opportunities
    
    def generate_seasonal_forecast(self, store_code: str, industry_segment: str, 
                                 forecast_months: int = 6) -> Dict:
        """Generate seasonal demand forecast for store and industry segment"""
        try:
            current_month = datetime.now().month
            forecast_data = []
            
            # Get seasonal pattern for the segment
            seasonal_pattern = self.MINNESOTA_SEASONAL_PATTERNS.get(industry_segment, {})
            peak_months = seasonal_pattern.get('peak_months', list(range(1, 13)))
            
            # Get historical data for baseline
            query = text("""
                SELECT 
                    MONTH(pt.contract_date) as month,
                    AVG(COALESCE(pt.rent_amt, 0) + COALESCE(pt.sale_amt, 0)) as avg_revenue,
                    COUNT(*) as contract_count
                FROM pos_transactions pt
                JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
                JOIN equipment_categorization ec ON pti.item_num = ec.item_num
                WHERE pt.store_no = :store_code
                    AND ec.industry_segment = :segment
                    AND pt.contract_date >= DATE_SUB(NOW(), INTERVAL 2 YEAR)
                GROUP BY MONTH(pt.contract_date)
                ORDER BY MONTH(pt.contract_date)
            """)
            
            historical_df = pd.read_sql(query, db.engine, params={
                'store_code': store_code,
                'segment': industry_segment
            })
            
            # Create monthly forecasts
            for i in range(forecast_months):
                month = ((current_month + i - 1) % 12) + 1
                
                # Get historical baseline for this month
                historical_data = historical_df[historical_df['month'] == month]
                base_revenue = float(historical_data['avg_revenue'].iloc[0]) if not historical_data.empty else 100.0
                base_contracts = int(historical_data['contract_count'].iloc[0]) if not historical_data.empty else 5
                
                # Apply seasonal multiplier
                if month in peak_months:
                    seasonal_multiplier = 1.3  # 30% increase during peak
                else:
                    seasonal_multiplier = 0.8   # 20% decrease during off-peak
                
                # Apply weather considerations (simplified)
                weather_adjustment = 1.0
                if industry_segment == 'party_event' and month in [11, 12, 1, 2, 3]:  # Winter months
                    weather_adjustment = 0.6  # Significant drop for outdoor events
                elif industry_segment == 'construction_diy' and month in [12, 1, 2]:  # Deep winter
                    weather_adjustment = 0.4  # Major drop for outdoor construction
                
                final_multiplier = seasonal_multiplier * weather_adjustment
                
                forecast_data.append({
                    'month': month,
                    'month_name': calendar.month_name[month] if 'calendar' in globals() else f"Month {month}",
                    'base_revenue': base_revenue,
                    'seasonal_multiplier': seasonal_multiplier,
                    'weather_adjustment': weather_adjustment,
                    'predicted_revenue': base_revenue * final_multiplier,
                    'predicted_contracts': max(1, int(base_contracts * final_multiplier)),
                    'confidence_level': 0.7 if not historical_data.empty else 0.4
                })
            
            return {
                'store_code': store_code,
                'industry_segment': industry_segment,
                'forecast_period_months': forecast_months,
                'seasonal_pattern': seasonal_pattern,
                'monthly_forecasts': forecast_data,
                'total_predicted_revenue': sum(f['predicted_revenue'] for f in forecast_data),
                'peak_months_in_forecast': [f['month'] for f in forecast_data if f['month'] in peak_months]
            }
            
        except Exception as e:
            self.logger.error(f"Seasonal forecast generation failed: {e}")
            return {'error': str(e)}
    
    def get_categorization_settings(self) -> Dict:
        """Get current categorization settings and thresholds"""
        try:
            # Get categorization statistics
            query = text("""
                SELECT 
                    industry_segment,
                    classification_method,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence
                FROM equipment_categorization
                GROUP BY industry_segment, classification_method
                ORDER BY industry_segment, count DESC
            """)
            
            stats_df = pd.read_sql(query, db.engine)
            
            settings = {
                'confidence_thresholds': {
                    'high_confidence': 0.8,
                    'medium_confidence': 0.6,
                    'low_confidence': 0.4,
                    'review_required': 0.4
                },
                'industry_ratios': {
                    'party_event': {'target_ratio': 0.3, 'current_ratio': 0},
                    'construction_diy': {'target_ratio': 0.5, 'current_ratio': 0},
                    'landscaping': {'target_ratio': 0.15, 'current_ratio': 0},
                    'mixed': {'target_ratio': 0.05, 'current_ratio': 0}
                },
                'classification_methods': {
                    'keyword_match': {'enabled': True, 'weight': 1.0},
                    'ml_classification': {'enabled': False, 'weight': 1.5},
                    'manual_override': {'enabled': True, 'weight': 2.0}
                },
                'statistics': stats_df.to_dict('records') if not stats_df.empty else [],
                'keywords': {
                    'party_event': self.PARTY_EVENT_KEYWORDS,
                    'construction_diy': self.CONSTRUCTION_DIY_KEYWORDS,
                    'landscaping': self.LANDSCAPING_KEYWORDS
                }
            }
            
            # Calculate current ratios
            total_items = stats_df['count'].sum()
            if total_items > 0:
                for segment in settings['industry_ratios']:
                    segment_count = stats_df[stats_df['industry_segment'] == segment]['count'].sum()
                    settings['industry_ratios'][segment]['current_ratio'] = float(segment_count / total_items)
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to get categorization settings: {e}")
            return {'error': str(e)}

import calendar