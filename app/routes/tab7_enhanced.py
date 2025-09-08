# app/routes/tab7_enhanced.py
# Enhanced Executive Dashboard with YoY/MoM/WoW Comparisons
# Version: 2025-08-28-v1

from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import PayrollTrends, ScorecardTrends, ExecutiveKPI, ItemMaster
from ..services.logger import get_logger
from sqlalchemy import func, desc, and_, or_, text, case, extract
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, date
import json
from decimal import Decimal
import calendar

from ..utils.date_ranges import get_date_range_from_params

logger = get_logger(__name__)

# Import centralized store configuration
from ..config.stores import STORE_MAPPING, get_store_name


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
        ).filter(PayrollTrends.week_ending.between(start_date, end_date))

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
            "contracts": int(scorecard.contracts or 0),
            "ar_aging": float(scorecard.ar_aging or 0),
            "revenue_per_hour": float(result.revenue or 0) / float(result.hours or 1),
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


@tab7_bp.route("/api/executive/period_comparison", methods=["GET"])
def get_period_comparison():
    """Get comprehensive period-over-period comparison."""
    session = None
    try:
        session = db.session()
        store_filter = request.args.get("store", "all")
        comparison_type = request.args.get(
            "comparison_type", "wow"
        )  # wow, mom, yoy, custom

        # Get base period dates
        base_start, base_end = get_date_range_from_params(request)

        if not base_start or not base_end:
            return jsonify({"error": "Invalid date range specified"}), 400

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


@tab7_bp.route("/api/executive/data_availability", methods=["GET"])
def get_data_availability():
    """Get the date range of available data."""
    session = None
    try:
        session = db.session()

        # Get date range from PayrollTrends
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
        start_date, end_date = get_date_range_from_params(request)

        if not start_date or not end_date:
            return jsonify({"error": "Invalid date range"}), 400

        # Build query for trending data
        query = session.query(
            PayrollTrends.week_ending,
            func.sum(PayrollTrends.total_revenue).label("revenue"),
            func.sum(PayrollTrends.rental_revenue).label("rental_revenue"),
            func.sum(PayrollTrends.payroll_cost).label("payroll"),
            func.sum(PayrollTrends.wage_hours).label("hours"),
            func.avg(PayrollTrends.labor_efficiency_ratio).label("efficiency"),
            func.avg(PayrollTrends.revenue_per_hour).label("revenue_per_hour"),
        ).filter(PayrollTrends.week_ending.between(start_date, end_date))

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

        # Calculate period aggregations (weekly, monthly, quarterly)
        aggregations = {"weekly": trending_data, "monthly": [], "quarterly": []}

        # Group by month
        monthly_groups = {}
        for point in trending_data:
            date_obj = datetime.strptime(point["date"], "%Y-%m-%d").date()
            month_key = date_obj.strftime("%Y-%m")
            if month_key not in monthly_groups:
                monthly_groups[month_key] = []
            monthly_groups[month_key].append(point)

        # Calculate monthly aggregates
        for month_key, points in monthly_groups.items():
            monthly_agg = {"period": month_key}
            for metric in metrics:
                if metric in ["efficiency", "profit_margin", "revenue_per_hour"]:
                    # Average for ratio metrics
                    monthly_agg[metric] = sum(p.get(metric, 0) for p in points) / len(
                        points
                    )
                else:
                    # Sum for absolute metrics
                    monthly_agg[metric] = sum(p.get(metric, 0) for p in points)
            aggregations["monthly"].append(monthly_agg)

        # Sort monthly data
        aggregations["monthly"].sort(key=lambda x: x["period"])

        return jsonify(
            {
                "trending_data": trending_data,
                "aggregations": aggregations,
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
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting trending analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()
