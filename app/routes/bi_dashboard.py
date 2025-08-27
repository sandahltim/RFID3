"""
Business Intelligence Dashboard Routes
Provides executive dashboards and analytics views
"""

from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime, date, timedelta
import json
import io
import csv
from sqlalchemy import text
from app import db
from app.services.bi_analytics import BIAnalyticsService
from app.services.logger import setup_logger

logger = setup_logger(__name__)
bi_bp = Blueprint('bi', __name__, url_prefix='/bi')
bi_service = BIAnalyticsService()

@bi_bp.route('/dashboard')
def executive_dashboard():
    """Main executive dashboard view"""
    try:
        # Get date range from query params
        end_date = request.args.get('end_date', date.today().isoformat())
        weeks = int(request.args.get('weeks', 12))
        
        # Fetch executive KPIs
        kpis = _get_executive_kpis(end_date, weeks)
        
        # Fetch store performance comparison
        store_comparison = _get_store_comparison(end_date)
        
        # Fetch alerts
        alerts = bi_service.check_alert_conditions()
        
        # Fetch predictions
        predictions = _get_predictions()
        
        return render_template('bi_dashboard.html',
                             kpis=kpis,
                             store_comparison=store_comparison,
                             alerts=alerts,
                             predictions=predictions,
                             end_date=end_date,
                             weeks=weeks)
    except Exception as e:
        logger.error(f"Error loading executive dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/api/kpis')
def api_executive_kpis():
    """API endpoint for executive KPIs"""
    try:
        end_date = request.args.get('end_date', date.today().isoformat())
        weeks = int(request.args.get('weeks', 12))
        
        kpis = _get_executive_kpis(end_date, weeks)
        return jsonify(kpis)
        
    except Exception as e:
        logger.error(f"Error fetching KPIs: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/api/store-performance')
def api_store_performance():
    """API endpoint for store performance metrics"""
    try:
        store_code = request.args.get('store')
        end_date = request.args.get('end_date', date.today().isoformat())
        periods = int(request.args.get('periods', 26))
        
        query = """
            SELECT 
                sp.period_ending,
                sp.store_code,
                sp.total_revenue,
                sp.rental_revenue,
                sp.labor_cost_ratio,
                sp.revenue_per_hour,
                sp.avg_wage_rate,
                sp.revenue_growth_pct,
                os.new_contracts_count,
                os.reservation_pipeline_total,
                os.ar_over_45_days_pct
            FROM bi_store_performance sp
            LEFT JOIN bi_operational_scorecard os 
                ON sp.store_code = os.store_code 
                AND sp.period_ending = os.week_ending
            WHERE sp.period_ending <= :end_date
            {store_filter}
            ORDER BY sp.period_ending DESC
            LIMIT :periods
        """
        
        store_filter = "AND sp.store_code = :store_code" if store_code else ""
        query = query.format(store_filter=store_filter)
        
        params = {'end_date': end_date, 'periods': periods}
        if store_code:
            params['store_code'] = store_code
            
        results = db.session.execute(text(query), params).fetchall()
        
        data = []
        for row in results:
            data.append({
                'period_ending': row.period_ending.isoformat(),
                'store_code': row.store_code,
                'total_revenue': float(row.total_revenue) if row.total_revenue else 0,
                'rental_revenue': float(row.rental_revenue) if row.rental_revenue else 0,
                'labor_cost_ratio': float(row.labor_cost_ratio) if row.labor_cost_ratio else 0,
                'revenue_per_hour': float(row.revenue_per_hour) if row.revenue_per_hour else 0,
                'avg_wage_rate': float(row.avg_wage_rate) if row.avg_wage_rate else 0,
                'revenue_growth_pct': float(row.revenue_growth_pct) if row.revenue_growth_pct else 0,
                'new_contracts': row.new_contracts_count or 0,
                'pipeline': float(row.reservation_pipeline_total) if row.reservation_pipeline_total else 0,
                'ar_aging': float(row.ar_over_45_days_pct) if row.ar_over_45_days_pct else 0
            })
            
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error fetching store performance: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/api/inventory-analytics')
def api_inventory_analytics():
    """API endpoint for inventory performance analytics"""
    try:
        store_code = request.args.get('store')
        rental_class = request.args.get('class')
        end_date = request.args.get('end_date', date.today().isoformat())
        
        query = """
            SELECT 
                ip.*,
                rc.common_name
            FROM bi_inventory_performance ip
            LEFT JOIN seed_rental_classes rc ON ip.rental_class = rc.rental_class_num
            WHERE ip.period_ending = (
                SELECT MAX(period_ending) 
                FROM bi_inventory_performance 
                WHERE period_ending <= :end_date
            )
            {filters}
            ORDER BY ip.utilization_rate DESC, ip.roi_percentage DESC
        """
        
        filters = []
        params = {'end_date': end_date}
        
        if store_code:
            filters.append("AND ip.store_code = :store_code")
            params['store_code'] = store_code
            
        if rental_class:
            filters.append("AND ip.rental_class = :rental_class")
            params['rental_class'] = rental_class
            
        query = query.format(filters=' '.join(filters))
        results = db.session.execute(text(query), params).fetchall()
        
        data = []
        for row in results:
            data.append({
                'store_code': row.store_code,
                'rental_class': row.rental_class,
                'class_name': row.common_name or row.rental_class,
                'total_units': row.total_units,
                'available_units': row.available_units,
                'on_rent_units': row.on_rent_units,
                'utilization_rate': float(row.utilization_rate) if row.utilization_rate else 0,
                'turnover_rate': float(row.turnover_rate) if row.turnover_rate else 0,
                'inventory_value': float(row.inventory_value) if row.inventory_value else 0,
                'roi_percentage': float(row.roi_percentage) if row.roi_percentage else 0,
                'revenue_per_unit': float(row.revenue_per_unit) if row.revenue_per_unit else 0
            })
            
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error fetching inventory analytics: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/api/labor-analytics')
def api_labor_analytics():
    """API endpoint for labor efficiency analytics"""
    try:
        store_code = request.args.get('store')
        end_date = request.args.get('end_date', date.today().isoformat())
        periods = int(request.args.get('periods', 26))
        
        query = """
            SELECT 
                period_ending,
                store_code,
                wage_hours,
                payroll_cost,
                avg_wage_rate,
                labor_cost_ratio,
                revenue_per_hour,
                total_revenue,
                (total_revenue - payroll_cost) as contribution_margin
            FROM bi_store_performance
            WHERE period_ending <= :end_date
            {store_filter}
            ORDER BY period_ending DESC
            LIMIT :periods
        """
        
        store_filter = "AND store_code = :store_code" if store_code else ""
        query = query.format(store_filter=store_filter)
        
        params = {'end_date': end_date, 'periods': periods}
        if store_code:
            params['store_code'] = store_code
            
        results = db.session.execute(text(query), params).fetchall()
        
        data = []
        for row in results:
            data.append({
                'period': row.period_ending.isoformat(),
                'store': row.store_code,
                'hours': float(row.wage_hours) if row.wage_hours else 0,
                'payroll': float(row.payroll_cost) if row.payroll_cost else 0,
                'wage_rate': float(row.avg_wage_rate) if row.avg_wage_rate else 0,
                'labor_ratio': float(row.labor_cost_ratio) if row.labor_cost_ratio else 0,
                'revenue_per_hour': float(row.revenue_per_hour) if row.revenue_per_hour else 0,
                'contribution': float(row.contribution_margin) if row.contribution_margin else 0
            })
            
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error fetching labor analytics: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/api/predictions')
def api_predictions():
    """API endpoint for predictive analytics"""
    try:
        metric = request.args.get('metric', 'total_revenue')
        store_code = request.args.get('store')
        horizon = int(request.args.get('horizon', 4))  # weeks ahead
        
        query = """
            SELECT 
                target_date,
                store_code,
                metric_name,
                predicted_value,
                confidence_low,
                confidence_high,
                confidence_level,
                actual_value,
                variance_pct
            FROM bi_predictive_analytics
            WHERE metric_name = :metric
            AND target_date BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL :horizon WEEK)
            {store_filter}
            ORDER BY target_date
        """
        
        store_filter = "AND store_code = :store_code" if store_code else "AND store_code IS NULL"
        query = query.format(store_filter=store_filter)
        
        params = {'metric': metric, 'horizon': horizon}
        if store_code:
            params['store_code'] = store_code
            
        results = db.session.execute(text(query), params).fetchall()
        
        data = []
        for row in results:
            data.append({
                'date': row.target_date.isoformat(),
                'store': row.store_code,
                'metric': row.metric_name,
                'prediction': float(row.predicted_value) if row.predicted_value else 0,
                'confidence_low': float(row.confidence_low) if row.confidence_low else 0,
                'confidence_high': float(row.confidence_high) if row.confidence_high else 0,
                'confidence': float(row.confidence_level) if row.confidence_level else 0,
                'actual': float(row.actual_value) if row.actual_value else None,
                'variance': float(row.variance_pct) if row.variance_pct else None
            })
            
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error fetching predictions: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/import/payroll', methods=['POST'])
def import_payroll():
    """Import payroll data from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Save temporary file
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)
        
        # Import data
        stats = bi_service.import_payroll_data(temp_path)
        
        # Calculate KPIs for imported periods
        if stats['records_imported'] > 0:
            _recalculate_kpis()
            
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error importing payroll data: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/import/scorecard', methods=['POST'])
def import_scorecard():
    """Import scorecard data from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Save temporary file
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)
        
        # Import data
        stats = bi_service.import_scorecard_data(temp_path)
        
        # Calculate KPIs for imported periods
        if stats['records_imported'] > 0:
            _recalculate_kpis()
            
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error importing scorecard data: {e}")
        return jsonify({'error': str(e)}), 500

@bi_bp.route('/export/executive-report')
def export_executive_report():
    """Export executive report as CSV"""
    try:
        end_date = request.args.get('end_date', date.today().isoformat())
        weeks = int(request.args.get('weeks', 52))
        
        # Fetch data
        query = """
            SELECT 
                e.period_ending,
                e.total_revenue,
                e.revenue_growth_pct,
                e.gross_margin_pct,
                e.labor_cost_ratio,
                e.inventory_turnover,
                e.best_performing_store
            FROM bi_executive_kpis e
            WHERE e.period_type = 'WEEKLY'
            AND e.period_ending <= :end_date
            ORDER BY e.period_ending DESC
            LIMIT :weeks
        """
        
        results = db.session.execute(text(query), {
            'end_date': end_date,
            'weeks': weeks
        }).fetchall()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Period Ending', 'Total Revenue', 'Revenue Growth %',
            'Gross Margin %', 'Labor Cost Ratio', 'Inventory Turnover',
            'Best Performing Store'
        ])
        
        # Data rows
        for row in results:
            writer.writerow([
                row.period_ending,
                f"${row.total_revenue:,.2f}" if row.total_revenue else '',
                f"{row.revenue_growth_pct:.1f}%" if row.revenue_growth_pct else '',
                f"{row.gross_margin_pct:.1f}%" if row.gross_margin_pct else '',
                f"{row.labor_cost_ratio:.1f}%" if row.labor_cost_ratio else '',
                f"{row.inventory_turnover:.2f}" if row.inventory_turnover else '',
                row.best_performing_store or ''
            ])
        
        # Return CSV file
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'executive_report_{end_date}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting executive report: {e}")
        return jsonify({'error': str(e)}), 500

