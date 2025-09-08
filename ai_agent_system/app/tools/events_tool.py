"""
Events Data Tool for Minnesota Equipment Rental AI Agent
Tracks Minnesota events, festivals, and activities that drive equipment rental demand
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
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event data structure"""
    name: str
    date_start: datetime
    date_end: datetime
    location: str
    category: str
    expected_attendance: Optional[int]
    description: str
    equipment_demand_level: str  # low, medium, high
    outdoor: bool
    source: str
    url: Optional[str] = None


@dataclass
class EventImpact:
    """Event impact analysis"""
    event: Event
    rental_opportunity: str
    equipment_types: List[str]
    demand_multiplier: float
    preparation_lead_time: int  # days
    local_business_impact: str


class EventsQueryInput(BaseModel):
    """Input schema for events queries"""
    query_type: str = Field(
        description="Type of query: 'upcoming', 'search', 'impact_analysis', 'calendar'"
    )
    timeframe_days: int = Field(
        default=30, description="Number of days to look ahead"
    )
    category: Optional[str] = Field(
        description="Event category filter: 'festival', 'corporate', 'sports', 'construction'"
    )
    location: Optional[str] = Field(
        description="Location filter for events"
    )
    search_term: Optional[str] = Field(
        description="Search term for finding specific events"
    )
    attendance_min: Optional[int] = Field(
        description="Minimum expected attendance filter"
    )


