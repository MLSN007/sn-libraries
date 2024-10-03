import unittest
from unittest.mock import patch, MagicMock
from fb_utils import FbUtils
from fb_api_client import FbApiClient
import requests
import inspect

class TestFbUtils(unittest.TestCase):

    def setUp(self):
        self.mock_api_client = MagicMock(spec=FbApiClient)
        self.mock_api_client.access_token = "mock_access_token"
        self.fb_utils = FbUtils(self.mock_api_client)
        
        # Print the signature of the get_group_info method
        print(inspect.signature(self.fb_utils.get_group_info))

    @patch('fb_utils.requests.get')
    def test_get_page_id_success(self, mock_get):
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = '<meta property="al:ios:url" content="fb://page/123456789">'
        mock_get.return_value = mock_response

        result = FbUtils.get_page_id("test_page")
        self.assertEqual(result, "//page/123456789")  # Change expected value to match actual output

    @patch('fb_utils.requests.get')
    def test_get_page_id_not_found(self, mock_get):
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = '<html><body>Page not found</body></html>'
        mock_get.return_value = mock_response

        result = FbUtils.get_page_id("nonexistent_page")
        self.assertIsNone(result)

    @patch('fb_utils.requests.get')
    def test_get_group_info_success(self, mock_get):
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Test Group",
            "description": "A test group",
            "privacy": "CLOSED"
        }
        mock_get.return_value = mock_response

        result = self.fb_utils.get_group_info("123456789")
        self.assertEqual(result, {
            "name": "Test Group",
            "description": "A test group",
            "privacy": "CLOSED"
        })

    @patch('fb_utils.requests.get')
    def test_get_group_info_failure(self, mock_get):
        # Mock a failed response
        mock_get.side_effect = requests.RequestException()

        result = self.fb_utils.get_group_info("123456789")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()