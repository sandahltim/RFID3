import json
from time import time
from typing import Dict, Any

from .. import cache
from ..models.db_models import RentalClassMapping, UserRentalClassMapping

MAPPINGS_CACHE_TIMEOUT = 300
_mappings_cache: Dict[int, Dict[str, Any]] | None = None
_mappings_cache_time = 0.0


def _load_mappings(session):
    base_mappings = session.query(RentalClassMapping).all()
    user_mappings = session.query(UserRentalClassMapping).all()
    mappings_dict = {
        str(m.rental_class_id).strip(): {
            "category": m.category,
            "subcategory": m.subcategory,
            "short_common_name": getattr(m, "short_common_name", None),
        }
        for m in base_mappings
    }
    for um in user_mappings:
        mappings_dict[str(um.rental_class_id).strip()] = {
            "category": um.category,
            "subcategory": um.subcategory,
            "short_common_name": getattr(um, "short_common_name", None),
        }
    return mappings_dict


def get_cached_mappings(session):
    """Return rental class mappings using Redis or in-memory cache."""
    cache_key = "rental_class_mappings"
    mappings_dict = None
    if getattr(cache, "get", None):
        try:
            cached = cache.get(cache_key)
            if cached:
                try:
                    mappings_dict = json.loads(cached)
                except Exception:
                    mappings_dict = None
        except Exception:
            mappings_dict = None

    global _mappings_cache, _mappings_cache_time
    if mappings_dict is None:
        if _mappings_cache and time() - _mappings_cache_time < MAPPINGS_CACHE_TIMEOUT:
            mappings_dict = _mappings_cache
        else:
            mappings_dict = _load_mappings(session)
            _mappings_cache = mappings_dict
            _mappings_cache_time = time()
            if getattr(cache, "set", None):
                try:
                    cache.set(
                        cache_key, json.dumps(mappings_dict), ex=MAPPINGS_CACHE_TIMEOUT
                    )
                except Exception:
                    pass
    return mappings_dict
