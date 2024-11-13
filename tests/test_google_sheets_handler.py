"""
Test suite for Google Sheets handler functionality.
"""

import os
import unittest
import logging
import warnings
import tracemalloc
from pathlib import Path
import json

from google_services import GoogleSheetsHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestGoogleSheetsHandler(unittest.TestCase):
    """Test cases for GoogleSheetsHandler class."""

    # Define class variables first
    account_id = "JK"  # Test account
    test_folder_name = "ig JK tests"
    test_spreadsheet_name = "JK IG input table"

    @classmethod
    def verify_credentials_file(cls) -> None:
        """Verify the credentials file exists and has required fields."""
        env_var_name = f"GOOGLE_SHEETS_CONFIG_{cls.account_id}"
        creds_path = os.getenv(env_var_name)
        print(f"Using credentials path from {env_var_name}: {creds_path}")

        if not creds_path:
            raise ValueError(f"{env_var_name} environment variable not set")

        if not os.path.exists(creds_path):
            raise ValueError(f"Credentials file not found at: {creds_path}")

        try:
            with open(creds_path) as f:
                creds_data = json.load(f)

            # Check for OAuth2 credentials structure
            required_fields = ['token']
            missing_fields = [field for field in required_fields if field not in creds_data]
            if missing_fields:
                raise ValueError(f"Credentials file missing fields: {missing_fields}")

            # Parse token data
            token_data = json.loads(creds_data['token'])
            token_required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret']
            missing_token_fields = [field for field in token_required_fields if field not in token_data]
            if missing_token_fields:
                raise ValueError(f"Token data missing fields: {missing_token_fields}")

            logger.info("Credentials file verified successfully")

        except json.JSONDecodeError:
            raise ValueError("Credentials file is not valid JSON")
        except Exception as e:
            raise ValueError(f"Error verifying credentials: {str(e)}")

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        tracemalloc.start()
        cls.verify_credentials_file()
        
        # Create a single handler instance for all tests
        cls.handler = GoogleSheetsHandler(cls.account_id)
        if not cls.handler.authenticate():
            raise ValueError("Failed to authenticate with Google services")
        
        # Get folder ID
        cls.test_folder_id = cls.handler.get_folder_id(cls.test_folder_name)
        if not cls.test_folder_id:
            raise ValueError(f"Could not find folder: {cls.test_folder_name}")
        
        # Get spreadsheet ID
        cls.test_spreadsheet_id = cls.handler.get_file_id_by_name(
            cls.test_spreadsheet_name, cls.test_folder_id
        )
        if not cls.test_spreadsheet_id:
            raise ValueError(f"Could not find spreadsheet: {cls.test_spreadsheet_name}")
        
        logger.info("Test setup completed successfully")
        logger.info("Using folder ID: %s", cls.test_folder_id)
        logger.info("Using spreadsheet ID: %s", cls.test_spreadsheet_id)

    def setUp(self):
        """Set up each test."""
        # Use the class handler instance instead of creating a new one
        self.handler = self.__class__.handler
        # Ensure handler is authenticated
        if not self.handler.sheets_service or not self.handler.drive_service:
            self.handler.authenticate()

    def test_1_authentication(self):
        """Test Google services authentication."""
        self.assertTrue(self.handler.sheets_service is not None)
        self.assertTrue(self.handler.drive_service is not None)

    def test_2_spreadsheet_initialization(self):
        """Test spreadsheet initialization."""
        success = self.handler.initialize_spreadsheet(self.test_spreadsheet_id)
        self.assertTrue(success, "Spreadsheet initialization should succeed")
        self.assertEqual(self.handler.spreadsheet_id, self.test_spreadsheet_id)

    def test_3_folder_access(self):
        """Test Google Drive folder access."""
        folder_id = self.handler.get_folder_id(self.test_folder_name)
        self.assertIsNotNone(folder_id, "Should find the folder ID")
        self.assertEqual(folder_id, self.test_folder_id)
        logger.info("Found folder ID: %s", folder_id)

    def test_4_file_operations(self):
        """Test file operations in Google Drive."""
        contents = self.handler.list_folder_contents(self.test_folder_id)
        self.assertIsInstance(contents, list)
        self.assertTrue(len(contents) > 0, "Folder should not be empty")
        
        if contents:
            logger.info("First file in folder: %s", contents[0]["name"])
            file_id = contents[0]["id"]
            self.assertTrue(
                self.handler.verify_file_access(file_id),
                "Should be able to verify file access"
            )
            file_name = contents[0]["name"]
            found_id = self.handler.get_file_id_by_name(file_name, self.test_folder_id)
            self.assertEqual(file_id, found_id)

    def test_5_nonexistent_file(self):
        """Test handling of nonexistent files."""
        self.assertFalse(
            self.handler.verify_file_access("invalid_file_id"),
            "Should return False for invalid file ID"
        )
        self.assertIsNone(
            self.handler.get_file_id_by_name("nonexistent_file.txt"),
            "Should return None for nonexistent file"
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if hasattr(cls, 'handler'):
            cls.handler.cleanup()
        
        # Stop tracemalloc and get statistics
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        logger.info("Memory leak statistics:")
        for stat in top_stats[:3]:
            logger.info(str(stat))
            
        tracemalloc.stop()


def run_tests():
    """Run the test suite."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
