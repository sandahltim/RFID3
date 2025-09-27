# POS Category Mappings Configuration
# Version: 2025-09-27-v1
# Purpose: Category mapping and filtering for bedrock transformation service

from typing import Dict, Optional

def get_category_description(csv_category: str) -> Dict[str, str]:
    """
    Get category and subcategory from CSV category number
    Returns dict with 'category' and 'subcategory' keys

    This is a fallback for items not in user_rental_class_mappings
    """
    # Default fallback category
    return {
        'category': 'Uncategorized',
        'subcategory': 'General'
    }

def is_filtered_category(csv_category: str) -> bool:
    """
    Check if a category should be filtered out
    Returns True if category should be excluded
    """
    if not csv_category:
        return False

    # Add any categories that should be filtered here
    filtered_categories = []

    return csv_category in filtered_categories