# Helper functions
def _get_executive_kpis(end_date: str, weeks: int) -> dict:
    """Fetch executive KPIs for dashboard"""
    query = """
        SELECT 
            e.*,
            LAG(e.total_revenue) OVER (ORDER BY e.period_ending) as prev_revenue
        FROM bi_executive_kpis e
        WHERE e.period_type = 'WEEKLY'
        AND e.period_ending <= :end_date
        ORDER BY e.period_ending DESC
        LIMIT :weeks
    """
    
    results = db.session.execute(text(query), {
        'end_date': end_date,
        'weeks': weeks
    }).fetchall()
    
    if not results:
        return {}
    
    latest = results[0]
    
    # Calculate trends
    revenues = [float(r.total_revenue) for r in results if r.total_revenue]
    margins = [float(r.gross_margin_pct) for r in results if r.gross_margin_pct]
    
    return {
        'current': {
            'revenue': float(latest.total_revenue) if latest.total_revenue else 0,
            'growth': float(latest.revenue_growth_pct) if latest.revenue_growth_pct else 0,
            'margin': float(latest.gross_margin_pct) if latest.gross_margin_pct else 0,
            'labor_ratio': float(latest.labor_cost_ratio) if latest.labor_cost_ratio else 0,
            'turnover': float(latest.inventory_turnover) if latest.inventory_turnover else 0
        },
        'trends': {
            'revenue': revenues[:12] if revenues else [],
            'margins': margins[:12] if margins else []
        },
        'period': latest.period_ending.isoformat()
    }

