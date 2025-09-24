# app/routes/tab1.py
# tab1.py version: 2025-09-24-v26-bedrock-fixed
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, render_template
from .. import db
from ..models.db_models import (
    ItemMaster,
    Transaction,
    RentalClassMapping,
    UserRentalClassMapping,
)
from ..services.unified_api_client import UnifiedAPIClient
from ..services.unified_dashboard_service import UnifiedDashboardService
from ..services.logger import get_logger
from sqlalchemy import func, desc, or_, asc, case, select
from time import time
from urllib.parse import unquote
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = get_logger(__name__)

tab1_bp = Blueprint("tab1", __name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Valid values for quality
VALID_QUALITIES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", ""]

# Version marker
logger.info("Deployed tab1.py version: 2025-09-24-v26-bedrock-fixed")

from ..services.mappings_cache import get_cached_mappings
from ..utils.filters import build_global_filters


def get_category_data(
    session,
    filter_query="",
    sort="",
    status_filter="",
    bin_filter="",
    store_filter="all",
    type_filter="all",
):
    """Return aggregated category counts using a single grouped query."""
    logger.debug(
        "get_category_data: filter_query=%s, sort=%s, status_filter=%s, bin_filter=%s, store_filter=%s, type_filter=%s",
        filter_query,
        sort,
        status_filter,
        bin_filter,
        store_filter,
        type_filter,
    )

    mappings_dict = get_cached_mappings(session)
    if not mappings_dict:
        logger.warning("No rental class mappings found")
        return []

    rc_ids = list(mappings_dict.keys())

    latest_txn_subq = (
        session.query(
            Transaction.tag_id.label("tag_id"),
            func.max(Transaction.scan_date).label("max_date"),
        )
        .group_by(Transaction.tag_id)
        .subquery()
    )

    service_required_subq = (
        session.query(Transaction.tag_id)
        .join(
            latest_txn_subq,
            (Transaction.tag_id == latest_txn_subq.c.tag_id)
            & (Transaction.scan_date == latest_txn_subq.c.max_date),
        )
        .filter(Transaction.service_required == True)
        .subquery()
    )

    base_query = session.query(
        func.trim(func.cast(ItemMaster.rental_class_num, db.String)).label("rc_id"),
        func.count(ItemMaster.tag_id).label("total_items"),
        func.sum(
            case((ItemMaster.status.in_(["On Rent", "Delivered"]), 1), else_=0)
        ).label("items_on_contracts"),
        func.sum(
            case(
                (
                    or_(
                        ItemMaster.status.notin_(
                            ["Ready to Rent", "On Rent", "Delivered"]
                        ),
                        ItemMaster.tag_id.in_(select(service_required_subq.c.tag_id)),
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("items_in_service"),
        func.sum(case((ItemMaster.status == "Ready to Rent", 1), else_=0)).label(
            "items_available"
        ),
    ).filter(func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rc_ids))

    for condition in build_global_filters(store_filter, type_filter):
        base_query = base_query.filter(condition)

    if status_filter:
        base_query = base_query.filter(
            func.lower(ItemMaster.status) == status_filter.lower()
        )
    if bin_filter:
        base_query = base_query.filter(
            func.lower(func.trim(func.coalesce(ItemMaster.bin_location, "")))
            == bin_filter.lower()
        )

    base_query = base_query.group_by("rc_id")
    results = base_query.all()

    category_totals = {}
    for row in results:
        rc_id = row.rc_id
        mapping = mappings_dict.get(rc_id, {})
        cat = mapping.get("category", "Unmapped")
        if filter_query and filter_query not in cat.lower():
            continue
        entry = category_totals.setdefault(
            cat,
            {
                "category": cat,
                "cat_id": cat.lower().replace(" ", "_").replace("/", "_"),
                "total_items": 0,
                "items_on_contracts": 0,
                "items_in_service": 0,
                "items_available": 0,
            },
        )
        entry["total_items"] += row.total_items or 0
        entry["items_on_contracts"] += row.items_on_contracts or 0
        entry["items_in_service"] += row.items_in_service or 0
        entry["items_available"] += row.items_available or 0

    category_data = list(category_totals.values())
    if not sort:
        sort = "category_asc"

    if sort == "category_asc":
        category_data.sort(key=lambda x: x["category"].lower())
    elif sort == "category_desc":
        category_data.sort(key=lambda x: x["category"].lower(), reverse=True)
    elif sort == "total_items_asc":
        category_data.sort(key=lambda x: x["total_items"])
    elif sort == "total_items_desc":
        category_data.sort(key=lambda x: x["total_items"], reverse=True)

    logger.debug(f"Returning {len(category_data)} categories")
    return category_data


@tab1_bp.route("/tab/1")
def tab1_view():
    logger.debug("Tab 1 route accessed - bedrock version")
    current_app.logger.debug("Tab 1 route accessed - bedrock version")

    try:
        # Get filter parameters
        filter_query = request.args.get("filter", "").lower()
        sort = request.args.get("sort", "")
        status_filter = request.args.get("statusFilter", "").lower()
        bin_filter = request.args.get("binFilter", "").lower()
        store_filter = request.args.get("store", "all")
        type_filter = request.args.get("type", "all")

        logger.debug(
            f"Tab 1 bedrock parameters: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}, store_filter={store_filter}, type_filter={type_filter}"
        )

        # Use unified dashboard service instead of direct database queries
        dashboard_service = UnifiedDashboardService()

        # Build filters dictionary
        filters = {
            'category': filter_query if filter_query else None,
            'sort': sort,
            'status': status_filter if status_filter else None,
            'bin': bin_filter if bin_filter else None,
            'store': store_filter if store_filter != "all" else None,
            'type': type_filter if type_filter != "all" else None
        }

        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        # Get category data from bedrock service
        result = dashboard_service.get_tab1_category_data(filters)

        if result.get('success'):
            category_data = result.get('data', {})
            logger.info(f"Bedrock service fetched {len(category_data)} categories for tab1")
        else:
            logger.error(f"Bedrock service error: {result.get('error')}")
            category_data = {}

        return render_template(
            "common.html", categories=category_data, tab_num=1, cache_bust=int(time())
        )

    except Exception as e:
        logger.error(f"Error rendering Tab 1 with bedrock: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 1 with bedrock: {str(e)}", exc_info=True)
        return render_template(
            "common.html", categories=[], tab_num=1, cache_bust=int(time())
        )


@tab1_bp.route("/tab/1/filter", methods=["POST"])
def tab1_filter():
    logger.debug("Tab 1 filter route accessed - bedrock version")

    try:
        # Get filter parameters from form
        filter_query = request.form.get("category-filter", "").lower()
        sort = request.form.get("category-sort", "")
        status_filter = request.form.get("statusFilter", "").lower()
        bin_filter = request.form.get("binFilter", "").lower()
        store_filter = request.form.get("store", "all")
        type_filter = request.form.get("type", "all")

        logger.debug(
            f"Bedrock filter parameters: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}, store_filter={store_filter}, type_filter={type_filter}"
        )

        # Use unified dashboard service instead of direct database queries
        dashboard_service = UnifiedDashboardService()

        # Build filters dictionary
        filters = {
            'category': filter_query if filter_query else None,
            'sort': sort,
            'status': status_filter if status_filter else None,
            'bin': bin_filter if bin_filter else None,
            'store': store_filter if store_filter != "all" else None,
            'type': type_filter if type_filter != "all" else None
        }

        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        # Get category data from bedrock service
        result = dashboard_service.get_tab1_category_data(filters)

        if result.get('success'):
            category_data = result.get('data', {})
            logger.info(f"Bedrock filter service fetched {len(category_data)} categories")
        else:
            logger.error(f"Bedrock filter service error: {result.get('error')}")
            category_data = {}

        return render_template("_category_rows.html", categories=category_data)

    except Exception as e:
        logger.error(f"Error filtering Tab 1 with bedrock: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to filter categories"}), 500


@tab1_bp.route("/tab/1/subcat_data")
def tab1_subcat_data():
    category = unquote(request.args.get("category"))
    page = int(request.args.get("page", 1))
    per_page = 10
    filter_query = request.args.get("filter", "").lower()
    sort = request.args.get("sort", "")
    status_filter = request.args.get("statusFilter", "").lower()
    bin_filter = request.args.get("binFilter", "").lower()
    store_filter = request.args.get("store", "all")
    type_filter = request.args.get("type", "all")
    logger.debug(
        f"subcat_data: category={category}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}, store_filter={store_filter}, type_filter={type_filter}"
    )

    if not category:
        logger.error("Category parameter is missing in subcat_data request")
        return jsonify({"error": "Category is required"}), 400

    logger.info(f"Fetching subcategories for category: {category}")
    session = None
    try:
        session = db.session()

        mappings_dict = get_cached_mappings(session)
        category_mappings = {
            rc_id: data
            for rc_id, data in mappings_dict.items()
            if data["category"].lower() == category.lower()
        }
        if not category_mappings:
            logger.warning(f"No mappings found for category {category}")
            return jsonify(
                {
                    "subcategories": [],
                    "total_subcats": 0,
                    "page": page,
                    "per_page": per_page,
                    "message": f"No mappings found for category '{category}'. Please add mappings in the Categories tab.",
                }
            )

        subcategories = {}
        for rental_class_id, data in category_mappings.items():
            subcategory = data["subcategory"]
            if not subcategory:
                continue
            subcategories.setdefault(subcategory, []).append(rental_class_id)

        subcat_list = sorted(subcategories.keys())
        if filter_query:
            subcat_list = [s for s in subcat_list if filter_query in s.lower()]
        if sort == "subcategory_asc":
            subcat_list.sort()
        elif sort == "subcategory_desc":
            subcat_list.sort(reverse=True)

        total_subcats = len(subcat_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_subcats = subcat_list[start:end]
        logger.debug(
            f"Total subcategories: {total_subcats}, paginated: {paginated_subcats}"
        )

        global_filters = build_global_filters(store_filter, type_filter)

        subcategory_data = []
        for subcat in paginated_subcats:
            rental_class_ids = subcategories[subcat]
            logger.debug(
                f"Processing subcategory {subcat} with rental_class_ids: {rental_class_ids}"
            )

            total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                    rental_class_ids
                )
            )
            for condition in global_filters:
                total_items_query = total_items_query.filter(condition)
            if status_filter:
                total_items_query = total_items_query.filter(
                    func.lower(ItemMaster.status) == status_filter.lower()
                )
            if bin_filter:
                total_items_query = total_items_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, "")))
                    == bin_filter.lower()
                )
            total_items = total_items_query.scalar() or 0

            items_on_contracts_query = session.query(
                func.count(ItemMaster.tag_id)
            ).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                    rental_class_ids
                ),
                ItemMaster.status.in_(["On Rent", "Delivered"]),
            )
            for condition in global_filters:
                items_on_contracts_query = items_on_contracts_query.filter(condition)
            if status_filter:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.status) == status_filter.lower()
                )
            if bin_filter:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, "")))
                    == bin_filter.lower()
                )
            items_on_contracts = items_on_contracts_query.scalar() or 0

            subquery = (
                session.query(
                    Transaction.tag_id,
                    Transaction.scan_date,
                    Transaction.service_required,
                )
                .filter(Transaction.tag_id == ItemMaster.tag_id)
                .order_by(Transaction.scan_date.desc())
                .subquery()
            )

            items_in_service_query = session.query(
                func.count(ItemMaster.tag_id)
            ).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                    rental_class_ids
                ),
                or_(
                    ItemMaster.status.notin_(["Ready to Rent", "On Rent", "Delivered"]),
                    ItemMaster.tag_id.in_(
                        session.query(subquery.c.tag_id).filter(
                            subquery.c.scan_date
                            == session.query(func.max(Transaction.scan_date))
                            .filter(Transaction.tag_id == subquery.c.tag_id)
                            .correlate(subquery)
                            .scalar_subquery(),
                            subquery.c.service_required == True,
                        )
                    ),
                ),
            )
            for condition in global_filters:
                items_in_service_query = items_in_service_query.filter(condition)
            if status_filter:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(ItemMaster.status) == status_filter.lower()
                )
            if bin_filter:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, "")))
                    == bin_filter.lower()
                )
            items_in_service = items_in_service_query.scalar() or 0

            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                    rental_class_ids
                ),
                ItemMaster.status == "Ready to Rent",
            )
            for condition in global_filters:
                items_available_query = items_available_query.filter(condition)
            if status_filter:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.status) == status_filter.lower()
                )
            if bin_filter:
                items_available_query = items_available_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, "")))
                    == bin_filter.lower()
                )
            items_available = items_available_query.scalar() or 0

            subcategory_data.append(
                {
                    "subcategory": subcat,
                    "total_items": total_items,
                    "items_on_contracts": items_on_contracts,
                    "items_in_service": items_in_service,
                    "items_available": items_available,
                }
            )

        if sort == "total_items_asc":
            subcategory_data.sort(key=lambda x: x["total_items"])
        elif sort == "total_items_desc":
            subcategory_data.sort(key=lambda x: x["total_items"], reverse=True)

        logger.debug(f"Returning subcategory_data: {subcategory_data}")
        return jsonify(
            {
                "subcategories": subcategory_data,
                "total_subcats": total_subcats,
                "page": page,
                "per_page": per_page,
            }
        )
    except Exception as e:
        logger.error(
            f"Error fetching subcategory data for category {category}: {str(e)}",
            exc_info=True,
        )
        return (
            jsonify({"error": "Failed to fetch subcategory data", "details": str(e)}),
            500,
        )
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/common_names")
def tab1_common_names():
    logger.debug("Tab 1 common_names route accessed - bedrock version")

    category = unquote(request.args.get("category"))
    subcategory = unquote(request.args.get("subcategory"))
    page = int(request.args.get("page", 1))
    per_page = 10
    filter_query = request.args.get("filter", "").lower()
    sort = request.args.get("sort", "")
    status_filter = request.args.get("statusFilter", "").lower()
    bin_filter = request.args.get("binFilter", "").lower()
    logger.debug(
        f"common_names: category={category}, subcategory={subcategory}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}"
    )

    if not category or not subcategory:
        logger.error("Category and subcategory are required in common_names request")
        return jsonify({"error": "Category and subcategory are required"}), 400

    try:
        # Use unified dashboard service instead of direct database queries
        dashboard_service = UnifiedDashboardService()

        # Build filters dictionary for bedrock service
        filters = {
            'category': category,
            'subcategory': subcategory,
            'page': page,
            'per_page': per_page,
            'filter': filter_query if filter_query else None,
            'sort': sort,
            'status': status_filter if status_filter else None,
            'bin': bin_filter if bin_filter else None
        }

        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        # Get common names data from bedrock service
        result = dashboard_service.get_tab1_common_names_data(filters)

        if result.get('success'):
            data = result.get('data', {})
            logger.info(f"Bedrock common names service returned {len(data.get('common_names', []))} items")
            return jsonify(data)
        else:
            logger.error(f"Bedrock common names service error: {result.get('error')}")
            return jsonify({"error": "Failed to fetch common names from bedrock service"}), 500

    except Exception as e:
        logger.error(
            f"Error fetching common names with bedrock for category {category}, subcategory {subcategory}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to fetch common names"}), 500


