# app/routes/tab1.py
# tab1.py version: 2025-07-10-v24
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, render_template
from .. import db
from ..models.db_models import (
    ItemMaster,
    Transaction,
    RentalClassMapping,
    UserRentalClassMapping,
)
from ..services.api_client import APIClient
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
logger.info("Deployed tab1.py version: 2025-07-10-v24")

from ..services.mappings_cache import get_cached_mappings


def get_category_data(
    session, filter_query="", sort="", status_filter="", bin_filter=""
):
    """Return aggregated category counts using a single grouped query."""
    logger.debug(
        f"get_category_data: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}"
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
    logger.debug("Tab 1 route accessed")
    current_app.logger.debug("Tab 1 route accessed")
    session = None
    try:
        session = db.session()
        filter_query = request.args.get("filter", "").lower()
        sort = request.args.get("sort", "")
        status_filter = request.args.get("statusFilter", "").lower()
        bin_filter = request.args.get("binFilter", "").lower()

        # Global filters for store-aware functionality
        store_filter = request.args.get("store", "all")
        type_filter = request.args.get("type", "all")
        logger.debug(
            f"Tab 1 parameters: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}"
        )

        category_data = get_category_data(
            session, filter_query, sort, status_filter, bin_filter
        )
        logger.info(f"Fetched {len(category_data)} categories for tab1")

        return render_template(
            "common.html", categories=category_data, tab_num=1, cache_bust=int(time())
        )
    except Exception as e:
        logger.error(f"Error rendering Tab 1: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 1: {str(e)}", exc_info=True)
        return render_template(
            "common.html", categories=[], tab_num=1, cache_bust=int(time())
        )
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/filter", methods=["POST"])
def tab1_filter():
    logger.debug("Tab 1 filter route accessed")
    session = None
    try:
        session = db.session()
        filter_query = request.form.get("category-filter", "").lower()
        sort = request.form.get("category-sort", "")
        status_filter = request.form.get("statusFilter", "").lower()
        bin_filter = request.form.get("binFilter", "").lower()
        logger.debug(
            f"Filter parameters: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}"
        )

        category_data = get_category_data(
            session, filter_query, sort, status_filter, bin_filter
        )

        return render_template("_category_rows.html", categories=category_data)
    except Exception as e:
        logger.error(f"Error filtering Tab 1: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to filter categories"}), 500
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/subcat_data")
def tab1_subcat_data():
    category = unquote(request.args.get("category"))
    page = int(request.args.get("page", 1))
    per_page = 10
    filter_query = request.args.get("filter", "").lower()
    sort = request.args.get("sort", "")
    status_filter = request.args.get("statusFilter", "").lower()
    bin_filter = request.args.get("binFilter", "").lower()
    logger.debug(
        f"subcat_data: category={category}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}"
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

    session = None
    try:
        session = db.session()

        base_mappings = (
            session.query(RentalClassMapping)
            .filter(
                func.lower(RentalClassMapping.category) == category.lower(),
                func.lower(RentalClassMapping.subcategory) == subcategory.lower(),
            )
            .all()
        )
        user_mappings = (
            session.query(UserRentalClassMapping)
            .filter(
                func.lower(UserRentalClassMapping.category) == category.lower(),
                func.lower(UserRentalClassMapping.subcategory) == subcategory.lower(),
            )
            .all()
        )
        logger.debug(
            f"Found {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}, subcategory {subcategory}"
        )

        mappings_dict = {
            str(m.rental_class_id): {
                "category": m.category,
                "subcategory": m.subcategory,
            }
            for m in base_mappings
        }
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {
                "category": um.category,
                "subcategory": um.subcategory,
            }

        rental_class_ids = list(mappings_dict.keys())
        logger.debug(f"rental_class_ids: {rental_class_ids}")

        common_names_query = session.query(
            ItemMaster.common_name, func.count(ItemMaster.tag_id).label("total_items")
        ).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                rental_class_ids
            )
        )
        if filter_query:
            common_names_query = common_names_query.filter(
                func.lower(ItemMaster.common_name).like(f"%{filter_query}%")
            )
        if status_filter:
            common_names_query = common_names_query.filter(
                func.lower(ItemMaster.status) == status_filter.lower()
            )
        if bin_filter:
            common_names_query = common_names_query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, "")))
                == bin_filter.lower()
            )
        common_names_query = common_names_query.group_by(ItemMaster.common_name)

        if sort == "name_asc":
            common_names_query = common_names_query.order_by(
                asc(func.lower(ItemMaster.common_name))
            )
        elif sort == "name_desc":
            common_names_query = common_names_query.order_by(
                desc(func.lower(ItemMaster.common_name))
            )
        elif sort == "total_items_asc":
            common_names_query = common_names_query.order_by(asc("total_items"))
        elif sort == "total_items_desc":
            common_names_query = common_names_query.order_by(desc("total_items"))

        common_names_all = common_names_query.all()
        logger.debug(f"Total common names fetched: {len(common_names_all)}")

        common_names = []
        for name, total in common_names_all:
            if not name:
                continue

            items_on_contracts_query = session.query(
                func.count(ItemMaster.tag_id)
            ).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                    rental_class_ids
                ),
                ItemMaster.common_name == name,
                ItemMaster.status.in_(["On Rent", "Delivered"]),
            )
            if filter_query:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.common_name).like(f"%{filter_query}%")
                )
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
                ItemMaster.common_name == name,
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
            if filter_query:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(ItemMaster.common_name).like(f"%{filter_query}%")
                )
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
                ItemMaster.common_name == name,
                ItemMaster.status == "Ready to Rent",
            )
            if filter_query:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.common_name).like(f"%{filter_query}%")
                )
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

            common_names.append(
                {
                    "name": name,
                    "total_items": total,
                    "items_on_contracts": items_on_contracts,
                    "items_in_service": items_in_service,
                    "items_available": items_available,
                }
            )

        total_common_names = len(common_names)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_common_names = common_names[start:end]
        logger.debug(
            f"Returning {len(paginated_common_names)} paginated common names out of {total_common_names}"
        )

        return jsonify(
            {
                "common_names": paginated_common_names,
                "total_common_names": total_common_names,
                "page": page,
                "per_page": per_page,
            }
        )
    except Exception as e:
        logger.error(
            f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to fetch common names"}), 500
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/data")
def tab1_data():
    category = unquote(request.args.get("category"))
    subcategory = unquote(request.args.get("subcategory"))
    common_name = unquote(request.args.get("common_name"))
    page = int(request.args.get("page", 1))
    per_page = 10
    filter_query = request.args.get("filter", "").lower()
    sort = request.args.get("sort", "")
    status_filter = request.args.get("statusFilter", "").lower()
    bin_filter = request.args.get("binFilter", "").lower()
    logger.debug(
        f"data: category={category}, subcategory={subcategory}, common_name={common_name}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}"
    )

    if not category or not subcategory or not common_name:
        logger.error(
            "Category, subcategory, and common name are required in data request"
        )
        return (
            jsonify({"error": "Category, subcategory, and common name are required"}),
            400,
        )

    session = None
    try:
        session = db.session()

        base_mappings = (
            session.query(RentalClassMapping)
            .filter(
                func.lower(RentalClassMapping.category) == category.lower(),
                func.lower(RentalClassMapping.subcategory) == subcategory.lower(),
            )
            .all()
        )
        user_mappings = (
            session.query(UserRentalClassMapping)
            .filter(
                func.lower(UserRentalClassMapping.category) == category.lower(),
                func.lower(UserRentalClassMapping.subcategory) == subcategory.lower(),
            )
            .all()
        )
        logger.debug(
            f"Found {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}, subcategory {subcategory}"
        )

        mappings_dict = {
            str(m.rental_class_id): {
                "category": m.category,
                "subcategory": m.subcategory,
            }
            for m in base_mappings
        }
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {
                "category": um.category,
                "subcategory": um.subcategory,
            }

        rental_class_ids = list(mappings_dict.keys())
        logger.debug(f"rental_class_ids: {rental_class_ids}")

        query = session.query(ItemMaster).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                rental_class_ids
            ),
            ItemMaster.common_name == common_name,
        )
        if filter_query:
            query = query.filter(
                or_(
                    func.lower(ItemMaster.tag_id).like(f"%{filter_query}%"),
                    func.lower(ItemMaster.bin_location).like(f"%{filter_query}%"),
                    func.lower(ItemMaster.status).like(f"%{filter_query}%"),
                    func.lower(ItemMaster.last_contract_num).like(f"%{filter_query}%"),
                )
            )
        if status_filter:
            query = query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            query = query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, "")))
                == bin_filter.lower()
            )

        if sort == "tag_id_asc":
            query = query.order_by(asc(ItemMaster.tag_id))
        elif sort == "tag_id_desc":
            query = query.order_by(desc(ItemMaster.tag_id))
        elif sort == "last_scanned_date_asc":
            query = query.order_by(asc(ItemMaster.date_last_scanned))
        elif sort == "last_scanned_date_desc":
            query = query.order_by(desc(ItemMaster.date_last_scanned))

        total_items = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        logger.debug(
            f"Fetched {len(items)} items out of {total_items} for common_name {common_name}"
        )

        items_data = []
        for item in items:
            last_scanned_date = (
                item.date_last_scanned.isoformat() if item.date_last_scanned else "N/A"
            )

            # Get customer name from latest transaction for this item
            customer_name = "N/A"
            if item.last_contract_num:
                latest_transaction = (
                    db.session.query(Transaction.client_name)
                    .filter(
                        Transaction.tag_id == item.tag_id,
                        Transaction.contract_number == item.last_contract_num,
                    )
                    .order_by(desc(Transaction.scan_date))
                    .first()
                )
                customer_name = (
                    latest_transaction.client_name
                    if latest_transaction and latest_transaction.client_name
                    else "N/A"
                )

            items_data.append(
                {
                    "tag_id": item.tag_id,
                    "common_name": item.common_name,
                    "bin_location": item.bin_location,
                    "status": item.status,
                    "last_contract_num": item.last_contract_num,
                    "customer_name": customer_name,
                    "last_scanned_date": last_scanned_date,
                    "quality": item.quality,
                    "notes": item.notes,
                }
            )

        logger.debug(f"Returning items_data: {len(items_data)} items")
        return jsonify(
            {
                "items": items_data,
                "total_items": total_items,
                "page": page,
                "per_page": per_page,
            }
        )
    except Exception as e:
        logger.error(
            f"Error fetching items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to fetch items"}), 500
    finally:
        if session:
            session.close()


