# common.py version: 2025-05-29-v2

"""
Common.py: Shared server-side utilities for all tabs.
"""

from flask import Blueprint, request, jsonify, current_app
from .. import db
from ..models.db_models import Transaction
from sqlalchemy import func
import logging
import sys

# Configure logging
logger = logging.getLogger('common')
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

common_bp = Blueprint('common', __name__)

@common_bp.route('/get_contract_date', methods=['GET'])
def get_contract_date():
    contract_number = request.args.get('contract_number')
    if not contract_number:
        logger.error("Missing required parameter: contract_number is required")
        current_app.logger.error("Missing required parameter: contract_number is required")
        return jsonify({'error': 'Contract number is required'}), 400

    session = None
    try:
        session = db.session()
        logger.info("Successfully created session for get_contract_date")

        latest_transaction = session.query(Transaction.scan_date).filter(
            Transaction.contract_number == contract_number,
            Transaction.scan_type == 'Rental'
        ).order_by(desc(Transaction.scan_date)).first()

        if latest_transaction and latest_transaction.scan_date:
            return jsonify({'date': latest_transaction.scan_date.isoformat()})
        return jsonify({'date': 'N/A'})
    except Exception as e:
        logger.error(f"Error fetching contract date for {contract_number}: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching contract date for {contract_number}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch contract date'}), 500
    finally:
        if session:
            session.close()