@tab1_bp.route("/tab/1/data")
def tab1_data():
    logger.debug("Tab 1 data route accessed - bedrock version")

    category = unquote(request.args.get("category"))
    subcategory = unquote(request.args.get("subcategory"))
    common_name = unquote(request.args.get("common_name"))
    page = int(request.args.get("page", 1))
    per_page = 10
    filter_query = request.args.get("filter", "").lower()
    sort = request.args.get("sort", "")
    status_filter = request.args.get("statusFilter", "").lower()
    bin_filter = request.args.get("binFilter", "").lower()
    store_filter = request.args.get("store", "all")
    type_filter = request.args.get("type", "all")

    logger.debug(
        f"Bedrock data: category={category}, subcategory={subcategory}, common_name={common_name}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}, store_filter={store_filter}, type_filter={type_filter}"
    )

    if not category or not subcategory or not common_name:
        logger.error(
            "Category, subcategory, and common name are required in data request"
        )
        return (
            jsonify({"error": "Category, subcategory, and common name are required"}),
            400,
        )

    try:
        # Use unified dashboard service instead of direct database queries
        dashboard_service = UnifiedDashboardService()

        # Build filters dictionary for bedrock service
        filters = {
            'category': category,
            'subcategory': subcategory,
            'common_name': common_name,
            'page': page,
            'per_page': per_page,
            'filter': filter_query if filter_query else None,
            'sort': sort,
            'status': status_filter if status_filter else None,
            'bin': bin_filter if bin_filter else None,
            'store': store_filter,
            'type': type_filter
        }

        # Remove None values but keep 'all' values
        filters = {k: v for k, v in filters.items() if v is not None}

        # Get equipment list from bedrock service
        result = dashboard_service.get_tab1_equipment_list(filters)

        if result.get('success'):
            equipment_list = result.get('data', [])
            total_count = result.get('total_count', 0)

            # Transform equipment data to match expected format
            items_data = []
            for equipment in equipment_list:
                items_data.append({
                    "tag_id": equipment.get('tag_id', ''),
                    "common_name": equipment.get('common_name', ''),
                    "bin_location": equipment.get('bin_location', ''),
                    "status": equipment.get('status', ''),
                    "last_contract_num": equipment.get('last_contract_num', ''),
                    "customer_name": equipment.get('customer_name', 'N/A'),
                    "last_scanned_date": equipment.get('last_scanned_date', 'N/A'),
                    "quality": equipment.get('quality', ''),
                    "notes": equipment.get('notes', ''),
                })

            logger.info(f"Bedrock data service returned {len(items_data)} items for {category}/{subcategory}/{common_name}")

            return jsonify({
                "items": items_data,
                "total_items": total_count,
                "page": page,
                "per_page": per_page,
            })

        else:
            logger.error(f"Bedrock data service error: {result.get('error')}")
            return jsonify({"error": "Failed to fetch items from bedrock service"}), 500

    except Exception as e:
        logger.error(
            f"Error fetching items with bedrock for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to fetch items"}), 500


