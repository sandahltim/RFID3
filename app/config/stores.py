# app/config/stores.py
# Centralized Store Configuration - Version: 2025-08-27-v1
"""
Centralized store mapping configuration for all RFID system components.
This file serves as the single source of truth for store information.

IMPORTANT: When adding or modifying stores, update all references:
- Executive Dashboard (tab7.py, tab7.html)
- Global Filters (global_filters.html)
- Inventory Analytics (inventory_analytics.html)
- Any other store-aware components
"""

from typing import Dict, NamedTuple


class StoreInfo(NamedTuple):
    """Comprehensive store information structure."""

    store_code: str  # Primary identifier (standardized as store_code)
    name: str
    location: str
    pos_code: str  # POS system code (001, 002, 003, 004, 000)
    emoji: str
    approximate_items: str
    opened_date: str  # YYYY-MM-DD format
    business_type: str  # Business model description
    manager: str  # Current manager name
    active: bool  # Store operational status


# Master store configuration - THIS IS THE SINGLE SOURCE OF TRUTH
# Updated 2025-09-02 with comprehensive store information
STORES = {
    "3607": StoreInfo(
        store_code="3607",
        name="Wayzata",
        location="Wayzata, MN",
        pos_code="001",  # POS system uses 001 (may appear as 1)
        emoji="🏬",
        approximate_items="5K+",
        opened_date="2008-01-01",  # Oldest location
        business_type="90% DIY/10% Events",
        manager="TYLER",
        active=True
    ),
    "6800": StoreInfo(
        store_code="6800",
        name="Brooklyn Park",
        location="Brooklyn Park, MN",
        pos_code="002",  # POS system uses 002 (may appear as 2)
        emoji="🏪",
        approximate_items="22K+",
        opened_date="2022-01-01",
        business_type="100% Construction",
        manager="ZACK",
        active=True
    ),
    "8101": StoreInfo(
        store_code="8101",
        name="Fridley",
        location="Fridley, MN",
        pos_code="003",  # POS system uses 003 (may appear as 3)
        emoji="🏢",
        approximate_items="3K+",
        opened_date="2022-01-01",
        business_type="100% Events (Broadway Tent & Event)",
        manager="TIM",
        active=True
    ),
    "728": StoreInfo(
        store_code="728",
        name="Elk River",
        location="Elk River, MN",
        pos_code="004",  # POS system uses 004 (may appear as 4)
        emoji="🏭",
        approximate_items="3K+",
        opened_date="2024-01-01",  # Newest location
        business_type="90% DIY/10% Events",
        manager="BRUCE",
        active=True
    ),
    "000": StoreInfo(
        store_code="000",
        name="Legacy/Unassigned",
        location="Multiple Locations",
        pos_code="000",  # Legacy/unassigned items
        emoji="❓",
        approximate_items="20K+",
        opened_date="2008-01-01",  # Historical data
        business_type="Mixed/Historical Data",
        manager="SYSTEM",
        active=False  # Not an active store location
    ),
}

# Convenience mappings for backward compatibility and easy access
STORE_MAPPING = {store_code: info.name for store_code, info in STORES.items()}
STORE_LOCATIONS = {store_code: info.location for store_code, info in STORES.items()}
STORE_MANAGERS = {store_code: info.manager for store_code, info in STORES.items()}
STORE_BUSINESS_TYPES = {store_code: info.business_type for store_code, info in STORES.items()}
STORE_OPENING_DATES = {store_code: info.opened_date for store_code, info in STORES.items()}

# POS code mappings (handles leading zero variations)
POS_CODE_MAPPING = {info.pos_code: store_code for store_code, info in STORES.items()}
POS_CODE_MAPPING.update({info.pos_code.lstrip('0') or '0': store_code for store_code, info in STORES.items()})  # Handle stripped zeros

# Active stores only (excludes legacy/system entries)
ACTIVE_STORES = {store_code: info for store_code, info in STORES.items() if info.active}


def get_store_name(store_code: str) -> str:
    """Get store name by code with fallback."""
    return STORES.get(store_code, StoreInfo("", store_code, "", "", "❓", "0", "1900-01-01", "Unknown", "UNKNOWN", False)).name


