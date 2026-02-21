import unittest
from unittest.mock import patch, MagicMock
from trading_212_client import Trading212Client

class TestTrading212Client(unittest.TestCase):

    @patch("trading_212_client.Trading212Client.fetch_account_balance")
    def test_fetch_account_balance(self, mock_fetch_balance):
        mock_balance = {"currency": "USD", "amount": 1000.0}
        mock_fetch_balance.return_value = mock_balance

        client = Trading212Client()
        result = client.fetch_account_balance()

        self.assertEqual(result, mock_balance)
        mock_fetch_balance.assert_called_once()

    @patch("trading_212_client.Trading212Client.place_order")
    def test_place_order(self, mock_place_order):
        mock_response = {"status": "success"}
        mock_place_order.return_value = mock_response

        client = Trading212Client()
        result = client.place_order(ticker="AAPL", quantity=10, action="BUY")

        self.assertEqual(result, mock_response)
        mock_place_order.assert_called_once_with(ticker="AAPL", quantity=10, action="BUY")

if __name__ == "__main__":
    unittest.main()