def _get_store_comparison(end_date: str) -> list:
    """Get store performance comparison"""
    query = """
        SELECT 
            sp.store_code,
            sp.total_revenue,
            sp.revenue_growth_pct,
            sp.labor_cost_ratio,
            sp.revenue_per_hour,
            os.new_contracts_count,
            os.ar_over_45_days_pct
        FROM bi_store_performance sp
        LEFT JOIN bi_operational_scorecard os 
            ON sp.store_code = os.store_code 
            AND sp.period_ending = os.week_ending
        WHERE sp.period_ending = (
            SELECT MAX(period_ending) 
            FROM bi_store_performance 
            WHERE period_ending <= :end_date
        )
        ORDER BY sp.total_revenue DESC
    """
    
    results = db.session.execute(text(query), {'end_date': end_date}).fetchall()
    
    comparison = []
    for row in results:
        comparison.append({
            'store': row.store_code,
            'revenue': float(row.total_revenue) if row.total_revenue else 0,
            'growth': float(row.revenue_growth_pct) if row.revenue_growth_pct else 0,
            'labor_ratio': float(row.labor_cost_ratio) if row.labor_cost_ratio else 0,
            'efficiency': float(row.revenue_per_hour) if row.revenue_per_hour else 0,
            'contracts': row.new_contracts_count or 0,
            'ar_aging': float(row.ar_over_45_days_pct) if row.ar_over_45_days_pct else 0
        })
    
    return comparison

