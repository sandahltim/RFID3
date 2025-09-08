"""
Building Permits Tool for Minnesota Equipment Rental AI Agent
Tracks construction permits to predict equipment rental demand
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import asyncio
import aiohttp
from dataclasses import dataclass, asdict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import re

logger = logging.getLogger(__name__)


@dataclass
class BuildingPermit:
    """Building permit data structure"""
    permit_id: str
    permit_type: str
    project_description: str
    address: str
    city: str
    issue_date: datetime
    estimated_start_date: Optional[datetime]
    estimated_completion_date: Optional[datetime]
    estimated_value: float
    contractor: Optional[str]
    owner: Optional[str]
    status: str
    equipment_demand_category: str
    source: str


@dataclass
class PermitImpact:
    """Permit impact analysis"""
    permit: BuildingPermit
    equipment_needs: List[str]
    demand_level: str  # low, medium, high, very_high
    rental_duration_estimate: int  # days
    seasonal_factor: float
    proximity_to_stores: Dict[str, float]  # store -> distance in miles


class PermitsQueryInput(BaseModel):
    """Input schema for permits queries"""
    query_type: str = Field(
        description="Type of query: 'recent', 'forecast', 'area_analysis', 'equipment_demand'"
    )
    timeframe_days: int = Field(
        default=90, description="Number of days to analyze"
    )
    permit_type: Optional[str] = Field(
        description="Filter by permit type: 'residential', 'commercial', 'industrial'"
    )
    city: Optional[str] = Field(
        description="Filter by city: 'Minneapolis', 'Saint Paul', etc."
    )
    min_value: Optional[float] = Field(
        description="Minimum project value filter"
    )
    area_radius: Optional[float] = Field(
        description="Search radius in miles from store locations"
    )


class PermitsTool(BaseTool):
    """
    LangChain tool for building permits data and construction equipment demand forecasting
    
    Integrates with Minneapolis and St. Paul permit databases to predict:
    - Equipment rental demand from new construction projects
    - Seasonal construction activity patterns
    - Geographic distribution of construction activity
    - Project value correlation with equipment needs
    """
    
    name = "permits_data"
    description = """
    Analyze building permits data to forecast construction equipment rental demand.
    
    Use this tool for:
    - Recent permits indicating upcoming construction projects
    - Construction activity forecasting by area and project type
    - Equipment demand prediction based on permit values and types
    - Seasonal construction pattern analysis
    - Geographic clustering of construction activity near store locations
    - Commercial vs residential construction trends
    
    Covers:
    - Minneapolis building permits
    - St. Paul construction permits  
    - Suburban Twin Cities area permits
    - Commercial and residential projects
    - Infrastructure and utility projects
    """
    
    def __init__(
        self,
        minneapolis_api_key: Optional[str] = None,
        saint_paul_api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.minneapolis_api_key = minneapolis_api_key
        self.saint_paul_api_key = saint_paul_api_key
        
        # API endpoints for permit data
        self.permit_sources = {
            'minneapolis': {
                'url': 'http://opendata.minneapolismn.gov/datasets/building-permits.json',
                'api_endpoint': 'https://services.arcgis.com/afSMGVsC7QSyUl/arcgis/rest/services/',
                'requires_key': False
            },
            'saint_paul': {
                'url': 'https://information.stpaul.gov/City-Infrastructure/Building-Permits/rp6g-z4y9.json',
                'api_endpoint': 'https://information.stpaul.gov/resource/',
                'requires_key': True
            }
        }
        
        # Store locations for proximity analysis
        self.store_locations = {
            'wayzata': {'lat': 44.9733, 'lon': -93.5066},
            'brooklyn_park': {'lat': 45.0941, 'lon': -93.3563},
            'fridley': {'lat': 45.0861, 'lon': -93.2633},
            'elk_river': {'lat': 45.3033, 'lon': -93.5678}
        }
        
        # Equipment demand patterns by permit type and value
        self.equipment_patterns = {
            'residential_new': {
                'base_equipment': [
                    'excavators', 'skid_steers', 'compactors', 'generators',
                    'concrete_mixers', 'scaffolding', 'lifts'
                ],
                'duration_estimate': 120,  # days
                'value_multiplier': 0.001  # equipment demand per $1000 of project value
            },
            'residential_addition': {
                'base_equipment': [
                    'skid_steers', 'mini_excavators', 'scaffolding', 'generators',
                    'concrete_tools', 'lifts'
                ],
                'duration_estimate': 60,
                'value_multiplier': 0.002
            },
            'commercial_new': {
                'base_equipment': [
                    'large_excavators', 'cranes', 'bulldozers', 'compactors',
                    'concrete_pumps', 'large_generators', 'scaffolding_systems',
                    'lifts', 'welding_equipment'
                ],
                'duration_estimate': 365,
                'value_multiplier': 0.0008
            },
            'commercial_renovation': {
                'base_equipment': [
                    'skid_steers', 'lifts', 'scaffolding', 'generators',
                    'air_compressors', 'concrete_tools', 'demolition_tools'
                ],
                'duration_estimate': 90,
                'value_multiplier': 0.0015
            },
            'industrial': {
                'base_equipment': [
                    'large_excavators', 'bulldozers', 'cranes', 'pile_drivers',
                    'concrete_pumps', 'large_generators', 'compressors',
                    'specialized_lifting'
                ],
                'duration_estimate': 540,
                'value_multiplier': 0.0006
            },
            'infrastructure': {
                'base_equipment': [
                    'excavators', 'bulldozers', 'road_equipment', 'compactors',
                    'pumps', 'generators', 'traffic_control'
                ],
                'duration_estimate': 180,
                'value_multiplier': 0.001
            }
        }
        
        # Seasonal construction factors (Minnesota climate considerations)
        self.seasonal_factors = {
            1: 0.3,   # January - very limited outdoor construction
            2: 0.4,   # February
            3: 0.6,   # March - some activity begins
            4: 0.9,   # April - spring ramp-up
            5: 1.2,   # May - peak activity begins
            6: 1.3,   # June - peak summer construction
            7: 1.3,   # July - peak summer construction
            8: 1.3,   # August - peak summer construction
            9: 1.2,   # September - still good weather
            10: 1.0,  # October - activity declining
            11: 0.7,  # November - limited outdoor work
            12: 0.4   # December - very limited activity
        }
    
    def _run(self, query_input: str) -> str:
        """Execute permits query"""
        try:
            # Parse input
            if isinstance(query_input, str):
                try:
                    input_data = json.loads(query_input)
                except json.JSONDecodeError:
                    # Treat as city query
                    input_data = {
                        'query_type': 'recent',
                        'city': query_input
                    }
            else:
                input_data = query_input
            
            query_params = PermitsQueryInput(**input_data)
            
            # Route to appropriate method
            if query_params.query_type == 'recent':
                result = asyncio.run(self._get_recent_permits(
                    query_params.timeframe_days,
                    query_params.permit_type,
                    query_params.city
                ))
            elif query_params.query_type == 'forecast':
                result = self._forecast_construction_demand(
                    query_params.timeframe_days,
                    query_params.permit_type
                )
            elif query_params.query_type == 'area_analysis':
                result = self._analyze_construction_areas(
                    query_params.area_radius or 10.0,
                    query_params.timeframe_days
                )
            elif query_params.query_type == 'equipment_demand':
                result = asyncio.run(self._analyze_equipment_demand(
                    query_params.timeframe_days,
                    query_params.permit_type,
                    query_params.min_value
                ))
            else:
                result = {
                    'success': False,
                    'error': f"Unknown query type: {query_params.query_type}"
                }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Permits tool error: {e}", exc_info=True)
            return json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def _get_recent_permits(
        self,
        timeframe_days: int,
        permit_type: Optional[str],
        city: Optional[str]
    ) -> Dict[str, Any]:
        """Get recent building permits"""
        
        # In production, this would fetch from real APIs
        # For now, generating sample data
        sample_permits = self._generate_sample_permits(timeframe_days, city)
        
        # Filter by permit type if specified
        if permit_type:
            sample_permits = [
                p for p in sample_permits
                if permit_type.lower() in p.permit_type.lower()
            ]
        
        # Analyze impact of each permit
        permit_impacts = []
        for permit in sample_permits:
            impact = self._calculate_permit_impact(permit)
            permit_impacts.append(impact)
        
        # Sort by demand level and project value
        demand_order = {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1}
        permit_impacts.sort(
            key=lambda x: (demand_order.get(x.demand_level, 0), x.permit.estimated_value),
            reverse=True
        )
        
        return {
            'success': True,
            'timeframe_days': timeframe_days,
            'permits_found': len(permit_impacts),
            'filters': {
                'permit_type': permit_type,
                'city': city
            },
            'permits': [asdict(pi) for pi in permit_impacts],
            'summary': self._generate_permits_summary(permit_impacts),
            'timestamp': datetime.now().isoformat()
        }
    
    def _forecast_construction_demand(
        self,
        timeframe_days: int,
        permit_type: Optional[str]
    ) -> Dict[str, Any]:
        """Forecast construction equipment demand based on permits"""
        
        permits = self._generate_sample_permits(timeframe_days)
        if permit_type:
            permits = [p for p in permits if permit_type.lower() in p.permit_type.lower()]
        
        # Group permits by month for trend analysis
        monthly_demand = {}
        current_date = datetime.now()
        
        for month_offset in range(0, min(timeframe_days // 30, 12)):
            month_date = current_date + timedelta(days=month_offset * 30)
            month_key = month_date.strftime('%Y-%m')
            monthly_demand[month_key] = {
                'permits_count': 0,
                'total_value': 0,
                'equipment_demand_score': 0,
                'seasonal_factor': self.seasonal_factors.get(month_date.month, 1.0)
            }
        
        # Aggregate permit data by month
        equipment_demand_totals = {}
        
        for permit in permits:
            month_key = permit.issue_date.strftime('%Y-%m')
            if month_key in monthly_demand:
                impact = self._calculate_permit_impact(permit)
                
                monthly_demand[month_key]['permits_count'] += 1
                monthly_demand[month_key]['total_value'] += permit.estimated_value
                monthly_demand[month_key]['equipment_demand_score'] += len(impact.equipment_needs)
                
                # Aggregate equipment types
                for equipment in impact.equipment_needs:
                    if equipment not in equipment_demand_totals:
                        equipment_demand_totals[equipment] = 0
                    equipment_demand_totals[equipment] += 1
        
        # Apply seasonal factors
        for month_key in monthly_demand:
            monthly_data = monthly_demand[month_key]
            seasonal_factor = monthly_data['seasonal_factor']
            monthly_data['adjusted_demand_score'] = (
                monthly_data['equipment_demand_score'] * seasonal_factor
            )
        
        return {
            'success': True,
            'forecast_period': f'{timeframe_days} days',
            'permit_type_filter': permit_type,
            'monthly_forecast': monthly_demand,
            'top_equipment_demand': dict(
                sorted(equipment_demand_totals.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            'construction_outlook': self._generate_construction_outlook(monthly_demand),
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_construction_areas(
        self,
        radius_miles: float,
        timeframe_days: int
    ) -> Dict[str, Any]:
        """Analyze construction activity by geographic area relative to stores"""
        
        permits = self._generate_sample_permits(timeframe_days)
        
        # Calculate distance from each permit to each store
        area_analysis = {}
        for store_name, store_coords in self.store_locations.items():
            area_analysis[store_name] = {
                'nearby_permits': [],
                'total_value': 0,
                'equipment_opportunities': set()
            }
        
        for permit in permits:
            # For sample data, assign permits to stores based on city
            closest_store = self._assign_permit_to_store(permit)
            impact = self._calculate_permit_impact(permit)
            
            if closest_store in area_analysis:
                area_analysis[closest_store]['nearby_permits'].append(permit)
                area_analysis[closest_store]['total_value'] += permit.estimated_value
                area_analysis[closest_store]['equipment_opportunities'].update(impact.equipment_needs)
        
        # Convert sets to lists for JSON serialization
        for store in area_analysis:
            area_analysis[store]['equipment_opportunities'] = list(
                area_analysis[store]['equipment_opportunities']
            )
            area_analysis[store]['permits_count'] = len(area_analysis[store]['nearby_permits'])
            # Convert permit objects to dictionaries
            area_analysis[store]['nearby_permits'] = [
                asdict(p) for p in area_analysis[store]['nearby_permits']
            ]
        
        return {
            'success': True,
            'analysis_radius_miles': radius_miles,
            'timeframe_days': timeframe_days,
            'store_area_analysis': area_analysis,
            'recommendations': self._generate_area_recommendations(area_analysis),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _analyze_equipment_demand(
        self,
        timeframe_days: int,
        permit_type: Optional[str],
        min_value: Optional[float]
    ) -> Dict[str, Any]:
        """Analyze equipment demand patterns from permits data"""
        
        permits = self._generate_sample_permits(timeframe_days)
        
        # Apply filters
        if permit_type:
            permits = [p for p in permits if permit_type.lower() in p.permit_type.lower()]
        
        if min_value:
            permits = [p for p in permits if p.estimated_value >= min_value]
        
        # Analyze equipment demand
        equipment_analysis = {}
        total_rental_days = 0
        
        for permit in permits:
            impact = self._calculate_permit_impact(permit)
            total_rental_days += impact.rental_duration_estimate
            
            for equipment in impact.equipment_needs:
                if equipment not in equipment_analysis:
                    equipment_analysis[equipment] = {
                        'demand_count': 0,
                        'total_rental_days': 0,
                        'average_duration': 0,
                        'peak_demand_level': 'low',
                        'associated_permit_types': set()
                    }
                
                equipment_analysis[equipment]['demand_count'] += 1
                equipment_analysis[equipment]['total_rental_days'] += impact.rental_duration_estimate
                equipment_analysis[equipment]['associated_permit_types'].add(permit.permit_type)
                
                # Update peak demand level
                current_level = equipment_analysis[equipment]['peak_demand_level']
                if (impact.demand_level == 'very_high' or
                    (impact.demand_level == 'high' and current_level not in ['very_high']) or
                    (impact.demand_level == 'medium' and current_level == 'low')):
                    equipment_analysis[equipment]['peak_demand_level'] = impact.demand_level
        
        # Calculate averages and convert sets to lists
        for equipment in equipment_analysis:
            data = equipment_analysis[equipment]
            if data['demand_count'] > 0:
                data['average_duration'] = data['total_rental_days'] / data['demand_count']
            data['associated_permit_types'] = list(data['associated_permit_types'])
        
        # Sort by demand count
        sorted_equipment = sorted(
            equipment_analysis.items(),
            key=lambda x: x[1]['demand_count'],
            reverse=True
        )
        
        return {
            'success': True,
            'analysis_period': f'{timeframe_days} days',
            'permits_analyzed': len(permits),
            'filters': {
                'permit_type': permit_type,
                'min_value': min_value
            },
            'equipment_demand_analysis': dict(sorted_equipment),
            'total_estimated_rental_days': total_rental_days,
            'demand_insights': self._generate_demand_insights(equipment_analysis),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_sample_permits(
        self,
        timeframe_days: int,
        city_filter: Optional[str] = None
    ) -> List[BuildingPermit]:
        """Generate sample building permits data"""
        
        permits = []
        current_date = datetime.now()
        
        # Sample residential permits
        for i in range(0, timeframe_days, 10):
            issue_date = current_date - timedelta(days=i)
            
            city = 'Minneapolis' if i % 2 == 0 else 'Saint Paul'
            if city_filter and city_filter.lower() not in city.lower():
                continue
            
            permits.append(BuildingPermit(
                permit_id=f"RES-{issue_date.strftime('%Y%m%d')}-{i:03d}",
                permit_type="Residential New Construction",
                project_description="Single family home construction",
                address=f"{1000 + i} Sample Street",
                city=city,
                issue_date=issue_date,
                estimated_start_date=issue_date + timedelta(days=30),
                estimated_completion_date=issue_date + timedelta(days=150),
                estimated_value=350000 + (i * 1000),
                contractor=f"Sample Construction Co {i % 5 + 1}",
                owner="Private Owner",
                status="Active",
                equipment_demand_category="medium",
                source="city_permits"
            ))
        
        # Sample commercial permits
        for i in range(0, timeframe_days, 30):
            issue_date = current_date - timedelta(days=i)
            
            city = 'Minneapolis' if i % 3 == 0 else 'Saint Paul'
            if city_filter and city_filter.lower() not in city.lower():
                continue
            
            permits.append(BuildingPermit(
                permit_id=f"COM-{issue_date.strftime('%Y%m%d')}-{i:03d}",
                permit_type="Commercial New Construction",
                project_description="Office building construction",
                address=f"{2000 + i} Business Avenue",
                city=city,
                issue_date=issue_date,
                estimated_start_date=issue_date + timedelta(days=60),
                estimated_completion_date=issue_date + timedelta(days=365),
                estimated_value=2500000 + (i * 10000),
                contractor=f"Commercial Builders Inc {i % 3 + 1}",
                owner="Commercial Developer LLC",
                status="Active",
                equipment_demand_category="high",
                source="city_permits"
            ))
        
        return permits
    
    def _calculate_permit_impact(self, permit: BuildingPermit) -> PermitImpact:
        """Calculate rental impact for a building permit"""
        
        # Determine equipment pattern based on permit type and value
        pattern_key = 'residential_new'  # default
        
        permit_type_lower = permit.permit_type.lower()
        if 'commercial' in permit_type_lower and 'new' in permit_type_lower:
            pattern_key = 'commercial_new'
        elif 'commercial' in permit_type_lower:
            pattern_key = 'commercial_renovation'
        elif 'residential' in permit_type_lower and 'addition' in permit_type_lower:
            pattern_key = 'residential_addition'
        elif 'industrial' in permit_type_lower:
            pattern_key = 'industrial'
        elif 'infrastructure' in permit_type_lower or 'utility' in permit_type_lower:
            pattern_key = 'infrastructure'
        
        pattern = self.equipment_patterns[pattern_key]
        
        # Calculate equipment needs based on project value
        base_equipment = pattern['base_equipment'].copy()
        value_factor = permit.estimated_value * pattern['value_multiplier']
        
        # Add additional equipment for higher-value projects
        if value_factor > 500:
            base_equipment.extend(['additional_generators', 'specialized_tools'])
        if value_factor > 1000:
            base_equipment.extend(['large_cranes', 'concrete_pumps'])
        
        # Determine demand level
        if permit.estimated_value > 5000000:
            demand_level = 'very_high'
        elif permit.estimated_value > 1000000:
            demand_level = 'high'
        elif permit.estimated_value > 250000:
            demand_level = 'medium'
        else:
            demand_level = 'low'
        
        # Apply seasonal factor
        if permit.estimated_start_date:
            seasonal_factor = self.seasonal_factors.get(permit.estimated_start_date.month, 1.0)
        else:
            seasonal_factor = 1.0
        
        # Calculate proximity to stores (simplified for sample data)
        proximity = {}
        for store_name in self.store_locations.keys():
            # In production, would calculate actual geographic distance
            proximity[store_name] = 5.0 + (hash(permit.address) % 20)  # Sample distance
        
        return PermitImpact(
            permit=permit,
            equipment_needs=list(set(base_equipment)),  # Remove duplicates
            demand_level=demand_level,
            rental_duration_estimate=pattern['duration_estimate'],
            seasonal_factor=seasonal_factor,
            proximity_to_stores=proximity
        )
    
    def _assign_permit_to_store(self, permit: BuildingPermit) -> str:
        """Assign permit to nearest store (simplified for sample data)"""
        city_store_mapping = {
            'minneapolis': 'fridley',
            'saint paul': 'brooklyn_park',
            'wayzata': 'wayzata',
            'brooklyn park': 'brooklyn_park',
            'fridley': 'fridley',
            'elk river': 'elk_river'
        }
        
        return city_store_mapping.get(permit.city.lower(), 'fridley')
    
    def _generate_permits_summary(self, permit_impacts: List[PermitImpact]) -> Dict[str, Any]:
        """Generate summary of permits analysis"""
        
        total_permits = len(permit_impacts)
        total_value = sum(pi.permit.estimated_value for pi in permit_impacts)
        high_demand_permits = [pi for pi in permit_impacts if pi.demand_level in ['high', 'very_high']]
        
        # Equipment demand aggregation
        equipment_counts = {}
        for impact in permit_impacts:
            for equipment in impact.equipment_needs:
                equipment_counts[equipment] = equipment_counts.get(equipment, 0) + 1
        
        top_equipment = sorted(equipment_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_permits': total_permits,
            'total_project_value': total_value,
            'high_demand_permits': len(high_demand_permits),
            'average_project_value': total_value / max(total_permits, 1),
            'top_equipment_demand': dict(top_equipment),
            'estimated_total_rental_days': sum(pi.rental_duration_estimate for pi in permit_impacts)
        }
    
    def _generate_construction_outlook(self, monthly_demand: Dict[str, Any]) -> Dict[str, Any]:
        """Generate construction outlook based on monthly demand"""
        
        peak_month = max(
            monthly_demand.keys(),
            key=lambda k: monthly_demand[k].get('adjusted_demand_score', 0)
        )
        
        low_month = min(
            monthly_demand.keys(),
            key=lambda k: monthly_demand[k].get('adjusted_demand_score', 0)
        )
        
        return {
            'peak_demand_month': peak_month,
            'lowest_demand_month': low_month,
            'seasonal_trend': 'Minnesota construction follows typical seasonal patterns with peak activity in summer months',
            'outlook': 'Moderate to high construction activity expected based on permit volume'
        }
    
    def _generate_area_recommendations(self, area_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on area analysis"""
        
        recommendations = []
        
        # Find store with highest permit activity
        highest_activity_store = max(
            area_analysis.keys(),
            key=lambda k: area_analysis[k]['permits_count']
        )
        
        recommendations.append(
            f"Highest construction activity near {highest_activity_store} store - consider inventory expansion"
        )
        
        # Check for equipment gaps
        all_equipment = set()
        for store_data in area_analysis.values():
            all_equipment.update(store_data['equipment_opportunities'])
        
        if len(all_equipment) > 10:
            recommendations.append("High equipment diversity needed - ensure comprehensive inventory")
        
        # Value-based recommendations
        high_value_stores = [
            store for store, data in area_analysis.items()
            if data['total_value'] > 1000000
        ]
        
        if high_value_stores:
            recommendations.append(
                f"High-value projects near {', '.join(high_value_stores)} - premium equipment demand expected"
            )
        
        return recommendations
    
    def _generate_demand_insights(self, equipment_analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from equipment demand analysis"""
        
        insights = []
        
        # Find most in-demand equipment
        if equipment_analysis:
            top_equipment = max(
                equipment_analysis.keys(),
                key=lambda k: equipment_analysis[k]['demand_count']
            )
            
            insights.append(
                f"Highest demand equipment: {top_equipment} with "
                f"{equipment_analysis[top_equipment]['demand_count']} project needs"
            )
        
        # Long-duration equipment identification
        long_duration_equipment = [
            equip for equip, data in equipment_analysis.items()
            if data['average_duration'] > 100
        ]
        
        if long_duration_equipment:
            insights.append(
                f"Long-term rental opportunities: {', '.join(long_duration_equipment[:3])}"
            )
        
        # High-value equipment opportunities
        very_high_demand = [
            equip for equip, data in equipment_analysis.items()
            if data['peak_demand_level'] == 'very_high'
        ]
        
        if very_high_demand:
            insights.append(
                f"Premium equipment opportunities: {', '.join(very_high_demand[:3])}"
            )
        
        return insights