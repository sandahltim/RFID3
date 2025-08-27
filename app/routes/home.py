# app/routes/home.py
# home.py version: 2025-07-10-v7
from flask import Blueprint, render_template
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RefreshState
from sqlalchemy import func, case
from time import time
import logging
from datetime import datetime
import os
import json
from config import LOG_FILE
from ..services.logger import get_logger
from ..utils.exceptions import DatabaseException, handle_api_error, log_and_handle_exception

# Configure logging with process ID
logger = get_logger(f'home_{os.getpid()}', level=logging.INFO, log_file=LOG_FILE)

home_bp = Blueprint('home', __name__)

@home_bp.route('/', endpoint='home')
@home_bp.route('/home', endpoint='home_page')
@handle_api_error
def home():
    cache_key = 'home_page_cache'
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug("Serving home page from cache")
        return render_template('home.html', **json.loads(cached_data), cache_bust=int(time()))

    try:
        logger.info("Starting new session for home")

        # Aggregate all counts in a single query for better performance
        try:
            counts = db.session.query(
                func.count(ItemMaster.tag_id).label("total"),
                func.sum(case((ItemMaster.status.in_(['On Rent', 'Delivered']), 1), else_=0)).label("on_rent"),
                func.sum(case((ItemMaster.status == 'Ready to Rent', 1), else_=0)).label("available"),
                func.sum(case((ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']), 1), else_=0)).label("in_service")
            ).one()
        except Exception as e:
            raise DatabaseException(f"Failed to fetch inventory counts: {str(e)}",
                                  error_code="INVENTORY_COUNT_FAILED",
                                  details={'query': 'inventory_aggregation'})
        
        # Extract aggregated values (convert to int for JSON serialization)
        total_items = int(counts.total or 0)
        items_on_rent = int(counts.on_rent or 0)
        items_available = int(counts.available or 0)
        items_in_service = int(counts.in_service or 0)
        
        logger.info(f'Aggregated counts - Total: {total_items}, On Rent: {items_on_rent}, Available: {items_available}, In Service: {items_in_service}')
        logger.debug(f"Performance optimized: Single query replaced multiple COUNT queries")

        # Status breakdown (keep separate for detailed breakdown)
        status_breakdown = db.session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id).label('count')
        ).group_by(ItemMaster.status).all()
        status_counts = [(status or 'Unknown', count) for status, count in status_breakdown]

        # Recent scans - increased to 50 for better real-time experience
        recent_scans = db.session.query(ItemMaster).filter(ItemMaster.date_last_scanned.isnot(None)).order_by(
            ItemMaster.date_last_scanned.desc()
        ).limit(50).all()
        logger.info(f'Recent scans count: {len(recent_scans)}')
        logger.debug(f"Recent scans sample: {[(item.tag_id, item.common_name, item.date_last_scanned) for item in recent_scans[:5]]}")

        # Last refresh state
        refresh_state = db.session.query(RefreshState).first()
        last_refresh = refresh_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S') if refresh_state and refresh_state.last_refresh else 'N/A'
        refresh_type = refresh_state.state_type if refresh_state else 'N/A'
        logger.info(f'Last refresh details: {last_refresh}, Type: {refresh_type}')
        logger.debug(f"Last refresh: {last_refresh}, Type: {refresh_type}")

        # Cache the response
        render_data = {
            'total_items': total_items or 0,
            'items_on_rent': items_on_rent or 0,
            'items_in_service': items_in_service or 0,
            'items_available': items_available or 0,
            'status_counts': status_counts,
            'recent_scans': [{
                'tag_id': item.tag_id, 
                'common_name': item.common_name,
                'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                'status': item.status,
                'last_contract_num': item.last_contract_num
            } for item in recent_scans],
            'last_refresh': last_refresh,
            'refresh_type': refresh_type
        }
        cache.set(cache_key, json.dumps(render_data), ex=60)  # Cache for 60 seconds

        return render_template('home.html',
                              total_items=total_items or 0,
                              items_on_rent=items_on_rent or 0,
                              items_in_service=items_in_service or 0,
                              items_available=items_available or 0,
                              status_counts=status_counts,
                              recent_scans=recent_scans,
                              last_refresh=last_refresh,
                              refresh_type=refresh_type,
                              cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
        return render_template('home.html',
                              total_items=0,
                              items_on_rent=0,
                              items_in_service=0,
                              items_available=0,
                              status_counts=[],
                              recent_scans=[],
                              last_refresh='N/A',
                              refresh_type='N/A',
                              cache_bust=int(time()))
    finally:
        pass  # Flask-SQLAlchemy automatically manages session lifecycle

@home_bp.route('/refresh_status')
def get_refresh_status():
    """Get current refresh operation status."""
    from flask import jsonify
    from ..services.refresh import refresh_status
    return jsonify(refresh_status)

@home_bp.route('/api/recent_scans')
@handle_api_error
def get_recent_scans():
    """Get recent scans with optional timestamp filtering for real-time updates."""
    from flask import request, jsonify
    from datetime import datetime, timedelta
    
    try:
        # Get parameters
        limit = int(request.args.get('limit', 50))
        since_timestamp = request.args.get('since')  # ISO timestamp string
        
        # Build query for recent scans
        query = db.session.query(
            ItemMaster.tag_id,
            ItemMaster.common_name,
            ItemMaster.date_last_scanned,
            ItemMaster.status,
            ItemMaster.last_contract_num,
            ItemMaster.rental_class_num
        ).filter(ItemMaster.date_last_scanned.isnot(None))
        
        # Apply timestamp filter if provided
        if since_timestamp:
            try:
                since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                query = query.filter(ItemMaster.date_last_scanned > since_dt)
                logger.debug(f"Filtering scans since {since_dt}")
            except ValueError:
                logger.warning(f"Invalid since_timestamp format: {since_timestamp}")
        
        # Order by most recent first and limit
        recent_items = query.order_by(ItemMaster.date_last_scanned.desc()).limit(limit).all()
        
        # Format response
        scans = []
        for item in recent_items:
            scans.append({
                'tag_id': item.tag_id,
                'common_name': item.common_name or 'N/A',
                'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                'status': item.status or 'N/A',
                'last_contract_num': item.last_contract_num or 'N/A',
                'rental_class_num': item.rental_class_num or 'N/A'
            })
        
        # Get latest timestamp for next poll
        latest_timestamp = None
        if scans:
            latest_timestamp = scans[0]['date_last_scanned']
        
        logger.debug(f"Returning {len(scans)} recent scans, latest timestamp: {latest_timestamp}")
        
        return jsonify({
            'scans': scans,
            'count': len(scans),
            'latest_timestamp': latest_timestamp,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching recent scans: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@home_bp.route('/api/summary_stats')
@handle_api_error
def get_summary_stats():
    """Get summary statistics with caching for better performance."""
    from flask import jsonify
    
    cache_key = 'home_summary_stats'
    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        # Aggregate all counts in a single query for better performance
        counts = db.session.query(
            func.count(ItemMaster.tag_id).label("total"),
            func.sum(case((ItemMaster.status.in_(['On Rent', 'Delivered']), 1), else_=0)).label("on_rent"),
            func.sum(case((ItemMaster.status == 'Ready to Rent', 1), else_=0)).label("available"),
            func.sum(case((ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']), 1), else_=0)).label("in_service")
        ).one()
        
        # Extract aggregated values (convert to int for JSON serialization)
        total_items = int(counts.total or 0)
        items_on_rent = int(counts.on_rent or 0)
        items_available = int(counts.available or 0)
        items_in_service = int(counts.in_service or 0)
        
        # Status breakdown
        status_counts = db.session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id).label('count')
        ).group_by(ItemMaster.status).all()
        
        stats = {
            'total_items': total_items or 0,
            'items_on_rent': items_on_rent or 0,
            'items_in_service': items_in_service,
            'items_available': items_available or 0,
            'status_counts': [(status or 'Unknown', count) for status, count in status_counts],
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache for 30 seconds (summary stats change less frequently)
        cache.set(cache_key, json.dumps(stats), ex=30)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error fetching summary stats: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
