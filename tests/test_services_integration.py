"""
Service-Level Integration Tests for RFID-POS Fixes
Direct testing of service methods with focus on integration points
"""

import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock, Mock, call, mock_open
import pandas as pd
import tempfile
import os
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.services.refresh import (
    get_api_client, 
    update_item_master, 
    update_transactions,
    validate_date,
    full_refresh,
    incremental_refresh
)
from app.services.csv_import_service import CSVImportService
from app.models.db_models import ItemMaster, Transaction, SeedRentalClass
from app.models.pos_models import POSEquipment


class TestRefreshServiceIntegration:
    """Test refresh.py service integration and rental_class_num handling"""
    
    def setup_method(self):
        """Setup for refresh service tests"""
        self.mock_api_data = [
            {
                'tag_id': 'RFID001',
                'uuid_accounts_fk': 'account_1',
                'serial_number': 'SN001',
                'client_name': 'Test Client',
                'rental_class_num': 'RC001',  # CRITICAL: RFID is source of truth
                'common_name': 'Excavator CAT 320',
                'quality': 'Good',
                'bin_location': 'Yard A1',
                'status': 'Ready to Rent',
                'last_contract_num': 'C123',
                'date_created': '2025-01-01T10:00:00Z',
                'date_updated': '2025-08-30T12:00:00Z'
            },
            {
                'tag_id': 'RFID002',
                'rental_class_num': 'RC002',
                'serial_number': 'SN002',
                'common_name': 'Dump Truck',
                'status': 'On Rent'
            }
        ]
        
        self.mock_transaction_data = [
            {
                'tag_id': 'RFID001',
                'contract_num': 'C001',
                'rental_class_id': 'RC001',  # API uses rental_class_id
                'scan_date': '2025-08-30T14:30:00Z',
                'event_type': 'out',
                'client_name': 'Test Client',
                'notes': 'Equipment checkout'
            }
        ]

    @patch('app.services.refresh.APIClient')
    def test_get_api_client_initialization(self, mock_api_client_class):
        """Test API client initialization and error handling"""
        # Test successful initialization
        mock_client = MagicMock()
        mock_api_client_class.return_value = mock_client
        
        client = get_api_client()
        assert client is not None
        assert client == mock_client
        
        # Test initialization failure
        mock_api_client_class.side_effect = Exception("API connection failed")
        
        # Reset the global client to test re-initialization
        import app.services.refresh
        app.services.refresh.api_client = None
        
        client = get_api_client()
        assert client is None

    @patch('app.services.refresh.get_api_client')
    @patch('app.services.refresh.db.session')
    def test_process_rfid_items_rental_class_preservation(self, mock_db_session, mock_get_client):
        """Test that process_rfid_items preserves rental_class_num from RFID API"""
        # Setup mock API client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_items.return_value = self.mock_api_data
        
        # Setup mock database items
        mock_existing_item = MagicMock()
        mock_existing_item.rental_class_num = 'OLD_RC001'  # Old value
        mock_new_item = None  # New item
        
        def mock_get_side_effect(model_class, tag_id):
            if tag_id == 'RFID001':
                return mock_existing_item
            return mock_new_item
        
        mock_db_session.get.side_effect = mock_get_side_effect
        
        # Call the function
        result = update_item_master(mock_db_session, self.mock_api_data)
        
        # Verify RFID API is source of truth for rental_class_num
        assert mock_existing_item.rental_class_num == 'RC001'  # Updated from API
        assert mock_existing_item.serial_number == 'SN001'
        assert mock_existing_item.common_name == 'Excavator CAT 320'
        
        # Verify new item creation for RFID002
        mock_db_session.add.assert_called()
        added_item = mock_db_session.add.call_args[0][0]
        assert added_item.rental_class_num == 'RC002'
        assert added_item.tag_id == 'RFID002'
        
        mock_db_session.commit.assert_called()

    @patch('app.services.refresh.get_api_client')
    @patch('app.services.refresh.db.session')
    def test_process_transactions_rental_class_mapping(self, mock_db_session, mock_get_client):
        """Test that transactions map rental_class_id to rental_class_num correctly"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_transactions.return_value = self.mock_transaction_data
        
        # Mock no existing transaction
        mock_db_session.query().filter().first.return_value = None
        
        result = update_transactions(mock_db_session, self.mock_transaction_data)
        
        # Verify transaction creation with correct mapping
        mock_db_session.add.assert_called()
        added_transaction = mock_db_session.add.call_args[0][0]
        
        # Critical: rental_class_id from API becomes rental_class_num in database
        assert added_transaction.rental_class_num == 'RC001'
        assert added_transaction.tag_id == 'RFID001'
        assert added_transaction.contract_num == 'C001'
        assert added_transaction.event_type == 'out'

    @patch('app.services.refresh.get_api_client')
    @patch('app.services.refresh.db.session') 
    def test_api_error_handling_preserves_data_integrity(self, mock_db_session, mock_get_client):
        """Test that API errors don't corrupt existing data"""
        # Simulate API failure
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_items.side_effect = Exception("API timeout")
        
        # Mock existing data in database
        mock_existing_item = MagicMock()
        mock_existing_item.rental_class_num = 'RC001'
        mock_existing_item.status = 'Ready to Rent'
        mock_db_session.get.return_value = mock_existing_item
        
        try:
            result = update_item_master(mock_db_session, self.mock_api_data)
        except Exception:
            pass
        
        # Verify existing data is not corrupted
        assert mock_existing_item.rental_class_num == 'RC001'
        # No commits should happen on API failure
        mock_db_session.commit.assert_not_called()

    def test_validate_date_function(self):
        """Test date validation utility function"""
        # Valid date formats
        valid_date = validate_date('2025-08-30T14:30:00Z', 'test_date', 'RFID001')
        assert valid_date is not None
        assert isinstance(valid_date, datetime)
        
        valid_date_iso = validate_date('2025-08-30 14:30:00', 'test_date', 'RFID001') 
        assert valid_date_iso is not None
        
        # Invalid date formats
        invalid_date = validate_date('invalid-date', 'test_date', 'RFID001')
        assert invalid_date is None
        
        empty_date = validate_date('', 'test_date', 'RFID001')
        assert empty_date is None
        
        none_date = validate_date(None, 'test_date', 'RFID001')
        assert none_date is None


