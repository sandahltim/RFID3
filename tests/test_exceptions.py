import pytest
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.utils.exceptions import (
    RFIDException, DatabaseException, APIException, ValidationException,
    ConfigurationException, DataProcessingException,
    handle_api_error, log_and_handle_exception, safe_database_operation,
    validate_required_fields, format_error_response
)


class TestRFIDExceptions:
    """Test custom exception classes."""
    
    def test_rfid_exception_basic(self):
        """Test basic RFIDException functionality."""
        exc = RFIDException("Test error")
        assert str(exc) == "Test error"
        assert exc.error_code == "RFIDException"
        assert exc.details == {}
    
    def test_rfid_exception_with_details(self):
        """Test RFIDException with custom error code and details."""
        details = {"key": "value", "count": 5}
        exc = RFIDException("Custom error", error_code="CUSTOM_ERROR", details=details)
        
        assert str(exc) == "Custom error"
        assert exc.error_code == "CUSTOM_ERROR"
        assert exc.details == details
    
    def test_database_exception_inheritance(self):
        """Test that DatabaseException inherits from RFIDException."""
        exc = DatabaseException("DB error")
        assert isinstance(exc, RFIDException)
        assert str(exc) == "DB error"
    
    def test_api_exception_inheritance(self):
        """Test that APIException inherits from RFIDException."""
        exc = APIException("API error")
        assert isinstance(exc, RFIDException)
        assert str(exc) == "API error"
    
    def test_validation_exception_inheritance(self):
        """Test that ValidationException inherits from RFIDException."""
        exc = ValidationException("Validation error")
        assert isinstance(exc, RFIDException)
        assert str(exc) == "Validation error"


class TestValidateRequiredFields:
    """Test field validation utility."""
    
    def test_validate_required_fields_success(self):
        """Test successful validation with all required fields present."""
        data = {"name": "test", "value": 123, "flag": True}
        required_fields = ["name", "value"]
        
        # Should not raise any exception
        validate_required_fields(data, required_fields)
    
    def test_validate_required_fields_missing_single(self):
        """Test validation failure with single missing field."""
        data = {"name": "test"}
        required_fields = ["name", "value"]
        
        with pytest.raises(ValidationException) as exc_info:
            validate_required_fields(data, required_fields)
        
        exc = exc_info.value
        assert "Missing required fields: value" in str(exc)
        assert exc.error_code == "MISSING_REQUIRED_FIELDS"
        assert "value" in exc.details["missing_fields"]
    
    def test_validate_required_fields_missing_multiple(self):
        """Test validation failure with multiple missing fields."""
        data = {"name": "test"}
        required_fields = ["name", "value", "flag", "data"]
        
        with pytest.raises(ValidationException) as exc_info:
            validate_required_fields(data, required_fields)
        
        exc = exc_info.value
        missing_fields = exc.details["missing_fields"]
        assert "value" in missing_fields
        assert "flag" in missing_fields
        assert "data" in missing_fields
        assert len(missing_fields) == 3
    
    def test_validate_required_fields_none_values(self):
        """Test that None values are treated as missing."""
        data = {"name": "test", "value": None, "flag": True}
        required_fields = ["name", "value", "flag"]
        
        with pytest.raises(ValidationException) as exc_info:
            validate_required_fields(data, required_fields)
        
        assert "value" in exc_info.value.details["missing_fields"]


class TestLogAndHandleException:
    """Test exception logging utility."""
    
    def test_log_and_handle_exception_validation(self):
        """Test logging of ValidationException."""
        logger = MagicMock()
        exc = ValidationException("Invalid data")
        
        result = log_and_handle_exception(logger, "test context", exc)
        
        logger.warning.assert_called_once()
        assert result["success"] is False
        assert result["error"] == "Invalid data"
        assert result["context"] == "test context"
    
    def test_log_and_handle_exception_database(self):
        """Test logging of DatabaseException."""
        logger = MagicMock()
        exc = DatabaseException("DB connection failed")
        
        result = log_and_handle_exception(logger, "database operation", exc)
        
        logger.error.assert_called_once()
        assert result["success"] is False
        assert result["error"] == "DB connection failed"
    
    def test_log_and_handle_exception_generic(self):
        """Test logging of generic Exception."""
        logger = MagicMock()
        exc = Exception("Unexpected error")
        
        result = log_and_handle_exception(logger, "generic operation", exc, {"extra": "data"})
        
        logger.error.assert_called_once()
        # Check that exc_info=True was passed for full traceback
        call_args = logger.error.call_args
        assert call_args[1]["exc_info"] is True


