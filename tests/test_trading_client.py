import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import from scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.trading_212_client import Trading212Client

class TestTrading212Client(unittest.TestCase):

    @patch("scripts.trading_212_client.get_credential")
    @patch("scripts.trading_212_client.requests.get")
    def test_fetch_account_balance(self, mock_get, mock_get_credential):
        """Test fetching account balance with mocked API response."""
        # Mock credential
        mock_get_credential.return_value = "test_api_key"
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"currency": "USD", "free": 1000.0, "total": 1500.0}
        mock_get.return_value = mock_response

        client = Trading212Client()
        result = client.fetch_account_balance()

        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["free"], 1000.0)
        mock_get.assert_called_once()

    @patch("scripts.trading_212_client.get_credential")
    @patch("scripts.trading_212_client.requests.post")
    def test_place_order(self, mock_post, mock_get_credential):
        """Test placing an order with mocked API response."""
        # Mock credential
        mock_get_credential.return_value = "test_api_key"
        
        # Mock successful order response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"orderId": "12345", "status": "CONFIRMED"}
        mock_post.return_value = mock_response

        client = Trading212Client()
        result = client.place_order(ticker="AAPL", quantity=10, action="BUY")

        self.assertEqual(result["orderId"], "12345")
        self.assertEqual(result["status"], "CONFIRMED")
        mock_post.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_post.call_args
        self.assertIn("AAPL", str(call_args))

if __name__ == "__main__":
    unittest.main()