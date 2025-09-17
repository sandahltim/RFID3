# Unified API Client - Routes to Operations API or RFIDpro based on config
# Version: 2025-09-17-v1
from config import USE_OPERATIONS_API
from .api_client import APIClient  # Original RFIDpro client
from .operations_api_client import OperationsAPIClient
import logging

class UnifiedAPIClient:
    """
    Unified client that routes calls to either Operations API or RFIDpro
    Based on USE_OPERATIONS_API configuration flag
    """

    def __init__(self):
        self.use_operations_api = USE_OPERATIONS_API
        self.base_url = "unified_api_client"  # For health check compatibility

        if self.use_operations_api:
            self.client = OperationsAPIClient()
            logging.info("Using Operations API as primary data source")
        else:
            self.client = APIClient()
            logging.info("Using RFIDpro API as primary data source")

        # Always keep RFIDpro client for manual sync
        self.rfidpro_client = APIClient()

    # Standard operations (routed based on config)
    def get_item_master(self, **kwargs):
        """Get item master data"""
        return self.client.get_item_master(**kwargs)

    def get_transactions(self, **kwargs):
        """Get transaction data"""
        return self.client.get_transactions(**kwargs)

    def update_status(self, tag_id: str, status: str):
        """Update item status"""
        if self.use_operations_api:
            return self.client.update_item_status(tag_id, status)
        else:
            return self.client.update_status(tag_id, status)

    def update_bin_location(self, tag_id: str, bin_location: str):
        """Update item location"""
        return self.client.update_bin_location(tag_id, bin_location)

    def insert_item(self, item_data):
        """Insert new item"""
        return self.client.insert_item(item_data)

    def lookup_item(self, identifier: str):
        """Lookup item by identifier"""
        if self.use_operations_api:
            return self.client.lookup_item(identifier)
        else:
            # RFIDpro doesn't have direct lookup, search item master
            items = self.client.get_item_master()
            for item in items:
                if item.get('tag_id') == identifier:
                    return item
            return None

    # Manual RFIDpro operations (always use RFIDpro)
    def manual_rfidpro_sync(self, sync_type: str = "incremental"):
        """Manual sync from RFIDpro - always uses RFIDpro client"""
        if self.use_operations_api:
            # Trigger sync via operations API
            return self.client.trigger_rfidpro_sync(sync_type)
        else:
            # Direct RFIDpro refresh
            from .refresh import refresh_from_rfidpro
            return refresh_from_rfidpro(sync_type)

    def test_rfidpro_connection(self):
        """Test RFIDpro connection - for manual sync testing"""
        try:
            self.rfidpro_client.authenticate()
            return {"status": "success", "message": "RFIDpro connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_api_status(self):
        """Get current API status"""
        if self.use_operations_api:
            ops_health = self.client.get_health()
            rfidpro_health = self.test_rfidpro_connection()

            return {
                "primary_api": "operations",
                "operations_api": ops_health,
                "rfidpro_api": rfidpro_health,
                "manual_sync_available": True
            }
        else:
            rfidpro_health = self.test_rfidpro_connection()

            return {
                "primary_api": "rfidpro",
                "rfidpro_api": rfidpro_health,
                "operations_api": {"status": "not_configured"},
                "manual_sync_available": True
            }
    # Compatibility methods for health check and existing code
    @property  
    def item_master_endpoint(self):
        """Compatibility for health check"""
        return "operations_api/items" if self.use_operations_api else getattr(self.rfidpro_client, 'item_master_endpoint', 'rfidpro/items')

    @property
    def transaction_endpoint(self):
        """Compatibility for health check"""
        return "operations_api/transactions" if self.use_operations_api else getattr(self.rfidpro_client, 'transaction_endpoint', 'rfidpro/transactions')
    
    @property
    def token(self):
        """Compatibility for health check"""
        return "operations_api_token" if self.use_operations_api else getattr(self.rfidpro_client, "token", None)