@tab1_bp.route("/tab/1/update_bin_location", methods=["POST"])
@limiter.limit("10 per minute")
def update_bin_location():
    logger.debug("update_bin_location route accessed")
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
            api_client = APIClient()
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
    logger.debug("update_status route accessed")
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
            api_client = APIClient()
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
    logger.debug("update_quality route accessed")
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
            api_client = APIClient()
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
    logger.debug("update_notes route accessed")
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
            api_client = APIClient()
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
        f"full_items_by_rental_class: category={category}, subcategory={subcategory}, common_name={common_name}"
    )

    if not category or not subcategory or not common_name:
        logger.error(
            "Category, subcategory, and common name are required in full_items_by_rental_class request"
        )
        return (
            jsonify({"error": "Category, subcategory, and common name are required"}),
            400,
        )

    session = None
    try:
        session = db.session()

        base_mappings = (
            session.query(RentalClassMapping)
            .filter(
                func.lower(RentalClassMapping.category) == category.lower(),
                func.lower(RentalClassMapping.subcategory) == subcategory.lower(),
            )
            .all()
        )
        user_mappings = (
            session.query(UserRentalClassMapping)
            .filter(
                func.lower(UserRentalClassMapping.category) == category.lower(),
                func.lower(UserRentalClassMapping.subcategory) == subcategory.lower(),
            )
            .all()
        )
        logger.debug(
            f"Found {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}, subcategory {subcategory}"
        )

        mappings_dict = {
            str(m.rental_class_id): {
                "category": m.category,
                "subcategory": m.subcategory,
            }
            for m in base_mappings
        }
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {
                "category": um.category,
                "subcategory": um.subcategory,
            }

        rental_class_ids = list(mappings_dict.keys())
        logger.debug(f"rental_class_ids: {rental_class_ids}")

        items_query = (
            session.query(ItemMaster)
            .filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(
                    rental_class_ids
                ),
                ItemMaster.common_name == common_name,
            )
            .order_by(ItemMaster.tag_id)
        )

        items = items_query.all()
        items_data = []
        for item in items:
            last_scanned_date = (
                item.date_last_scanned.isoformat() if item.date_last_scanned else "N/A"
            )
            items_data.append(
                {
                    "tag_id": item.tag_id,
                    "common_name": item.common_name,
                    "rental_class_num": item.rental_class_num,
                    "bin_location": item.bin_location,
                    "status": item.status,
                    "last_contract_num": item.last_contract_num,
                    "last_scanned_date": last_scanned_date,
                    "quality": item.quality,
                    "notes": item.notes,
                }
            )

        logger.debug(f"Returning {len(items_data)} items for common_name {common_name}")
        return jsonify({"items": items_data, "total_items": len(items_data)})
    except Exception as e:
        logger.error(
            f"Error fetching full items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to fetch full items"}), 500
    finally:
        if session:
            session.close()
