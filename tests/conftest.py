import pytest
import sys
import os
from unittest.mock import MagicMock

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def mock_db():
    """Mock database session for testing."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.query.return_value.all.return_value = []
    mock_session.query.return_value.count.return_value = 0
    return mock_session


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        'tag_id': 'TEST001',
        'common_name': 'Test Item',
        'status': 'Ready to Rent',
        'rental_class_num': 100,
        'date_last_scanned': '2025-01-01 12:00:00'
    }


@pytest.fixture 
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        'tag_id': 'TEST001',
        'contract_num': 'C001',
        'scan_date': '2025-01-01 12:00:00',
        'event_type': 'out'
    }


@pytest.fixture
def mock_flask_app():
    """Mock Flask application for testing."""
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return MagicMock()


@pytest.fixture 
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setnx.return_value = True
    mock_redis.expire.return_value = True
    mock_redis.delete.return_value = True
    return mock_redis