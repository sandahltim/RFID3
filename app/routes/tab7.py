# app/routes/tab7.py
# Executive Dashboard - Version: 2025-08-27-v1
from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import (
    PayrollTrends, ScorecardTrends, ExecutiveKPI, ItemMaster
)
from ..services.logger import get_logger
from sqlalchemy import func, desc, and_, or_, text, case
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, date
import json
from decimal import Decimal

logger = get_logger(__name__)

tab7_bp = Blueprint('tab7', __name__)

# Version marker
logger.info("Deployed tab7.py (Executive Dashboard) version: 2025-08-27-v1 at %s", 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Import centralized store configuration
from ..config.stores import STORE_MAPPING, get_store_name

@tab7_bp.route('/tab/7')
def tab7_view():
    """Main Executive Dashboard page."""
    logger.info("Loading Executive Dashboard at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return render_template('tab7.html', store_mapping=STORE_MAPPING)

@tab7_bp.route('/api/executive/dashboard_summary', methods=['GET'])
def get_executive_summary():
    """Get high-level executive metrics with store filtering."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get('store', 'all')
        period = request.args.get('period', '4weeks')  # 4weeks, 12weeks, 52weeks, ytd
        
        logger.info(f"Fetching executive summary: store={store_filter}, period={period}")
        
        # Calculate date range based on period
        end_date = datetime.now().date()
        if period == '4weeks':
            start_date = end_date - timedelta(weeks=4)
        elif period == '12weeks':
            start_date = end_date - timedelta(weeks=12)
        elif period == '52weeks':
            start_date = end_date - timedelta(weeks=52)
        else:  # YTD
            start_date = date(end_date.year, 1, 1)
        
        # Build base query for payroll trends
        payroll_query = session.query(
            func.sum(PayrollTrends.total_revenue).label('total_revenue'),
            func.sum(PayrollTrends.rental_revenue).label('rental_revenue'),
            func.sum(PayrollTrends.payroll_cost).label('total_payroll'),
            func.sum(PayrollTrends.wage_hours).label('total_hours'),
            func.avg(PayrollTrends.labor_efficiency_ratio).label('avg_labor_ratio'),
            func.avg(PayrollTrends.revenue_per_hour).label('avg_revenue_per_hour')
        ).filter(PayrollTrends.week_ending.between(start_date, end_date))
        
        if store_filter != 'all':
            payroll_query = payroll_query.filter(PayrollTrends.store_id == store_filter)
        
        payroll_metrics = payroll_query.first()
        
        # Get scorecard metrics
        scorecard_query = session.query(
            func.avg(ScorecardTrends.new_contracts_count).label('avg_new_contracts'),
            func.sum(ScorecardTrends.new_contracts_count).label('total_new_contracts'),
            func.avg(ScorecardTrends.deliveries_scheduled_next_7_days).label('avg_deliveries'),
            func.avg(ScorecardTrends.ar_over_45_days_percent).label('avg_ar_aging'),
            func.sum(ScorecardTrends.total_discount_amount).label('total_discounts')
        ).filter(ScorecardTrends.week_ending.between(start_date, end_date))
        
        if store_filter != 'all':
            scorecard_query = scorecard_query.filter(ScorecardTrends.store_id == store_filter)
        
        scorecard_metrics = scorecard_query.first()
        
        # Calculate YoY growth if we have data from last year
        last_year_start = start_date.replace(year=start_date.year - 1)
        last_year_end = end_date.replace(year=end_date.year - 1)
        
        last_year_revenue = session.query(
            func.sum(PayrollTrends.total_revenue)
        ).filter(
            PayrollTrends.week_ending.between(last_year_start, last_year_end)
        ).scalar() or 0
        
        current_revenue = float(payroll_metrics.total_revenue or 0)
        yoy_growth = ((current_revenue - float(last_year_revenue)) / float(last_year_revenue) * 100) if last_year_revenue else 0
        
        # Get current inventory value (from existing ItemMaster)
        inventory_query = session.query(
            func.sum(ItemMaster.retail_price).label('total_inventory_value'),
            func.count(ItemMaster.tag_id).label('total_items')
        )
        
        if store_filter != 'all':
            inventory_query = inventory_query.filter(
                or_(ItemMaster.home_store == store_filter,
                    ItemMaster.current_store == store_filter)
            )
        
        inventory_metrics = inventory_query.first()
        
        summary = {
            'financial_metrics': {
                'total_revenue': float(payroll_metrics.total_revenue or 0),
                'rental_revenue': float(payroll_metrics.rental_revenue or 0),
                'total_payroll': float(payroll_metrics.total_payroll or 0),
                'labor_efficiency': float(payroll_metrics.avg_labor_ratio or 0),
                'revenue_per_hour': float(payroll_metrics.avg_revenue_per_hour or 0),
                'yoy_growth': round(yoy_growth, 2)
            },
            'operational_metrics': {
                'new_contracts': int(scorecard_metrics.total_new_contracts or 0),
                'avg_weekly_contracts': float(scorecard_metrics.avg_new_contracts or 0),
                'avg_deliveries': float(scorecard_metrics.avg_deliveries or 0),
                'inventory_value': float(inventory_metrics.total_inventory_value or 0),
                'total_items': int(inventory_metrics.total_items or 0)
            },
            'health_indicators': {
                'ar_aging_percent': float(scorecard_metrics.avg_ar_aging or 0),
                'total_discounts': float(scorecard_metrics.total_discounts or 0),
                'profit_margin': round((float(current_revenue) - float(payroll_metrics.total_payroll or 0)) / float(current_revenue) * 100, 2) if current_revenue else 0
            },
            'metadata': {
                'store': store_filter,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"Executive summary calculated: Revenue: ${summary['financial_metrics']['total_revenue']:,.2f}")
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error fetching executive summary: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab7_bp.route('/api/executive/payroll_trends', methods=['GET'])
def get_payroll_trends():
    """Get detailed payroll trends for charting."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get('store', 'all')
        weeks = int(request.args.get('weeks', 52))
        
        # Get weekly data
        query = session.query(
            PayrollTrends.week_ending,
            PayrollTrends.store_id,
            PayrollTrends.total_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.labor_efficiency_ratio
        ).order_by(desc(PayrollTrends.week_ending)).limit(weeks * 4)  # 4 stores
        
        if store_filter != 'all':
            query = query.filter(PayrollTrends.store_id == store_filter)
        
        results = query.all()
        
        # Format data for charts
        trend_data = []
        for row in results:
            trend_data.append({
                'week': row.week_ending.isoformat(),
                'store': STORE_MAPPING.get(row.store_id, row.store_id),
                'revenue': float(row.total_revenue) if row.total_revenue else 0,
                'payroll': float(row.payroll_cost) if row.payroll_cost else 0,
                'efficiency': float(row.labor_efficiency_ratio) if row.labor_efficiency_ratio else 0
            })
        
        return jsonify({'trends': trend_data})
        
    except Exception as e:
        logger.error(f"Error fetching payroll trends: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab7_bp.route('/api/executive/store_comparison', methods=['GET'])
def get_store_comparison():
    """Get comparative metrics across all stores."""
    session = None
    try:
        session = db.session()
        period_weeks = int(request.args.get('weeks', 4))
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=period_weeks)
        
        # Get aggregated metrics by store
        store_metrics = session.query(
            PayrollTrends.store_id,
            func.sum(PayrollTrends.total_revenue).label('revenue'),
            func.sum(PayrollTrends.payroll_cost).label('payroll'),
            func.avg(PayrollTrends.labor_efficiency_ratio).label('efficiency'),
            func.sum(PayrollTrends.wage_hours).label('hours')
        ).filter(
            PayrollTrends.week_ending.between(start_date, end_date)
        ).group_by(PayrollTrends.store_id).all()
        
        comparison_data = []
        for store in store_metrics:
            # Calculate profitability
            profit = (float(store.revenue or 0) - float(store.payroll or 0))
            profit_margin = (profit / float(store.revenue) * 100) if store.revenue else 0
            
            comparison_data.append({
                'store_id': store.store_id,
                'store_name': STORE_MAPPING.get(store.store_id, store.store_id),
                'revenue': float(store.revenue or 0),
                'payroll': float(store.payroll or 0),
                'profit': profit,
                'profit_margin': round(profit_margin, 2),
                'efficiency': float(store.efficiency or 0),
                'total_hours': float(store.hours or 0),
                'revenue_per_hour': float(store.revenue / store.hours) if store.hours else 0
            })
        
        # Sort by revenue descending
        comparison_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Add ranking
        for i, store in enumerate(comparison_data, 1):
            store['rank'] = i
        
        return jsonify({'stores': comparison_data})
        
    except Exception as e:
        logger.error(f"Error fetching store comparison: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab7_bp.route('/api/executive/kpi_dashboard', methods=['GET'])
def get_kpi_dashboard():
    """Get executive KPIs with targets and variances."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get('store', 'all')
        
        # Get KPIs from database
        query = session.query(ExecutiveKPI)
        
        if store_filter != 'all':
            query = query.filter(
                or_(ExecutiveKPI.store_id == store_filter,
                    ExecutiveKPI.store_id.is_(None))  # Include company-wide KPIs
            )
        else:
            query = query.filter(ExecutiveKPI.store_id.is_(None))  # Only company-wide
        
        kpis = query.all()
        
        # Group KPIs by category
        kpi_data = {
            'financial': [],
            'operational': [],
            'efficiency': [],
            'growth': []
        }
        
        for kpi in kpis:
            category = kpi.kpi_category or 'operational'
            if category in kpi_data:
                kpi_data[category].append({
                    'name': kpi.kpi_name,
                    'current': float(kpi.current_value) if kpi.current_value else 0,
                    'target': float(kpi.target_value) if kpi.target_value else 0,
                    'variance': float(kpi.variance_percent) if kpi.variance_percent else 0,
                    'trend': kpi.trend_direction,
                    'period': kpi.period
                })
        
        return jsonify(kpi_data)
        
    except Exception as e:
        logger.error(f"Error fetching KPI dashboard: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

# Data loading endpoint for CSV import
@tab7_bp.route('/api/executive/load_historical_data', methods=['POST'])
def load_historical_data():
    """Load historical payroll and scorecard data from CSV files."""
    # This would be called once to populate the database
    # Implementation would parse the CSV files and insert into PayrollTrends and ScorecardTrends
    return jsonify({'status': 'not_implemented', 'message': 'Use data_loader.py script'})
