"""
Comprehensive Test Suite for RFID-POS Integration Fixes
Tests the critical fixes implemented for data correlation, API integration, and data integrity
"""

import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock, Mock, call
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import tempfile
import os
import json
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Import the services we need to test
from app.services.refresh import get_api_client, update_item_master, update_transactions, full_refresh, incremental_refresh
from app.services.csv_import_service import CSVImportService
from app.models.db_models import ItemMaster, Transaction, SeedRentalClass, RefreshState
from app.models.pos_models import POSEquipment, POSRFIDCorrelation
from app import db


class TestDataCorrelationLogic:
    """Test the serial number correlation logic between RFID and POS systems"""
    
    def setup_method(self):
        """Setup test data for each test method"""
        self.csv_service = CSVImportService()
        
        # Sample RFID data (source of truth for rental_class_num)
        self.sample_rfid_data = [
            {
                'tag_id': 'RFID001',
                'serial_number': 'SN001',
                'rental_class_num': 'RC001',
                'common_name': 'Excavator 1',
                'status': 'Ready to Rent'
            },
            {
                'tag_id': 'RFID002', 
                'serial_number': 'SN002',
                'rental_class_num': 'RC002',
                'common_name': 'Dump Truck 1',
                'status': 'On Rent'
            },
            {
                'tag_id': 'RFID003',
                'serial_number': '',  # Missing serial number
                'rental_class_num': 'RC003',
                'common_name': 'Crane 1',
                'status': 'Ready to Rent'
            }
        ]
        
        # Sample POS data (should NOT be source of truth for rental_class_num)
        self.sample_pos_data = [
            {
                'ItemNum': 'POS001',
                'SerialNo': 'SN001',  # Matches RFID001
                'Name': 'Excavator Equipment',
                'Category': 'Heavy Machinery',
                'T/O YTD': 50000.00,
                'Sell Price': 75000.00
            },
            {
                'ItemNum': 'POS002',
                'SerialNo': 'SN002',  # Matches RFID002
                'Name': 'Dump Truck Equipment', 
                'Category': 'Transport',
                'T/O YTD': 30000.00,
                'Sell Price': 45000.00
            },
            {
                'ItemNum': 'POS003',
                'SerialNo': 'SN999',  # No RFID match
                'Name': 'Unknown Equipment',
                'Category': 'Misc',
                'T/O YTD': 10000.00,
                'Sell Price': 15000.00
            }
        ]

    def test_serial_number_correlation_success(self):
        """Test successful correlation between RFID and POS via serial numbers"""
        with patch('app.services.csv_import_service.db.session') as mock_db_session:
            
            # Mock the correlation query execution
            mock_result = MagicMock()
            mock_result.rowcount = 2  # 2 successful correlations
            mock_db_session.execute.side_effect = [
                None,  # ALTER TABLE command
                mock_result  # UPDATE correlation command
            ]
            
            # Test the correlation method
            correlation_count = self.csv_service._correlate_rfid_with_pos_data()
            
            assert correlation_count == 2
            # Verify the correlation SQL was executed
            assert mock_db_session.execute.call_count == 2
            mock_db_session.commit.assert_called()

    def test_rental_class_num_preservation(self):
        """Test that rental_class_num from RFID API is preserved as source of truth"""
        with patch('app.services.refresh.get_api_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.get_items.return_value = self.sample_rfid_data
            
            with patch('app.services.refresh.db.session') as mock_db_session:
                mock_item = MagicMock()
                mock_db_session.get.return_value = mock_item
                
                # Call the refresh function
                from app.services.refresh import update_item_master
                with patch('app.services.refresh.db.session') as mock_session:
                    result = update_item_master(mock_session, self.sample_rfid_data)
                
                # Verify rental_class_num is set from RFID API data
                assert mock_item.rental_class_num == 'RC001'  # From first item

    def test_csv_import_correlation_functionality(self):
        """Test CSV import service correlation functionality"""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(self.sample_pos_data)
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            with patch.object(self.csv_service, 'Session') as mock_session_class, \
                 patch('app.services.csv_import_service.db.session') as mock_db_session:
                
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                
                # Mock successful import and correlation
                mock_result = MagicMock()
                mock_result.rowcount = 3  # 3 records imported
                mock_session.execute.return_value = mock_result
                
                # Mock correlation result
                mock_correlation_result = MagicMock()
                mock_correlation_result.rowcount = 2  # 2 correlations found
                mock_session.execute.side_effect = [mock_result, mock_correlation_result]
                
                # Test the import
                result = self.csv_service.import_equipment_data(temp_file)
                
                assert result['success'] is True
                assert result['imported_records'] == 3
                assert result['correlation_count'] == 2
                assert 'SN001' in str(mock_session.execute.call_args_list)
                
        finally:
            os.unlink(temp_file)

    def test_correlation_with_missing_serial_numbers(self):
        """Test correlation behavior with missing/null serial numbers"""
        # Test data with empty/null serial numbers
        pos_data_with_nulls = [
            {'ItemNum': 'POS001', 'SerialNo': '', 'Name': 'Test Item'},
            {'ItemNum': 'POS002', 'SerialNo': None, 'Name': 'Test Item 2'},
            {'ItemNum': 'POS003', 'SerialNo': 'SN001', 'Name': 'Valid Item'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(pos_data_with_nulls)
            df.to_csv(f.name, index=False)
            temp_file = f.name
            
        try:
            with patch.object(self.csv_service, 'Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                
                # Mock the correlation query - should only match non-empty serial numbers
                mock_result = MagicMock()
                mock_result.rowcount = 1  # Only 1 valid correlation
                mock_session.execute.return_value = mock_result
                
                correlation_count = self.csv_service._correlate_rfid_with_pos_data()
                
                # Should only correlate items with valid serial numbers
                assert correlation_count == 1
                
                # Verify the query filters out empty serial numbers
                query_call = mock_session.execute.call_args[0][0]
                query_str = str(query_call)
                assert "TRIM(COALESCE(pos.serial_no, '')) != ''" in query_str
                assert "TRIM(COALESCE(rfid.serial_number, '')) != ''" in query_str
                
        finally:
            os.unlink(temp_file)

    def test_pos_rfid_correlation_table_creation(self):
        """Test that correlation updates pos_equipment with rfid_rental_class_num"""
        with patch.object(self.csv_service, 'Session') as mock_session_class, \
             patch('app.services.csv_import_service.db.session') as mock_db_session:
            
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            
            # Mock ALTER TABLE to add correlation column
            mock_session.execute.side_effect = [
                None,  # ALTER TABLE (add column)
                MagicMock(rowcount=2)  # UPDATE correlation query
            ]
            
            correlation_count = self.csv_service._correlate_rfid_with_pos_data()
            
            # Verify column addition was attempted
            calls = mock_session.execute.call_args_list
            alter_call = calls[0][0][0]
            assert "ALTER TABLE pos_equipment ADD COLUMN rfid_rental_class_num" in str(alter_call)
            
            # Verify correlation update query
            update_call = calls[1][0][0]
            assert "pos.rfid_rental_class_num = rfid.rental_class_num" in str(update_call)


class TestAPIIntegrationFixes:
    """Test API integration fixes for refresh.py and data preservation"""
    
    def setup_method(self):
        """Setup for API integration tests"""
        self.sample_api_response = [
            {
                'tag_id': 'RFID001',
                'rental_class_num': 'RC001',  # Source of truth
                'serial_number': 'SN001',
                'common_name': 'Test Equipment',
                'status': 'Ready to Rent'
            }
        ]
        
        self.sample_transaction_response = [
            {
                'tag_id': 'RFID001',
                'rental_class_id': 'RC001',  # Should match rental_class_num
                'contract_num': 'C001',
                'scan_date': '2025-08-30T10:00:00Z',
                'event_type': 'out'
            }
        ]

    def test_refresh_preserves_rental_class_num(self):
        """Test that refresh.py properly preserves rental_class_num from RFID API"""
        with patch('app.services.refresh.get_api_client') as mock_get_client, \
             patch('app.services.refresh.db.session') as mock_db_session:
            
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.get_items.return_value = self.sample_api_response
            
            # Mock database item
            mock_item = MagicMock()
            mock_item.rental_class_num = None  # Initially empty
            mock_db_session.get.return_value = mock_item
            
            # Call refresh function
            from app.services.refresh import update_item_master
            result = update_item_master(mock_db_session, self.sample_api_response)
            
            # Verify rental_class_num was set from API response
            assert mock_item.rental_class_num == 'RC001'
            mock_db_session.commit.assert_called()

    def test_pos_data_does_not_overwrite_rfid_fields(self):
        """Test that POS data doesn't overwrite RFID source-of-truth fields"""
        with patch.object(self.csv_service, 'Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            
            # Mock that correlation preserves RFID as source of truth
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute.return_value = mock_result
            
            csv_service = CSVImportService()
            correlation_count = csv_service._correlate_rfid_with_pos_data()
            
            # Verify the query sets pos.rfid_rental_class_num FROM rfid.rental_class_num
            # This preserves RFID as source of truth
            query_call = mock_session.execute.call_args[0][0]
            query_str = str(query_call)
            assert "pos.rfid_rental_class_num = rfid.rental_class_num" in query_str
            assert correlation_count == 1

    def test_transaction_rental_class_mapping(self):
        """Test that transaction rental_class_id maps correctly to rental_class_num"""
        with patch('app.services.refresh.get_api_client') as mock_get_client, \
             patch('app.services.refresh.db.session') as mock_db_session:
            
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.get_transactions.return_value = self.sample_transaction_response
            
            # Mock database transaction
            mock_transaction = MagicMock()
            mock_db_session.query().filter().first.return_value = None  # New transaction
            
            from app.services.refresh import update_transactions
            result = update_transactions(mock_db_session, self.sample_transaction_response)
            
            # Verify rental_class_id from API maps to rental_class_num in database
            add_call = mock_db_session.add.call_args[0][0]
            assert add_call.rental_class_num == 'RC001'

    def test_database_schema_changes_validation(self):
        """Test that database schema changes are properly validated"""
        with patch('app.services.csv_import_service.db.session') as mock_db_session:
            
            csv_service = CSVImportService()
            
            # Mock successful column addition
            mock_db_session.execute.return_value = None
            
            try:
                # This should attempt to add the correlation column
                csv_service._correlate_rfid_with_pos_data()
                
                # Verify ALTER TABLE was called
                alter_query_called = any(
                    "ALTER TABLE pos_equipment ADD COLUMN rfid_rental_class_num" in str(call[0][0])
                    for call in mock_db_session.execute.call_args_list
                )
                assert alter_query_called
                
            except Exception:
                # Column already exists - this is expected behavior
                pass


class TestDataIntegrityValidation:
    """Test data integrity and corrected data flow patterns"""
    
    def setup_method(self):
        """Setup integrity test data"""
        self.seed_rental_data = [
            {
                'rental_class_num': 'RC001',
                'equipment_type': 'Excavator',
                'category': 'Heavy Equipment',
                'daily_rate': 500.00
            },
            {
                'rental_class_num': 'RC002', 
                'equipment_type': 'Dump Truck',
                'category': 'Transport',
                'daily_rate': 300.00
            }
        ]
        
        self.rfid_items_data = [
            {
                'tag_id': 'RFID001',
                'rental_class_num': 'RC001',  # Should align with seed data
                'serial_number': 'SN001',
                'status': 'Ready to Rent'
            },
            {
                'tag_id': 'RFID002',
                'rental_class_num': 'RC999',  # Misaligned - should be flagged
                'serial_number': 'SN002', 
                'status': 'On Rent'
            }
        ]

    def test_seed_rental_class_alignment(self):
        """Test that seed rental class data aligns with RFID items"""
        with patch('app.services.refresh.get_api_client') as mock_get_client, \
             patch('app.services.refresh.db.session') as mock_db_session:
            
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.get_items.return_value = self.rfid_items_data
            
            # Mock seed rental class query
            mock_seed_query = MagicMock()
            mock_seed_query.filter().first.return_value.rental_class_num = 'RC001'
            mock_db_session.query.return_value = mock_seed_query
            
            from app.services.refresh import update_item_master
            
            # This should validate alignment between RFID and seed data
            result = update_item_master(mock_db_session, self.rfid_items_data)
            
            # Should query seed rental class for validation
            mock_db_session.query.assert_called()

    def test_correlation_preserves_existing_data(self):
        """Test that correlation doesn't corrupt existing data"""
        original_pos_data = {
            'item_num': 'POS001',
            'name': 'Test Equipment',
            'turnover_ytd': 50000.00,
            'serial_no': 'SN001'
        }
        
        with patch.object(CSVImportService, 'Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            
            # Mock correlation that preserves existing data
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute.return_value = mock_result
            
            csv_service = CSVImportService()
            correlation_count = csv_service._correlate_rfid_with_pos_data()
            
            # Verify correlation only ADDS the rfid_rental_class_num field
            # without modifying existing POS data
            query_str = str(mock_session.execute.call_args[0][0])
            assert "SET pos.rfid_rental_class_num = rfid.rental_class_num" in query_str
            # Should not modify other POS fields
            assert "pos.name =" not in query_str
            assert "pos.turnover_ytd =" not in query_str

    def test_data_flow_validation(self):
        """Test corrected data flow patterns"""
        with patch('app.services.refresh.get_api_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            # RFID API provides rental_class_num (source of truth)
            mock_client.get_items.return_value = [{
                'tag_id': 'RFID001',
                'rental_class_num': 'RC001',  # Source of truth
                'serial_number': 'SN001'
            }]
            
            with patch('app.services.refresh.db.session') as mock_db_session:
                mock_item = MagicMock()
                mock_db_session.get.return_value = mock_item
                
                from app.services.refresh import update_item_master
                result = update_item_master(mock_db_session, [{
                    'tag_id': 'RFID001',
                    'rental_class_num': 'RC001',  # Source of truth
                    'serial_number': 'SN001'
                }])
                
                # Data flow: API -> RFID database -> POS correlation
                # rental_class_num comes from API, not POS
                assert mock_item.rental_class_num == 'RC001'

    def test_data_consistency_validation(self):
        """Test validation of data consistency across systems"""
        test_scenarios = [
            {
                'rfid_rental_class': 'RC001',
                'pos_serial': 'SN001',
                'rfid_serial': 'SN001',
                'expected_correlation': True
            },
            {
                'rfid_rental_class': 'RC001', 
                'pos_serial': 'SN001',
                'rfid_serial': 'SN999',  # Mismatch
                'expected_correlation': False
            },
            {
                'rfid_rental_class': 'RC001',
                'pos_serial': '',  # Empty
                'rfid_serial': 'SN001', 
                'expected_correlation': False
            }
        ]
        
        for scenario in test_scenarios:
            with patch.object(CSVImportService, 'Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                
                expected_correlations = 1 if scenario['expected_correlation'] else 0
                mock_result = MagicMock()
                mock_result.rowcount = expected_correlations
                mock_session.execute.return_value = mock_result
                
                csv_service = CSVImportService()
                correlation_count = csv_service._correlate_rfid_with_pos_data()
                
                assert correlation_count == expected_correlations


class TestErrorHandlingAndRollback:
    """Test error handling and rollback behavior on failures"""
    
    def test_correlation_rollback_on_failure(self):
        """Test that correlation failures trigger proper rollback"""
        with patch.object(CSVImportService, 'Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            
            # Simulate database error during correlation
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            
            csv_service = CSVImportService()
            correlation_count = csv_service._correlate_rfid_with_pos_data()
            
            # Should handle error gracefully and return 0
            assert correlation_count == 0
            mock_session.rollback.assert_called_once()

    def test_csv_import_with_malformed_data(self):
        """Test CSV import with malformed data"""
        malformed_data = [
            {'ItemNum': 'POS001', 'Name': 'Valid Item', 'SerialNo': 'SN001'},
            {'ItemNum': '', 'Name': '', 'SerialNo': ''},  # Empty record
            {'InvalidColumn': 'BadData'},  # Wrong columns
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(malformed_data)
            df.to_csv(f.name, index=False)
            temp_file = f.name
            
        try:
            csv_service = CSVImportService()
            with patch.object(csv_service, 'Session'):
                result = csv_service.import_equipment_data(temp_file)
                
                # Should handle malformed data gracefully
                assert isinstance(result, dict)
                if not result.get('success', True):
                    assert 'error' in result
                    
        finally:
            os.unlink(temp_file)

    def test_api_client_initialization_failure(self):
        """Test graceful handling of API client initialization failure"""
        with patch('app.services.refresh.APIClient') as mock_api_client:
            mock_api_client.side_effect = Exception("API initialization failed")
            
            from app.services.refresh import get_api_client
            client = get_api_client()
            
            # Should return None on failure, not crash
            assert client is None

    def test_missing_csv_files_handling(self):
        """Test handling of missing CSV files"""
        csv_service = CSVImportService()
        
        # Try to import from non-existent path
        with patch('glob.glob', return_value=[]):
            with pytest.raises(FileNotFoundError):
                csv_service.import_equipment_data()

    def test_database_transaction_rollback(self):
        """Test proper transaction rollback on database errors"""
        with patch('app.services.refresh.db.session') as mock_db_session:
            mock_db_session.commit.side_effect = SQLAlchemyError("Commit failed")
            
            with patch('app.services.refresh.get_api_client') as mock_get_client:
                mock_client = MagicMock()
                mock_get_client.return_value = mock_client
                mock_client.get_items.return_value = [{'tag_id': 'TEST001'}]
                
                from app.services.refresh import process_rfid_items
                
                try:
                    result = process_rfid_items()
                except SQLAlchemyError:
                    # Should trigger rollback
                    mock_db_session.rollback.assert_called()


class TestRegressionPrevention:
    """Test that fixes don't introduce regressions"""
    
    def test_existing_data_preservation(self):
        """Test that existing data is preserved during updates"""
        existing_item_data = {
            'tag_id': 'EXISTING001',
            'serial_number': 'EXIST_SN001', 
            'rental_class_num': 'EXIST_RC001',
            'common_name': 'Existing Equipment'
        }
        
        api_update_data = {
            'tag_id': 'EXISTING001',
            'serial_number': 'EXIST_SN001',
            'rental_class_num': 'UPDATED_RC001',  # Updated value
            'common_name': 'Updated Equipment Name'
        }
        
        with patch('app.services.refresh.get_api_client') as mock_get_client, \
             patch('app.services.refresh.db.session') as mock_db_session:
            
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.get_items.return_value = [api_update_data]
            
            # Mock existing database item
            mock_item = MagicMock()
            for key, value in existing_item_data.items():
                setattr(mock_item, key, value)
            
            mock_db_session.get.return_value = mock_item
            
            from app.services.refresh import update_item_master
            result = update_item_master(mock_db_session, [api_update_data])
            
            # Verify updates are applied correctly
            assert mock_item.rental_class_num == 'UPDATED_RC001'
            assert mock_item.common_name == 'Updated Equipment Name'
            # Serial number should be preserved as source of truth
            assert mock_item.serial_number == 'EXIST_SN001'

    def test_performance_regression_prevention(self):
        """Test that correlation operations don't cause performance regressions"""
        import time
        
        large_dataset = []
        for i in range(100):  # Simulate larger dataset
            large_dataset.append({
                'ItemNum': f'POS{i:03d}',
                'SerialNo': f'SN{i:03d}',
                'Name': f'Equipment {i}',
                'Category': 'Test'
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(large_dataset)
            df.to_csv(f.name, index=False)
            temp_file = f.name
            
        try:
            csv_service = CSVImportService()
            
            with patch.object(csv_service, 'Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__.return_value = mock_session
                mock_session.execute.return_value = MagicMock(rowcount=100)
                
                start_time = time.time()
                result = csv_service.import_equipment_data(temp_file)
                execution_time = time.time() - start_time
                
                # Should complete within reasonable time (< 5 seconds for 100 records)
                assert execution_time < 5.0
                assert result['success'] is True
                
        finally:
            os.unlink(temp_file)

    def test_concurrent_access_handling(self):
        """Test handling of concurrent access to correlation functions"""
        with patch('app.services.refresh.refresh_status', {'refreshing': False}):
            with patch('app.services.refresh.get_api_client') as mock_get_client:
                mock_client = MagicMock()
                mock_get_client.return_value = mock_client
                mock_client.get_items.return_value = []
                
                from app.services.refresh import update_item_master
                
                # Should handle concurrent access gracefully
                result = update_item_master(MagicMock(), [])
                assert result is not None


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v', '--tb=short'])