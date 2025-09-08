# app/services/manager_analytics_service.py
# Manager Analytics Service - Version: 2025-09-02-v1
"""
Service providing manager-specific analytics and KPIs.
Tailored insights based on store business type and operational focus.
"""

from sqlalchemy import text, func, and_, or_, desc
from app import db
from app.config.stores import STORES, ACTIVE_STORES, get_store_business_type, get_store_opening_date
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

class ManagerAnalyticsService:
    """Service for manager-specific analytics and insights."""
    
    def __init__(self, store_code: Optional[str] = None):
        """Initialize service for specific store or all stores."""
        self.store_code = store_code
        self.store_info = STORES.get(store_code) if store_code else None
    
    def _get_manager_config(self):
        """Get manager configuration with fallback defaults."""
        try:
            from app.models.config_models import ManagerDashboardConfiguration
            config = ManagerDashboardConfiguration.query.filter_by(
                user_id='default_user', 
                config_name='default'
            ).first()
            if config:
                return config
        except Exception as e:
            logger.warning(f"Could not load manager configuration: {e}")
        
        # Fallback configuration with default values
        class MockManagerConfig:
            def get_store_threshold(self, store_code, metric_name):
                defaults = {
                    'recent_activity_period_days': 30,
                    'comparison_period_days': 60,
                    'max_categories_displayed': 10,
                    'high_value_threshold': 100.0,
                    'max_high_value_items': 20,
                    'recent_transaction_days': 30,
                    'default_activity_limit': 10
                }
                return defaults.get(metric_name, 30)
        
        return MockManagerConfig()
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            query = text(f"SELECT 1 FROM {table_name} LIMIT 1")
            result = db.session.execute(query).fetchone()
            return True
        except Exception:
            return False
        
    def get_manager_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for manager."""
        try:
            data = {
                'kpis': self.get_manager_kpis(),
                'inventory_summary': self.get_inventory_summary(),
                'financial_summary': self.get_financial_summary(),
                'performance_trends': self.get_performance_trends(),
                'inventory_insights': self.get_inventory_insights(),
                'alerts': self.get_manager_alerts(),
                'recent_activity': self.get_recent_activity()
            }
            
            # Add business-type specific data
            if self.store_info:
                business_type = self.store_info.business_type
                if '100% Construction' in business_type:
                    data['construction_metrics'] = self.get_construction_metrics()
                elif '100% Events' in business_type:
                    data['events_metrics'] = self.get_events_metrics()
                elif 'DIY' in business_type:
                    data['diy_metrics'] = self.get_diy_metrics()
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting manager dashboard data: {str(e)}")
            return {}

    def get_manager_kpis(self) -> Dict[str, Any]:
        """Get key performance indicators for manager."""
        try:
            current_date = datetime.now().date()
            # OLD - HARDCODED (WRONG): thirty_days_ago = current_date - timedelta(days=30)
            # OLD - HARDCODED (WRONG): last_month = current_date - timedelta(days=60)
            # NEW - CONFIGURABLE (CORRECT):
            try:
                config = self._get_manager_config()
                recent_days = config.get_store_threshold(self.store_code or 'default', 'recent_activity_period_days')
                comparison_days = config.get_store_threshold(self.store_code or 'default', 'comparison_period_days')
            except Exception as e:
                logger.warning(f"Config loading error in get_manager_kpis, using defaults: {str(e)}")
                recent_days, comparison_days = 30, 60
            thirty_days_ago = current_date - timedelta(days=recent_days)
            last_month = current_date - timedelta(days=comparison_days)
            
            kpis = {}
            
            if self.store_code:
                # Store-specific KPIs - FIXED: Convert store_code to pos_code for database queries
                # Store codes (8101, 3607, etc.) → POS codes (3, 1, etc.) for pos_transactions table
                pos_code = self.store_info.pos_code.lstrip('0') if self.store_info else self.store_code
                store_filter = f"AND store_code = '{pos_code}'"
            else:
                # All stores KPIs
                store_filter = ""
            
            # Inventory KPIs using the new combined_inventory view
            inventory_query = text(f"""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN status = 'fully_rented' OR status = 'partially_rented' THEN 1 END) as rented_items,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_items,
                    COUNT(CASE WHEN status = 'maintenance' THEN 1 END) as maintenance_items,
                    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_items,
                    SUM(pos_quantity) as total_pos_inventory,
                    SUM(rfid_tag_count) as total_rfid_tags,
                    ROUND(AVG(utilization_percentage), 2) as avg_utilization,
                    SUM(current_rental_revenue) as current_revenue
                FROM combined_inventory 
                WHERE 1=1 {store_filter}
            """)
            
            inventory_result = db.session.execute(inventory_query).fetchone()
            
            if inventory_result:
                total_items = inventory_result.total_items or 0
                rented_items = inventory_result.rented_items or 0
                available_items = inventory_result.available_items or 0
                maintenance_items = inventory_result.maintenance_items or 0
                inactive_items = inventory_result.inactive_items or 0
                total_pos_inventory = inventory_result.total_pos_inventory or 0
                total_rfid_tags = inventory_result.total_rfid_tags or 0
                avg_utilization = inventory_result.avg_utilization or 0
                current_revenue = float(inventory_result.current_revenue or 0)
                
                utilization_rate = (rented_items / total_items * 100) if total_items > 0 else 0
                availability_rate = (available_items / total_items * 100) if total_items > 0 else 0
                correlation_coverage = (total_rfid_tags / total_pos_inventory * 100) if total_pos_inventory > 0 else 0
                
                kpis['inventory'] = {
                    'total_items': total_items,
                    'rented_items': rented_items,
                    'available_items': available_items,
                    'maintenance_items': maintenance_items,
                    'inactive_items': inactive_items,
                    'total_pos_inventory': total_pos_inventory,
                    'total_rfid_tags': total_rfid_tags,
                    'correlation_coverage': round(correlation_coverage, 1),
                    'utilization_rate': round(utilization_rate, 1),
                    'availability_rate': round(availability_rate, 1),
                    'avg_utilization_percentage': round(avg_utilization, 1),
                    'current_rental_revenue': round(current_revenue, 2)
                }
            
            # Financial KPIs from POS data
            if self._table_exists('pos_transactions'):
                # FIXED: Use correct column name and POS code mapping for pos_transactions
                pos_store_filter = store_filter.replace('store_code', 'store_no') if store_filter else ""
                financial_query = text(f"""
                    SELECT 
                        COUNT(*) as total_transactions,
                        SUM(CASE WHEN total > 0 THEN total ELSE 0 END) as total_revenue,
                        AVG(CASE WHEN total > 0 THEN total ELSE 0 END) as avg_transaction_value,
                        COUNT(CASE WHEN DATE(contract_date) >= :thirty_days_ago THEN 1 END) as recent_transactions,
                        SUM(CASE WHEN DATE(contract_date) >= :thirty_days_ago AND total > 0 THEN total ELSE 0 END) as recent_revenue
                    FROM pos_transactions 
                    WHERE contract_date IS NOT NULL {pos_store_filter}
                """)
                
                financial_result = db.session.execute(financial_query, {
                    'thirty_days_ago': thirty_days_ago
                }).fetchone()
                
                if financial_result:
                    kpis['financial'] = {
                        'total_transactions': financial_result.total_transactions or 0,
                        'total_revenue': round(financial_result.total_revenue or 0, 2),
                        'avg_transaction_value': round(financial_result.avg_transaction_value or 0, 2),
                        'recent_transactions': financial_result.recent_transactions or 0,
                        'recent_revenue': round(financial_result.recent_revenue or 0, 2)
                    }
            
            # Contract KPIs
            if self._table_exists('open_contracts'):
                contract_query = text(f"""
                    SELECT 
                        COUNT(*) as total_contracts,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_contracts,
                        COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_contracts,
                        AVG(CASE WHEN total_value > 0 THEN total_value END) as avg_contract_value,
                        SUM(CASE WHEN status = 'active' THEN total_value ELSE 0 END) as active_contract_value
                    FROM open_contracts 
                    WHERE 1=1 {store_filter}
                """)
                
                contract_result = db.session.execute(contract_query).fetchone()
                
                if contract_result:
                    kpis['contracts'] = {
                        'total_contracts': contract_result.total_contracts or 0,
                        'active_contracts': contract_result.active_contracts or 0,
                        'overdue_contracts': contract_result.overdue_contracts or 0,
                        'avg_contract_value': round(contract_result.avg_contract_value or 0, 2),
                        'active_contract_value': round(contract_result.active_contract_value or 0, 2)
                    }
            
            # Performance metrics
            kpis['performance'] = self.get_performance_metrics()
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error getting manager KPIs: {str(e)}")
            return {}

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary tailored to business type."""
        try:
            if not self.store_code:
                return {}
            
            summary = {}
            
            # Base inventory counts by category
            try:
                config = self._get_manager_config()
                max_categories = config.get_store_threshold(self.store_code, 'max_categories_displayed')
            except Exception as e:
                logger.warning(f"Config loading error in get_inventory_summary, using defaults: {str(e)}")
                max_categories = 10
            
            category_query = text("""
                SELECT 
                    category,
                    COUNT(*) as item_count,
                    COUNT(CASE WHEN status = 'rented' THEN 1 END) as rented_count,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_count,
                    COUNT(CASE WHEN status = 'maintenance' THEN 1 END) as maintenance_count
                FROM combined_inventory 
                WHERE store_code = :store_code
                GROUP BY category
                ORDER BY item_count DESC
                LIMIT :max_categories
            """)
            
            category_result = db.session.execute(category_query, {
                'store_code': self.store_code,
                'max_categories': max_categories
            }).fetchall()
            
            summary['top_categories'] = []
            for row in category_result:
                utilization = (row.rented_count / row.item_count * 100) if row.item_count > 0 else 0
                summary['top_categories'].append({
                    'category': row.category,
                    'total_items': row.item_count,
                    'rented': row.rented_count,
                    'available': row.available_count,
                    'maintenance': row.maintenance_count,
                    'utilization_rate': round(utilization, 1)
                })
            
            # High-value items tracking
            try:
                high_value_threshold = config.get_store_threshold(self.store_code, 'high_value_threshold')
                max_high_value_items = config.get_store_threshold(self.store_code, 'max_high_value_items')
            except Exception as e:
                logger.warning(f"Config loading error for high-value items, using defaults: {str(e)}")
                high_value_threshold, max_high_value_items = 100.0, 20
            
            high_value_query = text("""
                SELECT 
                    description,
                    category,
                    status,
                    COALESCE(rental_rate, 0) as rental_rate
                FROM combined_inventory 
                WHERE store_code = :store_code 
                AND COALESCE(rental_rate, 0) > :high_value_threshold
                ORDER BY rental_rate DESC
                LIMIT :max_high_value_items
            """)
            
            high_value_result = db.session.execute(high_value_query, {
                'store_code': self.store_code,
                'high_value_threshold': high_value_threshold,
                'max_high_value_items': max_high_value_items
            }).fetchall()
            
            summary['high_value_items'] = []
            for row in high_value_result:
                summary['high_value_items'].append({
                    'description': row.description,
                    'category': row.category,
                    'status': row.status,
                    'rental_rate': round(row.rental_rate, 2)
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting inventory summary: {str(e)}")
            return {}

    def get_financial_summary(self, period: str = 'month') -> Dict[str, Any]:
        """Get financial performance summary."""
        try:
            current_date = datetime.now().date()
            
            config = self._get_manager_config()
            quarter_comparison_days = config.get_store_threshold(self.store_code or 'default', 'quarter_comparison_days')
            
            if period == 'month':
                start_date = current_date.replace(day=1)
                prev_start_date = (start_date - timedelta(days=1)).replace(day=1)
            elif period == 'quarter':
                quarter_start_month = ((current_date.month - 1) // 3) * 3 + 1
                start_date = current_date.replace(month=quarter_start_month, day=1)
                prev_start_date = (start_date - timedelta(days=quarter_comparison_days))
            else:  # year
                start_date = current_date.replace(month=1, day=1)
                prev_start_date = start_date.replace(year=start_date.year - 1)
            
            summary = {}
            
            if self._table_exists('pos_transactions'):
                store_filter = f"AND store_no = '{self.store_code}'" if self.store_code else ""
                
                financial_query = text(f"""
                    SELECT 
                        SUM(CASE WHEN DATE(contract_date) >= :start_date AND total > 0 THEN total ELSE 0 END) as current_revenue,
                        COUNT(CASE WHEN DATE(contract_date) >= :start_date THEN 1 END) as current_transactions,
                        SUM(CASE WHEN DATE(contract_date) >= :prev_start_date AND DATE(contract_date) < :start_date AND total > 0 THEN total ELSE 0 END) as previous_revenue,
                        COUNT(CASE WHEN DATE(contract_date) >= :prev_start_date AND DATE(contract_date) < :start_date THEN 1 END) as previous_transactions
                    FROM pos_transactions 
                    WHERE contract_date IS NOT NULL {store_filter}
                """)
                
                result = db.session.execute(financial_query, {
                    'start_date': start_date,
                    'prev_start_date': prev_start_date
                }).fetchone()
                
                if result:
                    current_revenue = result.current_revenue or 0
                    previous_revenue = result.previous_revenue or 0
                    current_transactions = result.current_transactions or 0
                    previous_transactions = result.previous_transactions or 0
                    
                    revenue_change = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
                    transaction_change = ((current_transactions - previous_transactions) / previous_transactions * 100) if previous_transactions > 0 else 0
                    
                    summary.update({
                        'current_revenue': round(current_revenue, 2),
                        'previous_revenue': round(previous_revenue, 2),
                        'revenue_change_percent': round(revenue_change, 1),
                        'current_transactions': current_transactions,
                        'previous_transactions': previous_transactions,
                        'transaction_change_percent': round(transaction_change, 1),
                        'avg_transaction_current': round(current_revenue / current_transactions, 2) if current_transactions > 0 else 0,
                        'avg_transaction_previous': round(previous_revenue / previous_transactions, 2) if previous_transactions > 0 else 0
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting financial summary: {str(e)}")
            return {}

    def get_performance_trends(self, days: int = None) -> Dict[str, Any]:
        """Get performance trend data."""
        try:
            config = self._get_manager_config()
            if days is None:
                days = config.get_store_threshold(self.store_code or 'default', 'default_trend_period_days')
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            trends = {}
            
            if self._table_exists('pos_transactions'):
                store_filter = f"AND store_no = '{self.store_code}'" if self.store_code else ""
                
                # Daily revenue trends
                daily_trends_query = text(f"""
                    SELECT 
                        DATE(contract_date) as date,
                        SUM(CASE WHEN total > 0 THEN total ELSE 0 END) as daily_revenue,
                        COUNT(*) as daily_transactions
                    FROM pos_transactions 
                    WHERE DATE(contract_date) >= :start_date 
                    AND contract_date IS NOT NULL {store_filter}
                    GROUP BY DATE(contract_date)
                    ORDER BY DATE(contract_date)
                """)
                
                daily_result = db.session.execute(daily_trends_query, {'start_date': start_date}).fetchall()
                
                trends['daily_revenue'] = []
                trends['daily_transactions'] = []
                
                for row in daily_result:
                    trends['daily_revenue'].append({
                        'date': row.date.strftime('%Y-%m-%d'),
                        'value': round(row.daily_revenue, 2)
                    })
                    trends['daily_transactions'].append({
                        'date': row.date.strftime('%Y-%m-%d'),
                        'value': row.daily_transactions
                    })
            
            # Inventory utilization trends
            if self.store_code:
                utilization_query = text("""
                    SELECT 
                        category,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'rented' THEN 1 END) as rented
                    FROM combined_inventory 
                    WHERE store_code = :store_code
                    GROUP BY category
                    ORDER BY COUNT(*) DESC
                    LIMIT :max_trend_categories
                """)
                
                max_trend_categories = config.get_store_threshold(self.store_code, 'max_trend_categories')
                utilization_result = db.session.execute(utilization_query, {
                    'store_code': self.store_code,
                    'max_trend_categories': max_trend_categories
                }).fetchall()
                
                trends['category_utilization'] = []
                for row in utilization_result:
                    utilization_rate = (row.rented / row.total * 100) if row.total > 0 else 0
                    trends['category_utilization'].append({
                        'category': row.category,
                        'utilization_rate': round(utilization_rate, 1),
                        'total_items': row.total,
                        'rented_items': row.rented
                    })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {str(e)}")
            return {}

    def get_inventory_insights(self) -> Dict[str, Any]:
        """Get inventory-specific insights and recommendations."""
        try:
            insights = {
                'alerts': [],
                'opportunities': [],
                'recommendations': []
            }
            
            if not self.store_code:
                return insights
            
            # Check for underutilized high-value items
            config = self._get_manager_config()
            underutilized_threshold = config.get_store_threshold(self.store_code, 'underutilized_value_threshold')
            max_opportunities = config.get_store_threshold(self.store_code, 'max_opportunities_displayed')
            
            underutilized_query = text("""
                SELECT 
                    description,
                    category,
                    rental_rate,
                    status
                FROM combined_inventory 
                WHERE store_code = :store_code 
                AND COALESCE(rental_rate, 0) > :underutilized_threshold
                AND status = 'available'
                ORDER BY rental_rate DESC
                LIMIT :max_opportunities
            """)
            
            underutilized_result = db.session.execute(underutilized_query, {
                'store_code': self.store_code,
                'underutilized_threshold': underutilized_threshold,
                'max_opportunities': max_opportunities
            }).fetchall()
            
            for row in underutilized_result:
                insights['opportunities'].append({
                    'type': 'underutilized_asset',
                    'message': f"High-value item '{row.description}' (${row.rental_rate}/day) is available",
                    'category': row.category,
                    'value': row.rental_rate
                })
            
            # Check for maintenance backlog
            maintenance_query = text("""
                SELECT 
                    COUNT(*) as maintenance_count,
                    category,
                    AVG(COALESCE(rental_rate, 0)) as avg_value
                FROM combined_inventory 
                WHERE store_code = :store_code 
                AND status = 'maintenance'
                GROUP BY category
                HAVING COUNT(*) > :maintenance_backlog_threshold
                ORDER BY COUNT(*) DESC
            """)
            
            maintenance_backlog_threshold = config.get_store_threshold(self.store_code, 'maintenance_backlog_threshold')
            maintenance_result = db.session.execute(maintenance_query, {
                'store_code': self.store_code,
                'maintenance_backlog_threshold': maintenance_backlog_threshold
            }).fetchall()
            
            for row in maintenance_result:
                insights['alerts'].append({
                    'type': 'maintenance_backlog',
                    'message': f"{row.maintenance_count} {row.category} items need maintenance",
                    'priority': 'high' if row.maintenance_count > config.get_store_threshold(self.store_code, 'high_priority_maintenance_threshold') else 'medium',
                    'count': row.maintenance_count,
                    'avg_value': round(row.avg_value, 2)
                })
            
            # Business-type specific insights
            business_type = self.store_info.business_type
            
            if '100% Construction' in business_type:
                insights['recommendations'].append({
                    'type': 'business_specific',
                    'message': 'Focus on heavy equipment utilization and preventive maintenance schedules',
                    'priority': 'medium'
                })
            elif '100% Events' in business_type:
                insights['recommendations'].append({
                    'type': 'business_specific',
                    'message': 'Monitor seasonal demand patterns for tent and event equipment',
                    'priority': 'medium'
                })
            elif 'DIY' in business_type:
                insights['recommendations'].append({
                    'type': 'business_specific',
                    'message': 'Track weekend usage patterns for DIY tool optimization',
                    'priority': 'medium'
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting inventory insights: {str(e)}")
            return {}

    def get_manager_alerts(self) -> List[Dict[str, Any]]:
        """Get manager-specific alerts and notifications."""
        try:
            alerts = []
            
            if not self.store_code:
                # Executive alerts - cross-store issues
                return self.get_executive_alerts()
            
            # Store-specific alerts
            
            # High maintenance items alert
            maintenance_query = text("""
                SELECT COUNT(*) as count 
                FROM combined_inventory 
                WHERE store_code = :store_code AND status = 'maintenance'
            """)
            
            maintenance_count = db.session.execute(maintenance_query, {'store_code': self.store_code}).scalar() or 0
            
            config = self._get_manager_config()
            critical_maintenance_threshold = config.get_store_threshold(self.store_code, 'critical_maintenance_threshold')
            
            if maintenance_count > critical_maintenance_threshold:
                alerts.append({
                    'type': 'warning',
                    'title': 'High Maintenance Backlog',
                    'message': f'{maintenance_count} items need maintenance attention',
                    'priority': 'high',
                    'action': 'Review maintenance schedule'
                })
            
            # Low inventory alerts
            low_stock_query = text("""
                SELECT 
                    category,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_count,
                    COUNT(*) as total_count
                FROM combined_inventory 
                WHERE store_code = :store_code
                GROUP BY category
                HAVING COUNT(CASE WHEN status = 'available' THEN 1 END) < :low_stock_threshold
                AND COUNT(*) > :min_category_size
            """)
            
            low_stock_threshold = config.get_store_threshold(self.store_code, 'low_stock_threshold')
            min_category_size = config.get_store_threshold(self.store_code, 'min_category_size')
            
            low_stock_result = db.session.execute(low_stock_query, {
                'store_code': self.store_code,
                'low_stock_threshold': low_stock_threshold,
                'min_category_size': min_category_size
            }).fetchall()
            
            for row in low_stock_result:
                alerts.append({
                    'type': 'info',
                    'title': 'Low Inventory Alert',
                    'message': f'Only {row.available_count} {row.category} items available',
                    'priority': 'medium',
                    'action': 'Consider restocking or maintenance'
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting manager alerts: {str(e)}")
            return []

    def get_recent_activity(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get recent activity for the store."""
        try:
            activities = []
            
            if self._table_exists('pos_transactions') and self.store_code:
                recent_query = text("""
                    SELECT 
                        contract_date,
                        total,
                        type,
                        CONCAT('Contract ', contract_no, ' - ', COALESCE(contact, 'Unknown Customer')) as description
                    FROM pos_transactions 
                    WHERE store_no = :store_code
                    AND contract_date >= DATE_SUB(NOW(), INTERVAL :recent_transaction_days DAY)
                    ORDER BY contract_date DESC
                    LIMIT :limit
                """)
                
                config = self._get_manager_config()
                recent_transaction_days = config.get_store_threshold(self.store_code, 'recent_transaction_days')
                
                # Handle limit parameter
                if limit is None:
                    limit = config.get_store_threshold(self.store_code, 'default_activity_limit')
                
                recent_result = db.session.execute(recent_query, {
                    'store_code': self.store_code,
                    'limit': limit,
                    'recent_transaction_days': recent_transaction_days
                }).fetchall()
                
                for row in recent_result:
                    activities.append({
                        'timestamp': row.contract_date,
                        'type': row.type or 'transaction',
                        'description': row.description or f'${row.total:.2f} transaction',
                        'amount': row.total
                    })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []

    def get_construction_metrics(self) -> Dict[str, Any]:
        """Get construction-specific metrics for Brooklyn Park (Zack)."""
        try:
            metrics = {}
            
            # Heavy equipment utilization
            heavy_equipment_query = text("""
                SELECT 
                    COUNT(*) as total_heavy_equipment,
                    COUNT(CASE WHEN status = 'rented' THEN 1 END) as rented_heavy,
                    AVG(COALESCE(rental_rate, 0)) as avg_heavy_rate
                FROM combined_inventory 
                WHERE store_code = :store_code
                AND (category LIKE '%excavator%' OR category LIKE '%loader%' 
                     OR category LIKE '%crane%' OR category LIKE '%bulldozer%'
                     OR COALESCE(rental_rate, 0) > :heavy_equipment_threshold)
            """)
            
            config = self._get_manager_config()
            heavy_equipment_threshold = config.get_store_threshold(self.store_code, 'construction_heavy_equipment_threshold')
            
            result = db.session.execute(heavy_equipment_query, {
                'store_code': self.store_code,
                'heavy_equipment_threshold': heavy_equipment_threshold
            }).fetchone()
            
            if result:
                metrics['heavy_equipment'] = {
                    'total': result.total_heavy_equipment or 0,
                    'rented': result.rented_heavy or 0,
                    'avg_rate': round(result.avg_heavy_rate or 0, 2),
                    'utilization_rate': round((result.rented_heavy / result.total_heavy_equipment * 100) if result.total_heavy_equipment > 0 else 0, 1)
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting construction metrics: {str(e)}")
            return {}

    def get_events_metrics(self) -> Dict[str, Any]:
        """Get events-specific metrics for Fridley (Tim)."""
        try:
            metrics = {}
            
            # Event equipment tracking
            event_equipment_query = text("""
                SELECT 
                    COUNT(*) as total_event_items,
                    COUNT(CASE WHEN status = 'rented' THEN 1 END) as rented_event,
                    COUNT(CASE WHEN category LIKE '%tent%' OR category LIKE '%table%' OR category LIKE '%chair%' THEN 1 END) as core_event_items
                FROM combined_inventory 
                WHERE store_code = :store_code
            """)
            
            result = db.session.execute(event_equipment_query, {'store_code': self.store_code}).fetchone()
            
            if result:
                metrics['event_equipment'] = {
                    'total': result.total_event_items or 0,
                    'rented': result.rented_event or 0,
                    'core_items': result.core_event_items or 0,
                    'utilization_rate': round((result.rented_event / result.total_event_items * 100) if result.total_event_items > 0 else 0, 1)
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting events metrics: {str(e)}")
            return {}

    def get_diy_metrics(self) -> Dict[str, Any]:
        """Get DIY-specific metrics for Wayzata (Tyler) and Elk River (Bruce)."""
        try:
            metrics = {}
            
            # Tool categories popular in DIY
            diy_categories_query = text("""
                SELECT 
                    category,
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'rented' THEN 1 END) as rented,
                    AVG(COALESCE(rental_rate, 0)) as avg_rate
                FROM combined_inventory 
                WHERE store_code = :store_code
                AND (category LIKE '%tool%' OR category LIKE '%drill%' 
                     OR category LIKE '%saw%' OR category LIKE '%sander%'
                     OR category LIKE '%ladder%' OR category LIKE '%paint%')
                GROUP BY category
                ORDER BY COUNT(*) DESC
                LIMIT :diy_max_categories
            """)
            
            config = self._get_manager_config()
            diy_max_categories = config.get_store_threshold(self.store_code, 'diy_max_categories')
            
            result = db.session.execute(diy_categories_query, {
                'store_code': self.store_code,
                'diy_max_categories': diy_max_categories
            }).fetchall()
            
            metrics['diy_categories'] = []
            for row in result:
                utilization = (row.rented / row.total * 100) if row.total > 0 else 0
                metrics['diy_categories'].append({
                    'category': row.category,
                    'total': row.total,
                    'rented': row.rented,
                    'avg_rate': round(row.avg_rate, 2),
                    'utilization_rate': round(utilization, 1)
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting DIY metrics: {str(e)}")
            return {}

    def get_executive_overview(self) -> Dict[str, Any]:
        """Get executive overview data combining all stores."""
        try:
            overview = {}
            
            # Overall company metrics
            company_kpis = {}
            for store_code in ACTIVE_STORES.keys():
                service = ManagerAnalyticsService(store_code)
                store_kpis = service.get_manager_kpis()
                
                store_name = STORES[store_code].name
                company_kpis[store_name] = store_kpis
            
            overview['store_kpis'] = company_kpis
            
            # Cross-store comparisons
            overview['comparisons'] = self.get_store_comparison('revenue', 'month')
            
            # Executive alerts
            overview['alerts'] = self.get_executive_alerts()
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting executive overview: {str(e)}")
            return {}

    def get_store_comparison(self, metric: str, period: str) -> Dict[str, Any]:
        """Get cross-store performance comparison."""
        try:
            comparison = {}
            
            for store_code in ACTIVE_STORES.keys():
                service = ManagerAnalyticsService(store_code)
                
                if metric == 'revenue':
                    data = service.get_financial_summary(period)
                    comparison[store_code] = {
                        'store_name': STORES[store_code].name,
                        'manager': STORES[store_code].manager,
                        'value': data.get('current_revenue', 0),
                        'change': data.get('revenue_change_percent', 0)
                    }
                elif metric == 'inventory_turns':
                    kpis = service.get_manager_kpis()
                    utilization = kpis.get('inventory', {}).get('utilization_rate', 0)
                    comparison[store_code] = {
                        'store_name': STORES[store_code].name,
                        'manager': STORES[store_code].manager,
                        'value': utilization,
                        'change': 0  # Would need historical data
                    }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error getting store comparison: {str(e)}")
            return {}

    def get_executive_alerts(self) -> List[Dict[str, Any]]:
        """Get executive-level alerts across all stores."""
        try:
            alerts = []
            
            # Check each store for issues
            for store_code in ACTIVE_STORES.keys():
                service = ManagerAnalyticsService(store_code)
                store_alerts = service.get_manager_alerts()
                
                # Add store context to alerts
                for alert in store_alerts:
                    alert['store_code'] = store_code
                    alert['store_name'] = STORES[store_code].name
                    alert['manager'] = STORES[store_code].manager
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting executive alerts: {str(e)}")
            return []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the store."""
        try:
            metrics = {}
            
            if self.store_code:
                # Store age impact on performance
                store_age_months = self._get_store_age_months()
                metrics['store_age_months'] = store_age_months
                
                # Experience factor (newer stores might have different patterns)
                config = self._get_manager_config()
                new_store_threshold = config.get_store_threshold(self.store_code, 'new_store_threshold_months')
                developing_store_threshold = config.get_store_threshold(self.store_code, 'developing_store_threshold_months')
                
                if store_age_months < new_store_threshold:
                    metrics['experience_level'] = 'new'
                elif store_age_months < developing_store_threshold:
                    metrics['experience_level'] = 'developing'
                else:
                    metrics['experience_level'] = 'mature'
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}

    def _get_store_age_months(self) -> int:
        """Calculate store age in months."""
        if not self.store_info:
            return 0
        
        from datetime import datetime
        opened = datetime.strptime(self.store_info.opened_date, "%Y-%m-%d")
        now = datetime.now()
        
        return (now.year - opened.year) * 12 + (now.month - opened.month)

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            result = db.session.execute(text(f"SHOW TABLES LIKE '{table_name}'")).fetchone()
            return result is not None
        except Exception:
            return False
    
    def _get_manager_config(self):
        """Get manager dashboard configuration with safe defaults"""
        try:
            from app.models.config_models import ManagerDashboardConfiguration, get_default_manager_dashboard_config
            
            config = ManagerDashboardConfiguration.query.filter_by(
                user_id='default_user',
                config_name='default'
            ).first()
            
            if config:
                return config
            
            # Create MockConfig with defaults if none exists
            class MockConfig:
                def __init__(self):
                    defaults = get_default_manager_dashboard_config()
                    
                    # Time periods
                    self.recent_activity_period_days = defaults['time_periods']['recent_activity_days']
                    self.comparison_period_days = defaults['time_periods']['comparison_period_days']
                    self.default_trend_period_days = defaults['time_periods']['default_trend_days']
                    self.recent_transaction_days = defaults['time_periods']['recent_transaction_days']
                    self.quarter_comparison_days = defaults['time_periods']['quarter_comparison_days']
                    
                    # Display limits
                    self.max_categories_displayed = defaults['display_limits']['max_categories']
                    self.max_high_value_items = defaults['display_limits']['max_high_value_items']
                    self.max_trend_categories = defaults['display_limits']['max_trend_categories']
                    self.max_opportunities_displayed = defaults['display_limits']['max_opportunities']
                    self.default_activity_limit = defaults['display_limits']['default_activity_limit']
                    self.diy_max_categories = defaults['display_limits']['diy_max_categories']
                    
                    # Business thresholds
                    self.high_value_threshold = defaults['business_thresholds']['high_value_threshold']
                    self.underutilized_value_threshold = defaults['business_thresholds']['underutilized_threshold']
                    self.construction_heavy_equipment_threshold = defaults['business_thresholds']['construction_heavy_equipment']
                    
                    # Alert thresholds
                    self.maintenance_backlog_threshold = defaults['alert_thresholds']['maintenance_backlog']
                    self.high_priority_maintenance_threshold = defaults['alert_thresholds']['high_priority_maintenance']
                    self.critical_maintenance_threshold = defaults['alert_thresholds']['critical_maintenance']
                    self.low_stock_threshold = defaults['alert_thresholds']['low_stock_threshold']
                    self.min_category_size = defaults['alert_thresholds']['min_category_size']
                    
                    # Store classification
                    self.new_store_threshold_months = defaults['store_classification']['new_store_months']
                    self.developing_store_threshold_months = defaults['store_classification']['developing_store_months']
                    
                    # Business insights
                    self.diy_weekend_percentage = defaults['business_insights']['diy_weekend_percentage']
                
                def get_store_threshold(self, store_code: str, threshold_type: str):
                    """Get threshold value with fallback to attribute defaults"""
                    return getattr(self, threshold_type, 30)
            
            return MockConfig()
            
        except Exception as e:
            logger.warning(f"Could not load manager configuration, using safe fallback: {str(e)}")
            
            # Ultra-safe fallback MockConfig
            class SafeMockConfig:
                def get_store_threshold(self, store_code: str, threshold_type: str):
                    """Safe fallback with hardcoded defaults"""
                    defaults = {
                        'recent_activity_period_days': 30,
                        'comparison_period_days': 60,
                        'default_trend_period_days': 30,
                        'recent_transaction_days': 7,
                        'quarter_comparison_days': 90,
                        'max_categories_displayed': 10,
                        'max_high_value_items': 20,
                        'max_trend_categories': 10,
                        'max_opportunities_displayed': 10,
                        'default_activity_limit': 10,
                        'diy_max_categories': 10,
                        'high_value_threshold': 100.0,
                        'underutilized_value_threshold': 50.0,
                        'construction_heavy_equipment_threshold': 200.0,
                        'maintenance_backlog_threshold': 2,
                        'high_priority_maintenance_threshold': 5,
                        'critical_maintenance_threshold': 10,
                        'low_stock_threshold': 3,
                        'min_category_size': 5,
                        'new_store_threshold_months': 12,
                        'developing_store_threshold_months': 24,
                        'diy_weekend_percentage': 70.0
                    }
                    return defaults.get(threshold_type, 30)
            
            return SafeMockConfig()