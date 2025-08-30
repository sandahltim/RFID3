"""
Global Filtering System for RFID3 Inventory Management

This module provides unified filtering capabilities across all inventory views and APIs.
Enhanced in August 2025 with corrected RFID identification logic and unified store filtering.

Key Enhancements:
- Fixed RFID detection: 12,500+ items with NULL identifier_type + HEX EPC pattern
- Added Serialized filter: Combined QR + Sticker items (43,700+ total)  
- Proper SQLAlchemy NULL vs string handling
- Support for all inventory type filters: RFID, QR, Sticker, Serialized, Bulk
- Unified store filtering: Properly handles both RFID codes (000, 3607, 6800, 728, 8101) 
  and POS codes (0, 1, 2, 3, 4) with automatic correlation

Author: System Development Team
Last Updated: 2025-08-30 - Unified Store Filtering Implementation
"""

from sqlalchemy import and_, or_

from ..models.db_models import ItemMaster


def build_global_filters(store_filter="all", type_filter="all"):
    """
    Build SQLAlchemy filter conditions for store and inventory type filtering.
    
    This function creates the core filtering logic used across all inventory
    endpoints, database views, and analytics APIs. Supports multi-store 
    operations with unified RFID/POS store correlation and accurate inventory type classification.
    
    Args:
        store_filter (str): Store code filter or 'all'
            Valid values: 'all' or any valid store code
            RFID format: '000', '3607', '6800', '728', '8101'  
            POS format: '0', '1', '2', '3', '4'
            Both formats are automatically correlated to filter RFID data
            
        type_filter (str): Inventory type filter or 'all'
            Valid values: 'all', 'RFID', 'QR', 'Sticker', 'Serialized', 'Bulk'
            
            Type Filter Logic (CORRECTED in 2025-08-30):
            - RFID: identifier_type IS NULL AND tag_id REGEXP '^[0-9A-Fa-f]{16,}$'
                   (12,500+ genuine RFID items with HEX EPC format)
            - QR: identifier_type = 'QR' (42,200+ items)
            - Sticker: identifier_type = 'Sticker' (1,500+ items)  
            - Serialized: identifier_type IN ('QR', 'Sticker') (43,700+ combined)
            - Bulk: identifier_type = 'Bulk' (9,900+ items)
    
    Returns:
        list: List of SQLAlchemy filter conditions to be applied to queries
        
    Example:
        >>> # Both RFID and POS codes work automatically
        >>> filters = build_global_filters(store_filter='6800', type_filter='RFID')  # RFID code
        >>> filters = build_global_filters(store_filter='2', type_filter='RFID')     # POS code -> same result
        >>> query = session.query(ItemMaster).filter(*filters)
        >>> brooklyn_park_rfid_items = query.all()
        
    Note:
        Store filtering now uses unified correlation between RFID and POS systems.
        POS codes are automatically converted to RFID codes for filtering RFID data.
        This ensures consistent results regardless of input store code format.
    """
    filters = []
    
    # Store filtering - unified RFID/POS store correlation
    if store_filter and store_filter != "all":
        # Import here to avoid circular imports
        try:
            from ..services.store_correlation_service import get_store_correlation_service
            correlation_service = get_store_correlation_service()
            
            # Detect store type and convert to RFID format for filtering
            if store_filter in ['0', '1', '2', '3', '4']:
                # POS code - convert to RFID code
                rfid_code = correlation_service.correlate_pos_to_rfid(store_filter)
                if rfid_code:
                    target_store_code = rfid_code
                else:
                    # Fallback to original if correlation fails
                    target_store_code = store_filter
            elif store_filter in ['000', '3607', '6800', '728', '8101']:
                # Already RFID code
                target_store_code = store_filter
            else:
                # Unknown format - try as-is
                target_store_code = store_filter
            
            filters.append(
                or_(
                    ItemMaster.home_store == target_store_code,      # Default store assignment
                    ItemMaster.current_store == target_store_code,   # Current location
                )
            )
            
        except Exception as e:
            # Fallback to original behavior if correlation service fails
            filters.append(
                or_(
                    ItemMaster.home_store == store_filter,      
                    ItemMaster.current_store == store_filter,   
                )
            )
    
    # Inventory type filtering - enhanced with corrected RFID logic
    if type_filter and type_filter != "all":
        if type_filter == "RFID":
            # CRITICAL FIX (2025-08-30): Proper RFID identification  
            # Items with NULL identifier_type (not 'None' string) and HEX EPC format
            filters.append(
                and_(
                    ItemMaster.identifier_type.is_(None),         # SQLAlchemy NULL check
                    ItemMaster.tag_id.op("REGEXP")("^[0-9A-Fa-f]{16,}$"),  # HEX pattern
                )
            )
        elif type_filter == "Serialized":
            # NEW FILTER: Combined QR + Sticker items for comprehensive serial tracking
            filters.append(ItemMaster.identifier_type.in_(["QR", "Sticker"]))
        else:
            # Standard type filtering for QR, Sticker, Bulk, etc.
            filters.append(ItemMaster.identifier_type == type_filter)
    
    return filters


def apply_global_filters(query, store_filter="all", type_filter="all"):
    """
    Apply store and type filters to an existing SQLAlchemy query.
    
    This is a convenience function that applies the filters returned by
    build_global_filters() to a query object. Used extensively across
    inventory analytics, dashboard APIs, and database viewer.
    
    Args:
        query: SQLAlchemy Query object (typically ItemMaster query)
        store_filter (str): Store code filter or 'all' 
        type_filter (str): Inventory type filter or 'all'
        
    Returns:
        Query: Filtered SQLAlchemy Query object ready for execution
        
    Example:
        >>> base_query = session.query(ItemMaster)
        >>> filtered_query = apply_global_filters(base_query, '6800', 'RFID')
        >>> results = filtered_query.all()
        
    Usage across system:
        - inventory_analytics.py: Dashboard summary and BI analytics
        - database_viewer.py: Table data filtering and exploration  
        - enhanced_analytics_api.py: KPI calculations with filtering
        - All tab routes: Consistent filtering across operational views
    """
    for condition in build_global_filters(store_filter, type_filter):
        query = query.filter(condition)
    return query
