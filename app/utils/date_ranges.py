"""Date range utilities for dashboard routes."""

from datetime import datetime, timedelta, date
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


def get_date_range_from_params(request, session=None):
    """Extract and validate date range from request parameters.

    Supports custom start and end dates via query parameters. If not provided,
    falls back to a period parameter (4weeks, 12weeks, 52weeks, ytd). When a
    database session is supplied, the latest available data date is used as the
    end date instead of today's date.
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            return start_date, end_date
        except ValueError:
            logger.error(
                "Invalid date format: start=%s, end=%s", start_date_str, end_date_str
            )

    period = request.args.get("period", "4weeks")

    if session:
        from app.models.db_models import PayrollTrends

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
    elif period == "custom":
        # Custom period should have dates
        return None, None
    else:
        start_date = end_date - timedelta(weeks=4)

    return start_date, end_date