def _get_predictions() -> list:
    """Get latest predictions for dashboard"""
    query = """
        SELECT 
            target_date,
            metric_name,
            predicted_value,
            confidence_level
        FROM bi_predictive_analytics
        WHERE target_date BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL 4 WEEK)
        AND store_code IS NULL
        ORDER BY target_date, metric_name
    """
    
    results = db.session.execute(text(query)).fetchall()
    
    predictions = []
    for row in results:
        predictions.append({
            'date': row.target_date.isoformat(),
            'metric': row.metric_name,
            'value': float(row.predicted_value) if row.predicted_value else 0,
            'confidence': float(row.confidence_level) if row.confidence_level else 0
        })
    
    return predictions

def _recalculate_kpis():
    """Recalculate executive KPIs after data import"""
    try:
        # Get distinct periods that need KPI calculation
        query = """
            SELECT DISTINCT period_ending 
            FROM bi_store_performance 
            WHERE period_ending NOT IN (
                SELECT period_ending FROM bi_executive_kpis
            )
            ORDER BY period_ending
        """
        
        periods = db.session.execute(text(query)).fetchall()
        
        for period in periods:
            bi_service.calculate_executive_kpis(period[0], 'BIWEEKLY')
            bi_service.calculate_inventory_metrics(period[0])
            
        # Generate predictions for next 4 weeks
        for weeks_ahead in [1, 2, 3, 4]:
            target_date = date.today() + timedelta(weeks=weeks_ahead)
            bi_service.generate_predictions(target_date)
            
    except Exception as e:
        logger.error(f"Error recalculating KPIs: {e}")
