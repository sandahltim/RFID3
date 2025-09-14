# app/routes/mobile_api.py
# Mobile RFID API for simplified mobile scanning interface
# Version: 2025-09-12-v1

from flask import Blueprint, request, jsonify
from sqlalchemy import text, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging
import json
from .. import db
from ..models.db_models import ItemMaster, Transaction
# Configure logging
logger = logging.getLogger(__name__)

mobile_api_bp = Blueprint('mobile_api', __name__, url_prefix='/api/mobile')

@mobile_api_bp.route('/health', methods=['GET'])
def mobile_health():
    """Mobile API health check"""
    try:
        # Test database connection
        db.session.execute(text("SELECT 1")).scalar()
        return jsonify({
            "status": "healthy",
            "message": "Mobile RFID API operational",
            "timestamp": datetime.utcnow().isoformat(),
            "api_version": "2025-09-12-v1"
        }), 200
    except Exception as e:
        logger.error(f"Mobile API health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy", 
            "message": f"Database connection failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 503

@mobile_api_bp.route('/scan/<tag_id>', methods=['GET'])
def scan_item(tag_id):
    """
    Mobile RFID scan endpoint - Get item details by tag ID
    Optimized for mobile scanning operations
    """
    try:
        # Search in ItemMaster for the tag
        item = db.session.query(ItemMaster).filter(
            ItemMaster.tag_id == tag_id.upper()
        ).first()
        
        if not item:
            logger.info(f"Mobile scan: Tag {tag_id} not found in database")
            return jsonify({
                "success": False,
                "message": "Item not found",
                "tag_id": tag_id,
                "found": False
            }), 404
        
        # Get recent transaction history for this item (last 10)
        recent_transactions = db.session.query(Transaction).filter(
            Transaction.tag_id == tag_id.upper()
        ).order_by(Transaction.scan_date.desc()).limit(10).all()
        
        # Prepare mobile-optimized response
        response_data = {
            "success": True,
            "found": True,
            "tag_id": tag_id,
            "item": {
                "tag_id": item.tag_id,
                "rental_class_id": item.rental_class_id,
                "serial_number": getattr(item, 'serial_number', ''),
                "status": getattr(item, 'status', 'Unknown'),
                "bin_location": getattr(item, 'bin_location', ''),
                "notes": getattr(item, 'notes', ''),
                "last_scanned": item.date_last_scanned.isoformat() if item.date_last_scanned else None
            },
            "recent_scans": len(recent_transactions),
            "last_scan_date": recent_transactions[0].scan_date.isoformat() if recent_transactions else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Mobile scan successful: {tag_id} found")
        return jsonify(response_data), 200
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in mobile scan for {tag_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Database error occurred",
            "error": str(e)
        }), 500

@mobile_api_bp.route('/scan/<tag_id>/update', methods=['POST'])
# Removed decorator for compatibility
def update_item_mobile(tag_id):
    """
    Mobile item update endpoint - Update item details from mobile device
    Accepts: status, bin_location, notes
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        # Find the item
        item = db.session.query(ItemMaster).filter(
            ItemMaster.tag_id == tag_id.upper()
        ).first()
        
        if not item:
            return jsonify({
                "success": False,
                "message": "Item not found",
                "tag_id": tag_id
            }), 404
        
        # Track what was updated
        updates = []
        
        # Update allowed fields
        if 'status' in data and data['status']:
            item.status = data['status']
            updates.append("status")
            
        if 'bin_location' in data and data['bin_location']:
            item.bin_location = data['bin_location']
            updates.append("bin_location")
            
        if 'notes' in data and data['notes'] is not None:
            item.notes = data['notes']
            updates.append("notes")
        
        # Update last scanned time
        item.date_last_scanned = datetime.utcnow()
        
        # Create a transaction record for the mobile scan
        new_transaction = Transaction(
            tag_id=tag_id.upper(),
            scan_date=datetime.utcnow(),
            scan_type='mobile_update',
            user_id=data.get('user_id', 'mobile_user'),
            location=data.get('location', 'mobile')
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        logger.info(f"Mobile update successful for {tag_id}: {', '.join(updates)}")
        
        return jsonify({
            "success": True,
            "message": f"Updated: {', '.join(updates)}",
            "tag_id": tag_id,
            "updates": updates,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error in mobile update for {tag_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Database update failed",
            "error": str(e)
        }), 500

@mobile_api_bp.route('/inventory/search', methods=['GET'])
# Removed decorator for compatibility
def search_inventory():
    """
    Mobile inventory search - Find items by various criteria
    Query params: q (search term), status, location, limit
    """
    try:
        search_term = request.args.get('q', '').strip()
        status_filter = request.args.get('status', '').strip()
        location_filter = request.args.get('location', '').strip()
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 results
        
        # Build query
        query = db.session.query(ItemMaster)
        
        # Apply search term to multiple fields
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(
                ItemMaster.tag_id.like(search_pattern),
                ItemMaster.rental_class_id.like(search_pattern),
                ItemMaster.serial_number.like(search_pattern),
                ItemMaster.notes.like(search_pattern)
            ))
        
        # Apply filters
        if status_filter:
            query = query.filter(ItemMaster.status == status_filter)
            
        if location_filter:
            query = query.filter(ItemMaster.bin_location.like(f"%{location_filter}%"))
        
        # Execute query with limit
        items = query.limit(limit).all()
        
        # Prepare mobile-optimized results
        results = []
        for item in items:
            results.append({
                "tag_id": item.tag_id,
                "rental_class_id": item.rental_class_id,
                "serial_number": getattr(item, 'serial_number', ''),
                "status": getattr(item, 'status', 'Unknown'),
                "bin_location": getattr(item, 'bin_location', ''),
                "last_scanned": item.date_last_scanned.isoformat() if item.date_last_scanned else None
            })
        
        logger.info(f"Mobile search returned {len(results)} items for query: {search_term}")
        
        return jsonify({
            "success": True,
            "results": results,
            "count": len(results),
            "search_term": search_term,
            "filters": {
                "status": status_filter,
                "location": location_filter
            },
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in mobile search: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Search failed",
            "error": str(e)
        }), 500

@mobile_api_bp.route('/inventory/recent', methods=['GET'])
# Removed decorator for compatibility
def recent_activity():
    """
    Mobile recent activity - Get recently scanned items
    Query params: hours (default 24), limit (default 50)
    """
    try:
        hours_back = int(request.args.get('hours', 24))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        since_date = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Get recent transactions
        recent_transactions = db.session.query(Transaction).filter(
            Transaction.scan_date >= since_date
        ).order_by(Transaction.scan_date.desc()).limit(limit).all()
        
        # Group by tag_id and get item details
        results = []
        seen_tags = set()
        
        for transaction in recent_transactions:
            if transaction.tag_id not in seen_tags:
                seen_tags.add(transaction.tag_id)
                
                # Get item details
                item = db.session.query(ItemMaster).filter(
                    ItemMaster.tag_id == transaction.tag_id
                ).first()
                
                result_item = {
                    "tag_id": transaction.tag_id,
                    "scan_date": transaction.scan_date.isoformat(),
                    "scan_type": getattr(transaction, 'scan_type', 'scan'),
                    "location": getattr(transaction, 'location', 'Unknown')
                }
                
                if item:
                    result_item.update({
                        "rental_class_id": item.rental_class_id,
                        "status": getattr(item, 'status', 'Unknown'),
                        "bin_location": getattr(item, 'bin_location', '')
                    })
                
                results.append(result_item)
        
        logger.info(f"Mobile recent activity returned {len(results)} items from last {hours_back} hours")
        
        return jsonify({
            "success": True,
            "recent_items": results,
            "count": len(results),
            "hours_back": hours_back,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in mobile recent activity: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get recent activity",
            "error": str(e)
        }), 500

@mobile_api_bp.route('/batch/scan', methods=['POST'])
# Removed decorator for compatibility
def batch_scan():
    """
    Mobile batch scan endpoint - Process multiple RFID scans at once
    Accepts: {"tag_ids": ["TAG1", "TAG2", ...], "location": "warehouse", "user_id": "user123"}
    """
    try:
        data = request.get_json()
        if not data or 'tag_ids' not in data:
            return jsonify({
                "success": False,
                "message": "No tag_ids provided"
            }), 400
        
        tag_ids = [tag.upper() for tag in data['tag_ids']]
        location = data.get('location', 'mobile')
        user_id = data.get('user_id', 'mobile_user')
        
        if len(tag_ids) > 100:  # Limit batch size
            return jsonify({
                "success": False,
                "message": "Batch size too large (max 100 tags)"
            }), 400
        
        results = []
        found_count = 0
        
        # Process each tag
        for tag_id in tag_ids:
            try:
                # Find item
                item = db.session.query(ItemMaster).filter(
                    ItemMaster.tag_id == tag_id
                ).first()
                
                if item:
                    # Update last scanned time
                    item.date_last_scanned = datetime.utcnow()
                    
                    # Create transaction record
                    new_transaction = Transaction(
                        tag_id=tag_id,
                        scan_date=datetime.utcnow(),
                        scan_type='mobile_batch',
                        user_id=user_id,
                        location=location
                    )
                    db.session.add(new_transaction)
                    
                    results.append({
                        "tag_id": tag_id,
                        "found": True,
                        "status": getattr(item, 'status', 'Unknown'),
                        "location": getattr(item, 'bin_location', '')
                    })
                    found_count += 1
                else:
                    results.append({
                        "tag_id": tag_id,
                        "found": False,
                        "message": "Not found in database"
                    })
                    
            except Exception as tag_error:
                results.append({
                    "tag_id": tag_id,
                    "found": False,
                    "error": str(tag_error)
                })
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Mobile batch scan processed {len(tag_ids)} tags, found {found_count}")
        
        return jsonify({
            "success": True,
            "message": f"Processed {len(tag_ids)} tags, found {found_count}",
            "results": results,
            "summary": {
                "total_scanned": len(tag_ids),
                "found": found_count,
                "not_found": len(tag_ids) - found_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in mobile batch scan: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Batch scan failed",
            "error": str(e)
        }), 500

# Log deployment
logger.info("Deployed mobile_api.py version: 2025-09-12-v1")