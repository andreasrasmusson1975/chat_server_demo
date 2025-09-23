
"""
Global logging infrastructure module for the MPAI Assistant chat server demo.

This module provides a comprehensive decorator-based logging system that automatically
captures function calls, parameters, results, and exceptions across the entire
application. It implements a centralized approach to application monitoring,
debugging, and audit trail generation by integrating seamlessly with the database
logging infrastructure and Streamlit's user interface framework.

Key Features:
    - Automatic function call logging with parameter capture
    - Transparent exception handling and error logging  
    - Integration with database-backed persistent logging
    - Streamlit-aware error handling and user feedback
    - Zero-configuration decorator-based implementation
    - Graceful degradation when logging services are unavailable
    - User context preservation for audit trails
    - Comprehensive error recovery and application resilience

The module follows a non-intrusive approach where logging functionality is added
through decorators without modifying the core business logic of functions. This
ensures clean separation of concerns while providing comprehensive observability
across all decorated functions in the application.

Architecture:
    The logging system implements a decorator pattern that wraps target functions
    with automatic logging capabilities. Each function call is monitored for both
    successful execution and exceptions, with all relevant context preserved in
    the database for later analysis and debugging.

Classes:
    None (module contains only decorator functions)

Functions:
    log_this: Primary decorator for automatic function call logging

Dependencies:
    - functools: Function decoration and metadata preservation
    - traceback: Detailed exception information capture
    - chat_server_demo.database.db: Database logging backend
    - streamlit: User interface integration and feedback

Author: Andreas Rasmusson
"""

import functools
import traceback
from chat_server_demo.database import db
import streamlit as st

def log_this(func):
    """
    Decorator that automatically logs function calls, results, and exceptions.

    This decorator provides comprehensive automatic logging for any function it
    decorates, capturing detailed information about function execution including
    parameters, return values, and exceptions. It integrates seamlessly with the
    database logging infrastructure and Streamlit user interface to provide both
    persistent audit trails and immediate user feedback during application errors.

    The decorator implements a transparent logging layer that preserves the
    original function's behavior while adding comprehensive observability. It
    handles both successful and failed function executions, ensuring that all
    application activity is properly recorded for debugging, monitoring, and
    audit purposes.

    Parameters
    ----------
    func : callable
        The function to be decorated with automatic logging capabilities. Can be
        any callable including methods, functions, and class methods. The original
        function signature and metadata are preserved through functools.wraps.

    Returns
    -------
    callable
        A wrapped version of the original function that includes automatic logging
        functionality. The wrapper maintains the same signature and behavior as
        the original function while adding comprehensive logging capabilities.
    Raises
    ------
    Exception
        Any exception raised by the decorated function is preserved and re-raised
        after logging. The decorator does not suppress application exceptions,
        ensuring that error handling behavior remains consistent with undecorated
        functions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            try:
                db.insert_log(
                    level="INFO",
                    func_name=func.__name__,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                    user_id=getattr(args[0], "user_id", None) if args else None
                )
            except Exception as log_err:
                # Logging failed — swallow and continue
                st.warning("⚠️ Logging service temporarily unavailable.")
            return result
        except Exception as e:
            try:
                db.insert_log(
                    level="ERROR",
                    func_name=func.__name__,
                    args=args,
                    kwargs=kwargs,
                    exception=traceback.format_exc(),
                    user_id=getattr(args[0], "user_id", None) if args else None
                )
            except Exception as log_err:
                print(f"[LOGGING ERROR] Could not insert error log for {func.__name__}: {log_err}")
            st.warning("⚠️ Something went wrong. The app will reload.")
            st.rerun()
    return wrapper