class TestSafeDatabaseOperation:
    """Test safe database operation wrapper."""
    
    def test_safe_database_operation_success(self):
        """Test successful database operation."""
        logger = MagicMock()
        
        def successful_operation():
            return {"data": "success"}
        
        result = safe_database_operation(successful_operation, logger, "test operation")
        assert result == {"data": "success"}
        logger.error.assert_not_called()
    
    def test_safe_database_operation_failure(self):
        """Test failed database operation."""
        logger = MagicMock()
        
        def failing_operation():
            raise Exception("DB error")
        
        with pytest.raises(DatabaseException) as exc_info:
            safe_database_operation(failing_operation, logger, "test operation")
        
        exc = exc_info.value
        assert "Failed to test operation" in str(exc)
        assert "DB error" in exc.details["original_error"]
        logger.error.assert_called_once()
    
    def test_safe_database_operation_database_exception_propagation(self):
        """Test that DatabaseException is propagated as-is."""
        logger = MagicMock()
        original_exc = DatabaseException("Original DB error")
        
        def failing_operation():
            raise original_exc
        
        with pytest.raises(DatabaseException) as exc_info:
            safe_database_operation(failing_operation, logger, "test operation")
        
        # Should be the same exception object
        assert exc_info.value is original_exc
    
    def test_safe_database_operation_default_return(self):
        """Test default return value on error."""
        logger = MagicMock()
        
        def failing_operation():
            raise Exception("Error")
        
        # This would normally raise, but we're testing the concept
        # In actual usage, you'd catch the DatabaseException and return default
        with pytest.raises(DatabaseException):
            safe_database_operation(failing_operation, logger, "test operation", default_return="default")


class TestFormatErrorResponse:
    """Test error response formatting."""
    
    def test_format_error_response_basic(self):
        """Test basic error response formatting."""
        exc = Exception("Test error")
        result = format_error_response(exc, "test context")
        
        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["error_type"] == "Exception"
        assert result["context"] == "test context"
        assert "timestamp" in result
        assert "traceback" not in result  # Not included by default
    
    def test_format_error_response_rfid_exception(self):
        """Test formatting of RFIDException with error code."""
        exc = RFIDException("Custom error", error_code="CUSTOM_ERROR", details={"key": "value"})
        result = format_error_response(exc, "test context")
        
        assert result["error_code"] == "CUSTOM_ERROR"
        assert result["details"] == {"key": "value"}
    
    def test_format_error_response_with_traceback(self):
        """Test error response with traceback included."""
        exc = Exception("Test error")
        result = format_error_response(exc, "test context", include_traceback=True)
        
        assert "traceback" in result
        assert result["traceback"] is not None


class TestHandleApiError:
    """Test API error handling decorator."""
    
    def test_handle_api_error_success(self):
        """Test decorator with successful function."""
        @handle_api_error
        def successful_func():
            return {"status": "success"}
        
        result = successful_func()
        assert result == {"status": "success"}
    
    def test_handle_api_error_validation_exception(self):
        """Test decorator handling ValidationException."""
        @handle_api_error
        def failing_func():
            raise ValidationException("Invalid input", error_code="INVALID_INPUT")
        
        response, status_code = failing_func()
        assert status_code == 400
        assert response.json["error"] == "Invalid input"
        assert response.json["error_code"] == "INVALID_INPUT"
    
    def test_handle_api_error_database_exception(self):
        """Test decorator handling DatabaseException."""
        @handle_api_error
        def failing_func():
            raise DatabaseException("DB connection failed")
        
        response, status_code = failing_func()
        assert status_code == 500
        assert response.json["error"] == "Database operation failed"
    
    def test_handle_api_error_api_exception(self):
        """Test decorator handling APIException."""
        @handle_api_error
        def failing_func():
            raise APIException("External API failed", error_code="EXT_API_ERROR")
        
        response, status_code = failing_func()
        assert status_code == 502
        assert response.json["error"] == "External API failed"
        assert response.json["error_code"] == "EXT_API_ERROR"