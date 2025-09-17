# app/routes/categories.py
# categories.py version: 2025-07-05-v29
import json
from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import (
    RentalClassMapping,
    UserRentalClassMapping,
    SeedRentalClass,
    HandCountedCatalog,
)
from ..services.unified_api_client import UnifiedAPIClient
from ..services.logger import get_logger
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, ProgrammingError
from datetime import datetime
from time import time

logger = get_logger(__name__)

categories_bp = Blueprint("categories", __name__)

logger.info(f"Deployed categories.py version: 2025-06-26-v28")


def normalize_rental_class_id(rental_class_id):
    """Normalize rental_class_id for consistent lookup."""
    if not rental_class_id:
        return "N/A"
    return str(rental_class_id).strip().upper()


@categories_bp.route("/categories", methods=["GET", "POST"])
def manage_categories():
    session = None
    try:
        session = db.session()
        logger.info("Starting new session for categories")
        current_app.logger.info("Starting new session for categories")

        # Fetch mappings
        cache_key = "rental_class_mappings"
        mappings_dict_json = cache.get(cache_key)
        if mappings_dict_json is None:
            logger.debug("Cache miss for rental_class_mappings")
            base_mappings = session.query(RentalClassMapping).all()
            user_mappings = session.query(UserRentalClassMapping).all()
            mappings_dict = {
                normalize_rental_class_id(m.rental_class_id): {
                    "category": m.category,
                    "subcategory": m.subcategory,
                    "short_common_name": m.short_common_name or "N/A",
                }
                for m in base_mappings
            }
            for um in user_mappings:
                normalized_id = normalize_rental_class_id(um.rental_class_id)
                mappings_dict[normalized_id] = {
                    "category": um.category,
                    "subcategory": um.subcategory,
                    "short_common_name": um.short_common_name or "N/A",
                }
            try:
                cache.set(cache_key, json.dumps(mappings_dict), ex=3600)
                logger.info("Cached rental_class_mappings as JSON")
            except Exception as e:
                logger.error(
                    f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
                current_app.logger.error(
                    f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
        else:
            mappings_dict = json.loads(mappings_dict_json)
            logger.debug("Retrieved rental_class_mappings from cache")

        # Fetch seed data
        cache_key_seed = "seed_rental_classes"
        seed_data_json = cache.get(cache_key_seed)
        if seed_data_json is None:
            logger.debug("Cache miss for seed_rental_classes")
            seed_data = session.query(SeedRentalClass).all()
            if not seed_data:
                logger.info("No seed data in database, fetching from API")
                api_client = UnifiedAPIClient()
                seed_data_api = api_client.get_seed_data()
                for item in seed_data_api:
                    rental_class_id = item.get("rental_class_id")
                    if not rental_class_id:
                        logger.warning(
                            f"Skipping seed item with missing rental_class_id: {item}"
                        )
                        continue
                    db_seed = SeedRentalClass(
                        rental_class_id=rental_class_id,
                        common_name=item.get("common_name", "Unknown"),
                        bin_location=item.get("bin_location"),
                    )
                    session.merge(db_seed)
                session.commit()
                seed_data = session.query(SeedRentalClass).all()
            seed_data_copy = [
                {
                    "rental_class_id": item.rental_class_id,
                    "common_name": item.common_name,
                    "bin_location": item.bin_location,
                }
                for item in seed_data
            ]
            try:
                cache.set(cache_key_seed, json.dumps(seed_data_copy), ex=3600)
                logger.info("Cached seed_rental_classes as JSON")
            except Exception as e:
                logger.error(
                    f"Error caching seed_data: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
                current_app.logger.error(
                    f"Error caching seed_data: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
            common_name_dict = {
                item.rental_class_id: item.common_name for item in seed_data
            }
            logger.info(f"Built common_name_dict with {len(common_name_dict)} entries")
        else:
            seed_data_copy = json.loads(seed_data_json)
            common_name_dict = {
                item["rental_class_id"]: item["common_name"] for item in seed_data_copy
            }
            logger.info(
                f"Retrieved seed_rental_classes from cache with {len(common_name_dict)} entries"
            )

        if request.method == "POST":
            data = request.get_json()
            action = data.get("action")
            rental_class_id = normalize_rental_class_id(data.get("rental_class_id"))
            category = data.get("category")
            subcategory = data.get("subcategory")
            short_common_name = data.get("short_common_name", "")

            if action == "add":
                if not rental_class_id or not category or not subcategory:
                    logger.warning(f"Invalid input for add: {data}")
                    return (
                        jsonify(
                            {
                                "error": "Rental class ID, category, and subcategory are required"
                            }
                        ),
                        400,
                    )
                existing = (
                    session.query(UserRentalClassMapping)
                    .filter_by(rental_class_id=rental_class_id)
                    .first()
                )
                if existing:
                    logger.warning(
                        f"Mapping already exists for rental_class_id: {rental_class_id}"
                    )
                    return (
                        jsonify(
                            {"error": "Mapping already exists for this rental class ID"}
                        ),
                        400,
                    )
                new_mapping = UserRentalClassMapping(
                    rental_class_id=rental_class_id,
                    category=category,
                    subcategory=subcategory,
                    short_common_name=short_common_name,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                session.add(new_mapping)
                session.commit()
                cache.delete(cache_key)
                logger.info(f"Added new user mapping: {rental_class_id}")
                return jsonify({"message": "Mapping added successfully"}), 200

            elif action == "update":
                if not rental_class_id or not category or not subcategory:
                    logger.warning(f"Invalid input for update: {data}")
                    return (
                        jsonify(
                            {
                                "error": "Rental class ID, category, and subcategory are required"
                            }
                        ),
                        400,
                    )
                mapping = (
                    session.query(UserRentalClassMapping)
                    .filter_by(rental_class_id=rental_class_id)
                    .first()
                )
                if not mapping:
                    logger.warning(
                        f"No user mapping found for rental_class_id: {rental_class_id}"
                    )
                    return (
                        jsonify(
                            {"error": "No user mapping found for this rental class ID"}
                        ),
                        404,
                    )
                mapping.category = category
                mapping.subcategory = subcategory
                mapping.short_common_name = short_common_name
                mapping.updated_at = datetime.now()
                session.commit()
                cache.delete(cache_key)
                logger.info(f"Updated user mapping: {rental_class_id}")
                return jsonify({"message": "Mapping updated successfully"}), 200

            elif action == "delete":
                if not rental_class_id:
                    logger.warning(f"Invalid input for delete: {data}")
                    return jsonify({"error": "Rental class ID is required"}), 400
                mapping = (
                    session.query(UserRentalClassMapping)
                    .filter_by(rental_class_id=rental_class_id)
                    .first()
                )
                if not mapping:
                    logger.warning(
                        f"No user mapping found for rental_class_id: {rental_class_id}"
                    )
                    return (
                        jsonify(
                            {"error": "No user mapping found for this rental class ID"}
                        ),
                        404,
                    )
                session.delete(mapping)
                session.commit()
                cache.delete(cache_key)
                logger.info(f"Deleted user mapping: {rental_class_id}")
                return jsonify({"message": "Mapping deleted successfully"}), 200

            else:
                logger.warning(f"Invalid action: {action}")
                return jsonify({"error": "Invalid action"}), 400

        # GET request
        try:
            hand_counted_entries = session.query(HandCountedCatalog).all()
        except ProgrammingError:
            session.rollback()
            logger.warning(
                "hand_counted_catalog table missing; continuing without entries"
            )
            current_app.logger.warning(
                "hand_counted_catalog table missing; continuing without entries"
            )
            hand_counted_entries = []
        hand_counted_names = {entry.item_name for entry in hand_counted_entries}
        hand_counted_custom_names = {
            entry.item_name: entry.hand_counted_name for entry in hand_counted_entries
        }
        mappings = []
        for rental_class_id, mapping in mappings_dict.items():
            common_name = common_name_dict.get(rental_class_id, "Unknown")
            mappings.append(
                {
                    "rental_class_id": rental_class_id,
                    "common_name": common_name,
                    "category": mapping["category"],
                    "subcategory": mapping["subcategory"],
                    "short_common_name": mapping["short_common_name"],
                    "is_hand_counted": common_name in hand_counted_names,
                    "hand_counted_name": hand_counted_custom_names.get(common_name, ""),
                }
            )

        existing_names = {m["common_name"] for m in mappings}
        for entry in hand_counted_entries:
            if entry.item_name not in existing_names:
                mappings.append(
                    {
                        "rental_class_id": entry.rental_class_id or "",
                        "common_name": entry.item_name,
                        "category": "",
                        "subcategory": "",
                        "short_common_name": "",
                        "is_hand_counted": True,
                        "hand_counted_name": entry.hand_counted_name or "",
                    }
                )
        logger.info(f"Fetched {len(mappings)} category mappings")
        current_app.logger.info(f"Fetched {len(mappings)} category mappings")
        return render_template(
            "categories.html", mappings=mappings, cache_bust=int(time())
        )

    except Exception as e:
        logger.error(f"Error in manage_categories: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error in manage_categories: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return render_template("categories.html", mappings=[], error=str(e))
    finally:
        if session:
            session.close()


@categories_bp.route("/categories/mappings", methods=["GET"])
def get_mappings():
    session = None
    try:
        session = db.session()
        logger.info(f"Fetching rental class mappings for API at {time()}")
        current_app.logger.info(f"Fetching rental class mappings for API at {time()}")

        cache_key = "rental_class_mappings"
        mappings_dict_json = cache.get(cache_key)
        if mappings_dict_json is None:
            logger.debug("Cache miss for rental_class_mappings")
            base_mappings = session.query(RentalClassMapping).all()
            logger.info(
                f"Fetched {len(base_mappings)} base mappings from RentalClassMapping"
            )
            user_mappings = session.query(UserRentalClassMapping).all()
            logger.info(
                f"Fetched {len(user_mappings)} user mappings from UserRentalClassMapping"
            )
            mappings_dict = {
                normalize_rental_class_id(m.rental_class_id): {
                    "category": m.category,
                    "subcategory": m.subcategory,
                    "short_common_name": m.short_common_name or "N/A",
                }
                for m in base_mappings
            }
            for um in user_mappings:
                normalized_id = normalize_rental_class_id(um.rental_class_id)
                mappings_dict[normalized_id] = {
                    "category": um.category,
                    "subcategory": um.subcategory,
                    "short_common_name": um.short_common_name or "N/A",
                }
            try:
                cache.set(cache_key, json.dumps(mappings_dict), ex=3600)
                logger.info("Cached rental_class_mappings as JSON")
            except Exception as e:
                logger.error(
                    f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
                current_app.logger.error(
                    f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
        else:
            mappings_dict = json.loads(mappings_dict_json)
            logger.debug("Retrieved rental_class_mappings from cache")

        cache_key_seed = "seed_rental_classes"
        seed_data_json = cache.get(cache_key_seed)
        if seed_data_json is None:
            logger.info(
                "Seed data not found in cache or cache failed, fetching from database"
            )
            seed_data = session.query(SeedRentalClass).all()
            logger.info(f"Fetched {len(seed_data)} seed data records from database")
            if not seed_data:
                logger.info("No seed data in database, fetching from API")
                api_client = UnifiedAPIClient()
                seed_data_api = api_client.get_seed_data()
                for item in seed_data_api:
                    rental_class_id = item.get("rental_class_id")
                    if not rental_class_id:
                        logger.warning(
                            f"Skipping seed item with missing rental_class_id: {item}"
                        )
                        continue
                    db_seed = SeedRentalClass(
                        rental_class_id=rental_class_id,
                        common_name=item.get("common_name", "Unknown"),
                        bin_location=item.get("bin_location"),
                    )
                    session.merge(db_seed)
                session.commit()
                seed_data = session.query(SeedRentalClass).all()
            seed_data_copy = [
                {
                    "rental_class_id": item.rental_class_id,
                    "common_name": item.common_name,
                    "bin_location": item.bin_location,
                }
                for item in seed_data
            ]
            try:
                cache.set(cache_key_seed, json.dumps(seed_data_copy), ex=3600)
                logger.info("Cached seed_rental_classes as JSON")
            except Exception as e:
                logger.error(
                    f"Error caching seed_data: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
                current_app.logger.error(
                    f"Error caching seed_data: {str(e)}. Data will be fetched on next request.",
                    exc_info=True,
                )
            common_name_dict = {
                item.rental_class_id: item.common_name for item in seed_data
            }
        else:
            seed_data_copy = json.loads(seed_data_json)
            common_name_dict = {
                item["rental_class_id"]: item["common_name"] for item in seed_data_copy
            }
            logger.info(
                f"Retrieved seed_rental_classes from cache with {len(common_name_dict)} entries"
            )

        try:
            hand_counted_entries = session.query(HandCountedCatalog).all()
        except ProgrammingError:
            session.rollback()
            logger.warning(
                "hand_counted_catalog table missing; returning no hand-counted entries"
            )
            current_app.logger.warning(
                "hand_counted_catalog table missing; returning no hand-counted entries"
            )
            hand_counted_entries = []
        hand_counted_names = {entry.item_name for entry in hand_counted_entries}
        hand_counted_custom_names = {
            entry.item_name: entry.hand_counted_name for entry in hand_counted_entries
        }
        mappings = []
        for rental_class_id, mapping in mappings_dict.items():
            common_name = common_name_dict.get(rental_class_id, "Unknown")
            mappings.append(
                {
                    "rental_class_id": rental_class_id,
                    "common_name": common_name,
                    "category": mapping["category"],
                    "subcategory": mapping["subcategory"],
                    "short_common_name": mapping["short_common_name"],
                    "is_hand_counted": common_name in hand_counted_names,
                    "hand_counted_name": hand_counted_custom_names.get(common_name, ""),
                }
            )

        existing_names = {m["common_name"] for m in mappings}
        for entry in hand_counted_entries:
            if entry.item_name not in existing_names:
                mappings.append(
                    {
                        "rental_class_id": entry.rental_class_id or "",
                        "common_name": entry.item_name,
                        "category": "",
                        "subcategory": "",
                        "short_common_name": "",
                        "is_hand_counted": True,
                        "hand_counted_name": entry.hand_counted_name or "",
                    }
                )

        logger.info(f"Returning {len(mappings)} category mappings")
        current_app.logger.info(f"Returning {len(mappings)} category mappings")
        return jsonify(mappings)
    except Exception as e:
        logger.error(f"Error fetching mappings: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching mappings: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@categories_bp.route("/categories/update", methods=["POST"])
def update_mappings():
    session = None
    try:
        session = db.session()
        logger.info(f"Starting new session for update_mappings at {time()}")
        current_app.logger.info(f"Starting new session for update_mappings at {time()}")

        new_mappings = request.get_json()
        logger.info(f"Received {len(new_mappings)} new mappings")
        current_app.logger.info(f"Received {len(new_mappings)} new mappings")

        if not isinstance(new_mappings, list):
            logger.error("Invalid data format received, expected a list")
            current_app.logger.error("Invalid data format received, expected a list")
            return jsonify({"error": "Invalid data format, expected a list"}), 400

        for mapping in new_mappings:
            rental_class_id = mapping.get("rental_class_id")
            category = mapping.get("category")
            subcategory = mapping.get("subcategory", "")
            short_common_name = mapping.get("short_common_name", "")
            common_name = mapping.get("common_name")
            is_hand_counted = mapping.get("is_hand_counted", False)
            hand_counted_name = mapping.get("hand_counted_name", "")

            if rental_class_id and category:
                existing = (
                    session.query(UserRentalClassMapping)
                    .filter_by(rental_class_id=rental_class_id)
                    .first()
                )
                if existing:
                    existing.category = category
                    existing.subcategory = subcategory
                    existing.short_common_name = short_common_name
                    existing.updated_at = datetime.now()
                    logger.debug(
                        f"Updated existing mapping: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}"
                    )
                else:
                    user_mapping = UserRentalClassMapping(
                        rental_class_id=rental_class_id,
                        category=category,
                        subcategory=subcategory or "",
                        short_common_name=short_common_name or "",
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    session.add(user_mapping)
                    logger.debug(
                        f"Added new mapping: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}"
                    )
            elif not (is_hand_counted and common_name):
                logger.warning(
                    f"Skipping invalid mapping due to missing required fields: {mapping}"
                )
                current_app.logger.warning(
                    f"Skipping invalid mapping due to missing required fields: {mapping}"
                )
                continue

            # Handle hand-counted catalog updates
            if common_name:
                try:
                    existing_catalog = (
                        session.query(HandCountedCatalog)
                        .filter_by(item_name=common_name)
                        .first()
                    )
                    if is_hand_counted:
                        if not existing_catalog:
                            catalog_entry = HandCountedCatalog(
                                rental_class_id=rental_class_id,
                                item_name=common_name,
                                hand_counted_name=hand_counted_name,
                            )
                            session.add(catalog_entry)
                            logger.debug(
                                f"Added to hand-counted catalog: {common_name} with hand_counted_name: {hand_counted_name}"
                            )
                        else:
                            # Update existing catalog entry
                            if (
                                rental_class_id
                                and existing_catalog.rental_class_id != rental_class_id
                            ):
                                existing_catalog.rental_class_id = rental_class_id
                            existing_catalog.hand_counted_name = hand_counted_name
                            logger.debug(
                                f"Updated hand-counted catalog: {common_name} with hand_counted_name: {hand_counted_name}"
                            )
                    else:
                        if existing_catalog:
                            session.delete(existing_catalog)
                            logger.debug(
                                f"Removed from hand-counted catalog: {common_name}"
                            )
                except ProgrammingError:
                    session.rollback()
                    logger.warning(
                        "hand_counted_catalog table missing; skipping catalog updates"
                    )
                    current_app.logger.warning(
                        "hand_counted_catalog table missing; skipping catalog updates"
                    )

        session.commit()
        logger.info("Successfully committed rental class mappings")
        current_app.logger.info("Successfully committed rental class mappings")
        cache.delete("rental_class_mappings")
        return jsonify({"message": "Mappings updated successfully"})
    except IntegrityError as e:
        logger.error(
            f"Database integrity error during update_mappings: {str(e)}", exc_info=True
        )
        current_app.logger.error(
            f"Database integrity error during update_mappings: {str(e)}", exc_info=True
        )
        if session:
            session.rollback()
        return jsonify({"error": f"Database integrity error: {str(e)}"}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error during update_mappings: {str(e)}", exc_info=True)
        current_app.logger.error(
            f"Database error during update_mappings: {str(e)}", exc_info=True
        )
        if session:
            session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(
            f"Unexpected error during update_mappings: {str(e)}", exc_info=True
        )
        current_app.logger.error(
            f"Unexpected error during update_mappings: {str(e)}", exc_info=True
        )
        if session:
            session.rollback()
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    finally:
        if session:
            session.close()
            logger.info("Database session closed for update_mappings")
            current_app.logger.info("Database session closed for update_mappings")


@categories_bp.route("/categories/delete", methods=["POST"])
def delete_mapping():
    session = None
    try:
        session = db.session()
        data = request.get_json()
        rental_class_id = data.get("rental_class_id")

        if not rental_class_id:
            logger.error("Missing rental_class_id in delete request")
            current_app.logger.error("Missing rental_class_id in delete request")
            return jsonify({"error": "Rental class ID is required"}), 400

        logger.info(f"Deleting mapping for rental_class_id: {rental_class_id}")
        current_app.logger.info(
            f"Deleting mapping for rental_class_id: {rental_class_id}"
        )
        deleted_count = (
            session.query(UserRentalClassMapping)
            .filter_by(rental_class_id=rental_class_id)
            .delete()
        )
        session.commit()
        logger.info(
            f"Deleted {deleted_count} user mappings for rental_class_id: {rental_class_id}"
        )
        current_app.logger.info(
            f"Deleted {deleted_count} user mappings for rental_class_id: {rental_class_id}"
        )
        cache.delete("rental_class_mappings")
        return jsonify({"message": "Mapping deleted successfully"})
    except SQLAlchemyError as e:
        logger.error(f"Database error during delete_mapping: {str(e)}", exc_info=True)
        current_app.logger.error(
            f"Database error during delete_mapping: {str(e)}", exc_info=True
        )
        if session:
            session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during delete_mapping: {str(e)}", exc_info=True)
        current_app.logger.error(
            f"Unexpected error during delete_mapping: {str(e)}", exc_info=True
        )
        if session:
            session.rollback()
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    finally:
        if session:
            session.close()
            logger.info("Database session closed for delete_mapping")


@categories_bp.route("/categories/export", methods=["GET"])
def export_categories():
    """Export user mappings and hand-counted catalog as JSON with optional selective export"""
    session = None
    try:
        session = db.session()

        # Get what to include from query parameters (default: all)
        include_params = request.args.getlist("include")
        if not include_params:
            include_params = ["user_mappings", "hand_counted", "rental_mappings"]

        # Build description based on what's included
        description_parts = []
        if "user_mappings" in include_params:
            description_parts.append("User Mappings")
        if "hand_counted" in include_params:
            description_parts.append("Hand-Counted Catalog")
        if "rental_mappings" in include_params:
            description_parts.append("Base Rental Mappings")

        if len(description_parts) == 3:
            description = "RFID3 Complete Configuration Backup"
        else:
            description = f"RFID3 Backup - {', '.join(description_parts)}"

        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "version": "2.0",
                "description": description,
                "included_data": include_params,
            },
            "counts": {},
        }

        # Export user rental class mappings
        if "user_mappings" in include_params:
            user_mappings = session.query(UserRentalClassMapping).all()
            user_mappings_data = []
            for mapping in user_mappings:
                user_mappings_data.append(
                    {
                        "rental_class_id": mapping.rental_class_id,
                        "category": mapping.category,
                        "subcategory": mapping.subcategory,
                        "short_common_name": mapping.short_common_name,
                        "created_at": (
                            mapping.created_at.isoformat()
                            if mapping.created_at
                            else None
                        ),
                        "updated_at": (
                            mapping.updated_at.isoformat()
                            if mapping.updated_at
                            else None
                        ),
                    }
                )
            export_data["user_rental_class_mappings"] = user_mappings_data
            export_data["counts"]["user_mappings"] = len(user_mappings_data)
        else:
            export_data["user_rental_class_mappings"] = []
            export_data["counts"]["user_mappings"] = 0

        # Export hand-counted catalog
        if "hand_counted" in include_params:
            hand_counted_items = session.query(HandCountedCatalog).all()
            hand_counted_data = []
            for item in hand_counted_items:
                hand_counted_data.append(
                    {
                        "rental_class_id": item.rental_class_id,
                        "item_name": item.item_name,
                        "hand_counted_name": item.hand_counted_name,
                    }
                )
            export_data["hand_counted_catalog"] = hand_counted_data
            export_data["counts"]["hand_counted_items"] = len(hand_counted_data)
        else:
            export_data["hand_counted_catalog"] = []
            export_data["counts"]["hand_counted_items"] = 0

        # Export base rental class mappings
        if "rental_mappings" in include_params:
            rental_mappings = session.query(RentalClassMapping).all()
            rental_mappings_data = []
            for mapping in rental_mappings:
                rental_mappings_data.append(
                    {
                        "rental_class_id": mapping.rental_class_id,
                        "category": mapping.category,
                        "subcategory": mapping.subcategory,
                        "short_common_name": mapping.short_common_name,
                    }
                )
            export_data["rental_class_mappings"] = rental_mappings_data
            export_data["counts"]["rental_mappings"] = len(rental_mappings_data)
        else:
            export_data["rental_class_mappings"] = []
            export_data["counts"]["rental_mappings"] = 0

        total_items = sum(export_data["counts"].values())
        logger.info(f"Exported {total_items} total items: {export_data['counts']}")

        return jsonify(export_data)

    except Exception as e:
        logger.error(f"Error exporting categories: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@categories_bp.route("/categories/import", methods=["POST"])
def import_categories():
    """Import user mappings and hand-counted catalog from JSON"""
    session = None
    try:
        session = db.session()

        # Get the import data
        import_data = request.get_json()
        if not import_data:
            return jsonify({"error": "No data provided"}), 400

        # Validate import data structure
        required_keys = [
            "export_info",
            "user_rental_class_mappings",
            "hand_counted_catalog",
        ]
        for key in required_keys:
            if key not in import_data:
                return jsonify({"error": f"Missing required key: {key}"}), 400

        import_mode = request.args.get("mode", "merge")  # 'merge' or 'replace'

        results = {
            "user_mappings": {"added": 0, "updated": 0, "skipped": 0},
            "hand_counted": {"added": 0, "updated": 0, "skipped": 0},
            "rental_mappings": {"added": 0, "updated": 0, "skipped": 0},
        }

        # Import user rental class mappings
        for mapping_data in import_data["user_rental_class_mappings"]:
            rental_class_id = mapping_data["rental_class_id"]

            # Check if mapping already exists
            existing = (
                session.query(UserRentalClassMapping)
                .filter(UserRentalClassMapping.rental_class_id == rental_class_id)
                .first()
            )

            if existing:
                # Update existing mapping (same behavior for both merge and replace)
                existing.category = mapping_data["category"]
                existing.subcategory = mapping_data["subcategory"]
                existing.short_common_name = mapping_data.get("short_common_name")
                existing.updated_at = datetime.now()
                results["user_mappings"]["updated"] += 1
            else:
                # Create new mapping
                new_mapping = UserRentalClassMapping(
                    rental_class_id=rental_class_id,
                    category=mapping_data["category"],
                    subcategory=mapping_data["subcategory"],
                    short_common_name=mapping_data.get("short_common_name"),
                )
                session.add(new_mapping)
                results["user_mappings"]["added"] += 1

        # Import hand-counted catalog
        for item_data in import_data["hand_counted_catalog"]:
            item_name = item_data["item_name"]

            # Check if item already exists
            existing = (
                session.query(HandCountedCatalog)
                .filter(HandCountedCatalog.item_name == item_name)
                .first()
            )

            if existing:
                # Update existing item (same behavior for both merge and replace)
                existing.rental_class_id = item_data.get("rental_class_id")
                existing.hand_counted_name = item_data.get("hand_counted_name")
                results["hand_counted"]["updated"] += 1
            else:
                # Create new item
                new_item = HandCountedCatalog(
                    rental_class_id=item_data.get("rental_class_id"),
                    item_name=item_name,
                    hand_counted_name=item_data.get("hand_counted_name"),
                )
                session.add(new_item)
                results["hand_counted"]["added"] += 1

        # Import rental class mappings (if provided)
        # Note: Base rental mappings are typically system-managed, so we're cautious here
        if (
            "rental_class_mappings" in import_data
            and import_data["rental_class_mappings"]
        ):
            logger.info(
                f"Importing {len(import_data['rental_class_mappings'])} rental class mappings"
            )
            for mapping_data in import_data["rental_class_mappings"]:
                rental_class_id = mapping_data["rental_class_id"]

                # Check if mapping already exists
                existing = (
                    session.query(RentalClassMapping)
                    .filter(RentalClassMapping.rental_class_id == rental_class_id)
                    .first()
                )

                if existing:
                    # Update existing mapping
                    existing.category = mapping_data["category"]
                    existing.subcategory = mapping_data["subcategory"]
                    existing.short_common_name = mapping_data.get("short_common_name")
                    results["rental_mappings"]["updated"] += 1
                else:
                    # Create new mapping
                    new_mapping = RentalClassMapping(
                        rental_class_id=rental_class_id,
                        category=mapping_data["category"],
                        subcategory=mapping_data["subcategory"],
                        short_common_name=mapping_data.get("short_common_name"),
                    )
                    session.add(new_mapping)
                    results["rental_mappings"]["added"] += 1

        # Commit all changes
        session.commit()

        # Clear cache to force reload
        cache.delete("rental_class_mappings")
        cache.delete("seed_rental_classes")

        logger.info(f"Import completed: {results}")

        return jsonify(
            {
                "success": True,
                "message": "Categories imported successfully",
                "mode": import_mode,
                "results": results,
            }
        )

    except IntegrityError as e:
        if session:
            session.rollback()
        logger.error(f"Database integrity error during import: {str(e)}", exc_info=True)
        return (
            jsonify(
                {"error": "Database constraint violation - check for duplicate entries"}
            ),
            400,
        )
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error importing categories: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()
            current_app.logger.info("Database session closed for delete_mapping")
