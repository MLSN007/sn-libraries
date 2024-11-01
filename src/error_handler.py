"""
Error handling utilities for the Instagram automation project.
"""

from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handles errors and exceptions in the Instagram automation process."""

    @staticmethod
    def handle_error(error: Exception, context: Optional[str] = None) -> None:
        """
        Handle an error by logging it appropriately.

        Args:
            error (Exception): The error that occurred
            context (Optional[str]): Additional context about where the error occurred
        """
        error_message = f"{str(error)}"
        if context:
            error_message = f"{context}: {error_message}"
        
        logger.error(error_message, exc_info=True)

    @staticmethod
    def log_warning(message: str, *args: Any) -> None:
        """
        Log a warning message.

        Args:
            message (str): The warning message
            *args: Additional arguments for string formatting
        """
        logger.warning(message, *args)

    @staticmethod
    def log_error(message: str, *args: Any) -> None:
        """
        Log an error message.

        Args:
            message (str): The error message
            *args: Additional arguments for string formatting
        """
        logger.error(message, *args)
