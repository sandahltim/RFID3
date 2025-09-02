"""
Cross-System Analytics Service
Provides unified analytics across RFID Pro API and POS CSV data
Answers: "Who rented what where when for how much"
"""

from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from .. import db
from .store_correlation_service import get_store_correlation_service
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from app.config.stores import (
    STORES, STORE_MAPPING, STORE_MANAGERS,
    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,
    get_store_name, get_store_manager, get_store_business_type,
    get_store_opening_date, get_active_store_codes
)


logger = logging.getLogger(__name__)


class CrossSystemAnalyticsService:
    """
    Unified analytics service combining RFID Pro API and POS CSV data.
    
    Data Sources:
    - RFID System: id_item_master, id_transactions (real-time inventory)
    - POS System: pos_transactions, pos_transaction_items, pos_customers (historical transactions)
    - Equipment: pos_equipment (equipment details)
    
    Key Correlations:
    - Store: pos_transactions.store_no ↔ id_item_master.current_store via store_correlations
    - Equipment: pos_transaction_items.item_num ↔ id_item_master.item_num (partial)
    - Customer: pos_transactions.customer_no ↔ pos_customers.cnum
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db.session
        self.store_service = get_store_correlation_service()
    
    def get_unified_transaction_analysis(self, 
                                       store_filter: Optional[str] = None,
                                       customer_filter: Optional[str] = None,
                                       date_from: Optional[datetime] = None,
                                       date_to: Optional[datetime] = None,
                                       limit: int = 100) -> Dict[str, Any]:
        """
        Get unified transaction analysis: Who rented what where when for how much.
        
        Args:
            store_filter: Store code (POS or RFID format)
            customer_filter: Customer number or name pattern
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum results to return
            
        Returns:
            Dict with transaction details, equipment info, customer data
        """
        try:
            # Build dynamic WHERE clause
            where_conditions = ["pt.status IS NOT NULL"]
            params = {}
            
            # Store filter (auto-detect POS vs RFID code)
            if store_filter:
                if store_filter in ['1', '2', '3', '4']:
                    where_conditions.append("pt.store_no = :store_no")
                    params['store_no'] = store_filter
                else:
                    where_conditions.append("pt.rfid_store_code = :rfid_code")
                    params['rfid_code'] = store_filter
            
            # Customer filter
            if customer_filter:
                if customer_filter.isdigit():
                    where_conditions.append("pt.customer_no = :customer_no")
                    params['customer_no'] = customer_filter
                else:
                    where_conditions.append("pc.name LIKE :customer_name")
                    params['customer_name'] = f"%{customer_filter}%"
            
            # Date filters
            if date_from:
                where_conditions.append("pt.contract_date >= :date_from")
                params['date_from'] = date_from
            if date_to:
                where_conditions.append("pt.contract_date <= :date_to")
                params['date_to'] = date_to
            
            where_clause = " AND ".join(where_conditions)
            
            # Main query combining POS transaction data
            query = f"""
            SELECT 
                -- Transaction Info
                pt.contract_no,
                pt.store_no as pos_store,
                pt.rfid_store_code,
                sc.store_name,
                pt.contract_date,
                pt.status as transaction_status,
                pt.total,
                pt.rent_amt,
                pt.sale_amt,
                
                -- Customer Info  
                pt.customer_no,
                pc.name as customer_name,
                pc.city as customer_city,
                
                -- Equipment Items
                GROUP_CONCAT(
                    CONCAT(pti.item_num, ':', pti.qty, ':', pti.line_status, ':', pti.price) 
                    SEPARATOR ';'
                ) as equipment_items,
                COUNT(pti.item_num) as item_count,
                SUM(pti.price) as items_total
                
            FROM pos_transactions pt
            LEFT JOIN pos_customers pc ON pt.customer_no = pc.cnum
            LEFT JOIN store_correlations sc ON pt.rfid_store_code = sc.rfid_store_code
            LEFT JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
            WHERE {where_clause}
            GROUP BY pt.contract_no
            ORDER BY pt.contract_date DESC
            LIMIT :limit
            """
            
            params['limit'] = limit
            
            result = self.session.execute(text(query), params)
            transactions = []
            
            for row in result.fetchall():
                # Parse equipment items
                equipment_list = []
                if row[13]:  # equipment_items
                    for item_data in row[13].split(';'):
                        if ':' in item_data:
                            parts = item_data.split(':')
                            if len(parts) >= 4:
                                equipment_list.append({
                                    'item_num': parts[0],
                                    'qty': int(parts[1]) if parts[1].isdigit() else 1,
                                    'status': parts[2],  # RX, RR, S
                                    'price': float(parts[3]) if parts[3] else 0.0
                                })
                
                transactions.append({
                    'contract_no': row[0],
                    'store': {
                        'pos_code': row[1],
                        'rfid_code': row[2], 
                        'name': row[3] or 'Unknown Store'
                    },
                    'contract_date': row[4].isoformat() if row[4] else None,
                    'status': row[5],
                    'financial': {
                        'total': float(row[6]) if row[6] else 0.0,
                        'rent_amount': float(row[7]) if row[7] else 0.0,
                        'sale_amount': float(row[8]) if row[8] else 0.0,
                        'items_total': float(row[15]) if row[15] else 0.0
                    },
                    'customer': {
                        'number': row[9],
                        'name': row[10] or 'Unknown Customer',
                        'city': row[11]
                    },
                    'equipment': {
                        'count': row[14],
                        'items': equipment_list
                    }
                })
            
            # Generate summary statistics
            summary = self._generate_transaction_summary(transactions)
            
            logger.info(f"Unified transaction analysis: {len(transactions)} transactions analyzed")
            
            return {
                'transactions': transactions,
                'summary': summary,
                'filters_applied': {
                    'store_filter': store_filter,
                    'customer_filter': customer_filter, 
                    'date_from': date_from.isoformat() if date_from else None,
                    'date_to': date_to.isoformat() if date_to else None
                },
                'total_results': len(transactions),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Unified transaction analysis failed: {e}")
            return {
                'error': str(e),
                'transactions': [],
                'summary': {},
                'generated_at': datetime.now().isoformat()
            }
    
    def get_equipment_utilization_analysis(self, store_code: Optional[str] = None,
                                         days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze equipment utilization across RFID and POS systems with correlation.
        
        Args:
            store_code: Store to analyze (POS or RFID format)
            days_back: Number of days to analyze
            
        Returns:
            Equipment utilization metrics and trends with CSV-RFID correlation
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Convert store code for filtering
            pos_store = store_code
            rfid_store = store_code
            if store_code:
                if store_code in ['1', '2', '3', '4']:
                    rfid_store = self.store_service.correlate_pos_to_rfid(store_code)
                else:
                    pos_store = self.store_service.correlate_rfid_to_pos(store_code)
            
            # POS Transaction Items Analysis
            pos_filter = f"AND pt.store_no = '{pos_store}'" if pos_store else ""
            rfid_filter = f"AND current_store = '{rfid_store}'" if rfid_store else ""
            
            # Get equipment usage from POS transactions with CSV equipment details
            pos_query = f"""
            SELECT 
                pti.item_num,
                pe.name as equipment_name,
                pe.category as equipment_category,
                COUNT(*) as transaction_count,
                SUM(pti.qty) as total_quantity,
                AVG(pti.price) as avg_price,
                SUM(pti.price) as total_revenue,
                COUNT(DISTINCT pt.customer_no) as unique_customers,
                COUNT(DISTINCT CASE WHEN im.tag_id IS NOT NULL THEN im.tag_id END) as rfid_tagged_count
            FROM pos_transaction_items pti
            JOIN pos_transactions pt ON pti.contract_no = pt.contract_no
            LEFT JOIN pos_equipment pe ON pti.item_num = pe.item_num
            LEFT JOIN id_item_master im ON pti.item_num = im.item_num
            WHERE pt.contract_date >= :cutoff_date
            {pos_filter}
            GROUP BY pti.item_num, pe.name, pe.category
            ORDER BY transaction_count DESC
            LIMIT 50
            """
            
            result = self.session.execute(text(pos_query), {'cutoff_date': cutoff_date})
            pos_equipment = []
            
            for row in result.fetchall():
                pos_equipment.append({
                    'item_num': row[0],
                    'equipment_name': row[1] or 'Unknown Equipment',
                    'equipment_category': row[2] or 'Uncategorized',
                    'transaction_count': row[3],
                    'total_quantity': row[4],
                    'avg_price': float(row[5]) if row[5] else 0.0,
                    'total_revenue': float(row[6]) if row[6] else 0.0,
                    'unique_customers': row[7],
                    'rfid_tagged_count': row[8],
                    'has_rfid_correlation': row[8] > 0
                })
            
            # Get RFID inventory status
            rfid_query = f"""
            SELECT 
                rental_class_num,
                status,
                COUNT(*) as count,
                current_store,
                home_store
            FROM id_item_master
            WHERE 1=1 {rfid_filter}
            GROUP BY rental_class_num, status, current_store, home_store
            ORDER BY count DESC
            """
            
            result = self.session.execute(text(rfid_query))
            rfid_inventory = []
            
            for row in result.fetchall():
                rfid_inventory.append({
                    'rental_class': row[0],
                    'status': row[1] or 'Unknown',
                    'count': row[2],
                    'current_store': row[3],
                    'home_store': row[4]
                })
            
            # Calculate utilization metrics
            utilization_summary = {
                'pos_metrics': {
                    'total_items_analyzed': len(pos_equipment),
                    'total_transactions': sum(item['transaction_count'] for item in pos_equipment),
                    'total_revenue': sum(item['total_revenue'] for item in pos_equipment),
                    'avg_utilization': sum(item['transaction_count'] for item in pos_equipment) / len(pos_equipment) if pos_equipment else 0
                },
                'rfid_metrics': {
                    'total_classes': len(set(item['rental_class'] for item in rfid_inventory if item['rental_class'])),
                    'total_items': sum(item['count'] for item in rfid_inventory),
                    'status_distribution': {}
                }
            }
            
            # Calculate status distribution
            for item in rfid_inventory:
                status = item['status']
                if status not in utilization_summary['rfid_metrics']['status_distribution']:
                    utilization_summary['rfid_metrics']['status_distribution'][status] = 0
                utilization_summary['rfid_metrics']['status_distribution'][status] += item['count']
            
            # Calculate equipment correlation metrics
            correlation_metrics = self._analyze_equipment_correlation(pos_equipment)
            
            return {
                'pos_equipment_usage': pos_equipment,
                'rfid_inventory_status': rfid_inventory,
                'utilization_summary': utilization_summary,
                'equipment_correlation': correlation_metrics,
                'analysis_period': f"{days_back} days",
                'store_analyzed': {
                    'pos_code': pos_store,
                    'rfid_code': rfid_store,
                    'store_name': self.store_service.get_store_info(store_code)['name'] if store_code else 'All Stores'
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Equipment utilization analysis failed: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def get_store_performance_comparison(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Compare performance across all stores using correlated data.
        
        Returns:
            Store-by-store performance metrics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            query = """
            SELECT 
                sc.store_name,
                sc.pos_store_code,
                sc.rfid_store_code,
                COUNT(pt.contract_no) as transaction_count,
                COUNT(DISTINCT pt.customer_no) as unique_customers,
                SUM(pt.total) as total_revenue,
                SUM(pt.rent_amt) as rental_revenue,
                SUM(pt.sale_amt) as sales_revenue,
                AVG(pt.total) as avg_transaction_value,
                COUNT(DISTINCT pti.item_num) as unique_items_used
            FROM store_correlations sc
            LEFT JOIN pos_transactions pt ON sc.pos_store_code = pt.store_no 
                AND pt.contract_date >= :cutoff_date
            LEFT JOIN pos_transaction_items pti ON pt.contract_no = pti.contract_no
            WHERE sc.is_active = 1
            GROUP BY sc.store_name, sc.pos_store_code, sc.rfid_store_code
            ORDER BY total_revenue DESC
            """
            
            result = self.session.execute(text(query), {'cutoff_date': cutoff_date})
            store_performance = []
            
            for row in result.fetchall():
                store_performance.append({
                    'store_name': row[0],
                    'pos_code': row[1], 
                    'rfid_code': row[2],
                    'metrics': {
                        'transaction_count': row[3],
                        'unique_customers': row[4],
                        'total_revenue': float(row[5]) if row[5] else 0.0,
                        'rental_revenue': float(row[6]) if row[6] else 0.0,
                        'sales_revenue': float(row[7]) if row[7] else 0.0,
                        'avg_transaction_value': float(row[8]) if row[8] else 0.0,
                        'unique_items_used': row[9]
                    }
                })
            
            # Calculate totals and rankings
            totals = {
                'total_revenue': sum(store['metrics']['total_revenue'] for store in store_performance),
                'total_transactions': sum(store['metrics']['transaction_count'] for store in store_performance),
                'total_customers': sum(store['metrics']['unique_customers'] for store in store_performance)
            }
            
            return {
                'store_performance': store_performance,
                'totals': totals,
                'analysis_period': f"{days_back} days",
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Store performance comparison failed: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_transaction_summary(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics from transaction list."""
        if not transactions:
            return {}
        
        total_revenue = sum(t['financial']['total'] for t in transactions)
        total_rental = sum(t['financial']['rent_amount'] for t in transactions)
        total_sales = sum(t['financial']['sale_amount'] for t in transactions)
        total_items = sum(t['equipment']['count'] for t in transactions)
        
        # Store distribution
        store_counts = {}
        for t in transactions:
            store_name = t['store']['name']
            if store_name not in store_counts:
                store_counts[store_name] = 0
            store_counts[store_name] += 1
        
        return {
            'total_transactions': len(transactions),
            'total_revenue': total_revenue,
            'rental_revenue': total_rental,
            'sales_revenue': total_sales,
            'total_equipment_items': total_items,
            'avg_transaction_value': total_revenue / len(transactions) if transactions else 0,
            'avg_items_per_transaction': total_items / len(transactions) if transactions else 0,
            'store_distribution': store_counts
        }
    
    def _analyze_equipment_correlation(self, pos_equipment: List[Dict]) -> Dict[str, Any]:
        """Analyze equipment correlation between POS and RFID systems."""
        if not pos_equipment:
            return {'correlation_rate': 0, 'correlated_items': 0, 'total_items': 0}
        
        total_items = len(pos_equipment)
        correlated_items = len([eq for eq in pos_equipment if eq.get('has_rfid_correlation')])
        correlation_rate = (correlated_items / total_items * 100) if total_items > 0 else 0
        
        # Category correlation breakdown
        category_correlation = {}
        for eq in pos_equipment:
            category = eq.get('equipment_category', 'Unknown')
            if category not in category_correlation:
                category_correlation[category] = {'total': 0, 'correlated': 0}
            
            category_correlation[category]['total'] += 1
            if eq.get('has_rfid_correlation'):
                category_correlation[category]['correlated'] += 1
        
        # Calculate correlation rates per category
        for category in category_correlation:
            total = category_correlation[category]['total']
            correlated = category_correlation[category]['correlated']
            category_correlation[category]['correlation_rate'] = (correlated / total * 100) if total > 0 else 0
        
        return {
            'overall_correlation_rate': round(correlation_rate, 1),
            'total_items_analyzed': total_items,
            'correlated_items': correlated_items,
            'uncorrelated_items': total_items - correlated_items,
            'category_breakdown': category_correlation,
            'correlation_status': 'excellent' if correlation_rate >= 95 else 'good' if correlation_rate >= 80 else 'needs_improvement'
        }

    def get_equipment_lifecycle_analysis(self, item_num: str = None, 
                                       days_back: int = 365) -> Dict[str, Any]:
        """
        Analyze complete equipment lifecycle from CSV history to current RFID status.
        
        Args:
            item_num: Specific equipment item to analyze
            days_back: Historical period to analyze
            
        Returns:
            Complete equipment lifecycle data
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Build item filter
            item_filter = f"AND pe.item_num = '{item_num}'" if item_num else ""
            
            query = f"""
            SELECT 
                -- Equipment Identity
                pe.item_num,
                pe.name as equipment_name,
                pe.category,
                pe.sell_price as csv_sell_price,
                pe.current_store as csv_current_store,
                
                -- RFID Current Status
                GROUP_CONCAT(DISTINCT im.tag_id SEPARATOR ', ') as rfid_tags,
                GROUP_CONCAT(DISTINCT im.current_store SEPARATOR ', ') as rfid_current_stores,
                GROUP_CONCAT(DISTINCT im.status SEPARATOR ', ') as rfid_statuses,
                GROUP_CONCAT(DISTINCT im.rental_class_num SEPARATOR ', ') as rfid_classes,
                
                -- Usage History from POS Transactions
                COUNT(pti.contract_no) as total_transactions,
                SUM(pti.price) as total_revenue_generated,
                AVG(pti.price) as avg_transaction_value,
                MIN(pt.contract_date) as first_transaction,
                MAX(pt.contract_date) as last_transaction,
                COUNT(DISTINCT pt.customer_no) as unique_customers_served,
                COUNT(DISTINCT pt.store_no) as stores_used_in
                
            FROM pos_equipment pe
            LEFT JOIN pos_transaction_items pti ON pe.item_num = pti.item_num
            LEFT JOIN pos_transactions pt ON pti.contract_no = pt.contract_no 
                AND pt.contract_date >= :cutoff_date
            LEFT JOIN id_item_master im ON pe.item_num = im.item_num
            WHERE pe.inactive = 0
            {item_filter}
            GROUP BY pe.item_num, pe.name, pe.category, pe.sell_price, pe.current_store
            ORDER BY total_transactions DESC
            LIMIT 100
            """
            
            result = self.session.execute(text(query), {'cutoff_date': cutoff_date})
            equipment_lifecycle = []
            
            for row in result.fetchall():
                # Calculate lifecycle metrics
                first_use = row[12]  # first_transaction
                last_use = row[13]  # last_transaction
                
                lifecycle_days = 0
                if first_use and last_use:
                    lifecycle_days = (last_use - first_use).days
                
                utilization_score = 0
                if row[9]:  # total_transactions
                    utilization_score = min(100, (row[9] / (lifecycle_days + 1)) * 10) if lifecycle_days > 0 else 100
                
                equipment_lifecycle.append({
                    'item_num': row[0],
                    'equipment_name': row[1] or 'Unknown Equipment',
                    'category': row[2] or 'Uncategorized',
                    'csv_data': {
                        'sell_price': float(row[3]) if row[3] else 0.0,
                        'current_store': row[4]
                    },
                    'rfid_data': {
                        'tag_ids': row[5].split(', ') if row[5] else [],
                        'current_stores': row[6].split(', ') if row[6] else [],
                        'statuses': row[7].split(', ') if row[7] else [],
                        'rental_classes': row[8].split(', ') if row[8] else [],
                        'is_rfid_tracked': bool(row[5])
                    },
                    'usage_history': {
                        'total_transactions': row[9] or 0,
                        'total_revenue': float(row[10]) if row[10] else 0.0,
                        'avg_transaction_value': float(row[11]) if row[11] else 0.0,
                        'first_transaction': first_use.isoformat() if first_use else None,
                        'last_transaction': last_use.isoformat() if last_use else None,
                        'unique_customers': row[14] or 0,
                        'stores_used': row[15] or 0,
                        'lifecycle_days': lifecycle_days,
                        'utilization_score': round(utilization_score, 1)
                    }
                })
            
            # Generate lifecycle summary
            summary = self._generate_lifecycle_summary(equipment_lifecycle)
            
            return {
                'equipment_lifecycle': equipment_lifecycle,
                'lifecycle_summary': summary,
                'analysis_period': f"{days_back} days",
                'item_filter': item_num or 'All Items',
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Equipment lifecycle analysis failed: {e}")
            return {
                'error': str(e),
                'equipment_lifecycle': [],
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_lifecycle_summary(self, equipment_lifecycle: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics for equipment lifecycle analysis."""
        if not equipment_lifecycle:
            return {}
        
        total_items = len(equipment_lifecycle)
        rfid_tracked_items = len([eq for eq in equipment_lifecycle if eq['rfid_data']['is_rfid_tracked']])
        
        total_revenue = sum(eq['usage_history']['total_revenue'] for eq in equipment_lifecycle)
        total_transactions = sum(eq['usage_history']['total_transactions'] for eq in equipment_lifecycle)
        
        # Category breakdown
        category_stats = {}
        for eq in equipment_lifecycle:
            category = eq['category']
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'rfid_tracked': 0,
                    'total_revenue': 0.0,
                    'total_transactions': 0
                }
            
            category_stats[category]['count'] += 1
            if eq['rfid_data']['is_rfid_tracked']:
                category_stats[category]['rfid_tracked'] += 1
            category_stats[category]['total_revenue'] += eq['usage_history']['total_revenue']
            category_stats[category]['total_transactions'] += eq['usage_history']['total_transactions']
        
        return {
            'total_equipment_analyzed': total_items,
            'rfid_tracked_count': rfid_tracked_items,
            'rfid_tracking_rate': round((rfid_tracked_items / total_items * 100), 1) if total_items > 0 else 0,
            'total_revenue_generated': total_revenue,
            'total_transactions_processed': total_transactions,
            'avg_revenue_per_item': total_revenue / total_items if total_items > 0 else 0,
            'category_statistics': category_stats
        }


# Singleton instance for application use
_cross_system_analytics_service = None

def get_cross_system_analytics_service() -> CrossSystemAnalyticsService:
    """Get singleton cross-system analytics service instance."""
    global _cross_system_analytics_service
    if _cross_system_analytics_service is None:
        _cross_system_analytics_service = CrossSystemAnalyticsService()
    return _cross_system_analytics_service