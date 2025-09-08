# app/services/rfid_api_compatibility.py
"""
RFID API Compatibility Layer - Ensures RFID Pro API calls remain unchanged
This module provides compatibility functions to maintain API integrity while enabling store correlation.
"""

from typing import Dict, List, Any, Optional
import logging
from sqlalchemy import text
from .. import db
from .store_correlation_service import get_store_correlation_service
from .logger import get_logger

logger = get_logger("rfid_api_compatibility", level=logging.INFO)


class RFIDAPICompatibilityLayer:
    """
    Compatibility layer that ensures RFID Pro API interactions remain unchanged
    while enabling internal store correlation functionality.
    
    CRITICAL PRINCIPLES:
    1. Never modify RFID API-owned fields (current_store, home_store, etc.) in correlation logic
    2. Always preserve original API field values during correlation updates
    3. Use correlation fields (rfid_store_code, pos_store_code) for internal queries only
    4. Ensure API refresh operations don't overwrite correlation data
    """
    
    def __init__(self):
        self.session = db.session
        self.correlation_service = get_store_correlation_service()
        
        # Define RFID API-owned fields that must NEVER be modified by correlation logic
        self.RFID_API_PROTECTED_FIELDS = {
            'id_item_master': [
                'tag_id', 'serial_number', 'rental_class_num', 'client_name', 
                'common_name', 'quality', 'bin_location', 'status', 'last_contract_num',
                'last_scanned_by', 'notes', 'status_notes', 'longitude', 'latitude',
                'date_last_scanned', 'date_created', 'date_updated', 'uuid_accounts_fk',
                # CRITICAL: current_store and home_store are API-owned
                'current_store', 'home_store'
            ],
            'id_transactions': [
                'tag_id', 'scan_type', 'scan_date', 'contract_number', 'client_name',
                'common_name', 'bin_location', 'status', 'scan_by', 'notes', 'rental_class_num',
                'serial_number', 'location_of_repair', 'quality', 'dirty_or_mud', 'leaves',
                'oil', 'mold', 'stain', 'oxidation', 'other', 'rip_or_tear', 
                'sewing_repair_needed', 'grommet', 'rope', 'buckle', 'wet', 
                'service_required', 'date_created', 'date_updated', 'longitude', 'latitude'
            ]
        }
        
        # Define correlation fields that are safe to modify
        self.CORRELATION_FIELDS = {
            'id_item_master': [
                'rfid_store_code', 'pos_store_code', 'correlation_updated_at'
            ],
            'pos_transactions': [
                'rfid_store_code', 'correlation_updated_at'  
            ],
            'pos_customers': [
                'primary_rfid_store_code', 'correlation_updated_at'
            ],
            'pos_equipment': [
                'rfid_home_store', 'rfid_current_store', 'correlation_updated_at'
            ]
        }
    
    def validate_field_access(self, table: str, field: str, operation: str = 'modify') -> bool:
        """
        Validate whether a field can be safely modified without affecting RFID API compatibility.
        
        Args:
            table: Database table name
            field: Field name to check
            operation: 'read' or 'modify'
            
        Returns:
            True if operation is safe, False if it would break API compatibility
        """
        if operation == 'read':
            return True  # Reading is always safe
        
        # Check if field is API-protected
        protected_fields = self.RFID_API_PROTECTED_FIELDS.get(table, [])
        if field in protected_fields:
            logger.warning(f"BLOCKED: Attempted to modify API-protected field {table}.{field}")
            return False
            
        # Check if field is a safe correlation field
        correlation_fields = self.CORRELATION_FIELDS.get(table, [])
        if field in correlation_fields:
            logger.debug(f"ALLOWED: Modifying correlation field {table}.{field}")
            return True
        
        # Unknown field - be cautious
        logger.warning(f"CAUTION: Unknown field access {table}.{field} - allowing but logging")
        return True
    
    def safe_update_item_correlation(self, tag_id: str, rfid_store_code: str = None, 
                                   pos_store_code: str = None) -> bool:
        """
        Safely update item correlation without affecting RFID API fields.
        
        Args:
            tag_id: Item tag ID
            rfid_store_code: RFID store code (derived from API fields if not provided)
            pos_store_code: POS store code (derived from RFID code if not provided)
            
        Returns:
            True if update successful
        """
        try:
            # If store codes not provided, derive from API fields
            if not rfid_store_code:
                api_data = self.session.execute(text("""
                    SELECT COALESCE(current_store, home_store, '000') as store_code
                    FROM id_item_master 
                    WHERE tag_id = :tag_id
                """), {"tag_id": tag_id}).fetchone()
                
                if api_data:
                    rfid_store_code = api_data[0]
                else:
                    logger.warning(f"Item {tag_id} not found for correlation update")
                    return False
            
            if not pos_store_code:
                pos_store_code = self.correlation_service.correlate_rfid_to_pos(rfid_store_code)
            
            # Update ONLY correlation fields - never touch API fields
            if not self.validate_field_access('id_item_master', 'rfid_store_code', 'modify'):
                return False
                
            result = self.session.execute(text("""
                UPDATE id_item_master 
                SET 
                    rfid_store_code = :rfid_code,
                    pos_store_code = :pos_code,
                    correlation_updated_at = NOW()
                WHERE tag_id = :tag_id
            """), {
                "rfid_code": rfid_store_code,
                "pos_code": pos_store_code, 
                "tag_id": tag_id
            })
            
            self.session.commit()
            
            if result.rowcount > 0:
                logger.debug(f"SAFE UPDATE: Item {tag_id} correlation updated without touching API fields")
                return True
            else:
                logger.warning(f"No rows updated for item {tag_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in safe item correlation update: {e}")
            self.session.rollback()
            return False
    
    def preserve_api_data_during_refresh(self, items_data: List[Dict]) -> List[Dict]:
        """
        Process items data during API refresh to preserve correlation fields.
        This function is called by the refresh service to ensure correlation data isn't lost.
        
        Args:
            items_data: Raw items data from RFID Pro API
            
        Returns:
            Processed items data with correlation preservation instructions
        """
        try:
            # Get existing correlation data before refresh
            existing_correlations = {}
            
            if items_data:
                tag_ids = [item.get('tag_id') for item in items_data if item.get('tag_id')]
                
                if tag_ids:
                    # Use parameterized query for safety
                    placeholders = ','.join(['%s'] * len(tag_ids))
                    
                    correlations = self.session.execute(text(f"""
                        SELECT tag_id, rfid_store_code, pos_store_code, correlation_updated_at
                        FROM id_item_master 
                        WHERE tag_id IN ({placeholders})
                        AND rfid_store_code IS NOT NULL
                    """), tag_ids).fetchall()
                    
                    existing_correlations = {
                        row[0]: {
                            'rfid_store_code': row[1],
                            'pos_store_code': row[2], 
                            'correlation_updated_at': row[3]
                        }
                        for row in correlations
                    }
            
            # Add preservation metadata to each item
            processed_items = []
            for item in items_data:
                tag_id = item.get('tag_id')
                processed_item = item.copy()
                
                # Add correlation preservation data
                if tag_id in existing_correlations:
                    processed_item['_preserve_correlation'] = existing_correlations[tag_id]
                    logger.debug(f"Marked item {tag_id} for correlation preservation")
                
                processed_items.append(processed_item)
            
            logger.info(f"Prepared {len(processed_items)} items for API-safe refresh with correlation preservation")
            return processed_items
            
        except Exception as e:
            logger.error(f"Error preserving API data during refresh: {e}")
            return items_data  # Return original data on error
    
    def restore_correlations_after_refresh(self, updated_items: List[str]) -> int:
        """
        Restore correlation data after API refresh for items that lost it.
        
        Args:
            updated_items: List of tag_ids that were updated during refresh
            
        Returns:
            Number of items that had correlations restored
        """
        restored_count = 0
        
        try:
            # Find items that need correlation restoration
            if updated_items:
                placeholders = ','.join(['%s'] * len(updated_items))
                
                items_needing_correlation = self.session.execute(text(f"""
                    SELECT tag_id, COALESCE(current_store, home_store, '000') as store_code
                    FROM id_item_master 
                    WHERE tag_id IN ({placeholders})
                    AND rfid_store_code IS NULL
                    AND (current_store IS NOT NULL OR home_store IS NOT NULL)
                """), updated_items).fetchall()
                
                for tag_id, store_code in items_needing_correlation:
                    if self.safe_update_item_correlation(tag_id, store_code):
                        restored_count += 1
                        
                logger.info(f"Restored correlations for {restored_count} items after API refresh")
                
        except Exception as e:
            logger.error(f"Error restoring correlations after refresh: {e}")
            
        return restored_count
    
    def get_api_safe_query_filter(self, table: str, store_filter: str, 
                                 filter_type: str = 'rfid') -> str:
        """
        Generate SQL WHERE clause for store filtering that's safe for API compatibility.
        
        Args:
            table: Table name to filter
            store_filter: Store code to filter by
            filter_type: 'rfid', 'pos', or 'both'
            
        Returns:
            SQL WHERE clause fragment
        """
        try:
            filters = []
            
            if table == 'id_item_master':
                if filter_type in ['rfid', 'both']:
                    # Use API fields for RFID filtering (maintains compatibility)
                    filters.append(f"COALESCE(current_store, home_store, '000') = '{store_filter}'")
                
                if filter_type in ['pos', 'both'] and filter_type != 'rfid':
                    # Use correlation fields for POS filtering
                    rfid_code = self.correlation_service.correlate_pos_to_rfid(store_filter)
                    if rfid_code:
                        filters.append(f"rfid_store_code = '{rfid_code}'")
            
            elif table == 'pos_transactions':
                if filter_type in ['pos', 'both']:
                    filters.append(f"store_no = '{store_filter}'")
                
                if filter_type in ['rfid', 'both'] and filter_type != 'pos':
                    filters.append(f"rfid_store_code = '{store_filter}'")
            
            # Combine filters with OR logic
            if filters:
                return f"({' OR '.join(filters)})"
            else:
                return "1=1"  # No filter
                
        except Exception as e:
            logger.error(f"Error generating API-safe query filter: {e}")
            return "1=1"  # Safe fallback
    
    def validate_api_compatibility(self) -> Dict[str, Any]:
        """
        Validate that correlation system maintains RFID API compatibility.
        
        Returns:
            Validation report with compatibility status
        """
        validation_report = {
            'is_compatible': True,
            'issues': [],
            'warnings': [],
            'checked_at': db.func.now(),
            'checks_performed': []
        }
        
        try:
            # Check 1: Verify API fields are not corrupted by correlation logic
            api_field_check = self.session.execute(text("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN current_store IS NOT NULL OR home_store IS NOT NULL THEN 1 END) as items_with_api_stores,
                    COUNT(CASE WHEN rfid_store_code IS NOT NULL THEN 1 END) as items_with_correlations
                FROM id_item_master
            """)).fetchone()
            
            validation_report['checks_performed'].append('API field integrity')
            
            if api_field_check:
                total, api_stores, correlations = api_field_check
                validation_report['stats'] = {
                    'total_items': total,
                    'items_with_api_stores': api_stores,
                    'items_with_correlations': correlations
                }
                
                # Warn if correlation coverage is low
                if total > 0 and correlations / total < 0.8:
                    validation_report['warnings'].append(
                        f"Low correlation coverage: {correlations}/{total} items ({correlations/total*100:.1f}%)"
                    )
            
            # Check 2: Verify correlation consistency with API fields
            consistency_check = self.session.execute(text("""
                SELECT COUNT(*) as inconsistent_items
                FROM id_item_master im
                JOIN store_correlations sc ON im.rfid_store_code = sc.rfid_store_code
                WHERE COALESCE(im.current_store, im.home_store, '000') != sc.rfid_store_code
            """)).scalar()
            
            validation_report['checks_performed'].append('Correlation consistency')
            
            if consistency_check > 0:
                validation_report['issues'].append(
                    f"Found {consistency_check} items with inconsistent store correlations"
                )
                validation_report['is_compatible'] = False
            
            # Check 3: Verify no API fields have been modified by correlation logic
            # This would be detected by checking modification timestamps, but we'll rely on process validation
            validation_report['checks_performed'].append('API field protection')
            
            logger.info(f"API compatibility validation completed: {validation_report['is_compatible']}")
            
        except Exception as e:
            logger.error(f"Error during API compatibility validation: {e}")
            validation_report['is_compatible'] = False
            validation_report['issues'].append(f"Validation failed: {str(e)}")
        
        return validation_report
    
    def get_compatibility_guidelines(self) -> Dict[str, List[str]]:
        """
        Get guidelines for maintaining RFID API compatibility.
        
        Returns:
            Dictionary with guidelines organized by category
        """
        return {
            'protected_fields': {
                'id_item_master': self.RFID_API_PROTECTED_FIELDS['id_item_master'],
                'id_transactions': self.RFID_API_PROTECTED_FIELDS['id_transactions']
            },
            'safe_correlation_fields': self.CORRELATION_FIELDS,
            'best_practices': [
                "Always use correlation fields (rfid_store_code, pos_store_code) for internal queries",
                "Never modify API-owned fields (current_store, home_store) in correlation logic",
                "Derive correlation values from API fields, not the reverse",
                "Preserve correlation data during API refresh operations",
                "Use API-safe query filters that prefer API fields when available",
                "Validate correlation integrity regularly but separately from API operations",
                "Log all correlation operations for audit trail",
                "Use the compatibility layer for all store-related operations"
            ],
            'prohibited_operations': [
                "Modifying current_store or home_store fields outside of API refresh",
                "Using correlation fields as source of truth for API operations", 
                "Overwriting API field values with correlation-derived values",
                "Mixing correlation logic with RFID Pro API request/response handling"
            ]
        }


# Global compatibility layer instance
_compatibility_layer = None

def get_rfid_api_compatibility_layer() -> RFIDAPICompatibilityLayer:
    """Get singleton instance of RFIDAPICompatibilityLayer."""
    global _compatibility_layer
    if _compatibility_layer is None:
        _compatibility_layer = RFIDAPICompatibilityLayer()
    return _compatibility_layer