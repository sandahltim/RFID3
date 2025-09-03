"""
Comprehensive tests for DataReconciliationService
Tests revenue, utilization, and inventory reconciliation methods
Created: September 3, 2025
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.data_reconciliation_service import DataReconciliationService


class TestDataReconciliationService:
    """Test suite for DataReconciliationService"""
    
    @pytest.fixture
    def service(self):
        """Create a DataReconciliationService instance for testing"""
        with patch('app.services.data_reconciliation_service.FinancialAnalyticsService'):
            return DataReconciliationService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = MagicMock()
        return mock_session
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial revenue data"""
        return {
            'total': Decimal('125000.00'),
            'last_updated': '2025-09-01T10:30:00',
            'store_breakdown': {
                'STORE01': Decimal('50000.00'),
                'STORE02': Decimal('75000.00')
            }
        }
    
    @pytest.fixture
    def sample_pos_data(self):
        """Sample POS revenue data"""
        return {
            'total': Decimal('122500.00'),
            'last_updated': '2025-09-01T11:00:00',
            'transaction_count': 450,
            'store_breakdown': {
                'STORE01': Decimal('48000.00'),
                'STORE02': Decimal('74500.00')
            }
        }
    
    @pytest.fixture
    def sample_rfid_data(self):
        """Sample RFID revenue data with limited coverage"""
        return {
            'total': Decimal('2450.00'),  # Only 1.78% coverage
            'last_updated': '2025-09-01T08:15:00',
            'correlated_items': 290,
            'total_items': 16259
        }
    
    @pytest.fixture
    def mock_db_queries(self, mock_db_session):
        """Mock database queries for testing"""
        with patch('app.services.data_reconciliation_service.db.session', mock_db_session):
            yield mock_db_session

    # Revenue Reconciliation Tests
    
    def test_get_revenue_reconciliation_success(self, service, sample_financial_data, sample_pos_data, sample_rfid_data):
        """Test successful revenue reconciliation with all data sources"""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        with patch.object(service, '_get_financial_revenue', return_value=sample_financial_data):
            with patch.object(service, '_get_pos_revenue', return_value=sample_pos_data):
                with patch.object(service, '_get_rfid_revenue', return_value=sample_rfid_data):
                    
                    result = service.get_revenue_reconciliation(start_date, end_date, 'STORE01')
                    
                    # Verify structure
                    assert 'period' in result
                    assert 'revenue_sources' in result
                    assert 'variance_analysis' in result
                    
                    # Verify period data
                    assert result['period']['start_date'] == start_date.isoformat()
                    assert result['period']['end_date'] == end_date.isoformat()
                    assert result['period']['store_code'] == 'STORE01'
                    
                    # Verify revenue sources
                    sources = result['revenue_sources']
                    assert sources['financial_system']['value'] == sample_financial_data['total']
                    assert sources['pos_transactions']['value'] == sample_pos_data['total']
                    assert sources['rfid_correlation']['value'] == sample_rfid_data['total']
                    
                    # Verify confidence levels
                    assert sources['financial_system']['confidence'] == 'high'
                    assert sources['pos_transactions']['confidence'] == 'high'
                    assert sources['rfid_correlation']['confidence'] == 'low'
                    
                    # Verify RFID coverage limitation
                    assert '1.78%' in sources['rfid_correlation']['coverage']
    
    def test_get_revenue_reconciliation_default_dates(self, service, sample_financial_data, sample_pos_data, sample_rfid_data):
        """Test revenue reconciliation with default dates"""
        with patch.object(service, '_get_financial_revenue', return_value=sample_financial_data):
            with patch.object(service, '_get_pos_revenue', return_value=sample_pos_data):
                with patch.object(service, '_get_rfid_revenue', return_value=sample_rfid_data):
                    
                    result = service.get_revenue_reconciliation()
                    
                    # Should use default 7-day period
                    expected_start = date.today() - timedelta(days=7)
                    expected_end = date.today()
                    
                    assert result['period']['start_date'] == expected_start.isoformat()
                    assert result['period']['end_date'] == expected_end.isoformat()
                    assert result['period']['days'] == 8
    
    def test_revenue_variance_calculation(self, service, sample_financial_data, sample_pos_data, sample_rfid_data):
        """Test variance calculation accuracy"""
        # Modify test data for specific variance testing
        financial_data = sample_financial_data.copy()
        pos_data = sample_pos_data.copy()
        financial_data['total'] = Decimal('100000.00')
        pos_data['total'] = Decimal('102000.00')  # 2% higher
        
        with patch.object(service, '_get_financial_revenue', return_value=financial_data):
            with patch.object(service, '_get_pos_revenue', return_value=pos_data):
                with patch.object(service, '_get_rfid_revenue', return_value=sample_rfid_data):
                    
                    result = service.get_revenue_reconciliation()
                    variance = result['variance_analysis']['pos_vs_financial']
                    
                    assert variance['absolute'] == Decimal('2000.00')
                    assert variance['percentage'] == 2.0
                    assert variance['status'] in ['acceptable', 'minor']
    
    def test_revenue_reconciliation_error_handling(self, service):
        """Test error handling in revenue reconciliation"""
        with patch.object(service, '_get_financial_revenue', side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                service.get_revenue_reconciliation()
    
    # Utilization Reconciliation Tests
    
    def test_get_utilization_reconciliation_success(self, service):
        """Test successful utilization reconciliation"""
        pos_util_data = {
            'total_equipment': 1500,
            'on_rent_count': 1200,
            'utilization_rate': 80.0,
            'last_updated': '2025-09-01T12:00:00'
        }
        
        rfid_util_data = {
            'tracked_equipment': 267,  # 1.78% of 1500
            'on_rent_tracked': 195,
            'utilization_rate': 73.0,
            'last_updated': '2025-09-01T08:00:00'
        }
        
        estimated_util_data = {
            'methodology': 'historical_trending',
            'estimated_rate': 78.5,
            'confidence': 85
        }
        
        with patch.object(service, '_get_pos_utilization', return_value=pos_util_data):
            with patch.object(service, '_get_rfid_utilization', return_value=rfid_util_data):
                with patch.object(service, '_get_estimated_utilization', return_value=estimated_util_data):
                    
                    result = service.get_utilization_reconciliation('STORE01')
                    
                    # Verify structure
                    assert 'utilization_sources' in result
                    assert 'variance_analysis' in result
                    assert 'recommendations' in result
                    
                    # Verify POS data
                    pos_source = result['utilization_sources']['pos_system']
                    assert pos_source['utilization_rate'] == 80.0
                    assert pos_source['confidence'] == 'high'
                    assert pos_source['coverage'] == '100%'
                    
                    # Verify RFID data limitations
                    rfid_source = result['utilization_sources']['rfid_tracking']
                    assert rfid_source['utilization_rate'] == 73.0
                    assert rfid_source['confidence'] == 'low'
                    assert '1.78%' in rfid_source['coverage']
    
    def test_utilization_variance_analysis(self, service):
        """Test utilization variance calculation"""
        pos_util_data = {'utilization_rate': 80.0, 'total_equipment': 1500, 'on_rent_count': 1200}
        rfid_util_data = {'utilization_rate': 75.0, 'tracked_equipment': 300, 'on_rent_tracked': 225}
        estimated_util_data = {'estimated_rate': 78.0, 'confidence': 85}
        
        with patch.object(service, '_get_pos_utilization', return_value=pos_util_data):
            with patch.object(service, '_get_rfid_utilization', return_value=rfid_util_data):
                with patch.object(service, '_get_estimated_utilization', return_value=estimated_util_data):
                    
                    result = service.get_utilization_reconciliation()
                    variance = result['variance_analysis']['rfid_vs_pos']
                    
                    assert variance['absolute'] == -5.0
                    assert variance['percentage'] == -6.25  # (75-80)/80 * 100
                    assert 'low_rfid_coverage' in variance['likely_causes']
    
    # Inventory Reconciliation Tests
    
    def test_get_inventory_reconciliation_success(self, service):
        """Test successful inventory reconciliation"""
        mock_query_result = [
            {
                'category': 'Power Tools',
                'pos_count': 500,
                'rfid_count': 8,  # Very limited RFID coverage
                'variance': -492,
                'variance_pct': -98.4
            },
            {
                'category': 'Generators', 
                'pos_count': 150,
                'rfid_count': 3,
                'variance': -147,
                'variance_pct': -98.0
            }
        ]
        
        with patch('app.services.data_reconciliation_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = mock_query_result
            
            result = service.get_inventory_reconciliation('Power Tools')
            
            # Verify structure
            assert 'category_filter' in result
            assert 'inventory_comparison' in result
            assert 'coverage_analysis' in result
            assert 'recommendations' in result
            
            # Verify coverage analysis highlights RFID limitations
            coverage = result['coverage_analysis']
            assert coverage['total_pos_items'] > 0
            assert coverage['rfid_correlated_items'] < coverage['total_pos_items']
            assert coverage['correlation_percentage'] < 5  # Very low correlation
            
            # Verify recommendations address low coverage
            recommendations = result['recommendations']
            assert any('expand RFID tagging' in rec.lower() for rec in recommendations)
    
    def test_inventory_reconciliation_no_category_filter(self, service):
        """Test inventory reconciliation without category filter"""
        mock_query_result = [
            {'category': 'All Categories', 'pos_count': 16259, 'rfid_count': 290, 'variance': -15969, 'variance_pct': -98.22}
        ]
        
        with patch('app.services.data_reconciliation_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = mock_query_result
            
            result = service.get_inventory_reconciliation()
            
            assert result['category_filter'] == 'all'
            # Should reflect the actual 1.78% correlation rate
            coverage = result['coverage_analysis']
            assert abs(coverage['correlation_percentage'] - 1.78) < 0.1
    
    # Comprehensive Reconciliation Report Tests
    
    def test_get_comprehensive_reconciliation_report(self, service):
        """Test comprehensive reconciliation report generation"""
        # Mock all sub-methods
        revenue_data = {'variance_analysis': {'pos_vs_financial': {'status': 'acceptable'}}}
        utilization_data = {'variance_analysis': {'rfid_vs_pos': {'status': 'significant'}}}
        inventory_data = {'coverage_analysis': {'correlation_percentage': 1.78}}
        
        with patch.object(service, 'get_revenue_reconciliation', return_value=revenue_data):
            with patch.object(service, 'get_utilization_reconciliation', return_value=utilization_data):
                with patch.object(service, 'get_inventory_reconciliation', return_value=inventory_data):
                    
                    result = service.get_comprehensive_reconciliation_report()
                    
                    # Verify structure
                    assert 'summary' in result
                    assert 'detailed_reconciliation' in result
                    assert 'data_quality_score' in result
                    assert 'action_items' in result
                    
                    # Verify summary reflects RFID coverage limitations
                    summary = result['summary']
                    assert summary['rfid_coverage_rate'] == 1.78
                    assert summary['data_confidence'] == 'mixed'
                    
                    # Verify action items address coverage gaps
                    action_items = result['action_items']
                    assert len(action_items) > 0
                    assert any('RFID' in item.lower() for item in action_items)
    
    # Helper Method Tests
    
    def test_get_variance_status(self, service):
        """Test variance status classification"""
        assert service._get_variance_status(0.5) == 'excellent'
        assert service._get_variance_status(3.5) == 'good'
        assert service._get_variance_status(7.5) == 'acceptable'
        assert service._get_variance_status(12.5) == 'needs_attention'
    
    def test_get_discrepancy_severity(self, service):
        """Test discrepancy severity classification"""
        assert service._get_discrepancy_severity(1.0) == 'minor'
        assert service._get_discrepancy_severity(8.0) == 'moderate'
        assert service._get_discrepancy_severity(15.0) == 'major'
        assert service._get_discrepancy_severity(25.0) == 'major'
        assert service._get_discrepancy_severity(None) == 'no_rfid_data'
    
    # Revenue Source Method Tests
    
    @patch('app.services.data_reconciliation_service.db.session')
    def test_get_financial_revenue(self, mock_db, service):
        """Test financial revenue data retrieval"""
        mock_result = [
            {'week_date': '2025-08-25', 'store': 'STORE01', 'target_rent': 25000, 'actual_rent': 24500},
            {'week_date': '2025-09-01', 'store': 'STORE01', 'target_rent': 26000, 'actual_rent': 25800}
        ]
        mock_db.execute.return_value.fetchall.return_value = mock_result
        
        start_date = date(2025, 8, 25)
        end_date = date(2025, 9, 1)
        
        result = service._get_financial_revenue(start_date, end_date, 'STORE01')
        
        assert isinstance(result['total'], Decimal)
        assert result['total'] > 0
        assert 'last_updated' in result
    
    @patch('app.services.data_reconciliation_service.db.session')
    def test_get_pos_revenue(self, mock_db, service):
        """Test POS revenue data retrieval"""
        mock_result = [{'total_revenue': 50300.00, 'last_transaction': '2025-09-01 15:30:00'}]
        mock_db.execute.return_value.fetchone.return_value = mock_result[0]
        
        start_date = date(2025, 8, 25)
        end_date = date(2025, 9, 1)
        
        result = service._get_pos_revenue(start_date, end_date, 'STORE01')
        
        assert result['total'] == Decimal('50300.00')
        assert 'last_updated' in result
    
    @patch('app.services.data_reconciliation_service.db.session')
    def test_get_rfid_revenue_limited_coverage(self, mock_db, service):
        """Test RFID revenue calculation with limited coverage"""
        # Mock the combined inventory view with realistic RFID correlation data
        mock_result = [
            {'estimated_revenue': 1250.00, 'correlated_items': 145},
            {'estimated_revenue': 980.00, 'correlated_items': 89},
            {'estimated_revenue': 670.00, 'correlated_items': 56}
        ]
        mock_db.execute.return_value.fetchall.return_value = mock_result
        
        start_date = date(2025, 8, 25)
        end_date = date(2025, 9, 1)
        
        result = service._get_rfid_revenue(start_date, end_date, None)
        
        # Should reflect limited RFID coverage
        assert result['total'] == Decimal('2900.00')
        assert result['correlated_items'] == 290
        assert 'last_updated' in result
    
    # Utilization Helper Method Tests
    
    @patch('app.services.data_reconciliation_service.db.session')
    def test_get_pos_utilization(self, mock_db, service):
        """Test POS utilization calculation"""
        mock_result = {'total_equipment': 1500, 'on_rent': 1200, 'last_scan': '2025-09-01 14:00:00'}
        mock_db.execute.return_value.fetchone.return_value = mock_result
        
        result = service._get_pos_utilization('STORE01')
        
        assert result['total_equipment'] == 1500
        assert result['on_rent_count'] == 1200
        assert result['utilization_rate'] == 80.0  # 1200/1500 * 100
        assert 'last_updated' in result
    
    @patch('app.services.data_reconciliation_service.db.session')
    def test_get_rfid_utilization(self, mock_db, service):
        """Test RFID utilization with limited tracking"""
        mock_result = {'tracked_items': 267, 'on_rent_tracked': 195, 'last_scan': '2025-09-01 08:30:00'}
        mock_db.execute.return_value.fetchone.return_value = mock_result
        
        result = service._get_rfid_utilization('STORE01')
        
        assert result['tracked_equipment'] == 267
        assert result['on_rent_tracked'] == 195
        assert result['utilization_rate'] == 73.03  # 195/267 * 100
        assert 'last_updated' in result
    
    # Error Handling Tests
    
    def test_database_connection_error(self, service):
        """Test handling of database connection errors"""
        with patch('app.services.data_reconciliation_service.db.session') as mock_db:
            mock_db.execute.side_effect = Exception("Connection timeout")
            
            with pytest.raises(Exception):
                service.get_revenue_reconciliation()
    
    def test_empty_data_handling(self, service):
        """Test handling of empty datasets"""
        with patch.object(service, '_get_financial_revenue', return_value={'total': Decimal('0'), 'last_updated': None}):
            with patch.object(service, '_get_pos_revenue', return_value={'total': Decimal('0'), 'last_updated': None}):
                with patch.object(service, '_get_rfid_revenue', return_value={'total': Decimal('0'), 'last_updated': None}):
                    
                    result = service.get_revenue_reconciliation()
                    
                    # Should handle zero values gracefully
                    assert result['revenue_sources']['financial_system']['value'] == Decimal('0')
                    assert result['variance_analysis']['pos_vs_financial']['percentage'] == 0
    
    # Integration Tests with Real Data Patterns
    
    def test_realistic_rfid_coverage_scenario(self, service):
        """Test with realistic RFID coverage data (1.78%)"""
        # Simulate real system state: 290 RFID items out of 16,259 total
        financial_data = {'total': Decimal('125000.00'), 'last_updated': '2025-09-01T10:00:00'}
        pos_data = {'total': Decimal('123500.00'), 'last_updated': '2025-09-01T11:00:00'}
        rfid_data = {'total': Decimal('2195.50'), 'last_updated': '2025-09-01T08:00:00'}  # ~1.78% of POS
        
        with patch.object(service, '_get_financial_revenue', return_value=financial_data):
            with patch.object(service, '_get_pos_revenue', return_value=pos_data):
                with patch.object(service, '_get_rfid_revenue', return_value=rfid_data):
                    
                    result = service.get_revenue_reconciliation()
                    
                    # Verify RFID source is marked as low confidence
                    rfid_source = result['revenue_sources']['rfid_correlation']
                    assert rfid_source['confidence'] == 'low'
                    assert '1.78%' in rfid_source['coverage']
                    
                    # Verify recommendations address RFID limitations
                    if 'recommendations' in result:
                        recommendations = result['recommendations']
                        assert any('RFID correlation coverage' in str(rec) for rec in recommendations)