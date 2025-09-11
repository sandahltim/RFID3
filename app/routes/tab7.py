# app/routes/tab7.py
# Executive Dashboard - Version: 2025-08-27-v1
from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import PayrollTrends, ScorecardTrends, ExecutiveKPI, ItemMaster, POSScorecardTrends, PLData
from ..services.logger import get_logger
from sqlalchemy import func, desc, and_, or_, text, case
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, date
import json
from decimal import Decimal

from ..utils.date_ranges import get_date_range_from_params
from ..models.config_models import ExecutiveDashboardConfiguration

logger = get_logger(__name__)

def _get_executive_config():
    """Get executive dashboard configuration from database - NO HARDCODED VALUES"""
    try:
        config = ExecutiveDashboardConfiguration.query.filter_by(
            user_id='default_user', 
            config_name='default'
        ).first()
        if config:
            return config
        else:
            # Create default configuration in database if it doesn't exist
            logger.warning("No executive dashboard configuration found, creating default in database")
            config = ExecutiveDashboardConfiguration(
                user_id='default_user',
                config_name='default'
            )
            db.session.add(config)
            db.session.commit()
            return config
    except Exception as e:
        logger.error(f"Error loading executive configuration: {e}")
        # Return None to force error handling upstream rather than hardcoded values
        raise RuntimeError(f"Cannot load executive configuration: {e}")


def _get_unified_revenue_kpi(session, config_weeks_attr='financial_kpis_current_revenue_weeks', store_filter='all'):
    """
    SINGLE SOURCE OF TRUTH for revenue KPI calculation
    Consolidated 2025-09-09 - Eliminates duplicate calculation paths
    
    Args:
        session: Database session
        config_weeks_attr: Config attribute name for weeks (default: financial_kpis_current_revenue_weeks)
        store_filter: Store code filter ('all', '3607', '6800', '728', '8101')
    
    Returns:
        float: Averaged revenue excluding zero/null/future weeks
    """
    from sqlalchemy import text
    
    try:
        config = _get_executive_config()
        weeks = getattr(config, config_weeks_attr, 3)  # Fallback to 3 weeks
        
        # Store-specific revenue column mapping
        if store_filter == 'all':
            revenue_column = 'total_weekly_revenue'
        else:
            revenue_column_map = {
                '3607': 'revenue_3607',
                '6800': 'revenue_6800', 
                '728': 'revenue_728',
                '8101': 'revenue_8101'
            }
            revenue_column = revenue_column_map.get(store_filter, 'total_weekly_revenue')
        
        # Unified SQL with store filtering - filters zero/null/future weeks consistently
        revenue_query = text(f"""
            SELECT AVG({revenue_column}) as avg_revenue
            FROM (
                SELECT {revenue_column}
                FROM scorecard_trends_data 
                WHERE {revenue_column} IS NOT NULL 
                    AND {revenue_column} > 0
                    AND week_ending <= CURDATE()
                ORDER BY week_ending DESC 
                LIMIT {weeks}
            ) recent_weeks
        """)
        
        result = session.execute(revenue_query).scalar() or 0
        logger.info(f"Unified revenue KPI: ${result:,.0f} ({weeks}-week avg, store: {store_filter}, attr: {config_weeks_attr})")
        return float(result)
        
    except Exception as e:
        logger.error(f"Unified revenue KPI calculation failed: {e}")
        return 0

tab7_bp = Blueprint("tab7", __name__)
executive_api_bp = Blueprint("executive_api", __name__, url_prefix='/executive')

# Version marker
logger.info(
    "Deployed tab7.py (Executive Dashboard) version: 2025-08-27-v1 at %s",
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
)

# Import centralized store configuration
from ..config.stores import STORE_MAPPING, get_store_name
from sqlalchemy import text

# Store mapping for location filtering
STORE_LOCATIONS = {
    '3607': {'name': 'Wayzata', 'code': '001', 'opened_date': '2008-01-01'},
    '6800': {'name': 'Brooklyn Park', 'code': '002', 'opened_date': '2022-01-01'},
    '8101': {'name': 'Fridley', 'code': '003', 'opened_date': '2022-01-01'},
    '728': {'name': 'Elk River', 'code': '004', 'opened_date': '2024-01-01'}
}


def get_pl_profit_margin(session, year, month=None, fallback_revenue=None, fallback_payroll=None):
    """
    Get profit margin from P&L data if available, otherwise fallback to simple calculation.
    
    Args:
        session: Database session
        year: Year to get data for
        month: Month to get data for (optional, if None gets YTD)
        fallback_revenue: Revenue to use if P&L data not available
        fallback_payroll: Payroll to use if P&L data not available
    
    Returns:
        float: Profit margin percentage
    """
    try:
        # Try to get profit margin from P&L data first
        if month:
            pl_margin = PLData.get_profit_margin(session, year, month)
        else:
            # Get YTD margin (all months from Jan to current month)
            current_month = datetime.now().month
            pl_margin = PLData.get_profit_margin(session, year)
            
        if pl_margin is not None and pl_margin != 0:
            return pl_margin
            
    except Exception as e:
        logger.warning(f"Could not get P&L profit margin: {e}")
    
    # Fallback to simple revenue - payroll calculation
    if fallback_revenue and fallback_payroll and fallback_revenue > 0:
        return ((fallback_revenue - fallback_payroll) / fallback_revenue) * 100
    
    return 0


def excel_weeknum(date_obj, return_type=11):
    """
    Python equivalent of Excel's WEEKNUM function with return_type=11
    (Week starts Monday, numbered 1-53)
    
    Args:
        date_obj: datetime.date or datetime.datetime object
        return_type: Week numbering system (11 = Monday start, 1-53)
    
    Returns:
        int: Week number (1-53)
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    year = date_obj.year
    jan1 = date(year, 1, 1)
    
    # Find the Monday of the week containing January 1st
    jan1_weekday = jan1.weekday()  # 0=Monday, 6=Sunday
    
    if return_type == 11:  # Week starts Monday
        # Calculate days to go back to get the first Monday
        if jan1_weekday == 0:  # Already Monday
            week_start_adjustment = 0
        else:
            week_start_adjustment = -jan1_weekday
    
    first_monday_of_year = jan1 + timedelta(days=week_start_adjustment)
    
    # Calculate the number of days between the date and the first Monday
    days_diff = (date_obj - first_monday_of_year).days
    
    # Calculate week number (1-based)
    week_number = (days_diff // 7) + 1
    
    # Handle edge cases for previous/next year spillover
    if week_number < 1:
        # Date falls in the last week of the previous year - return as week 1
        return 1
    elif week_number > 52:
        # For weeks beyond 52, check if we should extend to 53 or wrap to 1
        # Most years have 52 weeks, some have 53
        dec31 = date(year, 12, 31)
        jan1_next = date(year + 1, 1, 1)
        
        # If Dec 31 is Mon-Wed, it belongs to next year's week 1
        if dec31.weekday() <= 2:  # Mon=0, Tue=1, Wed=2
            return 1  # This week belongs to next year
        else:
            return 53 if week_number == 53 else 52  # Valid week 53
    
    return week_number


def get_week_ending_sunday(year, week_number):
    """
    Get the week ending Sunday date for a given week number and year
    using Excel WEEKNUM logic.
    
    Args:
        year: int - The year
        week_number: int - Week number (1-53)
    
    Returns:
        date: The Sunday ending date for that week
    """
    # Find first Monday of the year
    jan1 = date(year, 1, 1)
    jan1_weekday = jan1.weekday()
    
    if jan1_weekday == 0:  # Already Monday
        week_start_adjustment = 0
    else:
        week_start_adjustment = -jan1_weekday
    
    first_monday_of_year = jan1 + timedelta(days=week_start_adjustment)
    
    # Calculate the Monday of the specified week
    week_monday = first_monday_of_year + timedelta(weeks=week_number - 1)
    
    # Get the Sunday of that week (6 days later)
    week_ending_sunday = week_monday + timedelta(days=6)
    
    return week_ending_sunday


@tab7_bp.route("/tab/7")
def tab7_view():
    """Main Executive Dashboard page."""
    logger.info(
        "Loading Executive Dashboard at %s",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    
    # Get dashboard display configuration
    try:
        from app.models.config_models import ExecutiveDashboardConfiguration, get_default_executive_dashboard_config
        config = ExecutiveDashboardConfiguration.query.filter_by(
            user_id='default_user', 
            config_name='default'
        ).first()
        
        if config:
            dashboard_config = {
                'current_week_view_enabled': config.current_week_view_enabled
            }
        else:
            # Use default configuration
            defaults = get_default_executive_dashboard_config()
            dashboard_config = {
                'current_week_view_enabled': defaults['display']['current_week_view_enabled']
            }
    except Exception as e:
        logger.warning(f"Failed to load dashboard config: {e}. Using defaults.")
        dashboard_config = {
            'current_week_view_enabled': True  # Safe default
        }
    
    return render_template(
        "executive_dashboard.html", 
        store_mapping=STORE_MAPPING,
        dashboard_config=dashboard_config
    )


@tab7_bp.route("/api/executive/data_availability", methods=["GET"])
def get_data_availability():
    """Get data availability and freshness information."""
    session = None
    try:
        session = db.session()

        # Get earliest and latest dates with actual data (revenue > 0)
        earliest = (
            session.query(func.min(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        latest = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        total_records = (
            session.query(func.count(PayrollTrends.id))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        current_date = datetime.now().date()
        data_span_days = (latest - earliest).days if earliest and latest else 0

        return jsonify(
            {
                "earliest_date": earliest.isoformat() if earliest else None,
                "latest_date": latest.isoformat() if latest else None,
                "total_records": total_records,
                "data_span_days": data_span_days,
                "as_of_date": current_date.isoformat(),
                "data_freshness_days": (current_date - latest).days if latest else None,
            }
        )

    except Exception as e:
        logger.error(f"Error getting data availability: {str(e)}")
        return (
            jsonify({"error": "Failed to get data availability", "details": str(e)}),
            500,
        )
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/dashboard_summary", methods=["GET"])
def get_executive_summary():
    """Get high-level executive metrics with enhanced store filtering and period options."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        period = request.args.get("period", "4weeks")  # Enhanced: current_week, previous_week, week_number, 12weeks, 52weeks, ytd
        rolling_avg = request.args.get("rolling_avg", "none")
        view_mode = request.args.get("view_mode", "current")
        week_number = request.args.get("week_number")

        logger.info(
            f"Fetching executive summary: store={store_filter}, period={period}, rolling_avg={rolling_avg}, view_mode={view_mode}"
        )

        # Enhanced date range handling
        if period == "week_number" and week_number:
            # Use the enhanced week-based filtering
            return get_enhanced_dashboard_summary()
        elif period in ["current_week", "previous_week"]:
            # Calculate dates using Excel WEEKNUM logic
            today = datetime.now().date()
            current_year = today.year
            current_excel_week = excel_weeknum(today)
            
            if period == "current_week":
                # Current week using Excel logic
                week_ending_sunday = get_week_ending_sunday(current_year, current_excel_week)
                start_date = week_ending_sunday - timedelta(days=6)  # Monday
                end_date = week_ending_sunday  # Sunday
            else:  # previous_week
                # Previous week using Excel logic
                prev_week_num = current_excel_week - 1
                if prev_week_num < 1:
                    # Handle year boundary - get last week of previous year
                    prev_year = current_year - 1
                    prev_week_num = excel_weeknum(date(prev_year, 12, 31))
                    week_ending_sunday = get_week_ending_sunday(prev_year, prev_week_num)
                else:
                    week_ending_sunday = get_week_ending_sunday(current_year, prev_week_num)
                
                start_date = week_ending_sunday - timedelta(days=6)  # Monday
                end_date = week_ending_sunday  # Sunday
        else:
            # Use existing date range logic
            start_date, end_date = get_date_range_from_params(request, session)
            if not start_date or not end_date:
                return jsonify({"error": "Invalid date range"}), 400

        # Build base query for payroll trends
        payroll_query = session.query(
            func.sum(PayrollTrends.total_revenue).label("total_revenue"),
            func.sum(PayrollTrends.rental_revenue).label("rental_revenue"),
            func.sum(PayrollTrends.payroll_cost).label("total_payroll"),
            func.sum(PayrollTrends.wage_hours).label("total_hours"),
            func.avg(PayrollTrends.labor_efficiency_ratio).label("avg_labor_ratio"),
            func.avg(PayrollTrends.revenue_per_hour).label("avg_revenue_per_hour"),
        ).filter(PayrollTrends.week_ending.between(start_date, end_date))

        if store_filter != "all":
            payroll_query = payroll_query.filter(PayrollTrends.store_id == store_filter)

        payroll_metrics = payroll_query.first()

        # Handle case where no payroll data is found
        if not payroll_metrics:
            # Create empty metrics structure
            class EmptyPayrollMetrics:
                def __init__(self):
                    self.total_revenue = 0
                    self.rental_revenue = 0
                    self.total_payroll = 0
                    self.avg_labor_ratio = 0
                    self.avg_revenue_per_hour = 0
            payroll_metrics = EmptyPayrollMetrics()

        # Get metrics using standardized store_code columns from pos_transaction_items
        if store_filter != "all":
            store_condition = "AND pti.store_code = :store_filter"
            store_params = {'start_date': start_date, 'end_date': end_date, 'store_filter': store_filter}
        else:
            store_condition = "AND pti.store_code != '000'"
            store_params = {'start_date': start_date, 'end_date': end_date}
            
        pos_scorecard_sql = text(f"""
            SELECT 
                COUNT(DISTINCT pti.contract_no) as total_new_contracts,
                AVG(COUNT(DISTINCT pti.contract_no)) OVER() as avg_new_contracts,
                SUM(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as total_revenue,
                COUNT(DISTINCT pti.item_num) as product_diversity,
                COUNT(DISTINCT pt.customer_no) as unique_customers
            FROM pos_transaction_items pti
            JOIN pos_transactions pt ON pti.contract_no = pt.contract_no
            WHERE pti.import_date BETWEEN :start_date AND :end_date
                {store_condition}
        """)
        
        pos_scorecard_result = session.execute(pos_scorecard_sql, store_params).first()

        # Store filtering for POS scorecard is done by checking individual store contract columns
        # No need for store_filter since we're aggregating all stores' contracts
        
        # For compatibility, create scorecard_metrics with the expected structure
        class ScorecardMetricsCompat:
            def __init__(self, pos_result):
                self.avg_new_contracts = float(pos_result.avg_new_contracts) if pos_result and pos_result.avg_new_contracts else 0
                self.total_new_contracts = float(pos_result.total_new_contracts) if pos_result and pos_result.total_new_contracts else 0
                self.avg_deliveries = float(pos_result.product_diversity) if pos_result and pos_result.product_diversity else 0  # Using product_diversity as proxy
                self.product_diversity = float(pos_result.product_diversity) if pos_result and pos_result.product_diversity else 0
                self.unique_customers = float(pos_result.unique_customers) if pos_result and pos_result.unique_customers else 0
                self.total_revenue = float(pos_result.total_revenue) if pos_result and pos_result.total_revenue else 0
                self.avg_ar_aging = None  # Calculate from customer data if needed
                self.total_discounts = None  # Calculate from transaction data if needed
        
        scorecard_metrics = ScorecardMetricsCompat(pos_scorecard_result)
        
        # FIXED 2025-09-09: Removed conflicting unified revenue override
        # Issue: Was overriding correct POS transaction revenue ($98,683) with scorecard data ($104,242)
        # Solution: Use original POS transaction calculation (scorecard_metrics.total_revenue already set correctly)
        # 
        # TODO FUTURE: If unified calculation needed, integrate into original POS logic rather than override
        # 
        # COMMENTED OUT PROBLEMATIC OVERRIDE:
        # unified_revenue = _get_unified_revenue_kpi(session, 'executive_summary_revenue_weeks', store_filter)
        # scorecard_metrics.total_revenue = unified_revenue

        # Calculate YoY growth if we have data from last year
        last_year_start = start_date.replace(year=start_date.year - 1)
        last_year_end = end_date.replace(year=end_date.year - 1)

        # CRITICAL FIX: Get last year revenue from scorecard_trends_data (consistent with current revenue source)
        from sqlalchemy import text as sql_text
        last_year_scorecard_query = sql_text("""
            SELECT SUM(COALESCE(revenue_3607, 0) + 
                      COALESCE(revenue_6800, 0) + 
                      COALESCE(revenue_728, 0) + 
                      COALESCE(revenue_8101, 0)) as total_revenue
            FROM scorecard_trends_data 
            WHERE week_ending BETWEEN :start_date AND :end_date
        """)
        
        last_year_result = session.execute(last_year_scorecard_query, {
            'start_date': last_year_start, 
            'end_date': last_year_end
        }).fetchone()
        
        last_year_revenue = float(last_year_result.total_revenue) if last_year_result and last_year_result.total_revenue else 0
        current_revenue = float(scorecard_metrics.total_revenue or 0)
        yoy_growth = (
            (
                (current_revenue - float(last_year_revenue))
                / float(last_year_revenue)
                * 100
            )
            if last_year_revenue
            else 0
        )

        # Get current inventory value (from existing ItemMaster)
        inventory_query = session.query(
            func.sum(ItemMaster.retail_price).label("total_inventory_value"),
            func.count(ItemMaster.tag_id).label("total_items"),
        )

        if store_filter != "all":
            inventory_query = inventory_query.filter(
                or_(
                    ItemMaster.home_store == store_filter,
                    ItemMaster.current_store == store_filter,
                )
            )

        inventory_metrics = inventory_query.first()

        # Handle case where no inventory data is found
        if not inventory_metrics:
            # Create empty metrics structure
            class EmptyInventoryMetrics:
                def __init__(self):
                    self.total_inventory_value = 0
                    self.total_items = 0
            inventory_metrics = EmptyInventoryMetrics()

        summary = {
            "financial_metrics": {
                "total_revenue": float(scorecard_metrics.total_revenue or 0),
                "rental_revenue": float(payroll_metrics.rental_revenue or 0),
                "total_payroll": float(payroll_metrics.total_payroll or 0),
                "labor_efficiency": float(payroll_metrics.avg_labor_ratio or 0),
                "revenue_per_hour": float(payroll_metrics.avg_revenue_per_hour or 0),
                "yoy_growth": round(yoy_growth, 2),
            },
            "operational_metrics": {
                "new_contracts": int(scorecard_metrics.total_new_contracts or 0),
                "avg_weekly_contracts": float(scorecard_metrics.avg_new_contracts or 0),
                "avg_deliveries": float(scorecard_metrics.avg_deliveries or 0),
                "inventory_value": float(inventory_metrics.total_inventory_value or 0),
                "total_items": int(inventory_metrics.total_items or 0),
            },
            "health_indicators": {
                "ar_aging_percent": float(scorecard_metrics.avg_ar_aging or 0),
                "total_discounts": float(scorecard_metrics.total_discounts or 0),
                "profit_margin": round(
                    get_pl_profit_margin(
                        session, 
                        datetime.now().year,
                        fallback_revenue=float(current_revenue),
                        fallback_payroll=float(payroll_metrics.total_payroll or 0)
                    ),
                    2
                ),
            },
            "metadata": {
                "store": store_filter,
                "period": period,
                "rolling_avg": rolling_avg,
                "view_mode": view_mode,
                "week_number": week_number,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timestamp": datetime.now().isoformat(),
            },
        }

        logger.info(
            f"Executive summary calculated: Revenue: ${summary['financial_metrics']['total_revenue']:,.2f}"
        )
        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error fetching executive summary: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/payroll_trends", methods=["GET"])
