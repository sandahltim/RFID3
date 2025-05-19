# common.py version: 2025-05-19-v1

"""
Common.py: Minimal shared server-side utilities for all tabs.
Currently a placeholder; add shared endpoints (e.g., /get_contract_date) as needed.
"""

from flask import Blueprint

common_bp = Blueprint('common', __name__)

# Placeholder for shared endpoints
# Example: /get_contract_date (used by printTable in common.js)
# @common_bp.route('/get_contract_date', methods=['GET'])
# def get_contract_date():
#     # Implement shared logic here
#     pass