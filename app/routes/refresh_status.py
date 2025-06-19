# refresh_status.py version: 2025-06-19-v1
from flask import Blueprint, jsonify, current_app
from .. import db
from ..models.db_models import RefreshState
import logging
import sys

# Configure logging
logger = logging.getLogger('refresh_status')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

refresh_status_bp = Blueprint('refresh_status', __name__)

@refresh_status_bp.route('/refresh/status', methods=['GET'])
def get_refresh_status():
    """Fetch the latest refresh status from the refresh_state table."""
    session = db.session()
    try:
        logger.info("Fetching refresh status")
        refresh_state = session.query(RefreshState).first()
        if refresh_state:
            return jsonify({
                'status': 'success',
                'last_refresh': refresh_state.last_refresh,
                'refresh_type': refresh_state.state_type
            })
        else:
            logger.info("No refresh state found")
            return jsonify({
                'status': 'success',
                'last_refresh': 'N/A',
                'refresh_type': 'N/A'
            })
    except Exception as e:
        logger.error(f"Error fetching refresh status: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        session.close()