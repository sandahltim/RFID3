# Bedrock API Service - Provides API layer for bedrock transformed data
# Version: 2025-09-25-v2-common-names-added
# Purpose: API service layer using bedrock transformation service
#
# CHANGELOG v2:
# - Added get_common_names() method for Tab 1 common names functionality
# - Fixed parameter naming consistency (store_filter vs store)
# - Proper pagination support for common names

from typing import Dict, List, Optional, Any
from app.services.bedrock_transformation_service import bedrock_transformation_service
from app.services.logger import get_logger

logger = get_logger(__name__)

class BedrockAPIService:
    """
    API service layer that provides business object access using bedrock transformation service
    """

    def __init__(self):
        self.transformation_service = bedrock_transformation_service

    def get_equipment_catalog(self, filters: Dict = None) -> Dict[str, Any]:
        """Get equipment catalog with optional filters including user categories"""
        try:
            filters = filters or {}
            limit = filters.get('limit', 100)
            offset = filters.get('offset', 0)
            category = filters.get('category')
            user_category = filters.get('user_category')
            store = filters.get('store')
            search = filters.get('search')
            type_filter = filters.get('type')
            status = filters.get('status')
            bin_filter = filters.get('bin')

            equipment_list = self.transformation_service.get_equipment_catalog(
                limit=limit,
                offset=offset,
                category=category,
                user_category=user_category,
                store=store,
                search=search,
                type_filter=type_filter,
                status=status,
                bin_filter=bin_filter
            )

            return {
                'success': True,
                'data': equipment_list.get('items', []),
                'pagination': {
                    'offset': offset,
                    'limit': limit,
                    'total': equipment_list.get('total', 0),
                    'has_more': equipment_list.get('has_more', False)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get equipment catalog: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def get_common_names(self, filters: Dict = None) -> Dict[str, Any]:
        """Get common names for a category/subcategory with POS vs RFID comparison"""
        try:
            filters = filters or {}
            category = filters.get('category')
            subcategory = filters.get('subcategory')
            store = filters.get('store')
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 10)

            if not category or not subcategory:
                return {
                    'success': False,
                    'error': 'Category and subcategory are required',
                    'data': []
                }

            # Use transformation service to get common names data
            common_names_list = self.transformation_service.get_common_names_for_category(
                category=category,
                subcategory=subcategory,
                store_filter=store,
                page=page,
                per_page=per_page
            )

            return {
                'success': True,
                'data': common_names_list.get('items', []),
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': common_names_list.get('total', 0),
                    'has_more': common_names_list.get('has_more', False)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get common names: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def get_individual_rfid_items(self, filters: Dict = None) -> Dict[str, Any]:
        """Get individual RFID tagged items for a specific equipment name"""
        try:
            filters = filters or {}
            category = filters.get('category')
            subcategory = filters.get('subcategory')
            equipment_name = filters.get('equipment_name')
            store = filters.get('store')
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 10)

            if not category or not subcategory or not equipment_name:
                return {
                    'success': False,
                    'error': 'Category, subcategory, and equipment_name are required',
                    'data': []
                }

            # Use transformation service to get individual RFID items
            rfid_items = self.transformation_service.get_individual_rfid_items(
                category=category,
                subcategory=subcategory,
                equipment_name=equipment_name,
                store_filter=store,
                page=page,
                per_page=per_page
            )

            return {
                'success': True,
                'data': rfid_items.get('items', []),
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': rfid_items.get('total', 0),
                    'has_more': rfid_items.get('has_more', False)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get individual RFID items: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def get_contract_details(self, contract_no: str) -> Dict[str, Any]:
        """Get contract details with items and correlations"""
        try:
            contract = self.transformation_service.get_contract_details(contract_no)

            if not contract:
                return {
                    'success': False,
                    'error': 'Contract not found',
                    'data': None
                }

            return {
                'success': True,
                'data': contract
            }

        except Exception as e:
            logger.error(f"Failed to get contract details: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }

    def get_customer_profile(self, customer_no: str) -> Dict[str, Any]:
        """Get customer profile with contract history"""
        try:
            customer = self.transformation_service.get_customer_profile(customer_no)

            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found',
                    'data': None
                }

            return {
                'success': True,
                'data': customer
            }

        except Exception as e:
            logger.error(f"Failed to get customer profile: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }

    def get_rfid_correlations(self, filters: Dict = None) -> Dict[str, Any]:
        """Get RFID-POS correlations with filters"""
        try:
            filters = filters or {}
            limit = filters.get('limit', 100)
            offset = filters.get('offset', 0)
            correlation_type = filters.get('type')

            correlations = self.transformation_service.get_rfid_correlations(
                limit=limit,
                offset=offset,
                correlation_type=correlation_type
            )

            return {
                'success': True,
                'data': correlations.get('correlations', []),
                'pagination': {
                    'offset': offset,
                    'limit': limit,
                    'total': correlations.get('total', 0),
                    'has_more': correlations.get('has_more', False)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get RFID correlations: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def search_equipment(self, query: str, filters: Dict = None) -> Dict[str, Any]:
        """Search equipment across all fields"""
        try:
            filters = filters or {}
            limit = filters.get('limit', 50)

            results = self.transformation_service.search_equipment(
                search_query=query,
                limit=limit
            )

            return {
                'success': True,
                'data': results.get('items', []),
                'query': query,
                'total_found': results.get('total', 0)
            }

        except Exception as e:
            logger.error(f"Failed to search equipment: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def get_store_analytics(self, store_code: str, date_range: Dict = None) -> Dict[str, Any]:
        """Get analytics data for a specific store"""
        try:
            analytics = self.transformation_service.get_store_analytics(
                store_code=store_code,
                date_range=date_range
            )

            return {
                'success': True,
                'data': analytics
            }

        except Exception as e:
            logger.error(f"Failed to get store analytics: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }

    def get_recent_transactions(self, filters: Dict = None) -> Dict[str, Any]:
        """Get recent transactions with filters"""
        try:
            filters = filters or {}
            limit = filters.get('limit', 100)
            store = filters.get('store')
            days = filters.get('days', 30)

            transactions = self.transformation_service.get_recent_transactions(
                limit=limit,
                store_filter=store,
                days_back=days
            )

            return {
                'success': True,
                'data': transactions.get('transactions', []),
                'summary': transactions.get('summary', {})
            }

        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def get_inventory_status(self, filters: Dict = None) -> Dict[str, Any]:
        """Get inventory status summary"""
        try:
            filters = filters or {}
            category = filters.get('category')
            store = filters.get('store')

            status = self.transformation_service.get_inventory_status(
                category_filter=category,
                store_filter=store
            )

            return {
                'success': True,
                'data': status
            }

        except Exception as e:
            logger.error(f"Failed to get inventory status: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }

    def get_equipment_details(self, equipment_key: str) -> Dict[str, Any]:
        """Get detailed equipment information"""
        try:
            equipment = self.transformation_service.get_equipment_details(equipment_key)

            if not equipment:
                return {
                    'success': False,
                    'error': 'Equipment not found',
                    'data': None
                }

            return {
                'success': True,
                'data': equipment
            }

        except Exception as e:
            logger.error(f"Failed to get equipment details: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary data"""
        try:
            summary = self.transformation_service.get_dashboard_summary()

            return {
                'success': True,
                'data': summary
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }

# Service instance for API routes
bedrock_api_service = BedrockAPIService()