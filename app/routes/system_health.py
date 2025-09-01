"""
System Health Check and Monitoring Endpoints
Comprehensive health monitoring for RFID3 Analytics Framework
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import psutil
import os
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

system_health_bp = Blueprint('system_health', __name__)

@system_health_bp.route('/api/health/status', methods=['GET'])
def health_status():
    """Comprehensive system health check"""
    try:
        health_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy',
            'checks': {},
            'performance': {}
        }
        
        # Database connectivity check
        try:
            result = db.session.execute(text('SELECT 1')).fetchone()
            health_data['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_data['status'] = 'degraded'
        
        # Memory usage check
        memory_info = psutil.virtual_memory()
        memory_usage_percent = memory_info.percent
        health_data['performance']['memory'] = {
            'used_percent': memory_usage_percent,
            'available_gb': memory_info.available / 1024 / 1024 / 1024,
            'status': 'healthy' if memory_usage_percent < 85 else 'warning'
        }
        
        # CPU usage check
        cpu_usage = psutil.cpu_percent(interval=1)
        health_data['performance']['cpu'] = {
            'usage_percent': cpu_usage,
            'status': 'healthy' if cpu_usage < 80 else 'warning'
        }
        
        # Disk usage check
        disk_usage = psutil.disk_usage('/')
        disk_usage_percent = disk_usage.used / disk_usage.total * 100
        health_data['performance']['disk'] = {
            'used_percent': disk_usage_percent,
            'free_gb': disk_usage.free / 1024 / 1024 / 1024,
            'status': 'healthy' if disk_usage_percent < 85 else 'warning'
        }
        
        # Analytics services check
        try:
            from app.services.multi_store_analytics_service import MultiStoreAnalyticsService
            from app.services.financial_analytics_service import FinancialAnalyticsService
            
            # Quick service initialization test
            multi_store = MultiStoreAnalyticsService()
            financial = FinancialAnalyticsService()
            
            health_data['checks']['analytics_services'] = {
                'status': 'healthy',
                'message': 'Analytics services operational'
            }
        except Exception as e:
            health_data['checks']['analytics_services'] = {
                'status': 'unhealthy',
                'message': f'Analytics services error: {str(e)}'
            }
            health_data['status'] = 'degraded'
        
        # Data integrity check
        try:
            # Check key data tables
            table_counts = {}
            key_tables = ['pos_transactions', 'pos_transaction_items', 'pos_profit_loss']
            
            for table in key_tables:
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()
                    table_counts[table] = result[0]
                except:
                    table_counts[table] = 0
            
            health_data['checks']['data_integrity'] = {
                'status': 'healthy' if sum(table_counts.values()) > 0 else 'warning',
                'table_counts': table_counts,
                'message': 'Data integrity check completed'
            }
            
        except Exception as e:
            health_data['checks']['data_integrity'] = {
                'status': 'unhealthy',
                'message': f'Data integrity check failed: {str(e)}'
            }
        
        # Overall status determination
        unhealthy_checks = [check for check in health_data['checks'].values() if check['status'] == 'unhealthy']
        warning_checks = [check for check in health_data['checks'].values() if check['status'] == 'warning']
        
        if unhealthy_checks:
            health_data['status'] = 'unhealthy'
        elif warning_checks:
            health_data['status'] = 'degraded'
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@system_health_bp.route('/api/health/metrics', methods=['GET'])
def system_metrics():
    """Detailed system performance metrics"""
    try:
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'uptime_seconds': psutil.boot_time(),
                'processes': len(psutil.pids()),
                'cpu_cores': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024
            },
            'database': {},
            'analytics': {}
        }
        
        # Database metrics
        try:
            # Get database table sizes
            result = db.session.execute(text("""
                SELECT table_name, table_rows, data_length, index_length
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY data_length DESC 
                LIMIT 10
            """)).fetchall()
            
            metrics['database']['top_tables'] = [
                {
                    'table_name': row[0],
                    'rows': row[1],
                    'data_size_mb': (row[2] or 0) / 1024 / 1024,
                    'index_size_mb': (row[3] or 0) / 1024 / 1024
                }
                for row in result
            ]
            
        except Exception as e:
            metrics['database']['error'] = str(e)
        
        # Analytics performance metrics
        try:
            from app.services.financial_analytics_service import FinancialAnalyticsService
            
            start_time = datetime.now()
            financial = FinancialAnalyticsService()
            dashboard_data = financial.get_executive_financial_dashboard()
            end_time = datetime.now()
            
            metrics['analytics']['financial_dashboard_response_ms'] = (end_time - start_time).total_seconds() * 1000
            metrics['analytics']['financial_data_points'] = len(dashboard_data) if dashboard_data else 0
            
        except Exception as e:
            metrics['analytics']['error'] = str(e)
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@system_health_bp.route('/api/health/services', methods=['GET'])
def services_status():
    """Check status of all analytics services"""
    try:
        services_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Test each analytics service
        services_to_test = [
            ('MultiStoreAnalyticsService', 'app.services.multi_store_analytics_service'),
            ('FinancialAnalyticsService', 'app.services.financial_analytics_service'),
            ('BusinessAnalyticsService', 'app.services.business_analytics_service'),
            ('EquipmentCategorizationService', 'app.services.equipment_categorization_service'),
            ('MinnesotaIndustryAnalytics', 'app.services.minnesota_industry_analytics')
        ]
        
        for service_name, module_path in services_to_test:
            try:
                module_name = module_path.split('.')[-1]
                module = __import__(module_path, fromlist=[service_name])
                service_class = getattr(module, service_name)
                
                # Try to initialize the service
                start_time = datetime.now()
                service_instance = service_class()
                end_time = datetime.now()
                
                services_status['services'][service_name] = {
                    'status': 'operational',
                    'initialization_time_ms': (end_time - start_time).total_seconds() * 1000,
                    'message': 'Service initialized successfully'
                }
                
            except Exception as e:
                services_status['services'][service_name] = {
                    'status': 'error',
                    'error': str(e),
                    'message': 'Service initialization failed'
                }
        
        # Calculate overall services health
        operational_count = sum(1 for service in services_status['services'].values() if service['status'] == 'operational')
        total_count = len(services_status['services'])
        
        services_status['summary'] = {
            'operational': operational_count,
            'total': total_count,
            'health_percentage': (operational_count / total_count * 100) if total_count > 0 else 0
        }
        
        return jsonify(services_status)
        
    except Exception as e:
        logger.error(f"Services status check failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@system_health_bp.route('/api/health/diagnostics', methods=['GET'])
def run_diagnostics():
    """Run comprehensive system diagnostics"""
    try:
        diagnostics = {
            'timestamp': datetime.utcnow().isoformat(),
            'diagnostics': {},
            'recommendations': []
        }
        
        # Database connection diagnostics
        try:
            start_time = datetime.now()
            db.session.execute(text('SELECT COUNT(*) FROM pos_transactions LIMIT 1')).fetchone()
            end_time = datetime.now()
            
            query_time = (end_time - start_time).total_seconds() * 1000
            
            diagnostics['diagnostics']['database_query_performance'] = {
                'status': 'good' if query_time < 100 else 'slow',
                'query_time_ms': query_time,
                'threshold_ms': 100
            }
            
            if query_time > 100:
                diagnostics['recommendations'].append({
                    'area': 'database',
                    'issue': 'Slow query performance',
                    'recommendation': 'Consider database optimization or indexing improvements'
                })
                
        except Exception as e:
            diagnostics['diagnostics']['database_query_performance'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Memory usage diagnostics
        memory_info = psutil.virtual_memory()
        if memory_info.percent > 85:
            diagnostics['recommendations'].append({
                'area': 'memory',
                'issue': f'High memory usage: {memory_info.percent:.1f}%',
                'recommendation': 'Consider increasing available memory or optimizing application memory usage'
            })
        
        # Analytics services performance diagnostics
        try:
            from app.services.financial_analytics_service import FinancialAnalyticsService
            
            start_time = datetime.now()
            financial = FinancialAnalyticsService()
            financial.get_executive_financial_dashboard()
            end_time = datetime.now()
            
            service_time = (end_time - start_time).total_seconds() * 1000
            
            diagnostics['diagnostics']['analytics_performance'] = {
                'status': 'good' if service_time < 1000 else 'slow',
                'response_time_ms': service_time,
                'threshold_ms': 1000
            }
            
            if service_time > 1000:
                diagnostics['recommendations'].append({
                    'area': 'analytics',
                    'issue': 'Slow analytics response time',
                    'recommendation': 'Consider optimizing analytics queries or implementing caching'
                })
                
        except Exception as e:
            diagnostics['diagnostics']['analytics_performance'] = {
                'status': 'error',
                'error': str(e)
            }
        
        diagnostics['summary'] = {
            'total_checks': len(diagnostics['diagnostics']),
            'recommendations_count': len(diagnostics['recommendations']),
            'overall_health': 'good' if len(diagnostics['recommendations']) == 0 else 'needs_attention'
        }
        
        return jsonify(diagnostics)
        
    except Exception as e:
        logger.error(f"Diagnostics failed: {str(e)}")
        return jsonify({'error': str(e)}), 500