from sqlalchemy import and_, or_

from ..models.db_models import ItemMaster


def build_global_filters(store_filter="all", type_filter="all"):
    """Build SQLAlchemy filter conditions for store and inventory type."""
    filters = []
    if store_filter and store_filter != "all":
        filters.append(
            or_(
                ItemMaster.home_store == store_filter,
                ItemMaster.current_store == store_filter,
            )
        )
    if type_filter and type_filter != "all":
        if type_filter == "RFID":
            filters.append(
                and_(
                    ItemMaster.identifier_type.is_(None),
                    ItemMaster.tag_id.op("REGEXP")("^[0-9A-Fa-f]{16,}$"),
                )
            )
        elif type_filter == "Serialized":
            filters.append(ItemMaster.identifier_type.in_(["QR", "Sticker"]))
        else:
            filters.append(ItemMaster.identifier_type == type_filter)
    return filters


def apply_global_filters(query, store_filter="all", type_filter="all"):
    """Apply store/type filters to an SQLAlchemy query."""
    for condition in build_global_filters(store_filter, type_filter):
        query = query.filter(condition)
    return query
