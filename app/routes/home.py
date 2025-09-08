# app/routes/home.py
# home.py version: 2025-07-10-v7
from flask import Blueprint, render_template, request, jsonify
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RefreshState, RFIDTag
from ..models.pos_models import POSRFIDCorrelation, POSEquipment
from sqlalchemy import func, case, or_
from time import time
import logging
from datetime import datetime
import os
import json
from config import LOG_FILE
from ..services.logger import get_logger
from ..utils.exceptions import (
    DatabaseException,
    handle_api_error,
    log_and_handle_exception,
)

# Configure logging with process ID
logger = get_logger(f"home_{os.getpid()}", level=logging.INFO, log_file=LOG_FILE)

home_bp = Blueprint("home", __name__)


@home_bp.route("/", endpoint="home")
@home_bp.route("/home", endpoint="home_page")
@handle_api_error
def home():
    cache_key = "home_page_cache"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug("Serving home page from cache")
        return render_template(
            "home.html", **json.loads(cached_data), cache_bust=int(time())
        )

    try:
        logger.info("Starting new session for home")

        # Aggregate all counts in a single query for better performance
        try:
            counts = db.session.query(
                func.count(ItemMaster.tag_id).label("total"),
                func.sum(
                    case((ItemMaster.status.in_(["On Rent", "Delivered"]), 1), else_=0)
                ).label("on_rent"),
                func.sum(
                    case((ItemMaster.status == "Ready to Rent", 1), else_=0)
                ).label("available"),
                func.sum(
                    case(
                        (
                            ItemMaster.status.in_(
                                ["Needs to be Inspected", "Wet", "Repair", "Missing"]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("in_service"),
            ).one()
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch inventory counts: {str(e)}",
                error_code="INVENTORY_COUNT_FAILED",
                details={"query": "inventory_aggregation"},
            )

        # Extract aggregated values (convert to int for JSON serialization)
        total_items = int(counts.total or 0)
        items_on_rent = int(counts.on_rent or 0)
        items_available = int(counts.available or 0)
        items_in_service = int(counts.in_service or 0)

        logger.info(
            f"Aggregated counts - Total: {total_items}, On Rent: {items_on_rent}, Available: {items_available}, In Service: {items_in_service}"
        )
        logger.debug(
            f"Performance optimized: Single query replaced multiple COUNT queries"
        )

        # Status breakdown (keep separate for detailed breakdown)
        status_breakdown = (
            db.session.query(
                ItemMaster.status, func.count(ItemMaster.tag_id).label("count")
            )
            .group_by(ItemMaster.status)
            .all()
        )
        status_counts = [
            (status or "Unknown", count) for status, count in status_breakdown
        ]

        # Recent scans - increased to 50 for better real-time experience
        recent_scans = (
            db.session.query(ItemMaster)
            .filter(ItemMaster.date_last_scanned.isnot(None))
            .order_by(ItemMaster.date_last_scanned.desc())
            .limit(50)
            .all()
        )
        logger.info(f"Recent scans count: {len(recent_scans)}")
        logger.debug(
            f"Recent scans sample: {[(item.tag_id, item.common_name, item.date_last_scanned) for item in recent_scans[:5]]}"
        )

        # Last refresh state
        refresh_state = db.session.query(RefreshState).first()
        last_refresh = (
            refresh_state.last_refresh.strftime("%Y-%m-%d %H:%M:%S")
            if refresh_state and refresh_state.last_refresh
            else "N/A"
        )
        refresh_type = refresh_state.state_type if refresh_state else "N/A"
        logger.info(f"Last refresh details: {last_refresh}, Type: {refresh_type}")
        logger.debug(f"Last refresh: {last_refresh}, Type: {refresh_type}")

        # Cache the response
        render_data = {
            "total_items": total_items or 0,
            "items_on_rent": items_on_rent or 0,
            "items_in_service": items_in_service or 0,
            "items_available": items_available or 0,
            "status_counts": status_counts,
            "recent_scans": [
                {
                    "tag_id": item.tag_id,
                    "common_name": item.common_name,
                    "date_last_scanned": (
                        item.date_last_scanned.isoformat()
                        if item.date_last_scanned
                        else None
                    ),
                    "status": item.status,
                    "last_contract_num": item.last_contract_num,
                }
                for item in recent_scans
            ],
            "last_refresh": last_refresh,
            "refresh_type": refresh_type,
        }
        cache.set(cache_key, json.dumps(render_data), ex=60)  # Cache for 60 seconds

        return render_template(
            "home.html",
            total_items=total_items or 0,
            items_on_rent=items_on_rent or 0,
            items_in_service=items_in_service or 0,
            items_available=items_available or 0,
            status_counts=status_counts,
            recent_scans=recent_scans,
            last_refresh=last_refresh,
            refresh_type=refresh_type,
            cache_bust=int(time()),
        )
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
        return render_template(
            "home.html",
            total_items=0,
            items_on_rent=0,
            items_in_service=0,
            items_available=0,
            status_counts=[],
            recent_scans=[],
            last_refresh="N/A",
            refresh_type="N/A",
            cache_bust=int(time()),
        )
    finally:
        pass  # Flask-SQLAlchemy automatically manages session lifecycle


@home_bp.route("/refresh_status")
def get_refresh_status():
    """Get current refresh operation status."""
    from flask import jsonify
    from ..services.refresh import refresh_status

    return jsonify(refresh_status)


@home_bp.route("/api/recent_scans")
@handle_api_error
def get_recent_scans():
    """Get recent scans with optional timestamp filtering for real-time updates."""
    from flask import request, jsonify
    from datetime import datetime, timedelta

    try:
        # Get parameters
        limit = int(request.args.get("limit", 50))
        since_timestamp = request.args.get("since")  # ISO timestamp string

        # Build query for recent scans
        query = db.session.query(
            ItemMaster.tag_id,
            ItemMaster.common_name,
            ItemMaster.date_last_scanned,
            ItemMaster.status,
            ItemMaster.last_contract_num,
            ItemMaster.rental_class_num,
        ).filter(ItemMaster.date_last_scanned.isnot(None))

        # Apply timestamp filter if provided
        if since_timestamp:
            try:
                since_dt = datetime.fromisoformat(
                    since_timestamp.replace("Z", "+00:00")
                )
                query = query.filter(ItemMaster.date_last_scanned > since_dt)
                logger.debug(f"Filtering scans since {since_dt}")
            except ValueError:
                logger.warning(f"Invalid since_timestamp format: {since_timestamp}")

        # Order by most recent first and limit
        recent_items = (
            query.order_by(ItemMaster.date_last_scanned.desc()).limit(limit).all()
        )

        # Format response
        scans = []
        for item in recent_items:
            scans.append(
                {
                    "tag_id": item.tag_id,
                    "common_name": item.common_name or "N/A",
                    "date_last_scanned": (
                        item.date_last_scanned.isoformat()
                        if item.date_last_scanned
                        else None
                    ),
                    "status": item.status or "N/A",
                    "last_contract_num": item.last_contract_num or "N/A",
                    "rental_class_num": item.rental_class_num or "N/A",
                }
            )

        # Get latest timestamp for next poll
        latest_timestamp = None
        if scans:
            latest_timestamp = scans[0]["date_last_scanned"]

        logger.debug(
            f"Returning {len(scans)} recent scans, latest timestamp: {latest_timestamp}"
        )

        return jsonify(
            {
                "scans": scans,
                "count": len(scans),
                "latest_timestamp": latest_timestamp,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error fetching recent scans: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@home_bp.route("/api/summary_stats")
@handle_api_error
def get_summary_stats():
    """Get summary statistics with caching for better performance."""
    from flask import jsonify

    cache_key = "home_summary_stats"
    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(json.loads(cached_data))

    try:
        # Aggregate all counts in a single query for better performance
        counts = db.session.query(
            func.count(ItemMaster.tag_id).label("total"),
            func.sum(
                case((ItemMaster.status.in_(["On Rent", "Delivered"]), 1), else_=0)
            ).label("on_rent"),
            func.sum(case((ItemMaster.status == "Ready to Rent", 1), else_=0)).label(
                "available"
            ),
            func.sum(
                case(
                    (
                        ItemMaster.status.in_(
                            ["Needs to be Inspected", "Wet", "Repair", "Missing"]
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("in_service"),
        ).one()

        # Extract aggregated values (convert to int for JSON serialization)
        total_items = int(counts.total or 0)
        items_on_rent = int(counts.on_rent or 0)
        items_available = int(counts.available or 0)
        items_in_service = int(counts.in_service or 0)

        # Status breakdown
        status_counts = (
            db.session.query(
                ItemMaster.status, func.count(ItemMaster.tag_id).label("count")
            )
            .group_by(ItemMaster.status)
            .all()
        )

        stats = {
            "total_items": total_items or 0,
            "items_on_rent": items_on_rent or 0,
            "items_in_service": items_in_service,
            "items_available": items_available or 0,
            "status_counts": [
                (status or "Unknown", count) for status, count in status_counts
            ],
            "timestamp": datetime.now().isoformat(),
        }

        # Cache for 30 seconds (summary stats change less frequently)
        cache.set(cache_key, json.dumps(stats), ex=30)

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error fetching summary stats: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@home_bp.route("/sticky_test")
def sticky_test():
    """Simple test page to verify sticky positioning works"""
    return render_template("sticky_test.html")


@home_bp.route("/api/item-lookup", methods=["POST"])
@handle_api_error
def item_lookup():
    """
    Look up items by QR code, tag ID, or rental class number across both POS and RFID datasets.
    Supports searching by:
    - Tag ID (exact match in ItemMaster)
    - Rental Class Number (ItemMaster and RFIDTag)
    - QR Code content (flexible matching)
    - Serial Number
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter',
                'message': 'Please provide a query parameter in the request body'
            }), 400
            
        query = data['query'].strip()
        source = data.get('source', 'unknown')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Empty query',
                'message': 'Query parameter cannot be empty'
            }), 400
            
        start_time = time()
        logger.info(f"Item lookup request - Query: '{query}', Source: {source}")
        
        # Search results container
        found_items = []
        searched_tables = []
        
        # 1. Search ItemMaster by Tag ID (exact match)
        try:
            item_master_results = db.session.query(ItemMaster).filter(
                ItemMaster.tag_id == query
            ).all()
            
            for item in item_master_results:
                found_items.append({
                    'source': 'ItemMaster',
                    'match_type': 'tag_id_exact',
                    'tag_id': item.tag_id,
                    'common_name': item.common_name,
                    'rental_class_num': item.rental_class_num,
                    'status': item.status,
                    'quality': item.quality,
                    'bin_location': item.bin_location,
                    'last_contract_num': item.last_contract_num,
                    'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                    'client_name': item.client_name,
                    'serial_number': item.serial_number
                })
            
            searched_tables.append('ItemMaster(tag_id)')
            logger.debug(f"ItemMaster tag_id search found {len(item_master_results)} items")
            
        except Exception as e:
            logger.error(f"Error searching ItemMaster by tag_id: {str(e)}")
        
        # 2. If no exact tag match, search by rental class number in ItemMaster
        if not found_items:
            try:
                rental_class_results = db.session.query(ItemMaster).filter(
                    ItemMaster.rental_class_num == query
                ).limit(10).all()  # Limit to prevent too many results
                
                for item in rental_class_results:
                    found_items.append({
                        'source': 'ItemMaster',
                        'match_type': 'rental_class_exact',
                        'tag_id': item.tag_id,
                        'common_name': item.common_name,
                        'rental_class_num': item.rental_class_num,
                        'status': item.status,
                        'quality': item.quality,
                        'bin_location': item.bin_location,
                        'last_contract_num': item.last_contract_num,
                        'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                        'client_name': item.client_name,
                        'serial_number': item.serial_number
                    })
                
                searched_tables.append('ItemMaster(rental_class)')
                logger.debug(f"ItemMaster rental_class search found {len(rental_class_results)} items")
                
            except Exception as e:
                logger.error(f"Error searching ItemMaster by rental_class: {str(e)}")
        
        # 3. Search RFIDTag table if still no results
        if not found_items:
            try:
                rfid_tag_results = db.session.query(RFIDTag).filter(
                    or_(
                        RFIDTag.tag_id == query,
                        RFIDTag.rental_class_num == query,
                        RFIDTag.serial_number == query
                    )
                ).limit(10).all()
                
                for item in rfid_tag_results:
                    found_items.append({
                        'source': 'RFIDTag',
                        'match_type': 'flexible',
                        'tag_id': item.tag_id,
                        'common_name': item.common_name,
                        'rental_class_num': item.rental_class_num,
                        'status': item.status,
                        'quality': item.quality,
                        'bin_location': item.bin_location,
                        'last_contract_num': None,  # RFIDTag doesn't have this field
                        'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                        'client_name': item.client_name,
                        'serial_number': item.serial_number
                    })
                
                searched_tables.append('RFIDTag')
                logger.debug(f"RFIDTag search found {len(rfid_tag_results)} items")
                
            except Exception as e:
                logger.error(f"Error searching RFIDTag: {str(e)}")
        
        # 4. Search POSEquipment table (POS system data with financials)
        if not found_items:
            try:
                pos_equipment_results = db.session.query(POSEquipment).filter(
                    or_(
                        POSEquipment.item_num == query,
                        POSEquipment.key == query,
                        POSEquipment.serial_no == query,
                        POSEquipment.part_no == query,
                        POSEquipment.name.ilike(f'%{query}%')
                    )
                ).limit(10).all()
                
                for pos_item in pos_equipment_results:
                    found_items.append({
                        'source': 'POSEquipment',
                        'match_type': 'pos_flexible',
                        'item_num': pos_item.item_num,
                        'key': pos_item.key,
                        'name': pos_item.name,
                        'location': pos_item.location,
                        'category': pos_item.category,
                        'department': pos_item.department,
                        'quantity': pos_item.quantity,
                        'current_store': pos_item.current_store,
                        'home_store': pos_item.home_store,
                        'manufacturer': pos_item.manufacturer,
                        'model_no': pos_item.model_no,
                        'serial_no': pos_item.serial_no,
                        'part_no': pos_item.part_no,
                        # Financial data
                        'sell_price': float(pos_item.sell_price) if pos_item.sell_price else 0.0,
                        'retail_price': float(pos_item.retail_price) if pos_item.retail_price else 0.0,
                        'deposit': float(pos_item.deposit) if pos_item.deposit else 0.0,
                        'turnover_mtd': float(pos_item.turnover_mtd) if pos_item.turnover_mtd else 0.0,
                        'turnover_ytd': float(pos_item.turnover_ytd) if pos_item.turnover_ytd else 0.0,
                        'turnover_ltd': float(pos_item.turnover_ltd) if pos_item.turnover_ltd else 0.0,
                        'repair_cost_mtd': float(pos_item.repair_cost_mtd) if pos_item.repair_cost_mtd else 0.0,
                        'repair_cost_ltd': float(pos_item.repair_cost_ltd) if pos_item.repair_cost_ltd else 0.0,
                        'identifier_type': pos_item.identifier_type,
                        'inactive': pos_item.inactive
                    })
                
                searched_tables.append('POSEquipment')
                logger.debug(f"POSEquipment search found {len(pos_equipment_results)} items")
                
            except Exception as e:
                logger.error(f"Error searching POSEquipment: {str(e)}")
        
        # 5. Search POS correlation table for additional context
        pos_correlations = []
        try:
            pos_results = db.session.query(POSRFIDCorrelation).filter(
                or_(
                    POSRFIDCorrelation.rfid_tag_id == query,
                    POSRFIDCorrelation.rfid_rental_class_num == query,
                    POSRFIDCorrelation.pos_item_num == query
                )
            ).limit(5).all()
            
            for correlation in pos_results:
                pos_correlations.append({
                    'pos_item_num': correlation.pos_item_num,
                    'pos_item_desc': correlation.pos_item_desc,
                    'rfid_tag_id': correlation.rfid_tag_id,
                    'rfid_rental_class_num': correlation.rfid_rental_class_num,
                    'correlation_type': correlation.correlation_type,
                    'confidence_score': float(correlation.confidence_score) if correlation.confidence_score else 0.0
                })
            
            searched_tables.append('POSRFIDCorrelation')
            logger.debug(f"POS correlation search found {len(pos_results)} correlations")
            
        except Exception as e:
            logger.error(f"Error searching POS correlations: {str(e)}")
        
        # 6. Flexible search if still no results (partial matches)
        if not found_items:
            try:
                flexible_results = db.session.query(ItemMaster).filter(
                    or_(
                        ItemMaster.common_name.ilike(f'%{query}%'),
                        ItemMaster.serial_number == query,
                        ItemMaster.rental_class_num.ilike(f'%{query}%')
                    )
                ).limit(5).all()
                
                for item in flexible_results:
                    found_items.append({
                        'source': 'ItemMaster',
                        'match_type': 'partial',
                        'tag_id': item.tag_id,
                        'common_name': item.common_name,
                        'rental_class_num': item.rental_class_num,
                        'status': item.status,
                        'quality': item.quality,
                        'bin_location': item.bin_location,
                        'last_contract_num': item.last_contract_num,
                        'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                        'client_name': item.client_name,
                        'serial_number': item.serial_number
                    })
                
                searched_tables.append('ItemMaster(partial)')
                logger.debug(f"Flexible ItemMaster search found {len(flexible_results)} items")
                
            except Exception as e:
                logger.error(f"Error in flexible search: {str(e)}")
        
        search_time = int((time() - start_time) * 1000)  # Convert to milliseconds
        
        response = {
            'success': True,
            'query': query,
            'items': found_items,
            'pos_correlations': pos_correlations,
            'count': len(found_items),
            'search_time': search_time,
            'searched_tables': searched_tables,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Item lookup completed - Query: '{query}', Found: {len(found_items)} items, Time: {search_time}ms")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Item lookup error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to perform item lookup',
            'timestamp': datetime.now().isoformat()
        }), 500
