# app/utils/exceptions.py
# Custom exceptions and error handling utilities for RFID Dashboard

import logging
from functools import wraps
from flask import jsonify, request
from typing import Dict, Any, Optional, Callable
import traceback


class RFIDException(Exception):
    """Base exception class for RFID Dashboard."""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(RFIDException):
    """Database-related exceptions."""
    pass


class APIException(RFIDException):
    """API-related exceptions."""
    pass


class ValidationException(RFIDException):
    """Data validation exceptions."""
    pass


class ConfigurationException(RFIDException):
    """Configuration-related exceptions."""
    pass


class DataProcessingException(RFIDException):
    """Data processing and transformation exceptions."""
    pass


def handle_api_error(func: Callable) -> Callable:
    """
    Decorator for consistent API error handling.
    
    Usage:
    @handle_api_error
    def my_api_endpoint():
        # endpoint logic
        pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationException as e:
            return jsonify({
                'error': e.message,
                'error_code': e.error_code,
                'details': e.details
            }), 400
        except DatabaseException as e:
            return jsonify({
                'error': 'Database operation failed',
                'error_code': e.error_code,
                'details': e.details
            }), 500
        except APIException as e:
            return jsonify({
                'error': e.message,
                'error_code': e.error_code,
                'details': e.details
            }), 502
        except RFIDException as e:
            return jsonify({
                'error': e.message,
                'error_code': e.error_code,
                'details': e.details
            }), 500
        except Exception as e:
            # Log unexpected errors with full traceback
            logger = logging.getLogger(func.__module__)
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", 
                        exc_info=True, 
                        extra={'endpoint': request.endpoint, 
                              'method': request.method,
                              'url': request.url})
            
            return jsonify({
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR',
                'details': {'function': func.__name__}
            }), 500
    
    return wrapper


def log_and_handle_exception(logger: logging.Logger, 
                           context: str,
                           exception: Exception,
                           extra_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Centralized exception logging and response formatting.
    
    Args:
        logger: Logger instance to use
        context: Description of what was being done when error occurred
        exception: The exception that was caught
        extra_data: Additional context data to include in logs
        
    Returns:
        Standardized error response dictionary
    """
    error_data = {
        'context': context,
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'traceback': traceback.format_exc() if logger.level <= logging.DEBUG else None
    }
    
    if extra_data:
        error_data.update(extra_data)
    
    # Log with appropriate level based on exception type
    if isinstance(exception, (ValidationException, APIException)):
        logger.warning(f"{context}: {str(exception)}", extra=error_data)
    elif isinstance(exception, DatabaseException):
        logger.error(f"Database error in {context}: {str(exception)}", extra=error_data)
    else:
        logger.error(f"Unexpected error in {context}: {str(exception)}", 
                    exc_info=True, extra=error_data)
    
    return {
        'success': False,
        'error': str(exception),
        'error_type': type(exception).__name__,
        'context': context
    }


def safe_database_operation(func: Callable, 
                          logger: logging.Logger,
                          operation_name: str,
                          default_return: Any = None) -> Any:
    """
    Safely execute database operations with consistent error handling.
    
    Args:
        func: Function to execute
        logger: Logger to use for errors
        operation_name: Description of the operation
        default_return: Value to return on error
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"Database operation failed ({operation_name}): {str(e)}", 
                    exc_info=True)
        if isinstance(e, DatabaseException):
            raise
        else:
            raise DatabaseException(f"Failed to {operation_name}", details={'original_error': str(e)})


def validate_required_fields(data: Dict[str, Any], 
                            required_fields: list,
                            context: str = "data validation") -> None:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context description for error messages
        
    Raises:
        ValidationException: If required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationException(
            f"Missing required fields: {', '.join(missing_fields)}",
            error_code="MISSING_REQUIRED_FIELDS",
            details={'missing_fields': missing_fields, 'context': context}
        )


def format_error_response(error: Exception, 
                         context: str,
                         include_traceback: bool = False) -> Dict[str, Any]:
    """
    Format exception as standardized error response.
    
    Args:
        error: Exception to format
        context: Context where error occurred
        include_traceback: Whether to include full traceback
        
    Returns:
        Formatted error dictionary
    """
    response = {
        'success': False,
        'error': str(error),
        'error_type': type(error).__name__,
        'context': context,
        'timestamp': logging.Formatter().formatTime(logging.LogRecord(
            name='', level=0, pathname='', lineno=0, msg='', args=(), exc_info=None
        ))
    }
    
    if isinstance(error, RFIDException):
        response['error_code'] = error.error_code
        response['details'] = error.details
    
    if include_traceback:
        response['traceback'] = traceback.format_exc()
    
    return response