"""
Business Intelligence Analytics Service
Handles data import, processing, and KPI calculations
"""

import csv
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)


class BIAnalyticsService:
    """Service for managing business intelligence data and analytics"""

    STORE_CODES = ["6800", "3607", "8101", "728"]

    def __init__(self):
        self.logger = logger

    def import_payroll_data(self, file_path: str) -> Dict:
        """
        Import payroll trends data from CSV file
        Returns: Dict with import statistics
        """
        stats = {
            "records_processed": 0,
            "records_imported": 0,
            "records_skipped": 0,
            "errors": [],
        }

        try:
            # Read CSV file
            df = pd.read_csv(file_path)

            for index, row in df.iterrows():
                stats["records_processed"] += 1

                try:
                    # Parse date
                    period_date = pd.to_datetime(row["2 WEEK ENDING SUN"])

                    # Skip future dates with no data
                    if period_date > datetime.now() and all(
                        pd.isna(row[col]) or row[col] == 0
                        for col in row.index
                        if "Revenue" in col
                    ):
                        stats["records_skipped"] += 1
                        continue

                    # Process each store
                    for store in self.STORE_CODES:
                        revenue_col = f" Rental Revenue {store} "
                        total_rev_col = f" All Revenue {store} "
                        payroll_col = f" Payroll {store} "
                        hours_col = f"Wage Hours {store}"

                        # Skip if no data for this store
                        if revenue_col not in row or pd.isna(row[revenue_col]):
                            continue

                        # Parse values
                        rental_revenue = self._parse_currency(row.get(revenue_col, 0))
                        total_revenue = self._parse_currency(row.get(total_rev_col, 0))
                        payroll_cost = self._parse_currency(row.get(payroll_col, 0))
                        wage_hours = self._parse_number(row.get(hours_col, 0))

                        # Calculate metrics
                        labor_cost_ratio = None
                        revenue_per_hour = None
                        avg_wage_rate = None

                        if total_revenue and total_revenue > 0:
                            if payroll_cost:
                                labor_cost_ratio = float(payroll_cost / total_revenue)
                            if wage_hours and wage_hours > 0:
                                revenue_per_hour = float(total_revenue / wage_hours)

                        if wage_hours and wage_hours > 0 and payroll_cost:
                            avg_wage_rate = float(payroll_cost / wage_hours)

                        # Insert or update record
                        self._upsert_store_performance(
                            period_ending=period_date.date(),
                            store_code=store,
                            rental_revenue=rental_revenue,
                            total_revenue=total_revenue,
                            payroll_cost=payroll_cost,
                            wage_hours=wage_hours,
                            labor_cost_ratio=labor_cost_ratio,
                            revenue_per_hour=revenue_per_hour,
                            avg_wage_rate=avg_wage_rate,
                        )

                    stats["records_imported"] += 1

                except Exception as e:
                    stats["errors"].append(f"Row {index}: {str(e)}")
                    self.logger.error(f"Error processing payroll row {index}: {e}")

            # Log import
            self._log_import("PAYROLL", file_path, stats)

        except Exception as e:
            self.logger.error(f"Error importing payroll data: {e}")
            stats["errors"].append(str(e))

        return stats

    def import_scorecard_data(self, file_path: str) -> Dict:
        """
        Import operational scorecard data from CSV file
        Returns: Dict with import statistics
        """
        stats = {
            "records_processed": 0,
            "records_imported": 0,
            "records_skipped": 0,
            "errors": [],
        }

        try:
            # Read CSV with proper handling of malformed rows
            df = pd.read_csv(file_path, on_bad_lines="skip", nrows=1048)

            for index, row in df.iterrows():
                stats["records_processed"] += 1

                try:
                    # Parse week ending date
                    week_date = pd.to_datetime(row["Week ending Sunday"])

                    # Skip future dates with no data
                    if week_date > datetime.now() and pd.isna(
                        row.get(" Total Weekly Revenue ", 0)
                    ):
                        stats["records_skipped"] += 1
                        continue

                    # Company-wide metrics
                    total_revenue = self._parse_currency(
                        row.get(" Total Weekly Revenue ", 0)
                    )
                    ar_over_45_pct = self._parse_percentage(
                        row.get("% -Total AR ($) > 45 days", 0)
                    )
                    discount_total = self._parse_currency(
                        row.get("Total Discount $ Company Wide", 0)
                    )

                    # Process each store
                    for store in ["3607", "6800", "8101", "728"]:
                        # Store-specific metrics
                        new_contracts = self._parse_number(
                            row.get(f"# New Open Contracts {store}", 0)
                        )

                        if store != "728":  # 728 doesn't have reservation data
                            reservation_14d = self._parse_currency(
                                row.get(
                                    f" $ on Reservation - Next 14 days - {store} ", 0
                                )
                            )
                            reservation_total = self._parse_currency(
                                row.get(f" Total $ on Reservation {store} ", 0)
                            )
                        else:
                            reservation_14d = None
                            reservation_total = None

                        # Insert or update record
                        self._upsert_operational_scorecard(
                            week_ending=week_date.date(),
                            store_code=store,
                            new_contracts_count=new_contracts,
                            reservation_pipeline_14d=reservation_14d,
                            reservation_pipeline_total=reservation_total,
                            ar_over_45_days_pct=ar_over_45_pct,
                            discount_total=discount_total,
                        )

                    stats["records_imported"] += 1

                except Exception as e:
                    stats["errors"].append(f"Row {index}: {str(e)}")
                    self.logger.error(f"Error processing scorecard row {index}: {e}")

            # Log import
            self._log_import("SCORECARD", file_path, stats)

        except Exception as e:
            self.logger.error(f"Error importing scorecard data: {e}")
            stats["errors"].append(str(e))

        return stats

    def calculate_executive_kpis(
        self, period_ending: date, period_type: str = "WEEKLY"
    ) -> None:
        """
        Calculate and store executive KPIs for a given period
        """
        try:
            # Fetch aggregated data
            query = """
                SELECT 
                    SUM(sp.total_revenue) as total_revenue,
                    SUM(sp.rental_revenue) as rental_revenue,
                    AVG(sp.labor_cost_ratio) as avg_labor_ratio,
                    SUM(sp.payroll_cost) as total_payroll,
                    SUM(sp.wage_hours) as total_hours
                FROM bi_store_performance sp
                WHERE sp.period_ending = :period_date
                AND sp.period_type = :period_type
            """

            result = db.session.execute(
                text(query), {"period_date": period_ending, "period_type": period_type}
            ).fetchone()

            if result and result.total_revenue:
                # Calculate growth metrics
                revenue_growth = self._calculate_growth(
                    period_ending, "total_revenue", result.total_revenue
                )

                # Calculate margins (simplified - would need cost data)
                gross_margin = 0.65  # Placeholder - replace with actual calculation
                ebitda_margin = 0.25  # Placeholder - replace with actual calculation

                # Get store rankings
                store_rankings = self._get_store_rankings(period_ending)

                # Upsert executive KPIs
                self._upsert_executive_kpis(
                    period_ending=period_ending,
                    period_type=period_type,
                    total_revenue=result.total_revenue,
                    rental_revenue=result.rental_revenue,
                    revenue_growth_pct=revenue_growth,
                    gross_margin_pct=gross_margin,
                    ebitda_margin_pct=ebitda_margin,
                    labor_cost_ratio=result.avg_labor_ratio,
                    store_rankings=json.dumps(store_rankings),
                    best_performing_store=(
                        store_rankings[0]["store"] if store_rankings else None
                    ),
                )

        except Exception as e:
            self.logger.error(f"Error calculating executive KPIs: {e}")
            raise

    def calculate_inventory_metrics(self, period_ending: date) -> None:
        """
        Calculate inventory performance metrics by integrating with existing POS data
        """
        try:
            query = """
                SELECT 
                    im.current_store as store_code,
                    im.rental_class_num,
                    COUNT(*) as total_units,
                    SUM(CASE WHEN im.status = 'Available' THEN 1 ELSE 0 END) as available_units,
                    SUM(CASE WHEN im.status = 'On Rent' THEN 1 ELSE 0 END) as on_rent_units,
                    SUM(CASE WHEN im.status IN ('Repair', 'Service Required') THEN 1 ELSE 0 END) as repair_units,
                    AVG(im.turnover_ytd) as avg_turnover_ytd,
                    SUM(im.retail_price) as total_value,
                    AVG(im.repair_cost_ltd) as avg_repair_cost
                FROM id_item_master im
                WHERE im.current_store IS NOT NULL
                GROUP BY im.current_store, im.rental_class_num
            """

            results = db.session.execute(text(query)).fetchall()

            for row in results:
                if row.total_units > 0:
                    utilization_rate = (
                        row.on_rent_units / row.total_units if row.total_units else 0
                    )

                    # Calculate rental revenue for this class (would need transaction data)
                    rental_revenue = self._calculate_class_revenue(
                        row.store_code, row.rental_class_num, period_ending
                    )

                    roi = (
                        (rental_revenue / row.total_value * 100)
                        if row.total_value
                        else 0
                    )
                    revenue_per_unit = (
                        rental_revenue / row.total_units if row.total_units else 0
                    )

                    self._upsert_inventory_performance(
                        period_ending=period_ending,
                        store_code=row.store_code,
                        rental_class=row.rental_class_num,
                        total_units=row.total_units,
                        available_units=row.available_units,
                        on_rent_units=row.on_rent_units,
                        in_repair_units=row.repair_units,
                        utilization_rate=utilization_rate,
                        turnover_rate=row.avg_turnover_ytd,
                        inventory_value=row.total_value,
                        rental_revenue=rental_revenue,
                        roi_percentage=roi,
                        revenue_per_unit=revenue_per_unit,
                        repair_cost=row.avg_repair_cost,
                    )

        except Exception as e:
            self.logger.error(f"Error calculating inventory metrics: {e}")
            raise

    def generate_predictions(
        self, target_date: date, store_code: Optional[str] = None
    ) -> None:
        """
        Generate predictive analytics for key metrics using time series analysis
        """
        metrics_to_predict = [
            "total_revenue",
            "new_contracts_count",
            "utilization_rate",
        ]

        for metric in metrics_to_predict:
            try:
                # Get historical data
                historical_data = self._get_historical_data(metric, store_code)

                if len(historical_data) < 8:  # Need at least 8 weeks of data
                    continue

                # Simple moving average prediction (replace with more sophisticated models)
                values = [float(d[1]) for d in historical_data if d[1] is not None]
                if not values:
                    continue

                # Calculate trend
                recent_avg = np.mean(values[-4:])
                older_avg = np.mean(values[-8:-4])
                trend_factor = recent_avg / older_avg if older_avg > 0 else 1

                # Make prediction
                predicted_value = recent_avg * trend_factor
                confidence_interval = np.std(values) * 1.96  # 95% confidence

                self._upsert_prediction(
                    forecast_date=date.today(),
                    target_date=target_date,
                    store_code=store_code,
                    metric_name=metric,
                    predicted_value=predicted_value,
                    confidence_low=predicted_value - confidence_interval,
                    confidence_high=predicted_value + confidence_interval,
                    confidence_level=0.95,
                    model_type="MOVING_AVERAGE_TREND",
                )

            except Exception as e:
                self.logger.error(f"Error generating prediction for {metric}: {e}")

    def check_alert_conditions(self) -> List[Dict]:
        """
        Check all active alert rules and return triggered alerts
        """
        alerts = []

        try:
            query = """
                SELECT * FROM bi_alert_rules 
                WHERE is_active = TRUE
            """

            rules = db.session.execute(text(query)).fetchall()

            for rule in rules:
                # Get current metric value
                current_value = self._get_current_metric_value(
                    rule.metric_name, rule.store_code
                )

                if current_value is None:
                    continue

                # Check thresholds
                status = "NORMAL"
                if rule.critical_threshold and current_value >= rule.critical_threshold:
                    status = "CRITICAL"
                elif rule.warning_threshold and current_value >= rule.warning_threshold:
                    status = "WARNING"

                # Update rule status
                if status != rule.current_status:
                    self._update_alert_status(rule.id, status)

                    if status != "NORMAL":
                        alerts.append(
                            {
                                "rule_name": rule.rule_name,
                                "metric": rule.metric_name,
                                "store": rule.store_code,
                                "current_value": current_value,
                                "threshold": (
                                    rule.critical_threshold
                                    if status == "CRITICAL"
                                    else rule.warning_threshold
                                ),
                                "status": status,
                                "emails": rule.notification_emails,
                            }
                        )

        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")

        return alerts

    # Helper methods
    def _parse_currency(self, value) -> Optional[Decimal]:
        """Parse currency string to Decimal"""
        if pd.isna(value) or value == "" or value == 0:
            return None
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").strip()
        try:
            return Decimal(str(value))
        except:
            return None

    def _parse_number(self, value) -> Optional[float]:
        """Parse number string to float"""
        if pd.isna(value) or value == "":
            return None
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        try:
            return float(value)
        except:
            return None

    def _parse_percentage(self, value) -> Optional[float]:
        """Parse percentage string to float"""
        if pd.isna(value) or value == "":
            return None
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        try:
            return float(value) / 100
        except:
            return None

    def _upsert_store_performance(self, **kwargs):
        """Insert or update store performance record"""
        query = """
            INSERT INTO bi_store_performance 
            (period_ending, store_code, period_type, rental_revenue, total_revenue, 
             payroll_cost, wage_hours, labor_cost_ratio, revenue_per_hour, avg_wage_rate)
            VALUES 
            (:period_ending, :store_code, 'BIWEEKLY', :rental_revenue, :total_revenue,
             :payroll_cost, :wage_hours, :labor_cost_ratio, :revenue_per_hour, :avg_wage_rate)
            ON DUPLICATE KEY UPDATE
                rental_revenue = VALUES(rental_revenue),
                total_revenue = VALUES(total_revenue),
                payroll_cost = VALUES(payroll_cost),
                wage_hours = VALUES(wage_hours),
                labor_cost_ratio = VALUES(labor_cost_ratio),
                revenue_per_hour = VALUES(revenue_per_hour),
                avg_wage_rate = VALUES(avg_wage_rate),
                updated_at = CURRENT_TIMESTAMP
        """
        db.session.execute(text(query), kwargs)
        db.session.commit()

    def _upsert_operational_scorecard(self, **kwargs):
        """Insert or update operational scorecard record"""
        query = """
            INSERT INTO bi_operational_scorecard
            (week_ending, store_code, new_contracts_count, reservation_pipeline_14d,
             reservation_pipeline_total, ar_over_45_days_pct, discount_total)
            VALUES
            (:week_ending, :store_code, :new_contracts_count, :reservation_pipeline_14d,
             :reservation_pipeline_total, :ar_over_45_days_pct, :discount_total)
            ON DUPLICATE KEY UPDATE
                new_contracts_count = VALUES(new_contracts_count),
                reservation_pipeline_14d = VALUES(reservation_pipeline_14d),
                reservation_pipeline_total = VALUES(reservation_pipeline_total),
                ar_over_45_days_pct = VALUES(ar_over_45_days_pct),
                discount_total = VALUES(discount_total),
                updated_at = CURRENT_TIMESTAMP
        """
        db.session.execute(text(query), kwargs)
        db.session.commit()

    def _upsert_executive_kpis(self, **kwargs):
        """Insert or update executive KPIs"""
        query = """
            INSERT INTO bi_executive_kpis
            (period_ending, period_type, total_revenue, rental_revenue, revenue_growth_pct,
             gross_margin_pct, ebitda_margin_pct, labor_cost_ratio, store_rankings,
             best_performing_store)
            VALUES
            (:period_ending, :period_type, :total_revenue, :rental_revenue, :revenue_growth_pct,
             :gross_margin_pct, :ebitda_margin_pct, :labor_cost_ratio, :store_rankings,
             :best_performing_store)
            ON DUPLICATE KEY UPDATE
                total_revenue = VALUES(total_revenue),
                rental_revenue = VALUES(rental_revenue),
                revenue_growth_pct = VALUES(revenue_growth_pct),
                gross_margin_pct = VALUES(gross_margin_pct),
                ebitda_margin_pct = VALUES(ebitda_margin_pct),
                labor_cost_ratio = VALUES(labor_cost_ratio),
                store_rankings = VALUES(store_rankings),
                best_performing_store = VALUES(best_performing_store),
                updated_at = CURRENT_TIMESTAMP
        """
        db.session.execute(text(query), kwargs)
        db.session.commit()

    def _upsert_inventory_performance(self, **kwargs):
        """Insert or update inventory performance record"""
        query = """
            INSERT INTO bi_inventory_performance
            (period_ending, store_code, rental_class, total_units, available_units,
             on_rent_units, in_repair_units, utilization_rate, turnover_rate,
             inventory_value, rental_revenue, roi_percentage, revenue_per_unit, repair_cost)
            VALUES
            (:period_ending, :store_code, :rental_class, :total_units, :available_units,
             :on_rent_units, :in_repair_units, :utilization_rate, :turnover_rate,
             :inventory_value, :rental_revenue, :roi_percentage, :revenue_per_unit, :repair_cost)
            ON DUPLICATE KEY UPDATE
                total_units = VALUES(total_units),
                available_units = VALUES(available_units),
                on_rent_units = VALUES(on_rent_units),
                in_repair_units = VALUES(in_repair_units),
                utilization_rate = VALUES(utilization_rate),
                turnover_rate = VALUES(turnover_rate),
                inventory_value = VALUES(inventory_value),
                rental_revenue = VALUES(rental_revenue),
                roi_percentage = VALUES(roi_percentage),
                revenue_per_unit = VALUES(revenue_per_unit),
                repair_cost = VALUES(repair_cost),
                updated_at = CURRENT_TIMESTAMP
        """
        db.session.execute(text(query), kwargs)
        db.session.commit()

    def _upsert_prediction(self, **kwargs):
        """Insert or update prediction"""
        query = """
            INSERT INTO bi_predictive_analytics
            (forecast_date, target_date, store_code, metric_name, predicted_value,
             confidence_low, confidence_high, confidence_level, model_type)
            VALUES
            (:forecast_date, :target_date, :store_code, :metric_name, :predicted_value,
             :confidence_low, :confidence_high, :confidence_level, :model_type)
            ON DUPLICATE KEY UPDATE
                predicted_value = VALUES(predicted_value),
                confidence_low = VALUES(confidence_low),
                confidence_high = VALUES(confidence_high),
                confidence_level = VALUES(confidence_level),
                model_type = VALUES(model_type),
                updated_at = CURRENT_TIMESTAMP
        """
        db.session.execute(text(query), kwargs)
        db.session.commit()

    def _log_import(self, import_type: str, file_name: str, stats: Dict):
        """Log import activity"""
        query = """
            INSERT INTO bi_import_log
            (import_type, file_name, records_processed, records_imported,
             records_skipped, records_error, status, completed_at)
            VALUES
            (:import_type, :file_name, :records_processed, :records_imported,
             :records_skipped, :records_error, :status, NOW())
        """

        db.session.execute(
            text(query),
            {
                "import_type": import_type,
                "file_name": file_name,
                "records_processed": stats.get("records_processed", 0),
                "records_imported": stats.get("records_imported", 0),
                "records_skipped": stats.get("records_skipped", 0),
                "records_error": len(stats.get("errors", [])),
                "status": (
                    "COMPLETED" if not stats.get("errors") else "COMPLETED_WITH_ERRORS"
                ),
            },
        )
        db.session.commit()

    def _calculate_growth(
        self, current_date: date, metric: str, current_value: float
    ) -> Optional[float]:
        """Calculate period-over-period growth"""
        try:
            # Get previous period value (2 weeks ago for biweekly)
            prev_date = current_date - timedelta(days=14)
            query = """
                SELECT total_revenue 
                FROM bi_store_performance 
                WHERE period_ending = :prev_date
            """
            result = db.session.execute(
                text(query), {"prev_date": prev_date}
            ).fetchone()

            if result and result[0]:
                prev_value = float(result[0])
                if prev_value > 0:
                    return ((current_value - prev_value) / prev_value) * 100
        except Exception as e:
            self.logger.error(f"Error calculating growth: {e}")

        return None

    def _get_store_rankings(self, period_ending: date) -> List[Dict]:
        """Get store performance rankings"""
        query = """
            SELECT 
                store_code,
                total_revenue,
                labor_cost_ratio,
                revenue_per_hour
            FROM bi_store_performance
            WHERE period_ending = :period_date
            ORDER BY total_revenue DESC
        """

        results = db.session.execute(
            text(query), {"period_date": period_ending}
        ).fetchall()

        rankings = []
        for i, row in enumerate(results, 1):
            rankings.append(
                {
                    "rank": i,
                    "store": row.store_code,
                    "revenue": float(row.total_revenue) if row.total_revenue else 0,
                    "efficiency": (
                        float(row.revenue_per_hour) if row.revenue_per_hour else 0
                    ),
                }
            )

        return rankings

    def _calculate_class_revenue(
        self, store_code: str, rental_class: str, period_ending: date
    ) -> float:
        """Calculate revenue for a specific rental class"""
        # This would need to integrate with transaction data
        # For now, returning estimated value based on turnover
        return 0.0

    def _get_historical_data(
        self, metric: str, store_code: Optional[str]
    ) -> List[Tuple]:
        """Get historical data for a metric"""
        table_map = {
            "total_revenue": "bi_store_performance",
            "new_contracts_count": "bi_operational_scorecard",
            "utilization_rate": "bi_inventory_performance",
        }

        table = table_map.get(metric)
        if not table:
            return []

        query = f"""
            SELECT period_ending, {metric}
            FROM {table}
            WHERE {metric} IS NOT NULL
            {'AND store_code = :store_code' if store_code else ''}
            ORDER BY period_ending DESC
            LIMIT 52
        """

        params = {"store_code": store_code} if store_code else {}
        results = db.session.execute(text(query), params).fetchall()

        return [(r[0], r[1]) for r in results]

    def _get_current_metric_value(
        self, metric_name: str, store_code: Optional[str]
    ) -> Optional[float]:
        """Get current value for a metric"""
        # Map metric to appropriate table and column
        metric_queries = {
            "utilization_rate": """
                SELECT AVG(utilization_rate) 
                FROM bi_inventory_performance 
                WHERE period_ending = (SELECT MAX(period_ending) FROM bi_inventory_performance)
                {store_filter}
            """,
            "labor_cost_ratio": """
                SELECT AVG(labor_cost_ratio)
                FROM bi_store_performance
                WHERE period_ending = (SELECT MAX(period_ending) FROM bi_store_performance)
                {store_filter}
            """,
            "ar_over_45_days_pct": """
                SELECT ar_over_45_days_pct
                FROM bi_operational_scorecard
                WHERE week_ending = (SELECT MAX(week_ending) FROM bi_operational_scorecard)
                {store_filter}
                LIMIT 1
            """,
            "revenue_growth_pct": """
                SELECT revenue_growth_pct
                FROM bi_executive_kpis
                WHERE period_ending = (SELECT MAX(period_ending) FROM bi_executive_kpis)
            """,
        }

        query_template = metric_queries.get(metric_name)
        if not query_template:
            return None

        store_filter = "AND store_code = :store_code" if store_code else ""
        query = query_template.format(store_filter=store_filter)

        params = {"store_code": store_code} if store_code else {}
        result = db.session.execute(text(query), params).fetchone()

        return float(result[0]) if result and result[0] else None

    def _update_alert_status(self, rule_id: int, status: str):
        """Update alert rule status"""
        query = """
            UPDATE bi_alert_rules
            SET current_status = :status,
                last_triggered = CASE WHEN :status != 'NORMAL' THEN NOW() ELSE last_triggered END
            WHERE id = :rule_id
        """
        db.session.execute(text(query), {"rule_id": rule_id, "status": status})
        db.session.commit()