def get_store_location(store_code: str) -> str:
    """Get store location by code with fallback."""
    return STORES.get(store_code, StoreInfo("", "", store_code, "", "❓", "0", "1900-01-01", "Unknown", "UNKNOWN", False)).location


def get_store_by_pos_code(pos_code: str) -> str:
    """Get store code by POS code (handles leading zeros)."""
    # Try exact match first
    if pos_code in POS_CODE_MAPPING:
        return POS_CODE_MAPPING[pos_code]
    # Try without leading zeros
    stripped = pos_code.lstrip('0') or '0'
    return POS_CODE_MAPPING.get(stripped, "000")


def get_all_store_codes() -> list:
    """Get list of all valid store codes."""
    return list(STORES.keys())

def get_active_store_codes() -> list:
    """Get list of active store codes only."""
    return list(ACTIVE_STORES.keys())

def get_store_manager(store_code: str) -> str:
    """Get manager name for store."""
    return STORES.get(store_code, StoreInfo("", "", "", "", "❓", "0", "1900-01-01", "Unknown", "UNKNOWN", False)).manager

def get_store_business_type(store_code: str) -> str:
    """Get business type for store."""
    return STORES.get(store_code, StoreInfo("", "", "", "", "❓", "0", "1900-01-01", "Unknown", "UNKNOWN", False)).business_type

def get_store_opening_date(store_code: str) -> str:
    """Get opening date for store."""
    return STORES.get(store_code, StoreInfo("", "", "", "", "❓", "0", "1900-01-01", "Unknown", "UNKNOWN", False)).opened_date


def format_store_option(store_code: str, include_count: bool = True, include_manager: bool = False) -> str:
    """Format store for HTML select options with flexible display."""
    info = STORES.get(store_code)
    if not info:
        return store_code

    base = f"{info.emoji} {info.name}"
    
    if include_count:
        base += f" ({info.approximate_items} items)"
    
    if include_manager:
        base += f" - {info.manager}"
    
    return base


# Store validation
def validate_store_code(store_code: str) -> bool:
    """Validate if store code exists."""
    return store_code in STORES or store_code == "all"

def is_store_active(store_code: str) -> bool:
    """Check if store is currently active."""
    return STORES.get(store_code, StoreInfo("", "", "", "", "❓", "0", "1900-01-01", "Unknown", "UNKNOWN", False)).active


# Store statistics and metadata (updated with comprehensive info)
STORE_STATS_UPDATED = "2025-09-02"
STORE_NOTES = {
    "3607": "Original location (2008) - Specialty DIY items and high-end equipment",
    "6800": "Primary construction location (2022) - Largest inventory",
    "8101": "Broadway Tent & Event location (2022) - 100% event equipment",
    "728": "Newest DIY location (2024) - Satellite location",
    "000": "Legacy/system data requiring cleanup and reassignment",
}

def get_store_notes(store_code: str) -> str:
    """Get additional notes about a store."""
    return STORE_NOTES.get(store_code, "")

# Timeline helpers for analytics
def get_stores_open_on_date(date_str: str) -> list:
    """Get list of stores that were open on a specific date."""
    open_stores = []
    for store_code, info in STORES.items():
        if info.active and info.opened_date <= date_str:
            open_stores.append(store_code)
    return open_stores

def get_store_age_months(store_code: str, as_of_date: str = None) -> int:
    """Get age of store in months from opening date."""
    from datetime import datetime
    
    info = STORES.get(store_code)
    if not info:
        return 0
    
    if as_of_date is None:
        as_of_date = datetime.now().strftime("%Y-%m-%d")
    
    opened = datetime.strptime(info.opened_date, "%Y-%m-%d")
    as_of = datetime.strptime(as_of_date, "%Y-%m-%d")
    
    return (as_of.year - opened.year) * 12 + (as_of.month - opened.month)

# Backward compatibility aliases (to avoid breaking existing code)
get_store_name_by_id = get_store_name  # Legacy function name
get_all_store_ids = get_all_store_codes  # Legacy function name
validate_store_id = validate_store_code  # Legacy function name
