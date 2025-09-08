# app/services/enhanced_filtering_service.py
"""
Enhanced Filtering Service with Cross-System Store Correlation
Provides unified filtering capabilities across RFID and POS data systems.
"""

from typing import Dict, List, Optional, Union, Any
from sqlalchemy import text, and_, or_, func
from sqlalchemy.orm import Query
from datetime import datetime, timedelta
import logging

from .. import db
from ..models.db_models import ItemMaster
from .store_correlation_service import get_store_correlation_service
from .rfid_api_compatibility import get_rfid_api_compatibility_layer
from .logger import get_logger

logger = get_logger("enhanced_filtering", level=logging.INFO)


class EnhancedFilteringService:
    """
    Enhanced filtering service that provides unified filtering across RFID and POS systems
    while maintaining API compatibility and enabling cross-system correlations.
    """
    
    def __init__(self):
        self.session = db.session
        self.correlation_service = get_store_correlation_service()
        self.compatibility_layer = get_rfid_api_compatibility_layer()
    
    def apply_store_filter(self, query: Query, store_code: str, 
                          table_alias: str = None, store_type: str = 'auto') -> Query:
        """
        Apply store filtering to a query with cross-system correlation support.
        
        Args:
            query: SQLAlchemy query object
            store_code: Store code to filter by
            table_alias: Table alias if using joins
            store_type: 'rfid', 'pos', 'auto', or 'both'
            
        Returns:
            Modified query with store filter applied
        """
        if not store_code or store_code == 'all':
            return query
        
        try:
            # Auto-detect store type if needed
            if store_type == 'auto':
                store_type = self._detect_store_type(store_code)
            
            table_prefix = f"{table_alias}." if table_alias else ""
            
            # Get the model class from the query
            model_class = query.column_descriptions[0]['type']
            table_name = model_class.__tablename__
            
            if table_name == 'id_item_master':
                return self._apply_item_master_store_filter(query, store_code, store_type, table_prefix)
            elif table_name == 'pos_transactions':
                return self._apply_pos_transactions_store_filter(query, store_code, store_type, table_prefix)
            elif table_name == 'pos_equipment':
                return self._apply_pos_equipment_store_filter(query, store_code, store_type, table_prefix)
            else:
                logger.warning(f"Store filtering not implemented for table: {table_name}")
                return query
                
        except Exception as e:
            logger.error(f"Error applying store filter: {e}")
            return query
    
    def _detect_store_type(self, store_code: str) -> str:
        """Detect whether store code is RFID or POS format."""
        if store_code in ['1', '2', '3', '4', '0']:
            return 'pos'
        elif store_code in ['3607', '6800', '728', '8101', '000']:
            return 'rfid'
        else:
            logger.warning(f"Unknown store code format: {store_code}, defaulting to RFID")
            return 'rfid'
    
    def _apply_item_master_store_filter(self, query: Query, store_code: str, 
                                       store_type: str, table_prefix: str) -> Query:
        """Apply store filter to id_item_master table."""
        filter_conditions = []
        
        if store_type in ['rfid', 'both']:
            # Use API fields for RFID filtering (maintains compatibility)
            if store_type == 'rfid':
                # Direct RFID code filtering
                filter_conditions.append(
                    or_(
                        text(f"{table_prefix}current_store = :rfid_code"),
                        and_(
                            text(f"{table_prefix}current_store IS NULL"),
                            text(f"{table_prefix}home_store = :rfid_code")
                        ),
                        and_(
                            text(f"{table_prefix}current_store IS NULL"),
                            text(f"{table_prefix}home_store IS NULL"),
                            text(f"'{store_code}' = '000'")  # Legacy/unassigned
                        )
                    )
                )
            else:  # both
                filter_conditions.append(text(f"{table_prefix}rfid_store_code = :rfid_code"))
        
        if store_type in ['pos', 'both']:
            if store_type == 'pos':
                # Convert POS code to RFID code for filtering
                rfid_code = self.correlation_service.correlate_pos_to_rfid(store_code)
                if rfid_code:
                    filter_conditions.append(
                        or_(
                            text(f"{table_prefix}current_store = :corr_rfid_code"),
                            and_(
                                text(f"{table_prefix}current_store IS NULL"),
                                text(f"{table_prefix}home_store = :corr_rfid_code")
                            )
                        )
                    )
                    query = query.params(corr_rfid_code=rfid_code)
            else:  # both
                filter_conditions.append(text(f"{table_prefix}pos_store_code = :pos_code"))
        
        if filter_conditions:
            combined_filter = or_(*filter_conditions) if len(filter_conditions) > 1 else filter_conditions[0]
            query = query.filter(combined_filter)
            
            # Add parameters
            if store_type in ['rfid', 'both']:
                query = query.params(rfid_code=store_code)
            if store_type in ['pos', 'both']:
                query = query.params(pos_code=store_code)
        
        return query
    
    def _apply_pos_transactions_store_filter(self, query: Query, store_code: str,
                                           store_type: str, table_prefix: str) -> Query:
        """Apply store filter to pos_transactions table."""
        filter_conditions = []
        
        if store_type in ['pos', 'both']:
            filter_conditions.append(text(f"{table_prefix}store_no = :pos_code"))
        
        if store_type in ['rfid', 'both']:
            if store_type == 'rfid':
                # Convert RFID to POS for native filtering, plus use correlation field
                pos_code = self.correlation_service.correlate_rfid_to_pos(store_code)
                if pos_code:
                    filter_conditions.extend([
                        text(f"{table_prefix}store_no = :corr_pos_code"),
                        text(f"{table_prefix}rfid_store_code = :rfid_code")
                    ])
                    query = query.params(corr_pos_code=pos_code, rfid_code=store_code)
            else:  # both
                filter_conditions.append(text(f"{table_prefix}rfid_store_code = :rfid_code"))
        
        if filter_conditions:
            combined_filter = or_(*filter_conditions) if len(filter_conditions) > 1 else filter_conditions[0]
            query = query.filter(combined_filter)
            
            if store_type in ['pos', 'both'] and 'pos_code' not in query.statement.compile().params:
                query = query.params(pos_code=store_code)
        
        return query
    
    def _apply_pos_equipment_store_filter(self, query: Query, store_code: str,
                                        store_type: str, table_prefix: str) -> Query:
        """Apply store filter to pos_equipment table."""
        filter_conditions = []
        
        if store_type in ['pos', 'both']:
            filter_conditions.extend([
                text(f"{table_prefix}home_store = :pos_code"),
                text(f"{table_prefix}current_store = :pos_code")
            ])
        
        if store_type in ['rfid', 'both']:
            filter_conditions.extend([
                text(f"{table_prefix}rfid_home_store = :rfid_code"),
                text(f"{table_prefix}rfid_current_store = :rfid_code")
            ])
        
        if filter_conditions:
            combined_filter = or_(*filter_conditions)
            query = query.filter(combined_filter)
            
            # Add parameters
            if store_type in ['pos', 'both']:
                query = query.params(pos_code=store_code)
            if store_type in ['rfid', 'both']:
                query = query.params(rfid_code=store_code)
        
        return query
    
    def build_cross_system_query(self, base_query: str, filters: Dict[str, Any]) -> str:
        """
        Build cross-system query with correlation joins and filters.
        
        Args:
            base_query: Base SQL query template
            filters: Dictionary of filter parameters
            
        Returns:
            Enhanced SQL query with cross-system correlations
        """
        try:
            enhanced_query = base_query
            where_conditions = []
            join_clauses = []
            parameters = {}
            
            # Store filtering
            if filters.get('store_code') and filters['store_code'] != 'all':
                store_code = filters['store_code']
                store_type = filters.get('store_type', 'auto')
                
                if store_type == 'auto':
                    store_type = self._detect_store_type(store_code)
                
                store_condition = self._build_store_condition(store_code, store_type)
                if store_condition:
                    where_conditions.append(store_condition)
                    parameters[f'store_code'] = store_code
            
            # Date range filtering
            if filters.get('date_from') or filters.get('date_to'):
                date_condition = self._build_date_condition(
                    filters.get('date_from'),
                    filters.get('date_to'),
                    filters.get('date_field', 'created_at')
                )
                if date_condition:
                    where_conditions.append(date_condition)
                    if filters.get('date_from'):
                        parameters['date_from'] = filters['date_from']
                    if filters.get('date_to'):
                        parameters['date_to'] = filters['date_to']
            
            # Status filtering
            if filters.get('status') and filters['status'] != 'all':
                status_list = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
                status_placeholders = ', '.join([f"'{status}'" for status in status_list])
                where_conditions.append(f"status IN ({status_placeholders})")
            
            # Category filtering (for equipment/inventory)
            if filters.get('category') and filters['category'] != 'all':
                where_conditions.append(f"category = '{filters['category']}'")
            
            # Add cross-system correlation joins if needed
            if filters.get('include_correlations', False):
                correlation_joins = self._build_correlation_joins(filters.get('base_table', 'id_item_master'))
                join_clauses.extend(correlation_joins)
            
            # Assemble final query
            if join_clauses:
                # Find the FROM clause and add joins
                from_pos = enhanced_query.upper().find('FROM')
                if from_pos != -1:
                    where_pos = enhanced_query.upper().find('WHERE', from_pos)
                    if where_pos != -1:
                        insert_pos = where_pos
                    else:
                        insert_pos = len(enhanced_query)
                    
                    join_clause = ' ' + ' '.join(join_clauses) + ' '
                    enhanced_query = enhanced_query[:insert_pos] + join_clause + enhanced_query[insert_pos:]
            
            # Add WHERE conditions
            if where_conditions:
                if 'WHERE' in enhanced_query.upper():
                    enhanced_query += ' AND ' + ' AND '.join(where_conditions)
                else:
                    enhanced_query += ' WHERE ' + ' AND '.join(where_conditions)
            
            logger.debug(f"Built enhanced query with {len(where_conditions)} conditions and {len(join_clauses)} joins")
            return enhanced_query, parameters
            
        except Exception as e:
            logger.error(f"Error building cross-system query: {e}")
            return base_query, {}
    
    def _build_store_condition(self, store_code: str, store_type: str) -> Optional[str]:
        """Build store filtering condition for SQL query."""
        conditions = []
        
        if store_type in ['rfid', 'both']:
            conditions.append(f"COALESCE(current_store, home_store, '000') = '{store_code}'")
        
        if store_type in ['pos', 'both']:
            # For POS filtering, use correlation or convert to RFID
            if store_type == 'pos':
                rfid_code = self.correlation_service.correlate_pos_to_rfid(store_code)
                if rfid_code:
                    conditions.append(f"COALESCE(current_store, home_store, '000') = '{rfid_code}'")
            else:  # both
                conditions.append(f"pos_store_code = '{store_code}'")
        
        return f"({' OR '.join(conditions)})" if conditions else None
    
    def _build_date_condition(self, date_from: str, date_to: str, date_field: str) -> Optional[str]:
        """Build date range filtering condition."""
        conditions = []
        
        if date_from:
            conditions.append(f"{date_field} >= '{date_from}'")
        if date_to:
            conditions.append(f"{date_field} <= '{date_to}'")
        
        return ' AND '.join(conditions) if conditions else None
    
    def _build_correlation_joins(self, base_table: str) -> List[str]:
        """Build correlation join clauses for cross-system queries."""
        joins = []
        
        if base_table == 'id_item_master':
            joins.append("""
                LEFT JOIN store_correlations sc ON 
                COALESCE(id_item_master.current_store, id_item_master.home_store, '000') = sc.rfid_store_code
            """)
        elif base_table == 'pos_transactions':
            joins.append("""
                LEFT JOIN store_correlations sc ON pos_transactions.store_no = sc.pos_store_code
            """)
        
        return joins
    
    def get_unified_store_analytics(self, store_code: str = None, 
                                   date_range_days: int = 30) -> Dict[str, Any]:
        """
        Get unified analytics across both RFID and POS systems for a store.
        
        Args:
            store_code: Store code (auto-detects type)
            date_range_days: Date range for analytics
            
        Returns:
            Unified analytics dictionary
        """
        try:
            store_type = self._detect_store_type(store_code) if store_code else 'both'
            
            # Get store information
            store_info = self.correlation_service.get_store_info(store_code, store_type)
            
            # Build date filter
            date_filter = f"AND contract_date >= DATE_SUB(NOW(), INTERVAL {date_range_days} DAY)" if date_range_days else ""
            
            # Get cross-system analytics
            analytics_query = f"""
                SELECT 
                    -- Store identification
                    sc.rfid_store_code,
                    sc.pos_store_code,
                    sc.store_name,
                    
                    -- RFID System metrics
                    COUNT(DISTINCT im.tag_id) as rfid_total_items,
                    SUM(CASE WHEN im.status IN ('On Rent', 'Delivered', 'Out to Customer') THEN 1 ELSE 0 END) as rfid_on_rent,
                    SUM(CASE WHEN im.status = 'Ready to Rent' THEN 1 ELSE 0 END) as rfid_available,
                    SUM(CASE WHEN im.date_last_scanned >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as rfid_recent_scans,
                    
                    -- POS System metrics
                    COUNT(DISTINCT pt.contract_no) as pos_total_contracts,
                    SUM(COALESCE(pt.total, 0)) as pos_total_revenue,
                    AVG(COALESCE(pt.total, 0)) as pos_avg_contract_value,
                    COUNT(DISTINCT pt.customer_no) as pos_unique_customers,
                    
                    -- Equipment metrics
                    COUNT(DISTINCT pe.item_num) as pos_equipment_items,
                    SUM(COALESCE(pe.turnover_ytd, 0)) as pos_equipment_turnover,
                    
                    -- Correlation health
                    SUM(CASE WHEN im.rfid_store_code IS NOT NULL THEN 1 ELSE 0 END) as correlated_items_count,
                    SUM(CASE WHEN pt.rfid_store_code IS NOT NULL THEN 1 ELSE 0 END) as correlated_transactions_count
                    
                FROM store_correlations sc
                LEFT JOIN id_item_master im ON (
                    sc.rfid_store_code = COALESCE(im.current_store, im.home_store, '000')
                )
                LEFT JOIN pos_transactions pt ON (
                    sc.pos_store_code = pt.store_no {date_filter}
                )
                LEFT JOIN pos_equipment pe ON (
                    sc.pos_store_code = pe.current_store OR sc.pos_store_code = pe.home_store
                )
                WHERE sc.is_active = TRUE
                {f"AND sc.rfid_store_code = '{store_code}'" if store_type == 'rfid' and store_code else ""}
                {f"AND sc.pos_store_code = '{store_code}'" if store_type == 'pos' and store_code else ""}
                GROUP BY sc.rfid_store_code, sc.pos_store_code, sc.store_name
            """
            
            if store_code:
                analytics_query += f" HAVING sc.rfid_store_code = '{store_info.get('rfid_store_code')}'"
            
            result = self.session.execute(text(analytics_query)).fetchone()
            
            if result:
                analytics = {
                    'store_info': store_info,
                    'rfid_metrics': {
                        'total_items': int(result[3] or 0),
                        'items_on_rent': int(result[4] or 0),
                        'items_available': int(result[5] or 0),
                        'recent_scans': int(result[6] or 0),
                        'utilization_rate': round((int(result[4] or 0) / max(int(result[3] or 0), 1)) * 100, 1)
                    },
                    'pos_metrics': {
                        'total_contracts': int(result[7] or 0),
                        'total_revenue': float(result[8] or 0),
                        'avg_contract_value': float(result[9] or 0),
                        'unique_customers': int(result[10] or 0)
                    },
                    'equipment_metrics': {
                        'equipment_items': int(result[11] or 0),
                        'equipment_turnover': float(result[12] or 0)
                    },
                    'correlation_health': {
                        'correlated_items': int(result[13] or 0),
                        'correlated_transactions': int(result[14] or 0),
                        'correlation_rate': round((int(result[13] or 0) / max(int(result[3] or 0), 1)) * 100, 1)
                    },
                    'date_range_days': date_range_days
                }
                
                return analytics
            
        except Exception as e:
            logger.error(f"Error getting unified store analytics: {e}")
        
        return {}
    
    def validate_filter_performance(self, query_type: str = 'basic') -> Dict[str, Any]:
        """
        Validate performance of enhanced filtering system.
        
        Args:
            query_type: Type of query to test ('basic', 'correlation', 'cross_system')
            
        Returns:
            Performance validation results
        """
        performance_results = {
            'query_type': query_type,
            'tested_at': datetime.now().isoformat(),
            'results': {}
        }
        
        try:
            start_time = datetime.now()
            
            if query_type == 'basic':
                # Test basic store filtering
                query = self.session.query(ItemMaster)
                query = self.apply_store_filter(query, '3607', store_type='rfid')
                result_count = query.count()
                
            elif query_type == 'correlation':
                # Test correlation-based filtering
                result = self.session.execute(text("""
                    SELECT COUNT(*) FROM id_item_master im
                    JOIN store_correlations sc ON im.rfid_store_code = sc.rfid_store_code
                    WHERE sc.is_active = TRUE
                """)).scalar()
                result_count = result
                
            elif query_type == 'cross_system':
                # Test cross-system analytics
                analytics = self.get_unified_store_analytics('3607', 30)
                result_count = len(analytics)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            performance_results['results'] = {
                'execution_time_seconds': execution_time,
                'result_count': result_count,
                'performance_rating': 'good' if execution_time < 1.0 else 'needs_optimization',
                'recommendations': []
            }
            
            if execution_time > 2.0:
                performance_results['results']['recommendations'].append(
                    "Consider adding database indexes for better performance"
                )
            
        except Exception as e:
            logger.error(f"Error validating filter performance: {e}")
            performance_results['results']['error'] = str(e)
        
        return performance_results


# Global service instance
_enhanced_filtering_service = None

def get_enhanced_filtering_service() -> EnhancedFilteringService:
    """Get singleton instance of EnhancedFilteringService."""
    global _enhanced_filtering_service
    if _enhanced_filtering_service is None:
        _enhanced_filtering_service = EnhancedFilteringService()
    return _enhanced_filtering_service