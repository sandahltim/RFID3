# app/utils/__init__.py
# Utility modules for RFID Dashboard

from .exceptions import (
    RFIDException,
    DatabaseException,
    APIException,
    ValidationException,
    ConfigurationException,
    DataProcessingException,
    handle_api_error,
    log_and_handle_exception,
    safe_database_operation,
    validate_required_fields,
    format_error_response,
)

__all__ = [
    "RFIDException",
    "DatabaseException",
    "APIException",
    "ValidationException",
    "ConfigurationException",
    "DataProcessingException",
    "handle_api_error",
    "log_and_handle_exception",
    "safe_database_operation",
    "validate_required_fields",
    "format_error_response",
]
