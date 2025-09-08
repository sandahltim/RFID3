# common.py version: 2025-06-27-v3

"""
Common.py: Shared server-side utilities for all tabs.
"""

from flask import Blueprint, request, jsonify, current_app
from .. import db
from ..models.db_models import Transaction
from ..services.logger import get_logger
from sqlalchemy import func

logger = get_logger(__name__)

common_bp = Blueprint("common", __name__)


@common_bp.route("/get_contract_date", methods=["GET"])
def get_contract_date():
    contract_number = request.args.get("contract_number")
    if not contract_number:
        logger.error("Missing required parameter: contract_number is required")
        return jsonify({"error": "Contract number is required"}), 400

    session = None
    try:
        session = db.session()
        logger.debug("Successfully created session for get_contract_date")

        latest_transaction = (
            session.query(Transaction.scan_date)
            .filter(
                Transaction.contract_number == contract_number,
                Transaction.scan_type == "Rental",
            )
            .order_by(Transaction.scan_date.desc())
            .first()
        )

        if latest_transaction and latest_transaction.scan_date:
            logger.debug(
                f"Found contract date for {contract_number}: {latest_transaction.scan_date}"
            )
            return jsonify({"date": latest_transaction.scan_date.isoformat()})
        logger.debug(f"No contract date found for {contract_number}")
        return jsonify({"date": "N/A"})
    except Exception as e:
        logger.error(
            f"Error fetching contract date for {contract_number}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to fetch contract date"}), 500
    finally:
        if session:
            try:
                session.rollback()
            except Exception as e:
                logger.warning(f"Session rollback failed: {str(e)}")
            session.close()