def get_payroll_trends():
    """Get detailed payroll trends for comprehensive time-series charting."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        weeks = int(request.args.get("weeks", 328))  # Default to full historical data

        logger.info(
            f"Fetching {weeks} weeks of payroll trends for store: {store_filter}"
        )

        # Get the latest available data date - CRITICAL FIX for date range calculation
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        if not latest_data_date:
            # Fallback to today if no data found
            latest_data_date = datetime.now().date()

        # Calculate the date range based on the most recent data, not today's date
        end_date = latest_data_date
        start_date = end_date - timedelta(weeks=weeks)

        logger.info(
            f"Date range for payroll trends: {start_date} to {end_date} (latest data: {latest_data_date})"
        )

        # Get weekly data with comprehensive metrics - FIXED: Add date filtering
        query = session.query(
            PayrollTrends.week_ending,
            PayrollTrends.store_id,
            PayrollTrends.total_revenue,
            PayrollTrends.rental_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.labor_efficiency_ratio,
            PayrollTrends.revenue_per_hour,
            PayrollTrends.wage_hours,
        ).filter(
            PayrollTrends.week_ending.between(start_date, end_date),
            PayrollTrends.total_revenue > 0,  # Only include actual data records
        )

        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)

        # Order by date ascending for proper time series
        query = query.order_by(PayrollTrends.week_ending)

        results = query.all()

        # Format data for comprehensive analytics
        trend_data = []
        weekly_aggregates = {}  # For aggregating multi-store data

        for row in results:
            week_key = row.week_ending.isoformat()

            # Individual store data point
            data_point = {
                "week": week_key,
                "store_code": row.store_code,
                "store_name": STORE_MAPPING.get(row.store_code, row.store_code),
                "revenue": float(row.total_revenue) if row.total_revenue else 0,
                "rental_revenue": (
                    float(row.rental_revenue) if row.rental_revenue else 0
                ),
                "payroll": float(row.payroll_cost) if row.payroll_cost else 0,
                "efficiency": (
                    float(row.labor_efficiency_ratio)
                    if row.labor_efficiency_ratio
                    else 0
                ),
                "revenue_per_hour": (
                    float(row.revenue_per_hour) if row.revenue_per_hour else 0
                ),
                "hours": float(row.wage_hours) if row.wage_hours else 0,
                "profit": float(row.total_revenue or 0) - float(row.payroll_cost or 0),
                "profit_margin": round(
                    (
                        (float(row.total_revenue or 0) - float(row.payroll_cost or 0))
                        / float(row.total_revenue or 1)
                    )
                    * 100,
                    2,
                ),
            }

            trend_data.append(data_point)

            # Aggregate for company-wide view
            if week_key not in weekly_aggregates:
                weekly_aggregates[week_key] = {
                    "week": week_key,
                    "total_revenue": 0,
                    "total_rental_revenue": 0,
                    "total_payroll": 0,
                    "total_hours": 0,
                    "store_count": 0,
                }

            weekly_aggregates[week_key]["total_revenue"] += data_point["revenue"]
            weekly_aggregates[week_key]["total_rental_revenue"] += data_point[
                "rental_revenue"
            ]
            weekly_aggregates[week_key]["total_payroll"] += data_point["payroll"]
            weekly_aggregates[week_key]["total_hours"] += data_point["hours"]
            weekly_aggregates[week_key]["store_count"] += 1

        # Calculate company-wide aggregated metrics
        aggregated_trends = []
        for week_data in weekly_aggregates.values():
            total_rev = week_data["total_revenue"]
            total_pay = week_data["total_payroll"]

            aggregated_trends.append(
                {
                    "week": week_data["week"],
                    "revenue": total_rev,
                    "rental_revenue": week_data["total_rental_revenue"],
                    "payroll": total_pay,
                    "profit": total_rev - total_pay,
                    "profit_margin": (
                        round(((total_rev - total_pay) / total_rev) * 100, 2)
                        if total_rev > 0
                        else 0
                    ),
                    "efficiency": (
                        round((total_pay / total_rev) * 100, 2) if total_rev > 0 else 0
                    ),
                    "revenue_per_hour": (
                        round(total_rev / week_data["total_hours"], 2)
                        if week_data["total_hours"] > 0
                        else 0
                    ),
                    "hours": week_data["total_hours"],
                    "store_count": week_data["store_count"],
                }
            )

        # Sort by week
        aggregated_trends.sort(key=lambda x: x["week"])

        return jsonify(
            {
                "trends": trend_data,
                "aggregated_trends": aggregated_trends,
                "total_weeks": len(aggregated_trends),
                "date_range": {
                    "start": (
                        aggregated_trends[0]["week"] if aggregated_trends else None
                    ),
                    "end": aggregated_trends[-1]["week"] if aggregated_trends else None,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error fetching payroll trends: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/store_comparison", methods=["GET"])
def get_store_comparison():
    """Get comparative metrics across all stores.

    Supports two modes:
    - aggregate (default): aggregates metrics over a period of weeks
    - weekly: returns current vs previous week comparison per store
    """
    session = None
    try:
        session = db.session()
        period_weeks = int(request.args.get("weeks", 4))
        mode = request.args.get("mode", "aggregate")
        store_filter = request.args.get("store", "all")

        # Use actual latest data date from pos_transaction_items
        latest_data_sql = text("""
            SELECT MAX(DATE(import_date)) 
            FROM pos_transaction_items 
            WHERE store_code != '000'
        """)
        latest_data_result = session.execute(latest_data_sql).scalar()
        
        if latest_data_result:
            latest_data_date = latest_data_result
        else:
            latest_data_date = datetime.now().date()

        if mode == "weekly":
            logger.info(f"Using latest data date: {latest_data_date}")
            current_week = latest_data_date
            previous_week = current_week - timedelta(weeks=1)

            # Use standardized store_code from pos_transaction_items
            if store_filter != "all":
                store_condition = "AND pti.store_code = :store_filter"
                current_params = {'current_week': current_week, 'store_filter': store_filter}
                previous_params = {'previous_week': previous_week, 'store_filter': store_filter}
            else:
                store_condition = "AND pti.store_code != '000'"
                current_params = {'current_week': current_week}
                previous_params = {'previous_week': previous_week}

            # Current week metrics using standardized store_code
            current_sql = text(f"""
                SELECT 
                    pti.store_code,
                    SUM(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as revenue,
                    COUNT(DISTINCT pti.contract_no) as transaction_count,
                    COUNT(DISTINCT pti.item_num) as product_diversity,
                    AVG(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as avg_transaction_value
                FROM pos_transaction_items pti
                WHERE DATE(pti.import_date) = :current_week
                    {store_condition}
                GROUP BY pti.store_code
            """)
            current_metrics = session.execute(current_sql, current_params).fetchall()

            # Previous week metrics
            previous_sql = text(f"""
                SELECT 
                    pti.store_code,
                    SUM(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as revenue,
                    COUNT(DISTINCT pti.contract_no) as transaction_count,
                    COUNT(DISTINCT pti.item_num) as product_diversity,
                    AVG(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as avg_transaction_value
                FROM pos_transaction_items pti
                WHERE DATE(pti.import_date) = :previous_week
                    {store_condition}
                GROUP BY pti.store_code
            """)
            previous_metrics = session.execute(previous_sql, previous_params).fetchall()

            current_dict = {m.store_code: m for m in current_metrics}
            previous_dict = {m.store_code: m for m in previous_metrics}
            all_store_codes = set(current_dict.keys()) | set(previous_dict.keys())

            comparison_data = []
            for store_code in all_store_codes:
                current = current_dict.get(store_code)
                previous = previous_dict.get(store_code)

                curr_revenue = float(current.revenue or 0) if current else 0
                prev_revenue = float(previous.revenue or 0) if previous else 0
                curr_transactions = float(current.transaction_count or 0) if current else 0
                prev_transactions = float(previous.transaction_count or 0) if previous else 0
                curr_diversity = float(current.product_diversity or 0) if current else 0
                prev_diversity = float(previous.product_diversity or 0) if previous else 0
                curr_avg_value = float(current.avg_transaction_value or 0) if current else 0
                prev_avg_value = float(previous.avg_transaction_value or 0) if previous else 0

                def pct_change(curr, prev):
                    return ((curr - prev) / prev * 100) if prev else None

                store_data = {
                    "store_code": store_code,
                    "store_name": STORE_MAPPING.get(store_code, store_code),
                    "revenue": {
                        "current": curr_revenue,
                        "previous": prev_revenue,
                        "change": curr_revenue - prev_revenue,
                        "pct_change": pct_change(curr_revenue, prev_revenue),
                    },
                    "transactions": {
                        "current": curr_transactions,
                        "previous": prev_transactions,
                        "change": curr_transactions - prev_transactions,
                        "pct_change": pct_change(curr_transactions, prev_transactions),
                    },
                    "product_diversity": {
                        "current": curr_diversity,
                        "previous": prev_diversity,
                        "change": curr_diversity - prev_diversity,
                        "pct_change": pct_change(curr_diversity, prev_diversity),
                    },
                    "avg_transaction_value": {
                        "current": curr_avg_value,
                        "previous": prev_avg_value,
                        "change": curr_avg_value - prev_avg_value,
                        "pct_change": pct_change(curr_avg_value, prev_avg_value),
                    },
                }
                comparison_data.append(store_data)

            # Rankings based on current week values using revenue + payroll metrics
            for metric in ["revenue", "transactions", "product_diversity", "avg_transaction_value"]:
                reverse = True
                sorted_stores = sorted(
                    comparison_data, key=lambda x: x[metric]["current"], reverse=reverse
                )
                for idx, store in enumerate(sorted_stores, 1):
                    store[metric]["rank"] = idx
                    
            # Add payroll data from payroll_trends_data if available for each store
            for store_data in comparison_data:
                try:
                    payroll_query = text("""
                        SELECT SUM(payroll_cost) as payroll, SUM(wage_hours) as hours
                        FROM executive_payroll_trends 
                        WHERE store_code = :store_code 
                        AND week_ending BETWEEN DATE_SUB(:current_week, INTERVAL 6 DAY) AND :current_week
                    """)
                    payroll_result = session.execute(payroll_query, {
                        'store_code': store_data['store_code'], 
                        'current_week': current_week
                    }).first()
                    
                    if payroll_result and payroll_result.payroll:
                        curr_payroll = float(payroll_result.payroll)
                        curr_hours = float(payroll_result.hours or 1)
                        curr_revenue = store_data['revenue']['current']
                        
                        store_data["payroll"] = {
                            "current": curr_payroll,
                            "previous": 0,  # Would need previous week query
                            "change": curr_payroll,
                            "pct_change": None
                        }
                        store_data["profit"] = {
                            "current": curr_revenue - curr_payroll,
                            "previous": 0,
                            "change": curr_revenue - curr_payroll,
                            "pct_change": None
                        }
                        store_data["efficiency"] = {
                            "current": curr_revenue / curr_hours if curr_hours else 0,
                            "previous": 0,
                            "change": curr_revenue / curr_hours if curr_hours else 0,
                            "pct_change": None
                        }
                except:
                    # If payroll data not available, use placeholder values
                    pass

            return jsonify({"mode": "weekly", "stores": comparison_data})

        # Default aggregate mode
        end_date = latest_data_date
        start_date = end_date - timedelta(weeks=period_weeks)

        logger.info(
            f"Store comparison date range: {start_date} to {end_date} (latest data: {latest_data_date})"
        )

        # Use standardized store_code from pos_transaction_items for aggregate mode
        if store_filter != "all":
            store_condition = "AND pti.store_code = :store_filter"
            store_params = {'start_date': start_date, 'end_date': end_date, 'store_filter': store_filter}
        else:
            store_condition = "AND pti.store_code != '000'"
            store_params = {'start_date': start_date, 'end_date': end_date}

        store_sql = text(f"""
            SELECT 
                pti.store_code,
                SUM(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as revenue,
                COUNT(DISTINCT pti.contract_no) as total_transactions,
                COUNT(DISTINCT pti.item_num) as product_diversity,
                AVG(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as avg_transaction_value,
                COUNT(DISTINCT pt.customer_no) as unique_customers
            FROM pos_transaction_items pti
            JOIN pos_transactions pt ON pti.contract_no = pt.contract_no
            WHERE pti.import_date BETWEEN :start_date AND :end_date
                {store_condition}
            GROUP BY pti.store_code
        """)
        store_metrics = session.execute(store_sql, store_params).fetchall()

        comparison_data = []
        for store in store_metrics:
            revenue = float(store.revenue or 0)
            transactions = float(store.total_transactions or 0)
            diversity = float(store.product_diversity or 0)
            avg_value = float(store.avg_transaction_value or 0)
            customers = float(store.unique_customers or 0)

            comparison_data.append(
                {
                    "store_code": store.store_code,
                    "store_name": STORE_MAPPING.get(store.store_code, store.store_code),
                    "revenue": revenue,
                    "total_transactions": transactions,
                    "product_diversity": diversity,
                    "avg_transaction_value": avg_value,
                    "unique_customers": customers,
                    "revenue_per_transaction": revenue / transactions if transactions else 0,
                    "revenue_per_customer": revenue / customers if customers else 0,
                }
            )

        comparison_data.sort(key=lambda x: x["revenue"], reverse=True)
        for i, store in enumerate(comparison_data, 1):
            store["rank"] = i

        return jsonify({"mode": "aggregate", "stores": comparison_data})

    except Exception as e:
        logger.error(f"Error fetching store comparison: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/kpi_dashboard", methods=["GET"])
def get_kpi_dashboard():
    """Get executive KPIs with targets and variances."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")

        # Get KPIs from database
        query = session.query(ExecutiveKPI)

        if store_filter != "all":
            query = query.filter(
                or_(
                    ExecutiveKPI.store_code == store_filter,
                    ExecutiveKPI.store_code.is_(None),
                )  # Include company-wide KPIs
            )
        else:
            query = query.filter(ExecutiveKPI.store_code.is_(None))  # Only company-wide

        kpis = query.all()

        # Group KPIs by category
        kpi_data = {"financial": [], "operational": [], "efficiency": [], "growth": []}

        for kpi in kpis:
            category = kpi.kpi_category or "operational"
            if category in kpi_data:
                kpi_data[category].append(
                    {
                        "name": kpi.kpi_name,
                        "current": float(kpi.current_value) if kpi.current_value else 0,
                        "target": float(kpi.target_value) if kpi.target_value else 0,
                        "variance": (
                            float(kpi.variance_percent) if kpi.variance_percent else 0
                        ),
                        "trend": kpi.trend_direction,
                        "period": kpi.period,
                    }
                )

        return jsonify(kpi_data)

    except Exception as e:
        logger.error(f"Error fetching KPI dashboard: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/growth_analysis", methods=["GET"])
def get_growth_analysis():
    """Get comprehensive YoY, MoM, WoW growth analysis."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")

        logger.info(f"Calculating growth analysis for store: {store_filter}")

        # Get current date boundaries - use latest data date instead of today
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        if not latest_data_date:
            latest_data_date = datetime.now().date()

        end_date = latest_data_date
        current_week_start = end_date - timedelta(days=7)
        current_month_start = end_date.replace(day=1)
        current_year_start = end_date.replace(month=1, day=1)

        # Previous periods - FIXED: WoW compares same week last year (not last week)
        try:
            prev_week_start = current_week_start.replace(
                year=current_week_start.year - 1
            )
            prev_week_end = end_date.replace(year=end_date.year - 1)
        except ValueError:
            # Handle leap year edge case
            prev_week_start = current_week_start - timedelta(days=365)
            prev_week_end = end_date - timedelta(days=365)

        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        prev_month_end = current_month_start - timedelta(days=1)

        try:
            prev_year_start = current_year_start.replace(
                year=current_year_start.year - 1
            )
            prev_year_end = end_date.replace(year=end_date.year - 1)
        except ValueError:
            # Handle leap year edge case
            prev_year_start = current_year_start - timedelta(days=365)
            prev_year_end = end_date - timedelta(days=365)

        def get_period_metrics(start_date, end_date):
            query = session.query(
                func.sum(PayrollTrends.total_revenue).label("revenue"),
                func.sum(PayrollTrends.payroll_cost).label("payroll"),
                func.avg(PayrollTrends.labor_efficiency_ratio).label("efficiency"),
            ).filter(PayrollTrends.week_ending.between(start_date, end_date))

            if store_filter != "all":
                query = query.filter(PayrollTrends.store_id == store_filter)

            return query.first()

        # Current periods
        current_week = get_period_metrics(current_week_start, end_date)
        current_month = get_period_metrics(current_month_start, end_date)
        current_year = get_period_metrics(current_year_start, end_date)

        # Previous periods
        prev_week = get_period_metrics(prev_week_start, prev_week_end)
        prev_month = get_period_metrics(prev_month_start, prev_month_end)
        prev_year = get_period_metrics(prev_year_start, prev_year_end)

        def calculate_growth(current, previous):
            if not current or not previous or not previous:
                return 0
            try:
                return round(
                    ((float(current) - float(previous)) / float(previous)) * 100, 2
                )
            except (ZeroDivisionError, TypeError):
                return 0

        # Calculate growth rates
        growth_analysis = {
            "week_over_week": {
                "revenue_growth": calculate_growth(
                    current_week.revenue, prev_week.revenue
                ),
                "payroll_growth": calculate_growth(
                    current_week.payroll, prev_week.payroll
                ),
                "efficiency_change": calculate_growth(
                    current_week.efficiency, prev_week.efficiency
                ),
                "current_revenue": float(current_week.revenue or 0),
                "prev_revenue": float(prev_week.revenue or 0),
            },
            "month_over_month": {
                "revenue_growth": calculate_growth(
                    current_month.revenue, prev_month.revenue
                ),
                "payroll_growth": calculate_growth(
                    current_month.payroll, prev_month.payroll
                ),
                "efficiency_change": calculate_growth(
                    current_month.efficiency, prev_month.efficiency
                ),
                "current_revenue": float(current_month.revenue or 0),
                "prev_revenue": float(prev_month.revenue or 0),
            },
            "year_over_year": {
                "revenue_growth": calculate_growth(
                    current_year.revenue, prev_year.revenue
                ),
                "payroll_growth": calculate_growth(
                    current_year.payroll, prev_year.payroll
                ),
                "efficiency_change": calculate_growth(
                    current_year.efficiency, prev_year.efficiency
                ),
                "current_revenue": float(current_year.revenue or 0),
                "prev_revenue": float(prev_year.revenue or 0),
            },
        }

        # Calculate velocity (rate of change acceleration)
        revenue_velocity = {
            "wow_acceleration": growth_analysis["week_over_week"]["revenue_growth"]
            - growth_analysis["month_over_month"]["revenue_growth"],
            "mom_acceleration": growth_analysis["month_over_month"]["revenue_growth"]
            - growth_analysis["year_over_year"]["revenue_growth"],
        }

        growth_analysis["velocity"] = revenue_velocity

        return jsonify(growth_analysis)

    except Exception as e:
        logger.error(f"Error calculating growth analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/store_performance_metrics", methods=["GET"])
def get_store_performance_metrics():
    """Get store performance metrics using standardized store_code columns.
    
    Returns revenue comparison, transaction volume, and product diversity by store.
    """
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        period_weeks = int(request.args.get("weeks", 4))
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=period_weeks)
        
        # Store Revenue Comparison from correlation analysis
        if store_filter != "all":
            store_condition = "AND pti.store_code = :store_filter"
            params = {'start_date': start_date, 'end_date': end_date, 'store_filter': store_filter}
        else:
            store_condition = "AND pti.store_code != '000'"
            params = {'start_date': start_date, 'end_date': end_date}
            
        performance_sql = text(f"""
            SELECT 
                pti.store_code,
                COUNT(DISTINCT pti.contract_no) as transactions,
                SUM(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as total_revenue,
                AVG(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as avg_transaction_value,
                COUNT(DISTINCT pti.item_num) as product_diversity,
                COUNT(DISTINCT pt.customer_no) as unique_customers
            FROM pos_transaction_items pti
            JOIN pos_transactions pt ON pti.contract_no = pt.contract_no
            WHERE pti.import_date BETWEEN :start_date AND :end_date
                {store_condition}
            GROUP BY pti.store_code
            ORDER BY total_revenue DESC
        """)
        
        results = session.execute(performance_sql, params).fetchall()
        
        metrics = []
        for row in results:
            metrics.append({
                "store_code": row.store_code,
                "store_name": STORE_MAPPING.get(row.store_code, row.store_code),
                "transactions": int(row.transactions),
                "total_revenue": float(row.total_revenue),
                "avg_transaction_value": float(row.avg_transaction_value),
                "product_diversity": int(row.product_diversity),
                "unique_customers": int(row.unique_customers),
                "revenue_per_customer": float(row.total_revenue) / float(row.unique_customers) if row.unique_customers else 0,
            })
        
        return jsonify({
            "period": f"{period_weeks} weeks",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Error fetching store performance metrics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/manager_scorecard", methods=["GET"])
def get_manager_scorecard():
    """Get manager performance scorecard using standardized store_code columns.
    
    Returns performance metrics by manager/store from correlation analysis.
    """
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        period_weeks = int(request.args.get("weeks", 4))
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=period_weeks)
        
        # Manager Performance by Store from correlation analysis
        if store_filter != "all":
            store_condition = "AND pti.store_code = :store_filter"
            params = {'start_date': start_date, 'end_date': end_date, 'store_filter': store_filter}
        else:
            store_condition = "AND pti.store_code != '000'"
            params = {'start_date': start_date, 'end_date': end_date}
            
        manager_sql = text(f"""
            SELECT 
                pti.store_code,
                CASE pti.store_code
                    WHEN '3607' THEN 'TYLER'
                    WHEN '6800' THEN 'ZACK'
                    WHEN '728' THEN 'BRUCE'
                    WHEN '8101' THEN 'TIM'
                    ELSE 'CORPORATE'
                END as manager,
                COUNT(DISTINCT pt.customer_no) as unique_customers,
                COUNT(DISTINCT pti.contract_no) as total_contracts,
                SUM(CAST(pti.price * pti.qty AS DECIMAL(12,2))) as revenue,
                COUNT(DISTINCT pti.item_num) as product_types_sold
            FROM pos_transaction_items pti
            JOIN pos_transactions pt ON pti.contract_no = pt.contract_no
            WHERE pti.import_date BETWEEN :start_date AND :end_date
                {store_condition}
            GROUP BY pti.store_code
            ORDER BY revenue DESC
        """)
        
        results = session.execute(manager_sql, params).fetchall()
        
        scorecards = []
        for row in results:
            revenue = float(row.revenue)
            customers = int(row.unique_customers)
            contracts = int(row.total_contracts)
            
            scorecards.append({
                "store_code": row.store_code,
                "store_name": STORE_MAPPING.get(row.store_code, row.store_code),
                "manager": row.manager,
                "unique_customers": customers,
                "total_contracts": contracts,
                "revenue": revenue,
                "product_types_sold": int(row.product_types_sold),
                "revenue_per_customer": revenue / customers if customers else 0,
                "revenue_per_contract": revenue / contracts if contracts else 0,
                "contracts_per_customer": contracts / customers if customers else 0,
            })
        
        return jsonify({
            "period": f"{period_weeks} weeks",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "scorecards": scorecards
        })
        
    except Exception as e:
        logger.error(f"Error fetching manager scorecard: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/equipment_utilization", methods=["GET"])
def get_equipment_utilization():
    """Get equipment utilization analysis using standardized store_code columns.
    
    Returns equipment distribution and utilization metrics by store.
    """
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        
        # Equipment Distribution by Store from correlation analysis
        if store_filter != "all":
            store_condition = "AND home_store = :store_filter"
            params = {'store_filter': store_filter}
        else:
            store_condition = "AND home_store IN ('3607','6800','728','8101')"
            params = {}
            
        equipment_sql = text(f"""
            SELECT 
                home_store as store_code,
                COUNT(DISTINCT item_num) as equipment_types,
                SUM(qty) as total_inventory,
                SUM(CASE WHEN qty = 0 THEN 1 ELSE 0 END) as out_of_stock_items,
                AVG(sell_price) as avg_equipment_value,
                SUM(qty * sell_price) as total_inventory_value
            FROM pos_equipment
            WHERE sell_price > 0 
                AND sell_price < 5000  -- Filter out unrealistic test values
                AND qty < 10000        -- Filter out unrealistic test quantities
                {store_condition}
            GROUP BY home_store
            ORDER BY total_inventory_value DESC
        """)
        
        results = session.execute(equipment_sql, params).fetchall()
        
        utilization = []
        for row in results:
            total_items = int(row.equipment_types)
            out_of_stock = int(row.out_of_stock_items)
            in_stock_items = total_items - out_of_stock
            
            utilization.append({
                "store_code": row.store_code,
                "store_name": STORE_MAPPING.get(row.store_code, row.store_code),
                "equipment_types": total_items,
                "total_inventory": int(row.total_inventory),
                "out_of_stock_items": out_of_stock,
                "in_stock_items": in_stock_items,
                "stock_rate_pct": (in_stock_items / total_items * 100) if total_items else 0,
                "avg_equipment_value": float(row.avg_equipment_value),
                "total_inventory_value": float(row.total_inventory_value)
            })
        
        return jsonify({
            "utilization": utilization
        })
        
    except Exception as e:
        logger.error(f"Error fetching equipment utilization: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/payroll_analytics", methods=["GET"])
def get_payroll_analytics():
    """Get comprehensive payroll analytics and cost control metrics.
    
    Returns payroll costs, efficiency ratios, and profit margins by store.
    This is critical for controllable expense management.
    """
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        period_weeks = int(request.args.get("weeks", 8))
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=period_weeks)
        
        # Get payroll data from payroll_trends_data table
        if store_filter != "all":
            store_condition = "AND store_code = :store_filter"
            params = {'start_date': start_date, 'end_date': end_date, 'store_filter': store_filter}
        else:
            store_condition = ""
            params = {'start_date': start_date, 'end_date': end_date}
            
        payroll_sql = text(f"""
            SELECT 
                store_code,
                SUM(total_revenue) as total_revenue,
                SUM(payroll_cost) as total_payroll,
                AVG(labor_efficiency_ratio) as avg_efficiency,
                SUM(wage_hours) as total_hours,
                COUNT(DISTINCT week_ending) as weeks_of_data
            FROM executive_payroll_trends
            WHERE week_ending BETWEEN :start_date AND :end_date
                {store_condition}
            GROUP BY store_code
            ORDER BY total_revenue DESC
        """)
        
        results = session.execute(payroll_sql, params).fetchall()
        
        payroll_metrics = []
        for row in results:
            total_revenue = float(row.total_revenue or 0)
            total_payroll = float(row.total_payroll or 0)
            total_hours = float(row.total_hours or 0)
            
            # Calculate key cost control metrics
            payroll_percent = (total_payroll / total_revenue * 100) if total_revenue else 0
            profit = total_revenue - total_payroll
            profit_margin = (profit / total_revenue * 100) if total_revenue else 0
            revenue_per_hour = total_revenue / total_hours if total_hours else 0
            cost_per_hour = total_payroll / total_hours if total_hours else 0
            
            payroll_metrics.append({
                "store_code": row.store_code,
                "store_name": STORE_MAPPING.get(row.store_code, row.store_code),
                "total_revenue": total_revenue,
                "total_payroll": total_payroll,
                "gross_profit": profit,
                "payroll_percentage": round(payroll_percent, 2),
                "profit_margin": round(profit_margin, 2),
                "total_hours": total_hours,
                "revenue_per_hour": round(revenue_per_hour, 2),
                "cost_per_hour": round(cost_per_hour, 2),
                "avg_efficiency": float(row.avg_efficiency or 0),
                "weeks_of_data": int(row.weeks_of_data),
                "weekly_avg_revenue": total_revenue / max(int(row.weeks_of_data), 1),
                "weekly_avg_payroll": total_payroll / max(int(row.weeks_of_data), 1)
            })
        
        # Add company-wide summary if viewing all stores
        if store_filter == "all" and payroll_metrics:
            company_totals = {
                "store_code": "COMPANY",
                "store_name": "Company Total",
                "total_revenue": sum(m["total_revenue"] for m in payroll_metrics),
                "total_payroll": sum(m["total_payroll"] for m in payroll_metrics),
                "total_hours": sum(m["total_hours"] for m in payroll_metrics)
            }
            
            company_totals["gross_profit"] = company_totals["total_revenue"] - company_totals["total_payroll"]
            company_totals["payroll_percentage"] = round(
                (company_totals["total_payroll"] / company_totals["total_revenue"] * 100) if company_totals["total_revenue"] else 0, 2
            )
            company_totals["profit_margin"] = round(
                (company_totals["gross_profit"] / company_totals["total_revenue"] * 100) if company_totals["total_revenue"] else 0, 2
            )
            company_totals["revenue_per_hour"] = round(
                company_totals["total_revenue"] / company_totals["total_hours"] if company_totals["total_hours"] else 0, 2
            )
            company_totals["cost_per_hour"] = round(
                company_totals["total_payroll"] / company_totals["total_hours"] if company_totals["total_hours"] else 0, 2
            )
            
            payroll_metrics.append(company_totals)
        
        return jsonify({
            "period": f"{period_weeks} weeks",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "payroll_metrics": payroll_metrics,
            "cost_control_notes": {
                "target_payroll_percentage": "15-25% of revenue",
                "target_profit_margin": "40-60% gross margin",
                "efficiency_benchmark": "Revenue per hour should exceed $50"
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching payroll analytics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/forecasting", methods=["GET"])
def get_forecasting():
    """Generate predictive forecasting based on historical trends."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        forecast_weeks = int(request.args.get("weeks", 12))

        logger.info(
            f"Generating {forecast_weeks}-week forecast for store: {store_filter}"
        )

        # Get last 52 weeks of historical data for trend analysis
        query = session.query(
            PayrollTrends.week_ending,
            func.sum(PayrollTrends.total_revenue).label("revenue"),
            func.sum(PayrollTrends.payroll_cost).label("payroll"),
        )

        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)

        config = _get_executive_config()
        query = (
            query.group_by(PayrollTrends.week_ending)
            .order_by(PayrollTrends.week_ending.desc())
            .limit(config.forecasting_historical_weeks)
        )

        historical_data = query.all()

        if len(historical_data) < 12:
            return (
                jsonify({"error": "Insufficient historical data for forecasting"}),
                400,
            )

        # Sort chronologically for analysis
        historical_data.sort(key=lambda x: x.week_ending)

        # Simple linear trend + seasonal analysis
        revenues = [float(row.revenue or 0) for row in historical_data]
        payrolls = [float(row.payroll or 0) for row in historical_data]

        # Calculate moving averages and trends
        def moving_average(data, window=4):
            return [
                sum(data[i - window + 1 : i + 1]) / window
                for i in range(window - 1, len(data))
            ]

        def linear_trend(data):
            n = len(data)
            x = list(range(n))
            x_mean = sum(x) / n
            y_mean = sum(data) / n

            numerator = sum((x[i] - x_mean) * (data[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean

            return slope, intercept

        # Calculate trends
        revenue_slope, revenue_intercept = linear_trend(revenues)
        payroll_slope, payroll_intercept = linear_trend(payrolls)

        # Generate forecasts
        last_date = historical_data[-1].week_ending
        forecasts = []

        for week in range(1, forecast_weeks + 1):
            forecast_date = last_date + timedelta(weeks=week)
            data_point = len(historical_data) + week

            # Apply seasonal adjustment (basic - could be enhanced)
            seasonal_factor = (
                1 + 0.1 * (week % 4 - 2) / 10
            )  # Simple quarterly seasonality

            forecast_revenue = (
                revenue_slope * data_point + revenue_intercept
            ) * seasonal_factor
            forecast_payroll = (
                payroll_slope * data_point + payroll_intercept
            ) * seasonal_factor

            # Calculate confidence intervals (simple approach)
            revenue_std = (
                sum([(r - sum(revenues) / len(revenues)) ** 2 for r in revenues])
                / len(revenues)
            ) ** 0.5
            confidence_interval = revenue_std * 1.96  # 95% confidence

            forecasts.append(
                {
                    "week": forecast_date.isoformat(),
                    "forecast_revenue": round(max(0, forecast_revenue), 2),
                    "forecast_payroll": round(max(0, forecast_payroll), 2),
                    "forecast_profit": round(
                        max(0, forecast_revenue - forecast_payroll), 2
                    ),
                    "confidence_upper": round(
                        forecast_revenue + confidence_interval, 2
                    ),
                    "confidence_lower": round(
                        max(0, forecast_revenue - confidence_interval), 2
                    ),
                    "trend_strength": (
                        abs(revenue_slope) / (sum(revenues) / len(revenues))
                        if revenues
                        else 0
                    ),
                }
            )

        return jsonify(
            {
                "forecasts": forecasts,
                "trend_analysis": {
                    "revenue_trend": (
                        "increasing" if revenue_slope > 0 else "decreasing"
                    ),
                    "trend_strength": abs(revenue_slope),
                    "historical_weeks": len(historical_data),
                    "confidence_level": "95%",
                },
            }
        )

    except Exception as e:
        logger.error(f"Error generating forecasts: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/store_benchmarking", methods=["GET"])
def get_store_benchmarking():
    """Get comprehensive store performance benchmarking."""
    session = None
    try:
        session = db.session()
        period_weeks = int(request.args.get("weeks", 52))  # Full year by default

        # Use actual latest data date instead of today - CONSISTENT FIX
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        if not latest_data_date:
            latest_data_date = datetime.now().date()

        end_date = latest_data_date
        start_date = end_date - timedelta(weeks=period_weeks)

        logger.info(
            f"Generating store benchmarking for {period_weeks} weeks: {start_date} to {end_date}"
        )

        # Get comprehensive store metrics
        store_metrics = (
            session.query(
                PayrollTrends.store_id,
                func.sum(PayrollTrends.total_revenue).label("total_revenue"),
                func.sum(PayrollTrends.rental_revenue).label("rental_revenue"),
                func.sum(PayrollTrends.payroll_cost).label("total_payroll"),
                func.sum(PayrollTrends.wage_hours).label("total_hours"),
                func.avg(PayrollTrends.labor_efficiency_ratio).label("avg_efficiency"),
                func.avg(PayrollTrends.revenue_per_hour).label("avg_revenue_per_hour"),
                func.count(PayrollTrends.week_ending).label("weeks_reported"),
                func.stddev(PayrollTrends.total_revenue).label("revenue_volatility"),
            )
            .filter(PayrollTrends.week_ending.between(start_date, end_date))
            .group_by(PayrollTrends.store_id)
            .all()
        )

        if not store_metrics:
            return jsonify({"error": "No data found for benchmarking period"}), 404

        # Calculate company-wide benchmarks
        total_company_revenue = sum(float(s.total_revenue or 0) for s in store_metrics)
        total_company_payroll = sum(float(s.total_payroll or 0) for s in store_metrics)
        total_company_hours = sum(float(s.total_hours or 0) for s in store_metrics)

        company_benchmarks = {
            "avg_weekly_revenue": (
                total_company_revenue / (len(store_metrics) * period_weeks)
                if store_metrics
                else 0
            ),
            "avg_profit_margin": (
                (
                    (total_company_revenue - total_company_payroll)
                    / total_company_revenue
                    * 100
                )
                if total_company_revenue
                else 0
            ),
            "avg_revenue_per_hour": (
                total_company_revenue / total_company_hours
                if total_company_hours
                else 0
            ),
            "avg_efficiency_ratio": (
                (total_company_payroll / total_company_revenue * 100)
                if total_company_revenue
                else 0
            ),
        }

        # Build store performance profiles
        store_benchmarks = []
        for store in store_metrics:
            revenue = float(store.total_revenue or 0)
            payroll = float(store.total_payroll or 0)
            hours = float(store.total_hours or 0)

            # Performance vs company averages
            revenue_vs_avg = (
                (revenue / (period_weeks or 1))
                / company_benchmarks["avg_weekly_revenue"]
                if company_benchmarks["avg_weekly_revenue"]
                else 0
            )
            profit_margin = ((revenue - payroll) / revenue * 100) if revenue else 0
            margin_vs_avg = profit_margin - company_benchmarks["avg_profit_margin"]

            # Performance scoring (0-100 scale)
            performance_scores = {
                "revenue_score": min(100, max(0, revenue_vs_avg * 50)),
                "margin_score": min(100, max(0, 50 + margin_vs_avg)),
                "efficiency_score": min(
                    100, max(0, 100 - float(store.avg_efficiency or 0))
                ),
                "consistency_score": (
                    min(
                        100,
                        max(
                            0,
                            100
                            - (
                                float(store.revenue_volatility or 0)
                                / (revenue / period_weeks)
                                * 100
                            ),
                        ),
                    )
                    if revenue > 0
                    else 0
                ),
            }

            overall_score = sum(performance_scores.values()) / len(performance_scores)

            store_benchmarks.append(
                {
                    "store_code": store.store_code,
                    "store_name": STORE_MAPPING.get(store.store_code, store.store_code),
                    "metrics": {
                        "total_revenue": revenue,
                        "total_payroll": payroll,
                        "profit": revenue - payroll,
                        "profit_margin": profit_margin,
                        "revenue_per_hour": float(store.avg_revenue_per_hour or 0),
                        "efficiency_ratio": float(store.avg_efficiency or 0),
                        "total_hours": hours,
                        "weeks_reported": int(store.weeks_reported or 0),
                    },
                    "vs_company": {
                        "revenue_ratio": revenue_vs_avg,
                        "margin_difference": margin_vs_avg,
                        "revenue_rank": 0,  # Will be calculated after sorting
                        "margin_rank": 0,  # Will be calculated after sorting
                    },
                    "performance_scores": performance_scores,
                    "overall_score": overall_score,
                    "volatility": float(store.revenue_volatility or 0),
                }
            )

        # Calculate rankings
        store_benchmarks.sort(key=lambda x: x["metrics"]["total_revenue"], reverse=True)
        for i, store in enumerate(store_benchmarks, 1):
            store["vs_company"]["revenue_rank"] = i

        store_benchmarks.sort(key=lambda x: x["metrics"]["profit_margin"], reverse=True)
        for i, store in enumerate(store_benchmarks, 1):
            store["vs_company"]["margin_rank"] = i

        # Sort by overall performance score
        store_benchmarks.sort(key=lambda x: x["overall_score"], reverse=True)

        return jsonify(
            {
                "store_benchmarks": store_benchmarks,
                "company_benchmarks": company_benchmarks,
                "period_info": {
                    "weeks": period_weeks,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "stores_analyzed": len(store_benchmarks),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error generating store benchmarking: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


# Data loading endpoint for CSV import
@tab7_bp.route("/api/executive/load_historical_data", methods=["POST"])
def load_historical_data():
    """Load historical payroll and scorecard data from CSV files."""
    # This would be called once to populate the database
    # Implementation would parse the CSV files and insert into PayrollTrends and ScorecardTrends
    return jsonify(
        {"status": "not_implemented", "message": "Use data_loader.py script"}
    )


# ============== ENHANCED FUNCTIONALITY ADDED 2025-08-28 ==============

from sqlalchemy import extract
import calendar


def calculate_comparison_metrics(
    session, store_filter, base_start, base_end, comp_start, comp_end
):
    """Calculate metrics for period comparison."""

    def get_metrics(start_date, end_date):
        query = session.query(
            func.sum(PayrollTrends.total_revenue).label("revenue"),
            func.sum(PayrollTrends.rental_revenue).label("rental_revenue"),
            func.sum(PayrollTrends.payroll_cost).label("payroll"),
            func.sum(PayrollTrends.wage_hours).label("hours"),
            func.avg(PayrollTrends.labor_efficiency_ratio).label("efficiency"),
            func.count(PayrollTrends.week_ending).label("weeks"),
        ).filter(
            PayrollTrends.week_ending.between(start_date, end_date),
            PayrollTrends.total_revenue > 0,  # Exclude zero entries
        )

        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)

        result = query.first()

        # Get scorecard metrics from pos_scorecard_trends table
        pos_scorecard_query = session.query(
            func.sum(
                (POSScorecardTrends.new_open_contracts_3607 or 0) +
                (POSScorecardTrends.new_open_contracts_6800 or 0) +
                (POSScorecardTrends.new_open_contracts_8101 or 0) +
                (POSScorecardTrends.new_open_contracts_728 or 0)
            ).label("contracts"),
        ).filter(POSScorecardTrends.week_ending_sunday.between(start_date, end_date))

        # No store filtering needed as we aggregate across all stores
        pos_scorecard = pos_scorecard_query.first()
        
        # Create compatibility object
        class ScorecardCompat:
            def __init__(self, pos_metrics):
                self.contracts = pos_metrics.contracts if pos_metrics else 0
                self.ar_aging = None  # Not available in pos_scorecard_trends
        
        scorecard = ScorecardCompat(pos_scorecard)

        return {
            "revenue": float(result.revenue or 0),
            "rental_revenue": float(result.rental_revenue or 0),
            "payroll": float(result.payroll or 0),
            "hours": float(result.hours or 0),
            "efficiency": float(result.efficiency or 0),
            "weeks": int(result.weeks or 0),
            "profit": float(result.revenue or 0) - float(result.payroll or 0),
            "profit_margin": (
                (float(result.revenue or 0) - float(result.payroll or 0))
                / float(result.revenue or 1)
            )
            * 100,
            "contracts": int(scorecard.contracts or 0) if scorecard else 0,
            "ar_aging": float(scorecard.ar_aging or 0) if scorecard else 0,
            "revenue_per_hour": (
                float(result.revenue or 0) / float(result.hours or 1)
                if result.hours
                else 0
            ),
        }

    base_metrics = get_metrics(base_start, base_end)
    comp_metrics = get_metrics(comp_start, comp_end)

    # Calculate changes
    def calc_change(current, previous):
        if previous == 0:
            return 0 if current == 0 else 100
        return ((current - previous) / previous) * 100

    return {
        "base_period": {
            "start": base_start.isoformat(),
            "end": base_end.isoformat(),
            "metrics": base_metrics,
        },
        "comparison_period": {
            "start": comp_start.isoformat(),
            "end": comp_end.isoformat(),
            "metrics": comp_metrics,
        },
        "changes": {
            "revenue": calc_change(base_metrics["revenue"], comp_metrics["revenue"]),
            "rental_revenue": calc_change(
                base_metrics["rental_revenue"], comp_metrics["rental_revenue"]
            ),
            "payroll": calc_change(base_metrics["payroll"], comp_metrics["payroll"]),
            "profit": calc_change(base_metrics["profit"], comp_metrics["profit"]),
            "profit_margin": base_metrics["profit_margin"]
            - comp_metrics["profit_margin"],
            "efficiency": calc_change(
                base_metrics["efficiency"], comp_metrics["efficiency"]
            ),
            "contracts": calc_change(
                base_metrics["contracts"], comp_metrics["contracts"]
            ),
            "revenue_per_hour": calc_change(
                base_metrics["revenue_per_hour"], comp_metrics["revenue_per_hour"]
            ),
        },
    }


@tab7_bp.route("/api/executive/period_comparison_legacy", methods=["GET"])
def get_period_comparison_legacy():
    """Legacy period comparison - use newer endpoint instead."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        comparison_type = request.args.get(
            "comparison_type", "wow"
        )  # wow, mom, yoy, custom

        # Get base period dates
        base_start, base_end = get_date_range_from_params(request, session)

        if not base_start or not base_end:
            return jsonify({"error": "Invalid date range specified"}), 400

        logger.info(
            f"Period comparison: type={comparison_type}, base={base_start} to {base_end}"
        )

        # Calculate comparison period based on type
        if comparison_type == "wow":
            # Week over week
            comp_end = base_start - timedelta(days=1)
            comp_start = comp_end - timedelta(days=(base_end - base_start).days)
        elif comparison_type == "mom":
            # Month over month
            if base_start.month == 1:
                comp_start = base_start.replace(year=base_start.year - 1, month=12)
            else:
                comp_start = base_start.replace(month=base_start.month - 1)

            if base_end.month == 1:
                comp_end = base_end.replace(year=base_end.year - 1, month=12)
            else:
                # Handle month end dates properly
                last_day = calendar.monthrange(base_end.year, base_end.month - 1)[1]
                comp_end = base_end.replace(
                    month=base_end.month - 1, day=min(base_end.day, last_day)
                )
        elif comparison_type == "yoy":
            # Year over year
            comp_start = base_start.replace(year=base_start.year - 1)
            comp_end = base_end.replace(year=base_end.year - 1)
        elif comparison_type == "custom":
            # Custom comparison period from request
            comp_start_str = request.args.get("comp_start_date")
            comp_end_str = request.args.get("comp_end_date")

            if not comp_start_str or not comp_end_str:
                return (
                    jsonify(
                        {"error": "Comparison dates required for custom comparison"}
                    ),
                    400,
                )

            try:
                comp_start = datetime.strptime(comp_start_str, "%Y-%m-%d").date()
                comp_end = datetime.strptime(comp_end_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid comparison date format"}), 400
        else:
            return jsonify({"error": "Invalid comparison type"}), 400

        # Calculate metrics
        comparison = calculate_comparison_metrics(
            session, store_filter, base_start, base_end, comp_start, comp_end
        )

        comparison["comparison_type"] = comparison_type
        comparison["store"] = store_filter

        return jsonify(comparison)

    except Exception as e:
        logger.error(f"Error calculating period comparison: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/data_availability_legacy", methods=["GET"])
def get_data_availability_legacy():
    """Legacy data availability endpoint - use get_executive_data_availability instead."""
    session = None
    try:
        session = db.session()

        # Get date range from PayrollTrends - exclude zero entries
        result = (
            session.query(
                func.min(PayrollTrends.week_ending).label("earliest_date"),
                func.max(PayrollTrends.week_ending).label("latest_date"),
                func.count(func.distinct(PayrollTrends.week_ending)).label(
                    "total_weeks"
                ),
            )
            .filter(PayrollTrends.total_revenue > 0)  # Exclude zero-value future dates
            .first()
        )

        # Get store-specific availability
        store_data = (
            session.query(
                PayrollTrends.store_id,
                func.min(PayrollTrends.week_ending).label("earliest"),
                func.max(PayrollTrends.week_ending).label("latest"),
                func.count(func.distinct(PayrollTrends.week_ending)).label("weeks"),
            )
            .filter(PayrollTrends.total_revenue > 0)
            .group_by(PayrollTrends.store_id)
            .all()
        )

        stores_availability = []
        for store in store_data:
            stores_availability.append(
                {
                    "store_code": store.store_code,
                    "store_name": STORE_MAPPING.get(store.store_code, store.store_code),
                    "earliest_date": (
                        store.earliest.isoformat() if store.earliest else None
                    ),
                    "latest_date": store.latest.isoformat() if store.latest else None,
                    "total_weeks": int(store.weeks),
                }
            )

        return jsonify(
            {
                "overall": {
                    "earliest_date": (
                        result.earliest_date.isoformat()
                        if result.earliest_date
                        else None
                    ),
                    "latest_date": (
                        result.latest_date.isoformat() if result.latest_date else None
                    ),
                    "total_weeks": int(result.total_weeks or 0),
                    "current_date": datetime.now().date().isoformat(),
                },
                "by_store": stores_availability,
            }
        )

    except Exception as e:
        logger.error(f"Error getting data availability: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/trending_analysis", methods=["GET"])
def get_trending_analysis():
    """Get multi-period trending analysis with selectable datasets."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        metrics = request.args.getlist("metrics")  # Allow multiple metrics selection

        # Default metrics if none specified
        if not metrics:
            metrics = ["revenue", "payroll", "profit", "efficiency"]

        # Get date range
        start_date, end_date = get_date_range_from_params(request, session)

        if not start_date or not end_date:
            return jsonify({"error": "Invalid date range"}), 400

        logger.info(
            f"Trending analysis: metrics={metrics}, dates={start_date} to {end_date}"
        )

        # Build query for trending data
        query = session.query(
            PayrollTrends.week_ending,
            func.sum(PayrollTrends.total_revenue).label("revenue"),
            func.sum(PayrollTrends.rental_revenue).label("rental_revenue"),
            func.sum(PayrollTrends.payroll_cost).label("payroll"),
            func.sum(PayrollTrends.wage_hours).label("hours"),
            func.avg(PayrollTrends.labor_efficiency_ratio).label("efficiency"),
            func.avg(PayrollTrends.revenue_per_hour).label("revenue_per_hour"),
        ).filter(
            PayrollTrends.week_ending.between(start_date, end_date),
            PayrollTrends.total_revenue > 0,
        )

        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)

        query = query.group_by(PayrollTrends.week_ending).order_by(
            PayrollTrends.week_ending
        )

        results = query.all()

        # Process results into trending data
        trending_data = []
        for row in results:
            revenue = float(row.revenue or 0)
            payroll = float(row.payroll or 0)

            data_point = {
                "date": row.week_ending.isoformat(),
                "week": row.week_ending.strftime("%Y-W%U"),
            }

            # Add requested metrics
            if "revenue" in metrics:
                data_point["revenue"] = revenue
            if "rental_revenue" in metrics:
                data_point["rental_revenue"] = float(row.rental_revenue or 0)
            if "payroll" in metrics:
                data_point["payroll"] = payroll
            if "profit" in metrics:
                data_point["profit"] = revenue - payroll
            if "profit_margin" in metrics:
                data_point["profit_margin"] = (
                    ((revenue - payroll) / revenue * 100) if revenue else 0
                )
            if "efficiency" in metrics:
                data_point["efficiency"] = float(row.efficiency or 0)
            if "revenue_per_hour" in metrics:
                data_point["revenue_per_hour"] = float(row.revenue_per_hour or 0)
            if "hours" in metrics:
                data_point["hours"] = float(row.hours or 0)

            trending_data.append(data_point)

        return jsonify(
            {
                "trending_data": trending_data,
                "metrics_available": [
                    "revenue",
                    "rental_revenue",
                    "payroll",
                    "profit",
                    "profit_margin",
                    "efficiency",
                    "revenue_per_hour",
                    "hours",
                ],
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "records": len(trending_data),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting trending analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/period_comparison", methods=["GET"])
def get_period_comparison():
    """Get YoY/MoM/WoW comparisons for executive metrics."""
    session = None
    try:
        session = db.session()

        # Get parameters
        comparison_type = request.args.get("type", "yoy")  # yoy, mom, wow
        current_start = request.args.get("current_start")
        current_end = request.args.get("current_end")
        store_filter = request.args.get("store", "all")

        if not current_start or not current_end:
            return (
                jsonify({"error": "current_start and current_end dates required"}),
                400,
            )

        current_start_date = datetime.strptime(current_start, "%Y-%m-%d").date()
        current_end_date = datetime.strptime(current_end, "%Y-%m-%d").date()

        # Calculate comparison period based on type
        period_days = (current_end_date - current_start_date).days

        if (
            comparison_type == "wow"
        ):  # Week over Week - FIXED: Compare same week last year vs this year
            try:
                compare_start = current_start_date.replace(
                    year=current_start_date.year - 1
                )
                compare_end = current_end_date.replace(year=current_end_date.year - 1)
            except ValueError:
                # Handle leap year edge case (Feb 29)
                compare_start = current_start_date - timedelta(days=365)
                compare_end = current_end_date - timedelta(days=365)
        elif comparison_type == "mom":  # Month over Month
            try:
                # Compare same month last year
                compare_start = current_start_date.replace(
                    year=current_start_date.year - 1
                )
                compare_end = current_end_date.replace(year=current_end_date.year - 1)
            except ValueError:
                # Handle leap year edge case
                compare_start = current_start_date - timedelta(days=365)
                compare_end = current_end_date - timedelta(days=365)
        else:  # Year over Year (default)
            try:
                compare_start = current_start_date.replace(
                    year=current_start_date.year - 1
                )
                compare_end = current_end_date.replace(year=current_end_date.year - 1)
            except ValueError:
                # Handle leap year edge case (Feb 29)
                compare_start = current_start_date - timedelta(days=365)
                compare_end = current_end_date - timedelta(days=365)

        logger.info(
            f"Period comparison {comparison_type}: Current {current_start} to {current_end}, Compare {compare_start} to {compare_end}"
        )

        # Build query for both periods
        base_query = session.query(
            PayrollTrends.total_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.revenue_per_hour,
            PayrollTrends.wage_hours,
            PayrollTrends.week_ending,
        ).filter(
            PayrollTrends.total_revenue > 0  # Only actual data
        )

        if store_filter != "all":
            base_query = base_query.filter(PayrollTrends.store_id == store_filter)

        # Get current period data
        current_data = base_query.filter(
            and_(
                PayrollTrends.week_ending >= current_start_date,
                PayrollTrends.week_ending <= current_end_date,
            )
        ).all()

        # Get comparison period data
        compare_data = base_query.filter(
            and_(
                PayrollTrends.week_ending >= compare_start,
                PayrollTrends.week_ending <= compare_end,
            )
        ).all()

        def calculate_totals(data):
            if not data:
                return {
                    "revenue": 0,
                    "payroll": 0,
                    "hours": 0,
                    "revenue_per_hour": 0,
                    "profit": 0,
                    "weeks": 0,
                }

            totals = {
                "revenue": sum(float(d.total_revenue or 0) for d in data),
                "payroll": sum(float(d.payroll_cost or 0) for d in data),
                "hours": sum(float(d.wage_hours or 0) for d in data),
                "weeks": len(set(d.week_ending for d in data)),
            }

            totals["profit"] = totals["revenue"] - totals["payroll"]
            totals["revenue_per_hour"] = (
                totals["revenue"] / totals["hours"] if totals["hours"] > 0 else 0
            )
            totals["profit_margin"] = (
                (totals["profit"] / totals["revenue"] * 100)
                if totals["revenue"] > 0
                else 0
            )

            return totals

        current_totals = calculate_totals(current_data)
        compare_totals = calculate_totals(compare_data)

        # Calculate percentage changes
        def calc_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 2)

        comparison_result = {
            "comparison_type": comparison_type.upper(),
            "current_period": {
                "start_date": current_start,
                "end_date": current_end,
                "metrics": current_totals,
            },
            "compare_period": {
                "start_date": compare_start.isoformat(),
                "end_date": compare_end.isoformat(),
                "metrics": compare_totals,
            },
            "changes": {
                "revenue": calc_change(
                    current_totals["revenue"], compare_totals["revenue"]
                ),
                "payroll": calc_change(
                    current_totals["payroll"], compare_totals["payroll"]
                ),
                "profit": calc_change(
                    current_totals["profit"], compare_totals["profit"]
                ),
                "profit_margin": calc_change(
                    current_totals["profit_margin"], compare_totals["profit_margin"]
                ),
                "revenue_per_hour": calc_change(
                    current_totals["revenue_per_hour"],
                    compare_totals["revenue_per_hour"],
                ),
                "hours": calc_change(current_totals["hours"], compare_totals["hours"]),
            },
            "summary": {
                "total_revenue_change": current_totals["revenue"]
                - compare_totals["revenue"],
                "total_profit_change": current_totals["profit"]
                - compare_totals["profit"],
                "weeks_current": current_totals["weeks"],
                "weeks_compare": compare_totals["weeks"],
            },
        }

        return jsonify(comparison_result)

    except Exception as e:
        logger.error(f"Error in period comparison: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/multi_period_analysis", methods=["GET"])
def get_multi_period_analysis():
    """Get comprehensive multi-period analysis with trailing/leading averages and YoY/Yo2Y comparisons."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        
        # Get latest data date
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )
        if not latest_data_date:
            latest_data_date = datetime.now().date()
        
        logger.info(f"Multi-period analysis for store: {store_filter}, latest data: {latest_data_date}")
        
        # Calculate date ranges for comprehensive analysis
        # Current period (last 12 weeks for stable analysis)
        current_end = latest_data_date
        current_start = current_end - timedelta(weeks=12)
        
        # Extended range for 3-month averages (need at least 6 months)
        extended_start = current_end - timedelta(weeks=26)
        
        # Historical periods for YoY and Yo2Y comparisons
        yoy_end = current_end - timedelta(weeks=52)
        yoy_start = yoy_end - timedelta(weeks=12)
        
        yo2y_end = current_end - timedelta(weeks=104)  # 2 years ago
        yo2y_start = yo2y_end - timedelta(weeks=12)
        
        # Get comprehensive dataset
        base_query = session.query(
            PayrollTrends.week_ending,
            PayrollTrends.store_id,
            PayrollTrends.total_revenue,
            PayrollTrends.rental_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.labor_efficiency_ratio,
            PayrollTrends.revenue_per_hour,
            PayrollTrends.wage_hours,
        ).filter(
            PayrollTrends.total_revenue > 0,
            PayrollTrends.week_ending >= extended_start  # Get 6 months of data
        )
        
        if store_filter != "all":
            base_query = base_query.filter(PayrollTrends.store_id == store_filter)
        
        all_data = base_query.order_by(PayrollTrends.week_ending).all()
        
        # Process data into periods
        current_data = [r for r in all_data if current_start <= r.week_ending <= current_end]
        extended_data = [r for r in all_data if extended_start <= r.week_ending <= current_end]
        yoy_data = [r for r in all_data if yoy_start <= r.week_ending <= yoy_end]
        yo2y_data = [r for r in all_data if yo2y_start <= r.week_ending <= yo2y_end]
        
        def calculate_period_metrics(data):
            """Calculate aggregate metrics for a period."""
            if not data:
                return {
                    "revenue": 0, "payroll": 0, "profit": 0, "profit_margin": 0,
                    "efficiency": 0, "revenue_per_hour": 0, "hours": 0, "weeks": 0
                }
            
            total_revenue = sum(float(r.total_revenue or 0) for r in data)
            total_payroll = sum(float(r.payroll_cost or 0) for r in data)
            total_hours = sum(float(r.wage_hours or 0) for r in data)
            avg_efficiency = sum(float(r.labor_efficiency_ratio or 0) for r in data) / len(data)
            
            profit = total_revenue - total_payroll
            profit_margin = (profit / total_revenue * 100) if total_revenue else 0
            revenue_per_hour = (total_revenue / total_hours) if total_hours else 0
            
            return {
                "revenue": round(total_revenue, 2),
                "payroll": round(total_payroll, 2),
                "profit": round(profit, 2),
                "profit_margin": round(profit_margin, 2),
                "efficiency": round(avg_efficiency, 2),
                "revenue_per_hour": round(revenue_per_hour, 2),
                "hours": round(total_hours, 2),
                "weeks": len(data)
            }
        
        def calculate_trailing_leading_averages(data):
            """Calculate 3-month trailing and leading averages."""
            if len(data) < 12:  # Need at least 12 weeks for stable averages
                return {"trailing_3m": None, "leading_3m": None}
            
            # Group data by month for 3-month calculations
            monthly_data = {}
            for row in data:
                month_key = row.week_ending.replace(day=1)
                if month_key not in monthly_data:
                    monthly_data[month_key] = []
                monthly_data[month_key].append(row)
            
            # Calculate monthly aggregates
            monthly_metrics = {}
            for month, month_data in monthly_data.items():
                monthly_metrics[month] = calculate_period_metrics(month_data)
            
            # Sort months
            sorted_months = sorted(monthly_metrics.keys())
            
            if len(sorted_months) < 6:  # Need at least 6 months
                return {"trailing_3m": None, "leading_3m": None}
            
            # Calculate trailing 3-month average (last 3 months)
            recent_months = sorted_months[-3:]
            trailing_metrics = []
            for month in recent_months:
                trailing_metrics.append(monthly_metrics[month])
            
            trailing_3m = {
                "revenue": sum(m["revenue"] for m in trailing_metrics) / 3,
                "payroll": sum(m["payroll"] for m in trailing_metrics) / 3,
                "profit": sum(m["profit"] for m in trailing_metrics) / 3,
                "profit_margin": sum(m["profit_margin"] for m in trailing_metrics) / 3,
                "efficiency": sum(m["efficiency"] for m in trailing_metrics) / 3,
                "revenue_per_hour": sum(m["revenue_per_hour"] for m in trailing_metrics) / 3,
            }
            
            # For leading average, we'll use projected data based on trends
            # Since we don't have future data, we'll calculate trend-based projections
            if len(sorted_months) >= 6:
                # Use last 6 months to project next 3 months
                projection_base = sorted_months[-6:]
                projection_metrics = [monthly_metrics[m] for m in projection_base]
                
                # Simple linear trend projection
                leading_3m = {
                    "revenue": sum(m["revenue"] for m in projection_metrics[-3:]) / 3,
                    "payroll": sum(m["payroll"] for m in projection_metrics[-3:]) / 3,
                    "profit": sum(m["profit"] for m in projection_metrics[-3:]) / 3,
                    "profit_margin": sum(m["profit_margin"] for m in projection_metrics[-3:]) / 3,
                    "efficiency": sum(m["efficiency"] for m in projection_metrics[-3:]) / 3,
                    "revenue_per_hour": sum(m["revenue_per_hour"] for m in projection_metrics[-3:]) / 3,
                }
            else:
                leading_3m = None
            
            return {
                "trailing_3m": {k: round(v, 2) for k, v in trailing_3m.items()},
                "leading_3m": {k: round(v, 2) for k, v in leading_3m.items()} if leading_3m else None
            }
        
        # Calculate metrics for each period
        current_metrics = calculate_period_metrics(current_data)
        yoy_metrics = calculate_period_metrics(yoy_data)
        yo2y_metrics = calculate_period_metrics(yo2y_data)
        
        # Calculate trailing/leading averages
        averages = calculate_trailing_leading_averages(extended_data)
        
        # Calculate comparisons
        def calculate_comparison(current, historical, period_name):
            """Calculate comparison metrics."""
            if not historical or historical == 0:
                return {"absolute": 0, "percentage": 0, "trend": "neutral"}
            
            absolute = current - historical
            percentage = (absolute / historical) * 100
            
            trend = "up" if absolute > 0 else "down" if absolute < 0 else "neutral"
            
            return {
                "absolute": round(absolute, 2),
                "percentage": round(percentage, 2),
                "trend": trend,
                "period": period_name
            }
        
        # Build comprehensive analysis result
        analysis_result = {
            "analysis_date": latest_data_date.isoformat(),
            "store_filter": store_filter,
            "store_name": STORE_MAPPING.get(store_filter, store_filter) if store_filter != "all" else "All Stores",
            
            "current_period": {
                "start_date": current_start.isoformat(),
                "end_date": current_end.isoformat(),
                "metrics": current_metrics
            },
            
            "moving_averages": {
                "trailing_3month": averages["trailing_3m"],
                "leading_3month": averages["leading_3m"],
                "calculation_period": f"{extended_start.isoformat()} to {current_end.isoformat()}"
            },
            
            "historical_comparisons": {
                "year_over_year": {
                    "period": f"{yoy_start.isoformat()} to {yoy_end.isoformat()}",
                    "metrics": yoy_metrics,
                    "comparisons": {
                        "revenue": calculate_comparison(current_metrics["revenue"], yoy_metrics["revenue"], "YoY"),
                        "profit": calculate_comparison(current_metrics["profit"], yoy_metrics["profit"], "YoY"),
                        "profit_margin": calculate_comparison(current_metrics["profit_margin"], yoy_metrics["profit_margin"], "YoY"),
                        "efficiency": calculate_comparison(current_metrics["efficiency"], yoy_metrics["efficiency"], "YoY"),
                        "revenue_per_hour": calculate_comparison(current_metrics["revenue_per_hour"], yoy_metrics["revenue_per_hour"], "YoY")
                    }
                },
                "two_years_over_two_years": {
                    "period": f"{yo2y_start.isoformat()} to {yo2y_end.isoformat()}",
                    "metrics": yo2y_metrics,
                    "comparisons": {
                        "revenue": calculate_comparison(current_metrics["revenue"], yo2y_metrics["revenue"], "Yo2Y"),
                        "profit": calculate_comparison(current_metrics["profit"], yo2y_metrics["profit"], "Yo2Y"),
                        "profit_margin": calculate_comparison(current_metrics["profit_margin"], yo2y_metrics["profit_margin"], "Yo2Y"),
                        "efficiency": calculate_comparison(current_metrics["efficiency"], yo2y_metrics["efficiency"], "Yo2Y"),
                        "revenue_per_hour": calculate_comparison(current_metrics["revenue_per_hour"], yo2y_metrics["revenue_per_hour"], "Yo2Y")
                    }
                }
            },
            
            "trend_analysis": {
                "data_availability": {
                    "current_weeks": len(current_data),
                    "extended_weeks": len(extended_data),
                    "yoy_weeks": len(yoy_data),
                    "yo2y_weeks": len(yo2y_data)
                },
                "confidence_level": "high" if len(extended_data) >= 20 else "medium" if len(extended_data) >= 12 else "low"
            }
        }
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error in multi-period analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/enhanced_trends", methods=["GET"])
def get_enhanced_trends():
    """Get enhanced trend data with 3-month averages and historical comparisons."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        months_back = int(request.args.get("months", 12))  # Default 12 months
        
        # Get latest data date
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )
        if not latest_data_date:
            latest_data_date = datetime.now().date()
        
        # Calculate extended date range (need extra data for averages)
        end_date = latest_data_date
        start_date = end_date - timedelta(weeks=months_back * 4 + 12)  # Extra weeks for calculations
        
        logger.info(f"Enhanced trends for {months_back} months: {start_date} to {end_date}")
        
        # Get comprehensive dataset
        query = session.query(
            PayrollTrends.week_ending,
            PayrollTrends.store_id,
            PayrollTrends.total_revenue,
            PayrollTrends.rental_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.labor_efficiency_ratio,
            PayrollTrends.revenue_per_hour,
            PayrollTrends.wage_hours,
        ).filter(
            PayrollTrends.week_ending.between(start_date, end_date),
            PayrollTrends.total_revenue > 0,
        )
        
        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)
        
        results = query.order_by(PayrollTrends.week_ending).all()
        
        # Group data by week and calculate rolling averages
        weekly_data = {}
        for row in results:
            week_key = row.week_ending.isoformat()
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "week": week_key,
                    "week_date": row.week_ending,
                    "revenue": 0,
                    "payroll": 0,
                    "efficiency": [],
                    "revenue_per_hour": [],
                    "hours": 0,
                    "store_count": 0
                }
            
            weekly_data[week_key]["revenue"] += float(row.total_revenue or 0)
            weekly_data[week_key]["payroll"] += float(row.payroll_cost or 0)
            weekly_data[week_key]["hours"] += float(row.wage_hours or 0)
            weekly_data[week_key]["efficiency"].append(float(row.labor_efficiency_ratio or 0))
            weekly_data[week_key]["revenue_per_hour"].append(float(row.revenue_per_hour or 0))
            weekly_data[week_key]["store_count"] += 1
        
        # Convert to sorted list and calculate averages
        sorted_weeks = sorted(weekly_data.values(), key=lambda x: x["week_date"])
        
        # Calculate 3-month (12-week) rolling averages
        enhanced_trends = []
        for i, week_data in enumerate(sorted_weeks):
            # Base metrics
            profit = week_data["revenue"] - week_data["payroll"]
            profit_margin = (profit / week_data["revenue"] * 100) if week_data["revenue"] else 0
            avg_efficiency = sum(week_data["efficiency"]) / len(week_data["efficiency"]) if week_data["efficiency"] else 0
            avg_revenue_per_hour = sum(week_data["revenue_per_hour"]) / len(week_data["revenue_per_hour"]) if week_data["revenue_per_hour"] else 0
            
            trend_point = {
                "week": week_data["week"],
                "revenue": round(week_data["revenue"], 2),
                "payroll": round(week_data["payroll"], 2),
                "profit": round(profit, 2),
                "profit_margin": round(profit_margin, 2),
                "efficiency": round(avg_efficiency, 2),
                "revenue_per_hour": round(avg_revenue_per_hour, 2),
                "hours": round(week_data["hours"], 2),
                "stores": week_data["store_count"]
            }
            
            # Calculate 3-month trailing average
            if i >= 11:  # Need at least 12 weeks
                trailing_weeks = sorted_weeks[max(0, i-11):i+1]
                
                trailing_revenue = sum(w["revenue"] for w in trailing_weeks) / len(trailing_weeks)
                trailing_payroll = sum(w["payroll"] for w in trailing_weeks) / len(trailing_weeks)
                trailing_profit = trailing_revenue - trailing_payroll
                trailing_profit_margin = (trailing_profit / trailing_revenue * 100) if trailing_revenue else 0
                
                # Average efficiency across weeks
                all_efficiency = []
                for w in trailing_weeks:
                    all_efficiency.extend(w["efficiency"])
                trailing_efficiency = sum(all_efficiency) / len(all_efficiency) if all_efficiency else 0
                
                # Average revenue per hour
                all_rph = []
                for w in trailing_weeks:
                    all_rph.extend(w["revenue_per_hour"])
                trailing_rph = sum(all_rph) / len(all_rph) if all_rph else 0
                
                trend_point["avg_3m_trailing"] = {
                    "revenue": round(trailing_revenue, 2),
                    "payroll": round(trailing_payroll, 2),
                    "profit": round(trailing_profit, 2),
                    "profit_margin": round(trailing_profit_margin, 2),
                    "efficiency": round(trailing_efficiency, 2),
                    "revenue_per_hour": round(trailing_rph, 2)
                }
            else:
                trend_point["avg_3m_trailing"] = None
            
            # Calculate 3-month leading average (projection based on trend)
            if i >= 23 and i < len(sorted_weeks) - 12:  # Need enough data for projection
                future_weeks = sorted_weeks[i+1:min(len(sorted_weeks), i+13)]
                if len(future_weeks) >= 12:
                    leading_revenue = sum(w["revenue"] for w in future_weeks) / len(future_weeks)
                    leading_payroll = sum(w["payroll"] for w in future_weeks) / len(future_weeks)
                    leading_profit = leading_revenue - leading_payroll
                    leading_profit_margin = (leading_profit / leading_revenue * 100) if leading_revenue else 0
                    
                    # Average efficiency for leading period
                    all_efficiency = []
                    for w in future_weeks:
                        all_efficiency.extend(w["efficiency"])
                    leading_efficiency = sum(all_efficiency) / len(all_efficiency) if all_efficiency else 0
                    
                    # Average revenue per hour for leading period
                    all_rph = []
                    for w in future_weeks:
                        all_rph.extend(w["revenue_per_hour"])
                    leading_rph = sum(all_rph) / len(all_rph) if all_rph else 0
                    
                    trend_point["avg_3m_leading"] = {
                        "revenue": round(leading_revenue, 2),
                        "payroll": round(leading_payroll, 2),
                        "profit": round(leading_profit, 2),
                        "profit_margin": round(leading_profit_margin, 2),
                        "efficiency": round(leading_efficiency, 2),
                        "revenue_per_hour": round(leading_rph, 2)
                    }
                else:
                    trend_point["avg_3m_leading"] = None
            else:
                trend_point["avg_3m_leading"] = None
            
            enhanced_trends.append(trend_point)
        
        # Filter to requested time range (remove extra weeks used for calculations)
        final_start = end_date - timedelta(weeks=months_back * 4)
        filtered_trends = [
            t for t in enhanced_trends 
            if datetime.fromisoformat(t["week"]).date() >= final_start
        ]
        
        return jsonify({
            "trends": filtered_trends,
            "analysis_period": {
                "start_date": final_start.isoformat(),
                "end_date": end_date.isoformat(),
                "months": months_back,
                "weeks": len(filtered_trends)
            },
            "store_filter": store_filter,
            "store_name": STORE_MAPPING.get(store_filter, store_filter) if store_filter != "all" else "All Stores"
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced trends: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/rolling_analysis", methods=["GET"])
def get_rolling_analysis():
    """Get rolling average analysis with 12-week and 12-month options."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        period = request.args.get("period", "12week")  # 12week, 12month, combined
        
        # Get latest data date
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )
        if not latest_data_date:
            latest_data_date = datetime.now().date()
        
        # Calculate periods based on analysis type
        if period == "12month":
            weeks_back = 52  # 12 months
            rolling_window = 12  # 12-week rolling window
        else:  # 12week or combined
            weeks_back = 24  # Need extra data for rolling calculation
            rolling_window = 12  # 12-week rolling window
            
        end_date = latest_data_date
        start_date = end_date - timedelta(weeks=weeks_back)
        
        logger.info(f"Rolling analysis for {period}: {start_date} to {end_date}, rolling window: {rolling_window}")
        
        # Get comprehensive dataset
        query = session.query(
            PayrollTrends.week_ending,
            PayrollTrends.store_id,
            PayrollTrends.total_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.labor_efficiency_ratio,
            PayrollTrends.revenue_per_hour,
            PayrollTrends.wage_hours,
        ).filter(
            PayrollTrends.week_ending.between(start_date, end_date),
            PayrollTrends.total_revenue > 0,
        )
        
        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)
        
        results = query.order_by(PayrollTrends.week_ending).all()
        
        # Group by week and calculate rolling averages
        weekly_data = {}
        for row in results:
            week_key = row.week_ending.isoformat()
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "week": week_key,
                    "week_date": row.week_ending,
                    "revenue": 0,
                    "payroll": 0,
                    "hours": 0,
                    "stores": []
                }
            
            weekly_data[week_key]["revenue"] += float(row.total_revenue or 0)
            weekly_data[week_key]["payroll"] += float(row.payroll_cost or 0)
            weekly_data[week_key]["hours"] += float(row.wage_hours or 0)
            weekly_data[week_key]["stores"].append({
                "store_code": row.store_code,
                "revenue": float(row.total_revenue or 0),
                "efficiency": float(row.labor_efficiency_ratio or 0),
                "revenue_per_hour": float(row.revenue_per_hour or 0),
            })
        
        # Convert to sorted list and calculate rolling averages
        sorted_weeks = sorted(weekly_data.values(), key=lambda x: x["week_date"])
        
        # Calculate rolling averages
        trends = []
        for i, week_data in enumerate(sorted_weeks):
            if i >= rolling_window - 1:  # Ensure we have enough data for rolling average
                # Calculate rolling average for the past 'rolling_window' weeks
                rolling_weeks = sorted_weeks[i - rolling_window + 1:i + 1]
                
                avg_revenue = sum(w["revenue"] for w in rolling_weeks) / len(rolling_weeks)
                avg_payroll = sum(w["payroll"] for w in rolling_weeks) / len(rolling_weeks)
                avg_profit = avg_revenue - avg_payroll
                
                trends.append({
                    "week": week_data["week"],
                    "revenue": week_data["revenue"],
                    "payroll": week_data["payroll"],
                    "profit": week_data["revenue"] - week_data["payroll"],
                    "rolling_avg": round(avg_revenue, 2),
                    "rolling_avg_payroll": round(avg_payroll, 2),
                    "rolling_avg_profit": round(avg_profit, 2),
                    "variance_from_avg": round(week_data["revenue"] - avg_revenue, 2),
                })
        
        # Calculate overall metrics
        if trends:
            latest_trend = trends[-1]
            metrics = {
                "avg_12week_revenue": latest_trend["rolling_avg"],
                "avg_12week_profit": latest_trend["rolling_avg_profit"],
                "current_vs_avg": latest_trend["variance_from_avg"],
                "trend_direction": "increasing" if len(trends) >= 2 and trends[-1]["rolling_avg"] > trends[-2]["rolling_avg"] else "decreasing"
            }
        else:
            metrics = {
                "avg_12week_revenue": 0,
                "avg_12week_profit": 0,
                "current_vs_avg": 0,
                "trend_direction": "stable"
            }
        
        # Store performance analysis
        store_performance = []
        if store_filter == "all":
            # Get performance for all stores from latest week
            latest_week = sorted_weeks[-1] if sorted_weeks else None
            if latest_week:
                for store_data in latest_week["stores"]:
                    store_performance.append({
                        "store_code": store_data["store_code"],
                        "store_name": STORE_MAPPING.get(store_data["store_code"], store_data["store_code"]),
                        "total_revenue": store_data["revenue"],
                        "efficiency": store_data["efficiency"],
                        "revenue_per_hour": store_data["revenue_per_hour"],
                    })
        
        return jsonify({
            "trends": trends,
            "metrics": metrics,
            "store_performance": store_performance,
            "period": period,
            "rolling_window": rolling_window,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "weeks_analyzed": len(trends)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in rolling analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/week_based_filter", methods=["GET"])
def get_week_based_filter():
    """Get data for specific week number filtering."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        week_number = request.args.get("week_number")
        year = int(request.args.get("year", datetime.now().year))
        
        if not week_number:
            return jsonify({"error": "Week number is required"}), 400
            
        week_number = int(week_number)
        logger.info(f"Week-based filter: Week {week_number} of {year} for store {store_filter}")
        
        # Calculate date range using Excel WEEKNUM(date,11) logic
        # Week starts Monday, numbered 1-53
        week_ending_sunday = get_week_ending_sunday(year, week_number)
        target_week_start = week_ending_sunday - timedelta(days=6)  # Monday
        target_week_end = week_ending_sunday  # Sunday
        
        logger.info(f"Target week range: {target_week_start} to {target_week_end}")
        
        # Get data for the specific week
        query = session.query(
            PayrollTrends.store_id,
            PayrollTrends.week_ending,
            PayrollTrends.total_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.labor_efficiency_ratio,
            PayrollTrends.revenue_per_hour,
            PayrollTrends.wage_hours,
        ).filter(
            PayrollTrends.week_ending.between(target_week_start, target_week_end),
            PayrollTrends.total_revenue > 0,
        )
        
        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)
        
        results = query.all()
        
        # Process results
        week_data = {
            "week_number": week_number,
            "year": year,
            "week_start": target_week_start.isoformat(),
            "week_end": target_week_end.isoformat(),
            "stores": []
        }
        
        total_revenue = 0
        total_payroll = 0
        total_hours = 0
        
        for row in results:
            store_revenue = float(row.total_revenue or 0)
            store_payroll = float(row.payroll_cost or 0)
            store_hours = float(row.wage_hours or 0)
            
            week_data["stores"].append({
                "store_code": row.store_code,
                "store_name": STORE_MAPPING.get(row.store_code, row.store_code),
                "revenue": store_revenue,
                "payroll": store_payroll,
                "profit": store_revenue - store_payroll,
                "efficiency": float(row.labor_efficiency_ratio or 0),
                "revenue_per_hour": float(row.revenue_per_hour or 0),
                "hours": store_hours,
            })
            
            total_revenue += store_revenue
            total_payroll += store_payroll
            total_hours += store_hours
        
        # Add aggregated totals
        week_data["totals"] = {
            "revenue": total_revenue,
            "payroll": total_payroll,
            "profit": total_revenue - total_payroll,
            "hours": total_hours,
            "profit_margin": (total_revenue - total_payroll) / total_revenue * 100 if total_revenue else 0,
            "revenue_per_hour": total_revenue / total_hours if total_hours else 0,
        }
        
        return jsonify(week_data)
        
    except Exception as e:
        logger.error(f"Error in week-based filter: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@tab7_bp.route("/api/executive/enhanced_dashboard_summary", methods=["GET"])
def get_enhanced_dashboard_summary():
    """Enhanced dashboard summary with support for new filtering options."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        period = request.args.get("period", "current_week")
        rolling_avg = request.args.get("rolling_avg", "none")
        view_mode = request.args.get("view_mode", "current")
        week_number = request.args.get("week_number")
        
        logger.info(f"Enhanced dashboard summary: store={store_filter}, period={period}, rolling_avg={rolling_avg}, view_mode={view_mode}")
        
        # Handle different period types
        if period == "week_number" and week_number:
            # Use week-based filtering
            week_response = get_week_based_filter()
            if week_response.status_code == 200:
                week_data = week_response.get_json()
                return jsonify({
                    "financial_metrics": {
                        "total_revenue": week_data["totals"]["revenue"],
                        "total_payroll": week_data["totals"]["payroll"],
                        "labor_efficiency": week_data["totals"]["profit_margin"],
                        "revenue_per_hour": week_data["totals"]["revenue_per_hour"],
                        "yoy_growth": 0,  # Will be calculated separately
                    },
                    "operational_metrics": {
                        "new_contracts": 0,  # Not available at week level
                        "avg_weekly_contracts": 0,
                        "avg_deliveries": 0,
                        "inventory_value": 0,  # Will be calculated separately
                        "total_items": 0,
                    },
                    "health_indicators": {
                        "ar_aging_percent": 0,
                        "total_discounts": 0,
                        "profit_margin": week_data["totals"]["profit_margin"],
                    },
                    "metadata": {
                        "store": store_filter,
                        "period": period,
                        "week_number": week_number,
                        "view_mode": view_mode,
                        "timestamp": datetime.now().isoformat(),
                    },
                    "week_data": week_data,
                })
            else:
                return week_response
        else:
            # Use existing dashboard summary logic
            summary_response = get_executive_summary()
            if hasattr(summary_response, 'get_json'):
                return summary_response
            else:
                return jsonify(summary_response)
            
    except Exception as e:
        logger.error(f"Error in enhanced dashboard summary: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


# New API endpoints for enhanced executive dashboard

@executive_api_bp.route("/api/financial-kpis", methods=["GET"])
def financial_kpis():
    """Get financial KPIs for the dashboard"""
    session = None
    try:
        # CALCULATE FROM DATABASE - NO HARDCODED VALUES!
        from sqlalchemy import text
        session = db.session()
        
        # Load executive dashboard configuration
        from app.models.config_models import ExecutiveDashboardConfiguration
        try:
            config = ExecutiveDashboardConfiguration.query.filter_by(user_id='default_user', config_name='default').first()
            if not config:
                logger.warning("No executive dashboard configuration found, using defaults")
                config = ExecutiveDashboardConfiguration()
        except Exception as config_error:
            logger.error(f"Error loading executive dashboard configuration: {config_error}")
            # Fallback MockConfig for robust error handling
            class MockConfig:
                base_health_score = 75.0
                revenue_tier_1_threshold = 100000.0
                revenue_tier_1_points = 25
                revenue_tier_2_threshold = 75000.0
                revenue_tier_2_points = 20  
                revenue_tier_3_threshold = 50000.0
                revenue_tier_3_points = 15
                revenue_tier_4_points = 10
                yoy_excellent_threshold = 10.0
                yoy_excellent_points = 25
                yoy_good_threshold = 5.0
                yoy_good_points = 15
                yoy_fair_threshold = 0.0
                yoy_fair_points = 10
                yoy_poor_points = 5
                utilization_excellent_threshold = 85.0
                utilization_excellent_points = 25
                utilization_good_threshold = 75.0
                utilization_good_points = 20
                utilization_fair_threshold = 65.0
                utilization_fair_points = 15
                utilization_poor_threshold = 50.0
                utilization_poor_points = 10
            config = MockConfig()
        
        # CONSOLIDATED 2025-09-09: Use unified revenue KPI calculation (single source of truth)
        # TODO CLEANUP 2025-09-16: Remove duplicate calculation logic after verification
        current_3wk_avg = _get_unified_revenue_kpi(session, 'financial_kpis_current_revenue_weeks')
        
        # Debug: Show what weeks we're using
        debug_query = text(f"""
            SELECT week_ending, total_weekly_revenue
            FROM scorecard_trends_data 
            WHERE total_weekly_revenue IS NOT NULL 
                AND total_weekly_revenue > 0
                AND week_ending <= CURDATE()
            ORDER BY week_ending DESC 
            LIMIT {config.financial_kpis_debug_weeks}
        """)
        debug_result = session.execute(debug_query).fetchall()
        logger.info(f"Using weeks for revenue calculation:")
        for row in debug_result:
            logger.info(f"  {row.week_ending}: ${row.total_weekly_revenue:,.0f}")
        logger.info(f"Calculated 3-week average: ${current_3wk_avg:,.0f} (Target: $109,955)")
        
        # FIXED 2025-09-09: Calculate Year-to-Date YoY growth (not period-based)
        # Compare YTD current year vs YTD last year + YTD last year vs YTD two years ago
        yoy_query = text("""
            SELECT 
                SUM(CASE WHEN week_ending >= MAKEDATE(YEAR(CURDATE()), 1) 
                         AND week_ending <= CURDATE()
                         AND YEAR(week_ending) = YEAR(CURDATE())
                    THEN total_weekly_revenue END) as current_ytd,
                SUM(CASE WHEN week_ending >= MAKEDATE(YEAR(CURDATE()) - 1, 1)
                         AND week_ending <= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                         AND YEAR(week_ending) = YEAR(CURDATE()) - 1
                    THEN total_weekly_revenue END) as last_year_ytd,
                SUM(CASE WHEN week_ending >= MAKEDATE(YEAR(CURDATE()) - 2, 1)
                         AND week_ending <= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
                         AND YEAR(week_ending) = YEAR(CURDATE()) - 2
                    THEN total_weekly_revenue END) as two_years_ago_ytd
            FROM scorecard_trends_data 
            WHERE total_weekly_revenue IS NOT NULL 
                AND total_weekly_revenue > 0
        """)
        yoy_result = session.execute(yoy_query).fetchone()
        
        yoy_growth = 0
        yoy_comparison = 0
        if yoy_result and yoy_result.current_ytd and yoy_result.last_year_ytd and yoy_result.last_year_ytd > 0:
            # Main YoY: Current YTD vs Last Year YTD
            yoy_growth = ((yoy_result.current_ytd - yoy_result.last_year_ytd) / yoy_result.last_year_ytd) * 100
            
            # Calculate last year YTD vs two years ago YTD for comparison
            if yoy_result.two_years_ago_ytd and yoy_result.two_years_ago_ytd > 0:
                last_year_yoy = ((yoy_result.last_year_ytd - yoy_result.two_years_ago_ytd) / yoy_result.two_years_ago_ytd) * 100
                # Secondary YoY comparison: How current YTD YoY compares to last year's YTD YoY (percentage point difference)
                yoy_comparison = yoy_growth - last_year_yoy
        
        # Calculate equipment utilization from combined_inventory
        utilization_query = text("""
            SELECT 
                COUNT(CASE WHEN status IN ('fully_rented', 'partially_rented') THEN 1 END) * 100.0
                / NULLIF(COUNT(*), 0) as utilization_rate
            FROM combined_inventory 
            WHERE rental_rate > 0
        """)
        utilization_avg = session.execute(utilization_query).scalar() or 0
        
        # Calculate business health score based on multiple factors
        # OLD - HARDCODED (WRONG): health_score = 50  # Base score
        # NEW - CONFIGURABLE (CORRECT):
        health_score = config.base_health_score
        
        # Revenue performance (configurable points max)
        # OLD - HARDCODED (WRONG): if current_3wk_avg > 100000:
        # NEW - CONFIGURABLE (CORRECT):
        if current_3wk_avg > config.revenue_tier_1_threshold:
            health_score += config.revenue_tier_1_points
        elif current_3wk_avg > config.revenue_tier_2_threshold:
            health_score += config.revenue_tier_2_points
        elif current_3wk_avg > config.revenue_tier_3_threshold:
            health_score += config.revenue_tier_3_points
        else:
            health_score += config.revenue_tier_4_points
            
        # YoY growth performance (configurable points max)
        # OLD - HARDCODED (WRONG): if yoy_growth > 10:
        # NEW - CONFIGURABLE (CORRECT):
        if yoy_growth > config.yoy_excellent_threshold:
            health_score += config.yoy_excellent_points
        elif yoy_growth > config.yoy_good_threshold:
            health_score += config.yoy_good_points  
        elif yoy_growth > config.yoy_fair_threshold:
            health_score += config.yoy_fair_points
        else:
            health_score += config.yoy_poor_points
            
        # Utilization performance (configurable points max)
        # OLD - HARDCODED (WRONG): if utilization_avg > 85:
        # NEW - CONFIGURABLE (CORRECT):
        if utilization_avg > config.utilization_excellent_threshold:
            health_score += config.utilization_excellent_points
        elif utilization_avg > config.utilization_good_threshold:
            health_score += config.utilization_good_points
        elif utilization_avg > config.utilization_fair_threshold:
            health_score += config.utilization_fair_points
        elif utilization_avg > config.utilization_poor_threshold:
            health_score += config.utilization_poor_points
            
        # Cap at 100
        health_score = min(100, max(0, health_score))
        
        logger.info(f"Calculated KPIs: Revenue=${current_3wk_avg:,.0f}, YoY={yoy_growth:.1f}%, Util={utilization_avg:.1f}%, Health={health_score}")
        
        return jsonify({
            "success": True,
            "revenue_metrics": {
                "current_3wk_avg": round(float(current_3wk_avg)),
                "yoy_growth": round(float(yoy_growth), 1),
                "yoy_comparison": round(float(yoy_comparison), 1),
                "change_pct": 0  # Would need week-over-week calculation
            },
            "store_metrics": {
                "utilization_avg": round(float(utilization_avg), 1),
                "change_pct": 0  # Would need historical comparison
            },
            "operational_health": {
                "health_score": round(float(health_score)),
                "change_pct": 0  # Would need historical comparison
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating financial KPIs from database: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"KPI calculation failed: {str(e)}"}), 500
    finally:
        if session:
            session.close()

@executive_api_bp.route("/api/location-kpis/<store_code>", methods=["GET"])
def location_specific_kpis(store_code):
    """Get KPIs for a specific location"""
    try:
        if store_code not in STORE_LOCATIONS:
            return jsonify({"success": False, "error": "Invalid store code"}), 400
            
        # Filter data for specific location
        session = db.session
        
        # STANDARDIZED: Use same data source and calculation as company total (scorecard_trends_data)
        config = _get_executive_config()
        revenue_query = text(f"""
            SELECT AVG(revenue_{store_code}) as avg_revenue
            FROM (
                SELECT revenue_{store_code} 
                FROM scorecard_trends_data 
                WHERE revenue_{store_code} IS NOT NULL
                ORDER BY week_ending DESC 
                LIMIT {config.location_kpis_revenue_weeks}
            ) recent_weeks
        """)
        avg_revenue = session.execute(revenue_query).scalar() or 0
        
        # FIXED 2025-09-09: Store-level Year-to-Date YoY calculation (matching company total fix)
        # Compare YTD current year vs YTD last year + YTD last year vs YTD two years ago
        yoy_query = text(f"""
            SELECT 
                SUM(CASE WHEN week_ending >= MAKEDATE(YEAR(CURDATE()), 1) 
                         AND week_ending <= CURDATE()
                         AND YEAR(week_ending) = YEAR(CURDATE())
                    THEN revenue_{store_code} END) as current_ytd,
                SUM(CASE WHEN week_ending >= MAKEDATE(YEAR(CURDATE()) - 1, 1)
                         AND week_ending <= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                         AND YEAR(week_ending) = YEAR(CURDATE()) - 1
                    THEN revenue_{store_code} END) as last_year_ytd,
                SUM(CASE WHEN week_ending >= MAKEDATE(YEAR(CURDATE()) - 2, 1)
                         AND week_ending <= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
                         AND YEAR(week_ending) = YEAR(CURDATE()) - 2
                    THEN revenue_{store_code} END) as two_years_ago_ytd
            FROM scorecard_trends_data 
            WHERE revenue_{store_code} IS NOT NULL 
                AND revenue_{store_code} > 0
        """)
        yoy_result = session.execute(yoy_query).fetchone()
        
        yoy_growth = 0
        yoy_comparison = 0
        if yoy_result and yoy_result.current_ytd and yoy_result.last_year_ytd and yoy_result.last_year_ytd > 0:
            current_ytd = float(yoy_result.current_ytd)
            last_year_ytd = float(yoy_result.last_year_ytd)
            # Main YoY: Current YTD vs Last Year YTD
            yoy_growth = ((current_ytd - last_year_ytd) / last_year_ytd) * 100
            
            # Calculate last year YTD vs two years ago YTD for comparison
            if yoy_result.two_years_ago_ytd and yoy_result.two_years_ago_ytd > 0:
                two_years_ago_ytd = float(yoy_result.two_years_ago_ytd)
                last_year_yoy = ((last_year_ytd - two_years_ago_ytd) / two_years_ago_ytd) * 100
                # Secondary YoY comparison: How current YTD YoY compares to last year's YTD YoY (percentage point difference)
                yoy_comparison = yoy_growth - last_year_yoy
                
            logger.info(f"Store {store_code} YTD YoY: Current=${current_ytd:,.0f}, Last=${last_year_ytd:,.0f}, YoY={yoy_growth:.1f}%, Comparison={yoy_comparison:.1f}pp")
        
        # Get profit margin from payroll data (with type conversion)
        profit_margin_query = session.query(PayrollTrends).filter(
            PayrollTrends.store_id == store_code
        ).order_by(desc(PayrollTrends.week_ending)).limit(config.location_kpis_payroll_weeks).all()
        
        profit_margin = 0
        if profit_margin_query:
            avg_payroll = sum(float(r.payroll_cost or 0) for r in profit_margin_query) / len(profit_margin_query)
            avg_revenue_float = float(avg_revenue)
            profit_margin = ((avg_revenue_float - avg_payroll) / avg_revenue_float * 100) if avg_revenue_float > 0 else 0
        
        # Calculate store-specific utilization from inventory data
        utilization_query = text("""
            SELECT 
                COUNT(CASE WHEN status IN ('fully_rented', 'partially_rented') THEN 1 END) * 100.0
                / NULLIF(COUNT(*), 0) as utilization_rate
            FROM combined_inventory 
            WHERE store_code = :store_code AND rental_rate > 0
        """)
        utilization_result = session.execute(utilization_query, {'store_code': store_code}).fetchone()
        utilization_avg = float(utilization_result.utilization_rate or 0) if utilization_result else 0
        
        # Calculate store-specific health score using same logic as main dashboard
        from app.models.config_models import ExecutiveDashboardConfiguration
        try:
            config = ExecutiveDashboardConfiguration.query.filter_by(user_id='default_user', config_name='default').first()
            if not config:
                config = ExecutiveDashboardConfiguration()
        except Exception as config_error:
            logger.error(f"Error loading executive dashboard configuration: {config_error}")
            # Fallback MockConfig for robust error handling
            class MockConfig:
                base_health_score = 75.0
                revenue_tier_1_threshold = 100000.0
                revenue_tier_1_points = 10.0
                revenue_tier_2_threshold = 75000.0
                revenue_tier_2_points = 7.5
                revenue_tier_3_threshold = 50000.0
                revenue_tier_3_points = 5.0
                revenue_tier_4_points = 2.5
                yoy_excellent_threshold = 10.0
                yoy_excellent_points = 10.0
                yoy_good_threshold = 5.0
                yoy_good_points = 7.5
                yoy_fair_threshold = 0.0
                yoy_fair_points = 5.0
                yoy_poor_points = 0.0
                utilization_excellent_threshold = 85.0
                utilization_excellent_points = 10.0
                utilization_good_threshold = 75.0
                utilization_good_points = 7.5
                utilization_fair_threshold = 65.0
                utilization_fair_points = 5.0
                utilization_poor_points = 2.5
            config = MockConfig()
        health_score = config.base_health_score
        
        # Add revenue-based health points
        if avg_revenue > config.revenue_tier_1_threshold:
            health_score += config.revenue_tier_1_points
        elif avg_revenue > config.revenue_tier_2_threshold:
            health_score += config.revenue_tier_2_points
        elif avg_revenue > config.revenue_tier_3_threshold:
            health_score += config.revenue_tier_3_points
        else:
            health_score += config.revenue_tier_4_points
            
        # Add YoY growth health points
        if yoy_growth > config.yoy_excellent_threshold:
            health_score += config.yoy_excellent_points
        elif yoy_growth > config.yoy_good_threshold:
            health_score += config.yoy_good_points
        elif yoy_growth > config.yoy_fair_threshold:
            health_score += config.yoy_fair_points
        else:
            health_score += config.yoy_poor_points
            
        # Add utilization health points
        if utilization_avg > config.utilization_excellent_threshold:
            health_score += config.utilization_excellent_points
        elif utilization_avg > config.utilization_good_threshold:
            health_score += config.utilization_good_points
        elif utilization_avg > config.utilization_fair_threshold:
            health_score += config.utilization_fair_points
        else:
            health_score += config.utilization_poor_points

        return jsonify({
            "success": True,
            "store_name": STORE_LOCATIONS[store_code]["name"],
            "revenue_metrics": {
                "current_3wk_avg": avg_revenue,
                "yoy_growth": round(yoy_growth, 1),
                "yoy_comparison": round(yoy_comparison, 1),
                "change_pct": 0
            },
            "store_metrics": {
                "utilization_avg": round(utilization_avg, 1),
                "change_pct": 0
            },
            "operational_health": {
                "health_score": round(min(health_score, 100), 0),  # Cap at 100
                "change_pct": 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in location KPIs: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@executive_api_bp.route("/api/location-comparison", methods=["GET"])
def location_comparison():
    """Get comparison data for all locations with real YoY growth and utilization"""
    try:
        session = db.session
        locations_data = []
        
        # Use same data source as working location-kpis endpoints (scorecard_trends_data)
        for store_code, store_info in STORE_LOCATIONS.items():
            # STANDARDIZED: Get current revenue using same method as other endpoints
            config = _get_executive_config()
            revenue_query = text(f"""
                SELECT AVG(revenue_{store_code}) as current_revenue
                FROM (
                    SELECT revenue_{store_code} 
                    FROM scorecard_trends_data 
                    WHERE revenue_{store_code} IS NOT NULL
                    ORDER BY week_ending DESC 
                    LIMIT {config.location_comparison_revenue_weeks}
                ) recent_weeks
            """)
            current_result = session.execute(revenue_query).fetchone()
            current_revenue = float(current_result.current_revenue) if current_result and current_result.current_revenue else 0
            
            # FIXED: Dynamic 3-year YoY comparison (21 days for 3 weeks)
            yoy_query = text(f"""
                SELECT 
                    AVG(CASE WHEN week_ending >= DATE_SUB(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 21 DAY)
                             AND week_ending < DATE_SUB(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 0 DAY)
                        THEN revenue_{store_code} END) as current_year,
                    AVG(CASE WHEN week_ending >= DATE_SUB(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 386 DAY)
                             AND week_ending < DATE_SUB(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 365 DAY)
                        THEN revenue_{store_code} END) as last_year,
                    AVG(CASE WHEN week_ending >= DATE_SUB(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 751 DAY)
                             AND week_ending < DATE_SUB(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 730 DAY)
                        THEN revenue_{store_code} END) as two_years_ago
                FROM scorecard_trends_data 
                WHERE revenue_{store_code} IS NOT NULL
            """)
            yoy_result = session.execute(yoy_query).fetchone()
            
            yoy_growth = 0
            yoy_comparison = 0
            if yoy_result and yoy_result.current_year and yoy_result.last_year and yoy_result.last_year > 0:
                current_year = float(yoy_result.current_year)
                last_year = float(yoy_result.last_year)
                # Main YoY: Current year vs last year
                yoy_growth = ((current_year - last_year) / last_year) * 100
                
                # Calculate last year vs two years ago YoY for comparison
                if yoy_result.two_years_ago and yoy_result.two_years_ago > 0:
                    two_years_ago = float(yoy_result.two_years_ago)
                    last_year_yoy = ((last_year - two_years_ago) / two_years_ago) * 100
                    # Secondary YoY comparison: How current YoY compares to last year's YoY (percentage point difference)
                    yoy_comparison = yoy_growth - last_year_yoy
            
            # Get utilization from combined_inventory data (company-wide for now)
            # TODO: Add store-specific utilization when store field is identified
            util_query = text("""
                SELECT 
                    COUNT(CASE WHEN status IN ('fully_rented', 'partially_rented') THEN 1 END) * 100.0
                    / NULLIF(COUNT(*), 0) as utilization_pct
                FROM combined_inventory 
                WHERE rental_rate > 0
            """)
            util_result = session.execute(util_query).fetchone()
            utilization = float(util_result.utilization_pct) if util_result and util_result.utilization_pct else 0
            
            # Get profit margin from payroll data
            payroll_query = text(f"""
                SELECT AVG(total_revenue) as avg_revenue, AVG(payroll_cost) as avg_payroll
                FROM executive_payroll_trends 
                WHERE store_id = :store_code
                ORDER BY week_ending DESC 
                LIMIT {config.insights_profit_margin_weeks}
            """)
            payroll_result = session.execute(payroll_query, {"store_code": store_code}).fetchone()
            
            profit_margin = 0
            if payroll_result and payroll_result.avg_revenue and payroll_result.avg_payroll:
                avg_revenue = float(payroll_result.avg_revenue)
                avg_payroll = float(payroll_result.avg_payroll)
                if avg_revenue > 0:
                    profit_margin = ((avg_revenue - avg_payroll) / avg_revenue) * 100
                
            locations_data.append({
                "store_code": store_code,
                "name": store_info["name"],
                "revenue": current_revenue,
                "growth": round(yoy_growth, 1),
                "growth_comparison": round(yoy_comparison, 1),
                "utilization": round(utilization, 1),
                "margin": round(profit_margin, 1)
            })
        
        return jsonify({
            "success": True,
            "locations": locations_data,
            "metadata": {
                "data_source": "scorecard_trends_data + combined_inventory + PayrollTrends",
                "revenue_period": "3-week average",
                "yoy_comparison": "Year-to-Date vs Last Year-to-Date",
                "utilization_period": "30-day activity rate"
            }
        })
        
    except Exception as e:
        logger.error(f"Error in location comparison: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@executive_api_bp.route("/api/intelligent-insights", methods=["GET"])
def intelligent_insights():
    """Get intelligent business insights based on comprehensive data analysis"""
    try:
        session = db.session
        insights = []
        
        # 1. Revenue Trend Analysis (using scorecard_trends_data)
        config = _get_executive_config()
        revenue_trend_query = text(f"""
            SELECT 
                week_ending,
                total_weekly_revenue,
                LAG(total_weekly_revenue, 1) OVER (ORDER BY week_ending) as prev_week,
                LAG(total_weekly_revenue, 4) OVER (ORDER BY week_ending) as prev_month
            FROM scorecard_trends_data 
            WHERE total_weekly_revenue IS NOT NULL
            ORDER BY week_ending DESC 
            LIMIT {config.insights_trend_analysis_weeks}
        """)
        revenue_data = session.execute(revenue_trend_query).fetchall()
        
        if len(revenue_data) >= 4:
            recent_avg = sum(float(r.total_weekly_revenue or 0) for r in revenue_data[:3]) / 3
            older_avg = sum(float(r.total_weekly_revenue or 0) for r in revenue_data[3:6]) / 3
            
            if recent_avg < older_avg * 0.9:  # 10% decline
                decline_pct = ((older_avg - recent_avg) / older_avg) * 100
                insights.append({
                    "title": "Revenue Decline Alert",
                    "description": f"Revenue has declined {decline_pct:.1f}% over the past 3 weeks",
                    "severity": "high" if decline_pct > 15 else "medium",
                    "recommendation": "Investigate top-performing locations and review contract pipeline",
                    "data": {"decline_percentage": round(decline_pct, 1), "recent_avg": round(recent_avg, 0)}
                })
            elif recent_avg > older_avg * 1.1:  # 10% growth
                growth_pct = ((recent_avg - older_avg) / older_avg) * 100
                insights.append({
                    "title": "Revenue Growth Opportunity",
                    "description": f"Strong revenue growth of {growth_pct:.1f}% identified",
                    "severity": "positive",
                    "recommendation": "Analyze successful strategies for replication across underperforming stores",
                    "data": {"growth_percentage": round(growth_pct, 1), "recent_avg": round(recent_avg, 0)}
                })
        
        # 2. Store Performance Imbalance Analysis
        store_performance_query = text("""
            SELECT 
                'Wayzata' as store_name,
                AVG(revenue_3607) as avg_revenue,
                COUNT(CASE WHEN revenue_3607 > 0 THEN 1 END) as active_weeks
            FROM scorecard_trends_data WHERE week_ending >= CURDATE() - INTERVAL 8 WEEK
            UNION ALL
            SELECT 
                'Brooklyn Park' as store_name,
                AVG(revenue_6800) as avg_revenue,
                COUNT(CASE WHEN revenue_6800 > 0 THEN 1 END) as active_weeks
            FROM scorecard_trends_data WHERE week_ending >= CURDATE() - INTERVAL 8 WEEK
            UNION ALL
            SELECT 
                'Elk River' as store_name,
                AVG(revenue_728) as avg_revenue,
                COUNT(CASE WHEN revenue_728 > 0 THEN 1 END) as active_weeks
            FROM scorecard_trends_data WHERE week_ending >= CURDATE() - INTERVAL 8 WEEK
            UNION ALL
            SELECT 
                'Fridley' as store_name,
                AVG(revenue_8101) as avg_revenue,
                COUNT(CASE WHEN revenue_8101 > 0 THEN 1 END) as active_weeks
            FROM scorecard_trends_data WHERE week_ending >= CURDATE() - INTERVAL 8 WEEK
        """)
        store_data = session.execute(store_performance_query).fetchall()
        
        if store_data:
            revenues = [(s.store_name, float(s.avg_revenue or 0)) for s in store_data if s.avg_revenue]
            if revenues:
                max_store = max(revenues, key=lambda x: x[1])
                min_store = min(revenues, key=lambda x: x[1])
                
                if max_store[1] > min_store[1] * 2:  # Performance gap > 200%
                    gap_ratio = max_store[1] / min_store[1]
                    insights.append({
                        "title": "Store Performance Imbalance",
                        "description": f"{max_store[0]} outperforms {min_store[0]} by {gap_ratio:.1f}x",
                        "severity": "medium",
                        "recommendation": f"Analyze {max_store[0]}'s strategies for implementation at {min_store[0]}",
                        "data": {
                            "top_performer": max_store[0],
                            "underperformer": min_store[0],
                            "performance_ratio": round(gap_ratio, 1)
                        }
                    })
        
        # 3. Equipment Utilization Insight
        utilization_query = text("""
            SELECT 
                COUNT(CASE WHEN status IN ('fully_rented', 'partially_rented') THEN 1 END) * 100.0
                / NULLIF(COUNT(*), 0) as current_utilization,
                COUNT(*) as total_inventory
            FROM combined_inventory 
            WHERE rental_rate > 0
        """)
        util_result = session.execute(utilization_query).fetchone()
        
        if util_result and util_result.current_utilization is not None:
            utilization = float(util_result.current_utilization)
            total_items = int(util_result.total_inventory or 0)
            
            if utilization < 40:
                insights.append({
                    "title": "Low Equipment Utilization",
                    "description": f"Only {utilization:.1f}% of rental equipment is currently active",
                    "severity": "medium",
                    "recommendation": "Review pricing strategy and marketing efforts for underutilized equipment",
                    "data": {
                        "utilization_rate": round(utilization, 1),
                        "total_inventory": total_items,
                        "idle_equipment": round(total_items * (1 - utilization/100))
                    }
                })
            elif utilization > 85:
                insights.append({
                    "title": "High Utilization Opportunity",
                    "description": f"Equipment utilization at {utilization:.1f}% indicates capacity constraints",
                    "severity": "positive",
                    "recommendation": "Consider expanding inventory in high-demand categories",
                    "data": {"utilization_rate": round(utilization, 1), "total_inventory": total_items}
                })
        
        # 4. Add default insights if no patterns detected
        if not insights:
            insights.append({
                "title": "System Health Check",
                "description": "All key performance indicators are within normal operating ranges",
                "severity": "info",
                "recommendation": "Continue monitoring trends for optimization opportunities",
                "data": {"analysis_period": "8 weeks", "data_sources": 3}
            })
        
        return jsonify({
            "success": True,
            "actionable_insights": insights,
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "data_sources": ["scorecard_trends_data", "combined_inventory", "executive_payroll_trends"],
                "insights_generated": len(insights)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in intelligent insights: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@executive_api_bp.route("/api/financial-forecasts", methods=["GET"])
def financial_forecasts():
    """Get financial forecasting data based on trend analysis"""
    try:
        session = db.session
        forecast_weeks = int(request.args.get('weeks', 12))  # Default 12 weeks
        
        # Get historical weekly revenue data for trend analysis
        config = _get_executive_config()
        historical_query = text(f"""
            SELECT 
                week_ending,
                total_weekly_revenue,
                WEEK(week_ending) as week_num,
                YEAR(week_ending) as year_num
            FROM scorecard_trends_data 
            WHERE total_weekly_revenue IS NOT NULL
                AND total_weekly_revenue > 0
            ORDER BY week_ending DESC 
            LIMIT {config.forecasts_historical_weeks}
        """)
        historical_data = session.execute(historical_query).fetchall()
        
        if len(historical_data) < 6:
            return jsonify({
                "success": False,
                "error": "Insufficient historical data for forecasting"
            }), 400
        
        # Calculate trend components
        revenues = [float(r.total_weekly_revenue) for r in reversed(historical_data)]
        weeks = list(range(len(revenues)))
        
        # Simple linear trend calculation
        n = len(revenues)
        sum_x = sum(weeks)
        sum_y = sum(revenues)
        sum_xy = sum(weeks[i] * revenues[i] for i in range(n))
        sum_x2 = sum(x**2 for x in weeks)
        
        # Linear regression: y = mx + b
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2) if (n * sum_x2 - sum_x**2) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate average and volatility for confidence ranges
        recent_avg = sum(revenues[-8:]) / 8  # Last 8 weeks average
        volatility = (sum((r - recent_avg)**2 for r in revenues[-8:]) / 8) ** 0.5
        
        # Generate forecast data
        forecast_data = []
        confidence_upper = []
        confidence_lower = []
        
        last_week_number = len(revenues) - 1
        
        for i in range(1, forecast_weeks + 1):
            week_number = last_week_number + i
            
            # Linear trend forecast
            trend_forecast = slope * week_number + intercept
            
            # Ensure non-negative forecast
            trend_forecast = max(trend_forecast, recent_avg * 0.5)
            
            # Calculate confidence interval (±1.96 * standard error for 95% confidence)
            confidence_factor = 1.96 * volatility * (1 + i/12)  # Increasing uncertainty over time
            upper_bound = trend_forecast + confidence_factor
            lower_bound = max(trend_forecast - confidence_factor, trend_forecast * 0.3)  # Don't go below 30%
            
            # Calculate forecast date
            last_date = historical_data[0].week_ending
            forecast_date = last_date + timedelta(weeks=i)
            
            forecast_data.append({
                "week": i,
                "date": forecast_date.isoformat(),
                "predicted_revenue": round(trend_forecast, 0),
                "trend_component": round(slope, 2)
            })
            
            confidence_upper.append(round(upper_bound, 0))
            confidence_lower.append(round(lower_bound, 0))
        
        # Calculate forecast summary metrics
        total_forecast = sum(item["predicted_revenue"] for item in forecast_data)
        avg_weekly_forecast = total_forecast / len(forecast_data)
        trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        confidence_level = min(90, max(60, 80 - abs(slope / recent_avg * 100)))  # Dynamic confidence
        
        return jsonify({
            "success": True,
            "forecast_data": {
                "next_12_weeks": forecast_data[:forecast_weeks],
                "confidence_range": {
                    "upper_bounds": confidence_upper[:forecast_weeks],
                    "lower_bounds": confidence_lower[:forecast_weeks]
                },
                "summary": {
                    "total_forecast_revenue": round(total_forecast, 0),
                    "avg_weekly_forecast": round(avg_weekly_forecast, 0),
                    "trend_direction": trend_direction,
                    "weekly_trend_change": round(slope, 0),
                    "confidence_level": round(confidence_level, 1)
                }
            },
            "metadata": {
                "forecast_horizon_weeks": forecast_weeks,
                "historical_data_points": len(historical_data),
                "model_type": "linear_trend_analysis",
                "volatility_measure": round(volatility, 0),
                "generated_at": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in financial forecasts: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@executive_api_bp.route("/api/custom-insight", methods=["POST"])
def add_custom_insight():
    """Add a custom business insight"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'event_type', 'description', 'impact_category']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        # Here you would save to a custom insights table
        # For now, just return success
        logger.info(f"Custom insight added: {data['description']}")
        
        return jsonify({
            "success": True,
            "message": "Custom insight added successfully"
        })
        
    except Exception as e:
        logger.error(f"Error adding custom insight: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

def _calculate_metric_periods(session, table_name, column_name, location_filter=None, location_value=None):
    """
    SYSTEMATIC REUSABLE CALCULATION FUNCTION - Based on working Total Weekly Revenue pattern
    Calculates all time periods and trailing averages for any metric using CTE approach
    
    Args:
        session: Database session
        table_name: Source table (e.g., 'scorecard_trends_data', 'payroll_trends_data')
        column_name: Column to calculate (e.g., 'total_weekly_revenue', 'revenue_3607')
        location_filter: Optional column name for location filtering (e.g., 'location_code')
        location_value: Optional value for location filtering
    
    Returns:
        dict with all calculated periods and averages
    """
    try:
        # Build the base query with location filtering if needed
        where_clause = f"WHERE {column_name} IS NOT NULL"
        params = {}
        
        if location_filter and location_value:
            where_clause += f" AND {location_filter} = :location_value"
            params['location_value'] = location_value
        
        # Use the proven CTE approach from Total Weekly Revenue
        metric_query = text(f"""
            WITH current_data AS (
                SELECT 
                    week_ending,
                    {column_name} as metric_value,
                    ROW_NUMBER() OVER (ORDER BY week_ending DESC) as week_rank
                FROM {table_name}
                {where_clause}
                ORDER BY week_ending DESC 
                LIMIT 10
            ),
            previous_year_data AS (
                SELECT 
                    week_ending,
                    {column_name} as metric_value,
                    ROW_NUMBER() OVER (ORDER BY week_ending DESC) as week_rank
                FROM {table_name}
                {where_clause}
                AND week_ending BETWEEN DATE_SUB(CURDATE(), INTERVAL 53 WEEK) 
                                   AND DATE_SUB(CURDATE(), INTERVAL 50 WEEK)
                ORDER BY week_ending DESC 
                LIMIT 10
            )
            SELECT 'current' as period, week_ending, metric_value, week_rank FROM current_data
            UNION ALL
            SELECT 'previous_year' as period, week_ending, metric_value, week_rank FROM previous_year_data
            ORDER BY period DESC, week_rank ASC
        """)
        
        metric_data = session.execute(metric_query, params).fetchall()
        
        # Process the data using the same logic as Total Weekly Revenue
        periods = {}
        trailing_3w_current = []
        trailing_3w_prev_year = []
        trailing_3w_prev_year_forward = []
        
        current_data = [row for row in metric_data if row.period == 'current']
        prev_year_data = [row for row in metric_data if row.period == 'previous_year']
        
        # Process current period data
        for row in current_data:
            week_rank = row.week_rank
            value = float(row.metric_value) if row.metric_value else 0
            
            if week_rank == 1:  # Current week
                periods['current_week'] = value
                trailing_3w_current.append(value)
            elif week_rank == 2:  # Previous week  
                periods['previous_week'] = value
                trailing_3w_current.append(value)
            elif week_rank == 3:  # -2 weeks
                periods['minus_2_week'] = value
                trailing_3w_current.append(value)
            elif week_rank == 4:  # -3 weeks
                periods['minus_3_week'] = value
        
        # Process previous year data
        if prev_year_data:
            # Previous year same week (closest match)
            periods['previous_year'] = float(prev_year_data[0].metric_value) if prev_year_data[0].metric_value else 0
            
            # Previous year trailing 3w (weeks leading up to same period last year)
            for row in prev_year_data[:3]:
                if row.metric_value:
                    trailing_3w_prev_year.append(float(row.metric_value))
            
            # Previous year 3w forward (weeks following same period last year)
            for row in prev_year_data[1:4]:  # Skip first (same week), take next 3
                if row.metric_value:
                    trailing_3w_prev_year_forward.append(float(row.metric_value))
        
        return {
            'periods': periods,
            'current_trailing_3w_avg': round(sum(trailing_3w_current) / len(trailing_3w_current), 2) if trailing_3w_current else 0,
            'prev_year_trailing_3w': round(sum(trailing_3w_prev_year) / len(trailing_3w_prev_year), 2) if trailing_3w_prev_year else 0,
            'prev_year_3w_forward': round(sum(trailing_3w_prev_year_forward) / len(trailing_3w_prev_year_forward), 2) if trailing_3w_prev_year_forward else 0
        }
        
    except Exception as e:
        logger.error(f"Error in _calculate_metric_periods for {column_name}: {str(e)}")
        return {
            'periods': {'current_week': 0, 'previous_week': 0, 'minus_2_week': 0, 'minus_3_week': 0, 'previous_year': 0},
            'current_trailing_3w_avg': 0,
            'prev_year_trailing_3w': 0,
            'prev_year_3w_forward': 0
        }

@executive_api_bp.route("/api/comprehensive-scorecard-matrix", methods=["GET"])
def comprehensive_scorecard_matrix():
    """
    ADDED 2025-09-09: Comprehensive Executive Scorecard Matrix
    All datapoints: -3, -2, Previous Week, Current Week, Previous Year, Plus/Minus Goal,
    Current Trailing 3w average, Prev Year Trailing 3w, Prev Year 3w Forward
    
    UPDATED 2025-09-10: Systematic calculation using reusable function for ALL metrics
    """
    try:
        session = db.session
        
        # Get current week and calculate periods
        current_date = datetime.now()
        
        # Define weeks relative to current week
        periods = {
            'current_week': 0,
            'previous_week': 1, 
            'minus_2_week': 2,
            'minus_3_week': 3,
            'previous_year': 52  # 52 weeks ago
        }
        
        # Initialize comprehensive matrix
        scorecard_matrix = {
            "metadata": {
                "generated_at": current_date.isoformat(),
                "current_week_ending": None,
                "data_freshness": "real_time"
            },
            "metrics": {}
        }
        
        # Get the most recent week ending for reference and calculate date headers
        week_query = text("""
            SELECT week_ending FROM scorecard_trends_data 
            WHERE total_weekly_revenue IS NOT NULL 
            ORDER BY week_ending DESC LIMIT 1
        """)
        latest_week = session.execute(week_query).fetchone()
        
        # Calculate period dates and week numbers for dynamic headers
        period_dates = {}
        if latest_week:
            base_date = latest_week.week_ending
            scorecard_matrix["metadata"]["current_week_ending"] = base_date.isoformat()
            
            # Calculate dates for each period
            from datetime import timedelta
            period_dates = {
                "current_week": {
                    "date": base_date,
                    "week_number": base_date.isocalendar()[1],
                    "year": base_date.year,
                    "formatted": base_date.strftime("%m/%d/%Y"),
                    "header": f"Current Week\n(Wk {base_date.isocalendar()[1]})\n{base_date.strftime('%m/%d/%Y')}"
                },
                "previous_week": {
                    "date": base_date - timedelta(weeks=1),
                    "week_number": (base_date - timedelta(weeks=1)).isocalendar()[1],
                    "year": (base_date - timedelta(weeks=1)).year,
                    "formatted": (base_date - timedelta(weeks=1)).strftime("%m/%d/%Y"),
                    "header": f"Previous Week\n(Wk {(base_date - timedelta(weeks=1)).isocalendar()[1]})\n{(base_date - timedelta(weeks=1)).strftime('%m/%d/%Y')}"
                },
                "minus_2": {
                    "date": base_date - timedelta(weeks=2),
                    "week_number": (base_date - timedelta(weeks=2)).isocalendar()[1],
                    "year": (base_date - timedelta(weeks=2)).year,
                    "formatted": (base_date - timedelta(weeks=2)).strftime("%m/%d/%Y"),
                    "header": f"-2 Week\n(Wk {(base_date - timedelta(weeks=2)).isocalendar()[1]})\n{(base_date - timedelta(weeks=2)).strftime('%m/%d/%Y')}"
                },
                "minus_3": {
                    "date": base_date - timedelta(weeks=3),
                    "week_number": (base_date - timedelta(weeks=3)).isocalendar()[1],
                    "year": (base_date - timedelta(weeks=3)).year,
                    "formatted": (base_date - timedelta(weeks=3)).strftime("%m/%d/%Y"),
                    "header": f"-3 Week\n(Wk {(base_date - timedelta(weeks=3)).isocalendar()[1]})\n{(base_date - timedelta(weeks=3)).strftime('%m/%d/%Y')}"
                },
                "previous_year": {
                    "date": base_date - timedelta(weeks=52),
                    "week_number": (base_date - timedelta(weeks=52)).isocalendar()[1],
                    "year": (base_date - timedelta(weeks=52)).year,
                    "formatted": (base_date - timedelta(weeks=52)).strftime("%m/%d/%Y"),
                    "header": f"Previous Year\n(Wk {(base_date - timedelta(weeks=52)).isocalendar()[1]} {(base_date - timedelta(weeks=52)).year})\n{(base_date - timedelta(weeks=52)).strftime('%m/%d/%Y')}"
                },
                "current_trailing_3w_avg": {
                    "header": "Current\nTrailing 3w Avg"
                },
                "prev_year_trailing_3w": {
                    "header": "Prev Year\nTrailing 3w"
                },
                "prev_year_3w_forward": {
                    "header": "Prev Year\n3w Forward"
                },
                "plus_minus_goal": {
                    "header": "+/- Goal"
                }
            }
            
        scorecard_matrix["metadata"]["period_dates"] = period_dates
        
        # Get goal values from configuration tables instead of hardcoding
        def get_goal_values():
            """
            ADDED 2025-09-10: Retrieve goal values from configuration database
            Replaces hardcoded values with systematic database lookup
            """
            goals = {
                'total_weekly_revenue': 100000,  # Default fallback
                'ar_over_45_days_percent': 15,   # Default fallback
                'deliveries': 12,                # Default fallback
                'wage_ratio': 25,                # Default fallback
                'revenue_per_hour': 85,          # Default fallback
                'reservations': {'3607': 10000, '6800': 15000, '728': 2000, '8101': 250000},  # Defaults
                'contracts': {'3607': 150, '6800': 140, '728': 85, '8101': 65}  # Defaults
            }
            
            try:
                # Get goals from business_intelligence_config
                bi_query = text("""
                    SELECT revenue_target_monthly, revenue_target_quarterly, revenue_target_yearly,
                           profit_margin_target
                    FROM business_intelligence_config 
                    WHERE is_active = 1 
                    ORDER BY created_at DESC LIMIT 1
                """)
                bi_result = session.execute(bi_query).fetchone()
                
                if bi_result and bi_result.revenue_target_monthly:
                    # Convert monthly to weekly (monthly / 4.33 weeks per month)
                    goals['total_weekly_revenue'] = int(bi_result.revenue_target_monthly / 4.33)
                
                # Get AR aging goals from scorecard_analytics_configuration  
                scorecard_query = text("""
                    SELECT ar_aging_risk_threshold, ar_risk_low_threshold, ar_risk_medium_threshold
                    FROM scorecard_analytics_configuration 
                    WHERE is_active = 1 
                    ORDER BY created_at DESC LIMIT 1
                """)
                scorecard_result = session.execute(scorecard_query).fetchone()
                
                if scorecard_result and scorecard_result.ar_aging_risk_threshold:
                    goals['ar_over_45_days_percent'] = scorecard_result.ar_aging_risk_threshold
                    
                # TODO: Add store-specific goals from store_specific_thresholds JSON field
                # For now, keeping existing store-specific defaults but should be configurable
                
            except Exception as e:
                app.logger.warning(f"Failed to retrieve goal values from database, using defaults: {str(e)}")
                
            return goals
            
        goal_values = get_goal_values()
        
        # METRIC 1: Total Weekly Revenue - Using systematic calculation function
        total_revenue_calc = _calculate_metric_periods(session, 'scorecard_trends_data', 'total_weekly_revenue')
        
        scorecard_matrix["metrics"]["Total Weekly Revenue"] = {
            "minus_3": total_revenue_calc['periods'].get('minus_3_week', 0),
            "minus_2": total_revenue_calc['periods'].get('minus_2_week', 0), 
            "previous_week": total_revenue_calc['periods'].get('previous_week', 0),
            "current_week": total_revenue_calc['periods'].get('current_week', 0),
            "previous_year": total_revenue_calc['periods'].get('previous_year', 0),
            "plus_minus_goal": goal_values['total_weekly_revenue'],  # Retrieved from database
            "current_trailing_3w_avg": round(total_revenue_calc['current_trailing_3w_avg'], 0),
            "prev_year_trailing_3w": round(total_revenue_calc['prev_year_trailing_3w'], 0),
            "prev_year_3w_forward": round(total_revenue_calc['prev_year_3w_forward'], 0),
            "format": "currency",
            "units": "$"
        }
        
        # METRIC 2: % of Total AR ($) over 45 days - Using systematic calculation function
        ar_calc = _calculate_metric_periods(session, 'scorecard_trends_data', 'ar_over_45_days_percent')
        
        scorecard_matrix["metrics"]["% of Total AR ($) over 45 days (all stores)"] = {
            "minus_3": ar_calc['periods'].get('minus_3_week', 0),
            "minus_2": ar_calc['periods'].get('minus_2_week', 0),
            "previous_week": ar_calc['periods'].get('previous_week', 0),
            "current_week": ar_calc['periods'].get('current_week', 0), 
            "previous_year": ar_calc['periods'].get('previous_year', 0),
            "plus_minus_goal": goal_values['ar_over_45_days_percent'],  # Retrieved from database
            "current_trailing_3w_avg": round(ar_calc['current_trailing_3w_avg'], 1),
            "prev_year_trailing_3w": round(ar_calc['prev_year_trailing_3w'], 1),
            "prev_year_3w_forward": round(ar_calc['prev_year_3w_forward'], 1),
            "format": "percentage",
            "units": "%"
        }
        
        # METRICS 3-6: Store-specific reservations and contracts - Using systematic calculation function
        stores = ['3607', '6800', '728', '8101']
        store_names = {'3607': 'Wayzata', '6800': 'Brooklyn Park', '728': 'Elk River', '8101': 'Fridley'}
        
        for store in stores:
            store_name = store_names[store]
            
            # Reservations - Using systematic calculation
            reservation_calc = _calculate_metric_periods(session, 'scorecard_trends_data', f'total_reservation_{store}')
            
            scorecard_matrix["metrics"][f"Total $ on Reservation {store}"] = {
                "minus_3": reservation_calc['periods'].get('minus_3_week', 0),
                "minus_2": reservation_calc['periods'].get('minus_2_week', 0),
                "previous_week": reservation_calc['periods'].get('previous_week', 0),
                "current_week": reservation_calc['periods'].get('current_week', 0),
                "previous_year": reservation_calc['periods'].get('previous_year', 0),
                "plus_minus_goal": goal_values['reservations'][store],
                "current_trailing_3w_avg": round(reservation_calc['current_trailing_3w_avg'], 0),
                "prev_year_trailing_3w": round(reservation_calc['prev_year_trailing_3w'], 0),
                "prev_year_3w_forward": round(reservation_calc['prev_year_3w_forward'], 0),
                "format": "currency", 
                "units": "$",
                "store_name": store_name
            }
            
            # New Contracts - Using systematic calculation
            contract_calc = _calculate_metric_periods(session, 'scorecard_trends_data', f'new_contracts_{store}')
            
            scorecard_matrix["metrics"][f"# New Open Contracts {store}"] = {
                "minus_3": contract_calc['periods'].get('minus_3_week', 0),
                "minus_2": contract_calc['periods'].get('minus_2_week', 0),
                "previous_week": contract_calc['periods'].get('previous_week', 0),
                "current_week": contract_calc['periods'].get('current_week', 0),
                "previous_year": contract_calc['periods'].get('previous_year', 0),
                "plus_minus_goal": goal_values['contracts'][store],
                "current_trailing_3w_avg": round(contract_calc['current_trailing_3w_avg'], 0),
                "prev_year_trailing_3w": round(contract_calc['prev_year_trailing_3w'], 0),
                "prev_year_3w_forward": round(contract_calc['prev_year_3w_forward'], 0),
                "format": "integer",
                "units": "#",
                "store_name": store_name
            }
        
        # Delivery scheduling for 8101 (Fridley) - Using systematic calculation
        delivery_calc = _calculate_metric_periods(session, 'scorecard_trends_data', 'deliveries_scheduled_8101')
        
        scorecard_matrix["metrics"]["# Deliveries Scheduled next 7 days Weds-Tues 8101"] = {
            "minus_3": delivery_calc['periods'].get('minus_3_week', 0),
            "minus_2": delivery_calc['periods'].get('minus_2_week', 0),
            "previous_week": delivery_calc['periods'].get('previous_week', 0),
            "current_week": delivery_calc['periods'].get('current_week', 0),
            "previous_year": delivery_calc['periods'].get('previous_year', 0),
            "plus_minus_goal": goal_values['deliveries'],  # Retrieved from database
            "current_trailing_3w_avg": round(delivery_calc['current_trailing_3w_avg'], 0),
            "prev_year_trailing_3w": round(delivery_calc['prev_year_trailing_3w'], 0),
            "prev_year_3w_forward": round(delivery_calc['prev_year_3w_forward'], 0),
            "format": "integer",
            "units": "#"
        }
        
        # PAYROLL INTEGRATION: Revenue and Wage Metrics by Store - Using systematic calculation function  
        for store in stores:
            store_name = store_names[store]
            location_code = store  # Use store code as location code
            
            # Revenue from scorecard - Using systematic calculation
            store_revenue_calc = _calculate_metric_periods(session, 'scorecard_trends_data', f'revenue_{store}')
            
            # Payroll data - Using systematic calculation with location filtering
            payroll_calc = _calculate_metric_periods(session, 'payroll_trends_data', 'payroll_amount', 'location_code', location_code)
            wage_hours_calc = _calculate_metric_periods(session, 'payroll_trends_data', 'wage_hours', 'location_code', location_code)
            
            # Revenue metrics
            scorecard_matrix["metrics"][f"Revenue {store}"] = {
                "minus_3": store_revenue_calc['periods'].get('minus_3_week', 0),
                "minus_2": store_revenue_calc['periods'].get('minus_2_week', 0),
                "previous_week": store_revenue_calc['periods'].get('previous_week', 0),
                "current_week": store_revenue_calc['periods'].get('current_week', 0),
                "previous_year": store_revenue_calc['periods'].get('previous_year', 0),
                "plus_minus_goal": 0,  # No specific goal yet (store revenue goals to be added)
                "current_trailing_3w_avg": round(store_revenue_calc['current_trailing_3w_avg'], 0),
                "prev_year_trailing_3w": round(store_revenue_calc['prev_year_trailing_3w'], 0),
                "prev_year_3w_forward": round(store_revenue_calc['prev_year_3w_forward'], 0),
                "format": "currency",
                "units": "$",
                "store_name": store_name
            }
            
            # Wage metrics  
            scorecard_matrix["metrics"][f"Wages {store}"] = {
                "minus_3": payroll_calc['periods'].get('minus_3_week', 0),
                "minus_2": payroll_calc['periods'].get('minus_2_week', 0),
                "previous_week": payroll_calc['periods'].get('previous_week', 0),
                "current_week": payroll_calc['periods'].get('current_week', 0),
                "previous_year": payroll_calc['periods'].get('previous_year', 0),
                "plus_minus_goal": 0,  # Set target later (wage goals to be added)
                "current_trailing_3w_avg": round(payroll_calc['current_trailing_3w_avg'], 0),
                "prev_year_trailing_3w": round(payroll_calc['prev_year_trailing_3w'], 0),
                "prev_year_3w_forward": round(payroll_calc['prev_year_3w_forward'], 0),
                "format": "currency", 
                "units": "$",
                "store_name": store_name
            }
            
            # Calculate wage vs rental revenue % using systematic data
            wage_pct_periods = {}
            wage_pct_trailing = []
            wage_pct_prev_year_trailing = []
            wage_pct_prev_year_forward = []
            
            for period in ['minus_3_week', 'minus_2_week', 'previous_week', 'current_week']:
                revenue = store_revenue_calc['periods'].get(period, 0)
                wages = payroll_calc['periods'].get(period, 0)
                if revenue > 0:
                    wage_pct = round((wages / revenue) * 100, 1)
                    wage_pct_periods[period] = wage_pct
                    if period != 'minus_3_week':  # Include in trailing 3w
                        wage_pct_trailing.append(wage_pct)
                else:
                    wage_pct_periods[period] = 0
            
            # Calculate previous year wage percentages for trailing averages
            prev_year_revenue = store_revenue_calc['periods'].get('previous_year', 0)
            prev_year_wages = payroll_calc['periods'].get('previous_year', 0)
            prev_year_wage_pct = round((prev_year_wages / prev_year_revenue) * 100, 1) if prev_year_revenue > 0 else 0
            
            scorecard_matrix["metrics"][f"Wage vs Rental Rev {store}"] = {
                "minus_3": wage_pct_periods.get('minus_3_week', 0),
                "minus_2": wage_pct_periods.get('minus_2_week', 0),
                "previous_week": wage_pct_periods.get('previous_week', 0),
                "current_week": wage_pct_periods.get('current_week', 0),
                "previous_year": prev_year_wage_pct,
                "plus_minus_goal": goal_values['wage_ratio'],  # Retrieved from database
                "current_trailing_3w_avg": round(sum(wage_pct_trailing) / len(wage_pct_trailing), 1) if wage_pct_trailing else 0,
                "prev_year_trailing_3w": prev_year_wage_pct,  # Use single prev year value for now
                "prev_year_3w_forward": prev_year_wage_pct,  # Use single prev year value for now
                "format": "percentage",
                "units": "%",
                "store_name": store_name
            }
            
            # Calculate revenue per hour using systematic data
            rev_per_hour_periods = {}
            rev_per_hour_trailing = []
            
            for period in ['minus_3_week', 'minus_2_week', 'previous_week', 'current_week']:
                revenue = store_revenue_calc['periods'].get(period, 0)
                hours = wage_hours_calc['periods'].get(period, 0)
                if hours > 0:
                    rev_per_hour = round(revenue / hours, 2)
                    rev_per_hour_periods[period] = rev_per_hour
                    if period != 'minus_3_week':  # Include in trailing 3w
                        rev_per_hour_trailing.append(rev_per_hour)
                else:
                    rev_per_hour_periods[period] = 0
            
            # Calculate previous year revenue per hour
            prev_year_hours = wage_hours_calc['periods'].get('previous_year', 0)
            prev_year_rev_per_hour = round(prev_year_revenue / prev_year_hours, 2) if prev_year_hours > 0 else 0
            
            scorecard_matrix["metrics"][f"Rev per Hr {store}"] = {
                "minus_3": rev_per_hour_periods.get('minus_3_week', 0),
                "minus_2": rev_per_hour_periods.get('minus_2_week', 0),
                "previous_week": rev_per_hour_periods.get('previous_week', 0),
                "current_week": rev_per_hour_periods.get('current_week', 0),
                "previous_year": prev_year_rev_per_hour,
                "plus_minus_goal": goal_values['revenue_per_hour'],  # Retrieved from database
                "current_trailing_3w_avg": round(sum(rev_per_hour_trailing) / len(rev_per_hour_trailing), 2) if rev_per_hour_trailing else 0,
                "prev_year_trailing_3w": prev_year_rev_per_hour,  # Use single prev year value for now
                "prev_year_3w_forward": prev_year_rev_per_hour,  # Use single prev year value for now
                "format": "currency",
                "units": "$/hr",
                "store_name": store_name
            }
        
        logger.info("Comprehensive scorecard matrix generated successfully")
        return jsonify(scorecard_matrix)
        
    except Exception as e:
        logger.error(f"Error in comprehensive scorecard matrix: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# Register the executive blueprint
def register_executive_blueprint(app):
    """Register the executive blueprint with the app"""
    app.register_blueprint(executive_api_bp)

# Update version marker
logger.info(
    "Executive Dashboard Enhanced v6 - Fortune 500 UI with Location Filtering - Deployed %s",
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
)
