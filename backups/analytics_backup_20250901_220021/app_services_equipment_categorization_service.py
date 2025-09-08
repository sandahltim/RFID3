"""
Equipment Categorization Service
Automatically categorizes equipment into A1 Rent It (Construction) vs Broadway Tent & Event
Optimized for Minnesota equipment rental business intelligence
"""

import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from app import db
from app.services.logger import get_logger
import pandas as pd
import numpy as np

logger = get_logger(__name__)

class EquipmentCategorizationService:
    """Service for intelligent equipment categorization and business mix analysis"""
    
    def __init__(self):
        self.logger = logger
        
        # CORRECTED store profiles based on actual business operations
        self.store_profiles = {
            '3607': {
                'name': 'Wayzata', 
                'brand': 'A1 Rent It',
                'address': '3607 Shoreline Drive, Wayzata, MN 55391',
                'construction_ratio': 0.90, 
                'events_ratio': 0.10, 
                'delivery': True,
                'specialization': 'Lake Minnetonka DIY/homeowners + limited events'
            },
            '6800': {
                'name': 'Brooklyn Park', 
                'brand': 'A1 Rent It',
                'construction_ratio': 1.00, 
                'events_ratio': 0.00, 
                'delivery': True,
                'specialization': 'Pure construction/industrial - no party equipment'
            },
            '8101': {
                'name': 'Fridley', 
                'brand': 'Broadway Tent & Event',
                'address': '8101 Ashton Ave NE, Fridley, MN',
                'construction_ratio': 0.00, 
                'events_ratio': 1.00, 
                'delivery': True,
                'specialization': 'Pure events/weddings/corporate functions'
            },
            '728': {
                'name': 'Elk River', 
                'brand': 'A1 Rent It',
                'construction_ratio': 0.90, 
                'events_ratio': 0.10, 
                'delivery': True,
                'specialization': 'Rural/suburban DIY + agricultural support + limited events'
            }
        }
        
        # Minnesota-specific equipment categorization patterns
        self.construction_patterns = {
            'excavation': ['excavator', 'backhoe', 'mini ex', 'track hoe', 'digger'],
            'earthwork': ['skid steer', 'bobcat', 'loader', 'dozer', 'compactor'],
            'power_tools': ['drill', 'saw', 'grinder', 'hammer drill', 'impact', 'demo'],
            'air_power': ['compressor', 'pneumatic', 'air tool', 'jackhammer'],
            'material_handling': ['forklift', 'telehandler', 'boom lift', 'scissor lift'],
            'concrete': ['mixer', 'vibrator', 'screed', 'power trowel', 'concrete'],
            'generators': ['generator', 'welder', 'power station', 'portable power']
        }
        
        self.event_patterns = {
            'shelter': ['tent', 'canopy', 'pavilion', 'marquee', 'awning'],
            'seating': ['chair', 'stool', 'bench', 'bleacher', 'seating'],
            'tables': ['table', 'cocktail table', 'round table', 'rectangle table'],
            'staging': ['stage', 'platform', 'riser', 'deck', 'flooring'],
            'lighting': ['lighting', 'chandelier', 'uplighting', 'string lights'],
            'audio_visual': ['sound', 'speaker', 'microphone', 'projector', 'screen'],
            'climate': ['heater', 'fan', 'cooling', 'hvac', 'air conditioning'],
            'decor': ['linens', 'draping', 'backdrop', 'decor', 'centerpiece']
        }
        
        # Minnesota seasonal equipment patterns
        self.seasonal_patterns = {
            'winter_construction': ['heater', 'warming', 'ice_melt', 'snow'],
            'summer_events': ['cooling', 'misting', 'shade', 'outdoor'],
            'landscaping': ['mower', 'trimmer', 'leaf blower', 'aerator', 'seeder']
        }
    
    def categorize_equipment_item(self, 
                                  common_name: str, 
                                  pos_category: Optional[str] = None,
                                  pos_department: Optional[str] = None,
                                  pos_name: Optional[str] = None) -> Dict:
        """
        Categorize a single equipment item with confidence scoring
        
        Returns:
            Dict with category, confidence, subcategory, and business_line
        """
        try:
            # Normalize input text for analysis
            text_to_analyze = ' '.join(filter(None, [
                common_name or '',
                pos_name or '',
                pos_category or '',
                pos_department or ''
            ])).lower()
            
            construction_score = 0
            event_score = 0
            construction_matches = []
            event_matches = []
            
            # Score against construction patterns
            for category, patterns in self.construction_patterns.items():
                for pattern in patterns:
                    if pattern in text_to_analyze:
                        construction_score += 1
                        construction_matches.append(f"{category}:{pattern}")
            
            # Score against event patterns
            for category, patterns in self.event_patterns.items():
                for pattern in patterns:
                    if pattern in text_to_analyze:
                        event_score += 1
                        event_matches.append(f"{category}:{pattern}")
            
            # Determine primary category
            if construction_score > event_score:
                primary_category = 'A1_RentIt_Construction'
                confidence = min(construction_score / (construction_score + event_score + 1), 0.95)
                matches = construction_matches
                business_ratio = 0.75  # Corrected: 75% construction based on store analysis
            elif event_score > construction_score:
                primary_category = 'Broadway_TentEvent'
                confidence = min(event_score / (construction_score + event_score + 1), 0.95)
                matches = event_matches
                business_ratio = 0.25  # Corrected: 25% events based on store analysis
            else:
                # Mixed or unclear - use POS data hints
                if pos_department:
                    if any(term in pos_department.lower() for term in ['construction', 'tool', 'power']):
                        primary_category = 'A1_RentIt_Construction'
                        confidence = 0.60
                        business_ratio = 0.75
                    elif any(term in pos_department.lower() for term in ['event', 'party', 'tent']):
                        primary_category = 'Broadway_TentEvent'
                        confidence = 0.60
                        business_ratio = 0.25
                    else:
                        primary_category = 'Mixed_Category'
                        confidence = 0.50
                        business_ratio = 0.50
                else:
                    primary_category = 'Mixed_Category'
                    confidence = 0.40
                    business_ratio = 0.50
                matches = []
            
            # Determine subcategory
            subcategory = 'General'
            if matches:
                # Get most specific match
                subcategory = matches[0].split(':')[0].title().replace('_', ' ')
            
            return {
                'category': primary_category,
                'confidence': round(confidence, 3),
                'subcategory': subcategory,
                'business_line': 'Construction' if 'A1_RentIt' in primary_category else 
                               'Events' if 'Broadway' in primary_category else 'Mixed',
                'business_ratio': business_ratio,
                'matches': matches,
                'analyzed_text': text_to_analyze[:100]  # First 100 chars for debugging
            }
            
        except Exception as e:
            self.logger.error(f"Error categorizing equipment: {e}")
            return {
                'category': 'Unknown',
                'confidence': 0.0,
                'subcategory': 'Unknown',
                'business_line': 'Unknown',
                'business_ratio': 0.50,
                'matches': [],
                'error': str(e)
            }
    
    def analyze_inventory_mix(self, store_code: Optional[str] = None) -> Dict:
        """
        Analyze the business mix (Construction vs Events) for inventory
        
        Args:
            store_code: Optional store filter (3607, 6800, 728, 8101)
            
        Returns:
            Comprehensive business mix analysis
        """
        try:
            # Base query for equipment analysis
            query = text("""
                SELECT 
                    im.tag_id,
                    im.common_name,
                    im.current_store,
                    im.turnover_ytd,
                    im.status,
                    pe.name as pos_name,
                    pe.category as pos_category,
                    pe.department as pos_department,
                    pe.turnover_ytd as pos_turnover_ytd
                FROM id_item_master im
                LEFT JOIN pos_rfid_correlations prc ON im.rental_class_num = prc.rfid_rental_class_num
                LEFT JOIN pos_equipment pe ON prc.pos_item_num = pe.item_num
                WHERE im.status != 'Retired' 
                AND im.common_name IS NOT NULL
                """ + (f"AND im.current_store = '{store_code}'" if store_code else ""))
            
            equipment_data = db.session.execute(query).fetchall()
            
            if not equipment_data:
                return {'status': 'no_data', 'message': 'No equipment data found'}
            
            # Categorize all equipment
            categorized_equipment = []
            for item in equipment_data:
                category_result = self.categorize_equipment_item(
                    common_name=item.common_name,
                    pos_category=item.pos_category,
                    pos_department=item.pos_department,
                    pos_name=item.pos_name
                )
                
                categorized_equipment.append({
                    'tag_id': item.tag_id,
                    'common_name': item.common_name,
                    'current_store': item.current_store,
                    'turnover_ytd': float(item.turnover_ytd or 0),
                    'pos_turnover_ytd': float(item.pos_turnover_ytd or 0),
                    **category_result
                })
            
            # Analyze results
            df = pd.DataFrame(categorized_equipment)
            
            # Business mix analysis
            category_summary = df.groupby('category').agg({
                'tag_id': 'count',
                'turnover_ytd': ['sum', 'mean'],
                'confidence': 'mean',
                'business_ratio': 'first'
            }).round(2)
            
            # Store-level analysis if no specific store requested
            store_analysis = {}
            if not store_code:
                for store in df['current_store'].unique():
                    if store:
                        store_df = df[df['current_store'] == store]
                        store_analysis[store] = {
                            'total_items': len(store_df),
                            'construction_items': len(store_df[store_df['category'] == 'A1_RentIt_Construction']),
                            'event_items': len(store_df[store_df['category'] == 'Broadway_TentEvent']),
                            'mixed_items': len(store_df[store_df['category'] == 'Mixed_Category']),
                            'total_turnover': store_df['turnover_ytd'].sum(),
                            'construction_turnover': store_df[store_df['category'] == 'A1_RentIt_Construction']['turnover_ytd'].sum(),
                            'event_turnover': store_df[store_df['category'] == 'Broadway_TentEvent']['turnover_ytd'].sum(),
                            'avg_confidence': store_df['confidence'].mean()
                        }
            
            # Minnesota-specific insights
            high_confidence_items = df[df['confidence'] > 0.8]
            low_confidence_items = df[df['confidence'] < 0.5]
            
            # Revenue analysis by category
            revenue_analysis = {
                'construction_revenue': df[df['category'] == 'A1_RentIt_Construction']['turnover_ytd'].sum(),
                'event_revenue': df[df['category'] == 'Broadway_TentEvent']['turnover_ytd'].sum(),
                'mixed_revenue': df[df['category'] == 'Mixed_Category']['turnover_ytd'].sum(),
                'total_revenue': df['turnover_ytd'].sum()
            }
            
            # Calculate actual business ratios
            total_revenue = revenue_analysis['total_revenue']
            if total_revenue > 0:
                actual_construction_ratio = revenue_analysis['construction_revenue'] / total_revenue
                actual_event_ratio = revenue_analysis['event_revenue'] / total_revenue
            else:
                actual_construction_ratio = 0
                actual_event_ratio = 0
            
            return {
                'status': 'success',
                'analysis_scope': f'Store {store_code}' if store_code else 'All Stores',
                'total_items_analyzed': len(df),
                'business_mix': {
                    'target_construction_ratio': 0.75,  # Updated based on actual CSV analysis
                    'target_event_ratio': 0.25,  # Updated based on actual CSV analysis
                    'actual_construction_ratio': round(actual_construction_ratio, 3),
                    'actual_event_ratio': round(actual_event_ratio, 3),
                    'ratio_variance': {
                        'construction_variance': round(actual_construction_ratio - 0.75, 3),
                        'event_variance': round(actual_event_ratio - 0.25, 3)
                    }
                },
                'category_breakdown': {
                    'A1_RentIt_Construction': {
                        'item_count': len(df[df['category'] == 'A1_RentIt_Construction']),
                        'revenue': revenue_analysis['construction_revenue'],
                        'avg_turnover': df[df['category'] == 'A1_RentIt_Construction']['turnover_ytd'].mean(),
                        'percentage_of_items': len(df[df['category'] == 'A1_RentIt_Construction']) / len(df) * 100
                    },
                    'Broadway_TentEvent': {
                        'item_count': len(df[df['category'] == 'Broadway_TentEvent']),
                        'revenue': revenue_analysis['event_revenue'],
                        'avg_turnover': df[df['category'] == 'Broadway_TentEvent']['turnover_ytd'].mean(),
                        'percentage_of_items': len(df[df['category'] == 'Broadway_TentEvent']) / len(df) * 100
                    },
                    'Mixed_Category': {
                        'item_count': len(df[df['category'] == 'Mixed_Category']),
                        'revenue': revenue_analysis['mixed_revenue'],
                        'avg_turnover': df[df['category'] == 'Mixed_Category']['turnover_ytd'].mean() if len(df[df['category'] == 'Mixed_Category']) > 0 else 0,
                        'percentage_of_items': len(df[df['category'] == 'Mixed_Category']) / len(df) * 100
                    }
                },
                'confidence_analysis': {
                    'high_confidence_items': len(high_confidence_items),
                    'low_confidence_items': len(low_confidence_items),
                    'avg_confidence': round(df['confidence'].mean(), 3),
                    'review_needed': len(low_confidence_items)
                },
                'store_analysis': store_analysis,
                'recommendations': self._generate_recommendations(df, actual_construction_ratio, actual_event_ratio)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing inventory mix: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_seasonal_equipment_demand(self, season: str = 'current') -> Dict:
        """
        Analyze seasonal equipment demand patterns for Minnesota
        
        Args:
            season: 'spring', 'summer', 'fall', 'winter', or 'current'
            
        Returns:
            Seasonal demand analysis with Minnesota-specific insights
        """
        try:
            import datetime
            current_month = datetime.datetime.now().month
            
            # Define Minnesota seasons
            if season == 'current':
                if current_month in [3, 4, 5]:
                    season = 'spring'
                elif current_month in [6, 7, 8]:
                    season = 'summer'
                elif current_month in [9, 10, 11]:
                    season = 'fall'
                else:
                    season = 'winter'
            
            # Minnesota seasonal patterns
            seasonal_equipment = {
                'spring': {
                    'high_demand': ['excavator', 'skid steer', 'compactor', 'generator'],
                    'construction_focus': 0.80,  # Heavy construction season starts
                    'event_focus': 0.20,
                    'weather_factors': ['frost_thaw', 'mud_season', 'permit_season']
                },
                'summer': {
                    'high_demand': ['tent', 'table', 'chair', 'stage', 'generator'],
                    'construction_focus': 0.65,  # Construction continues, events peak
                    'event_focus': 0.35,
                    'weather_factors': ['wedding_season', 'state_fair', 'outdoor_events']
                },
                'fall': {
                    'high_demand': ['heater', 'generator', 'tent', 'excavator'],
                    'construction_focus': 0.70,  # Fall construction push
                    'event_focus': 0.30,
                    'weather_factors': ['harvest_season', 'weather_protection', 'project_completion']
                },
                'winter': {
                    'high_demand': ['heater', 'generator', 'power_tools'],
                    'construction_focus': 0.60,  # Indoor work focus
                    'event_focus': 0.40,  # Indoor events increase
                    'weather_factors': ['heating_demand', 'indoor_projects', 'holiday_events']
                }
            }
            
            season_data = seasonal_equipment.get(season, seasonal_equipment['summer'])
            
            # Analyze current inventory against seasonal needs
            inventory_analysis = self.analyze_inventory_mix()
            
            return {
                'season': season,
                'month': current_month,
                'seasonal_focus': season_data,
                'current_inventory': inventory_analysis,
                'recommendations': {
                    'equipment_priority': season_data['high_demand'],
                    'business_mix_target': {
                        'construction': season_data['construction_focus'],
                        'events': season_data['event_focus']
                    },
                    'minnesota_factors': season_data['weather_factors']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing seasonal demand: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _generate_recommendations(self, df: pd.DataFrame, 
                                  construction_ratio: float, 
                                  event_ratio: float) -> List[str]:
        """Generate business recommendations based on analysis"""
        recommendations = []
        
        # Business mix recommendations
        if construction_ratio < 0.65:
            recommendations.append("Consider increasing construction equipment inventory - below 70% target")
        if construction_ratio > 0.75:
            recommendations.append("High construction focus - consider expanding event equipment for balance")
        
        if event_ratio < 0.25:
            recommendations.append("Event equipment inventory below 30% target - growth opportunity")
        if event_ratio > 0.35:
            recommendations.append("Strong event equipment performance - consider expansion")
        
        # Low confidence items need review
        low_confidence = len(df[df['confidence'] < 0.5])
        if low_confidence > 0:
            recommendations.append(f"{low_confidence} items need manual categorization review")
        
        # Store-specific recommendations
        if 'current_store' in df.columns:
            for store in df['current_store'].unique():
                if store:
                    store_df = df[df['current_store'] == store]
                    store_construction_ratio = len(store_df[store_df['category'] == 'A1_RentIt_Construction']) / len(store_df)
                    
                    if store == '3607' and store_construction_ratio > 0.60:  # Wayzata should be more event-focused
                        recommendations.append(f"Wayzata (3607) has high construction ratio - optimize for events near Lake Minnetonka")
                    elif store == '728' and store_construction_ratio < 0.80:  # Fridley should be construction-focused
                        recommendations.append(f"Fridley (728) could increase construction equipment for industrial corridor")
        
        return recommendations
    
    def get_store_profile(self, store_code: str) -> Dict:
        """
        Get corrected store profile with business mix expectations
        
        Args:
            store_code: Store identifier (3607, 6800, 728, 8101)
            
        Returns:
            Complete store profile with corrected business ratios
        """
        try:
            if store_code not in self.store_profiles:
                return {'status': 'error', 'message': f'Unknown store code: {store_code}'}
            
            profile = self.store_profiles[store_code].copy()
            
            # Add expected business metrics based on corrected analysis
            profile['expected_metrics'] = {
                'revenue_percentage_of_total': {
                    '3607': 15.3,  # Wayzata
                    '6800': 27.5,  # Brooklyn Park - largest operation
                    '728': 12.1,   # Elk River - smallest 
                    '8101': 24.8   # Fridley - major events
                }.get(store_code, 0),
                'business_focus': {
                    '3607': 'Mixed DIY with Lake Minnetonka affluent customers',
                    '6800': 'Pure construction - commercial contractors',
                    '728': 'Mixed DIY with rural/agricultural support',
                    '8101': 'Pure events - weddings and corporate functions'
                }.get(store_code, 'Unknown'),
                'seasonal_patterns': {
                    '3607': 'Spring DIY peak, summer lake events',
                    '6800': 'Year-round construction with spring peak',
                    '728': 'Agricultural spring, construction summer, events fall',
                    '8101': 'Wedding season May-October, corporate year-round'
                }.get(store_code, 'Unknown')
            }
            
            return {
                'status': 'success',
                'store_code': store_code,
                'profile': profile
            }
            
        except Exception as e:
            self.logger.error(f"Error getting store profile: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def analyze_store_compliance(self, store_code: str) -> Dict:
        """
        Analyze how well a store's inventory matches its expected business profile
        
        Args:
            store_code: Store to analyze
            
        Returns:
            Compliance analysis with recommendations
        """
        try:
            # Get store profile expectations
            profile = self.get_store_profile(store_code)
            if profile['status'] != 'success':
                return profile
            
            expected_construction_ratio = profile['profile']['construction_ratio']
            expected_events_ratio = profile['profile']['events_ratio']
            
            # Analyze actual inventory
            inventory_analysis = self.analyze_inventory_mix(store_code)
            if inventory_analysis['status'] != 'success':
                return inventory_analysis
            
            actual_construction = inventory_analysis['business_mix']['actual_construction_ratio']
            actual_events = inventory_analysis['business_mix']['actual_event_ratio']
            
            # Calculate compliance scores
            construction_compliance = 1 - abs(expected_construction_ratio - actual_construction)
            events_compliance = 1 - abs(expected_events_ratio - actual_events)
            overall_compliance = (construction_compliance + events_compliance) / 2
            
            return {
                'status': 'success',
                'store_code': store_code,
                'store_name': profile['profile']['name'],
                'brand': profile['profile']['brand'],
                'compliance_scores': {
                    'construction_compliance': round(max(0, construction_compliance), 3),
                    'events_compliance': round(max(0, events_compliance), 3),
                    'overall_compliance': round(max(0, overall_compliance), 3)
                },
                'expected_vs_actual': {
                    'expected_construction': expected_construction_ratio,
                    'actual_construction': actual_construction,
                    'construction_variance': round(actual_construction - expected_construction_ratio, 3),
                    'expected_events': expected_events_ratio,
                    'actual_events': actual_events,
                    'events_variance': round(actual_events - expected_events_ratio, 3)
                },
                'recommendations': self._generate_store_recommendations(
                    store_code, expected_construction_ratio, actual_construction, 
                    expected_events_ratio, actual_events
                ),
                'inventory_summary': inventory_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing store compliance: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _generate_store_recommendations(self, store_code: str, 
                                       expected_construction: float, actual_construction: float,
                                       expected_events: float, actual_events: float) -> List[str]:
        """Generate store-specific recommendations based on corrected profiles"""
        recommendations = []
        store_name = self.store_profiles.get(store_code, {}).get('name', store_code)
        
        construction_variance = actual_construction - expected_construction
        events_variance = actual_events - expected_events
        
        if store_code == '6800':  # Brooklyn Park - Pure construction
            if actual_events > 0.05:  # Should have no events equipment
                recommendations.append(f"Brooklyn Park has {actual_events:.1%} events equipment - should be 0% (pure construction)")
            if actual_construction < 0.90:
                recommendations.append(f"Brooklyn Park construction ratio at {actual_construction:.1%} - should be near 100%")
        
        elif store_code == '8101':  # Fridley - Pure events
            if actual_construction > 0.05:  # Should have no construction equipment
                recommendations.append(f"Fridley has {actual_construction:.1%} construction equipment - should be 0% (pure events)")
            if actual_events < 0.90:
                recommendations.append(f"Fridley events ratio at {actual_events:.1%} - should be near 100%")
        
        elif store_code in ['3607', '728']:  # Mixed stores
            if construction_variance < -0.10:
                recommendations.append(f"{store_name} construction equipment below target - consider adding DIY tools")
            if construction_variance > 0.10:
                recommendations.append(f"{store_name} too construction-focused - add party equipment for balance")
            if events_variance < -0.05:
                recommendations.append(f"{store_name} needs more event equipment to serve local market")
        
        # General recommendations
        if abs(construction_variance) > 0.15 or abs(events_variance) > 0.15:
            recommendations.append(f"Significant business mix variance - review inventory allocation strategy")
        
        return recommendations
    
    def update_equipment_categories_bulk(self) -> Dict:
        """
        Bulk update equipment categories in the database
        
        Returns:
            Summary of categorization updates
        """
        try:
            # This would extend the ItemMaster model to include category fields
            # For now, return analysis that could be used for updates
            analysis = self.analyze_inventory_mix()
            
            return {
                'status': 'analysis_complete',
                'message': 'Categorization analysis complete - ready for database schema updates',
                'analysis': analysis,
                'next_steps': [
                    'Add category columns to id_item_master table',
                    'Implement category update API endpoint',
                    'Create categorization dashboard for manual review'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error in bulk categorization update: {e}")
            return {'status': 'error', 'error': str(e)}