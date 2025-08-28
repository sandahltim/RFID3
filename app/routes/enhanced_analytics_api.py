"""
Enhanced Analytics API
Fixes data calculation issues and provides accurate visualization data
Version: 2025-08-28 - Executive Dashboard Data Enhancement
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func, text, and_, or_
from datetime import datetime, timedelta
from .. import db
from ..models.db_models import ItemMaster, Transaction, StorePerformance
from ..services.logger import get_logger
from decimal import Decimal
import json

logger = get_logger(__name__)

enhanced_analytics_bp = Blueprint('enhanced_analytics', __name__, url_prefix='/api/enhanced')

@enhanced_analytics_bp.route('/dashboard/kpis')
def get_enhanced_kpis():
    """Get accurate KPI data with proper calculations"""
    try:
        # Get filter parameters
        weeks = int(request.args.get('weeks', 12))
        store_filter = request.args.get('store', 'all')
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Build base query with proper store filtering
        base_query = db.session.query(ItemMaster)
        if store_filter != 'all':
            base_query = base_query.filter(
                or_(ItemMaster.home_store == store_filter,
                    ItemMaster.current_store == store_filter)
            )
        
        # Calculate accurate inventory metrics
        total_items = base_query.count()
        items_on_rent = base_query.filter(
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).count()
        items_available = base_query.filter(
            ItemMaster.status == 'Ready to Rent'
        ).count()
        items_in_service = base_query.filter(
            ItemMaster.status.in_(['Repair', 'Needs to be Inspected', 'Wash'])
        ).count()
        
        # Calculate utilization rate with error handling
        utilization_rate = 0
        if total_items > 0:
            utilization_rate = round((items_on_rent / total_items) * 100, 2)
        
        # Get revenue data from store performance
        revenue_query = db.session.query(
            func.sum(StorePerformance.total_revenue).label('total_revenue'),
            func.avg(StorePerformance.revenue_per_hour).label('avg_efficiency')
        )
        
        if store_filter != 'all':
            revenue_query = revenue_query.filter(StorePerformance.store_code == store_filter)
        
        revenue_data = revenue_query.filter(
            StorePerformance.period_ending >= start_date.date()
        ).first()
        
        total_revenue = float(revenue_data.total_revenue or 0)
        avg_efficiency = float(revenue_data.avg_efficiency or 0)
        
        # Get trend data for the last 12 weeks
        trend_data = []
        for i in range(min(weeks, 12)):
            week_start = end_date - timedelta(weeks=i+1)
            week_end = end_date - timedelta(weeks=i)
            
            week_revenue = db.session.query(
                func.sum(StorePerformance.total_revenue)
            ).filter(
                and_(
                    StorePerformance.period_ending >= week_start.date(),
                    StorePerformance.period_ending < week_end.date()
                )
            ).scalar() or 0
            
            trend_data.insert(0, float(week_revenue))
        
        # Calculate growth rates
        revenue_growth = 0
        utilization_trend = 0
        efficiency_trend = 0
        
        if len(trend_data) >= 2:
            current_revenue = trend_data[-1]
            previous_revenue = trend_data[-2]
            if previous_revenue > 0:
                revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
        
        # Get active alerts count
        active_alerts = db.session.query(
            func.count()
        ).select_from(
            text("inventory_health_alerts")
        ).filter(
            text("status = 'active'")
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_items': total_items,
                'items_on_rent': items_on_rent,
                'items_available': items_available,
                'items_in_service': items_in_service,
                'utilization_rate': utilization_rate,
                'total_revenue': total_revenue,
                'avg_efficiency': avg_efficiency,
                'revenue_growth': round(revenue_growth, 2),
                'utilization_trend': utilization_trend,
                'efficiency_trend': efficiency_trend,
                'active_alerts': active_alerts,
                'trends': {
                    'revenue': trend_data
                },
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'filter_context': {
                    'weeks': weeks,
                    'store': store_filter,
                    'total_items_in_view': total_items
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching enhanced KPIs: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'total_items': 0,
                'items_on_rent': 0,
                'items_available': 0,
                'items_in_service': 0,
                'utilization_rate': 0,
                'total_revenue': 0,
                'avg_efficiency': 0,
                'revenue_growth': 0,
                'active_alerts': 0,
                'trends': {'revenue': []},
                'period': 'Error loading data'
            }
        }), 500

@enhanced_analytics_bp.route('/dashboard/store-performance')
def get_store_performance():
    """Get accurate store performance comparison data"""
    try:
        weeks = int(request.args.get('weeks', 4))
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Get store performance data
        store_performance = db.session.query(
            StorePerformance.store_code,
            func.avg(StorePerformance.total_revenue).label('avg_revenue'),
            func.avg(StorePerformance.revenue_per_hour).label('avg_efficiency'),
            func.avg(StorePerformance.labor_cost_ratio).label('avg_labor_ratio')
        ).filter(
            StorePerformance.period_ending >= start_date.date()
        ).group_by(
            StorePerformance.store_code
        ).all()
        
        # Format store performance data
        stores_data = []
        for store in store_performance:
            stores_data.append({
                'store_code': store.store_code,
                'store_name': get_store_name(store.store_code),
                'avg_revenue': float(store.avg_revenue or 0),
                'efficiency': float(store.avg_efficiency or 0),
                'labor_ratio': float(store.avg_labor_ratio or 0)
            })
        
        # Sort by efficiency descending
        stores_data.sort(key=lambda x: x['efficiency'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': stores_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching store performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@enhanced_analytics_bp.route('/dashboard/inventory-distribution')
def get_inventory_distribution():
    """Get accurate inventory distribution by status and store"""
    try:
        store_filter = request.args.get('store', 'all')
        
        # Build base query
        base_query = db.session.query(ItemMaster)
        if store_filter != 'all':
            base_query = base_query.filter(
                or_(ItemMaster.home_store == store_filter,
                    ItemMaster.current_store == store_filter)
            )
        
        # Get distribution by status
        status_distribution = base_query.with_entities(
            ItemMaster.status,
            func.count(ItemMaster.id).label('count')
        ).group_by(ItemMaster.status).all()
        
        # Format status distribution
        status_labels = []
        status_values = []
        total_items = 0
        
        for status, count in status_distribution:
            status_labels.append(status or 'Unknown')
            status_values.append(count)
            total_items += count
        
        # Get distribution by store if no store filter
        store_data = []
        if store_filter == 'all':
            store_distribution = base_query.with_entities(
                ItemMaster.current_store,
                func.count(ItemMaster.id).label('count')
            ).group_by(ItemMaster.current_store).all()
            
            for store_code, count in store_distribution:
                store_data.append({
                    'store_code': store_code or '000',
                    'store_name': get_store_name(store_code),
                    'item_count': count
                })
        
        # Get type distribution
        type_distribution = base_query.with_entities(
            ItemMaster.identifier_type,
            func.count(ItemMaster.id).label('count')
        ).group_by(ItemMaster.identifier_type).all()
        
        type_labels = []
        type_values = []
        
        for inv_type, count in type_distribution:
            type_labels.append(inv_type or 'Unknown')
            type_values.append(count)
        
        return jsonify({
            'success': True,
            'data': {
                'status_distribution': {
                    'labels': status_labels,
                    'values': status_values
                },
                'store_distribution': store_data,
                'type_distribution': {
                    'labels': type_labels,
                    'values': type_values
                },
                'totals': {
                    'total_items': total_items,
                    'unique_stores': len(store_data) if store_data else 1,
                    'unique_types': len(type_labels)
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching inventory distribution: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'status_distribution': {'labels': [], 'values': []},
                'store_distribution': [],
                'type_distribution': {'labels': [], 'values': []},
                'totals': {'total_items': 0, 'unique_stores': 0, 'unique_types': 0}
            }
        }), 500

@enhanced_analytics_bp.route('/dashboard/financial-metrics')
def get_financial_metrics():
    """Get enhanced financial metrics with POS integration"""
    try:
        store_filter = request.args.get('store', 'all')
        
        # Build base query
        base_query = db.session.query(ItemMaster)
        if store_filter != 'all':
            base_query = base_query.filter(
                or_(ItemMaster.home_store == store_filter,
                    ItemMaster.current_store == store_filter)
            )
        
        # Get financial metrics from POS data
        financial_metrics = base_query.with_entities(
            func.sum(ItemMaster.sell_price).label('total_inventory_value'),
            func.avg(ItemMaster.sell_price).label('avg_sell_price'),
            func.count(ItemMaster.sell_price).label('items_with_price'),
            func.sum(
                func.case(
                    [(ItemMaster.sell_price >= 1000, ItemMaster.sell_price)],
                    else_=0
                )
            ).label('high_value_inventory')
        ).filter(
            ItemMaster.sell_price.isnot(None)
        ).first()
        
        # Calculate repair costs
        repair_cost_query = base_query.filter(
            ItemMaster.status.in_(['Repair', 'Needs to be Inspected'])
        ).with_entities(
            func.sum(ItemMaster.sell_price).label('repair_inventory_value')
        ).first()
        
        # Format financial data
        total_inventory_value = float(financial_metrics.total_inventory_value or 0)
        avg_sell_price = float(financial_metrics.avg_sell_price or 0)
        items_with_price = int(financial_metrics.items_with_price or 0)
        high_value_inventory = float(financial_metrics.high_value_inventory or 0)
        repair_inventory_value = float(repair_cost_query.repair_inventory_value or 0)
        
        # Calculate derived metrics
        high_value_items = base_query.filter(
            ItemMaster.sell_price >= 1000
        ).count() if total_inventory_value > 0 else 0
        
        # Get manufacturer insights
        manufacturer_data = base_query.with_entities(
            ItemMaster.manufacturer,
            func.count(ItemMaster.id).label('item_count'),
            func.sum(ItemMaster.sell_price).label('total_value')
        ).filter(
            ItemMaster.manufacturer.isnot(None)
        ).group_by(
            ItemMaster.manufacturer
        ).order_by(
            func.count(ItemMaster.id).desc()
        ).limit(10).all()
        
        top_manufacturers = []
        for mfg in manufacturer_data:
            top_manufacturers.append({
                'name': mfg.manufacturer,
                'item_count': mfg.item_count,
                'total_value': float(mfg.total_value or 0),
                'avg_value': float(mfg.total_value or 0) / max(mfg.item_count, 1)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'financial_insights': {
                    'total_inventory_value': total_inventory_value,
                    'avg_sell_price': avg_sell_price,
                    'items_with_data': items_with_price,
                    'high_value_items': high_value_items,
                    'high_value_inventory': high_value_inventory,
                    'total_repair_costs': repair_inventory_value,
                    'total_turnover_ytd': 0  # Would need transaction history
                },
                'manufacturer_insights': {
                    'top_manufacturers': top_manufacturers
                },
                'coverage_metrics': {
                    'data_completeness': (items_with_price / max(base_query.count(), 1)) * 100,
                    'high_value_percentage': (high_value_items / max(base_query.count(), 1)) * 100
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching financial metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'financial_insights': {
                    'total_inventory_value': 0,
                    'avg_sell_price': 0,
                    'items_with_data': 0,
                    'high_value_items': 0,
                    'total_repair_costs': 0,
                    'total_turnover_ytd': 0
                },
                'manufacturer_insights': {'top_manufacturers': []},
                'coverage_metrics': {'data_completeness': 0, 'high_value_percentage': 0}
            }
        }), 500

@enhanced_analytics_bp.route('/dashboard/utilization-analysis')
def get_utilization_analysis():
    """Get detailed utilization analysis with accurate calculations"""
    try:
        store_filter = request.args.get('store', 'all')
        days = int(request.args.get('days', 30))
        
        # Build base query
        base_query = db.session.query(ItemMaster)
        if store_filter != 'all':
            base_query = base_query.filter(
                or_(ItemMaster.home_store == store_filter,
                    ItemMaster.current_store == store_filter)
            )
        
        # Calculate utilization by category
        utilization_by_category = base_query.with_entities(
            ItemMaster.category,
            func.count(
                func.case(
                    [(ItemMaster.status.in_(['On Rent', 'Delivered']), ItemMaster.id)]
                )
            ).label('on_rent_count'),
            func.count(ItemMaster.id).label('total_count')
        ).group_by(
            ItemMaster.category
        ).all()
        
        category_utilization = []
        for category in utilization_by_category:
            if category.total_count > 0:
                utilization_rate = (category.on_rent_count / category.total_count) * 100
                category_utilization.append({
                    'category': category.category or 'Uncategorized',
                    'utilization_rate': round(utilization_rate, 2),
                    'on_rent': category.on_rent_count,
                    'total': category.total_count
                })
        
        # Sort by utilization rate
        category_utilization.sort(key=lambda x: x['utilization_rate'], reverse=True)
        
        # Calculate overall utilization
        total_items = base_query.count()
        items_on_rent = base_query.filter(
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).count()
        
        overall_utilization = 0
        if total_items > 0:
            overall_utilization = (items_on_rent / total_items) * 100
        
        return jsonify({
            'success': True,
            'data': {
                'overall_utilization': round(overall_utilization, 2),
                'category_utilization': category_utilization,
                'summary': {
                    'total_items': total_items,
                    'items_on_rent': items_on_rent,
                    'items_available': total_items - items_on_rent,
                    'high_utilization_categories': len([c for c in category_utilization if c['utilization_rate'] >= 80]),
                    'low_utilization_categories': len([c for c in category_utilization if c['utilization_rate'] <= 40])
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching utilization analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'overall_utilization': 0,
                'category_utilization': [],
                'summary': {
                    'total_items': 0,
                    'items_on_rent': 0,
                    'items_available': 0,
                    'high_utilization_categories': 0,
                    'low_utilization_categories': 0
                }
            }
        }), 500

def get_store_name(store_code):
    """Helper function to get readable store names"""
    store_names = {
        '6800': 'Brooklyn Park',
        '3607': 'Wayzata',
        '8101': 'Fridley', 
        '728': 'Elk River',
        '000': 'Legacy/Unassigned'
    }
    return store_names.get(store_code, store_code or 'Unknown')

# Error handler for the blueprint
@enhanced_analytics_bp.errorhandler(Exception)
def handle_analytics_error(error):
    logger.error(f"Enhanced analytics error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error in analytics API',
        'details': str(error)
    }), 500