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
from app.services.enhanced_executive_service import EnhancedExecutiveService
from app.services.data_reconciliation_service import DataReconciliationService
# from app.services.predictive_analytics_service import PredictiveAnalyticsService  # Temporarily disabled due to sklearn dependency
from app.services.logger import get_logger
from app.models.config_models import ExecutiveDashboardConfiguration, get_default_executive_dashboard_config

logger = get_logger(__name__)
executive_bp = Blueprint("executive", __name__, url_prefix="/executive")

# Initialize services
financial_service = FinancialAnalyticsService()
insights_service = ExecutiveInsightsService()
enhanced_service = EnhancedExecutiveService()
reconciliation_service = DataReconciliationService()
# predictive_service = PredictiveAnalyticsService()  # Temporarily disabled


@executive_bp.route("/dashboard")
def executive_dashboard():
    """Main KVC Companies executive dashboard view"""
    try:
        # Get comprehensive executive financial dashboard
        dashboard_data = financial_service.get_executive_financial_dashboard()
        
        # Get intelligent insights with event correlation
        insights_data = insights_service.get_executive_insights()
        
        # Get store performance summary
        # OLD - HARDCODED (WRONG): store_performance = financial_service.analyze_multi_store_performance(26)
        # NEW - CONFIGURABLE (CORRECT):
        config = _get_dashboard_config()
        analysis_period = int(config.get_store_threshold('default', 'default_analysis_period_weeks'))
        store_performance = financial_service.analyze_multi_store_performance(analysis_period)
        
        # Get real-time KPIs
        kpis = _get_executive_kpis()
        
        # Get recent financial alerts
        alerts = insights_service.get_financial_alerts()
        
        # Get dashboard display configuration
        dashboard_config = {
            'current_week_view_enabled': config.current_week_view_enabled
        }
        
        return render_template(
            "executive_dashboard.html",
            dashboard_data=dashboard_data,
            insights=insights_data,
            store_performance=store_performance,
            kpis=kpis,
            alerts=alerts,
            dashboard_config=dashboard_config,
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
        # OLD - HARDCODED (WRONG): revenue_analysis = financial_service.calculate_rolling_averages('revenue', 26)
        # NEW - CONFIGURABLE (CORRECT):
        config = _get_dashboard_config()
        analysis_period = int(config.get_store_threshold('default', 'default_analysis_period_weeks'))
        revenue_analysis = financial_service.calculate_rolling_averages('revenue', analysis_period)
        yoy_analysis = financial_service.calculate_year_over_year_analysis('revenue')
        # OLD - HARDCODED (WRONG): store_analysis = financial_service.analyze_multi_store_performance(26)
        # NEW - CONFIGURABLE (CORRECT):
        store_analysis = financial_service.analyze_multi_store_performance(analysis_period)
        
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
        # OLD - HARDCODED (WRONG): analysis_period = int(request.args.get("weeks", 26))
        # NEW - CONFIGURABLE (CORRECT):
        config = _get_dashboard_config()
        default_weeks = int(config.get_store_threshold('default', 'default_analysis_period_weeks'))
        analysis_period = int(request.args.get("weeks", default_weeks))
        
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
        # OLD - HARDCODED (WRONG): horizon_weeks = int(request.args.get("weeks", 12))
        # NEW - CONFIGURABLE (CORRECT):
        config = _get_dashboard_config()
        default_horizon = config.get_store_threshold('default', 'default_forecast_horizon_weeks')
        horizon_weeks = int(request.args.get("weeks", default_horizon))
        # OLD - HARDCODED (WRONG): confidence_level = float(request.args.get("confidence", 0.95))
        # NEW - CONFIGURABLE (CORRECT):
        default_confidence = config.get_store_threshold('default', 'default_confidence_level')
        confidence_level = float(request.args.get("confidence", default_confidence))
        
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


@executive_bp.route("/api/enhanced-dashboard")
def api_enhanced_dashboard():
    """API endpoint for enhanced executive dashboard with correlation data"""
    try:
        enhanced_data = enhanced_service.get_executive_dashboard_with_correlations()
        return jsonify(enhanced_data)
        
    except Exception as e:
        logger.error(f"Error fetching enhanced dashboard: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/equipment-roi")
def api_equipment_roi():
    """API endpoint for equipment-level ROI analysis"""
    try:
        roi_analysis = enhanced_service.get_equipment_roi_analysis()
        return jsonify(roi_analysis)
        
    except Exception as e:
        logger.error(f"Error fetching equipment ROI: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/correlation-quality")
def api_correlation_quality():
    """API endpoint for correlation quality metrics"""
    try:
        quality_metrics = enhanced_service.get_correlation_quality_metrics()
        return jsonify(quality_metrics)
        
    except Exception as e:
        logger.error(f"Error fetching correlation quality: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/real-time-utilization")
def api_real_time_utilization():
    """API endpoint for real-time utilization metrics"""
    try:
        utilization_data = enhanced_service.get_real_time_utilization_metrics()
        return jsonify(utilization_data)
        
    except Exception as e:
        logger.error(f"Error fetching real-time utilization: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/enhanced-kpis")
def api_enhanced_kpis():
    """API endpoint for enhanced executive KPIs using correlation data"""
    try:
        enhanced_kpis = enhanced_service.get_enhanced_executive_kpis()
        
        # Add accurate correlation coverage note
        if enhanced_kpis.get('success'):
            # OLD - HARDCODED (WRONG): enhanced_kpis['coverage_note'] = 'Based on 1.78% RFID correlation coverage (290 of 16,259 items)'
            # NEW - CONFIGURABLE (CORRECT):
            config = _get_dashboard_config()
            coverage_pct = config.get_store_threshold('default', 'rfid_coverage_percentage')
            correlated_items = int(config.get_store_threshold('default', 'rfid_correlated_items'))
            total_items = int(config.get_store_threshold('default', 'total_equipment_items'))
            enhanced_kpis['coverage_note'] = f'Based on {coverage_pct}% RFID correlation coverage ({correlated_items} of {total_items:,} items)'
            enhanced_kpis['data_transparency'] = {
                # OLD - HARDCODED (WRONG): 'rfid_correlated_items': 290, 'total_equipment_items': 16259, 'coverage_percentage': 1.78,
                # NEW - CONFIGURABLE (CORRECT):
                'rfid_correlated_items': correlated_items,
                'total_equipment_items': total_items,
                'coverage_percentage': coverage_pct,
                'pos_estimated_items': 15969
            }
        
        return jsonify(enhanced_kpis)
        
    except Exception as e:
        logger.error(f"Error fetching enhanced KPIs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/data-reconciliation")
def api_data_reconciliation():
    """API endpoint for data reconciliation between POS, RFID, and Financial systems"""
    try:
        report_type = request.args.get('type', 'revenue')
        
        if report_type == 'revenue':
            result = reconciliation_service.get_revenue_reconciliation()
        elif report_type == 'utilization':
            result = reconciliation_service.get_utilization_reconciliation()
        elif report_type == 'comprehensive':
            result = reconciliation_service.get_comprehensive_reconciliation_report()
        else:
            result = reconciliation_service.get_revenue_reconciliation()
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in data reconciliation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/predictive-forecasts")
def api_predictive_forecasts():
    """API endpoint for predictive analytics and forecasting"""
    try:
        # OLD - HARDCODED (WRONG): horizon_weeks = int(request.args.get('horizon', 12))
        # NEW - CONFIGURABLE (CORRECT):
        config = _get_dashboard_config()
        default_horizon = config.get_store_threshold('default', 'default_forecast_horizon_weeks')
        horizon_weeks = int(request.args.get('horizon', default_horizon))
        analysis_type = request.args.get('type', 'revenue')
        
        if analysis_type == 'revenue':
            result = predictive_service.generate_revenue_forecasts(horizon_weeks)
        elif analysis_type == 'demand':
            result = predictive_service.predict_equipment_demand()
        elif analysis_type == 'utilization':
            result = predictive_service.analyze_utilization_opportunities()
        elif analysis_type == 'comprehensive':
            result = predictive_service.get_predictive_dashboard_data()
        else:
            result = predictive_service.generate_revenue_forecasts(horizon_weeks)
        
        return jsonify(result)
        
    except ValueError as e:
        logger.warning(f"Invalid parameter in predictive forecasts: {e}")
        return jsonify({"success": False, "error": "Invalid parameters"}), 400
    except Exception as e:
        logger.error(f"Error in predictive forecasts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@executive_bp.route("/api/multi-timeframe")
def api_multi_timeframe():
    """API endpoint for multi-timeframe financial analysis"""
    try:
        timeframe = request.args.get('timeframe', 'weekly')  # daily, weekly, monthly, quarterly, yearly
        metric = request.args.get('metric', 'revenue')
        # OLD - HARDCODED (WRONG): periods = int(request.args.get('periods', 26))
        # NEW - CONFIGURABLE (CORRECT):
        config = _get_dashboard_config()
        default_periods = int(config.get_store_threshold('default', 'default_analysis_period_weeks'))
        periods = int(request.args.get('periods', default_periods))
        
        # Map timeframes to appropriate analysis periods
        timeframe_mapping = {
            'daily': periods // 7,  # Convert to weeks for existing service
            'weekly': periods,
            'monthly': periods // 4,  # Convert to approximate months
            'quarterly': periods // 13,  # Convert to quarters
            'yearly': min(periods // 52, 3)  # Max 3 years of data
        }
        
        analysis_periods = timeframe_mapping.get(timeframe, periods)
        
        if timeframe == 'yearly':
            result = financial_service.calculate_year_over_year_analysis(metric)
        else:
            result = financial_service.calculate_rolling_averages(metric, analysis_periods)
        
        # Add timeframe metadata
        if result.get('success'):
            result['timeframe_info'] = {
                'requested_timeframe': timeframe,
                'requested_periods': periods,
                'analysis_periods': analysis_periods,
                'metric': metric,
                'data_sources': 'Scorecard (196 weeks), P&L (1,818 records), Payroll (328 records)'
            }
        
        return jsonify(result)
        
    except ValueError as e:
        logger.warning(f"Invalid parameter in multi-timeframe: {e}")
        return jsonify({"success": False, "error": "Invalid parameters"}), 400
    except Exception as e:
        logger.error(f"Error in multi-timeframe analysis: {e}")
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
        # Get configuration with safe defaults
        config = _get_dashboard_config()
        
        # OLD - HARDCODED (WRONG): score = 75  # Base score
        # NEW - CONFIGURABLE (CORRECT):
        score = config.get_store_threshold('default', 'base_health_score')
        
        # Revenue trend component
        if revenue_analysis.get("success"):
            trend = revenue_analysis.get("summary", {}).get("smoothed_trend", 0)
            
            # OLD - HARDCODED (WRONG): if trend > 5: / elif trend > 0: / elif trend < -5: / elif trend < 0:
            # NEW - CONFIGURABLE (CORRECT):
            strong_positive_threshold = config.get_store_threshold('default', 'strong_positive_trend_threshold')
            strong_negative_threshold = config.get_store_threshold('default', 'strong_negative_trend_threshold')
            
            if trend > strong_positive_threshold:
                score += config.get_store_threshold('default', 'strong_positive_trend_points')
            elif trend > 0:
                score += config.get_store_threshold('default', 'weak_positive_trend_points')
            elif trend < strong_negative_threshold:
                score += config.get_store_threshold('default', 'strong_negative_trend_points')  # Already negative value
            elif trend < 0:
                score += config.get_store_threshold('default', 'weak_negative_trend_points')  # Already negative value
        
        # YoY growth component
        if yoy_analysis.get("success"):
            growth = yoy_analysis.get("comparison_period", {}).get("overall_growth_rate", 0)
            
            # OLD - HARDCODED (WRONG): if growth > 10: / elif growth > 0: / elif growth < -10: / elif growth < 0:
            # NEW - CONFIGURABLE (CORRECT):
            strong_growth_threshold = config.get_store_threshold('default', 'strong_growth_threshold')
            strong_decline_threshold = config.get_store_threshold('default', 'strong_decline_threshold')
            
            if growth > strong_growth_threshold:
                score += config.get_store_threshold('default', 'strong_growth_points')
            elif growth > 0:
                score += config.get_store_threshold('default', 'weak_growth_points')
            elif growth < strong_decline_threshold:
                score += config.get_store_threshold('default', 'strong_decline_points')  # Already negative value
            elif growth < 0:
                score += config.get_store_threshold('default', 'weak_decline_points')  # Already negative value
        
        # Apply min/max bounds from configuration
        min_score = config.get_store_threshold('default', 'min_health_score')
        max_score = config.get_store_threshold('default', 'max_health_score')
        return max(min_score, min(max_score, score))
        
    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        return 75


def _get_dashboard_config():
    """Get executive dashboard configuration with safe defaults"""
    try:
        config = ExecutiveDashboardConfiguration.query.filter_by(
            user_id='default_user', 
            config_name='default'
        ).first()
        
        if config:
            return config
            
        # Create a mock config object with default values if none exists
        class MockConfig:
            def __init__(self):
                defaults = get_default_executive_dashboard_config()
                self.base_health_score = defaults['health_scoring']['base_score']
                self.strong_positive_trend_threshold = defaults['health_scoring']['strong_positive_trend_threshold']
                self.strong_positive_trend_points = defaults['health_scoring']['strong_positive_trend_points']
                self.weak_positive_trend_points = defaults['health_scoring']['weak_positive_trend_points']
                self.strong_negative_trend_threshold = defaults['health_scoring']['strong_negative_trend_threshold']
                self.strong_negative_trend_points = defaults['health_scoring']['strong_negative_trend_points']
                self.weak_negative_trend_points = defaults['health_scoring']['weak_negative_trend_points']
                self.strong_growth_threshold = defaults['health_scoring']['strong_growth_threshold']
                self.strong_growth_points = defaults['health_scoring']['strong_growth_points']
                self.weak_growth_points = defaults['health_scoring']['weak_growth_points']
                self.strong_decline_threshold = defaults['health_scoring']['strong_decline_threshold']
                self.strong_decline_points = defaults['health_scoring']['strong_decline_points']
                self.weak_decline_points = defaults['health_scoring']['weak_decline_points']
                self.default_forecast_horizon_weeks = defaults['forecasting']['default_horizon_weeks']
                self.default_confidence_level = defaults['forecasting']['default_confidence_level']
                self.default_analysis_period_weeks = defaults['analysis']['default_period_weeks']
                self.rfid_coverage_percentage = defaults['rfid_coverage']['coverage_percentage']
                self.rfid_correlated_items = defaults['rfid_coverage']['correlated_items']
                self.total_equipment_items = defaults['rfid_coverage']['total_equipment_items']
                self.min_health_score = 0.0
                self.max_health_score = 100.0
                self.current_week_view_enabled = defaults['display']['current_week_view_enabled']
                
            def get_store_threshold(self, store_code: str, threshold_type: str):
                return getattr(self, threshold_type, 75.0)
        
        return MockConfig()
        
    except Exception as e:
        logger.warning(f"Failed to load executive dashboard config: {e}. Using defaults.")
        # Create a mock config with hardcoded defaults as fallback
        class MockConfig:
            def __init__(self):
                self.base_health_score = 75.0
                self.strong_positive_trend_threshold = 5.0
                self.strong_positive_trend_points = 15
                self.weak_positive_trend_points = 5
                self.strong_negative_trend_threshold = -5.0
                self.strong_negative_trend_points = -15
                self.weak_negative_trend_points = -5
                self.strong_growth_threshold = 10.0
                self.strong_growth_points = 10
                self.weak_growth_points = 5
                self.strong_decline_threshold = -10.0
                self.strong_decline_points = -15
                self.weak_decline_points = -5
                self.default_forecast_horizon_weeks = 12
                self.default_confidence_level = 0.95
                self.default_analysis_period_weeks = 26
                self.current_week_view_enabled = True
                self.rfid_coverage_percentage = 1.78
                self.rfid_correlated_items = 290
                self.total_equipment_items = 16259
                self.min_health_score = 0.0
                self.max_health_score = 100.0
                
            def get_store_threshold(self, store_code: str, threshold_type: str):
                return getattr(self, threshold_type, 75.0)
        
        return MockConfig()