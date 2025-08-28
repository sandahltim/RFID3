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

        # Calculate date range based on period
        end_date = datetime.now().date()
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

        # Get weekly data with comprehensive metrics
        query = session.query(
            PayrollTrends.week_ending,
            PayrollTrends.store_id,
            PayrollTrends.total_revenue,
            PayrollTrends.rental_revenue,
            PayrollTrends.payroll_cost,
            PayrollTrends.labor_efficiency_ratio,
            PayrollTrends.revenue_per_hour,
            PayrollTrends.wage_hours,
        )

        if store_filter != "all":
            query = query.filter(PayrollTrends.store_id == store_filter)

        # Order by date ascending for proper time series
        query = query.order_by(PayrollTrends.week_ending).limit(
            weeks * 4 if store_filter == "all" else weeks
        )

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
    """Get comparative metrics across all stores."""
    session = None
    try:
        session = db.session()
        period_weeks = int(request.args.get("weeks", 4))

        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=period_weeks)

        # Get aggregated metrics by store
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
            # Calculate profitability
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

        # Sort by revenue descending
        comparison_data.sort(key=lambda x: x["revenue"], reverse=True)

        # Add ranking
        for i, store in enumerate(comparison_data, 1):
            store["rank"] = i

        return jsonify({"stores": comparison_data})

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

        # Get current date boundaries
        end_date = datetime.now().date()
        current_week_start = end_date - timedelta(days=7)
        current_month_start = end_date.replace(day=1)
        current_year_start = end_date.replace(month=1, day=1)

        # Previous periods
        prev_week_start = current_week_start - timedelta(days=7)
        prev_week_end = current_week_start - timedelta(days=1)
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        prev_month_end = current_month_start - timedelta(days=1)
        prev_year_start = current_year_start.replace(year=current_year_start.year - 1)
        prev_year_end = end_date.replace(year=end_date.year - 1)

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

        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=period_weeks)

        logger.info(f"Generating store benchmarking for {period_weeks} weeks")

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