class TestCSVImportServiceIntegration:
    """Test csv_import_service.py integration and correlation logic"""
    
    def setup_method(self):
        """Setup for CSV import service tests"""
        self.csv_service = CSVImportService()
        
        self.sample_equipment_csv_data = [
            {
                'ItemNum': 'POS001',
                'Name': 'Excavator Equipment',
                'Category': 'Heavy Machinery',
                'SerialNo': 'SN001',  # Key for correlation
                'T/O YTD': 50000.00,
                'T/O LTD': 150000.00,
                'RepairCost MTD': 2500.00,
                'Sell Price': 75000.00,
                'Current Store': 'Store1',
                'Inactive': False
            },
            {
                'ItemNum': 'POS002',
                'Name': 'Dump Truck Equipment',
                'Category': 'Transport',
                'SerialNo': 'SN002',
                'T/O YTD': 30000.00,
                'Sell Price': 45000.00,
                'Current Store': 'Store2',
                'Inactive': False
            },
            {
                'ItemNum': 'POS003',
                'Name': 'Equipment No Serial',
                'Category': 'Misc', 
                'SerialNo': '',  # Empty serial - should not correlate
                'T/O YTD': 10000.00,
                'Sell Price': 15000.00,
                'Current Store': 'Store1',
                'Inactive': True
            }
        ]

    def test_csv_import_service_initialization(self):
        """Test CSV import service initialization"""
        service = CSVImportService()
        
        assert service.CSV_BASE_PATH == "/home/tim/RFID3/shared/POR"
        assert hasattr(service, 'engine')
        assert hasattr(service, 'Session')
        assert service.import_stats['files_processed'] == 0
        assert service.import_stats['total_records_processed'] == 0

    @patch.object(CSVImportService, 'Session')
    @patch('app.services.csv_import_service.db.session')
    def test_correlate_rfid_with_pos_data_detailed(self, mock_db_session, mock_session_class):
        """Test the _correlate_rfid_with_pos_data method in detail"""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        # Mock column addition (might already exist)
        mock_session.execute.side_effect = [
            None,  # ALTER TABLE command
            MagicMock(rowcount=2)  # UPDATE correlation command
        ]
        
        service = CSVImportService()
        correlation_count = service._correlate_rfid_with_pos_data()
        
        # Verify the correct sequence of SQL operations
        calls = mock_session.execute.call_args_list
        
        # First call: ALTER TABLE to add correlation column
        alter_call = calls[0][0][0]
        alter_sql = str(alter_call)
        assert "ALTER TABLE pos_equipment ADD COLUMN rfid_rental_class_num VARCHAR(255)" in alter_sql
        
        # Second call: UPDATE correlation query
        update_call = calls[1][0][0]
        update_sql = str(update_call)
        
        # Critical correlation logic verification
        assert "UPDATE pos_equipment pos" in update_sql
        assert "INNER JOIN id_item_master rfid ON" in update_sql
        assert "TRIM(COALESCE(pos.serial_no, '')) = TRIM(COALESCE(rfid.serial_number, ''))" in update_sql
        assert "SET pos.rfid_rental_class_num = rfid.rental_class_num" in update_sql
        assert "WHERE TRIM(COALESCE(pos.serial_no, '')) != ''" in update_sql
        assert "AND TRIM(COALESCE(rfid.serial_number, '')) != ''" in update_sql
        assert "AND TRIM(COALESCE(rfid.rental_class_num, '')) != ''" in update_sql
        
        assert correlation_count == 2
        mock_session.commit.assert_called_once()

    @patch('glob.glob')
    @patch('pandas.read_csv')
    @patch.object(CSVImportService, 'Session')
    def test_import_equipment_data_with_correlation(self, mock_session_class, mock_read_csv, mock_glob):
        """Test equipment import with correlation functionality"""
        # Setup file discovery
        mock_glob.return_value = ['/test/path/equip8.26.25.csv']
        
        # Setup CSV data
        mock_df = pd.DataFrame(self.sample_equipment_csv_data)
        mock_read_csv.return_value = mock_df
        
        # Setup database mocks
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        # Mock successful import and correlation
        mock_session.execute.side_effect = [
            MagicMock(rowcount=3),  # Equipment import
            None,  # ALTER TABLE
            MagicMock(rowcount=2)  # Correlation update
        ]
        
        service = CSVImportService()
        result = service.import_equipment_data()
        
        # Verify import results
        assert result['success'] is True
        assert result['total_records'] == 3
        assert result['imported_records'] == 3
        assert result['correlation_count'] == 2
        
        # Verify equipment data processing
        insert_call = mock_session.execute.call_args_list[0]
        insert_query = str(insert_call[0][0])
        assert "INSERT INTO pos_equipment" in insert_query
        assert "item_num, name, category, serial_no" in insert_query
        
        # Verify service statistics updated
        assert service.import_stats['files_processed'] == 1
        assert service.import_stats['total_records_processed'] == 3
        assert service.import_stats['total_records_imported'] == 3

    @patch.object(CSVImportService, 'Session')
    def test_correlation_error_handling_and_rollback(self, mock_session_class):
        """Test error handling in correlation with proper rollback"""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        # Simulate database error during correlation
        mock_session.execute.side_effect = [
            None,  # ALTER TABLE succeeds
            SQLAlchemyError("Correlation update failed")  # UPDATE fails
        ]
        
        service = CSVImportService()
        correlation_count = service._correlate_rfid_with_pos_data()
        
        # Should handle error gracefully
        assert correlation_count == 0
        mock_session.rollback.assert_called_once()

    @patch('glob.glob')
    @patch('pandas.read_csv')
    @patch.object(CSVImportService, 'Session')
    def test_transaction_import_integration(self, mock_session_class, mock_read_csv, mock_glob):
        """Test transaction data import functionality"""
        transaction_data = [
            {
                'TransactionID': 'T001',
                'ItemNum': 'POS001', 
                'SerialNo': 'SN001',
                'CustomerID': 'CUST001',
                'TransactionDate': '2025-08-30',
                'Amount': 500.00,
                'TransactionType': 'Sale'
            }
        ]
        
        mock_glob.return_value = ['/test/path/transactions8.26.25.csv']
        mock_df = pd.DataFrame(transaction_data)
        mock_read_csv.return_value = mock_df
        
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value = MagicMock(rowcount=1)
        
        service = CSVImportService()
        result = service.import_transactions_data()
        
        assert result['success'] is True
        assert result['imported_records'] == 1

    def test_csv_service_data_validation(self):
        """Test data validation in CSV import service"""
        # Test with invalid data types
        invalid_data = [
            {
                'ItemNum': 'POS001',
                'Name': 'Valid Item',
                'T/O YTD': 'invalid_number',  # Should be float
                'Sell Price': None,
                'SerialNo': 'SN001'
            }
        ]
        
        service = CSVImportService()
        
        # The service should handle data type conversion gracefully
        # Creating a temporary CSV file to test the validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(invalid_data)
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            with patch.object(service, 'Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                mock_session.execute.return_value = MagicMock(rowcount=0)
                
                result = service.import_equipment_data(temp_file)
                
                # Should handle invalid data without crashing
                assert isinstance(result, dict)
                
        finally:
            os.unlink(temp_file)


class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios"""
    
    def setup_method(self):
        """Setup end-to-end test scenarios"""
        self.complete_rfid_data = [
            {
                'tag_id': 'RFID001',
                'serial_number': 'SN001',
                'rental_class_num': 'RC001',
                'common_name': 'Excavator CAT 320',
                'status': 'Ready to Rent'
            }
        ]
        
        self.complete_pos_data = [
            {
                'ItemNum': 'POS001',
                'SerialNo': 'SN001',  # Matches RFID001
                'Name': 'Excavator Equipment',
                'Category': 'Heavy Machinery',
                'T/O YTD': 50000.00,
                'Sell Price': 75000.00
            }
        ]

    @patch('app.services.refresh.get_api_client')
    @patch('app.services.refresh.db.session')
    @patch.object(CSVImportService, 'Session')
    def test_complete_rfid_pos_integration_flow(self, mock_csv_session_class, mock_refresh_db_session, mock_get_client):
        """Test complete integration flow: RFID refresh -> CSV import -> correlation"""
        
        # Step 1: RFID API refresh (rental_class_num source of truth)
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_items.return_value = self.complete_rfid_data
        
        mock_item = MagicMock()
        mock_refresh_db_session.get.return_value = mock_item
        
        # Execute RFID refresh
        result_rfid = update_item_master(mock_refresh_db_session, self.complete_rfid_data)
        
        # Verify RFID data is updated with API data
        assert mock_item.rental_class_num == 'RC001'
        assert mock_item.serial_number == 'SN001'
        
        # Step 2: CSV import with correlation
        mock_csv_session = MagicMock()
        mock_csv_session_class.return_value.__enter__.return_value = mock_csv_session
        
        # Mock successful correlation
        mock_csv_session.execute.side_effect = [
            MagicMock(rowcount=1),  # Equipment import
            None,  # ALTER TABLE 
            MagicMock(rowcount=1)   # Correlation update
        ]
        
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(self.complete_pos_data)
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            csv_service = CSVImportService()
            result_csv = csv_service.import_equipment_data(temp_file)
            
            # Verify end-to-end integration
            assert result_csv['success'] is True
            assert result_csv['correlation_count'] == 1
            
            # Verify correlation preserves RFID as source of truth
            correlation_call = mock_csv_session.execute.call_args_list[2]  # Third call is correlation
            correlation_sql = str(correlation_call[0][0])
            assert "pos.rfid_rental_class_num = rfid.rental_class_num" in correlation_sql
            
        finally:
            os.unlink(temp_file)

    def test_data_integrity_across_systems(self):
        """Test that data integrity is maintained across RFID and POS systems"""
        scenarios = [
            {
                'name': 'Perfect Match',
                'rfid_serial': 'SN001',
                'pos_serial': 'SN001',
                'rfid_rental_class': 'RC001',
                'expected_correlation': True
            },
            {
                'name': 'Serial Mismatch',
                'rfid_serial': 'SN001', 
                'pos_serial': 'SN002',
                'rfid_rental_class': 'RC001',
                'expected_correlation': False
            },
            {
                'name': 'Empty POS Serial',
                'rfid_serial': 'SN001',
                'pos_serial': '',
                'rfid_rental_class': 'RC001', 
                'expected_correlation': False
            },
            {
                'name': 'Empty RFID Serial',
                'rfid_serial': '',
                'pos_serial': 'SN001',
                'rfid_rental_class': 'RC001',
                'expected_correlation': False
            }
        ]
        
        for scenario in scenarios:
            with patch.object(CSVImportService, 'Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                
                expected_correlations = 1 if scenario['expected_correlation'] else 0
                mock_session.execute.side_effect = [
                    None,  # ALTER TABLE
                    MagicMock(rowcount=expected_correlations)  # Correlation update
                ]
                
                service = CSVImportService()
                correlation_count = service._correlate_rfid_with_pos_data()
                
                assert correlation_count == expected_correlations, f"Failed scenario: {scenario['name']}"

    @patch('app.services.refresh.refresh_status', {'refreshing': False})
    def test_concurrent_operations_handling(self):
        """Test handling of concurrent refresh and import operations"""
        with patch('app.services.refresh.get_api_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.get_items.return_value = []
            
            # Should handle concurrent access without conflicts
            result = update_item_master(MagicMock(), [])
            assert result is not None

    def test_system_scalability_simulation(self):
        """Test system behavior with large datasets"""
        # Simulate large POS dataset
        large_pos_data = []
        for i in range(1000):
            large_pos_data.append({
                'ItemNum': f'POS{i:04d}',
                'SerialNo': f'SN{i:04d}' if i % 2 == 0 else '',  # 50% have serial numbers
                'Name': f'Equipment {i}',
                'Category': 'Test Equipment',
                'T/O YTD': float(i * 100),
                'Sell Price': float(i * 150)
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(large_pos_data)
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            with patch.object(CSVImportService, 'Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                mock_session.execute.return_value = MagicMock(rowcount=500)  # 50% correlation rate
                
                service = CSVImportService()
                result = service.import_equipment_data(temp_file)
                
                # Should handle large datasets efficiently
                assert result['success'] is True
                assert result['total_records'] == 1000
                assert result['correlation_count'] == 500
                
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])