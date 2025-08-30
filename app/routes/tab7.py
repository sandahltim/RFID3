# app/routes/tab7.py
# Executive Dashboard - Version: 2025-08-27-v1
from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import PayrollTrends, ScorecardTrends, ExecutiveKPI, ItemMaster
from ..services.logger import get_logger
from sqlalchemy import func, desc, and_, or_, text, case
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, date
import json
from decimal import Decimal

logger = get_logger(__name__)

tab7_bp = Blueprint("tab7", __name__)

# Version marker
logger.info(
    "Deployed tab7.py (Executive Dashboard) version: 2025-08-27-v1 at %s",
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
)

# Import centralized store configuration
from ..config.stores import STORE_MAPPING, get_store_name


@tab7_bp.route("/tab/7")
def tab7_view():
    """Main Executive Dashboard page."""
    logger.info(
        "Loading Executive Dashboard at %s",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    return render_template("tab7.html", store_mapping=STORE_MAPPING)


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
    """Get high-level executive metrics with store filtering."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        period = request.args.get("period", "4weeks")  # 4weeks, 12weeks, 52weeks, ytd

        logger.info(
            f"Fetching executive summary: store={store_filter}, period={period}"
        )

        # Calculate date range based on period - use actual latest data date instead of today
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        if not latest_data_date:
            # Fallback to today if no data found
            latest_data_date = datetime.now().date()

        end_date = latest_data_date
        if period == "4weeks":
            start_date = end_date - timedelta(weeks=4)
        elif period == "12weeks":
            start_date = end_date - timedelta(weeks=12)
        elif period == "52weeks":
            start_date = end_date - timedelta(weeks=52)
        else:  # YTD
            start_date = date(end_date.year, 1, 1)

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

        # Get scorecard metrics
        scorecard_query = session.query(
            func.avg(ScorecardTrends.new_contracts_count).label("avg_new_contracts"),
            func.sum(ScorecardTrends.new_contracts_count).label("total_new_contracts"),
            func.avg(ScorecardTrends.deliveries_scheduled_next_7_days).label(
                "avg_deliveries"
            ),
            func.avg(ScorecardTrends.ar_over_45_days_percent).label("avg_ar_aging"),
            func.sum(ScorecardTrends.total_discount_amount).label("total_discounts"),
        ).filter(ScorecardTrends.week_ending.between(start_date, end_date))

        if store_filter != "all":
            scorecard_query = scorecard_query.filter(
                ScorecardTrends.store_id == store_filter
            )

        scorecard_metrics = scorecard_query.first()

        # Calculate YoY growth if we have data from last year
        last_year_start = start_date.replace(year=start_date.year - 1)
        last_year_end = end_date.replace(year=end_date.year - 1)

        last_year_revenue = (
            session.query(func.sum(PayrollTrends.total_revenue))
            .filter(PayrollTrends.week_ending.between(last_year_start, last_year_end))
            .scalar()
            or 0
        )

        current_revenue = float(payroll_metrics.total_revenue or 0)
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

        summary = {
            "financial_metrics": {
                "total_revenue": float(payroll_metrics.total_revenue or 0),
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
                "profit_margin": (
                    round(
                        (
                            float(current_revenue)
                            - float(payroll_metrics.total_payroll or 0)
                        )
                        / float(current_revenue)
                        * 100,
                        2,
                    )
                    if current_revenue
                    else 0
                ),
            },
            "metadata": {
                "store": store_filter,
                "period": period,
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
                "store_id": row.store_id,
                "store_name": STORE_MAPPING.get(row.store_id, row.store_id),
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

        # Use actual latest data date instead of today - CONSISTENT FIX
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )

        if not latest_data_date:
            latest_data_date = datetime.now().date()

        if mode == "weekly":
            current_week = latest_data_date
            previous_week = current_week - timedelta(weeks=1)

            # Metrics for current week
            current_metrics = (
                session.query(
                    PayrollTrends.store_id,
                    func.sum(PayrollTrends.total_revenue).label("revenue"),
                    func.sum(PayrollTrends.payroll_cost).label("payroll"),
                    func.avg(PayrollTrends.labor_efficiency_ratio).label("efficiency"),
                )
                .filter(PayrollTrends.week_ending == current_week)
                .group_by(PayrollTrends.store_id)
                .all()
            )

            previous_metrics = (
                session.query(
                    PayrollTrends.store_id,
                    func.sum(PayrollTrends.total_revenue).label("revenue"),
                    func.sum(PayrollTrends.payroll_cost).label("payroll"),
                    func.avg(PayrollTrends.labor_efficiency_ratio).label("efficiency"),
                )
                .filter(PayrollTrends.week_ending == previous_week)
                .group_by(PayrollTrends.store_id)
                .all()
            )

            current_dict = {m.store_id: m for m in current_metrics}
            previous_dict = {m.store_id: m for m in previous_metrics}
            all_store_ids = set(current_dict.keys()) | set(previous_dict.keys())

            comparison_data = []
            for store_id in all_store_ids:
                current = current_dict.get(store_id)
                previous = previous_dict.get(store_id)

                curr_revenue = float(current.revenue or 0) if current else 0
                prev_revenue = float(previous.revenue or 0) if previous else 0
                curr_payroll = float(current.payroll or 0) if current else 0
                prev_payroll = float(previous.payroll or 0) if previous else 0
                curr_eff = float(current.efficiency or 0) if current else 0
                prev_eff = float(previous.efficiency or 0) if previous else 0

                curr_profit = curr_revenue - curr_payroll
                prev_profit = prev_revenue - prev_payroll

                def pct_change(curr, prev):
                    return ((curr - prev) / prev * 100) if prev else None

                store_data = {
                    "store_id": store_id,
                    "store_name": STORE_MAPPING.get(store_id, store_id),
                    "revenue": {
                        "current": curr_revenue,
                        "previous": prev_revenue,
                        "change": curr_revenue - prev_revenue,
                        "pct_change": pct_change(curr_revenue, prev_revenue),
                    },
                    "payroll": {
                        "current": curr_payroll,
                        "previous": prev_payroll,
                        "change": curr_payroll - prev_payroll,
                        "pct_change": pct_change(curr_payroll, prev_payroll),
                    },
                    "profit": {
                        "current": curr_profit,
                        "previous": prev_profit,
                        "change": curr_profit - prev_profit,
                        "pct_change": pct_change(curr_profit, prev_profit),
                    },
                    "efficiency": {
                        "current": curr_eff,
                        "previous": prev_eff,
                        "change": curr_eff - prev_eff,
                        "pct_change": pct_change(curr_eff, prev_eff),
                    },
                }
                comparison_data.append(store_data)

            # Rankings based on current week values
            for metric in ["revenue", "payroll", "profit", "efficiency"]:
                reverse = True
                sorted_stores = sorted(
                    comparison_data, key=lambda x: x[metric]["current"], reverse=reverse
                )
                for idx, store in enumerate(sorted_stores, 1):
                    store[metric]["rank"] = idx

            return jsonify({"mode": "weekly", "stores": comparison_data})

        # Default aggregate mode
        end_date = latest_data_date
        start_date = end_date - timedelta(weeks=period_weeks)

        logger.info(
            f"Store comparison date range: {start_date} to {end_date} (latest data: {latest_data_date})"
        )

        store_metrics = (
            session.query(
                PayrollTrends.store_id,
                func.sum(PayrollTrends.total_revenue).label("revenue"),
                func.sum(PayrollTrends.payroll_cost).label("payroll"),
                func.avg(PayrollTrends.labor_efficiency_ratio).label("efficiency"),
                func.sum(PayrollTrends.wage_hours).label("hours"),
            )
            .filter(PayrollTrends.week_ending.between(start_date, end_date))
            .group_by(PayrollTrends.store_id)
            .all()
        )

        comparison_data = []
        for store in store_metrics:
            profit = float(store.revenue or 0) - float(store.payroll or 0)
            profit_margin = (
                (profit / float(store.revenue) * 100) if store.revenue else 0
            )

            comparison_data.append(
                {
                    "store_id": store.store_id,
                    "store_name": STORE_MAPPING.get(store.store_id, store.store_id),
                    "revenue": float(store.revenue or 0),
                    "payroll": float(store.payroll or 0),
                    "profit": profit,
                    "profit_margin": round(profit_margin, 2),
                    "efficiency": float(store.efficiency or 0),
                    "total_hours": float(store.hours or 0),
                    "revenue_per_hour": (
                        float(store.revenue / store.hours) if store.hours else 0
                    ),
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
                    ExecutiveKPI.store_id == store_filter,
                    ExecutiveKPI.store_id.is_(None),
                )  # Include company-wide KPIs
            )
        else:
            query = query.filter(ExecutiveKPI.store_id.is_(None))  # Only company-wide

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

        query = (
            query.group_by(PayrollTrends.week_ending)
            .order_by(PayrollTrends.week_ending.desc())
            .limit(52)
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
                    "store_id": store.store_id,
                    "store_name": STORE_MAPPING.get(store.store_id, store.store_id),
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


def get_date_range_from_params(request, session=None):
    """Extract and validate date range from request parameters."""
    # Check for custom date range
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            return start_date, end_date
        except ValueError:
            logger.error(
                f"Invalid date format: start={start_date_str}, end={end_date_str}"
            )

    # Fall back to period-based selection - FIXED: Use latest data date instead of today
    period = request.args.get("period", "4weeks")

    if session:
        # Get latest available data date
        latest_data_date = (
            session.query(func.max(PayrollTrends.week_ending))
            .filter(PayrollTrends.total_revenue > 0)
            .scalar()
        )
        end_date = latest_data_date if latest_data_date else datetime.now().date()
    else:
        end_date = datetime.now().date()

    if period == "4weeks":
        start_date = end_date - timedelta(weeks=4)
    elif period == "12weeks":
        start_date = end_date - timedelta(weeks=12)
    elif period == "52weeks":
        start_date = end_date - timedelta(weeks=52)
    elif period == "ytd":
        start_date = date(end_date.year, 1, 1)
    else:
        start_date = end_date - timedelta(weeks=4)

    return start_date, end_date


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

        # Get scorecard metrics
        scorecard_query = session.query(
            func.sum(ScorecardTrends.new_contracts_count).label("contracts"),
            func.avg(ScorecardTrends.ar_over_45_days_percent).label("ar_aging"),
        ).filter(ScorecardTrends.week_ending.between(start_date, end_date))

        if store_filter != "all":
            scorecard_query = scorecard_query.filter(
                ScorecardTrends.store_id == store_filter
            )

        scorecard = scorecard_query.first()

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
                    "store_id": store.store_id,
                    "store_name": STORE_MAPPING.get(store.store_id, store.store_id),
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


# Update version marker
logger.info(
    "Executive Dashboard Enhanced v3 - YoY/MoM/WoW Comparisons - Deployed %s",
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
)
