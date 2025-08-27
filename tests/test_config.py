import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class TestConfiguration:
    """Test configuration module and validation."""
    
    def test_base_dir_is_path_object(self):
        """Test that BASE_DIR is a pathlib.Path object."""
        import config
        assert isinstance(config.BASE_DIR, Path)
        assert config.BASE_DIR.is_absolute()
    
    def test_dynamic_paths(self):
        """Test that dynamic paths are properly constructed."""
        import config
        
        # LOG_DIR should be BASE_DIR / "logs"
        expected_log_dir = config.BASE_DIR / "logs"
        assert config.LOG_DIR == expected_log_dir
        
        # STATIC_DIR should be BASE_DIR / "static"  
        expected_static_dir = config.BASE_DIR / "static"
        assert config.STATIC_DIR == expected_static_dir
    
    def test_path_strings_conversion(self):
        """Test that paths can be converted to strings for compatibility."""
        import config
        
        # Should be able to convert to strings
        log_dir_str = str(config.LOG_DIR)
        static_dir_str = str(config.STATIC_DIR)
        
        assert isinstance(log_dir_str, str)
        assert isinstance(static_dir_str, str)
        assert log_dir_str.endswith('logs')
        assert static_dir_str.endswith('static')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_configuration_values(self):
        """Test that default values are used when environment variables are not set."""
        # Clear the config module cache to force re-import
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Should have default values
        assert config.API_USERNAME == "api"
        assert config.API_PASSWORD == "password"
        assert config.DB_PASSWORD == "password"
    
    @patch.dict(os.environ, {
        'API_USERNAME': 'test_user',
        'API_PASSWORD': 'test_pass',
        'DB_PASSWORD': 'test_db_pass'
    }, clear=True)
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        # Clear the config module cache to force re-import
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        
        # Should use environment values
        assert config.API_USERNAME == "test_user"
        assert config.API_PASSWORD == "test_pass" 
        assert config.DB_PASSWORD == "test_db_pass"
    
    @patch('config.logging.warning')
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_config_warns_about_defaults(self, mock_warning):
        """Test that validate_config warns when using default values."""
        # Clear the config module cache to force re-import
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        config.validate_config()
        
        # Should have called warning
        mock_warning.assert_called_once()
        call_args = mock_warning.call_args[0][0]
        assert "Using default values for" in call_args
        assert "API_USERNAME" in call_args
        assert "API_PASSWORD" in call_args
        assert "DB_PASSWORD" in call_args
    
    @patch('config.logging.warning')
    @patch.dict(os.environ, {
        'API_USERNAME': 'test_user',
        'API_PASSWORD': 'test_pass',
        'DB_PASSWORD': 'test_db_pass'
    }, clear=True)
    def test_validate_config_no_warning_with_env_vars(self, mock_warning):
        """Test that validate_config doesn't warn when environment variables are set."""
        # Clear the config module cache to force re-import
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        config.validate_config()
        
        # Should not have called warning
        mock_warning.assert_not_called()
    
    @patch('config.logging.warning')
    @patch.dict(os.environ, {
        'API_USERNAME': 'test_user',
        # API_PASSWORD and DB_PASSWORD not set
    }, clear=True)
    def test_validate_config_partial_env_vars(self, mock_warning):
        """Test validate_config with partial environment variable coverage."""
        # Clear the config module cache to force re-import
        if 'config' in sys.modules:
            del sys.modules['config']
        
        import config
        config.validate_config()
        
        # Should warn about the missing ones
        mock_warning.assert_called_once()
        call_args = mock_warning.call_args[0][0]
        assert "API_PASSWORD" in call_args
        assert "DB_PASSWORD" in call_args
        assert "API_USERNAME" not in call_args  # This one was set
    
    def test_required_config_constants(self):
        """Test that all required configuration constants are present."""
        import config
        
        # Database configuration
        assert hasattr(config, 'DB_HOST')
        assert hasattr(config, 'DB_USERNAME')
        assert hasattr(config, 'DB_PASSWORD')
        assert hasattr(config, 'DB_NAME')
        
        # API configuration
        assert hasattr(config, 'API_USERNAME')
        assert hasattr(config, 'API_PASSWORD')
        assert hasattr(config, 'LOGIN_URL')
        
        # Path configuration
        assert hasattr(config, 'BASE_DIR')
        assert hasattr(config, 'LOG_DIR')
        assert hasattr(config, 'STATIC_DIR')
        assert hasattr(config, 'LOG_FILE')
        
        # Redis configuration
        assert hasattr(config, 'REDIS_HOST')
        assert hasattr(config, 'REDIS_PORT')
    
    def test_log_file_path_construction(self):
        """Test that LOG_FILE is properly constructed."""
        import config
        
        expected_log_file = config.LOG_DIR / "rfid_dashboard.log"
        assert config.LOG_FILE == expected_log_file
        
        # Should be able to convert to string
        log_file_str = str(config.LOG_FILE)
        assert log_file_str.endswith("rfid_dashboard.log")
    
    def test_database_url_construction(self):
        """Test database URL construction if applicable."""
        import config
        
        # Check if DATABASE_URL or similar exists
        if hasattr(config, 'DATABASE_URL'):
            assert isinstance(config.DATABASE_URL, str)
            assert config.DB_HOST in config.DATABASE_URL
            assert config.DB_NAME in config.DATABASE_URL
    
    def test_cross_platform_compatibility(self):
        """Test that paths work across different platforms."""
        import config
        
        # Paths should be absolute and properly formatted
        assert config.BASE_DIR.is_absolute()
        assert config.LOG_DIR.is_absolute()
        assert config.STATIC_DIR.is_absolute()
        
        # Should work with both forward and backward slashes
        log_dir_parts = config.LOG_DIR.parts
        static_dir_parts = config.STATIC_DIR.parts
        
        assert len(log_dir_parts) > 1
        assert len(static_dir_parts) > 1
        assert log_dir_parts[-1] == "logs"
        assert static_dir_parts[-1] == "static"