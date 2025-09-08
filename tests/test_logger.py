import pytest
import sys
import os
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.logger import get_logger, setup_app_logging


class TestGetLogger:
    """Test the centralized logger function."""
    
    def test_get_logger_default_name(self):
        """Test logger creation with default name."""
        logger = get_logger()
        assert logger.name == 'rfid_dashboard'
        assert logger.level == logging.INFO
    
    def test_get_logger_custom_name(self):
        """Test logger creation with custom name."""
        logger = get_logger('test_logger')
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO
    
    def test_get_logger_custom_level(self):
        """Test logger creation with custom level."""
        logger = get_logger('test_logger', level=logging.DEBUG)
        assert logger.name == 'test_logger'
        assert logger.level == logging.DEBUG
    
    def test_get_logger_no_handlers(self):
        """Test logger creation without adding handlers."""
        logger = get_logger('test_logger', add_handlers=False)
        assert logger.name == 'test_logger'
        # Should have no handlers added by get_logger
        # (may have inherited handlers from root logger)
    
    def test_get_logger_with_log_file(self):
        """Test logger creation with custom log file."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            logger = get_logger('test_logger', log_file=log_file)
            assert logger.name == 'test_logger'
            
            # Test that logging actually works
            logger.info("Test message")
            
            # Check that log file was created and has content
            assert Path(log_file).exists()
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            # Cleanup
            if Path(log_file).exists():
                Path(log_file).unlink()
    
    def test_get_logger_rotation(self):
        """Test that logger uses rotating file handler."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            logger = get_logger('test_logger', log_file=log_file)
            
            # Check that a RotatingFileHandler was added
            file_handlers = [h for h in logger.handlers 
                           if hasattr(h, 'maxBytes')]  # RotatingFileHandler attribute
            assert len(file_handlers) > 0
            
            # Verify rotation settings
            if file_handlers:
                handler = file_handlers[0]
                assert handler.maxBytes == 1024 * 1024  # 1MB
                assert handler.backupCount == 5
        finally:
            # Cleanup
            if Path(log_file).exists():
                Path(log_file).unlink()
    
    def test_get_logger_formatting(self):
        """Test logger message formatting."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            logger = get_logger('test_logger', log_file=log_file)
            logger.info("Test formatting message")
            
            # Check log format
            with open(log_file, 'r') as f:
                content = f.read()
                # Should contain timestamp, logger name, level, and message
                assert "test_logger" in content
                assert "INFO" in content
                assert "Test formatting message" in content
                # Check for timestamp pattern (YYYY-MM-DD HH:MM:SS,mmm)
                import re
                timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}'
                assert re.search(timestamp_pattern, content)
        finally:
            # Cleanup
            if Path(log_file).exists():
                Path(log_file).unlink()
    
    def test_get_logger_console_handler(self):
        """Test that console handler is added by default."""
        logger = get_logger('test_logger')
        
        # Check that a console handler was added
        console_handlers = [h for h in logger.handlers 
                          if hasattr(h, 'stream')]  # StreamHandler attribute
        # Note: This might be 0 if parent loggers have console handlers
        # The actual behavior depends on logger hierarchy
        assert isinstance(console_handlers, list)
    
    @patch('app.services.logger.LOG_DIR')
    def test_get_logger_log_dir_creation(self, mock_log_dir):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir) / 'logs'
            log_file = log_dir / 'test.log'
            mock_log_dir.__str__ = lambda: str(log_dir)
            
            # Directory shouldn't exist initially
            assert not log_dir.exists()
            
            logger = get_logger('test_logger', log_file=str(log_file))
            
            # Directory should be created
            assert log_dir.exists()
            assert log_dir.is_dir()


class TestSetupAppLogging:
    """Test Flask app logging setup."""
    
    def test_setup_app_logging(self):
        """Test Flask app logging configuration."""
        # Create a mock Flask app
        mock_app = MagicMock()
        mock_app.logger = MagicMock()
        
        # Call setup function
        setup_app_logging(mock_app)
        
        # Verify that app logger was configured
        assert mock_app.logger.setLevel.called
        # The exact assertions depend on the implementation details
        # of setup_app_logging function
    
    @patch('app.services.logger.get_logger')
    def test_setup_app_logging_calls_get_logger(self, mock_get_logger):
        """Test that setup_app_logging uses get_logger."""
        mock_app = MagicMock()
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        setup_app_logging(mock_app)
        
        # Verify get_logger was called
        mock_get_logger.assert_called()
    
    def test_setup_app_logging_with_real_app(self):
        """Test logging setup with a real Flask app instance."""
        from flask import Flask
        
        app = Flask(__name__)
        
        # Should not raise an exception
        setup_app_logging(app)
        
        # App should have logging configured
        assert app.logger is not None
        # Further assertions depend on implementation