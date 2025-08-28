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
    """Store information structure."""

    store_id: str
    name: str
    location: str
    pos_code: str
    emoji: str
    approximate_items: str


# Master store configuration - THIS IS THE SINGLE SOURCE OF TRUTH
STORES = {
    "6800": StoreInfo(
        store_id="6800",
        name="Brooklyn Park",
        location="Brooklyn Park, MN",
        pos_code="002",
        emoji="🏪",
        approximate_items="22K+",
    ),
    "3607": StoreInfo(
        store_id="3607",
        name="Wayzata",
        location="Wayzata, MN",
        pos_code="001",
        emoji="🏬",
        approximate_items="5K+",
    ),
    "8101": StoreInfo(
        store_id="8101",
        name="Fridley",
        location="Fridley, MN",
        pos_code="003",
        emoji="🏢",
        approximate_items="3K+",
    ),
    "728": StoreInfo(
        store_id="728",
        name="Elk River",
        location="Elk River, MN",
        pos_code="004",
        emoji="🏭",
        approximate_items="3K+",
    ),
    "000": StoreInfo(
        store_id="000",
        name="Legacy/Unassigned",
        location="Multiple Locations",
        pos_code="000",
        emoji="❓",
        approximate_items="20K+",
    ),
}

# Convenience mappings for backward compatibility
STORE_MAPPING = {store_id: info.name for store_id, info in STORES.items()}
STORE_LOCATIONS = {store_id: info.location for store_id, info in STORES.items()}
POS_CODE_MAPPING = {info.pos_code: store_id for store_id, info in STORES.items()}


def get_store_name(store_id: str) -> str:
    """Get store name by ID with fallback."""
    return STORES.get(store_id, StoreInfo("", store_id, "", "", "❓", "0")).name


def get_store_location(store_id: str) -> str:
    """Get store location by ID with fallback."""
    return STORES.get(store_id, StoreInfo("", "", store_id, "", "❓", "0")).location


def get_store_by_pos_code(pos_code: str) -> str:
    """Get store ID by POS code."""
    return POS_CODE_MAPPING.get(pos_code, "000")


def get_all_store_ids() -> list:
    """Get list of all valid store IDs."""
    return list(STORES.keys())


def format_store_option(store_id: str, include_count: bool = True) -> str:
    """Format store for HTML select options."""
    info = STORES.get(store_id)
    if not info:
        return store_id

    if include_count:
        return f"{info.emoji} {info.name} ({info.approximate_items} items)"
    else:
        return f"{info.emoji} {info.name}"


# Store validation
def validate_store_id(store_id: str) -> bool:
    """Validate if store ID exists."""
    return store_id in STORES or store_id == "all"


# Store statistics (should be updated periodically)
STORE_STATS_UPDATED = "2025-08-27"
STORE_NOTES = {
    "6800": "Primary location with largest inventory",
    "3607": "Specialty items and high-end equipment",
    "8101": "Regional service center",
    "728": "Satellite location",
    "000": "Legacy data requiring cleanup and reassignment",
}


def get_store_notes(store_id: str) -> str:
    """Get additional notes about a store."""
    return STORE_NOTES.get(store_id, "")
