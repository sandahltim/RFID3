# Operations API Client - Replaces RFIDpro for most operations
# Version: 2025-09-17-v1
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .logger import get_logger

logger = get_logger("operations_api_client", level=logging.INFO)

class OperationsAPIClient:
    """
    Client for our self-hosted Operations API
    Replaces RFIDpro calls except for manual sync operations
    """

    def __init__(self, base_url: str = "http://localhost:8444/api/v1", api_key: str = "executive_readonly_key"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = self._create_session()

    def _create_session(self):
        """Create requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

        return session

    def get_item_master(self, limit: int = 1000, skip: int = 0, **filters) -> List[Dict]:
        """Get items from operations API - replaces RFIDpro get_item_master"""
        try:
            params = {"limit": limit, "skip": skip}
            params.update(filters)  # Add any filters (status, store, etc.)

            response = self.session.get(f"{self.base_url}/items", params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get item master: {e}")
            return []

    def get_transactions(self, limit: int = 1000, skip: int = 0, **filters) -> List[Dict]:
        """Get transactions from operations API - replaces RFIDpro get_transactions"""
        try:
            params = {"limit": limit, "skip": skip}
            params.update(filters)

            response = self.session.get(f"{self.base_url}/transactions", params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get transactions: {e}")
            return []

    def get_equipment(self, limit: int = 1000, skip: int = 0, **filters) -> List[Dict]:
        """Get equipment from operations API - new functionality"""
        try:
            params = {"limit": limit, "skip": skip}
            params.update(filters)

            response = self.session.get(f"{self.base_url}/equipment", params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get equipment: {e}")
            return []

    def update_item_status(self, tag_id: str, status: str, updated_by: str = "manager_interface") -> bool:
        """Update item status - replaces RFIDpro update_status"""
        try:
            data = {
                "status": status,
                "last_scanned_by": updated_by
            }

            response = self.session.patch(f"{self.base_url}/items/{tag_id}/status", json=data)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to update item status for {tag_id}: {e}")
            return False

    def update_bin_location(self, tag_id: str, bin_location: str, updated_by: str = "manager_interface") -> bool:
        """Update item location - replaces RFIDpro update_bin_location"""
        try:
            response = self.session.patch(
                f"{self.base_url}/items/{tag_id}/location",
                params={
                    "bin_location": bin_location
                }
            )
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to update bin location for {tag_id}: {e}")
            return False

    def insert_item(self, item_data: Dict) -> bool:
        """Create new item - replaces RFIDpro insert_item"""
        try:
            response = self.session.post(f"{self.base_url}/items", json=item_data)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to insert item: {e}")
            return False

    def lookup_item(self, identifier: str) -> Optional[Dict]:
        """Lookup item by any identifier - enhanced functionality"""
        try:
            response = self.session.get(f"{self.base_url}/items/lookup/{identifier}")
            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to lookup item {identifier}: {e}")
            return None

    def get_health(self) -> Dict:
        """Check operations API health"""
        try:
            response = self.session.get(f"{self.base_url.replace('/api/v1', '')}/health")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get API health: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def trigger_rfidpro_sync(self, sync_type: str = "incremental") -> Dict:
        """Trigger manual RFIDpro sync - read-only pull"""
        try:
            data = {"sync_type": sync_type}
            response = self.session.post(f"{self.base_url}/rfidpro/manual-pull", json=data)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to trigger RFIDpro sync: {e}")
            return {"status": "error", "message": str(e)}