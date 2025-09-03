"""
Enhanced Executive Analytics Service
Leverages the 533 equipment correlations for advanced executive insights
Provides equipment-level ROI, predictive analytics, and cross-system intelligence
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, func
from decimal import Decimal
import logging

from app import db
from app.services.logger import get_logger
from app.services.financial_analytics_service import FinancialAnalyticsService

logger = get_logger(__name__)

class EnhancedExecutiveService:
    """
    Executive analytics service that fully utilizes POS-RFID correlation data
    """
    
    def __init__(self):
        self.financial_service = FinancialAnalyticsService()
        self.logger = logger
    
    def get_executive_dashboard_with_correlations(self) -> Dict:
        """
        Get comprehensive executive dashboard leveraging correlation data
        """
        try:
            dashboard_data = {
                'equipment_roi_analysis': self.get_equipment_roi_analysis(),
                'correlation_quality_metrics': self.get_correlation_quality_metrics(),
                'real_time_utilization': self.get_real_time_utilization_metrics(),
                'revenue_attribution': self.get_revenue_attribution_analysis(),
                'predictive_insights': self.get_predictive_insights(),
                'cross_system_alerts': self.get_cross_system_alerts(),
                'executive_kpis': self.get_enhanced_executive_kpis()
            }
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data': dashboard_data,
                'correlation_coverage': self.get_correlation_coverage_stats()
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced executive dashboard: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_equipment_roi_analysis(self) -> Dict:
        """
        Analyze ROI at equipment level using correlation data
        """
        try:
            # Get equipment performance data using correlations
            roi_query = text("""
                SELECT 
                    ci.category,
                    ci.equipment_name,
                    ci.pos_quantity,
                    ci.rfid_tag_count,
                    ci.rental_rate,
                    ci.utilization_percentage,
                    ci.current_rental_revenue,
                    ci.data_quality_flag,
                    ci.store_code,
                    
                    -- Calculate potential revenue
                    (ci.rental_rate * ci.pos_quantity * 30) as monthly_potential_revenue,
                    
                    -- Performance metrics
                    CASE 
                        WHEN ci.utilization_percentage >= 80 THEN 'high_performer'
                        WHEN ci.utilization_percentage >= 50 THEN 'moderate_performer'
                        WHEN ci.utilization_percentage >= 20 THEN 'low_performer'
                        ELSE 'underperformer'
                    END as performance_category
                    
                FROM combined_inventory ci
                WHERE ci.rental_rate > 0
                AND ci.data_quality_flag IN ('good_quality', 'quantity_mismatch')
                ORDER BY ci.current_rental_revenue DESC
                LIMIT 100
            """)
            
            results = db.session.execute(roi_query).fetchall()
            
            # Process results for ROI analysis
            equipment_analysis = []
            category_performance = {}
            
            for row in results:
                equipment_data = {
                    'category': row.category,
                    'name': row.equipment_name[:50] + '...' if len(row.equipment_name) > 50 else row.equipment_name,
                    'store': row.store_code,
                    'quantity': row.pos_quantity,
                    'rfid_tags': row.rfid_tag_count,
                    'rental_rate': float(row.rental_rate or 0),
                    'utilization': float(row.utilization_percentage or 0),
                    'current_revenue': float(row.current_rental_revenue or 0),
                    'potential_revenue': float(row.monthly_potential_revenue or 0),
                    'performance_category': row.performance_category,
                    'data_quality': row.data_quality_flag
                }
                
                # Calculate ROI efficiency
                if equipment_data['potential_revenue'] > 0:
                    equipment_data['roi_efficiency'] = round(
                        (equipment_data['current_revenue'] / equipment_data['potential_revenue']) * 100, 1
                    )
                else:
                    equipment_data['roi_efficiency'] = 0
                
                equipment_analysis.append(equipment_data)
                
                # Aggregate by category
                category = row.category
                if category not in category_performance:
                    category_performance[category] = {
                        'total_items': 0,
                        'total_current_revenue': 0,
                        'total_potential_revenue': 0,
                        'avg_utilization': 0,
                        'performance_categories': {'high_performer': 0, 'moderate_performer': 0, 'low_performer': 0, 'underperformer': 0}
                    }
                
                category_performance[category]['total_items'] += 1
                category_performance[category]['total_current_revenue'] += equipment_data['current_revenue']
                category_performance[category]['total_potential_revenue'] += equipment_data['potential_revenue']
                category_performance[category]['avg_utilization'] += equipment_data['utilization']
                category_performance[category]['performance_categories'][row.performance_category] += 1
            
            # Calculate category averages
            for category in category_performance:
                data = category_performance[category]
                if data['total_items'] > 0:
                    data['avg_utilization'] = round(data['avg_utilization'] / data['total_items'], 1)
                    data['category_roi_efficiency'] = round(
                        (data['total_current_revenue'] / data['total_potential_revenue']) * 100, 1
                    ) if data['total_potential_revenue'] > 0 else 0
                    
            return {
                'success': True,
                'equipment_analysis': equipment_analysis[:20],  # Top 20 for performance
                'category_performance': category_performance,
                'total_analyzed_items': len(equipment_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in equipment ROI analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_correlation_quality_metrics(self) -> Dict:
        """
        Analyze the quality and coverage of POS-RFID correlations
        """
        try:
            quality_query = text("""
                SELECT 
                    data_quality_flag,
                    COUNT(*) as item_count,
                    SUM(pos_quantity) as total_pos_inventory,
                    SUM(rfid_tag_count) as total_rfid_tags,
                    ROUND(AVG(utilization_percentage), 2) as avg_utilization,
                    SUM(current_rental_revenue) as total_current_revenue,
                    COUNT(DISTINCT store_code) as stores_covered,
                    COUNT(DISTINCT category) as categories_covered
                FROM combined_inventory
                GROUP BY data_quality_flag
                ORDER BY item_count DESC
            """)
            
            results = db.session.execute(quality_query).fetchall()
            
            quality_metrics = {}
            totals = {
                'total_items': 0,
                'total_pos_inventory': 0,
                'total_rfid_tags': 0,
                'total_revenue': 0
            }
            
            for row in results:
                quality_flag = row.data_quality_flag
                quality_metrics[quality_flag] = {
                    'item_count': row.item_count,
                    'pos_inventory': row.total_pos_inventory,
                    'rfid_tags': row.total_rfid_tags,
                    'avg_utilization': float(row.avg_utilization or 0),
                    'current_revenue': float(row.total_current_revenue or 0),
                    'stores_covered': row.stores_covered,
                    'categories_covered': row.categories_covered
                }
                
                totals['total_items'] += row.item_count
                totals['total_pos_inventory'] += row.total_pos_inventory
                totals['total_rfid_tags'] += row.total_rfid_tags
                totals['total_revenue'] += float(row.total_current_revenue or 0)
            
            # Calculate coverage percentages
            correlation_summary = {
                'total_coverage_stats': totals,
                'quality_breakdown': quality_metrics,
                'coverage_analysis': {
                    'good_quality_percentage': round(
                        (quality_metrics.get('good_quality', {}).get('item_count', 0) / totals['total_items']) * 100, 1
                    ) if totals['total_items'] > 0 else 0,
                    'correlation_effectiveness': round(
                        (totals['total_rfid_tags'] / totals['total_pos_inventory']) * 100, 1
                    ) if totals['total_pos_inventory'] > 0 else 0
                }
            }
            
            return {
                'success': True,
                'correlation_summary': correlation_summary,
                'improvement_opportunities': self._identify_correlation_improvements(quality_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlation quality: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_real_time_utilization_metrics(self) -> Dict:
        """
        Get real-time utilization metrics across all stores using correlation data
        """
        try:
            utilization_query = text("""
                SELECT 
                    store_code,
                    category,
                    COUNT(*) as total_items,
                    ROUND(AVG(utilization_percentage), 2) as avg_utilization,
                    COUNT(CASE WHEN status = 'fully_rented' THEN 1 END) as fully_rented_count,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_count,
                    SUM(current_rental_revenue) as total_revenue,
                    
                    -- Capacity analysis
                    SUM(pos_quantity) as total_capacity,
                    SUM(CASE WHEN status = 'fully_rented' OR status = 'partially_rented' THEN pos_quantity ELSE 0 END) as utilized_capacity
                    
                FROM combined_inventory
                WHERE rental_rate > 0
                GROUP BY store_code, category
                ORDER BY store_code, total_revenue DESC
            """)
            
            results = db.session.execute(utilization_query).fetchall()
            
            store_metrics = {}
            category_insights = {}
            
            for row in results:
                store_code = row.store_code
                category = row.category
                
                # Store-level aggregation
                if store_code not in store_metrics:
                    store_metrics[store_code] = {
                        'total_items': 0,
                        'total_revenue': 0,
                        'total_capacity': 0,
                        'utilized_capacity': 0,
                        'avg_utilization': 0,
                        'categories': {}
                    }
                
                store_data = {
                    'total_items': row.total_items,
                    'avg_utilization': float(row.avg_utilization or 0),
                    'fully_rented': row.fully_rented_count,
                    'available': row.available_count,
                    'revenue': float(row.total_revenue or 0),
                    'capacity': row.total_capacity,
                    'utilized_capacity': row.utilized_capacity
                }
                
                store_metrics[store_code]['categories'][category] = store_data
                store_metrics[store_code]['total_items'] += row.total_items
                store_metrics[store_code]['total_revenue'] += store_data['revenue']
                store_metrics[store_code]['total_capacity'] += row.total_capacity
                store_metrics[store_code]['utilized_capacity'] += row.utilized_capacity
                
                # Category insights across all stores
                if category not in category_insights:
                    category_insights[category] = {
                        'total_items': 0,
                        'total_revenue': 0,
                        'utilization_scores': [],
                        'stores_with_category': 0
                    }
                
                category_insights[category]['total_items'] += row.total_items
                category_insights[category]['total_revenue'] += store_data['revenue']
                category_insights[category]['utilization_scores'].append(store_data['avg_utilization'])
                category_insights[category]['stores_with_category'] += 1
            
            # Calculate store-level averages
            for store_code in store_metrics:
                store = store_metrics[store_code]
                if store['total_items'] > 0:
                    store['overall_capacity_utilization'] = round(
                        (store['utilized_capacity'] / store['total_capacity']) * 100, 1
                    ) if store['total_capacity'] > 0 else 0
            
            # Calculate category averages
            for category in category_insights:
                data = category_insights[category]
                if data['utilization_scores']:
                    data['avg_utilization'] = round(np.mean(data['utilization_scores']), 1)
                    data['utilization_variance'] = round(np.var(data['utilization_scores']), 1)
            
            return {
                'success': True,
                'store_metrics': store_metrics,
                'category_insights': category_insights,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time utilization: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_enhanced_executive_kpis(self) -> Dict:
        """
        Get enhanced executive KPIs using correlation data
        """
        try:
            # Overall system KPIs
            system_query = text("""
                SELECT 
                    COUNT(*) as total_equipment_items,
                    COUNT(DISTINCT store_code) as active_stores,
                    COUNT(DISTINCT category) as equipment_categories,
                    SUM(pos_quantity) as total_inventory_units,
                    SUM(rfid_tag_count) as total_rfid_tracked,
                    
                    -- Revenue metrics
                    SUM(current_rental_revenue) as total_current_revenue,
                    ROUND(AVG(rental_rate), 2) as avg_rental_rate,
                    ROUND(AVG(utilization_percentage), 2) as system_wide_utilization,
                    
                    -- Quality metrics
                    COUNT(CASE WHEN data_quality_flag = 'good_quality' THEN 1 END) as high_quality_correlations,
                    COUNT(CASE WHEN data_quality_flag = 'quantity_mismatch' THEN 1 END) as quantity_mismatches,
                    
                    -- Status distribution
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_items,
                    COUNT(CASE WHEN status = 'fully_rented' THEN 1 END) as fully_rented_items,
                    COUNT(CASE WHEN status = 'partially_rented' THEN 1 END) as partially_rented_items
                    
                FROM combined_inventory
                WHERE rental_rate > 0
            """)
            
            result = db.session.execute(system_query).fetchone()
            
            if not result:
                return {'success': False, 'error': 'No data available'}
            
            # Calculate key executive metrics
            total_items = result.total_equipment_items
            correlation_coverage = round(
                (result.total_rfid_tracked / result.total_inventory_units) * 100, 1
            ) if result.total_inventory_units > 0 else 0
            
            data_quality_score = round(
                (result.high_quality_correlations / total_items) * 100, 1
            ) if total_items > 0 else 0
            
            operational_efficiency = round(
                ((result.fully_rented_items + result.partially_rented_items) / total_items) * 100, 1
            ) if total_items > 0 else 0
            
            enhanced_kpis = {
                'system_overview': {
                    'total_equipment_items': total_items,
                    'active_stores': result.active_stores,
                    'equipment_categories': result.equipment_categories,
                    'correlation_coverage_percent': correlation_coverage,
                    'data_quality_score': data_quality_score
                },
                'revenue_performance': {
                    'total_current_revenue': round(float(result.total_current_revenue or 0), 2),
                    'avg_rental_rate': float(result.avg_rental_rate or 0),
                    'system_utilization_percent': float(result.system_wide_utilization or 0)
                },
                'operational_metrics': {
                    'available_items': result.available_items,
                    'fully_rented_items': result.fully_rented_items,
                    'partially_rented_items': result.partially_rented_items,
                    'operational_efficiency_percent': operational_efficiency
                },
                'data_quality_metrics': {
                    'high_quality_correlations': result.high_quality_correlations,
                    'quantity_mismatches': result.quantity_mismatches,
                    'total_rfid_tracked': result.total_rfid_tracked,
                    'total_inventory_units': result.total_inventory_units
                }
            }
            
            return {
                'success': True,
                'enhanced_kpis': enhanced_kpis,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced executive KPIs: {e}")
            return {'success': False, 'error': str(e)}
    
    def _identify_correlation_improvements(self, quality_metrics: Dict) -> List[str]:
        """
        Identify opportunities to improve correlation quality
        """
        improvements = []
        
        no_correlation = quality_metrics.get('no_rfid_correlation', {})
        if no_correlation.get('item_count', 0) > 0:
            improvements.append(f"Establish RFID tracking for {no_correlation['item_count']} uncorrelated items")
        
        quantity_mismatch = quality_metrics.get('quantity_mismatch', {})
        if quantity_mismatch.get('item_count', 0) > 0:
            improvements.append(f"Resolve quantity discrepancies for {quantity_mismatch['item_count']} items")
        
        low_confidence = quality_metrics.get('low_confidence_match', {})
        if low_confidence.get('item_count', 0) > 0:
            improvements.append(f"Improve correlation confidence for {low_confidence['item_count']} items")
        
        return improvements
    
    def get_correlation_coverage_stats(self) -> Dict:
        """
        Get correlation coverage statistics
        """
        try:
            coverage_query = text("""
                SELECT 
                    'Overall System' as metric,
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN data_quality_flag != 'no_rfid_correlation' THEN 1 END) as correlated_items
                FROM combined_inventory
            """)
            
            result = db.session.execute(coverage_query).fetchone()
            
            if result and result.total_items > 0:
                coverage_percent = round((result.correlated_items / result.total_items) * 100, 1)
                return {
                    'total_items': result.total_items,
                    'correlated_items': result.correlated_items,
                    'coverage_percent': coverage_percent
                }
            
            return {'total_items': 0, 'correlated_items': 0, 'coverage_percent': 0}
            
        except Exception as e:
            logger.error(f"Error getting coverage stats: {e}")
            return {'error': str(e)}
    
    # Placeholder methods for future implementation
    def get_revenue_attribution_analysis(self) -> Dict:
        """Future: Revenue attribution using correlations"""
        return {'success': True, 'message': 'Revenue attribution analysis - coming soon'}
    
    def get_predictive_insights(self) -> Dict:
        """Future: Predictive analytics using correlation trends"""
        return {'success': True, 'message': 'Predictive insights - coming soon'}
    
    def get_cross_system_alerts(self) -> List[Dict]:
        """Future: Cross-system alerts based on correlation data"""
        return [{'type': 'info', 'message': 'Cross-system alerting - coming soon'}]