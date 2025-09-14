# app/services/api_client.py
# api_client.py version: 2025-09-12-DISABLED
# DISABLED: All RFIDpro API integration removed to prevent data corruption

import requests
import time
import copy
import redis
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import (
    API_USERNAME,
    API_PASSWORD,
    LOGIN_URL,
    INCREMENTAL_FALLBACK_SECONDS,
    LOG_FILE,
)
import logging
from urllib.parse import quote
from contextlib import nullcontext
from .. import cache
from .logger import get_logger
from ..utils.exceptions import APIException, log_and_handle_exception

# Configure logging
logger = get_logger("api_client", level=logging.INFO, log_file=LOG_FILE)


def create_session():
    """Create a new requests session with retry strategy."""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        allowed_methods=["GET", "POST", "PATCH"],
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class APIClient:
    """
    DISABLED: RFIDpro API client disabled to prevent data corruption.
    
    All methods return empty results or success responses without making external API calls.
    This maintains interface compatibility while preventing data corruption.
    """

    def __init__(self):
        # DISABLED: RFIDpro API integration removed to prevent data corruption
        logger.info("RFIDpro API client initialized in DISABLED mode")
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = LOGIN_URL
        self.item_master_endpoint = "14223767938169344381"
        self.token = "DISABLED_MODE"
        self.token_expiry = datetime.now() + timedelta(days=365)
        self.session = create_session()
        logger.info("RFIDpro API authentication skipped - running in disabled mode")

    def authenticate(self):
        """DISABLED: RFIDpro API authentication disabled to prevent data corruption"""
        logger.info("RFIDpro API authentication call skipped - running in disabled mode")
        self.token = "DISABLED_MODE"
        self.token_expiry = datetime.now() + timedelta(days=365)
        return True

    def _make_request(
        self,
        endpoint_id,
        params=None,
        method="GET",
        data=None,
        timeout=20,
        user_operation=False,
        headers=None,
    ):
        """DISABLED: All RFIDpro API requests disabled to prevent data corruption"""
        logger.info(f"RFIDpro API request blocked - {method} to endpoint {endpoint_id}")
        # Return empty response to prevent application errors
        return []

    def validate_date(self, date_str, field_name):
        """Validate date string and return datetime object or None."""
        if date_str is None or date_str == "0000-00-00 00:00:00":
            logger.debug(f"Null or invalid {field_name}: {date_str}, returning None")
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError as e:
                logger.warning(
                    f"Invalid {field_name}: {date_str}. Error: {str(e)}. Returning None."
                )
                return None

    def get_item_master(self, since_date=None, full_refresh=False):
        """DISABLED: RFIDpro API get_item_master disabled to prevent data corruption"""
        logger.info("RFIDpro API get_item_master call blocked - returning empty list")
        return []

    def get_transactions(self, since_date=None, full_refresh=False):
        """DISABLED: RFIDpro API get_transactions disabled to prevent data corruption"""
        logger.info("RFIDpro API get_transactions call blocked - returning empty list")
        return []

    def get_seed_data(self, since_date=None):
        """DISABLED: RFIDpro API get_seed_data disabled to prevent data corruption"""
        logger.info("RFIDpro API get_seed_data call blocked - returning empty list")
        return []

    def update_bin_location(self, tag_id, bin_location, timeout=20):
        """DISABLED: RFIDpro API update_bin_location disabled to prevent data corruption"""
        logger.info(f"RFIDpro API update_bin_location call blocked for tag_id {tag_id}")
        return {"success": True, "message": "API disabled - no external update performed"}

    def update_status(self, tag_id, status, timeout=20):
        """DISABLED: RFIDpro API update_status disabled to prevent data corruption"""
        logger.info(f"RFIDpro API update_status call blocked for tag_id {tag_id}")
        return {"success": True, "message": "API disabled - no external update performed"}

    def update_notes(self, tag_id, notes):
        """DISABLED: RFIDpro API update_notes disabled to prevent data corruption"""
        logger.info(f"RFIDpro API update_notes call blocked for tag_id {tag_id}")
        return {"success": True, "message": "API disabled - no external update performed"}

    def update_quality(self, tag_id, quality):
        """DISABLED: RFIDpro API update_quality disabled to prevent data corruption"""
        logger.info(f"RFIDpro API update_quality call blocked for tag_id {tag_id}")
        return {"success": True, "message": "API disabled - no external update performed"}

    def insert_item(self, item_data, timeout=20):
        """DISABLED: RFIDpro API insert_item disabled to prevent data corruption"""
        logger.info("RFIDpro API insert_item call blocked")
        return {"success": True, "message": "API disabled - no external insert performed"}