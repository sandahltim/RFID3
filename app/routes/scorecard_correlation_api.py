"""
Scorecard Correlation API Routes
Provides correlation insights for executive dashboard
"""

from flask import Blueprint, jsonify, request
from app.services.scorecard_correlation_service import get_scorecard_service
from datetime import datetime

scorecard_correlation_bp = Blueprint('scorecard_correlation', __name__, url_prefix='/api/scorecard')

@scorecard_correlation_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data with correlations"""
    try:
        service = get_scorecard_service()
        data = service.get_dashboard_data()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/store-metrics', methods=['GET'])
def get_store_metrics():
    """Get store performance metrics"""
    try:
        service = get_scorecard_service()
        metrics = service.get_store_performance_metrics()
        
        # Add rankings
        stores_by_revenue = sorted(metrics.items(), key=lambda x: x[1]['avg_weekly_revenue'], reverse=True)
        stores_by_efficiency = sorted(metrics.items(), key=lambda x: x[1]['revenue_per_contract'], reverse=True)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'rankings': {
                'by_revenue': [{'store': s[0], 'revenue': s[1]['avg_weekly_revenue']} for s in stores_by_revenue],
                'by_efficiency': [{'store': s[0], 'revenue_per_contract': s[1]['revenue_per_contract']} for s in stores_by_efficiency]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/revenue-prediction/<store_code>', methods=['GET'])
def get_revenue_prediction(store_code):
    """Get revenue prediction for a specific store"""
    try:
        service = get_scorecard_service()
        prediction = service.get_revenue_predictions(store_code)
        
        if prediction:
            return jsonify({
                'success': True,
                'store_code': store_code,
                'prediction': prediction
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Insufficient data for prediction'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/financial-health', methods=['GET'])
def get_financial_health():
    """Get financial health score and metrics"""
    try:
        service = get_scorecard_service()
        health = service.get_financial_health_score()
        
        if health:
            return jsonify({
                'success': True,
                'health': health
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No financial data available'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get executive alerts"""
    try:
        service = get_scorecard_service()
        alerts = service.get_executive_alerts()
        
        # Group alerts by type
        critical = [a for a in alerts if a['type'] == 'critical']
        warnings = [a for a in alerts if a['type'] == 'warning']
        
        return jsonify({
            'success': True,
            'alerts': {
                'critical': critical,
                'warning': warnings,
                'total': len(alerts)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/correlations', methods=['GET'])
def get_correlations():
    """Get correlation insights"""
    try:
        service = get_scorecard_service()
        insights = service.get_correlation_insights()
        
        # Group by type
        grouped = {}
        for insight in insights:
            insight_type = insight['type']
            if insight_type not in grouped:
                grouped[insight_type] = []
            grouped[insight_type].append(insight)
        
        return jsonify({
            'success': True,
            'insights': insights,
            'grouped': grouped,
            'total': len(insights)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/store-comparison', methods=['GET'])
def get_store_comparison():
    """Get detailed store comparison data"""
    try:
        service = get_scorecard_service()
        metrics = service.get_store_performance_metrics()
        
        # Calculate relative performance
        if metrics:
            avg_revenue = sum(m['avg_weekly_revenue'] for m in metrics.values()) / len(metrics)
            
            comparison = {}
            for store, data in metrics.items():
                comparison[store] = {
                    **data,
                    'revenue_vs_avg': round((data['avg_weekly_revenue'] / avg_revenue - 1) * 100, 1),
                    'performance_grade': 'A' if data['avg_weekly_revenue'] > avg_revenue * 1.2 else 
                                       'B' if data['avg_weekly_revenue'] > avg_revenue * 0.9 else 
                                       'C' if data['avg_weekly_revenue'] > avg_revenue * 0.7 else 'D'
                }
            
            return jsonify({
                'success': True,
                'comparison': comparison,
                'company_avg_revenue': round(avg_revenue, 2)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No store data available'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/store-timeline', methods=['GET'])
def get_store_timeline():
    """Get store timeline analysis with data quality insights"""
    try:
        service = get_scorecard_service()
        timeline = service.get_store_timeline_analysis()
        
        return jsonify({
            'success': True,
            'timeline_analysis': timeline,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scorecard_correlation_bp.route('/refresh', methods=['POST'])
def refresh_data():
    """Refresh the scorecard data"""
    try:
        # Reinitialize the service to reload data
        global _service_instance
        from app.services.scorecard_correlation_service import ScorecardCorrelationService
        _service_instance = ScorecardCorrelationService()
        
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500