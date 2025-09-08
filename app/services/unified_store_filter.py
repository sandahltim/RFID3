# app/services/unified_store_filter.py
"""
Unified Store Filtering Service for RFID3 System

This service provides unified store filtering that properly combines:
1. RFID data (id_item_master with store codes: 000, 3607, 6800, 728, 8101)
2. POS equipment data (pos_equipment with decimal stores converted to string codes)  
3. POS transaction data (pos_transactions with correlated RFID store codes)

Handles the store mapping between POS decimal codes (0.0, 1.0, etc.) and 
RFID string codes (000, 3607, etc.) using the store_correlations table.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from sqlalchemy import text, and_, or_, func, case
from sqlalchemy.orm import Query, Session
from datetime import datetime
import logging

from .. import db
from ..models.db_models import ItemMaster
from .store_correlation_service import get_store_correlation_service
from .logger import get_logger

logger = get_logger("unified_store_filter", level=logging.INFO)


class UnifiedStoreFilterService:
    """
    Provides unified store filtering across RFID and POS systems.
    Handles proper data type conversion and correlation between systems.
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db.session
        self.correlation_service = get_store_correlation_service()
        
    def get_available_stores(self) -> List[Dict[str, Any]]:
        """
        Get all available stores with their mappings and item counts.
        
        Returns:
            List of store dictionaries with RFID codes, POS codes, names, and counts
        """
        try:
            # Get store mappings
            mappings = self.correlation_service.get_all_mappings()
            
            store_data = []
            for mapping in mappings:
                if not mapping['is_active']:
                    continue
                    
                rfid_code = mapping['rfid_code']
                pos_code = mapping['pos_code']
                
                # Get RFID item count
                rfid_count = self.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM id_item_master 
                    WHERE current_store = :rfid_code OR home_store = :rfid_code
                """), {'rfid_code': rfid_code}).scalar()
                
                # Get POS equipment count  
                pos_count = self.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM pos_equipment 
                    WHERE pos_store_code = :pos_code
                """), {'pos_code': pos_code}).scalar()
                
                # Get POS transaction count (recent 30 days)
                transaction_count = self.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM pos_transactions 
                    WHERE rfid_store_code = :rfid_code 
                    AND import_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                """), {'rfid_code': rfid_code}).scalar()
                
                store_data.append({
                    'rfid_code': rfid_code,
                    'pos_code': pos_code,
                    'name': mapping['name'],
                    'location': mapping['location'],
                    'rfid_item_count': rfid_count or 0,
                    'pos_equipment_count': pos_count or 0,
                    'recent_transaction_count': transaction_count or 0,
                    'total_items': (rfid_count or 0) + (pos_count or 0),
                    'is_active': True
                })
            
            # Sort by POS code for consistent ordering
            store_data.sort(key=lambda x: int(x['pos_code']))
            
            logger.info(f"Retrieved {len(store_data)} active stores with unified counts")
            return store_data
            
        except Exception as e:
            logger.error(f"Error getting available stores: {e}")
            return []
    
    def build_unified_store_filter(self, store_filter: str, table_context: str = 'rfid') -> Tuple[str, Dict[str, Any]]:
        """
        Build SQL filter conditions for unified store filtering.
        
        Args:
            store_filter: Store code (RFID format preferred, e.g., '3607', '6800') or 'all'
            table_context: 'rfid', 'pos_equipment', 'pos_transactions', or 'combined'
            
        Returns:
            Tuple of (SQL where clause, parameters dict)
        """
        if not store_filter or store_filter == 'all':
            return ('TRUE', {})
        
        # Detect store type and get correlations
        store_type = self._detect_store_type(store_filter)
        
        if store_type == 'rfid':
            rfid_code = store_filter
            pos_code = self.correlation_service.correlate_rfid_to_pos(rfid_code)
        elif store_type == 'pos':
            pos_code = store_filter  
            rfid_code = self.correlation_service.correlate_pos_to_rfid(pos_code)
        else:
            logger.warning(f"Unknown store code format: {store_filter}")
            return ('TRUE', {})
        
        # Build context-specific filters
        if table_context == 'rfid':
            # RFID data filtering (id_item_master)
            where_clause = """
                (current_store = :rfid_code OR 
                 (current_store IS NULL AND home_store = :rfid_code))
            """
            params = {'rfid_code': rfid_code}
            
        elif table_context == 'pos_equipment':
            # POS equipment filtering
            where_clause = "pos_store_code = :pos_code"
            params = {'pos_code': pos_code}
            
        elif table_context == 'pos_transactions':
            # POS transaction filtering (uses correlated RFID codes)
            where_clause = "rfid_store_code = :rfid_code"
            params = {'rfid_code': rfid_code}
            
        elif table_context == 'combined':
            # Combined filtering for union queries
            where_clause = """
                (current_store = :rfid_code OR 
                 home_store = :rfid_code OR 
                 pos_store_code = :pos_code OR
                 rfid_store_code = :rfid_code)
            """
            params = {'rfid_code': rfid_code, 'pos_code': pos_code}
            
        else:
            logger.warning(f"Unknown table context: {table_context}")
            return ('TRUE', {})
        
        logger.debug(f"Built store filter for {table_context}: {where_clause} with params {params}")
        return (where_clause, params)
    
    def get_unified_store_summary(self, store_filter: str = 'all') -> Dict[str, Any]:
        """
        Get unified summary of items across RFID and POS systems for a specific store.
        
        Args:
            store_filter: Store code or 'all'
            
        Returns:
            Dictionary with unified store statistics
        """
        try:
            if store_filter == 'all':
                # Get totals across all stores
                rfid_total = self.session.execute(text("""
                    SELECT COUNT(*) FROM id_item_master 
                    WHERE current_store IS NOT NULL OR home_store IS NOT NULL
                """)).scalar()
                
                pos_equipment_total = self.session.execute(text("""
                    SELECT COUNT(*) FROM pos_equipment 
                    WHERE pos_store_code IS NOT NULL
                """)).scalar()
                
                pos_transaction_total = self.session.execute(text("""
                    SELECT COUNT(*) FROM pos_transactions 
                    WHERE rfid_store_code IS NOT NULL
                    AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                """)).scalar()
                
                return {
                    'store_code': 'all',
                    'store_name': 'All Stores',
                    'rfid_items': rfid_total or 0,
                    'pos_equipment': pos_equipment_total or 0,
                    'recent_transactions': pos_transaction_total or 0,
                    'total_items': (rfid_total or 0) + (pos_equipment_total or 0),
                    'is_unified': True
                }
            
            # Get specific store data
            where_rfid, params_rfid = self.build_unified_store_filter(store_filter, 'rfid')
            where_pos_equipment, params_pos_equipment = self.build_unified_store_filter(store_filter, 'pos_equipment')
            where_pos_transactions, params_pos_transactions = self.build_unified_store_filter(store_filter, 'pos_transactions')
            
            # RFID item count
            rfid_count = self.session.execute(text(f"""
                SELECT COUNT(*) FROM id_item_master WHERE {where_rfid}
            """), params_rfid).scalar()
            
            # POS equipment count
            pos_equipment_count = self.session.execute(text(f"""
                SELECT COUNT(*) FROM pos_equipment WHERE {where_pos_equipment}
            """), params_pos_equipment).scalar()
            
            # Recent transaction count
            transaction_count = self.session.execute(text(f"""
                SELECT COUNT(*) FROM pos_transactions 
                WHERE {where_pos_transactions}
                AND import_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """), params_pos_transactions).scalar()
            
            # Get store info
            store_info = self.correlation_service.get_store_info(store_filter, 'auto')
            store_name = store_info['name'] if store_info else f"Store {store_filter}"
            
            summary = {
                'store_code': store_filter,
                'store_name': store_name,
                'rfid_items': rfid_count or 0,
                'pos_equipment': pos_equipment_count or 0,
                'recent_transactions': transaction_count or 0,
                'total_items': (rfid_count or 0) + (pos_equipment_count or 0),
                'is_unified': True,
                'correlation_health': 'good' if rfid_count and pos_equipment_count else 'partial'
            }
            
            logger.info(f"Generated unified summary for store {store_filter}: {summary['total_items']} total items")
            return summary
            
        except Exception as e:
            logger.error(f"Error getting unified store summary: {e}")
            return {
                'store_code': store_filter,
                'error': str(e),
                'is_unified': False
            }
    
    def _detect_store_type(self, store_code: str) -> str:
        """Detect whether store code is RFID or POS format."""
        if store_code in ['0', '1', '2', '3', '4']:
            return 'pos'
        elif store_code in ['000', '3607', '6800', '728', '8101']:
            return 'rfid'
        else:
            # Try to auto-detect based on length and format
            if len(store_code) == 1:
                return 'pos'
            elif len(store_code) >= 3:
                return 'rfid'
            else:
                logger.warning(f"Cannot detect store type for: {store_code}")
                return 'rfid'  # Default to RFID
    
    def validate_store_filtering_health(self) -> Dict[str, Any]:
        """
        Validate the health of unified store filtering system.
        
        Returns:
            Dictionary with health status and recommendations
        """
        try:
            health_report = {
                'overall_status': 'healthy',
                'checks': [],
                'recommendations': [],
                'stats': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Check 1: Store correlation completeness
            mappings = self.correlation_service.get_all_mappings()
            active_mappings = [m for m in mappings if m['is_active']]
            
            health_report['checks'].append({
                'name': 'Store Correlation Completeness',
                'status': 'pass' if len(active_mappings) >= 5 else 'warning',
                'details': f'{len(active_mappings)}/5 store mappings active'
            })
            
            # Check 2: POS equipment correlation coverage
            pos_correlated = self.session.execute(text("""
                SELECT COUNT(*) FROM pos_equipment WHERE pos_store_code IS NOT NULL
            """)).scalar()
            
            pos_total = self.session.execute(text("""
                SELECT COUNT(*) FROM pos_equipment
            """)).scalar()
            
            coverage_rate = (pos_correlated / max(pos_total, 1)) * 100
            
            health_report['checks'].append({
                'name': 'POS Equipment Correlation Coverage',
                'status': 'pass' if coverage_rate >= 95 else 'warning',
                'details': f'{coverage_rate:.1f}% ({pos_correlated:,}/{pos_total:,}) items correlated'
            })
            
            # Check 3: Cross-system data consistency
            for mapping in active_mappings:
                rfid_code = mapping['rfid_code']
                pos_code = mapping['pos_code']
                
                rfid_count = self.session.execute(text("""
                    SELECT COUNT(*) FROM id_item_master 
                    WHERE current_store = :rfid_code OR home_store = :rfid_code
                """), {'rfid_code': rfid_code}).scalar()
                
                pos_count = self.session.execute(text("""
                    SELECT COUNT(*) FROM pos_equipment 
                    WHERE pos_store_code = :pos_code
                """), {'pos_code': pos_code}).scalar()
                
                # Both systems should have some data for active stores
                if rfid_count == 0 and pos_count == 0:
                    health_report['checks'].append({
                        'name': f'Store {mapping["name"]} Data Presence',
                        'status': 'warning',
                        'details': f'No items found in either RFID or POS systems'
                    })
            
            # Determine overall status
            warning_checks = [c for c in health_report['checks'] if c['status'] == 'warning']
            error_checks = [c for c in health_report['checks'] if c['status'] == 'error']
            
            if error_checks:
                health_report['overall_status'] = 'error'
            elif warning_checks:
                health_report['overall_status'] = 'warning'
            
            # Add statistics
            health_report['stats'] = {
                'total_mappings': len(mappings),
                'active_mappings': len(active_mappings),
                'pos_correlation_coverage': f'{coverage_rate:.1f}%',
                'total_pos_equipment': pos_total,
                'correlated_pos_equipment': pos_correlated
            }
            
            logger.info(f"Store filtering health check completed: {health_report['overall_status']}")
            return health_report
            
        except Exception as e:
            logger.error(f"Error validating store filtering health: {e}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Singleton instance
_unified_store_filter_service = None

def get_unified_store_filter_service() -> UnifiedStoreFilterService:
    """Get singleton unified store filter service instance."""
    global _unified_store_filter_service
    if _unified_store_filter_service is None:
        _unified_store_filter_service = UnifiedStoreFilterService()
    return _unified_store_filter_service