@tab1_bp.route("/tab/1/update_bin_location", methods=["POST"])
@limiter.limit("10 per minute")
def update_bin_location():
    logger.debug("update_bin_location route accessed - bedrock version")
    session = None
    try:
        session = db.session()
        data = request.get_json()
        tag_id = data.get("tag_id")
        new_bin_location = data.get("bin_location")
        date_updated = data.get("date_updated")
        logger.debug(
            f"update_bin_location: tag_id={tag_id}, bin_location={new_bin_location}, date_updated={date_updated}"
        )

        if not tag_id:
            logger.error("tag_id is required")
            return jsonify({"error": "Tag ID is required"}), 400

        valid_bin_locations = ["resale", "sold", "pack", "burst", ""]
        if new_bin_location not in valid_bin_locations:
            logger.warning(f"Invalid bin location value: {new_bin_location}")
            return (
                jsonify(
                    {
                        "error": f'Bin location must be one of {", ".join(valid_bin_locations)}'
                    }
                ),
                400,
            )

        item = session.query(ItemMaster).filter(ItemMaster.tag_id == tag_id).first()
        if not item:
            logger.warning(f"Item not found for tag_id {tag_id}")
            return jsonify({"error": "Item not found"}), 404

        item.bin_location = new_bin_location if new_bin_location else None
        item.date_updated = (
            datetime.now()
            if not date_updated
            else datetime.fromisoformat(date_updated.replace("+00:00", "Z"))
        )
        session.commit()

        try:
            api_client = UnifiedAPIClient()
            api_client.update_bin_location(
                tag_id, new_bin_location if new_bin_location else ""
            )
            logger.info(
                f"Successfully updated API bin location for tag_id {tag_id} to {new_bin_location}"
            )
        except Exception as e:
            logger.error(
                f"Failed to update API bin location for tag_id {tag_id}: {str(e)}",
                exc_info=True,
            )
            session.rollback()
            return (
                jsonify(
                    {
                        "error": f"Failed to update API: {str(e)}",
                        "local_update": "success",
                    }
                ),
                200,
            )

        logger.info(f"Updated bin location for tag_id {tag_id} to {new_bin_location}")
        return jsonify({"message": "Bin location updated successfully"})
    except Exception as e:
        logger.error(f"Error updating bin location: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({"error": "Failed to update bin location"}), 500
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/update_status", methods=["POST"])
@limiter.limit("10 per minute")
def update_status():
    logger.debug("update_status route accessed - bedrock version")
    session = None
    try:
        session = db.session()
        data = request.get_json()
        tag_id = data.get("tag_id")
        new_status = data.get("status")
        date_updated = data.get("date_updated")
        logger.debug(
            f"update_status: tag_id={tag_id}, status={new_status}, date_updated={date_updated}"
        )

        if not tag_id or not new_status:
            logger.error("tag_id and status are required")
            return jsonify({"error": "Tag ID and status are required"}), 400

        valid_statuses = [
            "Ready to Rent",
            "Sold",
            "Repair",
            "Needs to be Inspected",
            "Wash",
            "Wet",
        ]
        if new_status not in valid_statuses:
            logger.warning(f"Invalid status value: {new_status}")
            return (
                jsonify(
                    {"error": f'Status must be one of {", ".join(valid_statuses)}'}
                ),
                400,
            )

        item = session.query(ItemMaster).filter(ItemMaster.tag_id == tag_id).first()
        if not item:
            logger.warning(f"Item not found for tag_id {tag_id}")
            return jsonify({"error": "Item not found"}), 404

        if new_status in ["On Rent", "Delivered"]:
            logger.warning(
                f"Attempted manual update to restricted status {new_status} for tag_id {tag_id}"
            )
            return (
                jsonify(
                    {
                        "error": 'Status cannot be updated to "On Rent" or "Delivered" manually'
                    }
                ),
                400,
            )

        item.status = new_status
        item.date_updated = (
            datetime.now()
            if not date_updated
            else datetime.fromisoformat(date_updated.replace("+00:00", "Z"))
        )
        session.commit()

        try:
            api_client = UnifiedAPIClient()
            api_client.update_status(tag_id, new_status)
            logger.info(
                f"Successfully updated API status for tag_id {tag_id} to {new_status}"
            )
        except Exception as e:
            logger.error(
                f"Failed to update API status for tag_id {tag_id}: {str(e)}",
                exc_info=True,
            )
            session.rollback()
            return (
                jsonify(
                    {
                        "error": f"Failed to update API: {str(e)}",
                        "local_update": "success",
                    }
                ),
                200,
            )

        logger.info(f"Updated status for tag_id {tag_id} to {new_status}")
        return jsonify({"message": "Status updated successfully"})
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({"error": "Failed to update status"}), 500
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/update_quality", methods=["POST"])
@limiter.limit("10 per minute")
def update_quality():
    logger.debug("update_quality route accessed - bedrock version")
    session = None
    try:
        session = db.session()
        data = request.get_json()
        tag_id = data.get("tag_id")
        new_quality = data.get("quality", "")
        date_updated = data.get("date_updated")
        logger.debug(
            f"update_quality: tag_id={tag_id}, quality={new_quality}, date_updated={date_updated}"
        )

        if not tag_id:
            logger.error("tag_id is required")
            return jsonify({"error": "Tag ID is required"}), 400

        if new_quality not in VALID_QUALITIES:
            logger.warning(f"Invalid quality value: {new_quality}")
            return (
                jsonify(
                    {"error": f'Quality must be one of {", ".join(VALID_QUALITIES)}'}
                ),
                400,
            )

        item = session.query(ItemMaster).filter(ItemMaster.tag_id == tag_id).first()
        if not item:
            logger.warning(f"Item not found for tag_id {tag_id}")
            return jsonify({"error": "Item not found"}), 404

        item.quality = new_quality if new_quality else None
        item.date_updated = (
            datetime.now()
            if not date_updated
            else datetime.fromisoformat(date_updated.replace("+00:00", "Z"))
        )
        session.commit()

        try:
            api_client = UnifiedAPIClient()
            api_client.update_item(
                tag_id, {"quality": new_quality if new_quality else ""}
            )
            logger.info(
                f"Successfully updated API quality for tag_id {tag_id} to {new_quality}"
            )
        except Exception as e:
            logger.error(
                f"Failed to update API quality for tag_id {tag_id}: {str(e)}",
                exc_info=True,
            )
            session.rollback()
            return (
                jsonify(
                    {
                        "error": f"Failed to update API: {str(e)}",
                        "local_update": "success",
                    }
                ),
                200,
            )

        logger.info(f"Updated quality for tag_id {tag_id} to {new_quality}")
        return jsonify({"message": "Quality updated successfully"})
    except Exception as e:
        logger.error(f"Error updating quality: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({"error": "Failed to update quality"}), 500
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/update_notes", methods=["POST"])
@limiter.limit("10 per minute")
def update_notes():
    logger.debug("update_notes route accessed - bedrock version")
    session = None
    try:
        session = db.session()
        data = request.get_json()
        tag_id = data.get("tag_id")
        new_notes = data.get("notes")
        date_updated = data.get("date_updated")
        logger.debug(
            f"update_notes: tag_id={tag_id}, notes={new_notes}, date_updated={date_updated}"
        )

        if not tag_id:
            logger.error("tag_id is required")
            return jsonify({"error": "Tag ID is required"}), 400

        item = session.query(ItemMaster).filter(ItemMaster.tag_id == tag_id).first()
        if not item:
            logger.warning(f"Item not found for tag_id {tag_id}")
            return jsonify({"error": "Item not found"}), 404

        item.notes = new_notes if new_notes else ""
        item.date_updated = (
            datetime.now()
            if not date_updated
            else datetime.fromisoformat(date_updated.replace("+00:00", "Z"))
        )
        session.commit()

        try:
            api_client = UnifiedAPIClient()
            api_client.update_notes(tag_id, new_notes if new_notes else "")
            logger.info(f"Successfully updated API notes for tag_id {tag_id}")
        except Exception as e:
            logger.error(
                f"Failed to update API notes for tag_id {tag_id}: {str(e)}",
                exc_info=True,
            )
            session.rollback()
            return (
                jsonify(
                    {
                        "error": f"Failed to update API: {str(e)}",
                        "local_update": "success",
                    }
                ),
                200,
            )

        logger.info(f"Updated notes for tag_id {tag_id}")
        return jsonify({"message": "Notes updated successfully"})
    except Exception as e:
        logger.error(f"Error updating notes: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({"error": "Failed to update notes"}), 500
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/full_items_by_rental_class")
def full_items_by_rental_class():
    category = unquote(request.args.get("category"))
    subcategory = unquote(request.args.get("subcategory"))
    common_name = unquote(request.args.get("common_name"))
    logger.debug(
        f"full_items_by_rental_class route accessed - bedrock version: category={category}, subcategory={subcategory}, common_name={common_name}"
    )

    if not category or not subcategory or not common_name:
        logger.error(
            "Category, subcategory, and common name are required in full_items_by_rental_class request"
        )
        return (
            jsonify({"error": "Category, subcategory, and common name are required"}),
            400,
        )

    try:
        # Use unified dashboard service instead of direct database queries
        dashboard_service = UnifiedDashboardService()

        # Build filters dictionary for bedrock service
        filters = {
            'category': category,
            'subcategory': subcategory,
            'common_name': common_name,
            'limit': None  # Get all items for this specific combination
        }

        # Get equipment list from bedrock service
        result = dashboard_service.get_tab1_equipment_list(filters)

        if result.get('success'):
            equipment_list = result.get('data', [])

            # Transform equipment data to match expected format and filter by exact match
            full_items = []
            for equipment in equipment_list:
                # Filter by category hierarchy and common name
                if (equipment.get('category', '').lower() == category.lower() and
                    equipment.get('subcategory', '').lower() == subcategory.lower() and
                    equipment.get('common_name') == common_name):

                    full_items.append({
                        "tag_id": equipment.get('tag_id', equipment.get('num', '')),
                        "common_name": equipment.get('common_name', ''),
                        "bin_location": equipment.get('bin_location', equipment.get('current_location', '')),
                        "status": equipment.get('status', equipment.get('current_status', '')),
                        "last_contract_num": equipment.get('last_contract_num', ''),
                        "customer_name": equipment.get('customer_name', 'N/A'),
                        "last_scanned_date": equipment.get('last_scanned_date', 'N/A'),
                        "quality": equipment.get('quality', ''),
                        "notes": equipment.get('notes', ''),
                    })

            logger.info(f"Bedrock full_items service returned {len(full_items)} items for {category}/{subcategory}/{common_name}")

            return jsonify({
                "items": full_items
            })

        else:
            logger.error(f"Bedrock full_items service error: {result.get('error')}")
            return jsonify({"error": "Failed to fetch full items from bedrock service"}), 500

    except Exception as e:
        logger.error(
            f"Error fetching full items with bedrock for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to fetch full items"}), 500
