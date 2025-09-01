"""
KVC Companies Executive Dashboard Routes
Comprehensive executive-level analytics for equipment rental business
Provides intelligent insights with external event correlation
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, date, timedelta
import json
from app import db
from app.services.financial_analytics_service import FinancialAnalyticsService
from app.services.executive_insights_service import ExecutiveInsightsService
from app.services.logger import get_logger

logger = get_logger(__name__)
executive_bp = Blueprint("executive", __name__, url_prefix="/executive")

# Initialize services
financial_service = FinancialAnalyticsService()
insights_service = ExecutiveInsightsService()


@executive_bp.route("/dashboard")
def executive_dashboard():
    """Main KVC Companies executive dashboard view"""
    try:
        # Get comprehensive executive financial dashboard
        dashboard_data = financial_service.get_executive_financial_dashboard()
        
        # Get intelligent insights with event correlation
        insights_data = insights_service.get_executive_insights()
        
        # Get store performance summary
        store_performance = financial_service.analyze_multi_store_performance(26)
        
        # Get real-time KPIs
        kpis = _get_executive_kpis()
        
        # Get recent financial alerts
        alerts = insights_service.get_financial_alerts()
        
        return render_template(
            "executive_dashboard.html",
            dashboard_data=dashboard_data,
            insights=insights_data,
            store_performance=store_performance,
            kpis=kpis,
            alerts=alerts,
            company_info={
                "name": "KVC Companies",
                "brands": ["A1 Rent It", "Broadway Tent & Event"],
                "locations": ["Wayzata", "Brooklyn Park", "Fridley", "Elk River"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading executive dashboard: {e}")
        return render_template(
            "executive_dashboard.html",
            error=f"Dashboard temporarily unavailable: {str(e)}",
            dashboard_data={"success": False},
            insights={"success": False},
            store_performance={"success": False}
        )


@executive_bp.route("/api/financial-kpis")
def api_financial_kpis():
    """API endpoint for executive financial KPIs"""
    try:
        # Get comprehensive financial analytics
        revenue_analysis = financial_service.calculate_rolling_averages('revenue', 26)
        yoy_analysis = financial_service.calculate_year_over_year_analysis('revenue')
        store_analysis = financial_service.analyze_multi_store_performance(26)
        
        # Extract key metrics
        kpis = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "revenue_metrics": {
                "current_3wk_avg": revenue_analysis.get("summary", {}).get("current_3wk_avg", 0),
                "growth_trend": revenue_analysis.get("summary", {}).get("smoothed_trend", 0),
                "yoy_growth": yoy_analysis.get("comparison_period", {}).get("overall_growth_rate", 0)
            },
            "store_metrics": {
                "top_performer": _get_top_performing_store(store_analysis),
                "store_count": len(financial_service.STORE_CODES),
                "utilization_avg": _calculate_avg_utilization(store_analysis)
            },
            "operational_health": {
                "health_score": _calculate_health_score(revenue_analysis, yoy_analysis),
                "trend_direction": "up" if revenue_analysis.get("summary", {}).get("smoothed_trend", 0) > 0 else "down"
            }
        }
        
        return jsonify(kpis)
        
    except Exception as e:
        logger.error(f"Error fetching financial KPIs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/intelligent-insights")
def api_intelligent_insights():
    """API endpoint for intelligent business insights with event correlation"""
    try:
        # Get insights with external event correlation
        insights = insights_service.analyze_financial_anomalies_with_context()
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error fetching intelligent insights: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/store-comparison")
def api_store_comparison():
    """API endpoint for store performance comparison"""
    try:
        analysis_period = int(request.args.get("weeks", 26))
        
        # Get comprehensive store analysis
        store_data = financial_service.analyze_multi_store_performance(analysis_period)
        
        if not store_data.get("success"):
            return jsonify({"success": False, "error": "Store analysis unavailable"}), 500
        
        # Format for executive dashboard
        comparison_data = {
            "success": True,
            "analysis_period_weeks": analysis_period,
            "stores": []
        }
        
        store_metrics = store_data.get("store_metrics", {})
        benchmarks = store_data.get("performance_benchmarks", {})
        
        for store_name, metrics in store_metrics.items():
            financial = metrics.get("financial_metrics", {})
            operational = metrics.get("operational_metrics", {})
            
            store_info = {
                "name": store_name,
                "store_code": metrics.get("store_code", ""),
                "revenue": {
                    "total": financial.get("total_revenue", 0),
                    "weekly_avg": financial.get("avg_weekly_revenue", 0),
                    "per_contract": financial.get("revenue_per_contract", 0)
                },
                "profitability": {
                    "gross_profit": financial.get("gross_profit", 0),
                    "margin_pct": financial.get("profit_margin", 0)
                },
                "efficiency": {
                    "revenue_per_hour": operational.get("revenue_per_hour", 0),
                    "contracts_per_hour": operational.get("contracts_per_hour", 0),
                    "total_contracts": operational.get("total_contracts", 0)
                },
                "ranking": benchmarks.get("store_rankings", {}).get(store_name, {})
            }
            
            comparison_data["stores"].append(store_info)
        
        # Sort by overall performance
        comparison_data["stores"].sort(
            key=lambda x: x["ranking"].get("overall_score", 0), 
            reverse=True
        )
        
        return jsonify(comparison_data)
        
    except Exception as e:
        logger.error(f"Error fetching store comparison: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/financial-forecasts")
def api_financial_forecasts():
    """API endpoint for financial forecasting"""
    try:
        horizon_weeks = int(request.args.get("weeks", 12))
        confidence_level = float(request.args.get("confidence", 0.95))
        
        # Get financial forecasts
        forecasts = financial_service.generate_financial_forecasts(
            horizon_weeks, confidence_level
        )
        
        return jsonify(forecasts)
        
    except Exception as e:
        logger.error(f"Error fetching financial forecasts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/custom-insight", methods=["POST"])
def api_add_custom_insight():
    """API endpoint for adding custom business insights"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Add custom insight through insights service
        result = insights_service.add_custom_insight(
            date=data.get("date"),
            event_type=data.get("event_type"),
            description=data.get("description"),
            impact_category=data.get("impact_category"),
            impact_magnitude=data.get("impact_magnitude"),
            user_notes=data.get("user_notes")
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding custom insight: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/dashboard-config", methods=["GET", "POST"])
def api_dashboard_config():
    """API endpoint for dashboard configuration management"""
    try:
        if request.method == "GET":
            # Get current dashboard configuration
            config = insights_service.get_dashboard_configuration()
            return jsonify(config)
            
        elif request.method == "POST":
            # Update dashboard configuration
            data = request.get_json()
            result = insights_service.update_dashboard_configuration(data)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error managing dashboard config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Helper functions
def _get_executive_kpis():
    """Get high-level executive KPIs"""
    try:
        # Get recent financial data for KPIs
        revenue_data = financial_service.calculate_rolling_averages('revenue', 4)
        
        if not revenue_data.get("success"):
            return {"error": "KPI data unavailable"}
        
        summary = revenue_data.get("summary", {})
        
        return {
            "revenue": {
                "current_3wk_avg": summary.get("current_3wk_avg", 0),
                "trend": summary.get("smoothed_trend", 0),
                "status": "up" if summary.get("smoothed_trend", 0) > 0 else "down"
            },
            "contracts": {
                "weekly_avg": summary.get("avg_weekly_contracts", 0),
                "velocity": summary.get("contract_velocity_trend", 0)
            },
            "stores": {
                "total": len(financial_service.STORE_CODES),
                "performance_spread": "normal"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting executive KPIs: {e}")
        return {"error": str(e)}


def _get_top_performing_store(store_analysis):
    """Get the top performing store from analysis"""
    try:
        if not store_analysis.get("success") or not store_analysis.get("performance_benchmarks"):
            return "Data unavailable"
        
        rankings = store_analysis["performance_benchmarks"].get("store_rankings", {})
        
        if not rankings:
            return "Analysis unavailable"
        
        # Find store with rank 1
        for store_name, ranking in rankings.items():
            if ranking.get("overall_rank") == 1:
                return store_name
        
        return "No data"
        
    except Exception as e:
        logger.error(f"Error getting top performing store: {e}")
        return "Error"


def _calculate_avg_utilization(store_analysis):
    """Calculate average utilization across all stores"""
    try:
        if not store_analysis.get("success"):
            return 0
        
        store_metrics = store_analysis.get("store_metrics", {})
        
        if not store_metrics:
            return 0
        
        # Use efficiency scores as proxy for utilization
        total_efficiency = 0
        count = 0
        
        for metrics in store_metrics.values():
            efficiency_scores = metrics.get("efficiency_scores", {})
            if "revenue_efficiency" in efficiency_scores:
                total_efficiency += efficiency_scores["revenue_efficiency"]
                count += 1
        
        return round(total_efficiency / max(count, 1), 1)
        
    except Exception as e:
        logger.error(f"Error calculating average utilization: {e}")
        return 0


def _calculate_health_score(revenue_analysis, yoy_analysis):
    """Calculate overall business health score"""
    try:
        score = 75  # Base score
        
        # Revenue trend component
        if revenue_analysis.get("success"):
            trend = revenue_analysis.get("summary", {}).get("smoothed_trend", 0)
            if trend > 5:
                score += 15
            elif trend > 0:
                score += 5
            elif trend < -5:
                score -= 15
            elif trend < 0:
                score -= 5
        
        # YoY growth component
        if yoy_analysis.get("success"):
            growth = yoy_analysis.get("comparison_period", {}).get("overall_growth_rate", 0)
            if growth > 10:
                score += 10
            elif growth > 0:
                score += 5
            elif growth < -10:
                score -= 15
            elif growth < 0:
                score -= 5
        
        return max(0, min(100, score))
        
    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        return 75