class EventsTool(BaseTool):
    """
    LangChain tool for Minnesota events data and rental demand analysis
    
    Tracks events that drive equipment rental demand:
    - Minnesota State Fair and major festivals
    - Corporate events and conventions
    - Sports events and tournaments
    - Construction and building projects
    - Wedding and social events
    - Educational institution events
    """
    
    name = "events_data"
    description = """
    Get Minnesota events data for equipment rental demand forecasting.
    
    Use this tool for:
    - Upcoming events that may drive rental demand
    - Event impact analysis on different equipment categories
    - Seasonal event patterns and planning
    - Corporate and wedding event forecasting
    - Festival and outdoor event equipment needs
    - Construction project calendars
    
    Event sources include:
    - Minnesota State Fair
    - Explore Minnesota tourism events
    - Minneapolis and St. Paul event calendars
    - Corporate venue bookings
    - Sports and entertainment venues
    - Construction permit schedules
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Minnesota event sources
        self.event_sources = {
            'mn_state_fair': {
                'url': 'https://www.mnstatefair.org',
                'api': None,  # Would integrate with actual API
                'seasons': ['summer'],
                'equipment_demand': 'extremely_high'
            },
            'explore_mn': {
                'url': 'https://www.exploreminnesota.com/events',
                'seasons': ['year_round'],
                'equipment_demand': 'variable'
            },
            'minneapolis_events': {
                'url': 'https://www.minneapolis.org/calendar/',
                'seasons': ['year_round'],
                'equipment_demand': 'medium'
            },
            'saint_paul_events': {
                'url': 'https://visitsaintpaul.com/events/',
                'seasons': ['year_round'],
                'equipment_demand': 'medium'
            }
        }
        
        # Equipment demand patterns by event type
        self.equipment_patterns = {
            'state_fair': {
                'equipment_types': [
                    'generators', 'lighting', 'fencing', 'stages', 'tents',
                    'power_distribution', 'cooling_fans', 'heaters'
                ],
                'demand_multiplier': 5.0,
                'lead_time_days': 180,
                'duration_impact': 'extreme'
            },
            'outdoor_festival': {
                'equipment_types': [
                    'stages', 'tents', 'generators', 'lighting', 'sound_barriers',
                    'portable_restrooms', 'fencing', 'tables_chairs'
                ],
                'demand_multiplier': 3.0,
                'lead_time_days': 90,
                'duration_impact': 'high'
            },
            'corporate_event': {
                'equipment_types': [
                    'tables_chairs', 'linens', 'av_equipment', 'stages',
                    'lighting', 'tents', 'heaters_cooling'
                ],
                'demand_multiplier': 2.0,
                'lead_time_days': 30,
                'duration_impact': 'medium'
            },
            'wedding': {
                'equipment_types': [
                    'tents', 'tables_chairs', 'linens', 'lighting',
                    'dance_floors', 'generators', 'heaters'
                ],
                'demand_multiplier': 1.5,
                'lead_time_days': 180,
                'duration_impact': 'low'
            },
            'sports_event': {
                'equipment_types': [
                    'bleachers', 'fencing', 'generators', 'lighting',
                    'sound_equipment', 'tents', 'portable_restrooms'
                ],
                'demand_multiplier': 2.5,
                'lead_time_days': 60,
                'duration_impact': 'medium'
            },
            'construction_project': {
                'equipment_types': [
                    'excavators', 'skid_steers', 'generators', 'lighting',
                    'pumps', 'compressors', 'scaffolding'
                ],
                'demand_multiplier': 4.0,
                'lead_time_days': 14,
                'duration_impact': 'very_high'
            }
        }
        
        # Seasonal event patterns
        self.seasonal_patterns = {
            'spring': {
                'peak_events': ['graduation', 'wedding_season_start', 'construction_ramp_up'],
                'equipment_focus': ['tents', 'construction_equipment', 'landscaping']
            },
            'summer': {
                'peak_events': ['state_fair', 'festivals', 'weddings', 'corporate_picnics'],
                'equipment_focus': ['event_equipment', 'cooling', 'outdoor_staging']
            },
            'fall': {
                'peak_events': ['harvest_festivals', 'homecoming', 'construction_finish'],
                'equipment_focus': ['construction_equipment', 'heating', 'indoor_events']
            },
            'winter': {
                'peak_events': ['holiday_parties', 'conventions', 'indoor_events'],
                'equipment_focus': ['indoor_equipment', 'heating', 'lighting']
            }
        }
    
    def _run(self, query_input: str) -> str:
        """Execute events query"""
        try:
            # Parse input
            if isinstance(query_input, str):
                try:
                    input_data = json.loads(query_input)
                except json.JSONDecodeError:
                    # Treat as search term
                    input_data = {
                        'query_type': 'search',
                        'search_term': query_input
                    }
            else:
                input_data = query_input
            
            query_params = EventsQueryInput(**input_data)
            
            # Route to appropriate method
            if query_params.query_type == 'upcoming':
                result = self._get_upcoming_events(
                    query_params.timeframe_days,
                    query_params.category,
                    query_params.location
                )
            elif query_params.query_type == 'search':
                result = self._search_events(
                    query_params.search_term,
                    query_params.timeframe_days
                )
            elif query_params.query_type == 'impact_analysis':
                result = self._analyze_event_impact(
                    query_params.timeframe_days,
                    query_params.category
                )
            elif query_params.query_type == 'calendar':
                result = self._get_event_calendar(
                    query_params.timeframe_days,
                    query_params.category
                )
            else:
                result = {
                    'success': False,
                    'error': f"Unknown query type: {query_params.query_type}"
                }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Events tool error: {e}", exc_info=True)
            return json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def _get_upcoming_events(
        self, 
        timeframe_days: int, 
        category: Optional[str], 
        location: Optional[str]
    ) -> Dict[str, Any]:
        """Get upcoming events within timeframe"""
        
        # In production, this would fetch from real APIs
        # For now, generating sample data based on known Minnesota events
        sample_events = self._generate_sample_events(timeframe_days)
        
        # Filter by category and location if specified
        if category:
            sample_events = [e for e in sample_events if e.category.lower() == category.lower()]
        
        if location:
            sample_events = [e for e in sample_events if location.lower() in e.location.lower()]
        
        # Analyze each event's rental impact
        event_impacts = []
        for event in sample_events:
            impact = self._calculate_event_impact(event)
            event_impacts.append(impact)
        
        # Sort by demand level and date
        event_impacts.sort(key=lambda x: (
            x.demand_multiplier,
            x.event.date_start
        ), reverse=True)
        
        return {
            'success': True,
            'timeframe_days': timeframe_days,
            'events_found': len(event_impacts),
            'events': [asdict(ei) for ei in event_impacts],
            'summary': self._generate_events_summary(event_impacts),
            'timestamp': datetime.now().isoformat()
        }
    
    def _search_events(self, search_term: str, timeframe_days: int) -> Dict[str, Any]:
        """Search for specific events"""
        if not search_term:
            return {'success': False, 'error': 'No search term provided'}
        
        # Generate sample events and filter by search term
        all_events = self._generate_sample_events(timeframe_days)
        
        search_lower = search_term.lower()
        matching_events = [
            e for e in all_events
            if (search_lower in e.name.lower() or
                search_lower in e.description.lower() or
                search_lower in e.category.lower())
        ]
        
        # Calculate impact for matching events
        event_impacts = [
            self._calculate_event_impact(event)
            for event in matching_events
        ]
        
        return {
            'success': True,
            'search_term': search_term,
            'matches_found': len(event_impacts),
            'events': [asdict(ei) for ei in event_impacts],
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_event_impact(
        self, 
        timeframe_days: int, 
        category: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze overall event impact on equipment rental business"""
        
        events = self._generate_sample_events(timeframe_days)
        if category:
            events = [e for e in events if e.category.lower() == category.lower()]
        
        # Calculate total impact
        total_impact = {
            'high_demand_periods': [],
            'equipment_type_demand': {},
            'revenue_opportunity': 0,
            'capacity_requirements': {}
        }
        
        for event in events:
            impact = self._calculate_event_impact(event)
            
            # Track high demand periods
            if impact.demand_multiplier >= 3.0:
                total_impact['high_demand_periods'].append({
                    'event_name': event.name,
                    'date_start': event.date_start.isoformat(),
                    'date_end': event.date_end.isoformat(),
                    'demand_multiplier': impact.demand_multiplier
                })
            
            # Aggregate equipment demand
            for equipment in impact.equipment_types:
                if equipment not in total_impact['equipment_type_demand']:
                    total_impact['equipment_type_demand'][equipment] = 0
                total_impact['equipment_type_demand'][equipment] += impact.demand_multiplier
        
        # Sort equipment by demand
        sorted_equipment = sorted(
            total_impact['equipment_type_demand'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'success': True,
            'analysis_period': f'{timeframe_days} days',
            'category_filter': category,
            'events_analyzed': len(events),
            'total_impact': total_impact,
            'top_equipment_demand': dict(sorted_equipment[:10]),
            'business_recommendations': self._generate_business_recommendations(events),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_event_calendar(
        self, 
        timeframe_days: int, 
        category: Optional[str]
    ) -> Dict[str, Any]:
        """Get event calendar view"""
        
        events = self._generate_sample_events(timeframe_days)
        if category:
            events = [e for e in events if e.category.lower() == category.lower()]
        
        # Organize events by month
        monthly_calendar = {}
        for event in events:
            month_key = event.date_start.strftime('%Y-%m')
            if month_key not in monthly_calendar:
                monthly_calendar[month_key] = []
            
            impact = self._calculate_event_impact(event)
            monthly_calendar[month_key].append({
                'event': asdict(event),
                'impact': asdict(impact)
            })
        
        # Sort each month's events by date
        for month in monthly_calendar:
            monthly_calendar[month].sort(
                key=lambda x: x['event']['date_start']
            )
        
        return {
            'success': True,
            'calendar_period': f'{timeframe_days} days',
            'category_filter': category,
            'monthly_calendar': monthly_calendar,
            'total_events': len(events),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_sample_events(self, timeframe_days: int) -> List[Event]:
        """Generate sample Minnesota events (would be replaced with real API calls)"""
        
        current_date = datetime.now()
        end_date = current_date + timedelta(days=timeframe_days)
        
        sample_events = []
        
        # Minnesota State Fair (typically late August - early September)
        if current_date.month <= 9:
            fair_start = datetime(current_date.year, 8, 24)
            fair_end = datetime(current_date.year, 9, 4)
            if fair_start <= end_date:
                sample_events.append(Event(
                    name="Minnesota State Fair",
                    date_start=fair_start,
                    date_end=fair_end,
                    location="St. Paul, MN",
                    category="festival",
                    expected_attendance=2000000,
                    description="The Great Minnesota Get-Together - largest state fair in the US",
                    equipment_demand_level="extremely_high",
                    outdoor=True,
                    source="mn_state_fair",
                    url="https://www.mnstatefair.org"
                ))
        
        # Sample corporate events
        for i in range(0, timeframe_days, 14):
            event_date = current_date + timedelta(days=i)
            sample_events.append(Event(
                name=f"Corporate Conference {i//14 + 1}",
                date_start=event_date,
                date_end=event_date + timedelta(days=2),
                location="Minneapolis Convention Center",
                category="corporate",
                expected_attendance=500,
                description="Multi-day corporate conference requiring AV and staging",
                equipment_demand_level="medium",
                outdoor=False,
                source="corporate_venues"
            ))
        
        # Sample wedding season events (spring/summer)
        if 4 <= current_date.month <= 10:  # April to October
            for i in range(0, min(timeframe_days, 90), 7):
                event_date = current_date + timedelta(days=i)
                if event_date.weekday() in [5, 6]:  # Saturday or Sunday
                    sample_events.append(Event(
                        name=f"Wedding Event",
                        date_start=event_date,
                        date_end=event_date,
                        location="Various venues - Twin Cities",
                        category="wedding",
                        expected_attendance=150,
                        description="Outdoor wedding requiring tents, tables, and lighting",
                        equipment_demand_level="medium",
                        outdoor=True,
                        source="wedding_venues"
                    ))
        
        # Sample construction projects
        for i in range(0, timeframe_days, 30):
            event_date = current_date + timedelta(days=i)
            sample_events.append(Event(
                name=f"Construction Project - Phase {i//30 + 1}",
                date_start=event_date,
                date_end=event_date + timedelta(days=45),
                location="Twin Cities Metro",
                category="construction",
                expected_attendance=None,
                description="Major construction project requiring heavy equipment",
                equipment_demand_level="high",
                outdoor=True,
                source="construction_permits"
            ))
        
        # Filter events within timeframe
        return [e for e in sample_events if e.date_start <= end_date]
    
    def _calculate_event_impact(self, event: Event) -> EventImpact:
        """Calculate rental impact for a specific event"""
        
        # Match event to equipment pattern
        pattern_key = 'corporate_event'  # default
        
        if 'state fair' in event.name.lower():
            pattern_key = 'state_fair'
        elif event.category == 'festival':
            pattern_key = 'outdoor_festival'
        elif event.category == 'wedding':
            pattern_key = 'wedding'
        elif event.category == 'corporate':
            pattern_key = 'corporate_event'
        elif event.category == 'construction':
            pattern_key = 'construction_project'
        elif 'sport' in event.category.lower():
            pattern_key = 'sports_event'
        
        pattern = self.equipment_patterns[pattern_key]
        
        # Calculate demand multiplier based on event size and type
        base_multiplier = pattern['demand_multiplier']
        
        if event.expected_attendance:
            if event.expected_attendance > 10000:
                base_multiplier *= 1.5
            elif event.expected_attendance > 1000:
                base_multiplier *= 1.2
        
        # Determine rental opportunity level
        if base_multiplier >= 4.0:
            opportunity = "extremely_high"
        elif base_multiplier >= 3.0:
            opportunity = "high"
        elif base_multiplier >= 2.0:
            opportunity = "medium"
        else:
            opportunity = "low"
        
        # Local business impact assessment
        impact_radius = "metro_wide" if base_multiplier >= 3.0 else "local"
        
        return EventImpact(
            event=event,
            rental_opportunity=opportunity,
            equipment_types=pattern['equipment_types'],
            demand_multiplier=base_multiplier,
            preparation_lead_time=pattern['lead_time_days'],
            local_business_impact=impact_radius
        )
    
    def _generate_events_summary(self, event_impacts: List[EventImpact]) -> Dict[str, Any]:
        """Generate summary of events and their impacts"""
        
        total_events = len(event_impacts)
        high_impact_events = [ei for ei in event_impacts if ei.demand_multiplier >= 3.0]
        
        # Equipment demand aggregation
        equipment_counts = {}
        for impact in event_impacts:
            for equipment in impact.equipment_types:
                equipment_counts[equipment] = equipment_counts.get(equipment, 0) + 1
        
        top_equipment = sorted(equipment_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_events': total_events,
            'high_impact_events': len(high_impact_events),
            'average_demand_multiplier': sum(ei.demand_multiplier for ei in event_impacts) / max(total_events, 1),
            'top_equipment_types': dict(top_equipment),
            'peak_demand_dates': [
                ei.event.date_start.isoformat()
                for ei in high_impact_events[:3]
            ]
        }
    
    def _generate_business_recommendations(self, events: List[Event]) -> List[str]:
        """Generate business recommendations based on event analysis"""
        
        recommendations = []
        
        # Check for high-demand periods
        high_demand_events = [e for e in events if e.equipment_demand_level in ['high', 'extremely_high']]
        
        if high_demand_events:
            recommendations.append(
                f"Prepare for {len(high_demand_events)} high-demand events in the upcoming period"
            )
        
        # Seasonal recommendations
        current_month = datetime.now().month
        if 3 <= current_month <= 5:  # Spring
            recommendations.append("Spring season: Increase construction and landscaping equipment inventory")
        elif 6 <= current_month <= 8:  # Summer
            recommendations.append("Summer peak: Maximize event equipment availability, expect high tent/staging demand")
        elif 9 <= current_month <= 11:  # Fall
            recommendations.append("Fall season: Focus on construction completion equipment and indoor event setup")
        else:  # Winter
            recommendations.append("Winter season: Prioritize heating equipment and indoor event supplies")
        
        # Equipment-specific recommendations
        outdoor_events = [e for e in events if e.outdoor]
        if len(outdoor_events) > len(events) / 2:
            recommendations.append("High outdoor event volume: Ensure weather protection equipment availability")
        
        corporate_events = [e for e in events if e.category == 'corporate']
        if corporate_events:
            recommendations.append("Corporate events detected: AV equipment and professional staging in high demand")
        
        return recommendations