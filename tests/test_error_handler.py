"""
Test suite for error handling functionality.
"""

import unittest
import logging
from sn_utils import ErrorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestErrorHandler(unittest.TestCase):
    """Test cases for ErrorHandler class."""

    def test_handle_error(self):
        """Test error handling with context."""
        try:
            raise ValueError("Test error")
        except Exception as e:
            ErrorHandler.handle_error(e, "Test context")

    def test_log_warning(self):
        """Test warning logging."""
        ErrorHandler.log_warning("Test warning message")

    def test_log_error(self):
        """Test error logging."""
        ErrorHandler.log_error("Test error message")

if __name__ == '__main__':
    unittest.main() 