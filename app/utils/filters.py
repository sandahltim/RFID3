"""
Global Filtering System for RFID3 Inventory Management

This module provides unified filtering capabilities across all inventory views and APIs.
Enhanced in August 2025 with corrected RFID identification logic and new filter types.

Key Enhancements:
- Fixed RFID detection: 12,500+ items with NULL identifier_type + HEX EPC pattern
- Added Serialized filter: Combined QR + Sticker items (43,700+ total)  
- Proper SQLAlchemy NULL vs string handling
- Support for all inventory type filters: RFID, QR, Sticker, Serialized, Bulk

Author: System Development Team
Last Updated: 2025-08-30 - Post-Refactoring Enhancements
"""

from sqlalchemy import and_, or_

from ..models.db_models import ItemMaster


def build_global_filters(store_filter="all", type_filter="all"):
    """
    Build SQLAlchemy filter conditions for store and inventory type filtering.
    
    This function creates the core filtering logic used across all inventory
    endpoints, database views, and analytics APIs. Supports multi-store 
    operations and accurate inventory type classification.
    
    Args:
        store_filter (str): Store code filter or 'all'
            Valid values: 'all', '6800', '3607', '8101', '728'
            Maps to both home_store and current_store fields
            
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
        >>> filters = build_global_filters(store_filter='6800', type_filter='RFID')
        >>> query = session.query(ItemMaster).filter(*filters)
        >>> rfid_items_6800 = query.all()
        
    Note:
        The RFID detection logic was corrected in commit b474622 to properly
        identify items with NULL (not 'None' string) identifier_type and valid
        hexadecimal EPC tag formats. This fix revealed 12,500+ genuine RFID
        items vs 47 previously mislabeled items.
    """
    filters = []
    
    # Store filtering - supports multi-store item tracking
    if store_filter and store_filter != "all":
        filters.append(
            or_(
                ItemMaster.home_store == store_filter,      # Default store assignment
                ItemMaster.current_store == store_filter,   # Current location
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
